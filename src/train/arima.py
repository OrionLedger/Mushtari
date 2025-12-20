# import numpy as np
# from pmdarima import auto_arima
# from statsmodels.stats.
# def train_arima_forecaster(y_train):
#     model = auto_arima(
#         y=y_train, 
#         start_p=0,
#         start_q=0,
#         max_p=5,
#         max_q=5,
#         max_d=2,
#         seasonal=False,
#         stepwise=True,
#         trace=True,
#         suppress_warnings=True
#     )
#     sm_model = model.to_statsmodels()
#     y_pred = sm_model.predict(n_periods=12, return_conf_int=True)
#     print ("Model Residuals: ", sm_model.resid())
#     print(sm_model.summary())

#     return sm_model


from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.metrics import mean_squared_error
