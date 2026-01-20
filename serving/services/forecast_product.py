from models.forecasting.arima import start_arima_forecaster
from models.forecasting.arimax import start_arimax_forecaster

def forecast_with_arima(
        y,
        n_periods: int = 12,
        seasonal: bool = False
        ):
    model, y_pred, conf_int = start_arima_forecaster(
        y,
        n_periods,
        seasonal
        )
    return model, y_pred, conf_int

def forecast_with_arimax(
        y,
        X,
        n_periods: int = 12,
        seasonal: bool = False
        ):
    model, y_pred, conf_int = start_arimax_forecaster(
        y,
        X,
        n_periods,
        seasonal
        )
    return model, y_pred, conf_int
