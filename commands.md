# 🚀 Counterparty Minting Master Guide

Comprehensive commands for SKRYBIT to mint various asset types. Includes examples for local and remote nodes using environment variables.

## 🛠 Setup & Requirements
Load your secure credentials before running any commands:
```bash
export $(grep -v '^#' .env | xargs)
```

**Helper Function**: Generate unique numeric asset names (A-prefix).
```bash
ordiname(){
    echo "A17$(date +%s)$(jot -r 1 100000 999999)"
}
```

---

## 1️⃣ Numeric Asset Minting
*Free to register (No XCP fee). Perfect for bulk inscriptions.*

### Local Node
```bash
ASSET=$(ordiname)
curl -v -X POST "http://$LOCAL_NODE/v2/addresses/$WALLET/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=$ASSET" \
     --data-urlencode "quantity=1" \
     --data-urlencode "divisible=false" \
     --data-urlencode "description=Local Numeric Test" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "inscription=true" \
     --data-urlencode "fee_rate=0.6"
```

### Remote Node
```bash
ASSET=$(ordiname)
curl -v -X POST "http://$REMOTE_NODE:4000/v2/addresses/$WALLET/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=$ASSET" \
     --data-urlencode "quantity=1" \
     --data-urlencode "divisible=false" \
     --data-urlencode "description=Remote Numeric Test" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "inscription=true" \
     --data-urlencode "fee_rate=0.1"
```

---

## 2️⃣ Named Asset Minting
*Requires 0.5 XCP fee. Best for tokens, brands, and collections.*

### Local Node
```bash
ASSET="MYNAMEDTOKEN"
curl -v -X POST "http://$LOCAL_NODE/v2/addresses/$WALLET/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=$ASSET" \
     --data-urlencode "quantity=1000" \
     --data-urlencode "divisible=true" \
     --data-urlencode "description=Named Asset Local" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "fee_rate=0.6"
```

### Remote Node
```bash
ASSET="MYNAMEDTOKEN"
curl -v -X POST "http://$REMOTE_NODE:4000/v2/addresses/$WALLET/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=$ASSET" \
     --data-urlencode "quantity=1000" \
     --data-urlencode "divisible=true" \
     --data-urlencode "description=Named Asset Remote" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "fee_rate=0.1"
```

---

## 3️⃣ Media Inscriptions (Large Files)
*Requires the `--data-binary` method to handle large payloads (Opus, JPEG, etc).*

> **Note:** Use `sat_per_vbyte` (not `fee_rate`). Named assets (alphabetic) require **0.5 XCP** in the wallet. The server must have `electrs-url` configured in `server.conf` for UTXO lookups during compose.

### 🎵 Single Audio Mint — via `mint.sh` (recommended)
*Runs entirely on the server. Output saved directly to nginx-served directory.*
```bash
# From local machine — streams file to server, curl runs there
./mint.sh MYAUDIO "tomint/1. Make a YouTube Video.opus"

# With custom fee rate
./mint.sh MYAUDIO "tomint/1. Make a YouTube Video.opus" 3.0

# Output accessible at: http://$REMOTE_NODE:8080/MYAUDIO.txt
```

### 🎵 Full Collection Mint — via `mint_collection.sh`
*Loops all .opus files in `tomint/`, derives asset name from filename, saves all outputs.*
```bash
# Run on the server — mint all tracks
bash ~/mint_collection.sh

# Mint a single asset by name
bash ~/mint_collection.sh LOVEATTHEEND

# With custom fee rate
bash ~/mint_collection.sh LOVEATTHEEND 3.0

# Outputs go to /data/xcp-api-mime/output_txs/<ASSET>.txt
# Served at: http://$REMOTE_NODE:8080/<ASSET>.txt
```

### 🎵 Audio (OGG/Opus) - Manual Remote
```bash
ASSET="MYAUDIO"
FILE="tomint/1. Make a YouTube Video.opus"

rm -f /tmp/mint_audio.dat
echo -n "asset=${ASSET}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=audio%2Fogg%3Bcodecs%3Dopus&sat_per_vbyte=2.01&description=" > /tmp/mint_audio.dat
xxd -p "$FILE" | tr -d '\012' >> /tmp/mint_audio.dat

curl -s -X POST "http://$REMOTE_NODE:4000/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-binary "@/tmp/mint_audio.dat" > output_txs/${ASSET}.txt
```

### 🖼️ Image (JPEG) - Remote
```bash
ASSET="MYIMAGE"
FILE="tomint/artwork.jpg"

rm -f /tmp/mint_image.dat
echo -n "asset=${ASSET}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=image%2Fjpeg&sat_per_vbyte=2.01&description=" > /tmp/mint_image.dat
xxd -p "$FILE" | tr -d '\012' >> /tmp/mint_image.dat

curl -s -X POST "http://$REMOTE_NODE:4000/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-binary "@/tmp/mint_image.dat" > output_txs/${ASSET}.txt
```

---

## 4️⃣ Rare Sat Inscriptions
*Inscribe on a specific rare satoshi by controlling UTXO input ordering.*

The inscription binds to the **first satoshi of the first input**. To inscribe on a rare sat, you must ensure the UTXO containing it is the first input and the rare sat is at offset 0.

### Prerequisites
1. Identify the rare sat (e.g., via `ord wallet sats` or a sat hunter tool)
2. Isolate it into its own UTXO — the rare sat must be at the **beginning** (offset 0) of the UTXO
3. Note the `txid:vout` of that UTXO

### Simple Inscription on a Rare Sat
```bash
ASSET=$(ordiname)
RARE_UTXO="<txid>:<vout>"

curl -v -X POST "http://$REMOTE_NODE:4000/v2/addresses/$WALLET/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=$ASSET" \
     --data-urlencode "quantity=1" \
     --data-urlencode "divisible=false" \
     --data-urlencode "description=Rare Sat Inscription" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "inscription=true" \
     --data-urlencode "sat_per_vbyte=1" \
     --data-urlencode "inputs_set=$RARE_UTXO" \
     --data-urlencode "use_all_inputs_set=true"
```

### Rare Sat + Separate Fee UTXO
*When the rare sat UTXO is too small to cover fees, add a second UTXO for funding. The rare sat UTXO must be listed first.*
```bash
ASSET=$(ordiname)
RARE_UTXO="<rare_sat_txid>:<vout>"
FEE_UTXO="<fee_funding_txid>:<vout>"

curl -v -X POST "http://$REMOTE_NODE:4000/v2/addresses/$WALLET/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=$ASSET" \
     --data-urlencode "quantity=1" \
     --data-urlencode "divisible=false" \
     --data-urlencode "description=Rare Sat with Fee UTXO" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "inscription=true" \
     --data-urlencode "sat_per_vbyte=1" \
     --data-urlencode "inputs_set=${RARE_UTXO},${FEE_UTXO}" \
     --data-urlencode "use_all_inputs_set=true"
```

### Rare Sat + Media Inscription (Template)
*Generic template for inscribing any media onto a rare sat.*
```bash
ASSET="MYRAREAUDIO"
FILE="path/to/file.opus"
RARE_UTXO="<txid>:<vout>"
FEE_UTXO="<txid>:<vout>"

# Step 1: Build data file
rm -f /tmp/mint_rare.dat
echo -n "asset=${ASSET}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=audio%2Fogg%3Bcodecs%3Dopus&sat_per_vbyte=1.5&inputs_set=${RARE_UTXO},${FEE_UTXO}&use_all_inputs_set=true&description=" > /tmp/mint_rare.dat
xxd -p "$FILE" | tr -d '\012' >> /tmp/mint_rare.dat

# Step 2: Send binary data
curl -v -X POST "http://$REMOTE_NODE:4000/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-binary "@/tmp/mint_rare.dat" > output_txs/${ASSET}.txt
```

### 💎 Practical Example: Rare Sat + 1. Make a YouTube Video.opus
*The exact configuration for the MAKEAYOUTUBE inscription using combined UTXOs.*
```bash
ASSET="MAKEAYOUTUBE"
FILE="tomint/1. Make a YouTube Video.opus"
# Rare UTXO (1000 sats) followed by Fee Funding UTXO
INPUTS="07f016291c86b3be282e78465125a0ba4f183827571d4224033e6f952301c4dc:1,1dcc60e840de9148b268e71739490b3da4453ea7f37f359fc808b967480d3979:0"

# Step 1: Prepare data binary
rm -f /tmp/mint_rare_audio.dat
echo -n "asset=${ASSET}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=audio%2Fogg%3Bcodecs%3Dopus&sat_per_vbyte=2.01&inputs_set=${INPUTS}&use_all_inputs_set=true&description=" > /tmp/mint_rare_audio.dat

# Step 2: Append media hex
xxd -p "$FILE" | tr -d '\012' >> /tmp/mint_rare_audio.dat

# Step 3: Send to Remote Node
curl -v -X POST "http://$REMOTE_NODE:4000/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-binary "@/tmp/mint_rare_audio.dat" > output_txs/${ASSET}_RARE.txt
```

### Tips
- **Verify sat offset**: Use `ord wallet sats` or similar to confirm your rare sat is at offset 0 in the UTXO
- **Use `exact_fee`** for precise control: `exact_fee=1000` (in satoshis) prevents fee estimation from shuffling sats unexpectedly
- **Change address**: Add `change_address=<addr>` to route change away from the rare sat UTXO
- **Exclude balanced UTXOs**: Add `exclude_utxos_with_balances=true` to avoid accidentally spending UTXOs that hold other Counterparty assets

---

## 🎯 Advanced Options

### Minting to a Different Destination
Add `&destination=${DEST_WALLET}` to any of the data strings:
```bash
# Example snippet for the data file:
echo -n "asset=${ASSET}&...&destination=${DEST_WALLET}&description=" > /tmp/mint.dat
```

### Verifying Results
Check the balance of your wallet on a public node to see pending/confirmed assets:
```bash
curl -u "$API_AUTH" "https://$PODMAN_NODE/v2/addresses/$WALLET/balances"
```

---

## 🖥️ Server Setup (`/data/xcp-api-mime/`)

### Key paths
| Path | Purpose |
|---|---|
| `/data/xcp-api-mime/config/server.conf` | Counterparty server config |
| `/data/xcp-api-mime/output_txs/` | Nginx-served output directory |
| `/data/xcp-api-mime/data/counterparty/` | DB files (`counterparty.db`, `state.db`) |

### Required `server.conf` entries
```ini
[Default]
api-port = 4000
api-host = 0.0.0.0
rpc-host = 0.0.0.0
max-message-size = 50000000
electrs-url = https://mempool.space/api   # required for compose UTXO lookups
```

### Docker containers
```bash
# Check status
docker ps

# Tail logs (filter out heartbeat noise)
docker logs xcp-api --tail 50 2>&1 | grep -v 'PoolMonitor\|POOL_STATS'

# Verify nginx is serving the right directory
docker inspect xcp-outputs --format '{{json .HostConfig.Binds}}'
docker exec xcp-outputs ls /usr/share/nginx/html/
```

### Node is api-only — XCP balance caveat
The node runs with `--api-only` and does not process new blocks. If the wallet received XCP after the node's last synced block, the compose will return `insufficient funds` even though funds exist on-chain. Verify on-chain with:
```bash
curl -s "https://mempool.space/api/address/$WALLET"
```

---

*Efficiency in Counterparty Media.*
