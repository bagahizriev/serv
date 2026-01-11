## Node (Xray + Agent API)

### Сборка

```bash
docker build -t xray-node .
```

### Запуск

```bash
docker run -d --name xray-node \
  -p 8585:8585 \
  -e XRAY_API_KEY=change_me \
  -e XRAY_APPLY_DEBOUNCE_SECONDS=1.5 \
  -v xray_node_db:/var/lib/xray-api \
  -v xray_node_config:/etc/xray \
  xray-node
```

### Проверка

```bash
curl -H 'X-API-Key: change_me' http://localhost:8585/inbounds
```

### Reality пример

Создать inbound (Reality):

```bash
curl -X POST 'http://localhost:8585/inbounds?name=reality1&security=reality&protocol=vless&network=tcp&port=443&sni=vk.com' \
  -H 'X-API-Key: change_me'
```

Создать клиента:

```bash
curl -X POST 'http://localhost:8585/clients?username=user1&inbound_id=1' \
  -H 'X-API-Key: change_me'
```

Получить VLESS URI:

```bash
curl -H 'X-API-Key: change_me' http://localhost:8585/clients/1/vless
```
