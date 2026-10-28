import logging

import pytest

import main as pipeline
from main import PipelineInputError, run_pipeline

HEADER = "transaction_id,customer_id,transaction_date,amount,status\n"

def test_non_utf8_file_raises_input_error(tmp_path):
    csv = tmp_path / "utf16.csv"
    csv.write_bytes("transaction_id,amount\n".encode("utf-16"))  # BOM 0xff 0xfe

    with pytest.raises(PipelineInputError, match="CSV UTF-8"):
        run_pipeline(input_path=csv, rejected_dir=tmp_path / "rejected")


def test_empty_batch_raises_input_error(tmp_path):
    csv = tmp_path / "empty_batch.csv"
    csv.write_text(HEADER)  # encabezados, 0 filas

    with pytest.raises(PipelineInputError, match="0 filas"):
        run_pipeline(input_path=csv, rejected_dir=tmp_path / "rejected")


def test_zero_byte_file_raises_input_error(tmp_path):
    csv = tmp_path / "zero_bytes.csv"
    csv.write_text("")

    with pytest.raises(PipelineInputError, match="vacío"):
        run_pipeline(input_path=csv, rejected_dir=tmp_path / "rejected")


def test_missing_columns_raises_input_error(tmp_path):
    csv = tmp_path / "bad_schema.csv"
    csv.write_text("transaction_id,amount\nTXN_1,10\n")

    with pytest.raises(PipelineInputError, match="Esquema"):
        run_pipeline(input_path=csv, rejected_dir=tmp_path / "rejected")


def test_main_exits_1_with_clean_log_on_empty_batch(tmp_path, monkeypatch, caplog):
    csv = tmp_path / "empty_batch.csv"
    csv.write_text(HEADER)
    real_run = pipeline.run_pipeline
    monkeypatch.setattr(
        pipeline,
        "run_pipeline",
        lambda: real_run(input_path=csv, rejected_dir=tmp_path / "rejected"),
    )

    with caplog.at_level(logging.INFO):
        exit_code = pipeline.main()

    assert exit_code == 1
    assert "event=pipeline_failed" in caplog.text
    assert "Traceback" not in caplog.text