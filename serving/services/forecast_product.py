from repo.cassandra_repo import CassandraRepository
from src.retrieving.get_product_sales import get_product_sales
from models.forecasting.arima import start_arima_forecaster

def forecast_product(product_id: int, horizon: int):
    repo = CassandraRepository()

    data = get_product_sales(
        product_id=product_id,
        columns=["sales"],
        repo=repo
    )

    y = [float(r["sales"]) for r in data]

    model, y_pred, conf_int = start_arima_forecaster(
        y=y,
        steps=horizon
    )

    return {
        "product_id": product_id,
        "horizon": horizon,
        "forecast": y_pred.tolist()
    }
