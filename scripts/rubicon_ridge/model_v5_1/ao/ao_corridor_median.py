"""Corridor true-colour composite (Edmonton - Wainwright): for each pixel, the median of up to K clear Sentinel-2 samples,
taking scenes in order of closeness to Oct. 17 (clearer first on ties). Clear = SCL not nodata/defective/cloud shadow/
cloud/cirrus/snow, and not near-white. Usage: python3 ao_corridor_median.py RES OUT.tif"""
import sys, json, time, numpy as np, rasterio, urllib.request, datetime as dt
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from pyproj import Transformer
res = float(sys.argv[1]); out = sys.argv[2]; K = 5
x0, y0, x1, y1 = -113.80, 52.60, -110.55, 53.65
tr = Transformer.from_crs(4326, 3400, always_xy=True)
xs, ys = zip(*[tr.transform(a, b) for a in (x0, x1) for b in (y0, y1)])
L, B, R, T = min(xs), min(ys), max(xs), max(ys); W, H = int((R - L) / res), int((T - B) / res); tf = from_origin(L, T, res, res)
q = {"collections": ["sentinel-2-l2a"], "bbox": [x0, y0, x1, y1], "datetime": "2026-10-04T00:00:00Z/2026-10-26T23:59:59Z", "limit": 300}
r = urllib.request.Request("https://earth-search.aws.element84.com/v1/search", data=json.dumps(q).encode(), headers={"Content-Type": "application/json"})
feats = [f for f in json.load(urllib.request.urlopen(r, timeout=90))["features"] if f["properties"].get("eo:cloud_cover", 100) < 85]
ref = dt.datetime(2026, 10, 17)
feats.sort(key=lambda f: (abs((dt.datetime.fromisoformat(f["properties"]["datetime"][:10]) - ref).days), f["properties"]["eo:cloud_cover"]))
S = np.zeros((K, 3, H, W), np.uint8); n = np.zeros((H, W), np.uint8); used = {}
for f in feats:
    if (n >= K).all(): break
    kw = dict(crs="EPSG:3400", transform=tf, width=W, height=H)
    for k in range(4):
        try:
            with rasterio.open(f["assets"]["visual"]["href"]) as s, WarpedVRT(s, resampling=Resampling.average, **kw) as v: a = v.read()
            with rasterio.open(f["assets"]["scl"]["href"]) as s, WarpedVRT(s, resampling=Resampling.nearest, **kw) as v: scl = v.read(1)
            break
        except Exception as e: print("retry", f["id"], e, flush=True); time.sleep(10)
    else: continue
    ok = (a.min(0) > 0) & ~np.isin(scl, [0, 1, 3, 8, 9, 10, 11]) & (a.astype(np.int16).sum(0) < 560) & (n < K)
    yy, xx = np.nonzero(ok)
    S[n[yy, xx], :, yy, xx] = a[:, yy, xx].T; n[yy, xx] += 1
    used[f["id"]] = int(ok.sum()); print(f["id"], int(ok.sum()), f"cover>=1 {(n > 0).mean():.3f} >=3 {(n >= 3).mean():.3f}", flush=True)
    del a, scl
np.save('ao/_stack_n.npy', n)
outa = np.zeros((3, H, W), np.uint8)
for r0 in range(0, H, 256):
    blk = S[:, :, r0:r0 + 256].astype(np.float32); cnt = n[r0:r0 + 256]
    msk = (np.arange(K)[:, None, None] >= cnt[None])[:, None]
    blk = np.where(msk, np.nan, blk)
    with np.errstate(all="ignore"): m = np.nanmedian(blk, axis=0)
    outa[:, r0:r0 + 256] = np.nan_to_num(m).astype(np.uint8)
with rasterio.open(out, "w", driver="GTiff", width=W, height=H, count=3, dtype="uint8", crs="EPSG:3400", transform=tf, compress="deflate", tiled=True, photometric="RGB") as d: d.write(outa)
json.dump({"bbox_lonlat": [x0, y0, x1, y1], "crs": "EPSG:3400", "res_m": res, "size": [W, H], "method": f"per-pixel median of up to {K} clear samples, scenes ordered by closeness to Oct. 17",
           "scenes_pixels": used, "pixels_without_clear_sample": float((n == 0).mean())}, open(out.replace(".tif", ".json"), "w"), indent=1)
print("done", W, H, "no-sample frac", float((n == 0).mean()))
