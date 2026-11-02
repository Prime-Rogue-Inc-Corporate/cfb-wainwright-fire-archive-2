"""Plan-view map (median arrival isochrones, direction of travel, ground hidden from the road head) and approach-timeline chart.
Usage: python3 maps2d.py GRIDS_DIR OUTDIR"""
import sys, os, json
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.colors import LightSource
from pyproj import Transformer
G, OUT = sys.argv[1:3]
minx, maxy, RES, H, W = np.load(os.path.join(G, "meta.npy")); H, W = int(H), int(W)
med = np.load(os.path.join(OUT, "median_arrival_min_after_1500.npy")); z10 = np.load(os.path.join(OUT, "dem10_mrdem.npy")); hr = np.load(os.path.join(OUT, "hreq_mrdem_roadhead.npy"))
bs = json.load(open(os.path.join(OUT, "behaviour_summary.json"))); ss = json.load(open(os.path.join(OUT, "sightline_summary.json")))
T = Transformer.from_crs(4326, "EPSG:3400", always_xy=True); rx, ry = T.transform(-110.89965, 52.77045)
P = {"Road head": (-110.89965, 52.77045), "Range 15": (-110.89946, 52.77034), "Range 2": (-110.90089, 52.772)}
E10 = [minx - rx, minx + W * RES - rx, maxy - H * RES - ry, maxy - ry]
x0, x1, y0, y1 = -3200, 1200, -1900, 1900
fig, ax = plt.subplots(figsize=(11, 9.4))
hs = LightSource(315, 40).hillshade(np.nan_to_num(z10, nan=np.nanmean(z10)), vert_exag=6, dx=10, dy=10)
ax.imshow(hs, extent=E10, cmap="gray", vmin=0, vmax=1.2)
hidden = np.where(hr > 6, 1.0, np.nan)
ax.imshow(hidden, extent=E10, cmap="Blues", vmin=0, vmax=1.4, alpha=.45)
pre = np.where(med <= 28, 1.0, np.nan); ax.imshow(pre, extent=E10, cmap="Greys", vmin=0, vmax=1.3, alpha=.55)
xs = minx + (np.arange(W) + .5) * RES - rx; ys = maxy - (np.arange(H) + .5) * RES - ry
from scipy import ndimage
sc = ndimage.binary_erosion(np.load(os.path.join(G, "scar_m.npy")), iterations=1)
cs = ax.contour(xs, ys, np.where((med > 28) & sc, med, np.nan), levels=np.arange(30, 61, 2), cmap="inferno_r", linewidths=1.6)
ax.clabel(cs, fmt=lambda v: f"15:{int(v):02d}" if v < 60 else "16:00", fontsize=7.5, inline=True)
for k, (lo, la) in P.items():
    x, y = T.transform(lo, la); ax.plot(x - rx, y - ry, "D" if k != "Range 15" else "*", ms=8 if k != "Range 15" else 13, mfc="gold" if k == "Range 15" else "w", mec="k", zorder=6)
d = np.radians(bs["Road head"]["direction_of_travel_deg_weighted_mean"])
ax.annotate("", xy=(0, 0), xytext=(-700 * np.sin(d), -700 * np.cos(d)), arrowprops=dict(color="#dc2626", width=3, headwidth=12))
ax.text(-760 * np.sin(d) - 40, -760 * np.cos(d) + 40, f"fire's travel into the\nroad head (~{bs['Road head']['direction_of_travel_deg_weighted_mean']}°)", color="#dc2626", fontsize=8.5, weight="bold", ha="right")
ax.annotate("", xy=(700, -650), xytext=(200, -150), arrowprops=dict(color="#2563eb", width=2, headwidth=10)); ax.text(720, -700, "post-front wind\n(from ~310°)", color="#2563eb", fontsize=8.5, weight="bold")
for r in (500, 1000):
    t = np.linspace(0, 2 * np.pi, 200); ax.plot(r * np.cos(t), r * np.sin(t), color="w", lw=.8, ls="--"); ax.text(r * .71, r * .71, f"{r} m", color="w", fontsize=8)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_xticks([]); ax.set_yticks([])
ax.legend(handles=[Patch(fc="#555", alpha=.7, label="Burned before the front reached the fire (~15:28)"), Line2D([], [], color="#f59e0b", lw=1.6, label="Weighted-median fire position, every 2 min after the front"),
                   Patch(fc="#60a5fa", alpha=.6, label="Ground where even 6 m flames are hidden from a standing person at the road head"),
                   Line2D([], [], ls="", marker="D", mfc="w", mec="k", label="Road head, Range 2 (official grid)"), Line2D([], [], ls="", marker="*", mfc="gold", mec="k", ms=12, label="Range 15 (official grid)")], loc="lower left", fontsize=8, framealpha=.92)
ax.set_title("How the fire came into the range area after the wind shift (v5 ensemble, weighted median) · working model v5", fontsize=10.5, loc="left")
fig.text(.01, .005, "Terrain: NRCan MRDEM-30 hillshade (×6). Hidden ground: line of sight from 1.7 m eye height at the road head over bare earth. Model: Prime Rogue v5 (1,425 weighted runs, 99.5% of weight).", fontsize=6.6, color="#333")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_plan_approach.png"), dpi=150); plt.close(fig)
# ---------- approach timeline (median distance + first in sight + arrival)
runs = pd.read_csv(os.path.join(OUT, "behaviour_runs.csv"))
fig, ax = plt.subplots(figsize=(11, 4.4))
ap = bs["Road head"]["approach_median_distance_m_by_minute"]; tt = [int(k.split(":")[1]) + (60 if k.startswith("16") else 0) for k in ap]; dd = [v for v in ap.values()]
ax.plot(tt, dd, color="#1e3452", lw=2.5, marker="o", ms=3, label="Distance from the road head to the nearest fire (weighted median)")
arr = bs["Road head"]["arrival"]; am = [int(a.split(":")[1]) for a in arr]
ax.axvspan(am[0], am[2], color="#f59e0b", alpha=.15, label=f"Fire reaches road head (10–90%: {arr[0]}–{arr[2]})"); ax.axvline(am[1], color="#b45309", lw=1.5)
ax.axvline(28, color="#0e7490", ls="--"); ax.text(28.2, 1150, "front reaches\nthe fire ~15:28", color="#0e7490", fontsize=8, va="top")
lead = ss["summary"]["Road head"]["MRDEM (bare earth) | flame top 2.5 m: minutes between active front first in sight and arrival (10/50/90)"]
ax.axvspan(am[1] - lead[1], am[1], ymin=0, ymax=.06, color="#dc2626", alpha=.8); ax.text(am[1] - lead[1], 80, f"flames first in sight ~{lead[1]:.0f} min before\narrival (median; hidden by the rise before that)", color="#dc2626", fontsize=8)
ax.set_xlim(20, 55); ax.set_ylim(0, 1250); ax.set_xticks(range(20, 56, 5)); ax.set_xticklabels([f"15:{m:02d}" for m in range(20, 56, 5)])
ax.set_ylabel("metres"); ax.legend(fontsize=8, loc="upper right"); ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Approach to the road head after the wind shift: ~1.1 km in ~14 minutes, the last 400 m in ~6 · working model v5", fontsize=10, loc="left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_approach_timeline.png"), dpi=150); plt.close(fig)
# ---------- profile
pr = ss["profiles"]["Road head"]
fig, ax = plt.subplots(figsize=(11, 3.4))
ax.fill_between(pr["dist_m"], 650, pr["elev_m"], color="#a3a38c"); ax.plot(pr["dist_m"], pr["elev_m"], color="k", lw=1)
ax.plot(0, pr["elev_m"][pr["dist_m"].index(0)] + 1.7, marker="$☺$", ms=14, color="#1e3452"); ax.text(10, pr["elev_m"][pr["dist_m"].index(0)] + 3, "eye 1.7 m at the road head", fontsize=8)
ax.set_xlim(-1200, 100); ax.set_ylim(655, 690); ax.set_xlabel("metres along the fire's direction of travel (negative = where the fire came from)"); ax.set_ylabel("elevation (m)")
ax.set_title("Ground the fire crossed into the road head (MRDEM): a 678 m rise 600 m out, then gently downhill into a hollow at 669 m", fontsize=10, loc="left")
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_profile.png"), dpi=150)
print("ok")
