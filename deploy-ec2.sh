#!/bin/bash
set -e

# Counterparty API EC2 Deployment Script
# This script automates the deployment of Counterparty API with OGG/Opus support on AWS EC2

echo "========================================"
echo "Counterparty API EC2 Deployment"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Ubuntu/Debian
if [ ! -f /etc/debian_version ]; then
    print_error "This script is designed for Ubuntu/Debian systems"
    exit 1
fi

print_info "Starting deployment process..."

# Step 1: Update system
print_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Docker
if ! command -v docker &> /dev/null; then
    print_info "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_info "Docker installed successfully"
else
    print_info "Docker already installed"
fi

# Step 3: Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_info "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_info "Docker Compose installed successfully"
else
    print_info "Docker Compose already installed"
fi

# Step 4: Install additional utilities
print_info "Installing additional utilities..."
sudo apt install -y git curl wget htop nginx certbot python3-certbot-nginx fail2ban ufw

# Step 5: Setup UFW firewall
print_info "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 4000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
print_info "Firewall configured"

# Step 6: Setup Fail2Ban
print_info "Configuring Fail2Ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Step 7: Clone repository (if not already cloned)
REPO_DIR="$HOME/xcp-api-mime"
if [ ! -d "$REPO_DIR" ]; then
    print_info "Cloning repository..."
    read -p "Enter your GitHub repository URL (or press Enter to skip): " REPO_URL
    if [ -n "$REPO_URL" ]; then
        git clone "$REPO_URL" "$REPO_DIR"
    else
        print_warning "Repository not cloned. Please clone manually."
        REPO_DIR=""
    fi
else
    print_info "Repository already exists at $REPO_DIR"
fi

# Step 8: Configure Counterparty
if [ -n "$REPO_DIR" ]; then
    cd "$REPO_DIR"
    
    # Create config directory
    mkdir -p config
    
    # Get Bitcoin RPC credentials
    print_info "Configuring Counterparty..."
    echo ""
    read -p "Bitcoin RPC Host (default: host.docker.internal): " BTC_HOST
    BTC_HOST=${BTC_HOST:-host.docker.internal}
    
    read -p "Bitcoin RPC Port (default: 8332): " BTC_PORT
    BTC_PORT=${BTC_PORT:-8332}
    
    read -p "Bitcoin RPC Username (default: rpc): " BTC_USER
    BTC_USER=${BTC_USER:-rpc}
    
    read -sp "Bitcoin RPC Password: " BTC_PASS
    echo ""
    
    # Create server.conf
    cat > config/server.conf << EOF
[Default]
backend-connect=$BTC_HOST
backend-port=$BTC_PORT
backend-user=$BTC_USER
backend-password=$BTC_PASS
rpc-host=0.0.0.0
rpc-port=4000
EOF
    
    # Update docker-compose.yml environment variables
    print_info "Updating docker-compose.yml..."
    sed -i "s/BACKEND_CONNECT=.*/BACKEND_CONNECT=$BTC_HOST/" docker-compose.yml
    sed -i "s/BACKEND_PORT=.*/BACKEND_PORT=$BTC_PORT/" docker-compose.yml
    sed -i "s/BACKEND_USER=.*/BACKEND_USER=$BTC_USER/" docker-compose.yml
    sed -i "s/BACKEND_PASSWORD=.*/BACKEND_PASSWORD=$BTC_PASS/" docker-compose.yml
    
    print_info "Configuration complete"
fi

# Step 9: Setup systemd service
print_info "Creating systemd service..."
sudo tee /etc/systemd/system/counterparty.service > /dev/null << EOF
[Unit]
Description=Counterparty API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$REPO_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable counterparty

# Step 10: Setup backup script
print_info "Creating backup script..."
cat > "$HOME/backup-counterparty.sh" << 'EOF'
#!/bin/bash
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Counterparty data
cd ~/xcp-api-mime
docker-compose exec -T counterparty tar czf - /root/.local/share/counterparty > $BACKUP_DIR/counterparty_$DATE.tar.gz

# Keep only last 7 days
find $BACKUP_DIR -name "counterparty_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/counterparty_$DATE.tar.gz"
EOF

chmod +x "$HOME/backup-counterparty.sh"

# Add to crontab
(crontab -l 2>/dev/null | grep -v backup-counterparty.sh; echo "0 2 * * * $HOME/backup-counterparty.sh") | crontab -

print_info "Backup script created and scheduled (daily at 2 AM)"

# Step 11: Setup Nginx (optional)
read -p "Do you want to setup Nginx reverse proxy? (y/n): " SETUP_NGINX
if [ "$SETUP_NGINX" = "y" ] || [ "$SETUP_NGINX" = "Y" ]; then
    read -p "Enter your domain name (or press Enter to skip SSL): " DOMAIN
    
    sudo tee /etc/nginx/sites-available/counterparty > /dev/null << EOF
server {
    listen 80;
    server_name ${DOMAIN:-_};

    location / {
        proxy_pass http://localhost:4000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/counterparty /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl restart nginx
    
    if [ -n "$DOMAIN" ]; then
        read -p "Do you want to setup SSL with Let's Encrypt? (y/n): " SETUP_SSL
        if [ "$SETUP_SSL" = "y" ] || [ "$SETUP_SSL" = "Y" ]; then
            sudo certbot --nginx -d "$DOMAIN"
        fi
    fi
fi

# Step 12: Build and start services
if [ -n "$REPO_DIR" ]; then
    print_info "Building Docker images..."
    cd "$REPO_DIR"
    docker-compose build
    
    read -p "Do you want to start the services now? (y/n): " START_NOW
    if [ "$START_NOW" = "y" ] || [ "$START_NOW" = "Y" ]; then
        print_info "Starting services..."
        docker-compose up -d
        
        print_info "Waiting for services to start..."
        sleep 10
        
        print_info "Checking service status..."
        docker-compose ps
        
        echo ""
        print_info "Deployment complete!"
        echo ""
        print_info "You can check logs with: docker-compose logs -f counterparty"
        print_info "API will be available at: http://localhost:4000"
        if [ -n "$DOMAIN" ]; then
            print_info "Or at: http://$DOMAIN"
        fi
        echo ""
        print_warning "Note: The first bootstrap will take several hours to days."
        print_warning "Monitor progress with: docker-compose logs -f counterparty"
    fi
fi

echo ""
print_info "========================================"
print_info "Deployment script completed!"
print_info "========================================"
echo ""
print_info "Next steps:"
echo "  1. Monitor bootstrap: docker-compose logs -f counterparty"
echo "  2. Test API: curl http://localhost:4000/v2/"
echo "  3. Check AWS_DEPLOYMENT.md for detailed usage instructions"
echo ""
print_info "To start services manually: sudo systemctl start counterparty"
print_info "To check status: sudo systemctl status counterparty"
echo ""
