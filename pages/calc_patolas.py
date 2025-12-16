# calc_patolas.py
import numpy as np
import pandas as pd

from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from scipy.spatial import ConvexHull

from app import app
from components.tabela_component import TabelaDadosComponent
from models.inputs_guindaste import EntradaGuindaste
from shapely.geometry import Polygon, Point, LineString
from engine.calc_reactions import calc_reactions

# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================


def convex_hull_xy(df):
    df_xy = df[["X", "Y"]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(df_xy) < 3:
        return None
    hull = ConvexHull(df_xy.to_numpy())
    return df_xy.to_numpy()[hull.vertices]


def plot_vista_superior(
    patolas_df: pd.DataFrame,
    cm: pd.Series,
    lanca: pd.Series,
    angulo_deg: float,
    vento: pd.Series | None = None,
    reacoes: dict | None = None,  # <<< NOVO
):

    fig = go.Figure()

    cores = []

    for _, row in patolas_df.iterrows():
        if not isinstance(reacoes, dict):
            # antes do cálculo → todas azuis
            cores.append("blue")
        else:
            r = reacoes.get(row["Patola"], 0.0)
            cores.append("red" if r < 0 else "blue")

    # ======================
    # Patolas
    # ======================
    fig.add_trace(
        go.Scatter(
            x=patolas_df["X"],
            y=patolas_df["Y"],
            mode="markers+text",
            text=patolas_df["Patola"],
            marker=dict(size=12, color=cores),
            name="Patolas",
        )
    )

    # ======================
    # Convex Hull
    # ======================
    hull_pts = convex_hull_xy(patolas_df)

    if hull_pts is not None:
        hull_closed = np.vstack([hull_pts, hull_pts[0]])
        fig.add_trace(
            go.Scatter(
                x=hull_closed[:, 0],
                y=hull_closed[:, 1],
                mode="lines",
                line=dict(color="blue", width=2),
                fill="toself",
                fillcolor="rgba(0,0,255,0.05)",
                name="Polígono de Apoio",
            )
        )

    # ======================
    # Centro de Massa
    # ======================
    fig.add_trace(
        go.Scatter(
            x=[cm["Xcm"]],
            y=[cm["Ycm"]],
            mode="markers",
            marker=dict(size=14, color="red", symbol="x"),
            name="Centro de Massa",
        )
    )

    # ======================
    # Lança (projeção)
    # ======================
    R = float(lanca["Raio"])
    theta = np.deg2rad(angulo_deg)

    x_lanca = [cm["Xcm"], cm["Xcm"] + R * np.cos(theta)]
    y_lanca = [cm["Ycm"], cm["Ycm"] + R * np.sin(theta)]

    fig.add_trace(
        go.Scatter(
            x=x_lanca,
            y=y_lanca,
            mode="lines+markers",
            line=dict(width=3, color="black"),
            marker=dict(size=6),
            name="Lança (projeção)",
        ),
    )

    # ======================
    # Vetores de Vento (unitários)
    # ======================
    if vento is not None:
        Vi = float(vento.get("Vi", 0.0))
        Vj = float(vento.get("Vj", 0.0))

        Vnorm = np.hypot(Vi, Vj)

        if Vnorm > 0:
            vi_u = Vi / Vnorm
            vj_u = Vj / Vnorm

            # ponto médio do raio
            xm = cm["Xcm"] + 0.5 * R * np.cos(theta)
            ym = cm["Ycm"] + 0.5 * R * np.sin(theta)

            Lvec = R * 0.3  # comprimento visual (fixo)

            # Vento em X (i)
            fig.add_trace(
                go.Scatter(
                    x=[xm, xm + Lvec * vi_u],
                    y=[ym, ym],
                    mode="lines+markers",
                    line=dict(color="purple", width=3),
                    marker=dict(size=6),
                    name="Vento i (X)",
                )
            )

            # Vento em Y (j)
            fig.add_trace(
                go.Scatter(
                    x=[xm, xm],
                    y=[ym, ym + Lvec * vj_u],
                    mode="lines+markers",
                    line=dict(color="orange", width=3),
                    marker=dict(size=6),
                    name="Vento j (Y)",
                )
            )

    # ======================
    # Layout
    # ======================
    fig.update_layout(
        title="Vista Superior – Patolas e Lança",
        xaxis_title="X [m]",
        yaxis_title="Y [m]",
        template="plotly_white",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        legend=dict(orientation="h", y=-0.2),
    )

    fig.update_xaxes(showgrid=True, zeroline=True)
    fig.update_yaxes(showgrid=True, zeroline=True)

    return fig


def plot_lanca_3d(cm, lanca, angulo_deg):
    L = float(lanca["Lanca"])
    R = float(lanca["Raio"])
    theta = np.deg2rad(angulo_deg)

    x0, y0, z0 = cm["Xcm"], cm["Ycm"], cm["Zcm"]

    x1 = x0 + R * np.cos(theta)
    y1 = y0 + R * np.sin(theta)
    z1 = z0 + np.sqrt(max(L**2 - R**2, 0))

    fig = go.Figure()

    # Lança
    fig.add_trace(
        go.Scatter3d(
            x=[x0, x1],
            y=[y0, y1],
            z=[z0, z1],
            mode="lines+markers",
            line=dict(width=6, color="black"),
            name="Lança",
        )
    )

    # Carga (vertical)
    fig.add_trace(
        go.Scatter3d(
            x=[x1, x1],
            y=[y1, y1],
            z=[z1, 0],
            mode="lines",
            line=dict(color="red", dash="dot"),
            name="Carga",
        )
    )

    fig.update_layout(
        title="Modelo 3D da Lança (EN 13000 / FEM)",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data",
        ),
        template="plotly_white",
    )

    return fig


def construir_entrada(
    pat, cm, lanca, carga, vento, solo, angulo, pesos
) -> EntradaGuindaste:

    df_pat = pd.DataFrame(pat).apply(pd.to_numeric, errors="coerce")
    df_cm = pd.DataFrame(cm).iloc[0]
    df_lanca = pd.DataFrame(lanca).iloc[0]
    df_pesos = pd.DataFrame(pesos).iloc[0]
    df_carga = pd.DataFrame(carga)
    df_vento = pd.DataFrame(vento).iloc[0]
    df_solo = pd.DataFrame(solo).iloc[0]

    return EntradaGuindaste(
        patolas=df_pat,
        centro_massa=df_cm,
        lanca=df_lanca,
        angulo_giro_deg=float(angulo),
        peso_guindaste=float(df_pesos["Peso_Guindaste"]),
        contrapeso=float(df_pesos["Contrapeso"]),
        cargas=df_carga,
        vento=df_vento,
        solo=df_solo,
    )


def calcular_estabilidade(entrada: EntradaGuindaste) -> str:
    """
    Placeholder de cálculo.
    Aqui entra sua engenharia.
    """
    X, residuos, rank, s = calc_reactions(entrada)

    reacoes = {
        "P1": float(X[2]),
        "P2": float(X[3]),
        "P3": float(X[4]),
        "P4": float(X[5]),
    }

    if min(X) > 0:
        status = "OK"
        return "Sistema estável (exemplo)"
    else:
        status = "REPROVED"
        return "Sistema instável (exemplo)"


# =====================================================
# TABELAS
# =====================================================

tabela_patolas = TabelaDadosComponent(
    app,
    "patolas",
    [
        {"name": "Patola", "id": "Patola"},
        {"name": "X [m]", "id": "X", "type": "numeric"},
        {"name": "Y [m]", "id": "Y", "type": "numeric"},
        {"name": "Z [m]", "id": "Z", "type": "numeric"},
    ],
    [
        {"Patola": "P1", "X": 2, "Y": 2, "Z": 0},
        {"Patola": "P2", "X": -2, "Y": 2, "Z": 0},
        {"Patola": "P3", "X": -2, "Y": -2, "Z": 0},
        {"Patola": "P4", "X": 2, "Y": -2, "Z": 0},
    ],
    allow_add_rows=False,
    row_deletable=False,
)

tabela_cm = TabelaDadosComponent(
    app,
    "centro-massa",
    [
        {"name": "Xcm [m]", "id": "Xcm", "type": "numeric"},
        {"name": "Ycm [m]", "id": "Ycm", "type": "numeric"},
        {"name": "Zcm [m]", "id": "Zcm", "type": "numeric"},
    ],
    [{"Xcm": 0.0, "Ycm": 0.0, "Zcm": 4.0}],
    allow_add_rows=False,
    row_deletable=False,
)

tabela_lanca = TabelaDadosComponent(
    app,
    "lanca",
    [
        {"name": "Comprimento L [m]", "id": "Lanca", "type": "numeric"},
        {"name": "Raio R [m]", "id": "Raio", "type": "numeric"},
    ],
    [{"Lanca": 32.0, "Raio": 12.0}],
    allow_add_rows=False,
    row_deletable=False,
)

tabela_carga = TabelaDadosComponent(
    app,
    "carga",
    [
        {"name": "Designação", "id": "Desig"},
        {"name": "Carga [ton]", "id": "Carga", "type": "numeric"},
    ],
    [{"Desig": "Carga Principal", "Carga": 10.0}],
)

tabela_vento = TabelaDadosComponent(
    app,
    "vento",
    [
        {"name": "Vento i (X)", "id": "Vi", "type": "numeric"},
        {"name": "Vento j (Y)", "id": "Vj", "type": "numeric"},
    ],
    [{"Vi": 0.0, "Vj": 0.0}],
    allow_add_rows=False,
    row_deletable=False,
)

tabela_solo = TabelaDadosComponent(
    app,
    "solo",
    [
        {"name": "Solo", "id": "solo"},
        {"name": "Rigidez [MPa]", "id": "soil_k", "type": "numeric"},
        {"name": "Área [m²]", "id": "soil_area_i", "type": "numeric"},
    ],
    [{"solo": "Comum", "soil_k": 1.0, "soil_area_i": 1.0}],
    allow_add_rows=False,
    row_deletable=False,
)

tabela_pesos = TabelaDadosComponent(
    app,
    "pesos",
    [
        {"name": "Peso do Guindaste [ton]", "id": "Peso_Guindaste", "type": "numeric"},
        {"name": "Contrapeso [ton]", "id": "Contrapeso", "type": "numeric"},
    ],
    [{"Peso_Guindaste": 60.0, "Contrapeso": 12.0}],
    allow_add_rows=False,
    row_deletable=False,
)

# =====================================================
# CALLBACK – VALIDAÇÃO
# =====================================================


@app.callback(
    Output("btn-calcular", "disabled"),
    Output("msg-validacao", "children"),
    Input("patolas-data-table", "data"),
    Input("centro-massa-data-table", "data"),
    Input("lanca-data-table", "data"),
    Input("carga-data-table", "data"),
    Input("vento-data-table", "data"),
    Input("solo-data-table", "data"),
    Input("angulo-giro", "value"),
    Input("pesos-data-table", "data"),
)
def validar_entrada(pat, cm, lanca, carga, vento, solo, angulo, pesos):
    entrada = construir_entrada(pat, cm, lanca, carga, vento, solo, angulo, pesos)

    if entrada.is_valid():
        return False, dbc.Alert("Dados válidos ✔", color="success")
    return True, dbc.Alert(
        "Preencha corretamente todos os dados antes de calcular.",
        color="warning",
    )


# =====================================================
# CALLBACK – CÁLCULO
# =====================================================


@app.callback(
    Output("store-reacoes", "data"),
    Output("resultado-calculo", "children"),
    Input("btn-calcular", "n_clicks"),
    State("patolas-data-table", "data"),
    State("centro-massa-data-table", "data"),
    State("lanca-data-table", "data"),
    State("carga-data-table", "data"),
    State("vento-data-table", "data"),
    State("solo-data-table", "data"),
    State("pesos-data-table", "data"),
    State("angulo-giro", "value"),
    prevent_initial_call=True,
)
def executar_calculo(_, pat, cm, lanca, carga, vento, solo, pesos, angulo):

    entrada = construir_entrada(pat, cm, lanca, carga, vento, solo, angulo, pesos)

    if not entrada.is_valid():
        return None, dbc.Alert("Erro de validação.", color="danger")

    X, _, _, _ = calc_reactions(entrada)

    # 🔴 ajuste aqui conforme sua ordem real das incógnitas
    reacoes = {
        "P1": float(X[2]),
        "P2": float(X[3]),
        "P3": float(X[4]),
        "P4": float(X[5]),
    }

    mensagem = [
        html.B("Cálculo concluído"),
        html.Br(),
        html.Ul(
            [
                html.Li(f"P1 = {reacoes['P1']:.2f} N"),
                html.Li(f"P2 = {reacoes['P2']:.2f} N"),
                html.Li(f"P3 = {reacoes['P3']:.2f} N"),
                html.Li(f"P4 = {reacoes['P4']:.2f} N"),
            ]
        ),
    ]

    status = (
        dbc.Alert(mensagem, color="success")
        if min(reacoes.values()) >= 0
        else dbc.Alert(mensagem + ["⚠ Perda de contato"], color="danger")
    )

    return reacoes, status


# ====================================================
# GRÁFICOS
# ====================================================


@app.callback(
    Output("grafico-vista-superior", "figure"),
    Output("grafico-3d-estrutural", "figure"),
    Input("patolas-data-table", "data"),
    Input("centro-massa-data-table", "data"),
    Input("lanca-data-table", "data"),
    Input("vento-data-table", "data"),
    Input("angulo-giro", "value"),
    Input("store-reacoes", "data"),  # <<< NOVO
    Input("btn-calcular", "n_clicks"),
)
def atualizar_graficos(pat, cm, lanca, vento, angulo, reacoes, _):

    # ------------------
    # DataFrames
    # ------------------
    df_pat = pd.DataFrame(pat)
    cm_s = pd.DataFrame(cm).iloc[0]
    lanca_s = pd.DataFrame(lanca).iloc[0]
    vento_s = pd.DataFrame(vento).iloc[0] if vento else None

    # ------------------
    # Gráfico 2D
    # ------------------
    fig_superior = plot_vista_superior(
        df_pat, cm_s, lanca_s, angulo, vento_s, reacoes=reacoes
    )

    # ------------------
    # Gráfico 3D (placeholder por enquanto)
    # ------------------
    fig_3d = go.Figure()
    fig_3d.update_layout(
        title="Estrutura 3D (em desenvolvimento)",
        template="plotly_white",
    )

    return fig_superior, fig_3d


# =====================================================
# LAYOUT
# =====================================================


def layout():
    return dbc.Container(
        [
            dcc.Store(id="store-reacoes"),
            html.H3("Guindaste – Estabilidade nas Patolas"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            tabela_patolas.layout(),
                            html.Hr(),
                            tabela_cm.layout(),
                            html.Hr(),
                            tabela_lanca.layout(),
                            html.H5("Giro do Guindaste"),
                            dcc.Slider(
                                id="angulo-giro",
                                min=0,
                                max=360,
                                step=1,
                                value=0,
                                marks={0: "0°", 180: "180°", 360: "360°"},
                            ),
                            html.Hr(),
                            tabela_carga.layout(),
                            html.Hr(),
                            tabela_vento.layout(),
                            html.Hr(),
                            tabela_solo.layout(),
                            html.Hr(),
                            tabela_pesos.layout(),
                            html.Hr(),
                            dbc.Button(
                                "Calcular Estabilidade",
                                id="btn-calcular",
                                color="success",
                                disabled=True,
                            ),
                            html.Div(id="msg-validacao", className="mt-2"),
                            html.Div(id="resultado-calculo", className="mt-3"),
                        ],
                        md=5,
                    ),
                    dbc.Col(
                        [
                            dcc.Graph(
                                id="grafico-vista-superior", style={"height": "55vh"}
                            ),
                            dcc.Graph(
                                id="grafico-3d-estrutural", style={"height": "55vh"}
                            ),
                        ],
                        md=7,
                    ),
                ]
            ),
        ],
        fluid=True,
    )
