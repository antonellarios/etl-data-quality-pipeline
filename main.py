import logging
import sys
import time
from pathlib import Path
from uuid import uuid4

import pandas as pd

from src.database import init_database, load_and_audit
from src.quality import DataQualityEngine


PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "transactions_raw.csv"
REJECTED_DIR = PROJECT_ROOT / "data" / "rejected"
QUALITY_GATE_THRESHOLD = 90.0
PIPELINE_NAME = "daily_transactions_ingestion"

logger = logging.getLogger(__name__)


def run_pipeline(
    input_path: Path = INPUT_PATH,
    rejected_dir: Path = REJECTED_DIR,
    quality_gate_threshold: float = QUALITY_GATE_THRESHOLD,
) -> str:
    """Run the local CSV ETL, quarantine rejected rows, and audit the batch.

    Returns the batch status. Raises an exception if extraction, validation,
    persistence, or audit logging fails so the process/CI can report failure.
    """
    run_id = str(uuid4())
    started_at = time.perf_counter()

    logger.info("run_id=%s event=pipeline_started input=%s", run_id, input_path)

    if not input_path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de origen: {input_path}")

    logger.info("run_id=%s event=database_initialization_started", run_id)
    init_database()

    logger.info("run_id=%s event=extraction_started input=%s", run_id, input_path)
    df_raw = pd.read_csv(input_path)
    logger.info(
        "run_id=%s event=extraction_completed total_records=%d",
        run_id,
        len(df_raw),
    )

    logger.info("run_id=%s event=validation_started", run_id)
    validator = DataQualityEngine(df_raw)
    df_valid, df_rejected, metrics = validator.run_validations()

    pass_rate = float(metrics["pass_rate_percentage"])
    run_status = (
        "SUCCESS"
        if pass_rate >= quality_gate_threshold
        else "WARNING_LOW_QUALITY"
    )

    logger.info(
        "run_id=%s event=validation_completed valid_records=%s "
        "rejected_records=%s pass_rate_pct=%.2f status=%s",
        run_id,
        metrics["valid_records"],
        metrics["rejected_records"],
        pass_rate,
        run_status,
    )

    rejected_dir.mkdir(parents=True, exist_ok=True)
    rejected_output_path = rejected_dir / f"quarantine_transactions_{run_id}.csv"
    if not df_rejected.empty:
        df_rejected.to_csv(rejected_output_path, index=False)
        logger.warning(
            "run_id=%s event=quarantine_written rejected_records=%d path=%s",
            run_id,
            len(df_rejected),
            rejected_output_path,
        )
    else:
        logger.info("run_id=%s event=no_rejected_records", run_id)

    logger.info("run_id=%s event=load_started valid_records=%d", run_id, len(df_valid))
    load_and_audit(
        df_valid=df_valid,
        pipeline_name=PIPELINE_NAME,
        metrics=metrics,
        status=run_status,
    )

    elapsed_seconds = time.perf_counter() - started_at
    logger.info(
        "run_id=%s event=pipeline_completed status=%s elapsed_seconds=%.3f",
        run_id,
        run_status,
        elapsed_seconds,
    )
    return run_status


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        status = run_pipeline()
    except Exception:
        logger.exception("event=pipeline_failed")
        return 1

    logger.info("event=pipeline_finished status=%s", status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
