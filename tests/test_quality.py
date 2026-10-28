import pandas as pd
import pytest

from src.quality import DataQualityEngine

# Columnas que usan las reglas de calidad (si exigís también transaction_date, agregala).
REQUIRED_COLUMNS = ["transaction_id", "customer_id", "amount", "status"]
ALL_COLUMNS = ["transaction_id", "customer_id", "transaction_date", "amount", "status"]


def make_row(**overrides):
    """Fila válida por defecto; cada test pisa solo lo que quiere romper."""
    row = {
        "transaction_id": "TXN_OK",
        "customer_id": "CUST_01",
        "transaction_date": "2026-10-21",
        "amount": 1000.0,
        "status": "COMPLETED",
    }
    row.update(overrides)
    return row


@pytest.fixture
def base_valid_data():
    """Dataset fixture con un registro limpio."""
    return pd.DataFrame([make_row()])


def test_valid_record_passes(base_valid_data):
    """Verifica que un registro correcto sea aprobado al 100%."""
    df_valid, df_rejected, metrics = DataQualityEngine(base_valid_data).run_validations()

    assert len(df_valid) == 1
    assert len(df_rejected) == 0
    assert metrics["pass_rate_percentage"] == 100.0


def test_null_or_duplicated_transaction_id():
    """Verifica detección de IDs nulos y repetidos, con el motivo exacto por fila."""
    data = pd.DataFrame([
        make_row(transaction_id=None, customer_id="CUST_01", amount=100.0),
        make_row(transaction_id="TXN_DUP", customer_id="CUST_02", amount=200.0),
        make_row(transaction_id="TXN_DUP", customer_id="CUST_03", amount=300.0),
    ])
    df_valid, df_rejected, _ = DataQualityEngine(data).run_validations()

    assert len(df_valid) == 0
    assert list(df_rejected["rejection_reasons"]) == [
        "ID_NULO",
        "ID_DUPLICADO",
        "ID_DUPLICADO",
    ]


def test_invalid_amount():
    """Verifica descarte de montos negativos o en cero."""
    data = pd.DataFrame([
        make_row(transaction_id="TXN_01", amount=-50.0),
        make_row(transaction_id="TXN_02", amount=0.0),
    ])
    df_valid, df_rejected, _ = DataQualityEngine(data).run_validations()

    assert len(df_valid) == 0
    assert len(df_rejected) == 2
    assert all(r == "MONTO_INVALIDO" for r in df_rejected["rejection_reasons"])


def test_invalid_status_and_missing_customer():
    """Verifica descarte de estados fuera de dominio y clientes faltantes."""
    data = pd.DataFrame([
        make_row(transaction_id="TXN_01", status="FRAUD_STATE"),
        make_row(transaction_id="TXN_02", customer_id=None),
    ])
    df_valid, df_rejected, _ = DataQualityEngine(data).run_validations()

    assert len(df_valid) == 0
    assert list(df_rejected["rejection_reasons"]) == [
        "ESTADO_NO_PERMITIDO",
        "CLIENTE_FALTANTE",
    ]


@pytest.mark.parametrize(
    "bad_amount",
    ["cien", "", None, float("nan"), float("inf"), float("-inf")],
    ids=["texto", "cadena_vacia", "none", "nan", "inf", "menos_inf"],
)
def test_non_numeric_or_non_finite_amount_is_rejected(bad_amount):
    """Texto, vacío, NaN e infinitos van a cuarentena sin romper el pipeline."""
    data = pd.DataFrame([make_row(amount=bad_amount)])
    df_valid, df_rejected, metrics = DataQualityEngine(data).run_validations()

    assert len(df_valid) == 0
    assert list(df_rejected["rejection_reasons"]) == ["MONTO_INVALIDO"]
    assert metrics["rejected_records"] == 1


def test_bad_amount_does_not_contaminate_valid_rows():
    """Un monto inválido en el lote no debe afectar a las filas válidas."""
    data = pd.DataFrame([
        make_row(transaction_id="TXN_OK"),
        make_row(transaction_id="TXN_BAD", amount="cien"),
    ])
    df_valid, df_rejected, metrics = DataQualityEngine(data).run_validations()

    assert list(df_valid["transaction_id"]) == ["TXN_OK"]
    assert list(df_rejected["transaction_id"]) == ["TXN_BAD"]
    assert metrics["pass_rate_percentage"] == 50.0


@pytest.mark.parametrize("missing_column", REQUIRED_COLUMNS)
def test_missing_required_column_raises_value_error(missing_column):
    """Un esquema incompleto debe fallar rápido y de forma explícita."""
    data = pd.DataFrame([make_row()]).drop(columns=[missing_column])

    with pytest.raises(ValueError):
        DataQualityEngine(data).run_validations()


def test_empty_dataframe_returns_zero_metrics():
    """Un lote de 0 filas no rompe el motor; la política la decide main.py."""
    data = pd.DataFrame(columns=ALL_COLUMNS)
    df_valid, df_rejected, metrics = DataQualityEngine(data).run_validations()

    assert df_valid.empty
    assert df_rejected.empty
    assert metrics["total_records"] == 0
    assert metrics["valid_records"] == 0
    assert metrics["rejected_records"] == 0
    assert metrics["pass_rate_percentage"] == 0.0