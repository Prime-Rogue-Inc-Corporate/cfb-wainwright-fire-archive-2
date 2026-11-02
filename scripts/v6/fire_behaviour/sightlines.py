"""Terrain and sightlines with the v5 ensemble. DEM: NRCan MRDEM-30 (bare earth; resampled 10 m), Copernicus GLO-30 DSM as a check
(includes trees and shrubs). For observers standing at Road head, Range 15 and Range 2 (eye 1.7 m), the height above ground a flame or
smoke top must reach to be seen at every cell; then, per weighted run, when the active front (cells igniting in the last 2 min)
first comes into view for flame tops of 2.5 m and 6 m, vs arrival. Plus slope along the direction of travel and the elevation profile.
Usage: python3 sightlines.py GRIDS_DIR ARCHIVE_1 OUTDIR"""
import sys, os, json
import numpy as np, pandas as pd, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from pyproj import Transformer
G, A1, OUT = sys.argv[1:4]
minx, maxy, RES, H, W = np.load(os.path.join(G, "meta.npy")); H, W = int(H), int(W)
F = 4; R10 = RES / F; H10, W10 = H * F, W * F; T10 = from_origin(minx, maxy, R10, R10)
def dem(name):
    with rasterio.open(os.path.join(A1, "data/dem", name)) as s:
        a = np.full((H10, W10), np.nan, "float32")
        reproject(rasterio.band(s, 1), a, src_nodata=s.nodata, dst_transform=T10, dst_crs="EPSG:3400", dst_nodata=np.nan, resampling=Resampling.bilinear)
    a[a < 100] = np.nan; return a
Z = {"MRDEM (bare earth)": dem("mrdem30_dtm_3400_10m.tif"), "Copernicus DSM (with vegetation)": dem("copernicus_glo30_dsm_3400_10m.tif")}
np.save(os.path.join(OUT, "dem10_mrdem.npy"), Z["MRDEM (bare earth)"])
rso = pd.read_csv(os.path.join(A1, "data/reference/range_standing_orders_2024/rso_points.csv")).dropna(subset=["lat"]).set_index("name")
T = Transformer.from_crs(4326, "EPSG:3400", always_xy=True)
P = {"Road head": (-110.89965, 52.77045), "Range 15": (rso.loc["Range 15", "lon"], rso.loc["Range 15", "lat"]), "Range 2": (rso.loc["Range 2", "lon"], rso.loc["Range 2", "lat"])}
yy, xx = np.mgrid[0:H10, 0:W10]; X10 = minx + (xx + .5) * R10; Y10 = maxy - (yy + .5) * R10
def hreq(z, ox, oy, eye=1.7, rmax=2500.0, step=10.0):
    oi, oj = int((maxy - oy) // R10), int((ox - minx) // R10); oz = z[oi, oj] + eye
    dx, dy = X10 - ox, Y10 - oy; dist = np.hypot(dx, dy); m = (dist <= rmax) & (dist > 5) & np.isfinite(z)
    tx, ty, td, tz = dx[m], dy[m], dist[m], z[m]
    maxtan = np.full(td.shape, -np.inf)
    ns = int(rmax / step)
    for k in range(1, ns):
        f = (k * step) / td; ok = f < 1
        if not ok.any(): break
        si = ((maxy - (oy + ty[ok] * f[ok])) // R10).astype(int); sj = ((ox + tx[ok] * f[ok] - minx) // R10).astype(int)
        inb = (si >= 0) & (si < H10) & (sj >= 0) & (sj < W10)
        zz = np.full(si.shape, np.nan); zz[inb] = z[si[inb], sj[inb]]
        tn = (zz - oz) / (k * step)
        cur = maxtan[ok]; maxtan[ok] = np.where(np.isfinite(tn), np.maximum(cur, tn), cur)
    need = np.maximum(0, oz + np.maximum(maxtan, -1e9) * td - tz)
    out = np.full(z.shape, np.nan, "float32"); out[m] = need; return out
HR = {}
for dn, z in Z.items():
    for pn, (lo, la) in P.items():
        x, y = T.transform(lo, la); HR[(dn, pn)] = hreq(z, x, y)
np.save(os.path.join(OUT, "hreq_mrdem_roadhead.npy"), HR[("MRDEM (bare earth)", "Road head")])
# block-min to the 40 m model grid (a 40 m cell counts as visible if any part of it is)
def to40(a): return np.nanmin(a.reshape(H, F, W, F), axis=(1, 3))
HR40 = {k: to40(v) for k, v in HR.items()}
# runs
fw = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(OUT)), "..", "cfb-wainwright-fire-archive-2/data/rubicon-ridge/model_v5/fit_weights.csv")) if False else pd.read_csv("/home/claude/cfb-wainwright-fire-archive-2/data/rubicon-ridge/model_v5/fit_weights.csv")
fw = fw[fw.weighted & (fw.weight > 0)].sort_values("weight", ascending=False); fw["cum"] = fw.weight.cumsum() / fw.weight.sum(); keep = fw[fw.cum <= .995]
PIX = {pn: (int((maxy - T.transform(*v)[1]) // RES), int((T.transform(*v)[0] - minx) // RES)) for pn, v in P.items()}
rows = []
for key, grp in keep.groupby(keep.case + "_" + keep.front.str.replace(":", "")):
    zs = np.load(os.path.join(G, f"scar_{key}.npz"))
    for _, r in grp.iterrows():
        A = zs[r.run.replace("|", "__")].astype("float32")
        o = dict(run=r.run, weight=r.weight)
        for pn, (i, j) in PIX.items():
            ta = float(A[i, j]); o[f"{pn}|arr"] = ta
            for dn in Z:
                hr = HR40[(dn, pn)]
                for fh in (2.5, 6.0):
                    first = np.nan
                    for t in np.arange(0, min(ta, 120) + .01, .5):
                        act = (A > t - 2) & (A <= t) & np.isfinite(hr) & (hr <= fh)
                        if act.any(): first = t; break
                    o[f"{pn}|{dn}|{fh}|lead_min"] = ta - first if np.isfinite(first) else np.nan
            # line-of-sight to the pre-front fire edge at the front's arrival (15:28): any burning cell visible?
            for dn in Z:
                hr = HR40[(dn, pn)]; b = (A <= 28) & np.isfinite(hr)
                o[f"{pn}|{dn}|burned_area_visible_at_1528_2.5m"] = float((hr[b] <= 2.5).mean()) if b.any() else np.nan
        rows.append(o)
df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, "sightline_runs.csv"), index=False)
def wq(v, w, qs=(.1, .5, .9)):
    v = np.asarray(v, float); w = np.asarray(w, float); ok = np.isfinite(v); v, w = v[ok], w[ok]
    if not len(v): return [None] * 3
    o = np.argsort(v); v, w = v[o], w[o]; c = (np.cumsum(w) - .5 * w) / w.sum(); return [round(float(np.interp(q, c, v)), 1) for q in qs]
summ = {}
for pn in P:
    s = {}
    for dn in Z:
        for fh in (2.5, 6.0):
            s[f"{dn} | flame top {fh} m: minutes between active front first in sight and arrival (10/50/90)"] = wq(df[f"{pn}|{dn}|{fh}|lead_min"], df.weight)
        s[f"{dn} | share of the pre-front burned area visible at 15:28 (2.5 m flames)"] = wq(df[f"{pn}|{dn}|burned_area_visible_at_1528_2.5m"], df.weight)
    summ[pn] = s
# slope and profile along the weighted direction of travel (from behaviour_summary.json)
bs = json.load(open(os.path.join(OUT, "behaviour_summary.json")))
z = Z["MRDEM (bare earth)"]; prof = {}
for pn, (lo, la) in P.items():
    x, y = T.transform(lo, la); d = np.radians(bs[pn]["direction_of_travel_deg_weighted_mean"])
    ds = np.arange(-1200, 101, 20)          # metres along travel direction (negative = where the fire came from)
    px, py = x + ds * np.sin(d), y + ds * np.cos(d)
    zi = z[((maxy - py) // R10).astype(int), ((px - minx) // R10).astype(int)]
    prof[pn] = dict(dist_m=ds.tolist(), elev_m=[round(float(v), 1) for v in zi])
    g = np.polyfit(ds[(ds >= -300) & (ds <= 0)], zi[(ds >= -300) & (ds <= 0)], 1)[0]
    summ[pn]["slope_last_300m_along_travel_pct"] = round(float(g * 100), 1)
    summ[pn]["fbp_slope_factor_last_300m"] = round(float(np.exp(3.533 * max(g, 0) ** 1.2)), 2) if g > 0 else "downslope: no FBP boost (≈1.0)"
    summ[pn]["elev_point_m"] = round(float(zi[ds == 0][0]), 1); summ[pn]["max_elev_last_1200m_m"] = round(float(np.nanmax(zi[ds <= 0])), 1)
json.dump(dict(summary=summ, profiles=prof), open(os.path.join(OUT, "sightline_summary.json"), "w"), indent=1)
print(json.dumps(summ, indent=1))
