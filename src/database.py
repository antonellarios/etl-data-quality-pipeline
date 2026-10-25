from sqlalchemy import create_engine, text
import pandas as pd
from typing import Dict, Any

DB_PATH = "warehouse.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

def init_database():
    """Inicializa la tabla dimensional de transacciones y la de auditoría."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_transactions (
                transaction_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS etl_audit_logs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_name TEXT NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_processed INTEGER NOT NULL,
                valid_loaded INTEGER NOT NULL,
                rejected_count INTEGER NOT NULL,
                pass_rate_pct REAL NOT NULL,
                status TEXT NOT NULL
            );
        """))

def load_valid_records(df_valid: pd.DataFrame):
    """
    Inserta registros aprobados de forma idempotente.
    Usa INSERT OR IGNORE para no fallar ante reprocesamientos del mismo lote.
    """
    if df_valid.empty:
        return

    records = df_valid.to_dict(orient="records")
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT OR IGNORE INTO fact_transactions (
                    transaction_id, customer_id, transaction_date, amount, status
                ) VALUES (
                    :transaction_id, :customer_id, :transaction_date, :amount, :status
                )
            """),
            records
        )

def log_pipeline_run(pipeline_name: str, metrics: Dict[str, Any], status: str):
    """Registra la métrica del lote en la tabla de auditoría."""
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO etl_audit_logs (
                    pipeline_name, total_processed, valid_loaded, 
                    rejected_count, pass_rate_pct, status
                ) VALUES (
                    :name, :total, :valid, :rejected, :pass_rate, :status
                )
            """),
            {
                "name": pipeline_name,
                "total": metrics["total_records"],
                "valid": metrics["valid_records"],
                "rejected": metrics["rejected_records"],
                "pass_rate": metrics["pass_rate_percentage"],
                "status": status
            }
        )