import dash
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc


class DropdownButtonComponent:
    """
    Componente reutilizável de Dropdown Button (dbc.DropdownMenu)
    com callback interno para atualizar o label do botão com a opção selecionada.
    """

    def __init__(self, app, id_base, options=None, label="Selecionar Opção"):
        self.app = app
        self.id_base = id_base
        self.label = label

        # IDs únicos
        self.dropdown_id = f"{id_base}-dropdown"
        self.output_id = f"{id_base}-output"
        self.output_graph_id = f"{id_base}-output-graph"  # <<< NOVO

        # Lista de opções
        self.options = (
            options if options is not None else ["Opção 1", "Opção 2", "Opção 3"]
        )

        # Registrar callbacks
        self._register_callbacks()

    def layout(self):
        """Retorna o layout pronto para ser usado em Tabs ou Containers."""

        menu_items = [
            dbc.DropdownMenuItem(opt, id=f"{self.dropdown_id}-{i}")
            for i, opt in enumerate(self.options)
        ]

        return html.Div(
            [
                html.H4(self.label, className="mb-3"),
                dbc.DropdownMenu(
                    # O label inicial será 'self.label' e será atualizado pelo callback
                    label=self.label,
                    children=menu_items,
                    color="primary",
                    className="mb-3",
                    id=self.dropdown_id,
                ),
                # O output mostra o item selecionado
                html.Div(id=self.output_id, className="text-info"),
                # <<< Onde o gráfico será exibido
                # html.Div(id=self.output_graph_id),
            ]
        )

    def _register_callbacks(self):
        """
        Registra callbacks automaticamente para todos os itens do dropdown.
        Atualiza tanto o rótulo do botão quanto o Div de saída.
        """

        # Inputs dinâmicos dos itens (usamos n_clicks como gatilho)
        inputs = [
            Input(f"{self.dropdown_id}-{i}", "n_clicks")
            for i in range(len(self.options))
        ]

        @self.app.callback(
            [
                Output(self.dropdown_id, "label"),  # 1. Atualiza o rótulo do botão
                Output(self.output_id, "children"),
            ],  # 2. Atualiza o Div de saída
            inputs,
        )
        def update_output(*clicks):
            ctx = dash.callback_context

            # Se não houver clique, retorna o estado inicial (ou a última seleção)
            if not ctx.triggered:
                # Retorna o label inicial e nada no output
                return self.label, ""

            # Pega o ID do componente que disparou o callback
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

            # Percorre as opções para encontrar a correspondência
            for i, opt in enumerate(self.options):
                expected_id = f"{self.dropdown_id}-{i}"

                # Verifica se o ID disparado corresponde ao ID esperado
                if triggered_id == expected_id:
                    new_label = opt
                    feedback = f"Selecionado: {opt}"
                    return new_label, feedback

            # Fallback (caso o item clicado não seja encontrado, o que é improvável)
            return self.label, "Erro ao identificar seleção."
