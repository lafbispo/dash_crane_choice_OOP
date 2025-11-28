import dash_bootstrap_components as dbc
from dash import html

class NavbarComponent:
    """
    Componente Navbar que encapsula o layout de cabeçalho do aplicativo.
    """
    
    def layout(self):
        """Retorna o objeto dbc.Navbar do cabeçalho."""
        return dbc.Navbar(
            dbc.Container(
                [
                    # Coluna do Título/Logo
                    dbc.Row(
                        [
                            dbc.Col(
                                html.A(
                                    html.H2("CraneChoice", className="text-light mb-0"),
                                    href="/",
                                    style={"textDecoration": "none"},
                                ),
                                align="center",
                            ),
                            # Coluna dos Itens de Navegação à Direita
                            dbc.Col(
                                dbc.Nav(
                                    [
                                        dbc.NavItem(dbc.NavLink("Link 1", href="#")),
                                        dbc.DropdownMenu(
                                            [dbc.DropdownMenuItem("Subitem 1")],
                                            nav=True,
                                            in_navbar=True,
                                            label="Menu",
                                        ),
                                    ],
                                    className="ms-auto", # Empurra para a direita (Bootstrap margin-start auto)
                                ),
                                width="auto",
                                align="center",
                            ),
                        ],
                        className="g-0 w-100",
                        align="center",
                    )
                ],
                fluid=True,
            ),
            color="primary",  # Define a cor de fundo (usando tema Bootstrap)
            dark=True,        # Torna o texto claro
            className="mb-4", # Adiciona margem na parte inferior
        )