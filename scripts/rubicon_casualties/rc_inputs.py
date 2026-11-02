"""Rubicon Casualties (working model v5.3), step 1: inputs.
- 300 runs drawn (with replacement) from the v5 weighted ensemble (fit weights, spring factor 0.5/0.75), scar-limited arrival grids.
- Per drawn run: local fire speed (m/s) from the arrival-time gradient; refuge map = nearest cell that never burned (index arrays).
- Terrain: MRDEM-30 (10 m resample) -> 40 m block mean; TPI at 500 m (hollow <= -2 m, rise >= +2 m).
- Viewshed origins on an 80 m lattice within 800 m of the road head: for each origin the height a flame top needs to be seen (40 m grid,
  eye 1.7 m, bare earth). For each run x origin: first time an active post-front cell is visible (flame top 3 m) and first time the fire
  is within 200/300/400 m.
Usage: python3 rc_inputs.py GRIDS_DIR DEM10_NPY OUTDIR"""
import sys, os, json
import numpy as np, pandas as pd
from scipy import ndimage
from pyproj import Transformer
G, DEM10, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)
minx, maxy, RES, H, W = np.load(os.path.join(G, "meta.npy")); H, W = int(H), int(W)
V5 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data/rubicon-ridge/model_v5/fit_weights.csv")
fw = pd.read_csv(V5); fw = fw[fw.weighted & (fw.weight > 0)].reset_index(drop=True)
rng = np.random.default_rng(53)
pick = rng.choice(len(fw), size=300, replace=True, p=(fw.weight / fw.weight.sum()).values)
sel = fw.iloc[pick].reset_index(drop=True)
A = np.empty((300, H, W), "float32"); cache = {}
for k, r in sel.iterrows():
    key = f"{r.case}_{r.front.replace(':', '')}"
    if key not in cache: cache = {key: np.load(os.path.join(G, f"scar_{key}.npz"))}
    a = cache[key][r.run.replace("|", "__")].astype("float32"); a[a >= 399] = np.inf; A[k] = a
# fire speed (m/s)
SPD = np.empty_like(A)
for k in range(300):
    a = np.where(np.isfinite(A[k]) & (A[k] < 300), A[k], np.nan); a = ndimage.generic_filter(np.nan_to_num(a, nan=np.nanmax(a)), np.nanmean, size=3) if False else a
    gy, gx = np.gradient(np.nan_to_num(a, nan=1e3), RES)                          # min per m
    g = np.hypot(gx, gy); SPD[k] = np.clip(np.where(g > 0, 1 / g / 60, 0.3), 0.15, 4.0)
# refuge (nearest never-burned cell, within the first 2 h)
RI = np.empty((300, 2, H, W), "int16")
for k in range(300):
    unb = ~(np.isfinite(A[k]) & (A[k] < 120))
    _, idx = ndimage.distance_transform_edt(~unb, return_indices=True); RI[k] = idx.astype("int16")
# terrain
z10 = np.load(DEM10).astype(float); z40 = np.nanmean(z10.reshape(H, 4, W, 4), axis=(1, 3)); z40 = np.where(np.isfinite(z40), z40, np.nanmean(z40))
k = int(500 / RES); yy, xx = np.ogrid[-k:k + 1, -k:k + 1]; d = (xx * xx + yy * yy <= k * k).astype(float)
tpi = z40 - ndimage.convolve(z40, d / d.sum(), mode="nearest")
# origins + viewshed
T = Transformer.from_crs(4326, "EPSG:3400", always_xy=True); rx, ry = T.transform(-110.89965, 52.77045)
X = minx + (np.arange(W) + .5) * RES; Y = maxy - (np.arange(H) + .5) * RES; XX, YY = np.meshgrid(X, Y)
org = [(x, y) for x in np.arange(rx - 800, rx + 801, 80) for y in np.arange(ry - 800, ry + 801, 80) if np.hypot(x - rx, y - ry) <= 800]
def hreq(ox, oy, eye=1.7, rmax=2000.0):
    oi, oj = int((maxy - oy) // RES), int((ox - minx) // RES); oz = z40[oi, oj] + eye
    dx, dy = XX - ox, YY - oy; dist = np.hypot(dx, dy); m = (dist <= rmax) & (dist > 1)
    tx, ty, td, tz = dx[m], dy[m], dist[m], z40[m]; mt = np.full(td.shape, -np.inf)
    for s in np.arange(20, rmax, 20):
        f = s / td; ok = f < 1
        si = np.clip(((maxy - (oy + ty[ok] * f[ok])) // RES).astype(int), 0, H - 1); sj = np.clip(((ox + tx[ok] * f[ok] - minx) // RES).astype(int), 0, W - 1)
        mt[ok] = np.maximum(mt[ok], (z40[si, sj] - oz) / s)
    out = np.full((H, W), np.inf, "float32"); out[m] = np.maximum(0, oz + mt * td - tz); return out
TVIS = np.full((300, len(org)), np.inf, "float32"); TNEAR = np.full((300, len(org), 3), np.inf, "float32")
for o, (ox, oy) in enumerate(org):
    vis = hreq(ox, oy) <= 3.0
    dist = np.hypot(XX - ox, YY - oy)
    for k in range(300):
        a = A[k]; post = np.isfinite(a) & (a >= 26)
        v = a[vis & post]; TVIS[k, o] = v.min() if v.size else np.inf
        for j, dc in enumerate((200, 300, 400)):
            v = a[(dist <= dc) & np.isfinite(a)]; TNEAR[k, o, j] = v.min() if v.size else np.inf
np.savez_compressed(os.path.join(OUT, "rc_inputs.npz"), A=A.astype("float16"), SPD=SPD.astype("float16"), RI=RI, z40=z40.astype("float32"), tpi=tpi.astype("float32"),
                    org=np.array(org), TVIS=TVIS, TNEAR=TNEAR, meta=np.array([minx, maxy, RES, H, W, rx, ry]))
sel.to_csv(os.path.join(OUT, "rc_runs_drawn.csv"), index=False)
print("ok", len(org), "origins")
