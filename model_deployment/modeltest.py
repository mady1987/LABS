from sklearn.linear_model import LogisticRegression
from sklearn.datasets import load_iris
import joblib
import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

iris = load_iris()
X, y = iris.data, iris.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = LogisticRegression(max_iter=200)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))

model_path = "logistic_regression_iris_model.joblib"
joblib.dump(model, model_path)
print(f"Model saved to {model_path}")
if os.path.exists(model_path):
    loaded_model = joblib.load(model_path)
    sample_data = np.array([[5.1, 3.5, 1.4, 0.2]])
    prediction = loaded_model.predict(sample_data)
    print(f"Prediction for sample data {sample_data}: {prediction}")