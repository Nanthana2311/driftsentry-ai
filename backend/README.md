# DriftSentry backend

FastAPI service and statistical monitoring engine.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn driftsentry_api.main:app --reload
```

Application code uses a `src/` layout so tests import the installed package rather than accidentally importing files from the repository root.
