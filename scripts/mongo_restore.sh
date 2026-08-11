#!/usr/bin/env bash
# Restore a mongodump backup into the local Docker MongoDB instance (mongo_db container).
# The local MongoDB must be running before executing this script.
#
# Usage:
#   ./scripts/mongo_restore.sh [backup_dir]
#
#   backup_dir  Path to mongodump output (default: data/mongo)
#
# To start the local MongoDB first:
#   docker compose -f docker-compose.yml -f docker-compose.local.yml up -d mongodb_container

set -euo pipefail

HOST="localhost"
PORT="27017"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${1:-$SCRIPT_DIR/../data/mongo}"

if ! docker inspect mongo_db &>/dev/null; then
    echo "Error: mongo_db container is not running."
    echo "Start it with: docker compose -f docker-compose.yml -f docker-compose.local.yml up -d mongodb_container"
    exit 1
fi

echo "Restoring from $BACKUP_DIR into $HOST:$PORT ..."

mongorestore \
    --host "$HOST" \
    --port "$PORT" \
    --username "root" \
    --password "rootpassword" \
    --authenticationDatabase "admin" \
    --drop \
    "$BACKUP_DIR"

echo "Restore complete."
echo
echo "Update your .env with:"
echo '  NMDC_MONGO_HOST="mongo_db"'
echo '  NMDC_MONGO_PORT=27017'
echo '  NMDC_MONGO_DATABASE="nmdc"'
echo '  NMDC_MONGO_USER="root"'
echo '  NMDC_MONGO_PASSWORD="rootpassword"'
