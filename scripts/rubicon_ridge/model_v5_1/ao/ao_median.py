"""Per-pixel median of several post-fire Sentinel-2 passes (SCL-masked) for a detail box: removes small cumulus and shadows
that single-scene SCL masks miss. Usage: python3 ao_median.py minlon minlat maxlon maxlat RES OUT.tif SCENE[,SCENE...]"""
import sys, json, time, numpy as np, rasterio, urllib.request
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from pyproj import Transformer
x0, y0, x1, y1, res = map(float, sys.argv[1:6]); out = sys.argv[6]; scenes = sys.argv[7].split(",")
tr = Transformer.from_crs(4326, 3400, always_xy=True)
xs, ys = zip(*[tr.transform(a, b) for a in (x0, x1) for b in (y0, y1)])
L, B, R, T = min(xs), min(ys), max(xs), max(ys); W, H = int((R - L) / res), int((T - B) / res); tf = from_origin(L, T, res, res)
stack = []
for sid in scenes:
    for k in range(5):
        try: j = json.load(urllib.request.urlopen(f"https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/{sid}", timeout=60)); break
        except Exception as e: time.sleep(5)
    kw = dict(crs="EPSG:3400", transform=tf, width=W, height=H)
    with rasterio.open(j["assets"]["visual"]["href"]) as s, WarpedVRT(s, resampling=Resampling.bilinear, **kw) as v: a = v.read().astype(np.float32)
    with rasterio.open(j["assets"]["scl"]["href"]) as s, WarpedVRT(s, resampling=Resampling.nearest, **kw) as v: scl = v.read(1)
    bad = (a.max(0) == 0) | np.isin(scl, [0, 1, 3, 8, 9, 10]); a[:, bad] = np.nan; stack.append(a); print(sid, f"{(~bad).mean():.2f}", flush=True)
S = np.stack(stack)                       # n,3,H,W
med = np.nanmedian(S, axis=0)
med = np.where(np.isfinite(med), med, np.nanmax(S, axis=0)); med = np.nan_to_num(med)
with rasterio.open(out, "w", driver="GTiff", width=W, height=H, count=3, dtype="uint8", crs="EPSG:3400", transform=tf, compress="deflate", tiled=True, photometric="RGB") as d:
    d.write(np.clip(med, 0, 255).astype(np.uint8))
json.dump({"bbox_lonlat": [x0, y0, x1, y1], "crs": "EPSG:3400", "res_m": res, "size": [W, H], "method": "per-pixel median of SCL-masked TCI", "scenes": scenes},
          open(out.replace(".tif", ".json"), "w"), indent=1)
