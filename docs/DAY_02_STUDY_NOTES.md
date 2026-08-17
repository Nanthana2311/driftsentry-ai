# DriftSentry AI — Day 2 Study Notes

## 1. Day 2 result

DriftSentry can now register a binary-classification model, validate its feature schema, save both in PostgreSQL, generate a secret ingestion key, reject duplicate versions, and retrieve registered models without exposing secrets.

Implemented endpoints:

```text
POST /api/v1/models
GET  /api/v1/models
GET  /api/v1/models/{model_id}
```

## 2. Why a model registry is needed

Before accepting prediction telemetry, DriftSentry must know:

- which model produced the prediction;
- which version is running;
- what task the model performs;
- which features it expects;
- how the client is authenticated.

The model registry is a catalogue of that metadata. The MVP does not store the trained `.joblib` model itself.

## 3. Relational database fundamentals

### Table

A table stores one type of entity. DriftSentry now has `models` and `feature_definitions` tables.

### Row

One row is one record. A row in `models` represents one registered model version.

### Column

A column defines one stored property, such as `name`, `version`, or `created_at`.

### Primary key

`models.id` is a UUID primary key. It uniquely identifies one model row.

### Foreign key

`feature_definitions.model_id` references `models.id`. This associates every feature with its parent model.

### Unique constraint

```text
UNIQUE(name, version)
```

This prevents `customer-churn` version `1.0.0` from being registered twice while still allowing version `2.0.0`.

```text
UNIQUE(model_id, name)
```

This prevents duplicate feature names inside one model while allowing different models to use the same feature name.

### Cascade delete

```text
ON DELETE CASCADE
```

Deleting a model also deletes only its associated feature definitions, preventing orphan records.

## 4. SQLAlchemy ORM

ORM means Object-Relational Mapping. It maps Python classes to relational tables.

```text
RegisteredModel   → models
FeatureDefinition → feature_definitions
```

A `RegisteredModel` Python object can be added to a SQLAlchemy session, and SQLAlchemy translates that operation into SQL for PostgreSQL.

Important distinction:

- The ORM model describes the schema to Python.
- The Alembic migration actually creates that schema in the database.

## 5. Alembic migrations

A migration is a version-controlled database change.

The first DriftSentry revision is:

```text
20260816_01
```

It creates:

- `models`;
- `feature_definitions`;
- primary, foreign, and unique constraints;
- an index on `feature_definitions.model_id`.

Alembic also creates:

```text
alembic_version
```

That table records the current revision. Therefore, restarting the backend does not create the same tables again.

### Upgrade and downgrade

- `upgrade()` applies the change.
- `downgrade()` reverses it.

The backend starts with:

```text
alembic upgrade head
```

`head` means the newest available revision.

## 6. Async database migration lesson

SQLAlchemy uses an asynchronous database connection, but Alembic's migration body is synchronous. The correct bridge is:

```text
Async connection → connection.run_sync(...) → Alembic migration
```

Using `async with` on Alembic's synchronous transaction object produced:

```text
TypeError: _ProxyTransaction does not support the asynchronous context manager protocol
```

The fix placed configuration and migration execution inside a synchronous function passed to `run_sync`.

This debugging experience demonstrates an important idea: an asynchronous application may still need to call synchronous library APIs through an explicit bridge.

## 7. Request validation with Pydantic

`ModelCreate` is the request contract for model registration.

It validates:

- model-name format and length;
- version format;
- supported task type;
- at least one and at most 200 features;
- feature-name format;
- supported feature data types;
- duplicate feature names, ignoring case.

Invalid input returns:

```text
422 Unprocessable Entity
```

Validation occurs before business logic writes to PostgreSQL.

## 8. Application layers

The feature is separated into layers.

### Route layer

File:

```text
api/routes/models.py
```

Responsibilities:

- define HTTP paths and methods;
- accept validated request schemas;
- convert domain errors into HTTP responses;
- return response schemas.

### Dependency layer

File:

```text
api/dependencies.py
```

FastAPI dependency injection provides one asynchronous database session to the request.

### Service layer

File:

```text
services/model_registry.py
```

Responsibilities:

- execute the registration use case;
- generate credentials;
- construct model and feature objects;
- commit or roll back the transaction;
- list and retrieve models.

### Persistence layer

Files:

```text
db/models/registry.py
db/session.py
```

Responsibilities:

- describe database mappings;
- create asynchronous sessions;
- execute SQL through SQLAlchemy.

### Schema layer

File:

```text
schemas/models.py
```

Responsibilities:

- validate request data;
- define safe response shapes;
- ensure secrets are not accidentally serialized.

This separation makes each layer easier to understand, test, and change.

## 9. Registration request flow

```text
Client
  ↓ POST /api/v1/models
FastAPI route
  ↓ validate JSON with Pydantic
ModelRegistryService
  ↓ generate key and ORM objects
SQLAlchemy session
  ↓ INSERT inside transaction
PostgreSQL
  ↓ commit
Response schema
  ↓ 201 Created + raw key once
Client
```

If PostgreSQL detects a duplicate `(name, version)`, SQLAlchemy raises an integrity error. The service rolls back the transaction, and the route returns `409 Conflict`.

## 10. Secure ingestion keys

A registration creates a key similar to:

```text
ds_live_<random-token>
```

DriftSentry stores:

- a short visible prefix;
- a 64-character HMAC-SHA256 digest.

It does not store the raw key.

### Why not store the raw key?

If a database leak exposed raw keys, an attacker could immediately send fake telemetry. A one-way digest reduces that risk.

### Why use a pepper?

A pepper is an application secret combined with the key during HMAC calculation. It is stored in environment configuration, separate from database records.

### Verification

When a client later supplies an ingestion key:

1. Compute its HMAC digest using the pepper.
2. Compare it with the stored digest.
3. Use a constant-time comparison to reduce timing leakage.

The raw key is returned only once during registration. List and get endpoints return neither the raw key nor its digest.

## 11. HTTP status codes used

### 201 Created

A new model version was registered successfully.

### 404 Not Found

The requested model UUID does not exist.

### 409 Conflict

The same model name and version already exist.

### 422 Unprocessable Entity

The JSON was readable, but it violated the request schema—for example, an empty feature list.

## 12. Automated tests

The complete suite now has seven tests.

Model-registry tests verify:

- successful registration;
- raw key returned only during registration;
- database stores a digest instead of raw key;
- duplicate version returns 409;
- list and get do not expose secrets;
- duplicate feature names return 422;
- unknown UUID returns 404.

The tests use temporary in-memory SQLite storage for fast, isolated API checks. The migration was separately verified against the real PostgreSQL container.

This provides two types of confidence:

- fast application tests;
- real database migration verification.

## 13. Docker development lesson

The backend uses a `src/` package layout. The Docker image contains an installed package, while development mounts the current source folder.

Without:

```text
PYTHONPATH=/app/src
```

Python imported the older installed package from `site-packages`, even though the reload watcher noticed file changes.

The solution makes the mounted source path take priority. Migration files are also mounted during development so fixes do not require a full dependency rebuild.

## 14. Manual verification completed

You verified:

```text
GET /api/v1/models → one persisted customer-churn model
POST duplicate      → 409
POST empty features → 422
```

PostgreSQL confirmed:

- model row exists;
- task and status are stored;
- key prefix is stored;
- HMAC digest length is 64;
- three related feature rows exist.

## 15. Interview-ready explanation

> I implemented a versioned model registry using FastAPI, Pydantic, asynchronous SQLAlchemy, PostgreSQL, and Alembic. A model registration saves model metadata and ordered feature definitions in one transaction. Composite unique constraints prevent duplicate model versions and features, while foreign keys enforce ownership. Registration returns a random ingestion key once and stores only an HMAC-SHA256 digest. The API maps validation, conflict, and missing-resource cases to 422, 409, and 404 responses, and the behaviour is covered by isolated API tests plus a real PostgreSQL migration check.

## 16. Self-check

1. Why is `(name, version)` unique instead of only `name`?
2. What is the difference between an ORM model and a migration?
3. What does `model_id` do in `feature_definitions`?
4. What happens to features when their model is deleted?
5. Why is the raw ingestion key returned only once?
6. Which layer converts `ModelAlreadyExistsError` into HTTP 409?
7. Why did we need `run_sync` in the Alembic environment?
8. Why did mounted source code require `PYTHONPATH=/app/src`?

## 17. Day 3 preview

The next feature is idempotent prediction-event ingestion. A registered model will use its ingestion key to send batches containing:

- event ID;
- event time;
- feature values;
- prediction;
- probability.

The unique pair `(model_id, event_id)` will make client retries safe without duplicating telemetry.
