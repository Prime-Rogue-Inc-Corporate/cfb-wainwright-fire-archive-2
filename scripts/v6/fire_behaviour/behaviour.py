"""Fire behaviour when the fire reached the range area: weighted v5 ensemble (stored grids), aggregate only.
For Road head, Range 15 and Range 2 (official grids): arrival; local spread rate and direction (from the arrival-time gradient over
+-2 cells); ratio of local spread to the run's head spread (1 = head fire, ~0.1-0.3 = flank); width of the fire line that reached the
point (cells igniting within +-1 min of arrival, within 1.5 km, connected); approach timeline (distance from the point to the nearest
burning cell at each minute). Byram intensity and flame length from the local spread rate.
Usage: python3 behaviour.py GRIDS_DIR V5_DIR ARCHIVE_1 OUTDIR"""
import sys, os, json
import numpy as np, pandas as pd
from scipy import ndimage
from pyproj import Transformer
G, V5, A1, OUT = sys.argv[1:5]
minx, maxy, RES, H, W = np.load(os.path.join(G, "meta.npy")); H, W = int(H), int(W)
fw = pd.read_csv(os.path.join(V5, "fit_weights.csv"))
fw = fw[fw.weighted & (fw.weight > 0)].sort_values("weight", ascending=False)
fw["cum"] = fw.weight.cumsum() / fw.weight.sum(); keep = fw[fw.cum <= 0.995]
print("runs kept", len(keep), "of", len(fw), "weight share", round(keep.weight.sum() / fw.weight.sum(), 3))
rso = pd.read_csv(os.path.join(A1, "data/reference/range_standing_orders_2024/rso_points.csv")).dropna(subset=["lat"]).set_index("name")
T = Transformer.from_crs(4326, "EPSG:3400", always_xy=True)
P = {"Road head": (-110.89965, 52.77045), "Range 15": (rso.loc["Range 15", "lon"], rso.loc["Range 15", "lat"]), "Range 2": (rso.loc["Range 2", "lon"], rso.loc["Range 2", "lat"])}
PIX = {}
for k, (lo, la) in P.items():
    x, y = T.transform(lo, la); PIX[k] = (int((maxy - y) // RES), int((x - minx) // RES), x, y)
yy, xx = np.mgrid[0:H, 0:W]; X = minx + (xx + .5) * RES; Y = maxy - (yy + .5) * RES
HEAT, LOAD = 18000.0, 0.35
def local(A, i, j, k=2):
    sub = A[i - k:i + k + 1, j - k:j + k + 1].astype(float)
    if not np.isfinite(sub).all() or (sub > 300).any(): return np.nan, np.nan
    gy_, gx_ = np.gradient(sub, RES)            # minutes per metre; row index increases southward
    gx = gx_[k, k]; gy = -gy_[k, k]              # +y north
    g = np.hypot(gx, gy)
    if g <= 0: return np.nan, np.nan
    return 1 / g, (np.degrees(np.arctan2(gx, gy)) + 360) % 360   # m/min, direction of travel (bearing)
rows, timelines = [], {k: [] for k in P}
tgrid = np.arange(0, 61, 1.0)                    # minutes after 15:00 ... 16:00
for key, grp in keep.groupby(keep.case + "_" + keep.front.str.replace(":", "")):
    zs = np.load(os.path.join(G, f"scar_{key}.npz")); zf = np.load(os.path.join(G, f"free_{key}.npz"))
    for _, r in grp.iterrows():
        nk = r.run.replace("|", "__")
        As = zs[nk].astype("float32"); Af = zf[nk].astype("float32")
        out = dict(run=r.run, weight=r.weight, head_kmh=r.head_ros_kmh_mean_0_30, schedule=r.schedule, shape=r["shape"], front=r.front)
        for name, (i, j, x, y) in PIX.items():
            ta = float(As[i, j]); out[f"{name}|arr"] = ta
            ros, dirn = local(Af, i, j); out[f"{name}|ros_m_min"] = ros; out[f"{name}|dir"] = dirn
            out[f"{name}|head_ratio"] = ros * 0.06 / r.head_ros_kmh_mean_0_30 if np.isfinite(ros) else np.nan
            # width of the line that reached the point: cells igniting within +-1 min of ta, within 1.5 km, connected to the point's neighbourhood
            if np.isfinite(ta) and ta < 300:
                band = (np.abs(As - ta) <= 1.0) & (np.hypot(X - x, Y - y) <= 1500)
                lab, n = ndimage.label(band)
                win = lab[max(i - 2, 0):i + 3, max(j - 2, 0):j + 3]; ids = [v for v in np.unique(win) if v]
                if ids:
                    m = np.isin(lab, ids); cy, cx = np.nonzero(m)
                    pts = np.c_[X[m], Y[m]]; c = pts - pts.mean(0); ev, evec = np.linalg.eigh(c.T @ c / len(c))
                    out[f"{name}|line_width_m"] = float(4 * np.sqrt(ev[-1]))   # extent along the band's long axis (~ +-2 sd)
                # approach timeline (nearest burning cell)
                d = []
                for t in tgrid:
                    b = As <= t
                    d.append(float(np.min(np.hypot(X[b] - x, Y[b] - y))) if b.any() else np.nan)
                timelines[name].append((r.weight, d))
        rows.append(out)
df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, "behaviour_runs.csv"), index=False)
def wq(v, w, qs=(.1, .5, .9)):
    v = np.asarray(v, float); w = np.asarray(w, float); ok = np.isfinite(v); v, w = v[ok], w[ok]
    o = np.argsort(v); v, w = v[o], w[o]; c = (np.cumsum(w) - .5 * w) / w.sum(); return [float(np.interp(q, c, v)) for q in qs]
def hm(m): m = int(round(15 * 60 + m)); return f"{m // 60}:{m % 60:02d}"
summ = {}
for name in P:
    s = {}
    a = wq(df[f"{name}|arr"], df.weight); s["arrival"] = [hm(v) for v in a]
    ros = wq(df[f"{name}|ros_m_min"], df.weight); s["local_spread_kmh"] = [round(v * .06, 1) for v in ros]
    hr = wq(df[f"{name}|head_ratio"], df.weight); s["local_over_head_ratio"] = [round(v, 2) for v in hr]
    s["share_weight_head_like(ratio>=0.6)"] = round(float(df.weight[df[f"{name}|head_ratio"] >= .6].sum() / df.weight.sum()), 2)
    s["share_weight_flank_like(ratio<0.35)"] = round(float(df.weight[df[f"{name}|head_ratio"] < .35].sum() / df.weight.sum()), 2)
    dd = df[f"{name}|dir"]; ang = np.radians(dd); okm = np.isfinite(ang)
    s["direction_of_travel_deg_weighted_mean"] = round(float((np.degrees(np.arctan2((np.sin(ang[okm]) * df.weight[okm]).sum(), (np.cos(ang[okm]) * df.weight[okm]).sum())) + 360) % 360))
    if f"{name}|line_width_m" in df: s["line_width_m"] = [round(v) for v in wq(df[f"{name}|line_width_m"], df.weight)]
    I = [round(HEAT * LOAD * v / 60) for v in ros]; s["byram_kW_m"] = I
    s["flame_length_m"] = [round(0.0775 * i ** 0.46, 1) for i in I]
    W_ = np.array([t[0] for t in timelines[name]]); D = np.array([t[1] for t in timelines[name]])
    med = [wq(D[:, k], W_)[1] if np.isfinite(D[:, k]).any() else np.nan for k in range(len(tgrid))]
    s["approach_median_distance_m_by_minute"] = {hm(t): (None if not np.isfinite(m) else round(m)) for t, m in zip(tgrid, med)}
    for thr in (1000, 500, 200):
        tt = []
        for w_, d in timelines[name]:
            d = np.array(d); a_ = np.where(d <= thr)[0]; tt.append(tgrid[a_[0]] if len(a_) else np.nan)
        s[f"time_fire_within_{thr}m"] = [hm(v) for v in wq(tt, W_)]
    summ[name] = s
json.dump(summ, open(os.path.join(OUT, "behaviour_summary.json"), "w"), indent=1)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "approach_median_distance_m_by_minute"} for k, v in summ.items()}, indent=1))
