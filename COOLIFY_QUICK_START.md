# Быстрый старт для Coolify

## 🚀 Быстрая установка

### 1. Подготовка файла

```bash
# Скопируйте Coolify-версию docker-compose
cp docker-compose.coolify.yml docker-compose.yml

# Или переименуйте в репозитории через Git
git mv docker-compose.coolify.yml docker-compose.yml
```

### 2. В Coolify UI

1. **Создайте новый ресурс:**
   - Resources → New Resource → Docker Compose
   - Название: `prosnabdb`

2. **Подключите репозиторий:**
   - Source: GitHub/GitLab
   - Репозиторий: `muafikd/prosnabdb`
   - Ветка: `main`
   - Docker Compose файл: `docker-compose.yml`

3. **Настройте переменные окружения:**

   **Обязательные:**
   ```env
   DATABASE_PASSWORD=your_secure_password
   SECRET_KEY=your_django_secret_key
   DEBUG=0
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

   **Опциональные:**
   ```env
   DATABASE_NAME=prosnab_db
   DATABASE_USER=postgres
   BACKEND_PORT=8000
   FRONTEND_PORT=80
   ```

4. **Добавьте домены:**
   - Frontend: `app.yourdomain.com`
   - Backend: `api.yourdomain.com`

5. **Деплой:**
   - Нажмите **Deploy**
   - Дождитесь завершения сборки

### 3. После деплоя

```bash
# Создайте суперпользователя
# В Coolify: Resources → prosnabdb → backend → Terminal
python manage.py createsuperuser
```

## ✅ Проверка

- Frontend: `https://app.yourdomain.com`
- Backend API: `https://api.yourdomain.com/api/`
- Admin: `https://api.yourdomain.com/admin/`

## 📚 Полная документация

См. `COOLIFY_DEPLOYMENT_GUIDE.md` для детальных инструкций.
