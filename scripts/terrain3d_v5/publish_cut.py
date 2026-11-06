"""Publication cut of the v5 timeline film (3D-T3): slower pacing, Prime Rogue title and end cards, publication labels.
The base renders behind compose_story.py are not kept, so this works from the T3 draft itself:
  * retimes each storyboard segment (story.py durations) by its own factor, blending neighbouring frames;
  * replaces the "working results, not yet published" header label and footer with publication wording and the logo;
  * adds a house-style title card and an end card with sources, caveats and licence.
Usage: python3 publish_cut.py PART1_ROOT T3_DRAFT.mp4 OUT.mp4 ["PUBLICATION DATE"]
"""
import sys, os, subprocess, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
P1, SRC, OUT = sys.argv[1:4]; PUB = sys.argv[4] if len(sys.argv) > 4 else ""
F = "/usr/share/fonts/opentype/inter/"
f_ = lambda n, s: ImageFont.truetype(F + n, int(s))
B = lambda s: f_("Inter-Bold.otf", s); M = lambda s: f_("Inter-Medium.otf", s); R = lambda s: f_("Inter-Regular.otf", s)
D = lambda s: f_("InterDisplay-Black.otf", s); K = lambda s: f_("Inter-Black.otf", s)
BG = (28, 20, 15); GOLD = (212, 175, 104); CREAM = (238, 230, 214); MUTED = (169, 155, 132); NAVY = (30, 52, 82)
YEL = (255, 214, 0); INK = (20, 14, 10); FILM_INK = (14, 16, 20); AMBER = (255, 196, 64); FMUTED = (200, 205, 212)
LOGO = Image.open(P1 + "/data/graphics_published/oct20_flank_became_the_front/cfb-wainwright-burn-pattern.jpg").crop((1688, 1203, 1772, 1287))
W, H, FPS = 1920, 1080, 24

# storyboard segment boundaries (seconds in the draft) and slow-down factor for each
SEG = [(0, 4, 1.6), (4, 6, 1.3), (6, 9.5, 1.5), (9.5, 11.5, 1.3), (11.5, 15, 1.6), (15, 17.5, 1.6), (17.5, 21, 1.7),
       (21, 25.7, 1.5), (25.7, 29.2, 1.8), (29.2, 31.7, 1.6), (31.7, 35.2, 1.8), (35.2, 36.7, 1.3), (36.7, 58.7, 1.55),
       (58.7, 60.2, 1.3), (60.2, 63.2, 1.6), (63.2, 67.04, 2.2)]
knots_out, knots_src = [0.0], [0.0]
for a, b, k in SEG: knots_out.append(knots_out[-1] + (b - a) * k); knots_src.append(b)
DUR = knots_out[-1]

def header_fix(im):
    """Cover the amber 'not yet published' label (header band is translucent ink) and write the publication label."""
    a = np.asarray(im).copy()
    band = a[126:160, 980:1900].reshape(-1, 3); col = tuple(int(v) for v in np.median(band, 0))
    d = ImageDraw.Draw(im); d.rectangle([980, 128, 1906, 160], fill=col)
    lab = "RUBICON RIDGE · WORKING MODEL v5" + (f" · PUBLISHED {PUB.upper()}" if PUB else "") + " · PRIME ROGUE INC."
    d.text((1892, 144), lab, font=B(20), fill=AMBER, anchor="rm")
def footer_fix(im):
    d = ImageDraw.Draw(im); d.rectangle([0, H - 80, W, H], fill=FILM_INK)
    d.text((36, H - 66), "Clock not to scale · true scale · fire: Rubicon Ridge working model v5, weighted median of 1,440 runs (modelled) · observed: Landsat 8, VIIRS,", font=R(21), fill=FMUTED)
    d.text((36, H - 34), "CZWN wind, ECCC, Sentinel-2 scar · figures representative, not to scale · flames true scale (Byram) · smoke illustrative · ranges: 2024 Standing Orders", font=R(21), fill=FMUTED)
    lg = LOGO.resize((66, 66)); im.paste(lg, (W - 84, H - 74))

def card(lines_fn):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); d.rectangle([0, 0, 18, H], fill=GOLD); lines_fn(im, d); return np.asarray(im)
def title(im, d):
    d.text((90, 150), "CFB WAINWRIGHT FIRE · OCT. 17, 2026", font=B(34), fill=GOLD)
    d.text((84, 215), "How the fire ran", font=D(120), fill=CREAM)
    d.text((84, 345), "A 3D reconstruction, from the first wind", font=D(64), fill=CREAM)
    d.text((84, 420), "warning to the run past the ranges", font=D(64), fill=CREAM)
    d.text((90, 540), "Prime Rogue's working model v5, \"Rubicon Ridge\": the most likely fire across 1,440 model runs", font=M(30), fill=CREAM)
    d.text((90, 585), "weighted by fit to the burn scar, on true-scale terrain. Modelled, not observed.", font=M(30), fill=CREAM)
    lab = "WORKING MODEL v5 · RUBICON RIDGE"; bw = d.textlength(lab, font=K(32)) + 50
    d.rounded_rectangle([90, 700, 90 + bw, 770], radius=12, fill=YEL); d.text((115, 735), lab, font=K(32), fill=INK, anchor="lm")
    im.paste(LOGO.resize((150, 150)), (W - 230, 110))
    d.text((W - 80, H - 60), "Prime Rogue Inc." + (f" · {PUB}" if PUB else ""), font=B(26), fill=MUTED, anchor="rs")
def end(im, d):
    d.text((90, 110), "WHAT YOU WATCHED", font=B(34), fill=GOLD)
    L = [("The fire", "The weighted median of Rubicon Ridge v5's 1,440 best-fitting runs, cell by cell. Nothing is drawn burning before"),
         ("", "the first satellite detection at 12:17 p.m. The model has no smoke, embers, roads, firebreaks or firefighting."),
         ("The clock", "The gust reached the base weather station at 3:16 p.m.; the fitted front reached the fire at about 3:28."),
         ("", "The fire reached the official Range 2 grid at about 3:39 and Range 15 / the road head at about 3:42 (10-90%: 3:34-3:58)."),
         ("The figures", "Representative only. DND has not said where the soldiers were. No individual is placed or described."),
         ("The scenarios", "Leaving Range 2 at 3:28, 3:33 or 3:38 and the share of runs that got clear: modelled scenarios, not what happened."),
         ("Sources", "Landsat 8, VIIRS, Sentinel-2 (contains modified Copernicus Sentinel data, 2026), ECCC, Alberta ACIS, PurpleAir,"),
         ("", "NRCan MRDEM-30 terrain, CFB Wainwright Range Standing Orders (2024).")]
    y = 185
    for h, t in L:
        if h: d.text((90, y), h, font=B(30), fill=CREAM)
        d.text((330, y + 3), t, font=R(26), fill=MUTED if not h else CREAM); y += 46 + (12 if not h else 0)
    d.rectangle([0, H - 210, W, H], fill=NAVY); d.rectangle([0, H - 210, W, H - 202], fill=GOLD)
    d.text((90, H - 170), "Method, data and code: github.com/primerogueinc/cfb-wainwright-fire-archive-2", font=M(30), fill=CREAM)
    d.text((90, H - 125), "Video: Kevin J.S. Duska Jr. (Prime Rogue Inc.), CC BY-NC 4.0. A working model, not a final finding.", font=M(30), fill=CREAM)
    d.text((90, H - 60), "PRIME ROGUE", font=K(38), fill=GOLD)
    im.paste(LOGO.resize((150, 150)), (W - 230, H - 185))

def pipe_out(path):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
out = pipe_out(OUT); w = out.stdin
def emit(a, n=1):
    for _ in range(n): w.write(np.ascontiguousarray(a, dtype=np.uint8).tobytes())
def fade(a, b, n):
    for k in range(n): q = (k + 1) / (n + 1); emit(a * (1 - q) + b * q)
black = np.zeros((H, W, 3), np.uint8)
T = card(title); fade(black, T, 12); emit(T, int(5.0 * FPS))
cap = cv2.VideoCapture(SRC); NSRC = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); SFPS = cap.get(cv2.CAP_PROP_FPS)
buf = {}; cur = -1
def get(i):
    global cur
    i = min(i, NSRC - 1)
    while cur < i:
        ok, fr = cap.read(); cur += 1
        if not ok: buf[cur] = buf[cur - 1]; continue
        im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); header_fix(im); footer_fix(im); buf[cur] = np.asarray(im, np.float32)
        for k in [k for k in buf if k < cur - 2]: del buf[k]
    return buf[i]
nout = int(DUR * FPS); first = last = None
for j in range(nout):
    ts = float(np.interp(j / FPS, knots_out, knots_src)) * SFPS; i0 = int(ts); q = ts - i0
    a = get(i0); b = get(i0 + 1) if q > 1e-3 else a
    fr = a * (1 - q) + b * q
    if first is None: first = fr; fade(T.astype(np.float32), fr, 14)
    emit(fr); last = fr
E = card(end); fade(last, E.astype(np.float32), 14); emit(E, int(9.0 * FPS)); fade(E.astype(np.float32), black, 12)
w.close(); out.wait(); print("wrote", OUT, f"{DUR:.1f} s of film + cards")
