#!/bin/bash

# Configuration
WALLET="bc1pnum2kywslj3d2gcnmsuhqvm0qecqu7erl7tp6h5pj2fwcflgsnnq7p3tcs"
API_URL="http://localhost:4000/v2"
OUTPUT_DIR="/Users/marco/code/UCASH/xcp-api-mime/output_txs"

TARGET_LABEL=$1
CURRENT_WALLET="${2:-$WALLET}"
TARGET_FEE_RATE="${3:-2.01}"

mkdir -p "$OUTPUT_DIR"

echo "Minting collection from tomint/ directory..."
echo "Wallet: $CURRENT_WALLET"
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

    # Set specific asset names based on track number
    case "$num" in
        1) label="MAKEAYOUTUBE" ;;
        2) label="LOVEENDWORLD" ;;
        3) label="SAFEWITHYOU" ;;
        4) label="SAMESIDE" ;;
        5) label="ENDOFTHEDAY" ;;
        6) label="CALLYOUOUT" ;;
        7) label="COMEAROUND" ;;
        8) label="KEEPTHEFAITH" ;;
        9) label="OUTINTHEWIND" ;;
        10) label="SILKROADSONG" ;;
        11) label="BTCJINGLE" ;;
        *) 
            base_name=$(echo "$filename" | sed -E 's/^[0-9]+\. //' | sed 's/\.opus$//')
            label=$(echo "$base_name" | tr '[:lower:]' '[:upper:]' | tr -dc 'A-Z' | cut -c 1-12)
            ;;
    esac

    # FILTER: If an argument is provided, skip if label doesn't match
    if [[ -n "$TARGET_LABEL" && "$TARGET_LABEL" != "$label" ]]; then
        continue
    fi

    echo "Processing: $filename"
    echo "  -> Asset: $label (named asset, costs 0.5 XCP)"
    echo "  -> Size: $(ls -lh "$filepath" | awk '{print $5}')"

    data_file="temp_mint_${label}.dat"

    echo "  -> Using Wallet: $CURRENT_WALLET"
    echo "  -> Fee Rate: $TARGET_FEE_RATE sat/vbyte"

    echo -n "asset=${label}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=audio%2Fogg%3Bcodecs%3Dopus&sat_per_vbyte=${TARGET_FEE_RATE}&description=" > "$data_file"

    xxd -p "$filepath" | tr -d '\n' >> "$data_file"

    echo "  -> Requesting mint transaction..."

    response=$(curl -s -X POST "$API_URL/addresses/${CURRENT_WALLET}/compose/issuance" \
         -H "Content-Type: application/x-www-form-urlencoded" \
         --data-binary "@$data_file")

    rm "$data_file"

    outfile="${OUTPUT_DIR}/${label}.txt"
    echo "$response" > "$outfile"
    
    # Check for "insufficient funds" which implies a lack of BTC for fees or XCP for registration
    if echo "$response" | grep -q "insufficient funds"; then
         echo "  [FAIL] Insufficient Funds! (BTC for fees or 0.5 XCP for named asset registration)"
         echo "         Check balance: curl -s http://localhost:4000/v2/addresses/${CURRENT_WALLET}/balances"
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
