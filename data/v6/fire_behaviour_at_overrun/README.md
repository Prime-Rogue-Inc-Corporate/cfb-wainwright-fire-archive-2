# Fire behaviour when the fire reached the range area (v6 working material, Nov. 1, 2026)

Working analysis built on the v5 (Rubicon Ridge) ensemble in `data/rubicon-ridge/model_v5/`. It covers aggregate fire physics only, not where any individual was, nor anyone's injuries. Times are MDT. Prime Rogue Inc., CC BY-NC 4.0.

## What it shows (weighted v5 ensemble, 1,425 runs = 99.5% of the fit weight)
| | Road head | Range 15 (official grid) | Range 2 (official grid) |
|---|---|---|---|
| Fire arrives (10/50/90%) | 15:36 / **15:42** / 15:56 | 15:36 / **15:42** / 15:58 | 15:34 / **15:39** / 15:51 |
| Local spread rate at the point | 1.2 / **3.1** / 7.1 km/h | 1.7 / **3.8** / 8.7 km/h | 1.6 / **4.3** / 17.1 km/h |
| Local spread ÷ the run's head rate | 0.24 / **0.47** / 0.80 | 0.27 / **0.53** / 1.09 | 0.27 / **0.63** / 2.18 |
| Direction of travel into the point | ~144° (from the NNW) | ~160° | ~177° |
| Width of the fire line that reached it | **~1.9 km** (0.35–2.2) | ~1.9 km | ~2.1 km |
| Fire intensity (Byram) | 2,200 / **5,500** / 12,400 kW/m | 3,000 / **6,600** / 15,200 | 2,900 / **7,500** / 29,900 |
| Flame length | 2.7 / **4.1** / 5.9 m | 3.1 / **4.4** / 6.5 m | 3.0 / **4.7** / 8.9 m |
| Fire within 1 km / 500 m / 200 m | 15:30 / 15:35 / 15:39 | 15:30 / 15:36 / 15:39 | (already) / 15:34 / 15:37 |
| Active flames first in sight (2.5 m tops, bare earth), minutes before arrival | 5.4 / **8.7** / 19.3 | 6.2 / **10.2** / 23.1 | 4.8 / **7.5** / 15.7 |
| Share of the pre-front burned area visible at 15:28 | **0%** | **0%** | 0% (2.5 m tops) |
| Slope over the last 300 m | −1.5% (downhill) | −1.6% | −1.4% |

Reading:
1. **It arrived as a wide, oblique line, not the main head.** The fire came into the road head from the north-north-west, about 15–30° off the post-front wind, at roughly half the head-fire rate. It was the turning shoulder of the old south-east flank, about 2 km wide, so there was no edge to get around.
2. **It was still far beyond anything survivable or fightable on contact.** A median of about 5,500–6,600 kW/m with 4 m flames, laid over by a 48 km/h wind. In 10–90% of runs it was 2,200–15,000 kW/m. Direct attack fails above about 4,000 kW/m.
3. **The approach.** It covered about 1.1 km in about 14 minutes after the front, and the last 400 m in about 6.
4. **The terrain hid it.** The road head and Range 15 sit in a hollow (669 m) behind a 678 m rise about 600 m out. None of the pre-front fire was in line of sight at 15:28. Active flames came into view only about 9–10 minutes (median) before arrival, when the fire was about 700 m away. Smoke and the gust front were not hidden.
5. **No slope boost.** The fire came gently downhill into the hollow, so slope did not accelerate it.
6. **The edge.** Both official grids sit 10–20 m outside the mapped burn. The fire reached the road or track there and stopped, so the range area was on the margin of the burn, not in its middle.

## Caveats
- v5's post-front spread rate is effectively its prior (3.5–12.9 km/h at the head). Local rates and intensities inherit that spread.
- Directions and rates come from arrival-time gradients on a 40 m grid over about 200 m.
- Fuel load is the FBP grass default (0.35 kg/m²). Flame length uses Byram's formula.
- Sightlines use bare earth (MRDEM). The Copernicus surface model (with vegetation) gives the same answer at the road head and Range 15.

## Files
- Scripts are in `scripts/v6/fire_behaviour/`: `behaviour.py`, `sightlines.py`, `render3d.py`, `maps2d.py`, `render3d_figures.py` and `sprites.py`. They read the v5 stored run grids, which are written by `v5_ensemble.py` to the v5 scratch folder and are not committed because of their size.
- `tables/`: `behaviour_summary.json`, `sightline_summary.json` and the per-run CSVs
- `figures/`: `fig_plan_approach.png`, `fig_approach_timeline.png`, `fig_profile.png`, `fig_3d_from_southwest.png`, `fig_3d_from_northwest.png`
- `interactive/`: `3d_fire_arrival_range_area.html` and `3d_fire_with_figures_animated.html`. Both load plotly from a CDN.

## Figures added Nov. 1 (broader view, representative figures)
- `figures/fig3d_snapshots_sheet.png`: six 3D snapshots across the anti-tank and AGL ranges and the full burn. The snapshots are 12:17, 15:28, 15:33, 15:37, 15:40 and 15:42; each is also saved as `fig3d_snap_*.png`.
- `interactive/3d_fire_with_figures_animated.html`: interactive 3D with a time slider (12:17, then 15:26–15:46).
- Figures are **representative and not to scale**; DND has not said how many soldiers were where.
  - About 20 figures stand near Range 2 (grenade) and about 10 near Range 15 / road head, following Rutland's Oct. 18 description.
  - The prone AGL firing line at Range 11 appears in the morning panel only.
  - No figure is shown reacting, and figures are left out of the arrival panel.
- Sprites are in `sprites/`: simple generic silhouettes, plus the prone grenadier from the part 1 archive.
