# Руководство по миграции на Ubuntu 24.04

## Быстрый старт

### 1. Подготовка Ubuntu 24.04 сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Установить Docker Compose v2
sudo apt-get install docker-compose-plugin -y

# Проверить установку
docker --version
docker compose version
```

### 2. Клонирование и настройка проекта

```bash
# Клонировать репозиторий
git clone https://github.com/muafikd/prosnabdb.git
cd prosnabdb

# Создать .env файл
cat > .env << EOF
DATABASE_NAME=prosnab_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password_here
DATABASE_PORT=5435
DEBUG=0
ALLOWED_HOSTS=yourdomain.com,localhost,127.0.0.1
EOF

# Использовать Ubuntu-совместимый docker-compose
cp docker-compose.ubuntu.yml docker-compose.yml
```

### 3. Запуск проекта

```bash
# Собрать образы
docker compose build

# Запустить все сервисы
docker compose up -d

# Проверить статус
docker compose ps

# Просмотреть логи
docker compose logs -f
```

### 4. Проверка работоспособности

```bash
# Проверить backend
curl http://localhost:8002/api/

# Проверить frontend
curl http://localhost:3006

# Проверить базу данных
docker compose exec postgres psql -U postgres -d prosnab_db -c "\dt"
```

## Различия между macOS и Ubuntu версиями

### macOS версия (docker-compose.yml)
- Использует `host.docker.internal` для доступа к PostgreSQL на хосте
- PostgreSQL запущен вне Docker
- Подходит для разработки на macOS/Windows

### Ubuntu версия (docker-compose.ubuntu.yml)
- PostgreSQL запущен как Docker сервис
- Все сервисы в одной Docker сети
- Подходит для production и Linux серверов

## Миграция данных (если нужно)

Если у вас уже есть база данных на macOS:

```bash
# На macOS: экспортировать данные
pg_dump -h localhost -U postgres -d prosnab_db > backup.sql

# На Ubuntu: импортировать данные
docker compose exec -T postgres psql -U postgres -d prosnab_db < backup.sql
```

## Troubleshooting

### Проблема: Контейнеры не могут подключиться к PostgreSQL

**Решение:**
- Убедитесь, что используете `docker-compose.ubuntu.yml`
- Проверьте, что PostgreSQL сервис запущен: `docker compose ps postgres`
- Проверьте логи: `docker compose logs postgres`

### Проблема: Permission denied при монтировании volumes

**Решение:**
```bash
# Изменить владельца директорий
sudo chown -R $USER:$USER .
```

### Проблема: Frontend не может подключиться к backend

**Решение:**
- Проверьте, что backend запущен: `docker compose ps backend`
- Проверьте nginx конфигурацию в `frontend/nginx.conf`
- Убедитесь, что backend доступен по имени сервиса `backend:8000`

### Проблема: Celery worker не работает

**Решение:**
```bash
# Проверить логи worker
docker compose logs worker

# Проверить подключение к Redis
docker compose exec worker celery -A prosnabdb inspect ping
```

## Production рекомендации

1. **Изменить пароли:**
   - Обновите `DATABASE_PASSWORD` в `.env`
   - Используйте сильные пароли

2. **Настроить SSL:**
   - Используйте reverse proxy (nginx/traefik) для SSL
   - Настройте Let's Encrypt сертификаты

3. **Настроить backup:**
   ```bash
   # Создать скрипт backup
   cat > backup.sh << 'EOF'
   #!/bin/bash
   docker compose exec -T postgres pg_dump -U postgres prosnab_db > backup_$(date +%Y%m%d_%H%M%S).sql
   EOF
   chmod +x backup.sh
   ```

4. **Мониторинг:**
   - Настроить логирование
   - Добавить мониторинг (Prometheus/Grafana)
   - Настроить алерты

5. **Обновление:**
   ```bash
   # Обновить код
   git pull
   
   # Пересобрать и перезапустить
   docker compose build
   docker compose up -d
   
   # Применить миграции
   docker compose exec backend python manage.py migrate
   ```

## Откат на macOS версию

Если нужно вернуться к macOS версии:

```bash
# Восстановить оригинальный docker-compose.yml
git checkout docker-compose.yml

# Или использовать macOS-специфичную версию
# (нужно создать docker-compose.macos.yml)
```
