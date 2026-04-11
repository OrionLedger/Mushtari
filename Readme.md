<img src='./thumpnail.jpg' alt='Moshtari — Demand Analysis Model'></img>

<div align="center">

# Moshtari  مشتري

**AI-powered demand forecasting microservice**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](#tech-stack)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](#tech-stack)
[![XGBoost](https://img.shields.io/badge/XGBoost-FF6600?logo=xgboost&logoColor=white)](#tech-stack)
[![MLflow](https://img.shields.io/badge/MLflow-0194E2?logo=mlflow&logoColor=white)](#tech-stack)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](#docker-deployment)
[![License](https://img.shields.io/badge/License-Private-red)](#)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [Docker Deployment](#docker-deployment)
- [Testing](#testing)
- [Configuration](#configuration)
- [Roadmap](#roadmap)

---

## Overview

**Moshtari** (مشتري — Arabic for *customer*) is a production-oriented demand forecasting microservice built for the **OrionLedger** platform. It ingests historical sales data, trains time-series and regression models, and exposes prediction & forecasting endpoints through a RESTful API.

### Key Capabilities

| Capability | Description |
|---|---|
| **Demand Prediction** | XGBoost regression on engineered lag features to predict upcoming demand |
| **Time-Series Forecasting** | ARIMA / ARIMAX models with automatic parameter tuning via `pmdarima` |
| **On-Demand Retraining** | Trigger model retraining per product through a single API call |
| **Experiment Tracking** | MLflow integration for tracking runs, parameters, and metrics |
| **Containerised Deployment** | Production-ready Dockerfile with non-root user and Uvicorn server |

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **API Framework** | FastAPI · Uvicorn · Pydantic |
| **ML / Forecasting** | XGBoost · scikit-learn · pmdarima · statsmodels |
| **Experiment Tracking** | MLflow |
| **Databases** | Apache Cassandra / ScyllaDB (primary) · MongoDB (legacy) |
| **Data & Compute** | pandas · NumPy · matplotlib |
| **Logging** | Loguru |
| **HTTP Client** | httpx · requests |
| **Testing** | pytest |
| **Containerisation** | Docker |

---

## Architecture

```
                ┌──────────────────────────────────────────────────────────────┐
                │                     FastAPI Application                      │
                │  main.py  ──►  /docs (Swagger UI)                           │
                └────────────────────────┬─────────────────────────────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │    API Router Layer  │
                              │   api/router/demand  │
                              └──────────┬──────────┘
                                         │
                    ┌────────────────────┼─────────────────────┐
                    │                    │                      │
          ┌─────────▼────────┐ ┌────────▼─────────┐ ┌─────────▼────────┐
          │  Predict Service │ │ Forecast Service │ │  Train Service   │
          │  (XGBoost infer) │ │  (ARIMA forecast)│ │ (XGBoost train)  │
          └─────────┬────────┘ └────────┬─────────┘ └─────────┬────────┘
                    │                    │                      │
          ┌─────────▼────────┐ ┌────────▼─────────┐           │
          │  Model Loaders   │ │   Forecasting    │           │
          │ (Singleton cache)│ │  Models (ARIMA)  │           │
          └─────────┬────────┘ └──────────────────┘           │
                    │                                          │
             ┌──────▼──────────────────────────────────────────▼──┐
             │              Data Retrieval & Preprocessing        │
             │   src/retrieving  ·  src/preprocessing  ·  src/   │
             └──────────────────────────┬─────────────────────────┘
                                        │
                             ┌──────────▼──────────┐
                             │   Repository Layer   │
                             │  (Cassandra / Mongo) │
                             └──────────────────────┘
```

### Design Patterns

- **Repository Pattern** — `CassandraRepository` abstracts all database I/O, keeping business logic DB-agnostic.
- **Service Layer** — `serving/services/` orchestrates model loading, data retrieval, and prediction in cohesive units.
- **Singleton Model Cache** — `serving/loaders/load_models.py` ensures each model is loaded into memory only once.
- **Dependency Injection** — Services accept an optional `repo` parameter, making them fully testable with mocks.
- **Centralised Logging** — All modules use `get_logger(__name__)` from `infrastructure/logging/logger.py`.

---

## Project Structure

```
Moshtari/
├── main.py                          # FastAPI app entry point (Uvicorn target)
├── Dockerfile                       # Production container image
├── requirements.txt                 # Python dependencies
├── .dockerignore                    # Docker build exclusions
│
├── api/                             # — API Layer —
│   ├── router/
│   │   └── demand.py                # FastAPI router: /api/predict, /forecast, /sales, /train
│   └── models/
│       └── demand_models.py         # Pydantic request/response schemas
│
├── serving/                         # — Service / Orchestration Layer —
│   ├── loaders/
│   │   └── load_models.py           # XGBoost model cache (singleton dict)
│   └── services/
│       ├── predict_product_demand.py # XGBoost inference pipeline
│       ├── forecast_product.py      # ARIMA forecasting pipeline
│       ├── train_xgboost_regressor_sales.py  # On-demand XGBoost training
│       └── add_records.py           # Insert sales records
│
├── models/                          # — ML Model Implementations —
│   ├── forecasting/
│   │   ├── arima.py                 # Auto-ARIMA forecaster (pmdarima)
│   │   ├── arimax.py                # ARIMAX with exogenous variables
│   │   └── naive_baseline.py        # Last-value baseline
│   └── inference/                   # (Reserved for inference artifacts)
│
├── src/                             # — Core Business Logic —
│   ├── train/
│   │   └── xg_boost.py             # XGBoost regressor training logic
│   ├── evaluation/
│   │   ├── mean_absolute_error.py   # MAE metric
│   │   └── squared_mean_error.py    # MSE / RMSE metric
│   ├── preprocessing/
│   │   ├── clean_data.py            # Missing-value imputation, outlier removal
│   │   ├── normalize_data.py        # Feature normalisation
│   │   └── transform_data.py        # Feature transformations
│   ├── retrieving/
│   │   └── get_product_sales.py     # Fetch sales data from repository
│   ├── features/                    # (Reserved for feature engineering)
│   └── utils/                       # (Reserved for shared utilities)
│
├── repo/                            # — Data Access Layer —
│   └── cassandra_repo.py            # CassandraRepository (Cassandra / ScyllaDB)
│
├── infrastructure/                  # — Cross-Cutting Concerns —
│   ├── configs/
│   │   ├── cassandra_db.py          # Cassandra connection manager
│   │   └── mongo_db.py              # MongoDB connection manager (legacy)
│   ├── logging/
│   │   └── logger.py                # Loguru config (console + rotating file)
│   ├── monitoring/                  # (Reserved for health checks & metrics)
│   └── utils/
│       └── request.py               # HTTP request wrapper (httpx / requests)
│
├── tests/                           # — Test Suite —
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── unit/
│   │   ├── test_evaluation.py
│   │   ├── test_preprocessing.py
│   │   ├── test_retrieving.py
│   │   ├── test_services.py
│   │   └── test_train.py
│   └── integration/
│       └── test_api.py
│
├── notebooks/                       # — Exploratory Analysis —
│   ├── exploratory/                 # Active experimentation notebooks
│   ├── archived/                    # Archived / superseded notebooks
│   └── reports/                     # Notebook-generated reports
│
├── data/                            # — Data Directory (gitignored) —
│   ├── external/                    # Third-party datasets
│   ├── extracts/                    # Extracted / intermediate data
│   └── processed/                   # Cleaned, ready-to-train data
│
├── reports/                         # — Project Documentation —
│   ├── project_overview.md
│   ├── swot_analysis.md
│   └── refactoring_and_fixing_tasks.md
│
├── logs/                            # — Application Logs (gitignored) —
├── mlruns/                          # — MLflow Experiment Runs (gitignored) —
└── mlflow.db                        # — MLflow Tracking Store (gitignored) —
```

---

## Getting Started

### Prerequisites

- **Python** 3.11+
- **Apache Cassandra** or **ScyllaDB** instance (for primary data store)
- **MongoDB** (optional — legacy support)

### 1. Clone & Install

```powershell
git clone <repository-url>
cd Demand_analysis_model

# Create a virtual environment (recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MODELS_DIR` | Directory for serialised model files | `./models/` |
| `CASSANDRA_HOST` | Cassandra cluster contact point(s) | — |
| `CASSANDRA_KEYSPACE` | Cassandra keyspace name | — |
| `CASSANDRA_USERNAME` | Cassandra auth username | — |
| `CASSANDRA_PASSWORD` | Cassandra auth password | — |
| `MONGO_URI` | MongoDB connection URI | `mongodb://127.0.0.1:27017` |

### 3. Run the API Server

```powershell
uvicorn main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**. The root `/` redirects to the interactive **Swagger UI** at `/docs`.

---

## API Reference

All endpoints are prefixed with `/api`.

### `GET /api/`
Returns a summary of all available endpoints.

### `POST /api/predict`
Predict demand for a product using a trained XGBoost model.

```json
{
  "product_id": 1,
  "features": ["lag_1", "lag_7", "month"],
  "start_date": "2026-01-01",
  "end_date": "2026-02-01"
}
```

### `GET /api/forecast?product_id=1&horizon=7`
Generate a time-series forecast using ARIMA.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `product_id` | `int` | required | Target product ID |
| `horizon` | `int` | `7` | Number of future steps to forecast |

### `POST /api/sales`
Insert a new sales record into the database.

```json
{
  "table_name": "Sales",
  "record": {
    "product_id": 1,
    "date": "2026-01-23",
    "sales": 15.5
  }
}
```

### `PATCH /api/train/xgboost`
Trigger on-demand retraining of the XGBoost model for a specific product.

```json
{
  "product_id": 1,
  "columns": ["sales", "price"],
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "test_size": 0.2
}
```

---

## Machine Learning Pipeline

### Forecasting Models

| Model | Module | Description |
|---|---|---|
| **Auto-ARIMA** | `models/forecasting/arima.py` | Automatic p, d, q selection via `pmdarima.auto_arima` (p: 0-5, q: 0-5, d: 0-2) |
| **ARIMAX** | `models/forecasting/arimax.py` | ARIMA with exogenous variables for incorporating external signals |
| **Naive Baseline** | `models/forecasting/naive_baseline.py` | Last-observation-carried-forward baseline |
| **XGBoost** | `src/train/xg_boost.py` | Gradient boosting regressor with MAE objective, configurable hyperparameters |

### Data Pipeline

```
Raw Sales Data (Cassandra)
       │
       ▼
  Retrieval  ──►  get_product_sales()
       │
       ▼
  Preprocessing
  ├── clean_data()        — impute missing values, remove outliers
  ├── normalize_data()    — scale features
  └── transform_data()    — engineer lag & temporal features
       │
       ▼
  Train / Evaluate
  ├── train_xg_boost_regressor()
  └── Evaluation metrics (MAE, MSE)
       │
       ▼
  Serialised Model  ──►  models/inference/
       │
       ▼
  Serving  ──►  load_models.py (singleton cache)  ──►  API Response
```

### Experiment Tracking

MLflow is integrated for experiment tracking. Runs, parameters, and metrics are stored in the local `mlruns/` directory with a SQLite backend (`mlflow.db`).

---

## Docker Deployment

### Build

```powershell
docker build -t moshtari:latest .
```

### Run

```powershell
docker run -d `
  --name moshtari `
  -p 8000:8000 `
  -e CASSANDRA_HOST=<cassandra-host> `
  -e CASSANDRA_KEYSPACE=<keyspace> `
  -e CASSANDRA_USERNAME=<username> `
  -e CASSANDRA_PASSWORD=<password> `
  moshtari:latest
```

The container runs as a non-privileged `appuser` for security. The API is served by Uvicorn on port **8000**.

### Image Details

- **Base**: `python:3.11-slim`
- **Port**: `8000`
- **Entrypoint**: `uvicorn main:app --host 0.0.0.0 --port 8000`

---

## Testing

The project uses **pytest** with separate unit and integration test suites.

```powershell
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v
```

### Test Coverage

| Suite | File | Covers |
|---|---|---|
| Unit | `test_preprocessing.py` | Data cleaning, normalisation, transformation |
| Unit | `test_evaluation.py` | MAE, MSE metric calculations |
| Unit | `test_retrieving.py` | Sales data retrieval logic |
| Unit | `test_services.py` | Predict, forecast, and train services |
| Unit | `test_train.py` | XGBoost training pipeline |
| Unit | `test_mlflow_loader.py`| MLflow integration and tracking |
| Unit | `test_etl_flow.py` | ETL pipeline dispatcher logic |
| Integration | `test_api.py` | End-to-end API endpoint tests |

---

## Configuration

### Logging

Logging is handled by **Loguru** with dual output:

| Output | Level | Details |
|---|---|---|
| **Console** | `INFO` | Coloured, human-readable format |
| **File** | `DEBUG` | Rotated at 10 MB, compressed (zip), retained 7 days |

Log files are written to `logs/app.log`. The logger is thread-safe (`enqueue=True`).

### Database Setup

#### Cassandra / ScyllaDB (Primary)
The project expects Cassandra running externally (e.g., Docker containers). Configure with:
- **Replicas**: Multiple contact points across separate machines/containers on the same network
- **Authentication**: Username and password via environment variables
- **Keyspace**: Must be specified before first use

#### MongoDB (Legacy)
MongoDB support is retained for backward compatibility. Default connection: `mongodb://127.0.0.1:27017`, database: `mushtari`.

---

## Roadmap

- [ ] **Optimize Inference Endpoints** — Explore caching, batch inference, or async endpoints for high-throughput prediction requests.
- [ ] **Develop Data Gatekeeper** — Implement formal data validations (e.g., Pandera/Pydantic) upstream of ETL flows to secure the ingestion process.
- [ ] **Implement Usage Telemetry** — Centralize observability using Prometheus or OpenTelemetry for tracking usage of endpoints and pipelines.
- [ ] **Define Market Fit KPIs** — Draft metrics and KPI reporting outlining real-world effectiveness of forecasting outputs.
- [ ] **Execute UAT Environment** — Configure CI/CD automated test deployments to establish a verified User Acceptance Testing (UAT) workspace.

---

<div align="center">

**Moshtari** · Part of the [OrionLedger](https://github.com/orionledger) Platform

</div>