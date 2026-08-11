# DriftSentry AI — MVP Product Specification

## 1. Product statement

DriftSentry is a self-hostable ML reliability platform for teams operating tabular binary-classification models. It records prediction telemetry, detects data and model degradation, and produces incidents backed by inspectable evidence.

## 2. Primary user

**ML engineer at a small team** who has deployed a model but does not have a dedicated model-observability platform.

### Jobs to be done

- Know whether production inputs still resemble the model's training data.
- Discover broken or newly missing features before users report bad predictions.
- Understand which features changed and by how much.
- Track model quality after delayed ground-truth labels become available.
- Produce a concise incident report for engineers and non-technical stakeholders.

## 3. Demonstration model

The first integration is the existing customer-churn classifier. A simulator will replay stable traffic and then inject controlled changes such as:

- an increase in fibre-optic customers;
- a shift in monthly charges;
- missing `TotalCharges` values;
- an unseen payment category;
- a change in churn prevalence.

This produces a reproducible end-to-end demonstration without collecting real customer data.

## 4. MVP scope

### Included

1. One local workspace with multiple registered model versions.
2. Tabular binary-classification models.
3. HTTP batch ingestion and a Python SDK.
4. Reference profiles computed from CSV or Parquet data.
5. Fixed or manually triggered monitoring windows.
6. Numerical, categorical, schema, missingness, prediction, and performance checks.
7. Delayed ground-truth label ingestion.
8. Incident creation and lifecycle states.
9. A React dashboard.
10. Optional LLM reports with validated evidence citations.
11. A deterministic report fallback requiring no API key.
12. Controlled drift-injection evaluation.

### Explicitly excluded from the two-week MVP

- Multi-tenant billing and enterprise RBAC
- Kafka or high-volume streaming infrastructure
- Kubernetes
- Automated retraining
- Computer-vision or generative-model monitoring
- Causal claims about why drift occurred
- LoRA fine-tuning
- A complex agent framework used only for branding

## 5. Core terminology

- **Reference profile:** summary statistics representing expected input and prediction behavior.
- **Prediction event:** features, output, confidence, model version, and event time for one inference.
- **Monitoring window:** a bounded set of production events compared with the reference.
- **Drift signal:** a measured distributional or quality difference.
- **Incident:** one or more signals grouped into an actionable reliability problem.
- **Delayed label:** ground truth received after the original prediction.

## 6. Functional requirements

### FR-1 Model registry

A user can register a model name, version, task type, feature schema, and monitoring configuration. A model version has a stable UUID and a revocable ingestion key.

### FR-2 Idempotent event ingestion

The API accepts a batch of prediction events. `(model_id, event_id)` is unique, so client retries cannot create duplicate telemetry.

### FR-3 Reference profiling

The system computes counts, missing rates, quantiles, histogram bins, and categorical frequencies. The saved profile records the algorithm version used to create it.

### FR-4 Monitoring runs

A user can compare a production time window with the active reference profile. Runs are repeatable and store their configuration and results.

### FR-5 Drift detection

The engine returns metric value, threshold, status, effect information, sample counts, and machine-readable evidence for every evaluated feature.

### FR-6 Incidents

Failed checks are grouped into an incident with severity, state, title, affected features, and evidence links.

### FR-7 Delayed labels

Ground-truth labels can be linked to predictions by event ID. Performance metrics are computed only when adequate labelled samples are present.

### FR-8 Grounded report

The report generator receives evidence records with stable IDs. Every numerical claim must cite one or more evidence IDs. Unknown or unsupported explanations must be labelled as hypotheses.

### FR-9 Evaluation

A benchmark creates known drift scenarios and records which signals were expected and detected.

## 7. Non-functional requirements

- **Privacy:** demo data only; raw values are not sent to an LLM.
- **Reliability:** event ingestion is idempotent.
- **Reproducibility:** monitoring runs save algorithm and configuration versions.
- **Testability:** statistical functions are pure wherever practical.
- **Observability:** logs are structured and include request/run IDs.
- **Portability:** the complete local stack starts with Docker Compose.
- **Security:** secrets stay in environment variables and are never committed.

## 8. MVP success criteria

1. The churn API can log events through the SDK.
2. Stable simulated traffic produces no high-severity incident.
3. At least 8 of 10 initial injected failure scenarios are detected.
4. The benchmark reports false positives instead of hiding them.
5. Every incident links to stored metric evidence.
6. Every AI report citation resolves to evidence used for that report.
7. CI runs tests, linting, formatting checks, and type checks.
8. A new developer can start the project from the README.

## 9. Product risks

| Risk | Mitigation |
|---|---|
| Small windows make statistical tests noisy | Enforce minimum sample sizes and report `insufficient_data` |
| Many feature tests create false alerts | Apply effect thresholds and multiple-testing correction where appropriate |
| LLM invents causes | Send only summaries, require evidence IDs, validate citations, describe causes as hypotheses |
| Scope exceeds two weeks | Support binary classification first and defer streaming infrastructure |
| Demo looks synthetic | Integrate a real deployed churn model and clearly document controlled drift injection |
