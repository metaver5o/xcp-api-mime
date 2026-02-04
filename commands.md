# Counterparty Production Commands (Podman Server)

Standard commands for the SKRYBIT/UCASH server.

**Server**: `https://podman-03.ferret-elver.ts.net/v2/`
**Auth**: `skrybit-party:PkqSsVP9z8YO4U`
**Test Wallet**: `bc1p865lxyp372lg0nhkze7kkd6u38vpaglrv5cdfjs3r83nk7jaqalqxzxhq8`

---

## 🛠 Helper Function
Add this to your `~/.zshrc` or `~/.functions` to generate unique, valid-length numeric IDs:

```bash
ordiname(){
    echo "A17$(date +%s)$(jot -r 1 100000 999999)"
}
```

---

## 1. Named Asset (Requires 0.5 XCP)
*Note: Make sure the name is unique and not taken.*
```bash
WALLET="bc1p865lxyp372lg0nhkze7kkd6u38vpaglrv5cdfjs3r83nk7jaqalqxzxhq8"

ordiname(){
    echo "A17$(date +%s)$(jot -r 1 100000 999999)"
}

ASSET_NAME=$(ordiname)

curl -u "skrybit-party:PkqSsVP9z8YO4U" \
     -X POST "https://podman-03.ferret-elver.ts.net/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=${ASSET_NAME}" \
     --data-urlencode "quantity=1" \
     --data-urlencode "divisible=false" \
     --data-urlencode "description=SKRYBIT Named Asset" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "inscription=true" \
     --data-urlencode "fee_rate=1"
```

## 2. Numeric Asset (FREE)
Uses the `ordiname` function for a guaranteed valid ID.
```bash
WALLET="bc1p865lxyp372lg0nhkze7kkd6u38vpaglrv5cdfjs3r83nk7jaqalqxzxhq8"
ASSET_NUM=$(ordiname)

curl -u "skrybit-party:PkqSsVP9z8YO4U" \
     -X POST "https://podman-03.ferret-elver.ts.net/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=${ASSET_NUM}" \
     --data-urlencode "quantity=1" \
     --data-urlencode "divisible=false" \
     --data-urlencode "description=Free Numeric Inscription" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "inscription=true" \
     --data-urlencode "fee_rate=1"
```

## 3. Image Inscription (Verified)
This command successfully produced a signed Taproot reveal transaction.
```bash
WALLET="bc1p865lxyp372lg0nhkze7kkd6u38vpaglrv5cdfjs3r83nk7jaqalqxzxhq8"
ASSET_NUM=$(ordiname)
# Ensure the image is resized to < 8KB for best results
HEX_DATA=$(xxd -p "path/to/image.jpg" | tr -d '\n')

curl -u "skrybit-party:PkqSsVP9z8YO4U" \
     -X POST "https://podman-03.ferret-elver.ts.net/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=${ASSET_NUM}" \
     --data-urlencode "quantity=1" \
     --data-urlencode "divisible=false" \
     --data-urlencode "description=${HEX_DATA}" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "inscription=true" \
     --data-urlencode "mime_type=image/jpeg" \
     --data-urlencode "fee_rate=1"
```

## 4. Audio Inscription
When the OGG/Opus patch is active, use this:
```bash
WALLET="bc1p865lxyp372lg0nhkze7kkd6u38vpaglrv5cdfjs3r83nk7jaqalqxzxhq8"
ASSET_NUM=$(ordiname)
HEX_DATA=$(xxd -p "tomint/comingsoon.opus" | tr -d '\n')

curl -u "skrybit-party:PkqSsVP9z8YO4U" \
     -X POST "https://podman-03.ferret-elver.ts.net/v2/addresses/${WALLET}/compose/issuance" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "asset=${ASSET_NUM}" \
     --data-urlencode "quantity=1" \
     --data-urlencode "divisible=false" \
     --data-urlencode "description=${HEX_DATA}" \
     --data-urlencode "encoding=taproot" \
     --data-urlencode "inscription=true" \
     --data-urlencode "mime_type=audio/ogg;codecs=opus" \
     --data-urlencode "fee_rate=1"
```