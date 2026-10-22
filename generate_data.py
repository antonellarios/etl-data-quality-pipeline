import pandas as pd
import numpy as np

def generate_mock_transactions():
    """Genera un archivo CSV con datos transaccionales limpios y con anomalías intencionales."""
    data = [
        # Registros válidos
        {"transaction_id": "TXN_1001", "customer_id": "CUST_01", "transaction_date": "2026-10-20", "amount": 15000.50, "status": "COMPLETED"},
        {"transaction_id": "TXN_1002", "customer_id": "CUST_02", "transaction_date": "2026-10-20", "amount": 8450.00, "status": "COMPLETED"},
        {"transaction_id": "TXN_1003", "customer_id": "CUST_03", "transaction_date": "2026-10-21", "amount": 2300.00, "status": "PENDING"},
        {"transaction_id": "TXN_1004", "customer_id": "CUST_04", "transaction_date": "2026-10-21", "amount": 45000.00, "status": "COMPLETED"},
        {"transaction_id": "TXN_1005", "customer_id": "CUST_05", "transaction_date": "2026-10-21", "amount": 1200.00, "status": "CANCELLED"},
        
        # Errores intencionales para evaluar Data Quality
        {"transaction_id": None, "customer_id": "CUST_06", "transaction_date": "2026-10-21", "amount": 5400.00, "status": "COMPLETED"},          # ID NULO
        {"transaction_id": "TXN_1002", "customer_id": "CUST_07", "transaction_date": "2026-10-21", "amount": 9900.00, "status": "COMPLETED"},       # ID DUPLICADO
        {"transaction_id": "TXN_1008", "customer_id": "CUST_08", "transaction_date": "2026-10-21", "amount": -350.00, "status": "COMPLETED"},       # MONTO NEGATIVO
        {"transaction_id": "TXN_1009", "customer_id": None, "transaction_date": "2026-10-21", "amount": 12000.00, "status": "COMPLETED"},           # CLIENTE NULO
        {"transaction_id": "TXN_1010", "customer_id": "CUST_10", "transaction_date": "2026-10-21", "amount": 7600.00, "status": "FAILED_UNKNOWN"}   # ESTADO INVALIDO
    ]

    df = pd.DataFrame(data)
    output_path = "data/raw/transactions_raw.csv"
    df.to_csv(output_path, index=False)
    print(f"Archivo generado exitosamente en: {output_path} ({len(df)} registros totales)")

if __name__ == "__main__":
    generate_mock_transactions()