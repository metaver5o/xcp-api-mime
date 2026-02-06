# Ansible Deployment for Patched Counterparty

This folder contains an Ansible playbook to deploy a patched version of Counterparty Core (with OGG/Opus support) on a remote server using the **official image** as a base.

## 📁 Structure
- `deploy.yml`: The main playbook.
- `inventory.ini`: Server connection details.
- `templates/docker-compose.yml.j2`: Template for the service configuration.

## 🚀 How to Use

### A. Remote Deployment
1. **Update Inventory**:
   Edit `inventory.ini` and add your server's IP and user:
   ```ini
   [counterparty_nodes]
   your_server_ip ansible_user=ubuntu
   ```

2. **Run Playbook**:
   Execute the deployment:
   ```bash
   ansible-playbook -i inventory.ini deploy.yml
   ```

### B. Local Testing (localhost)
You can test the automation locally on your machine without a remote server.

1. **Install Requirements**:
   ```bash
   ansible-galaxy collection install community.docker
   pip install docker
   ```

2. **Run Playbook (Local)**:
   This will deploy the stack to `./xcp-auto-deployed` (safe to run):
   ```bash
   ansible-playbook -i inventory.ini deploy.yml \
     --connection=local \
     --extra-vars "hosts=localhost app_dir=$(pwd)/../xcp-auto-deployed bitcoin_rpc_connect=bitcoin-rpc.publicnode.com bitcoin_rpc_user=rpc bitcoin_rpc_password=ignore"
   ```

## 🛠 What this does
1. Creates a directory (default `/opt/counterparty-patched`) on the target.
2. Copies our local `patch_mime.py` script.
3. Creates a small `Dockerfile` that:
   - Starts `FROM` the official `counterparty/counterparty:latest`.
   - Runs `python3 patch_mime.py` to modify `helpers.py` in-place.
4. Starts the service using `docker-compose` with:
   - `ENABLE_ALL_PROTOCOL_CHANGES=1` (fixes height 0 logic).
   - `BACKEND_SSL=1` (secure public RPC).

## ⚙️ Configuration
You can modify variables at the top of `deploy.yml`:
- `bitcoin_rpc_connect`: Hostname/IP of the Bitcoin node.
- `bitcoin_rpc_user`: RPC Username.
- `bitcoin_rpc_password`: RPC Password.
