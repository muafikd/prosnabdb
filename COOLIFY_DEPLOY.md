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
