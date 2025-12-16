import pandas as pd
import numpy as np


def calc_reactions(entrada):

    gravity = 9.8

    # Ponto fixo para somatórios de momentos
    Pfix = entrada.centro_massa.values

    # Cria o dicionário das distâncias
    R_keys = ["R1", "R2", "R3", "R4"]
    R_dict = dict.fromkeys(R_keys, 0)

    for i, vali in enumerate(R_keys):
        R_dict[vali] = np.array(
            [
                entrada.patolas.X[i] - Pfix[0],
                entrada.patolas.Y[i] - Pfix[1],
                entrada.patolas.Z[i] - Pfix[2],
            ]
        )

    R_dict["R5"] = np.array(
        [
            entrada.lanca.Raio * np.cos(entrada.angulo_giro_deg),
            entrada.lanca.Raio * np.sin(entrada.angulo_giro_deg),
            np.sqrt(entrada.lanca.Lanca**2 - entrada.lanca.Raio**2),
        ]
    )

    wl_k = entrada.cargas.Carga.sum() * gravity * 1000
    wc = entrada.contrapeso * gravity * 1000
    wg = entrada.peso_guindaste * gravity * 1000
    wv_i, wv_j = entrada.vento

    # Wload = np.array([wli, wlj, -wc - wg - wlift])

    r1_i, r1_j, r1_k = R_dict["R1"]
    r2_i, r2_j, r2_k = R_dict["R2"]
    r3_i, r3_j, r3_k = R_dict["R3"]
    r4_i, r4_j, r4_k = R_dict["R4"]
    r5_i, r5_j, r5_k = R_dict["R5"]

    stifiness_k = entrada.solo[1]
    area_i = entrada.solo[2]
    K = stifiness_k * area_i

    m23 = (r2_i - r3_i) * r4_j + (r3_j - r2_j) * r4_i - r2_i * r3_j + r2_j * r3_i
    m31 = (r3_i - r1_i) * r4_j + (r1_j - r3_j) * r4_i + r1_i * r3_j - r1_j * r3_i
    m12 = (r1_i - r2_i) * r4_j + (r2_j - r1_j) * r4_i - r1_i * r2_j + r1_j * r2_i
    m21 = (r2_i - r1_i) * r3_j + (r1_j - r2_j) * r3_i + r1_i * r2_j - r1_j * r2_i

    # fmt: off
    A = [[0.0, -r1_k,  r1_j,  r2_j,  r3_j,  r4_j],
         [r1_k,  0.0, -r1_i, -r2_i, -r3_i, -r4_i],
         [-r1_j, r1_i, 0.0,   0.0,   0.0,   0.0],
         [1.0,   0.0,  0.0,   0.0,   0.0,   0.0],
         [0.0,   1.0,  0.0,   0.0,   0.0,   0.0], 
         [0.0,   0.0,  1.0,   1.0,   1.0,   1.0],
         [0.0,   0.0,  m23,   m31,   m12,   m21]]
    # fmt: on

    A = np.array(A, dtype=float)

    momento_geom = (
        -r2_i * r3_j * r4_k
        + r1_i * r3_j * r4_k
        + r2_j * r3_i * r4_k
        - r1_j * r3_i * r4_k
        - r1_i * r2_j * r4_k
        + r1_j * r2_i * r4_k
        + r2_i * r3_k * r4_j
        - r1_i * r3_k * r4_j
        - r2_k * r3_i * r4_j
        + r1_k * r3_i * r4_j
        + r1_i * r2_k * r4_j
        - r1_k * r2_i * r4_j
        - r2_j * r3_k * r4_i
        + r1_j * r3_k * r4_i
        + r2_k * r3_j * r4_i
        - r1_k * r3_j * r4_i
        - r1_j * r2_k * r4_i
        + r1_k * r2_j * r4_i
        + r1_i * r2_j * r3_k
        - r1_j * r2_i * r3_k
        - r1_i * r2_k * r3_j
        + r1_k * r2_i * r3_j
        + r1_j * r2_k * r3_i
        - r1_k * r2_j * r3_i
    )

    B = np.array(
        [
            [r5_k * wv_j + r5_j * wl_k],
            [-(r5_k * wv_i + r5_i * wl_k)],
            [r5_j * wv_i - r5_i * wv_j],
            [wv_i],
            [wv_j],
            [wl_k + wg + wc],
            [K * momento_geom * 0],
        ],
        dtype=float,
    )

    X, residuals, rank, s = np.linalg.lstsq(A, B, rcond=None)

    return X, residuals, rank, s
