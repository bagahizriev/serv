## Node (Xray + Agent API)

### Сборка

```bash
docker build -t xray-node .
```

### Запуск

```bash
docker run -d --name xray-node \
  -p 8585:8585 \
  -e XRAY_NODE_KEY=change_me \
  -e XRAY_PANEL_ALLOW_IPS=46.32.186.181,146.158.124.131 \
  -v xray_node_config:/etc/xray \
  xray-node
```

### Проверка

```bash
curl http://localhost:8585/health
```

### Применить config.json (делает панель)

Агент принимает полный config Xray и применяет его:

1. пишет во временный файл
2. проверяет `xray -test`
3. атомарно заменяет `/etc/xray/config.json`
4. перезапускает Xray через supervisor

Пример ручного запроса (для отладки):

```bash
curl -X POST http://localhost:8585/apply-config \
  -H 'X-Node-Key: change_me' \
  -H 'Content-Type: application/json' \
  -d '{"config":{"log":{"loglevel":"warning"},"inbounds":[],"outbounds":[{"protocol":"freedom"}]}}'
```
