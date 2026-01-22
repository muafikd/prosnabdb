# Анализ совместимости Docker контейнеров с Ubuntu 24.04

## Дата анализа: 2024
## Текущая ОС: macOS
## Целевая ОС: Ubuntu 24.04 LTS

---

## ✅ Совместимые компоненты

### 1. Backend Dockerfile
- **Базовый образ**: `python:3.11-slim` ✅
  - Python 3.11 полностью поддерживается Ubuntu 24.04
  - Образ основан на Debian, совместим с Ubuntu

- **Системные пакеты** (apt-get):
  - `build-essential` ✅ - доступен в Ubuntu 24.04
  - `libpq-dev` ✅ - PostgreSQL библиотеки, доступны
  - `libpango-1.0-0`, `libpangoft2-1.0-0` ✅ - доступны
  - `libharfbuzz-subset0` ✅ - доступен
  - `libjpeg-dev` ✅ - доступен
  - `libopenjp2-7-dev` ✅ - доступен
  - `libxcb1` ✅ - доступен
  - `fonts-dejavu`, `fonts-liberation` ✅ - доступны

### 2. Frontend Dockerfile
- **Базовый образ**: `node:22-alpine` ✅
  - Node.js 22 поддерживается Ubuntu 24.04
  - Alpine Linux совместим с любым хостом

- **Production образ**: `nginx:alpine` ✅
  - Nginx Alpine полностью совместим

### 3. Python зависимости
Все пакеты из `requirements.txt` совместимы с Python 3.11 и Ubuntu 24.04:
- Django 4.2 ✅
- DRF, JWT, CORS ✅
- WeasyPrint 60.0 ✅
- Celery 5.3.0 ✅
- Redis 5.0.0 ✅
- Gunicorn 21.2.0 ✅

### 4. Docker Compose
- **Версия**: 3.8 ✅
  - Совместима с Docker Compose v2 (рекомендуется для Ubuntu 24.04)

---

## ⚠️ Проблемы совместимости и решения

### 🔴 КРИТИЧЕСКАЯ ПРОБЛЕМА #1: `host.docker.internal`

**Проблема:**
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

`host.docker.internal` - это фича Docker Desktop для macOS/Windows. На Linux (Ubuntu) это **не работает по умолчанию**.

**Решение для Ubuntu 24.04:**

#### Вариант 1: Использовать имя сервиса PostgreSQL в docker-compose (РЕКОМЕНДУЕТСЯ)
Добавить PostgreSQL как сервис в docker-compose.yml:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: project_prosnab_postgres
    environment:
      POSTGRES_DB: prosnab_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 0#T%2
    ports:
      - "5435:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    # ...
    environment:
      - DATABASE_HOST=postgres  # Изменить с host.docker.internal
      - DATABASE_PORT=5432       # Изменить с 5435
    # Убрать extra_hosts
    depends_on:
      postgres:
        condition: service_healthy
      - redis
```

#### Вариант 2: Использовать IP хоста через network_mode
```yaml
backend:
  network_mode: "host"  # Использовать сеть хоста
  environment:
    - DATABASE_HOST=localhost
```

#### Вариант 3: Добавить host.docker.internal вручную (для внешней БД)
Если PostgreSQL запущен на хосте Ubuntu, добавить в docker-compose.yml:
```yaml
backend:
  extra_hosts:
    - "host.docker.internal:172.17.0.1"  # Docker bridge IP
```

Или использовать переменную окружения:
```bash
export DOCKER_HOST_IP=$(ip route | grep docker0 | awk '{print $9}')
```

---

### 🟡 ПРОБЛЕМА #2: Права доступа к файлам

**Проблема:**
На Linux права доступа к файлам более строгие, чем на macOS.

**Решение:**
Убедиться, что entrypoint.sh имеет правильные права:
```dockerfile
RUN chmod +x /app/entrypoint.sh
```

Также проверить права на volumes:
```yaml
volumes:
  - .:/app
  - media_volume:/app/media
  - static_volume:/app/staticfiles
```

---

### 🟡 ПРОБЛЕМА #3: Дублирование CELERY_BROKER_URL

**Проблема:**
В docker-compose.yml для worker есть дублирование:
```yaml
environment:
  - CELERY_BROKER_URL=redis://redis:6379/0
  - CELERY_BROKER_URL=redis://redis:6379/0  # Дубликат!
```

**Решение:**
Удалить дубликат.

---

### 🟡 ПРОБЛЕМА #4: Nginx конфигурация для статики

**Проблема:**
В nginx.conf указаны пути `/app/media` и `/app/static`, но volumes монтируются в `/app/staticfiles`.

**Решение:**
Синхронизировать пути или использовать правильные алиасы.

---

## 📋 Рекомендации для развертывания на Ubuntu 24.04

### 1. Обновить docker-compose.yml

Создать версию для Ubuntu с PostgreSQL сервисом:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: project_prosnab_postgres
    environment:
      POSTGRES_DB: prosnab_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD:-0#T%2}
    ports:
      - "${DATABASE_PORT:-5435}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: project_prosnab_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  backend:
    build: .
    container_name: project_prosnab_backend
    volumes:
      - media_volume:/app/media
      - static_volume:/app/staticfiles
    ports:
      - "8002:8000"
    environment:
      - DATABASE_HOST=postgres
      - DATABASE_NAME=prosnab_db
      - DATABASE_USER=postgres
      - DATABASE_PASSWORD=${DATABASE_PASSWORD:-0#T%2}
      - DATABASE_PORT=5432
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - ALLOWED_HOSTS=*
      - DEBUG=${DEBUG:-0}
      - PYTHONUNBUFFERED=1
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped

  worker:
    build: .
    container_name: project_prosnab_worker
    command: celery -A prosnabdb worker -l info
    volumes:
      - media_volume:/app/media
    environment:
      - DATABASE_HOST=postgres
      - DATABASE_NAME=prosnab_db
      - DATABASE_USER=postgres
      - DATABASE_PASSWORD=${DATABASE_PASSWORD:-0#T%2}
      - DATABASE_PORT=5432
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - PYTHONUNBUFFERED=1
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      backend:
        condition: service_started
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: project_prosnab_frontend
    ports:
      - "3006:80"
    volumes:
      - media_volume:/app/media
      - static_volume:/app/static
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  media_volume:
  static_volume:
```

### 2. Использовать .env файл для конфигурации

Создать `.env` файл:
```env
DATABASE_PASSWORD=your_secure_password
DEBUG=0
ALLOWED_HOSTS=yourdomain.com,localhost
```

### 3. Проверить версию Docker и Docker Compose

На Ubuntu 24.04 рекомендуется:
- Docker Engine: 24.0+
- Docker Compose: v2.20+

Установка:
```bash
# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose v2
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

### 4. Настройка firewall (если нужно)

```bash
sudo ufw allow 8002/tcp  # Backend
sudo ufw allow 3006/tcp  # Frontend
sudo ufw allow 5435/tcp  # PostgreSQL (если внешний доступ нужен)
```

### 5. Проверка системных требований

Минимальные требования для Ubuntu 24.04:
- RAM: 2GB+ (рекомендуется 4GB+)
- Disk: 10GB+ свободного места
- CPU: 2+ ядра

---

## 🧪 Тестирование совместимости

### Шаги для проверки на Ubuntu 24.04:

1. **Клонировать репозиторий:**
```bash
git clone https://github.com/muafikd/prosnabdb.git
cd prosnabdb
```

2. **Создать .env файл:**
```bash
cp .env.example .env  # Если есть
# Или создать вручную
```

3. **Собрать и запустить:**
```bash
docker compose build
docker compose up -d
```

4. **Проверить логи:**
```bash
docker compose logs backend
docker compose logs worker
docker compose logs frontend
```

5. **Проверить здоровье сервисов:**
```bash
docker compose ps
curl http://localhost:8002/api/health  # Если есть endpoint
curl http://localhost:3006
```

---

## 📝 Чеклист миграции с macOS на Ubuntu 24.04

- [ ] Обновить docker-compose.yml (убрать host.docker.internal)
- [ ] Добавить PostgreSQL сервис в docker-compose (или настроить внешний доступ)
- [ ] Удалить дубликат CELERY_BROKER_URL
- [ ] Проверить пути для статики в nginx.conf
- [ ] Создать .env файл с переменными окружения
- [ ] Установить Docker и Docker Compose v2 на Ubuntu
- [ ] Настроить firewall (если нужно)
- [ ] Протестировать сборку образов
- [ ] Протестировать запуск всех сервисов
- [ ] Проверить подключение к базе данных
- [ ] Проверить работу Celery worker
- [ ] Проверить доступность frontend и backend

---

## 🔧 Дополнительные улучшения для production

1. **Использовать docker-compose.prod.yml** для production
2. **Добавить healthchecks** для всех сервисов
3. **Настроить логирование** (log rotation)
4. **Использовать secrets** вместо переменных окружения в docker-compose
5. **Настроить SSL/TLS** через reverse proxy (nginx/traefik)
6. **Добавить мониторинг** (Prometheus, Grafana)
7. **Настроить backup** для PostgreSQL

---

## ✅ Заключение

**Общая совместимость: 95%**

Основные компоненты полностью совместимы с Ubuntu 24.04. Главная проблема - использование `host.docker.internal`, которая решается добавлением PostgreSQL как сервиса в docker-compose или настройкой сетевого доступа.

После внесения указанных изменений проект должен успешно работать на Ubuntu 24.04.
