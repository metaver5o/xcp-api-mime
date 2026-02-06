#!/bin/bash

# Configuration
WALLET="bc1p865lxyp372lg0nhkze7kkd6u38vpaglrv5cdfjs3r83nk7jaqalqxzxhq8"
API_URL="http://localhost:4000/v2"
SPK="51203ea9f31031f2be87cef6167d6b375c89d81ea3e36530d4ca1119e33b7a5d077e"
INPUTS="feecf20b488f4163aff604972594e44991f5c6a5bda9b49b9ad5f798a2330401:1:278199:${SPK},7cbb0d8abf8be155e272fff5cb2ffc2f108a0ca1be8e0214d88651e428fe9ee6:1:17550:${SPK}"

mkdir -p output_txs

echo "Minting collection from tomint_48k/ directory..."
echo "Wallet: $WALLET"
echo "---------------------------------------------------"

for num in $(ls tomint_48k | grep -o '^[0-9]\+' | sort -nu); do
    filepath=$(ls tomint_48k/$num.*.opus 2>/dev/null)

    if [[ -z "$filepath" ]]; then
        echo "Warning: Could not find file for number $num"
        continue
    fi

    filename=$(basename "$filepath")

    # Generate numeric asset name (free, no XCP fee)
    ASSET_NUM="A96$(date +%s)$(jot -r 1 100000 999999)"

    # Readable label for output file
    base_name=$(echo "$filename" | sed -E 's/^[0-9]+\. //' | sed 's/\.opus$//')
    label=$(echo "$base_name" | tr '[:lower:]' '[:upper:]' | tr -dc 'A-Z' | cut -c 1-12)

    echo "Processing: $filename"
    echo "  -> Asset: $ASSET_NUM (label: $label)"
    echo "  -> Size: $(ls -lh "$filepath" | awk '{print $5}')"

    data_file="temp_mint_${label}.dat"

    echo -n "asset=${ASSET_NUM}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=audio%2Fogg%3Bcodecs%3Dopus&fee_rate=0.001&inputs_set=${INPUTS}&description=" > "$data_file"

    xxd -p "$filepath" | tr -d '\n' >> "$data_file"

    echo "  -> Requesting mint transaction..."

    response=$(curl -s -X POST "$API_URL/addresses/${WALLET}/compose/issuance" \
         -H "Content-Type: application/x-www-form-urlencoded" \
         --data-binary "@$data_file")

    rm "$data_file"

    outfile="output_txs/${label}.txt"
    echo "$response" > "$outfile"
    echo "  -> Saved response to $outfile"
    echo "---------------------------------------------------"

    sleep 1
done
