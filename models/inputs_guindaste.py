# models/entrada_guindaste.py
from dataclasses import dataclass
import numpy as np
import pandas as pd

# @dataclass(frozen=True)
# class EntradaGuindaste:
#     patolas: np.ndarray  # shape (n, 3)
#     centro_massa: np.ndarray  # (3,)
#     raio: float
#     comprimento_lanca: float
#     carga: float  # ton
#     vento: np.ndarray  # (2,) -> [Vi, Vj]
#     angulo_giro: float  # rad


@dataclass(frozen=True)
class EntradaGuindaste:
    # Geometria e apoio
    patolas: pd.DataFrame  # X, Y, Z
    centro_massa: pd.Series  # Xcm, Ycm, Zcm
    lanca: pd.Series  # Lanca, Raio
    angulo_giro_deg: float  # graus

    # Pesos
    peso_guindaste: float  # ton
    contrapeso: float  # ton
    cargas: pd.DataFrame  # várias cargas

    # Ações externas
    vento: pd.Series  # Vi, Vj
    solo: pd.Series  # soil_k, soil_area_i

    # -----------------------------
    # Validação do modelo
    # -----------------------------
    def is_valid(self) -> bool:
        try:
            # ===== Patolas =====
            if len(self.patolas) < 3:
                return False
            if self.patolas[["X", "Y", "Z"]].isna().any().any():
                return False

            # ===== Centro de massa =====
            if self.centro_massa[["Xcm", "Ycm", "Zcm"]].isna().any():
                return False

            # ===== Lança =====
            L = float(self.lanca["Lanca"])
            R = float(self.lanca["Raio"])
            if L <= 0 or R < 0 or R > L:
                return False

            # ===== Pesos =====
            # if self.peso_guindaste <= 0:
            #     return False
            # if self.contrapeso < 0:
            #     return False

            # ===== Cargas =====
            if self.cargas.empty:
                return False
            if self.cargas["Carga"].isna().any():
                return False
            if (self.cargas["Carga"] <= 0).any():
                return False

            # ===== Solo =====
            if self.solo["soil_k"] <= 0:
                return False
            if self.solo["soil_area_i"] <= 0:
                return False

            # ===== Ângulo =====
            if not (0 <= self.angulo_giro_deg <= 360):
                return False

            return True

        except (KeyError, TypeError, ValueError):
            return False
