import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator # Importação necessária

import matplotlib.pyplot as plt
import scienceplots

#plt.style.use('science')
#plt.style.use(['science','ieee'])
from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator, SmoothBivariateSpline
# import scienceplots # Removido para garantir compatibilidade se não instalado

# --- SEU CÓDIGO DE PREPARAÇÃO DE DADOS ---
db = pd.read_excel('guindaste_80TON.xlsx')
x_orig = db.Raio.values
z_orig = db.Lanca.values
y_orig = np.sin(np.arccos(x_orig/z_orig)) * z_orig
w_orig = db.Carga.values

# Pontos de dados originais (limpos)
pts_clean = np.column_stack((x_orig, y_orig))

# --- 1. CRIAR A MALHA (GRID) 2D COMPLETA ---
x_grid = np.linspace(np.min(x_orig) * 1.02, np.max(x_orig) * .98, 100)
y_grid = np.linspace(np.min(y_orig) * 1.02, np.max(y_orig) * .98, 100)

X, Y = np.meshgrid(x_grid, y_grid)
pontos_grade = np.column_stack((X.flatten(), Y.flatten()))

# --- 2. MÁSCARA DE REGIÃO VÁLIDA (Convex Hull) ---
tri = Delaunay(pts_clean)
mascara_dentro_flat = tri.find_simplex(pontos_grade) >= 0
mascara_dentro_2d = mascara_dentro_flat.reshape(X.shape) 

# --- 3. INTERPOLAR E APLICAR A MÁSCARA ---
interp = LinearNDInterpolator(pts_clean, w_orig)
#interp_spline = SmoothBivariateSpline(x_orig, y_orig, w_orig, s=1)
W_grid = interp(X, Y)

#W_grid = interp_spline.ev(X, Y)
W_grid_mascarado = np.where(mascara_dentro_2d, W_grid, np.nan)

# --- 4. PLOTAR COM CONTOURF E CONTOUR ---

fig, ax = plt.subplots(figsize=(10, 8))

# 4a. Plotar o preenchimento de Carga (W)
nivel=30
CS_W = ax.contourf(X, Y, W_grid_mascarado, levels=nivel, cmap='jet', extend='both')
cbar = fig.colorbar(CS_W, ax=ax, label='Carga [ton]')

#CT_W = ax.contour(X, Y, W_grid_mascarado, levels=nivel,  colors='gray', linewidths=1., linestyles='-')
#ax.clabel(CT_W, inline=True, fontsize=10, fmt='%1.0f ton', colors='gray')

# 4b. Plotar linhas de contorno (Z = Lança)
Z_grid = np.sqrt(X**2 + Y**2)
Z_grid_mascarado = np.where(mascara_dentro_2d, Z_grid, np.nan)

CS_Z = ax.contour(X, Y, Z_grid_mascarado, levels=30, colors='red', linewidths=1., linestyles=':')
ax.clabel(CS_Z, inline=True, fontsize=8, fmt='L=%1.0f m', colors='red')

# Adicionar linha fantasma para a LEGENDA da Lança
_ = ax.plot([], [], color='red', linestyle=':', linewidth=1., label='Lança (Z) [m]')

# 4c. Configurações Finais
ax.set_xlabel('Raio [m]')
ax.set_ylabel('Altura [m]')
ax.set_title('Região Operacional Válida do Guindaste - Carga (Cores) e Lança (Linhas)')

plt.suptitle('Guindaste 90ton', fontsize=16, fontweight='bold')
ax.grid(True, linestyle='-', alpha=0.6)

# ⭐️ AJUSTE DA GRADAÇÃO DOS EIXOS (2 em 2 m)
ax.xaxis.set_major_locator(MultipleLocator(2))
ax.yaxis.set_major_locator(MultipleLocator(2))

ax.legend(loc='lower right')

plt.show()