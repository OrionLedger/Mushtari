from ... import get_logger
import pandas as pd
import numpy as np

logger = get_logger(__name__)

class Preprocessor:
    def __init__(self):
        pass
    def clean_comtrade_dateset(self, dataset):
        try:
            cleaned_data = dataset.dropna()
            
        except Exception as e:
            logger.exception(f"Data preprocessing failed: {e}")