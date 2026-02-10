# Refactoring and Fixing Roadmap

**Perspective**: Senior AI / ML Engineer
**Source**: SWOT Analysis of Demand Analysis Model project

This report outlines the prioritized tasks required to transform the current codebase into a production-ready system.

---

## 1. Critical Bug Fixes (Highest Priority)
These tasks address direct logic errors that currently cause runtime failures or incorrect behavior.

- [ ] **Fix String Comparisons**: Replace `is` and `is not` with `==` and `!=` for string literals in `src/preprocessing/clean_data.py`.
- [ ] **Fix Model Loader Logic**:
    - Update `serving/loaders/load_models.py` to handle the case where a model is not in the dictionary (implement `dict.get()` or a proper initialization check).
    - Correct `MODELS_DIR` pathing to point to actual model artifact locations.
- [ ] **Sync Repository Method Signatures**: Update `src/retrieving/get_product_sales.py` to pass arguments correctly to `CassandraRepository.get_sales_records`.
- [ ] **Fix Data Imputation**: Ensure `SimpleImputer` in `clean_data.py` returns a DataFrame with preserved column names (instead of a NumPy array) to prevent downstream breakage.

## 2. Architectural Integration
These tasks bridge the gaps between the currently disconnected modules.

- [ ] **Populate `main.py`**: Implement a proper application entry point that initializes the FastAPI server and database connections.
- [ ] **Wire API to Services**: Replace hardcoded return strings in `src/api/router/ml.py` with calls to appropriate functions in `serving/services/`.
- [ ] **Dependency Injection**: Refactor service modules (e.g., in `retrieving` and `serving`) to accept repository instances via parameters rather than instantiating them within default arguments.
- [ ] **Unified Logging**: Standardize all modules to use `infrastructure/logging/logger.py` (loguru) instead of the standard library `logging`.

## 3. Implementation of Missing Logic
Bringing functionality to the currently empty placeholder modules.

- [ ] **Complete Preprocessing Strategies**: Implement STL decomposition, Rolling curve, and Hampel filter logic in `clean_data.py`.
- [ ] **Implement Evaluation Metrics**: Flesh out `mean_absolute_error.py` and `squared_mean_error.py` in `src/evaluation/`.
- [ ] **Inference Layer**: Populate `./models/inference` logic for transforming raw inputs into model-ready tensors/DataFrames.

## 4. Stability and Dev-Ops
Enhancing the resilience and deployability of the system.

- [ ] **Global Error Handling**: Implement specialized Exception classes and middleware for FastAPI to catch and log database/model errors gracefully.
- [ ] **Containerization**: 
    - Create a `Dockerfile` for the application.
    - Create a `docker-compose.yml` to orchestrate ScyllaDB/Cassandra, MongoDB, and the API.
- [ ] **Input Validation**: Utilize `Pydantic` models in the API layer to validate request data before it reaches the processing/model layers.
- [ ] **Async Support**: Transition database retrieval in `repo/` and `src/retrieving/` to `async` methods to leverage FastAPI's concurrency.

## 5. Risk Mitigation (Technical Debt)
- [ ] **Remove "Not yet ready" Prints**: Replace all placeholder print statements with appropriate logging or `NotImplementedError` raises.
- [ ] **Standardize Return Types**: Ensure all data processing functions return explicit types (e.g., `pd.DataFrame`) and utilize type hints consistently.
