from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd

class PredictRequest(BaseModel):
    """
    Ожидается список цен за последние N дней (скользящее окно).
    """
    window: list

app = FastAPI()

# Загружаем модель при старте приложения
model = joblib.load("model.pkl")

@app.post("/predict")
def predict(req: PredictRequest):
    # Преобразуем вход в DataFrame (одна строка с признаками)
    data = pd.DataFrame([req.window])
    prediction = model.predict(data)
    return {"prediction": prediction.tolist()}
