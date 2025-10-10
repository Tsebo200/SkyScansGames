# Deploying the SkyScansGames backend to Render

This folder contains a Dockerfile and a `render.yaml` blueprint to deploy the FastAPI backend quickly to Render with a persistent disk for the SQLite database.

## One-time setup

1. Push your branch to GitHub (or your Git provider).
2. In the Render dashboard, click New > Blueprint and point it at this repo.
3. Render will read `backend/render.yaml` and propose a service named `skyscans-backend`.
4. Click Apply. The first build will start automatically.

Alternatively, you can create a Web Service manually:
- Type: Web Service
- Environment: Docker
- Root directory: `backend/`
- Add a disk named `data`, mount path `/data`, size 3GB

## Environment variables

Set these in the Render service settings (or keep them from the blueprint):
- PORT=10000
- PYTHONUNBUFFERED=1
- DATABASE_URL=/data/skyscans_games.db
- ALLOWED_ORIGINS=comma-separated list of your frontend URLs
- RAWG_API_KEY=... (add in Render as Secret)
- STEAM_API_KEY=... (optional)
- OPENAI_API_KEY=... (optional)
- ANTHROPIC_API_KEY=... (optional)
- USE_LLM_INNOVATION=0 or 1
- API_CACHE_TTL=1800
- SEARCH_CACHE_TTL=600
- API_CACHE_DISABLE_EXPIRY=0 (set to 1 to serve cache regardless of expiry during outages)

## Persistent data

- The SQLite database lives at `/data/skyscans_games.db`, stored on the attached disk.
- Render restarts won’t lose data; scaling to multiple instances is not recommended with SQLite. For scale, migrate to Postgres and remove the disk.

## Health checks

- The app exposes `GET /api/health` which returns 200 when healthy. You can configure Render’s health check to that path if desired.

## CORS

- CORS origins are controlled via the `ALLOWED_ORIGINS` env var (comma-separated). Update it to include your frontend URL (e.g., `https://your-frontend.onrender.com`).

## Logs

- Gunicorn + Uvicorn logs are visible in Render Logs. You can add structured logging later if needed.

## Frontend changes

- In production, set `REACT_APP_API_BASE` in the frontend to your Render backend URL (e.g., `https://skyscans-backend.onrender.com`).
- Remove/ignore the CRA proxy in production; it’s for local dev only.

## Upgrades / rollbacks

- Render keeps previous deploys; you can roll back from the UI.
- The blueprint enables `autoDeploy: true` for changes to the blueprint or code. You can disable it in Render if desired.
