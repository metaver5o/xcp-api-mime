# Counterparty API with OGG/Opus & MIME Parameter Support

This repository provides a deployment and patching solution for **Counterparty Core** to support advanced ordinal inscriptions, specifically **OGG/Opus** audio files and MIME types with parameters (e.g., `audio/ogg;codecs=opus`).

Instead of forking the entire codebase, this repo uses the **official Counterparty Docker image** and applies a critical patch at runtime.

## 🚀 Key Features

- **OGG/Opus Support**: Validates and indexes `audio/opus` and `audio/ogg` assets.
- **MIME Parameter Fix**: Runtime IPatch for [PR #3266](https://github.com/CounterpartyXCP/counterparty-core/pull/3266) to allow MIME parameters (e.g. `codecs=opus`).
- **External Bitcoin RPC**: Configured to connect easily to public or private Bitcoin nodes (like PublicNode).
- **Automated Deployment**: Includes **Ansible** playbooks for one-click deployment to remote servers.

---

## 🛠 Project Structure

- `patch_mime.py`: The Python script that inserts the MIME logic into the running container.
- `Dockerfile`: A wrapper that layers our patch on top of the official image.
- `docker-compose.yml`: Local development environment configuration.
- `ansible/`: Playbooks to deploy this exact patched setup to production servers.

---

## ⚡ Quick Start (Local)

To run the patched API locally on your machine:

1. **Configure Environment**:
   Copy the example and set your RPC details (default uses PublicNode):
   ```bash
   cp .env.example .env
   ```

2. **Build and Start**:
   This builds the custom image with the patch applied:
   ```bash
   docker compose up -d --build
   ```

3. **Check Status**:
   Wait for the node to sync (height > 0):
   ```bash
   curl -s http://localhost:4000/v2/ | grep height
   ```

---

## 🎵 Minting OGG/Opus Assets

You can now use complex MIME types in your issuance requests.

### Helper Function
Add this to your terminal session to generate unique, valid numeric IDs (> 9.54e16):
```bash
ordiname(){
    echo "A17$(date +%s)$(jot -r 1 100000 999999)"
}
```

### Example Command (Local Node)
```bash
WALLET="bc1p..."
ASSET_NUM=$(ordiname)
HEX_DATA=$(xxd -p my_song.opus | tr -d '\n')

curl -v -X POST "http://localhost:4000/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=${ASSET_NUM}" \
     --data-urlencode "quantity=1" \
     --data-urlencode "divisible=false" \
     --data-urlencode "description=${HEX_DATA}" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "inscription=true" \
     --data-urlencode "mime_type=audio/ogg;codecs=opus" \
     --data-urlencode "fee_rate=0.6"
```

---

## ☁️ Production Deployment (Ansible)

To deploy to a remote server (e.g., AWS, DigitalOcean):

1. Edit **`ansible/inventory.ini`** with your server IP.
2. Run the playbook:
   ```bash
    ansible-playbook -i ansible/inventory.ini ansible/deploy.yml
   ```

See [ansible/README.md](ansible/README.md) for full details.

---

## 📄 Credits

- **Counterparty Core**: The official upstream project.
- **Patch Logic**: Based on [PR #3266](https://github.com/CounterpartyXCP/counterparty-core/pull/3266).
- **Setup**: Created for the **UCASH Ecosystem**.
