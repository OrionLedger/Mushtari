from fastapi import APIRouter

router = APIRouter(prefix='/api' , tags=['ML'])

@router.get('/forecast')
def forecast_api():
    return 'forecasting'

@router.get('/predict')
def predict_api():
    return 'predict'

