from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.exceptions import AirflowSkipException
from datetime import datetime , timedelta
import os
import yfinance as yf

def extract_finance_data(ds, **kwargs):

  tickers = ['SCB.BK', 'KBANK.BK', 'BBL.BK', 'KTC.BK']

  start_date = ds
  end_date = (datetime.strptime(ds, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
  print(f"Fetching data from {start_date} to {end_date}")

  df = yf.download(tickers, start=start_date, end=end_date)

  if df.empty:
    print(f"No data found {ds} (Market closed)")
    raise AirflowSkipException(f"No data found: {ds}")
  
  df_close = df['Close'].reset_index()

  output_path = f'/opt/airflow/data/prices_{ds}.csv'
  df_close.to_csv(output_path, index=False)
  print(f"Data saved to {output_path}")

def upload_to_minio(ds, **kwargs):
  hook = S3Hook('minio_conn')
  
  local_file = f'/opt/airflow/data/prices_{ds}.csv'
  minio_key = f'raw/{ds}/prices.csv'

  if os.path.exists(local_file):
    print(f"Uploading {local_file} to minio")
    hook.load_file(
      filename=local_file,
      key=minio_key,
      bucket_name='finance-market',
      replace=True
    )
    os.remove(local_file)
  else:
    raise AirflowSkipException(f"No data found: {ds}")

with DAG(
  dag_id='finance_market_evolution',
  start_date=datetime(2026, 3, 20),
  schedule='@daily',
  catchup=True,
  max_active_runs=1
) as dag:
  task_extract = PythonOperator(
    task_id='extract_data',
    python_callable=extract_finance_data
  )

  task_upload = PythonOperator(
    task_id='upload_to_storage',
    python_callable=upload_to_minio
  )

  task_extract >> task_upload
