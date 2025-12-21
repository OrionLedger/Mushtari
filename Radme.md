# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**Moshtari** is an AI/ML pipeline for demand forecasting of products, services, and goods. The system integrates MongoDB for data persistence, multiple forecasting models (ARIMA, ARIMAX, XGBoost, Naive Baseline), and a modular infrastructure for logging and data operations.

## Development Commands

### Installation
```pwsh
pip install -r requirements.txt
```

**Note**: `requirements.txt` is incomplete. The project also requires:
- `loguru` (used in `infrastructure/logging/logger.py`)
- `pmdarima` (used in `src/train/arima.py`)
- `xgboost` (used in `src/train/xg_boost.py`)
- `scikit-learn` (used in `src/train/xg_boost.py`)
- `pandas` (used in `src/train/xg_boost.py` and `src/train/naive_baseline.py`)
- `numpy` (used in multiple training modules)
- `matplotlib` (imported in `src/train/xg_boost.py`)

### Running the Application
```pwsh
python main.py
```

The main script initializes a MongoDB connection, performs basic CRUD operations as a demonstration, and closes the connection.

### MongoDB Setup
The project expects MongoDB running locally at `mongodb://127.0.0.1:27017` with database name `orion_ledger`. Ensure MongoDB is running before executing `main.py`.

### Exploratory Work
Jupyter notebooks for exploratory data analysis are located in `notebooks/exploratory/`. Use these for data exploration and model experimentation.

## Architecture

### Directory Structure

```
├── infrastructure/       # Core infrastructure components
│   ├── DB/              # Database modules
│   ├── logging/         # Logging configuration using loguru
│   └── utils/           # HTTP request utilities
├── repo/                # Repository pattern implementation
├── src/                 # Source code for ML models
│   ├── train/           # Training modules for different models
│   └── evaluation/      # Model evaluation utilities
├── notebooks/           # Jupyter notebooks for exploration
│   ├── exploratory/     # Active exploratory notebooks
│   └── archived/        # Archived analysis notebooks
├── data/                # Data directory (gitignored)
└── main.py             # Application entry point
```

### Core Components

#### Infrastructure Layer (`infrastructure/`)
- **MongoDB Module** (`DB/mongo_db.py`): `Mongo_DB_Module` class handles all database operations (CRUD) with integrated logging
- **Logger** (`logging/logger.py`): Centralized logging using `loguru` with both console and file output. Logs stored in `logs/` directory with 10MB rotation and 7-day retention
- **HTTP Utils** (`utils/request.py`): Wrapper functions for GET, POST, PUT, DELETE requests using the `requests` library

#### Repository Pattern (`repo/`)
- **DBRepo** (`db_repo.py`): Abstraction layer over `Mongo_DB_Module`, providing a clean interface for data operations. Acts as the repository pattern implementation separating data access logic from business logic.

#### ML Models (`src/train/`)
The project supports multiple forecasting approaches:
- **ARIMA** (`arima.py`): Auto-tuning ARIMA using `pmdarima.auto_arima` with parameter search (p: 0-5, q: 0-5, d: 0-2)
- **ARIMAX** (`arimax.py`): Placeholder for ARIMA with exogenous variables (not yet implemented)
- **XGBoost** (`xg_boost.py`): Gradient boosting regressor with MAE objective, configurable estimators/depth/learning rate
- **Naive Baseline** (`naive_baseline.py`): Simple last-value forecasting for baseline comparison

#### Evaluation (`src/evaluation/`)
- `forecasting_eval.py`: Placeholder for model evaluation metrics (not yet implemented)

### Data Flow

1. **Data Ingestion**: Data is expected to be collected and stored in MongoDB via the `Mongo_DB_Module` or `DBRepo`
2. **Model Training**: Training scripts in `src/train/` consume data and produce forecasting models
3. **Persistence**: Models and data operations are logged via the centralized logger
4. **Evaluation**: Models should be evaluated using metrics from `src/evaluation/` (to be implemented)

### Key Design Patterns

- **Repository Pattern**: `DBRepo` abstracts database operations from business logic
- **Dependency Injection**: `DBRepo` accepts a `db_module` parameter allowing different DB implementations
- **Centralized Logging**: All modules use `get_logger(__name__)` from `infrastructure/logging/logger.py`
- **Module Isolation**: Infrastructure, data access, and ML models are separated into distinct layers

## Important Notes

### Database Configuration
- MongoDB URI and database name are hardcoded in `main.py`. For production use, move to environment variables or configuration files.
- Default connection: `mongodb://127.0.0.1:27017` with database `orion_ledger`

### Logging
- Logs are written to `logs/app.log` with DEBUG level
- Console output shows INFO level with colored formatting
- Log files are rotated at 10MB, compressed, and retained for 7 days

### Data Directory
- `data/` is gitignored and should contain raw data for model training
- Current structure: `data/raw/` for raw datasets

### Incomplete Components
- `src/train/train.py`: Empty file, intended to be a unified training orchestrator
- `src/train/arimax.py`: Empty file, ARIMAX implementation pending
- `src/evaluation/forecasting_eval.py`: Empty file, evaluation metrics pending
- `requirements.txt`: Missing several dependencies (see Installation section)

### Windows Environment
This project is being developed on Windows with PowerShell. File paths use Windows conventions (`\`), and line endings are CRLF (`\r\n`).
