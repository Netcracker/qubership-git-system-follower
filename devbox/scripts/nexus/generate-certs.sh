#!/bin/sh
set -e

SSL_DIR="/etc/nginx/ssl"
mkdir -p $SSL_DIR

CERT="$SSL_DIR/nexus.crt"
KEY="$SSL_DIR/nexus.key"

if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
    echo "Generating self-signed SSL certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout $KEY -out $CERT \
        -subj "/C=US/ST=Local/L=Local/O=Nexus/OU=Dev/CN=nexus.localhost"
    echo "SSL certificate generated successfully!"
else
    echo "SSL certificate already exists, skipping generation."
fi
