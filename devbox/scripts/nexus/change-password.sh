#!/bin/bash

TIMEOUT=60
INTERVAL=5

host=$1
current_password=$2
username=$3
password=$4

for ((i=0; i<TIMEOUT; i+=INTERVAL)); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$host/service/rest/v1/status")
    if [[ "$STATUS" == "200" ]]; then
        curl -X PUT "$host/service/rest/v1/security/users/$username/change-password" \
             -u "$username:$current_password" -H "Content-Type: text/plain" -d "$password"
        echo "Changed $username password to '$password'"
        exit 0
    fi
    sleep $INTERVAL
done

echo "Timeout! Nexus REST API did not respond with 200"
exit 1