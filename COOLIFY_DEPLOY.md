# Развёртывание в Coolify

## Почему фронт не открывается по адресу (404 / не запускается)

1. **Формат домена** — Coolify ждёт **полный URL с протоколом**.
2. **SSL** — отдельной кнопки «Let's Encrypt» нет: если указать домен с `https://`, сертификат запрашивается автоматически.
3. **К какому сервису привязан домен** — домен должен быть только у **frontend**, не у backend/worker.

---

## Как правильно указать домен (в т.ч. https://kp.mevent.kz)

### В Coolify → приложение → General → Domains for frontend

В поле **Domains for frontend** введи **полный URL с протоколом**:

- Для **HTTPS и автоматического Let's Encrypt**:
  ```text
  https://kp.mevent.kz
  ```
- Не вводи просто `kp.mevent.kz` и не только `http://` — для авто-SSL нужен именно **https://**.

**Domains for backend** и **Domains for worker** оставь пустыми.

После правок нажми **Save** и сделай **Redeploy** приложения.

---

## DNS

Запись для домена должен вести на сервер Coolify:

- **Тип:** A  
- **Имя:** `kp` (для kp.mevent.kz)  
- **Значение:** IP сервера (например `93.115.14.207`)

Проверка: `ping kp.mevent.kz` — должен отвечать этот IP.

---

## Environment приложения

- **ALLOWED_HOSTS** — должен быть либо `*`, либо список хостов с твоим доменом, например:
  ```text
  ALLOWED_HOSTS=localhost,kp.mevent.kz
  ```
- Остальные переменные (БД, SECRET_KEY и т.д.) — как уже настроено.

---

## Итог

| Что сделать | Где |
|-------------|-----|
| Домен с **https://** | General → Domains for frontend: `https://kp.mevent.kz` |
| DNS A → IP сервера | Панель домена mevent.kz |
| ALLOWED_HOSTS с доменом или `*` | Environment |
| Save + Redeploy | После любых изменений домена/переменных |

Отдельно настраивать SSL в docker-compose или Dockerfile не нужно — Coolify и Traefik делают это по полю домена с `https://`.

---

## Если фронт не открывается

### Проверка DNS (без протокола)

Команда `host` принимает только имя хоста, **без** `https://`:

```bash
host kp.mevent.kz
# или
ping -c 2 kp.mevent.kz
```

Должен отвечать IP сервера. Если NXDOMAIN — проверь A-запись для `kp.mevent.kz`.

### Frontend в статусе unhealthy

Если контейнер frontend **unhealthy**, Traefik может не направлять на него трафик. Логи и содержимое:

```bash
docker logs 89d237fb2aae
# или подставь ID/имя из docker ps:
docker ps
docker logs <CONTAINER_ID_или_имя_frontend>

# Есть ли index.html в контейнере:
docker exec <CONTAINER_ID_frontend> ls -la /usr/share/nginx/html/
```

В compose для frontend включён более мягкий healthcheck: любой ответ с порта 80 (в т.ч. 404) считается успехом. После пуша и Redeploy контейнер должен стать healthy.
