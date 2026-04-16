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
| **Repository Pattern** | Standardised `BaseRepo` interface for seamless DB switching (Cassandra, SQL, Mongo) |
| **High-Performance ETL** | Optimized data ingestion via Cassandra batch operations and Prefect orchestration |
| **Flexible Querying** | Support for complex range filters (`__gte`, `__lte`) across all storage backends |
| **Experiment Tracking** | MLflow integration for tracking runs, parameters, and metrics |

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **API Framework** | FastAPI · Uvicorn · Pydantic |
| **ML / Forecasting** | XGBoost · scikit-learn · pmdarima · statsmodels |
| **Experiment Tracking** | MLflow |
| **Databases** | Cassandra · MongoDB · PostgreSQL (SQLAlchemy) |
| **Data Validation** | Pandera (Data Gatekeeper) |
| **Observability** | Prometheus · Loguru |
| **Data & Compute** | pandas · NumPy · matplotlib |
| **HTTP Client** | httpx · requests |
| **Testing** | pytest |
| **Containerisation** | Docker · Docker Compose |

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

- **Abstract Repository Pattern** — All data access flows through a unified `BaseRepo` contract (defined in `repo/base.py`), ensuring the system remains high-performing and database-agnostic.
- **Service Layer Orchestration** — `serving/services/` separates business logic from API concerns, handling model loading and forecasting in isolated units.
- **Batch Processing** — ETL loaders utilize `bulk_insert` via Cassandra `BatchStatement` for ultra-fast ingestion of historical records.
- **Suffix Filtering** — The repository layer supports Django-style suffix filters (`field__gte`, `field__lt`) for intuitive range queries without custom SQL boilerplate.
- **Singleton Model Cache** — `serving/loaders/load_models.py` ensures each XGBoost model is loaded into memory only once.
- **Component-Based Logging** — Standardised telemetry and logging via Loguru and Prometheus.

---

## Project Structure

```
Moshtari/
├── main.py                          # FastAPI app entry point
├── Dockerfile                       # Production container image
├── docker-compose.yml               # UAT orchestration
├── requirements.txt                 # Python dependencies
├── .dockerignore                    # Docker build exclusions
│
├── api/                             # -- API Layer --
│   ├── router/
│   │   ├── demand.py                # Prediction & batch endpoints
│   │   ├── data.py                  # ETL Pipeline endpoints
│   │   └── kpi.py                   # Market Fit reporting
│   └── models/
│       ├── demand_models.py         # Prediction schemas
│       └── data_models.py           # ETL schemas
│
├── etl/                             # -- ETL Pipeline (Prefect) --
│   ├── flows/
│   │   └── etl_flow.py              # Main orchestrator
│   ├── gatekeeper/
│   │   ├── schemas.py               # Pandera rules
│   │   └── validator.py             # Validation task
│   └── load/
│       └── database.py              # Multi-DB loader
│
├── infrastructure/                  # -- Cross-Cutting --
│   ├── monitoring/
│   │   └── telemetry.py             # Metrics utility
│   └── ...
└── ...
```

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

### ML & Prediction (`/api`)
- `POST /api/predict`: Synchronous prediction with thread-offloading.
- `POST /api/predict/batch`: Asynchronous prediction for multiple products.
- `GET /api/forecast`: Cached ARIMA forecast with TTL background revalidation.
- `PATCH /api/train/xgboost`: Trigger model training.

### Data & ETL (`/api/data`)
- `POST /api/data/extract`: Trigger Prefect ETL pipeline as a background task. Supports `--db-type` (cassandra, mongo, postgres).

### Business KPIs (`/api/kpi`)
- `POST /api/kpi/market-fit`: Calculate Forecast Bias, Inventory Accuracy, etc.

### Monitoring
- `GET /health`: Liveness probe for UAT/Production.
- `GET /metrics`: Prometheus formatted application metrics.

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

### Docker Compose (UAT)
Recommended for spinning up the full environment (API, Cassandra, MLflow).
```powershell
docker-compose up --build
```

### Manual Docker Run
```powershell
docker build -t moshtari:latest .
docker run -d -p 8000:8000 moshtari:latest
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

- [x] **Standardise Data Access Layer** — Implemented `BaseRepo` abstract contract for all repository implementations.
- [x] **Optimize Cassandra Load** — Replaced row-by-row insertion with high-performance `BatchStatement` operations.
- [x] **Unified Query Interface** — Added suffix-based range filtering for flexible data retrieval.
- [x] **Stabilise Environment** — Resolved versioning conflicts between statsmodels, pandera, and scipy.
- [ ] **Next Gen Forecasting** — Integrate Transformer-based models for long-horizon demand planning.
- [ ] **Advanced Monitoring** — Add automated model drift detection and retraining triggers (Drift Guard).

---

<div align="center">

**Moshtari** · Part of the [OrionLedger](https://github.com/orionledger) Platform

</div>