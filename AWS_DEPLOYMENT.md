# AWS EC2 Deployment Guide for Counterparty API with OGG/Opus Support

This guide walks you through deploying the Counterparty API with OGG/Opus MIME type support to an AWS EC2 instance.

## Prerequisites

- AWS account with EC2 access
- SSH key pair for EC2 instance access
- Domain name (optional, for HTTPS setup)
- Bitcoin Core node (can be on the same EC2 instance or external)

## EC2 Instance Requirements

### Recommended Specifications
- **Instance Type**: `t3.medium` or larger (2 vCPU, 4GB RAM minimum)
- **Storage**: 100GB+ SSD (for Counterparty database)
- **OS**: Ubuntu 22.04 LTS or Amazon Linux 2023
- **Security Group**: 
  - Port 22 (SSH)
  - Port 4000 (Counterparty API)
  - Port 8332 (Bitcoin RPC, if running Bitcoin node on same instance)
  - Port 443 (HTTPS, optional)

## Step 1: Launch EC2 Instance

1. **Launch Instance**:
   ```bash
   # Using AWS CLI (optional)
   aws ec2 run-instances \
     --image-id ami-0c55b159cbfafe1f0 \
     --instance-type t3.medium \
     --key-name your-key-pair \
     --security-group-ids sg-xxxxxxxxx \
     --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]' \
     --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=counterparty-api}]'
   ```

2. **Connect to Instance**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-public-ip
   ```

## Step 2: Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## Step 3: Setup Bitcoin Core Node (Optional)

If you're running Bitcoin Core on the same EC2 instance:

```bash
# Create Bitcoin data directory
mkdir -p ~/bitcoin-data

# Create bitcoin.conf
cat > ~/bitcoin-data/bitcoin.conf << 'EOF'
# Bitcoin Core Configuration
server=1
rpcuser=rpc
rpcpassword=CHANGE_THIS_PASSWORD
rpcallowip=0.0.0.0/0
rpcbind=0.0.0.0
txindex=1
prune=0

# Network (use testnet for testing)
# testnet=1
EOF

# Run Bitcoin Core in Docker
docker run -d \
  --name bitcoind \
  --restart unless-stopped \
  -v ~/bitcoin-data:/bitcoin/.bitcoin \
  -p 8332:8332 \
  -p 8333:8333 \
  bitcoin/bitcoin:28.0 \
  bitcoind -conf=/bitcoin/.bitcoin/bitcoin.conf
```

**Note**: Bitcoin Core will take several days to sync. For faster deployment, use an external Bitcoin node.

## Step 4: Deploy Counterparty API

1. **Clone Repository**:
   ```bash
   cd ~
   git clone https://github.com/YOUR_USERNAME/xcp-api-mime.git
   cd xcp-api-mime
   ```

2. **Configure Environment**:
   ```bash
   # Create config directory
   mkdir -p config

   # Create server.conf
   cat > config/server.conf << 'EOF'
[Default]
backend-connect=host.docker.internal
backend-port=8332
backend-user=rpc
backend-password=CHANGE_THIS_PASSWORD
rpc-host=0.0.0.0
rpc-port=4000
EOF
   ```

3. **Update docker-compose.yml** (if needed):
   ```bash
   # Edit docker-compose.yml to match your Bitcoin node configuration
   nano docker-compose.yml
   ```

   Update the environment variables:
   ```yaml
   environment:
     - BACKEND_CONNECT=host.docker.internal  # or IP of external Bitcoin node
     - BACKEND_PORT=8332
     - BACKEND_USER=rpc
     - BACKEND_PASSWORD=YOUR_PASSWORD
   ```

4. **Build and Start Services**:
   ```bash
   # Build the Docker image
   docker-compose build

   # Start services
   docker-compose up -d

   # Check logs
   docker-compose logs -f counterparty
   ```

## Step 5: Bootstrap Counterparty Database

The first time you run Counterparty, it needs to bootstrap (sync with Bitcoin blockchain):

```bash
# Monitor bootstrap progress
docker-compose logs -f counterparty

# This will take several hours to days depending on:
# - Bitcoin node sync status
# - Network speed
# - EC2 instance performance
```

## Step 6: Test API

Once bootstrapped, test the API:

```bash
# Health check
curl http://localhost:4000/v2/

# Test OGG/Opus support
# Create a test OGG file hex
echo "4f676753" > /tmp/test.hex  # "OggS" magic number

# Test minting with audio/ogg;codecs=opus
WALLET_ADDRESS="YOUR_BITCOIN_ADDRESS"
HEX_DATA=$(cat /tmp/test.hex)

curl -X POST "http://localhost:4000/v2/addresses/$WALLET_ADDRESS/compose/issuance" \
  -H "Accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "asset=TESTOPUS" \
  --data-urlencode "quantity=1" \
  --data-urlencode "divisible=false" \
  --data-urlencode "description=$HEX_DATA" \
  --data-urlencode "encoding=taproot" \
  --data-urlencode "inscription=true" \
  --data-urlencode "mime_type=audio/ogg;codecs=opus" \
  --data-urlencode "fee_rate=1"
```

## Step 7: Setup HTTPS (Optional but Recommended)

### Using Nginx as Reverse Proxy

1. **Install Nginx**:
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx -y
   ```

2. **Configure Nginx**:
   ```bash
   sudo nano /etc/nginx/sites-available/counterparty
   ```

   Add:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:4000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Enable Site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/counterparty /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. **Setup SSL with Let's Encrypt**:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

## Step 8: Setup Monitoring and Auto-Restart

1. **Create systemd service** (alternative to docker-compose):
   ```bash
   sudo nano /etc/systemd/system/counterparty.service
   ```

   Add:
   ```ini
   [Unit]
   Description=Counterparty API
   Requires=docker.service
   After=docker.service

   [Service]
   Type=oneshot
   RemainAfterExit=yes
   WorkingDirectory=/home/ubuntu/xcp-api-mime
   ExecStart=/usr/local/bin/docker-compose up -d
   ExecStop=/usr/local/bin/docker-compose down
   TimeoutStartSec=0

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable service**:
   ```bash
   sudo systemctl enable counterparty
   sudo systemctl start counterparty
   ```

## Step 9: Backup Strategy

```bash
# Create backup script
cat > ~/backup-counterparty.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Counterparty data
docker-compose exec -T counterparty tar czf - /root/.local/share/counterparty > $BACKUP_DIR/counterparty_$DATE.tar.gz

# Keep only last 7 days
find $BACKUP_DIR -name "counterparty_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/counterparty_$DATE.tar.gz"
EOF

chmod +x ~/backup-counterparty.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * ~/backup-counterparty.sh") | crontab -
```

## Step 10: Security Hardening

1. **Setup UFW Firewall**:
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 4000/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Disable Password Authentication**:
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   sudo systemctl restart sshd
   ```

3. **Setup Fail2Ban**:
   ```bash
   sudo apt install fail2ban -y
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

## Troubleshooting

### API Not Responding
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs counterparty

# Restart services
docker-compose restart
```

### Bitcoin Connection Issues
```bash
# Test Bitcoin RPC connection
docker-compose exec counterparty curl -u rpc:password \
  --data-binary '{"jsonrpc":"1.0","id":"test","method":"getblockchaininfo","params":[]}' \
  -H 'content-type: text/plain;' \
  http://host.docker.internal:8332/
```

### Database Corruption
```bash
# Stop services
docker-compose down

# Remove corrupted database
rm -rf data/counterparty/*

# Restart and re-bootstrap
docker-compose up -d
```

## Maintenance

### Update Counterparty
```bash
cd ~/xcp-api-mime
git pull
docker-compose build
docker-compose up -d
```

### Monitor Disk Space
```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Clean up old images
docker system prune -a
```

## Cost Estimation (AWS)

- **t3.medium instance**: ~$30/month
- **100GB gp3 storage**: ~$8/month
- **Data transfer**: Variable (estimate $10-20/month)
- **Total**: ~$50-60/month

## Support

For issues related to:
- **Counterparty Core**: https://github.com/CounterpartyXCP/counterparty-core/issues
- **This PR**: https://github.com/CounterpartyXCP/counterparty-core/pull/3266
- **OGG/Opus Support**: Contact the maintainers or create an issue

## Testing OGG/Opus Inscriptions

### Example: Minting Real OGG/Opus File

```bash
# Convert your audio file to OGG/Opus (if needed)
ffmpeg -i input.mp3 -c:a libopus -b:a 128k output.opus

# Convert to hex
HEX_DATA=$(xxd -p output.opus | tr -d '\n')

# Mint inscription
curl -X POST "http://your-domain.com/v2/addresses/$WALLET_ADDRESS/compose/issuance" \
  -H "Accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "asset=MYMUSIC" \
  --data-urlencode "quantity=1" \
  --data-urlencode "divisible=false" \
  --data-urlencode "description=$HEX_DATA" \
  --data-urlencode "encoding=taproot" \
  --data-urlencode "inscription=true" \
  --data-urlencode "mime_type=audio/ogg;codecs=opus" \
  --data-urlencode "fee_rate=10"
```

The API will return an unsigned transaction. Sign and broadcast it using your Bitcoin wallet.
