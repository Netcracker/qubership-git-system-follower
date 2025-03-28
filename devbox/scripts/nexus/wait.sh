#!/bin/bash

TIMEOUT=60
INTERVAL=5

for ((i=0; i<TIMEOUT; i+=INTERVAL)); do
    PASSWORD=$(docker exec nexus cat /nexus-data/admin.password 2>/dev/null)
    if [[ -n "$PASSWORD" ]]; then
        echo "$PASSWORD"
        exit 0
    fi
    sleep $INTERVAL
done

echo "Timeout! Password file not found"
exit 1