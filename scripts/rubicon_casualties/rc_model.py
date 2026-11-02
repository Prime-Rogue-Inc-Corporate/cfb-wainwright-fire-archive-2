"""Rubicon Casualties (working model v5.3), step 2: aggregate casualty Monte Carlo and backtest.

Purpose: test whether the v5 fire, on the real terrain, can produce the publicly reported toll (4 dead, 39 injured, 19 of them critical
on Oct. 18, out of 84 C Company soldiers per Maj.-Gen. Rutland) and how that depends on whether people were on low or high ground.
Positions are SCENARIOS, not reconstructions. Nothing here describes any individual.

Each replicate: one v5 run (weighted draw), a parameter draw, 84 people placed by the scenario rule. Each person:
  cue     = earliest of (active flames visible, 3 m tops) / (fire within d_cue) / (radio warning, if any)  + reaction delay
  escape  = mode drawn per replicate (50/50): 'nearest_safe' = straight line to the nearest ground that never burned in that run
            (needs knowing where the fire will stop); 'away' = directly away from the approaching flames (the fire's local direction of
            travel) until reaching ground that never burned, up to 1.5 km. Foot speed adjusted for slope (Tobler).
  overrun = the fire reaches a point on the path (or the start point) before the person does
  dose    = radiant pre-exposure while the fire closes (tilted flame panel, emissive power 70 kW/m2) + in-flame exposure if overrun
            (total heat flux q_f for the time inside the flame zone); thermal dose D = sum q^(4/3) dt  [(kW/m2)^(4/3) s, 'TDU']
  categories: dead / critical / hospital-level burn (non-critical) / 'close-exposed' (fire passed within 30 m without a burn-level dose:
            smoke and heat exposure, the kind of casualty usually transported in a mass-casualty response) / uninjured.
  outcome = effective skin dose D_eff = k_skin * D (clothing/kit cover); death by the Eisenberg probit Y = -14.9 + 2.56 ln(D_eff);
            critical if D_eff >= T_crit or airway exposure (time inside flames); hospital injury if D_eff >= T_inj.
Priors (uniform unless stated; deliberately wide, so the backtest can show what had to be true): foot speed 1.0-2.8 m/s; delay before
moving 0.5-12 min (log-uniform: noticing, deciding, gathering, accounting for people); visual cue works (smoke/dust) with probability
p_see ~ U(0,1) per group; proximity cue at 200/300/400 m or only once the fire is within ~25-50 m; share who stay put (vehicles,
sheltering, tasks) 0-60%; radio warning none (60%) /
15:32 (20%) / 15:36 (20%); flame residence 8-15 s; q_f 60-120 kW/m2 scaled by sqrt(local intensity / 6,000 kW/m); k_skin 0.1-0.6 (share of incident heat reaching skin through and around uniform, kit and helmet);
T_inj 150-350 TDU; T_crit 700-1,600 TDU; airway injury if inside flames p = 1 - exp(-t_in / tau_a), tau_a 4-12 s; share who turn and go through the flames to burned
ground 0-50%; anyone overrun close to unburned ground leaves the flames after the remaining distance.
Scenarios (84 people). Except 'official', people are placed on ground that burned (inside the observed scar), within 800 m of the
road head, because the official range grids themselves sit 10-20 m outside the burn:
  official   74 near Range 2 (sd 60 m), 10 near Range 15 (sd 30 m)  [Rutland, Oct. 18 and 22]
  low        hollow ground (TPI500 <= -2 m)
  high       rises (TPI500 >= +2 m)
  uniform    anywhere burned within 800 m
  low_near / high_near   within 400 m: hollow (TPI500 <= -2 m) / raised ground (TPI500 >= +1 m; there are few true rises this close)
Usage: python3 rc_model.py INPUTS_NPZ OUTDIR SCAR_MASK_NPY [N_REP]"""
import sys, os, json, math
import numpy as np, pandas as pd
from scipy.stats import norm
IN, OUT, SCAR = sys.argv[1:4]; NREP = int(sys.argv[4]) if len(sys.argv) > 4 else 2000
os.makedirs(OUT, exist_ok=True)
Z = np.load(IN); A = Z["A"].astype("float32"); SPD = Z["SPD"].astype("float32"); RI = Z["RI"]; z40 = Z["z40"]; tpi = Z["tpi"]
org = Z["org"]; TVIS = Z["TVIS"]; TNEAR = Z["TNEAR"]; minx, maxy, RES, H, W, rx, ry = Z["meta"]; H, W = int(H), int(W)
from pyproj import Transformer
T = Transformer.from_crs(4326, "EPSG:3400", always_xy=True)
R2 = T.transform(-110.90089, 52.772); R15 = T.transform(-110.89946, 52.77034)
X = minx + (np.arange(W) + .5) * RES; Y = maxy - (np.arange(H) + .5) * RES; XX, YY = np.meshgrid(X, Y)
dist0 = np.hypot(XX - rx, YY - ry)
def cells(mask): ii, jj = np.nonzero(mask); return np.c_[XX[ii, jj], YY[ii, jj]]
from scipy import ndimage
scar = ndimage.binary_erosion(np.load(SCAR), iterations=1)          # inside the observed burn (one 40 m cell in from its edge)
POOLS = {"low": cells((tpi <= -2) & (dist0 <= 800) & scar), "high": cells((tpi >= 2) & (dist0 <= 800) & scar), "uniform": cells((dist0 <= 800) & scar),
         "low_near": cells((tpi <= -2) & (dist0 <= 400) & scar), "high_near": cells((tpi >= 1) & (dist0 <= 400) & scar)}
print({k: len(v) for k, v in POOLS.items()})
def ij(x, y): return np.clip(((maxy - y) // RES).astype(int), 0, H - 1), np.clip(((x - minx) // RES).astype(int), 0, W - 1)
def place(scn, rng, n=84):
    if scn == "official":
        a = np.c_[rng.normal(R2[0], 60, 74), rng.normal(R2[1], 60, 74)]; b = np.c_[rng.normal(R15[0], 30, 10), rng.normal(R15[1], 30, 10)]
        return np.r_[a, b]
    p = POOLS[scn]; k = rng.integers(0, len(p), n); return p[k] + rng.uniform(-RES / 2, RES / 2, (n, 2))
def flux(d, L):  # radiant flux (kW/m2) from a wind-tilted grass flame front at horizontal distance d (m) ahead of its base
    tilt = np.radians(64.0); Hf = L * np.cos(tilt); lean = L * np.sin(tilt)
    de = np.maximum(d - lean, 0.5); return 70.0 * 0.5 * Hf / np.sqrt(Hf ** 2 + de ** 2)
def replicate(scn, rng):
    k = rng.integers(0, A.shape[0]); a = A[k] * 60.0   # seconds after 15:00
    v0 = rng.uniform(1.0, 2.8); delay = math.exp(rng.uniform(math.log(30), math.log(720))); dci = rng.integers(0, 4)
    p_see = rng.uniform(0, 1); p_stay = rng.uniform(0, .6)
    radio = rng.choice([np.inf, 32 * 60, 36 * 60], p=[.6, .2, .2]); tres = rng.uniform(8, 15); q0 = rng.uniform(60, 120)
    ks = rng.uniform(.1, .6); Tinj = rng.uniform(150, 350); Tcrit = rng.uniform(700, 1600)
    P = place(scn, rng); n = len(P); pi, pj = ij(P[:, 0], P[:, 1])
    o = np.argmin(np.hypot(org[None, :, 0] - P[:, 0, None], org[None, :, 1] - P[:, 1, None]), axis=1)
    sees = rng.random() < p_see                                        # smoke/dust: does the visual cue work for this group at all?
    near = TNEAR[k, o, min(dci, 2)] * 60 if dci < 3 else TNEAR[k, o, 0] * 60 + 200 / max(float(np.median(SPD[k][pi, pj])), .2)  # dci 3: ~0-50 m
    tcue = np.minimum.reduce([np.where(sees, TVIS[k, o] * 60, np.inf), near, np.full(n, radio)]) + delay
    stay = rng.random(n) < p_stay; tcue = np.where(stay, np.inf, tcue)
    mode = "away" if rng.random() < .5 else "nearest_safe"
    if mode == "nearest_safe":
        ri, rj = RI[k, 0, pi, pj], RI[k, 1, pi, pj]; tx, ty = XX[ri, rj], YY[ri, rj]
        dvec = np.c_[tx - P[:, 0], ty - P[:, 1]]; L = np.hypot(dvec[:, 0], dvec[:, 1])
    else:
        ak = np.where(np.isfinite(a) & (a < 7200), a, 7200.0)
        gy, gx = np.gradient(ak, RES); ux, uy = gx[pi, pj], -gy[pi, pj]; nn = np.hypot(ux, uy); nn = np.where(nn > 0, nn, 1)
        ux, uy = ux / nn, uy / nn                                     # direction the fire travels (arrival increases)
        sx = P[:, 0, None] + np.arange(0, 1510, 10)[None, :] * ux[:, None]; sy = P[:, 1, None] + np.arange(0, 1510, 10)[None, :] * uy[:, None]
        si, sj = ij(sx, sy); unb = ~(np.isfinite(a[si, sj]) & (a[si, sj] < 7200))
        stop = np.where(unb.any(1), unb.argmax(1), 150) * 10.0
        dvec = np.c_[ux * stop, uy * stop]; L = stop
    nst = np.maximum(1, np.ceil(L / 10).astype(int)); ms = int(nst.max())
    f = np.minimum(np.arange(ms + 1)[None, :] / nst[:, None], 1.0)
    px, py = P[:, 0, None] + f * dvec[:, 0, None], P[:, 1, None] + f * dvec[:, 1, None]
    ci, cj = ij(px, py); zz = z40[ci, cj]
    seg = np.hypot(np.diff(px, axis=1), np.diff(py, axis=1)); slope = np.where(seg > 0, np.diff(zz, axis=1) / np.maximum(seg, 1e-6), 0)
    v = v0 * np.exp(-3.5 * np.abs(slope + .05)) / math.exp(-3.5 * .05)
    dt = np.where(seg > 0, seg / v, 0); tpos = tcue[:, None] + np.c_[np.zeros(n), np.cumsum(dt, axis=1)]
    ta = a[ci, cj]; ta = np.where(np.isfinite(ta), ta, np.inf); vf = SPD[k][ci, cj].astype(float)
    # start: if the fire reaches the start point before they move, they are overrun there
    caught = ta <= tpos; caught[:, 1:] &= f[:, 1:] < 1.0      # reaching the refuge cell ends exposure
    first = np.where(caught.any(1), caught.argmax(1), -1)
    # radiant pre-dose along the path until caught or safe: gap = fire speed * time margin
    stepdt = np.c_[np.diff(tpos, axis=1), np.zeros(n)]
    I = 18000 * .35 * vf; Lf = .0775 * np.maximum(I, 300) ** .46
    with np.errstate(invalid='ignore'): gap = np.nan_to_num(np.clip((ta - tpos) * vf, 0, 500), nan=500.0, posinf=500.0)
    alive = np.arange(ms + 1)[None, :] <= np.where(first >= 0, first, ms)[:, None]
    qr = np.where(alive & np.isfinite(tpos) & (gap < 500), flux(gap, Lf), 0)
    # people waiting before moving: radiant exposure while stationary before tcue (fire may close in)
    t_wait = np.linspace(0, 1, 13)[None, :] * np.maximum(np.minimum(tcue, ta[:, 0]) - (ta[:, 0] - 120), 0)[:, None] + (ta[:, 0] - 120)[:, None]
    with np.errstate(invalid='ignore'): gw = np.nan_to_num(np.clip((ta[:, 0, None] - t_wait) * vf[:, 0, None], 0, 500), nan=500.0); qw = flux(gw, Lf[:, 0, None]); dtw = np.diff(t_wait, axis=1)
    Dw = ((qw[:, 1:] ** (4 / 3)) * dtw * (t_wait[:, 1:] < tcue[:, None])).sum(1)
    stepdt = np.nan_to_num(stepdt, nan=0.0, posinf=0.0)
    D = np.nan_to_num(((qr ** (4 / 3)) * stepdt).sum(1)) + np.nan_to_num(Dw)
    # in-flame dose for those overrun
    rowk = np.arange(n); fk = np.maximum(first, 0)
    vfl = vf[rowk, fk]; Il = I[rowk, fk]; vp = np.where(first > 0, v0, 0.0)
    p_through = rng.uniform(0, .5); tau_a = rng.uniform(4, 12)
    through = rng.random(n) < p_through                                  # turn and go through the flames to burned ground
    tin = np.where(vp < vfl, tres * vfl / np.maximum(vfl - vp, 0.05), tres); tin = np.minimum(tin, 3 * tres)
    tin = np.where(through & (vp > 0), tres * vfl / (vfl + vp), tin)
    r_rem = (1 - f[rowk, fk]) * L                                        # overrun close to unburned ground: out of the flames sooner
    tin = np.where(vp > 0, np.minimum(tin, r_rem / np.maximum(vp, .1) + 1.0), tin)
    qf = q0 * np.clip(np.sqrt(Il / 6000), .5, 1.5)
    D = D + np.where(first >= 0, qf ** (4 / 3) * tin, 0)
    De = ks * D
    pdead = norm.cdf(-14.9 + 2.56 * np.log(np.maximum(De, 1e-9)) - 5)
    dead = rng.random(n) < pdead
    airway = (first >= 0) & (rng.random(n) < 1 - np.exp(-tin / tau_a))
    crit = ~dead & ((De >= Tcrit) | airway); inj = ~dead & ~crit & (De >= Tinj)
    gmin = np.where(alive & np.isfinite(tpos), gap, 500).min(1)
    close = ~dead & ~crit & ~inj & (first < 0) & (gmin < 30)          # fire passed within 30 m: smoke/heat exposure, likely transported
    return dict(run=int(k), mode=mode, v0=v0, delay=delay, dcue=(200, 300, 400, 25)[dci], p_through=p_through, tau_a=tau_a, p_see=p_see, sees=bool(sees), p_stay=p_stay, radio=("none" if not np.isfinite(radio) else f"15:{int(radio // 60)}"),
                tres=tres, q0=q0, k_skin=ks, T_inj=Tinj, T_crit=Tcrit, dead=int(dead.sum()), critical=int(crit.sum()), injured_noncrit=int(inj.sum()), close_exposed=int(close.sum()),
                overrun=int((first >= 0).sum()), mean_tpi=float(tpi[pi, pj].mean()), med_warning_s=float(np.median(ta[:, 0] - tcue)),
                frac_moved_before_arrival=float(np.mean(tcue < ta[:, 0])))
OBS = dict(dead=4, critical=19, hospital=39)
rows = []
for scn in ("official", "low", "high", "uniform", "low_near", "high_near"):
    rng = np.random.default_rng(hash(scn) % 2**32)
    for r in range(NREP):
        d = replicate(scn, rng); d["scenario"] = scn; d["hospital"] = d["critical"] + d["injured_noncrit"]; d["hospital_plus_close"] = d["hospital"] + d["close_exposed"]; rows.append(d)
    print(scn, flush=True)
df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, "rc_replicates.csv"), index=False)
df["match"] = df.dead.between(2, 7) & df.critical.between(13, 26) & df.hospital_plus_close.between(30, 48)
df["match_burns_only"] = df.dead.between(2, 7) & df.critical.between(13, 26) & df.hospital.between(30, 48)
df["match_strict"] = df.dead.between(3, 5) & df.critical.between(16, 22) & df.hospital_plus_close.between(35, 43)
summ = df.groupby("scenario").agg(dead_med=("dead", "median"), dead_p10=("dead", lambda s: s.quantile(.1)), dead_p90=("dead", lambda s: s.quantile(.9)),
                                  crit_med=("critical", "median"), crit_p10=("critical", lambda s: s.quantile(.1)), crit_p90=("critical", lambda s: s.quantile(.9)),
                                  hosp_med=("hospital", "median"), hosp_p10=("hospital", lambda s: s.quantile(.1)), hosp_p90=("hospital", lambda s: s.quantile(.9)),
                                  overrun_med=("overrun", "median"), close_med=("close_exposed", "median"), match_rate=("match", "mean"), match_burns_only=("match_burns_only", "mean"), match_strict=("match_strict", "mean"),
                                  warning_med_min=("med_warning_s", lambda s: s.median() / 60), mean_tpi=("mean_tpi", "mean")).round(2)
summ.to_csv(os.path.join(OUT, "rc_scenario_summary.csv")); print(summ.to_string())
json.dump(dict(observed=OBS, n_rep=NREP), open(os.path.join(OUT, "rc_meta.json"), "w"))
