# Counterparty API with OGG/Opus & MIME Parameter Support

This repository is a customized version of **Counterparty Core** designed to support advanced ordinal inscriptions, specifically **OGG/Opus** audio files and MIME types with parameters (e.g., `audio/ogg;codecs=opus`).

## 🚀 Key Features

- **OGG/Opus Support**: Full support for minting and indexing `audio/opus` and `audio/ogg` assets.
- **MIME Parameter Handling**: Fixes validation to allow MIME types with codec parameters (implements [PR #3266](https://github.com/CounterpartyXCP/counterparty-core/pull/3266)).
- **External Bitcoin Node Integration**: Optimized Docker configuration to connect to a baremetal Bitcoin node (via `host.docker.internal`).
- **One-Click AWS Deployment**: Includes scripts and documentation for rapid deployment on AWS EC2.

---

## 🛠 Project Structure

- `/counterparty-core-original`: The patched Counterparty Core source code.
- `docker-compose.yml`: Ready-to-use Docker setup build from the patched source.
- `deploy-ec2.sh`: Automation script for setting up the environment on AWS.
- `AWS_DEPLOYMENT.md`: Detailed guide for cloud hosting.
- `SOLUTION_README.md`: Technical details on the Opus implementation and API usage.

---

## ⚡ Quick Start (Docker)

To start the Counterparty API connecting to a local Bitcoin node:

1. **Configure Environment**:
   Edit `docker-compose.yml` to set your Bitcoin RPC credentials:
   ```yaml
   environment:
     - BACKEND_CONNECT=host.docker.internal
     - BACKEND_USER=rpc
     - BACKEND_PASSWORD=your_password
   ```

2. **Build and Start**:
   ```bash
   docker-compose up -d --build
   ```

3. **Check Status**:
   ```bash
   docker-compose logs -f counterparty
   ```

---

## 🎵 Minting OGG/Opus Assets

You can now use complex MIME types in your issuance requests.

### Example:
```bash
WALLET_ADDRESS="bc1p..."
HEX_DATA=$(xxd -p my_song.opus | tr -d '\n')

curl -X POST "http://localhost:4000/v2/addresses/$WALLET_ADDRESS/compose/issuance" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "asset=MYOPUS" \
  --data-urlencode "quantity=1" \
  --data-urlencode "description=$HEX_DATA" \
  --data-urlencode "encoding=taproot" \
  --data-urlencode "inscription=true" \
  --data-urlencode "mime_type=audio/ogg;codecs=opus"
```

---

## ☁️ AWS Deployment

For production deployment on AWS EC2, follow the **[AWS Deployment Guide](AWS_DEPLOYMENT.md)** or run:

```bash
chmod +x deploy-ec2.sh
./deploy-ec2.sh
```

---

## 📄 License and Credits

- Based on **[Counterparty Core](https://github.com/CounterpartyXCP/counterparty-core)**.
- Implements the fix from **[PR #3266](https://github.com/CounterpartyXCP/counterparty-core/pull/3266)** by `antron3000`.
