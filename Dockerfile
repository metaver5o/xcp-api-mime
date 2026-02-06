# syntax=docker/dockerfile:1
#
# criptografia/xcp-api:patch
#
# Counterparty API with MIME parameter support (PR #3266)
# Runs API-only mode — connects to an external Bitcoin Core RPC endpoint.
# No local Bitcoin node required.
#
FROM --platform=linux/amd64 counterparty/counterparty:latest

# Apply the MIME type patch (PR #3266)
# Fixes validation to support MIME types with codec parameters
# e.g. audio/ogg;codecs=opus
COPY patch_mime.py /tmp/patch_mime.py
RUN python3 /tmp/patch_mime.py && rm /tmp/patch_mime.py

# Custom entrypoint that maps env vars to CLI flags
COPY entrypoint.sh /entrypoint-custom.sh
RUN chmod +x /entrypoint-custom.sh

EXPOSE 4000

ENTRYPOINT ["/entrypoint-custom.sh"]
