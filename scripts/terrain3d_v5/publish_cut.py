"""Publication cut of the v5 timeline film (3D-T3): slower pacing, Prime Rogue title and end cards, publication labels.
The base renders behind compose_story.py are not kept, so this works from the T3 draft itself:
  * retimes each storyboard segment (story.py durations) by its own factor, blending neighbouring frames;
  * replaces the "working results, not yet published" header label and footer with publication wording and the logo;
  * adds a house-style title card and an end card with sources, caveats and licence.
  * optional (MUSIC=lament.mp3): stretches the film to the CAF lament and lays it underneath;
  * optional (MEMORIAL=folder with keyed poppy.png, ppcli.png, ler.png): closing memorial card with the four names,
    carrying the last 15 s of the lament, then 4 s of silence. The badge and poppy images are not kept in this repo.
Usage: [MUSIC=...] [MEMORIAL=...] python3 publish_cut.py PART1_ROOT T3_DRAFT.mp4 OUT.mp4 ["PUBLICATION DATE"]
"""
import sys, os, subprocess, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
P1, SRC, OUT = sys.argv[1:4]; PUB = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else ""
MUSIC = os.environ.get("MUSIC")          # optional: lament audio; the film is stretched to its length
MEMORIAL = os.environ.get("MEMORIAL")    # optional: folder with keyed poppy.png, ppcli.png, ler.png (not kept in this repo)
MEM_MUSIC, MEM_SIL = 15.0, 4.0           # memorial card: last 15 s of the lament, then silence before black
M_IN, M_OUT = float(os.environ.get("M_IN", 27.8)), float(os.environ.get("M_OUT", 215.5))   # music section of the file (s)
TITLE_S, M_LEAD, TAIL = 6.0, 1.0, 2.5
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
MOVES = {1, 3, 11, 13}   # camera moves: keep near their own pace
END_S = 9.0
if MUSIC:   # stretch the static and clock segments so title + film + end card = the lament (music starts M_LEAD s in)
    if MEMORIAL:   # the memorial card carries the last phrase of the lament, then holds in silence
        END_S = 13.0; total = M_LEAD + (M_OUT - M_IN) + MEM_SIL + 12 / 24
        film = M_LEAD + (M_OUT - M_IN) - MEM_MUSIC - (TITLE_S - 0.5) - 14 / 24 - END_S - 2 * 14 / 24
    else:
        total = M_LEAD + (M_OUT - M_IN) + TAIL; END_S = 16.0
        film = total - TITLE_S - END_S - 3 * 14 / 24 - 12 / 24
    fixed = sum((b - a) * k for i, (a, b, k) in enumerate(SEG) if i in MOVES); var = sum((b - a) * k for i, (a, b, k) in enumerate(SEG) if i not in MOVES)
    sc = (film - fixed) / var; SEG = [(a, b, k if i in MOVES else k * sc) for i, (a, b, k) in enumerate(SEG)]
    print(f"stretch x{sc:.2f} on static segments, film {film:.1f} s, total {total:.1f} s")
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
         ("", "They fade as the fire reaches the range area: the model can't show what happened to anyone."),
         ("The scenarios", "Leaving Range 2 at 3:28, 3:33 or 3:38 and the share of runs that got clear: modelled scenarios, not what happened."),
         ("Music", "\"The Lament - Flowers of the Forest\", performed by Cpl Timothy Reid, Royal Canadian Air Force Pipes and Drums."),
         ("", "Canadian Armed Forces, 2021. Crown copyright, reproduced with credit, unaltered except for length and level."),
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

NAMES = [("Sgt. Morgan Wong", "The Loyal Edmonton Regiment, serving with 3rd Battalion, PPCLI"),
         ("Pte. Shaun Farrell", "3rd Battalion, Princess Patricia's Canadian Light Infantry"),
         ("Pte. Aidan Goulding", "3rd Battalion, Princess Patricia's Canadian Light Infantry"),
         ("Pte. Hayden Lykkemark", "3rd Battalion, Princess Patricia's Canadian Light Infantry")]
def memorial_layers():
    """Base card (poppy, Lest We Forget, crests, date) and one RGBA layer per name, for sequential fade-ins."""
    def asset(n, hgt):
        im = Image.open(os.path.join(MEMORIAL, n)).convert("RGBA"); im = im.crop(im.split()[-1].point(lambda v: 255 if v > 40 else 0).getbbox())
        return im.resize((round(im.width * hgt / im.height), hgt), Image.LANCZOS)
    base = Image.new("RGBA", (W, H), BG + (255,)); d = ImageDraw.Draw(base)
    pop = asset("poppy.png", 200); base.alpha_composite(pop, ((W - pop.width) // 2, 70))
    d.text((W // 2, 335), "Lest We Forget", font=D(76), fill=CREAM, anchor="mm")
    d.rectangle([W // 2 - 90, 392, W // 2 + 90, 395], fill=GOLD)
    for n, x in (("ppcli.png", 250), ("ler.png", W - 250)):
        c = asset(n, 300); base.alpha_composite(c, (x - c.width // 2, 470))
    d.text((W // 2, 905), "October 17, 2026  ·  CFB Wainwright", font=M(34), fill=GOLD, anchor="mm")
    d.text((W // 2, H - 42), "Badges and poppy shown in remembrance. No endorsement by DND, the regiments or the Royal Canadian Legion is implied.",
           font=R(20), fill=MUTED, anchor="mm")
    layers = []
    for i, (nm, unit) in enumerate(NAMES):
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(L); y = 455 + i * 105
        dl.text((W // 2, y), nm, font=B(46), fill=CREAM, anchor="mm"); dl.text((W // 2, y + 42), unit, font=R(25), fill=MUTED, anchor="mm")
        layers.append(np.asarray(L, np.float32))
    return np.asarray(base.convert("RGB"), np.float32), layers
NAME_T0, NAME_DT, NAME_FADE = 1.2, 2.2, 1.4

# ---- the figures at Range 2: when the fire reaches them they fade under a smoke veil instead of standing in the flames
# (the model can't show what happened to anyone). Draft-time schedule from story.py's shot C tmap: 3:39 = 49.4 s, 3:42 = 53.1 s.
BOX_C = (868, 428, 1046, 592); BOX_B = (885, 296, 982, 394); BOX_T = (860, 260, 1050, 600)
T_VEIL0, T_FADE0, T_FADE1, T_VEIL1, T_C_END, T_B = 48.6, 49.4, 52.2, 57.5, 58.7, 60.2
rng = np.random.default_rng(7); NOISE = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 18); NOISE = (NOISE - NOISE.min()) / (NOISE.max() - NOISE.min())
def box_at(t):
    return BOX_C if t <= T_C_END else (BOX_B if t >= T_B else BOX_T)
M0 = None   # static mask of the group in shot C (camera holds still), taken from a pre-fire frame
def white_mask(a):
    return cv2.dilate((a.min(2) >= 237).astype(np.uint8), np.ones((5, 5), np.uint8))
def figure_mask(a, box, lo=115):
    x0, y0, x1, y1 = box; sub = a[y0:y1, x0:x1].astype(np.int16)
    mx, mn = sub.max(2), sub.min(2)
    m = ((mx >= lo) & (mx <= 236) & ((mx - mn) < 42)).astype(np.uint8)
    white = cv2.dilate((mn >= 237).astype(np.uint8), np.ones((5, 5), np.uint8))   # dots, the scenario walker, label text
    m = cv2.dilate(m, np.ones((3, 3), np.uint8)) & (1 - white)
    if box == BOX_C: m[int(545 - y0):, int(1022 - x0):] = 0                          # keep the "Range 15 / road head" label
    full = np.zeros(a.shape[:2], np.uint8); full[y0:y1, x0:x1] = m; return full
def box_mask(shape, box):
    z = np.zeros(shape[:2], np.uint8); x0, y0, x1, y1 = box; z[y0:y1, x0:x1] = 1; return z
def figfix(a, t):
    """a: RGB uint8 frame of the draft at draft time t (s). Returns the frame with the Range 2 figures faded and veiled."""
    if t < T_VEIL0: return a
    out = a.copy()
    if t >= T_FADE0:
        box = box_at(t)
        if t <= T_C_END: m = cv2.dilate(M0, np.ones((3, 3), np.uint8)) & (1 - white_mask(a))
        else: m = figure_mask(a, box, lo=85)
        if m.any():
            ai = a.astype(np.int16); line = ((ai[..., 0] - np.maximum(ai[..., 1], ai[..., 2]) > 70) & (box_mask(a.shape, box) > 0)).astype(np.uint8)
            line = cv2.dilate(line, np.ones((3, 3), np.uint8))           # the red/amber scenario line: keep it, and don't let it bleed
            clean = cv2.inpaint(a, (m | line).astype(np.uint8), 5, cv2.INPAINT_TELEA)
            clean[line > 0] = a[line > 0]
            k = min(1.0, (t - T_FADE0) / (T_FADE1 - T_FADE0)); k = k * k * (3 - 2 * k)
            mm = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2)[..., None] * k
            out = (a * (1 - mm) + clean * mm).astype(np.uint8)
    if t < T_VEIL1 and t <= T_C_END:
        up = min(1.0, (t - T_VEIL0) / 1.6); down = max(0.0, min(1.0, (T_VEIL1 - t) / 2.5)); amp = 0.62 * min(up, down)
        cx, cy = 955 + (t - T_VEIL0) * 6, 492 - (t - T_VEIL0) * 2.5
        yy, xx = np.ogrid[:H, :W]
        g = np.exp(-(((xx - cx) / 120.0) ** 2 + ((yy - cy) / 78.0) ** 2))
        alpha = (amp * g * (0.55 + 0.45 * np.roll(NOISE, int(t * 30), axis=1)))[..., None]
        out = (out * (1 - alpha) + np.array([118, 110, 102], np.float32) * alpha).astype(np.uint8)
    return out
CAPTION = ("The fire reaches the range area at about 3:39 to 3:42. The model can't show what happened to each person.",
           "Officials said four soldiers died and 39 were taken to hospital, 19 in critical condition.")
def caption_box(im, t):
    if not (50.6 <= t <= T_C_END): return
    k = min(1.0, (t - 50.6) / 0.8, (T_C_END - t) / 0.6)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle([36, H - 196, 1330, H - 98], radius=10, fill=FILM_INK + (int(225 * k),))
    d.text((60, H - 182), CAPTION[0], font=M(25), fill=(255, 255, 255, int(255 * k)))
    d.text((60, H - 140), CAPTION[1], font=M(25), fill=(255, 214, 120, int(255 * k)))
    im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))

def pipe_out(path):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
out = pipe_out(OUT); w = out.stdin
def emit(a, n=1):
    for _ in range(n): w.write(np.ascontiguousarray(a, dtype=np.uint8).tobytes())
def fade(a, b, n):
    for k in range(n): q = (k + 1) / (n + 1); emit(a * (1 - q) + b * q)
black = np.zeros((H, W, 3), np.uint8)
T = card(title); fade(black, T, 12); emit(T, int((TITLE_S - 1.0) * FPS))
cap0 = cv2.VideoCapture(SRC); cap0.set(cv2.CAP_PROP_POS_FRAMES, int(46.0 * cap0.get(cv2.CAP_PROP_FPS))); _ok, _f = cap0.read()
M0 = cv2.dilate(figure_mask(cv2.cvtColor(_f, cv2.COLOR_BGR2RGB), BOX_C), np.ones((5, 5), np.uint8)); cap0.release()
cap = cv2.VideoCapture(SRC); NSRC = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); SFPS = cap.get(cv2.CAP_PROP_FPS)
buf = {}; cur = -1
def get(i):
    global cur
    i = min(i, NSRC - 1)
    while cur < i:
        ok, fr = cap.read(); cur += 1
        if not ok: buf[cur] = buf[cur - 1]; continue
        td = cur / SFPS; im = Image.fromarray(figfix(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB), td)); header_fix(im); footer_fix(im); caption_box(im, td); buf[cur] = np.asarray(im, np.float32)
        for k in [k for k in buf if k < cur - 2]: del buf[k]
    return buf[i]
nout = int(DUR * FPS); first = last = None; CLAST = None
for j in range(nout):
    tsec = float(np.interp(j / FPS, knots_out, knots_src))
    if T_C_END - 0.05 < tsec < T_B + 0.05:
        if CLAST is None: CLAST = get(int((T_C_END - 0.05) * SFPS)).copy()
        q = (tsec - (T_C_END - 0.05)) / (T_B + 0.1 - T_C_END); q = q * q * (3 - 2 * q)
        fr = CLAST * (1 - q) + get(int((T_B + 0.05) * SFPS)) * q
    else:
        ts = tsec * SFPS; i0 = int(ts); q = ts - i0
        a = get(i0); b = get(i0 + 1) if q > 1e-3 else a
        fr = a * (1 - q) + b * q
    if first is None: first = fr; fade(T.astype(np.float32), fr, 14)
    emit(fr); last = fr
E = card(end); fade(last, E.astype(np.float32), 14); emit(E, int(END_S * FPS))
if MEMORIAL:
    MB, ML = memorial_layers(); fade(E.astype(np.float32), MB, 14)
    for j in range(int((MEM_MUSIC + MEM_SIL) * FPS)):
        t = j / FPS; fr = MB.copy()
        for i, L in enumerate(ML):
            k = min(1.0, max(0.0, (t - NAME_T0 - i * NAME_DT) / NAME_FADE)); k = k * k * (3 - 2 * k)
            if k > 0: al = L[..., 3:4] / 255 * k; fr = fr * (1 - al) + L[..., :3] * al
        emit(fr); last = fr
    fade(last, black, 12)
else:
    fade(E.astype(np.float32), black, 12)
w.close(); out.wait(); print("wrote", OUT, f"{DUR:.1f} s of film + cards")
if MUSIC:   # lay the lament under the film: music from M_LEAD s, loudness-normalized, gentle fade at the end
    tmp = OUT[:-4] + "_silent.mp4"; os.replace(OUT, tmp)
    af = (f"atrim={M_IN}:{M_OUT},asetpts=PTS-STARTPTS,afade=t=in:d=0.8,afade=t=out:st={M_OUT - M_IN - 3}:d=3,"
          f"loudnorm=I=-18:TP=-1.5:LRA=11,adelay={int(M_LEAD * 1000)}|{int(M_LEAD * 1000)},apad")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", MUSIC, "-filter_complex", f"[1:a]{af}[a]", "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
    os.remove(tmp); print("music added")
