# Mint Output Transactions

Signed raw transactions for the "Keep The Faith" album by Tatiana Moroz, minted as Counterparty assets with embedded OGG/Opus audio inscriptions on Bitcoin.

## Mint Parameters

- **Source (minting) wallet:** `bc1p865lxyp372lg0nhkze7kkd6u38vpaglrv5cdfjs3r83nk7jaqalqxzxhq8`
- **Destination wallet:** `bc1px2erw8wqqck92q3tjrq5sj2mhvh7jsdnwerydc0h59mcrwz2vs9squ67wj`
- **API endpoint:** `http://localhost:4000/v2/addresses/{WALLET}/compose/issuance`
- **Asset type:** Numeric (free, no XCP fee)
- **Quantity:** 1 (indivisible)
- **Encoding:** Taproot inscription
- **MIME type:** `audio/ogg;codecs=opus`
- **Fee rate:** 0.001 sat/vbyte
- **Source files:** `tomint_48k/` (48k OGG/Opus)

## Asset Mapping

| # | Track | Asset ID | Output File |
|---|-------|----------|-------------|
| 1 | Make a YouTube Video | A961770419733853910 | MAKEAYOUTUBE.txt |
| 2 | Love At The End Of The World | A961770419794445390 | LOVEATTHEEND.txt |
| 3 | Safe With You | A961770419827558573 | SAFEWITHYOU.txt |
| 4 | Same Side | A961770419853905880 | SAMESIDE.txt |
| 5 | End of the Day | A961770419880426539 | ENDOFTHEDAY.txt |
| 6 | Call You Out | A961770419909601452 | CALLYOUOUT.txt |
| 7 | He'll Come Around | A961770419929609919 | HELLCOMEAROU.txt |
| 8 | Keep the Faith | A961770419949896916 | KEEPTHEFAITH.txt |
| 9 | Out In The Wind | A961770419986796718 | OUTINTHEWIND.txt |
| 10 | Silk Road | A961770419756265693 | SILKROAD.txt |
| 11 | Bitcoin Jingle | A961770419778379994 | BITCOINJINGL.txt |

## Mint Command Used

For each track, a data file was built and POSTed via curl:

```bash
# Step 1: Set variables
WALLET="bc1p865lxyp372lg0nhkze7kkd6u38vpaglrv5cdfjs3r83nk7jaqalqxzxhq8"
DEST="bc1px2erw8wqqck92q3tjrq5sj2mhvh7jsdnwerydc0h59mcrwz2vs9squ67wj"
ASSET_NUM="A96$(date +%s)$(jot -r 1 100000 999999)"

# Step 2: Build the data file (hex-encoded audio as description)
echo -n "asset=${ASSET_NUM}&quantity=1&divisible=false&encoding=taproot&inscription=true&mime_type=audio%2Fogg%3Bcodecs%3Dopus&fee_rate=0.001&destination=${DEST}&description=" > mint_data.dat

xxd -p "tomint_48k/<TRACK_FILE>.opus" | tr -d '\012' >> mint_data.dat

# Step 3: POST to Counterparty API
curl -s -X POST "http://localhost:4000/v2/addresses/${WALLET}/compose/issuance" -H "Content-Type: application/x-www-form-urlencoded" --data-binary "@mint_data.dat" > output_txs/<LABEL>.txt
```

Each `.txt` file contains the JSON response with `signed_reveal_rawtransaction` and `rawtransaction` fields ready for broadcast.

