#!/bin/bash

# --- INDSTILLINGER ---
PROJEKT_MAPPE="$HOME/smart-FP"
BACKUP_MAPPE="$HOME/backups"
DATO=$(date +%Y-%m-%d_%H-%M-%S)

# 1. TJEK OM DATABASEN FINDES
if [ ! -f "$PROJEKT_MAPPE/database.db" ]; then
    echo "FEJL: Ingen database fundet i $PROJEKT_MAPPE"
    exit 1
fi

# 2. UDFØR BACKUP
sqlite3 "$PROJEKT_MAPPE/database.db" ".backup '$BACKUP_MAPPE/db_backup_$DATO.db'"

# 3. OPRYDNING (Slet filer ældre end 7 dage)
find "$BACKUP_MAPPE" -name "db_backup_*.db" -mtime +7 -delete

# 4. LOGFØRING
echo "[$(date)] Backup oprettet: db_backup_$DATO.db" >> "$BACKUP_MAPPE/backup.log"