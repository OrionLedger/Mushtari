from fastapi import APIRouter

router = APIRouter(prefix='/api' , tags=['ML'])

@router.get('/api/forecast')
def forecast_api():
    return 'forecasting'

@router.get('/api/predict')
def predict_api():
    return 'predict'