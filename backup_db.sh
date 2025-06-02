set -e
set -o allexport
source .env
set +o allexport

DATE=$(date +%F)

mkdir -p "$BACKUP_DIR"

echo "[$(date +'%Y-%m-%d %H:%M:%S')] Iniciando backup para $DATE..."

docker exec -t "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip | openssl enc -aes-256-cbc -pbkdf2 -e -pass pass:$PASS_PHRASE -out "$BACKUP_DIR/db_$DATE.sql.gz.enc"

if [ $? -eq 0 ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Backup de base de datos exitoso: db_$DATE.sql.gz.enc"
else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Error al generar el backup de la base de datos"
    exit 1
fi

tar -czf - "$MEDIA_PATH" | openssl enc -aes-256-cbc -pbkdf2 -e -pass pass:$PASS_PHRASE -out "$BACKUP_DIR/media_$DATE.tar.gz.enc"

if [ $? -eq 0 ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Backup de media exitoso: media_$DATE.tar.gz.enc"
else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Error al generar el backup de media"
    exit 1
fi

find "$BACKUP_DIR" -type f -name "*.enc" -mtime +7 -exec rm {} \;

echo "[$(date +'%Y-%m-%d %H:%M:%S')] Backups de más de 7 días eliminados."
echo "[$(date +'%Y-%m-%d %H:%M:%S')] Backup completo finalizado correctamente."
