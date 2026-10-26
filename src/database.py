from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "warehouse.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def init_database() -> None:
    """Crea las tablas necesarias si aún no existen."""
    with engine.begin() as conn:
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS fact_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )

        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS etl_audit_logs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pipeline_name TEXT NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_processed INTEGER NOT NULL,
                    valid_loaded INTEGER NOT NULL,
                    rejected_count INTEGER NOT NULL,
                    pass_rate_pct REAL NOT NULL,
                    status TEXT NOT NULL
                )
            """)
        )


def load_valid_records(
    df_valid: pd.DataFrame,
    conn: Connection,
) -> None:
    """Inserta los registros válidos usando la transacción recibida."""
    if df_valid.empty:
        return

    records = df_valid.to_dict(orient="records")

    conn.execute(
        text("""
            INSERT OR IGNORE INTO fact_transactions (
                transaction_id,
                customer_id,
                transaction_date,
                amount,
                status
            ) VALUES (
                :transaction_id,
                :customer_id,
                :transaction_date,
                :amount,
                :status
            )
        """),
        records,
    )


def log_pipeline_run(
    pipeline_name: str,
    metrics: dict[str, Any],
    status: str,
    conn: Connection,
) -> None:
    """Registra las métricas de la ejecución usando la misma transacción."""
    conn.execute(
        text("""
            INSERT INTO etl_audit_logs (
                pipeline_name,
                total_processed,
                valid_loaded,
                rejected_count,
                pass_rate_pct,
                status
            ) VALUES (
                :pipeline_name,
                :total_processed,
                :valid_loaded,
                :rejected_count,
                :pass_rate_pct,
                :status
            )
        """),
        {
            "pipeline_name": pipeline_name,
            "total_processed": metrics["total_records"],
            "valid_loaded": metrics["valid_records"],
            "rejected_count": metrics["rejected_records"],
            "pass_rate_pct": metrics["pass_rate_percentage"],
            "status": status,
        },
    )


def load_and_audit(
    df_valid: pd.DataFrame,
    pipeline_name: str,
    metrics: dict[str, Any],
    status: str,
) -> None:
    """Carga los datos y registra la auditoría en una sola transacción."""
    with engine.begin() as conn:
        load_valid_records(df_valid, conn)
        log_pipeline_run(pipeline_name, metrics, status, conn)
