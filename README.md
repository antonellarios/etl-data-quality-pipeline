# Pipeline ETL con Controles de Calidad de Datos y Registro de Auditoría

Un pipeline por lotes (batch) desarrollado en Python que valida datos transaccionales antes de cargar los registros aprobados en una base de datos relacional. Las filas no válidas se aíslan en un archivo de cuarentena con motivos explícitos de rechazo, mientras que las métricas de calidad y el estado de cada ejecución quedan registrados para su posterior revisión.

> **Alcance:** El flujo incluido procesa un archivo CSV local y utiliza datos sintéticos con fines demostrativos. No representa una integración activa con una API externa. El comportamiento con bases de datos depende de la configuración e implementación del repositorio.

[![CI](BADGE_URL)](WORKFLOW_URL)
*Reemplaza `BADGE_URL` y `WORKFLOW_URL` con los enlaces correspondientes de este repositorio, o elimina esta línea hasta que la integración continua (CI) esté configurada.*

---

## Por qué este pipeline

La entrada de datos con formato incorrecto puede introducir transacciones duplicadas, incompletas o no válidas en tablas y reportes analíticos finales. Este pipeline aplica controles explícitos de calidad antes de la carga, aísla los registros que requieren revisión y registra los resultados a nivel de lote para visibilizar las anomalías en lugar de dejarlas pasar de forma silenciosa.

Esta demo no pretende adjudicarse un ahorro financiero medido. Para una implementación con clientes reales, el impacto puede evaluarse frente a una línea de base como el tiempo dedicado a la limpieza manual, el conteo de filas rechazadas por regla, la frecuencia de incidentes recurrentes y el tiempo promedio de diagnóstico tras un lote fallido.

---

## Flujo de datos

```text
CSV local de transacciones
           │
           ▼
     Extracción del lote
           │
           ▼
 Validación de reglas de negocio ───────► CSV de cuarentena
           │                              (Motivos de rechazo explícitos)
           ▼
   Registros aprobados
           │
           ├────────────────────────────► Base de datos relacional
           └────────────────────────────► Métricas de auditoría del lote
```

El script actual `main.py` lee `data/raw/transactions_raw.csv`. El flujo documentado utiliza una base de datos local según la configuración del módulo correspondiente. La ingesta de archivos JSON, APIs externas, orquestación programada, envío de alertas y procesamiento distribuido no están incluidos en esta demostración.

---

## Reglas de calidad de datos

| Dimensión | Campo | Regla | Acción | Motivo de rechazo |
| :--- | :--- | :--- | :--- | :--- |
| **Integridad** | `transaction_id` | Obligatorio y único dentro del lote | Cuarentena | `ID_NULO`, `ID_DUPLICADO` |
| **Completitud** | `customer_id` | Obligatorio | Cuarentena | `CLIENTE_FALTANTE` |
| **Validez** | `amount` | Numérico y mayor a cero | Cuarentena | `MONTO_INVALIDO` |
| **Validez de dominio** | `status` | Debe pertenecer a `COMPLETED`, `PENDING` o `CANCELLED` | Cuarentena | `ESTADO_NO_PERMITIDO` |

Todas las filas que contengan un `transaction_id` duplicado y no nulo se rechazan; el pipeline no selecciona arbitrariamente el "primer" registro. Una fila rechazada puede contener más de un motivo de rechazo simultáneo.

*Alcance de validación:* Revisa cómo maneja el validador valores numéricos malformados (como cadenas de texto o valores infinitos) antes de asumir que dichos casos se descartan de forma segura.

---

## Barrera de calidad (Quality Gate) y métricas de auditoría

El umbral de aceptación del ejemplo está configurado en un 90% por lote. Cualquier ejecución por debajo de ese porcentaje se registra con el estado `WARNING_LOW_QUALITY`. En la implementación actual, esto opera como una advertencia en la auditoría; no bloquea automáticamente el proceso de carga.

Este umbral funciona como un parámetro operativo de control de calidad, no como un SLA contractual. En proyectos para clientes, debe acordarse previamente si un lote de baja calidad debe limitarse a una alerta, aislar el lote completo en cuarentena o abortar la carga.

Las métricas de auditoría computan el total de registros procesados, válidos y rechazados, junto con el porcentaje de aprobación. Una corrida de ejemplo produce:

| Pipeline | Total | Cargados | Rechazados | Tasa de aprobación | Estado |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `daily_transactions_ingestion` | 10 | 4 | 6 | 40.0% | `WARNING_LOW_QUALITY` |

*Esta salida es de carácter ilustrativo; los conteos finales dependen directamente de los datos procesados.*

---

## Cuarentena y recuperación

Las filas rechazadas se exportan al directorio `data/rejected/` en un archivo con marca temporal bajo el patrón `quarantine_transactions_<timestamp>.csv`. El archivo incluye el campo `rejection_reasons` para facilitar la auditoría y corrección.

El repositorio se enfoca en segregar registros defectuosos para su posterior análisis. No contempla reintentos automáticos ni flujos de reprocesamiento a menos que se implementen por separado.

---

## Componentes del repositorio

| Componente | Responsabilidad |
| :--- | :--- |
| `main.py` | Orquesta la inicialización de la base de datos, ingesta del CSV, validación, exportación a cuarentena, carga y registro de auditoría. |
| `quality.py` | Aplica las reglas de validación vectorizadas en Pandas y calcula las métricas del lote. |
| `tests/test_quality.py` | Prueba registros válidos y casos representativos de rechazo por cada regla. |
| `generate_data.py` | Crea datos sintéticos de entrada con anomalías deliberadas. |
| `check_db.py` | Consulta y expone los resultados persistidos en la base de datos. |
| `.github/workflows/ci.yml` | Ejecuta las comprobaciones automáticas ante eventos configurados en GitHub Actions. |

*Verifica estas rutas y responsabilidades con tu repositorio local antes de publicar, especialmente si existen diferencias en la estructura de carpetas.*

---

## Stack tecnológico

- **Python 3.10+**
- **Pandas:** Transformaciones por lotes y validaciones de calidad vectorizadas.
- **SQLite y SQLAlchemy:** Según la configuración de la capa de persistencia.
- **pytest:** Pruebas automatizadas.
- **GitHub Actions:** Integración continua (CI).

---

## Instalación y ejecución

### Requisitos previos
- Git
- Python 3.10 o superior (compatible con las dependencias del proyecto).

### 1. Clonar el repositorio
```bash
git clone [https://github.com/antonellarios/etl-data-quality-pipeline.git](https://github.com/antonellarios/etl-data-quality-pipeline.git)
cd etl-data-quality-pipeline
```

### 2. Instalar dependencias

**En Windows PowerShell:**
```powershell
py -m pip install -r requirements.txt
```

**En macOS / Linux:**
```bash
python3 -m pip install -r requirements.txt
```

### 3. Ejecutar pruebas unitarias

**En Windows PowerShell:**
```powershell
py -m pytest -v
```

**En macOS / Linux:**
```bash
python3 -m pytest -v
```

### 4. Generar datos sintéticos y ejecutar el pipeline

**En Windows PowerShell:**
```powershell
py generate_data.py
py main.py
py check_db.py
```

**En macOS / Linux:**
```bash
python3 generate_data.py
python3 main.py
python3 check_db.py
```

*Estos comandos asumen que los scripts y rutas de datos coinciden con la estructura del proyecto. Revisa el módulo de base de datos para confirmar la ubicación efectiva del archivo `.db` y los nombres de las tablas.*

---

## CI y pruebas automatizadas

La suite actual de pruebas cubre:
- Registro válido superando todas las reglas.
- Identificadores de transacción (`transaction_id`) nulos y duplicados.
- Montos iguales a cero o negativos.
- Estados categóricos no permitidos y clientes faltantes.

GitHub Actions ejecuta las comprobaciones descritas en `.github/workflows/ci.yml`. Añade la insignia de workflow correspondiente una vez confirmada la ruta y la rama predeterminada.

*Casos recomendados para ampliar la cobertura:* columnas faltantes en el origen, valores numéricos no finitos o con caracteres extraños, archivos de entrada vacíos, múltiples fallas simultáneas en un mismo registro, pruebas de rollback en la persistencia e idempotencia frente a reejecuciones.

---

## Decisiones de ingeniería y alcance actual

- **Validación vectorizada:** Las máscaras booleanas de Pandas aplican las reglas a nivel de columnas completas, evitando la iteración fila por fila en el flujo principal.
- **Flujo de base de datos local:** SQLite permite correr la demostración localmente sin infraestructura adicional. Evita catalogar la capa de datos como apta para producción o compatible con PostgreSQL sin antes haber realizado las pruebas de integración correspondientes sobre esa base de datos de destino.
- **Procesamiento por lotes:** La implementación actual carga el archivo CSV directamente en memoria. Cargas de trabajo de mayor escala requerirán estrategias de procesamiento por particiones (*chunking*) o motores distribuidos evaluados según el caso de uso.
- **Control de fallos:** Conviene incorporar y validar logging estructurado, límites transaccionales de carga, mecanismos de rollback y códigos de salida (*exit codes*) consistentes antes de garantizar tolerancia total a fallos.
- **Seguridad:** No incluyas credenciales reales, datos sensibles de clientes ni archivos `.env` completos en commits de Git. Documenta únicamente las variables de entorno que la aplicación consuma efectivamente.

---

## Próximos pasos (Roadmap)

- [ ] Validar explícitamente el esquema de entrada y casos de borde en datos numéricos.
- [ ] Incorporar logging estructurado, identificadores de ejecución (`run_id`), métricas de duración y códigos de salida claros del proceso.
- [ ] Definir comportamiento atómico para la carga/auditoría y reejecuciones idempotentes; probar rollback ante fallas parciales.
- [ ] Configurar políticas flexibles para la barrera de calidad (advertir vs. bloquear la carga).
- [ ] Sumar pruebas de integración y capturas de pantalla de ejecuciones reales.
- [ ] Evaluar conectores hacia PostgreSQL, herramientas de orquestación, alertas externas o procesamiento distribuido cuando el caso de uso lo demande.

---

## Autoría

Proyecto desarrollado por **Antonella Ríos** para portafolio técnico. Para consultas, comentarios o sugerencias, abre un *issue* en este repositorio.
---

## 👤 Autoría

**Antonella Ríos** — *Data & Analytics*  
Para consultas técnicas o reportes, puedes abrir un *issue* en este repositorio.
