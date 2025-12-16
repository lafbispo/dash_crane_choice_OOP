import dash
from dash import dash_table, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc


class TabelaDadosComponent:
    """
    Componente reutilizável de DataTable com:
    - título customizável
    - opção de permitir ou não adicionar linhas
    - opção de permitir ou não deletar linhas
    """

    def __init__(
        self,
        app,
        id_base,
        columns=None,
        initial_data=None,
        title_color="text-dark",
        allow_add_rows=True,
        row_deletable=True,
    ):
        self.app = app
        self.id_base = id_base
        self.title_color = title_color

        self.allow_add_rows = allow_add_rows
        self.row_deletable = row_deletable

        # IDs
        self.table_id = f"{id_base}-data-table"
        self.add_row_button_id = f"{id_base}-add-row-btn"
        self.output_feedback_id = f"{id_base}-output-feedback"

        # Colunas e dados
        if columns is None:
            self.columns = [
                {"name": "Produto", "id": "Produto", "editable": True},
                {
                    "name": "Quantidade",
                    "id": "Quantidade",
                    "editable": True,
                    "type": "numeric",
                },
                {
                    "name": "Valor Unitário",
                    "id": "Valor_Unitario",
                    "editable": True,
                    "type": "numeric",
                },
            ]
            self.initial_data = [
                {"Produto": "Exemplo", "Quantidade": 10, "Valor_Unitario": 5.5}
            ]
        else:
            self.columns = columns
            self.initial_data = initial_data if initial_data is not None else []

        self._register_callbacks()

    # ======================================================
    # Layout
    # ======================================================
    def layout(self):

        children = [
            html.H4(
                f"Tabela: {self.id_base.capitalize()}",
                className=(
                    f"mb-3 text-{self.title_color}"
                    if not self.title_color.startswith("#")
                    else "mb-3"
                ),
                style=(
                    {"color": self.title_color}
                    if self.title_color.startswith("#")
                    else {}
                ),
            ),
            dash_table.DataTable(
                id=self.table_id,
                columns=self.columns,
                data=self.initial_data,
                editable=True,
                row_deletable=self.row_deletable,
                style_table={"overflowX": "auto", "width": "100%"},
                style_cell={
                    "minWidth": "120px",
                    "width": "120px",
                    "maxWidth": "120px",
                    "textAlign": "center",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
                style_header={
                    "backgroundColor": "#2a4260",
                    "color": "white",
                    "fontWeight": "bold",
                },
                style_data_conditional=[
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "rgb(248, 248, 248)",
                    }
                ],
                export_format="csv",
            ),
        ]

        # Botão adicionar linha (condicional)
        if self.allow_add_rows:
            children.append(
                dbc.Button(
                    "Adicionar Linha",
                    id=self.add_row_button_id,
                    color="primary",
                    className="mt-3",
                )
            )

        children.append(
            html.Div(id=self.output_feedback_id, className="mt-3 text-success")
        )

        return dbc.Tab(
            html.Div(children),
            label=self.id_base.capitalize(),
            tab_id=self.id_base,
        )

    # ======================================================
    # Callbacks
    # ======================================================
    def _register_callbacks(self):

        # Adicionar linha somente se permitido
        if self.allow_add_rows:

            @self.app.callback(
                Output(self.table_id, "data"),
                Input(self.add_row_button_id, "n_clicks"),
                State(self.table_id, "data"),
                State(self.table_id, "columns"),
                prevent_initial_call=True,
            )
            def add_row(n_clicks, rows, columns):
                if rows is None:
                    rows = []

                rows.append({c["id"]: None for c in columns})
                return rows

        # Feedback
        @self.app.callback(
            Output(self.output_feedback_id, "children"),
            Input(self.table_id, "data_timestamp"),
            State(self.table_id, "data"),
        )
        def display_data_status(timestamp, data):
            if timestamp is not None and data is not None:
                return f"Dados atualizados. Total de {len(data)} registros."
            return ""
