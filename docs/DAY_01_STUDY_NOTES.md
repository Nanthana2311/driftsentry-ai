# DriftSentry AI — Day 1 Study Notes

## 1. The project in one sentence

**DriftSentry monitors a deployed machine-learning model, detects when production data or model quality changes, and creates an incident supported by statistical evidence.**

## 2. The real-world problem

Training and deploying a model is not the end of an ML system's life.

Imagine that a churn model was trained in January. At that time:

- 30% of customers used fibre internet;
- the median monthly charge was ₹1,000;
- all payment methods belonged to four known categories.

Six months later, production traffic may look different:

- 60% of customers use fibre internet;
- the median monthly charge is ₹1,500;
- a new payment method appears;
- `TotalCharges` is missing for many customers.

The API can still return HTTP 200 and produce predictions, but those predictions may be less reliable because the model is seeing data different from its training experience.

DriftSentry will compare expected data with current production data, measure the differences, and notify an ML engineer when the differences are important.

## 3. A simple analogy

Think of a deployed ML model as a student who prepared using one syllabus.

- **Training data:** the syllabus used for preparation.
- **Production data:** the questions in the real examination.
- **Data drift:** the examination starts asking very different kinds of questions.
- **Model degradation:** the student's marks decrease.
- **DriftSentry:** a teacher who compares the syllabus with the examination, measures the differences, and reports what changed.

## 4. What you completed today

Today you built and verified the **foundation**, not the drift-detection engine itself.

You successfully:

1. Enabled and verified WSL 2.
2. Installed Docker Desktop.
3. Verified Docker by running the `hello-world` container.
4. Downloaded the project's required container images.
5. Created the local `.env` configuration file.
6. Started four services with Docker Compose.
7. Opened the React dashboard.
8. Verified that FastAPI was alive.
9. Verified that PostgreSQL and Redis were ready.
10. Ran backend tests.
11. Ran Python linting.
12. Ran strict Python type checking.
13. Ran TypeScript type checking.
14. Created a successful production frontend build.

This is important engineering work. Before adding ML logic, we made sure that the system can run predictably and that errors can be detected early.

## 5. The four running services

### 5.1 Frontend — React and TypeScript

The frontend is the dashboard visible at:

```text
http://localhost:5173
```

Its future responsibilities include displaying:

- registered models;
- prediction traffic;
- drifting features;
- monitoring runs;
- incidents;
- benchmark results.

Today, the dashboard only shows foundation information and checks whether the backend API is alive.

### 5.2 Backend — FastAPI and Python

The backend runs at:

```text
http://localhost:8000
```

It receives requests, validates data, communicates with infrastructure, and will eventually execute DriftSentry's business rules.

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

### 5.3 PostgreSQL — persistent database

PostgreSQL will permanently store:

- model registrations;
- feature definitions;
- prediction events;
- delayed ground-truth labels;
- reference profiles;
- drift metrics;
- monitoring runs;
- incidents and reports.

The database container is running today, but the application tables will be created during Day 2 using SQLAlchemy and Alembic.

### 5.4 Redis — fast queue infrastructure

Redis will support background jobs.

For example, when 10,000 prediction events need analysis, the API should not make the user wait while it computes every statistic. The API will submit a job, and a worker will process it separately.

Redis is running and its connection is checked today. The monitoring worker itself has not been implemented yet.

## 6. How the current system communicates

```text
Browser
   |
   | opens the dashboard
   v
React frontend :5173
   |
   | GET /api/v1/health/live
   v
FastAPI backend :8000
   |
   +---- checks PostgreSQL
   |
   +---- checks Redis
```

The frontend calls a relative URL such as:

```text
/api/v1/health/live
```

During development, Vite proxies that request to FastAPI. This is better than placing `http://localhost:8000` in browser code because the same frontend can later work behind a production domain without source-code changes.

## 7. Docker concepts

### Docker image

An image is a packaged blueprint containing an operating-system layer, runtime, dependencies, and application files.

Examples downloaded today:

- `python:3.12-slim`
- `node:22-alpine`
- `postgres:16-alpine`
- `redis:7-alpine`

### Docker container

A container is a running instance of an image.

Analogy:

- Image = class or blueprint
- Container = object or running instance

### Dockerfile

A Dockerfile contains instructions for building one image. DriftSentry has separate Dockerfiles for the Python backend and React frontend.

### Docker Compose

Docker Compose starts and connects multiple containers using one configuration file:

```text
compose.yaml
```

The command:

```powershell
docker compose up --build
```

means:

1. build application images if needed;
2. create the containers;
3. create a private network;
4. start PostgreSQL and Redis;
5. wait for their health checks;
6. start the backend;
7. start the frontend;
8. display combined logs.

## 8. Environment configuration

You created `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

The `.env` file stores configuration that can vary between environments, such as database addresses and external API keys.

Important rule:

**Commit `.env.example`, but never commit a real `.env` containing secrets.**

This is called environment-based or twelve-factor configuration.

## 9. Liveness versus readiness

### Liveness

Endpoint:

```text
/api/v1/health/live
```

Question answered:

> Is the FastAPI process alive and capable of responding?

Liveness intentionally does not check PostgreSQL or Redis. If the database is temporarily unavailable, restarting a healthy API repeatedly may make the failure worse.

### Readiness

Endpoint:

```text
/api/v1/health/ready
```

Question answered:

> Can this service currently handle real work using all required dependencies?

Your result was:

```json
{
  "status": "ready",
  "checks": {
    "postgres": "up",
    "redis": "up"
  }
}
```

If PostgreSQL is unavailable, the API can still be alive while readiness returns HTTP 503. A load balancer can use readiness to temporarily stop sending traffic to that instance.

## 10. Quality checks you ran

### Pytest

Command:

```powershell
docker compose exec backend pytest
```

Result:

```text
2 passed
```

Pytest executes automated tests. The existing tests verify the API's liveness metadata and root documentation response.

### Ruff

Command:

```powershell
docker compose exec backend ruff check .
```

Ruff detects Python style problems, unused imports, suspicious code, and common mistakes.

### mypy

Command:

```powershell
docker compose exec backend mypy src
```

mypy checks Python type annotations without running the application. It helps detect cases such as passing a string where a number is expected.

### TypeScript compiler

Command:

```powershell
docker compose exec frontend npm run typecheck
```

TypeScript provides static type checking for JavaScript-based frontend code.

### Vite production build

Command:

```powershell
docker compose exec frontend npm run build
```

Vite transformed the React source into optimized HTML, CSS, and JavaScript files suitable for production deployment.

## 11. Important ML-monitoring vocabulary

### Prediction telemetry

A record describing what happened during inference, usually including:

- model ID and version;
- event ID;
- timestamp;
- input features;
- predicted class;
- prediction probability.

### Reference distribution

A statistical description of the data considered normal, often created from training or validation data.

### Current or monitoring window

A recent group of production events, such as the latest 1,000 predictions or the previous 24 hours.

### Data drift

The distribution of model inputs changes:

```text
Pproduction(X) differs from Preference(X)
```

Example: monthly charges become much higher than they were in training data.

### Prediction drift

The distribution of model outputs changes.

Example: a model previously predicted 20% churn but now predicts 55% churn.

Prediction drift is a warning signal, but it does not automatically prove that the model is wrong.

### Concept drift

The relationship between inputs and the correct outcome changes:

```text
Pproduction(Y | X) differs from Preference(Y | X)
```

Detecting real performance degradation normally requires ground-truth labels.

### Incident

An actionable record grouping important failed checks. It includes severity, affected features, evidence, status, and investigation notes.

## 12. Why event ingestion must be idempotent

A client may retry a request because its network connection failed before it received the response. The server might already have stored the event.

DriftSentry will enforce uniqueness using:

```text
(model_id, event_id)
```

This means the same event can be retried safely without producing duplicate telemetry. `event_id` alone is insufficient because two different models could legitimately use the same client-generated event ID.

## 13. Why monitoring belongs in a worker

Prediction ingestion should be quick. Statistical monitoring can involve thousands of rows and many feature-level tests.

Running monitoring inside the ingestion request would cause:

- slow responses;
- request timeouts;
- lost work if the API restarts;
- difficulty retrying failures;
- reduced ingestion capacity.

Instead:

1. The API validates and stores events.
2. It submits a monitoring job to Redis.
3. A worker performs the expensive analysis.
4. Results are stored in PostgreSQL.
5. The dashboard reads the completed result.

## 14. The LLM's future role

The LLM will not decide whether drift exists.

Statistical Python code will calculate drift and create evidence records. The LLM will receive only those records and create a readable investigation report. Every numerical claim must cite an evidence ID.

This design prevents the project from becoming an unreliable chatbot wrapper.

## 15. What has not been built yet

Be accurate when discussing the current project. The following are planned, not yet implemented:

- model registration;
- feature schemas;
- database migrations and tables;
- prediction-event ingestion;
- Python telemetry SDK;
- reference profiling;
- statistical drift calculations;
- background worker;
- incident creation;
- delayed-label metrics;
- AI incident reports;
- drift-injection benchmark.

## 16. Interview-ready Day 1 summary

> I established the foundation for a production ML-monitoring platform using React, FastAPI, PostgreSQL, Redis, and Docker Compose. I implemented separate liveness and dependency-readiness checks, environment-based configuration, structured logging, and automated quality gates using Pytest, Ruff, mypy, TypeScript, and Vite. The next phase adds the model registry and idempotent telemetry ingestion.

Only use this statement after you understand each term in it.

## 17. Short answers to the Day 1 knowledge check

### Why should liveness avoid checking PostgreSQL and Redis?

Because liveness checks whether the API process itself is alive. A temporary dependency failure should not cause an otherwise healthy API to be restarted repeatedly.

### Why can readiness return HTTP 503 while the API is alive?

The process can answer requests but may be unable to perform real work because PostgreSQL or Redis is unavailable. HTTP 503 tells traffic-management systems not to send production work temporarily.

### Why does the frontend use `/api/v1/...`?

A relative URL works through the Vite development proxy and can later work behind a production domain. Hard-coding localhost would break after deployment and can create browser-origin problems.

### Why use a unique `(model_id, event_id)` constraint?

It prevents duplicate events when a client retries while still allowing different models to use the same event ID.

### Why use a worker for drift analysis?

Drift calculations can be slow and retryable. A worker keeps ingestion responsive and allows jobs to continue independently from browser or API requests.

## 18. Suggested study session

### First 20 minutes

Review:

- image versus container;
- Dockerfile versus Docker Compose;
- the four DriftSentry services.

### Next 20 minutes

Review:

- frontend request flow;
- FastAPI responsibility;
- PostgreSQL responsibility;
- Redis and worker responsibility.

### Next 15 minutes

Review:

- liveness;
- readiness;
- why your readiness response proves dependency connectivity.

### Final 15 minutes

Explain aloud without reading:

1. What problem DriftSentry solves.
2. What each of the four containers does.
3. What tests and type checks accomplished.
4. What is already built and what is still planned.

If you cannot explain one section, reread only that section rather than the entire document.

## 19. Self-check questions

1. Can an ML API return HTTP 200 while its predictions become less reliable?
2. What is the difference between an image and a container?
3. Why do we need PostgreSQL?
4. What future job will Redis support?
5. What is the difference between liveness and readiness?
6. Why does data drift not automatically prove model degradation?
7. Which component should compute expensive monitoring statistics?
8. Is the drift engine already implemented?

### Answer key

1. Yes. Technical availability does not guarantee prediction quality.
2. An image is a blueprint; a container is a running instance.
3. To persist model, telemetry, monitoring, evidence, and incident data.
4. Queuing monitoring work for a background worker.
5. Liveness checks the process; readiness checks its ability to serve real work with dependencies.
6. Inputs can change while model accuracy remains acceptable; labels are needed to measure actual performance.
7. A background monitoring worker.
8. No. Day 1 established and verified the system foundation.
