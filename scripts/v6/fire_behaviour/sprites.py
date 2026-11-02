"""Draw simple representative soldier silhouettes (standing, kneeling) as RGBA PNGs. Generic shapes, no insignia; for 'not to scale'
figures in the 3D renders. The prone grenadier sprite is copied from the part 1 archive (data/terrain3d/layers/prone_launcher_right.png).
Usage: python3 sprites.py OUTDIR ARCHIVE_1"""
import sys, os, shutil
from PIL import Image, ImageDraw
OUT, A1 = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
S = 4  # supersample
def soldier(kneel=False, right=True):
    W, H = 70 * S, 140 * S; im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = (255, 255, 255, 255)
    cx = 35 * S
    top = 40 * S if kneel else 8 * S
    # helmet + head
    d.ellipse([cx - 11 * S, top, cx + 11 * S, top + 18 * S], fill=c)
    d.rectangle([cx - 13 * S, top + 8 * S, cx + 13 * S, top + 11 * S], fill=c)
    d.ellipse([cx - 8 * S, top + 9 * S, cx + 8 * S, top + 25 * S], fill=c)
    # torso with pack
    t0 = top + 24 * S; tl = 42 * S
    d.rounded_rectangle([cx - 13 * S, t0, cx + 13 * S, t0 + tl], radius=5 * S, fill=c)
    d.rounded_rectangle([cx - 20 * S, t0 + 4 * S, cx - 10 * S, t0 + 30 * S], radius=3 * S, fill=c)
    # arms + rifle held across
    d.line([cx + 10 * S, t0 + 6 * S, cx + 20 * S, t0 + 28 * S], fill=c, width=7 * S)
    d.line([cx - 4 * S, t0 + 30 * S, cx + 30 * S, t0 + 2 * S], fill=c, width=4 * S)
    if kneel:
        hb = t0 + tl
        d.line([cx - 6 * S, hb, cx - 6 * S, hb + 26 * S], fill=c, width=10 * S)          # kneeling leg (shin on ground)
        d.line([cx - 6 * S, hb + 26 * S, cx - 26 * S, hb + 30 * S], fill=c, width=9 * S)
        d.line([cx + 6 * S, hb, cx + 22 * S, hb + 4 * S], fill=c, width=10 * S)          # forward thigh
        d.line([cx + 22 * S, hb + 4 * S, cx + 22 * S, hb + 30 * S], fill=c, width=9 * S)
        d.rectangle([cx + 16 * S, hb + 27 * S, cx + 30 * S, hb + 31 * S], fill=c)
    else:
        hb = t0 + tl
        d.line([cx - 6 * S, hb - 2 * S, cx - 8 * S, H - 8 * S], fill=c, width=13 * S)
        d.line([cx + 6 * S, hb - 2 * S, cx + 8 * S, H - 8 * S], fill=c, width=13 * S)
        d.rectangle([cx - 17 * S, H - 9 * S, cx - 3 * S, H - 4 * S], fill=c); d.rectangle([cx + 3 * S, H - 9 * S, cx + 17 * S, H - 4 * S], fill=c)
    im = im.resize((W // S, H // S), Image.LANCZOS)
    im = im.crop(im.getbbox())
    return im if right else im.transpose(Image.FLIP_LEFT_RIGHT)
for k, kn in (("standing", False), ("kneeling", True)):
    for side in ("right", "left"):
        soldier(kn, side == "right").save(os.path.join(OUT, f"{k}_{side}.png"))
shutil.copy(os.path.join(A1, "data/terrain3d/layers/prone_launcher_right.png"), os.path.join(OUT, "prone_right.png"))
print(os.listdir(OUT))
