from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
import pendulum

ROOT_DIR = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT_DIR / "recon" / "wema"


WEMA_ACCOUNT_NUMBER="0000221110"
WEMA_LOOKBACK_DAYS=7


def load_sql(filename: str) -> str:
    path = SQL_DIR / filename
    with open(path, encoding="utf-8") as fh:
        return fh.read()
    
default_args = {
        "owner": "recon_team",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5)
    }

with DAG(
    dag_id="recon_wema_reconcilliation",
    default_args = default_args,
    description="Load ledger data, deduplicate, and reconcile WEMA transactions.",
    schedule="30 3 * * *",
    start_date=pendulum.now().subtract(days=1),
    catchup=False,
    params={
        "schema": os.getenv("SCHEMA"),
        "raw": "wema_raw",
        "staging": "wema_staging",
        "recon_results": "wema_recon_results",
        "reconciliation": "reconciliation_view",
        "ledger_schema": os.getenv("LEDGER_SCHEMA"),
        "account_number": os.getenv("WEMA_ACCOUNT_NUMBER", ""),
        "lookback_days": int(os.getenv("WEMA_LOOKBACK_DAYS", 2)),
    },
    tags=["maintainer: mubaraq.sani@lumenpay.com",
          "recon", "wema", "recon-v1"]
) as dag:

    start = EmptyOperator(task_id="start")

    create_tables = SQLExecuteQueryOperator(
        task_id="create_recon_tables",
        conn_id="postgres_default",
        sql=load_sql("create_initial_tables.sql")
    )

    load_raw_ledger = SQLExecuteQueryOperator(
        task_id="load_raw_ledger",
        conn_id="postgres_default",
        sql=load_sql("extract_ledger.sql")

    )

    deduplicate_to_staging = SQLExecuteQueryOperator(
        task_id="deduplicate_to_staging",
        conn_id="postgres_default",
        sql=load_sql("stage_dedup.sql")

    )

    insert_reconciliation_results = SQLExecuteQueryOperator(
        task_id="insert_reconciliation_results",
        conn_id="postgres_default",
        sql=load_sql("reconcile_results.sql")

    )


    clear_tables = SQLExecuteQueryOperator(
        task_id="clear_tables",
        conn_id="postgres_default",
        sql=load_sql("truncate_staging.sql")

    )

    end = EmptyOperator(task_id="end")

    start >> create_tables >> load_raw_ledger >> deduplicate_to_staging >> insert_reconciliation_results >> clear_tables >> end
