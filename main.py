import os
import pandas as pd
from datetime import datetime

from src.database import init_database, load_valid_records, log_pipeline_run
from src.quality import DataQualityEngine

def run_pipeline():
    print("=" * 60)
    print("INICIANDO PIPELINE ETL CON CONTROL DE CALIDAD Y AUDITORÍA")
    print("=" * 60)

    # 1. Inicializar esquema de Base de Datos
    print("\n[1/5] Inicializando base de datos SQLite y tablas de auditoría...")
    init_database()

    # 2. Extracción (Ingesta desde data/raw)
    raw_file_path = "data/raw/transactions_raw.csv"
    if not os.path.exists(raw_file_path):
        print(f"ERROR: No se encontró el archivo de origen en {raw_file_path}")
        return

    print(f"[2/5] Extrayendo datos crudos desde: {raw_file_path}")
    df_raw = pd.read_csv(raw_file_path)
    print(f"      Total de registros ingeridos: {len(df_raw)}")

    # 3. Transformación y Validación (Motor de Data Quality)
    print("[3/5] Ejecutando motor de validación de reglas de negocio...")
    validator = DataQualityEngine(df_raw)
    df_valid, df_rejected, metrics = validator.run_validations()

    print(f"      Registros limpios (aprobados): {metrics['valid_records']}")
    print(f"      Registros anómalos (rechazados): {metrics['rejected_records']}")
    print(f"      Tasa de aprobación (Pass Rate): {metrics['pass_rate_percentage']}%")

    # 4. Manejo de Datos Rechazados (Dead Letter Queue / Quarantine)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rejected_output_path = f"data/rejected/quarantine_transactions_{timestamp}.csv"
    
    if not df_rejected.empty:
        df_rejected.to_csv(rejected_output_path, index=False)
        print(f"[4/5] Registros rechazados aislados en: {rejected_output_path}")
    else:
        print("[4/5] Sin registros rechazados para aislar.")

    # 5. Carga a SQL y Registro de Auditoría
    print("[5/5] Cargando registros aprobados a la base de datos...")
    load_valid_records(df_valid)

    # Determinamos el estado del pipeline según el umbral de calidad (SLA)
    # Por ejemplo: Si el pass rate es menor a 50%, lo marcamos como WARNING
    run_status = "SUCCESS" if metrics["pass_rate_percentage"] >= 50.0 else "WARNING_LOW_QUALITY"
    
    log_pipeline_run(
        pipeline_name="daily_transactions_ingestion",
        metrics=metrics,
        status=run_status
    )
    print("      Auditoría registrada exitosamente en tabla 'etl_audit_logs'.")

    print("\n" + "=" * 60)
    print(f"PIPELINE FINALIZADO CON ESTADO: {run_status}")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()