# Counterparty API v2 with Opus Support & External Bitcoin Node

This solution provides a Dockerized Counterparty API v2 instance configured to:
1.  **Support Opus Audio**: Mint and index `audio/opus` assets (Ordinals).
2.  **Connect to External Bitcoin Node**: Communicate with a baremetal Bitcoin node running on the host machine properly.

## Prerequisites

- **Bitcoin Core Node**: You need a fully synced Bitcoin node running on your host machine (or accessible via network).
  - Must have `server=1` in `bitcoin.conf`.
  - Must allow RPC connections from the Docker container (e.g., `rpcallowip=0.0.0.0/0` or specific Docker subnet).
  - RPC username and password must be known.
- **Docker & Docker Compose**: Installed on the machine running this API.

## Configuration

The `docker-compose.yml` is pre-configured to connect to the host's Bitcoin node.

### Environment Variables
Adjust the following variables in `docker-compose.yml` if your setup differs:

- `BACKEND_CONNECT`: Hostname or IP of the Bitcoin node. Defaults to `host.docker.internal` (Docker's special DNS for host machine).
- `BACKEND_PORT`: Bitcoin RPC port (Default: `8332`).
- `BACKEND_USER`: Bitcoin RPC username.
- `BACKEND_PASSWORD`: Bitcoin RPC password.

## Deployment

1.  **Build and Start**:
    ```bash
    docker compose up -d --build
    ```

2.  **Check Logs**:
    ```bash
    docker compose logs -f counterparty
    ```
    Ensure it connects to your Bitcoin node and starts indexing/serving.

## Use Cases & Examples

### Minting an Opus Asset (Ordinal)

This API supports `audio/opus` as a valid MIME type for issuances.

#### 1. Prepare your data
Convert your `.opus` file to hex string.

```bash
# Example
HEX_DATA=$(xxd -p path/to/your/audio.opus | tr -d '\n')
```

#### 2. Execute Minting (Issuance) via cURL

Replace `YOUR_WALLET_ADDRESS` with your actual address.

```bash
WALLET_ADDRESS="bc1p..."

curl -X POST "http://localhost:4000/v2/addresses/$WALLET_ADDRESS/compose/issuance" \
  -H "Accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "asset=OPUSAUDIO" \
  --data-urlencode "quantity=1" \
  --data-urlencode "divisible=false" \
  --data-urlencode "description=$HEX_DATA" \
  --data-urlencode "encoding=taproot" \
  --data-urlencode "inscription=true" \
  --data-urlencode "mime_type=audio/opus" \
  --data-urlencode "fee_rate=1"
```

The API will return an unsigned transaction hex. You will need to sign and broadcast this transaction using your wallet software.

## Troubleshooting

- **Connection Refused**: 
  - Check if `bitcoind` is running.
  - Check `bitcoin.conf` for `rpcallowip` settings.
  - Verify firewall rules allow connection on port 8332.
- **MIME Type Errors**:
  - Ensure you rebuilt the container if you made changes (`docker compose up -d --build`).
  - The API explicitly registers `audio/opus` on startup.
