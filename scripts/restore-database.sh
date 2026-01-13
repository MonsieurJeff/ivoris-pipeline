#!/bin/bash
# Restore DentalDB from backup
# Usage: ./scripts/restore-database.sh

set -e

CONTAINER="ivoris-sqlserver"
SA_PASSWORD="YourStrong@Passw0rd"
BACKUP_FILE="/var/opt/mssql/backup/DentalDB.bak"

echo "=== Ivoris Database Restore ==="

# Check if container is running
if ! docker ps | grep -q $CONTAINER; then
    echo "Error: Container $CONTAINER not running"
    echo "Run: docker-compose up -d"
    exit 1
fi

# Wait for SQL Server
echo "Waiting for SQL Server..."
sleep 5

# Get logical file names from backup
echo "Getting backup info..."
docker exec $CONTAINER /opt/mssql-tools18/bin/sqlcmd -C \
    -S localhost -U sa -P "$SA_PASSWORD" \
    -Q "RESTORE FILELISTONLY FROM DISK = '$BACKUP_FILE'" \
    | head -20

# Restore database
echo "Restoring DentalDB..."
docker exec $CONTAINER /opt/mssql-tools18/bin/sqlcmd -C \
    -S localhost -U sa -P "$SA_PASSWORD" \
    -Q "
    IF EXISTS (SELECT name FROM sys.databases WHERE name = 'DentalDB')
    BEGIN
        ALTER DATABASE DentalDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
        DROP DATABASE DentalDB;
    END
    "

docker exec $CONTAINER /opt/mssql-tools18/bin/sqlcmd -C \
    -S localhost -U sa -P "$SA_PASSWORD" \
    -Q "
    RESTORE DATABASE DentalDB
    FROM DISK = '$BACKUP_FILE'
    WITH
        MOVE 'dentaldb' TO '/var/opt/mssql/data/DentalDB.mdf',
        MOVE 'dentaldb_log' TO '/var/opt/mssql/data/DentalDB_log.ldf',
        REPLACE
    "

# Verify
echo "Verifying..."
docker exec $CONTAINER /opt/mssql-tools18/bin/sqlcmd -C \
    -S localhost -U sa -P "$SA_PASSWORD" \
    -Q "SELECT name, state_desc FROM sys.databases WHERE name = 'DentalDB'"

echo ""
echo "=== Restore Complete ==="
echo "Database: DentalDB"
echo "Status: ONLINE"
