import numpy as np

def naive_forecast(train, steps):
    return np.repeat(train.iloc[-1], steps)
