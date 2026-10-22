import pandas as pd
from typing import Tuple, Dict, Any

class DataQualityEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def run_validations(self) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Ejecuta reglas de integridad y negocio.
        Separa registros aptos para carga de aquellos anómalos,
        adjuntando la causa del error.
        """
        total_records = len(self.df)

        # Regla 1: Identificador no nulo y sin duplicados
        is_id_null = self.df['transaction_id'].isna()
        is_id_dup = self.df.duplicated(subset=['transaction_id'], keep=False) & ~is_id_null

        # Regla 2: Monto numérico mayor a cero
        is_invalid_amount = (self.df['amount'].isna()) | (self.df['amount'] <= 0)

        # Regla 3: Estado dentro del dominio permitido
        valid_statuses = {'COMPLETED', 'PENDING', 'CANCELLED'}
        is_invalid_status = ~self.df['status'].isin(valid_statuses)

        # Regla 4: Identificador de cliente obligatorio
        is_customer_missing = self.df['customer_id'].isna()

        # Condición total de registro rechazado
        failed_mask = is_id_null | is_id_dup | is_invalid_amount | is_invalid_status | is_customer_missing

        # Partición de datasets
        df_valid = self.df[~failed_mask].copy()
        df_rejected = self.df[failed_mask].copy()

        # Documentación de causales de descarte
        df_rejected['rejection_reasons'] = ""
        df_rejected.loc[is_id_null, 'rejection_reasons'] += "ID_NULO; "
        df_rejected.loc[is_id_dup, 'rejection_reasons'] += "ID_DUPLICADO; "
        df_rejected.loc[is_invalid_amount, 'rejection_reasons'] += "MONTO_INVALIDO; "
        df_rejected.loc[is_invalid_status, 'rejection_reasons'] += "ESTADO_NO_PERMITIDO; "
        df_rejected.loc[is_customer_missing, 'rejection_reasons'] += "CLIENTE_FALTANTE; "
        df_rejected['rejection_reasons'] = df_rejected['rejection_reasons'].str.strip('; ')

        # Métricas de ejecución (SLA y calidad)
        valid_count = len(df_valid)
        rejected_count = len(df_rejected)
        pass_rate = round((valid_count / total_records * 100), 2) if total_records > 0 else 0.0

        metrics = {
            "total_records": total_records,
            "valid_records": valid_count,
            "rejected_records": rejected_count,
            "pass_rate_percentage": pass_rate
        }

        return df_valid, df_rejected, metrics