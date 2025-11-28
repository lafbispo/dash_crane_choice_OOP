import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator
from dash import html


class OperationalMapComponent:

    def __init__(self, df, title="Mapa Operacional", title_color=None, grid_step=2):
        """
        df: DataFrame contendo colunas obrigatórias:
            - Raio
            - Lanca
            - Carga
        """

        self.df = df
        self.title = title
        self.title_color = title_color
        self.grid_step = grid_step

        # Chamadas internas
        self._process_data()
        self.fig = self._build_figure()

    # =============================================================
    # ------------ 1) PROCESSAMENTO COMPLETO DOS DADOS -------------
    # =============================================================
    def _process_data(self):

        db = self.df
        x = db.Raio.values
        z = db.Lanca.values

        # Altura Y calculada fisicamente
        y = np.sin(np.arccos(x / z)) * z
        w = db.Carga.values

        self.pts = np.column_stack((x, y))

        # Malha automática
        self.x_grid = np.linspace(np.min(x) * 1.02, np.max(x) * 0.98, 120)
        self.y_grid = np.linspace(np.min(y) * 1.02, np.max(y) * 0.98, 120)

        X, Y = np.meshgrid(self.x_grid, self.y_grid)
        self.X, self.Y = X, Y

        # Convex hull mask
        tri = Delaunay(self.pts)
        mask_flat = tri.find_simplex(np.column_stack((X.flatten(), Y.flatten()))) >= 0
        self.mask = mask_flat.reshape(X.shape)

        # Interpolação
        interp = LinearNDInterpolator(self.pts, w)
        W = interp(X, Y)
        self.interp = interp
        self.W = np.where(self.mask, W, np.nan)

        # Linhas de lança
        Z = np.sqrt(X**2 + Y**2)
        self.Z = np.where(self.mask, Z, np.nan)

    # =============================================================
    # ------------ 2) GERA A FIGURA PLOTLY COMPLETA ---------------
    # =============================================================
    def _build_figure(self):

        fig = go.Figure()

        # Contourf da carga
        fig.add_trace(
            go.Contour(
                x=self.x_grid,
                y=self.y_grid,
                z=self.W,
                colorscale="Jet",
                contours=dict(showlines=False),
                colorbar=dict(title="Carga [ton]"),
            )
        )

        # Linhas da lança
        fig.add_trace(
            go.Contour(
                x=self.x_grid,
                y=self.y_grid,
                z=self.Z,
                name="Lança",
                contours=dict(
                    coloring="none",
                    showlabels=True,
                    labelfont=dict(size=10, color="red"),
                ),
                line=dict(color="red", dash="dot"),
                showscale=False,
            )
        )

        # Layout
        fig.update_layout(
            title=self.title,
            xaxis_title="Raio [m]",
            yaxis_title="Altura [m]",
            height=750,
            template="plotly_white",
        )

        # Grid
        fig.update_xaxes(dtick=self.grid_step, showgrid=True)
        fig.update_yaxes(dtick=self.grid_step, showgrid=True)

        return fig

    # =============================================================
    # ------------ 3) RETORNA COMPONENTE PARA O DASH --------------
    # =============================================================
    def layout(self):

        title_style = {}
        title_class = "mb-3"

        if self.title_color:
            if self.title_color.startswith("#"):
                title_style["color"] = self.title_color
            else:
                title_class += f" text-{self.title_color}"

        return html.Div(
            [html.H4(self.title, className=title_class, style=title_style), self.fig]
        )
