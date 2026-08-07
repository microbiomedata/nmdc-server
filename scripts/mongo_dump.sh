#!/usr/bin/env bash
# Dump ingest-relevant collections from MongoDB via the local SSH tunnel.
#
# Usage:
#   ./scripts/mongo_dump.sh <user> <password> [port] [backup_dir]
#
# Arguments:
#   user        MongoDB username      (required)
#   password    MongoDB password      (required)
#   port        MongoDB port          (default: 27124 — prod tunnel)
#   backup_dir  Destination directory (default: ../backup/nmdc)
#
# Examples:
#   ./scripts/mongo_dump.sh cody.odonnell '<pass>'               # prod (port 27124)
#   ./scripts/mongo_dump.sh cody.odonnell '<pass>' 37018         # dev  (port 37018)

set -euo pipefail

USER="${1:?Usage: $0 <user> <password> [port] [backup_dir]}"
PASSWORD="${2:?Usage: $0 <user> <password> [port] [backup_dir]}"
PORT="${3:-27124}"
# Ensure the backup directory is based on the script's location, not the current working directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${4:-$SCRIPT_DIR/../data/mongo}"

HOST="localhost"
DATABASE="nmdc"
AUTH_DB="admin"

collections=(
    "biosample_set"
    "configuration_set"
    "data_object_set"
    "field_research_site_set"
    "instrument_set"
    "material_sample_set"
    "processed_sample_set"
    "study_set"
    "planned_process_set"
    "collecting_biosamples_from_site_set"
    "data_generation_set"
    "material_processing_set"
    "protocol_execution_set"
    "storage_process_set"
    "workflow_execution_set"
    "manifest_set"
    # Largest collection — only needed to test gene function annotation ingest/search.
    # Uncomment to include:
    # "functional_annotation_agg"
)

mkdir -p "$BACKUP_DIR"

echo "Dumping from $HOST:$PORT (database: $DATABASE) into $BACKUP_DIR"

for collection in "${collections[@]}"; do
    echo "  -> $collection"
    mongodump \
        --host "$HOST" \
        --port "$PORT" \
        --username "$USER" \
        --password "$PASSWORD" \
        --authenticationDatabase "$AUTH_DB" \
        --db "$DATABASE" \
        --collection "$collection" \
        --out "$BACKUP_DIR"
done

echo "Dump complete: $BACKUP_DIR"
