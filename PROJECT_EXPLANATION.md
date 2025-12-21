# Demand Analysis Model - Project Explanation

## Table of Contents
1. [Project Structure](#project-structure)
2. [End-to-End Execution Flow](#end-to-end-execution-flow)
3. [Deep Dive: arima.py](#deep-dive-arimapy)
4. [How to Modify Safely](#how-to-modify-safely)
5. [Runbook](#runbook)
6. [Open Questions](#open-questions)

---

## 1. Project Structure

### Top-Level Overview

```
Demand_Analysis_Model/
├── data/                      # Data directory (gitignored)
│   └── raw/                  # Raw CSV data files
│       ├── train.csv         # Training dataset (~17MB, 913K rows)
│       ├── test.csv          # Test dataset (~975KB, 45K rows)
│       └── Daily Demand...   # Additional forecasting data
│
├── infrastructure/           # Core infrastructure components
│   ├── DB/                  # MongoDB database module
│   │   └── mongo_db.py     # CRUD operations for MongoDB
│   ├── logging/            # Logging configuration
│   │   └── logger.py       # Loguru-based logging setup
│   └── utils/              # Utility functions
│       └── request.py      # HTTP request wrappers
│
├── repo/                    # Repository pattern implementation
│   └── db_repo.py          # Abstraction layer over DB operations
│
├── src/                     # Source code for ML models
│   ├── train/              # Training modules
│   │   ├── arima.py        # ★ ARIMA forecasting (focus file)
│   │   ├── arimax.py       # ARIMAX (empty - not implemented)
│   │   ├── xg_boost.py     # XGBoost regression model
│   │   ├── naive_baseline.py # Naive baseline forecasting
│   │   └── train.py        # (empty - orchestration placeholder)
│   └── evaluation/
│       └── forecasting_eval.py  # (empty - metrics placeholder)
│
├── notebooks/              # Jupyter notebooks for exploration
│   ├── exploratory/       # Active analysis notebooks
│   │   ├── train.ipynb    # Training data exploration
│   │   └── test.ipynb     # Test data exploration
│   └── archived/          # Old notebooks
│
├── main.py                # Entry point (MongoDB demo)
├── requirements.txt       # Python dependencies (incomplete)
├── __init__.py           # Package initialization
└── Readme.md             # Project documentation

```

### Role of Each Component

**Infrastructure Layer (`infrastructure/`)**
- **MongoDB Module**: Provides database connectivity and CRUD operations with integrated logging
- **Logger**: Centralized logging using loguru with file rotation (10MB, 7-day retention)
- **HTTP Utils**: Wrapper functions for RESTful API calls

**Repository Pattern (`repo/`)**
- Abstracts database operations from business logic
- Provides clean interface for data persistence

**ML Models (`src/train/`)**
- **arima.py**: Auto-tuning ARIMA for time series forecasting ★ PRIMARY FOCUS
- **xg_boost.py**: Gradient boosting regressor for demand prediction
- **naive_baseline.py**: Last-value baseline for comparison

**Data Layer (`data/raw/`)**
- Training dataset: 913,000 rows with columns: date, store, item, sales
- Test dataset: 45,000 rows (2018-01-01 to 2018-03-31)
- Time range: 2013-01-01 to 2017-12-31 (train), 2018 Q1 (test)

---

## 2. End-to-End Execution Flow

### Entry Points

**Current State**: The project has **no integrated pipeline**. There are three isolated components:

1. **main.py** - MongoDB demonstration (not connected to ML models)
2. **src/train/arima.py** - Standalone ARIMA function
3. **notebooks/** - Interactive exploratory analysis

### Expected Inputs

**Data Format** (from notebooks analysis):
- **CSV Files**: `train.csv`, `test.csv`
- **Columns**: 
  - `date`: Date string (YYYY-MM-DD)
  - `store`: Integer (1-10)
  - `item`: Integer (1-50)
  - `sales`: Integer (target variable)

**ARIMA Function Input**:
```python
y_train: pandas Series or array-like
        Time series data (univariate)
        Expected to be stationary or near-stationary
```

### Expected Outputs

**ARIMA Function Returns**:
- Statsmodels ARIMA model object
- **Side effects**: 
  - Prints residuals to console
  - Prints model summary statistics
  - **WARNING**: Generates predictions but doesn't return them!

**Current Limitations**:
- No file outputs (no CSV, no plots saved)
- No metrics persistence
- No model serialization
- No integrated pipeline from data loading → training → evaluation → prediction

---

## 3. Deep Dive: arima.py

### File Location
`src/train/arima.py`

### Purpose
Implements automatic ARIMA parameter selection and model training for univariate time series forecasting.

---

### Function: `train_arima_forecaster`

#### Function Signature
```python
def train_arima_forecaster(y_train):
```

#### Parameters

| Parameter | Type | Description | Expected Format |
|-----------|------|-------------|-----------------|
| `y_train` | pandas Series, numpy array, or list | Univariate time series training data | Numeric values, ideally stationary or detrended |

**Parameter Expectations**:
- **No explicit type checking** - relies on pmdarima/statsmodels to handle validation
- **No missing value handling** - will fail if NaN/None present
- **No frequency information** - assumes uniform time intervals
- **No date index requirement** - uses positional indexing

#### Returns

| Return Value | Type | Description |
|-------------|------|-------------|
| `sm_model` | `statsmodels.tsa.arima.model.ARIMAResults` | Fitted ARIMA model object |

**Return Value Details**:
- Converted from pmdarima wrapper to statsmodels native format
- Can be used for further predictions via `model.predict(n_periods=...)`
- Retains all model diagnostics and fitted parameters

#### Side Effects

1. **Console Output**:
   - Line 19: Prints model residuals (errors on training data)
   - Line 20: Prints full model summary (coefficients, diagnostics, AIC/BIC)

2. **Internal Computations**:
   - Line 18: Generates 12-period forecast (stored in `y_pred` but **not returned!**)
   - Grid search over (p, q) parameter space

3. **No File I/O**:
   - Does not save model to disk
   - Does not save predictions or plots
   - Does not log to file (only console)

---

### ARIMA Logic Implementation

#### Step 1: Automatic Parameter Selection (Lines 5-16)

```python
model = auto_arima(
    y=y_train, 
    start_p=0,
    start_q=0,
    max_p=5,
    max_q=5,
    max_d=2,
    seasonal=False,
    stepwise=True,
    trace=True,
    suppress_warnings=True
)
```

**What Happens**:
1. **Grid Search**: Tests ARIMA(p,d,q) combinations where:
   - `p` (AR order): 0 to 5
   - `d` (differencing): 0 to 2
   - `q` (MA order): 0 to 5

2. **Stepwise Algorithm** (`stepwise=True`):
   - **Not exhaustive search** - uses heuristic to reduce search space
   - Starts with simple models (low p, q)
   - Iteratively adds complexity if AIC improves
   - **Faster but may miss global optimum**

3. **Selection Criterion**:
   - Uses **AIC (Akaike Information Criterion)** by default
   - Lower AIC = better model (balances fit vs. complexity)

4. **Differencing Selection** (`max_d=2`):
   - Tests d=0 (no differencing), d=1 (first difference), d=2 (second difference)
   - Automatically determines stationarity needs
   - **No explicit stationarity test** shown in code

5. **Seasonality** (`seasonal=False`):
   - **Does not model seasonal patterns** (daily/weekly/monthly cycles)
   - For seasonal data, this is a **major limitation**

**Inference**: The function assumes the user has already handled seasonality elsewhere or that data is non-seasonal.

#### Step 2: Model Conversion (Line 17)

```python
sm_model = model.to_statsmodels()
```

**Why Conversion?**:
- `pmdarima.auto_arima` returns a pmdarima wrapper object
- Converts to native `statsmodels` ARIMA model for broader compatibility
- Allows use of statsmodels-specific methods and diagnostics

#### Step 3: Prediction Generation (Line 18)

```python
y_pred = sm_model.predict(n_periods=12, return_conf_int=True)
```

**What Happens**:
- Generates **12-step-ahead forecast**
- `return_conf_int=True`: Returns confidence intervals along with point predictions
- **Problem**: `y_pred` is computed but **never used or returned**!
- **Result structure** (if returned): Tuple of (predictions, confidence_intervals)

**Bug/Design Flaw**: This line serves no purpose in current implementation.

#### Step 4: Diagnostics Output (Lines 19-20)

```python
print("Model Residuals: ", sm_model.resid())
print(sm_model.summary())
```

**`sm_model.resid()`**:
- Returns array of residuals: actual - predicted for each training point
- Used to check for:
  - Autocorrelation (should be white noise)
  - Heteroscedasticity (constant variance)
  - Normality (for valid confidence intervals)

**`sm_model.summary()`**:
- Comprehensive statistical summary:
  - Model order (p, d, q)
  - Coefficient estimates with standard errors
  - AIC, BIC scores
  - Log-likelihood
  - Statistical tests (Ljung-Box, Jarque-Bera, etc.)

---

### Time Series Preparation

#### What the Function **Does NOT** Do:

1. **Date Indexing**:
   - No `pd.DatetimeIndex` requirement
   - No frequency inference
   - **Risk**: If data has irregular intervals, predictions will be wrong

2. **Frequency Specification**:
   - No `freq` parameter passed to ARIMA
   - Assumes uniform time steps
   - **Risk**: Multi-frequency data (e.g., skipping weekends) will cause errors

3. **Missing Value Handling**:
   - No `fillna()` or `dropna()`
   - Will crash if `y_train` contains NaN
   - **User must pre-clean data**

4. **Stationarity Testing**:
   - No ADF (Augmented Dickey-Fuller) test
   - Relies on `auto_arima` internal differencing
   - **Risk**: May over-difference if d selection is suboptimal

5. **Outlier Detection**:
   - No outlier removal or treatment
   - Extreme values will distort parameters

#### What **auto_arima** Does Internally (Inferred):

1. Tests for stationarity using KPSS or ADF test (default pmdarima behavior)
2. Applies differencing up to `max_d=2` if non-stationary
3. Fits each (p,d,q) combination using MLE (Maximum Likelihood Estimation)
4. Compares models using AIC

---

### Train/Test Split Method

**Current Implementation**: **NO SPLIT INSIDE FUNCTION**

- Function receives `y_train` as input
- Assumes splitting was done **before calling** the function
- **No validation set** used for early stopping or hyperparameter tuning

**Expected Usage** (from notebooks):
```python
# User must manually split:
train_size = int(0.8 * len(data))
y_train = data[:train_size]
y_test = data[train_size:]

model = train_arima_forecaster(y_train)
predictions = model.predict(n_periods=len(y_test))
```

**Missing Best Practice**: No time series cross-validation (e.g., rolling window, expanding window)

---

### Metrics Used

**None within function!**

The function does **not** compute or return any evaluation metrics.

**What Should Be Added**:
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- MAPE (Mean Absolute Percentage Error)
- MASE (Mean Absolute Scaled Error)

**Workaround** (user must implement):
```python
from sklearn.metrics import mean_absolute_error

model = train_arima_forecaster(y_train)
y_pred = model.predict(n_periods=len(y_test))
mae = mean_absolute_error(y_test, y_pred)
```

---

### Prediction/Forecast Generation

**How Forecasts Are Made**:

1. **Point Forecasts**:
   ```python
   model.predict(n_periods=12)  # 12 steps ahead
   ```

2. **With Confidence Intervals**:
   ```python
   model.predict(n_periods=12, return_conf_int=True)
   # Returns: (predictions, conf_int_array)
   ```

3. **Forecast Object** (alternative):
   ```python
   model.forecast(steps=12)  # Same as predict
   ```

**Where Predictions Are NOT Saved**:
- Line 18 computes predictions but doesn't return them
- No CSV export
- No plot generation
- **User must manually call predict() after function returns**

---

### Dependencies

#### External Libraries Used

1. **numpy** (`import numpy as np`)
   - **Usage**: Implicitly used by pmdarima/statsmodels
   - **Not directly called** in this function

2. **pmdarima** (`from pmdarima import auto_arima`)
   - **Purpose**: Automatic ARIMA order selection
   - **Key Feature**: Stepwise search algorithm
   - **Version Sensitivity**: API changed significantly pre-v1.0
   - **Installation**: `pip install pmdarima`

3. **statsmodels** (Indirect via `to_statsmodels()`)
   - **Purpose**: Core ARIMA estimation engine
   - **Classes Used**: `statsmodels.tsa.arima.model.ARIMA`
   - **Installation**: `pip install statsmodels`

#### Dependency Chain

```
arima.py
  └─> pmdarima.auto_arima
       ├─> statsmodels.tsa.arima.model.ARIMA  (fitting)
       ├─> statsmodels.tsa.stattools  (stationarity tests)
       └─> scipy.optimize  (MLE optimization)
```

---

### Potential Bugs / Pitfalls

#### 1. Data Leakage
**Issue**: None currently, but **high risk** if user calls function on full dataset
```python
# WRONG:
model = train_arima_forecaster(full_data)  # Includes test data!

# CORRECT:
model = train_arima_forecaster(train_only_data)
```

#### 2. Date Handling / Frequency Issues
**Issue**: No date index enforcement
```python
# Will fail silently with wrong intervals:
irregular_dates = pd.Series([1, 2, 3], index=['2020-01-01', '2020-01-05', '2020-01-10'])
model = train_arima_forecaster(irregular_dates)  # Treats as uniform intervals!
```

**Fix**: User must resample data:
```python
data = data.asfreq('D')  # Daily frequency
data = data.fillna(method='ffill')  # Forward fill gaps
```

#### 3. Non-Stationarity Assumptions
**Issue**: `max_d=2` may be insufficient for highly trending data
```python
# Example: Exponential growth
model = train_arima_forecaster(exponential_series)  # May need log transformation first
```

**Fix**: Pre-process data:
```python
y_train_log = np.log(y_train)
model = train_arima_forecaster(y_train_log)
# Remember to exponentiate predictions!
```

#### 4. Model Saving/Loading Issues
**Issue**: No serialization provided
```python
# User must manually save:
import pickle
with open('arima_model.pkl', 'wb') as f:
    pickle.dump(sm_model, f)

# Loading:
with open('arima_model.pkl', 'rb') as f:
    loaded_model = pickle.load(f)
```

**Risk**: Statsmodels models may not serialize perfectly across versions

#### 5. Hardcoded Paths
**None** - Function has no file I/O

#### 6. Seasonal Data Mishandling
**Issue**: `seasonal=False` ignores seasonal patterns
```python
# For monthly data with yearly seasonality:
# Should use SARIMA instead:
from statsmodels.tsa.statespace.sarimax import SARIMAX
model = SARIMAX(y_train, order=(1,1,1), seasonal_order=(1,1,1,12))
```

#### 7. Unused Prediction (Line 18)
**Issue**: `y_pred` is computed but never returned
**Fix**: Either return it or remove the line

#### 8. Missing Error Handling
**No try-except blocks** - Will crash on:
- NaN values
- Insufficient data (need at least p+d+q+1 obs)
- Non-numeric data

---

## 4. How to Modify Safely

### Change Data Source

**Current**: No data loading in `arima.py` (user must load externally)

**To add CSV loading**:
```python
# Add at top of file:
import pandas as pd

def train_arima_forecaster(csv_path, target_column='sales'):
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    y_train = df[target_column]
    # ... rest of function
```

**Where to change**:
- Add parameters to function signature (Line 4)
- Insert data loading before `auto_arima` call (Line 5)

### Tune ARIMA Parameters

**Location**: Lines 6-10

**To change max AR/MA orders**:
```python
model = auto_arima(
    y=y_train,
    start_p=1,      # ← Start search at p=1 instead of 0
    start_q=1,      # ← Start search at q=1 instead of 0
    max_p=10,       # ← Increase from 5
    max_q=10,       # ← Increase from 5
    max_d=2,        # Keep same
    seasonal=False,
    stepwise=True,
    trace=True,
    suppress_warnings=True
)
```

**To enable seasonality**:
```python
model = auto_arima(
    y=y_train,
    start_p=0,
    start_q=0,
    max_p=5,
    max_q=5,
    max_d=2,
    seasonal=True,              # ← Enable
    m=12,                       # ← Seasonal period (e.g., 12 for monthly)
    start_P=0, max_P=2,        # ← Seasonal AR
    start_Q=0, max_Q=2,        # ← Seasonal MA
    stepwise=True,
    trace=True,
    suppress_warnings=True
)
```

### Change Forecasting Horizon

**Location**: Line 18

```python
# Change from 12 to desired steps:
y_pred = sm_model.predict(n_periods=30, return_conf_int=True)  # 30 periods

# To return predictions:
return sm_model, y_pred  # ← Add to Line 22
```

### Change Evaluation Metrics

**Location**: Add before return statement (after Line 20)

```python
# Compute metrics on training data:
from sklearn.metrics import mean_squared_error, mean_absolute_error

y_train_pred = sm_model.predict_in_sample()  # In-sample predictions
train_mae = mean_absolute_error(y_train, y_train_pred)
train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))

print(f"Training MAE: {train_mae:.4f}")
print(f"Training RMSE: {train_rmse:.4f}")
```

**To compute test metrics** (requires passing test data):
```python
def train_arima_forecaster(y_train, y_test=None):
    # ... existing code ...
    
    if y_test is not None:
        y_pred = sm_model.predict(n_periods=len(y_test))
        test_mae = mean_absolute_error(y_test, y_pred)
        print(f"Test MAE: {test_mae:.4f}")
    
    return sm_model
```

### Common Mistakes to Avoid

1. **Don't modify training data inside function** without documenting
   - Bad: `y_train = np.log(y_train)` without user knowledge
   - Good: Add parameter `log_transform=False`

2. **Don't hardcode file paths**
   - Bad: `df = pd.read_csv('C:/Users/...')`
   - Good: Pass as function parameter

3. **Don't suppress all warnings**
   - Current `suppress_warnings=True` hides convergence issues
   - Better: `suppress_warnings=False, error_action='warn'`

4. **Don't assume data is clean**
   - Add validation:
     ```python
     if y_train.isnull().any():
         raise ValueError("Training data contains missing values")
     ```

5. **Don't ignore returned predictions** (Line 18 issue)
   - Either return them or remove the line

---

## 5. Runbook

### Exact Commands to Run

**IMPORTANT**: There is **no working end-to-end pipeline** in the current codebase.

#### Option 1: MongoDB Demo (main.py)
```powershell
# Ensure MongoDB is running on localhost:27017
python main.py
```
**What it does**: 
- Connects to MongoDB
- Inserts/reads a test record
- Closes connection
- **Does NOT train models or make predictions**

#### Option 2: Use ARIMA Function Manually (Python REPL)
```powershell
python
```
```python
# In Python shell:
import pandas as pd
import sys
sys.path.append(r'C:\Users\lenovo\Desktop\Demand_Analysis_Model')

from src.train.arima import train_arima_forecaster

# Load data
df = pd.read_csv(r'C:\Users\lenovo\Desktop\Demand_Analysis_Model\data\raw\train.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter one store/item combination
subset = df[(df['store'] == 1) & (df['item'] == 1)]
subset = subset.set_index('date').sort_index()
y_train = subset['sales']

# Train model
model = train_arima_forecaster(y_train)

# Make predictions
predictions = model.predict(n_periods=90)  # 90-day forecast
print(predictions)
```

#### Option 3: Run Jupyter Notebooks
```powershell
jupyter notebook notebooks/exploratory/train.ipynb
```
**What it does**:
- Loads train.csv
- Performs EDA (histograms, date range analysis)
- Extracts date features (year, month, day, dayofweek)
- **Does NOT train ARIMA model** (only exploration)

### Assumptions Made

1. **Data is pre-split** into train.csv and test.csv
2. **MongoDB is installed** and running (for main.py)
3. **Python dependencies are installed**:
   ```powershell
   pip install pmdarima statsmodels xgboost scikit-learn pandas numpy matplotlib seaborn loguru pymongo jupyter
   ```
4. **No integrated pipeline exists** - each component must be used separately
5. **Windows environment** with PowerShell

### Proposed End-to-End Workflow

**Since no pipeline exists, here's what SHOULD be built**:

```python
# pseudocode for missing pipeline
import pandas as pd
from src.train.arima import train_arima_forecaster

# 1. Load data
train_df = pd.read_csv('data/raw/train.csv')
test_df = pd.read_csv('data/raw/test.csv')

# 2. Preprocess
train_df['date'] = pd.to_datetime(train_df['date'])
train_df = train_df.set_index('date').sort_index()

# 3. Train model per store/item
results = {}
for store in range(1, 11):
    for item in range(1, 51):
        subset = train_df[(train_df['store'] == store) & (train_df['item'] == item)]
        y_train = subset['sales']
        
        model = train_arima_forecaster(y_train)
        predictions = model.predict(n_periods=90)
        
        results[(store, item)] = predictions

# 4. Save results
# ... not implemented ...
```

---

## 6. Open Questions

### Data-Related
1. **What is the business context?**
   - What products are being forecasted?
   - Why 10 stores and 50 items?
   - What is the unit of 'sales' (units sold, revenue)?

2. **Why is data gitignored?**
   - Is it proprietary?
   - How do new users get access to data?

3. **What happened to Daily Demand Forecasting Orders.csv?**
   - Only 6KB file
   - Not used in any notebooks
   - Purpose unclear

### Model-Related
4. **Why no seasonal ARIMA?**
   - Retail data typically has weekly/monthly seasonality
   - Current implementation ignores this

5. **What is the target forecast horizon?**
   - Line 18 uses 12 periods but context is unclear
   - Test data covers 90 days (Q1 2018)

6. **Why convert from pmdarima to statsmodels?**
   - Adds extra step
   - Loses some pmdarima convenience methods

### Architecture-Related
7. **What is the intended deployment?**
   - Batch predictions?
   - Real-time API?
   - Scheduled jobs?

8. **Why MongoDB for time series data?**
   - SQL or time series DB (InfluxDB) might be more appropriate

9. **What is ingestion_strategy (referenced in __init__.py)?**
   - Import fails: `from .src.ingestion.ingestion_strategy import DataCollector`
   - File doesn't exist

### Implementation Gaps
10. **When will train.py be implemented?**
    - Currently empty
    - Should orchestrate training pipeline

11. **What metrics should forecasting_eval.py contain?**
    - MAE, RMSE, MAPE?
    - Need stakeholder input

12. **Why is arimax.py empty?**
    - Was it planned?
    - Should it be removed?

### Next Steps to Investigate
- [ ] Talk to stakeholders about forecast requirements
- [ ] Check if seasonal patterns exist in data (via ACF/PACF plots)
- [ ] Decide on evaluation metrics (business-driven)
- [ ] Determine deployment architecture
- [ ] Fix incomplete requirements.txt
- [ ] Implement end-to-end pipeline in train.py
- [ ] Add model serialization/versioning
- [ ] Add logging to arima.py (currently only prints)

---

## Summary

**Project State**: **Early development** with isolated components but no integrated pipeline.

**arima.py Strengths**:
- Clean automatic parameter selection via pmdarima
- Flexible model output (statsmodels compatible)
- Simple API

**arima.py Weaknesses**:
- No seasonality support
- No data validation
- No metrics computation
- Unused prediction generation (Line 18)
- No error handling
- No model persistence

**Critical Next Steps**:
1. Implement end-to-end pipeline
2. Add seasonal ARIMA support
3. Implement evaluation metrics
4. Add model saving/loading
5. Fix requirements.txt
6. Document expected data format
7. Add data preprocessing module
