# Area of operations base layers: Rubicon Cloud (v5.1) crew-view reconstruction

Prime Rogue Inc. · built Nov. 6, 2026 · working material for the STARS crew-view film (additive to v5.1)

The fire-site model covered only the base. These layers cover the whole route the STARS helicopters flew on Oct. 17 and 18: Edmonton International and the University of Alberta Hospital, the corridor east, and Wainwright Airport, the town and the base. With them, the flights can be rebuilt on real terrain and real ground imagery.

Imagery is stored as JPEG-compressed GeoTIFF (quality 90) to keep the repo small; the scripts rebuild the lossless versions. All layers are in **EPSG:3400 (NAD83 / Alberta 10-TM)**, the same projection as the v5 model.

| File | What | Resolution | Source and date |
|---|---|---|---|
| `s2_corridor_30m.tif` | True-colour composite, Edmonton to Wainwright (113.80° W–110.55° W, 52.60° N–53.65° N) | 30 m (matches the terrain) | Sentinel-2 L2A, Oct. 4–26. For each pixel, the median of up to five cloud-free samples, taking passes closest to Oct. 17 first (cloud, shadow, cirrus and snow masked with the scene classification layer). 0.6% of pixels had no clear sample and were filled from neighbours. The `.json` lists each scene's contribution. |
| `overview_star03_tracks.jpg` | Preview: the corridor composite with STAR03's four legs | | |
| `s2_wainwright_10m.tif` | Wainwright Airport, the town, the garrison and the burn | 10 m | Per-pixel median of the post-fire passes on Oct. 19, 21 and 24, so the burn scar shows. |
| `s2_edmonton_10m.tif` | Edmonton International, the University of Alberta Hospital and the river valley | 10 m | Oct. 15, with gaps filled from Oct. 17 and 22. |
| `dem_glo30_3400_dm.tif` | Terrain for the whole corridor, in **decimetres** (divide by 10 for metres; -32768 = no data) | 30 m | Copernicus DEM GLO-30. This is a surface model, so it includes trees and buildings. |
| `stars_helicopter_tracks.csv` | Every heard position of the three STARS helicopters (C-FLCI STAR03, C-FDRP STAR11, C-FLNK STAR01), by flight and leg, with EPSG:3400 coordinates | ADS-B | adsb.lol (ODbL), from the v5.1 tables |

## Limits

- Sentinel-2 shows the ground from a few days before or after Oct. 17, not at 5:37 p.m. that day. The burn scar in the Wainwright layers is the Oct. 19–24 scar. At 5:37 p.m. on Oct. 17 the burn was hours old and parts may still have been smoking.
- At 10 m a vehicle is one pixel or less. Aircraft, vehicles and people in the film are representative sprites placed by us, not detected objects.
- The terrain is a surface model, so towns and tree lines stand a few metres proud. That's fine for a crew's-eye view from 2,000 ft or more above the ground.
- **Not included yet:**
  - **Building footprints.** The Microsoft footprints on Planetary Computer are blocked from our cloud workspace. OSM buildings need a download from your machine.
  - **Night lights.** NASA Black Marble needs an Earthdata login.
  - **Higher-resolution aerial photos of the airport and the hospital helipad.** Alberta and City of Edmonton open orthophotos are worth checking.

## Credits

Contains modified Copernicus Sentinel data (2026). Copernicus DEM © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA. Flight data © adsb.lol contributors (ODbL 1.0). Processing © Prime Rogue Inc., CC BY-NC 4.0.

## Scripts

`scripts/rubicon_ridge/model_v5_1/ao/`: `ao_mosaic.py` (corridor and detail mosaics), `ao_median.py` (median composite), `ao_dem.py` (terrain).

## Added Nov. 7: the live environment around the burn

### `burn_from_model_v5/`: the fire, from our own model (not from any image)

The film shows the burn and its state from **Rubicon Ridge v5** (weighted median of the fitted runs), because it is our inference. It's on the v5 grid (EPSG:3400, 40 m).

| File | What |
|---|---|
| `arrival_min_after_1500_v5median.tif` | When the model's fire reached each cell, in minutes after 3:00 p.m. MDT. Cells burning before the front are -60. Blank where fewer than half the runs burn the cell. |
| `burn_probability_v5.tif` | The weighted share of runs that burn each cell |
| `burn_perimeter_v5.geojson` | The model's burn outline: 13.3 km² |
| `burn_state_1732.tif`, `_1737`, `_2140`, `_0210` | The fire's state at each film moment (STAR03's ingress, its landing, the first egress, the second egress). 1 = burned more than 90 minutes earlier (cooling); 2 = 30–90 minutes (smouldering); 3 = less than 30 minutes (flaming edge). |
| `burn_state_summary.json` | Cell counts by state |

What the model implies for the crew:
- **At 5:37 p.m.:** most of the burn was 30–90+ minutes old. About 170 cells (roughly 0.3 km²) at the latest-burning edges were still within 30 minutes of the flame front, so active fire and smoke were plausibly visible from the approach.
- **By 9:40 p.m.:** everything the model burns was more than 90 minutes old. Any glow then would be residual smouldering, which the model doesn't simulate.

### `derived_satellogic/`: layout of the scene, traced from the licensed 70 cm image (vectors only)

The image itself is not in this repository. These are generalised, derived vectors for building the 3D scene. Credit: "Derived from imagery by Satellogic via SkyFi, Oct. 20, 2026".

| File | What |
|---|---|
| `landcover_generalised_3400.geojson` | Eight generalised surface classes, about 14 m detail with a 0.05 ha minimum: trees and shrubs (with and without leaves), open grass or field, green grass, lawn or conifer, dry slough or alkali flat, bare ground, gravel or roof, and "burned". Inside the burn, the film takes the fire's extent and state from model v5, not from this layer. The classes come from an automatic clustering labelled by rule, so treat them as texture guidance, not a survey. |
| (no buildings layer) | I tried automatic roof detection with shadow heights. It found barely half the houses in the country-residential area and almost no shadows long enough to measure, so it isn't good enough to publish. For the film, buildings more than 2–3 km from the camera are smaller than a pixel. If we need them, hand-tracing the 30–40 structures that matter (the airport's hangar row, the farmyards on the approach) is the viable route. |

The land-cover clustering and roof-test scripts read the licensed image directly, so, like the earlier Satellogic scripts, they are kept outside the repo.

Coverage is the 6.25 × 6.25 km image footprint: the burn, the ranges, the country-residential area south of the airport, and the airport's southern hangar row. **The runway and most of the apron are outside the image** (north of its edge), so the airport layout still needs another source (open aerial photos or OSM).
