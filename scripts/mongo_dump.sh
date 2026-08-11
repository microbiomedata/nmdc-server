#!/usr/bin/env bash
# Dump ingest-relevant collections from MongoDB via the local SSH tunnel.
#
# Usage:
#   ./scripts/mongo_dump.sh [port] [backup_dir]
#
# Arguments:
#   port        MongoDB port          (default: 27124 — prod tunnel)
#   backup_dir  Destination directory (default: ../backup/nmdc)
#
# Credentials are read from NMDC_MONGO_USER and NMDC_MONGO_PASSWORD in the
# repository's .env file. Set ENV_FILE to use a different environment file.
#
# Examples:
#   ./scripts/mongo_dump.sh         # prod (port 27124)
#   ./scripts/mongo_dump.sh 37018   # dev  (port 37018)

set -euo pipefail

# Ensure the backup directory is based on the script's location, not the current working directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
ENV_FILE="${ENV_FILE:-$REPO_ROOT/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: environment file not found: $ENV_FILE" >&2
    exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${NMDC_MONGO_USER:?NMDC_MONGO_USER must be set in $ENV_FILE}"
: "${NMDC_MONGO_PASSWORD:?NMDC_MONGO_PASSWORD must be set in $ENV_FILE}"

PORT="${1:-27124}"
BACKUP_DIR="${2:-$REPO_ROOT/data/mongo}"

HOST="localhost"
DATABASE="nmdc"
AUTH_DB="admin"

collections=(
    "biosample_set"
    "collecting_biosamples_from_site_set"
    "configuration_set"
    "data_generation_set"
    "data_object_set"
    "field_research_site_set"
    "instrument_set"
    "manifest_set"
    "material_processing_set"
    "material_sample_set"
    "planned_process_set"
    "processed_sample_set"
    "protocol_execution_set"
    "storage_process_set"
    "study_set"
    "workflow_execution_set"
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
        --username "$NMDC_MONGO_USER" \
        --password "$NMDC_MONGO_PASSWORD" \
        --authenticationDatabase "$AUTH_DB" \
        --db "$DATABASE" \
        --collection "$collection" \
        --out "$BACKUP_DIR"
done

echo "Dump complete: $BACKUP_DIR"
