#!/bin/bash

# Create data directories and set permissions
mkdir -p data/bitcoin data/addrindexrs data/counterparty counterparty-core-fork
chmod -R 777 data

echo "Setup complete! Directory structure created with proper permissions."
echo "Next steps:"
echo "1. Add your counterparty-core fork code to ./counterparty-core-fork/"
echo "2. Run: docker compose up -d bitcoind"
echo "3. Wait for Bitcoin sync, then: docker compose up -d"
echo "4. Bootstrap Counterparty: docker exec -it counterparty-dev counterparty-server bootstrap"
