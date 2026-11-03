# RWI-HC-010 hindcast: what it adds to v6

`RWI-HC-010-rev2-2026-11-02-wainwright-october.pdf` is Roger Wilco Imagery's automated, LLM-assisted hindcast of CFB Wainwright and its training area for Oct. 1 to Nov. 2, 2026 (revision 2, Prime Rogue Inc.). It is kept here unaltered. This note records what it adds to the archive, what we already had, and where it was corrected against our data on Nov. 2, 2026.

## New to the archive (integrate into v6)

- **ADS-B sweep for the whole month.** The adsb.lol archive, within 80 km of 52.80 N, 110.90 W, covering every day from Oct. 1 to Nov. 1. Until now we held only Oct. 17–18 (`data/rubicon-ridge/raw/adsb_night_low/` and part 1 `data/adsb/oct17/`).
  - **Result: nothing relevant.** Every military aircraft within 80 km was at cruise altitude, 24,000–37,000 ft, on the airways that cross the area. These include:
    - USAF C-17s and KC-135s;
    - RCAF CC-144 Challengers on Oct. 19–23, which matches the period of ministerial travel;
    - a CC-130J on Oct. 22 and a CC-330 on Oct. 29–30;
    - a USAF C-32A (callsign AF2) on Oct. 7;
    - a German Air Force Global Express on Oct. 31.
  - No military aircraft is in the archive landing at or flying low over the base. Coverage below about 5,000 ft is thin here, so this does not rule out low flying.
  - **v6 / v6.1 use:** context for the air-movement timeline only.
- **NASA Black Marble night lights at the garrison.** No outage or surge beyond cloud and moonlight effects. This is a null result, recorded so it isn't pulled again.
- **Later "after" scenes not yet in our v6 pulls:**
  - Sentinel-2, Oct. 29;
  - Landsat 8/9, Nov. 1;
  - Sentinel-1, Oct. 31.
  - Add these to the v6 edge and regrowth checks.

## Already in the archive

- **The 14 Oct, 17 Oct and 18 Oct VIIRS detections** are already in the FIRMS pulls: `data/firms/` and `data/firms/history_2012-2026/` in part 1, and `data/rubicon-ridge/raw/firms/` here.
- **Other items already held:**
  - the 12:17 MDT Landsat detection;
  - the CC-130H SAR jump with its transponder off (BRIEF-002);
  - the ~10.7 km² burn;
  - the Sentinel-1 dates (v6 CDSE IDs).

## Corrections to the hindcast

1. **The pre-October scar (lead L2) is dated.** The hindcast calls it undated and unreported because its window starts Oct. 1. Our 2012–2026 FIRMS history (part 1, `data/firms/history_2012-2026/all_detections_merged.csv`) shows VIIRS fires on **Sept. 18 and Sept. 20, 2026**, south and south-west of the lake (about 52.72–52.74 N, 110.88–110.94 W). It also shows fires on **Aug. 27–28** and the **Apr. 20–21, 2026** planned burn in PDA 2.
   - These burns are already excluded from the Oct. 17 outline (`data/rubicon-ridge/satellogic_2026-10-20/ABOUT.md`).
   - The open question for DND is whether those were range fires or planned burns. When the scar formed is no longer in question.
2. **The Oct. 18 detections (lead L1) are at the edge of the Oct. 17 burn, not clearly off-base.** See `oct18_viirs_vs_burn_outline.csv`.
   - Both pixel centres (14:12 and 14:32 MDT) fall **inside** the Oct. 17 outline, in its south-east lobe, but only **32–75 m** from its edge.
   - A VIIRS pixel is about 375 m across, so the heat could be smouldering just inside the edge or burning just outside it.
   - No new scar appears there on Oct. 24, which favours smouldering or mop-up at the edge over a new or escaped fire.
   - The question to the MD of Wainwright and DND stands: was the fire still active on the afternoon of Oct. 18?
3. **"1 km in 30–60 seconds" (section 5b) is repeated from reporting without a check.** That works out to 60–120 km/h, which is a gust-front speed, not a grass-fire spread rate. The v5 modelling has the fire moving about 3 km/h locally at the road head and about 8 km/h at the main head (`data/v6/fire_behaviour_at_overrun/`).
4. **Timing (section 5b).** "At least 3.5 h before the official 'about 4 p.m.'" is true of the 12:17 Landsat detection only. The 14:49 VIIRS detection came about 1 h 10 min before 4 p.m.

## Lessons for the tasking model

- Pull the long-term fire history before calling a scar undated or unreported.
- Test new detections against existing burn outlines, allowing for pixel size, before calling them a new fire.
- Flag reported speeds and figures that are physically implausible.
