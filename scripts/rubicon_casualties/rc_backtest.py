"""Rubicon Casualties (v5.3), step 3: backtest summary and figures from rc_replicates.csv.
Observed (public, aggregate): 4 dead; 39 injured taken to hospital, 19 of them critical (Oct. 18); out of 84 C Company soldiers.
Usage: python3 rc_backtest.py RUN_DIR OUTDIR"""
import sys, os, json
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
RUN, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
df = pd.read_csv(os.path.join(RUN, "rc_replicates.csv"))
df["match"] = df.dead.between(2, 7) & df.critical.between(13, 26) & df.hospital_plus_close.between(30, 48)
df["match_strict"] = df.dead.between(3, 5) & df.critical.between(16, 22) & df.hospital_plus_close.between(35, 43)
df["casualties"] = df.dead + df.hospital_plus_close
LAB = {"official": "Official\ngrids", "low": "Low\n≤800 m", "high": "High\n≤800 m", "uniform": "Any\n≤800 m", "low_near": "Low\n≤400 m", "high_near": "Raised\n≤400 m"}
ORDER = ["low_near", "low", "official", "uniform", "high", "high_near"]
out = {}
acc = df.groupby("scenario").agg(n=("match", "size"), accept=("match", "mean"), accept_strict=("match_strict", "mean")).reindex(ORDER)
out["acceptance"] = acc.round(4).to_dict()
A = df[df.match]
prior = df
def q(s): return [round(float(s.quantile(x)), 2) for x in (.1, .5, .9)]
post = {}
for c in ("delay", "v0", "p_stay", "p_see", "k_skin", "p_through", "tres", "q0", "tau_a"):
    post[c] = dict(prior=q(prior[c]), accepted=q(A[c]))
post["delay"] = {k: [round(v / 60, 1) for v in vv] for k, vv in post["delay"].items()}
for c in ("mode", "radio", "sees", "dcue"):
    post[c] = dict(prior=prior[c].value_counts(normalize=True).round(3).to_dict(), accepted=A[c].value_counts(normalize=True).round(3).to_dict())
out["what_had_to_be_true"] = post; out["n_accepted"] = int(len(A))
# terrain effect, conditional on the same behaviour regime (group could see, moved within 3 min, nobody stayed put)
reg = df[(df.sees) & (df.delay <= 180) & (df.p_stay <= .15)]
out["terrain_effect_fast_response"] = reg.groupby("scenario")[["dead", "critical", "hospital_plus_close", "overrun", "med_warning_s"]].median().reindex(ORDER).round(1).to_dict()
reg2 = df[(~df.sees)]
out["terrain_effect_no_visual_cue"] = reg2.groupby("scenario")[["dead", "critical", "hospital_plus_close", "overrun"]].median().reindex(ORDER).round(1).to_dict()
out["warning_minutes_median_by_scenario"] = (df.groupby("scenario").med_warning_s.median() / 60).reindex(ORDER).round(1).to_dict()
json.dump(out, open(os.path.join(OUT, "rc_backtest_summary.json"), "w"), indent=1, default=str)
# ---------- figures
fig, axs = plt.subplots(1, 3, figsize=(15, 5), sharey=False)
for ax, (col, obs, ttl) in zip(axs, (("dead", 4, "Deaths"), ("critical", 19, "Critical"), ("hospital_plus_close", 39, "Taken to hospital (critical + non-critical + close-exposed)"))):
    data = [df.loc[df.scenario == s, col] for s in ORDER]
    ax.boxplot(data, showfliers=False, whis=(10, 90)); ax.axhline(obs, color="#dc2626", lw=2); ax.text(.6, obs + 1, f"reported: {obs}", color="#dc2626", fontsize=9, weight="bold")
    ax.set_xticks(range(1, len(ORDER) + 1)); ax.set_xticklabels([LAB[s] for s in ORDER], fontsize=7.5); ax.set_title(ttl, fontsize=10, loc="left"); ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("people (of 84)")
fig.suptitle("Rubicon Casualties (working model v5.3): modelled toll by where people were, all behaviour assumptions (boxes 25–75%, whiskers 10–90%)", fontsize=11, x=.01, ha="left")
fig.text(.01, .005, "Low = hollows (≥2 m below the 500 m average); High = rises (≥2 m above); Raised = ≥1 m above; Any = anywhere that burned; Official grids = 74 near Range 2, 10 near Range 15. Distances from the road head.", fontsize=7.5, color="#333")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(os.path.join(OUT, "fig_rc_toll_by_scenario.png"), dpi=150); plt.close(fig)
fig, ax = plt.subplots(figsize=(9, 4))
x = np.arange(len(ORDER)); ax.bar(x - .2, acc.accept * 100, .4, label="matches the reported toll (loose)", color="#1e3452"); ax.bar(x + .2, acc.accept_strict * 100, .4, label="strict", color="#d4af68")
ax.set_xticks(x); ax.set_xticklabels([LAB[s] for s in ORDER], fontsize=8); ax.set_ylabel("% of simulations"); ax.legend(fontsize=8); ax.spines[["top", "right"]].set_visible(False)
ax.set_title("How often each placement reproduces the reported toll (loose: 2–7 dead, 13–26 critical, 30–48 to hospital;\nstrict: 3–5, 16–22, 35–43)", fontsize=9.5, loc="left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_rc_acceptance.png"), dpi=150); plt.close(fig)
fig, axs = plt.subplots(2, 3, figsize=(13, 7))
for ax, (c, lab, sc) in zip(axs.ravel(), (("delay", "delay before moving (min)", 1 / 60), ("p_stay", "share not moving before the fire arrived", 1), ("k_skin", "share of heat reaching skin", 1),
                                         ("v0", "foot speed on the flat (m/s)", 1), ("p_through", "share who went through the flames", 1), ("p_see", "chance the group could see flames (smoke/dust)", 1))):
    b = np.linspace(prior[c].min() * sc, prior[c].max() * sc, 25)
    ax.hist(prior[c] * sc, bins=b, density=True, color="#cbd5e1", label="all simulations"); ax.hist(A[c] * sc, bins=b, density=True, histtype="step", lw=2.2, color="#dc2626", label="those matching the toll")
    ax.set_title(lab, fontsize=9.5, loc="left"); ax.set_yticks([]); ax.spines[["top", "right", "left"]].set_visible(False)
axs[0, 0].legend(fontsize=8)
fig.suptitle(f"What had to be true for the model to reproduce 4 dead / 19 critical / 39 in hospital ({len(A)} matching simulations)", fontsize=11, x=.01, ha="left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_rc_what_had_to_be_true.png"), dpi=150); plt.close(fig)
print(json.dumps(out, indent=1, default=str)[:6000])
