## Panel (backend + frontend + PostgreSQL)

Панель хранит:

-   ноды
-   inbounds
-   clients

И умеет:

-   сгенерировать полный `config.json` для Xray на конкретную ноду
-   отправить (push) этот конфиг на ноду через node-agent

### Запуск

```bash
docker compose up --build
```

Backend API поднимется на `http://localhost:8000`.

Frontend (Next.js) поднимется на `http://localhost:3000`.

### Примеры запросов

Создать ноду (укажи URL node-agent и его `NODE_KEY`):

```bash
curl -X POST http://localhost:8000/nodes \
  -H 'Content-Type: application/json' \
  -d '{"name":"de-vps-1","url":"http://109.120.140.226:8585","node_key":"REPLACE_ME"}'
```

Создать inbound (Reality):

```bash
curl -X POST http://localhost:8000/inbounds \
  -H 'Content-Type: application/json' \
  -d '{"node_id":1,"name":"reality-vk","port":443,"protocol":"vless","network":"tcp","security":"reality","sni":"vk.com","reality_dest":"vk.com:443","reality_fingerprint":"chrome"}'
```

Создать клиента:

```bash
curl -X POST http://localhost:8000/clients \
  -H 'Content-Type: application/json' \
  -d '{"inbound_id":1,"username":"test1"}'
```

Получить сгенерированный config.json для ноды:

```bash
curl http://localhost:8000/nodes/1/config
```

Отправить (push) config.json на ноду:

```bash
curl -X POST http://localhost:8000/nodes/1/push
```
