#!/bin/bash

set -e

docker run -d -p 8086:8086 \
  -v influxdb_jeedom_test:/var/lib/influxdb2 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=4DM1NP455W0rD1NF1UXJ33D0M \
  -e DOCKER_INFLUXDB_INIT_ORG=JEEDOM \
  -e DOCKER_INFLUXDB_INIT_BUCKET=jeedom \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=4DM1N70K3N1NF1UXJ33D0M \
  --name docker_influx \
  influxdb:2.0

# Add some delay to let influxdb start
sleep 30

# Create admin configuration in order to be able to run influx CLI commands in the container
docker exec -it docker_influx influx config create --active -n admin-config -u http://localhost:8086 -t 4DM1N70K3N1NF1UXJ33D0M -o JEEDOM

# Get bucket ID of specific bucket
BUCKET_ID=$(docker exec -i docker_influx influx bucket list --org JEEDOM | grep jeedom | awk -F" " '{print $1}')

# Create token with read right for Grafana
GRAFANA_READ_TOKEN=$(docker exec -i docker_influx influx auth create --read-bucket $BUCKET_ID --description GRAFANA_READ_TOKEN | grep GRAFANA_READ_TOKEN | awk -F" " '{print $3}')

# Create token with read/write right for the bridge
BRIDGE_READ_WRITE_TOKEN=$(docker exec -i docker_influx influx auth create --read-bucket $BUCKET_ID --write-bucket $BUCKET_ID --description BRIDGE_READ_WRITE_TOKEN  | grep BRIDGE_READ_WRITE_TOKEN | awk -F" " '{print $3}')

# Update .env file
export GRAFANA_READ_TOKEN=$GRAFANA_READ_TOKEN
export BRIDGE_READ_WRITE_TOKEN=$BRIDGE_READ_WRITE_TOKEN
envsubst < ".env_template" > ".env"

# Shutdown all containers
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)

# Pull images from docker hub and/or github
docker-compose -f ./docker-compose.yml pull 

# Start the whole stack (bridge, influx, grafana)
docker-compose -f ./docker-compose.yml up 