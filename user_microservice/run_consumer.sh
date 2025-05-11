#!/bin/bash
# Script to start the Kafka consumer for processing like/unlike events

# Load environment variables if .env exists
if [ -f ../.env ]; then
  source ../.env
fi

# Navigate into the microservice directory
cd $(dirname "$0")

# Ensure Python dependencies are installed
pip install --no-cache-dir -r requirements.txt

# Run the consumer
python3 consume_likes.py
