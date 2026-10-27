import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

class DataQualityEngine:
    REQUIRED_COLUMNS = {'transaction_id', 'amount', 'status', 'customer_id'}

    def __init__(self, df: pd.DataFrame):
        # Validación temprana de esquema
        missing_cols = self.REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            raise ValueError(f"Faltan columnas obligatorias en el dataset de entrada: {sorted(list(missing_cols))}")
        
        self.df = df.copy()

    def run_validations(self) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Ejecuta reglas de integridad y negocio de forma vectorizada.
        Separa registros aptos para carga de aquellos anómalos,
        adjuntando la causa del error en la columna rejection_reasons.
        """
        total_records = len(self.df)

        if total_records == 0:
            empty_df = self.df.copy()
            empty_df['rejection_reasons'] = pd.Series(dtype='object')
            metrics = {
                "total_records": 0,
                "valid_records": 0,
                "rejected_records": 0,
                "pass_rate_percentage": 0.0
            }
            return self.df.copy(), empty_df, metrics

        # Regla 1: Identificador no nulo y sin duplicados en el lote
        is_id_null = self.df['transaction_id'].isna()
        is_id_dup = self.df.duplicated(subset=['transaction_id'], keep=False) & ~is_id_null

        # Regla 2: Monto numérico mayor a cero (coerción segura contra texto, NaN e infinitos)
        amount_numeric = pd.to_numeric(self.df['amount'], errors='coerce')
        is_invalid_amount = (
            amount_numeric.isna() | 
            ~np.isfinite(amount_numeric) | 
            (amount_numeric <= 0)
        )

        # Regla 3: Estado dentro del dominio permitido
        valid_statuses = {'COMPLETED', 'PENDING', 'CANCELLED'}
        is_invalid_status = ~self.df['status'].isin(valid_statuses)

        # Regla 4: Identificador de cliente obligatorio
        is_customer_missing = self.df['customer_id'].isna()

        # Condición total de registro anómalo
        failed_mask = (
            is_id_null | 
            is_id_dup | 
            is_invalid_amount | 
            is_invalid_status | 
            is_customer_missing
        )

        # Partición de datasets
        df_valid = self.df[~failed_mask].copy()
        df_rejected = self.df[failed_mask].copy()

        # Documentación vectorizada de motivos de rechazo
        df_rejected['rejection_reasons'] = ""
        df_rejected.loc[is_id_null, 'rejection_reasons'] += "ID_NULO; "
        df_rejected.loc[is_id_dup, 'rejection_reasons'] += "ID_DUPLICADO; "
        df_rejected.loc[is_invalid_amount, 'rejection_reasons'] += "MONTO_INVALIDO; "
        df_rejected.loc[is_invalid_status, 'rejection_reasons'] += "ESTADO_NO_PERMITIDO; "
        df_rejected.loc[is_customer_missing, 'rejection_reasons'] += "CLIENTE_FALTANTE; "
        df_rejected['rejection_reasons'] = df_rejected['rejection_reasons'].str.strip('; ')

        # Métricas de ejecución del lote
        valid_count = len(df_valid)
        rejected_count = len(df_rejected)
        pass_rate = round((valid_count / total_records * 100), 2)

        metrics = {
            "total_records": total_records,
            "valid_records": valid_count,
            "rejected_records": rejected_count,
            "pass_rate_percentage": pass_rate
        }

        return df_valid, df_rejected, metrics