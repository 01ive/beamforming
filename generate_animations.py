import sys
import getopt

try:
    opts, args = getopt.getopt(sys.argv[1:],"d:n:",["distance=","n_antenas="])
except getopt.GetoptError:
    sys.exit(2)

nb_antenas = [3, 5, 10]
d_antenas = 0.5

for opt, arg in opts:
    if opt in ("-d", "--distance"):
        d_antenas = float(arg)
    elif opt in ("-n", "--n_antenas"):
        nb_antenas = arg

# %% [markdown]
# # Generate beamforming animation

# %%
import numpy as np
import plotly.graph_objects as go
import beamforming

# %% [markdown]
# ## Create base signal tx_signal with f = 20kHz

# %%
sample_rate = 1e6
N = 10000 # number of samples to simulate

# Create a tone to act as the transmitter signal
t = np.arange(N)/sample_rate # time vector
f_tone = 0.02e6
tx_signal = beamforming.create_IQ_signal(f_tone, t)

# %% [markdown]
# ## Generate all beams

# %%
angles = np.arange(-90, 100, 10)

results = list()

for theta in angles:
    results.append(list())
    for id_antena in nb_antenas:
        results[-1].append(beamforming.calculate_beam(tx_signal, id_antena, d_antenas, theta))

# %% [markdown]
# ## Generate azimuth

# %%
theta_scan_deg = np.degrees(np.linspace(-1*np.pi, np.pi, 1000))

scan = list()

for i, theta in enumerate(angles):
    scan.append(list())
    for id_antena in range(len(nb_antenas)):
        scan[-1].append(list([None]*len(results[i][id_antena])))
        index = np.absolute(theta_scan_deg-theta).argmin()
        scan[-1][-1][index-1] = results[i][id_antena].min()
        scan[-1][-1][index] = 0

print(np.array(results).shape)
print(np.array(scan).shape)

# %% [markdown]
# ## Plot results

# %%
fig = go.Figure()
subplot_titles = [str(nb)+' antenas' for nb in nb_antenas]
fig = go.Figure().set_subplots(1, 3, horizontal_spacing=0.1, subplot_titles=subplot_titles,
            specs=[ [{"type": "scatterpolar"}, {"type": "scatterpolar"}, {"type": "scatterpolar"}] ])

# subplot 1
fig.add_trace(go.Scatterpolar(r=results[0][0], theta=theta_scan_deg, name='scan', mode='lines', showlegend=True), row=1, col=1)
fig.add_trace(go.Scatterpolar(r=scan[0], theta=theta_scan_deg, name='beam', mode='lines', showlegend=True, 
                                  textposition="top right", textfont=dict(color="Red") ), row=1, col=1)
fig.update_layout(polar = dict(radialaxis_angle = 90, angularaxis = dict(direction = "clockwise" ), sector=[0, 180]) )

# subplot 2
fig.add_trace(go.Scatterpolar(r=results[0][1], theta=theta_scan_deg, name='scan2', mode='lines', showlegend=True), row=1, col=2)
fig.add_trace(go.Scatterpolar(r=scan[1], theta=theta_scan_deg, name='beam2', mode='lines', showlegend=True, 
                                  textposition="top right", textfont=dict(color="Red") ), row=1, col=2)
fig.update_layout(polar2 = dict(radialaxis_angle = 90, angularaxis = dict(direction = "clockwise" ), sector=[0, 180]) )

# subplot 3
fig.add_trace(go.Scatterpolar(r=results[0][2], theta=theta_scan_deg, name='scan3', mode='lines', showlegend=True), row=1, col=3)
fig.add_trace(go.Scatterpolar(r=scan[2], theta=theta_scan_deg, name='beam3', mode='lines', showlegend=True, 
                                  textposition="top right", textfont=dict(color="Red") ), row=1, col=3)
fig.update_layout(polar3 = dict(radialaxis_angle = 90, angularaxis = dict(direction = "clockwise" ), sector=[0, 180]) )

# animation
base_text = "d=" + str(d_antenas) + " angle="
frames = list()
for i, r in enumerate(results):
    frames.append( go.Frame(data=[  go.Scatterpolar(r=r[0]), go.Scatterpolar(r=scan[i][0]),
                                    go.Scatterpolar(r=r[1]), go.Scatterpolar(r=scan[i][1]), 
                                    go.Scatterpolar(r=r[2]), go.Scatterpolar(r=scan[i][2]) ], 
                                    layout=go.Layout(title_text=base_text+str(angles[i])+"°") ) )

# button and style
fig.update_layout(updatemenus=[dict(type="buttons", buttons=[dict(label="Play", method="animate", args=[None, dict(frame=dict(duration=2000))]),
                               dict(label="Pause", method="animate", args=[[None], dict(frame=dict(duration=0), 
                                                                                        mode="immediate",
                                                                                        transition=dict(duration=0))])])])
fig.update(frames=frames)

fig.update_layout(template="plotly_dark", title_text=base_text+str(angles[0])+"°")
fig.write_html(base_text + str(nb_antenas) + ".html")


