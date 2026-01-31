# Руководство по настройке Nginx на VPS сервере

## 📋 Обзор

Это руководство поможет настроить внешний Nginx на VPS сервере для проксирования запросов к Docker контейнерам.

**Архитектура:**
```
Интернет → Nginx (VPS) → Docker контейнеры
                        ├── Frontend (localhost:3000)
                        └── Backend (localhost:8000)
```

---

## 🚀 Пошаговая настройка

### Шаг 1: Подготовка VPS сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Установить Docker Compose v2
sudo apt-get install docker-compose-plugin -y

# Установить Nginx
sudo apt install nginx -y

# Установить Certbot для SSL
sudo apt install certbot python3-certbot-nginx -y
```

### Шаг 2: Клонирование проекта

```bash
# Клонировать репозиторий
git clone https://github.com/muafikd/prosnabdb.git
cd prosnabdb

# Использовать VPS конфигурацию
cp docker-compose.vps.yml docker-compose.yml
```

### Шаг 3: Настройка переменных окружения

```bash
# Создать .env файл
cat > .env << EOF
# База данных
DATABASE_NAME=prosnab_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password_here
DATABASE_PORT=5432

# Django
SECRET_KEY=your_django_secret_key_here
DEBUG=0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Опционально
COMPOSE_PROJECT_NAME=prosnab
EOF

# Сгенерировать SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print('SECRET_KEY=' + get_random_secret_key())" >> .env
```

### Шаг 4: Запуск Docker контейнеров

```bash
# Собрать образы
docker compose build

# Запустить контейнеры
docker compose up -d

# Проверить статус
docker compose ps

# Проверить логи
docker compose logs -f
```

### Шаг 5: Настройка Nginx

#### 5.1. Копирование конфигурации

```bash
# Скопировать конфигурацию Nginx
sudo cp nginx/nginx-http.conf /etc/nginx/sites-available/prosnabdb

# Отредактировать конфигурацию (замените yourdomain.com на ваш домен)
sudo nano /etc/nginx/sites-available/prosnabdb
```

#### 5.2. Редактирование конфигурации

Замените `yourdomain.com` на ваш реальный домен в файле:
```bash
sudo sed -i 's/yourdomain.com/ваш-домен.com/g' /etc/nginx/sites-available/prosnabdb
```

#### 5.3. Активация конфигурации

```bash
# Создать символическую ссылку
sudo ln -s /etc/nginx/sites-available/prosnabdb /etc/nginx/sites-enabled/

# Удалить дефолтную конфигурацию (опционально)
sudo rm /etc/nginx/sites-enabled/default

# Проверить конфигурацию
sudo nginx -t

# Перезагрузить Nginx
sudo systemctl reload nginx
```

### Шаг 6: Настройка DNS

Убедитесь, что DNS записи для вашего домена указывают на IP адрес VPS:

```
A     @            -> ваш_ip_адрес
A     www          -> ваш_ip_адрес
```

Проверить DNS:
```bash
dig yourdomain.com
nslookup yourdomain.com
```

### Шаг 7: Настройка SSL (Let's Encrypt)

```bash
# Получить SSL сертификат
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Certbot автоматически обновит конфигурацию Nginx
# Используйте HTTPS версию конфигурации
sudo cp nginx/nginx.conf /etc/nginx/sites-available/prosnabdb
sudo sed -i 's/yourdomain.com/ваш-домен.com/g' /etc/nginx/sites-available/prosnabdb

# Проверить и перезагрузить
sudo nginx -t
sudo systemctl reload nginx
```

### Шаг 8: Настройка автообновления SSL

```bash
# Certbot автоматически настроит cron для обновления
# Проверить можно командой:
sudo certbot renew --dry-run
```

### Шаг 9: Создание суперпользователя Django

```bash
# Войти в контейнер backend
docker compose exec backend bash

# Создать суперпользователя
python manage.py createsuperuser

# Выйти
exit
```

### Шаг 10: Применение миграций

Миграции применяются автоматически через `entrypoint.sh`, но можно проверить:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
```

---

## 🔧 Дополнительная настройка

### Настройка firewall (UFW)

```bash
# Разрешить SSH
sudo ufw allow 22/tcp

# Разрешить HTTP и HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включить firewall
sudo ufw enable

# Проверить статус
sudo ufw status
```

### Оптимизация Nginx

Добавьте в `/etc/nginx/nginx.conf` (в блок `http {`):

```nginx
# Кэширование
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m use_temp_path=off;

# Сжатие
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
```

### Мониторинг логов

```bash
# Логи Nginx
sudo tail -f /var/log/nginx/prosnabdb_access.log
sudo tail -f /var/log/nginx/prosnabdb_error.log

# Логи Docker контейнеров
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f worker
```

### Бэкап базы данных

```bash
# Создать скрипт бэкапа
cat > backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U postgres prosnab_db > $BACKUP_DIR/backup_$DATE.sql
# Удалить бэкапы старше 30 дней
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
EOF

chmod +x backup_db.sh

# Добавить в cron (ежедневно в 2:00)
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/backup_db.sh") | crontab -
```

---

## 🐛 Troubleshooting

### Проблема: Nginx не может подключиться к контейнерам

**Решение:**
```bash
# Проверить, что контейнеры запущены
docker compose ps

# Проверить, что порты слушаются
sudo netstat -tlnp | grep -E '3000|8000'

# Проверить логи контейнеров
docker compose logs backend
docker compose logs frontend
```

### Проблема: 502 Bad Gateway

**Решение:**
1. Проверить, что контейнеры запущены: `docker compose ps`
2. Проверить логи: `docker compose logs backend`
3. Проверить, что порты правильные в nginx.conf
4. Проверить firewall: `sudo ufw status`

### Проблема: Статические файлы не загружаются

**Решение:**
```bash
# Собрать статические файлы
docker compose exec backend python manage.py collectstatic --noinput

# Проверить права доступа
docker compose exec backend ls -la /app/staticfiles
```

### Проблема: SSL сертификат не работает

**Решение:**
```bash
# Проверить конфигурацию
sudo nginx -t

# Проверить сертификат
sudo certbot certificates

# Обновить сертификат вручную
sudo certbot renew --force-renewal
```

### Проблема: CORS ошибки

**Решение:**
Убедитесь, что в `ALLOWED_HOSTS` указан ваш домен:
```env
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

И перезапустите backend:
```bash
docker compose restart backend
```

---

## 📊 Проверка работоспособности

### Тестирование endpoints

```bash
# Frontend
curl -I http://yourdomain.com

# Backend API
curl -I http://yourdomain.com/api/

# Django Admin
curl -I http://yourdomain.com/admin/

# Статические файлы
curl -I http://yourdomain.com/static/admin/css/base.css
```

### Проверка SSL

```bash
# Проверить SSL сертификат
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Онлайн проверка
# https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

---

## 🔒 Безопасность

### Рекомендации:

1. **Измените все пароли:**
   - DATABASE_PASSWORD
   - SECRET_KEY
   - Суперпользователь Django

2. **Настройте fail2ban:**
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

3. **Регулярные обновления:**
```bash
# Добавить в cron
0 3 * * 0 apt update && apt upgrade -y
```

4. **Ограничьте доступ к портам:**
   - Backend и Frontend доступны только через localhost
   - PostgreSQL и Redis не публикуются наружу

5. **Мониторинг:**
   - Настройте логирование
   - Используйте мониторинг (Prometheus, Grafana)
   - Настройте алерты

---

## 📝 Чеклист развертывания

- [ ] Docker и Docker Compose установлены
- [ ] Nginx установлен
- [ ] Проект клонирован
- [ ] docker-compose.vps.yml переименован в docker-compose.yml
- [ ] .env файл создан с правильными значениями
- [ ] Контейнеры собраны и запущены
- [ ] DNS записи настроены
- [ ] Nginx конфигурация скопирована и отредактирована
- [ ] Nginx конфигурация активирована
- [ ] Nginx перезагружен
- [ ] SSL сертификат получен
- [ ] Firewall настроен
- [ ] Суперпользователь Django создан
- [ ] Миграции применены
- [ ] Статические файлы собраны
- [ ] Тестирование всех endpoints
- [ ] Бэкапы настроены

---

## 🎉 Готово!

После выполнения всех шагов ваше приложение должно быть доступно по адресу:
- **Frontend:** `https://yourdomain.com`
- **Backend API:** `https://yourdomain.com/api/`
- **Django Admin:** `https://yourdomain.com/admin/`

---

## 📚 Дополнительные ресурсы

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
