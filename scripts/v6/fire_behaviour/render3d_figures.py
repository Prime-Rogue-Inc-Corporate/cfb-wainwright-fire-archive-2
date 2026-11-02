"""Broader 3D snapshots with representative figures, plus an animated interactive 3D (plotly, time slider).
Fire: before the front, v5 pre-front case v4b (start ~05:00; the four cases carry equal weight); after it, the v5 weighted-median
arrival. Figures are REPRESENTATIVE and NOT TO SCALE: DND has not said how many soldiers were where. Following Rutland (Oct. 18):
most of C Company was on the grenade range (Range 2), about ten on the attack/pairs serial (Range 15 / road head). Range 11 shows
a prone AGL firing line in the morning panel only. Figures are not shown reacting, and are left out of the arrival panel.
Usage: python3 render3d_figures.py GRIDS_DIR ARCHIVE_1 ARCHIVE_2 OUTDIR SPRITES"""
import sys, os, json, math
import numpy as np, pandas as pd, rasterio, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d import proj3d
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from pyproj import Transformer
from PIL import Image, ImageFilter
import plotly.graph_objects as go
G, A1, A2, OUT, SP = sys.argv[1:6]
minx, maxy, RES, H, W = np.load(os.path.join(G, "meta.npy")); H, W = int(H), int(W)
med = np.load(os.path.join(OUT, "median_arrival_min_after_1500.npy"))
with rasterio.open(os.path.join(A2, "data/rubicon-ridge/model_v5/prefront/arrival_prefront_v4b_2x_lb3.0_0500.tif")) as r:
    pre = np.full((H, W), np.nan, "float32")
    reproject(r.read(1), pre, src_transform=r.transform, src_crs=r.crs, src_nodata=np.nan, dst_transform=from_origin(minx, maxy, RES, RES), dst_crs="EPSG:3400", dst_nodata=np.nan, resampling=Resampling.nearest)
pre_min = (pre - 15) * 60                                   # minutes after 15:00 (negative = morning)
arr = np.where(np.isfinite(med) & (med > 28), med, np.where(np.isfinite(pre_min) & (pre_min <= 28), pre_min, np.where(np.isfinite(med), med, np.nan)))
z10 = np.load(os.path.join(OUT, "dem10_mrdem.npy")); z20 = np.nanmean(z10.reshape(H * 2, 2, W * 2, 2), axis=(1, 3))
arr20 = np.repeat(np.repeat(arr, 2, 0), 2, 1)
T = Transformer.from_crs(4326, "EPSG:3400", always_xy=True); rx, ry = T.transform(-110.89965, 52.77045)
rso = pd.read_csv(os.path.join(A1, "data/reference/range_standing_orders_2024/rso_points.csv")).dropna(subset=["lat"]).set_index("name")
RP = {k: tuple(np.subtract(T.transform(rso.loc[k, "lon"], rso.loc[k, "lat"]), (rx, ry))) for k in ("Range 2", "Range 10", "Range 11", "Range 13", "Range 15", "Range 22")}
X20 = minx + (np.arange(W * 2) + .5) * 20 - rx; Y20 = maxy - (np.arange(H * 2) + .5) * 20 - ry
x0, x1, y0, y1 = -5200, 3600, -3800, 2400                   # broadened: anti-tank/AGL ranges to the far end of the burn
ci = np.where((X20 >= x0) & (X20 <= x1))[0]; ri = np.where((Y20 >= y0) & (Y20 <= y1))[0]
Xs, Ys = np.meshgrid(X20[ci], Y20[ri]); Zs = z20[np.ix_(ri, ci)]; As = arr20[np.ix_(ri, ci)]
Zs = np.where(np.isfinite(Zs), Zs, np.nanmean(Zs))
def zat(x, y): return float(Zs[np.argmin(np.abs(Y20[ri] - y)), np.argmin(np.abs(X20[ci] - x))])
# ---------- representative figures
rng = np.random.default_rng(17)
def scatter_pts(cx, cy, n, spread, gap):
    pts = []
    while len(pts) < n:
        x, y = cx + rng.uniform(-spread, spread), cy + rng.uniform(-spread, spread)
        if all(math.hypot(x - a, y - b) >= gap for a, b in pts): pts.append((x, y))
    return pts
grenade = scatter_pts(*RP["Range 2"], 20, 110, 30)
pairs = scatter_pts(*RP["Range 15"], 10, 70, 22)
agl = [(RP["Range 11"][0], RP["Range 11"][1] + (k - 5.5) * 14) for k in range(12)]
SPR = {f[:-4]: Image.open(os.path.join(SP, f)).convert("RGBA") for f in os.listdir(SP) if f.endswith(".png")}
def paste_figs(png, ax, fig, figs, dpi):
    fig.canvas.draw(); im = Image.open(png).convert("RGBA"); Hpx = im.height
    items = []
    for (x, y, kind) in figs:
        x2, y2, _ = proj3d.proj_transform(x, y, zat(x, y), ax.get_proj())
        px, py = ax.transData.transform((x2, y2)); items.append((py, px, Hpx - py, kind))
    for _, px, py, kind in sorted(items, key=lambda t: -t[0]):
        sp = SPR[kind]; h = 22 if not kind.startswith("prone") else 9
        k = h / sp.height; s = sp.resize((max(1, int(sp.width * k)), max(1, int(sp.height * k))), Image.LANCZOS)
        a = s.split()[3]; halo = a.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.6))
        dark = Image.new("RGBA", s.size, (10, 10, 12, 0)); dark.putalpha(halo.point(lambda v: int(v * .95)))
        pos = (int(px - s.width / 2), int(py - s.height)); im.paste(dark, pos, dark); im.paste(s, pos, s)
    im.convert("RGB").save(png)
from PIL import ImageDraw, ImageFont, ImageOps
CAP = ("Prime Rogue Inc. · working model v5. Fire before 15:28: v5 pre-front case (start ~5 a.m.); after: weighted median of 1,425 runs. Terrain MRDEM-30, height exaggerated.",
       "Figures: representative, NOT to scale; DND has not said how many soldiers were where. Yellow = burning now, red = last 3 min",
       "(morning panel: last 75 min), black = burned, tan = unburned cured grass.")
def finish(p, title):
    im = Image.open(p).convert("RGB"); g = ImageOps.invert(im.convert("L")).point(lambda v: 255 if v > 8 else 0); bb = g.getbbox()
    im = im.crop((max(bb[0] - 20, 0), max(bb[1] - 20, 0), min(bb[2] + 20, im.width), min(bb[3] + 20, im.height)))
    k = 1500 / im.width; im = im.resize((1500, int(im.height * k)), Image.LANCZOS)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30); fr = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    out = Image.new("RGB", (1500, im.height + 132), "white"); out.paste(im, (0, 55)); d = ImageDraw.Draw(out)
    d.text((20, 12), title, font=fb, fill="#1e3452"); d.text((20, im.height + 62), CAP[0], font=fr, fill="#333"); d.text((20, im.height + 84), CAP[1], font=fr, fill="#333"); d.text((20, im.height + 106), CAP[2], font=fr, fill="#333")
    out.save(p)
# ---------- colours
ls = LightSource(azdeg=300, altdeg=40)
def colours(t):
    rgb = np.zeros(As.shape + (3,)); unb = ~(np.isfinite(As) & (As <= t))
    rgb[:] = (0.66, 0.60, 0.40)                                    # cured grass / unburned
    wa, wh = (25, 75) if t < 0 else (1, 3)                          # morning fire moves slowly: wider "burning" windows
    burned = np.isfinite(As) & (As <= t - wh); rgb[burned] = (0.16, 0.15, 0.15)
    hot = np.isfinite(As) & (As > t - wh) & (As <= t - wa); rgb[hot] = (0.75, 0.18, 0.05)
    act = np.isfinite(As) & (As > t - wa) & (As <= t); rgb[act] = (1.0, 0.72, 0.12)
    return ls.shade_rgb(rgb, Zs, vert_exag=4, blend_mode="soft", dx=20, dy=20)
PANELS = [(-2 * 60 - 43, "12:17 · Landsat sees ~2 km of fire in the AGL impact area"), (28, "15:28 · cold front reaches the fire; wind swings to the NW"),
          (33, "15:33 · flames first in sight from the road head (median)"), (37, "15:37 · ~300 m from the road head"),
          (40, "15:40 · ~100 m from the road head"), (42, "15:42 · fire reaches the road head and Range 15 (median); figures not shown")]
def hm(t): m = int(round(15 * 60 + t)); return f"{m // 60}:{m % 60:02d}"
st = 2; DPI = 110
files = []
for k, (t, title) in enumerate(PANELS):
    fig = plt.figure(figsize=(12, 7.2), dpi=DPI); ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(Xs[::st, ::st], Ys[::st, ::st], Zs[::st, ::st], facecolors=colours(t)[::st, ::st], rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
    ax.set_box_aspect((1.4, 1.0, .13), zoom=1.02); ax.view_init(30, 235); ax.set_axis_off()
    for name, (x, y) in RP.items():
        z = zat(x, y); lab = {"Range 2": "R2 grenade · R15 / road head", "Range 15": "", "Range 11": "R11 AGL", "Range 10": "R10 anti-tank", "Range 13": "R13 anti-tank", "Range 22": "R22 HHAA"}[name]
        ax.scatter([x], [y], [z + 2], s=14, c="#22d3ee", edgecolors="k", depthshade=False, zorder=9)
        if not lab: continue
        ax.text(x - (1100 if name == "Range 2" else 0), y + (700 if name == "Range 2" else 120), z + 9, lab, fontsize=8, color="w", weight="bold", ha="center", bbox=dict(fc="#1e3452", ec="none", alpha=.8, pad=1.5), zorder=10)
    fig.subplots_adjust(0, 0, 1, 1)
    p = os.path.join(OUT, f"fig3d_snap_{k + 1}_{hm(t).replace(':', '')}.png"); fig.savefig(p, dpi=DPI)
    figs = []
    if t < 0: figs = [(x, y, "prone_right") for x, y in agl]
    elif t < 42: figs = [(x, y, ("standing_" if i % 4 else "kneeling_") + ("right" if i % 2 else "left")) for i, (x, y) in enumerate(grenade + pairs)]
    paste_figs(p, ax, fig, figs, DPI); plt.close(fig); finish(p, title); files.append(p)
# contact sheet
ims = [Image.open(f) for f in files]; w, h = ims[0].size
sheet = Image.new("RGB", (w * 2, h * 3), "white")
for i, im in enumerate(ims): sheet.paste(im, ((i % 2) * w, (i // 2) * h))
sheet.save(os.path.join(OUT, "fig3d_snapshots_sheet.png"))
# ---------- interactive animated 3D (40 m)
s2 = 3; Xp, Yp, Zp, Ap = Xs[::s2, ::s2], Ys[::s2, ::s2], Zs[::s2, ::s2], As[::s2, ::s2]
def cval(t):  # 0 unburned, 1 burned, 2 hot, 3 burning
    v = np.zeros(Ap.shape); f = np.isfinite(Ap)
    v[f & (Ap <= t - 3)] = 1; v[f & (Ap > t - 3) & (Ap <= t - 1)] = 2; v[f & (Ap > t - 1) & (Ap <= t)] = 3; return v
cs = [[0, "#a89966"], [.249, "#a89966"], [.25, "#2a2626"], [.499, "#2a2626"], [.5, "#c02e0d"], [.749, "#c02e0d"], [.75, "#ffb81f"], [1, "#ffb81f"]]
times = [-163] + list(range(26, 47, 2))
def figtrace(t):
    pts = [(x, y) for x, y in agl] if t < 0 else ((grenade + pairs) if t < 42 else [])
    return go.Scatter3d(x=[p[0] for p in pts], y=[p[1] for p in pts], z=[zat(*p) + 6 for p in pts], mode="markers",
                        marker=dict(size=4, color="#22d3ee", line=dict(color="black", width=1)), name="Representative figures (not to scale)")
labels = go.Scatter3d(x=[v[0] for v in RP.values()], y=[v[1] for v in RP.values()], z=[zat(*v) + 40 for v in RP.values()], mode="text",
                      text=["R2 grenade", "R10 anti-tank", "R11 AGL", "R13 anti-tank", "R15 / road head", "R22 HHAA"], textfont=dict(color="white", size=12), name="Ranges")
surf = lambda t: go.Surface(x=Xp, y=Yp, z=Zp, surfacecolor=cval(t), cmin=0, cmax=3, colorscale=cs, showscale=False, lighting=dict(ambient=.6, diffuse=.8))
fig = go.Figure(data=[surf(times[0]), figtrace(times[0]), labels],
                frames=[go.Frame(data=[surf(t), figtrace(t), labels], name=hm(t)) for t in times])
fig.update_layout(title="CFB Wainwright, Oct. 17 · v5 fire over terrain (height ×6) · working model v5 · figures representative, not to scale",
                  scene=dict(aspectmode="manual", aspectratio=dict(x=1.4, y=1.0, z=.18), xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                             bgcolor="#0b1020", camera=dict(eye=dict(x=-1.1, y=-1.25, z=.8))),
                  paper_bgcolor="#0b1020", font=dict(color="#e5e7eb"), margin=dict(l=0, r=0, t=40, b=0),
                  sliders=[dict(active=0, currentvalue=dict(prefix="Time (MDT): "), steps=[dict(method="animate", label=hm(t), args=[[hm(t)], dict(mode="immediate", frame=dict(duration=0, redraw=True))]) for t in times])],
                  updatemenus=[dict(type="buttons", x=0, y=0, buttons=[dict(label="Play", method="animate", args=[None, dict(frame=dict(duration=600, redraw=True), fromcurrent=True)])])])
fig.write_html(os.path.join(OUT, "3d_fire_with_figures_animated.html"), include_plotlyjs="cdn")
print("ok", files)
