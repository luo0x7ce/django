#!/bin/bash
set -e

echo "Waiting for MySQL..."
# 等待数据库就绪（简单循环检查）
while ! python -c "import MySQLdb; MySQLdb.connect(host='$DB_HOST', user='$DB_USER', password='$DB_PASSWORD', db='$DB_NAME')" 2>/dev/null; do
    echo "Database not ready, sleeping..."
    sleep 2
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting application..."
exec "$@"

