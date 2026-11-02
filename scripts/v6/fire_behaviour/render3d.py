"""3D and map renders of the v5 ensemble at the range area: weighted median arrival (from P(burned by t)), draped on MRDEM terrain.
Outputs: interactive 3D HTML (plotly), static 3D PNGs, a viewshed map from the road head, and an approach-timeline chart.
Usage: python3 render3d.py GRIDS_DIR OUTDIR"""
import sys, os, json
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from pyproj import Transformer
import plotly.graph_objects as go
G, OUT = sys.argv[1:3]
minx, maxy, RES, H, W = np.load(os.path.join(G, "meta.npy")); H, W = int(H), int(W)
fw = pd.read_csv("/home/claude/cfb-wainwright-fire-archive-2/data/rubicon-ridge/model_v5/fit_weights.csv")
fw = fw[fw.weighted & (fw.weight > 0)].sort_values("weight", ascending=False); fw["cum"] = fw.weight.cumsum() / fw.weight.sum(); keep = fw[fw.cum <= .995]
MEDF = os.path.join(OUT, "median_arrival_min_after_1500.npy")
if os.path.exists(MEDF):
    med = np.load(MEDF)
else:
    TS = np.arange(0, 91, 1.0); P = np.zeros((len(TS), H, W)); wsum = 0.0
    for key, grp in keep.groupby(keep.case + "_" + keep.front.str.replace(":", "")):
        zs = np.load(os.path.join(G, f"scar_{key}.npz"))
        for _, r in grp.iterrows():
            A = zs[r.run.replace("|", "__")].astype("float32")
            P += r.weight * (A[None] <= TS[:, None, None]); wsum += r.weight
    P /= wsum
    med = np.full((H, W), np.nan)
    for k in range(len(TS) - 1, -1, -1): med = np.where(P[k] >= .5, TS[k], med)
np.save(os.path.join(OUT, "median_arrival_min_after_1500.npy"), med)
T = Transformer.from_crs(4326, "EPSG:3400", always_xy=True)
pts = {"Range 2 / Range 15 / road head (within 200 m)": (-110.9000, 52.7712)}
pxy = {k: T.transform(*v) for k, v in pts.items()}
z10 = np.load(os.path.join(OUT, "dem10_mrdem.npy")); F = 4
# 20 m terrain for 3D
z20 = np.nanmean(z10.reshape(H * 2, 2, W * 2, 2), axis=(1, 3))
med20 = np.repeat(np.repeat(med, 2, 0), 2, 1)
rx, ry = T.transform(-110.89965, 52.77045)
x0, x1, y0, y1 = rx - 3600, rx + 1400, ry - 2200, ry + 2000
X20 = minx + (np.arange(W * 2) + .5) * 20; Y20 = maxy - (np.arange(H * 2) + .5) * 20
ci = np.where((X20 >= x0) & (X20 <= x1))[0]; ri = np.where((Y20 >= y0) & (Y20 <= y1))[0]
Xs, Ys = np.meshgrid(X20[ci] - rx, Y20[ri] - ry); Zs = z20[np.ix_(ri, ci)]; Ms = med20[np.ix_(ri, ci)]
EX = 8.0
# colour: minutes after 15:00; <=28 = pre-front burned; nan = unburned
col = np.where(np.isnan(Ms), np.nan, np.clip(Ms, 20, 60))
colorscale = [[0, "#3f3f46"], [0.199, "#3f3f46"], [0.2, "#7f1d1d"], [0.45, "#ef4444"], [0.65, "#f59e0b"], [0.85, "#fde047"], [1, "#fef9c3"]]
surf = go.Surface(x=Xs, y=Ys, z=Zs * 1.0, surfacecolor=np.where(np.isnan(col), 15, col), cmin=15, cmax=60,
                  colorscale=[[0, "#6b8e23"], [0.111, "#6b8e23"], [0.112, "#3f3f46"], [0.29, "#3f3f46"], [0.3, "#7f1d1d"], [0.5, "#ef4444"], [0.7, "#f59e0b"], [0.88, "#fde047"], [1, "#fef9c3"]],
                  colorbar=dict(title="Model arrival<br>(min after 15:00)", tickvals=[15, 22, 30, 40, 50, 60], ticktext=["unburned", "before 15:28", "15:30", "15:40", "15:50", "16:00"]),
                  lighting=dict(ambient=.55, diffuse=.8, roughness=.9), showscale=True, name="terrain")
traces = [surf]
for t in range(30, 52, 2):
    m = (Ms >= t - .5) & (Ms < t + .5)
    if m.any(): traces.append(go.Scatter3d(x=Xs[m], y=Ys[m], z=Zs[m] + 1.5, mode="markers", marker=dict(size=1.6, color="white"), name=f"15:{t:02d} front", showlegend=(t % 4 == 2), hoverinfo="name"))
for k, (x, y) in pxy.items():
    i = np.argmin(np.abs(Y20[ri] - y)); j = np.argmin(np.abs(X20[ci] - x)); zz = Zs[i, j]
    traces.append(go.Scatter3d(x=[x - rx] * 2, y=[y - ry] * 2, z=[zz, zz + 12], mode="lines+markers+text", text=["", k], textposition="top center",
                               line=dict(color="cyan", width=5), marker=dict(size=[2, 5], color="cyan"), name=k, textfont=dict(color="white", size=13)))
fig = go.Figure(traces)
fig.update_layout(title="CFB Wainwright, Oct. 17: v5 weighted-median fire arrival on terrain (×8 vertical) · working model v5",
                  scene=dict(xaxis_title="m east of road head", yaxis_title="m north of road head", zaxis_title="elevation (m)",
                             aspectmode="manual", aspectratio=dict(x=1.25, y=1.05, z=0.35 * EX / 8), bgcolor="#0b1020",
                             camera=dict(eye=dict(x=-1.4, y=1.2, z=.75))),
                  paper_bgcolor="#0b1020", font=dict(color="#e5e7eb"), legend=dict(bgcolor="rgba(0,0,0,.4)"), margin=dict(l=0, r=0, t=40, b=0))
fig.write_html(os.path.join(OUT, "3d_fire_arrival_range_area.html"), include_plotlyjs="cdn")
# ---------- static 3D (matplotlib)
from matplotlib import cm
from matplotlib.colors import Normalize
cmap = matplotlib.colormaps["inferno_r"]
def fc(Ms):
    rgba = np.zeros(Ms.shape + (4,)); unb = np.isnan(Ms); pre = Ms <= 28
    rgba[unb] = (0.42, 0.56, 0.14, 1); rgba[pre & ~unb] = (0.25, 0.25, 0.27, 1)
    act = ~unb & ~pre; rgba[act] = cmap(Normalize(28, 60)(Ms[act]))
    return rgba
from matplotlib.colors import LightSource
ls = LightSource(azdeg=315, altdeg=35)
for nm, (el, az) in {"from_northwest": (32, 135), "from_southwest": (28, 225)}.items():
    f = plt.figure(figsize=(12, 8)); ax = f.add_subplot(111, projection="3d")
    st = 2
    rgb = ls.shade_rgb(fc(Ms[::st, ::st])[..., :3], Zs[::st, ::st], vert_exag=EX, blend_mode="soft")
    ax.plot_surface(Xs[::st, ::st], Ys[::st, ::st], Zs[::st, ::st], facecolors=rgb, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
    for k, (x, y) in pxy.items():
        i = np.argmin(np.abs(Y20[ri] - y)); j = np.argmin(np.abs(X20[ci] - x)); zz = Zs[i, j]
        ax.plot([x - rx] * 2, [y - ry] * 2, [zz, zz + 25], color="#06b6d4", lw=3); ax.text(x - rx, y - ry, zz + 27, "Range 2 / Range 15 /\nroad head", color="k", fontsize=9, weight="bold", bbox=dict(fc="w", alpha=.8, ec="none"))
    ax.set_box_aspect((1.25, 1.05, .33)); ax.view_init(el, az)
    ax.set_xlabel("m east of road head"); ax.set_ylabel("m north"); ax.set_zlabel("m")
    sm = cm.ScalarMappable(norm=Normalize(28, 60), cmap=cmap); cb = f.colorbar(sm, ax=ax, shrink=.5, pad=.08); cb.set_ticks([30, 35, 40, 45, 50, 55, 60]); cb.set_ticklabels(["15:30", "15:35", "15:40", "15:45", "15:50", "15:55", "16:00"]); cb.set_label("v5 weighted-median arrival")
    ax.set_title(f"Fire arrival after the wind shift, on terrain (×{EX:.0f} vertical), view {nm.replace('_', ' ')}\nDark grey: burned before the front (15:28). Green: did not burn. Working model v5.", fontsize=10)
    f.tight_layout(); f.savefig(os.path.join(OUT, f"fig_3d_{nm}.png"), dpi=140); plt.close(f)
print("ok")
