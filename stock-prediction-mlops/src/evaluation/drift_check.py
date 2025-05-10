import yaml
import pandas as pd
from evidently import Report
from evidently.metrics import *
from evidently.presets import *
import json

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.data.loader import download_from_s3

def main():
    config = yaml.safe_load(open('config.yaml'))
    s3_cfg = config['s3']

    # Здесь загружаем CSV с S3 и конкатенируем/разбиваем вручную
    download_from_s3(
        bucket=s3_cfg['bucket_name'], key="data/GOOG.csv",
        file_path="GOOG.csv",
        endpoint_url=s3_cfg['endpoint_url'],
        aws_access_key_id=s3_cfg['access_key'],
        aws_secret_access_key=s3_cfg['secret_key']
    )
    download_from_s3(
        bucket=s3_cfg['bucket_name'], key="data/GOOG.csv",
        file_path="GOOG.csv",
        endpoint_url=s3_cfg['endpoint_url'],
        aws_access_key_id=s3_cfg['access_key'],
        aws_secret_access_key=s3_cfg['secret_key']
    )

    ref_df = pd.read_csv("GOOG.csv")
    curr_df = pd.read_csv("GOOG.csv")

    # Инициализируем отчет Evidently с пресетом для дрейфа данных
    report = Report(metrics=[DataDriftPreset()])
    report_eval = report.run(reference_data=ref_df, current_data=curr_df)

    # Сохраняем HTML-отчет и JSON с метриками
    report_eval.save_html("report.html")
    with open("drift_report.json", "w") as f:
        json.dump(report_eval.dict(), f, indent=2)


if __name__ == "__main__":
    main()
