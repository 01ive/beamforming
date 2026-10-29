import sys
import getopt
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import beamforming

# 1. Lecture des paramètres CLI
nb_antenas = [3, 5, 10]
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

# 2. Génération du signal de base (f = 20 kHz)
sample_rate = 1e6
N = 2500
t = np.arange(N) / sample_rate
f_tone = 0.02e6
tx_signal = beamforming.create_IQ_signal(f_tone, t)

# 3. Paramètres de balayage
angles = np.arange(-90, 95, 5)
n_scan = 720
theta_scan_deg = np.degrees(np.linspace(-np.pi, np.pi, n_scan))
r_min_db = -35

results_noisy = []
results_ideal = []

for theta in angles:
    frame_noisy = []
    frame_ideal = []
    for n_ant in nb_antenas:
        res_n = beamforming.calculate_beam(tx_signal, n_ant, d_antenas, theta, n_scan)
        res_i = beamforming.calculate_ideal_beam(n_ant, d_antenas, theta, n_scan)
        frame_noisy.append(np.clip(res_n, r_min_db, 0))
        frame_ideal.append(np.clip(res_i, r_min_db, 0))
    results_noisy.append(frame_noisy)
    results_ideal.append(frame_ideal)

# 4. Fonction utilitaire pour la géométrie physique (Antennes + Front d'onde + Retards)
def compute_wavefront_geometry(theta_deg, ant_x, max_span):
    theta_rad = np.radians(theta_deg)
    ux, uy = np.sin(theta_rad), np.cos(theta_rad)
    wx, wy = np.cos(theta_rad), -np.sin(theta_rad)

    # 1. Rayon d'incidence (du centre vers la source)
    ray_len = max_span * 0.8
    ray_x = [0, ray_len * ux]
    ray_y = [0, ray_len * uy]

    # 2. Fronts d'onde (plans d'équiphase espacés de 1 lambda)
    wf_x, wf_y = [], []
    half_width = max_span * 0.75
    for dist in [0.0, 1.0, 2.0, 3.0]:
        cx, cy = dist * ux, dist * uy
        wf_x.extend([cx - half_width * wx, cx + half_width * wx, None])
        wf_y.extend([cy - half_width * wy, cy + half_width * wy, None])

    # 3. Segments de différence de marche (retard géométrique d*sin(theta))
    delay_x, delay_y = [], []
    for x_i in ant_x:
        proj_dist = x_i * np.sin(theta_rad)
        px = x_i - proj_dist * ux
        py = 0.0 - proj_dist * uy
        delay_x.extend([x_i, px, None])
        delay_y.extend([0.0, py, None])

    return ray_x, ray_y, wf_x, wf_y, delay_x, delay_y

max_ant = max(nb_antenas)
ant_x = (np.arange(max_ant) - (max_ant - 1) / 2.0) * d_antenas
ant_y = np.zeros(max_ant)
max_span = max((max_ant - 1) * d_antenas, 3.0)
n_cols = len(nb_antenas)

# 5. Création dynamique de la grille
subplot_titles = [f"<b>{nb} antennes</b> (d = {d_antenas}λ)" for nb in nb_antenas] + [
    "<b>Géométrie physique : Fronts d'onde (bleu), Direction d'arrivée (rouge) et Différence de marche Δd = x·sin(θ) (jaune)</b>"
]

fig = make_subplots(
    rows=2, cols=n_cols,
    row_heights=[0.60, 0.40],
    vertical_spacing=0.14,
    horizontal_spacing=0.07,
    subplot_titles=subplot_titles,
    specs=[
        [{"type": "scatterpolar"}] * n_cols,
        [{"type": "xy", "colspan": n_cols}] + [None] * (n_cols - 1)
    ]
)

colors = ["#00CC96", "#636EFA", "#AB63FA", "#FFA15A"]

# 6. Traces polaires (Haut)
for idx, n_ant in enumerate(nb_antenas):
    col_idx = idx + 1
    c_hex = colors[idx % len(colors)]
    rgb_tuple = tuple(int(c_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    # Courbe théorique sans bruit
    fig.add_trace(
        go.Scatterpolar(
            r=results_ideal[0][idx], theta=theta_scan_deg, mode="lines",
            line=dict(color="rgba(220, 220, 220, 0.5)", width=1.5, dash="dash"),
            name="Théorique (sans bruit)" if idx == 0 else None, showlegend=(idx == 0)
        ), row=1, col=col_idx
    )
    # Courbe avec bruit
    fig.add_trace(
        go.Scatterpolar(
            r=results_noisy[0][idx], theta=theta_scan_deg, mode="lines", fill="toself",
            fillcolor=f"rgba{rgb_tuple + (0.22,)}", line=dict(color=c_hex, width=2),
            name=f"Gain ({n_ant} ant.)", showlegend=True
        ), row=1, col=col_idx
    )
    # Aiguille rouge (Angle d'incidence de la source)
    fig.add_trace(
        go.Scatterpolar(
            r=[r_min_db, 0], theta=[angles[0], angles[0]], mode="lines+markers",
            line=dict(color="#FF3333", width=2.5, dash="dot"), marker=dict(size=[0, 9], color="#FF3333"),
            name="Angle source (θ)" if idx == 0 else None, showlegend=(idx == 0)
        ), row=1, col=col_idx
    )

# 7. Traces géométriques (Bas)
ray_x0, ray_y0, wf_x0, wf_y0, del_x0, del_y0 = compute_wavefront_geometry(angles[0], ant_x, max_span)

fig.add_trace(
    go.Scatter(
        x=wf_x0, y=wf_y0, mode="lines",
        line=dict(color="#00D4FF", width=2, dash="dash"),
        name="Fronts d'onde (crêtes espacées de λ)"
    ), row=2, col=1
)

fig.add_trace(
    go.Scatter(
        x=del_x0, y=del_y0, mode="lines",
        line=dict(color="#FFD700", width=3),
        name="Retard géométrique (Δd = d·sin θ)"
    ), row=2, col=1
)

fig.add_trace(
    go.Scatter(
        x=ray_x0, y=ray_y0, mode="lines+markers",
        line=dict(color="#FF3333", width=3),
        marker=dict(size=[0, 10], symbol="circle", color="#FF3333"),
        name="Direction de propagation"
    ), row=2, col=1
)

fig.add_trace(
    go.Scatter(
        x=ant_x, y=ant_y, mode="markers+text",
        marker=dict(size=12, symbol="triangle-up", color="#FFD700", line=dict(width=1, color="white")),
        text=[f"A{k+1}" for k in range(max_ant)], textposition="bottom center",
        name=f"Antennes ({max_ant})"
    ), row=2, col=1
)

# 8. Configuration des axes avec FOND NOIR EXPLICITE
polar_config = dict(
    bgcolor="#111111",  # Fond noir à l'intérieur des demi-cercles polaires
    sector=[0, 180],
    angularaxis=dict(
        rotation=90,
        direction="clockwise",
        tickvals=np.arange(-90, 91, 30),
        ticktext=[f"{a}°" for a in np.arange(-90, 91, 30)],
        gridcolor="#333333",
        linecolor="#444444"
    ),
    radialaxis=dict(
        range=[r_min_db, 0],
        tickvals=[-30, -20, -10, -3, 0],
        ticktext=["-30 dB", "-20 dB", "-10 dB", "-3 dB", "0 dB"],
        angle=0,
        tickfont=dict(size=10, color="lightgray"),
        gridcolor="#333333",
        linecolor="#444444"
    )
)
for idx in range(n_cols):
    key = "polar" if idx == 0 else f"polar{idx+1}"
    fig.update_layout(**{key: polar_config})

fig.update_xaxes(
    title_text="Axe du réseau d'antennes (en longueurs d'onde λ)",
    range=[-max_span, max_span],
    gridcolor="#282828", zeroline=True, zerolinecolor="#555555",
    row=2, col=1
)
fig.update_yaxes(
    title_text="Distance (λ)",
    range=[-max_span * 0.45, max_span * 0.85],
    scaleanchor="x", scaleratio=1,
    gridcolor="#282828", zeroline=True, zerolinecolor="#555555",
    row=2, col=1
)

# 9. Construction des Frames
frames = []
slider_steps = []

for i, theta in enumerate(angles):
    frame_data = []
    for idx in range(n_cols):
        frame_data.append(go.Scatterpolar(r=results_ideal[i][idx], theta=theta_scan_deg))
        frame_data.append(go.Scatterpolar(r=results_noisy[i][idx], theta=theta_scan_deg))
        frame_data.append(go.Scatterpolar(r=[r_min_db, 0], theta=[theta, theta]))
    
    rx, ry, wfx, wfy, delx, dely = compute_wavefront_geometry(theta, ant_x, max_span)
    frame_data.append(go.Scatter(x=wfx, y=wfy))
    frame_data.append(go.Scatter(x=delx, y=dely))
    frame_data.append(go.Scatter(x=rx, y=ry))
    frame_data.append(go.Scatter(x=ant_x, y=ant_y))

    frame_name = f"angle_{theta}"
    frames.append(go.Frame(data=frame_data, name=frame_name, layout=go.Layout(
        title_text=f"<b>Formation de faisceau (Beamforming)</b> — Espacement : d = {d_antenas}λ | Incidence : <b>θ = {theta}°</b>"
    )))
    slider_steps.append(dict(
        args=[[frame_name], dict(frame=dict(duration=150, redraw=True), mode="immediate", transition=dict(duration=0))],
        label=f"{theta}°",
        method="animate"
    ))

fig.frames = frames

# 10. Mise en page finale avec thème sombre verrouillé
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="#111111",  # Fond noir global de la page
    plot_bgcolor="#111111",   # Fond noir du graphique cartésien du bas
    font=dict(color="#EEEEEE"),
    height=820,
    title=dict(
        text=f"<b>Formation de faisceau (Beamforming)</b> — Espacement : d = {d_antenas}λ | Incidence : <b>θ = {angles[0]}°</b>",
        x=0.5,
        font=dict(size=18)
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="center", x=0.5),
    updatemenus=[
        dict(
            type="buttons",
            showactive=False,
            x=0.02, y=-0.06,
            direction="left",
            bgcolor="#222222",
            bordercolor="#555555",
            font=dict(color="white"),
            buttons=[
                dict(
                    label="▶ Lecture",
                    method="animate",
                    args=[None, dict(frame=dict(duration=250, redraw=True), fromcurrent=True, transition=dict(duration=80))]
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
            currentvalue=dict(font=dict(size=14, color="white"), prefix="Angle d'incidence (θ) : ", visible=True, xanchor="right"),
            transition=dict(duration=80),
            pad=dict(b=10, t=25),
            len=0.82, x=0.16, y=-0.04,
            bgcolor="#222222",
            bordercolor="#555555",
            font=dict(color="white"),
            steps=slider_steps
        )
    ]
)

output_filename = f"beamforming_d_{d_antenas}_{nb_antenas}.html"
fig.write_html(output_filename)
print(f"Animation générée avec succès : {output_filename}")