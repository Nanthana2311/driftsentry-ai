# DriftSentry AI — Learning Path

The objective is not merely to make the application run. You should be able to explain every major design decision in an interview.

## Day 1: System foundation

Study:

1. **Liveness versus readiness**
   - Liveness asks whether the process is alive.
   - Readiness asks whether it can currently serve real traffic using its dependencies.
2. **Twelve-factor configuration**
   - Configuration and secrets come from the environment, not source code.
3. **API versioning**
   - `/api/v1` allows future incompatible changes without immediately breaking clients.
4. **Monorepo boundaries**
   - Frontend, backend, and SDK have independent responsibilities and tooling.
5. **Idempotency**
   - Retrying an event must not create duplicate production telemetry.

You should be able to answer:

- Why should `/health/live` not fail merely because PostgreSQL is temporarily unavailable?
- Why is `(model_id, event_id)` a better uniqueness rule than `event_id` alone?
- Why should expensive monitoring calculations not execute inside the ingestion request?
- Why do browser requests use relative API URLs?

## Days 2–3: Persistence and telemetry

Study:

- SQLAlchemy session lifecycle
- Alembic migrations
- Database indexes and unique constraints
- UUIDs versus sequential public IDs
- API-key hashing
- Batch request validation
- At-least-once delivery and idempotent consumers

Practical target: register the churn model and ingest a retried batch without duplicate rows.

## Days 4–6: Statistical monitoring

Study:

- Reference versus current distributions
- Population Stability Index
- Kolmogorov–Smirnov test
- Chi-square test
- Jensen–Shannon divergence
- Effect size versus statistical significance
- Minimum sample sizes
- Multiple hypothesis testing

Critical idea: a very large dataset can produce a tiny p-value for a practically unimportant change. Drift severity must not depend on p-values alone.

## Day 7: Asynchronous jobs

Study:

- Message queues and workers
- Retry policies
- Idempotent jobs
- Poison messages
- Job lifecycle state machines
- Why FastAPI `BackgroundTasks` is not a durable distributed queue

## Days 8–9: React dashboard

Study:

- TypeScript interfaces
- Server state versus local UI state
- Loading, empty, success, and error states
- Accessible data visualizations
- Why tables and exact numbers should accompany charts

## Day 10: Performance monitoring

Study:

- Delayed ground truth
- Precision, recall, F1, and ROC-AUC
- Class-prevalence shift
- Threshold-dependent versus ranking metrics
- Calibration

## Day 11: Grounded AI reports

Study:

- Structured LLM output
- Prompt injection boundaries
- Evidence packaging
- Citation validation
- Deterministic fallback behavior
- Faithfulness evaluation

Critical idea: the LLM explains stored evidence; it does not decide whether drift exists.

## Day 12: Evaluation

Study:

- Synthetic fault injection
- Detection rate and false-positive rate
- Regression tests for statistical software
- Reproducible random seeds
- Evaluation scenario manifests

## Days 13–14: Production and presentation

Study:

- CI quality gates
- Container health checks
- Structured logs and correlation IDs
- Threat modelling
- Architecture documentation
- Writing measurable resume bullets
- Demonstrating a failure and recovery story

## Learning journal format

After each session, record:

```text
Concept learned:
Why the project needs it:
Implementation decision:
Alternative considered:
How I tested it:
One interview question I can now answer:
```

This journal will later become strong README design notes and interview preparation.
