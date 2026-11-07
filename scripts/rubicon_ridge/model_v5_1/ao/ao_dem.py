"""Copernicus DEM GLO-30 mosaic for the STAR03 area of operations, reprojected to EPSG:3400 at 30 m."""
import numpy as np, rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from pyproj import Transformer
x0, y0, x1, y1, res = -113.80, 52.60, -110.55, 53.65, 30
tr = Transformer.from_crs(4326, 3400, always_xy=True)
xs, ys = zip(*[tr.transform(a, b) for a in (x0, x1) for b in (y0, y1)])
L, B, R, T = min(xs), min(ys), max(xs), max(ys); W, H = int((R - L) / res), int((T - B) / res); tf = from_origin(L, T, res, res)
dem = np.full((H, W), np.nan, np.float32)
for lat in (52, 53):
    for lon in (114, 113, 112, 111):
        n = f"Copernicus_DSM_COG_10_N{lat}_00_W{lon:03d}_00_DEM"
        url = f"https://copernicus-dem-30m.s3.amazonaws.com/{n}/{n}.tif"
        with rasterio.open(url) as s, WarpedVRT(s, crs="EPSG:3400", transform=tf, width=W, height=H, resampling=Resampling.bilinear, src_nodata=-32767, nodata=np.nan) as v:
            a = v.read(1).astype(np.float32)
        ok = np.isfinite(a) & np.isnan(dem) & (a > -100); dem[ok] = a[ok]; print(n, ok.sum(), flush=True)
with rasterio.open("ao/dem_glo30_3400.tif", "w", driver="GTiff", width=W, height=H, count=1, dtype="float32", crs="EPSG:3400", transform=tf, compress="deflate", tiled=True, nodata=np.nan) as d: d.write(dem, 1)
print("nan frac", np.isnan(dem).mean(), "min/max", np.nanmin(dem), np.nanmax(dem))
