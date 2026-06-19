#!/usr/bin/env bash
# Raccourci prod : restaure aquademie_db
# Usage : ./scripts/restore_aquademie_db.sh [FICHIER.backup]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP="${1:-${SCRIPT_DIR}/../aquademie_db.backup}"
exec "${SCRIPT_DIR}/db_restore" aquademie_db "${BACKUP}"
