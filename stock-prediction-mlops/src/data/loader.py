import pandas as pd
from pandas_datareader import data as pdr
import boto3

def load_stock_data(ticker, start, end):
    """
    Загружает исторические данные по тикеру из stooq.
    """
    df = pdr.DataReader(ticker, 'stooq', start, end)
    df.reset_index(inplace=True)
    return df

def upload_to_s3(file_path, bucket, key, endpoint_url, aws_access_key_id, aws_secret_access_key):
    """
    Загружает файл на S3 (Yandex Cloud).
    """
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    s3.upload_file(file_path, bucket, key)

def download_from_s3(bucket, key, file_path, endpoint_url, aws_access_key_id, aws_secret_access_key):
    """
    Загружает файл из S3 (Yandex Cloud).
    """
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    print(f"Trying to download: s3://{bucket}/{key}")
    s3.download_file(bucket, key, file_path)
