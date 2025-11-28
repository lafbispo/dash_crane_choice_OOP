# index.py
from app import app
from dash import html, dcc
from dash.dependencies import Input, Output

from components.sidebar_component import SidebarComponent
from components.navbar_component import NavbarComponent

# Import das páginas
from pages.home import layout as home_layout
#from pages.vendas import layout as vendas_layout
#from pages.marketing import layout as marketing_layout

sidebar = SidebarComponent()
navbar = NavbarComponent()

app.layout = html.Div([
    dcc.Location(id='url'),
    sidebar.layout(),
    html.Div(
        [
            navbar.layout(),
            html.Div(id='page-content', className='p-4')
        ],
        id='main-content-wrapper',
        style=sidebar.CONTENT_STYLE
    )
], id='app-wrapper')


# 📌 Router das páginas
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):

    if pathname == '/':
        return home_layout()

    elif pathname == '/vendas':
        return vendas_layout()

    elif pathname == '/marketing':
        return marketing_layout()

    else:
        return html.Div([
            html.H1("404 - Página não encontrada"),
            html.P(f"Rota inválida: {pathname}")
        ])


if __name__ == '__main__':
    app.run(debug=True)
