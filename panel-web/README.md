## panel-web (Next.js)

Фронтенд для FastAPI панели.

### Требования

-   Node.js 18+

### Настройка

Скопируй переменные окружения:

```bash
cp .env.example .env.local
```

По умолчанию фронт ожидает API на `http://localhost:8000`.

### Запуск

```bash
npm install
npm run dev
```

Открой: `http://localhost:3000`

### Примечание

Backend (FastAPI) должен быть запущен (например через `panel/docker compose up`).
