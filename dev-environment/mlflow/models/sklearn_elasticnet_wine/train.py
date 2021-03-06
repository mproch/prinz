# Example based on example from mlflow repository https://github.com/mlflow/mlflow
# The data set used in this example is from http://archive.ics.uci.edu/ml/datasets/Wine+Quality
# P. Cortez, A. Cerdeira, F. Almeida, T. Matos and J. Reis.
# Modeling wine preferences by data mining from physicochemical properties. In Decision Support Systems, Elsevier, 47(4):547-553, 2009.

import os
import warnings
import sys
from uuid import uuid4

import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet
from urllib.parse import urlparse
import mlflow
import mlflow.sklearn
from mlflow.models.signature import ModelSignature
from mlflow.types.schema import Schema, ColSpec

import logging

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)


def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    np.random.seed(40)

    csv_url = ("http://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv")
    try:
        data = pd.read_csv(csv_url, sep=";")
    except Exception as e:
        logger.exception("Unable to download training & test CSV, check your internet connection. Error: {}".format(e))

    train, test = train_test_split(data)

    train_x = train.drop(["quality"], axis=1)
    test_x = test.drop(["quality"], axis=1)
    train_y = train[["quality"]]
    test_y = test[["quality"]]

    alpha = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    l1_ratio = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

    with mlflow.start_run():
        input_schema = Schema([
            ColSpec("double", "fixed acidity"),
            ColSpec("double", "volatile acidity"),
            ColSpec("double", "citric acid"),
            ColSpec("double", "residual sugar"),
            ColSpec("double", "chlorides"),
            ColSpec("double", "free sulfur dioxide"),
            ColSpec("double", "total sulfur dioxide"),
            ColSpec("double", "density"),
            ColSpec("double", "pH"),
            ColSpec("double", "sulphates"),
            ColSpec("double", "alcohol")
        ])
        output_schema = Schema([ColSpec("double")])
        signature = ModelSignature(inputs=input_schema, outputs=output_schema)

        lr = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)
        lr.fit(train_x, train_y)
        predicted_qualities = lr.predict(test_x)

        (rmse, mae, r2) = eval_metrics(test_y, predicted_qualities)

        print("Elasticnet model (alpha={}, l1_ratio={}):".format(alpha, l1_ratio))
        print("  RMSE: {}".format(rmse))
        print("  MAE: {}".format(mae))
        print("  R2: {}".format(r2))

        mlflow.log_param("alpha", alpha)
        mlflow.log_param("l1_ratio", l1_ratio)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)
        mlflow.log_metric("mae", mae)

        tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme
        if tracking_url_type_store != "file":
            mlflow.sklearn.log_model(lr, "model", registered_model_name="ElasticnetWineModel-{}".format(uuid4()), signature=signature)
        else:
            mlflow.sklearn.log_model(lr, "model")
