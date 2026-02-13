from serving.loaders.load_models import get_model
from src.retrieving.get_product_sales import get_product_sales
from repo.cassandra_repo import CassandraRepository
import xgboost as xgb

# Predict next value product demand using trained XGBoost model
def predict_product_demand(product_id, 
                           model_name="xgb_model", 
                           columns=None,
                           start_date=None,
                           end_date=None
    ):
    """
    Predicts the demand for a specific product.
    
    Args:
        product_id: The ID of the product to predict demand for.
        model_name: The name of the model to use for prediction.
        columns: The columns to use for prediction.
        start_date: The start date of the date range.
        end_date: The end date of the date range.
    
    Returns:
        A dictionary containing the prediction for the specified product.
    """
    model = get_model(model_name)
    data = get_product_sales(product_id, 
                            columns=columns, 
                            start_date=start_date, 
                            end_date=end_date
        )
    # dmatrix = xgb.DMatrix(data)
    predictions = model.predict(data)
    return predictions