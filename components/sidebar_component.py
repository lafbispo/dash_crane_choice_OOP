import dash_bootstrap_components as dbc
from dash import html

class SidebarComponent:
    """
    Componente Sidebar que encapsula o layout de navegação.
    Este componente não possui callbacks internos, sendo puramente de layout.
    """

    # --- Estilos CSS como atributos de classe ---
    SIDEBAR_WIDTH = "16rem"

    SIDEBAR_STYLE = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": SIDEBAR_WIDTH,
        "padding": "2rem 1rem",
        "background-color": "#c3ccd4",
        "zIndex": 1000, # Garante que fique acima do conteúdo
    }

    # Estilo necessário para empurrar o conteúdo principal
    CONTENT_STYLE = {
        "margin-left": SIDEBAR_WIDTH,
        "padding": "0",
        "background-color": "#ffffff",
        "min-height": "100vh"
    }
    # -------------------------------------------

    def layout(self):
        """Retorna o objeto html.Div do sidebar."""
        return html.Div(
            [
                html.H2("Menu", className="display-6 text-primary"),
                html.Hr(),
                dbc.Nav(
                    [
                        # Note que active="exact" é fundamental para destacar a página atual
                        dbc.NavLink("Página Inicial", href="/", active="exact", className="my-1"),
                        #dbc.NavLink("Relatório de Vendas", href="/vendas", active="exact", className="my-1"),
                        #dbc.NavLink("Relatório de Marketing", href="/marketing", active="exact", className="my-1"),
                    ],
                    vertical=True,
                    pills=True,
                ),
            ],
            style=self.SIDEBAR_STYLE,
        )
