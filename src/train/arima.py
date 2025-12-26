import pandas as pd
from pmdarima import auto_arima

def train_arima_forecaster(y_train, n_periods):
    model = auto_arima(
        y=y_train, 
        start_p=0,
        start_q=0,
        max_p=5,
        max_q=5,
        max_d=3,
        seasonal=False,
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
