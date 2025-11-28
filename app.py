# app.py
import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

server = app.server

#Para rodar esse arquivo deve-se fazer através do arquivo index.py
#python index.py