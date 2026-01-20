from typing import List
from repo.cassandra_repo import CassandraRepository
from src.train.xg_boost import train_xg_boost_regressor
from src.retrieving.get_product_sales import get_product_sales
from sklearn.model_selection import train_test_split
import pandas as pd
from os import environ

MODELS_DIR = environ.get("MODELS_DIR")
def train_xgboost_regressor(
        product_id,
        columns: List = ['sales'],
        start_date: str = None,
        end_date: str = None,
        repo = CassandraRepository(),
        test_size = 0.2
        ):
    data = get_product_sales(
        product_id,
        columns,
        start_date,
        end_date,
        repo
        )
    
    df = pd.DataFrame(data)
    df['sales'] = df['sales'].astype(float)
    X = df.drop(columns=['sales'])
    y = df['sales']
    X_sample = X.sample(frac=1, random_state=42)
    y_sample = y.sample(frac=1, random_state=42)
    X_train, X_eval, y_train, y_eval = train_test_split(
        X_sample, y_sample, test_size=test_size, random_state=42
    )
    X_test = df.drop(X_sample.index)
    y_test = df.loc[X_test.index, 'sales']

    
    model = train_xg_boost_regressor(
            X_train,
            y_train,
            X_eval,
            y_eval,
            X_test,
            y_test
        )
    model.save_model(f"{MODELS_DIR}xgboost_regressor_product_{product_id}.json")
    return model