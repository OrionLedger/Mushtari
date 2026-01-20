<img src='./thumpnail.jpg' alt='thumpnail.jpg'></img>

# Moshtari

## Project Overview

**Moshtari** is an AI/ML pipeline for demand forecasting of products, services, and goods. The system integrates MongoDB for data persistence, multiple forecasting models (ARIMA, ARIMAX, XGBoost, Naive Baseline), and a modular infrastructure for logging and data operations.

## Development Commands

### Installation
```pwsh
pip install -r requirements.txt
```

### Running the Application
```pwsh
python main.py
```

The main script initializes a MongoDB connection, performs basic CRUD operations as a demonstration, and closes the connection.

### Cassandra DB Setup
The project expects Cassandra running on an external docker container which can be connected to the system by container IP as a replica, in Cassandra module replicas ip, keyspace, needs to be spicified.

### Exploratory Work
Jupyter notebooks for exploratory data analysis are located in `notebooks/exploratory/`. Use these for data exploration and model experimentation.

## Architecture

### Directory Structure

```
├── infrastructure/       # Core infrastructure components
│   ├── config/              # Database modules
│   ├── logging/         # Logging configuration using loguru
│   └── monitoring/           # HTTP request utilities
├── repo/                # Repository pattern implementation
├── src/                 # Source code for ML models
│   ├── train/           # Training modules for different models
│   ├── evaluation/      # Model evaluation utilities
|   ├── preprocessing/
|   ├── retrieving/
|   ├── features
|   ├── utils
├── notebooks/           # Jupyter notebooks for exploration
│   ├── exploratory/     # Active exploratory notebooks
│   └── archived/        # Archived analysis notebooks
├── data/                # Data directory (gitignored)
└── main.py             # Application entry point
```

### Core Components

#### Infrastructure Layer (`infrastructure/`)
- **MongoDB Module** (`config/mongo_db.py`): `Mongo_DB_Module` class handles all database operations (CRUD) with integrated logging
- **Cassandra Module** (`config/cassandra_db.py`): `Cassandra_DB_Module` class handles all database operations (CRUD) with integrated logging
- **Logger** (`logging/logger.py`): Centralized logging using `loguru` with both console and file output. Logs stored in `logs/` directory

#### Repository Pattern (`repo/`)
- **DBRepo** (`mongodb_repo.py`) and (): Abstraction layer over `Mongo_DB_Module`, providing a clean interface for data operations. Acts as the repository pattern implementation separating data access logic from business logic.

#### ML Models (`src/train/`)
The project supports multiple forecasting approaches:
- **ARIMA** (`arima.py`): Auto-tuning ARIMA using `pmdarima.auto_arima` with parameter search (p: 0-5, q: 0-5, d: 0-2)
- **ARIMAX** (`arimax.py`): Placeholder for ARIMA with exogenous variables
- **XGBoost** (`xg_boost.py`): Gradient boosting regressor with MAE objective, configurable estimators/depth/learning rate
- **Naive Baseline** (`naive_baseline.py`): Simple last-value forecasting for baseline comparison

#### Evaluation (`src/evaluation/`)
- `forecasting_eval.py`: Placeholder for model evaluation metrics (not yet implemented)

### Data Flow

1. **Data Ingestion**: Data is expected to be collected and stored.
2. **Model Training**: Training scripts in `src/train/` consume data and produce forecasting / predicting models
3. **Persistence**: Models and data operations are logged via the centralized logger
4. **Evaluation**: Models should be evaluated using metrics from `src/evaluation/` (to be implemented)

### Key Design Patterns

- **Repository Pattern**: `DBRepo` abstracts database operations
- **Dependency Injection**: `DBRepo` accepts a `db_module` parameter allowing different DB implementations
- **Centralized Logging**: All modules use `get_logger(__name__)` from `infrastructure/logging/logger.py`
- **Module Isolation**: Infrastructure, data access, and ML models are separated into distinct layers

## Important Notes

### Database Configuration
- MongoDB URI and database name. For production use, move to environment variables or configuration files. Default connection: `mongodb://127.0.0.1:27017` with database `mushtari` (Deprecated)

- CassandraDB URI and keyspace name. which by default use 3 sepereated replicas each on different machine/container/ ... etc on the same network, needs a password and a username which can be setted as environment variables, and need to set a keyspace to operate on.

### Logging
- Logs are written to `logs/app.log` with DEBUG level
- Console output shows INFO level with colored formatting
- Log files are rotated at 10MB, compressed, and retained for 7 days

### Data Directory
- `data/` is gitignored and should contain raw data for model training
- Current structure: `data/raw/` for raw datasets

### Incomplete Components
- `src/train/train.py`: Empty file, intended to be a unified training orchestrator
- `src/evaluation/forecasting_eval.py`: Empty file, evaluation metrics pending

### Windows Environment
This project is being developed on Windows with PowerShell. File paths use Windows conventions (`\`), and line endings are CRLF (`\r\n`).

### Next Steps
1. Make an API and models Loaders
2. Containerize the service
3. Make data Models and schema validation
4. Creating Autotmatic batches training pipeline