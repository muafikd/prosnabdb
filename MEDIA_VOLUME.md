# Media Volume — проверка и права

## Текущее состояние (проверено)

- **Backend** (`/app/media`): владелец `app:app` (uid 1000), каталог `photos/` есть, 7 фото.
- **Frontend** (nginx): тот же volume смонтирован в `/app/media`; файлы видны как `1000:1000`, nginx (user `nginx`) читает их по правам `r--r--r--`.
- **HTTP**: `curl http://localhost:3006/media/photos/<uuid>.jpg` возвращает **200** — раздача работает.

## Как проверить самому

```bash
# Список файлов в volume (backend)
docker compose exec backend ls -la /app/media/photos/

# Проверка раздачи по HTTP (должен быть 200)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3006/media/photos/e3642e7988a64dd4be04189b73f64d7a.jpg
```

Скрипт проверки (в backend):

```bash
docker compose exec backend sh /app/scripts/check-media-volume.sh
```

## Если после пересоздания volume появился «Permission denied»

Новый пустой volume может создаться от root, и пользователь `app` не сможет писать в `/app/media`. Тогда:

1. Остановить контейнеры, чтобы не было обращений к volume:
   ```bash
   docker compose stop backend worker frontend
   ```

2. Временно запустить контейнер от root и поправить владельца:
   ```bash
   docker compose run --no-deps --user root backend sh -c "chown -R 1000:1000 /app/media && chmod -R 755 /app/media"
   ```

3. Запустить стек снова:
   ```bash
   docker compose up -d
   ```

После этого backend (user `app`, uid 1000) снова сможет создавать файлы в `/app/media/photos/`, а nginx во frontend — отдавать их по `/media/`.
