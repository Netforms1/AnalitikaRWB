# Деплой на VPS (reg.ru или любой Ubuntu 22.04+)

## 0. Что нужно

- VPS с Ubuntu 22.04/24.04, минимум 2 GB RAM, 20 GB диска.
- Доменное имя, у которого `A`-запись указывает на IP сервера.
- SSH-доступ с правами root.

## 1. DNS

В личном кабинете reg.ru → ваш домен → «Управление DNS» → добавьте запись:

| Тип | Имя | Значение | TTL |
|---|---|---|---|
| A | `@` | `IP_сервера` | 3600 |
| A | `www` | `IP_сервера` | 3600 |

DNS прорастает 5–30 минут. Проверить: `dig +short ваш-домен.ru` должен показать IP.

## 2. Подготовка сервера

```bash
ssh root@IP_СЕРВЕРА

# Docker
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

# Открыть фаервол (если ufw активен)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
```

## 3. Залить проект

```bash
apt install -y git
git clone -b claude/keen-lamport-pVC2M https://github.com/Netforms1/AnalitikaRWB.git
cd AnalitikaRWB

cp .env.prod.example .env
nano .env
```

В `.env` поставьте:
- `DOMAIN=ваш-домен.ru`
- `LETSENCRYPT_EMAIL=ваш@email.ru` — на него Let's Encrypt пришлёт уведомления.
- `POSTGRES_PASSWORD` — придумайте длинный.
- `JWT_SECRET` — сгенерируйте: `openssl rand -hex 32`.

Сохранить: Ctrl+O → Enter → Ctrl+X.

## 4. Запуск

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Первый запуск 3–5 минут (сборка фронта, тяжелее всего npm install).

Проверка:

```bash
docker compose -f docker-compose.prod.yml ps    # все 4 сервиса должны быть "Up"
docker compose -f docker-compose.prod.yml logs caddy | tail -20    # сертификат получен?
```

Открыть в браузере: **https://ваш-домен.ru** — должна появиться форма логина.

Зарегистрируйтесь — первый аккаунт сразу станет вашим. Дальше — добавляйте магазины и работайте.

## Полезные команды

```bash
# Перезапуск после git pull
git pull
docker compose -f docker-compose.prod.yml up -d --build

# Логи
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f caddy

# Бэкап БД
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U analitika analitika > backup-$(date +%F).sql

# Восстановление
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U analitika analitika < backup-2026-06-02.sql
```

## Регулярный бэкап (cron)

```bash
crontab -e
# раз в сутки в 3:30 ночи:
30 3 * * * cd /root/AnalitikaRWB && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U analitika analitika | gzip > /root/backups/db-$(date +\%F).sql.gz
```

## Перенос legacy-данных

Если у вас уже были данные в БД до апдейта с авторизацией, миграция
0004 создала "технический" аккаунт `legacy@local / changeme`. Войдите
под ним, посмотрите старые магазины. Чтобы перенести их на ваш
обычный аккаунт — через `psql` поменяйте `wb_accounts.user_id`:

```sql
UPDATE wb_accounts SET user_id = (SELECT id FROM users WHERE email='ваш@email.ru');
DELETE FROM users WHERE email='legacy@local';
```
