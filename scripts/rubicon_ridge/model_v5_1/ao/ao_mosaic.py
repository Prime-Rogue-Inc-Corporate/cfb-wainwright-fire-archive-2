"""Sentinel-2 true-colour mosaic of the STAR03 area of operations (Edmonton - Wainwright), cloud-masked with SCL.
Usage: python3 ao_mosaic.py NAME minlon minlat maxlon maxlat RES_m OUT.tif"""
import sys, json, numpy as np, rasterio, urllib.request
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from pyproj import Transformer
name, x0, y0, x1, y1, res, out = sys.argv[1], *map(float, sys.argv[2:6]), float(sys.argv[6]), sys.argv[7]
CRS = "EPSG:3400"
tr = Transformer.from_crs(4326, 3400, always_xy=True)
xs, ys = zip(*[tr.transform(a, b) for a in (x0, x1) for b in (y0, y1)])
L, B, R, T = min(xs), min(ys), max(xs), max(ys)
W, H = int((R - L) / res), int((T - B) / res); tf = from_origin(L, T, res, res)
ORDER = [# east (fire, Wainwright): closest clear post-fire passes first, so the burn scar is as fresh as possible
         "S2B_12UWD_20261019_0_L2A","S2B_12UVD_20261019_0_L2A","S2B_12UWE_20261019_0_L2A","S2B_12UVE_20261019_0_L2A",
         "S2C_12UWD_20261024_0_L2A","S2C_12UVD_20261024_0_L2A","S2C_12UWD_20261021_0_L2A","S2C_12UWE_20261021_0_L2A",
         "S2B_12UWD_20261022_0_L2A","S2B_12UWE_20261022_0_L2A","S2B_12UVE_20261022_0_L2A","S2B_12UVD_20261022_0_L2A",
         # west (Edmonton) and corridor: clearest passes nearest Oct. 17
         "S2B_11UQU_20261015_0_L2A","S2B_11UQV_20261015_0_L2A","S2B_12UUD_20261015_0_L2A","S2B_12UUE_20261015_0_L2A",
         "S2C_12UVD_20261014_0_L2A","S2C_12UVE_20261014_0_L2A","S2B_12UVD_20261012_0_L2A","S2B_12UVE_20261012_0_L2A",
         "S2C_12UUD_20261020_0_L2A","S2C_12UUE_20261020_0_L2A","S2C_12UVE_20261024_0_L2A","S2C_12UWE_20261024_0_L2A",
         "S2C_12UUE_20261014_0_L2A","S2C_12UUD_20261014_0_L2A","S2B_12UUE_20261022_2_L2A","S2C_12UUE_20261024_0_L2A",
         "S2C_12UUD_20261024_0_L2A","S2C_12UUE_20261017_0_L2A","S2C_11UQV_20261014_0_L2A","S2C_11UQU_20261014_0_L2A",
         "S2C_12UVD_20261004_0_L2A","S2C_12UWD_20261004_0_L2A"]
import os
PREFER = [x for x in os.environ.get("PREFER", "").split(",") if x]   # scenes to try first, e.g. one clear date for a detail box
ORDER = PREFER + [x for x in ORDER if x not in PREFER]
# then every other scene over the box, Oct. 4-24, clearest first (fills orbit-edge gaps)
_q = {"collections": ["sentinel-2-l2a"], "bbox": [x0, y0, x1, y1], "datetime": "2026-10-04T00:00:00Z/2026-10-24T23:59:59Z", "limit": 200}
_r = urllib.request.Request("https://earth-search.aws.element84.com/v1/search", data=json.dumps(_q).encode(), headers={"Content-Type": "application/json"})
_all = sorted(json.load(urllib.request.urlopen(_r, timeout=60))["features"], key=lambda f: f["properties"].get("eo:cloud_cover", 100))
ORDER += [f["id"] for f in _all if f["id"] not in ORDER and f["properties"].get("eo:cloud_cover", 100) < 60]
import time
def item(sid):
    for k in range(6):
        try: return json.load(urllib.request.urlopen(f"https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/{sid}", timeout=60))
        except Exception as e: print("retry", sid, e, flush=True); time.sleep(5 * (k + 1))
    raise RuntimeError(sid)
rgb = np.zeros((3, H, W), np.uint8); filled = np.zeros((H, W), bool); used = {}
for sid in ORDER:
    if filled.all(): break
    j = item(sid)
    kw = dict(crs=CRS, transform=tf, width=W, height=H)
    try:
        with rasterio.open(j["assets"]["visual"]["href"]) as s, WarpedVRT(s, resampling=Resampling.average, **kw) as v: a = v.read()
        with rasterio.open(j["assets"]["scl"]["href"]) as s, WarpedVRT(s, resampling=Resampling.nearest, **kw) as v: scl = v.read(1)
    except Exception as e:
        print(sid, "skip", e); continue
    ok = (a.max(0) > 0) & ~np.isin(scl, [0, 1, 3, 8, 9, 10]) & ~filled
    if ok.sum():
        rgb[:, ok] = a[:, ok]; filled |= ok; used[sid] = int(ok.sum())
    print(sid, ok.sum(), f"{filled.mean():.3f}", flush=True)
# fill remaining (cloud) pixels with any non-empty data so there are no holes
for sid in ORDER:
    if filled.all(): break
    j = item(sid)
    with rasterio.open(j["assets"]["visual"]["href"]) as s, WarpedVRT(s, resampling=Resampling.average, crs=CRS, transform=tf, width=W, height=H) as v: a = v.read()
    ok = (a.max(0) > 0) & ~filled; rgb[:, ok] = a[:, ok]; filled |= ok
with rasterio.open(out, "w", driver="GTiff", width=W, height=H, count=3, dtype="uint8", crs=CRS, transform=tf, compress="deflate", tiled=True, photometric="RGB") as d: d.write(rgb)
json.dump({"name": name, "bbox_lonlat": [x0, y0, x1, y1], "crs": CRS, "res_m": res, "size": [W, H], "scenes_pixels": used,
           "unfilled_frac": float(1 - filled.mean())}, open(out.replace(".tif", ".json"), "w"), indent=1)
print("done", W, H)
