import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///warehouse.db")

print("--- TABLA DE HECHOS (fact_transactions) ---")
df_facts = pd.read_sql("SELECT * FROM fact_transactions", con=engine)
print(df_facts)

print("\n--- TABLA DE AUDITORÍA (etl_audit_logs) ---")
df_logs = pd.read_sql("SELECT * FROM etl_audit_logs", con=engine)
print(df_logs)