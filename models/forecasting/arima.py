import pandas as pd
from pmdarima import auto_arima

def start_arima_forecaster(y, n_periods, seasonal=False):
    """
    Starts the ARIMA forecaster.
    
    Args:
        y: The time series data.
        n_periods: The number of periods to forecast.
        seasonal: Whether the time series is seasonal.
    
    Returns:
        The ARIMA model, the forecast, and the confidence interval.
    """
    model = auto_arima(
        y, 
        start_p=0,
        start_q=0,
        max_p=5,
        max_q=5,
        max_d=3,
        seasonal=seasonal,
        stepwise=True,
        trace=True,
        suppress_warnings=True
    )
    sm_model = model.to_statsmodels()
    y_pred = sm_model.predict(n_periods=12, return_conf_int=True)
    print ("Model Residuals: ", sm_model.resid())
    print(sm_model.summary())

    # Forecast with pmdarima (correct way)
    y_pred, conf_int = model.predict(n_periods=n_periods, return_conf_int=True)

    print("Model Residuals:", model.resid())
    print(model.summary())

    return model, y_pred, conf_int
