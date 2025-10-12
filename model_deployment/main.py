from fastapi import FastAPI
import joblib


model = joblib.load("logistic_regression_iris_model.joblib")
app = FastAPI()

@app.get("/")
def predict(sepal_length: float, sepal_width: float, petal_length: float, petal_width: float):
    sample_data = [[sepal_length, sepal_width, petal_length, petal_width]]
    prediction = model.predict(sample_data)
    return {"prediction": int(prediction[0])}
