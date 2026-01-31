#!/bin/sh
# Проверка media_volume и прав для раздачи фото.
# Запуск: ./scripts/check-media-volume.sh  или  docker compose exec backend sh /app/scripts/check-media-volume.sh

set -e

echo "=== 1. Backend: /app/media ==="
ls -la /app/media/ 2>/dev/null || { echo "ОШИБКА: нет доступа к /app/media"; exit 1; }
echo ""
echo "=== 2. Backend: /app/media/photos ==="
ls -la /app/media/photos/ 2>/dev/null || { echo "ОШИБКА: нет /app/media/photos"; exit 1; }
echo ""
echo "=== 3. Пользователь backend ==="
whoami
id
echo ""
echo "=== 4. Проверка записи (backend) ==="
touch /app/media/photos/.write_test 2>/dev/null && rm -f /app/media/photos/.write_test && echo "OK: запись возможна" || echo "ВНИМАНИЕ: нет прав на запись в /app/media/photos"
echo ""
echo "=== Готово. Volume и права в порядке, если выше нет ошибок. ==="
