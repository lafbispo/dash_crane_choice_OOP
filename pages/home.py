from dash import html, Output, Input, dcc
import dash_bootstrap_components as dbc

# Importa a instância global do aplicativo
from app import app

# Importa o componente da tabela
from components.tabela_component import TabelaDadosComponent
from components.dropdown_component import DropdownButtonComponent
import os

from components.plotly_component import OperationalMapComponent
import pandas as pd
import numpy as np
import plotly.graph_objects as go


dropdown_comp = DropdownButtonComponent(
    app,
    id_base="meu-dropdown",
    options=["Guindaste 90ton", "Guindaste - sem dados"],
    label="Escolha o Guindaste",
)


@app.callback(
    Output("div-grafico-operacional", "children"),
    [
        Input(dropdown_comp.dropdown_id, "label"),
        Input("dados-iniciais-data-table", "data"),  # tabela
    ],
)
def update_graph(selected, table_data):

    # Converte table_data em DataFrame
    df_table = pd.DataFrame(table_data) if table_data else pd.DataFrame()

    # ---- SELEÇÃO INVÁLIDA ----
    if selected is None or selected.startswith("Selecionar"):
        return html.Div("Selecione um guindaste acima.", className="text-muted")

    # ---- SEM DADOS ----
    if selected == "Guindaste - sem dados":
        return html.Div(
            "Nenhum dado disponível para esse guindaste.", className="text-warning"
        )

    # ---- GUINDASTE 90 TON ----
    if selected == "Guindaste 90ton":

        # carrega dados
        try:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            DATA_PATH = os.path.join(BASE_DIR, "..", "data", "guindaste_80TON.xlsx")
            df = pd.read_excel(DATA_PATH)

        except Exception as e:
            return html.Div(f"Erro ao carregar dados: {e}", className="text-danger")

        # cria figura do mapa
        mapa = OperationalMapComponent(df, title="Mapa Operacional 90 ton")
        fig = mapa.fig

        # ========== PROCESSAR TABELA ==========
        try:
            if not df_table.empty:

                df_table["Raio_conv"] = pd.to_numeric(
                    df_table.get("Raio"), errors="coerce"
                )
                df_table["Lanca_conv"] = pd.to_numeric(
                    df_table.get("Lanca"), errors="coerce"
                )
                df_table["Carga_conv"] = pd.to_numeric(
                    df_table.get("Carga"), errors="coerce"
                )

                df_valid = df_table.dropna(subset=["Raio_conv", "Lanca_conv"]).copy()

                if not df_valid.empty:

                    x = df_valid["Raio_conv"].to_numpy()
                    z = df_valid["Lanca_conv"].to_numpy()

                    # evita sqrt negativa
                    y = np.sqrt(np.maximum(z**2 - x**2, 0.0))

                    customdata = np.stack(
                        [x, y, df_valid["Carga_conv"].to_numpy()], axis=-1
                    )

                    carga_grafico = mapa.interp(list(zip(x, y)))
                    carga_ponto = df_valid["Carga_conv"]
                    ok_mask = carga_ponto <= carga_grafico
                    nok_mask = ~ok_mask

                    # --- Pontos APROVADOS ---
                    if ok_mask.any():
                        fig.add_trace(
                            go.Scatter(
                                x=x[ok_mask],
                                y=y[ok_mask],
                                mode="markers+text",
                                text=df_valid["Ponto"].to_numpy()[ok_mask],
                                textfont=dict(
                                    color="black",  # ← cor do texto acima do ponto
                                    size=12,
                                ),
                                textposition="top center",
                                marker=dict(
                                    size=10,
                                    color="green",
                                    symbol="circle",
                                    line=dict(width=1, color="black"),
                                ),
                                name="Aprovados",
                                customdata=np.stack(
                                    [
                                        x[ok_mask],
                                        y[ok_mask],
                                        carga_ponto[ok_mask],
                                        carga_grafico[ok_mask],
                                    ],
                                    axis=-1,
                                ),
                                hovertemplate=(
                                    "<b>Ponto:</b> %{text}<br>"
                                    "<b>Raio (x):</b> %{customdata[0]:.2f} m<br>"
                                    "<b>Altura (y):</b> %{customdata[1]:.2f} m<br>"
                                    "<b>Carga Ponto:</b> %{customdata[2]:.2f}<br>"
                                    "<b>Carga Máx:</b> %{customdata[3]:.2f}<br>"
                                    "<b>Status:</b> <span style='color:white'><b>OK</b></span><br>"
                                    "<extra></extra>"
                                ),
                            )
                        )

                    # --- Pontos REPROVADOS ---
                    if nok_mask.any():
                        fig.add_trace(
                            go.Scatter(
                                x=x[nok_mask],
                                y=y[nok_mask],
                                mode="markers+text",
                                text=df_valid["Ponto"].to_numpy()[nok_mask],
                                textfont=dict(
                                    color="black",  # ← cor do texto acima do ponto
                                    size=12,
                                ),
                                textposition="top center",
                                marker=dict(
                                    size=10,
                                    color="red",
                                    symbol="x",
                                    line=dict(width=1, color="black"),
                                ),
                                name="Reprovados",
                                customdata=np.stack(
                                    [
                                        x[nok_mask],
                                        y[nok_mask],
                                        carga_ponto[nok_mask],
                                        carga_grafico[nok_mask],
                                    ],
                                    axis=-1,
                                ),
                                hovertemplate=(
                                    "<b>Ponto:</b> %{text}<br>"
                                    "<b>Raio (x):</b> %{customdata[0]:.2f} m<br>"
                                    "<b>Altura (y):</b> %{customdata[1]:.2f} m<br>"
                                    "<b>Carga Ponto:</b> %{customdata[2]:.2f}<br>"
                                    "<b>Carga Máx:</b> %{customdata[3]:.2f}<br>"
                                    "<b>Status:</b> <span style='color:white'><b>NÃO OK</b></span><br>"
                                    "<extra></extra>"
                                ),
                            )
                        )

                fig.update_layout(
                    legend=dict(
                        orientation="h",  # horizontal
                        yanchor="top",
                        y=-0.2,  # abaixo do eixo X
                        xanchor="center",
                        x=0.5,  # centralizado horizontalmente
                    )
                )

        except Exception as e:
            print("Erro ao processar pontos da tabela:", e)

        return dcc.Graph(figure=fig)

    # ---- fallback ----
    return html.Div("Seleção inválida.", className="text-danger")


# Instancia o componente da tabela, passando a instância do app e um ID base
tab1Columns = [
    {"name": "Área içam.", "id": "Ponto", "editable": True},
    {"name": "Lança", "id": "Lanca", "editable": True, "type": "numeric"},
    {"name": "Raio", "id": "Raio", "editable": True, "type": "numeric"},
    {"name": "Carga [ton]", "id": "Carga", "editable": True, "type": "numeric"},
]

initial_data = [{"Ponto": "Aquecedor Fab.", "Lanca": 32, "Raio": 12.50, "Carga": 8.0}]
tabela_vendas = TabelaDadosComponent(
    app, id_base="dados-iniciais", columns=tab1Columns, initial_data=initial_data
)


def layout():
    return dbc.Container(
        [
            html.H3("Início - Instruções Básicas", className="mb-4"),
            dbc.Row(
                [
                    # ===== COLUNA ESQUERDA =====
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H4("Configurações"),
                                    html.Hr(),
                                    tabela_vendas.layout(),
                                    html.Br(),
                                    dropdown_comp.layout(),
                                ]
                            ),
                            className="shadow h-100",
                        ),
                        md=5,
                    ),
                    # ===== COLUNA DIREITA =====
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H4("Mapa Operacional"),
                                    html.Hr(),
                                    html.Div(
                                        id="div-grafico-operacional",
                                        style={
                                            "height": "70vh",  # controla altura visível
                                        },
                                    ),
                                ]
                            ),
                            className="shadow h-100",
                        ),
                        md=7,
                    ),
                ],
                className="g-3",  # espaçamento entre colunas
            ),
        ],
        fluid=True,
    )
