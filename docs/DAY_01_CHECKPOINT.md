# Day 1 Checkpoint — System Foundation

## Objective

Understand the product boundary and establish a reproducible development environment before implementing ML functionality.

## What was implemented

- Product specification with measurable MVP success criteria
- Component and data-flow architecture
- Proposed relational data model
- FastAPI application using a `src/` package layout
- Environment-based typed configuration
- JSON container logging
- Separate liveness and readiness endpoints
- React/TypeScript dashboard connected through a relative `/api` route
- Docker Compose definitions for PostgreSQL, Redis, backend, and frontend
- Backend tests, linting, formatting checks, and strict type checking
- Frontend strict TypeScript check and production build

## Run the project

### Recommended: Docker

From the repository root:

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
docker compose up --build
```

**Linux/macOS**

```bash
cp .env.example .env
docker compose up --build
```

Open:

- http://localhost:5173
- http://localhost:8000/docs
- http://localhost:8000/api/v1/health/live
- http://localhost:8000/api/v1/health/ready

With PostgreSQL and Redis running, readiness should return HTTP 200 with both dependencies marked `up`.

### Quality checks through Docker

Keep the stack running, open a second terminal in the repository root, and run:

```powershell
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec backend mypy src
docker compose exec frontend npm run typecheck
docker compose exec frontend npm run build
```

You do not need to install Python or Node.js locally when using these commands.

### Optional backend checks without Docker

```bash
cd backend
pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
mypy src
```

## Files to study first

Read in this order:

1. `docs/PRODUCT_SPEC.md`
2. `docs/ARCHITECTURE.md`
3. `backend/src/driftsentry_api/main.py`
4. `backend/src/driftsentry_api/core/config.py`
5. `backend/src/driftsentry_api/api/routes/health.py`
6. `compose.yaml`
7. `frontend/vite.config.ts`
8. `frontend/src/api.ts`

Do not try to memorize every line. Identify each file's responsibility and the boundary between components.

## Knowledge check

Write answers in `docs/learning-journal/01-foundation.md`.

1. Why does `/health/live` avoid checking PostgreSQL and Redis?
2. Why can `/health/ready` return HTTP 503 while the API process is still healthy?
3. Why does frontend code call `/api/v1/...` instead of `http://localhost:8000/api/v1/...`?
4. Why will prediction ingestion need a unique `(model_id, event_id)` constraint?
5. Why should drift analysis run in a worker instead of inside the prediction-ingestion request?

## Practical exercise

1. Start only the backend without PostgreSQL or Redis.
2. Call both health endpoints.
3. Observe that liveness is HTTP 200 while readiness is HTTP 503.
4. Start the complete Docker stack.
5. Call readiness again and observe HTTP 200.
6. Record the result in the learning journal.

This controlled dependency failure is intentional. It demonstrates the different meanings of liveness and readiness.

## Day 1 completion criteria

- [ ] Dashboard loads.
- [ ] API documentation loads.
- [ ] Complete Docker stack reports ready.
- [ ] Backend tests pass.
- [ ] Frontend production build passes.
- [ ] Five knowledge-check answers are written in your own words.
- [ ] First Git commit is created.

Suggested commit:

```bash
git add .
git commit -m "chore: establish DriftSentry system foundation"
```

## Next checkpoint

Day 2 implements the first real domain capability: model registration, feature schemas, PostgreSQL ORM models, and Alembic migrations.
