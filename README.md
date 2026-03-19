# ProsnabDB - Система управления коммерческими предложениями

Полнофункциональная система для управления оборудованием, клиентами и коммерческими предложениями с автоматическим расчетом себестоимости и цен.

## 📋 Содержание

- [Описание проекта](#описание-проекта)
- [Технологический стек](#технологический-стек)
- [Структура проекта](#структура-проекта)
- [Установка и настройка](#установка-и-настройка)
  - [Backend (Django)](#backend-django)
  - [Frontend (Vue.js)](#frontend-vuejs)
- [Настройка базы данных](#настройка-базы-данных)
- [Запуск проекта](#запуск-проекта)
- [API Документация](#api-документация)
- [Основные функции](#основные-функции)
- [Роли пользователей](#роли-пользователей)

## 🎯 Описание проекта

ProsnabDB - это веб-приложение для управления коммерческими предложениями, которое позволяет:

- Управлять каталогом оборудования с детальной информацией
- Создавать и редактировать коммерческие предложения (КП)
- Автоматически рассчитывать себестоимость оборудования с учетом:
  - Закупочных цен
  - Логистики (Китай → Казахстан, Россия → Казахстан, По Казахстану)
  - Складских расходов
  - Производственных расходов
  - Дополнительных расходов (процент, фиксированная сумма, коэффициент)
- Конвертировать валюты с учетом курсов обмена
- Генерировать PDF документы коммерческих предложений
- Управлять клиентами и платежами

## 🛠 Технологический стек

### Backend
- **Python 3.14+**
- **Django 4.2+** - веб-фреймворк
- **Django REST Framework** - API
- **PostgreSQL** - база данных
- **JWT (djangorestframework-simplejwt)** - аутентификация
- **ReportLab** - генерация PDF
- **Django CORS Headers** - обработка CORS
- **DRF Spectacular** - документация API

### Frontend
- **Vue.js 3** - фреймворк
- **TypeScript** - типизация
- **Vite** - сборщик
- **Vue Router** - маршрутизация
- **Pinia** - управление состоянием
- **Element Plus** - UI компоненты
- **Axios** - HTTP клиент
- **Vee-validate** - валидация форм

## 📁 Структура проекта

```
prosnabdb2/
├── frontend/                 # Vue.js фронтенд приложение
│   ├── src/
│   │   ├── api/             # API клиенты
│   │   ├── assets/          # Статические файлы
│   │   ├── components/      # Vue компоненты
│   │   ├── router/          # Маршрутизация
│   │   ├── stores/          # Pinia stores
│   │   └── views/           # Страницы
│   ├── public/              # Публичные файлы
│   ├── package.json
│   └── vite.config.ts
├── proposals/                # Django приложение
│   ├── migrations/          # Миграции БД
│   ├── models.py            # Модели данных
│   ├── serializers.py      # Сериализаторы
│   ├── views.py             # API views
│   ├── urls.py              # URL маршруты
│   ├── services.py          # Бизнес-логика
│   └── permissions.py       # Права доступа
├── prosnabdb/               # Настройки Django проекта
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py                # Django CLI
├── requirements.txt         # Python зависимости
└── README.md
```

## 🚀 Установка и настройка

### Требования

- Python 3.14 или выше
- Node.js 20.19+ или 22.12+
- PostgreSQL 12+
- npm или yarn

### Backend (Django)

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd prosnabdb2
```

2. **Создайте виртуальное окружение:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**

Создайте файл `.env` в корне проекта:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
SERVICE_URL_FRONTEND=https://kp.mevent.kz
DATABASE_NAME=prosnabdb
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

5. **Настройте базу данных** (см. раздел ниже)

6. **Примените миграции:**
```bash
python manage.py migrate
```

7. **Создайте суперпользователя:**
```bash
python manage.py createsuperuser
```

8. **Соберите статические файлы:**
```bash
python manage.py collectstatic --noinput
```

### Frontend (Vue.js)

1. **Перейдите в директорию frontend:**
```bash
cd frontend
```

2. **Установите зависимости:**
```bash
npm install
```

3. **Создайте файл `.env.local` для переменных окружения:**
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

4. **Запустите dev сервер:**
```bash
npm run dev
```

Приложение будет доступно по адресу `http://localhost:5173`

## 🗄 Настройка базы данных

### PostgreSQL

1. **Создайте базу данных:**
```sql
CREATE DATABASE prosnabdb;
CREATE USER prosnabuser WITH PASSWORD 'your-password';
ALTER ROLE prosnabuser SET client_encoding TO 'utf8';
ALTER ROLE prosnabuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE prosnabuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE prosnabdb TO prosnabuser;
```

2. **Настройте подключение в `prosnabdb/settings.py`:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'prosnabdb'),
        'USER': os.getenv('DATABASE_USER', 'postgres'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}
```

## ▶ Запуск проекта

### Development режим

**Backend:**
```bash
python manage.py runserver
```
Backend будет доступен по адресу `http://localhost:8000`

**Frontend:**
```bash
cd frontend
npm run dev
```
Frontend будет доступен по адресу `http://localhost:5173`

### Production режим

**Backend:**
```bash
# Используйте gunicorn или uwsgi
gunicorn prosnabdb.wsgi:application --bind 0.0.0.0:8000
```

**Frontend:**
```bash
cd frontend
npm run build
# Разверните содержимое папки dist на веб-сервере (nginx, apache)
```

## 📚 API Документация

После запуска сервера, API документация доступна по адресу:
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`

### Основные эндпоинты

#### Аутентификация
- `POST /api/auth/register/` - Регистрация пользователя
- `POST /api/auth/login/` - Вход в систему
- `POST /api/auth/logout/` - Выход из системы
- `GET /api/auth/profile/` - Профиль пользователя
- `POST /api/auth/token/refresh/` - Обновление JWT токена

#### Клиенты
- `GET /api/clients/` - Список клиентов
- `POST /api/clients/` - Создать клиента
- `GET /api/clients/{id}/` - Детали клиента
- `PATCH /api/clients/{id}/` - Обновить клиента
- `DELETE /api/clients/{id}/` - Удалить клиента

#### Оборудование
- `GET /api/equipment/` - Список оборудования
- `POST /api/equipment/` - Создать оборудование
- `GET /api/equipment/{id}/` - Детали оборудования
- `PATCH /api/equipment/{id}/` - Обновить оборудование
- `DELETE /api/equipment/{id}/` - Удалить оборудование

#### Коммерческие предложения
- `GET /api/commercial-proposals/` - Список КП
- `POST /api/commercial-proposals/` - Создать КП
- `GET /api/commercial-proposals/{id}/` - Детали КП
- `PATCH /api/commercial-proposals/{id}/` - Обновить КП
- `DELETE /api/commercial-proposals/{id}/` - Удалить КП
- `GET /api/commercial-proposals/{id}/pdf/` - Скачать PDF КП

#### Расчет себестоимости
- `POST /api/cost-calculations/calculate/` - Рассчитать себестоимость оборудования
- `GET /api/cost-calculations/` - История расчетов
- `GET /api/cost-calculations/equipment/{id}/history/` - История расчетов для оборудования

#### Дополнительные расходы
- `GET /api/additional-prices/` - Список дополнительных расходов
- `POST /api/additional-prices/` - Создать дополнительный расход
- `PATCH /api/additional-prices/{id}/` - Обновить дополнительный расход
- `DELETE /api/additional-prices/{id}/` - Удалить дополнительный расход

#### Логистика
- `GET /api/logistics/` - Список логистики
- `POST /api/logistics/` - Создать логистику
- `PATCH /api/logistics/{id}/` - Обновить логистику
- `DELETE /api/logistics/{id}/` - Удалить логистику

#### Курсы валют
- `GET /api/exchange-rates/` - Список курсов валют
- `GET /api/exchange-rates/latest/` - Последний курс валюты
- `POST /api/exchange-rates/` - Создать курс валюты

## ⚙ Основные функции

### Управление оборудованием

- Создание и редактирование оборудования с детальной информацией
- Управление спецификациями и технологическими процессами
- Загрузка изображений и документов
- Управление закупочными ценами
- Настройка логистики (Китай → Казахстан, Россия → Казахстан, По Казахстану)
- Просмотр в табличном и карточном виде

### Расчет себестоимости

Система автоматически рассчитывает себестоимость оборудования по формуле:

```
Себестоимость = (Закупочная цена + Логистика + Склад + Производство + Доп.расходы) × Курс валюты
```

**Дополнительные расходы** могут быть:
- **Процент** - процент от базовой себестоимости
- **Фиксированная сумма** - фиксированная сумма в KZT
- **Коэффициент** - коэффициент умножения базовой себестоимости

### Коммерческие предложения

- Создание КП с выбором оборудования
- Автоматический расчет итоговой цены с учетом маржи
- Генерация PDF документов
- Управление версиями КП
- Отслеживание статусов (черновик, отправлено, принято, отклонено)

### Управление клиентами

- CRUD операции с клиентами
- Поиск и фильтрация
- Пагинация

## 👥 Роли пользователей

### Viewer (Просмотр)
- Просмотр оборудования, клиентов и КП
- Просмотр расчетов себестоимости

### Manager (Менеджер)
- Все права Viewer
- Создание и редактирование оборудования
- Создание и редактирование клиентов
- Создание и редактирование КП
- Расчет себестоимости

### Admin (Администратор)
- Все права Manager
- Управление пользователями
- Управление курсами валют
- Полный доступ к системе

## 🔐 Безопасность

- JWT токены для аутентификации
- Автоматическое обновление токенов
- Ролевая система доступа
- CORS настройки для безопасности
- Валидация данных на клиенте и сервере

## 📝 Миграции

Для применения миграций:
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🧪 Тестирование

```bash
# Backend тесты
python manage.py test

# Frontend тесты (если настроены)
cd frontend
npm run test
```

## 🐛 Отладка

### Backend
- Логи Django доступны в консоли
- Используйте `DEBUG=True` в development режиме
- Проверьте логи PostgreSQL для ошибок БД

### Frontend
- Откройте DevTools в браузере (F12)
- Проверьте Network tab для API запросов
- Проверьте Console для ошибок JavaScript

## 📦 Развертывание

### Docker (опционально)

Создайте `Dockerfile` и `docker-compose.yml` для контейнеризации приложения.

### Nginx конфигурация

Пример конфигурации для production:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

## 🤝 Вклад в проект

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request



**Примечание:** Убедитесь, что все секретные ключи и пароли хранятся в переменных окружения и не попадают в репозиторий!

