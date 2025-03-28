#!/bin/bash

host=$1
username=$2
password=$3

curl -X POST "$host/service/rest/v1/repositories/docker/hosted" \
     -u "$username:$password" -H "Content-Type: application/json" \
     -d '{
          "name": "anon-docker-registry",
          "online": true,
          "storage": {
            "blobStoreName": "default",
            "strictContentTypeValidation": true,
            "writePolicy": "allow_once",
            "latestPolicy": true
          },
          "cleanup": {
            "policyNames": [
              "string"
            ]
          },
          "component": {
            "proprietaryComponents": true
          },
          "docker": {
            "v1Enabled": false,
            "forceBasicAuth": false,
            "httpPort": 17001,
            "httpsPort": 17002,
            "subdomain": "docker-a"
          }
        }'
echo 'Created anon-docker-registry in 17001/17002 for http/https'

curl -X POST "$host/service/rest/v1/repositories/docker/hosted" \
     -u "$username:$password" -H "Content-Type: application/json" \
     -d '{
          "name": "non-anon-docker-registry",
          "online": true,
          "storage": {
            "blobStoreName": "default",
            "strictContentTypeValidation": true,
            "writePolicy": "allow_once",
            "latestPolicy": true
          },
          "cleanup": {
            "policyNames": [
              "string"
            ]
          },
          "component": {
            "proprietaryComponents": true
          },
          "docker": {
            "v1Enabled": false,
            "forceBasicAuth": true,
            "httpPort": 17003,
            "httpsPort": 17004,
            "subdomain": "docker-a"
          }
        }'
echo 'Created non-anon-docker-registry in 17003/17004 for http/https'

curl -X PUT "$host/service/rest/v1/security/realms/active" \
     -u "$username:$password" -H "Content-Type: application/json" \
     -d '["NexusAuthenticatingRealm", "DockerToken"]'
echo "Activated DockerToken Realm"


curl -X PUT "$host/service/rest/v1/security/anonymous" \
     -u "$username:$password" -H "Content-Type: application/json" \
     -d '{"enabled": true, "userId": "anonymous", "realmName": "NexusAuthorizingRealm"}' \
     -s > /dev/null
echo "Allowed anonymous users to access the server"