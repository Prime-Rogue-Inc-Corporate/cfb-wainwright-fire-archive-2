"""Burn layers for the crew-view film, from OUR model only (Rubicon Ridge v5 weighted median), not from any imagery.
Writes, on the v5 grid (EPSG:3400, 40 m):
  arrival_hhmm_v5median.tif   arrival time, minutes after 15:00 MDT (pre-front burning = -60); NaN where burn probability < 0.5
  burn_probability_v5.tif     weighted share of runs that burn the cell
  burn_state_<HHMM>.tif       state at a film moment: 0 unburned, 1 burned >90 min earlier (cooling char), 2 burned 30-90 min
                              earlier (smouldering), 3 burned <30 min earlier (flaming edge)
  burn_perimeter_v5.geojson   outline where burn probability >= 0.5
Usage: python3 burn_state_from_v5.py GRIDS_DIR OUT_DIR"""
import sys, json, numpy as np, rasterio, rasterio.features, geopandas as gpd, shapely.geometry as sg
from rasterio.transform import from_origin
G, O = sys.argv[1], sys.argv[2]
minx, maxy, res, H, W = np.load(G + "/meta.npy"); H, W = int(H), int(W)
med, pb = np.load(G + "/_weighted_median.npy")
tf = from_origin(minx, maxy, res, res); prof = dict(driver="GTiff", width=W, height=H, count=1, crs="EPSG:3400", transform=tf, compress="deflate")
arr = np.where(np.isfinite(med) & (pb >= 0.5), med, np.nan).astype("float32")
with rasterio.open(O + "/arrival_min_after_1500_v5median.tif", "w", dtype="float32", nodata=np.nan, **prof) as d: d.write(arr, 1)
with rasterio.open(O + "/burn_probability_v5.tif", "w", dtype="float32", **prof) as d: d.write(pb.astype("float32"), 1)
moments = {"1732": "STAR03 drops below coverage, ingress", "1737": "STAR03 estimated landing at Wainwright Airport",
           "2140": "STAR03 first egress", "0210": "STAR03 second egress (Oct. 18)"}
summary = {}
for hhmm, what in moments.items():
    h, m = int(hhmm[:2]), int(hhmm[2:]); t = (h * 60 + m) - 15 * 60
    if h < 12: t += 24 * 60
    age = t - arr
    st = np.zeros((H, W), "uint8")
    st[np.isfinite(arr) & (age > 90)] = 1; st[np.isfinite(arr) & (age > 30) & (age <= 90)] = 2; st[np.isfinite(arr) & (age >= 0) & (age <= 30)] = 3
    with rasterio.open(O + f"/burn_state_{hhmm}.tif", "w", dtype="uint8", nodata=0, **prof) as d: d.write(st, 1)
    summary[hhmm] = {"moment": what, "cells_by_state": {s: int((st == k).sum()) for k, s in [(1, "cooling >90 min"), (2, "smouldering 30-90 min"), (3, "flaming <30 min")]}}
burned = (pb >= 0.5).astype("uint8")
polys = [sg.shape(g) for g, v in rasterio.features.shapes(burned, mask=burned > 0, transform=tf)]
gpd.GeoDataFrame({"source": ["Rubicon Ridge v5 weighted median, burn probability >= 0.5"]}, geometry=[sg.MultiPolygon([p for p in polys if p.area > 4 * 1600]).buffer(0)], crs=3400).to_file(O + "/burn_perimeter_v5.geojson", driver="GeoJSON")
summary["latest_arrival_min_after_1500"] = float(np.nanmax(arr)); summary["burned_km2"] = round(float(burned.sum() * res * res / 1e6), 2)
json.dump(summary, open(O + "/burn_state_summary.json", "w"), indent=1); print(json.dumps(summary, indent=1))
