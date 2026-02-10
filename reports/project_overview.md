# Project Overview Report

## 1. Project Structure
The project follows a modular structure intended to separate concerns, though the implementation is currently incomplete.

### Directory Layout
- **`./src`**: Core application logic.
    - **`api`**: Contains FastAPI router (`ml.py`) for serving predictions and forecasts.
    - **`evaluation`**: Intended for model evaluation metrics (currently empty placeholders).
    - **`preprocessing`**: Data cleaning and transformation logic.
    - **`retrieving`**: Logic to fetch data from the data layer.
    - **`train`**: Model training scripts (XGBoost).
- **`./models`**: Implementation of various forecasting algorithms (ARIMA, ARIMAX, Naive Baseline).
- **`./serving`**: Service layer that orchestrates model loading and execution.
- **`./repo`**: Data access layer (Repository pattern) interacting with Cassandra.
- **`./infrastructure`**: Infrastructure-level configurations (databases, logging, utility helpers).
- **`requirements.txt`**: Project dependencies.
- **`main.py`**: Intended entry point (currently empty).

## 2. Modules and Construction

### API Layer (`src/api`)
- Uses `FastAPI` to define a router.
- Endpoints `/api/forecast` and `/api/predict` are current placeholders.

### Models Layer (`models/forecasting`)
- Implements time-series models using `pmdarima` and `statsmodels`.
- Contains `arima.py`, `arimax.py`, and `naive_baseline.py`.

### Serving Layer (`serving`)
- **Loaders**: `load_models.py` uses a dictionary-based singleton pattern to cache loaded XGBoost boosters.
- **Services**: High-level services like `forecast_product.py` wrap the model logic for consumption by the API or other components.

### Data Retrieval (`src/retrieving`)
- Interacts with `CassandraRepository` to fetch sales data.

### Preprocessing (`src/preprocessing`)
- `clean_data.py`: Handles missing value imputation and outlier removal.

### Infrastructure Layer (`infrastructure`)
- **Configs**: Centralized connection management for `Cassandra` and `MongoDB`.
- **Logging**: Configures `loguru` with rotation, retention, and colored console output.
- **Utils**: Generic `requests` wrappers for internal or external API interaction.

### Repository Layer (`repo`)
- `CassandraRepository`: Manages connection to a Cassandra/Scylla database.

## 3. Dependencies
Key libraries used in the project:
- **Web Framework**: `fastapi`
- **Database**: `cassandra-driver`, `scylla-driver`, `pymongo`
- **Machine Learning**: `scikit-learn`, `xgboost`, `statsmodels`, `pmdarima`
- **Utilities**: `requests`, `loguru`, `pandas`, `numpy`
