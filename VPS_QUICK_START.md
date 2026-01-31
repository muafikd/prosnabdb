# Быстрый старт для VPS с внешним Nginx

## 🚀 Быстрая установка

### 1. На VPS сервере

```bash
# Установить Docker и Nginx
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo apt install nginx certbot python3-certbot-nginx -y

# Клонировать проект
git clone https://github.com/muafikd/prosnabdb.git
cd prosnabdb

# Использовать VPS конфигурацию
cp docker-compose.vps.yml docker-compose.yml

# Создать .env
cat > .env << EOF
DATABASE_PASSWORD=your_password
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
DEBUG=0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
EOF
```

### 2. Запустить контейнеры

```bash
docker compose build
docker compose up -d
```

### 3. Настроить Nginx

```bash
# Скопировать конфигурацию
sudo cp nginx/nginx-http.conf /etc/nginx/sites-available/prosnabdb

# Заменить домен
sudo sed -i 's/yourdomain.com/ваш-домен.com/g' /etc/nginx/sites-available/prosnabdb

# Активировать
sudo ln -s /etc/nginx/sites-available/prosnabdb /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Настроить SSL

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# После получения сертификата, использовать HTTPS конфигурацию
sudo cp nginx/nginx.conf /etc/nginx/sites-available/prosnabdb
sudo sed -i 's/yourdomain.com/ваш-домен.com/g' /etc/nginx/sites-available/prosnabdb
sudo nginx -t && sudo systemctl reload nginx
```

### 5. Создать суперпользователя

```bash
docker compose exec backend python manage.py createsuperuser
```

## ✅ Проверка

- Frontend: `https://yourdomain.com`
- API: `https://yourdomain.com/api/`
- Admin: `https://yourdomain.com/admin/`

## 📚 Полная документация

См. `VPS_NGINX_SETUP_GUIDE.md` для детальных инструкций.
