import sys
import getopt
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import beamforming

# Gestion des arguments
nb_antenas = [3, 10, 100]
d_antenas = 0.5

try:
    opts, args = getopt.getopt(sys.argv[1:], "d:n:", ["distance=", "n_antenas="])
    for opt, arg in opts:
        if opt in ("-d", "--distance"):
            d_antenas = float(arg)
        elif opt in ("-n", "--n_antenas"):
            nb_antenas = [int(x) for x in arg.split(",")]
except getopt.GetoptError:
    sys.exit(2)

# Paramètres du signal
sample_rate = 1e6
N = 2000  # 2000 échantillons suffisent largement pour stabiliser la variance
t = np.arange(N) / sample_rate
f_tone = 0.02e6
tx_signal = beamforming.create_IQ_signal(f_tone, t)

# Grille d'angles plus fine (pas de 5°) pour une animation plus fluide
angles = np.arange(-90, 95, 5)
theta_scan_deg = np.degrees(np.linspace(-np.pi, np.pi, 1000))
r_min_db = -35  # Plancher d'affichage fixe en dB

# Calcul des faisceaux
results = []
for theta in angles:
    frame_res = []
    for n_ant in nb_antenas:
        res = beamforming.calculate_beam(tx_signal, n_ant, d_antenas, theta)
        # On clippe les valeurs sous r_min_db pour un rendu polaire propre
        frame_res.append(np.clip(res, r_min_db, 0))
    results.append(frame_res)

# Création de la figure avec Subplots
subplot_titles = [f"<b>{nb} antennes</b> (d = {d_antenas}λ)" for nb in nb_antenas]
fig = make_subplots(
    rows=1, cols=len(nb_antenas),
    subplot_titles=subplot_titles,
    specs=[[{"type": "scatterpolar"}] * len(nb_antenas)],
    horizontal_spacing=0.08
)

colors = ["#00CC96", "#636EFA", "#EF553B"]

# Initialisation des traces (Angle 0)
for idx, n_ant in enumerate(nb_antenas):
    col_idx = idx + 1
    # Trace 1 : Diagramme de rayonnement (avec remplissage)
    fig.add_trace(
        go.Scatterpolar(
            r=results[0][idx],
            theta=theta_scan_deg,
            mode="lines",
            fill="toself",
            fillcolor=f"rgba{tuple(int(colors[idx].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.2,)}",
            line=dict(color=colors[idx], width=2),
            name=f"Gain ({n_ant} ant.)",
            showlegend=True
        ),
        row=1, col=col_idx
    )
    # Trace 2 : Consigne d'angle (Ligne rouge directe de r_min à 0 dB)
    fig.add_trace(
        go.Scatterpolar(
            r=[r_min_db, 0],
            theta=[angles[0], angles[0]],
            mode="lines+markers",
            line=dict(color="#FF2B2B", width=2.5, dash="dot"),
            marker=dict(size=[0, 8], color="#FF2B2B"),
            name="Direction cible" if idx == 0 else None,
            showlegend=(idx == 0)
        ),
        row=1, col=col_idx
    )

# Configuration des axes polaires (0° en haut, -90° à gauche, +90° à droite)
polar_config = dict(
    sector=[-90, 90], # Utile avec rotation=90 sous certaines versions, sinon [0, 180]
    angularaxis=dict(
        rotation=90,
        direction="clockwise",
        tickmode="array",
        tickvals=np.arange(-90, 91, 30),
        ticktext=[f"{a}°" for a in np.arange(-90, 91, 30)]
    ),
    radialaxis=dict(
        range=[r_min_db, 0],
        tickvals=[-30, -20, -10, -3, 0],
        ticktext=["-30 dB", "-20 dB", "-10 dB", "-3 dB", "0 dB"],
        angle=0,
        tickfont=dict(size=10, color="gray")
    )
)

# Application du style polaire à chaque sous-graphe (cadran supérieur 0..180 dans le repère écran)
polar_config["sector"] = [0, 180]
for idx in range(len(nb_antenas)):
    key = "polar" if idx == 0 else f"polar{idx+1}"
    fig.update_layout(**{key: polar_config})

# Construction des frames d'animation et des étapes du Slider
frames = []
slider_steps = []

for i, theta in enumerate(angles):
    frame_data = []
    for idx in range(len(nb_antenas)):
        frame_data.append(go.Scatterpolar(r=results[i][idx], theta=theta_scan_deg))
        frame_data.append(go.Scatterpolar(r=[r_min_db, 0], theta=[theta, theta]))
    
    frame_name = f"angle_{theta}"
    frames.append(
        go.Frame(
            data=frame_data,
            name=frame_name,
            layout=go.Layout(title_text=f"<b> Formation de faisceau (Beamforming)</b> — Espacement : {d_antenas}λ | Angle d'incidence : <b>{theta}°</b>")
        )
    )
    
    slider_steps.append(
        dict(
            args=[[frame_name], dict(frame=dict(duration=150, redraw=True), mode="immediate", transition=dict(duration=0))],
            label=f"{theta}°",
            method="animate"
        )
    )

fig.frames = frames

# Ajout des boutons Play/Pause et du Slider pédagogique
fig.update_layout(
    template="plotly_dark",
    title=dict(
        text=f"<b>Formation de faisceau (Beamforming)</b> — Espacement : {d_antenas}λ | Angle d'incidence : <b>{angles[0]}°</b>",
        x=0.5,
        font=dict(size=18)
    ),
    updatemenus=[
        dict(
            type="buttons",
            showactive=False,
            x=0.05, y=-0.05,
            direction="left",
            buttons=[
                dict(
                    label="▶ Lecture",
                    method="animate",
                    args=[None, dict(frame=dict(duration=300, redraw=True), fromcurrent=True, transition=dict(duration=100))]
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
                )
            ]
        )
    ],
    sliders=[
        dict(
            active=0,
            yanchor="top", xanchor="left",
            currentvalue=dict(font=dict(size=14), prefix="Angle d'incidence : ", visible=True, xanchor="right"),
            transition=dict(duration=100),
            pad=dict(b=10, t=30),
            len=0.8, x=0.18, y=-0.02,
            steps=slider_steps
        )
    ]
)

fig.write_html(f"beamforming_d_{d_antenas}_{nb_antenas}.html")