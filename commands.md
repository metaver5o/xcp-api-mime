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

### 🎵 Audio (OGG/Opus) - Remote
```bash
ASSET="MYAUDIO"
FILE="tomint/1. Make a YouTube Video.opus"

# Step 1: Prepare data with URL-encoded MIME type (audio/ogg;codecs=opus)
rm -f /tmp/mint_audio.dat
echo -n "asset=${ASSET}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=audio%2Fogg%3Bcodecs%3Dopus&fee_rate=0.1&description=" > /tmp/mint_audio.dat
xxd -p "$FILE" | tr -d '\012' >> /tmp/mint_audio.dat

# Step 2: Send binary data
curl -v -X POST "http://$REMOTE_NODE:4000/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-binary "@/tmp/mint_audio.dat" > output_txs/${ASSET}.txt
```

### 🖼️ Image (JPEG) - Remote
```bash
ASSET="MYIMAGE"
FILE="tomint/artwork.jpg"

# Step 1: Prepare data with standard MIME type
rm -f /tmp/mint_image.dat
echo -n "asset=${ASSET}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=image%2Fjpeg&fee_rate=0.1&description=" > /tmp/mint_image.dat
xxd -p "$FILE" | tr -d '\012' >> /tmp/mint_image.dat

# Step 2: Send binary data
curl -v -X POST "http://$REMOTE_NODE:4000/v2/addresses/${WALLET}/compose/issuance" \
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

### Rare Sat + Media Inscription (OGG/Opus)
*Inscribe audio onto a rare sat using the `--data-binary` method.*
```bash
ASSET="MYRAREAUDIO"
FILE="tomint/track.opus"
RARE_UTXO="<rare_sat_txid>:<vout>"
FEE_UTXO="<fee_funding_txid>:<vout>"

# Step 1: Build data file with rare sat UTXO as first input
rm -f /tmp/mint_rare.dat
echo -n "asset=${ASSET}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=audio%2Fogg%3Bcodecs%3Dopus&sat_per_vbyte=1&inputs_set=${RARE_UTXO},${FEE_UTXO}&use_all_inputs_set=true&description=" > /tmp/mint_rare.dat
xxd -p "$FILE" | tr -d '\012' >> /tmp/mint_rare.dat

# Step 2: Send to API
curl -v -X POST "http://$REMOTE_NODE:4000/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-binary "@/tmp/mint_rare.dat" > output_txs/${ASSET}.txt
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

*Efficiency in Counterparty Media.*
