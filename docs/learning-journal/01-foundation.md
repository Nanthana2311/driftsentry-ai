# Learning Journal 01 — Foundation

Name: Nanthana  
Date:  

## 1. Liveness

Why should the liveness endpoint avoid checking PostgreSQL and Redis?

> Write your answer here.

## 2. Readiness

Why can the readiness endpoint return HTTP 503 even though the API process is alive?

> Write your answer here.

## 3. Relative browser API URL

Why does the dashboard call `/api/v1/...` instead of hard-coding `http://localhost:8000/api/v1/...`?

> Write your answer here.

## 4. Idempotent prediction events

Why will `(model_id, event_id)` be a unique database constraint?

> Write your answer here.

## 5. Background monitoring

Why should statistical monitoring execute in a worker instead of the prediction-ingestion request?

> Write your answer here.

## Practical observation

Liveness response without dependencies:

```json
Paste response here.
```

Readiness response without dependencies:

```json
Paste response here.
```

Readiness response with the Docker stack running:

```json
Paste response here.
```

## Design reflection

Concept learned:

> 

Why the project needs it:

> 

Alternative considered:

> 

How I tested it:

> 

One interview question I can now answer:

> 
