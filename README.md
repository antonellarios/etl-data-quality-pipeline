# Automated ETL Pipeline with Data Quality & Observability

Pipeline ETL modular desarrollado en Python y SQL enfocado en ingesta controlada, validación estricta de calidad de datos (Data Quality) y trazabilidad mediante tablas de auditoría y SLAs de consistencia.

## 📌 Arquitectura y Flujo de Datos

    [Raw Data / APIs] 
           │
           ▼
    [Data Quality Engine] ──(Fails Rules)──► [Quarantine / Dead Letter Queue]
           │
       (Passes)
           ▼
    [Production Warehouse (SQL)] ◄──► [ETL Audit Logs & Metadata]

1. **Extract:** Ingesta de lotes transaccionales crudos (archivos planos/APIs).
2. **Transform & Quality Gates:**
   - Validación de reglas de integridad y negocio en memoria.
   - Segregación automática de anomalías a cuarentena (data/rejected/) con motivo de descarte detallado.
3. **Load & Audit:**
   - Carga transaccional en tabla de hechos fact_transactions.
   - Registro de observabilidad en etl_audit_logs evaluando el SLA del lote.

---

## 📋 Reglas de Calidad y Umbrales (Quality Gates)

| Dimensión | Campo | Regla / Condición | Acción | Motivo en Cuarentena |
| :--- | :--- | :--- | :--- | :--- |
| **Integridad** | transaction_id | No nulo (IS NOT NULL) y único (IS UNIQUE) | Cuarentena | ID_NULO / ID_DUPLICADO |
| **Completitud** | customer_id | Obligatorio (IS NOT NULL) | Cuarentena | CLIENTE_FALTANTE |
| **Consistencia** | amount | Valor numérico mayor a 0 (amount > 0) | Cuarentena | MONTO_INVALIDO |
| **Validez** | status | Pertenecer a: {'COMPLETED', 'PENDING', 'CANCELLED'} | Cuarentena | ESTADO_NO_PERMITIDO |

### SLA y Política de Alertas
- **Umbral de Calidad (Pass Rate SLA):** >= 50%.
- **Estado SUCCESS:** Si el lote alcanza o supera el 50% de registros aprobados, se registra con status de éxito.
- **Alerta WARNING_LOW_QUALITY:** Si el lote cae por debajo del 50%, se emite una advertencia formal en los logs y en la base de datos de auditoría para revisión operativa.

---

## 📊 Evidencia de Ejecución

### 1. Salida del Pipeline en Consola
============================================================
INICIANDO PIPELINE ETL CON CONTROL DE CALIDAD Y AUDITORÍA
============================================================

[1/5] Inicializando base de datos SQLite y tablas de auditoría...
[2/5] Extrayendo datos crudos desde: data/raw/transactions_raw.csv
      Total de registros ingeridos: 10
[3/5] Ejecutando motor de validación de reglas de negocio...
      Registros limpios (aprobados): 4
      Registros anómalos (rechazados): 6
      Tasa de aprobación (Pass Rate): 40.0%
[4/5] Registros rechazados aislados en: data/rejected/quarantine_transactions_20261021_223746.csv
[5/5] Cargando registros aprobados a la base de datos...
      Auditoría registrada exitosamente en tabla 'etl_audit_logs'.

============================================================
PIPELINE FINALIZADO CON ESTADO: WARNING_LOW_QUALITY
============================================================

### 2. Tabla de Auditoría de Producción (etl_audit_logs)
| run_id | pipeline_name | total_processed | valid_loaded | rejected_count | pass_rate_pct | status |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | daily_transactions_ingestion | 10 | 4 | 6 | 40.0 | WARNING_LOW_QUALITY |

### 3. Ejemplo de Cuarentena con Motivos (data/rejected/)
| transaction_id | customer_id | amount | status | rejection_reasons |
| :--- | :--- | :---: | :--- | :--- |
| None | CUST_06 | 5400.0 | COMPLETED | ID_NULO |
| TXN_1002 | CUST_07 | 9900.0 | COMPLETED | ID_DUPLICADO |
| TXN_1008 | CUST_08 | -350.0 | COMPLETED | MONTO_INVALIDO |
| TXN_1009 | None | 12000.0 | COMPLETED | CLIENTE_FALTANTE |
| TXN_1010 | CUST_10 | 7600.0 | FAILED_UNKNOWN | ESTADO_NO_PERMITIDO |

---

## 🛠️ Tecnologías

- Lenguaje: Python 3.10+
- Procesamiento de Datos: Pandas, NumPy
- Bases de Datos & ORM: SQLAlchemy, SQLite (compatible con PostgreSQL / SQL Server)
- Testing: Pytest
- Control de Versiones: Git & GitHub

---

## 🚀 Instalación y Uso

1. Clonar el repositorio:
   git clone https://github.com/antonellarios/etl-data-quality-pipeline.git
   cd etl-data-quality-pipeline

2. Instalar dependencias:
   python -m pip install -r requirements.txt

3. Ejecutar la suite de pruebas automatizadas:
   python -m pytest

4. Generar dataset de prueba:
   python generate_data.py

5. Ejecutar el pipeline ETL:
   python main.py

6. Verificar datos y tabla de auditoría:
   python check_db.py