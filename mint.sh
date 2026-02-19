#!/bin/bash

# Usage: ./mint.sh <ASSET> <"path/to/file.opus"> [sat_per_vbyte]
# Runs on the remote server, saves to /data/xcp-api-mime/output_txs/${ASSET}.txt

ASSET="$1"
FILE="$2"
SAT_PER_VBYTE="${3:-2.01}"
WALLET="bc1pnum2kywslj3d2gcnmsuhqvm0qecqu7erl7tp6h5pj2fwcflgsnnq7p3tcs"
REMOTE="ec2-18-191-178-208.us-east-2.compute.amazonaws.com"
OUTPUT_DIR="/data/xcp-api-mime/output_txs"

if [[ -z "$ASSET" || -z "$FILE" ]]; then
    echo "Usage: $0 <ASSET> <file.opus> [sat_per_vbyte]"
    exit 1
fi

echo "Asset      : $ASSET"
echo "File       : $FILE ($(du -h "$FILE" | cut -f1))"
echo "Fee        : $SAT_PER_VBYTE sat/vbyte"
echo "Output     : $OUTPUT_DIR/${ASSET}.txt"
echo "---"

# Stream file as hex to the server and run curl there
(
    echo -n "asset=${ASSET}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=audio%2Fogg%3Bcodecs%3Dopus&sat_per_vbyte=${SAT_PER_VBYTE}&description="
    xxd -p "$FILE" | tr -d '\n'
) | ssh ec2-user@${REMOTE} "
    cat > /tmp/mint_${ASSET}.dat
    curl -s -X POST 'http://localhost:4000/v2/addresses/${WALLET}/compose/issuance' \
         -H 'Content-Type: application/x-www-form-urlencoded' \
         --data-binary @/tmp/mint_${ASSET}.dat \
         -o '${OUTPUT_DIR}/${ASSET}.txt'
    rm -f /tmp/mint_${ASSET}.dat
    echo 'Saved to ${OUTPUT_DIR}/${ASSET}.txt'
    ls -lh '${OUTPUT_DIR}/${ASSET}.txt'
"
