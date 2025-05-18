#!/bin/bash

echo "Waiting for Kafka to start..."
sleep 15

echo "Creating Kafka topics..."
kafka-topics --create --if-not-exists \
  --bootstrap-server kafka:9092 \
  --topic sensor-data \
  --partitions 3 \
  --replication-factor 1

echo "Listing topics:"
kafka-topics --list --bootstrap-server kafka:9092