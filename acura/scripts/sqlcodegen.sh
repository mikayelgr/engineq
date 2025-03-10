#!/bin/bash
# Load environment variables from .env file
if [ -f .env ]; then
    set -a;
    source .env;
    set +a;
fi

# Generate models.py using sqlacodegen
sqlacodegen "$POSTGRES_URL" > models.py;
