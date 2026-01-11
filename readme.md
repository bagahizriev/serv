## Docker (Xray + API)

### Сборка

```bash
docker build -t xray-api .
```

### Запуск

```bash
docker run -d --name xray-api \
  -p 8585:8585 \
  -e XRAY_API_KEY=change_me \
  -e XRAY_APPLY_DEBOUNCE_SECONDS=1.5 \
  -v xray_api_db:/var/lib/xray-api \
  -v xray_config:/etc/xray \
  xray-api
```

-   **XRAY_API_KEY** обязательна (передаётся в заголовке `X-API-Key`).
-   **XRAY_APPLY_DEBOUNCE_SECONDS** схлопывает частые изменения в одно применение конфига.
-   Том `xray_api_db` сохраняет БД.
-   Том `xray_config` сохраняет `config.json`.

### Пример запроса

```bash
curl -H 'X-API-Key: change_me' http://localhost:8585/inbounds
```
