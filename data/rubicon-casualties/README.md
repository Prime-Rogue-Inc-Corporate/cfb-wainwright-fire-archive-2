# Rubicon Casualties (working model v5.3, Nov. 1, 2026)

**Question:** using the v5 (Rubicon Ridge) fire, run over the real terrain, can the model reproduce the publicly reported toll? And does it matter whether people were on low or high ground? It's a backtest: model against aggregate public figures. It is not a reconstruction of anyone's position, actions or injuries. Prime Rogue Inc., CC BY-NC 4.0. Times MDT.

**Reported toll used:**
- 4 dead.
- 39 injured and taken to hospital, 19 of them critical (premier and officials, Oct. 18).
- Out of 84 C Company soldiers training in the area (Maj.-Gen. Rutland, Oct. 18).

## What the model does (`scripts/rubicon_casualties/`)

1. **Fire (`rc_inputs.py`).** 300 runs drawn from the weighted v5 ensemble, with fire arrival time, local spread speed, and the nearest ground that never burned in each run.
2. **Terrain.** NRCan MRDEM-30. Hollow = 2 m or more below the 500 m average; rise = 2 m or more above it.
3. **What people could see.** Lines of sight from an 80 m lattice of points around the road head (eye height 1.7 m; a flame top of 3 m counts as visible).
4. **People (`rc_model.py`).** 84 people per simulation, placed by scenario:
   - **official grids:** 74 near Range 2, 10 near Range 15;
   - **low ground:** hollows on ground that burned, within 400 m or 800 m of the road head;
   - **high ground:** rises within 800 m, or ground at least 1 m raised within 400 m;
   - **anywhere burned** within 800 m.
5. **Each person:**
   - **Starts moving** at the first warning (flames visible, the fire within 200–400 m or about 25–50 m, or a radio warning), plus a delay.
   - **Moves** either toward the nearest ground that didn't burn, or directly away from the fire. Walking speed is adjusted for slope.
   - **Is overrun** if the fire reaches any point on their route before they do.
6. **Heat dose.** Radiant heat while the fire closes in, plus time inside the flames if overrun. Measured as thermal dose (heat flux^4/3 × seconds).
7. **Outcomes:**
   - death on the Eisenberg probit;
   - critical: a high dose, or airway exposure from time inside the flames;
   - non-critical burn;
   - "close-exposed": the fire passed within 30 m without a burn-level dose (the kind of casualty usually transported in a mass-casualty response);
   - uninjured.
8. **Assumptions are deliberately wide** (see the docstring), so the backtest can show which conditions are needed.
9. **Scale.** 6,000 simulations per scenario, 36,000 in all.
10. **Backtest (`rc_backtest.py`).**
    - Loose match: 2–7 dead, 13–26 critical, 30–48 to hospital.
    - Strict match: 3–5, 16–22, 35–43.

## Results

**1. The model can reproduce the toll, but only in a narrow range of conditions.** About 1% of simulations match loosely and about 0.1% strictly.

**2. In the matching simulations** (319):

| | Median (10–90%) |
|---|---|
| People overrun by the flames | **32** (22–40) of 84 |
| Dead / critical / non-critical burn / close-exposed | 4 / 23 / 5 / 7 |
| Warning: time between starting to move and the fire's arrival (median person) | **about 5 min** (1.7–10) |
| Share who got moving before the fire reached their starting point | **71%** (55–90%) |
| Share of incident heat reaching skin | **0.26** (0.16–0.41), against a prior of 0.10–0.60 |

- **What had to be true:** a large share of the group (roughly 20–45%) did not get moving before the fire arrived, and effective warning was about 5 minutes for the median person.
- **Why the exposures had to be limited:** keeping deaths around 4 with about 32 people overrun needs short time in the flames or partial protection. Examples are passing quickly through or past the flame edge, ending up near unburned ground, or protection from uniform, kit and helmet.
- **No blame implied:** these are conditions the numbers require, not findings about anyone's decisions. They are consistent with flames hidden by terrain, smoke and dust, no warning reaching the group, or people committed to tasks or vehicles.

**3. High vs low ground is a second-order effect.**
- **Matching rate:** loose matches run 0.8–1.1% for low ground, high ground, the official grids and anywhere burned. "Raised ground within 400 m" is 0.4%, but that pool is very small (there is little raised ground that close to the road head).
- **When the group could see the flames, moved within 3 minutes, and nobody stayed behind:** about 7–9 people overrun, about 2 dead and 3–4 critical in every placement. Fewer casualties than reported.
- **When the group couldn't see the flames (smoke and dust):** 53–71 overrun in every placement.
- **So behaviour and warning dominate; terrain matters through them.**
  - The road-head hollow and the 678 m rise hide the flames until about 9–10 minutes out (see `data/v6/fire_behaviour_at_overrun`).
  - Escaping uphill out of a hollow is slower.
  - The rises within 800 m sit closer to the fire's path, which offsets their better view.

**4. Placing everyone at the official range grids does not by itself produce casualties.** Both grids sit 10–20 m outside the burn. Casualties need people on ground that burned, consistent with field-firing lanes running out into the burn area.

## Limits
- **Dose and outcome rules come from literature priors** (Eisenberg probit; burn-dose thresholds), not from any patient data. The heat-to-skin share stands in for clothing, posture and kit.
- **The non-critical hospital category includes "close-exposed" people.** Hospital counts in a mass-casualty response include precautionary transports, smoke and heat exposure. Without that category, the model rarely produces enough non-critical injuries.
- **The fire is v5's weighted ensemble.** Its post-front spread rate is essentially a prior.
- **Movement is simplified:** straight-line routes, no vehicles, everyone acting independently.
- **The 84 and the reported counts are from official statements on Oct. 18.** Later counts (27 in hospital, 13 critical on Oct. 21) reflect discharges and recovery, not the toll.

## Files
- `figures/`: `fig_rc_toll_by_scenario.png`, `fig_rc_acceptance.png`, `fig_rc_what_had_to_be_true.png`
- `tables/`:
  - `rc_scenario_summary.csv`, `rc_backtest_summary.json`
  - `rc_replicates.csv.gz` (36,000 simulations)
  - `rc_runs_drawn.csv`, `rc_inputs.npz`, `rc_meta.json`
