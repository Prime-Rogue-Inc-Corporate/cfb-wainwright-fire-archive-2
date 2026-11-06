"""Rubicon Ridge (working model v5) article graphics in the Prime Rogue house style (scripts/maps/pr.py in part 1).
Usage (from part 2's root): python3 scripts/rubicon_ridge/graphics/v5_graphics.py PART1_ROOT [V5_GRIDS_DIR]
Writes data/graphics_published/rubicon_ridge_v5/. V5_GRIDS_DIR (the arrival-grid package) is needed only for the map."""
import sys, os, json, glob, math
P1 = os.path.abspath(sys.argv[1]); P2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
GR = sys.argv[2] if len(sys.argv) > 2 else None
sys.path.insert(0, os.path.join(P1, "scripts/maps")); os.chdir(P1)
from pr import *
from pr import _LOGO
import pr; pr.REPO = P1 + "/"
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, io
from pyproj import Transformer
hx = lambda c: "#%02x%02x%02x" % c
OUT = os.path.join(P2, "data/graphics_published/rubicon_ridge_v5/"); os.makedirs(OUT, exist_ok=True)
SRC = "Data and code: github.com/primerogueinc/cfb-wainwright-fire-archive-2. Graphic: Kevin J.S. Duska Jr. (Prime Rogue Inc.), CC BY-NC 4.0."
KICK = "CFB WAINWRIGHT FIRE · WORKING MODEL V5 (RUBICON RIDGE) · OCT. 17"
MD = os.path.join(P2, "data/rubicon-ridge/model_v5/")
fp = json.load(open(MD + "front_plane.json"))
def fig(w, h):
    f, ax = plt.subplots(figsize=(w / 100, h / 100), facecolor=hx(BG)); ax.set_facecolor(hx(BG))
    for s in ax.spines.values(): s.set_color(hx(MUTED))
    ax.tick_params(colors=hx(CREAM), labelsize=13); return f, ax
def to_img(f):
    b = io.BytesIO(); f.savefig(b, dpi=100, facecolor=hx(BG)); plt.close(f); b.seek(0); return Image.open(b).convert("RGBA")
def save(im, name): im.convert("RGB").save(OUT + name, quality=92); print(name)
def tlabel(m):   # minutes after 3:00 p.m. -> "3:28"
    m = int(round(m)); return f"{3 + m // 60}:{m % 60:02d}"

# ------------------------------------------------------------------ 1. header, social card, thumbnail
ph = Image.open(P1 + "/data/authentic-stoic-stress-test/model_v3/severity_oct24/raw_views/sentinel2-20261024-true-colour-zoomed-out.png").convert("RGBA")
def hero(W, H, out, ts, ss):
    im = Image.new("RGBA", (W, H), BG + (255,))
    crop = ph.resize((int(H * 1.05 * ph.size[0] / ph.size[1]), int(H * 1.05))); im.paste(crop, (W - crop.size[0] + int(W * 0.12), -int(H * 0.02)))
    grad = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(grad)
    for x in range(W): gd.line([(x, 0), (x, H)], fill=int(255 * max(0, min(1, (W * 0.70 - x) / (W * 0.28)))))
    im.paste(Image.new("RGBA", (W, H), BG + (255,)), (0, 0), grad)
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 14, H], fill=GOLD)
    d.text((58, int(H * 0.08)), "CFB WAINWRIGHT FIRE · OCT. 17, 2026", font=B(int(ts * 0.36)), fill=GOLD)
    y = int(H * 0.08) + int(ts * 0.75)
    for l in ("The front hit the fire", "at 3:28, not 3:16"): d.text((54, y), l, font=D(ts), fill=CREAM); y += int(ts * 1.08)
    y += int(ss * 0.8)
    for t in ("A new reconstruction puts the fire at Range 2 and Range 15", "at about 3:39 to 3:42 p.m., closer to DND's \"just before 4:00\""):
        d.text((58, y), t, font=M(ss), fill=CREAM); y += int(ss * 1.4)
    bx, by = 58, H - int(H * 0.16); lab = "WORKING MODEL v5 · RUBICON RIDGE"; bw = d.textlength(lab, font=K(int(ss * 1.0))) + 40
    d.rounded_rectangle([bx, by, bx + bw, by + int(ss * 2.1)], radius=10, fill=YEL); d.text((bx + 20, by + int(ss * 1.05)), lab, font=K(int(ss * 1.0)), fill=INK, anchor="lm")
    d.text((W - 40, H - 34), "Sentinel-2, Oct. 24 · Prime Rogue", font=B(int(ss * 0.8)), fill=CREAM, anchor="rs")
    im.paste(_LOGO, (W - 84 - 40, 40)); save(im, out)
hero(1600, 900, "cfb-wainwright-v5-header.jpg", 92, 28)
hero(1200, 630, "cfb-wainwright-v5-og.jpg", 64, 21)
hero(1280, 720, "cfb-wainwright-v5-thumbnail.jpg", 78, 25)

# ------------------------------------------------------------------ 2. when the front arrived (map)
W, H = 1600, 1350
im, d = canvas(W, H, KICK, "The front reached the fire at about 3:28 p.m.",
               "Nine weather stations and air sensors fit one line moving at 77 km/h toward the east-southeast. The base's own station,\n15 km upwind, felt it at 3:16. Times are MDT, when each site's air changed (wind shift, humidity jump or dust spike).")
fc = fp["fire_centre_lonlat"]; kx = 111.32 * math.cos(math.radians(fc[1]))
def xy(lon, lat): return (lon - fc[0]) * kx, (lat - fc[1]) * 111.2
f, ax = fig(1500, 990)
gx, gy = fp["fit"]["gradient_min_per_km"]; t0 = fp["fit"]["t_fire_min"]; n = math.hypot(gx, gy); ux, uy = gx / n, gy / n
L = np.linspace(-200, 200, 10)
for tt in range(0, 61, 15):
    dd = (tt - t0) / n; px = ux * dd - uy * L; py = uy * dd + ux * L
    ax.plot(px, py, color=hx(BLUE), lw=1.6, ls=(0, (6, 4)), alpha=0.9)
    k = np.argmin(np.abs(py + 88)); ax.text(px[k] + 1.5, -88, f"{tlabel(tt)}", color=hx(BLUE), fontsize=12.5, weight="bold", va="bottom")
bx_, _ = xy(-110.005, fc[1]); ax.axvline(bx_, color=hx(MUTED), lw=1, alpha=0.6); ax.text(bx_ - 2, -95, "ALTA. | SASK.", color=hx(MUTED), fontsize=11, ha="center")
mk = {"CZWN": ("o", GOLD), "CWCT": ("o", GOLD), "CYLL": ("o", GOLD), "AGCM": ("s", CREAM), "PurpleAir": ("^", TEAL)}
for s in fp["stations"]:
    x, y = xy(s["lon"], s["lat"]); key = next(k for k in mk if k in s["name"]); m, c = mk[key]
    ax.scatter(x, y, marker=m, s=150, color=hx(c), edgecolors=hx(INK), zorder=5)
    nm = s["name"].replace(" AGCM", "").replace(" CZWN", " (base station)").replace(" CWCT", "").replace(" CYLL", "").replace(" (PurpleAir)", " (air sensor)")
    h, mm = map(int, s["t_mdt"].split(":")); ox, oy = (-3, 3) if "CZWN" in s["name"] else (3, 3)
    ax.text(x + ox, y + oy, f"{nm}\n{h - 12}:{mm:02d} p.m.", color=hx(CREAM), fontsize=12.5, weight="bold", zorder=6, ha="right" if "CZWN" in s["name"] else "left")
ax.scatter(0, 0, marker="*", s=900, color=hx(RED), edgecolors=hx(CREAM), linewidths=1.5, zorder=7)
ax.annotate("THE FIRE\nfront arrives about 3:28 p.m.\n(3:27-3:29, fitted from all these sites)", (0, 0), xytext=(28, -55), color=hx(RED), fontsize=15, weight="bold",
            arrowprops=dict(arrowstyle="-", color=hx(RED), lw=1.5), bbox=dict(boxstyle="round,pad=0.5", fc=hx(INK), ec=hx(RED)))
ax.plot([-95, -45], [-100, -100], color=hx(CREAM), lw=4); ax.text(-70, -96, "50 km", color=hx(CREAM), ha="center", fontsize=12)
ax.set_xlim(-110, 75); ax.set_ylim(-108, 70); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
h_ = [plt.Line2D([], [], ls="", marker="o", color=hx(GOLD), ms=11, label="Environment Canada weather station"),
      plt.Line2D([], [], ls="", marker="s", color=hx(CREAM), ms=10, label="Alberta Agriculture (ACIS) weather station"),
      plt.Line2D([], [], ls="", marker="^", color=hx(TEAL), ms=11, label="PurpleAir air sensor (front = dust spike)"),
      plt.Line2D([], [], color=hx(BLUE), ls=(0, (6, 4)), lw=1.6, label="Where the front was, every 15 minutes (fitted)")]
ax.legend(handles=h_, loc="upper left", facecolor=hx(PANEL), edgecolor=hx(MUTED), labelcolor=hx(CREAM), fontsize=12.5)
f.subplots_adjust(0.01, 0.01, 0.99, 0.99); im.paste(to_img(f), (50, 205))
footer(im, ["Front times: ECCC 1-minute and hourly SWOB, Alberta ACIS hourly humidity, PurpleAir dust spikes. Least-squares moving-plane fit, 9 sites, RMS 3.0 min;",
            "leave-one-out 3:27-3:29. Bellshill is the worst fit (7 min early). No instrument stood at the fire. Peak gusts can come after the front.", SRC], fh=140)
save(im, "cfb-wainwright-v5-front-arrival-map.jpg")

# ------------------------------------------------------------------ 3. the clock: v4, v5 and DND
summ = json.load(open(MD + "arrival_summary.json"))
W, H = 1600, 1180
im, d = canvas(W, H, KICK, "What moved: the front, then the fire",
               "Our published v4 timed the fire from the 3:16 gust at the base station. v5 times it from the front at the fire itself, 12 minutes later.\nBars show v5's likely range (10th to 90th percentile of runs weighted by fit to the burn scar); dots are medians.")
f, ax = fig(1500, 760)
rows = [("Cold front at the fire", 16, 27.89, 27.46, 28.54),
        ("Fire at Range 2 (official grid)", 21, 39, 34, 51),
        ("Fire at Range 15 (official grid)", None, 42, 36, 58),
        ("Fire at the road head", 26, 42, 36, 56)]
for i, (lab, v4, med, lo, hi) in enumerate(rows):
    y = len(rows) - i
    ax.plot([lo, hi], [y, y], color=hx(RED), lw=16, solid_capstyle="butt", alpha=0.85)
    ax.scatter(med, y, s=260, color=hx(CREAM), edgecolors=hx(INK), zorder=5); ax.text(med, y + 0.27, f"v5: {tlabel(med)}", color=hx(CREAM), fontsize=14, weight="bold", ha="center")
    if v4 is not None:
        ax.scatter(v4, y, s=200, marker="D", color=hx(MUTED), edgecolors=hx(INK), zorder=5); ax.text(v4, y - 0.38, f"v4: {tlabel(v4)}", color=hx(MUTED), fontsize=13, ha="center")
    ax.text(-1.5, y, lab, color=hx(CREAM), fontsize=14, ha="right", va="center", weight="bold")
ax.text(21, 1.6, "(v4's Range 2 point was 375 m west of the official grid)", color=hx(MUTED), fontsize=11, ha="center")
ax.axvspan(50, 60, color=hx(GOLD), alpha=0.16); ax.text(55, 4.75, "DND, Oct. 22:\n\"just before 4:00\"", color=hx(GOLD), fontsize=14, weight="bold", ha="center", va="top")
ax.set_xlim(10, 63); ax.set_ylim(0.3, 5.0); ax.set_yticks([]); [t.set_clip_on(False) for t in ax.texts]
ax.set_xticks(range(10, 61, 5)); ax.set_xticklabels([tlabel(t) for t in range(10, 61, 5)]); ax.grid(axis="x", color=hx(GRIDC))
ax.set_xlabel("p.m., Oct. 17 (MDT)", color=hx(CREAM), fontsize=13)
f.subplots_adjust(left=0.33, right=0.98, top=0.98, bottom=0.10); im.paste(to_img(f), (50, 210))
d = ImageDraw.Draw(im); d.text((54, 985), "In v4, fewer than one in ten runs reached the road head after 3:45. In v5, about a third do. DND's time is now inside the model's range, at its slow end.", font=B(19), fill=CREAM)
footer(im, ["v5: 2,160 runs varying front timing, post-front wind, fuel, spread rate and the April 2026 planned burn, weighted by fit to the burn scar (arrival_summary.json).",
            "v4: as published Oct. 25 (front 3:16; OpenStreetMap Range 2 point). DND: Maj.-Gen. Rutland, Oct. 22 briefing.", SRC], fh=140)
save(im, "cfb-wainwright-v5-clock.jpg")

# ------------------------------------------------------------------ 4. spread rate decides the clock
W, H = 1600, 1000
im, d = canvas(W, H, KICK, "How fast it ran decides the clock",
               "The burn scar fixes the fire's shape, not its speed. So v5 brackets the spread rate after the front.\nWhen the fire reached each point, by spread rate (medians).")
f, ax = fig(1500, 650)
cases = [("Slow (3.5-5 km/h)", [48, 54, 53], BLUE), ("Standard (7-10 km/h)", [38, 41, 40], GOLD), ("Fast (11-13 km/h, near the 12.7 km/h\nan independent expert said to expect)", [35, 37, 37], RED)]
pts = ["Range 2", "Range 15", "Road head"]
for j, p in enumerate(pts):
    y = 3 - j
    ax.text(31.2, y, p, color=hx(CREAM), fontsize=15, weight="bold", ha="right", va="center")
    xs = [c[1][j] for c in cases]; ax.plot([min(xs), max(xs)], [y, y], color=hx(MUTED), lw=2)
    for (lab, v, c) in cases:
        ax.scatter(v[j], y, s=380, color=hx(c), edgecolors=hx(INK), zorder=5); ax.text(v[j], y + 0.22, tlabel(v[j]), color=hx(c), fontsize=13, weight="bold", ha="center")
ax.axvspan(50, 60, color=hx(GOLD), alpha=0.14); ax.text(55, 3.55, "DND: \"just before 4:00\"", color=hx(GOLD), fontsize=13, weight="bold", ha="center")
ax.axvline(27.89, color=hx(CREAM), lw=1.5, ls="--"); ax.text(28.3, 3.55, "front at the fire 3:28", color=hx(CREAM), fontsize=12)
ax.set_xlim(24, 61); ax.set_ylim(0.3, 3.8); ax.set_yticks([]); ax.set_xticks(range(25, 61, 5)); ax.set_xticklabels([tlabel(t) for t in range(25, 61, 5)]); ax.grid(axis="x", color=hx(GRIDC))
h_ = [plt.Line2D([], [], ls="", marker="o", color=hx(c), ms=13, label=l) for l, _, c in cases]
ax.legend(handles=h_, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3, facecolor=hx(PANEL), edgecolor=hx(MUTED), labelcolor=hx(CREAM), fontsize=12)
f.subplots_adjust(left=0.12, right=0.98, top=0.98, bottom=0.24); im.paste(to_img(f), (50, 200))
footer(im, ["Medians of v5 runs at each spread-rate setting (standard Canadian grass spread, FBP O-1a, scaled). The fit to the scar can't tell them apart.",
            "This is the biggest unknown left in the timeline: it moves the arrival times by up to 15 minutes.", SRC], fh=140)
save(im, "cfb-wainwright-v5-spread-rate.jpg")

# ------------------------------------------------------------------ 5. front speed vs fire speed
W, H = 1600, 900
im, d = canvas(W, H, KICK, "1 km in 30-60 seconds is the wind, not the flames",
               "The Canadian Armed Forces said the fire covered about a kilometre in 30 to 60 seconds after the wind shifted.\nThat matches the speed of the wind front. Grass fires in winds like these spread far slower.")
f, ax = fig(1500, 520)
bars = [("Cold front (fitted, 77 km/h)", 77, 77, GOLD, "1 km in about 47 s"),
        ("What 1 km in 60 s would need", 60, 60, MUTED, "60 km/h"), ("What 1 km in 30 s would need", 120, 120, MUTED, "120 km/h"),
        ("The fire after the front (v5 range)", 3.5, 13, RED, "3.5-13 km/h: 1 km in about 5-17 min")]
for i, (lab, lo, hi, c, note) in enumerate(bars):
    y = len(bars) - i
    ax.barh(y, hi, color=hx(c), height=0.55, alpha=0.9 if c != MUTED else 0.55)
    if lo != hi: ax.barh(y, lo, color=hx(BG), height=0.55); ax.barh(y, hi - lo, left=lo, color=hx(c), height=0.55)
    ax.text(-2, y, lab, color=hx(CREAM), fontsize=14, weight="bold", ha="right", va="center"); ax.text(hi + 2, y, note, color=hx(CREAM), fontsize=13, va="center")
ax.set_xlim(0, 160); ax.set_ylim(0.4, 4.6); ax.set_yticks([]); ax.set_xlabel("km/h", color=hx(CREAM), fontsize=13); ax.grid(axis="x", color=hx(GRIDC))
f.subplots_adjust(left=0.27, right=0.98, top=0.98, bottom=0.12); im.paste(to_img(f), (50, 205))
footer(im, ["Front speed: v5 moving-plane fit (77.3 km/h; first fit 87 km/h gives about 41 s). Fire: v5 implied head-fire spread after the front, 3.5 to 11.6 km/h, plus the 12.7 km/h expert estimate.",
            "A fire can seem to arrive in seconds through smoke and dust, spotting, or a flank turning into a head fire. The data can't say which, if any, happened.", SRC], fh=140)
save(im, "cfb-wainwright-v5-front-vs-fire-speed.jpg")

# ------------------------------------------------------------------ 6. dust, not smoke (Wainwright town PurpleAir)
js = json.load(open(P2 + "/data/rubicon-ridge/raw/purpleair/size_fractions_107254.json"))
df = pd.DataFrame(js["data"], columns=js["fields"]).sort_values("time_stamp")
df["t"] = pd.to_datetime(df.time_stamp, unit="s") - pd.Timedelta(hours=6)
df = df[(df.t >= "2026-10-17 14:30") & (df.t <= "2026-10-17 16:30")]
W, H = 1600, 1000
im, d = canvas(W, H, KICK, "The 3:28 p.m. spike in Wainwright was dust",
               "The town's PurpleAir sensor, 8 km north-north-east of the fire, as the front passed. Coarse particles (PM10) jumped; the finest (PM1) barely moved.\nSmoke is mostly fine particles. Once the front passed, the town was upwind of the fire.")
f, ax = fig(1500, 620)
mins = (df.t - pd.Timestamp("2026-10-17 15:00")).dt.total_seconds() / 60
ax.plot(mins, df["pm10.0_atm"], color=hx(GOLD), lw=3, label="PM10 (coarse: dust)"); ax.plot(mins, df["pm2.5_atm"], color=hx(RED), lw=2.5, label="PM2.5")
ax.plot(mins, df["pm1.0_atm"], color=hx(TEAL), lw=2.5, label="PM1 (finest: smoke-sized)")
ax.axvline(28, color=hx(CREAM), ls="--", lw=1.5); ax.text(28.6, ax.get_ylim()[1] * 0.92, "front passes\n3:28 p.m.", color=hx(CREAM), fontsize=13)
ax.set_xticks(range(-30, 91, 15)); ax.set_xticklabels([("2:" if t < 0 else "3:" if t < 60 else "4:") + f"{t % 60:02d}" for t in range(-30, 91, 15)])
ax.set_ylabel("µg/m³ (sensor, ATM)", color=hx(CREAM), fontsize=13); ax.grid(color=hx(GRIDC))
ax.legend(loc="upper right", facecolor=hx(PANEL), edgecolor=hx(MUTED), labelcolor=hx(CREAM), fontsize=13)
f.subplots_adjust(left=0.07, right=0.98, top=0.97, bottom=0.08); im.paste(to_img(f), (50, 200))
footer(im, ["PurpleAir sensor 107254 (Wainwright Town Hall), 2-minute readings, uncorrected. Matching coarse spikes at Castor and Lloydminster as the front reached them.",
            "NOAA GOES-18/19 show no identifiable smoke plume from 2:30 to 5:30 p.m. (frontal cloud from about 3:50). None of this rules out smoke at ground level near the fire.", SRC], fh=140)
save(im, "cfb-wainwright-v5-dust-not-smoke.jpg")

# ------------------------------------------------------------------ 7. the model against the burn (map)
if GR:
    T10 = Transformer.from_crs(3400, 4326, always_xy=True)
    meta = np.load(GR + "/meta.npy"); minx, maxy, res, Hh, Ww = meta; Hh, Ww = int(Hh), int(Ww)
    medf = GR + "/_weighted_median.npy"
    if os.path.exists(medf): med, pb = np.load(medf)
    else:
        wt = pd.read_csv(MD + "fit_weights.csv").set_index("run").weight; names, grids = [], []
        for fn in sorted(glob.glob(GR + "/scar_*.npz")):
            z = np.load(fn)
            for k in z.files: names.append(k.replace("__", "|")); grids.append(z[k])
        Gs = np.stack(grids).astype("float32"); del grids; Gs[~np.isfinite(Gs) | (Gs >= 210 - 1e-6)] = np.inf
        ww = wt.reindex(names).fillna(0).values; keep = ww > 0; Gs = Gs[keep]; ww = ww[keep] / ww[keep].sum()
        med = np.empty((Hh, Ww), "float32"); pb = (np.isfinite(Gs) * ww[:, None, None]).sum(0)
        for r0 in range(0, Hh, 15):
            b = Gs[:, r0:r0 + 15]; o = np.argsort(b, 0); s_ = np.take_along_axis(b, o, 0); c_ = np.cumsum(ww[o], 0) - .5 * ww[o]
            med[r0:r0 + 15] = np.take_along_axis(s_, np.clip((c_ < .5).sum(0), 0, len(ww) - 1)[None], 0)[0]
        del Gs; np.save(medf, np.stack([med, pb]))
    Wl, El, Sl, Nl = -110.965, -110.855, 52.732, 52.800
    mp = Map(Wl, El, Sl, Nl, pxkm=200, date="2026-10-19"); base = mp.base(bright=1.05)
    MW, MH = base.size; im = Image.new("RGBA", (max(1600, MW + 100), MH + 380), BG + (255,))
    W, H = im.size
    can, d = canvas(W, H, KICK, "Where the model's fire went, minute by minute",
                    "v5's weighted-median fire position every 5 minutes after the front, over the burn mapped from our 70 cm image of Oct. 20.\nThe model burns the pocket by the road head and too little of the south-east corner: its main misfit.")
    im = can
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    burn = gpd.read_file(P2 + "/data/rubicon-ridge/satellogic_2026-10-20/outline_for_model_v5.geojson").to_crs(4326).geometry.union_all()
    mp.outline(ld, burn, CREAM, width=4)
    xs = minx + (np.arange(Ww) + .5) * res; ys = maxy - (np.arange(Hh) + .5) * res
    XX, YY = np.meshgrid(xs, ys); LON, LAT = T10.transform(XX, YY)
    fm = np.where(np.isfinite(med) & (pb >= .5), med, np.nan)
    cmap = plt.get_cmap("inferno_r")
    import matplotlib.colors as mc
    f2, a2 = plt.subplots(); cs = a2.contour(LON, LAT, np.nan_to_num(fm, nan=999), levels=list(range(30, 71, 5))); plt.close(f2)
    for lev, segs in zip(cs.levels, cs.allsegs):
        col = tuple(int(255 * v) for v in cmap(min(0.8, (lev - 28) / 50))[:3])
        for sgm in segs:
            if len(sgm) > 3: ld.line([mp.P(la, lo) for lo, la in sgm], fill=col + (255,), width=4)
        if segs:
            sg = max(segs, key=len); lo, la = sg[len(sg) // 2]; x, y = mp.P(la, lo); label(ld, (x, y), tlabel(lev), col=col, size=15, pad=4)
    rso = pd.read_csv(P1 + "/data/reference/range_standing_orders_2024/rso_points.csv")
    for nm, lat, lon in [(r["name"], r.lat, r.lon) for _, r in rso[rso.name.isin(["Range 2", "Range 15"])].iterrows()] + [("Road head", 52.77045, -110.89965)]:
        x, y = mp.P(lat, lon); ld.ellipse([x - 9, y - 9, x + 9, y + 9], fill=YEL + (255,), outline=INK + (255,), width=2)
        label(ld, (x + 16, y - 40) if nm == "Range 2" else ((x + 16, y - 10) if nm == "Road head" else (x - 150, y + 14)), nm, col=YEL, size=17)
    x0 = 50; y0 = 210; im.paste(Image.alpha_composite(base, lay), (x0, y0))
    d = ImageDraw.Draw(im); sx = x0 + MW - 40 - int(mp.pxkm); d.rectangle([sx, y0 + MH - 40, sx + int(mp.pxkm), y0 + MH - 34], fill=CREAM); label(d, (sx + mp.pxkm / 2, y0 + MH - 72), "1 km", col=CREAM, size=16, anchor="ma")
    lx = x0 + MW + 20 if W - (x0 + MW) > 300 else x0 + 20
    footer(im, ["Base: Sentinel-2 L2A false colour (SWIR, NIR, red), Oct. 19, 2026 (contains modified Copernicus Sentinel data). Burn outline derived from Satellogic 70 cm imagery (vectors only).",
                "Model: median arrival across runs weighted by fit to the scar, shown where at least half the weight burned. Range points: CFB Wainwright Range Standing Orders (2024).", SRC], fh=140)
    save(im, "cfb-wainwright-v5-model-vs-burn.jpg")
print("done")
