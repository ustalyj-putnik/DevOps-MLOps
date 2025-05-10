import yaml
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import mlflow
import mlflow.sklearn
import joblib
from lakefs_client.client import LakeFSClient
from lakefs_client import Configuration, models, exceptions
import uuid
from lakefs_client.models import RepositoryCreation


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.data.loader import load_stock_data, download_from_s3, upload_to_s3
from src.data.processing import create_tsfresh_dataset
from src.features.extract import extract_tsfresh_features

import time
import requests

def wait_for_lakefs(endpoint, timeout=60):
    for _ in range(timeout):
        try:
            r = requests.get(f"{endpoint}/_health")
            if r.status_code == 200:
                print("LakeFS is available.")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    raise RuntimeError("LakeFS not available after timeout")

def main():
    # Загрузка конфигурации
    config = yaml.safe_load(open('config.yaml'))
    model_cfg = config['model']
    data_cfg = config['data']
    s3_cfg = config['s3']
    mlflow_cfg = config['mlflow']

    # Настройка MLflow
    mlflow.set_tracking_uri(mlflow_cfg['tracking_uri'])
    mlflow.set_experiment(mlflow_cfg['experiment_name'])

    # Загрузка данных (из интернета или S3)
    try:
        df = load_stock_data(
            data_cfg['ticker'],
            data_cfg['start_date'],
            data_cfg['end_date']
        )
    except Exception:
        # Если связь с stooq отсутствует, пробуем взять из S3
        download_from_s3(
            bucket=s3_cfg['bucket_name'],
            key=f"data/{data_cfg['ticker']}.csv",
            file_path=f"{data_cfg['ticker']}.csv",
            endpoint_url=s3_cfg['endpoint_url'],
            aws_access_key_id=s3_cfg['access_key'],
            aws_secret_access_key=s3_cfg['secret_key']
        )
        df = pd.read_csv(f"{data_cfg['ticker']}.csv")

    # Сохраняем загруженные данные в S3 для фиксации
    local_csv = f"{data_cfg['ticker']}.csv"
    df.to_csv(local_csv, index=False)
    upload_to_s3(
        file_path=local_csv,
        bucket=s3_cfg['bucket_name'],
        key=f"data/{data_cfg['ticker']}.csv",
        endpoint_url=s3_cfg['endpoint_url'],
        aws_access_key_id=s3_cfg['access_key'],
        aws_secret_access_key=s3_cfg['secret_key']
    )

    # Версионируем данные через LakeFS (фиктивный пример)
    # --- Инициализация клиента LakeFS ---
    lakefs_cfg = config['lakefs']
    lakefs_config = Configuration(
        host=lakefs_cfg['endpoint'],
        username=lakefs_cfg['access_key'],
        password=lakefs_cfg['secret_key']
    )
    wait_for_lakefs(config['lakefs']['endpoint'])
    lakefs = LakeFSClient(configuration=lakefs_config)

    # Проверка существования репозитория и создание, если его нет
    repo_name = lakefs_cfg['repository']
    storage_namespace = f"s3://{lakefs_cfg['s3_bucket']}/{repo_name}/"

    try:
        lakefs.repositories.get_repository(repository=repo_name)
        print(f"✅ Repository '{repo_name}' already exists.")
    except exceptions.NotFoundException:
        print(f"⚠️ Repository '{repo_name}' not found. Creating...")
        lakefs.repositories.create_repository(
            repository_creation=RepositoryCreation(
                name=repo_name,
                storage_namespace=storage_namespace,
                default_branch="main"
            )
        )
        print(f"✅ Repository '{repo_name}' created.")

    # Создаём уникальную ветку для этого эксперимента
    experiment_branch = f"exp-{uuid.uuid4().hex[:8]}"
    branch_creation = models.BranchCreation(name=experiment_branch, source=lakefs_cfg['branch'])

    lakefs.branches.create_branch(
        repository=lakefs_cfg['repository'],
        branch_creation=branch_creation
    )

    # Загружаем файл CSV в LakeFS (используется S3-бакет, поверх которого работает LakeFS)
    with open(local_csv, "rb") as f:
        lakefs.objects.upload_object(
            repository=lakefs_cfg['repository'],
            branch=experiment_branch,
            path=f"data/{data_cfg['ticker']}.csv",
            content=f
        )

    # Делаем коммит изменений
    commit_resp = lakefs.commits.commit(
        repository=lakefs_cfg['repository'],
        branch=experiment_branch,
        commit_creation=models.CommitCreation(
            message="Data snapshot for experiment",
            metadata={"source": "train_model.py"}
        )
    )
    data_commit_id = commit_resp.id
    print(f"LakeFS data committed under ID: {data_commit_id}")

    # Подготовка данных для tsfresh
    X_long, y = create_tsfresh_dataset(df, model_cfg['window_size'])
    # Извлечение и отбор признаков
    X = extract_tsfresh_features(X_long, y)

    # Разбиваем на обучающую и тестовую выборки
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Инициализация модели
    model = RandomForestRegressor(n_estimators=model_cfg['n_estimators'], random_state=42)

    # Обучение модели с логированием в MLflow:contentReference[oaicite:12]{index=12}
    with mlflow.start_run():
        mlflow.log_params(model_cfg)
        mlflow.log_param("lakefs_branch", experiment_branch)
        mlflow.log_param("lakefs_commit_id", data_commit_id)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mlflow.log_metric("mse", mse)
        mlflow.sklearn.log_model(model, "model")

    # Сохраняем модель локально и отправляем в S3
    os.makedirs("artifacts", exist_ok=True)
    model_path = "artifacts/model.pkl"
    joblib.dump(model, model_path)
    upload_to_s3(
        file_path=model_path,
        bucket=s3_cfg['bucket_name'],
        key="models/model.pkl",
        endpoint_url=s3_cfg['endpoint_url'],
        aws_access_key_id=s3_cfg['access_key'],
        aws_secret_access_key=s3_cfg['secret_key']
    )


if __name__ == "__main__":
    main()
