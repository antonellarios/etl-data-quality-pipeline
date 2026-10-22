# Automated ETL Pipeline with Data Quality & Observability

Pipeline ETL modular desarrollado en Python y SQL enfocado en ingesta controlada, validación estricta de calidad de datos (Data Quality) y trazabilidad mediante tablas de auditoría y SLAs de consistencia.

## 📌 Arquitectura y Flujo de Datos

    [Raw Data / APIs] 
           │
           ▼
    [Data Quality Engine] ──(Fails SLA / Corrupt)──► [Quarantine / Dead Letter Queue]
           │
       (Passes)
           ▼
    [Production Warehouse (SQL)] ◄──► [ETL Audit Logs & Metadata]

1. **Extract:** Ingesta de lotes transaccionales crudos (archivos planos/APIs).
2. **Transform & Quality Gates:**
   - Validación de unicidad y no nulidad en claves primarias (transaction_id).
   - Chequeo de consistencia de negocio (montos positivos, estados válidos).
   - Detección de completitud en entidades relacionales (customer_id).
   - Aislamiento automático de anomalías en cuarentena (data/rejected/) con motivo de descarte detallado.
3. **Load & Audit:**
   - Carga transaccional en tabla de hechos fact_transactions.
   - Registro de métricas de observabilidad en etl_audit_logs (tasa de aprobación, conteos y estado del SLA).

## 🛠️ Tecnologías

- Lenguaje: Python 3.10+
- Procesamiento: Pandas, NumPy
- Base de Datos y ORM: SQLAlchemy, SQLite (compatible con PostgreSQL / SQL Server)
- Control de Versiones: Git & GitHub

## 🚀 Instalación y Uso

1. Clonar el repositorio:
   git clone [https://github.com/tu-usuario/etl-data-quality-pipeline.git](https://github.com/tu-usuario/etl-data-quality-pipeline.git)
   cd etl-data-quality-pipeline

2. Instalar dependencias:
   pip install -r requirements.txt

3. Generar dataset de prueba con anomalías controladas:
   python generate_data.py

4. Ejecutar el pipeline:
   python main.py

5. Verificar datos cargados y logs de auditoría:
   python check_db.py