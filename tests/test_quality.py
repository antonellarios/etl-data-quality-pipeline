import pytest
import pandas as pd
from src.quality import DataQualityEngine

@pytest.fixture
def base_valid_data():
    """Dataset fixture con un registro limpio."""
    return pd.DataFrame([{
        "transaction_id": "TXN_OK",
        "customer_id": "CUST_01",
        "transaction_date": "2026-10-21",
        "amount": 1000.0,
        "status": "COMPLETED"
    }])

def test_valid_record_passes(base_valid_data):
    """Verifica que un registro correcto sea aprobado al 100%."""
    engine = DataQualityEngine(base_valid_data)
    df_valid, df_rejected, metrics = engine.run_validations()

    assert len(df_valid) == 1
    assert len(df_rejected) == 0
    assert metrics["pass_rate_percentage"] == 100.0

def test_null_or_duplicated_transaction_id():
    """Verifica detección de IDs nulos y repetidos."""
    data = pd.DataFrame([
        {"transaction_id": None, "customer_id": "CUST_01", "transaction_date": "2026-10-21", "amount": 100.0, "status": "COMPLETED"},
        {"transaction_id": "TXN_DUP", "customer_id": "CUST_02", "transaction_date": "2026-10-21", "amount": 200.0, "status": "COMPLETED"},
        {"transaction_id": "TXN_DUP", "customer_id": "CUST_03", "transaction_date": "2026-10-21", "amount": 300.0, "status": "COMPLETED"}
    ])
    engine = DataQualityEngine(data)
    df_valid, df_rejected, metrics = engine.run_validations()

    assert len(df_valid) == 0
    assert len(df_rejected) == 3
    assert any("ID_NULO" in r for r in df_rejected["rejection_reasons"])
    assert any("ID_DUPLICADO" in r for r in df_rejected["rejection_reasons"])

def test_invalid_amount():
    """Verifica descarte de montos negativos o en cero."""
    data = pd.DataFrame([
        {"transaction_id": "TXN_01", "customer_id": "CUST_01", "transaction_date": "2026-10-21", "amount": -50.0, "status": "COMPLETED"},
        {"transaction_id": "TXN_02", "customer_id": "CUST_02", "transaction_date": "2026-10-21", "amount": 0.0, "status": "COMPLETED"}
    ])
    engine = DataQualityEngine(data)
    df_valid, df_rejected, metrics = engine.run_validations()

    assert len(df_valid) == 0
    assert len(df_rejected) == 2
    assert all("MONTO_INVALIDO" in r for r in df_rejected["rejection_reasons"])

def test_invalid_status_and_missing_customer():
    """Verifica descarte de estados fuera de dominio y clientes faltantes."""
    data = pd.DataFrame([
        {"transaction_id": "TXN_01", "customer_id": "CUST_01", "transaction_date": "2026-10-21", "amount": 500.0, "status": "FRAUD_STATE"},
        {"transaction_id": "TXN_02", "customer_id": None, "transaction_date": "2026-10-21", "amount": 500.0, "status": "COMPLETED"}
    ])
    engine = DataQualityEngine(data)
    df_valid, df_rejected, metrics = engine.run_validations()

    assert len(df_valid) == 0
    assert len(df_rejected) == 2
    assert any("ESTADO_NO_PERMITIDO" in r for r in df_rejected["rejection_reasons"])
    assert any("CLIENTE_FALTANTE" in r for r in df_rejected["rejection_reasons"])