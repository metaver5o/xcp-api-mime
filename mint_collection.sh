#!/bin/bash

# Configuration
WALLET="bc1ptvkj9s2dap4u2fk88xu29y90knv6tgndc26t89jytnufkjuqkd4s5tj2zz"
API_URL="http://localhost:4000/v2"
OUTPUT_DIR="/data/xcp-api-mime/output_txs"

mkdir -p "$OUTPUT_DIR"

echo "Minting collection from tomint/ directory..."
echo "Wallet: $WALLET"
echo "---------------------------------------------------"

for num in $(ls tomint | grep -o '^[0-9]\+' | sort -nu); do
    filepath=$(ls tomint/$num.*.opus 2>/dev/null)

    if [[ -z "$filepath" ]]; then
        echo "Warning: Could not find file for number $num"
        continue
    fi

    filename=$(basename "$filepath")

    # Generate numeric asset name (free, no XCP fee)
    # Replaced 'jot' with bash RANDOM for portability
    ASSET_NUM="A96$(date +%s)$((RANDOM % 900000 + 100000))"

    # Readable label for output file
    base_name=$(echo "$filename" | sed -E 's/^[0-9]+\. //' | sed 's/\.opus$//')
    label=$(echo "$base_name" | tr '[:lower:]' '[:upper:]' | tr -dc 'A-Z' | cut -c 1-12)

    # FILTER: If an argument is provided, skip if label doesn't match
    if [[ -n "$1" && "$1" != "$label" ]]; then
        continue
    fi

    echo "Processing: $filename"
    echo "  -> Asset: $label (named asset, costs 0.5 XCP)"
    echo "  -> Size: $(ls -lh "$filepath" | awk '{print $5}')"

    data_file="temp_mint_${label}.dat"
    
    # Fee Rate: Use $2 argument if provided, else default to 2.01
    SAT_PER_VBYTE=${2:-2.01}

    echo "  -> Fee Rate: $SAT_PER_VBYTE sat/vbyte"

    echo -n "asset=${label}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=audio%2Fogg%3Bcodecs%3Dopus&sat_per_vbyte=${SAT_PER_VBYTE}&description=" > "$data_file"

    xxd -p "$filepath" | tr -d '\n' >> "$data_file"

    echo "  -> Requesting mint transaction..."

    response=$(curl -s -X POST "$API_URL/addresses/${WALLET}/compose/issuance" \
         -H "Content-Type: application/x-www-form-urlencoded" \
         --data-binary "@$data_file")

    rm "$data_file"

    outfile="${OUTPUT_DIR}/${label}.txt"
    echo "$response" > "$outfile"
    
    # Check for "insufficient funds" which implies a successful payload parse but lack of funds
    if echo "$response" | grep -q "insufficient funds"; then
         echo "  [OK] Server accepted payload! (Error: Insufficient Funds, expected on unsynced node)"
    elif echo "$response" | grep -q "Internal server error"; then
         echo "  [FAIL] Internal Server Error (possibly 413 or logic crash)"
    elif echo "$response" | grep -q "Bad Request"; then
         echo "  [FAIL] Bad Request (check syntax)"
    else
         echo "  -> Saved response to $outfile"
    fi
    echo "---------------------------------------------------"

    sleep 1
done
