#!/bin/bash
# Load environment variables from .env file
if [ -f .env ]; then
    set -a;
    source .env;
    set +a;
fi

eval $(poetry env activate);

# Use Python to check and modify POSTGRES_URL if it starts with "postgres+asyncpg://",
# because the runtime uses asyncpg and the migration script uses sync drivers.
POSTGRES_URL=$(python3 -c "
import os
url = os.getenv('POSTGRES_URL')
if url is None:
    raise ValueError('POSTGRES_URL is not set. Code generation script cannot run')

url = url.split('://')
url[0] = 'postgresql'
url = '://'.join(url)
print(url) # we must print, not return, because we are using python3 -c
")

# Generate models.py using sqlacodegen
sqlacodegen "$POSTGRES_URL" > ./internal/models/codegen/models.py;
