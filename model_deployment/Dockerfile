FROM python:3.9-slim

WORKDIR /app

COPY model_deployment/requirements.txt .

COPY model_deployment/main.py .

COPY model_deployment/logistic_regression_iris_model.joblib .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
