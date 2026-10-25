# Image–Shape Correspondence — project notes (read this first, every new pod)

**SINGLE SOURCE (since 2026-10-18): this file lives in the repo at `bsb/workspace_meta/PROJECT_NOTES.md`.**
On the pod, `/workspace/PROJECT_NOTES.md` is only a symlink to it. On the Mac / Run:ai there is no other copy.
Rule: `git pull` before working on any machine, `commit + push` at the end (notes included). Push from a pod needs
`source /workspace/activate_bsb.sh` first (it installs the deploy key the repo's `core.sshCommand` uses).

Tal switches RunPod pods roughly daily; pods are ephemeral (`/root`, OS
packages, GPU drivers/hub caches — all lost on switch). `/workspace` is a
persistent network volume and is the only thing that survives. **This one
file is the entire continuity mechanism** — when Tal says "read the project
notes," read this, summarize status in 3-4 lines, and ask what to continue
with. Keep it lean: state what's true **now**, trim old detail once it's
confirmed rather than keeping it forever.

**2026-08-07: this file replaces three separate docs** (PROJECT_NOTES.md,
FINE_TUNING_PLAN.md, PROGRESS.md) that had grown unwieldy. Archived at
`/workspace/archive/pre-consolidation-2026-08-07/`.

**2026-08-16: second consolidation pass, same reason** — this file had grown
back to ~2800 lines / 200KB (the whole 2026-08-08 through 2026-08-15 history,
in full blow-by-blow detail, most of it fully resolved/superseded by now).
**A complete verbatim copy of the pre-trim file is archived at
`/workspace/archive/pre-consolidation-2026-08-16/PROJECT_NOTES_full_2026-08-16.md`**
— go there for: the full mapping_loss (Phase 2) writeup, the full
relational_loss collapse/fix postmortem, every dated "Status as of ..."
entry from 2026-07-26 through 2026-08-15 (headstock-drift root-causing,
cyc_weight/balance_weight sweeps, bbox_norm/mu_3d_scale sweeps, the
demo/guitar/bsb/ reorg narrative, the old changelog), verbatim measurement
tables, everything. This file below keeps only what's still live: the
current recipe, the last ~2 days of open threads, and durable
reference/setup material that doesn't change session to session.

**2026-08-25: third consolidation pass, same pattern, Tal's explicit call** — the file had grown to
2,393 lines / 251KB, which is **~63k tokens ≈ 31% of a 200k context window** consumed before any work
starts. That context cost, not disk size, is the reason this file gets trimmed. **A complete verbatim
copy of the pre-trim file is archived at
`/workspace/archive/pre-consolidation-2026-08-25/PROJECT_NOTES_full_2026-08-25.md`** (verified
byte-identical at the time of copying). Result: **251KB → 79KB (-68%)**. What was condensed, and where
to look for the full version:
- **The two hard-parked directions, item 2 (AnyUp) and item 4 (GeoAware-SC)** — five full entries,
  ~26% of the old file, describing work that was deliberately stopped. Condensed into ONE section that
  keeps every result number, the park reasoning, the unresolved AnyUp normalization confound, idea (C)
  verbatim, and the live left-right-symmetry thread.
- **Recipe-evolution history, 2026-08-15 → 2026-08-22** — condensed into two dated lineage tables plus
  the durable lessons (the L2-normalize fix, the still-unexplained ZR/ZS puzzle, the axisfix→DFD
  supersession). The DFD phase-1 mechanism section was deliberately KEPT in full: it documents the
  CURRENT recipe, not history.
- **A pure-housekeeping disk-cleanup entry** — dropped entirely.
Nothing live was removed. If a condensed section is ever not enough, the archive has it verbatim.

**2026-09-02: fourth consolidation pass — and the criterion CHANGED.** The first three passes trimmed
for context cost. This one trimmed for **correctness**: the file was carrying reversed conclusions in
confident language, and a pod reading top-to-bottom could act on any of them. Verbatim copy at
`/workspace/archive/pre-consolidation-2026-09-02/PROJECT_NOTES_full_2026-09-02.md` (verified
byte-identical). Result: **309 KB -> 148 KB (-52%)**. Twelve dated status entries (2026-08-24 through
2026-08-31) were condensed or merged. **Every reversed claim now states BOTH what was claimed and what
refuted it**, so nobody re-derives the same mistake: the 2026-08-30 "temperature closed, T=1 wins"
(reversed 09-01), the 2026-08-28 stride-7 promotion (stride 7 lost 09-01), and the 2026-08-29 root
cause for feature-RKD's failure (shown wrong 08-31). Durable material was not touched.

**2026-09-14: sixth consolidation pass, Tal's call** — the file had grown back to **4,977 lines / 405 KB (~100k tokens, half a context window before any work starts)**, larger than at the 09-10 trim. Verbatim copy at
`/workspace/archive/pre-consolidation-2026-09-14/PROJECT_NOTES_full_2026-09-14.md` (verified byte-identical).
Result: **405 KB -> 132 KB (-67%)**. What changed, and the rule used:
- **Everything from 2026-08-31 through 2026-09-10 was condensed to its decisions, its result tables and its durable traps** — seventeen dated entries. The recipe they were arguing about is settled (soft anchor T=0.01 λ=3.5e-7 + cycle v2 T_cyc=0.05 c=1.05e-5 at stride 5 + L_dist γ=1/50 T_dist=1, w_spatial=1), so the narrative of how it was reached is archive material; the numbers that a future pod might quote are not.
- **Kept in full**: 09-11 through 09-14 (the live threads), every durable reference section (the two feature-path bugs, feature-space RKD, geodesic smoothing vs L_dist, the setup/analysis/how-to-work sections), both PROTECTED run flags, and **SHIC's verbatim equations**, which now live in the 09-09 second-thread entry and are the only copy in this file.
- **Nothing was deleted, only moved out of the startup context.** Six archives now exist, one per pass; the 09-14 one is a superset of all earlier live text.

Advisor: Itai Lang. Baseline: BSB (`threedle/bsb`), which we are extending.
Goal (long-term): dense correspondence between an image and a 3D object.

## 2026-10-25 (MAC) — MEETING WITH ITAI + TAL'S DECISIONS. **NOTHING IS RUNNING.**
- **Tal: XSEG is ON HOLD** ("does not deliver yet"; 20-bear result in the entry below). **No email to Itai needed for now** (the REMIND TAL items below are void).
- **Itai (2026-10-25):**
  1. Add VS Code usage to the Run:ai guide (how to work in the workspace from VS Code).
  2. **NEW DIRECTION:** lift the 2D image to 3D with an existing image-to-3D model (TRELLIS 2 from Microsoft, or Pixal / similar), and keep our
     rkd_spatial method with geodesic paths (i.e. the geodesic teacher computed on the lifted 3D shape instead of the 2D image). Not started.
- Obsidian: `Meetings/2026-10-25 Itai.md` (+ link in DISC.md); XSEG note marked hold.

## STATE AT CLOSE — 2026-10-24 (MAC session driving Run:ai `tberger3-disc-gpu2`, RTX A6000) — XSEG ON THE 20-BEAR SUBSET: ALL ARMS ~ EQUAL, THE FEATURE TERM ADDS NOTHING. **NOTHING IS RUNNING; workspace STOPPED.**
- **Result** (soft-snap, 228-normalised, mean over bears, 1 seed; segment map SAM 1; 2 bears have one segment -> perseg only):
  | arm | mean (n=20 / 18) | paired vs twostage | better on |
  |---|---|---|---|
  | ZS | 39.3 | +3.83 (SE 3.21) | 7/20 |
  | twostage (re-run on Run:ai) | 35.5 | -- | -- |
  | perseg | 33.1 | -2.39 (SE 2.32) | 15/20 |
  | nofeat | 33.1 | -2.57 (SE 2.49) | 12/18 |
  | Fonly | 32.9 | -2.74 (SE 2.89) | 12/18 |
  | SHIC (its own eval, argmax) | 33.84 | | |
  **Feature term: Fonly - nofeat = -0.16 (SE 0.87), Fonly better on 8/18 -> nothing**, same as the pod-53 horse ablation, now on 18 bears.
  All three single-stage arms are ~1 SE better than twostage (not significant). twostage 35.5 = the pod value on this subset (ours#1 35.48) -> Run:ai reproduces.
  **EXAMPLE TO KEEP (Tal, 2026-10-25): bear 117682 = why two-stage beats per-segment only** (twostage 18.1, SHIC 17.3 vs perseg/nofeat 40.6, Fonly 47.1;
  4 segments, head split from the body). Row 2 of `demo/shic/xseg_bears_runai_sub20/backproj_compare_bears.png`.
  Big per-bear swings both ways (117682: twostage 18.1 vs 40-47; 14974: twostage 55.0 vs 23-27; 154547: twostage 10.2 vs 20-23).
- Figure (4 picked bears: Fonly best vs twostage 14974, worst 117682, median 11234, largest |Fonly - nofeat| 5459), on the Mac:
  `demo/shic/xseg_bears_runai_sub20/backproj_compare_bears.png` (+ `summary.txt/.json` there). Built by `scripts/make_xseg_bears_figs.sh` (`a2bdb9e`; SHIC panel added 10-25 -- SHIC code/weights + dinov2 hub cache fetched to the PVC, `demo/shic/run/` links recreated).
- On the PVC: runs `data/densepose_lvis/runs_runai_sub20/` (two-stage + kept features/geo tables, ~1.5 GB/bear), `runs_xseg_bears_runai_sub20/`,
  `demo/shic/xseg_bears_runai_sub20/`, logs `/workspace/logs/xseg_bears*.log`, `/workspace/logs/xseg_bears_runai_sub20/`. NOT on the RunPod volume.
- Timing: 167 min for everything (two-stage prep ~2.5 min/bear, the 3 arms ~7 min/bear).
- **NEXT (Tal decides):** feature RKD looks dead on 2 horses + 18 bears; cross-segment teacher options (a) two-stage on VLPart maps, (b) 2D geodesic by
  default + another teacher only where suspect, (c) generic coarse-segment rule. Maybe perseg vs twostage on all 132 bears (the ~2.4 gain is 1 SE here).
  Still: email to Itai (pods 50-53 + this).
- **Obsidian:** DONE on the Mac (XSEG note, "Results 5").

## 2026-10-24 (MAC session, later) — XSEG ON THE 20-BEAR SUBSET, SETUP ON RUN:AI (`tberger3-disc-gpu2`). Results: entry above.
- **New workspace `tberger3-disc-gpu2`** (Tal): image `tberger3/disc:v2`, PVC `tal-disc-data` at `/workspace`, 1 GPU (got an RTX A6000 48 GB), **8 CPU, 32G RAM,
  LARGE SHARED MEMORY ON** (`/dev/shm` 30G). The old `tberger3-disc-gpu` (4 CPU, 16G, /dev/shm 64M) is stopped; only one may hold the RWO PVC.
- **TRAP (why the new workspace): `/dev/shm` 64 MB by default** -> `build_geodesic_tables.py` writes the 2D table into shared memory
  (2048 x 146k px x 4 B = 1.2 GB for bear 113202) -> every Dijkstra worker died with SIGBUS and the parent waited forever (looked like a fork deadlock:
  children in futex_wait, 0 s CPU; found with `python -X faulthandler` + `kill -ABRT`). Two code "fixes" for a fork deadlock were pushed and REVERTED
  (`749046f`, `77e325a`). No ptrace in the workspace (py-spy fails). No CPU quota is enforced (`cfs_quota_us -1`; 64 host cores visible).
- Speed on the A6000 (bear 113202): geo table 13 s (pod 49 s), two-stage phase 2 94 s (pod 238 s); features 92 s (first run 270 s: SD + DINO download).
- **Run:** `scripts/run_xseg_bears.sh` (new, `0b681d6`): prep = two-stage via `run_lvis_sam3_batch.sh --keep_intermediates` (re-run on Run:ai, not reused),
  then per bear perseg / nofeat / balance + Fonly through `run_xseg_horse.sh` (now takes CLASS, RUNS/DEMO/LOGS, amodal domain, NO_FIG=1), then a summary
  (means + paired differences vs twostage, and Fonly - nofeat = the feature term). Segment map SAM 1 (mask cache). One-segment bears: perseg only.
  Log `/workspace/logs/xseg_bears.log`; per bear `/workspace/logs/xseg_bears_runai_sub20/lvis<id>/`; summary `.../summary.txt`. Resumable.
  Inputs fetched from the RunPod volume over S3 (93 files: mask cache for the 20, bear assets, LVIS json, `.cache/dinov2_git`); key deleted after.

## 2026-10-24 (MAC session) — **FIRST DISC RUN ON RUN:AI WORKS END-TO-END** (perseg, horse 56069: mean 17.4 vs 18.0 on pod 50).
- **Result:** `ARM=perseg bash scripts/run_xseg_horse.sh` on the A5000: soft-snap 16.7 / 25.8 / 9.7, mean **17.4** (pod 50: 18.1 / 25.8 / 10.1, 18.0; ZS 10.3 and
  two-stage 39.3 reproduced exactly). Train 300 steps + eval ~3 min, peak GPU mem 2.2 GB. Log `/workspace/logs/runai_first_perseg.log`; figure copied to the Mac
  `demo/shic/runai_first/horse_lvis56069/perseg/lvis56069_perseg_backproj.png`.
- **How data got in (Run:ai cannot receive files from the Mac):** `runai workspace exec -i` fails ("inappropriate ioctl for device") and RunPod S3 has no presigned URLs.
  Working path: S3 key temporarily in `/workspace/.aws/credentials` (600), boto3 in `/workspace/.tools/boto3` (`pip --target`), downloader `/workspace/.tools/s3get.py <paths>`
  (copy in the Mac scratchpad only; paths relative to the volume's `disc/`), run DETACHED (`setsid nohup ... &`) -- a long `exec` gets cut off silently. Key deleted after.
  Getting small files back: `runai workspace exec ... -- base64 -w0 <file> | base64 -d > <file>`.
- Long jobs: always `setsid nohup ... > /workspace/logs/<x>.log 2>&1 < /dev/null &`, then poll with `exec tail`. No `pgrep`/`ps` in the image.
- Workspace: the UI may stay on "Stopping..." after STOP; the CLI (`runai workspace list -p avidan`) is right. `runai workspace resume tberger3-disc-gpu2 -p avidan` starts it
  (image pull ~2 min). Idle-GPU timeout ~1 h stops it automatically.
- (Earlier plan text below kept for the inputs list.)
- Run:ai (set up in another Claude session): VPN on; `runai login`; workspace `tberger3-disc-gpu` (project avidan, image `tberger3/disc:v2`, 1x RTX A5000 24 GB,
  PVC `tal-disc-data` at `/workspace`, RWO = one workspace at a time); `runai workspace exec tberger3-disc-gpu2 -p avidan -- <cmd>`. Repo at `/workspace/disc` (HTTPS + token).
  `env/Dockerfile` = the image `tberger3/disc:v2` (committed 2026-10-24). **STOP the workspace when done** (holds a lab GPU).
- **First run (proposed):** `ARM=perseg bash scripts/run_xseg_horse.sh` (horse 56069, SAM 1 map, 300 steps + eval). Reference pod 50: 18.1 / 25.8 / 10.1, mean 18.0.
- Inputs ~2 GB. On the Mac: `data/densepose_lvis/runs_debug_merge0.015_amodal_fillseg_sam3mask/lvis56069/` (mask, fine_segments, pix_sdsquare_fuse16, 2D geo table + meta,
  gt, png, encoder_loraW_all_r4_phase2/alpha/alpha0.5/pred_f.pth) + `demo/shic/debug_twostage/horse_lvis56069_merge0.015_amodal_fillseg_sam3mask/summary/backproj_lvis56069/lvis56069_position_color.png`.
  **NOT on the Mac (RunPod volume only):** `experiments/shic_horse/encoder_dfd_crossview_phase1/`, `experiments/shic_horse/geodesic_tables/shic_horse_geo_table_3d.pth`,
  `data/densepose_lvis/eval_shic_horse/horse_heat_geodesics_228.npy`, `demo/shic/colored_mesh/horse_mesh_checker16_uv_color.pth`, `demo/shic/shapes/horse.obj`.
- **RUNPOD VOLUME OVER S3, NO POD NEEDED (2026-10-24):** volume `DISC` id `c9sz3m72ye`, EU-RO-1, S3 enabled. Mac: key in `~/.aws/credentials` profile `runpods3`
  (never in the repo), aws CLI in `~/.local/awscli-venv/bin/aws`. Volume root = the pod's `/workspace`. Example:
  `~/.local/awscli-venv/bin/aws --profile runpods3 --region EU-RO-1 --endpoint-url https://s3api-eu-ro-1.runpod.io s3 cp s3://c9sz3m72ye/disc/<path> <path>` (`s3 sync` for dirs).
- **Steps:** (1) DONE 10-24: the 5 missing inputs were downloaded to the Mac over S3.
  (2) VPN on, workspace Running: tar the files from the Mac into `/workspace/disc` via `runai workspace exec` (check that it passes stdin), `git pull`, run.

## STATE AT CLOSE — 2026-10-22 evening (fifty-third pod, RTX 2000 Ada 16 GB) — FEATURE-RKD ABLATION: THE FEATURE TERM ADDS NOTHING. **NOTHING IS RUNNING.**
- **Question (Tal):** does feature RKD help at all? perseg vs XSEG is NOT only "+ feature RKD": perseg = 16 in-seg spatial pairs, XSEG = 8 in-seg spatial + 8 cross-seg -> feature.
  Two new arms (Tal chose both, feature mode Fonly), same recipe and maps as pod 52 (56069 vlpart4, 164135 vlpart8):
  `nofeat` = XSEG split with the feature term OFF (8 in-seg spatial + cycle, `--xseg_feat_weight 0`); `featonly` = Fonly on the cross pairs + cycle,
  `--rkd_spatial_dist_weight 0` (Fonly weights from pod 52's balance: 56069 6.0896e-03, 164135 2.0469e-03).
  | arm | 56069 mean | 164135 mean | 164135 leg x- / x+ / mixed (correct = x-) |
  |---|---|---|---|
  | ZS | 10.3 | 13.3 | 37 / 63 / 61 |
  | two-stage | 39.3 | 6.4 | 100 / 0 / 2 |
  | perseg (16 in) | 11.5 | 2.9 | 24 / 76 / 46 |
  | **nofeat** (8 in, no feature) | **10.6** | **2.9** | 28 / 72 / 55 |
  | Fonly (8 in + feature) | 12.0 | 2.9 | 46 / 54 / 45 |
  | featonly (feature only) | 26.1 (pt2 66.9) | 11.6 | 11 / 89 / 22 |
  - nofeat == Fonly within noise on both horses -> **the feature term adds nothing measurable**; only a small leg-mass shift (28 -> 46% x-), leg still not separated.
  - featonly breaks the map (as the 09-04 spatial-off run did). The work is done by the in-segment spatial term; only two-stage (2D geodesic ACROSS segments) fixes the leg.
  - 1 instance each, 1 seed, noise ~2. **Tal reviews the figures tomorrow.**
- **Code:** `scripts/run_xseg_horse.sh` new `ARM=nofeat` / `ARM=featonly WEIGHT=<w>`; `analysis/diag_seg_mapping.py` falls back to the photo next to the mask when the map
  is not `<tag>_fine_segments.pth` (VLPart maps). Queue `/workspace/logs/xseg_ablation/queue.sh` (has the 164135 env + TWOSTAGE path).
  **Leg metric TRAP:** `diag_seg_mapping.py` takes the map from `--run_dirs[0]`'s config -> put the two-stage run FIRST to get seg 3 = the old-map front leg (1654 px, comparable with pod 52); an xseg run first gives vlpart8 seg 3 (another region).
- Figures: `demo/shic/xseg_vlpart4/horse_lvis56069/featablation_backproj_lvis56069.png`, `demo/shic/xseg_164135_vlpart8/horse_lvis164135/featablation_backproj_lvis164135.png`,
  `demo/shic/xseg_164135_vlpart8/horse_lvis164135/leg_seg3/seg3_featablation_cols234.png` (+ .json). Runs `data/densepose_lvis/runs_xseg_{vlpart4,164135_vlpart8}/<tag>/{nofeat,featonly}/`, logs `/workspace/logs/xseg_{vlpart4,164135_vlpart8}/{nofeat,featonly}.log`.
- **Volume check (pod-52 request):** with the local env copy (`/root/disc_env`, unpack ~1-2 min at start) an arm takes ~5 min train + eval vs ~15 min on pod 52 -- the local env works; the raw volume speed was not measured.
- **REMIND TAL (Mac):** the email to Itai summarising pods 50-52 (+ this ablation) -- still open 10-24.
- **NEXT:** Tal reviews the ablation; if feature RKD is dropped, the open direction is the cross-segment teacher: (a) two-stage on the VLPart map of 164135,
  (b) 2D geodesic by default, another teacher only where it is suspect, (c) a generic coarse-segment rule. Still open: 2nd seed, bear 159218.
- **Obsidian:** DONE (Mac, 2026-10-23): merged into `2026-10-19 XSEG cross-segment feature RKD.md` as "Results 4" (+ Next), 3 figures in `Experiments/attachments/`; inbox emptied. SYNC TO MAC: all copied (the rest on 10-24 over S3).
- SYNC TO MAC: demo/shic/xseg_vlpart4/horse_lvis56069/featablation_backproj_lvis56069.png demo/shic/xseg_164135_vlpart8/horse_lvis164135/featablation_backproj_lvis164135.png demo/shic/xseg_164135_vlpart8/horse_lvis164135/leg_seg3/seg3_featablation_cols234.png demo/shic/xseg_164135_vlpart8/horse_lvis164135/leg_seg3/seg3_featablation_cols234.json demo/shic/xseg_vlpart4/horse_lvis56069/nofeat demo/shic/xseg_vlpart4/horse_lvis56069/featonly demo/shic/xseg_164135_vlpart8/horse_lvis164135/nofeat demo/shic/xseg_164135_vlpart8/horse_lvis164135/featonly

## STATE AT CLOSE — 2026-10-22 (fifty-second pod, RTX 4000 Ada 20 GB) — XSEG ON A 4-SEG MAP + NEW `full` ARM; XSEG ON HORSE 164135 (LEG COLLISION) DOES NOT SEPARATE THE LEGS. **NOTHING IS RUNNING.**
- **New arm `full`** (`--xseg_feat_mode full`, Tal): cross-segment feature RKD with NOTHING detached (V and w live; may form a cycle, accepted).
  `balance` now also reports its weight; `ARM=all` runs perseg, balance, table, wonly, Fonly, full.
- **Horse 56069, VLPart partimagenet>=0.3 map (4 segs 48/27/24/2; "head" still includes neck + upper chest)**, SEGTAG=vlpart4:
  | arm | pt1 | pt2 | pt3 nose | mean | mean, 5-seg map (10-21) |
  |---|---|---|---|---|---|
  | ZS | 6.3 | 24.6 | 0.0 | 10.3 | 10.3 |
  | perseg | 6.0 | 21.5 | 6.8 | 11.5 | 10.6 |
  | table | 5.3 | 23.6 | 3.7 | 10.9 | 11.9 |
  | wonly | 13.3 | 29.2 | 7.3 | 16.6 | 16.6 |
  | Fonly | 7.5 | 23.6 | 4.8 | 12.0 | 9.6 |
  | full | 6.0 | 21.5 | 5.1 | 10.9 | |
  No arm under ZS; all within ~2 noise. One-row figure (mesh key, photo, seg map, SHIC, old two-stage, 5 arms): `demo/shic/xseg_vlpart4/horse_lvis56069/backproj_all_arms_lvis56069.png`;
  v2 SUMMARYs `demo/shic/xseg_vlpart4/horse_lvis56069/<arm>/summary/SUMMARY_lvis56069.png`.
- **Horse 164135 (Leg Collision, seg 3 = front leg, correct = x-)**, inputs = the 09-28 ones (`data/densepose_lvis/runs/lvis164135/`), compared with the 09-28 two-stage sw150 run.
  Two maps: old SAM 1 map (SEGTAG=164135_sam1) and VLPart partimagenet>=0.3 (8 segs, every leg its own segment; SEGTAG=164135_vlpart8, own 2D geo table, see below).
  | arm | mean, old map | mean, VLPart | leg (VLPart) x- / x+ / mixed |
  |---|---|---|---|
  | ZS | 13.3 | 13.3 | 37 / 63 / 61 |
  | two-stage (09-28) | 6.4 | 6.4 | **100 / 0 / 2** |
  | perseg | 6.3 | **2.9** | 24 / 76 / 46 |
  | table | 9.2 | 5.9 | 27 / 73 / 66 |
  | wonly | 10.7 | 19.5 | 29 / 71 / 42 |
  | Fonly | 6.5 | **2.9** | 46 / 54 / 45 |
  | full | 6.5 | **2.9** | 44 / 56 / 50 |
  Old map leg: perseg 45/55/28, table 1/99/24 (consistent but WRONG leg), wonly 35/58/34, Fonly 37/63/23, full 34/66/26.
  - **Tal's reading: XSEG does not learn cross-segment relations** -- cross pairs follow FEATURES, not paths, and the two legs look alike in features,
    so the feature teacher pulls them together. The 2D geodesic is the wrong teacher on 56069 (nose/belly touch in the photo) and the RIGHT one on 164135.
    **Of the XSEG arms, Fonly and full are the most reasonable (Tal).** He wants to see everything summarised before deciding the direction.
  - VLPart map halves the 3-point error but does not fix the leg; the 3 GT points do not see the leg, so the two metrics disagree.
  - Ablation figure Tal asked for (rows ZS / two-stage / per-seg only [= mu_aniso_perseg, same recipe without stage A] / XSEG Fonly old map, cols 2-4):
    `demo/shic/lvis164135_mu/figures/leg_collision_compare/seg3_ZS_twostage_perseg_xsegFonly_cols234.png` (+ 3-row version without Fonly).
  - The end-of-stage-A analysis already existed (09-29): `demo/shic/lvis164135_mu/figures/manual_ellipses_B/seg3_mapping_step150_alpha0.5.png`.
  - Figures: back-proj both maps `demo/shic/xseg_164135_vlpart8/backproj_compare_lvis164135.png` (script next to it, `make_backproj_compare.py`, in demo/ = not in git);
    leg per map `demo/shic/xseg_164135_{sam1,vlpart8}/horse_lvis164135/leg_seg3/`; partimagenet threshold options
    `demo/shic/fine_segments_vlpart/horse_lvis164135/options/options_partimagenet_thr{,_high}_lvis164135.png` (0.3 / 0.38 = 8 segs, 0.4-0.46 = 6, 0.48 = 5, >=0.49 body drops -> 2).
- **Code (commit below):**
  - `scripts/run_xseg_horse.sh`: other instance via `TAG= SRC= TWOSTAGE= POSCOL= GEO2D=`; the 4 analysis scripts run in ONE python process
    (`analysis/run_in_one_process.py`, verified identical eval); each arm's analysis runs in the background while the next arm trains.
    Reproduce 164135 VLPart: `GEO2D=data/densepose_lvis/fine_segments_vlpart/geo_lvis164135_vlpart8/lvis164135_mask_geo_table_2d_seed0.pth TAG=lvis164135
    SEGTAG=164135_vlpart8 FINESEG=data/densepose_lvis/fine_segments_vlpart/lvis164135_fine_segments_partimagenet_thr0.3.pth SRC=data/densepose_lvis/runs/lvis164135
    TWOSTAGE=<09-28 sw150 run>/alpha/alpha0.5/pred_f.pth POSCOL=demo/shic/lvis164135_mu/ZS_phase1/backproj_lvis164135/lvis164135_position_color.png ARM=all bash scripts/run_xseg_horse.sh`.
  - **TRAP: a new segment map needs its own 2D geo table** -- centres are sampled from LABELLED pixels, so a map with different holes (fillseg vs the old map)
    fails the "stored centers do not match" check. Build: `analysis/build_geodesic_tables.py --skip_3d --fine_seg_path <map> --num_center_pixels 2048 --seed 0 --true_diameter --out_dir <dir>`.
  - `analysis/diag_seg_mapping.py --cols 2 3 4` (keep only some columns); `analysis/fine_segments_check/vlpart_label_maps.py --options vocab:thr,... --mask_suffix --out_name`.
  - **SLOW VOLUME / LOCAL ENV:** on this pod every small file on /workspace cost ~30 ms -> `import torch` ~60 s, arms ~15 min instead of ~9.
    Fix: env packed ONCE with conda-pack to `/workspace/env_packs/disc.tar` (11 GB; packing took 36 min); `env/pod_local_env.sh` unpacks it to
    `/root/disc_env` (**118 s** on this pod) and `env/activate.sh` uses it once `READY` exists (imports then take seconds). `/start-work` starts it in the background.
    **Rebuild the tar after installing anything into the env** (command in the script header). Tal: check on the next pod whether the volume is still slow.
  - `/start-work` skill: activate BEFORE `git pull` (the deploy key is installed by the activation).
- Runs `data/densepose_lvis/runs_xseg_{vlpart4,164135_sam1,164135_vlpart8}/`, logs `/workspace/logs/xseg_{vlpart4,164135_sam1,164135_vlpart8}/`.
- **REMIND TAL (Mac, 2026-10-22):** draft a simple email to Itai summarising pods 50-52 (XSEG + VLPart + leg collision). Pod 52 closed.
- **NEXT:** Tal summarises everything and decides. Options raised: (a) two-stage (global stage A) on the VLPart map of 164135 -- does it keep 2.9 AND fix the leg;
  (b) cross-segment pairs keep the 2D geodesic by default and switch to the feature teacher only where the geodesic is suspect (parts touching in the
  photo but far apart in features, e.g. nose/belly); (c) a generic coarse-segment rule for any object (Tal: must work for non-animals too; idea: merge by
  area threshold ~8-10%, or a generic custom VLPart vocabulary). Still open from 10-21: 2nd seed, `|gap|` in the logs, bear 159218.
- **Obsidian:** DONE (Mac, 2026-10-22): the inbox note was merged into `2026-10-19 XSEG cross-segment feature RKD.md` as "Results 3" (+ Next updated), 4 figures in `Experiments/attachments/`; inbox emptied. SYNC TO MAC paths copied.
- SYNC TO MAC: demo/shic/xseg_vlpart4/horse_lvis56069/backproj_all_arms_lvis56069.png demo/shic/xseg_164135_vlpart8/backproj_compare_lvis164135.png demo/shic/lvis164135_mu/figures/leg_collision_compare/seg3_ZS_twostage_perseg_xsegFonly_cols234.png demo/shic/lvis164135_mu/figures/leg_collision_compare/seg3_ZS_twostage_perseg_cols234.png demo/shic/xseg_164135_vlpart8/horse_lvis164135/leg_seg3 demo/shic/xseg_164135_sam1/horse_lvis164135/leg_seg3 demo/shic/fine_segments_vlpart/horse_lvis164135/options data/densepose_lvis/fine_segments_vlpart/lvis164135_fine_segments_partimagenet_thr0.3.pth data/densepose_lvis/fine_segments_vlpart/lvis56069_fine_segments_partimagenet_thr0.3.pth

## STATE AT CLOSE — 2026-10-21 (fifty-first pod, RTX 2000 Ada) — VLPART PART MAP SPLITS HEAD FROM CHEST; ALL 4 XSEG ARMS RE-RUN ON IT. **NOTHING IS RUNNING.**
- **Semantic-SAM dropped before install:** its README says "The currently released checkpoints are only trained with SA-1B data" (SwinT + SwinL)
  -> no part training in any public weights, same data as SAM. Clone left at `$DISC_WS/semantic_sam_repo` (no env). The 10-21 Mac entry's
  "trained on SA-1B + part datasets" is true of the PAPER only.
- **VLPart** (github.com/facebookresearch/VLPart, Tal chose it over PartGLEE, which has no demo code released): clone `$DISC_WS/vlpart_repo`,
  env `vlpart` (py 3.10, torch 2.4.1 cu124, detectron2 from source at `$DISC_WS/detectron2_src`, sm_89; conda needs `-c conda-forge --override-channels`,
  ToS), checkpoint `models/swinbase_cascade_lvis_paco_pascalpart_partimagenet_inparsed.pth`. Install script `$DISC_WS/logs/vlpart/install.sh`.
  - **Labelled parts, not class-agnostic:** fixed vocabulary. The masks are the SAME in both vocabularies, only the names change.
    partimagenet: head 46% / body 50% + 24% / feet. pascal_part: + ears, eyes, muzzle 23%, neck 18% (box-shaped, unreliable at score 0.49).
  - **Head separates from chest** (first model that does). Map options (merge 1.5% + fillseg, `analysis/fine_segments_check/vlpart_label_maps.py`):
    SAM 1 68/29/2/2; partimagenet>=0.3 48/27/24/2; **pascal_part>=0.5 52 body / 23 muzzle / 21 head / 2 / 2 ears (Tal chose this one)**; pascal_part>=0.3 + neck.
  - Per-part dump: `external/vlpart/dump_instances.py` (run inside `$DISC_WS/vlpart_repo`, env vlpart). Map file:
    `data/densepose_lvis/fine_segments_vlpart/lvis56069_fine_segments_pascalpart_thr0.5.pth` (int32 [400,271], same format as `_fine_segments.pth`).
- **XSEG re-run on the VLPart 5-seg map** (all else as 10-20; balance re-run: table 4.1373e-02 / wonly 4.5029e-02 / Fonly 6.7690e-03; XSEG check 1/0):
  | arm | pt1 | pt2 | pt3 nose | mean | mean, SAM 1 map (10-20) |
  |---|---|---|---|---|---|
  | ZS | 6.3 | 24.6 | 0.0 | 10.3 | |
  | perseg (exp 0) | 12.8 | 15.8 | 3.3 | 10.6 | 18.0 |
  | table | 11.8 | 21.5 | 2.3 | 11.9 | 12.6 |
  | wonly | 9.7 | 20.1 | 19.9 | 16.6 | 23.1 |
  | **Fonly** | 11.0 | **14.6** | 3.2 | **9.6** | 24.3 |
  | SHIC | 2.3 | 18.3 | 0.0 | 6.9 | |
  - Better map -> every arm improves. Fonly is the first arm under ZS (9.6 vs 10.3), within cross-pod noise (~2). pt1 worse than ZS in every arm.
    1 instance, 1 seed. **Tal has not reviewed the figures yet** ("looks interesting").
  - `scripts/run_xseg_horse.sh`: new `FINESEG=<map .pth> SEGTAG=<name>` (-> `runs_xseg_<name>/`, `demo/shic/xseg_<name>/`, `logs/xseg_<name>/`)
    and `ARM=balance_table`. Reproduce: `FINESEG=<above> SEGTAG=vlpart5 ARM=all bash scripts/run_xseg_horse.sh`.
  - Figures (v2 SUMMARY): `demo/shic/xseg_vlpart5/horse_lvis56069/<arm>/summary/SUMMARY_lvis56069.png`; map options
    `demo/shic/fine_segments_vlpart/horse_lvis56069/options/options_lvis56069.png`; runs `data/densepose_lvis/runs_xseg_vlpart5/`; logs `$DISC_WS/logs/xseg_vlpart5/`.
- **NEXT:** Tal reviews the 4 figures + decides; if VLPart stays: wire it into `build_fine_segments.py` as an option; 2nd example (bear 159218) to see
  if the gain holds; a 2nd seed for Fonly vs ZS; read `|gap|` in the logs (still open from 10-20).
- `/end-work` was not listed in this session because Claude was started from `/root`, not `/workspace` (the skills link exists now).
- **Obsidian:** DONE (Mac, 2026-10-21): the inbox note was merged into the two existing vault notes (`2026-10-21 Fine segments.md`: Semantic-SAM
  + VLPart sections; `2026-10-19 XSEG cross-segment feature RKD.md`: "Results 2" on the VLPart map), figures in `Experiments/attachments/`; inbox emptied.

## 2026-10-21 (MAC session, CPU only) — FINE SEGMENTS: SAM 1 / SAM 3 / UnSAMv2 CANNOT SPLIT HEAD FROM CHEST. **NEXT = SEMANTIC-SAM ON A GPU POD.** (Superseded 10-21 pod: Semantic-SAM's public weights are SA-1B only; VLPart used instead, entry above.)
**Why:** XSEG (10-20) found the training map of horse 56069 has 4 segments, one = 68% of the horse joining the head with the chest + left
body, so nose->chest pairs count as in-segment. Obsidian note (Hebrew, figures): `~/Documents/DISC/Experiments/2026-10-21 Fine segments.md`.
Scripts: `analysis/fine_segments_check/` (README there). Figures on the Mac only: `demo/shic/fine_segments_sweep/horse_lvis56069/`.
- **SAM 1 (`build_fine_segments.py`, vit_h AMG, our defaults copied from BSB's `encoder.py:97`, pred_iou 0.90 / stability 0.92 / box NMS 0.7):**
  - The Mac reproduces the pod's map exactly at 0.90 + merge 1.5% + fillseg (4 segs 67.7 / 28.6 / 2.1 / 1.6) -> CPU == GPU here.
  - **The 65.6% head + chest + left-body segment is ALREADY in SAM's raw map** -- not made by our 1.5% merge (the merge only eats eye / mane / strap).
  - pred_iou 0.90 / 0.88 / 0.85 / 0.80: 56 -> 68 masks, 15 -> 17 raw segments, largest stays 65.6%. box_nms 0.7/0.85/0.95 x stability 0.92/0.85:
    largest 65.2-65.6% in all 6. Single point prompts (multimask): the FINEST mask from the nose / forehead / between the eyes is already
    head + chest + left body (63-71%); a head-only mask does not exist for SAM 1. Right body separates (28%).
  - NOTE: `--crop_n_points_downscale_factor 2` does nothing (crop_n_layers is 0 and not exposed).
- **SAM 3 automatic:** Meta ships NO automatic mode (facebookresearch/sam3 issues #435, #371, #226, no maintainer answer). Hugging Face
  `transformers` 5.14.0 has `pipeline("mask-generation", model="facebook/sam3")` (point grid on SAM 3's SAM-2-style tracker head). Run on
  the Mac in a NEW env `sam3hf` (py 3.12, torch 2.8.0, transformers 5.14.0, conda-forge; `disc` untouched; HF login done on the Mac):
  default -> ONE mask (whole horse); pred_iou 0.5-0.3 / stability 0.8-0.7 / NMS 0.9 -> largest 93.7-94.4%, only ears / eye / strap added.
  `crops_n_layers=1` CRASHES inside transformers (torch.stack of different crop sizes) -- library bug, not patched. **Worse than SAM 1 here.**
  Paper: SAM 3's 1-click interactive mIoU 66.1 vs SAM 2.1 66.4 -> no reason to expect better parts; its novelty is TEXT concepts (not generic).
- **UnSAMv2** (SAM 2.1-based, continuous granularity, Apache 2.0): Tal tried the HF Space demo (whole image + interactive), no granularity
  splits the horse. **Roboflow** = a platform (hosts SAM / YOLO, labeling, training), not a part model -> no.
- **Conclusion:** the SAM family separates by colour / boundaries; a frontal horse's head and chest are the same colour -> no split.
  PartGLEE's paper says the same ("SAM ... predominantly relies on colors or boundaries ... especially for animals"). Need a model trained on PARTS.
- **NEXT (Tal, GPU pod): Semantic-SAM** (github.com/UX-Decoder/Semantic-SAM, ECCV 2024; trained on SA-1B + part datasets incl.
  PartImageNet = quadruped head / body / foot / tail; automatic generator with 6 granularity levels, class-agnostic output). Its web demos
  (semantic-sam.xyzou.net:6098 / :6080) were DOWN on 10-21. Needs detectron2 + a custom CUDA op (deformable attention) -> pod only.
  - Install in its OWN clone + env at `$DISC_WS/semantic_sam_repo` (do not touch `disc` / the sam3 env); follow its README / INSTALL for the
    exact versions and checkpoint -- not verified from the Mac. Our wrapper scripts go to `external/semantic_sam/` (git source of truth).
  - Run its automatic mask generator on `data/densepose_lvis/runs_debug_merge0.015_amodal_fillseg_sam3mask/lvis56069/lvis56069.png`, EVERY
    granularity level separately; turn each into a label map with `build_fine_segments.py::build_label_map` (min_pixels 50; template:
    `analysis/fine_segments_check/sam3_hf_auto.py`), raw and with merge 1.5% + fillseg. Report per level: #segments, largest %, and
    **does the head separate from the chest?** Figure: one panel per level, same overlay as the SAM 1 sweep; show it to Tal.
  - Then Obsidian inbox note (short bullets + the figures, see the rule below). If a level works: wire it into `build_fine_segments.py`
    as an option and re-run XSEG `table` on the new map (Tal decides).
- **NEW: `/start-work` and `/end-work` skills** in the repo (see "How Tal wants the assistant to work"). On the next pod: after the first
  `git pull`, create the `/workspace/.claude/skills` link (one-time; the skill does it) so they are available when Claude starts in `/workspace`.
- Mac state: SAM 1 vit_h checkpoint at `SAM_repo/model_checkpoints/` (gitignored); env `sam3hf`; git push from the Mac works over SSH.
  **TAU VPN on = RunPod SSH times out** (10-20): turn the VPN off for RunPod, on for Run:ai.

## STATE AT POD CLOSE — 2026-10-20 (fiftieth pod, RTX 2000 Ada) — XSEG RUN, ALL 4 ARMS DONE. **NOTHING IS RUNNING.** Tal reviews the results.
- **Ran the 10-19 plan as written** (`a566d3b`). Smoke test (`ARM=balance`) passed: `XSEG check` in-slice 1.0000 / cross-slice 0.0000; three
  `XSEG_WEIGHT` lines, table 1.0890e-01 / wonly 4.0686e-02 / Fonly 7.0602e-03 (re-run inside the queue: identical to the last digit = deterministic).
  Then `ARM=all` detached, **RATIO=1** (= the equal-grad weights above; `RATIO=3` in the 10-19 entry is only an option, not used). ~35 min total.
- **RESULTS** (soft-snap geodesic error, 228-normalized, lower = better; pt 3 = nose; 3 GT pts, 1 instance, 1 seed, cross-pod noise ~2):
  | arm | pt1 | pt2 | pt3 nose | mean |
  |---|---|---|---|---|
  | ZS | 6.3 | 24.6 | 0.0 | 10.3 |
  | two-stage (10-13 baseline) | 7.4 | 15.3 | 95.1 | 39.3 |
  | perseg (exp 0) | 18.1 | 25.8 | 10.1 | 18.0 |
  | **table** (exp 1, main) | **4.1** | 27.7 | **6.0** | **12.6** |
  | wonly | 26.2 | 22.3 | 20.9 | 23.1 |
  | Fonly | 28.6 | 23.5 | 20.6 | 24.3 |
  | SHIC | 2.3 | 18.3 | 0.0 | 6.9 |
  - Exp 0: no cross-segment pairs -> the nose no longer collapses (95.1 -> 10.1), but pt1/pt2 get worse (no constraint between parts).
  - Exp 1: `table` keeps the nose AND recovers pt1 = best of our arms, still behind ZS (10.3) and SHIC on mean; pt2 is missed by every
    method toward the shoulder (vertices ~2748). The two circular arms (wonly/Fonly) are worse than perseg. **Tal has not reviewed yet.**
  - Not yet read: `|gap|` / teacher-student in the step logs (did the feature term move?).
- **Figures** (v2 SUMMARY layout, SHIC half reused byte-identical from the old summary): `demo/shic/xseg/horse_lvis56069/<arm>/summary/SUMMARY_lvis56069.png`
  for perseg/table/wonly/Fonly; old baseline `demo/shic/debug_twostage/horse_lvis56069_merge0.015_amodal_fillseg_sam3mask/summary/SUMMARY_lvis56069.png`.
  Built with `ANN_ID=56069 CLASS=horse RUNS=data/densepose_lvis/runs_debug_merge0.015_amodal_fillseg_sam3mask PRED_F=<run>/alpha/alpha0.5/pred_f.pth
  BASE=<demo>/<arm>/summary SHIC_BASE=<old summary dir> bash scripts/make_lvis_arm_summary.sh`. Runs `data/densepose_lvis/runs_xseg/lvis56069/<arm>/`, logs `/workspace/logs/xseg/`.
- **SEGMENTATION IS THE NEXT PROBLEM (Tal):** the training map (`<SRC>/lvis56069_fine_segments.png`) has 4 segments; seg 1 = 68% of the horse
  and joins the head with the front body -> nose->chest pairs count as in-segment. "Still not what we wanted."
  - Fine segments come from **SAM 1** (vit_h `SamAutomaticMaskGenerator`, `analysis/build_fine_segments.py`) + merge 1.5% + fillseg; SAM 3 only makes the object mask.
  - **Tal prefers SAM 3 for the parts too** (newer, already in use). SAM 3 has NO built-in automatic "segment everything" mode; it takes points/box
    (SAM 1/2-style) or text. Proposed (not built, not decided): a point-grid wrapper on SAM 3 (generic, = what SAM 1 does today). Text prompts per part
    ("horse head") conflict with the stay-generic rule. Also cheap to check first: the map BEFORE the 1.5% merge.
- **NEXT:** Tal reviews the 4 SUMMARY figures + decides; segmentation (SAM 3 grid wrapper?); bear 159218 as 2nd example; read `|gap|` in the logs.
- **Obsidian:** DONE (Mac, 2026-10-20): moved to `~/Documents/DISC/Experiments/2026-10-19 XSEG cross-segment feature RKD.md` (Hebrew, vault format), inbox emptied.
- New working rule (images via `SendUserFile`) added to "How Tal wants the assistant to work".

## 2026-10-19 (MAC session, CPU only) — XSEG EXPERIMENT PLANNED + IMPLEMENTED. **RAN 2026-10-20, results in the entry above.**
**Other news:** Tal's TAU VPN works (Run:ai reachable); Docker / Run:ai setup continues AFTER this experiment. Tal's Obsidian vault is on the
Mac at `~/Documents/DISC` (the Mac's Claude writes it directly); meeting with Itai 2026-10-18 recorded there (`Meetings/2026-10-18 Itai.md`):
RunPod guide screenshots; revisit feature RKD (Itai: "the features are unstable"); bilateral-style split, no hard threshold.
- **Problem (Tal):** for CROSS-SEGMENT pairs the 2D geodesic is an inaccurate teacher where parts are crowded in the photo -- horse 56069:
  nose -> belly is short in the image, long on the mesh. The nose (GT pt 3, ZS 0.0) collapses in STAGE 1 (95.1), the only stage that has
  cross-segment pairs (stage 1 = global ellipse, 8 in + 8 out; stage 2 = segment ellipses, 16 in + 0 out).
- **The fix tried (Tal's design, agreed point by point):** ONE stage, 300 steps, no stage 2, 8 in + 8 out neighbours per centre.
  In-segment pair -> `rkd_spatial_dist` (the ORIGINAL 2D geodesic, no feature-geodesic metric), with ITS SEGMENT's ellipse.
  Cross-segment pair -> feature RKD INSTEAD (no spatial term, no mu -- so no global ellipse anywhere). HARD split by segment for now:
  the soft bilateral weight (`alpha_ij = exp(-(1-cos(f_i,f_j))/sigma)`) was proposed and PARKED by Tal ("too complicated for now").
  Both terms calibrated to equal gradient norms first (Tal: "similar proportion").
- **Feature term, three arms** (teacher always `cos(f_i, f_j)` of the FROZEN photo features; student `s_i = sum_a w_ia V[v_a]`):
  | arm (`--xseg_feat_mode`) | student | gradient path | why |
  |---|---|---|---|
  | `table` (main) | `<s_i, s_j>` with V = FROZEN phase-1 vertex features (unit) = `sum_a sum_b w_ia w_jb C[v_a,v_b]` | match `w` only | no circularity: a fixed table, exactly like D3D in rkd_spatial_dist |
  | `wonly` | `cos(s_i, s_j)`, V = live F detached | match `w` only | as `table` but the values drift (= the old "gradW") |
  | `Fonly` | `cos(s_i, s_j)`, V = live F, w detached | F only | the circular path alone (= the old "gradF") |
  No `xseg_spatial` control (cross pairs on spatial + global mu): Tal declined it -- "we already know spatial + global is the problem".
- **EXP 0 first (Tal):** per-segment only (`--mu_scope segment_aniso`, 16 in + 0 out, no stage 1) on the current recipe -- does the nose still
  collapse without any cross-segment pair? Never run on this horse with the current recipe (only on the guitar: per-seg-only beat
  two-stage by ~3). Known: no cross pairs -> left/right is NOT tested by exp 0 (horse 56069 has little left/right confusion); exp 1 tests it.
- **CODE (Mac, 2026-10-19; CPU unit test only, the training loop has NOT run yet):**
  `modules/feature_rkd_loss.py::xseg_feat_loss` (tested: `table` == the explicit `sum w w C`; gradient reaches F only via w for
  table / wonly, only directly for Fonly). `phase2/train_relational_loss.py`: `--xseg_feat_mode {off,table,wonly,Fonly}`,
  `--xseg_feat_weight`, `--xseg_feat_balance [--xseg_feat_balance_step 25]` (grad norms of all three modes vs the in-seg spatial term,
  prints `XSEG_WEIGHT mode=.. weight_equal=..`, stops). The split is by POSITION on the neighbour axis (cat([in, out])); step 1 prints
  `XSEG check` = in-slice same-segment fraction (must be 1) and cross-slice (must be 0). `off` (default) = bit-identical to before.
  Needs `--mu_mode learned --mu_scope segment_aniso` (the segment_aniso out>0 guard is relaxed only under xseg).
- **RUN (GPU pod):** `git pull && source env/activate.sh`, then `ARM=all bash scripts/run_xseg_horse.sh` (detached + watcher, per the rules
  below) = perseg -> balance -> table / wonly / Fonly at the equal-grad weights (`RATIO=3` = 1/3). Single arms: `ARM=perseg|balance`,
  `ARM=table WEIGHT=<w>`. Inputs = the 10-13 two-stage run's dir `data/densepose_lvis/runs_debug_merge0.015_amodal_fillseg_sam3mask/lvis56069`
  (SAM 3 mask, merge 1.5%, fillseg, no amodal: mask in one piece); same recipe otherwise (LoRA-W all r4 lr 1e-3 read at alpha 0.5, cycle v2
  c=1.676e-5 T_cyc=0.05 stride 3, T=0.01, mu lr 5e-2; NOTE the LVIS recipe has NO anchor and NO L_dist). Out: `data/densepose_lvis/runs_xseg/lvis56069/<arm>/`,
  `demo/shic/xseg/horse_lvis56069/<arm>/` (eval_arms.json with zs / twostage / arm, soft-snap back-projection), logs `$DISC_WS/logs/xseg/`.
  **First run = smoke test:** check the `XSEG check` line and that balance prints three `XSEG_WEIGHT` lines before trusting the queue.
- **Baseline to beat** (that run's `eval_arms.json`, soft-snap per point pt1 / pt2 / pt3 = nose, mean): ZS 6.3 / 24.6 / 0.0 (10.3);
  two-stage end of stage 1 9.4 / 15.3 / 95.1 (39.9); two-stage final 7.4 / 15.3 / 95.1 (39.3). 3 GT points, 1 instance, 1 seed.
- **Read the results on:** nose (pt 3) soft-snap vs ZS 0.0 / two-stage 95.1; the back-projection (left/right on the legs);
  `|gap|` and teacher/student in the step log (did the feature term actually move?). Then Tal decides.
- **Open:** the bilateral soft weight (parked); bear 159218 as the second example; the amodal-pixel fix stays required before any occluded
  `--feature_geodesic` run (REMIND TAL) -- not relevant to xseg, which uses the original 2D geodesic.

## STATE AT POD CLOSE — 2026-10-18 (forty-ninth pod, CPU only) — CLEANUP + MULTI-MACHINE SETUP. **NOTHING IS RUNNING, NOTHING WAS TRAINED.** Tal closes the pod.
**NEXT SESSION = ON THE MAC (Tal, 10-18):** `cd ~/Projects/disc && git pull && source env/activate.sh`, then read this file.
- **Open, in order:** (1) Tal finishes the TAU VPN (in progress) -> `runai workspace bash tberger3-dev` check (python, `df -h /workspace`, write test);
  (2) Dockerfile for Run:ai from `env/requirements_disc_gpu.txt` (+ external/ scripts; SAM 3 / pix2gestalt envs later), built on the Mac with Docker Desktop
  `--platform linux/amd64`, pushed as `tberger3/disc` (the `:v1` image was only a smoke test, not the project env); (3) research resumes from the pod-48
  NEXT POD list (path definition by segments / 3D distance / literature; REMIND TAL about the amodal-pixel fix before any occluded `--feature_geodesic` run).
- **On a new GPU pod:** `source /workspace/activate_bsb.sh` still works (it sources `/workspace/disc/env/activate.sh`); `cd /workspace/disc && git pull` first.
- **Research paused** on the feature-geodesic thread (pod 48 NEXT POD list still stands).
- **Disk freed ~69 GB** (Tal ran the delete himself; the auto-mode classifier blocked `rm -rf` this pod even with Tal's OK):
  324 intermediate `encoder_checkpoint_step*.pth` (KEPT: every final `encoder_checkpoint.pth`, every `*_stageA_end.pth`, and
  `encoder_checkpoint_step150.pth` = end of stage 1 in every run with `mu_switch_step=150` -- Tal: stage-1 weights must stay),
  the 4 pod-47 `runs_debug_..._featgeo_*` dirs, `/workspace/.cache/pip`. List: `/workspace/logs/cleanup_2026-10-18_to_delete.txt`.
  NOT deleted (Tal undecided): `runs_pod42_batch` 17 GB, the rest of `runs_debug_merge0.015_amodal_fillseg_sam3mask` ~29 GB, old `experiments/guitar` runs.
- **Git:** pods 38-48 committed + pushed, `analysis` 6e98aa9.
- **New way of working (Tal):** Mac (MacBook Air M5, 24 GB, CPU only = like a CPU pod) for daily work; GPU on a RunPod pod or on
  TAU's Run:ai cluster. Plan: (1) git = single source of code [done]; (2) portable env spec -> Mac CPU env + Docker image for Run:ai;
  (3) notes in the repo [done, see top of file]; (4) data/results stay on the server, rsync to the Mac only what is needed.
- **RENAME bsb -> disc (Tal: "we started from BSB but moved elsewhere"):** repo dir `/workspace/disc` (`/workspace/bsb` = symlink, so old
  run configs / paths still resolve); conda env `disc` (= symlink `miniconda3/envs/disc -> bsb`); paper clone `/workspace/DISC` -> `/workspace/DISC_paper`
  (avoids a disc/DISC clash on the case-insensitive Mac). GitHub repo renamed by Tal: `git@github.com:talberger/disc.git` (remote `github`), default branch = `analysis`; README cut to a minimal DISC one.
- **ACTIVATION, every machine: `source <repo>/env/activate.sh`** -> sets `DISC_ROOT` (repo), `DISC_WS` (folder around it: logs, .cache, sam3_repo,
  pix2gestalt_repo; pod `/workspace`, Mac = repo parent), TORCH_HOME/HF_HOME, activates `disc`, installs the deploy key on a pod, cds to the repo.
  `/workspace/activate_bsb.sh` (and `activate_disc.sh`) now only source it. All 375 shell scripts use `$DISC_ROOT` / `$DISC_WS` instead of `/workspace/...`.
- **kaolin is optional** (commit 7be2fa1): lazy import; OBJ files load without it (identical vertices/faces on all 101 repo meshes). Only rendering needs it
  (= GPU machine). Mac env = `env/requirements_disc_mac.txt` (same versions, CPU torch, no kaolin). Env files for all 3 envs in `env/`.
- **MAC SET UP (Tal's Claude Code on the Mac):** `~/Projects/disc` (DISC_WS=~/Projects), miniconda `~/miniconda3`, env `disc` python 3.9.23,
  torch 1.12.1 CPU / numpy 1.26.4 / open3d 0.17.0, module imports OK. Mac-only deviations (Tal chose same versions or nothing): NO pymeshlab
  (no py3.9 arm64 wheel -> remeshing stays on the pod); open3d needs `llvm-openmp` from conda-forge + DYLD_FALLBACK_LIBRARY_PATH (steps in the
  header of `env/requirements_disc_mac.txt`). `env/activate.sh` works there without conda's shell hook (6fbb1c4).
- **DATA TO THE MAC: `bash scripts/sync_from_pod.sh <pod IP> <SSH port> [base|horse56069|<repo path> ...]`** (run on the Mac, rsync pull-only;
  the Mac's SSH key is already in the pod's authorized_keys). Synced 2026-10-18: `base` + `horse56069` (~3.6 GB), mesh load checked on the Mac.
- **Code outside the repo moved in:** our SAM 3 / pix2gestalt scripts -> `external/` (bd0665c); copy them into the clones on a new GPU machine.
- **Run:ai status (from Tal's Claude Desktop session):** Docker Hub user `tberger3`, test image `tberger3/disc:v1` (built `--platform linux/amd64`);
  runai-cli 2.26.51, SSO login OK; project `avidan`, cluster hpc-220711; PVC `tal-disc-data` (lustre-user, RWO, 100G, at /workspace);
  workspace `tberger3-dev` (0 GPU) Running. **Blocked on the TAU VPN** (cluster API reachable only from TAU network).

## STATE AT POD CLOSE — 2026-10-14 (forty-eighth pod, CPU only, NO GPU). **NOTHING IS RUNNING, NOTHING WAS TRAINED.** Tal closes the pod.
**Thread: FEATURE-AWARE 2D GEODESIC, calibration sweep on DINO+SD with neighbours in ANY segment (horse 56069). RESULT: no sweet spot found; Tal parks the per-step cost and looks for a different path definition.**
- **Tal's framing (corrects pod 47):** the new metric SHOULD inflate paths inside a segment, but only SLIGHTLY compared with paths that leave the segment. The test is the ratio
  "same segment / other segment", not "does in-segment inflate".
- **Tool change:** `analysis/plot_2d_paths_in_segment.py --any_segment` -- the 8 neighbours (60 px, 8 directions) may lie in any fine segment; circle = same segment,
  square = other segment; titles + stdout print mean length/original for same vs other (pre-edit copy `/workspace/archive/plot_2d_paths_in_segment.py.bak_2026-10-14`).
  Centres (row, col) of pod 47: (270,150) nose, (110,140) forehead, (260,225) right body, (330,40) left chest, (190,130) between the eyes; last column = C (270,150) with
  N1 (250,230) / N2 (70,140) / N3 (330,30). Features `demo/shic/crowding/horse_lvis56069/features/lvis56069_pix_sdsquare_fuse16.pth`, inputs from
  `data/densepose_lvis/runs_debug_merge0.015_amodal_fillseg_sam3mask/lvis56069/`. ~30 s per figure on CPU.
- **CAVEAT for reading "segment":** after merge 1.5% segment 1 = head + left chest + left body (the border runs down the face). C -> N3 (nose -> chest) counts as SAME segment.
- **RESULTS (mean new/original path length, same segment / other segment; "-" = no other-segment neighbour):**
  | power, beta | nose | forehead | right body | left chest | between eyes | C->N1/N2/N3 |
  |---|---|---|---|---|---|---|
  | p4 b0.5 | 1.09 / 1.27 | 1.15 | 1.15 / 1.40 | 1.29 | 1.17 / 1.00 | 1.2 / 1.0 / 1.3 |
  | p4 b1 | 1.13 / 1.34 | 1.20 | 1.22 / 1.52 | 1.43 | 1.23 / 1.00 | 1.2 / 1.0 / 1.6 |
  | p4 b2 | 1.15 / 1.43 | 1.24 | 1.25 / 1.59 | 1.57 | 1.41 / 1.05 | 1.3 / 1.0 / 1.7 |
  | p4 b3 | 1.27 / 1.47 | 1.26 | 1.37 / 1.62 | 1.79 | 1.41 / 1.15 | 1.3 / 1.0 / 1.9 |
  | p4 b10 | 1.32 / 1.63 | 1.29 | 1.53 / 2.88 | 2.30 | 1.60 / 2.50 | 3.0 / 1.0 / 2.2 |
  | p4 b50 / b100 | 1.41 / 2.58 ; 1.43 / 2.62 | 1.44 ; 1.45 | 2.62 / 3.97 ; 2.71 / 4.05 | 2.53 ; 2.57 | 2.45 / 3.20 ; 2.51 / 3.20 | 3.2 / 1.2 / 2.4 |
  | p6 b10 | 1.32 / 2.53 | 1.32 | 1.54 / 3.81 | 2.47 | 1.74 / 2.50 | 3.0 / 1.0 / 2.3 |
  | p6 b50 / b100 | 1.37 / 3.65 ; 1.43 / 3.71 | 1.54 ; 1.62 | 2.54 / 4.13 ; 2.66 / 4.16 | 2.83 ; 2.88 | 3.12 / 3.30 ; 3.20 / 3.33 | 3.3/1.2/2.4 ; 3.3/1.2/4.1 |
  | p8 b0 | 1.00 everywhere (= original metric, sanity check passed) | | | | | |
  | p8 b0.5 | 1.10 / 1.34 | 1.18 | 1.23 / 1.52 | 1.58 (max 3.4) | 1.37 / 1.00 | 1.2 / 1.0 / 1.4 |
  | p8 b1 | 1.16 / 1.51 | 1.21 | 1.30 / 1.68 | 1.73 | 1.41 / 1.30 | 1.4 / 1.0 / 1.8 |
  | p8 b2 | 1.24 / 1.63 | 1.25 | 1.43 / 1.70 | 2.00 | 1.43 / 1.46 | 1.5 / 1.0 / 1.9 |
  | p8 b3 | 1.26 / 1.67 | 1.26 | 1.46 / 1.76 | 2.12 | 1.44 / 1.62 | 1.5 / 1.0 / 2.0 |
  | p8 b5 | 1.27 / 1.67 | 1.28 | 1.48 / 1.80 | 2.27 | 1.56 / 2.41 | 1.5 / 1.0 / 2.2 |
  | p8 b10 | 1.30 / 2.44 | 1.31 | 2.16 / 3.81 | 2.64 | 1.72 / 2.50 | 3.0 / 1.0 / 2.3 |
  | p8 b50 | 1.36 / 3.64 | 1.72 | 2.39 / 4.13 | 3.29 | 2.94 / 2.60 | 3.2 / 1.2 / 3.7 |
  | p8 b100 | 1.38 / 3.71 | 2.04 | 2.50 / 4.19 | 3.33 (max 10) | 3.12 / 2.97 | 3.2 / 1.2 / 4.1 |
- **Reading:** every setting that strengthens the separation somewhere also inflates in-segment paths somewhere else. Low beta (p4 b0.5-2) ~ the original metric
  (safe, but C->N1 nose->body only x1.2). Biggest separation jump p8 b5 -> b10 (nose other 1.67 -> 2.44, C->N1 1.5 -> 3.0). Above b10 separation barely grows,
  in-segment inflation does. The left chest (330,40), near the mask border, inflates at EVERY setting (vertical corridors). Power 8 creates corridors already at
  b0.5 (chest 1.58, between eyes 1.37) where power 4 does not (1.29 / 1.17). Power changes little versus the left-right vs up-down step asymmetry (x1.7, pod 47).
- **Literature search (Tal asked, web):** NO paper found that computes pixel-to-pixel paths on a DINO/SD feature map. Closest: GeoS (Criminisi 2008) and Geodesic
  Matting (Bai & Sapiro 2007) = the same mechanism (Dijkstra / fast marching, step cost `sqrt(1 + g^2 |grad I|^2)`, colour gradient, mild = ~power 1-2) for
  segmentation from seeds; Intelligent Scissors / minimal paths = explicit path but cost LOW on edges (follows the boundary = the opposite of ours).
  Family 2 (affinity graph, average over ALL paths: Random Walker, NCuts, Deep Spectral Methods on DINO, diffusion / biharmonic / heat) gives a distance, NO path,
  but is robust to single cheap corridors and isolated walls -- the two failure modes seen. Pod 45: biharmonic was the only method with a head/body boundary.
  Tal: the 2D papers "are not what we were looking for" (they are not a path between two pixels on a feature map) -- correct; recorded as building blocks only.
- **NEXT POD (Tal, nothing decided):** find a different path definition: (a) by segments, (b) move the distance to 3D, (c) keep searching the literature.
  Family-2 distance on DINO+SD with the same same/other check is cheap (CPU, minutes) if Tal wants it. Still open: hidden (amodal) pixels fix before any occluded
  instance with `--feature_geodesic` (REMIND TAL); the wider-span (14-28 px) idea is on hold; 3D geodesics for the three pairs; bear 159218.
- **Also this pod:** Obsidian note for the experiment (Tal's vault, written here then copied by Tal): `/workspace/obsidian/2026-10-13_2D_distance_path/`
  (`.md` + `attachments/`, zip next to it); today's section is appended to the same note. Recap of `rkd_feat_angle2` (closed 09-04 / 09-15) given to Tal for a new branch.
- **Figures** (`demo/shic/crowding/horse_lvis56069/`): `lvis56069_pod48_paths_any_segment_{beta100_power8, beta5_10_power8, beta10_50_100_power8,
  beta10_50_100_power6, beta0_5_power8, beta3_5_power8, beta3_10_50_100_power4, beta1_2_3_power4, beta0.5_1_power4, beta0.5_1_2_3_5_power8}.png`.
- Uncommitted in bsb: + the `--any_segment` change above (pods 38-48 all uncommitted). Disk: the 5 pod-47 run dirs (~10 GB) still waiting for Tal's OK to delete.
  Backups of this file: `/workspace/archive/PROJECT_NOTES_backup_2026-10-14_pod48_{open,close}.md`.

## STATE AT POD CLOSE — 2026-10-13 (forty-seventh pod, 1x RTX 2000 Ada sm_89 16 GB, same day as pod 46). **NOTHING IS RUNNING.** Tal closes the pod.
**Thread: FEATURE-AWARE 2D GEODESIC, now on the training's DINO+SD features and in real runs (horse 56069). RESULT: implemented and run; it does NOT fix the nose.**
- **IMPLEMENTED (default = the original metric, verified unchanged):** `analysis/build_geodesic_tables.py --feature_geodesic BETA POWER --pix_features_path F`
  (`build_2d_table(feature_cost=...)`: feature step cost chooses the path, table value = the path's PIXEL length via Dijkstra predecessors + `path_pixel_lengths`;
  the true diameter stays the pixel-metric one). Verified against the path plots (C -> N1 / N2 / N3 = 283.5 / 244.0 / 592.0 px, serial = parallel).
  Passed on by `scripts/run_lvis_worker.py --feature_geodesic B P [--feature_geodesic_diameter original|path]` and
  `FEATGEO="B P" [FEATGEO_DIAM=path] bash scripts/debug_twostage_instance.sh` (run / demo dir suffix `_featgeo_b<B>_p<P>[_pathdiam]`).
  `path` = divide the table by its own longest path (max over the table) instead of the original diameter. Table stage 18 s -> 93-122 s; training unchanged.
- **RUNS, horse 56069, current recipe (SAM 3 mask, mask in one piece so no amodal, FILLSEG, merge 1.5% -> 4 segments), soft-snap pt1 / pt2 / pt3, mean, 1 seed:**
  | run | end of stage 1 | final |
  |---|---|---|
  | original 2D distance (first current-recipe run of this horse) | 9.4 / 15.3 / 95.1, 39.9 | 7.4 / 15.3 / 95.1, 39.3 |
  | beta 100 power 8, / 481 | 10.9 / 19.4 / 95.1, 41.8 | 12.6 / 22.4 / 87.8, 40.9 |
  | beta 100 power 8, / own longest path (1138) | 7.3 / 22.4 / 87.4, 39.0 | 7.3 / 22.4 / 87.4, 39.0 |
  | beta 10 power 8, / 481 | 4.1 / 16.8 / 87.0, 36.0 | 2.3 / 16.8 / 82.1, 33.7 |
  | beta 10 power 8, / own longest path (837) | 9.4 / 21.6 / 76.3, 35.8 | 9.4 / 19.3 / 78.8, 35.8 |
  ZS 6.3 / 24.6 / 0.0, 10.3; SHIC 2.3 / 18.3 / 0.0, 6.9. Old-recipe runs of 10-06 (polygon): final 39.6-39.9, pt 3 94-95.
  **The nose (pt 3) stays destroyed by stage 1 in every run (76-95).** Beta 10 is better than beta 100 and the only one below the original, by 3-6 points on one
  instance / one seed = not established. The normalisation was not the problem.
- **WHY (checked, no training):**
  - On DINO+SD the paths at beta 10 power 8 are weaker than on DINO (C -> N3 0.69 vs 0.92; no climb through the head); beta 100 power 8 gives the climb (1.23). Tal chose 100 for the runs.
    The SAM 3 mask gives the same paths as the polygon. The pod-44..46 figures were on the LVIS polygon only because no SAM 3 mask existed; **the method never uses the polygon.**
  - **The feature metric inflates EVERYTHING, inside a part too.** Training table, norm by 481, beta 100: median all pairs 0.31 -> 0.74, in-segment 0.25 -> 0.50, 33% of pairs above 1;
    correlation with the 3D geodesic of the ZS-mapped vertices unchanged (0.398 -> 0.393), bias +0.08 -> +0.56. In-segment neighbours 60 px away get paths x2.0-3.5 on average,
    up to x10 (600 px); beta 10: x1.3-2.7, up to x6.
  - **Sideways steps cost far more than vertical ones: feature change per step, median, 1.28 left-right vs 0.77 up-down (x1.7; SD half x2.1, DINO half x1.4).** NOT a pipeline
    bug: the same numbers come out when the features are extracted from the crop rotated 90 deg (1.29 / 0.75), so it belongs to this frontal horse. Power 8 turns x1.7 into x58
    in cost -> vertical corridors, paths made of long vertical runs. Also visible: the feature map is a 16 x 11 cell grid (~25 px per cell) upsampled, so the cost is blocky.
  - **"Wall only" threshold (a step above a percentile of the change costs x(1 + beta), the rest plain length): no threshold separates.** Percentile 80-95: in-segment paths stable
    (x1.04-1.11) but the across-part paths do not change at all (body 0.18) -- the strong-change spots are islands, not a closed head / body line. Percentile 50 and below: body / chest
    move away and the in-segment paths inflate with them. Best point: percentile 50, beta 100 = in-segment x1.66, C -> N1 0.48, N2 0.42, N3 0.56 (power law beta 10: x1.98, 0.55 / 0.44 / 0.69).
  - **My conclusion (told to Tal, he has not answered): a cost built from the change between two NEIGHBOURING pixels cannot separate head from body on this horse, at any setting;**
    the head / body difference shows only over a larger distance.
- **NEXT POD (Tal continues from here; nothing decided):**
  1. Proposed and awaiting his answer: the **"feature change over a wider span (14-28 px)" experiment** he asked to be reminded of -- first fix the mask-border artefact
     (`span_rel`: the span shrinks at the border -> cheap corridor). Today's 28 px run at beta 100 power 8 on DINO+SD: N1 goes up through the head (0.66) but N3 circles the
     whole horse along the mask border (1.99) = the artefact, not a result.
  2. Check any new variant FIRST on the in-segment path figure + the across-part column (`plot_2d_paths_in_segment.py`, minutes), only then train (Tal: "this is a good check").
  3. Still open: 3D geodesics on the mesh for the three pairs (pod 44); bear 159218 as the second example; a cost for crossing a fine-segment boundary (Tal: "not now").
- **REMIND TAL (he said "you MUST remind me"): HIDDEN (amodal) PIXELS UNDER THE FEATURE GEODESIC.** As coded, a step that touches a hidden pixel costs its plain pixel
  length (no feature term) -> hidden regions are cheap shortcuts. "Cost of a typical step (1 + beta)" was rejected by Tal.
  **AGREED FIX, NOT IMPLEMENTED: harmonic interpolation of the FEATURES into the hidden pixels** (each hidden pixel = mean of its neighbours, iterated to convergence,
  visible pixels at the occluder's rim fixed; mid-fence ~ (x + y) / 2), then the normal feature step cost everywhere. Not needed on horse 56069 (mask in one piece).
  **The first time an occluded / split-mask instance is run with `--feature_geodesic`, raise this with Tal BEFORE running, implement it and check it.**
- **The formula, as explained to Tal:** `step cost = length * (1 + beta * (delta / median) ** power)`; the `1` = the plain distance (beta 0 = the original metric; without it a flat
  region is free); beta sets from which change a step counts as a wall (`beta ** (-1 / power)`: 0.56 of the median at beta 100, 0.75 at beta 10), power how sharp. At beta 100
  95% of the left-right steps and 69% of the up-down steps are above that threshold.
- **Figures** (`demo/shic/crowding/horse_lvis56069/`): `lvis56069_pod47_SUMMARY_dinosd.png`, `lvis56069_pod47_ALL_RUNS_dinosd.png` (pod-46 sweep on DINO+SD),
  `lvis56069_optionA_beta100_power8_span1_28_dinosd.png`, `..._sam3mask_dinosd.png`, `lvis56069_pod47_table_check_nose.png` (distance field from the nose: original / new / 3D target),
  `lvis56069_pod47_in_segment_paths_beta10_50_100_power8.png`, `lvis56069_pod47_step_direction_check.png`, `lvis56069_pod47_wall_only_paths.png` (+ `_view.jpg`: the PNG is 4.9 MB,
  too big to send), `lvis56069_pod47_three_runs_backproj_stages.png`, `lvis56069_pod47_beta10_runs_backproj_stages.png`. Features: `features/lvis56069_pix_sdsquare_fuse16.pth`.
  Run figures: `demo/shic/debug_twostage/horse_lvis56069_merge0.015_amodal_fillseg_sam3mask{,_featgeo_b100_p8,_featgeo_b100_p8_pathdiam,_featgeo_b10_p8,_featgeo_b10_p8_pathdiam}/`.
- **Disk added (free when Tal agrees):** 5 kept run dirs of horse 56069, ~2 GB each: `data/densepose_lvis/runs_debug_merge0.015_amodal_fillseg_sam3mask/lvis56069` and
  `runs_debug_merge0.015_amodal_fillseg_sam3mask_featgeo_{b100_p8,b100_p8_pathdiam,b10_p8,b10_p8_pathdiam}/`. Logs + queue scripts `/workspace/logs/pod47_featgeo/`.
- **Uncommitted in bsb** (last commit 18f350c; Tal did not ask for a commit): everything of pods 38-47. Today: M `analysis/build_geodesic_tables.py`, `scripts/run_lvis_worker.py`,
  `scripts/debug_twostage_instance.sh` (pre-edit copies `/workspace/archive/*.bak_2026-10-13`), `analysis/plot_2d_crowding_overview.py` (`--features_label`);
  NEW `analysis/plot_2d_paths_in_segment.py` (`--betas`, `--threshold_percentiles`, `--cross_points`; slow, ~5 min for 5 rows x 6 columns).
  One-off scripts (table statistics, direction check, threshold sweep) were in the session scratchpad and are gone; their numbers are above.
  Backups of this file: `/workspace/archive/PROJECT_NOTES_backup_2026-10-13_pod47_{open,close}.md`.

## STATE AT POD CLOSE — 2026-10-13 (forty-sixth pod, CPU only). **NOTHING IS RUNNING, NOTHING WAS TRAINED.** Tal closes the pod.
**Thread: FEATURE-AWARE 2D GEODESIC for crowded parts (horse 56069, same C / N1 / N2 / N3). DECISION (Tal): go to real experiments with option A, beta 10, power 8.**
- **The pod-45 open question is answered: Tal meant option A** (cost of a step = dissimilarity between the step's two pixels), and wants the algorithm to
  prefer a long route through similar pixels over a short one through dissimilar ones. Target behaviour in his words: C -> N3 should go UP through the head and down.
- **Formula (as coded, `analysis/plot_2d_feature_geodesic_paths.py`):** `step cost(p -> q) = |p - q| * (1 + beta * (delta / median_delta) ** power)`,
  `delta = 1 - cos(f_p, f_q)`, p and q 8-neighbours. median = units only (delta between neighbours is ~6.5e-4). power = how steep the wall is;
  beta = from which height a change counts as a wall (threshold `rel0 = beta ** (-1 / power)`).
- **DISTANCE DEFINITION (Tal approved): the features only CHOOSE the path; the distance is the path's LENGTH IN PIXELS / the ORIGINAL pixel diameter (481.4).**
  Dividing the cost by the same-metric diameter is broken at power >= 4 (one pixel behind a wall sets the diameter: 1.5e8 at power 8 -> every ratio 0).
- **Results, frozen DINO-ONLY features (CPU; NOT the training's DINO+SD), path px / 481.4:**
  | variant | N1 body | N2 forehead | N3 chest |
  |---|---|---|---|
  | original (no features) | 0.18 | 0.42 | 0.30 |
  | A power 1, beta 10 ... 1000 | 0.22 | 0.44-0.52 | 0.37 |
  | A power 4, beta 10 / 100 / 1000 | 0.24 / 0.63 / 0.65 | 0.52 / 0.53 / 0.54 | 0.56 / 0.59 / 0.98 |
  | **A power 8, beta 10 (CHOSEN)** | **0.57** | **0.44** | **0.92** |
  | A power 8, beta 100 / 1000 / 1e6+ | 0.64 / 0.67 / 0.74 | 0.57 / 0.74 / 0.89 | 0.99 / 1.00 / 1.01 |
  | A beta 10, power 12 / 32 / 256 | 0.53 / 0.52 / 0.50 | 0.44 / 0.43 / 0.43 | 0.91 / 0.85 / 0.82 |
  | A power 32, beta 1e3 / 1e6 / 1e9 | 0.54 / 0.64 / 0.71 | 0.49 / 0.70 / 1.11 | 1.01 / 1.13 / 1.36 |
  | B (unlike C) beta 10 power 8 | 0.19 | 0.46 | 0.40 |
  | A + B, beta 10 power 8 | 0.23 | 0.43 | 0.51 |
  - Power 1: beta does nothing at any value (no wall: neighbour delta is near uniform, p99 = 5x median; the head/body ridge is only 2-3x).
  - **Power 8, beta 10: C -> N3 climbs inside the head to eye height and only then crosses (145 -> 445 px); body ends up farther than the forehead.**
    Tal: "looks good"; "beta 1000 power 4 also fine, maybe a bit less".
  - Power above 8 at beta 10: saturated. Beta above 10 at power >= 8: the path to the FOREHEAD turns into a maze (walls inside the head) and the paths
    snap to DINO's 14 px patch grid -> worse. Beta >= 1e6 at power 8: frozen.
  - **C -> N1 never goes through the head** in any A variant: it drops under the muzzle and comes round from the right (the neck is hidden in this photo).
  - B and A + B: no good (B makes everything unlike C equally expensive and flattens A's walls). Tal: B "interesting but not the direction".
  - "Change measured over 7 / 14 / 28 px" (`--delta_spans`): at 28 px N1 DOES climb the head and cross at the shoulder, but N3 hugs the mask border --
    **an artefact of the implementation** (the span shrinks at the border -> cheap corridor; `span_rel` docstring). NOT conclusive.
- **NEXT POD (GPU), in this order:**
  1. **Implement the chosen metric in `build_2d_table` (`analysis/build_geodesic_tables.py`) behind a flag, default = the original metric:** feature step cost
     (beta 10, power 8), Dijkstra with predecessors, table value = path length in pixels, normalised by the ORIGINAL diameter. Needs the photo features before
     the table (already the stage order). Estimated cost: only the table stage (16-36 s today) grows, guessed 2-4x, NOT measured; training unchanged.
  2. Run it for real on horse 56069 (symptom to check: GT pt 3, the nose, ZS 0.0 -> stage 1 95.1) -- first re-render the paths with the training's DINO+SD
     features (`extract_dino_sd_features.py --sd_frame square_pad --cpu_postprocess`; **the GPU extraction was NOT run this pod**, so beta 10 / power 8 is
     tuned on DINO only and on ONE centre pixel of ONE horse; bear 159218 is the second example).
  3. **REMIND TAL (he asked): the "feature change over a wider span (14 px)" experiment** -- fix the mask-border artefact first (e.g. normalise by the span
     actually measured), then rerun 7 / 14 / 28.
  4. Later, maybe (Tal: "not now"): a cost for crossing a FINE-SEGMENT boundary. Still open from pod 44: the 3D geodesics on the mesh for the three pairs.
- **Figures** (`demo/shic/crowding/horse_lvis56069/`): `lvis56069_pod46_SUMMARY_dino.png` (original vs chosen, feature PCA, change map, 4 heatmaps),
  `lvis56069_pod46_ALL_RUNS_dino.png` (every variant, one row per experiment, chosen framed green), + one `lvis56069_option*_dino.png` per sweep, `lvis56069_setup_dino.png`,
  `lvis56069_feature_change_map_dino.png`. Rebuild: `analysis/plot_2d_crowding_overview.py` (`--overview_path`, `--summary_path`).
- Uncommitted in bsb: NEW `analysis/plot_2d_crowding_setup.py`, `plot_2d_feature_change_map.py`, `plot_2d_crowding_overview.py`; CHANGED
  `plot_2d_feature_geodesic_paths.py` (`--cost_modes step|start|both`, `--delta_spans`, `--similarity_row`, module-level `span_rel`; option B is now / median).
  Backup of this file before the entry: `/workspace/archive/PROJECT_NOTES_backup_2026-10-13_pod46_close.md`.

## STATE AT POD CLOSE — 2026-10-12 (forty-fifth pod, CPU only, same day as pod 44). **NOTHING IS RUNNING, NOTHING WAS TRAINED.** Tal closes the pod.
**Thread (Tal's idea): FEATURE-AWARE 2D DISTANCE for the crowded-parts problem** -- the path's cost depends on the features, so head -> body becomes "long".
- Horse 56069, same C (270, 150) / N1 (250, 230) / N2 (70, 140) / N3 (330, 30) as pod 44.
  frozen DINO-only features (CPU, NOT the training's DINO+SD), each method divided by its own diameter:
  | method | N1 body | N2 forehead | N3 chest |
  |---|---|---|---|
  | training metric | 0.183 | 0.424 | 0.301 |
  | 1 feature cost on the 8-direction graph, linear, beta 10 | 0.212 | 0.319 | 0.383 |
  | 2 fast marching, same cost as a per-pixel field | 0.227 | 0.326 | 0.361 |
  | 3 Isomap (feature-space kNN, k 8) | 0.236 | 0.399 | 0.361 |
  | 4 biharmonic (spatial graph, feature affinity) | 0.341 | 0.583 | 0.494 |
  | 5 spectral (15 eigenvectors) | 0.422 | 0.421 | 0.412 |
  Only biharmonic shows a head/body boundary (distance only, no path). Squared cost (beta 10: 0.130 / 0.140 / 0.247) pulls everything closer, N1 included.
  3-5 on a 4 px grid; 4-5 use a 99th-percentile diameter. Method 6 (functional maps) not run: it matches two images, not two pixels of one.
  Figure (source + methods 1-5, 6 columns): `demo/shic/crowding/horse_lvis56069/lvis56069_feature_distances_methods1to5_dino.png`; the older one with the
  squared column: `..._all_methods_dino.png`. Script `analysis/compare_2d_feature_distances.py` (`--power 1`), + `analysis/plot_2d_feature_geodesic_paths.py`.
  `scikit-fmm` 2025.1.29 installed with `--no-deps` (built from source). Still NOT done: the 3D geodesics on the mesh = no target number to compare against.
- **Tal's verdict: "none of them does what I wanted".** What he described: the feature map decides, and a path that passes through a pixel NOT SIMILAR TO WHERE WE
  STAND gets more expensive. Methods 1-2 are the closest, but they compare each pixel with the PREVIOUS pixel on the path; DINO features change gradually, so
  every step is cheap and head -> body costs almost nothing. **My reading (NOT confirmed by Tal): he means dissimilar to the START pixel C**, i.e. per-pixel cost
  `1 + beta * (1 - cos(f_p, f_C))`. NOT run. Caveats told to him: not symmetric (d(C,N) != d(N,C); could average both directions), and N2 (forehead) may get
  expensive too if it is unlike the nose.
- **NEXT:** ask Tal which "where we stand" he means (previous pixel = method 1, done; start pixel C = a few lines on top of the fast-marching column), then run it.
  Still open from pod 44: the 3D geodesics on the mesh for the three pairs (the target numbers).
- Uncommitted in bsb: + `analysis/compare_2d_feature_distances.py`, `analysis/plot_2d_feature_geodesic_paths.py` (and pod 44's `analysis/plot_2d_geodesic_paths.py`).
  Backup of this file before the entry: `/workspace/archive/PROJECT_NOTES_backup_2026-10-12_pod45_close.md`.

## STATE AT POD CLOSE — 2026-10-12 (forty-fourth pod, short morning session). **NOTHING IS RUNNING, NOTHING WAS TRAINED.** Tal closes the pod, continues the same day.
**New thread (Tal): CROWDED PARTS IN THE IMAGE** -- parts that touch in the 2D mask (head against the body) have a SHORT 2D geodesic while their mesh geodesic is long
(the 10-07 "parts that merge in the 2D mask" root cause). Tal wants to study it and has several fixes in mind (NOT told yet).
- **Working example = horse 56069** (Tal: easy to read; GT pt 3, the nose, ZS 0.0 -> stage 1 95.1, is the symptom -> the check after a fix). Bear 159218 is the second example.
  Horse inputs: `data/densepose_lvis/worst5_crops_2026-10-06/lvis56069/` (crop 271x400, LVIS polygon mask, gt). **No SAM 3 mask / current-recipe run for this horse yet**;
  its only runs are the old eval recipe (`demo/shic/debug_twostage/horse_lvis56069{,_segonly,_merge0.015_segonly}/`; `runs_debug` was deleted).
- **Shared language for pixels: Tal gives `(y, x)` = (row, col) on the crop**, read off `demo/shic/crowding/horse_lvis56069/lvis56069_pixel_grid.png`. Confirm by marking them first.
- **Chosen representative C = (270, 150)** (nose tip) and neighbours N1 (250, 230) body right, N2 (70, 140) forehead, N3 (330, 30) chest left.
- **2D geodesic paths as the training measures them** (NEW `analysis/plot_2d_geodesic_paths.py`: distance from `build_2d_table` itself with C as the only row, diameter =
  the `--true_diameter` double sweep, path = Dijkstra predecessors on the same 8-connected graph, length asserted equal to the table value):
  | pair | geodesic px | Euclidean px | norm_d_2D (/ diameter 481.4) |
  | C -> N1 | 88.3 | 82.5 | 0.183 |
  | C -> N2 | 204.1 | 200.2 | 0.424 |
  | C -> N3 | 144.9 | 134.2 | 0.301 |
  All three paths are straight lines across the mask (geo / Euclid 1.02-1.08 = the 8-direction grid metric, not a detour): nothing separates head from body.
  Tal: "about what I expected". Figure `demo/shic/crowding/horse_lvis56069/lvis56069_geodesic_paths_2d.png`. NOT done: the matching 3D geodesics on the mesh.
- **NEXT (Tal continues from here):** he presents his fix ideas; likely first the 3D side of the same three pairs.
- Uncommitted in bsb: + `analysis/plot_2d_geodesic_paths.py`. Backup of this file before the entry: `/workspace/archive/PROJECT_NOTES_backup_2026-10-12_pod44_close.md`.

## STATE AT POD CLOSE — 2026-10-11 (forty-third pod, 1x RTX 2000 Ada sm_89 16 GB, 10-10 -> 10-11). **NOTHING IS RUNNING.** Tal closes the pod.
**Days = full 131-bear eval of the current recipe (done), guitar on the current recipe, best/worst-vs-SHIC figures, related-work check of SHIC's citers.**
- **FULL BEAR EVAL OF THE CURRENT RECIPE (SAM 3 mask + amodal if split + FILLSEG + merge 1.5% + two-stage), 131/132, soft-snap, mean over instances, 1 seed:**
  | ZS | end of stage 1 | final | old recipe final (polygon, no merge; `results_twostage`) | SHIC |
  | 39.3 | 35.0 | 35.1 | 34.9 | 33.1 |
  new - old +0.18 (SE 0.76; 66 better / 61 worse) | new - SHIC +1.98 (SE 1.43; better on 49/131) | final - stage 1 +0.14 (SE 0.36; 59 / 49; on the 113 multi-segment
  bears +0.16, SE 0.42) | final - ZS -4.21 (SE 1.36; 83 / 48). **=> the new recipe equals the old one (dropping the LVIS polygon cost nothing); SHIC is not beaten;
  stage 2 adds nothing; the only gain clear of the noise is ZS -> stage 1.** 18 bears ended with ONE segment (stage 1 only). Bear 42071 FAILED
  (`asked for 2048 center pixels but only 1488 are eligible`), not scored.
  Results `data/densepose_lvis/results_full_sam3/` (`aggregate.json`), slim run dirs `runs_full_sam3/` (14 GB), logs `/workspace/logs/lvis_pod43_full/`
  (`launch.sh` = the resumable command, ids in `/workspace/logs/lvis_pod43_full_bear_ids.txt`). ~5-6.6 min per bear.
- **SLIM KEEP IS THE WORKER DEFAULT (Tal, 10-10):** after scoring, `run_lvis_worker.py` keeps only the alpha-0.5 `pred_f` of stage 1 + final, the ellipses, masks,
  segments, crop (~100 MB per bear) and drops the photo features, 2D geodesic table, encoder checkpoints. `--keep_intermediates` = everything, `--delete_run_dir` = nothing.
  Figures from a slim run, no training: `ANALYSIS_ONLY=1 RUNS_DIR=<runs> OUT_DIR=<dir> CLASS=bear ANN_ID=<id> SAM3=1 AMODAL=1 bash scripts/debug_twostage_instance.sh`
  (re-extracts the features, removes them again). VERIFIED identical to the original (eval per point + 3 figures byte-identical, bear 38529). It takes ~6 min, about
  the same as a full rerun (6.4 min): the time is Python start-up on the slow volume (`import torch, open3d, kaolin` 41 s), not training. The gain is that the
  figures come from the scored run itself. No other alpha can be exported from a slim run.
- **MASK + FINE-SEGMENT CACHE (Tal, 10-11):** `run_lvis_sam3_batch.sh` reuses SAM 3 / amodal masks from `data/densepose_lvis/mask_cache_sam3/<class>/` (`MASK_CACHE=none` = off)
  and passes `--fine_seg_cache <cache>/fine_segments` to the worker (key = instance + mask source + merge + fill). Seeded from the full run: 132 SAM 3 masks, 19 amodal,
  131 fine segments (177 MB). VERIFIED on bears 255 and 3044 (amodal): every per-point number identical to the full run; setup 22 s instead of ~20 min.
- **THE RUN DIED ONCE IN THE NIGHT** (last result 23:38 UTC, log silent from 01:57, process gone, no traceback, container not restarted; cause unknown) and nobody
  restarted it for hours: the assistant's watcher lived in a session that had ended. **RULE: a long run gets a DETACHED SUPERVISOR on the pod**
  (`/workspace/logs/lvis_pod43_full/supervisor.sh`: relaunch if dead or if the log is silent 40 min, max 6 restarts). Stop it when the run ends: an instance that
  always fails (42071) makes the batch exit 1 and the supervisor relaunch.
- **RESULTS REPRODUCE ON THE SAME GPU TYPE:** 4 bears rerun here gave exactly the pod-41 numbers (186445 18.0, 6462 89.1, 175661 20.8, 38529 97.4), both RTX 2000 Ada.
  So the pod-42 differences are A4500 vs 2000 Ada, not run-to-run noise.
- **GUITAR on the current recipe** (own SAM click mask, segments rebuilt with merge 1.5% + FILLSEG: 17 -> 6; eval v2 AUC snap/argmax/soft, read T=0.01, alpha 0.5, 1 seed):
  | ZS | 87.7 / 86.2 / 85.7 |
  | two-stage: end of stage 1 (step 149) | 87.2 / 86.3 / 85.4 |
  | two-stage: final | 88.2 / 88.7 / 86.7 |
  | per-segment only (no stage 1, 16 in-segment) | **91.6 / 91.2 / 89.2** |
  On the guitar the gain is all stage 2, and per-segment-only beats two-stage by ~3 (as on 09-27: 92.1 / 91.5 / 89.5 with 17 segments). Old 09-27 two-stage run
  along its step checkpoints: stage 1 rises early (step 25-75 ~88.3) and is back at ZS by its end. `scripts/run_guitar_twostage_current.sh` (`MU=aniso` = per-segment only),
  `analysis/eval_guitar_stage_ladder.py`; demo dirs `demo/guitar/runs/isobbox_prop/bsb_isobbox_sdsquare_mu_{globalthenaniso_sw150,aniso_in16out0}_merge0.015_fillseg_a0.5_phase2/eval/`,
  `.../stage_ladder_pod43/old_twostage_0927/`. A guitar run is 8.4 min (training 5.2); Tal asked where it can be shortened -- NOT profiled yet.
- **20-BEAR FIGURES (pod-41 ranking by ours - SHIC):** best 5 = 904 228115 181519 186445 65490; worst 5 = 159218 6462 175661 154652 38529; worst 6-10 = 203312 238826 159225 22063 32412.
  Combined images + per-bear analysis (back-projection ZS / stage 1 / final, segments + ellipses, training centres) in `demo/shic/debug_twostage/ALL10_bears_pod42/`
  (`{BEST5,WORST5,WORST6to10}_vs_shic_{summary,backproj_stages}.png`, `worst5_analysis/`, `worst6to10_analysis/`). Tal: "everything behaved as expected".
  - **Bear 76191 = WRONG GT LABELS in the dataset** (pts 1, 2 labelled on paw soles, drawn on thigh / forearm; our loading verified against the raw json) -> dropped from "best".
  - **Bear 7954 = the SAM 3 mask is the BACKGROUND, not the bear** (0/3 GT points inside) -> dropped from "worst"; its stage numbers mean nothing.
- **RELATED WORK (`/workspace/related_work/RELATED_WORK_SEARCH.md`, 10-11 sections):** Tal's criterion for a competitor = input a 2D image + a GIVEN 3D object mesh,
  output per pixel the matching point on the mesh surface. SHIC is the competitor to beat; BSB is our starting point (Itai's), not a competitor; CSE / CSM are older and weaker,
  not relevant. Of the 16 SHIC-citing papers none is a new competitor: MorphGS (2601.02716) computes such a map zero-shot (GeoAware-SC features + SHIC-style similarity)
  but only as a loss for motion transfer, never evaluated -> a baseline recipe, not a competitor; 2606.30058 maps pixels to a CUBE shared by all categories.
  2024+ citers of CSE / CSM / A-CSM / Universal Canonical Maps: 91 papers, 14 keyword hits, no new competitor. All from abstracts + machine summaries of the full text.
  Leftovers closed 10-11: the 2 citations missing from Semantic Scholar were found via OpenAlex (18 citing works in total) = a shape-analysis PhD thesis (not our task) and
  **"Towards more Transferable Architectures for Dense Pose Estimation" (Tarashima, Tagawa, ICIP 2026, DOI 10.1109/icip61757.2026.11629883): the ONE paper NOT resolved**
  (cites SHIC and CSE, no abstract anywhere, paywalled) -- open it by hand. The 3 entries without an abstract: two look like earlier titles of Morpheus, the third is image
  representation learning by its title. **Search status: SHIC is the only competitor found; 1 paper unresolved; nothing was read by a person.**
- **Disk:** deleted with Tal's OK (40 GB): `runs_debug`, `runs_debug_merge0.015{,_amodal,_amodal_sam3mask,_amodal_fillseg}`, `runs_speedtest`, `runs_sub20_sam3`.
  KEPT `runs/` (11 GB, Sept; holds horse 164135 -- not checked whether the paper figures read it). Could be slimmed: `runs_debug_merge0.015_amodal_fillseg_sam3mask/` 29 GB, `runs_pod42_batch/` 17 GB.
  An `rm -rf` of run dirs needs Tal's explicit OK in the chat (the permission system blocks it otherwise).
- **Uncommitted in bsb** (last commit 18f350c; Tal did not ask for a commit): everything of pods 38-43. New/changed here: `scripts/{run_lvis_worker.py,debug_twostage_instance.sh,run_lvis_sam3_batch.sh}`,
  NEW `scripts/run_guitar_twostage_current.sh`, `analysis/eval_guitar_stage_ladder.py`. Pre-edit copies `/workspace/archive/*.bak_2026-10-1{0,1}`.
- **NEXT (Tal decides):** what to do given that stage 2 adds nothing on 131 bears and SHIC is not beaten; shorten the run time (one-process analysis; profile the guitar run);
  bear 42071 (mask < 2048 px); horses on the current recipe not run.

## STATE AT POD CLOSE — 2026-10-09 (forty-second pod, 1x RTX A4500 sm_86 20 GB). **NOTHING IS RUNNING.** Tal closes the pod.
**Day = remaining figure bears of the 20-bear eval, moved from the per-instance debug script to one batch worker; one-segment fix; found that results differ between pods.**
- **NEXT:** Tal's verdict on the 10 bears shown; decide what "stage 2 helps" can be claimed given the pod-to-pod table (more seeds / same GPU?); Tal's step experiment
  (50 steps less per stage); maybe the full 132 bears with the new recipe.
- **POD OPENING (Tal, 2026-10-09): read the notes, give the 3-4 line summary, ASK. Run nothing** (no env timings, no queue) before he answers.
- **RESULTS ARE NOT REPRODUCIBLE ACROSS PODS / GPUs** (same code, seed 0; RTX 2000 Ada 10-08 vs A4500 10-09), soft-snap mean of 3 points, stage 1 / final:
  | bear | 10-08 | 10-09 | stage 1 -> final gain 10-08 | 10-09 |
  | 7954 | 38.2 / 24.3 | 37.8 / 34.5 | +13.9 | +3.3 |
  | 228115 | 74.8 / 70.4 | 75.6 / 75.2 | +4.5 | +0.4 |
  | 238826 | 18.1 / 14.1 | 13.9 / 16.1 | +4.0 | -2.3 |
  | 904 | 26.7 / 23.2 | 30.7 / 28.2 | +3.6 | +2.5 |
  | 208166 | 7.5 / 6.3 | 6.7 / 9.6 | +1.2 | -2.9 |
  | 159218 | 55.2 / 63.8 | 60.2 / 48.2 | -8.6 | +12.0 |
  The pod-to-pod difference is as large as stage 1 vs final and flips its sign; 228115's ZS also differs on one point (71.2 vs 87.4), so it starts before training
  (stage not located). A per-instance "stage 2 helps" claim from one run is not supported. On the SAME GPU a rerun is identical (below).
- **NO WEIGHT MIXING IN THE BATCH WORKER (Tal asked, checked):** 238826 (7th in the batch), 154652 (last), 159218 (first) = identical on every point
  (ZS / stage 1 / final) to their standalone runs of the same day on the same GPU.
- **ONE FINE SEGMENT = WHOLE MASK (bear 181519; Tal's decision):** run ONLY stage 1 (steps 1 .. mu_switch_step - 1), all 16 neighbours inside the one segment
  (= the whole mask with FILLSEG); final = end of stage 1, arm `stageA` = `ours`, json `single_segment_stage1_only: true`. In `scripts/run_lvis_worker.py`
  (pre-edit copy `/workspace/archive/run_lvis_worker.py.bak_2026-10-09`). 181519: 6 segments (93.7% + five < 1.5%) -> merge -> 1. Result ZS 33.8 -> 12.6 (SHIC 25.0).
  Figure `demo/shic/debug_twostage/bear_lvis181519_stage1_failure/lvis181519_masks_segments.png`.
- **GT points outside the SAM 3 mask** (181519: 2 of 3, far-side legs in shadow): scored as usual in `all`; only effect = those pixels are not in the training. Tal: not a problem.
- **VOLUME STILL SLOW** (`import torch, open3d, kaolin` 82-91 s; 200 small opens 8-11 s; 300 MB read 8.3 MB/s). Training itself is normal (264 s). The debug script
  (~15 processes per instance) took 20-30 min per bear -> **Tal: use the batch (one worker, models loaded once) and build figures afterwards**:
  `WORKER_ARGS="--keep_intermediates"` in `run_lvis_sam3_batch.sh`, then `ANALYSIS_ONLY=1 RUNS_DIR=<runs> OUT_DIR=<dir> SAM3=1 AMODAL=1 bash scripts/debug_twostage_instance.sh`.
  Batch today: 8 bears 3573 s (~7.4 min each incl. 613 s one-time setup; worker 266-460 s each). Analysis-only figures: 10-15 min each on the slow volume.
  Do NOT run a CPU job next to a training run (a CPU SAM run made phase 2 648 s instead of 264 s).
- **Runs today:** `data/densepose_lvis/{results,runs}_pod42_batch/` (159218 228115 208166 7954 904 181519 238826 154652; run dirs kept, ~2.2 GB each).
  Figures: `demo/shic/debug_twostage/bear_lvis<id>_merge0.015_amodal_fillseg_sam3mask[_pod42batch]/` for 76191 65490 (pod 41), 238826 154652 159218 (standalone today),
  7954 904 228115 208166 181519 (`_pod42batch`). All shown to Tal (summaries + stage back-projections of 159218, 7954, 904); no verdict yet.
- **Uncommitted in bsb** (last commit 18f350c; Tal did not ask for a commit): everything of pods 38-42. Today only `scripts/run_lvis_worker.py` (one-segment path).
  Queue scripts/logs: `/workspace/logs/debug_twostage/queue_pod42*.{sh,log}`, `/workspace/logs/lvis_pod42_batch/`.
- **Disk added today (free when Tal agrees):** `data/densepose_lvis/runs_pod42_batch/` 17 GB (8 kept runs), `runs_debug_merge0.015_amodal_fillseg_sam3mask/` now 14 GB
  (+ 238826, 154652, 159218 standalone). Deleted with Tal's OK: the partial 208166 run + demo dir of pod 41. The pod-41 "free when Tal agrees" list is untouched.
- **Open:** which three count as "largest stage 1 -> final gain" given the table above; Tal's step experiment; full 132 bears; `results_sub20_sam3` still has 19 (181519 is only in `results_pod42_batch`).

## STATE AT POD CLOSE — 2026-10-08 (forty-first pod, 1x RTX 2000 Ada sm_89 16 GB). **NOTHING IS RUNNING.** Tal closes the pod.
**Day = drop the LVIS polygon (object mask from SAM 3), make the end-to-end run fast, first 20-bear eval of the new recipe with stage 1 scored.**
**READ THIS FIRST:**
- **RECIPE NOW (all Tal's decisions of today, on top of 10-07):** object mask = **SAM 3, box prompt = the whole bbox crop, NO text, default threshold 0** (no LVIS polygon;
  LVIS gives only the bbox crop + the GT points) + amodal mask (pix2gestalt) **only when the mask is split** (largest connected part < 95% of the mask) with
  **a pixel kept if >= 1 of the 3 samples has it** (was 2 of 3) + `FILLSEG` + segment merge 1.5%.
  - One instance with figures: `CLASS=bear ANN_ID=<id> SAM3=1 AMODAL=1 bash scripts/debug_twostage_instance.sh` -> `demo/shic/debug_twostage/<class>_lvis<id>_merge0.015_amodal_fillseg_sam3mask/`
    (`AMODAL_FORCE=1` = pix2gestalt even if the mask is in one piece; `MIN_VOTES=2` = the old vote).
  - Many instances, no figures: `CLASS=bear ANN_IDS="..." RESULTS=data/densepose_lvis/results_X RUNS=data/densepose_lvis/runs_X setsid nohup bash scripts/run_lvis_sam3_batch.sh >> <log> 2>&1 < /dev/null &`
    (crops -> all SAM 3 masks in one process -> pix2gestalt once for the split ones -> one worker; resumable; masks kept in `$RESULTS/masks/`; the run dirs are DELETED).
  - `run_lvis_worker.py` defaults are still the old eval: pass `--mask_source sam3 --amodal_mask --amodal_wait 5 --merge_below_frac 0.015 --fill_unlabelled_segments` (the batch script does).
- **STAGE 1 IS NOW SCORED IN EVERY TWO-STAGE RUN** (Tal: "data I want for the next runs"): the worker saves the end-of-stage-A state and writes arm `stageA`
  next to `ours` / `zs` in `results_*/lvis<id>.json` (survives the cleanup, goes into `aggregate.json`). `--no_stage1` = off. The old 132-bear eval does NOT have it.
- **20-BEAR EVAL OF THE NEW RECIPE** (`data/densepose_lvis/results_sub20_sam3/`, subset = `subset20_bear_evenspaced.json`: 20 bears evenly spaced over the 132 sorted by
  ours - SHIC on the old eval; Tal wanted a set more representative than the pod-36 one; a 5+5+5+5 pick is saved as `subset20_bear_stratified.json` but is 10/10 wins, NOT used).
  19 scored, 1 failed. Soft-snap, mean over instances, 1 seed:
  | ZS | end of stage 1 | final | SHIC | old recipe final (polygon, no merge) |
  | 47.1 | 36.7 | 36.8 | 35.4 | 37.3 |
  final better than stage 1: 10/19 (1 equal, 8 worse; mean diff +0.11, SE 1.4) | final better than ZS 14/19 | better than SHIC 6/19 (diff +1.3, SE 5.5) | new better than old recipe 12/19.
  **CONCLUSION SO FAR: the gain is ZS -> stage 1; stage 2 adds nothing on average on these 19** (small gains on most, large losses on a few: 38529 81.8 -> 97.4,
  159218 55.2 -> 63.8, 159225 18.8 -> 26.0; the other way 7954 38.2 -> 24.3). Dropping the polygon did not hurt (36.8 vs 37.3). Tal wants to SHOW stage 1 -> stage 2 improves: not shown yet.
  - **181519 FAILED**: `segment 1 has no out-of-segment pixel` -- after merge + FILLSEG one segment covers the whole mask, stage 1 cannot draw "out" neighbours.
    Proposed (NOT answered): in that case draw all 16 neighbours from the whole mask.
  - **7954**: 0 of 3 GT points inside the SAM 3 mask (mask = 15% of the crop, score 0.63: probably another object); scored anyway (24.3).
- **WHERE WE STOPPED:** Tal asked for figures of 6 bears spread best -> worst vs SHIC + the best stage 1 -> final gain: 76191 65490 208166 238826 154652 159218 + 228115 (74.8 -> 70.4;
  the largest gain is 7954 but its GT is outside the mask). The batch had deleted the run dirs, so each needs a rerun (~8.5 min). DONE: **76191, 65490** (not shown to Tal yet).
  NOT done: 208166 (killed mid-run, its demo dir is partial -- rerun), 238826, 154652, 159218, 228115. Queue stopped because the volume became very slow (below).
  Then: Tal's step experiment (50 steps less per stage on a few instances); decide 181519; maybe the full 132 bears with the new recipe (Tal undecided; est. 11-15 h).
- **SAM 3 SETUP (survives a pod switch):** `/workspace/sam3_repo` (clone of facebookresearch/sam3) with its own conda-forge env `/workspace/sam3_repo/env` (python 3.12, torch 2.8.0+cu128;
  created with `conda create -p ... -c conda-forge --override-channels`, no ToS prompt), weights in `/workspace/.cache/huggingface` (facebook/sam3 is gated; Tal's token has access).
  Our files there: `run_box_mask.py` (N images in one call), `run_lvis_box.py`, `run_lvis_box_thresholds.py`. bsb side: `scripts/make_sam3_mask.sh`, `prep_lvis_instance.py --mask_source sam3`.
  SAM 3 uses its SAM-1-style interactive task (`build_sam3_image_model(enable_inst_interactivity=True)`, `model.predict_inst(state, box=...)`). Tal: NO text prompt, only the image goes in.
  - Mask quality on 20 instances vs the polygon (`demo/shic/sam_box_mask/`): IoU >= 0.8 on 15/20 with SAM 3 vs 10/20 with SAM 1 (same box). SAM 3 fixes the "selects the background" cases
    (186445, 51330, 2747). Still fails with two animals of the class in the crop (horse 22240, bear 159481) and on horse 28284. Threshold sweep (-2..2): 0 is best on IoU, -1 keeps more of
    the animal (recall 0.96) but lets background in; Tal kept 0. SAM 1 thresholds do not fix wrong-object picks either.
- **AMODAL VOTE 1 OF 3** (`analysis/merge_amodal_mask.py --min_votes`, default now 1): closes thin fence / branch holes (206034 475 -> 4 px) but not rider / saddle holes (no sample fills them),
  and lets one sample's hallucination in (7107, 7108: a blob under the bear). Figure `demo/shic/amodal_votes_preview/amodal_votes_preview.png` (8 instances). Tal rejected "fill enclosed holes".
  Completed pixels are for distances only. Only pix2gestalt adds them (the geometric gap fill is a fallback that did not trigger).
- **SPEED: one occluded instance with figures 15.3 -> 8.5 min (206034), every output bit-identical** (masks, geo table, pred_f stage 1 + final, all numbers):
  | change | wall s |
  | morning | ~920 |
  | amodal in the background + slim pix2gestalt weights (`ckpt/slim_ema.pt`, 5.1 GB, load 80 -> 50 s) + SHIC point cache | 754 |
  | + `sample_out_segment_neighbors`: the per-segment pool is built once per call (was once per entry) | 616 |
  | + features extracted while SAM 3 runs | 612 |
  | + pix2gestalt process started at the very beginning (loads during SAM 3) | 512 |
  - The sampler was the find: with merge 1.5% one segment is 75-90% of the mask, rejection sampling fails, ~1200 entries/step fell to a loop that rebuilt the pool each time = 45% of a
    stage-1 step. Training 426 -> 223 s. `analysis/profile_phase2.py` replays a kept run under cProfile. What is left in a step (~0.75 s): backward 0.33, encoder 0.17, soft mapping 0.17,
    feature indexing 0.10, cycle 0.06 (the cycle was NOT the cost). Loss is flat from ~step 100 of each stage but the features keep drifting (cos vs phase 1 0.85 -> 0.826 over the last 150).
  - Left: training ~245 s, figures ~130 s (untouched), SAM 3 + prep ~80 s (41 s is imports). Peak GPU 14.5 of 16 GB with the three models up together -- may fail on a larger mask (not tested).
  - In the batch (no figures) an instance is ~300-356 s. 1 pix2gestalt sample instead of 3 would save ~2 s in a single run (it runs in the background): rejected.
- **TODAY'S DEBUG RESULTS (new recipe, soft-snap mean, 1 seed):** bear 206034: ZS 30.5, stage 1 25.4, final 24.7, SHIC 19.8 (polygon + amodal 2of3, no FILLSEG: 26.2; SAM 3 same settings: 26.2, identical points).
  bear 7107: ZS 44.9, stage 1 39.7, final 37.6, SHIC 13.8 (10-07 polygon run: 35.4; pt 2 still ~71).
- **OLD 132-BEAR EVAL, final vs ZS** (Tal asked): better 79/132 (60%), worse 53; by > 5: 63 vs 33; by > 10: 42 vs 19. Stage 2 vs stage 1 cannot be computed there (not saved).
- **Why the polygon went** (Tal): SHIC's baseline gets only the bbox crop, no mask, so using the LVIS polygon was information the baseline does not have; also the polygon is rasterised
  at the original resolution and upscaled nearest -> a blocky rim of non-animal pixels (bear 159218). `FILLSEG` assigns ALL unlabelled mask pixels incl. such a rim (Tal: probably negligible, left as is).
- **Summaries Tal asked for:** horse 56069 / bear 159218 (stage-1 damage, merged-parts root cause -- unchanged from 10-06/07); occlusion before/after figures
  `demo/shic/occlusion_summary/occlusion_summary_bear{7107,206034}.png`.
- **TRAPS:** (1) **THE VOLUME GOT VERY SLOW IN THE EVENING**: ~28 ms per small-file open (4-12 s for 200 files; local disk 0.02 s), repeated reads no faster (no client cache);
  `import torch, open3d, kaolin` > 5 min instead of ~20 s; the debug script (~15 Python processes per instance) went 8.5 -> 28 min, the one-worker batch was hardly affected. Not our code
  (same script ran in 512 s in the afternoon). Check with `time python -c "import torch, open3d, kaolin"` before a figure queue. (2) A watcher that greps `ps` for the script name matches
  itself again -- wait on the PID from `ps -eo pid,args | awk '$2=="bash" && $3=="scripts/..."'`. (3) `realpath` of a relative path AFTER a `cd` in a subshell = wrong dir.
  (4) The worker's `timings` is a list of tuples, not a dict. (5) Activate the env in every fresh shell (`python3` without it has no matplotlib).
- **Uncommitted in bsb** (last commit 18f350c; Tal did not ask for a commit): everything of pods 38-41. Today: M `scripts/{run_lvis_worker.py,debug_twostage_instance.sh,make_amodal_mask.sh}`,
  `analysis/{prep_lvis_instance,prep_amodal_input,merge_amodal_mask,compare_ours_vs_shic_points}.py`, `modules/relational_loss.py`; NEW `scripts/{make_sam3_mask.sh,run_lvis_sam3_batch.sh}`,
  `analysis/{sam_box_mask_preview,sam_box_threshold_sweep,amodal_votes_preview,profile_phase2}.py`. Outside git: `/workspace/pix2gestalt_repo/run_amodal.py` (slim weights, `--wait_for_input`),
  `/workspace/sam3_repo/*.py`. Pre-edit copies `/workspace/archive/*.bak_2026-10-08*`.
- **Disk:** freed 55 GB in the morning (Tal: "delete what you think is safe"): `runs_{horse_,}twostage_examples`, `runs_debug_segonly`, `runs_debug_merge0.015_segonly`, `runs_horse_twostage`.
  Added: `/workspace/sam3_repo` 9.4 GB + weights ~10 GB in the HF cache (KEEP), `pix2gestalt_repo/.../slim_ema.pt` 5.1 GB (KEEP).
  Free when Tal agrees: `data/densepose_lvis/runs_debug/` 15 GB, `runs_debug_merge0.015/` 11 GB, `runs_debug_merge0.015_amodal_fillseg_sam3mask/` 11 GB (today's 206034, 7107, 76191, 65490 + partial 208166),
  `runs_debug_merge0.015_amodal{,_fillseg,_sam3mask}/` 7.8 GB, `runs_speedtest/` 2.2 GB, `runs_sub20_sam3/` 1.6 GB (the failed 181519), `runs/` 11 GB (content not checked), `sambox_preview/`, `amodal_votes_preview/`.
### Still open from earlier pods
Merged-parts root cause (bear 159218 / horse 56069): no fix. Stage 2 under occlusion (Tal still thinking). Pod 39: stage 1 drawing all 16 neighbours from the whole mask (now also the 181519 failure).
Pods 38/39: leg colouring choice, paper 3.4 step 5, cycle ablation, related-work reading. Horses with the new recipe: not run.

## STATE AT POD CLOSE — 2026-10-07 (fortieth pod, 1x RTX 2000 Ada sm_89 16 GB). **NOTHING IS RUNNING.** Tal closes the pod.
**Day = failure cases of the two-stage method -> found the OCCLUSION BUG, built a fix, first results are good.**
**(Recipe lines below are superseded by the 2026-10-08 entry above: SAM 3 mask, amodal only if split, 1-of-3 vote.)**
**READ THIS FIRST (the rest of the section is the detail):**
- **THE BUG:** with an occluder (fence, branches, rider, harness) the LVIS mask splits into parts and the 2D geodesic table kept only the largest one, so the training
  saw a fraction of the animal: 13/132 bears and 63/133 horses lose > 5% of the mask (44 horses > 20%).
- **THE FIX (Tal's spec, implemented, opt-in `AMODAL=1`):** an amodal mask (pix2gestalt, own venv) completes the hidden parts; 2D geodesics run through it in both stages;
  centres/neighbours come from the visible pixels of ALL parts, never from completed pixels.
- **RECIPE FOR EVERY DEBUG RUN NOW (all three are Tal's decisions of today):** segment merge 1.5% + unlabelled pixels join the nearest segment (`FILLSEG`, default ON in the
  debug script since the end of the day, "adopt it for now") + `AMODAL=1` for occluded instances (still opt-in: +~3 min).
  `CLASS=bear ANN_ID=<id> AMODAL=1 bash scripts/debug_twostage_instance.sh` -> `demo/shic/debug_twostage/<class>_lvis<id>_merge0.015_amodal_fillseg/`.
  `run_lvis_worker.py` defaults are ALL still off (`--merge_below_frac 0.015 --fill_unlabelled_segments --amodal_mask` must be passed explicitly in an eval/queue).
- **RESULTS (soft-snap mean, 1 seed):**
  | bear | ZS | full eval (no merge) | merge 1.5% | + occlusion fix | + fill unlabelled | SHIC |
  | 7107 | 44.9 | 49.2 | 54.8 | 36.6 | 35.4 | 13.8 |
  | 206034 | 30.5 | 34.4 | 35.8 | 26.2 | not run | 19.8 |
  Two instances. First time both end BELOW ZS; still above SHIC (7107 pt 2 stays ~70).
- **NEXT (Tal: "we continue tomorrow"):** (1) more occluded instances, horses first (5947 22789 22239 2747 22240 51330 already have pix2gestalt test masks);
  (2) Tal still wants to think about stage 2 under occlusion; (3) rerun the eval with the fix -- NOT done, not asked yet; (4) the merged-parts root cause (below) has no fix yet;
  (5) run time: amodal adds ~3 min (80 s is loading a 15.5 GB checkpoint -- a slim weights-only file would cut it; not done).
- **RULE (Tal): EVERY RUN FROM NOW ON USES SEGMENT MERGE 1.5%** (`--merge_below_frac 0.015`; "otherwise there are too many segments, I understand nothing").
  `scripts/debug_twostage_instance.sh` defaults to it (output dirs end in `_merge0.015`; `MERGE=0` = old recipe). `run_lvis_worker.py`'s default is STILL 0:
  pass the flag explicitly in any new eval/queue. The full-eval numbers (bear 34.91, horse 22.73) and the worst-10 ranking are WITHOUT merge.
- **HOW TO DEBUG ONE INSTANCE (~7.7 min here):** `CLASS=bear ANN_ID=<id> setsid nohup bash scripts/debug_twostage_instance.sh >> /workspace/logs/debug_twostage/<name>.log 2>&1 < /dev/null &`
  -> `demo/shic/debug_twostage/<class>_lvis<id>_merge0.015[_amodal]_fillseg/`: `eval_arms.json` (ZS / stageA / final per point), `summary/SUMMARY_lvis<id>.png` (v2, vs SHIC),
  `lvis<id>_backproj_stages.png`, `lvis<id>_segments_ellipses.png`, `_segments_one_by_one.png`, `_coarse_mask.png`. What Tal asks to see each time: the per-point table
  (ZS / stage 1 / final / SHIC) + ellipses + back-projection per stage + summary. Run instances one after another, not in parallel (one GPU).
  Options: `MERGE=`, `SEGONLY=1`, `AMODAL=1`, `FILLSEG=0`, `ANALYSIS_ONLY=1` (redo the analysis on a kept run, no training), `OUT_DIR=`, `RUNS_DIR=`.
  Raw-label check on the original image: `python analysis/lvis_label_check.py --ann_id <id> --class_name <cls> --output_path <png>`.
- **ROOT CAUSE of bear 159218 / horse 56069 (Tal's conclusion): PARTS THAT MERGE IN THE 2D MASK.** The method is anchored on the 2D image and forces the 3D
  relations to equal the 2D ones. When two parts touch/overlap in the image (head lying against the belly), their 2D geodesic is SHORT, so the loss pulls the mesh
  head and belly together although their true 3D geodesic is long. Hence the damage in stage 1, and merge / segonly cannot fix it. Understood; NO FIX CHOSEN YET.
- **Bear 237843 = suspected WRONG GT LABEL** (Tal spotted it): the 3 label pixels look like HIND legs, dp_vertex 3128 / 530 / 787 are FRONT-leg vertices (z 0.24-0.35, head is +z).
  Verified it is not our indexing (same annotation + same list index for pixel and vertex, ref_model bear_4936 = our 4936-vertex mesh, single annotation in the image;
  the same code gives 0.0 errors elsewhere). NOT certain the annotator is wrong -- "hind legs" is a by-eye call on an ambiguous pose.
  `demo/shic/debug_twostage/bear_lvis237843/lvis237843_label_check.png`. The other worst cases were NOT checked for label errors.
- **Results today** (soft-snap mean over the 3 points, 1 seed; reruns are bit-reproducible on this pod):
  | bear | segments | ZS | stage 1 | final | SHIC | what breaks |
  | 237843 no merge | 16 | 115.3 | 90.1 | 87.9 | 44.4 | suspected label error |
  | 237843 merge 1.5% | 7 | 115.3 | 91.7 | 82.8 | 44.4 | |
  | 7107 no merge | 23 | 44.9 | 48.7 | 49.9 | 13.8 | pt 2 wrong from ZS (104.2 -> 92.4); pt 1 pushed away in stage 1 (7.8 -> 32.2) |
  | 7107 merge 1.5% | 6 | 44.9 | 54.7 | 54.8 | 13.8 | pt 2 104.2 -> 113.8 |
  | 206034 merge 1.5% | 2 | 30.5 | 32.4 | 35.8 | 19.8 | pt 2 28.0 -> 42.6 -> 47.0 (training worse than ZS) |
  Tal has NOT yet given a verdict on 7107 / 206034. ZS-only summaries (v2 layout, "ours" = ZS): `demo/shic/debug_twostage/{bear_lvis159218,horse_lvis56069}/summary_zs/`.
- **OCCLUDED MASKS: THE 2D GEODESIC TABLE KEEPS ONLY THE LARGEST CONNECTED PART OF THE MASK** (`build_geodesic_tables.py::largest_connected_component`, written 09-03 for
  stray SAM specks). With an occluder (fence, branches) the LVIS polygon mask splits into big parts and the training sees one of them:
  | bear | mask parts | share of the mask in the table | GT points inside it |
  | 206034 (fence) | 7 | 37.5% (26116 / 69551 px) | 1 of 3 |
  | 7107 (branches) | 11 | 34.3% (14395 / 41913 px) | 0 of 3 |
  | 237843 | - | 98.1% | 3 of 3 |
  **Tal: this is a BUG. Wanted: train stage 1 AND stage 2 "as if the occluder is not there"** -- 2D geodesics may cross the occluder, every part/segment talks to the others;
  occluder pixels are used for distances only, never as centres/neighbours (Tal agreed) and never in the back-projection. Stage 2 details: Tal still thinking. NOTHING WIRED INTO TRAINING YET.
  **How big (survey of every evaluated instance, `demo/shic/occlusion_gapfill/survey_{bear,horse}.json`):**
  | class | instances | training sees < 95% of the mask | < 80% | < 50% | GT points outside the seen part |
  | bear | 132 | 13 | 7 | 3 | 15 / 393 |
  | horse | 133 | 63 | 44 | 13 | 57 / 390 |  (riders, harness, saddles)
  **Geometric gap fill prototype** (`analysis/gapfill_preview.py::gap_fill`: growing closing radius, keep added blobs that join >= 2 parts, then same-radius closing + enclosed holes
  touching the fill; one-part masks unchanged): joins thin occluders (fence, straps, branches) but FAILS on wide ones (horse 2747 53% connected, 22240 36%, rider/baskets)
  and still leaves some interior holes (bear 7108). Figures `demo/shic/occlusion_gapfill/gapfill_survey_{bear,horse}.png`, `gapfill_preview_bears_206034_7107.png`.
  Tal asked for a GENERIC solution and suggested a model (amodal segmentation); RUNTIME matters to him: prefers simple + fast over best. SAM / SAM 2 / SAM 3 are modal only.
  Candidates checked 2026-10-07 (papers' text + GitHub repo search by name; a repo under another name could have been missed):
  | model | paper | code found |
  | Amodal SAM (SAM + adapter; Tal liked it) | arXiv 2604.20748, Apr 2026 | NO link in the paper, no repo found |
  | SAMEO (EfficientSAM decoder fine-tuned, box prompt) | arXiv 2503.06261, CVPR 2025 | NO |
  | SAMBA "Towards Efficient Foundation Model for Zero-shot Amodal Seg." | CVPR 2025 | paper says "will be released"; no repo found |
  | Tuning-free amodal via inpainting | arXiv 2503.18947 | uses FLUX inpainting through diffusers -- heavy |
  | pix2gestalt | arXiv 2401.14398, CVPR 2024 | YES `cvlab-columbia/pix2gestalt` -- diffusion, slow, needs its own env |
  Fine segments already cross the occluder (206034 seg 1 spans all 7 parts).
  **pix2gestalt TESTED on 10 occluded instances (Tal: "check if it is worth investing"), separate env, bsb env untouched:**
  bears 7107 7108 206034 90357, horses 5947 22789 22239 2747 22240 51330. Figures `/workspace/pix2gestalt_repo/lvis_test/out_steps50/pix2gestalt_test_{1,2}.png`, `summary.json`.
  - Result: it completes the hidden body plausibly where the geometric fill cannot (baskets 2747, harness 22240, rider 51330, fence 206034): 7 of 10 are 100% connected in all
    3 samples; 22239 77/77/97%, 22240 94-96%, 22789 90-91%. Weak spots: the mask is a threshold on the WHITE background of the synthesized image, so white straps / a white
    horse (22240) leave holes; samples differ from each other (7107 area x1.8-2.1). Tal has NOT judged the figures yet.
  - Cost: model load 80 s, then 6.7 s per sample at 50 DDIM steps (their default is 200), 5.5 GB GPU. Input/output are 256x256.
  - Setup: repo `/workspace/pix2gestalt_repo` (clone of cvlab-columbia/pix2gestalt), venv `/workspace/pix2gestalt_repo/venv` (python 3.9 from the bsb env, torch 1.12.1+cu113;
    a venv because `conda create` asks to accept the Anaconda ToS), weights `pix2gestalt/ckpt/epoch=000005.ckpt` (15.5 GB), `setup_env.sh`, `stubs/` (carvekit stub).
    Run: `cd /workspace/pix2gestalt_repo/pix2gestalt && source ../venv/bin/activate && PYTHONPATH=../stubs:taming-transformers:CLIP python ../run_lvis_test.py --steps 50 --n_samples 3`,
    figure: `python /workspace/pix2gestalt_repo/make_test_figure.py --out_dir .../out_steps50` (bsb env). Inputs are built in the bsb env (snippet not saved as a script).
  - TRAPS: their loader puts the whole 15.5 GB checkpoint on the GPU (OOM on 16 GB) -> load on CPU; `ema_scope()` clones the UNet per call (OOM) -> copy the EMA weights in once
    and delete `model_ema` (then 5.2 GB). Their README says the demo needs 22-28 GB; with these two fixes 16 GB is plenty. albumentations 0.4.3 does not build (not needed).
- **OCCLUSION FIX IMPLEMENTED (Tal's spec) + FIRST RESULTS.** 2D geodesics are measured through an AMODAL mask (visible + completed hidden parts), in stage 1 and stage 2;
  centres / neighbours come from the VISIBLE pixels of ALL parts and never from completed pixels (Tal confirmed this is what he meant). The coarse mask file itself is
  unchanged (so fine segments, back-projection, eval are identical); the amodal mask is a second file used for distances only.
  | bear (merge 1.5%, soft-snap, 1 seed) | training saw | ZS | stage 1 | final | SHIC |
  | 7107 before | 34% of the mask | 44.9 | 54.7 | 54.8 | 13.8 |
  | 7107 amodal | 100% | 44.9 | 36.6 | 36.6 | 13.8 |  (pt 2: 113.8 -> 69.8)
  | 206034 before | 38% | 30.5 | 32.4 | 35.8 | 19.8 |
  | 206034 amodal | 100% | 30.5 | 29.4 | 26.2 | 19.8 |  (pt 2: 47.0 -> 24.7)
  Two instances only; Tal has not judged the figures yet. Outputs `demo/shic/debug_twostage/bear_lvis{7107,206034}_merge0.015_amodal/` (+ `lvis<id>_training_centres.png`).
  - Run: `CLASS=bear ANN_ID=<id> AMODAL=1 bash scripts/debug_twostage_instance.sh` (dirs end in `_amodal`). Cost: +~3 min for the mask (80 s model load, 30 s sampling, 2 preps)
    and phase-2 is slower when much more of the mask is trained (206034: 282 -> 444 s; 7107: 212 -> 201 s).
  - Mask recipe (Tal OK'd "start like this"): pix2gestalt, 3 samples x 50 steps, fixed seed 0, pixel kept if in >= 2 of 3 samples, visible mask always kept,
    geometric `gap_fill` only if still disconnected (was not needed on either bear). `scripts/make_amodal_mask.sh` = `analysis/prep_amodal_input.py` (bsb) ->
    `/workspace/pix2gestalt_repo/run_amodal.py` (venv) -> `analysis/merge_amodal_mask.py` (bsb) => `<run dir>/lvis<id>_amodal_mask.pth` (+ `_amodal_stats.json`, `.png`).
  - Code: `analysis/build_geodesic_tables.py --geodesic_domain_mask_path` (`occlusion_domain`, `restrict_table_to_visible`; the table keeps columns for visible pixels only,
    so the training sees an ordinary table; the true diameter is between visible pixels), `phase2/train_relational_loss.py --geodesic_domain_mask_path`,
    `scripts/run_lvis_worker.py --amodal_mask`. Without the flags nothing changes -- VERIFIED: bear 7107 merge 1.5% rerun on the new code = identical geodesic table, pred_f, all numbers and all 14 figures.
  - **OPEN, Tal flagged it as wrong: visible pixels with NO FINE SEGMENT get no centres** (7107: 28.9% of the mask, 206034: 6.4%; SAM's automatic masks do not cover them; same
    with and without merge). Proposed, NOT answered: every unlabelled mask pixel joins the nearest segment. Conflicts with his 10-06 "the unlabelled rim is not part of the animal"
    (that was about a 3-5% rim). Figure `demo/shic/debug_twostage/bear_lvis7107_merge0.015_amodal/lvis7107_unlabelled_pixels.png`.
    TRIAL run (Tal: "try one and see if it matters"): `FILLSEG=1` -> `run_lvis_worker.py --fill_unlabelled_segments` -> `build_fine_segments.py --fill_unlabelled` (opt-in, off by default).
    Bear 7107, merge 1.5% + amodal: final 36.6 -> 35.4 with the fill (pt 1 26.4 -> 21.6, pt 2 69.8 -> 70.8, pt 3 13.7 = 13.7); coverage 71.1% -> 100%. Small effect on this one
    instance. **ADOPTED by Tal "for now" (end of 10-07): `FILLSEG` defaults to 1 in the debug script; `FILLSEG=0` turns it off.** Output `demo/shic/debug_twostage/bear_lvis7107_merge0.015_amodal_fillseg/`.
  - Open: Tal still wants to think about stage 2; the full eval was NOT rerun with the fix (63/133 horses, 13/132 bears affected).
- **Worst 10 per class by (ours - SHIC)**, largest gap first (132 bears / 133 horses): `demo/shic/worst10_vs_shic/worst10_{bear,horse}.png` (crops + GT points).
  Bear: 159218(done) 237843(done) 7107(done) 230979 159481 7108 159486 6462 38528 31383. Also done: 206034 (Tal's pick, from the pod-38 list).
  Horse: 28284 6054 7995 56069(done) 57711 181055 28321 58504 2132 37278.
- **DEBUG RUN SPEED-UP (Tal approved; outputs verified IDENTICAL -- every number and all 14 figures pixel-for-pixel): 856 s -> 460 s per instance.**
  Cause: every Python process pays ~15-23 s of imports from the network volume (torch 5, kaolin 8, open3d 10) and the analysis launched 17 of them.
  - `modules/utils.py`, `modules/mesh.py`: open3d imported lazily (helps every script, the eval worker too).
  - `scripts/make_lvis_arm_summary.sh`: 3 chains in parallel; the old `<tag>_mesh_views.png` render dropped (v2 does not use it); no re-activation;
    `KEEP_PLAIN=1`, `PRECOMPUTED=1` (both only set by the debug script).
  - `scripts/debug_twostage_instance.sh`: chains in parallel; position colours + ZS + SHIC are built WHILE phase-2 trains; final/SHIC back-projection computed once.
  - Only the end-of-stage-1 + final checkpoints are kept (Tal: stage 1 must stay): `run_lvis_worker.py --stage1_checkpoint` -> train `--save_stageA_end`.
    The 12 step dumps are gone (3.2 -> 1.5 GB per run); `--step_checkpoints` still gives them if a step-progression figure is wanted.
  - Where the 460 s go now: startup ~40, segments 33, features 54, phase-2 212, analysis after training 110 (`compare_ours_vs_shic_points.py` 61 s -- it re-runs SHIC --
    then `render_lvis_markers_2d.py` 34 s). ~40 s more is possible there; below ~7 min needs a faster GPU.
  - **DROPPED (Tal): copying the conda env / weights to the pod's local disk.** One partial test: open3d alone on local disk imports in 15.1-15.9 s vs 15.8 s
    from the network (its dependencies stayed on the network). Env 17 GB + weight caches 12.7 GB vs 29 GB free locally. Do not re-propose without a full-env test.
- **Uncommitted in bsb** (last commit 18f350c; Tal was told, did not ask for a commit): the pod-38/39 lists + M `modules/{utils,mesh}.py`, `phase2/train_relational_loss.py`,
  `analysis/{build_geodesic_tables,build_fine_segments}.py`, `scripts/{run_lvis_worker.py,make_lvis_arm_summary.sh}`;
  NEW `analysis/{lvis_label_check,plot_training_centres,gapfill_preview,prep_amodal_input,merge_amodal_mask}.py`, `scripts/make_amodal_mask.sh`.
  Pre-edit copies `/workspace/archive/*.bak_2026-10-07` (`b`, `c` = later states of the same day). `/workspace/pix2gestalt_repo` is NOT in git (our files there:
  `setup_env.sh`, `run_amodal.py`, `run_lvis_test.py`, `make_test_figure.py`, `stubs/`, `lvis_test/`).
- **Disk added today (45 GB):** `/workspace/pix2gestalt_repo` 22 GB (15.5 GB checkpoint + venv -- KEEP, it is the amodal step); run dirs, free when Tal agrees:
  `data/densepose_lvis/runs_debug/lvis{237843,7107}` (6.9 GB), `runs_debug_merge0.015/` (11 GB), `runs_debug_merge0.015_amodal/` (3.9 GB), `runs_debug_merge0.015_amodal_fillseg/` (1.7 GB).
  The pod-38/39 lists below are still not deleted.
### Still open from earlier pods
Worst-10 list: Tal was going down it by gap vs SHIC (bears 230979 159481 7108 ... not run). Pod 39: stage 1 drawing all 16 neighbours from the whole mask (not answered).
Pods 38/39: leg colouring choice, paper 3.4 step 5, cycle ablation, related-work reading.

## STATE AT POD CLOSE — 2026-10-06 (thirty-ninth pod, 1x RTX A4500 sm_86 20 GB). **NOTHING IS RUNNING.** Tal closes the pod.
**Day = debugging failure cases of the two-stage method (Tal reviews the results himself, continues tomorrow).**
- **Bear 159218 and horse 56069: the damage is done in STAGE 1** (global ellipse) and stage 2 barely changes it. Horse 184389: stage 1 improves the mean but already pushes pt 1 the wrong way. Soft-snap, mean over the instance's 3 points, 1 seed each:
  | instance | ZS | after stage 1 | final | SHIC | what breaks |
  | horse 184389 | 16.7 | 11.3 | 12.5 (scored 13.1) | 9.2 | pt 1 (front leg): 10.8 -> 14.9 -> 20.1 |
  | bear 159218 | 44.8 | 72.8 | 71.7 (scored 78.5) | 14.3 | pt 1: 12.9 -> 85.0; pt 3: 0.0 -> 76.4 |
  | horse 56069 | 10.3 | 41.4 | 39.9 (scored 40.2) | 6.9 | pt 3: 0.0 -> 95.1, never recovered |
- **Two recipe options added, both OFF by default (existing evals unchanged):**
  - `--merge_below_frac F` (`analysis/build_fine_segments.py`, passed by `run_lvis_worker.py`): a segment under F of the mask is absorbed by the
    neighbouring NON-small segment with the longest shared border. Tal: 0.007 first, then 0.015.
  - `--out_neighbors_segmented_only` (train + worker): out-of-segment neighbours are never drawn from mask pixels with no fine segment
    (the 3-5% rim SAM leaves unlabelled). Tal: "the rim is not part of the animal". Centres never came from there.
  | final mean | eval recipe | no rim | no rim + merge 1.5% | SHIC |
  | bear 159218 | 71.7 | 52.9 | 56.3 | 14.3 |
  | horse 56069 | 39.9 | 39.9 | 39.6 | 6.9 |
  Horse 184389 with merge 0.7% only (9 -> 2 segments): 12.9 vs 12.5. Neither option fixes the stage-1 damage.
- **How stage 1 really samples (verified in code + files):** ONE ellipse for all pairs (per-segment rows still 1.0/1.0 at the switch), but neighbours are
  8 from the centre's FINE segment + 8 from outside it, and centres are only pixels with a fine segment. When one segment is 75-87% of the mask,
  the 8 "out" neighbours of most centres come from the remaining 13-25% only. Tal was asked whether stage 1 should draw all 16 from the whole mask -- NOT answered.
- **Horse 184389 front leg** (`analysis/diag_seg_mapping.py --box 162 297 225 296`): leg pixels landing on the mesh leg 61% (ZS) -> 27% -> 6%;
  the whole leg slides UP onto shoulder/chest, same (correct) side. Both front legs are ONE blob in the mask. Hypothesis (untested): the double-width
  2D leg does not fit the thin mesh leg and slides to the wider region. Tal: maybe SAM3 separates the legs (needs its own env, torch 1.12 here).
- **Worst 5 per class by (ours - SHIC)**, from all 132 bears / 133 horses: bear 159218 237843 7107 230979 159481; horse 28284 6054 7995 56069 57711.
  Crops `bsb/demo/shic/worst5_vs_shic/worst5_{bear,horse}.png`.
- **TRAPS found today:** (1) phase-2 must be launched as `phase2/train_relational_loss_l2norm.py`; plain `train_relational_loss.py` fails the resume gate
  (cos 0.839). (2) A matplotlib side view of the mesh must use screen-x = -side*z, else it is MIRRORED and shows the other flank's colours
  (cost one wrong conclusion). Horse mesh: x- = the horse's RIGHT side. (3) Two debug instances in parallel on one GPU = no time saved (~20 min).
### NEXT POD (Tal decides after reviewing)
1. Why stage 1 destroys points that ZS had right (horse 56069 pt 3, bear 159218 pt 1/3). Open question above: 16 neighbours from the whole mask in stage 1?
2. Leg colouring: Tal has not picked between the three (`analysis/leg_colorings.py`: legs4 / legbands / shicstyle).
3. Still open from pod 38: paper 3.4 step 5, cycle ablation, related-work reading (`/workspace/related_work/RELATED_WORK_SEARCH.md`).
- **Tools (new):** `scripts/debug_twostage_instance.sh` (`CLASS= ANN_ID= [MERGE=0.015] [SEGONLY=1]`, ~9 min: rerun with step checkpoints + stage-1 snapshot,
  eval ZS / stage 1 / final, v2 summary vs SHIC, figures) -> `bsb/demo/shic/debug_twostage/<class>_lvis<id>[_merge..][_segonly]/`;
  `analysis/debug_twostage_instance.py`, `analysis/leg_colorings.py`, `analysis/diag_region_on_mesh.py`.
  `train_relational_loss.py` saves `encoder_checkpoint_stageA_end.pth` + `mu_aniso_stageA_end.pth` when step checkpoints are on (`run_lvis_worker.py --step_checkpoints`).
  Horse 184389 figures: `bsb/demo/shic/horse_lvis_vs_shic_twostage/debug_lvis184389/`. Logs `/workspace/logs/debug_lvis184389/`, `/workspace/logs/debug_twostage/`.
- **Uncommitted in bsb** (last commit 18f350c): pod-38 list + M `analysis/build_fine_segments.py`, `modules/relational_loss.py`;
  NEW `analysis/{debug_twostage_instance,diag_region_on_mesh,leg_colorings}.py`, `scripts/debug_twostage_instance.sh`. Pre-edit copies `archive/*.bak_2026-10-06`.
- **Disk to free when Tal agrees (27 GB new today):** `data/densepose_lvis/runs_debug{,_segonly,_merge0.015_segonly}/` (7.6 GB each),
  `runs_horse_twostage_examples/lvis184389/debug_2026-10-06/` (4.3 GB). Plus the pod-38 list below (still not deleted).

## STATE AT POD CLOSE — 2026-10-05 (thirty-eighth pod, 1x RTX 2000 Ada sm_89 16 GB, 10-04 -> 10-05). **NOTHING IS RUNNING.** Tal closes the pod.
**The two days in one list** (details: the section just below):
- **PAPER is in git:** `/workspace/DISC` = clone of `itailang/DISC` (linked to Itai's Overleaf). Pushed b5f111b (method draft v3) and a11109a (Fig. 1: input = image only; mask + parts come out of the SAM box). Tal pulls into Overleaf.
  Mask facts for the text: demos = SAM with a click; LVIS eval = the dataset polygon (SAM only for parts); SHIC is run on the bbox without a mask -> say so in the experiments section.
- **BEAR full eval 132/132, two-stage learned (soft-snap): ours 34.91 | SHIC 32.95 | dir per-seg 33.03 | iso 34.81 | ZS 39.26.** Not better than SHIC or than directional per-seg; the 20-bear 30.50 did not hold.
- **HORSE eval stopped at 133/458 (Tal): ours 22.73 | SHIC 22.60 | ZS 24.09.** Not a random sample.
- **10 example figures per class in the approved v2 layout** (rule in "How Tal wants the assistant to work"): bear `demo/shic/lvis_vs_shic_twostage/v2/` (+ `ALL10_bears.png`), horse `demo/shic/horse_lvis_vs_shic_twostage/` (+ `ALL10_horses.png`).
- **Related-work search opened, not finished:** `/workspace/related_work/RELATED_WORK_SEARCH.md`.
- Tal's table preference (10-05): method + mean error only (soft-snap); no "ours minus it (SE)" / "better on" columns, no argmax, unless asked.
### NEXT POD (Tal, 2026-10-05): study the examples that did NOT work, bears and horses
1. Failure cases to start from. Bear: 159218 (78.5 vs SHIC 14.3, low-res teddy, face points, fragmented back-projection), 55342 (78.2 vs 63.7), 206034 (34.4 vs 19.8), 212408 (19.3 vs 8.9).
   Horse: 181055 (39.3 vs 8.5; one point on the wrong hind leg, looks like a left/right swap), 79982 (26.5 vs 9.9), 195553 (14.4 vs 7.6).
   Their intermediates are KEPT (features, pred_f, segments): `data/densepose_lvis/runs_twostage_examples/` (19 GB) and `runs_horse_twostage_examples/` (16 GB) -> any analysis can run without retraining.
   Per-instance scores for picking more failures: `results_twostage/lvis*.json`, `results_horse_twostage/lvis*.json`; SHIC per instance in `eval_shic_<cls>/results.json` (`bbox.per_instance`).
2. Paper: 3.4 walk-through step 5 still open; cycle ablation; the related-work reading.
3. texlive is per pod: `apt-get install` line as on pod 37 (~5 min), log `logs/texlive_install_pod38.log`. Compile in `/workspace/DISC` with `latexmk -pdf main.tex`.
- **Uncommitted in bsb** (last commit 18f350c): M `analysis/{aggregate_lvis_results,make_lvis_summary_figure}.py`, `phase2/train_relational_loss.py`, `scripts/{make_lvis_arm_summary,run_shicbear_mu_lora}.sh`, `scripts/run_lvis_worker.py`;
  NEW `analysis/{paper_fig_horse,render_lvis_markers_2d}.py`, `scripts/run_lvis_class_queue.sh`. `/workspace/DISC` is clean and pushed. `/workspace/paper` is the OLD copy (superseded by DISC).
- Disk to free when Tal agrees: the two `*_examples` run dirs (35 GB) and `runs_horse_twostage/` (1.6 GB of interrupted leftovers).

## 2026-10-04 / 10-05 (thirty-eighth pod) -- details
- **PAPER IS NOW IN GIT: `git@github.com:itailang/DISC.git` (Itai's repo, linked to his Overleaf project), clone at `/workspace/DISC`** -- this REPLACES `/workspace/paper` as the working copy.
  Tal's key (`talberger`) has push access. Pushed b5f111b (method draft v3: main/macros/preamble/cvpr.sty/bst/bib, `sec/*.tex`, `fig/*.{tex,pdf}`, `.gitignore`) on top of Itai's f8d2666; Tal pulled it into Overleaf and it compiles.
  Sync is MANUAL both ways: Overleaf "Push Overleaf changes to GitHub" -> `git pull` here -> edit -> push `main` -> Overleaf "Pull GitHub changes". Always pull before editing (Itai may have edited).
- **FULL 132-BEAR EVAL of the two-stage learned method (Tal)**, started 14:30 UTC, 1 worker, detached:
  `NUM_GPUS=1 RESULTS=data/densepose_lvis/results_twostage LOGDIR=/workspace/logs/lvis_full_twostage WORKER_ARGS="--mu_scope global_then_segment_aniso --mu_switch_step 150 --mu_lr 5e-2 --runs_dir data/densepose_lvis/runs_twostage" bash scripts/run_lvis_queue.sh`
  (launch with `setsid nohup ... > /workspace/logs/lvis_full_twostage/queue.log`). RESUMABLE: relaunch the same line, scored bears are skipped. 50/132 at 17:06 UTC, 0 errors.
  - The 20 scores of `results_sub20_twostage` were COPIED in (not rescored). mu_lr of that run was not recorded; a smoke test on 113202 with 5e-2 reproduced its step-25 log line to 3 digits -> 5e-2.
    Same bear, same seed, other GPU: final 21.2 here vs 19.1 there -> cross-pod run-to-run noise of ~2 on one bear.
  - **10 example bears** (random seed 0 from the unscored ones: 212408 206043 206034 181519 175388 167910 163066 159218 154548 55342) run by a 2nd worker with `--keep_intermediates`
    (`data/densepose_lvis/runs_twostage_examples/`, ~2 GB each, delete when done) INTO the same results dir. 2 workers on the 16 GB GPU: no OOM, but ~10 min/bear each instead of 5.
    Figures `demo/shic/lvis_vs_shic_twostage/SUMMARY_lvis<id>.png` (all shown to Tal). On these 10: ours soft 37.1 vs SHIC 33.8, 5/5; bear 159218 (low-res teddy, face points) = 78.5 vs 14.3.
  - `scripts/make_lvis_arm_summary.sh` now takes `RUNS=<runs dir>` (default unchanged) and passes `--run_dir`; pre-edit copy `archive/make_lvis_arm_summary.sh.bak_2026-10-04`.
- **FULL HORSE EVAL (Tal), chained to start when the bear queue exits:** `/workspace/logs/lvis_horse_twostage/chain_after_bear.sh` (the env line inside it is the resume command).
  **458 horses / 1337 pts, ~44 h on one GPU** (Tal told; alternatives offered: fixed subset, multi-GPU pod). Results `data/densepose_lvis/results_horse_twostage/`, logs `/workspace/logs/lvis_horse_twostage/`.
  SHIC horse reproduced 23.08. Smoke test horse 164135: soft 6.37 / argmax 7.47 / ZS 13.29 (identical to the 09-29 numbers).
  Code: `run_lvis_worker.py --class_name`, `aggregate_lvis_results.py --class_name`, NEW `scripts/run_lvis_class_queue.sh` (CLASS=...). Pre-edit copies `archive/*.bak_2026-10-04`.
  **TRAP: never edit a queue .sh while it is running -- bash reads it by byte offset** (run_lvis_queue.sh was edited mid-run, restored byte-identical before its `wait` returned).
- **BEAR FINAL 132/132 (two-stage learned, soft-snap, mean over instances): ours 34.91 | SHIC 32.95 (paired +1.96, SE 1.47, ours better 49/132) | dir per-seg 33.03 (+1.87, SE 0.89) | iso 34.81 | ZS 39.26 (-4.35, SE 1.37).**
  Per point 35.01. The 20-bear 30.50 did NOT hold; two-stage is not better than directional per-seg on the bear. `results_twostage/aggregate.json`.
- **HORSE partial (107/458, 10-05 08:55 UTC): ours 24.16 | SHIC 24.20 | ZS 25.84 (-1.68, SE 1.00).** Tal: 10 examples, then the run may be STOPPED (no need to finish).
  10 horse examples (`--keep_intermediates`, `runs_horse_twostage_examples/`): 206474 199065 195553 184389 181055 176532 170401 150964 137258 79982 -> `demo/shic/horse_lvis_vs_shic_twostage/`.
  Horse 42839 FAILED: mask 1784 px < the 2048 centres the recipe samples (no score).
- **HORSE RUN STOPPED by Tal's call at 133/458 (10-05 10:45 UTC): ours 22.73 | SHIC 22.60 | ZS 24.09** (soft-snap, mean over instances; NOT a random sample).
  Resume = the env line in `logs/lvis_horse_twostage/chain_after_bear.sh`. Leftovers of the interrupted instance: `data/densepose_lvis/runs_horse_twostage/` (1.6 GB, not deleted).
  10 horse examples: ours better on 3/10; largest misses 181055 (39.3 vs 8.5) and 79982 (26.5 vs 9.9). Combined images `ALL10_horses.png` there, `v2/ALL10_bears.png` for the bear.
- **RELATED-WORK SEARCH — OPEN, Tal will come back to it: `/workspace/related_work/RELATED_WORK_SEARCH.md`** (+ raw SHIC citation list, json, same folder). Two checks:
  (1) who cites SHIC AND outputs per-pixel 3D/template location; (2) does any paper use a proportion/scale PER SEGMENT like ours.
  State 10-05: lists from ABSTRACTS only, nothing read. Check 1 start: "Emergence of a Shared Canonical Object Frame" 2606.30058, then 2605.28257, Common3D, DINeMo.
  Check 2: nothing found (NOT a novelty claim); start with A-CSM 2004.00614, Shape-of-You 2603.11618, scale/affine-invariant geodesics. Remaining steps are listed in the file.
- v2 example figures: `demo/shic/lvis_vs_shic_twostage/v2/SUMMARY_lvis<id>.png` (layout rule in "How Tal wants the assistant to work"). Pre-edit copy `archive/make_lvis_summary_figure.py.bak_2026-10-05`.

## STATE AT POD CLOSE — 2026-10-04 (thirty-seventh pod, 1x RTX 2000 Ada sm_89 16 GB). **NOTHING IS RUNNING.** Tal closes the pod.
**PAPER day: Tal's first review round on the method draft, all applied.** Latest PDF `paper/review/DISC_v3_2026-10-04.pdf` (4 pages).
- Template verified = official CVPR 2026 kit (`paper_src/author-kit` @ 2917585, still upstream HEAD on 10-04; cvpr.sty/bst/preamble byte-identical). Tal: stay on the 2026 kit, `\confYear{2027}` (set; not printed in draft mode).
- Review workflow that worked: Tal highlights + comments in the PDF, uploads to `paper/review/`; extract with pypdf `/Annots` + `pdftotext -bbox` (word boxes inside each highlight quad). `DISC1.pdf` = 16 annotations.
  Send PDFs back with `SendUserFile` `display: attach` (he downloads them); **show figure changes as images in chat BEFORE putting them in the PDF** (Tal, 10-04).
- Text applied (`sec/3_method.tex`): mask optional via SAM; shorter motivation + symmetric ambiguity; DFD sentence; normalization = geodesic diameter of each domain, SHIC reference removed
  (verified in code: `--geodesic`, `true_diameter_2d`); parts $S_1..S_G$; cycle motivation + "makes the features more distinctive / helps symmetric ambiguity" (Tal's line) with a `\tal{}` todo: **needs the with/without-cycle ablation**.
- Figures (numbering now 1 overview, 2 loss, 3 ellipses, 4 legs), script `bsb/analysis/paper_fig_horse.py` modes `legs | ellipses | loss`:
  - Fig. 1 (Tal approved): 3 rows (shape / image->map / proportions + ONE shared "Losses" block holding L_rel and L_cyc), dashed gradient arrows back to LoRA and to the proportions, box "Soft correspondence" (not "Soft map"). Needs tikz `fit` (added in `macros.tex`).
  - Fig. 2 NEW `fig/horse_loss.pdf` (`loss`): a REAL pixel pair on seg 3; image 0.13, ZS expected geodesic 0.36 (two different legs), ours 0.10.
  - Fig. 3 ellipses + side render of the mesh, tail stub in the tail segment's colour.
  - Fig. 4 legs, `--top softw` (Tal: "we work with soft"): col 1 = image-row colour key, top = soft weight on the correct side (magma; col 2 of diag_seg_mapping.py), bottom = SOFT points (the off-surface bridge), mesh legs grey.
    Mean weight on the correct side: ZS 0.40, per-part only 0.38, two-stage 0.99. Soft-SNAP in the bottom row was tried and rejected: it hides the bridge.
- **Math of 3.4 (Tal walk-through, steps 1, 3, 4 done; step 5 = how s enters the loss / what is learned, still open).** Durable point: `s(u) = sqrt(u^T M u)` is the ellipse's HALF-WIDTH
  (support function) in direction u, NOT its radius; they agree only along the principal axes (major/minor). Never write "s is the radius of the ellipse" in the paper.
- texlive is per pod: `logs/texlive_install_pod37.log` has the apt line (latexmk lmodern texlive-{latex-base,latex-recommended,latex-extra,fonts-recommended,pictures,science,bibtex-extra,plain-generic,lang-greek} poppler-utils), ~5 min.
- Pre-edit copies: `archive/{3_method.tex,overview.tex,paper_fig_horse.py}.bak_2026-10-04`, `archive/paper_fig_bak_2026-10-04/`.
### NEXT POD (Tal decides)
1. Tal reads v3; finish the 3.4 walk-through (step 5); then upload to Itai's Overleaf (list in the 10-01 section, + `fig/horse_loss.{tex,pdf}`) and tell Itai.
2. Cycle ablation (with / without L_cyc) to back the "more distinctive" sentence.
3. Dual RKD leg flip; remaining figure ideas (see the 10-01 list).
- **Uncommitted** (bsb, last commit 18f350c): `phase2/train_relational_loss.py`, `scripts/run_shicbear_mu_lora.sh`, `analysis/paper_fig_horse.py`. `/workspace/paper/` is in no repo and NOT yet on Overleaf.

## STATE AT POD CLOSE — 2026-10-01 (thirty-sixth pod, 1x RTX A4500 sm_86 20 GB). **NOTHING IS RUNNING.** Tal closes the pod.
**The day in one list** (details: the 2026-10-01 section just below):
- **Git:** 2 weeks of code committed + pushed (`analysis` 8e1d5b9, then 18f350c: subset json, manual_mu, demo fig scripts, `workspace_meta/` notes backup).
- **Frozen 1.3 (horse tail):** Tal -- a hand-picked number is not a method; needs a GENERIC rule. Measured: 1.3 does NOT fix the tail's proportion
  (IN ratio 0.44, below learned 0.61); it holds the tail FARTHER from the body (OUT 1.22). Tal checks himself that 1.3 hurt nothing else.
- **PAPER started** (Itai: Overleaf + CVPR '26 kit, method section first). Local draft `/workspace/paper/` -- method v1 + Fig. 1 pipeline (TikZ),
  Fig. 2 per-part ellipses (horse), Fig. 3 two-stage / front leg (horse). Draft mode: no CVPR header, line numbers on, `\author{Itai Lang}`.
  **Not yet uploaded to Itai's Overleaf** (Tal reviews first; corrections by line number in chat or PDF annotations in `/workspace/paper/review/`).
- **bear3 LoRA vs no LoRA** (two-stage, same recipe): no-LoRA cells look MORE regular -> no evidence for a "LoRA improves" figure. Tal to judge.
- **DUAL global + local RKD (Tal's idea)** on the horse: tail stays on the stub (75% vs 29%) but the front leg FLIPS to the wrong side (x+ 99%).
### NEXT POD (Tal decides)
1. Tal's corrections to the method draft -> then upload to Itai's Overleaf project (upload list in the 10-01 section) and tell Itai.
2. Dual RKD: the leg flip -- weights other than 1:1 (more global), or dual only after a global warm-up? Still 1 instance, 1 seed.
3. Remaining figure ideas: directional (bear-132 numbers + a bear visual instead of the guitar), LoRA (only if a fair comparison supports it).
4. texlive must be re-installed on a new pod (apt, see the 10-01 section) to compile the paper locally.
- **Uncommitted** (last commit 18f350c): `phase2/train_relational_loss.py` (dual scope), `scripts/run_shicbear_mu_lora.sh` (NO_LORA, MU=dualaniso),
  NEW `analysis/paper_fig_horse.py`. `/workspace/paper/` is not in any repo. Pre-edit copies `archive/*.bak_2026-10-01`.

## 2026-10-01 (thirty-sixth pod, 1x RTX A4500 sm_86 20 GB)
- Committed + pushed 2 weeks of code: bsb `analysis` 8e1d5b9 -> `github` (code only). Still outside git (ignored): `subset20_bear.json`, 6 `demo/**/make_fig.py`, manual_mu files.
- **Tal on frozen 1.3:** a hand-picked number is NOT acceptable as the method -- it must come from a GENERIC rule (the model must run on any image).
  Rejected: "k x learned global" (k fitted on one horse). Tal checks himself that 1.3 did not hurt anything else.
- **Does 1.3 work by bringing the tail's IN ratio to ~1? NO.** NEW `analysis/diag_seg_pair_ratio.py` (rebuilds the 09-29 pair table; reproduces it: learned snap IN 0.49/0.61, OUT 1.04/1.06).
  Horse 164135 seg 2 (tail), 82 centres x 32 IN + 32 OUT, ratio = norm 3D / norm 2D (mu not applied), json `lvis164135_mu/figures/tail_mapping/pair_ratio_gcircle.json`:
  | reading | IN exp / snap | OUT exp / snap |
  | ZS | 0.25 / 0.12 | 1.12 / 1.12 |
  | learned s150 / s300 | 0.81 / 0.49 , 1.02 / 0.61 | 1.07 / 1.04 , 1.12 / 1.06 |
  | frozen 1.3 s150 / s300 | 0.52 / 0.44 , 0.56 / 0.44 | 1.22 / 1.23 , 1.22 / 1.22 |
  Reading: 1.3 keeps the tail COMPRESSED (IN 0.44, below learned) but holds it FARTHER from the body (OUT 1.22 ~ the scaled target 1.3x).
  The tail stays on the stub because it is pushed AWAY from the body, not because its proportion is matched. Stage B (16/0) has no OUT pairs, so the stage-A OUT distance persists.
  Also: learned "exp" IN reaches 1.02 at s300 while snap is 0.61 -> the expected-geodesic target is met by SPREADING the soft weights, not by moving the tail.
- **PAPER (Itai, 2026-10-01):** Overleaf project "dense_image_shape_correspondence" (Itai's; title "DISC: Dense Image Shape Correspondence"), CVPR '26 author-kit,
  draft the METHOD section first, then tell Itai for a pass. No paid Overleaf -> no git: local copy `/workspace/paper/` (one file per section in `sec/`),
  Tal uploads/pastes into Itai's EXISTING project (do NOT create a new one). Upload: root main.tex macros.tex preamble.tex cvpr.sty ieeenat_fullname.bst main.bib + sec/*.tex + fig/* (create folders first). Before each round, re-download from Overleaf (Itai may have edited).
  **Tal: the BSB paper (arXiv 2605.18193, source in `/workspace/paper_src/bsb_paper/`) is ONLY a reference for look/length -- do not copy its structure or wording.**
  texlive is apt-installed per pod (ephemeral): log `/workspace/logs/texlive_install.log`.
  Method draft v1 in `/workspace/paper/sec/3_method.tex` (Tal: no anchor/L_dist; two-stage learned mu; no frozen 1.3; DFD as a short cited paragraph).
  Draft mode: `[pagenumbers]` + lineno (no CVPR header), `\author{Itai Lang}`. Tal reviews via line numbers in chat or PDF annotations in `/workspace/paper/review/`.
  Figures: `fig/overview.tex` (TikZ block diagram), `fig/horse_ellipses.pdf` + `fig/horse_legs.pdf` from NEW `bsb/analysis/paper_fig_horse.py` (legs: ZS / dir per-seg / two-stage, seg 3).
  Tal asked for a guitar dir-per-seg figure and a bear LoRA with/without figure -- flagged: guitar gain is mostly LoRA (iso+LoRA 91.2, dir+LoRA 92.1, MAIN 89.4) and
  two-stage is 88.6 on the guitar; directional is better supported by the 132-bear eval (#2 vs #1: -1.78 +- 0.75 SE). LoRA: 2-instance check had no-LoRA winning 3/4.
- A 20-bear no-LoRA eval was launched by mistake and stopped; its results/logs/intermediates were DELETED (Tal). Tal wants the LoRA comparison on bear3 ONLY.
- **BEAR3 LoRA ABLATION (Tal, 2026-10-01):** NEW `NO_LORA=1` in `scripts/run_shicbear_mu_lora.sh` (full fine-tune, no alpha; pre-edit copy `archive/run_shicbear_mu_lora.sh.bak_2026-10-01`).
  Run two-stage learned (`MU=globalthenaniso MU_LR=5e-2 NIN=8 NOUT=8 SUFFIX=_mulr5e-2_in8out8_sw150 NO_LORA=1`), log `logs/bear3_globalthenaniso_sw150_nolora.log`, drift 0.857.
  Figure `bsb/demo/shic/comparison_bear3_lora_vs_nolora/bear3_twostage_lora_vs_nolora.png` (SHIC / LoRA a0.5 / no LoRA). Visually the no-LoRA cells look MORE regular (as on LVIS 09-20). Tal judges.
- **DUAL GLOBAL + LOCAL RKD (Tal's idea, 2026-10-01):** NEW `--mu_scope dual_global_local_aniso` (alias `dual_global_segment_aniso`) + `--dual_local_nin`;
  `MU=dualaniso DUAL_NIN=16` in run_shicbear_mu_lora.sh. Every step: GLOBAL term 8 in + 8 out with ONE shared ellipse (last row) AND LOCAL term 16 in with
  per-seg ellipses, one Huber mean -> 1:1. Pre-edit copy `archive/train_relational_loss.py.bak_2026-10-01`. Log `logs/horse164135_dual_g8in8out_l16.log`.
  | horse 164135 | seg 3 leg | tail on stub (soft-snap) | tail IN ratio snap | inst soft/argmax (3 pts) |
  | two-stage learned | x- 100% (correct), mixed 1.7% | 28.6% | 0.61 | 6.37 / 7.47 |
  | **dual 1:1** | **x+ 99% (WRONG side)**, mixed 4.3% | **75.2%** | 0.25 (compressed) | 5.55 / 5.55 |
  Global ellipse 0.97/0.84 @48; per-seg ellipses DO differ from it (tail 1.70/0.88), so the local term is not inert. Tail held but compressed, leg flipped.
  Figures `bsb/demo/shic/lvis164135_mu/figures/dual_global_local/{backproj_twostage_vs_dual.png, seg3_mapping.png, tail.png, tail_pair_ratio.json}`. 1 instance, 1 seed.

## STATE AT POD CLOSE — 2026-09-29 (thirty-fifth pod, 1x RTX 4000 Ada sm_89 20 GB). **NOTHING IS RUNNING.** Tal closes the pod.
**The day in one list** (details: the 2026-09-29 section just below):
- **20-BEAR EVAL, two-stage LEARNED (A global 8/8 -> B per-seg 16/0, LoRA all, alpha 0.5): soft 30.50 / argmax 32.91 vs SHIC 33.84 on the same 20**
  (paired -3.34 +- 2.56 SE; #2 dir per-seg 33.20, #1 iso 35.48, ZS 39.30). First run below SHIC; not significant on n=20.
  Fixed subset `data/densepose_lvis/subset20_bear.json` (representative of the 129) -- use it for every subset eval.
- **Tail study (horse 164135):** ZS puts the whole tail on the mesh stub (collapsed); training pulls ~88% onto the RUMP (right buttock) already in stage A.
  Cause (measured): in-seg tail pairs want 0.057 but the stub holds ~0.032 -> they stretch onto the rump. `analysis/diag_tail_mapping.py` (soft-snap).
- **What holds the tail:** stage-A global FROZEN circle **1.3** (tail 91% on stub, leg correct, inst 5.58/6.96) -- the only arm good on both.
  LoRA `last` (tail 77%) and alpha 0.3 (12%) trade it against the leg bridge (mixed 55% / 46%). 0.7 circle, 12/4, 4/12, manual ellipses, hybrid: no.
- **Leg flip explained:** a frozen PCA-manual global (1.09/0.92) flips seg 3 to x+ at step 150; a frozen mu=1 circle does not -> shape, not freezing.
- LoRA was ALREADY all layers everywhere (Tal thought last-only). bear3 learned global = 0.77/0.56 (horse ~0.97) -> scale is image-dependent.
### NEXT POD (Tal decides)
1. Full 132-bear eval of two-stage learned (~10.5 h on 1 GPU) to confirm the 30.50 vs SHIC trend, and/or the 20-bear eval of the **frozen-1.3** arm (~1.6 h).
2. Frozen 1.3 on bear3 / guitar: does a fixed stage-A scale transfer (bear's learned global is 0.77/0.56)? Maybe a scale RELATIVE to the learned one.
3. Tail with a generic fix (Tal's principle: extremities anchor, proportion pays in the body).
- **Uncommitted** (last commit 16e5b3d, 2026-09-15): today `phase2/train_relational_loss.py` (`--stageA_fixed`, `--mu_fix_seg_circle`, `--stageA_fixed_circle`),
  `scripts/run_shicbear_mu_lora.sh` (STAGEA_FIXED, FIX_SEG, GCIRCLE, LORA_LAYERS), `scripts/run_lvis_worker.py` (global_then_segment_aniso), NEW `analysis/diag_tail_mapping.py`.
  Pre-edit copies `archive/*.bak_2026-09-29{,b,c}`.
- `train_relational_loss.py -h` crashes on an old help string containing `%` (parsing works). SendUserFile returned 500 for ~1 h today, then recovered.

## STATE AT POD CLOSE — 2026-09-28 (thirty-fourth pod, 1x RTX 2000 Ada sm_89 16 GB). **NOTHING IS RUNNING** (all 8 queued runs DONE, last 16:08). Entry written 2026-09-29 (pod 35) -- it was missing.
**The day in one list** (details in the three 09-28 sections just below):
- **SHIC baseline input = `bbox`, no mask. FINAL** (reproduces Table 1: bear 33.09 vs 33.0).
- **"Leg Collision"** named; 7-run comparison on horse 164135 seg 3: cross-seg pairs (global 8/8, two-stage sw150) put the leg on the right side.
- **Manual (PCA shape-matched) ellipses, frozen:** horse -- no gain for two-stage; **hybrid + manual best on the horse** (seg 3 mixed 31% -> 4%, inst 6.04/6.14).
  Guitar -- manual HURTS: two-stage manual B 86.2/84.0/84.4, two-stage + hybrid-B manual 82.2/81.1/80.7 (worst) vs learned two-stage 88.6/88.5/86.9,
  **best still dir per-seg + LoRA 92.1/91.5/89.5**. Bear3 manual B: visual only.
- **Guitar read-time alpha sweep:** more LoRA (0.5 -> 0.75 -> 1) hurts monotonically, -2..-4 per step. Keep alpha 0.5.
- The first alpha-sweep log has a failed manual-B alpha 1.0 (`no such pred_f`); redone in `guitar_twostage_alpha_sweep2.log` -- numbers above are complete.
### NEXT POD (Tal decides)
1. Two-stage tuning (still open from 09-27): earlier switch (50/75) and/or 12 in + 4 out in stage A -- keep the horse fix, cut the guitar cost.
2. Second seed + more LVIS horses for the leg fix (still 1 instance, 1 seed for EVERY horse number).
3. LoRA lr / rank at TRAIN time (read-time alpha is exhausted).
4. Manual ellipses: shape-matching did not help -> "the ellipse does not align with the part" is probably not what limits the mapping. Tal to decide whether to drop it.
- **Uncommitted** (last commit 16e5b3d, 2026-09-15 -- two weeks of work is uncommitted): changed today `phase2/train_relational_loss.py`
  (`--mu_aniso_fixed_path`, `--switch_hybrid`), `scripts/run_shicbear_mu_lora.sh` (MU_FIXED, SWITCH_HYBRID), `scripts/run_isobbox_mu_loraW.sh`,
  `analysis/{diag_seg_mapping,plot_mu_annotated}.py`, NEW `analysis/make_manual_mu_aniso.py`. `git status` in bsb shows 8 modified + ~34 untracked.

## 2026-09-29 (thirty-fifth pod, 1x RTX 4000 Ada sm_89)
- **Two-stage with MANUAL stage A (Tal):** NEW `--stageA_fixed` (`STAGEA_FIXED=1` + `SWITCH_HYBRID=1` + `MU_FIXED=<file with global row>` in run_shicbear_mu_lora.sh):
  the manual file is loaded + frozen from step 0 (hook + lr 0), stage A = manual global row (1.09/0.92 @56), stage B = hybrid manual. Verified frozen.
  Pre-edit copies `archive/{train_relational_loss.py,run_shicbear_mu_lora.sh}.bak_2026-09-29`. Log `logs/horse164135_globalthenaniso_sw150_hybridB_manualB_stageAfixed.log`.
  **RESULT horse 164135 seg 3: WRONG leg -- x- 2% / x+ 98%, mixed 7%** (vs learned stage A 100% x-, 4.4%; hybrid manual from 0 100% x-, 3.9%). Inst 6.23/6.23 (3 pts, noise).
  Reading: the near-circular manual global ellipse does not separate the legs in stage A; the LEARNED global ellipse does. 1 instance, 1 seed.
  Figures `demo/shic/lvis164135_mu/figures/manual_ellipses_B/{backproj_stageAfixed.png, seg3_mapping_stageAfixed_alpha0.5.{png,json}}`.
- **WHEN does it go wrong? At the END OF STAGE A already** (checkpoint step 150 exported at alpha 0.5 -> `<run>/step150_alpha/`):
  learned global x- 100% / mixed 9%; manual global x+ 99% / mixed 5%. Stage B only keeps the side. ZS starts 63/37 -> the side is a tipping point.
  Figure `demo/shic/lvis164135_mu/figures/manual_ellipses_B/seg3_mapping_step150_alpha0.5.{png,json}`.
- Timing (horse LVIS, this GPU): training ~5 min, the LVIS analysis ~11 min.
- **RULE (Tal, 2026-09-29): GLOBAL mu training is ALWAYS cross-segment** (in + out neighbours, e.g. 8/8). Never run a global stage with 16/0.
- Manual variant `manual_mu/pow0.5_size1_seg2circ0.7` = manual B with seg 2 (TAIL, tiny in 3D) replaced by a circle 0.7/0.7 (was 1.43/0.70 @32.5).
  Figure `lvis164135_mu/figures/manual_ellipses_B/ellipses_manualB_seg2circ0.7.png`.
  **RUN** two-stage sw150 (A learned global 8/8, B manual per-seg 16/0) with this file: log `logs/horse164135_globalthenaniso_sw150_manualB_seg2circ0.7.log`.
  Seg 3 x- 98%, mixed 0% (manual B 99%/7%); inst soft/argmax 6.37/8.03 (manual B 7.10/8.09). Tail: visibly fewer, larger cells (Tal to judge).
  Figure `manual_ellipses_B/backproj_seg2circ.png`. (diag_seg_mapping on seg 2 is useless: the tail is not a leg class -> 100% body/head.)
- **Stage-A global ellipses compared** (`lvis164135_mu/figures/stageA_global_ellipses/`): learned@150 1.00/0.94 @53, manual 1.09/0.92 @56, iso 1/1.
  Near-identical, yet:
- **FROZEN-CIRCLE TEST (stage A = all rows mu=1 circle, frozen, 8/8; `manual_mu/circle1_all_xglobal`, log `logs/horse164135_globalthenaniso_sw150_stageAfixed_circle1.log`):
  seg 3 at step 150 -> x- 100%, mixed 2% = CORRECT.** So freezing is NOT the cause; the manual global's small elongation (1.19 @56) flips the leg to x+.
  The side choice is very sensitive to the shared ellipse. Figure `stageA_global_ellipses/seg3_step150_learned_manual_circle1.png`.
- **Tal: best so far = two-stage LEARNED sw150** (A global 8/8, B per-seg 16/0; `globalthenaniso_sw150`). Horse seg 3 100%/1.7% mixed; inst 6.37/7.47
  (3 pts, cannot rank); guitar 88.6 < dir per-seg 92.1. Figures `lvis164135_mu/figures/twostage_learned/`.
- **Tail fixed 2.5 on top of it:** NEW `--mu_fix_seg_circle SEG:VALUE` (`FIX_SEG="2:2.5"`): at the switch that row = circle, frozen; the rest learned.
  Pre-edit copies `archive/*.bak_2026-09-29b`. Log `logs/horse164135_globalthenaniso_sw150_tail2.5.log`. Seg 3 100%/2.5% mixed; inst 6.53/6.53.
  Visual: tail -> fewer, larger cells (big brown) vs learned tail 2.23/1.26. Figures `twostage_learned/{backproj,ellipses}_tail2.5.png`.
- **TAIL MAPPING STUDY (Tal, 2026-09-29; recipe = two-stage LEARNED sw150, no manual).** NEW `analysis/diag_tail_mapping.py` (side + rear views,
  pixels coloured root->tip, argmax mesh region: tail stub z<-0.66 |x|<0.03 0<y<0.3 (31 v) / rump / legs / body). Figure `lvis164135_mu/figures/tail_mapping/tail_ZS_stage1_stage2.png`.
  | reading | tail stub / rump | soft std (x,y,z) | corr(root->tip, soft y) |
  | ZS | 100 / 0 | .001/.011/.007 (COLLAPSED to ~4 vertices) | -0.87 |
  | step 150 | 46 / 54 | .025/.044/.032 | -0.92 |
  | step 300 | 62 / 38 | .028/.059/.040 | -0.97 |
  Reading: ZS puts the whole tail on the stub but as ONE point. Training stretches it in order, but the ROOT half goes UP onto the top of the rump,
  OFF-centre to x+ (mean x 0.04-0.05, the right buttock), the tip onto the stub. The mesh tail is too short to hold a long image tail.
  **SOFT-SNAP (what training reads; column 2 now soft-snap, argmax in json):** stub/rump ZS 100/0 (9 vertices) -> step 150 **11.5/88.5** -> step 300 28.6/71.4.
  **Centres/neighbours:** 82 of 2048 centres on the tail (tail = 4.1% of pixels). A tail centre's 8 OUT neighbours: 90% body seg 1.
  **2D target vs 3D (normalized, median over 82 centres x 64 pairs, soft-snap):**
  | pairs | 2D target | ZS 3D (ratio) | step150 3D (ratio) | step300 3D (ratio) |
  | IN tail-tail | 0.057 | 0.008 (0.11) | 0.028 (0.49) | 0.036 (0.60) |
  | OUT tail-body | 0.382 | 0.443 (1.13) | 0.391 (1.04) | 0.395 (1.07) |
  Mechanism: ZS collapses the tail (in-seg 9x too short) and puts it too FAR from the body (1.13). Stage 1 fixes both by pulling the tail
  toward the body AND spreading it -> onto the rump. The tail's IN pairs still only reach 0.49-0.60 of the target.
- **TAL'S PRINCIPLE (2026-09-29):** extremities (tail, head, legs) should act as ANCHORS; the learned proportion should pay the mismatch
  (photo horse != mesh horse) in the belly/body, not by moving the tail onto the rump. Fixes must be GENERIC (bear, guitar), not tail-specific.
  Rejected today: per-seg mu for the tail (leg-flip risk), a tail-only regional anchor (not generic).
- **Stage-A neighbour mix (stage B 16/0, all learned)**, logs `logs/horse164135_globalthenaniso_sw150_in{12out4,4out12}.log`, figs `tail_mapping/{tail,seg3}_nin_nout.png`.
  Tail soft-snap on stub, step150 -> 300: 8/8 11.5 -> 28.6 | 12/4 12.9 -> 7.6 | 4/12 13.7 -> 26.3. Seg 3: 8/8 correct | **12/4 WRONG leg (100% x+)** | 4/12 correct.
  -> neighbour mix does not hold the tail; fewer out pairs flips the leg again.
- ~~mu DIRECTION: larger mu = more 3D spread, so "compressed" = mu < 1~~ **WRONG in practice (assistant's code reading; Tal's intuition was right).**
  **STAGE-A GLOBAL FROZEN CIRCLE (Tal, 2026-09-29):** NEW `--stageA_fixed_circle X` (`GCIRCLE=X`): global row frozen to circle X in stage A, stage-B per-seg
  rows start from X and LEARN. Pre-edit copies `archive/*.bak_2026-09-29c`. Logs `logs/horse164135_globalthenaniso_sw150_gcircle{0.7,1.3}.log`.
  | stage A global | tail on stub, soft-snap, s150 -> s300 | seg 3 (s300) | inst soft/argmax |
  | learned (~0.97) | 11.5 -> 28.6 (rump 71) | x- 100, mixed 1.7 | 6.37/7.47 |
  | frozen 0.7 | 0 -> 0 (88% on the BODY flank) | **WRONG x+ 86** | 11.16/9.27 |
  | **frozen 1.3** | **96.8 -> 91.2** | **x- 100, mixed 0.2** | **5.58/6.96** |
- **Read-time alpha 0.3 (EXPERIMENT only, not the recipe; two-stage learned horse):** tail on stub s150 11.9 / s300 11.9 (alpha 0.5: 11.5 / 28.6);
  seg 3 x- 97%, **mixed 46%** (alpha 0.5: 1.7%). -> weaker LoRA does NOT keep the tail, and brings the leg bridge back. Fig `tail_mapping/tail_alpha03.png`.
- **LoRA layers: the recipe ALREADY trains ALL mlp layers** ([1,4,7,10,13,16], `--lora_w_layers all`, confirmed in the logs). Tal believed it was last-only.
- **LoRA LAST layer only, two-stage learned horse** (`LORA_LAYERS=last` in run_shicbear_mu_lora.sh; log `logs/horse164135_globalthenaniso_sw150_loraLast.log`):
  tail on stub s150 **76.0** / s300 **76.8** (ALL: 11.5 / 28.6); seg 3 x- 77%, x+ 23%, **mixed 55%** (ALL: 100%, 1.7%).
  -> fewer LoRA layers keep the tail but bring back the leg bridge (same trade as alpha 0.3). Fig `tail_mapping/tail_lora_last_vs_all.png`.
- **20-BEAR EVAL DONE (two-stage learned, LoRA all, alpha 0.5; 60 pts, 0 failures, ~4.8 min/instance):** `data/densepose_lvis/results_sub20_twostage/aggregate.json`
  | on the SAME 20 | soft |  | paired NEW - X (SE) | NEW better on |
  | **NEW two-stage** | **30.50** (argmax 32.91) | | | |
  | SHIC (bbox) | 33.84 | | -3.34 (2.56) | 12/20 |
  | #2 dir per-seg | 33.20 | | -2.70 (2.39) | 11/20 |
  | #1 iso per-seg | 35.48 | | -4.97 (2.64) | 10/20 |
  | ZS | 39.30 | | -8.80 (2.99) | 13/20 |
  First number BELOW SHIC, but every gap except ZS is < 2 SE -> promising, NOT significant on n=20.
- **BEAR3 two-stage LEARNED sw150** (log `logs/bear3_globalthenaniso_sw150.log`): runs clean, visual only (`demo/shic/bear3_..._in8out8_sw150_phase2/alpha0.5/comparison_vs_shic/`).
  Learned global at the switch = 0.77/0.56 on the bear (horse ~0.97) -> the global mu scale is image-dependent; a fixed 1.3 may not transfer.
- **BEAR EVAL SUBSET (Tal, 2026-09-29): 20 FIXED instances** `data/densepose_lvis/subset20_bear.json` -- SHIC-error-stratified, draw chosen so
  SHIC / ours#1 / ours#2 / ZS means match the full 129 within 0.5 (subset 33.84/35.48/33.20/39.30 vs full 33.38/35.07/33.30/39.36). Use for ALL subset evals.
  `scripts/run_lvis_worker.py` now takes `--mu_scope global_then_segment_aniso [--mu_switch_step 150]` (A 8/8, B 16/0). Pre-edit copy `archive/run_lvis_worker.py.bak_2026-09-29`.
  **1.3 keeps the tail on the tail AND the leg correct -- best horse run so far (1 instance, 1 seed).** Figs `tail_mapping/{tail_gcircle,backproj_gcircle,seg3_gcircle*}.png`.
- **Tail in the learned HYBRID** (`anisoxglobal_in8out8`, single stage): stub ZS 100 -> step150 16.3 -> step300 **3.8** (rump 96%), mean x 0.06 (right buttock).
  Same failure, worse at the end. Fig `tail_mapping/tail_hybrid_learned.png`. -> not specific to the two-stage schedule.
- **CONCLUSION (agreed with Tal, 2026-09-29): keep the stage-A global mu LEARNED (or at least never PCA-built).** Reason: the PCA manual
  global HURT (flipped the leg); freezing itself did NOT (frozen circle = correct). Do NOT quote this as "global mu must be learned". 1 instance, 1 seed.
- Tail variant 2: `manual_mu/pow0.5_size1_seg2circ1.5` (seg 2 = circle 1.5). Figure `manual_ellipses_B/ellipses_manualB_seg2circ1.5.png`.
  RUN (same recipe), log `logs/horse164135_globalthenaniso_sw150_manualB_seg2circ1.5.log`: seg 3 x- 99%, mixed 7%; inst 6.37/8.03.
  Tail: more cells (like manual B); 0.7 gave fewer, larger cells. Figure `manual_ellipses_B/backproj_tail_variants.png` (manual B | 0.7 | 1.5). Tal judges.

## DECISION — SHIC BASELINE INPUT VARIANT (Tal, 2026-09-28, thirty-fourth pod). **FINAL, do not re-open.**
- SHIC full eval (`analysis/eval_densepose_lvis.py`) was run in 3 input variants: **bbox** (crop to bbox, resize 224x224, aspect distorted, NO mask) |
  square (square crop, zero-pad) | square_mask (square + black bg). Bear 33.09 / 33.18 / 35.70 (paper 33.0); horse 23.08 / 23.16 / 24.86.
- **CHOSEN: `bbox`, no mask -- crop, then resize.** Reason: it is the variant that reproduces SHIC's Table 1 (33.09 vs 33.0); Tal does not want
  to add changes of our own to the baseline. Report SHIC numbers with this variant only; the other two are not used.
- Nuance (so it is not mis-quoted): the SHIC paper does not state its eval input; the released notebook feeds an RGBA cutout. "bbox, no mask" is the
  choice that MATCHES their published number, not a stated protocol. Our own method still uses the LVIS mask (see HONEST DIFFERENCES vs SHIC).

## LEG COLLISION — 7-run comparison, horse 164135 seg 3 (2026-09-28, analysis only, alpha 0.5)
**Name (Tal, 2026-09-28): "Leg Collision"** = two image legs with near-identical features land on the SAME mesh leg (or bridge between legs).
Figures `bsb/demo/shic/lvis164135_mu/figures/leg_collision_compare/{backproj_7runs_alpha0.5.png (make_backproj_fig.py), seg3_mapping_7runs_alpha0.5.{png,json}}`, mu_ellipses_6runs.png}` (backproj grid incl. SHIC argmax). Tools changed today: `diag_seg_mapping.py --fs` (font; wraps titles),
`plot_mu_annotated.py --ncols --fs` + handles global_aniso (one magenta ellipse); cross-seg/global ellipse now drawn top-centre. Pre-edit copies `archive/*.bak_2026-09-28`.
NEW ZS back-proj `lvis164135_mu/ZS_phase1/`. Seg 3 (correct leg = front x-), % px argmax x- / x+ / mixed(>10% both) / soft pts |x|<0.07:
| run | x- | x+ | mixed | between |
|---|---|---|---|---|
| ZS (phase-1) | 37 | 63 | 61 | 40 |
| iso per-seg | 40 | 60 | 30 | 25 |
| dir global 16in/0out | 4 | 96 | 6 | 5 |
| **dir global 8in/8out** | **100** | 0 | **0** | 2 |
| dir per-seg | 43 | 57 | 29 | 26 |
| hybrid 8/8 | 99.5 | 0.5 | 31 | 34 |
| **two-stage sw150** | **100** | 0 | **2** | 0.5 |
Reading: per-seg mu (iso or dir) keeps phase-1's bridge; shared mu without cross-seg -> consistent but WRONG leg; cross-seg pairs -> right leg;
hybrid right leg but lower half fans out; two-stage ~ global 8/8 on the leg. 1 instance, 1 seed.

## MANUAL ELLIPSES experiment (Tal, 2026-09-28): "if the ellipses matched the part's shape, would the mapping improve?"
- NEW `analysis/make_manual_mu_aniso.py`: per fine segment, PCA of its pixels -> major axis along the segment; ratio sqrt(l1/l2)^power;
  size sqrt(major*minor) = iso mu or a number. Variants in `bsb/demo/shic/lvis164135_mu/manual_mu/` (figure `figures/leg_collision_compare/mu_manual_ellipses.png`).
  **Tal chose B = power 0.5, size 1** (seg 3: 1.64 along / 0.61 across, 2 deg = along the leg). A (size from iso) blew seg 3 up to 4.98.
- NEW flag `--mu_aniso_fixed_path` (train_relational_loss.py; `MU_FIXED=` in run_shicbear_mu_lora.sh, globalthenaniso only): at the switch the
  stage-B segment rows are LOADED and FROZEN (grad hook; verified saved == manual, max diff 0). Pre-edit copy `archive/train_relational_loss.py.bak_2026-09-28`.
- Run: horse 164135 two-stage sw150, 8/8 -> 16/0, manual B. Log `/workspace/logs/horse164135_globalthenaniso_sw150_manualB.log`. Figures `lvis164135_mu/figures/manual_ellipses_B/`.
  **RESULT (seg 3, alpha 0.5):** leg still on the right leg (x- 99%, body 1%), mixed 7% (learned two-stage 2%); the hoof end (centres ~69-78) fans
  toward the middle. Instance soft/argmax 7.10/8.09 vs learned two-stage 6.37/7.47 (SHIC 7.37; 3 GT pts = noise). **No visible gain from shape-matched ellipses
  on this leg; 1 instance, 1 seed.**
- **Manual C + HYBRID manual (2026-09-28).** `--mu_aniso_fixed_path` now also works for `segment_aniso_xglobal`: ALL rows (segments + the global
  cross-seg row) frozen from step 0; `make_manual_mu_aniso.py --add_global` appends a global row = PCA of all object pixels (horse: 1.09/0.92 @56).
  Verified frozen (diff 0). Figures `lvis164135_mu/figures/manual_ellipses_B/{backproj_all.png, seg3_mapping_5runs_alpha0.5.png, ellipses_5runs.png}`.
  | seg 3, alpha 0.5 | x- | body | mixed | inst soft/argmax |
  |---|---|---|---|---|
  | two-stage learned | 100 | 0 | 2 | 6.37/7.47 |
  | two-stage manual B | 99 | 1 | 7 | 7.10/8.09 |
  | two-stage manual C | 92 | 8 | 0 | 6.78/8.03 |
  | hybrid learned | 99.5 | 0 | 31 | 6.37/6.37 |
  | **hybrid manual B + manual global** | **100** | 0 | **4** | **6.04/6.14** |
  Hybrid + manual removes the hybrid's lower-leg fan (31% -> 4% mixed) and has the best instance numbers (3 pts, noise). C: top of the leg drifts to body (8%).
- **TWO-STAGE with a HYBRID stage B (Tal, 2026-09-28):** NEW `--switch_hybrid` (`SWITCH_HYBRID=1` in run_shicbear_mu_lora.sh -> stage B 8 in + 8 out).
  Stage A = learned global + 8/8 (as before); at step 150 the FULL manual file (segments + global row, `manual_mu/pow0.5_size1_xglobal`) is loaded and
  ALL rows frozen (grad hook + that param group's lr -> 0, since the global row has Adam moments from stage A). Verified diff 0. Pre-edit copy `archive/train_relational_loss.py.bak_2026-09-28b`.
  Horse 164135 (log `logs/horse164135_globalthenaniso_sw150_hybridB_manualB.log`): seg 3 x- 100%, mixed 4.4%; instance soft/argmax 6.14/8.72.
  => on seg 3 same as hybrid+manual from step 0 (100%, 4%).
  GUITAR two-stage + HYBRID stage B + manual (global row 1.29/0.78 @32): **82.2/81.1/80.7** -- the worst guitar arm so far (learned two-stage 88.6/88.5/86.9,
  two-stage manual 86.2/84.0/84.4). Cross-seg pairs in stage B cost the guitar again (as global 8/8 did, 85.8). Log `logs/guitar_globalthenaniso_sw150_hybridB_manualB.log`,
  figure `demo/guitar/runs/isobbox_prop/comparison_mu_loraW/guitar_twostage_hybridB_backproj.png`. Figures `lvis164135_mu/figures/manual_ellipses_B/{backproj_hybridB.png, seg3_mapping_6runs_alpha0.5.png}`.
- **GUITAR alpha sweep (Tal 2026-09-28, "weaken the anchor = strengthen LoRA"; READ-TIME alpha only, no retraining)**, eval v2 snap/argmax/soft:
  two-stage LEARNED a0.5 88.6/88.5/86.9 | a0.75 86.0/85.3/84.4 | a1 82.3/82.0/81.2 ; two-stage MANUAL a0.5 86.2/84.0/84.4 | a0.75 82.2/79.2/80.3 | a1 78.8/77.1/77.0.
  **More LoRA at read time hurts monotonically (-2..-4 per step), both arms.** Log `logs/guitar_twostage_alpha_sweep{,2}.log`. Not yet tried: LoRA lr / rank at TRAIN time.
- QUEUED (same day): guitar two-stage + manual B (`logs/guitar_globalthenaniso_sw150_manualB.log`), bear3 two-stage + manual B (`logs/bear3_globalthenaniso_sw150_manualB.log`).
  bear3 has NO learned two-stage run to compare against.
  **RESULTS:** GUITAR two-stage + manual B eval v2 snap/argmax/soft **86.2/84.0/84.4** vs two-stage learned 88.6/88.5/86.9, dir per-seg 92.1/91.5/89.5
  -> manual ellipses HURT the guitar (-2..-4; neck seg 4 manual 1.69/0.59 @31.5deg). Figures `demo/guitar/runs/isobbox_prop/comparison_mu_loraW/guitar_{twostage_manualB_backproj,ellipses_learned_vs_manualB}.png`.
  BEAR3 two-stage + manual B: visual only (`demo/shic/comparison_bear3_manualB/bear3_backproj.png`, vs iso per-seg + LoRA); bear3 manual ellipses are near-circles (ratio 1.3-1.5).

## STATE AT POD CLOSE — 2026-09-27 (thirty-third pod, 1x RTX 2000 Ada sm_89 16 GB, RAM 251 GB). **NOTHING IS RUNNING.** Tal closes the pod. Disk 281 G.
**The day in one list** (details: the bullets appended under the 09-24 state entry just below):
- **Diag figures now read the PRODUCTION reading, alpha 0.5** (`--pred_rel`, default). The 09-24 figure was full LoRA (alpha 1); same picture.
- **mu_scope never changes neighbour sampling** -- global_aniso still samples in-segment. Tal assumed otherwise; clarified.
- **LESSON: OUT-OF-SEGMENT pairs are what separate symmetric parts.** Horse, global_aniso 8 in + 8 out: seg 3 moves to the RIGHT leg (100% x-, 0% mixed).
  Before, BOTH image front legs landed on mesh x+ (a collision, not a mirror flip). Hind legs were already split in every run. 1 instance, 1 seed.
- **Two new mu scopes:** `segment_aniso_xglobal` (hybrid: per-seg ellipse for in-seg pairs, one global ellipse for cross-seg pairs) and
  `global_then_segment_aniso --mu_switch_step N` (two-stage: global + 8/8 neighbours until N, then per-seg ellipses init from the global one + 16/0).
- **Horse 164135 (seg 3 mixed / leg side):** dir per-seg 29% split | global 8/8 0% right | hybrid 31% right | **two-stage sw150 1.7% right**.
  Two-stage seg-3 ellipse 1.12/0.81 @120 (dir per-seg 6.91/2.94 @91) -- no longer absorbs the error, still NOT along the leg.
- **Guitar with LORA-W (eval v2 snap/argmax/soft), MAIN 89.4/89.0/88.0:** iso+LoRA 91.2/91.3/89.0 | **dir per-seg+LoRA 92.1/91.5/89.5 (best)** |
  two-stage 88.6/88.5/86.9 | hybrid 86.5/86.0/84.9 | global 8/8 85.8/85.5/84.4 (worst). **LoRA gives most of the gain; cross-seg pairs COST the guitar ~6 pts
  and it has no symmetry to fix.** Two-stage recovers ~3.
- New tools: `analysis/plot_mu_annotated.py` (per-seg "along X / across Y" callouts; iso panel = one mu per segment) -- Tal's preferred mu view;
  `analysis/mu_table.py`; `analysis/export_seg_mapping_ply.py`; `diag_seg_mapping.py --box/--name/--pred_rel` + numbered-centres column.
- Comparison figures: ONE shared 3D render, then only the back-projection halves (Tal).
### NEXT POD (Tal decides)
1. Two-stage tuning: earlier switch (50/75) and/or fewer cross-seg pairs in stage A (12 in + 4 out) -- keep the horse fix, reduce the guitar cost.
2. A second seed for the horse leg fix (two-stage, global 8/8) before trusting it; more LVIS horses (only 1 instance so far).
3. Still open: why the per-seg ellipse does not align WITH the part (horse leg; guitar neck only weakly, 1.28/0.99 @19 vs neck ~30deg).
- **Uncommitted, new/changed today:** `phase2/train_relational_loss.py` (global_aniso out-seg allowed, `segment_aniso_xglobal`, `global_then_segment_aniso`,
  `--mu_switch_step/--switch_nin/--switch_nout`; pre-edit copy `archive/train_relational_loss.py.bak_2026-09-27`), `scripts/run_shicbear_mu_lora.sh`
  (NIN/NOUT, MU=anisoxglobal|globalthenaniso), NEW `scripts/run_isobbox_mu_loraW.sh`, `scripts/run_global_then_aniso_CHAIN.sh`,
  `analysis/{diag_seg_mapping,plot_mu_ellipses}.py` (changed), NEW `analysis/{export_seg_mapping_ply,mu_table,plot_mu_annotated}.py`.

## STATE AT POD CLOSE — 2026-09-24 (thirty-second pod, 1x RTX 2000 Ada sm_89 16 GB, RAM 251 GB). **NOTHING RAN (analysis only).**
**Focus (Tal): the horse front-leg bug, seg 3 of LVIS 164135.** Tal dropped the iso-vs-directional / mu_lr separation (item 3 below) -- not needed.
- **Seg 3 numbers** (1654 px, ~115 x 20 px vertical leg, **79 centres** of the fixed 2048; angle 0 = vertical, 90 = horizontal):
  iso per-seg mu **3.04** | dir per-seg major **6.91** / minor **2.94** at **91 deg (ACROSS the leg)** | global 1.05/0.96 |
  grid6 averaged over seg px major 1.25 (0.90-2.06) / minor 0.93 (node spacing ~80 px).
  The dir ellipse is perpendicular to the leg: it fits the mapping ERROR (horizontal pairs have tiny d2D, their ends land on different legs), not the leg.
  Other iso segments with mu far from 1 (NOT yet looked at): seg 7 6.71, seg 9 3.55, seg 11 2.03, seg 13 1.65.
- **NEW `analysis/diag_seg_mapping.py`** (one seg, phase-1 + runs): per pixel the argmax part (+ centres), the SOFT weight on leg x-, and
  the **SOFT-SNAP point** (sum w_i V_i over top-10, as in training) in front view (x,y -- separates left/right legs) + side view,
  coloured by image row. Figure `demo/shic/lvis164135_mu/figures/diag_seg3_mapping/seg3_mapping_soft.png` (+ `.json`;
  `seg3_mapping.png` = older argmax version -- Tal: use soft, the algorithm is soft-snap everywhere).
- **What it shows (soft):** phase-1 and dir per-seg form a diagonal **"bridge" through the air between the two front legs** (top of the
  leg on x-, bottom on x+, middle BETWEEN legs; dir: 35% of soft points at |x|<0.07; pixels with >10% weight on BOTH legs: phase-1 61%,
  dir 44%, grid6 0.3%). dir moved the split LOWER (argmax x+/x-: phase-1 63/37 -> dir 46/53). grid6: one continuous line top->hoof on ONE leg.
  Split soft weights also explain why even SAME-argmax-part pairs had high d3D/d2D (expected geodesic between bimodal distributions).
- **CORRECTION (Tal, 2026-09-24): grid6's single leg is the WRONG leg** (x+ is the other leg). So grid6 did NOT fix the mapping, it made it
  CONSISTENT. The relational loss only compares distances and is mirror-invariant -> it cannot tell left from right; grid6 likely drifted to
  phase-1's majority (63% x+). Revised reading: **per-seg mu absorbs the inconsistency (bridge survives); grid mu can't, so the mapping is
  forced onto one leg -- chosen arbitrarily.** Both fail to pick the right leg; that can only come from features/anchor.
  The "per-seg mu swallows the error" mechanism is still a HYPOTHESIS from end states only (no per-step checkpoints).
- **2026-09-27 (pod 33):** `diag_seg_mapping.py` now has a 6th column (training CENTRES only, soft-snap, numbered by image-row rank; same numbers on the col-3 crop) and a **dir_global** row. Figure `.../diag_seg3_mapping/seg3_mapping_soft_v2_alpha0.5.png` (production reading; `_fullLoRA` = alpha 1). **dir_global = like grid6: 100% on x+ (the WRONG leg), 1% mixed.** So only PER-SEG mu keeps the bridge; any shared mu (global or grid) collapses onto x+.
  - Checked: all 4 runs share instance/phase-1/fine_seg/features, pred_f md5s differ, mu_scope as labelled. **Figures read pred_f.pth (full LORA, alpha 1); the EVAL reads alpha/alpha0.5** -> `--pred_rel alpha/alpha0.5/pred_f.pth` (`seg3_mapping_soft_v2_alpha0.5.png`): same picture, softer (x+ argmax: global 96%, grid6 96%, perseg 57%; mixed 6/6/28%).
  - **mu_scope does NOT change neighbour sampling**: global_aniso = one ellipse, neighbours still IN-segment (out_segment=0 in all runs). Pairs never span the two image legs. New `analysis/export_seg_mapping_ply.py` (mesh coloured by one segment's soft mass + centre spheres), PLYs in `.../diag_seg3_mapping/ply/`.
- **OUT-OF-SEGMENT NEIGHBOURS for global_aniso (Tal, 2026-09-27, option 1):** the SystemExit now fires only for segment_aniso/grid_aniso; `run_shicbear_mu_lora.sh` takes `NIN`/`NOUT` (default 16/0 = unchanged). Launched horse 164135: `CLASS=horse IMG_TAG=lvis164135 MU=globalaniso MU_LR=5e-2 NIN=8 NOUT=8 SUFFIX=_mulr5e-2_in8out8` (log `/workspace/logs/horse164135_globalaniso_in8out8.log`).
  **RESULT (alpha 0.5, seg 3): in8out8 puts the WHOLE leg on x- (100% argmax, 0% mixed, one clean line top->hoof)** -- the leg Tal calls correct; dir_global (16 in) was 96% x+. Figure `.../diag_seg3_mapping/seg3_mapping_in8out8_alpha0.5.png`. CAVEATS: one seed; instance eval (3 GT pts only) got WORSE: soft 5.55 -> 6.37, argmax 6.23 -> 8.44 (SHIC 7.37); other front leg not checked (a whole-body mirror flip would look like this too).
  **OTHER 3 LEGS (they live inside body seg 1 -> new `--box R0 R1 C0 C1 --name` in diag_seg_mapping.py; figures `.../figures/diag_legs_in8out8/`):**
  front2 (near front, box 255-395 x 155-195): front x+ in ALL runs. hind1 (265-395 x 220-285): hind x- in all trained runs (phase-1 59% x+). hind2 (255-395 x 325-397): hind x+ in all runs.
  => **NOT a mirror flip. Before, BOTH image front legs landed on mesh x+ (collision); in8out8 splits them (seg3 -> x-, front2 -> x+).** Hind legs were already split in every run. in8out8 side effect: hind1's lower half drifts toward the middle (mixed 3% -> 32%, like phase-1).
  Back-projection stack: `lvis164135_mu/figures/backproj_global_vs_in8out8.png`.
- **DURABLE LESSON (Tal, 2026-09-27): OUT-OF-SEGMENT neighbours are what lets the relational loss tell symmetric parts apart** -- in-segment pairs never link the two legs, so nothing stops both image legs mapping onto ONE mesh leg. (1 instance, 1 seed so far.)
- **HYBRID mu, BUILT (Tal, 2026-09-27): `--mu_scope segment_aniso_xglobal`** (`MU=anisoxglobal` in run_shicbear_mu_lora.sh): IN-segment pair -> its segment's ellipse (proportions); CROSS-segment pair -> ONE shared global ellipse = the LAST row of mu_aniso (placement). `hybrid_aniso_mu_scale()` in train_relational_loss.py. Pre-edit copy `/workspace/archive/train_relational_loss.py.bak_2026-09-27`. Launched horse 164135 NIN=8 NOUT=8 mu_lr 5e-2 (log `/workspace/logs/horse164135_anisoxglobal_in8out8.log`).
  **RESULT (alpha 0.5; figures `lvis164135_mu/figures/diag_legs_hybrid/`, `backproj_perseg_global_hybrid.png`):** leg placement KEPT -- seg3 99.5% x- (right leg), front2 x+, hind1 x-, hind2 x+. But seg3 is 31% mixed (global_in8out8 0%): the LOWER half fans toward the middle again (a half-bridge), and seg 3's own ellipse is 1.42/0.91 at 104 deg = ACROSS the leg, the same signature as dir_perseg (6.9/2.9 at 91 deg) -> the per-seg ellipse still absorbs the spread, just less. hind1 mixed 20% (global 32%, perseg 13%). Global (last-row) ellipse 0.975/0.926 ~ circle. Instance soft/argmax: perseg 6.28/6.96, global_in8out8 6.37/8.44, hybrid 6.37/6.37 (SHIC 7.37; 3 GT pts, noise).
  Ellipse figure `lvis164135_mu/figures/ellipses_hybrid/ellipses_perseg_global_hybrid.png` (`plot_mu_ellipses.py` now handles segment_aniso_xglobal; cross-seg ellipse drawn magenta top-right). seg 3: perseg 6.9/2.9 -> hybrid 1.39/0.94 (both horizontal-major); tail seg 2 hybrid 1.94/1.31.
  **Tal (2026-09-27): still a problem -- seg 3's ellipse is flattened ACROSS the leg, not along it.** -> back to the GUITAR (simpler) with the hybrid: NEW `scripts/run_isobbox_mu_loraW.sh` = guitar MAIN (run_isobbox_main_T.sh flags, T=0.01, stride 5) + LORA-W all r4 a0.5 + mu_lr 5e-2 + MU (default anisoxglobal) + NIN/NOUT (default 8/8); SMALL analysis at alpha 0.5 + `ellipses.png` in the demo dir. Log `/workspace/logs/guitar_anisoxglobal_in8out8.log`.
  **GUITAR HYBRID RESULT:** eval v2 snap/argmax/soft **86.5/86.0/84.9 vs MAIN 89.4/89.0/88.0** (-3; but MAIN has no LORA-W, so 2 changes mixed). soft cov 31.5%. Body cells larger + irregular vs MAIN's clean checker; neck similar. Ellipses: body seg 2 (67%) 1.21 @12deg, neck seg 4 (16%) 1.08 ~circle, xglobal 1.20 @14deg; almost every segment's major axis is ~10-20deg (near vertical) -> looks like ONE image-wide anisotropy, not per-part. Figures `demo/guitar/runs/isobbox_prop/bsb_isobbox_sdsquare_mu_anisoxglobal_..._a0.5_phase2/{guitar_hybrid_vs_MAIN,ellipses_r70}.png`. MAIN predates mu_scale.pth -> no MAIN ellipse figure.
  Tal: hybrid not good enough on the guitar -> running **dir per-seg + LORA-W** on the guitar: `MU=aniso NIN=16 NOUT=0 scripts/run_isobbox_mu_loraW.sh` (log `/workspace/logs/guitar_aniso_in16out0.log`).
  **RESULT: dir per-seg + LORA-W = 92.1/91.5/89.5 -- BEATS MAIN (89.4/89.0/88.0) and the hybrid (86.5/86.0/84.9).** Body cells larger than MAIN, cleaner than hybrid. Neck ellipse (seg 4) 1.26/1.03 @19deg (neck runs ~30deg in the image -> roughly along it, ratio 1.3); body seg 2 1.15 ~circle. Figure `demo/guitar/runs/isobbox_prop/comparison_mu_loraW/guitar_MAIN_dirperseg_hybrid.png`. Still 2 changes vs MAIN (LoRA + directional mu); a guitar iso-per-seg + LoRA arm would isolate them. One seed.
  **iso per-seg + LORA-W (= MAIN + LoRA, `MU=learn NIN=16 NOUT=0`): 91.2/91.3/89.0.** So on the guitar LoRA gives most of the gain (MAIN 89.4/89.0/88.0 -> 91.2/91.3/89.0), directional adds a little (92.1/91.5/89.5, within 1 pt, one seed). Figure `comparison_mu_loraW/guitar_MAIN_iso_dir_hybrid.png`; per-segment mu table (iso mu vs ellipse major/minor/angle) `comparison_mu_loraW/mu_table.md`, NEW `analysis/mu_table.py`. Neck seg 4: iso 1.280, dir 1.284/0.989 @19deg (major = iso).
  Readable version (Tal): NEW `analysis/plot_mu_annotated.py` -> `comparison_mu_loraW/mu_annotated.png`: iso panel = one mu per segment; directional panels = each segment's ellipse with red (major) / blue (minor) axes drawn and a callout 'along X / across Y'.
- **TWO-STAGE mu (Tal, 2026-09-27): `--mu_scope global_then_segment_aniso --mu_switch_step 150`** (`MU=globalthenaniso [SWITCH=150]` in both launchers): stage A = ONE global ellipse (last row) + NIN/NOUT neighbours (8/8, cross-seg pairs fix left/right); stage B (step >= switch) = per-segment ellipses initialised from the global one, `--switch_nin/--switch_nout` (16/0). One run, LoRA + Adam continuous. `switch_aniso_mu_scale()`. Chain `scripts/run_global_then_aniso_CHAIN.sh`: guitar sw150, horse 164135 sw150, guitar global_aniso in8out8 (control: do cross-seg pairs alone hurt the guitar?). Logs `/workspace/logs/{guitar_globalthenaniso_sw150,horse164135_globalthenaniso_sw150,guitar_globalaniso_in8out8}.log`.
  **RESULTS:** GUITAR (eval v2 snap/argmax/soft): two-stage 88.6/88.5/86.9; global in8out8 control 85.8/85.5/84.4 (the WORST guitar arm -> cross-seg pairs themselves hurt the guitar; stage B recovers ~3 pts but not to dir per-seg 92.1/91.5/89.5 or iso+LoRA 91.2/91.3/89.0). Guitar neck seg 4 two-stage 1.00/0.78 (dir 1.28/0.99). HORSE: two-stage KEEPS all 4 legs placed (seg3 100% x-, **mixed 1.7%** vs hybrid 31%, dir per-seg 29%); front2 x+, hind1 x- (mixed 23%), hind2 x+. seg 3 ellipse 1.12/0.81 @120deg (dir per-seg 6.91/2.94 @91): much smaller, still not along the leg. Instance soft/argmax 6.37/7.47 (3 pts). Figures: `demo/guitar/runs/isobbox_prop/comparison_mu_loraW/{guitar_twostage_backproj,mu_annotated_twostage}.png`, `demo/shic/lvis164135_mu/figures/diag_legs_twostage/`. NEW `plot_mu_annotated.py` rep point = most interior pixel.
  NOTE (history): on 09-16 Tal rejected 8in+8out for the BEAR proportions ("seen to break runs") -- that was the isotropic per-seg recipe, before LORA-W.
### NEXT POD (Tal decides)
1. Continue the horse-leg research. Candidate tests: log seg-3 mu + % px on x- through training (does mu rise before the split freezes?);
   per-seg mu frozen/bounded toward global; what makes the RIGHT leg win (anchor / feature signal -- relational loss can't).
2. Check the other high-mu segments (7, 9, 11, 13) and bear/elephant segments with mu far from 1.
- Uncommitted additions today: `analysis/diag_seg_mapping.py`.

## STATE AT POD CLOSE — 2026-09-23 (thirty-first pod, 1x RTX 2000 Ada sm_89 16 GB, RAM 251 GB). **NOTHING RAN.**
Explanation only (Tal studied the directional per-seg algorithm). NEXT POD = the thirtieth pod's list below, unchanged.
- Wording (Tal): say **"iso / directional"**, not "scope" (`--mu_scope segment` = iso, `segment_aniso` = directional).
- Clarified: s = sqrt(u^T M u) = |L^T u| is M's metric length of the image direction u (the support function of the
  ellipse {Lv : |v|<=1}), NOT its polar radius. They agree on the principal axes, so the plotted major/minor/angle
  (`aniso_axes`) are exact; the drawn ellipse is not s(theta) at every angle.

## STATE AT POD CLOSE — 2026-09-22 (thirtieth pod, 2x RTX 4000 Ada, RAM 251 GB). **NOTHING IS RUNNING.** Tal closes the pod.
**The day in one list** (details in the thirtieth-pod entry below):
- **LVIS eval #2 (LORA + directional per-seg, mu_lr 5e-2) COMPLETE 132/132: soft 33.12** vs run #1 34.90; paired -1.78 +- 0.75 SE
  (82 better / 46 worse) -- just under the noise bar, and iso->directional + mu_lr both changed. ~= SHIC 33.0.
- **Horse diagnosis:** tail (seg 2) circle = no tail on the mesh (mapping spreads isotropically, the circle is the right fit).
  Front leg (seg 3): per-seg runs keep phase-1's left/right leg split, grid6/global fix it -- **per-seg mu grows (3-7) and absorbs
  the mapping error.** Hypothesis, one leg only.
- 2 GPUs + 251 GB RAM: 1 worker per GPU, no OOM (~200-430 s/instance).
- Uncommitted additions today: `analysis/diag_mu_segment.py`, `analysis/diag_mu_compare.py`.
### NEXT POD (Tal decides)
1. Test the hypothesis: per-seg mu bounded / regularised toward the global mu -> does the horse leg get fixed?
2. Check bear/elephant for segments whose per-seg mu is far from 1 (same effect?).
3. ~~Optional: separate iso-vs-directional from mu_lr on LVIS~~ -- DROPPED by Tal 2026-09-24. (Tal: say "iso / directional", not "scope".)

## STATE AT POD CLOSE — 2026-09-22 (twenty-ninth pod, 1x RTX A4500). **NOTHING IS RUNNING.** Tal moves to a 2-GPU pod.
**FIRST THING ON THE NEW POD:** resume the LVIS eval -- the exact command is in "FULL LVIS BEAR EVAL #2" below (25 instances left).
**The day in one list:**
- **mu_lr: 5e-2 ADOPTED** (1e-1 / 5e-1 changed nothing -- the ellipse saturates). Tal: an ANCHOR is necessary; LORA for now,
  anchor+L_dist comparison later.
- **Directional mu on 3 more instances** (LVIS 3044 bear, horse 164135, elephant 92018): ellipses follow the object
  (3044 vertical 1.41, elephant horizontal 1.31, horse ~circle 1.10) but the back-projections barely change.
  **On every instance ONE segment covers ~82-89% of the animal**, so per-seg ~= global; only the grid can localise.
- **HORSE + ELEPHANT are now full SHIC classes here** (phase-1, 3D table, checker, SHIC reproduced 23.08 / 26.37).
- **Full LVIS bear eval #2 (LORA + directional per-seg, mu_lr 5e-2): 107/132 done, soft 32.09 vs iso run #1 33.94 on the
  same subset (-1.84 +- 0.84).** Finish it first.
- **Disk: 455 GB -> 266 GB** (step checkpoints + phase-1 feature caches deleted, Tal approved).
- Uncommitted: everything from pods 25/27/28 PLUS today's scripts (`run_shicclass_setup.sh`, `run_lvis_prep.sh`, CLASS/IMG_TAG
  in `run_shicbear_mu_lora.sh` + `make_lvis_arm_summary.sh`, mu/runs_dir/NUM_WORKERS in the LVIS worker+queue,
  `plot_mu_ellipses.py --min_frac/--no_legend`, `make_lvis_summary_figure.py --class_name`, figure scripts under demo/shic).

## 2026-09-22 (thirtieth pod, 2x RTX 4000 Ada sm_89 20 GB, RAM 251 GB) -- LVIS eval #2 resumed + HORSE mu DIAGNOSIS
- **LVIS eval #2 DONE, 132/132 (1 worker/GPU, no OOM): ours soft 33.12 / argmax 34.14 | ZS 39.25 | SHIC 33.0 (repro 33.09).**
  Paired vs run #1 (iso per-seg mu_lr 1e-2, 34.90): **-1.78 +- 0.75 SE**, 82 better / 46 worse -- ~2.4 SE, just under the ~2.5 noise
  bar; two things differ (iso->directional + mu_lr). `data/densepose_lvis/results_aniso/aggregate.json`.
- **Horse 164135, dir per-seg -- WHY seg 2 (tail) is a circle and seg 3 (front leg) has a huge ellipse** (Tal):
  - Scripts: NEW `analysis/diag_mu_segment.py` (one run, one seg: centres, pair directions, d3D/d2D per direction vs learned
    ellipse) and NEW `analysis/diag_mu_compare.py` (same seg across runs: which mesh PART each pixel hits, painted on the photo).
    Figures `demo/shic/lvis164135_mu/figures/diag_seg{2,3}/`.
  - Tail: phase-1 maps all 2233 px to 4 vertices on the rump (no tail on the mesh); LORA spreads it to ~20 vertices ISOTROPICALLY
    -> d3D/d2D is flat in angle (~0.8) -> circle is the correct fit. Sampling is not the cause (82 centres, pairs 75% along the tail).
  - Leg (seg 3): phase-1 splits it between the two FRONT legs (66/34, left/right symmetry). **Per-seg runs (iso AND dir) keep the
    split; grid6 and global FIX it (100% one leg, 0.003 weight on the other).** Per-seg mu of seg 3 grows to absorb the inflated d3D
    (iso 3.04, dir 6.9/2.9 vs ~1 elsewhere), so the loss stops penalising the wrong mapping. grid6's mu on the leg stays ~1.1 (nodes are
    shared with body/background, spacing ~80 px vs a ~20 px leg) -> residual stays -> encoder fixes the mapping.
  - **Hypothesis (one leg, one horse): per-seg mu is too free and swallows mapping errors.** Proposed test: per-seg with mu
    bounded/regularised toward the global mu -> does the leg get fixed? Also check bear/elephant segments with mu far from 1. Tal decides.
  - Clarified for Tal: grid_aniso neighbours are still drawn from the same FINE SEGMENT; the grid only sets each pair's mu
    (bilinear blend of the 4 nodes around the CENTRE; gradient goes to those 4 nodes).

## 2026-09-22 (twenty-ninth pod, 1x RTX A4500 sm_86 20 GB, **container RAM cap 62 GB** -> 3 concurrent runs OK)
### TAL'S VERDICT on the 09-21 mu figures (verbatim in substance)
- **No LORA, directional per-seg: change too small** -- the bear is compact and evenly spread (not a giraffe with a long
  narrow part), so the per-segment ellipse is ~a circle.
- **Merge 2+3: first visible change, but it drifts from the source** -- no anchor here (no LORA, no anchor+L_dist).
- **mu_lr 5e-2 (flatter ellipse): helped, ADOPTED.** Proportions look good but SHIFTED -- again, no anchor. An even higher
  mu_lr may be worth a run -- decide after the full review, don't re-run everything blindly.
- **LORA clearly helped**; the 7 LORA arms look alike, hard to rank -> decide on more examples.
- **CONCLUSION: an ANCHOR IS NECESSARY.** Either LORA-W or anchor+L_dist (SHIC-style). Which is better is open; for now
  continue with LORA, compare the two later. Current research focus: directional mu.
### RUN: directional mu on LVIS 3044 (the bear there is more elongated -> Tal expects a different ellipse)
- 4 arms, all LORA-W (production: all layers r4 lr 1e-3, alpha 0.5), **all mu_lr 5e-2**: iso per-seg (baseline),
  directional per-seg, directional grid 6x6, directional global. No merge arms (3044's segments were never merged).
- Recipe = the bear3 LORA mu recipe EXCEPT `cyc_return_stride 3` (Tal's pick: matches the 400-px LVIS image and the LVIS
  eval run on 3044, so the iso arm is comparable to it). Inputs = kept LVIS intermediates in `data/densepose_lvis/runs/lvis3044`
  (geo_diag_2d 447.97 from the meta json).
- **3044's fine segmentation: segment 1 = 89% of the bear** (rest <3.3%) -> per-seg directional ~= global here; the grid is
  the arm that can show local direction.
- Plus bear3: directional per-seg WITH LORA at **mu_lr 5e-2** (the 09-21 LORA arm was 1e-2), tag `..._mu_aniso_..._seed0_mulr5e-2`.
- Code: `scripts/run_shicbear_mu_lora.sh` got `IMG_TAG=lvis<id>` (bear3 default unchanged; RET_STRIDE env). LVIS arms write to
  `experiments/shic_bear/lvis/lvis3044/encoder_<S>_phase2` and `demo/shic/lvis3044_mu/<S>/alpha0.5` (analysis =
  `make_lvis_arm_summary.sh`). Queue `/workspace/logs/mu_lora_3044_queue.sh`, logs `/workspace/logs/mulora_{3044_*,bear3_aniso_mulr5e-2}.log`.
- Status: **DONE, all 5 rc=0** (~2 h wall, 3 concurrent). Figure `bsb/demo/shic/lvis3044_mu/figures/lvis3044_directional_mu_lora.png`
  (`make_fig.py` there; ellipse plots `ellipses_{aniso,grid6,global}.png`). Tal's verdict pending.
- **Ellipses on 3044 are clearly VERTICAL** (the standing bear), unlike bear3: big seg 1 (89%) ratio **1.41** (mu vert 0.79 /
  horiz 0.56, iso 0.74); global 1.36 (~= seg 1, as expected); grid 1.06-1.67, most elongated in the lower body (node 4,2 1.67).
  Under LORA, bear3's global was 1.14 -> the more elongated object does give a more elongated ellipse, as Tal predicted.
- GT error (3 points only -- NOISE, do not rank on it): iso 16.8 | per-seg 16.4 | grid 14.8 | global 16.4 | SHIC 42.6.
  The iso arm here (mu_lr 5e-2) != the LVIS-queue 3044 run (mu_lr 1e-2, 12.4).
- bear3 LORA dir per-seg mu_lr 5e-2: max ratio 1.93, median 1.42 (vs 1e-2: seg2 1.38). Added as panel 5 of the anchor-options figure.
### RUN: more extreme mu_lr (Tal: sharper ellipse), LORA dir per-seg ONLY, bear3 + 3044, mu_lr **1e-1 and 5e-1**
Queue `/workspace/logs/mu_lora_highlr_queue.sh`, logs `mulora_{bear3,3044}_aniso_mulr{1e-1,5e-1}.log`, SUFFIX `_mulr1e-1/_mulr5e-1`.
Status: **DONE** (bear3 1e-1's analysis hit a GPU OOM while 3 ran concurrently -- analysis re-run alone, OK; training was fine).
**TAL'S DECISION: mu_lr stays at 5e-2** (no visible improvement at 1e-1 / 5e-1). Do not re-open without a new reason.
**RESULT: the big-segment ellipse SATURATES -- a higher mu_lr does NOT sharpen it.** bear3 seg2 ratio 1.38 / 1.42 / 1.41 / 1.46
(mu_lr 1e-2 / 5e-2 / 1e-1 / 5e-1), seg3 1.16 / 1.26 / 1.28 / 1.27; 3044 seg1 1.41 / 1.42 / 1.44 (5e-2 / 1e-1 / 5e-1). Axis stable.
Back-projections alike across lrs; 3044 GT err identical (16.41) at 5e-2/1e-1/5e-1. Only tiny sliver segments blow up (3044 max
ratio 17.97 at 5e-1). => At 5e-2 the ellipse is converged; its shape is what the data supports. A sharper ellipse needs a
different lever (e.g. forcing it = distortion the data does not support; or finer segments/grid so local directions don't average out).
Figure `bsb/demo/shic/comparison_bear3_anchor_options/lora_dir_perseg_mulr_progression.png` (`make_mulr_fig.py`); ellipse plots
`ellipses_bear3_lora_aniso_mulr*.png` there, `demo/shic/lvis3044_mu/figures/ellipses_aniso_mulr{1e-1,5e-1}.png`.
### FULL LVIS BEAR EVAL #2 -- LORA-W + DIRECTIONAL per-seg mu, mu_lr 5e-2 (Tal, 2026-09-22; bear only, 132)
- Launcher `/workspace/logs/lvis_aniso_launch.sh` (smoke test on 3044, then the queue): results
  `data/densepose_lvis/results_aniso/` (+ aggregate.json), intermediates `data/densepose_lvis/runs_aniso/` (deleted per instance),
  logs `/workspace/logs/lvis_aniso/`. RESUMABLE: relaunch the queue line with the same env; scored instances are skipped.
- Code: `run_lvis_worker.py` got `--mu_scope segment|segment_aniso`, `--mu_lr`, `--runs_dir` (**the worker DELETES
  `<runs_dir>/<tag>` after scoring -- the default dir holds the kept lvis3044/7108/... inputs, so new runs MUST use another
  runs_dir**). `run_lvis_queue.sh` got `NUM_WORKERS` (> NUM_GPUS allowed, round-robin on GPUs) and `WORKER_ARGS`.
  3 workers on the one A4500 (RAM cap 62 GB).
- Compare against run #1 (iso per-seg mu_lr 1e-2 + LORA): ours soft 34.90 / ZS 39.29 / SHIC 33.0. NOTE: #1 used mu_lr 1e-2,
  #2 uses 5e-2 -> two things differ (scope + lr).
- Smoke test (3044): 244 s/instance alone, ours 16.41 = identical to the separate 3044 dir-per-seg run (reproduces). Full queue
  launched right after (3 workers). Status: RUNNING.
- **3 workers on ONE 20 GB GPU -> GPU OOM in the SAM fine-segment stage** when it coincides with another worker's peak
  (17 of the first 62 failed, cheaply, at the start). Retry pass `/workspace/logs/lvis_aniso_retry.sh` waits for the queue,
  re-runs all ids with ONE worker (scored ones are skipped), re-aggregates (log `lvis_aniso/retry.log`). Throughput with 3
  workers: ~1 instance / 2.8 min (vs 4 min alone). **On a multi-GPU pod use 1 worker per GPU.**
- **STOPPED AT POD CLOSE with 107/132 scored** (Tal moved to a 2-GPU pod; both pods share /workspace and the worker has NO
  LOCK, so two pods must NOT run this queue at the same time). `runs_aniso/` emptied (interrupted leftovers; every stage is
  recomputed anyway). Results kept in `data/densepose_lvis/results_aniso/` -- **do not delete, the queue resumes from them.**
- **RESUME ON THE NEW POD (2 GPUs, 1 worker per GPU -- do NOT share a GPU, that is what caused the OOMs):**
  ```
  cd /workspace/bsb && source /workspace/activate_bsb.sh
  setsid nohup env NUM_GPUS=2 NUM_WORKERS=2 RESULTS=data/densepose_lvis/results_aniso LOGDIR=/workspace/logs/lvis_aniso \
    WORKER_ARGS="--mu_scope segment_aniso --mu_lr 5e-2 --runs_dir data/densepose_lvis/runs_aniso" \
    bash scripts/run_lvis_queue.sh > /workspace/logs/lvis_aniso/resume.log 2>&1 &
  ```
  Scored instances are skipped, so it only runs the 25 missing ones (~1 h on 2 GPUs): 1328 6463 14111 14150 25925 31441
  32412 37264 55342 74432 83570 95168 113202 113864 117682 146948 159218 159483 171627 186446 186447 187619 215097 228116 230979.
  The queue re-aggregates at the end; if it does not, run `python analysis/aggregate_lvis_results.py --results_dir
  data/densepose_lvis/results_aniso --out_json data/densepose_lvis/results_aniso/aggregate.json`.
- **PARTIAL RESULT (107 instances, the same ones in both runs):** directional **soft 32.09 / argmax 33.09** vs iso run #1
  **33.94** on that subset (its full-132 number is 34.90); paired per-instance diff **-1.84 +- 0.84 SE** -- ~2 SE, directional
  ahead but NOT above the ~2.5 noise threshold. The 25 missing are NOT random (they failed on GPU memory, which tracks image
  size), so the final number can still move.
- **DISK CLEANUP 2026-09-22 (Tal approved): 455 GB -> 266 GB.** Deleted: all `encoder_checkpoint_step*.pth` under
  experiments/shic_{bear,horse,elephant} (396 files, 88 GB; final checkpoints/pred_f/alpha kept) and the phase-1 feature caches
  `data/shic_{bear,horse,elephant}/encoder_data/dino_sd_f` (108 GB). Retraining phase-1 now needs the precompute again (~4 min).
  Kept: horse/elephant phase-1 encoders + 3D geo tables, all guitar data.

### NEW CLASSES vs SHIC: HORSE + ELEPHANT (Tal, 2026-09-22)
- SHIC's public release = bear/horse/elephant ONLY (weights + meshes in `demo/shic/`). Giraffe etc. are in Table 1 but we have
  neither SHIC weights nor the `giraffe_5002` mesh (DensePose publishes its UV; its geometry pkl unpickles to zeros -- old trap).
- LVIS ds2_val: horse 458 inst / 306 img (mesh horse_5004 = our horse.obj 5004v), elephant 539 / 321 (elephant_5002 = 5002v).
- Candidate sheets (20 each, 3 pts, side>=150px, one per image, seed 0): `bsb/demo/shic/{horse,elephant}_lvis/*_candidates_20.png`.
- **Tal's picks: horse #5 = ann 164135 (foal, side view); elephant #10 = ann 92018.**
- **SHIC horse reproduced: 23.08** (bbox variant, 1337 pts; square 23.16, square_mask 24.86). Paper's horse number not yet checked.
- **Phase-1 timing, measured on the horse (RTX A4500, file mtimes): ~6-7 min total** -- renders 1000 views ~40 s, DINO+SD
  features ~3.6 min, xyz targets ~30 s, training 46 s. The old "15-17 min / 1000 views" was the RTX 2000 Ada (weaker GPU);
  ~80% of the precompute is SD, so DINO-only would be ~1/5 (never measured directly). Whole class setup ~25 min incl. SHIC eval.
- Per-instance: NEW `scripts/run_lvis_prep.sh` (CLASS, ANN_ID; keeps inputs; builds the class 3D geo table on its first
  instance -> `experiments/shic_<cls>/geodesic_tables/`). `run_shicbear_mu_lora.sh` and `make_lvis_arm_summary.sh` take `CLASS`
  (default bear, unchanged); `make_lvis_summary_figure.py --class_name` prints that class's SHIC reproduction.
- Queue `/workspace/logs/horse_elephant_queue.sh`: preps, then the 3044 arm set (LORA, mu_lr 5e-2: iso / dir per-seg / grid6 /
  global) on both instances, logs `mulora_{horse,elephant}_*.log`. Outputs `demo/shic/lvis{164135,92018}_mu/`.
- **DONE** (first pass failed only at the figure: `render_colored_mesh.py` needs `--save_rendered_views_grid` to write the
  reference renders -- fixed in the setup script; analysis re-run, training untouched, all 8 rc=0). SHIC elephant reproduced **26.37**.
  Figures `bsb/demo/shic/lvis{164135,92018}_mu/figures/lvis*_directional_mu_lora.png` (`lvis3044_mu/figures/make_fig.py <ann> <class>`).
  GT err (3 pts, NOISE): horse iso 6.4 / per-seg 6.3 / grid 5.0 / global 5.5 vs SHIC 7.4; elephant 38.0 / 36.6 / 37.8 / 38.2 vs SHIC 66.0.
  Ellipses: horse ~circular (global 1.10, body seg 1.13); elephant HORIZONTAL (global 1.31, body seg 1.23, grid 1.18-1.39).
  Figures now show mesh renders from the PHOTO'S side (both instances face LEFT -> azim 45/0; bear stays 135/180) + the
  fine-segment map. **Both have ONE segment covering ~the whole animal** (elephant: body+trunk+head one segment; horse too),
  so per-seg mu ~= global here; only grid can localise (e.g. trunk).
  Why "more ellipses than segments": the fine map has 11-14 segments but most are <1% slivers (invisible); the plot drew one
  ellipse per segment. `plot_mu_ellipses.py` now has `--min_frac` (figures use 0.01 -> 3-5 segments drawn) and `--no_legend`;
  the figure writes the legend + per-segment colour swatch/size UNDER the image. Segment sizes: horse seg1 82.4%, elephant seg1 81.4%.
  Checker PLYs: `/workspace/bsb/demo/shic/colored_mesh/{horse,elephant}_mesh_checker16_uv_color.ply`.
  **Horse leg heatmaps (Tal):** vertex->vertex feature similarity (as in feature analysis), query vertices 4471/4384 (front, x+/x-),
  4209/4364 (hind), ~22% height; `demo/shic/lvis164135_mu/figures/heatmap_legs_vertex/heatmap_legs_vertex.png` (azim 45/135).
  Result: a front-leg vertex lights BOTH front legs ~equally (hind: both hind legs) -- front/hind separated, LEFT/RIGHT NOT
  (the known symmetry weakness); iso ~= directional. (Also made first by mistake: pixel->vertex version, `heatmap_legs/`.)
  **Rendering speed:** use `render_colored_mesh.py --ply_paths/--save_dirs/--output_paths` (ONE process): 8 renders 92 s vs ~1 min EACH.
  Tal's visual verdict pending.
- Class setup `scripts/run_shicclass_setup.sh` (CLASS=horse|elephant): SHIC LVIS eval -> `data/densepose_lvis/eval_shic_<cls>/`
  (+ heat geodesics), checker16 UV colours + renders `demo/shic/colored_mesh/<cls>_*`, phase-1 (1000 views, same recipe as the bear)
  -> `experiments/shic_<cls>/encoder_dfd_crossview_phase1`. Launched horse then elephant, logs `/workspace/logs/setup_{horse,elephant}.log`.
- STILL TO DO: generalise per-instance scripts (run_shicbear_mu_lora.sh / make_lvis_arm_summary.sh are bear-hardcoded: OBJ, NAME,
  P1, GEO3D, CHK, GEO228, class_name) and build the 3D geo table on the first instance.
### FIGURE: bear3 anchor options (Tal) -- `bsb/demo/shic/comparison_bear3_anchor_options/bear3_anchor_options_soft.png` (`make_fig.py` there)
Photo + mesh renders (azim 180/90/135), SHIC top1, then ours soft-snap: anchor+L_dist 1/80 sdist w=4.3e-4 (the
`..._g2.7951e-06_sdist_w4.3e-4_...` run = the "1/3x anchor" panel of `sdist_calibrated_sweep.png`, NOT the 1/10 one),
no-LORA merged dir per-seg 5e-2, LORA dir per-seg 1e-2, LORA dir per-seg 5e-2 (added when its run finishes), LORA merged dir per-seg 5e-2.
**"merged directional 5e-2" is PER-SEGMENT** (MU=aniso); no merged-global run exists (and grid/global in run_shicbear_main_T.sh hardcode mu_lr 1e-2).

## STATE AT POD CLOSE — 2026-09-21 (twenty-eighth pod, 1x RTX 2000 Ada). **NOTHING IS RUNNING.**
**The day in one list** (details in the sections right below):
- **LVIS eval COMPLETE: 132/132, ours soft-snap 34.90** (argmax 36.58) vs ZS 39.29 | SHIC 33.0 | CSE 35.7. Only the gap to ZS
  exceeds noise; vs SHIC/CSE it is within noise. Eval set aside for now (Tal).
- **Two more LVIS summary figures** (3044 we win, 7108 SHIC wins) + marker PLY upgrade (split spheres, 3D point numbers).
- **Directional mu BUILT** (`--mu_scope segment_aniso | grid_aniso | global_aniso`) and run in 7 arms, both without and WITH LORA-W.
  Findings: ellipses DO form; on the original 9 segments they barely change the back-projection because bear3 is essentially
  2 huge segments. **Merging segments 2+3 is the one visible change (larger, more regular cells) -- Tal: "I see an improvement".**
  It shows with iso mu too, so it comes mostly from the merge (wider neighbour sampling). Ellipses are sharper under LORA.
- **Tal is reviewing the figures visually** -- `demo/shic/comparison_aniso_vs_baseline/` (no LORA) and
  `demo/shic/comparison_aniso_vs_baseline_lora/` (LORA). His verdict decides the next step.
- **Constraints learned today:** container RAM cap 31 GB -> max 2 concurrent bear runs; `activate_bsb.sh` cd's to /workspace/bsb
  (use absolute paths in heredoc python after sourcing it); the Read tool's hook timed out late in the day (images unviewable by
  the assistant -- the files were sent to Tal instead).
- **Uncommitted** (commit when Tal asks): everything from pods 25 and 27, PLUS today's `phase2/train_relational_loss.py`
  (aniso scopes + mu_scale.pth/mu_aniso.pth saving), `analysis/compare_ours_vs_shic_points.py`, NEW `analysis/plot_mu_ellipses.py`,
  `scripts/run_shicbear_main_T.sh` (MU=aniso/grid/globalaniso, MU_LR, FINE, SUFFIX, SKIP_ANALYSIS), NEW `scripts/run_shicbear_mu_lora.sh`.
- Disk: `data/densepose_lvis/runs/lvis{3044,7108}` kept (~2 GB each) for the figures; delete when no longer needed.

### NEXT POD
1. Tal's visual verdict on the 7-arm figures (with / without LORA). Open questions it decides:
   - Is the merge improvement real and wanted? If so, the lever is SEGMENTATION GRANULARITY / neighbour range, not mu --
     test it directly (e.g. merge vs larger neighbour radius), and on a second object before generalising.
   - Is directional mu worth keeping? So far: learns real ellipses (ratio 1.2-1.5), tiny visual effect on its own.
2. Untried for directional mu: a local diagnostic (d3D/d2D by angle in small windows); closed-form ellipse per step.
3. Directional mu on LVIS is NOT scored -- only bear3 visuals exist.

### LVIS QUEUE (morning) — relaunched 10:10 IDT with `NUM_GPUS=1`, 28 left. **FINISHED 12:57 IDT, 132/132, zero errors.**
**FINAL (DensePose-LVIS bear, geodesic error, lower=better, 393 pts):** ours soft_snap **34.90** (argmax 36.58) | ZS soft_snap 39.29 |
SHIC 33.0 (reproduced 33.09) | CSE supervised 35.7 | zero-shot SD-DINO (paper) 48.2. SE/inst 2.33. `data/densepose_lvis/results/aggregate.json`.
Read: ours < ZS by 4.4; ours vs SHIC gap (1.9) is under the ~2.5 noise threshold -> not distinguishable.
Per-instance SHIC errors live in `data/densepose_lvis/eval_shic_bear/results.json` (`bbox.per_instance`) -- use them to pick examples.
Two more summary figures (Tal's layout): `demo/shic/lvis_vs_shic/SUMMARY_lvis3044.png` (we win 12.4 vs 42.6; a cardboard bear
cutout, SHIC flips 2 pts to the far side) and `SUMMARY_lvis7108.png` (SHIC wins 11.3 vs 65.5; bear heavily occluded by branches,
our back-projection fragments). Re-running both with `--keep_intermediates` (results in `results_examples/`) reproduced the
queue's scores exactly. Their intermediates (~2 GB each) are kept in `data/densepose_lvis/runs/lvis{3044,7108}`.
**Marker PLY upgraded (Tal, 2026-09-21)** in `analysis/compare_ours_vs_shic_points.py`: markers on the SAME vertex are merged into
one SPLIT sphere (longitude sectors, one colour per role -- before, the big GT sphere hid an exact hit, e.g. 3044 pt 3), and every
marker carries its GT point number as extruded 3D text in the PLY itself (`--label_height`, default 0.07). Regenerated for 3044 and
7108 only; 904/117683 still have the old-style PLY. Numbers are small in the 450-px summary render -- fine in a PLY viewer.
**Eval set aside for now (Tal), work returns to directional mu.**

### DIRECTIONAL MU — BUILT AND RUN ONCE (2026-09-21, Tal: build it + one A/B while he studies the algorithm; diagnostic skipped)
- Code: `--mu_scope segment_aniso` (learned only, in-segment pairs only) in `phase2/train_relational_loss.py`
  (`aniso_mu_scale`, `aniso_axes`). Per segment (a,b,c) -> L=[[e^a,0],[c,e^b]], M=LL^T; pair scale s=|L^T u|, u = unit IMAGE
  offset centre->neighbour (row,col); s divides the 3D side exactly like the isotropic mu. Init a=b=log s0, c=0 = circle
  (matches isotropic to 1e-7, not bit-identical). Saves `mu_aniso.pth` (params, major/minor, major-axis angle). Unit-tested.
- `scripts/run_shicbear_main_T.sh`: `MU=aniso`, and `SUFFIX` (re-run an arm into a fresh dir).
- A/B on bear3 MAIN recipe (both launched together on one GPU, ~2.6 GB each):
  baseline re-run `..._mu_learn_perseg_..._seed0_rerun0921_phase2` vs `..._mu_aniso_perseg_..._seed0_phase2`.
  **The fresh baseline is NOT bit-identical to the 09-16 MAIN bear** (step-25 loss 0.000380 vs 0.000381) -- compare against the re-run.
- Result: ellipses DO form: 8/9 segments ratio 1.1-1.7 (seg 1 ~circle 1.01). Loss@300 0.000098 vs 0.000101.
  Back-projection (`demo/shic/comparison_aniso_vs_baseline/backproj_soft_top1.png`): very similar to baseline by eye.
- **WHY little changed: bear3's segmentation is 2 big segments** (seg 2 front half 49.9%, seg 3 back half 44.4%; the rest are
  ears/eyes/nose/edge slivers <3%). The big ones learned weak ellipses (1.21 / 1.10); the strong ones (1.4-1.7) are in tiny segments.
  iso mu vs directional (vert/horiz): seg2 0.722 -> 0.686/0.807, seg3 0.823 -> 0.852/0.793.
- Runs now save their final mu: `mu_scale.pth` (isotropic, {'mu_scale'} = the --mu_init_path format) / `mu_aniso.pth`.
  Baseline re-run `..._rerun0921b` (training only, `SKIP_ANALYSIS=1`) reproduced `_rerun0921` bit-identically.
- More scopes: `--mu_scope grid_aniso --mu_grid 6` (ellipse field on a 6x6 node lattice over the mask bbox, bilinear per centre;
  script `MU=grid`) and `--mu_scope global_aniso` (one ellipse for the whole bear, sampling unchanged; `MU=globalaniso`).
  `FINE=` env override in `run_shicbear_main_T.sh`; `demo/shic/bear3/bear3_fine_segments_merge23.pth` = segs 2+3 merged (Tal).
- **RAM: the container is capped at 31 GB and each bear run takes ~11 GB -> at most 2 concurrent runs** (a 3rd got OOM-killed).
- Figure tool: `analysis/plot_mu_ellipses.py` (segment map + mu(direction) curve per segment / grid node / whole object, table).
  Figures in `demo/shic/comparison_aniso_vs_baseline/ellipses_*.png`.
- grid6: front half consistently wider horizontally (mu_h > mu_v, ratio up to 1.47), back half ~circular.
  merge23_aniso: the merged big segment ratio **1.30 -- MORE elongated than either half** (assistant predicted rounder; wrong).
  Caveat: merging also changes neighbour sampling (pairs longer: mu_2D 313 vs 220 px), not only mu.
- global_aniso: ONE ellipse for the whole bear came out ~a circle (ratio 1.04, mu ~0.75) -- directions cancel over the object.
- merge23_learn (iso on the merged map) done -> merged seg iso mu 0.634 vs directional 0.615 vert / 0.676 horiz.
- **6-run back-projection** `demo/shic/comparison_aniso_vs_baseline/backproj_all6_{soft,top1}.png`: runs 1-4 (baseline, per-seg dir,
  grid6, global dir) look alike. **The MERGE (5, 6) is the visible change: larger, more regular cells over the body** -- and it shows
  with iso mu too (5), so it comes from merging the segments (neighbour sampling spans the whole body), NOT from directional mu.
  5 vs 6 alike. Tal's verdict pending. PCA of merge23_aniso was OOM-killed (not needed).
- **Tal sees an improvement in the merged runs.** The ellipse was NOT converged at step 300 with mu_lr 1e-2 (ratio still rising
  1.13 -> 1.27 median). **mu_lr 5e-2** (`MU_LR=` in run_shicbear_main_T.sh, `..._merge23_mulr5e-2`): merged seg ratio **1.30 -> 1.46**,
  axis 124 -> 133 deg, median plateaus ~1.37-1.45 (converged). Figures `ellipse_merged_seg2_zoom_mulr.png`, `backproj_merged_mulr.png`.
  Forcing flatter ellipses (a penalty) was explicitly NOT recommended: it imposes a distortion the data does not support.
- **ALL 7 arms re-run WITH LORA-W (Tal)**: `scripts/run_shicbear_mu_lora.sh` (production LORA: all layers r4 lr 1e-3, read alpha 0.5,
  small analysis at alpha 0.5 only; env MU/MU_LR/MU_GRID/FINE/SUFFIX). Queue `/workspace/logs/mu_lora_queue.sh` (xargs -P 2),
  logs `/workspace/logs/mulora_<tag>.log`. The LORA iso baseline is `..._r0921` (the older un-suffixed LORA arm has no mu_scale.pth).
  **DONE 19:20 IDT, all 7.** Figures `demo/shic/comparison_aniso_vs_baseline_lora/` (`backproj_all7_{soft,top1}.png`, `ellipses_*.png`).
  Ellipses are SHARPER under LORA than without: per-seg seg2 1.38 (vs 1.21), seg3 1.16 (vs 1.10); grid median 1.30 max 1.52;
  global 1.14 (vs 1.04); merged 1.42 @ mu_lr 1e-2 (vs 1.30), 1.43 @ 5e-2 (so under LORA the lr no longer matters).
  Visual verdict: Tal's (assistant could not view images -- Read hook timing out).

## STATE AT POD CLOSE — 2026-09-20 (twenty-seventh pod). **NOTHING IS RUNNING.** Tal closes the pod himself.
**The day: a 3x RTX 2000 Ada pod was validated, a real blocking bug in `build_segment_index` was found by the smoke
test and fixed, and the DensePose-LVIS run reached 104/132 with ZERO failures before Tal stopped it for the night.**
### (DONE on the twenty-eighth pod: the queue was relaunched and finished 132/132 -- do NOT relaunch.)

### THE POD: 3x RTX 2000 Ada, sm_89 -- WORKS. "max 1" in the rental listing is irrelevant to us.
Tal's worry was that 3 GPUs might not be "connected together" and that the listing said max 1. **Neither matters:**
- **sm_89 (Ada), so the hard constraint from the twenty-sixth pod is satisfied.** Verified with a real kernel on EACH
  of the three devices separately (`CUDA_VISIBLE_DEVICES=$g` loop), not just `cuda.is_available()`. torch 1.12.1+cu113,
  kaolin 0.14.0 both fine.
- **GPU interconnect is irrelevant to this workload.** `scripts/run_lvis_queue.sh` does NOT use DDP/NCCL. It shards the
  instance list round-robin and runs one INDEPENDENT `run_lvis_worker.py` process per GPU under its own
  `CUDA_VISIBLE_DEVICES`. Zero bytes cross between cards. `nvidia-smi topo -m` showed PHB/NODE (plain PCIe, no NVLink)
  and it makes no difference. **Do not reject a pod for lacking NVLink/P2P on account of this queue.**
- **`nproc` 48 but the cgroup quota is 15.3 CPUs, and it is cgroup v1 here** (`/sys/fs/cgroup/cpu/cpu.cfs_quota_us`
  = 1530000 / period 100000), not v2. `default_num_workers()` already has the v1 fallback, so it picks 16 per worker.
  3 workers x 16 = 48 Dijkstra processes on a 15.3-CPU quota (~3x oversubscribed) -- deliberately NOT changed before a
  production run, same reasoning as the twenty-fifth pod. Costs seconds; the geodesic step is ~19 s/instance.

### **THE BUG THE SMOKE TEST CAUGHT -- `build_segment_index` crashed on an EMPTY segment (2 of 4 instances)**
**This is why the smoke test was worth running: it was NOT a rare degenerate instance, it was systematic and would
have failed a large fraction of the 132.** `NUM_GPUS=2 ANN_IDS="256 1328 3044 4777"`: 256 and 1328 scored, **3044 and
4777 both died** with the identical `IndexError('index 0 is out of bounds for axis 0 with size 0')` at
`modules/relational_loss.py:116`, `segment_pixel_coords[s, n:, 0] = int(rows[0])`.
- **Root cause:** `train_relational_loss.py`'s `--geodesic` path passes `build_segment_index` a COPY of
  `fine_segments` with every non-geodesic-safe pixel zeroed (the fix for disconnected specks being drawn as
  neighbours). A fine segment lying ENTIRELY outside the mask's largest connected component loses **all** of its
  pixels that way, so `np.nonzero(fine_segments == s)` returns empty and the padding line reads `rows[0]`.
  `build_segment_index`'s own docstring assumed every segment has >= `min_pixels_in_object` members -- true of the
  ORIGINAL `fine_segments`, not of the geodesic-safe copy the caller actually hands it.
  | instance | segments | emptied segment | its px inside the LCC mask | centers in it |
  |---|---|---|---|---|
  | lvis3044 | 10 | #4 (452 px -> 0) | **0** | none |
  | lvis4777 | 17 | #14 (92 px -> 0) | **0** | none |
- **Why it is safe to simply skip an empty segment:** measured on both instances, `geodesic_safe_mask` is a strict
  SUBSET of the LCC that centers are drawn from, and the emptied segments have **zero** pixels inside that LCC. So no
  center can ever carry such a segment id, `segment_pixel_count[s] == 0` keeps every sampler away, and the padding
  slots are never read. Also verified: **no segment anywhere has LCC pixels but zero safe pixels.**
- **The fix, two parts:**
  1. `modules/relational_loss.py` -- `if n == 0: continue` in the padding loop, leaving that segment's rows zero.
     **Bit-identical for every instance that currently passes** (the branch is exactly the case that used to raise);
     unit-tested against a reimplementation of the old loop on a synthetic no-empty-segment case.
  2. `phase2/train_relational_loss.py` -- an explicit guard right after `seg_idx` is built that RAISES if any center's
     segment has count 0. Without it, tolerating the empty segment would turn a loud crash into silent garbage:
     `sample_in_segment_neighbors` computes `(rand * 0).long().clamp(max=-1)` = **-1** and would draw the segment's
     last PADDING slot. Never observed; the guard is there so it can never happen unnoticed.
- **Verified end-to-end, not just unit-tested:** ann 3044 was re-run by the production queue and scored in 382 s.
  Also checked directly that every neighbour drawn by `sample_in_segment_neighbors` really belongs to its center's own
  segment on both previously-failing instances.
- **LESSON (same shape as the twenty-fifth pod's cross-instance leak): the smoke test earns its 15 minutes.** Both
  pods' worst bugs were invisible on the instances that had already been run by hand and only appeared on new data.

### THE RUN
```
setsid nohup env NUM_GPUS=3 bash scripts/run_lvis_queue.sh > /workspace/logs/lvis_queue.log 2>&1 &
```
- 44 instances dealt to each GPU; already-scored ones are skipped, so the real work was 127.
- **Measured pace ~300-310 s/instance** (smoke: 357-391 s; it settled faster), vs the ~5.8 min estimate -- the estimate
  held. VRAM **2662 MiB per GPU** of 16 GB, matching the 2.58 GB the slice-first fix predicted.
- **Zero failures in 99 instances run today** (104 scored total, 5 of which predate this pod). **Stopped by Tal at
  104/132 at 23:39 Israel time** to close the pod; 28 instances remain, ~50 min of 3-GPU time.
- **WATCH OUT -- the pod clock is UTC, Tal is UTC+3.** Every ETA quoted from `date` on the pod is 3 hours behind his
  wall clock; this caused a real miscommunication today. Use `TZ=Asia/Jerusalem date` when telling him a time.
- A `setsid nohup` launch prints `[1]+ Done` IMMEDIATELY and the queue log stays empty for ~40 s while the
  `ANN_IDS` python block imports torch and calls `load_instances`. **That is normal, not a failure** -- it was briefly
  misread as one today, and the debug re-run that followed became a DUPLICATE worker on the same instance (both
  writing `data/densepose_lvis/runs/lvis3044/`) before being killed. Check `pgrep -af run_lvis_worker.py` before
  concluding a detached launch died.

### RESUMING (the run is fully interruptible -- nothing is lost)
**DO NOT stop the workers with `pkill -f run_lvis_worker.py` / `pgrep -f ...` from inside a tool-call shell** -- the
pattern matches that shell's OWN `bash -c` command line, so the shell kills itself (exit 144) and the workers survive.
This bit twice today. Get the PIDs with `ps -eo pid,cmd | grep run_lvis_worker | grep -v grep | grep -v 'bash -c'`
and `kill -9 <pids>` explicitly, then confirm with `nvidia-smi` that VRAM dropped to ~2 MiB per card.
Then on the next pod relaunch the exact same command. A worker skips any instance with
an existing results JSON, and that JSON is written only AFTER an instance is fully scored, so an instance killed
mid-flight leaves no partial record and simply re-runs. Only the in-flight instance per GPU is repeated. Leftover
intermediates (~2.1 GB per worker) are overwritten when that instance re-runs. The aggregate only runs automatically
at the end of a complete queue; after a partial run call it by hand:
```
python analysis/aggregate_lvis_results.py --results_dir data/densepose_lvis/results \
  --out_json data/densepose_lvis/results/aggregate.json
```

### PARTIAL NUMBERS -- recorded to show HOW MUCH THEY MOVE, not as a result
| n scored | ours soft | ours argmax | zs soft | SE/inst |
|---|---|---|---|---|
| 26 | 34.92 | 37.04 | 40.24 | 4.54 |
| 59 | 37.37 | 39.50 | 42.43 | 3.49 |
| **104 (final for this pod)** | **35.39** | **37.22** | **39.74** | **2.53** |
Reference: SHIC 33.0 (reproduced 33.09) / CSE supervised 35.7 / zero-shot SD-DINO 48.2.
**The headline wandered 34.92 -> 37.37 -> 35.39 as instances came in** -- a ~2.5-point swing, exactly the noise scale
PROJECT_NOTES already warned about (1/3 subset 90% range 27.3-38.9), and a concrete demonstration of why partials are
not readable. `aggregate.json` at 104 is written and is the record of this pod.
**The one signal stable across all three partials is the ~4-5 point gap over ZS** (35.39 vs 39.74 at n=104), which is
now larger than the SE (2.53) -- the only comparison here that is starting to stand up.
At n=104 ours soft_snap 35.39 sits between SHIC 33.0 and CSE supervised 35.7, but the remaining 28 instances can still
move it by more than that whole spread. **Do not quote a partial number to anyone.**

### STILL OPEN / NOT TOUCHED TODAY
- **Directional mu** -- explained to Tal today, still NOT built. Diagnostic first (angle-binned d3D/d2D per segment on
  ZS + MAIN bear); only if anisotropic, build `--mu_scope segment_aniso` (per-segment 2x2 SPD metric, 3 params via
  Cholesky with `exp` diagonal, init `M = s^2 I` so step 0 is bit-identical to today's isotropic mu). Recorded for
  the writeup: this is standard -- Mahalanobis distance, metric learning (LMNN/ITML), the 2D metric tensor,
  structure tensors, and 3D Gaussian Splatting's anisotropic covariance all use the same object and parametrization.
- Uncommitted: the 12 files from the twenty-fifth pod, PLUS today's two fixes (`modules/relational_loss.py`,
  `phase2/train_relational_loss.py`). Commit when Tal asks.
- sdist ladder verdict; the 09-16/09-17 code commit.

## STATE AT POD CLOSE — 2026-09-20 (twenty-sixth pod, ABORTED AT STARTUP, ~10 min). **NOTHING RAN.** Tal closed the pod.
**The LVIS run did NOT happen: the pod's GPUs were Blackwell, and the `bsb` env cannot execute a single CUDA kernel on them.**
Tal found another option and closed the pod. **Nothing changed in the repo** -- the 12 uncommitted files from the
twenty-fifth pod are untouched, `results/` still holds 255 / 904 / 117683 / aggregate, and the entry below is still
the live plan. Just re-read it on the next pod and launch.

### **HARD CONSTRAINT DISCOVERED — THE GPU MUST BE sm_86 OR sm_89. NOT BLACKWELL. READ BEFORE RENTING.**
The pod came up as **4x RTX PRO 4500 Blackwell (32 GB, sm_120)**. The `bsb` env is **torch 1.12.1+cu113**, whose
compiled arch list ends at **sm_86**:
```
arch list: ['sm_37','sm_50','sm_60','sm_70','sm_75','sm_80','sm_86']
RuntimeError: CUDA error: no kernel image is available for execution on the device
```
This is not a warning that can be ignored -- a bare `torch.randn(64,64,device='cuda') @ x` raises it. `cuda.is_available()`
returns True and `device_count()` returns 4, so **the failure looks like success until the first kernel launches.**
- **Why every earlier pod worked:** the RTX 2000 Ada / A4500 are sm_89 / sm_86, i.e. CUDA major version 8, and a device
  runs cubins built for the same major version. **Blackwell is major 12** -- no minor-version compatibility path, and
  torch 1.12 ships no PTX it could JIT from either. Ada and Ampere work; Blackwell does not.
- **So the rule is: rent Ampere or Ada only.** `4x RTX A4500` ($0.25, sm_86) is both the cheapest option in the table
  below and the only card ever measured on this pipeline. Anything branded **RTX PRO (Blackwell), RTX 50xx, B200** is
  sm_120 and is dead on arrival, whatever its price or VRAM.
- **Check this in 5 seconds before doing anything else on a new pod:**
  ```bash
  source /workspace/activate_bsb.sh && python -c "import torch; x=torch.randn(64,64,device='cuda'); print('GPU OK', (x@x).sum().item())"
  ```
  Note the `source` must NOT be piped (`| tail`) -- a pipe runs it in a subshell, the env never activates, and you end up
  testing `/usr/bin/python3`, which has **torch 2.8.0+cu128** (works on Blackwell) but **no kaolin**. That is how this
  nearly got mistaken for a working setup.

### UPGRADING TORCH WAS CONSIDERED AND REJECTED (not attempted -- recorded so it is not re-litigated blind)
Making the env Blackwell-capable means torch >= 2.7/cu128, which drags **kaolin 0.14.0** (pinned to torch 1.12 /
python 3.9) and the rest of the stack with it. Two reasons not to do it under time pressure: it is a full stack
rebuild, and it would invalidate the **bit-identity verification that the entire twenty-fifth pod was spent
establishing**. If a torch upgrade is ever wanted, it is its own project with its own re-verification, not a step
taken to unblock a rented pod.

### POD FACTS WORTH KEEPING (this pod, for calibration)
- **`nproc` 112, cgroup quota 95.2 CPUs** -- vs 5.1 on the twenty-fifth pod. The `--num_workers` cgroup-sizing fix from
  that pod reads `/sys/fs/cgroup/cpu.max` and would have picked ~95 here, so it scales correctly; it was never exercised.
- Blackwell cards carry 32 GB. Irrelevant to us: phase-2 peaks at **2.58 GB** after the slice-first fix. The VRAM was
  never the reason this pod failed.

## STATE AT POD CLOSE — 2026-09-20 (twenty-fifth pod). **NOTHING IS RUNNING.** Tal closes the pod himself.
**The day: the LVIS pipeline was made ~4x faster and verified bit-identical, and it is READY for a multi-GPU run.**
- **Per instance: ~22 min -> ~5.8 min** on this pod (RTX 2000 Ada). **Disk per instance 9.3 GB -> 2.1 GB.**
- **Tal took a 4x RTX PRO 4000 pod for the full run.** Expect ~1.3-1.5 h for the remaining 129 instances.
- **Nothing committed** -- the day's 12 files are uncommitted but live on the persistent volume, so they survived
  the pod switch. Commit when Tal asks.
- Disk 284 G / 550 G (116 GB freed today, see below).

### WHAT TO RUN ON THE NEW POD
**Smoke-test multi-GPU first (~15 min) -- concurrent workers on real multiple GPUs is the ONE thing that could not be
tested on this single-GPU pod.** The sharding logic itself is verified (disjoint, complete, 33 each at 4 GPUs):
```
NUM_GPUS=2 ANN_IDS="256 1328 3044 4777" bash scripts/run_lvis_queue.sh
```
Then the full run (arm = LORA-W ALL r4 at alpha 0.5, Tal's call; it is the default):
```
setsid nohup env NUM_GPUS=4 bash scripts/run_lvis_queue.sh > /workspace/logs/lvis_queue.log 2>&1 &
```
**GPU — SUPERSEDED, SEE THE TWENTY-SIXTH POD ENTRY ABOVE: the RTX PRO line is Blackwell (sm_120) and CANNOT RUN THIS
ENV AT ALL.** The plan below was to take 4x RTX PRO 4000; the pod that was actually rented came up as 4x RTX PRO 4500
Blackwell and every CUDA kernel failed. **Rent Ampere or Ada only (sm_86 / sm_89) -- in practice, 4x RTX A4500.**
The timing note still stands for whatever card is taken: speeds below are ESTIMATES (assumed ~2.2x the RTX 2000 Ada
this was measured on); the A4500 was the only card with a real measurement behind it. If the first few instances come
in much slower than ~150 s each, the estimate was wrong, not the pipeline.

**Known minor inefficiency, DELIBERATELY not fixed before the run:** each of the 4 workers sizes its Dijkstra pool
from the whole container quota, so 4 x ~16 = ~64 processes land on ~48 vCPU (1.3x oversubscribed). The geodesic step
is only ~19 s/instance, so this costs seconds. A `--geo_workers` pass-through was considered and rejected: changing
verified code immediately before a production run is the larger risk. Fix it after the run if it ever matters.

Cost is independent of GPU COUNT -- the work is a fixed ~11.8
GPU-hours in RTX-2000-Ada units, so more GPUs buys wall time, not a bigger bill; the whole run costs **$2-8 on any of
them**. And **phase-2 peaks at 2.58 GB of VRAM after today's slice-first fix**, so anything above ~8 GB is wasted money
-- do NOT take an A100/PRO 6000/B200, you would be renting VRAM and tensor cores this workload cannot use.
| option | est. wall | est. cost | note |
|---|---|---|---|
| **4x RTX A4500 ($0.25), sm_86** | ~1.8 h | ~$1.85 | **TAKE THIS ONE** -- the only card we have MEASURED, the cheapest, and arch-compatible |
| 4x RTX PRO 4000 ($0.57), sm_120 | -- | -- | **UNUSABLE -- Blackwell.** Was taken 09-20 and the pod came up as PRO 4500; no kernel runs. |
| 4x RTX PRO 4500 ($0.72), sm_120 | -- | -- | **UNUSABLE -- Blackwell.** This is the card the aborted pod had. |
| 8x RTX 5090 ($0.99), sm_120 | -- | -- | **UNUSABLE -- Blackwell.** |
| 4x L4 ($0.49) | ~2.2-2.5 h | ~$4.60 | REJECTED -- slower AND pricier than the A4500; it is a 72W inference card, ~300 GB/s vs the A4500's ~640 GB/s, and our phase-2 loop is bandwidth-bound. |
Resumable: a worker skips any instance with an existing results JSON, so just relaunch after a crash.
Peak disk is ~N_GPUS x 2.1 GB, not 132 x anything -- intermediates are deleted per instance after scoring.
Aggregate runs automatically at the end (`analysis/aggregate_lvis_results.py`, mean over POINTS = SHIC's number).

### THE FIVE SPEEDUPS (all verified bit-identical -- see VERIFICATION below)
1. **2D Dijkstra parallelised** (`--num_workers`, `analysis/build_geodesic_tables.py`): 339 s -> 72 s at 800.
   **`--num_workers` defaults from the CONTAINER's CPU quota, not `nproc`** -- `/sys/fs/cgroup/cpu.max` said
   5.1 CPUs here while `nproc` reported the host's 48. Sizing off 48 thrashed: 24 workers 108.6 s vs 10 workers 72.0 s.
2. **True 2D diameter folded into the table build** (`--true_diameter`): a separate ~90 s process that rebuilt the
   identical graph -> **0.4 s**. `analysis/measure_2d_geodesic_diameter.py` still exists; nothing calls it in the pipeline.
   A sidecar `<table>_meta.json` now carries `diagonal`/`true_diameter_2d` so callers need not load the table to read them.
3. **Cycle v2 return-leg slice-first** (`phase2/train_relational_loss.py`): it built the FULL [2048 x 336278] float32
   table (2.75 GB) and the FULL [336278 x 2304] feature gather (3.1 GB), shipped both to GPU, and only THEN kept the
   stride-5 columns (4% of them). Now slices first. **Peak GPU memory 6.29 -> 2.58 GB**, ~55 s/instance.
4. **`--no_step_checkpoints`**: phase-2 wrote 13 x 144 MB of step checkpoints nothing in a production sweep reads.
5. **MERGED PROCESS** (`scripts/run_lvis_worker.py`): one persistent process runs every stage of every instance via
   `runpy.run_path(..., run_name='__main__')`, so the ~52 s of `import torch` per stage is paid once, not 7x/instance.
   NO refactor of the training code -- every stage already has an argparse `__main__`, and
   `phase2/train_relational_loss_l2norm.py` already used this exact pattern. Measured: alpha export 71 s -> 5 s,
   eval 60 s -> 2 s, prep 12 s -> 1 s.

### **THE CROSS-INSTANCE LEAK, FOUND AND FIXED — read this before touching the worker**
Tal asked directly whether a merged process lets instance i influence instance j (an instance = one image + the 3D
shape; they must be independent). **It did, and the bug was real.** `seed_everything()` (called by phase-2's
`load_phase1_encoder`) sets **`torch.backends.cudnn.deterministic = True` process-globally and never restores it**, so
instance i+1's DINO/SD feature extraction picked different conv algorithms than a fresh process would.
- Detected by running TWO instances: the FIRST was bit-identical to a standalone run on every artifact; the SECOND's
  features differed, maxdiff **2.362e-04** over 56% of the map, which propagated into its phase-2 checkpoint.
- Confirmed by isolated probe (same image, same process, toggling only that flag): **maxdiff 2.362e-04, the identical
  number**. torch defaults are `benchmark=False, deterministic=False`.
- Fixed: `reset_global_torch_state()` captures the flags at import and restores them before every stage.
- **The lesson: one instance is not enough to test process reuse.** A single-instance check passes either way.

### VERIFICATION (what was actually proved, not assumed)
- Parallel Dijkstra: `table`/`pixel_to_node`/`coords`/`geodesic_safe_mask` all `torch.equal`, `diagonal` equal to the
  last digit. Folded diameter reproduces the standalone script's number via the identical sweep path.
- Slice-first: unit-tested on the real data -- both the [13452, 2304] features and the [2048, 13452] table `torch.equal`
  between old and new code paths.
- Phase-2 old-vs-new code **on the same GPU**: every weight, `lora_state`, `fourier_basis`, `pred_f` and every step log
  line identical. **Cross-GPU bit-identity is NOT achievable** (an early comparison against the A4500-trained arm showed
  2.7e-2 and proved nothing) -- always compare on one card.
- Worker vs shell, BOTH instances, at the final settings: every artifact bit-identical. The only differing field anywhere
  is `object_mask_path`, a stored string naming the input directory.
- bear3 regression at 800 (`_REGRESS0920` arm): alpha0.5 extent 0.808 both, top1 vertices 465 vs 459/4936, drift
  0.732 vs 0.722. **Tal's visual verdict: identical.**

### MAIN WITHOUT LORA-W, ON THE TWO LVIS INSTANCES (Tal asked, 2026-09-20)
The pre-LORA arm (`rkd_spatial_dist` + learned per-segment mu + 16 in-segment + cycle v2, T=0.01 -- the whole encoder
trains, no frozen delta, so no read-time alpha and `pred_f` comes straight from the phase-2 dir). Run via a new
`--no_lora` flag on `scripts/run_lvis_worker.py`; results in `data/densepose_lvis/results_nolora/`.
| ann | arm | soft-snap | argmax |
|---|---|---|---|
| 904 | LORA-W all r4 a0.5 | 40.31 | 40.54 |
| 904 | **MAIN no-LORA** | **37.85** | **39.54** |
| 904 | ZS | 27.75 | 31.78 |
| 904 | SHIC | -- | 50.61 |
| 117683 | LORA-W all r4 a0.5 | **16.14** | 17.50 |
| 117683 | **MAIN no-LORA** | 16.56 | **15.20** |
| 117683 | ZS | 19.06 | 20.81 |
| 117683 | SHIC | -- | 6.95 |
- **no-LORA wins 3 of the 4 lines**, losing only 117683 soft-snap by 0.4. Drift: no-LORA 0.83/0.87 vs LORA-W ~0.80.
- **VISUALLY the no-LORA back-projection is clearly finer and more regular** -- smaller, checker-like cells where
  LORA-W gives large blobs. Same image, same resolution, only the three `--lora_w_*` flags differ. Figures:
  `demo/shic/lvis_vs_shic_nolora/COMPARE_arms_lvis{904,117683}.png` (three arms stacked) and `SUMMARY_lvis*.png`.
- **THE AWKWARD PART, do not gloss over it: ZS beats BOTH arms on 904** (27.75 vs 37.85/40.31). On that instance
  phase-2 makes things worse, not better. 117683 is the other way round (ZS 19.06, both arms better).
- **5 GT points total.** This does not settle LORA vs no-LORA.
- **TAL'S DECISION (2026-09-20): the full run goes with the LORA-W arm** (LORA-W ALL r4, read at alpha 0.5), which is
  already the default in `scripts/run_lvis_worker.py` / `run_lvis_queue.sh` -- no code change needed. The no-LORA arm
  stays available behind `--no_lora` and is worth revisiting after the full number is in, given that it won 3 of 4
  lines here and its back-projection is visibly finer.

### TOOLING ADDED FOR THE COMPARISON FIGURES
- `analysis/compare_ours_vs_shic_points.py` -- per GT point: our vertex (soft-snap) vs SHIC's (argmax) vs the label,
  the geodesic errors, and a marker PLY (GT green / ours blue / SHIC red).
- `analysis/make_lvis_summary_figure.py` -- composes Tal's layout: original crop + GT points | our back-projection |
  SHIC's back-projection; the mesh from 4 azimuths; legend and per-point errors.
- `scripts/make_lvis_arm_summary.sh` -- **the whole sequence for ONE arm on ONE instance in one command.** Written
  after assembling the first set by hand: the order matters (soft-snap correspondence before back-projection, marker
  PLY before render) and SHIC's panel is COPIED from a previous arm's output rather than recomputed, since SHIC's
  prediction does not depend on which arm of ours is being scored.
- Trap found: `analysis/color_mesh_from_soft_mapping.py` does NOT create its own `--save_dir`; it computes the whole
  mapping and then fails on `torch.save`. Make the directory first.
- Trap found: open3d writes PLY faces as `vertex_indices`, but `analysis/render_colored_mesh.py`'s reader wants
  `vertex_index`. Use `modules.utils.write_ply`.

### ORDER-INDEPENDENCE — TESTED AND PASSED (2026-09-20, after the cuDNN fix)
Worker run on **[255, 904, 117683]**, so 904 sat at position 2 and 117683 at position 3, each behind a DIFFERENT
predecessor than in the run that first exposed the leak. Both were then diffed against their fresh-process (shell)
references: **every artifact bit-identical** -- phase-2 checkpoint, `pred_f`, the alpha export, the pixel features, mask,
fine segments, GT. Only `object_mask_path` differs (a stored string naming the input directory).
So queue position no longer changes anything. Note the test only works with >= 2 instances; see the leak section above.

### 400 vs 800 ON LVIS — what the 2 instances actually say (NOT conclusive)
Both resolutions were run through the full pipeline on the same two instances, so this is a real comparison, not an
estimate. **Four of six numbers are identical**, including BOTH argmax lines:
| ann | arm | 800 | 400 |
|---|---|---|---|
| 904 | ours soft | 36.66 | 40.31 |
| 904 | ours argmax | 40.54 | 40.54 |
| 904 | ZS soft | 27.75 | 27.75 |
| 117683 | ours soft | 16.14 | 16.14 |
| 117683 | ours argmax | 17.50 | 17.50 |
| 117683 | ZS soft | 17.83 | 19.06 |
**This is 5 GT points.** Instance-level SE on the full set is 2.44, so it rules out a catastrophe and nothing more --
it cannot distinguish "no cost" from "a few points worse". Tal's call was to proceed at 400 (the information argument
is sound: we never shrink below the source, we only inflate less). **If the full 132 comes back worse than expected,
re-examine the HYPERPARAMETER REGIME first, not the method**: the fixed 2048 centres are now ~11% of the mask instead
of ~2.8%, which is the part bear3 could not test.

### SUMMARY FIGURES + SHIC BACK-PROJECTION (Tal's layout, 2026-09-20)
`analysis/make_lvis_summary_figure.py` composes, per instance: original crop + GT points | OUR back-projection
(soft-snap) | SHIC's (argmax); the mesh from 4 azimuths with GT green / ours blue / SHIC red; and a legend with the
per-point geodesic errors. Built on `analysis/compare_ours_vs_shic_points.py` (markers + numbers) and
`analysis/shic_infer_correspondence.py` (SHIC's DENSE correspondence, which already writes our format so
`color_image_from_knn.py` back-projects both methods through identical code).
Figures: `demo/shic/lvis_vs_shic/SUMMARY_lvis117683.png`, `SUMMARY_lvis904.png`.
- **Observation worth keeping: on ann 117683 BOTH back-projections look equally blobby** -- neither gives bear3's
  ordered checker. Tal's read was that it is simply a hard image (bear in water, occluded, a second bear's head in
  frame), and SHIC's picture confirms it.
- **And the back-projection looking bad did NOT mean the scored points were bad**: both GT points on 117683 scored
  6.7-17.8 against a dataset mean of 33. The eval samples 2-3 pixels per instance, so the visible mess can live
  entirely in regions nothing measures. Do not read a back-projection as a proxy for the Table 1 number.

### RESOLUTION DROPPED 800 -> 400 (Tal's call, method change, measured)
**The 800 had no justification** -- it came from bear3/guitar happening to be ~800 px natively. Every backbone resizes
internally anyway: **DINO -> 224, SD -> 512, SAM -> 1024**. No LVIS bear bbox reaches 800 (median long side **289**, max
612, 36 of 132 are <= 224), so every instance was being upscaled and then downscaled again.
**Kept FIXED at 400, not native**, because three hyperparameters are pixel-count-dependent and would otherwise mean
different things on instances that differ ~20x in bbox area. Scaled with it:
| knob | 800 | 400 | why |
|---|---|---|---|
| `num_center_pixels` | 2048 | 2048 | Tal: leave it |
| `min_pixels_in_object` | 200 | **50** | an AREA threshold -- area drops 4x when the long side halves |
| `cyc_return_stride` | 5 | **3** | a LINEAR spacing; exact ratio 2.5. **Stride 2 was tried first and OVERSHOT** (20022 return targets vs 13452 at 800 -- phase-2 got no faster). 3 gives 9335. |
- bear3 at 400: **9 segments at both resolutions**, and Tal's visual verdict on the back-projection was "same".
- Caveat recorded: on LVIS, segment counts went UP at 400 (904: 25, 117683: 15) and mask coverage fell 99.5% -> ~96.5%.
  SAM finds more, smaller regions at this scale. Not judged good or bad yet.

### EVAL FOR OUR METHOD — BUILT (`analysis/eval_lvis_ours.py`)
Scores one instance in SHIC's Table 1 metric. **Repeat `--arm name=path` rather than invoking once per arm** -- the cost
is startup (~60 s: imports + the pixel-feature file), not the scoring, so two arms in one call cost 60 s, not 120 s.
- Reports **soft_snap (ours, read T=0.01, k=10) AND argmax (SHIC's rule)**, each with an `all` and an `in_mask` block.
- Every instance also scores **ZS** (phase-1's `pred_f.pth`) for free -- it is the same file for all 132.
- **NO LABEL LEAKAGE, verified**: `<tag>_gt.pth` is written by `prep_lvis_instance.py` and read ONLY by this script.
  Crop and mask come from `bbox`/`segmentation` alone; `dp_x/dp_y/dp_vertex` never touch segments, geodesics, features
  or phase-2.

### HONEST DIFFERENCES vs SHIC (Tal asked "did we cheat?" -- no, but state these in any writeup)
1. **Mask**: we use the LVIS polygon; the 33.09 SHIC row used bbox crop with NO mask. (SHIC's own masked variant scored
   *worse*, 35.70, so this is probably not an advantage -- but it is an annotation that row did not use.)
2. **Resolution**: ours 400 long side; SHIC 224x224 squashed.
3. **Test-time training**: phase-2 trains on the test image itself (unsupervised). SHIC is feed-forward after training
   once on 6k images. **This is the biggest asymmetry** -- ours is test-time adaptation, a different setting.
4. Decoding rule differs (soft-snap vs argmax), which is why both lines are reported.

### FIRST NUMBERS (2 instances only -- NOT a result, the aggregator says so itself)
| ann | ours soft | ours argmax | ZS soft | SHIC |
|---|---|---|---|---|
| 117683 | 16.14 | 17.50 | 19.06 | **6.95** |
| 904 | 40.31 | 40.54 | **27.75** | 50.61 |
Visual comparison built: `analysis/compare_ours_vs_shic_points.py` renders the mesh with GREEN=GT, BLUE=ours, RED=SHIC
(figures in `demo/shic/lvis_vs_shic/`). On 117683 all three cluster on the shoulder, no flips, SHIC just tighter. On 904
SHIC's markers sit high on the neck while two GT labels are on the front leg. **Instance-level SE on the full set is
2.44 and a 1/3 subset spans 27-39, so nothing here is interpretable until the full 132 are in.**

### NEXT POD
1. **Run the full 132** (command at the top). Then read `data/densepose_lvis/results/aggregate.json`.
2. ~~Clean up the verification dirs~~ **DONE 2026-09-20 (Tal approved)**: `runs_ref`, `runs_ref400`, `runs`,
   `results_ref400` deleted, 300 G -> 279 G. **`data/densepose_lvis/results_ref` was KEPT** (984 K) -- it holds the
   800-resolution eval results, the record behind the 400-vs-800 table above.
   **`data/densepose_lvis/results/` already holds valid 400-setting results for lvis255, lvis904, lvis117683** from
   the final verified code, so the full run will skip those three and start at 129.
3. Commit the day's code when Tal asks: `analysis/build_geodesic_tables.py`, `analysis/eval_lvis_ours.py`,
   `analysis/aggregate_lvis_results.py`, `analysis/compare_ours_vs_shic_points.py`, `analysis/prep_lvis_instance.py`,
   `phase2/train_relational_loss.py`, `scripts/run_lvis_worker.py`, `scripts/run_lvis_queue.sh`,
   `scripts/run_lvis_instance.sh`, `scripts/run_shicbear_400_CHAIN.sh`, `scripts/analyze_shicbear_arm.sh`,
   `scripts/run_shicbear_loraW.sh`.
4. Known rough edge: `analyze_shicbear_arm.sh` hardcodes similarity-heatmap query pixels in 808-space, so that one step
   fails on a 400 arm (back-projection and PCA are fine). Cosmetic.
5. Still open from before: the sdist ladder has only the "1/3 region" verdict; directional-mu diagnostic never run.

## STATE AT POD CLOSE — 2026-09-19 (twenty-fourth pod). **NOTHING IS RUNNING.** Tal closes the pod himself.
- **SHIC Table 1 reproduced for the bear: 33.09 (paper 33.0)**, protocol = ds2_val, bbox crop no mask, argmax, heat geodesics max 228.
  The test set is resolved (ds2_val; 6k/735 = SHIC's training pool). Details in the 24th-pod entry below.
- **Our per-instance pipeline built and timed on one bear: 15.6 min on an A4500, 7.8 GB of intermediates per instance.**
- Tal: phase-2 stays per image (no joint training). Tomorrow: a 4-GPU pod over all 132 bears (full set: a 1/3 subset has 90% range 27-39, too noisy vs 33).
- Kept on disk for developing the eval step: `bsb/data/densepose_lvis/runs/lvis117683/` (7.8 GB, delete after). Nothing committed.

### NEXT POD (Tal: 4 GPUs)
1. **Free disk space first** (Tal). Budget: ~8 GB per instance in flight; the intermediates are deleted after each eval.
2. **Parallelize the 2D geodesic table over CPU cores** (`analysis/build_geodesic_tables.py`, 339 s single-core on 336k mask px): split the
   2048 centres over processes. Also check that `measure_2d_geodesic_diameter.py` (~90 s) scales.
3. **Write the eval step for our method** into `scripts/run_lvis_instance.sh`: features at the GT pixels (`<tag>_gt.pth`, crop coords) vs
   `alpha/alpha0.5/pred_f.pth`. **Main number = SOFT-SNAP (read T=0.01), plus an argmax line** (SHIC is argmax, see the PREDICTION RULE below).
   Geodesics = the cached `eval_shic_bear/bear_heat_geodesics_228.npy` (same bear.obj). Also run **ZS** (phase-1 encoder, no phase-2) on
   all 132 as the baseline row (SHIC's SD-DINO ZS = 48.2). Then **delete the geo table + features** of the instance; keep only a small
   results json per instance.
4. Check end to end on 2-3 bears, then a queue script: 132 instance ids split across 4 GPUs (`CUDA_VISIBLE_DEVICES`), resumable (skip
   instances that already have a results json), plus an aggregate script (mean over points, the same way as `eval_densepose_lvis.py`).
GPU choice (rough estimates only, measured on the A4500: GPU steps ~9.5 min/instance, CPU steps ~7 min before parallelizing). In the RunPod
   list the **RTX 2000 Ada (16 GB) and the RTX 4090 are "1 max" / "2 max" per pod**, so 4-8 of those means separate pods. Bear phase-2 peaks at
   ~6 GB, so 16 GB is enough. The 2000 Ada is ~1.5-2x slower than the A4500 -> ~18-23 min/instance -> 4 GPUs ~10-12 h, 8 GPUs ~5-6 h.
   Pods that allow 4 GPUs: RTX PRO 4000 (24 GB, $0.57), RTX PRO 4500 (32 GB, $0.72) -> ~3-4 h for all 132.
5. Still open from earlier: the sdist ladder has only the "1/3 region" verdict; directional-mu diagnostic; commit the code when Tal asks.

## STATE AT POD CLOSE — 2026-09-18 (twenty-second pod). **NOTHING IS RUNNING.** Tal closes the pod himself.
- Tal's LORA-W verdicts recorded (below): good band α≈0.5-0.75 at r=2/4/16, no ranking between them.
- **LORA-W ALL layers r=4 trained + analyzed** (below). Verdict pending — figure `demo/shic/comparison_bear_loraW_all_vs_last_r4.png`.
- **Directional per-segment mu** (Tal's idea for tomorrow) discussed — see below; nothing built, diagnostic not run.
- Disk 391 G / 550 G. Nothing committed (no new code today; only the figure + notes).

### NEXT POD
1. Tal's verdict on LORA-W all vs last (figure above).
2. **Directional mu:** run the angle-binned d3D/d2D diagnostic per segment (ZS + MAIN bear) FIRST; if anisotropic, build
   `--mu_scope segment_aniso` (per-segment 2x2 SPD metric, init = today's isotropic s, bit-identical at step 0), or Tal's 4-direction
   version if he prefers. Pair direction = image offset centre->neighbour (`neighbor_coords` in `rkd_spatial_dist_loss`).
3. sdist ladder still has no explicit verdict; still-open ideas from 09-17 §8 (second seed, cell-size metric, fast bear SMALL, LORA-F).
4. Commit the 09-16/09-17 code when Tal asks.

## STATE AT POD CLOSE — 2026-09-19 (twenty-third pod, short). **NOTHING IS RUNNING.** Tal closes the pod himself.
- **Direction switched to EVALUATION vs SHIC Table 1** (DensePose-LVIS, geodesic error). Directional per-segment mu is the next
  METHOD direction but is PAUSED. Details in the section just below.
- LORA-W verdict: LAST vs ALL not clear-cut; **runs continue with LORA-W ALL, α ≈ 0.5**.
- Downloaded DensePose-LVIS val annotations (~30 MB) + 6 COCO bear images. No code changed, nothing committed. Disk ~391 G / 550 G.
- New pod GPU was an RTX 2000 Ada 16 GB (may differ next time).

### NEXT POD
1. Discuss/decide the protocol open points below (split, phase-2 per image vs ZS vs joint, bbox crop + mask).
2. First concrete step (proposed, not yet approved): run SHIC's released bear weights (`demo/shic/weights/bear*.pth`,
   `analysis/shic_infer_correspondence.py`) on the 132 ds2_val bear instances, geodesic error normalized to max 228, and check ~33.0.
3. Still open: sdist ladder has only the "1/3 region" verdict; directional mu diagnostic; commit the 09-16/09-17 code when Tal asks.

## 2026-09-19 (twenty-fourth pod) — EVAL SET RESOLVED
- **The test set is DensePose-LVIS ds2_val** (132 bears with points, 3 points each, so about 390 points). The paper's "6k images / 735 bears"
  is the TRAINING pool (unlabelled crops + masks; they use the GT points only for eval). Chain of evidence: SHIC Table 1 CSE row = "[25] evaluated with
  their published weights", [25] = Neverova CVPR'21 (Universal Canonical Maps), which uses **ds2**. The 228 normalization cites DensePose'18 + CSE'20.
  CSE'20 (ds1) itself reports AP/GPS, not geodesic error: LVIS bear = 776 instances, close to SHIC's 735.
- The SHIC repo (github.com/suny-sht/shic) is inference-only: notebook + model, **no eval code**. Its input = RGBA cutout resized to 224x224 (not aspect-preserving),
  so for eval: bbox crop + mask (from the LVIS polygon) is SHIC's native input.

- **SHIC's released weights REPRODUCE Table 1: bear 33.09 (paper 33.0)** with `analysis/eval_densepose_lvis.py` (NEW; ~3 min for all variants, A4500).
  Protocol that matches: ds2_val bear (132 inst / 105 imgs / 393 pts), **bbox crop, NO mask**, resize 224x224, dot-product argmax at the GT pixel,
  potpourri3d heat geodesics on SHIC's bear.obj, max normalized to 228, mean over points, dp_vertex taken as 0-based.
  Other variants: square crop 33.18, square+mask(black bg) 35.70. Geodesics cached at `bsb/data/densepose_lvis/eval_shic_bear/`.
  **Noise:** instance-level SE on the full set = 2.44 (so CSE 35.7 vs SHIC 33.0 is only ~1 SE). Random 1/3 subset (44 inst): 90% range 27.3-38.9;
  1/2 (66 inst): 29.0-37.1. The mean is dominated by large errors (median 18.7), i.e. left/right or front/back flips.
- The SHIC released model is **DINOv2 ViT-S/14 + a learned decoder only**; SD is used in their TRAINING (SD-DINO pseudo-correspondences), not at inference.
- Tal: our phase-2 stays PER IMAGE (no joint training). Options under discussion for the cost: multi-GPU pod, faster GPU, subset.

- **Our per-instance pipeline for LVIS** (NEW): `analysis/prep_lvis_instance.py` (bbox crop, upscaled to long side 800 like bear3, LVIS polygon
  = mask, GT pts in crop px) + `scripts/run_lvis_instance.sh` (SAM fine segs, 2D geo table, sd_square fuse16 features, true 2D diam, phase-2
  MAIN + LORA-W ALL r4, export α=0.5). Features see the unmasked crop; the mask is only for losses/segments/geodesics (as with guitar/bear3).
  **TIMING, one median bear (ann 117683, 336k mask px), A4500, 15.6 min total:** prep 12 s, SAM segs 87 s, **2D geo table 339 s (CPU)**,
  features 148 s, diameter ~90 s, phase-2 257 s, α export 71 s. **Disk: 7.8 GB/instance** (geo table 2.8 GB + features 5.1 GB) -> must be
  deleted after eval (132 x 7.8 GB = 1 TB). Eval step for our method not written yet.

- **PREDICTION RULE — Tal, 2026-09-19, DO NOT FORGET:** SHIC's prediction is **argmax** (top-1 vertex by feature similarity); **ours is
  SOFT-SNAP** (`analysis/color_mesh_from_soft_mapping.py::compute_soft_snap`: softmax over the pixel's top-K vertices at read T -> weighted
  3D position -> nearest vertex). Our LVIS eval must predict with soft-snap (read T=0.01, as in our analyses), and should also report
  argmax for an apples-to-apples line against SHIC's 33.09.

## 2026-09-19 (twenty-third pod) — EVALUATION vs SHIC Table 1 (directional mu PAUSED, Tal's call)
- **Clarified:** Tal's "sdist ladder: 0.6 and 0.65 both good, can't tell which" = the LORA-W r16 α verdict (already recorded below).
  The real sdist ladder has only "1/3 of anchor (w=4.3e-4) is the interesting region".
- Figure (soft only, labelled rows): `bsb/demo/shic/comparison_bear_loraW_all_vs_last_r4_SOFT.png`.
  **Tal's verdict:** can't tell LAST vs ALL apart yet (not clear-cut); **use LORA-W ALL for runs going forward**, **α ≈ 0.5 region** is the one he likes.
- **SHIC Table 1 (from the paper, arXiv 2407.18907):** DensePose-LVIS, 7 classes, geodesic error (lower better), max geodesic
  normalized to 228, heat-solver geodesics. Bear: CSE (sup.) 35.7 / zero-shot SD-DINO 48.2 / SHIC 33.0. Avg: 26.6 / 36.2 / 24.9.
- **Data downloaded:** `bsb/data/densepose_lvis/densepose_lvis_v1_{ds2,ds1}_val_v1.json` (detectron2 DENSEPOSE_DATASETS.md URLs);
  images are COCO 2017 (`coco_url` per image; 6 bears in `coco_imgs/`). Example figure `bear_gt_examples.png` there.
- **Bear (ds2_val):** 132 instances with points in 105 COCO images; almost all (129) have **3 (pixel, vertex) pairs**.
  `dp_x/dp_y` are in a 256x256 frame over the bbox; polygon segmentation provided. `ref_model = bear_4936` = SHIC's `bear.obj`
  (4936v), so GT vertex ids apply directly. Data is hard: small/occluded bears, statues, signs.
- **Open points for the protocol:**
  1. Split: the paper says "6k images, 735 bears", which does not match ds2_val (223 bear instances). Plan: run SHIC's released
     weights on this set first and check we get ~33.0, validating the protocol before measuring ours.
  2. Structural: our phase-2 trains on ONE photo. Options: (a) ZS on all 105 images (cheap); (b) phase-2 per image (~11 min each,
     ~20 h for the bear); (c) phase-2 on all images jointly (a method change).
  3. Prediction: per GT pixel take the argmax vertex, then geodesic error GT -> predicted vertex. Open: crop to bbox + mask before
     feature extraction?

## 2026-09-18 (twenty-second pod) — TAL'S LORA-W VERDICTS
- **LORA-W good arms (Tal, visual):** r=16 α=0.6 and α=0.65 (`comparison_bear_loraW_r16_fine_alpha.png`; "both good, can't tell
  which is better"); r=2 α=0.75, r=4 α=0.75, r=16 α=0.5 or α=0.75 (`comparison_bear_loraW_rank_alpha.png`). He did not rank them.
  So the good band is roughly α 0.5-0.75, at every rank tested.
- Note: Tal first called the α 0.6/0.65 figure "the sdist ladder"; those values exist only in the LORA-W r16 fine-α figure.
  **The sdist ladder (`comparison_bear_anchor_dist/sdist_ladder_ldist1of10.png`) still has no explicit verdict** beyond 09-17's
  "the 1/3 region is the interesting one".
- **LORA-W ALL layers, r=4 — RUN** (`LAYERS=all RANK=4 ALPHAS="0.5 0.6 0.75"`, log `logs/shicbear_loraW_all_r4.log`):
  6 Linear layers, 119,820 params. **drift@300 0.732** (last r4 0.868, MAIN 0.908). mu_s max 2.57.
  | α | 0.5 | 0.6 | 0.75 | 1 |
  |---|---|---|---|---|
  | top1 cov | 9.42% | 9.30% | 7.98% | 7.66% |
  | soft cov | 20.64% | 20.04% | 19.37% | 18.78% |
  | extent | 0.808 | 0.808 | 0.811 | 0.814 |
  Soft cov barely moves with α (20.6->18.8%; last r4: 22.1->14.4%) -> α is a much weaker knob here, since the update is no longer
  linear in α. At α=1 the cells are larger than last r4 α=1. Figure `demo/shic/comparison_bear_loraW_all_vs_last_r4.png`. Tal's verdict pending.
- **Tal's idea for TOMORROW: DIRECTIONAL per-segment mu.** Problem: one isotropic mu per segment; a long, narrow segment
  gets the scale that fits its long axis, which may be wrong across its width (maybe the bear's belly: wide, not tall).
  Tal's proposal: ~4 learned mu per segment for the image-offset directions 0/90/45/135 deg (up-down, left-right, two diagonals),
  interpolated for angles in between. Assistant's suggestion: a per-segment 2x2 SPD metric tensor M
  (d_pred = sqrt(dp^T M dp), 3 params, Cholesky/log parametrization) is the smooth, principled version of the same thing.
  Diagnostic before building: bin each segment's d3D/d2D by pair angle on an existing run; a single mu is fine if flat.
  Not built.

## STATE AT POD CLOSE — 2026-09-17 (twenty-first pod). **NOTHING IS RUNNING.** Tal closes the pod himself.
**The day in one list** (details in the 2026-09-17 section just below):
- **Guitar set aside.** Tal's verdict on `comparison_mesh_isolated`: neck-rings SMOOTHER (cleaner seams), isobbox MORE ACCURATE ->
  MAIN stays on isobbox, neck-rings stays PROTECTED. Work moves to harder, more-3D objects: **the bear**.
- **The bear's proportion problem is created by `rkd_spatial_dist` in the first ~10 steps of phase-2** — not by phase-1 (view
  re-centring changed nothing), not by cycle. ZS has LARGE (SHIC-like) cells; by step 5-15 of MAIN they are small. w=0 control = ZS.
- **At the guitar's weights, spatial is ~770x the anchor on the bear.** Calibrated: spatial = anchor at w≈1.3e-3.
  **Tal: the interesting region is sdist ≈ 1/3 of the anchor (w=4.3e-4), L_dist at 1/10 of the anchor (γ=2.29e-5).** 1/9 and weaker -> ZS.
- **LORA-W (FROZEN-DELTA) built and run**: output layer, r = 2/4/16, read-time α. Smaller r keeps larger cells; α 0.5-0.75 interesting.
  **Tal: "nice results, not perfect yet" — he will look properly later / tomorrow and then we document his verdict.**
- Reply language: **Hebrew short by default; dense technical explanations in English** (Tal).
- **Disk quota = the 550 G /workspace volume** (`du -sh /workspace`; `df` shows the whole network FS). **388 G used at close.**
- **Nothing committed today** (file list in §7).

### NEXT POD
0. **Tal said: stop and think before new runs.** Nothing is queued on purpose.
1. **Tal's verdicts to record**: the full sdist ladder (`demo/shic/comparison_bear_anchor_dist/sdist_ladder_ldist1of10.png`) and LORA-W
   (`demo/shic/comparison_bear_loraW_rank_alpha.png`, `demo/shic/comparison_bear_loraW_r16_fine_alpha.png`).
2. The two candidates side by side: (a) MAIN + anchor λ=3.5e-7 + L_dist γ=2.29e-5 + sdist w=4.3e-4; (b) LORA-W r=2 α≈0.75 (no anchor).
3. Ideas raised, NOT approved (§8): second seed for both candidates; a direct per-cell-area metric (extent is not a cell-size proxy);
   a fast one-process bear SMALL analysis (the current one is ~5 min per arm/α and dominated today's queue time); LORA-W + weak
   sdist; LORA-W on all layers; LORA-F.
4. Commit today's code when Tal asks.

## 2026-09-17 (twenty-first pod) — details

### 1. Clarifications / decisions early in the day
- In-segment-only neighbour sampling (`NBR_IN=16 NBR_OUT=0`) IS already the recipe; 09-16 listed it only as a suspected cause.
- **Bear proportion ideas 1 (visible diameter) and 2 (ZS-fixed mu): CLOSED by Tal.** Tal: SHIC's larger cells look more correct.
- Squash is NOT used anywhere live (bear arms use `sdsquare_fuse16`; phase-1 renders are square so the SD framing is moot). Only
  old on-disk runs (PROTECTED squash, 09-03 bear mu3dscale arms, `bear3_dfd_crossview_ZS` analysis) carry it.

### 2. Bear phase-1 view distribution — tested, NOT the cause
- Bear phase-1 sampled views around azim 0 (script default = the bear's FAR side); photo is at ~135 (head-front 90). Bear mesh is
  also anisotropic (edge CV 0.863, area max/med 33) — remesh parked (breaks SHIC vertex ids / UV).
- `scripts/run_shicbear_phase1_az135_CHAIN.sh`: phase-1 retrained with ONLY `--frontview_center 0 2.356` ->
  `experiments/shic_bear/encoder_dfd_crossview_az135_phase1` (loss 0.2287->0.1953 vs old 0.2228->0.1907). Its render cache was deleted.
  | ZS (sd_square, read T 0.01) | top1 cov | soft cov | extent max/D | p99/D |
  |---|---|---|---|---|
  | phase-1 old (azim 0) | 9.62% | 25.57% | 0.907 | 0.730 |
  | phase-1 new (azim 135) | 13.11% | 25.00% | 0.904 | 0.709 |
  Visually old ≈ new. Figure `demo/shic/comparison_bear_phase1_az135/zs_old_vs_new_phase1.png`.
- **KEY: ZS cells are LARGE (even too large — one big body blob); phase-2 makes them small.** The "ZS over-spreads (0.91)" premise
  was wrong: `extent max/D` is set by scattered outliers, NOT cell size. Don't use it as a cell-size proxy (a direct per-cell area
  metric was suggested, not built).

### 3. Bear analysis infrastructure
- MAIN bear run dir: `/workspace/bsb/demo/shic/bear3_sdsquare_truediag2d_mu_learn_perseg_cycv2T0.05_c1.676e-05_retstride5_T0.01_seed0_phase2/`
  — FULL analysis done: `analysis_summary.png`, `step_progression_grid.png`, `analyze/` (k1/10/100, soft, tracked-9, hard-snap, PCA, heatmap).
- New: `scripts/analyze_shicbear_arm_FULL.sh` (SMALL + colorings + step grid + extent + summary), `analysis/topmatch_geo_extent.py`
  (reproduces MAIN 0.795), `build_analysis_summary.py` got `--soft_dir_name/--bp_k1_path/--bp_soft_path` (guitar defaults unchanged).
  Bear summary split widths: knn 808, backproj 750, hard-snap 808.

### 4. WHEN do the cells shrink — early steps
- MAIN bear step 25 (`.../step25_small/`) already looks like step 300 (top1 9.2%, soft 21.1%).
- `scripts/run_shicbear_main_early_steps.sh`: 25-step rerun, ckpt every 5 (`encoder_..._phase2_early_every5`), grid
  `.../early_steps/early_steps_grid.png`. Rerun not bit-identical (GPU shared with another job): weights max|diff| 1.2e-3, pred_f cos
  0.999999, top1 agreement 99.3% — equivalent.
  | step | 0 (ZS) | 5 | 10 | 15 | 20 | 25 |
  |---|---|---|---|---|---|---|
  | soft cov | 25.6% | 23.2% | 20.7% | 20.9% | 21.2% | 20.9% |
  | extent | 0.907 | 0.819 | 0.820 | 0.829 | 0.837 | 0.837 |
  | drift | 1 | 0.995 | 0.990 | 0.984 | 0.978 | 0.973 |
- Step 5 breaks ZS's body blob; cells reach ~final size by 15-20. **Tal: step 10 is interesting for proportion** — proportion kept,
  not yet accurate -> motivates holding the model near ZS (anchor + L_dist) while weakening spatial.

### 5. anchor + L_dist on the bear, and the rkd_spatial_dist weight
All arms: MAIN (rkd_spatial_dist + learned per-seg mu + 16 in-seg + cycle v2 c=1.676e-5, T=0.01) + soft anchor T=0.01 λ=3.5e-7 +
L_dist T=1, scaled by `--rkd_spatial_dist_weight` w. Under Adam, lowering w == raising anchor+L_dist together at a fixed ratio
(cycle also gains relatively). Script `scripts/run_shicbear_mainplus_rkdw_SWEEP.sh` (env `WS`, `DIST`). Figures in
`demo/shic/comparison_bear_anchor_dist/`.
- **Guitar weights, uncalibrated** (`scripts/run_shicbear_anchor_dist_CHAIN.sh`, then the sweep):
  | w | L_dist γ | top1 cov | soft cov | extent | anchor_KL | ZS agree |
  |---|---|---|---|---|---|---|
  | MAIN (no anchor) | — | 8.47% | 18.15% | 0.795 | — | — |
  | 1 | 2.8e-6 | 8.23% | 17.67% | 0.795 | 7.52 | 0.042 |
  | 0.3 | 2.8e-6 | 8.55% | 18.25% | 0.801 | 5.75 | 0.043 |
  | 0.1 | 2.8e-6 | 8.65% | 17.22% | 0.801 | 4.12 | 0.053 |
  | 0.03 | 2.8e-6 | 8.25% | 18.27% | 0.813 | 2.82 | 0.055 |
  | **0** | 2.8e-6 | 12.01% | 27.96% | 0.914 | 0.60 | **0.823** |
  All w>0 look like MAIN. **w=0 = ZS -> the shrink comes from rkd_spatial_dist, not cycle.** Also ran the SECONDARY baseline exactly
  (mu 1, 8in+8out, T=1 — knobs Tal rejects; reference only): 6.18% / 18.98%, extent 0.927.
- **CALIBRATION** (at the w=0.03 run's step 25, which is kept; log `/workspace/logs/shicbear_anchor_calibrate.log`): sdist grad
  1.446e-3 (unweighted), anchor 5.383 -> λ at equal norms **2.69e-4** (guitar 3.5e-7), L_dist 8.2e-3. At guitar weights spatial is
  **~770x** the weighted anchor; **equal at w≈1.3e-3**. L_dist at 2.8e-6 is ~1/80 of the anchor; **1/10 = γ 2.29e-5**.
- **Calibrated ladder:**
  | w | vs anchor | L_dist | top1 cov | soft cov | extent | anchor_KL | ZS agree |
  |---|---|---|---|---|---|---|---|
  | 3.9e-3 | 3x | 1/80 | 6.04% | 18.84% | 0.825 | 1.70 | 0.111 |
  | 1.3e-3 | 1x | 1/80 | 5.85% | 18.50% | 0.834 | 1.28 | 0.184 |
  | 1.3e-3 | 1x | 1/10 | 6.12% | 18.80% | 0.823 | 1.42 | 0.188 |
  | **4.3e-4** | **1/3** | 1/80 | 7.31% | 20.42% | 0.805 | 1.06 | 0.289 |
  | **4.3e-4** | **1/3** | **1/10** | 5.69% | 19.10% | 0.817 | 1.16 | 0.266 |
  | 1.4e-4 | 1/9 | 1/10 | 8.04% | 21.96% | 0.812 | 0.95 | 0.429 |
  | 4.8e-5 | 1/27 | 1/10 | 9.54% | 24.78% | 0.807 | 0.75 | 0.631 |
  - 3x still MAIN-like; 1x mixed; **1/3 = larger cells without ZS's blob — TAL AGREES THIS REGION IS THE INTERESTING ONE**; 1/9 and 1/27
    the ZS body blob returns. L_dist 1/10 vs 1/80: acts a little (L_dist 0.370->0.357, tail>0.2D 0.80->0.78), small visual effect.
  - top1 coverage drops to ~6% at 3x/1x (fewer, bigger hub vertices).
  - Figures: `sdist_calibrated_sweep.png`, `ldist_1of80_vs_1of10.png`, `sdist_ladder_ldist1of10.png` (the full ladder).
  - **Not yet**: a second seed; eval numbers (bear has none — judged by eye vs SHIC).

### 6. LORA-W — the FROZEN-DELTA direction, built
- **Names: `LORA-W` = LoRA on the encoder WEIGHTS (W_frozen + α·B·A). `LORA-F` = low-rank addition on the vertex FEATURE table
  (F_old + U·V) — not built, maybe later.** Tal's idea was LORA-F; LORA-W chosen first for smoothness over the mesh.
- Caveats agreed: freezing alone protects nothing — the rank is the protection; features must still move in the photo-feature space.
- **Decisions (Tal agreed to all):** output Linear only (feature change has rank ≤ r and stays smooth, since the frozen h(x) is smooth);
  r=16; LayerNorm/bias frozen; lr 1e-3; **MAIN WITHOUT anchor** (LoRA is meant to replace it); bear.
- Code: `modules/lora.py` (`LoRALinear`, `apply_lora_w`, `merged_state_dict`, `merge_lora_into_state_dict`; CPU unit test: step 0
  identical, merged == live 9e-8, α rebuild exact, rank == r). Trainer flags `--lora_w_rank` (0 = off, unchanged path),
  `--lora_w_layers last|all`, `--lora_w_lr`. Checkpoints store MERGED weights in `encoder_state_dict` (every loader works) + raw
  `lora_state`. `analysis/export_pred_f_lora_alpha.py` (read-time α). `scripts/run_shicbear_loraW.sh` (RANK/LAYERS/LR/ALPHAS).
- **r=16 result** (73,728 trainable params; step-0 drift 1.000000; step-300 drift **0.852** vs MAIN 0.908; mu_s max 3.52):
  | α | 0 (ZS) | 0.25 | 0.5 | 0.75 | 1 | MAIN |
  |---|---|---|---|---|---|---|
  | top1 cov | 9.62% | 10.60% | 10.68% | 9.26% | 8.33% | 8.47% |
  | soft cov | 25.57% | 23.50% | 20.46% | 16.65% | 13.86% | 18.15% |
  | extent | 0.907 | 0.907 | 0.801 | 0.805 | 0.758 | 0.795 |
  α=1 ≈ MAIN; 0.75 tidier/larger cells; 0.5 ZS blob partly back. **Tal: interesting, mainly α 0.5 and 0.75.**
  Figure `demo/shic/bear3_..._loraW_last_r16_lr1e-3_T0.01_seed0_phase2/loraW_alpha_sweep.png`.
- **DONE** `scripts/run_shicbear_loraW_next_CHAIN.sh` (log `logs/shicbear_loraW_next_chain.log`): r16 finer α, r=2, r=4.
  Figures `demo/shic/comparison_bear_loraW_rank_alpha.png` (r × α 0.5/0.75/1 + SHIC/ZS/MAIN), `demo/shic/comparison_bear_loraW_r16_fine_alpha.png`.
  | rank | trainable | drift@300 | soft cov α=0.5 / 0.75 / 1 | top1 cov α=1 | extent α=0.5 / 0.75 / 1 |
  |---|---|---|---|---|---|
  | 2 | 9,216 | 0.871 | 23.52 / 19.85 / 16.11% | 8.00% | 0.910 / 0.807 / 0.789 |
  | 4 | 18,432 | 0.868 | 22.12 / 18.94 / 14.36% | 7.54% | 0.896 / 0.805 / 0.759 |
  | 16 | 73,728 | 0.852 | 20.46 / 16.65 / 13.86% | 8.33% | 0.801 / 0.805 / 0.758 |
  r16 finer α soft cov: 0.6 19.59%, 0.65 18.64%, 0.7 17.56%.
  - Assistant's read: smaller rank keeps LARGER cells at α=1 (r=2 α=1 is between MAIN and ZS); r=2 α=0.75 is large and structured.
  - **Even r=2 drifts MORE than MAIN** (0.871 vs 0.908): cosine drift is not limited by rank — a rank-2 update can shift every
    vertex's feature along a shared direction (big cosine change) without making them more distinctive. Drift is a poor protection proxy here.
  - Tal (end of day): nice results, not perfect yet; proper verdict later / tomorrow. Note: bear SMALL analysis is ~5 min per α
    (old multi-process script) — most of the chain's time.
- Gotcha: a `while pgrep -f <script>` queue waiter matches its OWN `bash -c` command line and waits forever. Wait on a PID instead.

### 7. Housekeeping
- **Disk:** quota = 550 G `/workspace` (not `df`). Cleanup (Tal approved): `data/shic_bear/encoder_data_az135` (36 G) + 179 step
  checkpoints from 15 closed bear arms (mu_closed, zsfixed, both visdiam, MAIN T=1, SECONDARY, mainplus w=1/0.3/0.1/0.03 — w0.03 keeps
  step 25 —, w=0, four old mu3dscale arms). Kept steps: MAIN T=0.01, calibrated ladder, early_every5, LORA-W. **367 G / 550 G.**
  Notes backup before the mid-day restructure: `archive/PROJECT_NOTES_backup_2026-09-17_midday.md`. **388 G at pod close.**
- **Uncommitted, new/changed today:** `modules/lora.py`, `phase2/train_relational_loss.py` (LORA-W flags),
  `analysis/{topmatch_geo_extent,export_pred_f_lora_alpha}.py`, `analysis/build_analysis_summary.py`,
  `scripts/{analyze_shicbear_arm_FULL,run_shicbear_phase1_az135_CHAIN,run_shicbear_main_early_steps,run_shicbear_anchor_dist_CHAIN,run_shicbear_mainplus_rkdw_SWEEP,run_shicbear_loraW,run_shicbear_loraW_next_CHAIN}.sh`
  — plus everything the 09-16 entries list as uncommitted.

### 8. Ideas raised today, NOT approved (so nobody re-derives them)
- Second seed for the two candidates (sdist 1/3 + anchor + L_dist 1/10; LORA-W r=2 α 0.75).
- Direct cell-size metric: mean back-projected pixel area per checker cell (extent max/D failed as a proxy, §2).
- Fast bear SMALL analysis: port `analysis/analyze_arm_small.py` (one process, ~20 s on the guitar) or skip PCA/heatmap for α variants.
- LORA-W combined with a weak sdist / anchor; LORA-W on all Linear layers; LORA-F.
- "Early stop at step 10" as a control for anything that looks like a slowed-down MAIN (we already have MAIN step 10 in `early_steps/`).

## STATE AT POD CLOSE — 2026-09-16 (twentieth pod). **NOTHING IS RUNNING.** Tal closes the pod himself.
**The day in one list** (details: "THE BASELINES — UPDATED" and "SHIC comparison revisited" sections below):
- **BASELINES CHANGED**: MAIN = isobbox + MAIN recipe at **T=0.01** (89.4/89.0/88.0). PROTECTED: the old T=1 MAIN, and the
  neck-rings run (identical recipe, only the mesh — run_config diff verified). **New arms compare vs MAIN (T=0.01) ONLY** — not
  vs neck-rings, not vs squash (squash = BUG B).
- **SHIC on the guitar: DROPPED** (no public training code).
- **SHIC-bear on the MAIN recipe** (`scripts/run_shicbear_main_T.sh`, knobs `T`, `MU`=learn|closed|fixed1|zsfixed, `VISDIAM3D`;
  analysis `scripts/analyze_shicbear_arm.sh`): soft coverage 18.15% = SHIC's 18.19%, top1 8.47% vs 14.51%.
  **Tal: the PROPORTIONS look wrong** — our back-projected cells are ~2x smaller than SHIC's (image spread over too much mesh).
  - Ruled out: guitar leakage (none except c), T=1 (**Tal rejected, hurts**), closed-form vs learned mu (near-identical).
  - Tal rejected up front: fixed global mu (hurts locations), 8in+8out neighbours (breaks runs).
  - Tried and FAILED to zoom in: visible-part 3D diameter (`--geo_diag_3d`, with learned mu AND with mu frozen at 1),
    per-segment mu fixed from ZS (`--mu_init_path`, zooms OUT). **The global 3D normalizer is not the lever — hypothesis refuted.**
  - Extent diagnostic worth reusing (top1-matched vertex set, max geodesic / D): SHIC 0.71, old mu=0.6 0.62, MAIN 0.80, ZS 0.91.
- New reference renders `demo/shic/colored_mesh/checker16_uv_azim{180,90}.png` (side / head-front) head every bear figure.
- **Reply language: HEBREW, short** (Tal, 2026-09-16) — refined 09-17: dense technical explanations in English.

### NEXT POD
1. Proportion problem on the bear is OPEN, cause unknown. Untested directions: ZS itself already over-spreads (0.91), so the
   spread may come from phase-1 (bear phase-1 was trained on 09-03 with the raw mesh and frontview default); the in-segment-only
   neighbour sampling (local pairs cannot see global extent — but Tal rejected out-of-segment pairs); the fine segments on the bear
   are very coarse (2 segments hold 95% of centres).
2. Tal's visual verdicts OPEN: neck-rings mesh-isolated pair (from 09-16 nineteenth pod), all bear arms.
3. **Nothing committed.** New/changed today: `phase2/train_relational_loss.py` (`--geo_diag_3d`, `--mu_init_path`),
   `analysis/estimate_visible_geo_diameter.py`, `analysis/perseg_mu_from_zs.py`, `scripts/run_shicbear_main_T.sh`,
   `scripts/analyze_shicbear_arm.sh`, `scripts/run_shicbear_T1_and_closed_CHAIN.sh`, `scripts/run_shicbear_visdiam_zsfixed_CHAIN.sh`
   — plus everything listed under the nineteenth pod's NEXT POD.
4. Gotcha: editing a bash script while it runs can corrupt the run (bash reads scripts incrementally) — it survived today, don't repeat.

## 2026-09-16 (nineteenth pod) — **NECK-RINGS MESH: the neck gap was a real defect, and filling it REMOVES the long neck cell**

### The finding that started it
`meshes/guitar.obj`'s neck is a tube of **13 rings of 36 vertices**, spaced 0.04-0.066 apart — except
between y=-0.0267 and y=+0.2944, where there is a **0.3211 gap with ZERO vertices**, spanned by a single
quad strip of 72 long triangles (~15% of the guitar's length). Not "sparse" — empty. Vertex distribution
along the long axis, old mesh: 43% of all vertices sit in the headstock, the neck bands hold 4.5% and 2.9%.

### `meshes/guitar_neckrings4.obj` — guitar.obj + 4 rings x 36 vertices, NOTHING else
Built by **`analysis/densify_neck.py`** (`--num_rings 4`; a 5-ring variant `guitar_neckrings.obj` also
exists, Tal chose 4). 4036 -> **4180 v**, 8068 -> **8356 f**. Ring spacing in the gap becomes 0.0643,
matching its neighbours (0.059 below, 0.040 above); max neck ring spacing 0.3211 -> 0.0657.
- Vertices are **appended**, never renumbered — indices 0-4035 keep their exact positions, so the
  standard query vertices `2760 642 1545 1527` stay valid.
- Every new vertex sits on an existing RAIL edge of the strip (off-rail deviation **5.6e-17**), so it is
  exactly on the original surface. 0 non-manifold edges.
- **The one inexactness, stated up front**: the strip's 36 quads are re-triangulated, and they are
  non-planar by at most **1.15e-4** (guitar height ~1.80). The bit-exact alternative required cutting the
  diagonals too — 360 new vertices in rings of 72, i.e. double the circumferential density of the rest of
  the neck. Tal wanted natural sampling, so the quad route was taken deliberately.

### THE FRAME PIN — `{"center": "none"}`, a new sidecar mode. Read this before touching any derived mesh.
`guitar.obj` is **already stored normalized in the file** (raw centroid exactly [0,0,0], radius exactly
1.0), so `MeshNormalizer` on it is the IDENTITY. That is a coincidence of how the file was prepared, NOT
something the code guarantees — which is why upstream never needed a sidecar and every derived mesh does.
Adding 144 vertices at mean y=+0.13 moves `mean(vertices)` by 144*0.13/4180 = 0.0045 (measured 0.0046)
and the radius by +0.46%.
- **Measured cost of NOT pinning**: phase-1 reuse drops from cos 1.000000 to 0.9986, and — the number that
  actually mattered — **12.05% of the mask's 212,549 pixels change their argmax vertex** (moving a mean
  geodesic 0.0158, ~1.6 edge lengths). Cosine alone understated it; the behavioural test is what settled it.
- Tal's instruction was "do what Itai's original code did", and the first read of that was "no sidecar".
  **The measurement inverted it**: going without a sidecar is what *moves* the mesh 0.46%; the pin is what
  keeps Itai's frame. With `{"center": "none"}` the shared 4036 vertices load bit-identical and phase-1
  reuse is exact (cos **1.000000**, max|diff| 1.6e-06).
- Code: `load_mesh_normalizer_spec`/`loadmesh` accept `"none"` (no transform + `frame_locked`), and a new
  **`mesh_frame_normalizer(obj_path, raw_vertices)`** in `modules/utils.py` is now the single place that
  decides a mesh's frame. `join_eval_pixel_labels.py` and `compare_eval_runs.py` were each re-deriving it
  with their own `if ... == 'bbox'` branch that silently fell through to centroid for any unknown mode —
  both now route through the helper. Meshes without a sidecar are unaffected.

### PHASE-1 IS **NOT** RETRAINED — and the reason is not the one that looks obvious
Phase-1 (`train_encoder_dfd_crossview.py`) trains `f(xyz) -> feature` on flat **per-PIXEL** (xyz, feature)
pairs read from `xyz_bary_f/` + `dino_sd_f/`. **There is no render call in its training loop**, and vertex
features are never barycentrically interpolated. So **vertex count never enters phase-1's training data** —
the gap was already densely supervised, one pair per pixel. Vertex count appears only in the last line,
`pred_f = encoder(mesh.vertices)`, a pure evaluation.
- **A wrong turn worth recording**: this was first answered from `train_encoder_dino_sd_l2norm.py`, which
  DOES train through renders with barycentric interpolation, and which would have implied that the old
  encoder could only produce a linear ramp across the gap and therefore MUST be retrained. That script is
  a different, experimental phase-1 variant and is **not** what built `encoder_dino_sd_dfd_crossview_phase1`.
  Check which phase-1 script a checkpoint came from before reasoning about its supervision.
- Reuse is exact: `analysis/export_pred_f.py --l2norm` at 4180 vertices; shared 4036 cos 1.000000. The 144
  new neck vertices get feature spread 0.960, in line with the existing neck (lower 0.920, upper 0.947).
- Retraining phase-1 (new renders + ~51 GB cache + ~15 min) would only correct the 0.46% frame difference,
  which the pin already makes zero. It would also add a second change and stop isolating density. Available
  as a control arm later, not as the first arm.
- Reconstructing phase-1 needs **`EncoderL2Norm`** (not `Encoder`) + `seed_everything(0)`; the Fourier basis
  `_B` is not in the state_dict. With the wrong class the gate reads cos 0.842 instead of 1.000000.

### The clean environment — `scripts/lib_neckrings4_override.sh` (source after `lib_isobbox_common.sh`, `NECKRINGS4=1`)
| asset | value | verification |
|---|---|---|
| 3D geodesic table | `guitar_neckrings4_geo_table_3d.pth`, **t_coef 20** (same as guitar.obj), diagonal 1.90982 | vs old table on shared 4036 v: mean 0.00132 |
| phase-1 | `encoder_neckrings4_dino_sd_dfd_crossview_phase1` (same checkpoint, re-evaluated) | cos 1.000000 |
| checker | `demo/guitar/colored_mesh_neckrings4/` | grid identical (53 cells, [5 17 2], size 0.1127); **4036/4036 colours bit-identical** |
| eval v2 | `demo/guitar/eval_labels/v2_edge_inset/neckrings4/` | snap mean 0.0144 |
| unchanged | mask, fine segments, 2D geodesic table, photo features, `geo_diag_2d` = None | — |
- **t_coef: 5 is more ACCURATE (worst undershoot 0.0238 vs 0.0389) but 20 was chosen deliberately** — 20
  reproduces the old table closely (mean 0.00132, diagonal 1.90107 vs 1.90258) and accuracy would have been
  a SECOND change. The t_coef=5 table is not kept; rebuild with `--t_coef 5` if it is ever wanted.
- **v2 eval now exists for plain `guitar.obj` too** (`.../v2_edge_inset/oldmesh/`). All meshes share one raw
  `.obj` frame, so the same 100 picked points snap onto any of them; the old "v2 is isobbox-only" note is
  obsolete. `lib_oldmesh_override.sh` carries `EVALPAIRS`/`EVALDIR` now and old-mesh arms are no longer
  eval-less. **`compare_eval_runs.py` refuses to mix meshes without `--rescale_across_meshes`** — pass it.

### Three independent signs the gap was a real defect
1. **Geodesic solver**: at each mesh's own best t_coef, worst-case undershoot 0.0472 (old) -> 0.0238 (new).
2. **The eval ground truth was broken there**: 5 of the 100 hand-picked v2 points had no vertex to snap to
   on the old mesh — worst snap **0.153**, and all five sit inside the gap. On the new mesh: 0.024. Those
   are exactly the 5 labels (of 100) whose ground-truth vertex changes.
3. The 12% pixel-flip measurement above, which forced the frame pin.

### THE DENSITY RESULT — arm vs arm 3, identical except the 144 vertices
`scripts/run_neckrings4_arm.sh` (`T` env var, default 0.01) + `scripts/compare_neckrings4_vs_oldmesh.sh`.
Recipe = arm 3's exactly: squash photo features, learned per-segment mu, cycle v2 T_cyc=0.05
**c=1.676e-5 deliberately NOT recalibrated** (arm 3 did not either — matching arm 3 matters more than being
optimal, or the comparison stops isolating density), 16 in-segment neighbours, seed 0. 5m08s.
| arm | snap | argmax | soft | drift | mesh-feature cos |
|---|---|---|---|---|---|
| arm 3 — old mesh 4036v, T=0.01 | **89.9** | 88.0 | **87.3** | 0.55 | 0.173 |
| neck rings 4180v, T=0.01 | 88.5 | 88.0 | 86.7 | 0.55 | 0.188 |
| neck rings 4180v, T=1 | 89.3 | 86.2 | 85.2 | **-0.01** | 0.319 |
- **THE VISUAL RESULT: arm 3's one long neck cell is GONE.** That stretch of neck was 2-3 giant bands; with
  the rings it resolves into ~7 proper checker bands. The body is unchanged, as expected.
- **What that means, and it cuts against the 09-15 read**: the long neck cell that made arm 3 "move toward
  squash" was an **artifact of missing vertices**, not a property of the correspondence — there was nothing
  there to map to. So squash's smoothness is NOT explained by whatever arm 3 appeared to show. Tal's own
  verdict on the figures is still open at pod close.
- Eval is flat-to-slightly-worse (snap -1.4 is a little above the ~0.5 AUC seed floor). At T=1 the features
  travel all the way from phase-1 (drift -0.01) and get markedly LESS distinctive (0.188 -> 0.319).
- Figures: `.../bsb_neckrings4_..._T0.01_seed0_phase2/comparison_vs_oldmesh/` (the density test),
  `comparison_vs_main_and_squash/` per arm, and `isobbox_prop/comparison_neckrings4_T_sweep/`
  (T=0.01 vs T=1 vs squash, back-projection + heatmaps).

### The checker RENDER is inflated ~10% for any mesh WITHOUT a sidecar — render-only, no effect on results
`analysis/mesh_coloring.py --mode checker` writes a `.ply` with **split vertices** (3 per face, 38202 for the
old mesh) for flat shading. `render_colored_mesh.py` hands that to upstream `setcolor_mesh_batched`, which
calls `MeshNormalizer` — and for a mesh that is not `frame_locked` that re-centres on the mean of the SPLIT
vertices. Both meshes' plys have identical raw Y-extent 1.8040; the old one is divided by 0.90571 and renders
at 1.9918, the neck-rings one (frame_locked) stays at 1.8040. Measured pixel heights 358 vs 325 = 1.102.
- **So the OLD render is the inflated one and the new one is at true scale**, not the other way round. This is
  the same failure the 2026-09-02 comment in `render_colored_mesh.py` records for the isotropic mesh.
- **It affects ONLY the reference render.** Neither phase-1 nor phase-2 calls `setcolor_mesh`/`render_views`
  (verified), and the back-projection reads checker colours from the `.pth`, not from the render image.
- Separately: that prerequisite render was running at the **224** default instead of 512, which is why the new
  checker view looked stair-stepped. `analyze_isobbox_arm.sh` now passes `--render_res 512`.
- Not fixed: `demo/guitar/colored_mesh/`'s render is still the inflated one and the squash comparisons depend
  on it, so it was left alone.

### THE WALK-BACK — Tal, 2026-09-16: put the MAIN recipe back one knob at a time, keeping smoothness
Started from the neck-rings arm that matched arm 3 (squash, T=0.01) and restored MAIN's settings one at a
time, judging smoothness by eye at each step. `scripts/run_neckrings4_arm.sh` now carries all three knobs as
env vars: **`T`** (default 0.01), **`PIXARM`** (`sdsquash`/`sdsquare`), **`TRUEDIAG2D`** (0/1).
| step | arm | snap / argmax / soft | Tal's verdict |
|---|---|---|---|
| start | neck rings + squash, T=0.01 | 88.5 / 88.0 / 86.7 | smooth (the arm being kept) |
| T=1 | neck rings + squash, T=1 | 89.3 / 86.2 / 85.2 | **REJECTED — hurt the smoothness. Stay at T=0.01.** |
| +sd_square | neck rings + sd_square, T=0.01 | 89.5 / 88.8 / 87.5 | accepted ("נראה טוב") |
| +truediag2d | neck rings + sd_square + truediag2d, T=0.01 | **90.0 / 89.0 / 87.9** | accepted |
| control | **isobbox + sd_square + truediag2d, T=0.01** | 89.4 / 89.0 / 88.0 | verdict OPEN |
| reference | MAIN (isobbox, T=1) | 90.3 / 89.9 / 88.4 | — |
- At T=1 the features travel ALL the way from phase-1 (**drift -0.01**, essentially orthogonal) and get
  markedly LESS distinctive (mesh-feature mean pairwise cos 0.188 -> 0.319). That, not the eval, is the
  clearest signal that T is doing much more here than acting as a read-out temperature.
- `truediag2d` gave +0.5 / +0.2 / +0.4. **Predicted to be negligible and it slightly wasn't** — the
  reasoning was that mu should absorb a uniform 0.35% rescale. Still within the ~0.5 AUC seed floor, so do
  not treat the gain as established without a second seed.
- **`scripts/run_isobbox_main_T.sh`** (new): MAIN's exact recipe at a chosen `T`, copied flag-for-flag from
  MAIN's `run_config.json`. Built to run the T=0.01 control.
- **THE MESH-ISOLATED COMPARISON** (`isobbox_prop/comparison_mesh_isolated/`): with T, photo features and
  truediag2d all matched, **the two meshes are near-identical** — argmax exactly equal (89.0), soft differs
  0.1, snap 0.6. All inside the noise floor. **The mesh barely moves the numbers**; whether it moves the
  smoothness is Tal's visual call, still open.
- Note for interpretation: the baseline itself drops 90.3 -> 89.4 going from T=1 to T=0.01, so T=1 IS better
  on eval. Tal keeps T=0.01 anyway, on smoothness grounds.
- **Gotcha that cost a run**: `lib_isobbox_common.sh` already owns the name **`PIXTAG`** (the tracked-pixel
  set, `explicit9`) and is sourced before any arm script's own defaults, so an env var by that name is
  silently clobbered. The photo-feature knob is therefore `PIXARM`. Check for a name collision against
  `lib_isobbox_common.sh` before adding any new env knob.

### WHY THE BACK-PROJECTED SQUARES LOOK LESS REGULAR THAN THE BASELINE'S — Tal's observation, 2026-09-16
Tal noticed the checker squares on the body are unevenly sized and the neck colours less evenly spread than
the baseline's, and guessed it was the isotropic vertex distribution. **Measured, and he is right:**
| mesh | edge-length CV | tri-area CV | vertices per checker cell |
|---|---|---|---|
| isobbox (baseline) | **0.230** | **0.336** | median **90**, CV **0.474** |
| neckrings4 | 0.980 | 1.798 | median 51, CV 1.146 |
| old mesh | 1.497 | 1.903 | median 49, CV 1.164 |
- The checker is painted PER VERTEX, so a cell's edge in the back-projection can only be as sharp as the
  vertex spacing there. Our mesh gives each cell ~half the vertex budget (51 vs 90) **despite having more
  vertices overall** (4180 vs 3886) — 43% of them sit in the headstock. Hence coarser squares.
- And the cell-to-cell SPREAD is 2.4x larger (CV 1.15 vs 0.47), so some squares come out crisp and others
  ragged — which is exactly the "different sizes" Tal saw.
- Filling the gap moved edge CV 1.497 -> 0.980, real progress, but isobbox is at 0.230. **We fixed the one
  region that was EMPTY; the rest of the mesh is still strongly anisotropic.** If even squares matter, the
  next lever is broader remeshing, not another gap fill.

### NEXT POD
1. **Tal's visual verdict on the mesh-isolated pair is OPEN** — `isobbox_prop/comparison_mesh_isolated/`
   (isobbox vs neck-rings, both T=0.01/sd_square/truediag2d, + MAIN and squash as references).
   The eval says the mesh barely matters; the question is whether the eye agrees.
2. The walk-back is finished — only **the mesh** and **T=0.01 vs 1** now differ from MAIN, and T is a
   deliberate choice, not an open question.
3. If smoothness still is not explained, the open threads are: the remaining anisotropy of the old-mesh
   family (see the CV table above), and the original "why is squash smooth" question, which the 09-16 work
   made HARDER rather than easier — arm 3's long neck cell turned out to be an artifact.
4. **Nothing is committed.** New/changed 09-16: `analysis/densify_neck.py`, `scripts/lib_neckrings4_override.sh`,
   `scripts/run_neckrings4_arm.sh`, `scripts/run_isobbox_main_T.sh`, `scripts/compare_neckrings4_vs_oldmesh.sh`,
   `meshes/guitar_neckrings4.obj` + `.normalizer.json` + `guitar_neckrings.obj`, `modules/utils.py`,
   `analysis/join_eval_pixel_labels.py`, `analysis/compare_eval_runs.py`, `scripts/analyze_isobbox_arm.sh`,
   `scripts/compare_vs_main_and_squash.sh`, `scripts/lib_oldmesh_override.sh` — plus 09-15's five files.


## STATE AT POD CLOSE — 2026-09-15 (eighteenth pod, second of the day). **NOTHING IS RUNNING.** Tal closes the pod himself.
**The day in one list** (details in the 2026-09-15 section just below):
- **MAIN CHANGED: `mu_learn_perseg` + cycle v2** (c=1.676e-5, T_cyc=0.05, stride 5) — 90.3 / 89.9 / 88.4, drift 0.11, much more distinctive mesh features. FULL analysis done (`analysis_summary.png`). Its step checkpoints are gone (09-15 cleanup) — calibrate new arms at `mu_learn_perseg` step 25.
- **WHY IS SQUASH SMOOTH — started from the MAIN side**, three arms, SMALL analysis, train T = read T = 0.01, each compared vs MAIN + the PROTECTED smooth squash (`comparison_vs_main_and_squash/`):
  | arm | change on top of MAIN | AUC snap/argmax/soft | smooth like squash? |
  |---|---|---|---|
  | 1 | squash features + T=0.01 | 88.6 / 88.1 / 86.9 | **no** (Tal agreed) |
  | 2 | DINO only (width 1024) + T=0.01 | 90.0 / 88.4 / 87.3 | no (assistant's read; Tal did not comment) |
  | 3 | arm 1 + OLD MESH (4036v + its phase-1 + old geo table / 2D diameter) | no eval (no v2 labels) | **YES — Tal agreed at a quick look** |
- Demo dirs: `demo/guitar/runs/isobbox_prop/bsb_{isobbox_sdsquash,isobbox_dinoonly,oldmesh_sdsquash}_mu_learn_perseg_cycv2T0.05_c1.676e-05_retstride5_T0.01_seed0_phase2/comparison_vs_main_and_squash/`.
- **Git: NOT committed today.** New/changed: `scripts/compare_vs_main_and_squash.sh`, `run_squash_smooth_CHAIN.sh`, `run_squash_smooth_arm3_oldmesh.sh`, `lib_oldmesh_override.sh`, `analyze_isobbox_arm.sh` (`READ_T`, `OLDMESH`). Commit when Tal asks.
- Rebuilt on disk: isobbox DINO-only phase-1 `experiments/guitar/encoder_isobbox_dino_only_stride14_dfd_crossview_phase1`, photo features `demo/guitar/features_analyze/dino_only_stride14/`, cache `dino_only_isobbox` in `data/guitar/encoder_data_frontcentered_dinosd_isobbox`.

### NEXT POD
1. **Tal looks at the three arms properly and decides.** Arm 3 is the lead: the old-mesh switch bundles THREE things — mesh geometry, its phase-1 encoder, old 3D geo table / 2D diameter — so the natural next step is to split them (e.g. old mesh with the other factors back to MAIN's: sd_square, T=1), but that is Tal's call.
2. Arm 2's verdict from Tal is still open.
3. Commit the day's scripts when Tal asks.

## STATE AT POD CLOSE — 2026-09-15 (seventeenth pod) — superseded by the entry above
**The day in one list** (details in the sections below):
- **MAIN baseline = `mu_learn_perseg`**: `rkd_spatial_dist` only, 16 in-segment neighbours, learned per-segment mu (89.6 / 89.7 / 88.4). Full analysis + summary grid done. Chosen over the closed-form mu by Tal's eye; known cost: lower mesh-feature distinctiveness.
- **Baseline hierarchy recorded** (section THE BASELINES): MAIN, SECONDARY (old anchor+cycle+L_dist), two PROTECTED smooth old-mesh runs (SD-aligned; squash = smoothest, carries bug B, kept to learn WHY it is smooth).
- **Tried on MAIN, all CLOSED/PARKED by Tal**: `rkd_spatial_angle3` 1/10…10× (parked — no back-projection gain, slight distinctiveness gain); cycle only / anchor only / anchor½+cycle+L_dist (no back-projection value; **cycle clearly improves distinctiveness — adoption undecided**; anchor hurts, weaken if reused); `rkd_feat_angle2` 1/10…1/1 (closed — no gain, features less stable). Global-mu control and small-segment fixes: not needed.
- **Infrastructure**: loss names unified (section LOSS NAMES, verified bit-identical); `isobbox_prop/` run root + renames; SMALL analysis = one process (~20 s, verified identical); FULL analysis builds `analysis_summary.png`; 142.7 GB freed; git `d83ec9b` pushed.
- **Disk at close**: `experiments/guitar` 86 GB (the 3 `fangle2` arms still carry step checkpoints, ~15 GB — deletable, closed direction), `demo/guitar` 38 GB. Empty calibration scratch dirs removed.
- **Git: everything committed and pushed at pod close** — `16e5b3d` on `analysis` (loss-name refactor, `--rkd_feat_angle2_balance`, 27 script flag renames, `run_prop_fangle2_CHAIN.sh`), on top of `d83ec9b` from earlier the same day. Working tree clean.

### NEXT POD
1. **Pick the next direction — Tal is thinking it over.** Open candidates (none started): `FROZEN-DELTA`; `SHIC-ONLY` + `L_eq`/`L_syn`; understand the squash smoothness; decide on adopting cycle for distinctiveness. Older live threads: SD-aligned seeded stride-14 run, left-right symmetry idea (C), bbox-frame clean control, bear ZS verdict.
2. **Git is clean** (`16e5b3d` pushed). Commit again at end of day when Tal asks.
3. Any new arm on MAIN: `scripts/run_isobbox_prop_QUEUE.sh "<tag>_w<w>|<flags>|<label>"`, calibrate first at MAIN step 25 (the `*_balance` diagnostics), canonical loss names only.

## LOSS NAMES — Tal, 2026-09-15. ONE NAME PER TERM, EVERYWHERE (flags, logs, run tags, notes)
Too many overlapping names had accumulated ("L_spatial", "relational", "RKD-A", "pairwise angle", "featPA", "ANGLE-SPATIAL"...). From 2026-09-15 on, only these:
| name | what it compares | points | flag (old alias still accepted) | run tag | log field | function |
|---|---|---|---|---|---|---|
| **`rkd_spatial_dist`** | geodesic distance pixel↔pixel vs vertex↔vertex, over diameters, per-segment mu | 2 | `--rkd_spatial_dist_weight` (`--relational_weight`) | `sdist` (default 1, not written) | total `loss` | `rkd_spatial_dist_loss` (`relational_loss_geodesic`) |
| **`rkd_spatial_angle3`** | angle at the centre between rays to two neighbours; **Euclidean**: pixel rays vs chords between soft-mapped 3D points | 3 | `--rkd_spatial_angle3_weight` (`--spatial_angle_weight`), `_min_ray_px`, `_balance` | `sangle3_w<w>` | `spatial_angle3=` | `rkd_spatial_angle3_loss` (`spatial_angle_loss`) |
| **`rkd_feat_dist`** | distance between two photo features vs between the two mesh features | 2 | `--rkd_feat_dist_weight` (`--feat_dist_weight`) | `fdist_w<w>` | `feat_dist=` | `rkd_feat_dist_loss` (`feature_rkd_distance_loss`) |
| **`rkd_feat_angle2`** | cosine between centre and neighbour feature, photo vs mesh | 2 | `--rkd_feat_angle2_weight` (`--feat_pair_angle_weight`), `--rkd_feat_angle2_neighbors` | `fangle2_w<w>` | `feat_angle2=` | `rkd_feat_angle2_loss` (`feature_rkd_pairwise_angle_loss`) |
| **`rkd_feat_angle3`** | angle at the centre between the two neighbour rays, in feature space (the RKD paper's angle) | 3 | `--rkd_feat_angle3_weight` (`--feat_angle_weight`) | `fangle3_w<w>` | `feat_angle3=` | `rkd_feat_angle3_loss` (`feature_rkd_angle_loss`) |
- The mesh-side feature in the three `rkd_feat_*` terms is `soft` (weighted mean over the top-10 vertices) unless `--feat_student_mode argmax`.
- Old flags/functions remain as aliases so old scripts and `run_config.json` files reproduce; every new script, log line, run tag and note uses the canonical names. Archived/older sections of this file keep their original wording — translate with this table.
- **VERIFIED 2026-09-15, two ways**:
  1. *Static*: reverse-mapping every new name back to the old one and diffing against `d83ec9b` leaves only comments, docstrings, print labels / log field names, the dual option strings and the alias lines — no computational change. 25 of 27 edited scripts are pure flag renames; the other 2 only change the `sangle` tag to `sangle3_w`.
  2. *Runs (25 steps each)*: MAIN with the new flag is **bit-identical** to MAIN's original step-25 checkpoint; a run with ALL renamed terms on (`rkd_feat_dist`, `rkd_feat_angle3`, `rkd_feat_angle2` in_segment, `rkd_spatial_angle3`) is **bit-identical** across old code + old flags, new code + new flags, and new code + old flags — and differs from MAIN, so the terms were really active. Log values match to the last printed digit.
- **`rkd_feat_angle2` on MAIN — LAUNCHED 2026-09-15 (Tal: 2-point version, `soft` mesh feature, in-segment neighbours)**: new diagnostic `--rkd_feat_angle2_balance` (grad norm vs the weighted `rkd_spatial_dist` term; with `--anchor_balance_from` the anchor's own diagnostic is skipped so the feature block is reached). Chain `scripts/run_prop_fangle2_CHAIN.sh`: calibrate at MAIN step 25 (`logs/prop_fangle2_calibrate.log`) → arms `mu_learn_perseg_fangle2_w<w>` at 1/10, 1/3, 1/1 → `isobbox_prop/comparison_fangle2_sweep/` (back-proj soft + top1k, heatmap row, eval). Log `logs/prop_fangle2_chain.log`.
  - **Calibration**: rkd_spatial_dist grad 4.37e-6, rkd_feat_angle2 grad 3.37e-2, |cos gap| 0.132 → weights **1.2978e-5 (1/10), 4.326e-5 (1/3), 1.2978e-4 (1/1)**.
  - **RESULT (2026-09-15)**:
    | arm | AUC snap/argmax/soft | @1/@3% snap | cov | drift@300 | angle2 cos_gap@300 | mesh sim mean v535/v549/v1017/v2885 |
    |---|---|---|---|---|---|---|
    | MAIN | 89.6 / 89.7 / 88.4 | 17 / 80 | 36.3% | 0.84 | — | 0.49 / 0.32 / 0.08 / 0.45 |
    | fangle2 1/10 | 90.0 / 90.1 / 88.5 | 19 / 81 | 36.5% | 0.85 | 0.034 | 0.44 / 0.36 / 0.31 / 0.46 |
    | fangle2 1/3 | 89.9 / 90.1 / 88.2 | 15 / 87 | 36.2% | 0.85 | 0.026 | 0.44 / 0.41 / 0.37 / 0.45 |
    | fangle2 1/1 | 89.9 / 89.6 / 88.3 | 11 / 83 | 35.4% | 0.84 | 0.019 | 0.41 / 0.39 / 0.38 / 0.42 |
    - Eval flat, back-projection indistinguishable from MAIN. Mesh features NOT more distinctive (v1017 gets worse, 0.08 → 0.31–0.38) and the mesh heatmaps turn mottled with small dark speckles, most at 1/1. The term is satisfied easily (cos gap 0.132 → 0.02–0.03).
    - **TAL'S VERDICT (2026-09-15): no visual improvement at all in the back-projection; in feature space it is even LESS good — unstable.** No added value; `rkd_feat_angle2` on the new MAIN is CLOSED.
    - Arms (renamed the same day to one notation): `mu_learn_perseg_fangle2_w{1.3e-5,4.33e-5,1.3e-4}` (were `_w1.3e-05`, `_w4.33e-05`, `_w0.00013` — `%.3g` mixed notations; the chain now formats tags as mantissa + plain exponent). The comparison PNGs still show the old labels inside the image.
- Renamed on disk the same day: `isobbox_prop` arms `..._sangle<w>_...` → `..._sangle3_w<w>_...` (demo dir, encoder dir + `run_config.json`, eval files), and `comparison_sangle_{sweep,strong}` → `comparison_sangle3_{sweep,strong}`.

## 2026-09-15 (eighteenth pod, second of the day) — **CYCLE ADOPTED: MAIN is now `mu_learn_perseg` + cycle v2**
- Tal's call after re-viewing `.../bsb_isobbox_sdsquare_mu_learn_perseg_cycv2T0.05_c1.676e-05_retstride5_T1_seed0_phase2/comparison_vs_main/`: back-projection ≈ same, mesh features much more distinctive, eval slightly up (90.3 / 89.9 / 88.4 vs 89.6 / 89.7 / 88.4, within seed noise), drift 0.84 -> 0.11.
- **New MAIN** = `bsb_isobbox_sdsquare_mu_learn_perseg_cycv2T0.05_c1.676e-05_retstride5_T1_seed0_phase2` (encoder `encoder_isobbox_sdsquare_fuse16_truediag2d_mu_learn_perseg_cycv2T0.05_c1.676e-05_retstride5_T1_seed0_phase2`): `rkd_spatial_dist` + learned per-segment mu + cycle v2 T_cyc=0.05 c=1.676e-5 (1/5 of rkd_spatial_dist grad at step 25 of `mu_learn_perseg`), return stride 5. The old MAIN `mu_learn_perseg` stays kept in full (PREVIOUS MAIN; its step 25 is still the calibration state).
- **Caveat**: the new MAIN's step checkpoints were deleted in the 09-15 cleanup — only `encoder_checkpoint.pth` + `pred_f.pth` remain. Calibrating a new arm ON it needs a re-run (or calibrate at `mu_learn_perseg` step 25 as before).
- FULL analysis launched (`logs/full_analysis_main_cycle.log`) -> `<run>/analysis_summary.png`.
- The table below is the 09-15 order; read "MAIN" there as PREVIOUS MAIN.

### WHY IS SQUASH SMOOTH — started 2026-09-15, from the MAIN side
- Tal confirmed the smooth run: PROTECTED squash, old mesh 4036v, stride 14, train T=0.01, seed 0, soft-snap read T=0.01 (`demo/guitar/runs/oldmesh_sweeps/stride14/bsb_sd_dino_stride14_nosdsquare_T0.01_seed0_phase2/analyze_readT/back_projection/`).
- Differences vs MAIN: mesh+phase-1 (4036v vs isobbox) · SD frame squash vs sd_square · train T 0.01 vs 1 · read T 0.01 vs 1 · 2D diameter old vs truediag2d · 8in+8out vs 16in · mu fixed 1 vs learned per-seg · no cycle vs cycle.
- Tal: "smooth" is a visual judgement — no metric; the chain is judged by eye. An earlier auto-built chain (`isobbox_prop/comparison_squash_chain/`) was set aside by Tal.
- **Chain `scripts/run_squash_smooth_CHAIN.sh`** (log `logs/squash_smooth_chain.log`), SMALL analysis, read T = train T = 0.01, cycle c NOT recalibrated:
  1. MAIN + squash features + T=0.01 → `bsb_isobbox_sdsquash_mu_learn_perseg_cycv2..._T0.01_seed0_phase2`
  2. MAIN + DINO only + T=0.01 → `bsb_isobbox_dinoonly_mu_learn_perseg_cycv2..._T0.01_seed0_phase2` (isobbox DINO-only phase-1 + photo features REBUILT, width 1024)
- Every arm gets `comparison_vs_main_and_squash/` (`scripts/compare_vs_main_and_squash.sh`): soft + top1k back-projection, heatmap rows, eval (arm vs MAIN only; squash has no v2 labels; its heatmap uses old-mesh queries 2760 642 1545 1527). Tal: ALWAYS compare vs MAIN and vs squash smooth together.
- `analyze_isobbox_arm.sh` SMALL mode now honours `READ_T` (default 1).
- **ARM 1 RESULT**: 88.6 / 88.1 / 86.9 (MAIN 90.3 / 89.9 / 88.4), @3% snap 75 vs 85, cov 34.5%. Back-projection looks like MAIN, NOT like squash; mesh features washed out. **Tal: did not bring the smoothness back.**
- **ARM 2 RESULT** (DINO only, width 1024, T=0.01): 90.0 / 88.4 / 87.3, @3% snap 82, cov 31.8%. Soft back-projection like MAIN; top1k cell edges spiky on the body; photo heatmap shows the DINO lattice (dark spots) that squash does not have; mesh features washed out. Not smooth (assistant's read, Tal's verdict pending).
- **ARM 3 (Tal)**: arm 1 + OLD MESH — `guitar.obj` 4036v + its own phase-1 `encoder_dino_sd_dfd_crossview_phase1` (the one squash started from, so no phase-1 re-run) + old 3D geo table + old 2D diameter (no `--geo_diag_2d`). Script `scripts/run_squash_smooth_arm3_oldmesh.sh` (waits for the arm 1/2 chain), log `logs/squash_smooth_arm3_oldmesh.log`, demo `isobbox_prop/bsb_oldmesh_sdsquash_mu_learn_perseg_cycv2..._T0.01_seed0_phase2`. No eval (no v2 labels on old mesh). **RESULT (assistant's read, Tal's verdict pending): FIRST ARM THAT MOVES TOWARD SQUASH** — larger, cleaner cells, long neck cell like squash; top1k cells very large (some checker cells merge); mesh heatmap resembles squash's. The old-mesh switch bundles three things: mesh geometry, its phase-1 encoder, old 3D geo table / 2D diameter. Old-mesh constants: `scripts/lib_oldmesh_override.sh` (`OLDMESH=1` in analyze, `ARM_OLDMESH=1` in the comparison).

## THE BASELINES — UPDATED Tal, 2026-09-16. Supersedes the 09-15 table below it and every older "current baseline" line.
| role | arm (demo dir under `demo/guitar/runs/isobbox_prop/`, encoder `experiments/guitar/encoder_<same suffix>`) | eval v2 (snap/argmax/soft) |
|---|---|---|
| **MAIN baseline (T=0.01)** | `bsb_isobbox_sdsquare_mu_learn_perseg_cycv2T0.05_c1.676e-05_retstride5_T0.01_seed0_phase2` — isobbox mesh, sd_square, truediag2d, learned per-seg mu, cycle v2 T_cyc=0.05 c=1.676e-5 stride 5, T=0.01, seed 0 | 89.4 / 89.0 / 88.0 |
| **PROTECTED, T=1 companion** | the 09-15 MAIN: `bsb_isobbox_sdsquare_mu_learn_perseg_cycv2T0.05_c1.676e-05_retstride5_T1_seed0_phase2` (same recipe, T=1) — step checkpoints already gone | 90.3 / 89.9 / 88.4 |
| **PROTECTED, new mesh** | `bsb_neckrings4_sdsquare_truediag2d_mu_learn_perseg_cycv2T0.05_c1.676e-05_retstride5_T0.01_seed0_phase2` — **exactly MAIN's recipe, only the mesh differs** (run_config diff verified 2026-09-16: only obj_path, geo table, mesh-matched phase-1). Kept because the new mesh showed smoothness depends heavily on the mesh. | 90.0 / 89.0 / 87.9 |
- **Comparison rule (Tal, 2026-09-16): a new arm is compared vs MAIN (T=0.01) ONLY.** Not vs the neck-rings protected run, and **not vs squash** — squash carries BUG B, it is not a reference anymore. This replaces the 09-15 "compare vs MAIN AND squash" rule (`compare_vs_main_and_squash.sh` is retired as a default).
- The older PROTECTED runs (SD-aligned stride 14, squash) stay on disk untouched; they are just not comparison targets.

### SHIC comparison revisited (Tal, 2026-09-16)
- **SHIC on the guitar: direction DROPPED** (their training code is not public; Tal decided not to pursue).
- **Bear on the NEW MAIN recipe**: `scripts/run_shicbear_main_T.sh` (+ `scripts/analyze_shicbear_arm.sh`, SMALL + comparison grid,
  soft read at `READ_T`). Same raw `bear.obj`, phase-1, geo tables, mask, fine segs as 09-03; guitar's c=1.676e-5 NOT recalibrated.
  New for the bear: sd_square fuse16 features `demo/shic/features_analyze/sdsquare_fuse16/bear3_pix_sdsquare_fuse16.pth`, true 2D diameter **967.21 px**.
  Demo: `demo/shic/bear3_sdsquare_truediag2d_mu_learn_perseg_cycv2T0.05_c1.676e-05_retstride5_T0.01_seed0_phase2/`.
  | arm | top1 cov | soft-snap cov |
  |---|---|---|
  | SHIC | 14.51% | 18.19% |
  | **new MAIN, T=0.01** | 8.47% | 18.15% |
  | old pick mu=0.6 T=1 | 4.80% | 7.48% |
  | ZS | 9.26% | 24.13% |
  | learned mu, **T=1** | 7.27% | 14.89% |
  | **closed-form per-seg mu** (`--mu_mode optimal`), T=0.01 | 7.56% | 15.48% |
  Tal: "the PROPORTIONS look wrong". Audit: no guitar value leaked except c (all paths bear; 3D diam 2.338, 2D 967.21).
  On the bear, mean normalized 2D dist / 3D = 0.228/0.177 = **1.29**. Our back-projected cells are ~2x smaller than SHIC's /
  the old mu=0.6 pick in all three new arms (mu barely changes it). Last two arms: `T=1 MU=learn` / `T=0.01 MU=closed`
  env knobs on `run_shicbear_main_T.sh`, chain `run_shicbear_T1_and_closed_CHAIN.sh`. Extra reference renders
  `demo/shic/colored_mesh/checker16_uv_azim{180,90}.png` (side / head front) now head every bear comparison grid.
  **T=1 on the bear: REJECTED by Tal** ("does not help, even hurts") — stay at T=0.01.
  mu per segment at step 300 [min/med/max]: learned 0.724/1.000/1.874; closed-form 0.538/0.764/2.347 (closed-form median
  is below 1 — it shrinks d_3D-relative scale for most segments; learned barely leaves init). Figure:
  `demo/shic/bear3_..._mu_closed_perseg_..._T0.01_seed0_phase2/comparison_vs_learned/closed_vs_learned.png`. Closed vs learned verdict: OPEN.
  **Closed vs learned: near-identical** (mesh feature cos 0.986, top1 differs on 49% of pixels but by 1.6% D on average). Tal sees no difference.
  **Tal rejected** fixed mu (hurts locations, seen before) and 8in+8out (seen to break runs) as proportion fixes.
- **PROPORTION DIAGNOSTIC** — 3D geodesic extent of the top1-matched vertex set, fraction of full D: SHIC max 0.706 / p99 0.641;
  old mu=0.6 0.624/0.488; new MAIN 0.795/0.654; ZS 0.907/0.727. Hypothesis: d_3D is normalized by the WHOLE mesh diameter, which
  assumes the photo spans the whole object (true for the frontal guitar, false for a 3/4 bear).
- **Two ideas built and run (Tal: "try both"), T=0.01, everything else MAIN:**
  - idea 1 `--geo_diag_3d` (NEW flag): visible-part diameter from `analysis/estimate_visible_geo_diameter.py` (best silhouette-IoU
    phase-1 render views, IoU ~0.72, no SHIC used; xyz_bary_f background = 2.0) -> **2.00053 = 0.856 D** (p99 0.71 D).
  - idea 2 `--mu_init_path` (NEW flag) + `--mu_lr 0`: per-segment s fixed from the ZS mapping, `analysis/perseg_mu_from_zs.py`
    (p99 of the same in-segment pairs on both sides) -> `experiments/shic_bear/mu_perseg/zs_p99_mu_scale.pth`; the two segments holding
    95% of centres got s≈1.04 (ZS says "no zoom").
  | arm | top1 cov | soft cov | top1 extent max/D | p99/D |
  |---|---|---|---|---|
  | baseline (learned) | 8.47% | 18.15% | 0.795 | 0.654 |
  | idea 1 visible diam | 7.48% | 16.84% | 0.796 | 0.656 |
  | idea 2 ZS-fixed mu | 7.64% | 22.41% | 0.876 | 0.734 |
  **Neither zooms in.** Idea 1: learned mu absorbs it (max mu 1.87 -> 3.04, mu_3D_live unchanged 0.41). Idea 2 zooms OUT (mu_3D_live 0.55)
  and is noisier. Figure `demo/shic/comparison_bear_proportion_ideas/visdiam_vs_zsfixed.png`. Tal's verdict OPEN.
  - **idea 1 + per-seg mu FROZEN at 1** (`MU=fixed1`, `--mu_lr 0`): top1 8.06% / soft 18.56%, extent 0.837 / p99 0.697 D,
    mu_3D_live 0.458 (UP from 0.41, expected ~0.35). **Also no zoom — slightly wider, smaller cells.** So the whole-vs-visible
    normalizer is NOT the lever that sets the spread; the hypothesis is refuted. Figure `.../comparison_bear_proportion_ideas/visdiam_fixed1.png`.

### THE BASELINES as of 2026-09-15 (superseded by the table above)
| role | arm | what it is | eval v2 (snap/argmax/soft) |
|---|---|---|---|
| **MAIN baseline** | `bsb_isobbox_sdsquare_mu_learn_perseg_T1_seed0_phase2` (encoder `encoder_isobbox_sdsquare_fuse16_truediag2d_mu_learn_perseg_T1_seed0_phase2`) | `rkd_spatial_dist` ONLY, 16 neighbours ALL in-segment (`NBR_IN=16 NBR_OUT=0`), `--mu_mode learned --mu_scope segment --mu_lr 1e-2`, isobbox mesh, T=1, seed 0. No anchor / cycle / L_dist. | 89.6 / 89.7 / 88.4, mean 2.1%, cov 36.3%, drift 0.84 |
| **SECONDARY baseline** (feature-domain losses) | `bsb_isobbox_sdsquare_anchorsoftT0.01_w3.5e-7_cycv2T0.05_c1.05e-5_retstride5_distT1_g2.7951e-06_T1_seed0_phase2` | soft anchor T=0.01 λ=3.5e-7 + cycle v2 T_cyc=0.05 c=1.05e-5 (return stride 5) + L_dist γ=1/50 T_dist=1, w_spatial=1. **Kept as the comparison for anything that touches the feature domain.** | 78.9 / 69.4 / 76.1 |
| **PROTECTED, smooth** | SD-aligned stride 14 (old mesh 4036v, 2026-08-30) — see its PROTECTED section below | smoother back-projection than today's arms, less smooth than squash | old mesh, no eval v2 labels |
| **PROTECTED, smoothest** | squash stride 14 T=0.01 seed 0 (old mesh 4036v) `experiments/guitar/encoder_dino_sd_stride14_nosdsquare_relational_geodesic_mu3dscale1_T0.01_seed0_phase2/` + demo `demo/guitar/runs/oldmesh_sweeps/stride14/bsb_sd_dino_stride14_nosdsquare_T0.01_seed0_phase2/`; its T=1 companion is the other PROTECTED section below | **the smoothest back-projection this project has produced — and it carries BUG B (`sd_square` absent: SD and DINO see different frames).** Tal: it is strange that the buggy run is the smooth one, but that is what the images show; kept so we can come back and find out WHY, and carry that into the current recipe. Figure Tal confirmed 2026-09-15 (bottom, green panel): `demo/guitar/runs/isobbox/bsb_isobbox_sdsquash_T0.01_seed0_phase2/comparison_vs_baseline_T0.01/7_back_projection_readT_matched.png` | old mesh, no eval v2 labels |
- **Do not delete or strip checkpoints of any of the four** (all assets verified present 2026-09-15, step checkpoints included).
- **Why the main baseline is the LEARNED mu and not the closed-form one** (`..._mu_closed_perseg_...`, 91.0 / 90.3 / 89.1): Tal's visual read — learned is slightly better by eye although the metrics do not show it. **Known cost, recorded at Tal's request: mesh-feature DISTINCTIVENESS drops** (Tal's word in Hebrew: הפיצ'רים פחות נבדלים). Mean mesh-side similarity of the fixed query vertices, closed-form -> learned: 535 0.02 -> 0.49, 549 0.12 -> 0.32, 2885 0.33 -> 0.45 (1017 0.15 -> 0.08). Figure: `.../bsb_isobbox_sdsquare_mu_learn_perseg_T1_seed0_phase2/comparison_vs_closedform_and_ZS/4_features_sim_heatmap.png`. The closed-form arm is NOT a protected version (Tal, explicitly).
- Learned per-segment mu at step 300: 0.744 / 1.000 / 1.970 (min/med/max). Why the median sits exactly at the init value is NOT known — do not explain the distinctiveness drop by it.
- **New default comparison for a new arm: vs MAIN, and vs SECONDARY when the arm touches the feature domain.** (Replaces the 2026-08-31 rule "compare against both T=0.01 and T=1".)
- Script fixed the same day: `scripts/analyze_isobbox_arm.sh` in FULL mode (`SMALL` unset) now also renders knn k=1/10/100 + soft-snap + hard-snap and builds `<run>/analysis_summary.png`; it had claimed to in a comment but never did. SMALL mode unchanged.

### `rkd_spatial_angle3` (was `ANGLE-SPATIAL`) — BUILT 2026-09-15, on top of the MAIN baseline
- Code: `rkd_spatial_angle3_loss()` in `modules/relational_loss.py`; flags `--rkd_spatial_angle3_weight` (0 = off, bit-identical), `--rkd_spatial_angle3_min_ray_px` (14), `--rkd_spatial_angle3_balance` (grad-norm diagnostic, pair with `--anchor_balance_from <ckpt>`). For every centre and ordered neighbour pair (a, b): Huber on `cos θ_img − cos θ_mesh`, the angle AT the centre. **EUCLIDEAN angles**: image-plane pixel rays vs chords between the soft-mapped 3D points `Σ w·v` (the geodesic branch now keeps `soft_points` from `soft_map_to_vertices`). Triplets with an image ray < 14 px are dropped (one DINO patch). Scale-invariant, so no interaction with mu. Unit-tested on synthetic points: identical and rotated+scaled geometry give 0, an anisotropic stretch gives > 0.
- Known limit, stated before the run: the photo is a projection, so image angles equal surface angles only where the surface faces the camera.
- **Calibration** at step 25 of `mu_learn_perseg` (`logs/spatial_angle_calibrate.log`; the learned mu itself is not in the checkpoint, so it restarts at 1.0 there): L_spatial grad 4.37e-6, angle grad 4.95e-4, |cos gap| 0.111, 94% of triplets valid → weight **8.83e-3 at 1/1, 2.94e-3 at 1/3, 8.83e-4 at 1/10**.
- Queue: `scripts/run_isobbox_prop_QUEUE.sh "<tag>|<extra flags>|<label>"` — any arm on top of the main baseline; compares vs MAIN and ZS (+ SECONDARY with `VS_SECONDARY=1`). Three arms launched 2026-09-15: `mu_learn_perseg_sangle3_w{8.83e-3,2.94e-3,8.83e-4}`, log `logs/prop_sangle_queue.log`.
- **RESULT (2026-09-15), all L_spatial + learned per-segment mu + angle, seed 0** — figures `demo/guitar/runs/isobbox_prop/comparison_sangle3_sweep/`:
  | arm | AUC snap/argmax/soft | @3% snap | soft-snap cov | drift@300 | angle cos_gap@300 | mesh sim mean v535/v549/v1017/v2885 |
  |---|---|---|---|---|---|---|
  | MAIN (no angle) | 89.6 / 89.7 / 88.4 | 80 | 36.3% | 0.84 | (0.111 at step 25) | 0.49 / 0.32 / 0.08 / 0.45 |
  | angle 1/10 (8.83e-4) | 89.8 / 89.2 / 88.2 | 81 | 37.4% | 0.82 | 0.033 | 0.48 / 0.22 / 0.03 / 0.43 |
  | angle 1/3 (2.94e-3) | 89.8 / 89.4 / 88.1 | 80 | 39.1% | 0.79 | 0.029 | 0.47 / 0.14 / 0.13 / 0.41 |
  | angle 1/1 (8.83e-3) | 90.1 / 89.4 / 88.3 | 84 | 37.9% | 0.79 | 0.028 | 0.42 / 0.20 / 0.10 / **0.27** |
  - **Eval is flat** (all within 0.5 AUC, inside the seed floor) and back-projections look nearly identical by eye (assistant's read; Tal's visual verdict pending).
  - **What does move: mesh-feature distinctiveness partly RECOVERS with the angle weight** — the neck query 2885 goes 0.45 → 0.27 at 1/1 (closed-form arm was 0.33), coverage +1–3 pts. The angle term itself is easily satisfied: cos gap 0.111 → ~0.03 at every weight, so even 1/10 closes most of it.
- **Queued by Tal AFTER this**: MAIN + cycle only, and MAIN + anchor only. Weights recalibrated at step 25 of `mu_learn_perseg`, at the ratios the old weights had against the OLD L_spatial (Tal approved 2026-09-15): **anchor at 1/1 of L_spatial's grad norm** (old λ=3.5e-7 was exactly the equal-norm point, `logs/anchor_calibrate.log`), **cycle at 1/5** (old c=1.05e-5 × cycle grad 5.63e-2 ≈ 1/5 of relational grad 3.0e-6). Automated in `scripts/run_prop_cyc_anchor_CHAIN.sh` (waits for the angle queue, calibrates, launches both with `VS_SECONDARY=1`); logs `logs/prop_cyc_anchor_chain.log`, `logs/prop_cyc_anchor_calibrate.log`.
  - **Calibration at step 25 of MAIN**: L_spatial grad 4.37e-6, anchor λ at equal norm **6.221e-7**, cycle grad 5.22e-2 → **c = 1.676e-5** (1/5).
  - **RESULT (2026-09-15)**, figures `demo/guitar/runs/isobbox_prop/comparison_cyc_anchor/`:
    | arm | AUC snap/argmax/soft | @1/@3% snap | soft-snap cov | drift@300 | mesh sim mean v535/v549/v1017/v2885 |
    |---|---|---|---|---|---|
    | MAIN | 89.6 / 89.7 / 88.4 | 17 / 80 | 36.3% | 0.84 | 0.49 / 0.32 / 0.08 / 0.45 |
    | MAIN + cycle only (c=1.676e-5) | 90.3 / 89.9 / 88.4 | 19 / 85 | 36.4% | **0.11** | **-0.07 / 0.09 / -0.03 / 0.01** |
    | MAIN + anchor only (λ=6.221e-7) | **91.3** / 88.6 / 88.3 | 25 / 87 | 30.8% | **0.98** | 0.70 / 0.69 / 0.74 / 0.65 |
    | SECONDARY (old spatial) | 78.9 / 69.4 / 76.1 | 4 / 22 | — | 0.38 | — |
    - **cycle only**: back-projection as clean as MAIN, and the MOST distinctive mesh features of any arm, while the features move far from phase-1 (drift 0.11). Small gain on all three metrics.
    - **anchor only**: best snap AUC but it barely leaves ZS — drift 0.98, coverage at ZS level (30.8% vs 30.3%), mesh features washed out, body checker cells torn in the back-projection. At 1/1 the anchor dominates.
    - **TAL'S VERDICTS (2026-09-15)**:
      - **angle**: back-projection change almost invisible; feature space gains distinctiveness. → run STRONGER weights (3× and 10× of 1/1) before deciding. The 1/10 and 1/3 arms are visually identical to MAIN — leave them out of future comparisons.
      - **MAIN + cycle**: back-projection about the same, feature space clearly more distinctive — **remember: the cycle loss contributes distinctiveness, in a good way.**
      - **MAIN + anchor (1/1)**: looks bad visually and even worse in feature space. If re-run, weaken it.
      - **SECONDARY (old main + anchor + cycle + L_dist)**: not interesting any more, the old main is irrelevant. → re-run the combination ON THE NEW MAIN, with the anchor weakened GRADUALLY — "don't make it disappear, just weaken it a little": λ = 1/2 of the equal-norm point (3.11e-7), cycle unchanged (1.676e-5), L_dist at SHIC's 1/50 of the weighted anchor.
    - **RESULTS (2026-09-15)** — figures `isobbox_prop/comparison_sangle3_strong/` and `isobbox_prop/comparison_combo_new_main/`. L_dist calibrated γ = **2.292e-6** (1/50 of the weighted anchor at λ=3.11e-7).
      | arm | AUC snap/argmax/soft | @1/@3% snap | cov | drift@300 | mesh sim mean v535/v549/v1017/v2885 |
      |---|---|---|---|---|---|
      | MAIN | 89.6 / 89.7 / 88.4 | 17 / 80 | 36.3% | 0.84 | 0.49 / 0.32 / 0.08 / 0.45 |
      | angle 1/1 (8.83e-3) | 90.1 / 89.4 / 88.3 | 16 / 84 | 37.9% | 0.79 | 0.42 / 0.20 / 0.10 / 0.27 |
      | angle 3× (2.65e-2) | 89.7 / 88.1 / 87.6 | 21 / 83 | 36.8% | 0.86 | 0.38 / 0.21 / 0.33 / 0.29 |
      | angle 10× (8.83e-2) | **85.7 / 84.5 / 83.5** | 23 / 68 | 30.2% | 0.81 | 0.34 / 0.24 / 0.30 / 0.32 |
      | + cycle only | 90.3 / 89.9 / 88.4 | 19 / 85 | 36.4% | 0.11 | -0.07 / 0.09 / -0.03 / 0.01 |
      | + anchor 1/1 only | 91.3 / 88.6 / 88.3 | 25 / 87 | 30.8% | 0.98 | 0.70 / 0.69 / 0.74 / 0.65 |
      | **+ anchor 1/2 + cycle + L_dist 1/50** | **90.6** / 88.8 / **88.6** | **26** / 82 | 32.7% | 0.38 | **-0.05 / 0.02 / 0.05 / 0.02** |
      - **angle**: 3× ≈ 1/1 (eval flat, back-projection indistinguishable); **10× breaks it** — −4 to −5 AUC, @3% 68%, coverage −6 pts, neck checker cells break near the body joint, sharp dark seams on the body in the mesh heatmap. The useful range is 1/1–3×.
      - **combo on the new main**: back-projection clean (close to cycle only, far better than anchor 1/1), mesh features as distinctive as cycle only, best @1% (26%) and the best soft AUC measured on this baseline. Anchor KL 0.98, L_dist 0.29.
      - **TAL'S DECISIONS (2026-09-15)**:
        - **`rkd_spatial_angle3` — NO ADDED VALUE FOR NOW, PARKED.** Back-projection: no improvement at any weight, and the strongest (10×) degrades quality. Features: a slight distinctiveness gain at EVERY weight, starting from the weakest. May come back later as a distinctiveness tool, not now.
        - **Global-mu control with in-segment-only neighbours — CLOSED, NOT RUN (Tal):** in-segment-only neighbours were already run in the past without a per-segment scale and gave no value, so the per-segment mu is what helped, and that is good enough. **Small-segment fixes (raise `min_pairs`, per-segment centre floor) — not needed now, maybe later.**
        - **Cycle / anchor / combo arms**: back-projection — no added value visually. Features — **wherever the cycle loss is present, distinctiveness improves markedly.** Whether to adopt it is still open ("we'll think later whether to take it or not"). MAIN stays `mu_learn_perseg`, unchanged.
    - **LAUNCHED 2026-09-15** as `scripts/run_prop_angle_strong_combo_CHAIN.sh` (log `logs/prop_angle_strong_combo_chain.log`): angle `sangle3_w2.65e-2` (3×) and `sangle3_w8.83e-2` (10×) → L_dist calibration (`logs/prop_dist_calibrate.log`) → the combo arm → comparison sets `isobbox_prop/comparison_sangle3_strong/` (MAIN / 1/1 / 3× / 10×) and `isobbox_prop/comparison_combo_new_main/` (MAIN / +cycle / +anchor 1/1 / +anchor 1/2 + cycle + L_dist).

### SMALL ANALYSIS SLIMMED + ONE PROCESS (Tal, 2026-09-15) — ~4.5 min -> ~20 s per arm, numbers identical
- **Timing of the old small path** (arm `sangle3_w8.83e-4`, from output mtimes): training ~3:40; pixel_to_vertex_nn 1:38 · soft mapping 0:40 · back-proj top1k 0:28 · back-proj soft 0:26 · PCA 0:59 · sim heatmap grid 0:45 · eval 0:44; comparison vs MAIN 1:36 (37 s of it RE-computing the heatmap as one row); comparison vs ZS 0:45.
- **Why pixel_to_vertex_nn was slow**: not the similarity (212,549 mask pixels x 3886 vertices is seconds on GPU) — the photo feature file is [1080, 810, 2304] float32 = **8 GB**, loaded from scratch by five separate python processes per arm (17.6 s per load, measured). All 212K pixels ARE needed: the top1k back-projection colours every mask pixel.
- **Tal's calls**: keep back-projection top1k; drop PCA; heatmap only as ONE ROW (no 2x2 grid); no per-arm comparison vs ZS (identical ZS side every time; ZS stays in sweep eval figures); merge the rest into one process.
- **Done**: `analysis/analyze_arm_small.py` (called by `analyze_isobbox_arm.sh` when `SMALL` is set) runs back-proj top1k + soft-snap + coverage + heatmap row + eval v2 in one process, reading an **in-mask feature cache** `demo/guitar/features_analyze/dino_sd_aligned/guitar_01_pix_dino_sd_features_aligned_inmask_guitar_01_click_270_370_sam_mask_2.pth` (212,549 x 2304 float32, 1.96 GB, rebuilt automatically if the source file changes). It no longer writes the 28 MB `*_pixel_to_vertex_nn.pth` (FULL mode still does). `run_isobbox_prop_QUEUE.sh` no longer compares each arm to ZS.
- **Verified against the old path on `sangle3_w8.83e-4`**: both back-projection PNGs and the heatmap row pixel-identical, eval AUC identical (89.78 / 89.20 / 88.20), per-point snap/argmax vertices identical, per-pixel soft-snap vertex identical. **19 s end to end.**
- FULL mode (`SMALL` unset) is unchanged. Consequence for comparison scripts: new SMALL arms have no PCA panel — `compare_isobbox_arms.sh` already skips PCA when missing; anything stacking PCA by hand must drop it.

### DISK CLEANUP 2026-09-15 (Tal approved the list) — **142.7 GB freed; `experiments/guitar` 70 GB, `demo/guitar` 38 GB**
- **Step checkpoints deleted (288 files, 24 encoder dirs)**; each dir keeps `encoder_checkpoint.pth`, `pred_f.pth`, `run_config.json`, `relational_loss.png`, and every demo dir keeps all its figures/eval: the 5 `sangle3_w*` arms; `mu_learn_perseg_nbrmix_bug`, `mu_learn_global_nbrmix`, `mu_closed_perseg{,_nbrmix,_nbrmix_bug,_logfit}`, `mu_closed_global_nbrmix`; SHIC-ONLY (`rkdw0`); cycle-only / anchor-only / combo on the new main; the OLD-main family (`truediag2d_T1` baseline, `_stepladder`, soft anchor 3.5e-7, strong cycle 1.05e-5, both 09-12 L_dist arms); the two isobbox copies of the stride-14 squash recipe (`encoder_isobbox_dino_sd_stride14_nosdsquare_..._T{0.01,1}`).
- **219 `*_pixel_to_vertex_nn.pth` deleted** from demo dirs (regenerable from `pred_f.pth` in ~30 s).
- **Kept in full**: MAIN `mu_learn_perseg` (its step 25 is the calibration state for every arm on it), both PROTECTED old-mesh squash runs (T=0.01, T=1), SD-aligned, and their `pixel_to_vertex_nn` files.
- **Consequence**: `scripts/run_isobbox_anchor_CALIBRATE.sh` (old main) can no longer run — its `_stepladder` step-25 checkpoint is gone. Calibrations on the new main read `mu_learn_perseg` step 25, which is intact.

### `isobbox_prop` — the PROPORTION direction's own root, and the RENAME (Tal, 2026-09-15)
**`demo/guitar/runs/isobbox_prop/`** holds every arm of the per-segment/proportion family and everything built on the MAIN baseline from now on. ZS, the SECONDARY baseline and all older controls stay in `demo/guitar/runs/isobbox/`. Routing is automatic: `run_dir()` in `scripts/lib_isobbox_common.sh` sends any demo name containing `_mu_` to `isobbox_prop` (used by `analyze_isobbox_arm.sh` and `compare_isobbox_arms.sh`). Encoder dirs stay in `experiments/guitar/`, eval files stay in `demo/guitar/eval_labels/v2_edge_inset/isobbox/` — only their names changed.
**Name rule inside `isobbox_prop`**: `mu_<closed|learn>_<global|perseg>`, then only what differs from the default (16 neighbours all in-segment, absolute fit): `_nbrmix` = 8 in + 8 out, `_logfit` = relative fit, `_bug` = before the per-segment fit fix of 09-14. `run_isobbox_mu_QUEUE.sh` builds these names.
| old token (logs, archive, 09-14 text) | new token |
|---|---|
| `mulearnsegfixinonly` | **`mu_learn_perseg`** (MAIN) |
| `muoptsegfixinonly` | `mu_closed_perseg` |
| `muoptsegfixinonlylog` | `mu_closed_perseg_logfit` |
| `muoptsegfix` | `mu_closed_perseg_nbrmix` |
| `muoptseg` | `mu_closed_perseg_nbrmix_bug` |
| `mulearnseg` | `mu_learn_perseg_nbrmix_bug` |
| `muoptglobal` | `mu_closed_global_nbrmix` |
| `mulearnglobal` | `mu_learn_global_nbrmix` |
- Renamed in all three places (demo dir + encoder dir incl. `run_config.json` `out_dir` + eval `.pth/.png`), plus the scripts of 09-15 (`run_isobbox_mu_{learn,closed}_perseg_{FULL,analysis}.sh`, `compare_mu_perseg_3way.sh`). **Not renamed**: log files in `/workspace/logs`, and the `source:` path text baked INTO already-built comparison PNGs (still shows `runs/isobbox/...`).

## THE NEW DIRECTIONS — Tal, 2026-09-14, recorded before any of them is started
L_dist is closed and the next move has to come from outside it. Tal put three candidates on the table plus one late addition, and asked that **all of them be written down and only ONE be pursued**. **Names, because "direction 1/2/3" is useless a day later** — use these tags everywhere:
| tag | one line | status |
|---|---|---|
| **`ANGLE-SPATIAL`** | RKD's angle term, in the SPATIAL domain | **BUILT AND SWEPT 2026-09-15 (1/10 … 10×) — PARKED by Tal: no back-projection gain, slight distinctiveness gain only; see the 09-15 section** |
| **`MU-LEARNED`** | `mu_3d_scale` becomes a learned scalar instead of a swept constant | **runs FIRST, it is a precondition for ANGLE-SPATIAL** |
| `SHIC-ONLY` | drop L_spatial entirely, train on the SHIC-derived terms alone | parked, Tal wants more SHIC terms first (see below) |
| `FROZEN-DELTA` | freeze phase-1's features, learn an added component (LoRA-style) | parked, deliberately — it REPLACES the anchor rather than joining it |

**`ANGLE-SPATIAL` — extend the term that actually works, instead of adding more feature-space terms.**
*"ה-spatial rkd שלנו בגדול משווה בין המרחק בין 2 פיקסלים למרחק בין 2 קודקודים... אולי שווה להוסיף לזה שהזווית שנוצרת בין center to 2 neighbors במימד התמונה צריכה להיות שווה לזווית שנוצרת בין הקודקודים של כל אחד מהם, בצורה soft."* The angle at the centre's mapped VERTEX, between the ray to neighbour 1's vertex and the ray to neighbour 2's vertex, should match the same angle measured between the three PIXELS. This is RKD's own angle term (Park et al.), and it is the spatial twin of the pairwise-angle term we already built and closed **in feature space** (09-04, ten arms, none beat spatial alone) — the spatial version has never been run.
- **Why it is the strongest candidate: it is the only one of the three that attacks the PROPORTION problem directly.** Tal's diagnosis of the eval gap is that the mapping's proportions are wrong, so labelled points land outside their region. Pairwise distances alone do not constrain proportion — a mapping can get every pairwise distance roughly right and still shear the object. **Angles are scale-invariant, which is exactly the missing constraint.**
- **METRIC: EUCLIDEAN, Tal's call 2026-09-14.** L_spatial is GEODESIC on both sides (d_2D inside the mask, d_3D on the mesh, each over its own diameter) and angles are not geodesic quantities, so the term deliberately mixes metrics: **Euclidean rays in the image plane vs chordal rays between the mapped 3D points.** The geodesically-correct alternative (tangent-space / log-map angles on the mesh) was considered and rejected as much more work for this first pass. **Any figure or note about this term must say "Euclidean angles" — a later reader will otherwise assume geodesic, like everything else here.**
- Cost: one new term in `modules/relational_loss.py`, calibrated by gradient norm like every other term, ~4 min/arm at stride 5.

**`MU-LEARNED` — make the proportion coefficient a LEARNED scalar (Tal, 2026-09-14, added after the other three).**
*"את מקדם הפרופורציה mu_3d_scale נהפוך אותו לפרמטר נלמד? שווה נסיון להריץ רק rkd spatial כזה?"* Run L_spatial alone with `mu_3d_scale` as a trained parameter instead of a hand-swept constant.
- **This runs BEFORE `ANGLE-SPATIAL`, because it is the same hypothesis at lower cost and it changes how the angle term should be read.** Global scale and shape are separable: a learned scalar fixes the GLOBAL zoom, angles fix the SHAPE. If the zoom is what is wrong, one scalar finds it in one run; if it is not, `ANGLE-SPATIAL` is the right tool and we will know that before building it.
- **Cheapest correct implementation is CLOSED-FORM, not gradient**: with `L = MSE(d_2D/mu_2D, d_3D/(mu_3D·s))`, the optimal `s` at each step is a ratio of sums over the sampled pairs. No parameter, no optimizer group, no lr to tune. A learned `nn.Parameter` is the fallback if the closed form turns out to interact badly with Adam.
- **The honest limit, worth stating before the run: one scalar can only fix an ISOTROPIC zoom.** The 09-10 measurement says `mu<1` compresses the NECK specifically, i.e. the error has a regional/anisotropic component that no single scalar can absorb. So this is a cheap screen, not an expected fix.
- Prior: the manual sweep already found `mu=1` optimal on eval (09-03) and the derived ratio measured 0.99 — but every one of those points was judged on a FIXED scalar chosen in advance, never on one the optimizer was free to move during training.

**`FROZEN-DELTA` — frozen features + a trained additive part (LoRA-style), to separate the spatial and feature domains.**
*"מימד הפיצ'רים קצת נפגע כאשר אנחנו מאמנים spatial rkd... אולי במקום לשנות את הפיצ'רים הקיימים פשוט להוסיף להם מידע, והפיצ'רים הקיימים יהיו קפואים."* Keep phase-1's vertex features frozen and learn an added component, so the spatial objective can only ADD information and cannot damage what phase-1 already has.
- **It COLLIDES with the ZS anchor, and Tal says that is the point: it is meant to REPLACE the anchor**, not to sit next to it — *"זה סוג של מחליף את ה-anchor, ואז על גבי זה נאמן spatial או אפילו feature domain, פשוט שלא יפגע במה שכבר קיים."* Anything built here must therefore drop the anchor, not add to it, and `drift` stops meaning what it means today.
- Tal's scope note: he means this for the SPATIAL term specifically. **The SHIC-derived terms did not damage the feature space — they improved it** — so this is not an argument against them.

**`SHIC-ONLY` — drop spatial RKD entirely and train only with the SHIC-derived terms (plus more of SHIC's own terms).**
*"יכול להיות שהפגיעה שעושה rkd spatial בפרופורציה מונעת מאיתנו להיות דומים ל-SHIC."* Train with the anchor + cycle + L_dist and no L_rel at all, then consider adding the SHIC terms we have not built (`L_eq`, `L_syn`).
- **This one is nearly free to probe: `REL_W=0` is already a supported flag.** The closest thing on record is the 09-04 arm that removed the spatial term under FEATURE-RKD and collapsed to 16.4 AUC — but that had no anchor, no cycle and no L_dist, so **it does not answer this question.** One run does.

- **RUN 2026-09-14 (Tal approved it as a check), and the prediction held: it stays at ZS.** `REL_W=0` on the adopted recipe (anchor + cycle stride 5 + L_dist 1/50). Arm `..._retstride5_rkdw0_distT1_g2.7951e-06_...`.
  | | SHIC-ONLY (w_spatial=0) | same recipe WITH L_spatial | ZS |
  |---|---|---|---|
  | AUC geo snap | **88.5** | 78.9 | 87.9 |
  | @3% / @10% | 78% / 100% | 22% / 99% | 78% / 99% |
  | mean err | 2.3% | 4.2% | 2.4% |
  | soft-snap cov | 30.8% | 37.9% | 30.3% |
  | drift@300 | 0.28 | 0.44 | 1.00 |
  | anchor_KL@300 | **0.22** | 2.9 | 0 |
  | top1 agreement with ZS | **0.705** | 0.011 | 1.00 |
  - **It is the first phase-2 arm ever to beat ZS on eval (88.5 vs 87.9) — and that is NOT a result, it is the proof that it did not move.** 70% of pixels keep ZS's own argmax and anchor_KL is 0.22; the arm is ZS with a cosmetic nudge. Tal's read, same: *"כמו שציפינו זה נשאר כמו ה-ZS."*
  - **What it DOES establish, and it is worth keeping:** anchor + cycle + L_dist **do not damage phase-1** — the ~4.7% convergence that every arm since 09-08 suffers is caused by `L_spatial` alone. Whether those three terms ADD anything is still unknown, and cannot be answered while they sit this close to ZS.
  - **Tal, 2026-09-14: what to ADD to this arm is a question for another day, not today.**
- **Tal's position before the run** (kept, it is the reasoning): he is not convinced anchor + cycle + L_dist is enough on its own and wants to consider adding more of SHIC's terms first. **My answer, recorded so it is not re-asked:** as a METHOD it is probably not enough, and for a structural reason — SHIC trains an IMAGE encoder over a dataset of many images with augmentations, where `L_eq` and `L_syn` supply the signal that ties different views together; we train a MESH-side encoder on ONE photo, so removing L_spatial leaves only a pull toward ZS plus self-consistency, and the likely outcome is that the run simply converges back to ZS. **As a DIAGNOSTIC it is still worth one run** (`REL_W=0`, one flag, ~11 min) precisely because that outcome would be informative: it would say phase-2's entire deviation from ZS is L_spatial's doing. Run it as a measurement, never quote it as a candidate recipe.

**ORDER AGREED WITH TAL, 2026-09-14: `MU-LEARNED` first (cheap screen of the proportion hypothesis), then `ANGLE-SPATIAL` (the build), `SHIC-ONLY` and `FROZEN-DELTA` parked.**

### `MU-LEARNED` — BUILT AND RUN THE SAME DAY, ALL FOUR VARIANTS (2026-09-14)
Code: `--mu_mode {fixed,optimal,learned}` + `--mu_scope {global,segment}` + `--mu_lr` in `phase2/train_relational_loss.py`, `optimal_mu_3d_scale()` in `modules/relational_loss.py`, queue `scripts/run_isobbox_mu_QUEUE.sh <mode:scope> ...`. `fixed` is bit-identical to every earlier run. A pair's group is its CENTRE's segment. Log field `mu_s=` (global) or `mu_s[min/med/max]=` (per segment).
**All four arms are L_spatial ONLY** — no anchor, no cycle, no L_dist — so the control is the spatial-only baseline.
| arm | mu it settled at | AUC snap/argmax/soft | @3% | @10% | cov | drift@300 | L_rel@300 |
|---|---|---|---|---|---|---|---|
| **baseline, mu FIXED 1** | — | **77.0 / 76.8 / 75.1** | 21% | **97%** | **40.1%** | ~0.43 | ~1.9e-4 |
| optimal, global | 0.724 | 71.5 / 71.4 / 70.6 | 58% | 80% | 28.7% | 0.69 | **2.5e-5** |
| learned, global | 0.737 | 72.7 / 72.2 / 71.5 | **64%** | 80% | 29.2% | 0.66 | — |
| optimal, per segment | 0.724–0.738 | 71.7 / 71.9 / 70.8 | 59% | 80% | 28.5% | 0.69 | — |
| learned, per segment | 0.749–1.000 | 72.6 / 72.5 / 71.5 | 61% | 80% | 30.7% | 0.65 | — |
- **THE NUMBER IS ~0.73, and all four routes agree on it** — closed form and Adam, global and per-segment. It is close to the 0.75 Tal wanted to try back on 09-03, and far from the 0.99 the normalizer-ratio derivation predicted (09-03 §7), which is one more sign that derivation does not point at the interesting region.
- **PER-SEGMENT ADDS NOTHING, and this is a clean answer to Tal's anisotropy idea**: the closed-form fit spans 0.724–0.738 across all 17 segments, a 2% spread. (The learned per-segment arm shows one segment stuck at exactly 1.000 — that is a segment that received almost no gradient, not a finding.) **The correct zoom is uniform over the object, so the proportion error Tal sees is NOT regional scale.**
- **THE TRADE-OFF IS THE SAME IN ALL FOUR ARMS AND IT IS LARGE IN BOTH DIRECTIONS**: @3% goes 21% -> 58-64% (roughly three times as many points land inside 3% of D), while the tail collapses (@10% 97% -> 80%), coverage drops ~10 points and AUC drops 4-5.
- **WHY, and it is structural, not a bug: with the scale free the loss becomes SCALE-EQUIVARIANT.** Shrink every mapped 3D distance by c and the optimal s shrinks by c too, leaving the residuals identical — so the global size of the mapping is no longer constrained at all, only its relative structure. Measured: `mu_3D_live` fell 0.57 -> 0.42 and the loss fell ~8x. **Any future use of a free scale needs a separate absolute constraint** (the ZS anchor is exactly such a term, and none of these four arms had it).
- **Awaiting Tal's visual verdict** on `comparison_vs_mu1/` in each arm's demo dir.

### `MU-LEARNED`, SECOND ROUND — TAL FOUND THE BUG IN THE PER-SEGMENT FIT; FIXING IT MADE THE ARM COLLAPSE
**Tal's read of the first per-segment arm (2026-09-14):** the body's proportions improve, but the NECK and the HEADSTOCK get much worse — *"בבטן הגיטרה יש שיפור בפרופורציות אבל בצוואר ובראש זה גרוע מאוד"* — and he did not believe the per-segment fit could return the same answer as the global one. **He was right; it was not measuring per segment at all.** Three biases, all pulling every segment to the global value:
1. **Half of every centre's pairs are CROSS-segment by construction** (8 in-segment + 8 out-of-segment neighbours), and a pair was charged to its CENTRE's segment — so the same neck<->body pairs entered all 17 fits.
2. **The closed form is dominated by long pairs, quadratically** (`s = Σb²/Σab`), and the longest pairs are exactly the cross-segment ones.
3. **The centres are split by pixel AREA: 1367 of 2048 land in the body, and the smallest segments get 5 each** (measured). A 5-centre segment has ~40 in-segment pairs, barely over the `min_pairs=32` floor.

**FIXES APPLIED** (`optimal_mu_3d_scale(pair_mask=...)`, `per_pair_mu_scale()`):
1. a segment's scale is fitted ONLY from pairs with both ends inside it;
2. a cross-segment pair uses the GEOMETRIC mean of the two segments' scales (a scale is multiplicative, so half and double must cancel);
3. **`--mu_fit_space log`** (relative instead of absolute residual) exists but is **OFF by default — Tal's call**: he wants the long in-segment pairs to carry the scale, and unlike 1 and 2 this one is a modelling choice, not a bug.
**NOT done, recorded so it is not forgotten (Tal: "תרשום שלא נשכח מזה"): a per-segment FLOOR on the number of centres.** Sampling is proportional to pixel area, so the neck and headstock cannot support a scale of their own.

**RESULT — the corrected per-segment arm is the worst arm measured all day:**
| arm | AUC snap/argmax/soft | @3% | @10% | cov | mu range at step 300 |
|---|---|---|---|---|---|
| baseline mu=1 | **77.0 / 76.8 / 75.1** | 21% | **97%** | **40.1%** | — |
| per-segment, BEFORE the fix | 71.7 / 71.9 / 70.8 | 59% | 80% | 28.5% | 0.724–0.738 (i.e. global) |
| **per-segment, AFTER the fix** | **58.9 / 52.2 / 56.1** | 9% | 68% | 23.5% | **0.789–3.400** |
- **The fix is correct and it broke the arm, which is itself the finding: a free per-segment scale is not stable in this form.** Once each segment sets its own scale from its own pairs, the segments stop sharing a common unit — and half the loss consists of cross-segment pairs, which must then satisfy a target built from two independently-drifting scales.
- **There is a feedback loop**: features move -> the segment's scale refits -> the features are free to move further. Visible in the log: the spread ran 0.594–1.887 at step 150 to 0.789–3.400 at step 300. The 3.4 is almost certainly a small segment fitting ~40 noisy pairs.
- **To rescue the direction, three options, none tried**: shrink each segment's scale toward the global one, FREEZE the per-segment scales after an initial fit instead of refitting every step, or add the per-segment centre floor first.
- **The prior per-segment numbers must not be quoted as "per-segment works"** — that arm was a global fit wearing a per-segment label.
- Gotcha that cost ~10 min: under `set -e`, `VAR="...$( [ x = y ] && echo z )"` kills the script silently when the test is false. Never put a conditional command substitution in an assignment in these queue scripts.

**2026-09-14 (sixteenth pod) — L_dist WAS SWEPT UPWARD TO FULL STRENGTH AND SETTLED AT SHIC'S OWN 1/50; stride 5 was wired into every script; the comparison figures were reworked (row layout, diff highlighting, legend under the plot).**

### 1. TAL'S DECISIONS
- **L_dist: adopt γ = 1/50 of the weighted anchor (2.7951e-06) — SHIC's own γ/α ratio (0.002 / 0.1), and stop sweeping.** Tal's visual read of the whole sweep: *"L_dist עוזר ל-distinctiveness של מימד הפיצ'רים, גם אפילו שהוא מופעל באופן חלש. מבחינת back proj קצת משפר את החלקות ככל שזה יותר חזק."* Since weak already buys the distinctiveness, SHIC's ratio is the pick. **Caveat to keep straight: SHIC's 1/50 is relative to L_pseudo (hard CE); ours is relative to the SOFT anchor, calibrated by gradient norm — the same ratio, not the same reference term.**
- **Sweep DOWN was rejected before it ran** (Tal: the term is weak enough already; strengthen it instead, to see what it does).
- **`T_dist` STAYS 1. The 0.1 arm was run and rejected on sight** — *"לא רואה סיבה לקחת את זה, לא רואה שום שיפור"*. **L_dist is now fully closed: γ=1/50, T_dist=1, hard target.** (§2b)
- drift: see the reading rule Tal gave, recorded in the 09-13 entry's NEXT POD item 3.

### 2. THE UPWARD γ SWEEP — the term responds, the eval does not
All four arms on the soft anchor + cycle c=1.05e-5 with **return grid stride 5**, so the ladder is internally matched (the 09-12 L_dist arms used the full return and are NOT on this ladder).
| arm | AUC snap/argmax/soft | L_dist@300 | tail>0.2D | argmax cov | cyc refs | drift@300 |
|---|---|---|---|---|---|---|
| NO L_dist (control) | 78.8 / 71.7 / 76.1 | — | — | 11.4% | 336 | 0.55 |
| **γ=2.7951e-06 (1/50, SHIC) — ADOPTED** | 78.9 / 69.4 / 76.1 | 0.298 | 0.581 | 11.5% | 337 | 0.38 |
| γ=4.659e-05 (1/3) | 77.7 / **73.6** / 75.2 | 0.283 | 0.553 | 11.1% | 320 | 0.40 |
| γ=1.3976e-04 (1/1) | **79.0** / 71.2 / 75.6 | **0.272** | **0.530** | 8.2% | 249 | 0.22 |
| ZS (reference) | 87.9 / 86.2 / 85.7 | — | — | 23.3% | — | 1.00 |
- **The term itself scales exactly as designed: L_dist and the far-mass tail fall MONOTONICALLY with γ** (0.298→0.283→0.272 and 0.581→0.553→0.530). The floor under a uniform p is 0.687, so the tail is genuinely moving.
- **None of it reaches eval.** All four arms sit inside 1.3 AUC points on snap with no trend; argmax bounces (69.4 / 73.6 / 71.2) at seed-noise scale.
- **The one clear cost at full strength:** at γ=1/1 argmax coverage drops 11.4% → 8.2% and the cycle's reference-vertex count 336 → 249, i.e. the mass concentrates on fewer vertices.
- Figures, all five, all arms in one set: `demo/guitar/runs/isobbox/comparison_dist_gamma_sweep/`.

### 2b. `T_dist=0.1` — THE LAST UNTESTED KNOB, RUN AND CLOSED
Arm `..._retstride5_distT0.1_g7.6667e-07_...`, same anchor + cycle + stride 5, γ recalibrated to the SAME 1/50 ratio (γ scales with T because the gradient carries 1/T, so 7.6667e-07 here is not a weaker arm — it is the same strength with different leverage).
| | T_dist=0.1 | T_dist=1 (adopted) | no L_dist |
|---|---|---|---|
| AUC snap/argmax/soft | 78.4 / **73.4** / 75.9 | 78.9 / 69.4 / 76.1 | 78.8 / 71.7 / 76.1 |
| L_dist@300 | 0.116 | 0.298 | — |
| tail>0.2D: calibration → step 300 | 0.376 → **0.159 (−58%)** | 0.632 → 0.581 (−8%) | — |
| argmax cov | 9.6% | 11.5% | 11.4% |
| drift@300 | 0.25 | 0.38 | 0.55 |
- **A low T_dist gives the term far more grip** — it removes 58% of the far mass against 8% at T=1. **But part of the low absolute tail is the temperature itself, not the training**: a sharper p starts closer to the target (0.376 vs 0.632 before a single step), so only the RELATIVE drop is a fair comparison.
- Eval is flat again (argmax +4, snap/soft −0.5, coverage −2 points), and **Tal saw no visual improvement, so the arm is rejected.** The pattern of the whole day holds: L_dist's own diagnostics respond to every knob, and none of it reaches the evaluation.
- Comparison figures `.../bsb_isobbox_..._distT0.1_g7.6667e-07_.../comparison_vs_T_dist1/` (rows differ only in T_dist).

### 3. SCRIPT WORK
- **stride 5 is now the default everywhere** (`run_isobbox_cycv2_QUEUE.sh`, `run_isobbox_dist_QUEUE.sh`, `run_isobbox_anchor_CALIBRATE.sh`); `CYC_STRIDE=1` restores the full 212549-pixel return. The L_dist queue had ignored the flag entirely, which is why every 09-12/09-13 L_dist arm cost 15 min instead of 4.
- **`allpix` IS GONE EVERYWHERE** (Tal asked for the full fix, not just the demo side): 15 demo run dirs + 4 comparison dirs, 19 encoder dirs, 38 eval tag files, and the three scripts that build those names (`ALLPIX_TAG`/`BASE`/`TAGX` all emptied). Encoder dirs and eval tags still keep `_fuse16_truediag2d`, and the queues still map long→short with `demo_run()`.
  **Why it had been deferred, since it looked trivial:** the name is not stored in one place — it is in the encoder dir, the eval `.pth`/`.png` tag and the demo dir, and each is built by a different script, so a half-rename silently breaks the eval lookup rather than erroring. And there was one real COLLISION: the centers-return arm at c=1.05e-6 already owned the short name. That arm is now explicitly `_retcenters` in all three places, which is the correct name anyway now that all-pixel is the default.
- **Similarity heatmaps in 2-arm comparisons are now ONE ROW of 8 panels per arm, rows stacked** (`compare_isobbox_arms.sh`), so each query sits directly above its counterpart. It builds the row strip itself when an arm only has the old 2x2 grid; the queues pass `PF_A`/`PF_B` (each side's `pred_f.pth`) for that. This is the layout `compare_isobbox_3way.sh` has used since 09-08 — the 2-way path had been left behind.
- **Figure labels now highlight what DIFFERS between rows** (`make_run_vs_baseline_comparison.label_band`, used by both stackers): tokens carried by most rows are dimmed grey, the rest are drawn yellow. Punctuation is ignored when comparing (`stride 5,` = `stride 5`), and REFERENCE rows (ZS / baseline, `is_reference_label`) are excluded from the comparison and drawn plain — including them emptied the shared set and lit up the whole figure.
- **The eval legend moved OUT of the axes into its own strip under the three panels** (`compare_eval_runs.py`): the labels had grown long enough to cover the curves. One legend for the figure, one line per arm; per-panel legends were tried first and spilled into the neighbouring panel. Per-metric AUC is still in each metric's table.

### 4. DISK (Tal approved) — **`experiments/guitar` 136 GB -> 96 GB, 40 GB freed**
Step checkpoints deleted from the 8 arms of 09-13/09-14 (the stride-5, softqT, hard-anchor and γ-sweep arms); each keeps `encoder_checkpoint.pth`, `pred_f.pth`, `run_config.json`, `relational_loss.png`, so eval and every figure still rebuild. `analysis/soft_dist_median_check.py` deleted too (written 09-13, never run, and the soft-target direction it was meant to pre-screen is closed).

### STATE AT POD CLOSE (2026-09-14) — **NOTHING IS RUNNING.** Every arm below is trained, analyzed and compared; every queue exited 0.
Ten arms ran today: 3 γ-sweep + 1 T_dist=0.1 (L_dist, closed), 4 `MU-LEARNED` + 1 corrected per-segment, 1 `SHIC-ONLY`.
**Where each direction stands (but read THE RESULT OF THE DAY below first — it changed the picture at pod close):**
- **`MU-LEARNED`: the global fit is real and worth a decision** — ~0.73 by all four routes, @3% 21% -> 58-64%, at the cost of the tail (@10% 97% -> 80%), coverage (-10 pts) and AUC (-4). **Tal's visual verdict: the body improves, the neck and headstock get worse.** **THE PER-SEGMENT VARIANT IS NOT A WAY OUT as built** — fixing its bug collapsed the arm to 58.9 AUC (see the `MU-LEARNED` SECOND ROUND section above for the three rescue options, none tried).
- **The one arm NOT yet run and the obvious next one: a fitted global mu TOGETHER WITH the ZS anchor.** All four mu arms were L_spatial-only on purpose, and a free scale removes the only absolute constraint on the mapping's size — the anchor is exactly such a constraint. One run, ~11 min. Offered at pod close, not yet approved.
- **`SHIC-ONLY`: answered and closed as a diagnostic** (it stays at ZS; 70% of pixels keep ZS's argmax). Tal: what to ADD to it is for another day.
- **`ANGLE-SPATIAL`: not started.** Euclidean angles, decided. It is still the direction Tal picked to go deep on.
- **`FROZEN-DELTA`: not started, parked** (it replaces the anchor, so it is a bigger build).
**Disk:** `experiments/guitar` 96 GB -> ~130 GB (10 new arms; the `MU-LEARNED` and `SHIC-ONLY` arms still carry step checkpoints, ~6 GB each). `/workspace` well under the 500 GB ceiling.
**Uncommitted code added today:** `optimal_mu_3d_scale()` + `per_pair_mu_scale()` in `modules/relational_loss.py`; `--mu_mode/--mu_scope/--mu_lr/--mu_fit_space` in `phase2/train_relational_loss.py`; `scripts/run_isobbox_mu_QUEUE.sh`; the figure changes in `analysis/{make_run_vs_baseline_comparison,stack_images_nway,compare_eval_runs}.py` and `scripts/compare_isobbox_arms.sh`; stride-5 defaults in the three queue/calibrate scripts.

### **THE RESULT OF THE DAY — IN-SEGMENT-ONLY PAIRS + A PER-SEGMENT FITTED SCALE BEATS ZS ON EVERY METRIC (2026-09-14)**
Tal's idea at pod close: if a per-segment scale breaks because cross-segment pairs have to serve two scales, **remove the cross-segment pairs** (`--num_neighbors_in_segment 16 --num_neighbors_out_segment 0`, env `NBR_IN=16 NBR_OUT=0`). Arm `..._mu_closed_perseg_...`, L_spatial ONLY, closed-form per-segment scale, seed 0.
| | **in-segment only + per-segment mu** | baseline mu=1 | ZS | SHIC-ONLY |
|---|---|---|---|---|
| AUC snap/argmax/soft | **91.0 / 90.3 / 89.1** | 77.0 / 76.8 / 75.1 | 87.9 / 86.2 / 85.7 | 88.5 / — / — |
| mean err | **1.8%** | 4.6% | 2.4% | 2.3% |
| @1% / @3% / @5% / @10% | **29 / 82 / 96 / 100** | 1 / 21 / 62 / 97 | 12 / 78 / 91 / 99 | 14 / 78 / 93 / 100 |
| soft-snap cov | 33.3% | 40.1% | 30.3% | 30.8% |
| drift@300 | 0.72 | 0.43 | 1.00 | 0.28 |
| mu range @300 | 0.688–1.964 (median 0.921) | — | — | — |
- **This is the first arm that beats ZS by MOVING, not by standing still.** SHIC-ONLY's 88.5 came with 70% of pixels keeping ZS's own argmax; this one is +3.1 AUC over ZS and more than doubles @1% (12% -> 29%).
- **Why it most likely works, and it is exactly Tal's proportion diagnosis**: with every pair inside one segment, each segment gets the scale that fits IT, and the loss is no longer forced to reconcile neck and body through a single shared target. Removing the cross-segment pairs is also what stabilised the per-segment fit — the scales span 0.688–1.964 here versus a runaway 0.789–3.400 when cross-segment pairs were present.
- **Caveats to settle before this is treated as the recipe**: (1) ONE seed — the project's seed floor is 1.6-2.4 AUC and this gap is far larger, but it has not been repeated; (2) nothing now ties the segments to each other, so global structure rests entirely on the per-segment scales agreeing — the failure mode to look for is a whole part sliding as a unit; (3) it was run WITHOUT the anchor, cycle and L_dist; (4) `drift` is not a reliable proxy here — SHIC-ONLY sits at 0.28 while keeping 70% of ZS's argmax, so cosine drift and correspondence agreement are measuring different things.
- **Tal's visual verdict: approved** — *"נראה מעולה"*, and the three-way figure (ZS / baseline / this arm) is in `.../comparison_vs_baseline_and_ZS/`.
- **`--mu_fit_space log` WAS TESTED ON TOP OF THIS ARM AND IS REJECTED** (arm `..._mu_closed_perseg_logfit_...`): **76.9 / 76.1 / 74.5**, i.e. it throws the entire gain away and lands back at the baseline. The scales also ran wild (0.940–4.156, median 1.704) and drift fell to 0.53, while coverage rose to 41.7%. **Tal's instinct was right: the long in-segment pairs must carry the scale.** The flag stays in the code, default `abs`, and this is the measurement that closes fix 3. Figure: `.../comparison_abs_vs_log/` (4 rows: ZS, baseline, abs, log).
- **What the small segments actually contribute, asked by Tal and worth keeping**: with in-segment-only neighbours, a centre in a 305-pixel speck draws all 16 neighbours from inside that speck, so every one of its pairs is a few pixels long — below DINO's own 14 px patch, where the two features are nearly identical. Those pairs are mostly noise in the loss, AND they are the ONLY data fitting that segment's scale, which is where extreme values like 1.96 come from. A 5-centre segment yields 80 pairs, just over the `min_pairs=32` floor, so it gets its own noisy scale instead of falling back to the global one. **The robust one-line fix is to RAISE `min_pairs` (say 300); Tal deferred it — results are good enough and it can be revisited if something breaks.**
- **Segment granularity is NOT a knob we have**: the 17 fine segments come from SAM via `analysis/build_fine_segments.py`; there is no coarser body/neck/head map on disk. **Tal declined building one by hand** — the pipeline has to stay robust across images and objects. Their sizes are very uneven: body 66.9% of pixels, neck 16.3%, head 4.3%, and eight segments under 1% each (smallest 305 px), which is also how the centres split (1367 / 328 / 85 ... / 5).

### NEXT POD
1. **START FROM THE RESULT OF THE DAY.** The arm to build on is `..._mu_closed_perseg_...`: L_spatial with 16 in-segment neighbours and a closed-form per-segment zoom, 91.0 / 90.3 / 89.1, the first arm that beats ZS by actually moving. Obvious next steps, in order: (a) a second seed, (b) add the anchor + cycle + L_dist on top of it, (c) the global-zoom control with in-segment-only neighbours, to separate what the zoom bought from what dropping cross-segment pairs bought.
2. **GIT — the whole 09-10→09-14 backlog is still uncommitted** (Tal: commit at end of day; it did not happen on 09-14 either).
3. **`MU-LEARNED` global-only is superseded** by item 1 but not disproven: it traded the tail for @3%. Do not re-run the per-segment variant WITH cross-segment pairs — that configuration is closed.
4. **Build `ANGLE-SPATIAL`** — RKD's angle term in the spatial domain, Euclidean rays, calibrated by gradient norm like every other term.
4. **L_dist IS CLOSED** (γ=1/50, T_dist=1, hard target, on the soft anchor + cycle at stride 5). No knob on it is left untested: weight swept 1/50→1/1, target hard vs soft, temperature 1 vs 0.1, companion soft vs hard anchor.
5. **L_dist IS CLOSED** (γ=1/50, T_dist=1, hard target). No knob on it is left untested.
6. **TAL'S OWN FRAMING OF THE TWO BIG OPEN THREADS, 2026-09-14 — both were phrased wrongly above and in the 09-13 entry, this is the correction:**
   - **drift is not a "confound". It is the job.** *"זאת פשוט העבודה שלנו עכשיו שאנחנו רוצים לשנות את ה-ZS במידה מסוימת, פשוט עוד לא ידוע כמה."* Phase-2 is SUPPOSED to move the features off phase-1; the open part is only HOW FAR. So drift is the quantity being tuned, not an error term to control for.
   - **Why ZS wins on eval — Tal's diagnosis: a PROPORTION problem, not a correspondence problem.** The spatial RKD does connect the image domain to the mesh domain well, but the proportions come out wrong, so **many labelled eval points land OUTSIDE their own region** and are scored as far misses. That is what the eval gap is measuring. **Tal is working on a fix and will bring it** — do not start a competing direction against this one without asking.

**2026-09-13 (fifteenth pod) — THE FULL-SHIC ARM WAS RUN (hard anchor T=1: features leave phase-1 entirely), SOFT-TARGET L_dist CHANGES NOTHING, and the cycle return leg was CUT TO A STRIDE-5 GRID: 3.5x faster training at equal or better eval. Tal adopted stride 5.**
*(The pod closed before notes were written; this entry was reconstructed on 09-14 from the logs plus the 09-13 transcript, teleported with `claude --teleport <session-id>` — see §5.)*

### TAL'S DECISIONS
- **Stride-5 return: ADOPTED FOR RUNTIME ONLY.** Tal, restated 09-14: **the ONLY advantage is training time; on quality it is slightly WORSE, and that is being tolerated in exchange for the speed.** Do not read the eval table below as stride 5 winning — *"התוצאות דומות אך כן רואים קצת פגיעה בחלקות במימד הפיצ'רים. אפשר כרגע להמשיך עם זה לצורך נוחות וזמן ריצה"*. **It is NOT wired as a default: it is opt-in via `CYC_STRIDE=5`, and `run_isobbox_dist_QUEUE.sh` does not read it at all** (the edit making it the default was in flight when the pod died).
- **Soft-target L_dist: no visible change** — *"מבחינה ויזואלית אני כמעט לא רואה שינוי עם T=0.1"*. The hard target stays; this closes the departure-from-SHIC question for L_dist.
- Approved the stride flag + the matched control run (*"כן מאשר"*), and asked for an arm identical to the full return except for the stride.

All arms below on anchor + strong cycle (T_cyc=0.05, c=1.05e-5), w_spatial=1, eval v2 n=100, read T=1. Reference rows from 09-12: control 76.9/71.0/74.9, hard L_dist γ=1/50 78.5/73.3/76.1.
| arm | AUC snap/argmax/soft | @3% snap | argmax cov | soft-snap cov | anchor_KL@300 | drift@300 |
|---|---|---|---|---|---|---|
| **full SHIC**: `--anchor_hard` T_anchor=1 λ=2.6382e-05 + L_dist T_dist=1 γ=2.8313e-06 (1/50) | 77.6 / 73.2 / 72.0 | 35 | 5.35% | 30.0% | 7.19 | **−0.18** |
| soft-target L_dist, q_T=0.05, γ=2.9610e-06 | 78.3 / 72.4 / 76.2 | 24 | 10.65% | 37.75% | 4.10 | 0.37 |
| soft-target L_dist, q_T=0.1, γ=3.4485e-06 | **79.3** / 72.8 / 75.9 | 28 | 11.55% | 36.0% | 3.58 | 0.51 |
| no L_dist, cycle return on grid **stride 5** (8505 px instead of 212549) | 78.8 / 71.7 / 76.1 | 27 | 11.4% | 36.67% | 3.07 | 0.55 |

### 1. FULL SHIC (hard anchor) — THE FEATURES LEAVE PHASE-1 ENTIRELY
**drift@300 = −0.18: the mesh features end up ANTI-correlated with phase-1**, argmax coverage collapses to 5.35% (soft arms ~11%), soft-snap coverage 30.0% vs ~37%, anchor_KL 7.19. AUC lands at the soft L_dist arm's level (77.6/73.2/72.0 vs 78.5/73.3/76.1) but with far worse coverage, and the mesh features visibly collapse in `4_features_sim_heatmap.png` — the soft arms keep vertex_2885's neck-vs-body separation, the hard anchor does not. **The hard-anchor control, open since 09-10, is now CLOSED: our soft anchor is the right choice.**

### 2. SOFT-TARGET L_dist — NO EFFECT, DIRECTION CLOSED
New flag `--dist_soft_target_temperature` (env `DIST_QT`, dir tag `_softqT<T>`): the L_dist target becomes `E_{y~q_ZS at T}[d(x,y)]` instead of `d(x, argmax q_ZS)`. Ran at q_T=0.05 and 0.1; both sit inside seed noise of the hard target, and Tal saw no visual difference.
**Why it was predictable, and the pre-check that was offered:** soft L_dist is still LINEAR in p, so its minimizer is a delta at the **geodesic median of q_ZS**. At T_q=0.01 q spans ~75 vertices with 49% of the mass inside 3% of D, so the median ≈ the argmax and the run repeats the hard one; at T_q=1 q is ~uniform and the median is the middle of the mesh, which would pull every pixel to the body. `analysis/soft_dist_median_check.py` measures d(argmax, median)/D directly — **written but never run** (Tal chose to run the training arms instead).

### 3. STRIDE-5 RETURN LEG — 3.5x FASTER, AND IT COSTS NOTHING ON EVAL
Tal's idea: land the cycle's return leg only on the pixels of the stride-5 grid we already have.
- **The stride-5 geodesic table is NOT needed** — the live table's columns are all 212,549 mask pixels, so d(center, grid pixel) is a column selection. Exact lookup, not an approximation.
- New flag `--cyc_return_stride` (env `CYC_STRIDE`, dir tag `_retstride<s>`): 212,549 → 8,505 pixels, which fits in ONE pass, so the chunking + gradient checkpointing that made every run since 09-10 slow is gone.
- **Training 4 min 19 s vs 15.4 min.** For reference: centers-only return was ~3.3 min, and the all-pixel return is what cost the 12 extra minutes (each chunk's forward pass computed twice).
- **Step-25 calibration matches the full return to within 0.01%** (loss and grad norm, `logs/cyc_stride{1,5}_calibrate_check.log`), but **the two runs do NOT follow the same path**: at step 300 stride 5 has drift 0.55 vs 0.29 and anchor_KL 3.07 vs 5.59, i.e. it ends up CLOSER to phase-1. The eval numbers come out equal or slightly higher (78.8/71.7/76.1 vs 76.9/71.0/74.9), **but Tal's verdict is that quality is slightly WORSE (less smoothness in feature space) and the trade is being made for speed alone** — the AUC edge is not evidence for stride 5.

### 4. WHY A HARD (argmax) TARGET STILL TRAINS — Tal asked, durable
argmax is not differentiable, but **the gradient never passes through it**: it is applied to the FROZEN phase-1 teacher, which has no trainable parameters, so `x̃ = argmax q_ZS` is a constant — exactly like a class label. The loss is computed on the live student's softmax `p`, which is differentiable: hard anchor gives `∂L/∂logits = p − onehot(x̃)`, and L_dist gives `p(x)·(d(x) − E_p[d])/T` with `d(x, x̃)` a constant row of the geodesic table. **It would break only if argmax were applied to the STUDENT** (e.g. "distance from the student's top-1"), which is why every term here works on the full p.
Same mechanism in both references — only the label's SOURCE differs: **CSE** = human-annotated ground-truth vertex (`embed.py` hard CE; `soft_embed.py` = Gaussian-over-geodesic smoothing of that target), **SHIC** = argmax of frozen foundation features (no-grad), **ours** = argmax of frozen phase-1. All three keep the cycle loss fully soft on both legs.

### 5. POD/HOUSEKEEPING
- **GPU this pod was an RTX A4500, 20 GB** (up from 16 GB) — the OOM warning from 09-12 still applies: run queues ONE AT A TIME.
- **DISK CLEANUP WAS DONE: `experiments/guitar` 241 GB → 115 GB, `/workspace` now 316 GB of 500.** Deleted: the step checkpoints of 24 closed isobbox arms (mu sweep, mu0.75+anchor, soft anchor T=0.01 w3.5e-6/e-8, soft anchor T=1, cycle T_cyc=1 and T_cyc=0.05 losing weights, w_spatial 0.3/0.1, huber/resamplecenters, phase4, centers-return c1.05e-6) **plus the whole partial `..._cycv2T1_c1.19e-5_...` dir** — so item 3 of the 09-12 list is CLOSED. Each cleaned arm keeps `encoder_checkpoint.pth`, `pred_f.pth`, `run_config.json`, `relational_loss.png`, so eval still runs on all of them. Kept in full: the step ladder (calibration reads step 25), the isobbox baseline, the soft-anchor 3.5e-7 control, strong cycle c1.05e-5, both L_dist arms, the two protected old-mesh runs.
- Figures for every arm: `demo/guitar/runs/isobbox/<run>/comparison_vs_*`.
- **A LOST POD IS RECOVERABLE:** `claude --teleport <session-id>` (binary at `/root/.vscode-server/extensions/anthropic.claude-code-*/resources/native-binary/claude`) re-opens a previous session's transcript in a terminal — that is how this entry was written. It must be run BY TAL in a terminal (it stops on interactive setup screens), and the history is NOT written to a local `.jsonl`; ask that session to write a summary to `/workspace` instead. A public claude.ai session link is NOT readable by the pod (403).

### NEXT POD, in order (written 2026-09-14 from the recovered 09-13 session)
**Nothing is running.**
1. **Wire stride 5 in properly** — `CYC_STRIDE=5` is opt-in only and `run_isobbox_dist_QUEUE.sh` ignores it. Decide: default in both queue scripts, or keep explicit.
2. **L_dist γ sweep DOWN (1/100, 1/200) and `T_dist ≈ 0.1`** — still the only untested part of L_dist (open since 09-12). Now cheap: with stride 5 an arm costs ~4 min.
3. Open question nobody has answered: stride 5 ends CLOSER to phase-1 (drift 0.55 vs 0.29) from an identical step-25 state. If the drift, not the stride, is what carries the eval gain, the comparison is confounded the same way the w_spatial and γ sweeps were.
   **HOW TO READ `drift` — Tal, 2026-09-14, and this corrects the confident phrasing used above and on 09-11/09-12.** drift = cosine of the mesh features vs phase-1 (ZS = 1.00). **There is no known good value, and it is NOT an objective.** drift=1 is not good (it is ZS, i.e. no phase-2 at all); drift≈0 is probably also not good (the features have left the anchor entirely). Nobody can currently say which value means a healthy run, so: **report drift next to every eval number, use it to check whether two arms are even comparable — but do NOT rank arms by it and do not explain an AUC difference by it.** The one reading that is safe is an extreme: the hard anchor's −0.18 (anti-correlated with phase-1) came with collapsed coverage.
4. **GIT: still nothing committed** — Tal 09-14: *"גיט כרגע לא מעניין אותי נעדכן בסוף היום"*, so commit at END OF DAY, not first thing. The 09-10→09-13 backlog now also includes `modules/dist_loss.py`, `analysis/soft_dist_median_check.py`, `scripts/run_isobbox_dist_QUEUE.sh`, plus `--dist_soft_target_temperature` / `--cyc_return_stride` in `phase2/train_relational_loss.py` and both queue/calibrate scripts.
5. Disk: 316 GB of 500 after the big cleanup; 4 new arms from 09-13 still carry their step checkpoints (~24 GB).

**2026-09-12 (fourteenth pod) — SHIC's `L_dist` WAS BUILT AND RUN (two arms); the w_spatial sweep was CLOSED by Tal; and the gap between our L_dist and SHIC's was pinned down.**

### 1. TAL'S DECISIONS TODAY
- **w_spatial sweep: "לא ראיתי ערך מוסף למה שקיוויתי לראות" — CLOSED.** Stay at w_spatial=1.
- **After the L_dist results: stay on the current version** (anchor λ=3.5e-7 T=0.01 + cycle v2 all-pixel c=1.05e-5 T_cyc=0.05,
  w_spatial=1, plus L_dist as measured below). No further sweep this pod.
- **Do NOT move L_dist to all mask pixels** (reasoning in §6).

### 2. L_dist — WHAT WAS BUILT (uncommitted)
- `modules/dist_loss.py`: `L_dist = (1/n) Σ_u Σ_x p_d(x|u) · G[x̃_u, x] / D`, hard `x̃_u = argmax q_ZS`, over all 3886
  vertices on the 2048 centers. Reuses the existing `geo_table_3d` — **no new table**. Returns `(loss, tail_mass,
  top1_agreement, target_idx)`; `x̃_u` is cached (constant unless `--resample_centers`).
- `phase2/train_relational_loss.py`: `--dist_weight` (γ, default 0 = bit-identical), `--dist_temperature` (T_dist,
  default 1), `--dist_balance` (diagnostic, rides on `--anchor_balance_from`), per-step logging
  `L_dist=… tail>0.2D=… zs_top1=…`. Raises if `--dist_weight>0` without `--geodesic` (the 3D table only loads there).
- `scripts/run_isobbox_anchor_CALIBRATE.sh`: env `DIST_T`. `scripts/run_isobbox_dist_QUEUE.sh <γ> [<γ> ...]`: env
  `ANCHOR_W ANCHOR_T CYC_W CYC_T DIST_T MU REL_W`; matched control = the same anchor+cycle arm without L_dist.
- **`T_dist` IS A SEPARATE FLAG FROM `T_anchor`, default 1, and that is a deliberate DIVERGENCE from SHIC** — see §5.
  Reason: the gradient `p(x)(d − E_p[d])/T` is alive only where `p(x)>0`. At T=0.01 p spans ~75 vertices, so L_dist
  would only re-rank inside the anchor's own blob; at T=1 it spans all 3886, where the far mass actually is.
- **Two properties that differ from the anchor, both in the module docstring:** (1) L_dist's gradient is NOT zero at
  phase-1, so it is a DRIVING force and could be calibrated at step 1 (the anchor's is exactly 0 there); (2) it is
  linear in p, so its unique minimizer is δ at x̃_u — same fixed point as hard L_pseudo, reached metric-aware. The same
  algebra is why the SOFT-label variant stays rejected (→ geodesic median of q).

### 3. CALIBRATION (ladder step 25, anchor λ=3.5e-7, T_anchor=0.01)
| term | loss | ‖∇‖ | weight |
|---|---|---|---|
| relational | 2.7635e-04 | 2.9954e-06 | 1 |
| anchor (soft) | 1.1343e+01 | 8.4473e+00 | λ = 3.5e-7 |
| cycle v2 (T=0.05) | 1.3795e-01 | 5.6280e-02 | c = 1.05e-5 |
| **L_dist (T_dist=1)** | 3.3003e-01 | 2.1155e-02 | **γ = 1.3976e-05 (1/10) · 2.7951e-06 (1/50)** |

**READING THE `tail>0.2D` LOG FIELD — the floor is NOT zero.** Under a *uniform* p the mesh's own geometry gives
**0.687** (measured from `geo_table_3d`: 69% of vertices sit >0.2D from a typical vertex; p10 0.560 / median 0.680 /
p90 0.821). So the range is [0, 0.687], not [0, 1]. Observed: 0.632 at calibration → 0.569 at step 300 (γ=1.40e-5).

### 4. RESULTS (eval v2, n=100, on anchor + strong cycle, w_spatial=1)
| arm | AUC snap/argmax/soft | @3% | cov | argmax cov | anchor_KL@300 | drift@300 |
|---|---|---|---|---|---|---|
| control (no L_dist) | 76.9 / 71.0 / 74.9 | 24 | 38.5% | 11.0% | 5.59 | 0.29 |
| **γ=2.7951e-06 (1/50)** | **78.5 / 73.3 / 76.1** | 26 | 37.9% | 11.1% | 2.89 | 0.44 |
| γ=1.3976e-05 (1/10) | 78.9 / 71.8 / 76.0 | 20 | 36.6% | 11.3% | 3.86 | 0.28 |
| ZS (reference) | 87.9 / 86.2 / 85.7 | 78 | 30.3% | 23.3% | — | 1.00 |

- **Both arms beat the control on all three AUCs**, and the gain sits in the **5–15% tolerance band**, not the tight one
  (@1%/@3% flat or worse; @10% snap 100 vs 95, argmax 95 vs 89). That is the signature of a term that fixes FAR misses
  and not near ones — exactly what L_dist is for.
- **The WEAKER γ won**, the opposite of the mid-run prediction (which was written from L_dist plateauing and was wrong).
  **Confound, same one as the w_spatial sweep:** γ=1/50 also drifted less (0.44 vs 0.28), so part of its lead is just
  sitting closer to ZS. **γ=1/10 is the drift-matched comparison vs the control (0.28 vs 0.29), and there
  anchor_KL falls 5.59 → 3.86 at unchanged drift** — more grip on the anchor without extra rigidity.
- **Feature space is where it shows clearest** (`4_features_sim_heatmap.png`): a neck vertex (`vertex_2885`) becomes
  genuinely dissimilar to the whole body — bright neck, dark body — where the control is low-contrast throughout.
  Same for `vertex_1017`. PCA on the mesh side separates far more strongly too. **Caveat when reading the PCA IMAGE
  panels: photo features are frozen and identical in both rows; they look different only because the shared basis
  rotates with the mesh features. Do not read a change there.**
- Back-projection: by my eye slightly MORE fragmented in the body than the control. Tal did not overrule this.
- Figures: `demo/guitar/runs/isobbox/bsb_isobbox_sdsquare_anchorsoftT0.01_w3.5e-7_cycv2allpixT0.05_c1.05e-5_distT1_g<γ>_T1_seed0_phase2/{comparison_vs_anchor_cycle,comparison_vs_ZS}/`

### 5. OURS vs SHIC's L_dist — THREE REAL DIVERGENCES (Tal asked; SHIC eqs are already quoted verbatim further down this file)
```
SHIC:  L_dist = 1/|U| Σ_u Σ_x  d(x, x~) · p(x|u,I)          γ = 0.002, α = 0.1  (γ/α = 1/50)
ours:  L_dist = 1/n   Σ_u Σ_x  p_d(x|u) · G[x~_u, x] / D    γ = 1.3976e-05 · 2.7951e-06
```
The FORM is identical. What differs:
1. **Two temperatures instead of one shared `p`.** SHIC feeds ONE softmax to both L_pseudo and L_dist. We run `p_a` at
   T=0.01 and `p_d` at T=1. **This is forced by our choice of companion term, not by L_dist**: SHIC's companion is a
   one-hot L_pseudo, which does not care about the target's temperature; ours is a *distribution-matching* anchor, which
   needs a sharp target, hence T_anchor=0.01. Sharing at 0.01 makes L_dist near-redundant with the anchor; sharing at 1
   makes q_ZS ~uniform and breaks the anchor (measured 09-10).
2. **The companion is the soft anchor, not L_pseudo** — the deliberate divergence already argued further down this file.
   Note we are a HYBRID: soft label for the anchor, **hard** x̃_u for L_dist.
3. **U = the 2048 centers, not the foreground pixel set.** (`d/D` vs raw `d` is units only, absorbed by γ.)
- **Our 1/50 arm is exactly SHIC's own γ/α ratio** (0.002/0.1), reached independently by gradient-norm calibration —
  and it is the arm that scored best.

### 6. TWO THINGS ANALYSED AND PARKED, WITH THE REASONING (so nobody re-derives them)
- **Shared softmax (Tal's suggestion).** Blocked in both directions by §5.1. But the suggestion points at a real arm:
  **`--anchor_hard` + T=1 for BOTH + shared p + γ/α=1/50 IS SHIC as written**, and the hard-anchor control has never
  been run. **The "anchor at T=1 did not contribute anything" verdict (09-10) does NOT apply to it** — that was measured
  on the *soft* anchor at T=1, where q_ZS is ~uniform; a ONE-HOT target at T=1 is a different object entirely.
- **L_dist over all 212,549 mask pixels instead of the 2048 centers.** Does NOT add degrees of freedom — gradients reach
  only the 3886 vertex features and the photo features are frozen. What it changes is the **weighting over the mesh**:
  segment-balanced (centers) → pixel-area-weighted (all), so the body dominates and neck/headstock weaken — the very
  regions our back-projection and hub10 problems live in. Cost: `p_d` becomes [212549 × 3886] ≈ 3.3 GB plus the same
  again for the gathered distances, before autograd → **does not fit in this pod's 16 GB GPU without chunking.**
  (Cycle v2 got away with all-pixels because its table is [2048 × 212549] — only ONE axis grew.)

### 7. L_dist formula diagram (Tal's ask): artifact https://claude.ai/code/artifact/d37bb595-9463-47d5-9f4c-428cf0c20711
Blocks + arrows + formulas, **L_dist only** — Tal rejected two earlier drafts as too wordy and did not want L_pseudo or
the comparison material in it. Final shape: two branches (frozen teacher → `x̃_u`; live encoder → `p_d`) merging into ONE
loss box carrying both sums, then `loss += γ·L_dist`; below it, Terms / Gradient / Flags as three short slabs. HTML
source is in the pod's /tmp scratchpad and is lost at close — edit the published page by URL.

### NEXT POD, in order (written 2026-09-12 at pod close) — items 1 and 3 were DONE on 09-13, see that entry
**Nothing is running.** Both L_dist arms trained, analyzed and compared; queue exited 0.
1. **THE arm to run: full SHIC — `--anchor_hard --anchor_temperature 1 --dist_temperature 1`, shared-p structure,
   γ at SHIC's 1/50 of the weighted anchor.** See §6. This also finally runs the hard-anchor control that has been
   open since 09-10.
2. Lower-priority L_dist sweep if wanted: γ further DOWN (1/100, 1/200) to find the turnover, and `T_dist ≈ 0.1` — the
   untested middle, which changes the term's leverage rather than its size.
3. Still open from 09-10/09-11: needs Tal's OK to delete the partial `..._cycv2T1_c1.19e-5_...` dir and the
   centers-return T=0.05 arm — after which the demo dirs can drop `allpix` without a name collision.
4. **GIT: nothing committed this pod either.** New today: `modules/dist_loss.py`,
   `scripts/run_isobbox_dist_QUEUE.sh`. Changed: `phase2/train_relational_loss.py` (dist flags + loss + logging),
   `scripts/run_isobbox_anchor_CALIBRATE.sh` (`DIST_T`), on top of the whole 09-10/09-11 backlog.
5. Disk: 2 new phase-2 arms today with step checkpoints (~6 GB each, ~12 GB).
6. **OOM warning:** the first launch was OOM-killed (exit 137) because two trainings were alive at once. Each run holds
   the [2048 × 212549] cycle table; **run the queues one at a time.**

**2026-09-11 (thirteenth pod).**
- **TEMPERATURE NAMES (Tal, to stop confusing them) — use these in notes and replies:**
  | name | flag | what it tempers | current |
  |---|---|---|---|
  | `T_spatial` | `--temperature` | spatial-RKD pixel->vertex soft map (k=10 nearest); the `_T1_` in run names | 1 |
  **RENAMED same day (Tal): `T_rkd` -> `T_spatial`, `w_rkd` -> `w_spatial` (`--relational_weight`)** — "rkd" is ambiguous
  with the feature-RKD terms (`--feat_*_weight`, currently off). Dir tag `_rkdw<w>` kept for the two runs already launched.
  Why d(u,v) in L_cyc is divided by the diameter (Tal asked): mathematically redundant — d sits linearly outside the
  softmax, so d/1175.75 is exactly c/1175.75; c is calibrated anyway. Kept only for units (loss = fraction of diameter,
  same convention as L_spatial and eval) and so c transfers across masks of different pixel size.
  | `T_anchor` | `--anchor_temperature` | q_ZS and p over all 3886 vertices; `anchorsoftT0.01` | 0.01 |
  | `T_cyc` | `--cyc_temperature` | both legs of cycle v2; `cycv2allpixT0.05` | 1 (done), 0.05 |
  | `T_read` | analysis, not training | soft-snap / back-projection / eval read | 1 |
- **Tal: the BALANCED anchor (soft, T_anchor=0.01, lambda=3.5e-7) is the anchor for further experiments.**
- The T_cyc=0.05 queue died with the pod at step 275 of c=1.05e-7; relaunched (weak arm + `build_cycv2_sweep_figures.sh 0.05 1 1.05e-5 1.05e-6 1.05e-7`, chained).
- **RESULT — cycle v2 all-pixel at T_cyc=0.05 on the balanced anchor: the loss is ALIVE (0.138 -> 0.086-0.117, unlike
  T_cyc=1 at 99% of uniform) but eval does NOT beat the control.** Figures `demo/guitar/runs/isobbox/comparison_cycv2allpix_T0.05_sweep/` (1-5).
  | arm | AUC snap/argmax/soft | @3% | coverage | argmax cov | hub10 | drift@300 |
  |---|---|---|---|---|---|---|
  | strong c=1.05e-5 | 76.9 / 71.0 / 74.9 | 24 | 38.5% | 11.0% | 20.3% | 0.29 |
  | balanced c=1.05e-6 (1/50) | 79.8 / 74.7 / 77.1 | 27 | 36.6% | 9.5% | 19.1% | 0.58 |
  | weak c=1.05e-7 | 78.9 / 73.5 / 75.6 | 22 | 35.9% | 8.3% | 20.7% | — |
  | anchor only (control) | 79.1 / 72.0 / 75.9 | 26 | 34.8% | 9.3% | 22.0% | 0.76 |
  Balanced is +0.7/+2.7/+1.2 over control (argmax at the seed-floor edge); strong drifts to 0.29 and anchor_KL 2.8 -> 5.6.
  **TAL'S VISUAL VERDICT: STRONG (c=1.05e-5) LOOKS BEST and "improves things I was looking for"** — the opposite of
  the AUC ranking (strong is last on numbers). Following it: **stronger arm c=1.05e-4 launched** (log
  `/workspace/logs/cycv2_allpix_T0.05_stronger_queue.log`), figures chained into
  `comparison_cycv2allpix_T0.05_sweep_stronger/` (rows: ZS, 1.05e-4, 1.05e-5, 1.05e-6, control).
  `build_cycv2_sweep_figures.sh` gained `OUT_SUFFIX` + `LABEL_S/B/W` env so a second set does not overwrite the first.
- **STRONGER c=1.05e-4 RESULT:** 78.7 / 71.0 / 76.2, @3% 25, coverage 37.6%, argmax cov 12.7%, **hub10 14.7%**
  (lowest of any anchor arm; control 22.0%), L_cyc@300 0.048 (~56 px), drift 0.22, anchor_KL 6.6. On numbers it
  sits between strong and control; hubness drops clearly. Figures `comparison_cycv2allpix_T0.05_sweep_stronger/`.
  **Awaiting Tal's visual verdict.**
- **FIGURE LABELS (Tal): every panel/legend label must show what differs between rows; never write "allpix"** (all-pixel
  return is the only cycle variant in use). Bug fixed: `build_cycv2_sweep_figures.sh` stripped the parenthetical from eval
  legend labels, so the w_spatial rows were identical. All four cycle sets rebuilt (T_cyc=1, 0.05, _stronger, _rkdw).
  Dir names still contain `allpix`/`rkdw` — renaming would collide with the centers-return arm (item 5 of 09-10).
- **Tal: stronger is LESS good visually — STAY ON STRONG (c=1.05e-5).**
- **WEAKENING SPATIAL RKD on strong (Tal's ask), two arms: `--relational_weight` 0.3 and 0.1.** With anchor+cycle present
  this flag is NO LONGER a no-op (the 2026-09-09 no-op note holds only when L_rel is the sole term): it scales L_rel
  alone, i.e. Adam-equivalent to ANCHOR_W and c x 1/REL_W. At calibration lambda*grad_anchor = grad_rkd and strong cycle =
  grad_anchor/5, so at 0.1 RKD is already below the cycle. `run_isobbox_cycv2_QUEUE.sh` gained env `REL_W` (dir tag
  `_rkdw<w>`, untagged at 1); the figure builder gained `RW_S/RW_B/RW_W`. Log `/workspace/logs/cycv2_strong_rkdw_queue.log`,
  figures -> `comparison_cycv2allpix_T0.05_sweep_rkdw/` (rows: ZS, rkd 1, 0.3, 0.1, anchor-only control).
  **RESULT (awaiting Tal's visual verdict):**
  | w_spatial | AUC snap/argmax/soft | @3% | coverage | argmax cov | hub10 | drift@300 | anchor_KL@300 | L_cyc@300 |
  |---|---|---|---|---|---|---|---|---|
  | 1 (strong) | 76.9 / 71.0 / 74.9 | 24 | 38.5% | 11.0% | 20.3% | 0.29 | 5.59 | 0.086 |
  | 0.3 | 78.8 / 65.3 / 75.5 | 29 | 34.5% | 8.4% | 17.0% | 0.49 | 1.42 | 0.070 |
  | 0.1 | **81.0** / **64.6** / 76.4 | **36** | 31.3% | 7.3% | 21.5% | 0.43 | 0.86 | 0.067 |
  Weakening spatial moves snap/@3% toward ZS (81.0 = best mu=1 phase-2 snap on record) while feature ARGMAX COLLAPSES
  (71 -> 64.6) — the same snap-up/argmax-down split as the mu=1 anchor sweep. The anchor holds far better (KL 5.6 -> 0.9).
  By my eye the back-projection gets more ragged/speckled toward ZS as w_spatial drops (neck patches at 0.1).
- Why `e_x` is unit-norm (Tal asked): `EncoderL2Norm` ends in `L2Normalize` since 2026-08-19/20 (norm-inflation fix),
  photo features are L2-normalized on load, so every similarity is a cosine; `F.normalize` inside cycle v2 is a no-op.
- Cycle-loss v2 formula diagram (Tal's ask): artifact https://claude.ai/code/artifact/caffc5d1-6223-40f1-8a67-1d4623bdb401

### NEXT POD, in order (written 2026-09-11 at pod close) — items 1 and 2 were DONE on 09-12, see that entry
**Nothing is running.** All arms trained + analyzed; all four cycle figure sets rebuilt with fixed labels.
1. **Tal's visual verdict on the w_spatial sweep is outstanding** (`comparison_cycv2allpix_T0.05_sweep_rkdw/`): snap/@3% rise
   toward ZS as w_spatial drops, feature argmax falls. Current pick is strong cycle (c=1.05e-5) at w_spatial=1.
2. **Candidate next arm (discussed, not run): SHIC's `L_dist = sum_x p(x|u) d_3D(x, x~)` with a HARD x~ = argmax q_ZS**, on
   top of anchor + strong cycle; gamma calibrated by grad norms. L_pseudo(CE) = "be exactly at x~", L_dist = "if wrong, be
   wrong nearby" — our anchor is only the first. The SOFT-label form stays rejected (linear in p -> geodesic median of q).
3. Still open from 09-10: hard-anchor control never run; needs Tal's OK to delete the partial `..._cycv2T1_c1.19e-5_...`
   dir and the centers-return T=0.05 arm — after which the demo dirs can drop `allpix` without a name collision.
4. **GIT: nothing committed this pod either.** Changed today: `scripts/run_isobbox_cycv2_QUEUE.sh` (REL_W, labels),
   `scripts/build_cycv2_sweep_figures.sh` (OUT_SUFFIX, LABEL_*, RW_*, TITLE_NOTE, full labels),
   `analysis/compare_eval_runs.py` (sources block placed below the tables' real bottom), plus the whole 09-10 backlog.
5. Disk: 4 new phase-2 arms today with step checkpoints (~6 GB each, ~24 GB) on top of 371/500 GB.
6. **Artifact store in this session:** the cycle-loss diagram
   https://claude.ai/code/artifact/caffc5d1-6223-40f1-8a67-1d4623bdb401 (HTML source was in the pod's /tmp scratchpad and
   is lost at close; edit the published page by URL).

**2026-09-10 (twelfth pod) — CONDENSED 2026-09-14 (full text in `archive/pre-consolidation-2026-09-10/` and `.../2026-09-14/`) — THE ZS ANCHOR AND CYCLE LOSS v2 WERE BUILT. Both are in the live recipe; the sweeps below are closed.**

### NAMING (still in force)
`demo/guitar/runs/isobbox/`: `_fuse16` and `_truediag2d` are NOT in demo dir names (defaults are not named); encoder dirs and eval `.pth` tags DO keep them, because `run_config.json` stores absolute paths. (`allpix` was dropped everywhere on 09-14.)

### THE ANCHOR — why it is built the way it is
- **Precondition, measured**: ZS errors are NOT symmetry flips (0/10 wrong points near the L/R or F/B mirror) but ARE regionally coherent (8/10 at the neck-body junction). So a per-pixel pull toward ZS is meaningful.
- **Prior art, code read not recalled**: DensePose-CSE `embed.py` = CE over ALL vertices vs a GT vertex, `soft_embed.py` = CE against a geodesic-Gaussian target. SHIC = hard argmax `L_pseudo` + a separate `L_dist`. Ours = CE against the SOFT q_ZS of frozen phase-1.
- **The key property: the soft anchor's gradient is exactly 0 at phase-1 (p == q)** — a restoring force that grows with drift, so it costs nothing when phase-2 is behaving. (L_dist, added 09-12, does NOT have this property: it is a driving force.)
- **`q_ZS` vs T (V=3886)**: at T=1 the target is effectively uniform (3868 effective vertices, 65% of its mass >20% of D from the GT); at T=0.01 it spans ~75 vertices with 49% of the mass inside 3% of D. **That is why T_anchor=0.01 is the live setting.**

### ANCHOR SWEEP RESULTS (eval v2, n=100, read T=1) — the arm in the recipe is `mu=1, T=0.01, lambda 3.5e-7`
| arm | AUC snap/argmax/soft | @3% | cov | argmax cov | hub10 | drift@300 |
|---|---|---|---|---|---|---|
| ZS | 87.9 / 86.2 / 85.7 | 78 | 30.3% | 23.3% | 9.8% | 1.00 |
| baseline (mu=1, no anchor) | 77.0 / 76.8 / 75.1 | 21 | 40.1% | 30.9% | 14.2% | ~0.43 |
| T=0.01 lambda 3.5e-6 | 80.6 / 62.4 / 75.7 | 35 | 30.1% | 5.8% | 21.3% | 0.963 |
| **T=0.01 lambda 3.5e-7 (ADOPTED)** | 79.1 / 72.0 / 75.9 | 26 | 34.8% | 9.3% | 22.0% | 0.762 |
| T=0.01 lambda 3.5e-8 | 76.7 / 68.9 / 73.9 | 22 | 38.7% | 24.2% | 23.1% | 0.250 |
| T=1 lambda 1.1e-3 | 78.4 / 76.8 / 76.2 | 22 | 38.8% | 19.3% | 18.4% | 0.492 |
| mu=0.75 + T=0.01 lambda 3.5e-7 | 74.1 / 73.1 / 72.6 | **70** | 26.6% | 22.5% | 14.8% | 0.873 |
- **The snap-up / argmax-down split** (stronger anchor raises geo snap and @3%, sinks feature argmax) is the signature that recurs in every later sweep, including w_spatial on 09-11.
- **Hubness is NOT caused by a sharp target** — the near-uniform T=1 arm has the worst hub10 (34.2%).
- **mu=0.75 + anchor reached @3% = 70%, the best on record**, but Tal did not adopt mu<1 (documented 09-09, not adopted). **Anchor at T=1: "did not contribute anything"** (Tal) — and note this verdict is about the SOFT target at T=1, not the hard one, which was only run on 09-13.
- **mu_3d_scale < 1 COMPRESSES the neck** (measured here; it corrects a wrong line in the 09-08 entry that said the opposite). Sweep without anchor: 0.75 -> 72.1/72.4/71.1, 0.80 -> 74.0, 0.85 -> 75.1, 1 -> 77.0, with @3% going the other way (54/54/50/21).

### CYCLE LOSS v2 — also built here, also live
- **Why the OLD cycle loss could not work**: no temperature on either leg, so at T=1 the round trip is ~99% of uniform and the loss is inert. v2 = all vertices + a temperature on BOTH legs (CSE) + `--cyc_return_all_pixels` (SHIC as written, return over all 212,549 mask pixels, no new table).
- **All-pixel cycle v2 at T_cyc=1 on the anchor: NO EFFECT**, exactly as the temperature measurement predicted. T_cyc=0.05 is the live setting (09-11).

### ONE MORE FACT WORTH KEEPING
**After 25 phase-2 steps NOT ONE pixel keeps its ZS argmax** (0/2048 centers, 0/100 eval points). Phase-2 does not refine phase-1's answer — it replaces it.

## GEODESIC SMOOTHING vs L_dist — why they are NOT substitutes (durable, written 2026-09-14 at Tal's request)

Tal's question: *does CSE have only `L_pseudo`, because the Gaussian gives them what `L_dist` gives SHIC?*
**Half right, and the half that is wrong matters.**

CSE has **no separate distance term.** It offers two forms of the SAME loss and the config picks one:
`embed.py` = CE against a one-hot GT vertex; `soft_embed.py` = CE against a **Gaussian over geodesic
distance** centred on that GT vertex (**sigma 0.01** in their released configs). So geometry enters through
the SHAPE OF THE TARGET, not through an added term.

**But a sigma-0.01 Gaussian is LOCAL.** It puts a little mass on the true vertex's immediate neighbours, so a
near miss is no longer punished as a total error. About mass sitting on the far side of the object it says
nothing at all: out there the Gaussian target is already zero, exactly like the one-hot. **`L_dist` is the
opposite: linear in distance across all 3886 vertices, so every unit of far mass is penalised in proportion
to how far it sits.** In one line each:
- **CSE:** "a near miss is fine." Local repair of the target.
- **SHIC:** "if you are wrong, be wrong nearby." Global, and it needs its own term to say it.
- **OURS: we have BOTH, which is very likely why L_dist bought so little.** Our soft anchor target at
  T_anchor=0.01 spans ~75 vertices with 49% of its mass inside 3% of D — that IS a geodesic-smoothed target,
  reached by temperature instead of by an explicit Gaussian. L_dist was then added on top of a target that
  had already done the local half of the job (measured: 09-12 §4, 09-14 §2/§2b — every L_dist knob moves the
  term's own diagnostics and none of it reaches eval).

### NEXT POD, in order (written 2026-09-10 at pod close)
**RUNNING overnight (Tal approved, 2026-09-10 evening): cycle v2 all-pixel at T=0.05** — calibration `cycv2_allpix_calibrate_T0.05.log`:
loss 0.138, **cyc_weight at 1/50 of anchor = 1.05e-6**. Detached: `run_isobbox_cycv2_QUEUE.sh 1.05e-6 1.05e-5 1.05e-7` then
`build_cycv2_sweep_figures.sh 0.05 1 1.05e-5 1.05e-6 1.05e-7` (chained). Logs `/workspace/logs/cycv2_allpix_T0.05_{queue,figures}.log`,
figures -> `demo/guitar/runs/isobbox/comparison_cycv2allpix_T0.05_sweep/`. **Item 1 below is therefore already launched — next pod: read the table + SHOW the 5 figures.**
1. **Cycle v2 all-pixel at a REAL temperature, T=0.05** (Tal's order was T=1 first, then T; T=1 had no effect).
   ASK TAL FIRST, then: calibrate `CYC_ALLPIX=1 CYC_T=0.05 ANCHOR_W=3.5e-7 MODES=soft scripts/run_isobbox_anchor_CALIBRATE.sh 25`
   (prints the 1/50 weight), launch DETACHED `CYC_ALLPIX=1 CYC_T=0.05 ANCHOR_W=3.5e-7 ANCHOR_T=0.01 MU=1 setsid nohup
   scripts/run_isobbox_cycv2_QUEUE.sh <c> <10c> <c/10> >> /workspace/logs/cycv2_allpix_T0.05_queue.log 2>&1 < /dev/null &`
   (~1 h), then `scripts/build_cycv2_sweep_figures.sh 0.05 1 <10c> <c> <c/10>` and SHOW the 5 figures.
2. (Merged into 1.)
3. **Tal's visual verdict is outstanding** on the three anchor figure sets and the cycle T=1 set
   (`comparison_anchor_soft_sweep{,_mu0.75,_T1}/`, `comparison_cycv2allpix_T1_sweep/`).
4. Hard-anchor control never run. Unexplained: hubness vs anchor strength; non-monotone drift.
5. **Needs Tal's OK:** partial dir `experiments/guitar/encoder_isobbox_sdsquare_fuse16_truediag2d_anchorsoftT0.01_w3.5e-7_cycv2T1_c1.19e-5_T1_seed0_phase2`
   (stopped at step 75, no pred_f) — delete; centers-return T=0.05 c=1.05e-6 arm (trained, analysis incomplete) — finish or delete.
6. **GIT: nothing committed this pod.** New: `modules/anchor_loss.py`, `modules/cycle_consistency_loss_v2.py`,
   `analysis/zs_error_structure_check.py`, `scripts/run_isobbox_anchor_{QUEUE,CALIBRATE}.sh`, `scripts/run_isobbox_cycv2_QUEUE.sh`, `scripts/build_cycv2_sweep_figures.sh`;
   modified `phase2/train_relational_loss.py`, `scripts/analyze_isobbox_arm.sh`, 29 scripts (rename refs); plus the earlier backlog.
7. Disk: `/workspace` at 371 GB of 500 (~6 GB per phase-2 arm with its step checkpoints).

**2026-09-09 (eleventh pod) — CONDENSED 2026-09-14 (full text in the archive) — TAL'S DECISIONS, AND THREE DEAD KNOBS FOUND IN THE LOSS.**
- **Tal's decisions**: `mu_3d_scale` 0.75/0.80/0.85 documented, NOT adopted. **`input resolution 840`: REJECTED, do not run it** (*"אני לא רוצה ללכת לכיוון הזה"*).
- **Tal's framing, still the frame for everything since**: ZS's feature space looks right and phase-2 damages it, so the question is how to keep phase-2's spatial coherence without losing phase-1's features. (The anchor, the cycle and L_dist are all answers to this.)
- **THREE DEAD KNOBS, found by reading the code**:
  - **`--relational_weight` was a NO-OP** when L_rel was the ONLY term — scaling the sole loss just rescales Adam's step. **This stopped being true on 09-11**, when the anchor and cycle joined it: there it scales L_rel alone and is a real knob (`w_spatial`).
  - **`--huber_delta 1.0` had NEVER done anything — the loss has been plain MSE the whole time.**
  - **`--resample_centers` requires a `--center_mode grid` table that no longer exists**, so it silently did nothing. It is the overfit knob: the 2048 centers are sampled once and reused for all 300 steps.
  - Also present and never used: **`--stop_at_drift`**. New diagnostic added: `--dump_residuals`.
- **THE RESULT OF THE WHOLE WEAKENING EFFORT: the loss was not too strong.** Every weakening knob is flat. Under Adam, `lr/10` for 300 steps ≈ `lr` for 300 steps, which is why "fewer steps" was the weakest of the three suspects.
- **THE STEP LADDER WAS THE CRUX**: ZS has the best features, and phase-2 destroys them inside the first ~25 steps. **ZS beats phase-2 at EVERY tolerance, not just on average** — the "phase-2 is better in the tail" escape route is closed.
- **Why feature-RKD failed: neither normalization nor symmetry — it is circularity** (the student's own features supply the target). Full write-up in the durable FEATURE-SPACE RKD section.

**2026-09-09 (eleventh pod, SECOND THREAD — the cycle-loss / anchor design question) — CONDENSED 2026-09-14 (full text in the archive).**
- **Tal's objection, and it is the correct one**: a pure cycle loss has a known degenerate solution — any self-consistent mapping satisfies it, including a wrong one.
- **What stops it in SHIC: three ABSOLUTE signals we do not have** (a hard pseudo-label pinning real vertices, `L_dist` penalising far mass, and supervision from their frozen teacher). **Verified against our flag list: phase-2 had NO absolute term at all** — which is exactly the gap the ZS anchor was built to fill the next day.
- **SHIC'S ACTUAL EQUATIONS** (arXiv 2407.18907, fetched from the paper's HTML, not from memory; their repo is inference-only and has no loss code). **This is the only verbatim copy left in this file — everything else quotes it:**
  ```
  x~(u,I)    = argmax_{x_k in V} Sigma_I(u, x_k)            <- the label: HARD argmax
  p(x_k|u,I) = softmax(<e_I(u), e(x_k)>)                    <- the prediction: SOFT distribution
  L_pseudo   = -1/|U| sum_u log p(x~(u,I)|u,I)              alpha = 0.1
  L_dist     =  1/|U| sum_u sum_x d(x, x~) p(x|u,I)         gamma = 0.002
  L_cyc      =  sum_u sum_v ||u-v|| p(v|u)                  beta  = 0.002
  L_eq       =  1/|U| sum_u sum_x |p(x|u,I) - p(x_F|u_F,I_F)|   delta = 0.001
  L = 1/|D| sum_I (alpha*L_pseudo + beta*L_cyc + gamma*L_dist + delta*L_eq) + zeta*sum_i L_syn
  zeta = 0.1
  ```
- **"HARD OR SOFT" IS TWO SEPARATE AXES** (Tal asked): the student side is ALWAYS soft (a softmax over all vertices, never an argmax); the LABEL is hard (argmax of the frozen similarity); the PENALTY is soft (`L_dist` = expected geodesic distance to the same `x~`). **SHIC softened the penalty, not the label.** `L_pseudo` alone knows nothing about the mesh — wrong by 1 mm and wrong by half the guitar cost the same.
- **Why we can use a SOFT label where SHIC could not**: their teacher gives them one argmax per pixel; ours gives a full distribution, so we can match the distribution instead of its peak.
- **A geometry-aware variant was proposed and rejected in the same session** — recorded so it is not re-derived.

**2026-09-08 (tenth pod) — CONDENSED 2026-09-14 (full text in the archive) — THERE IS NOW EXACTLY ONE BASELINE: `sdsquare_fuse16`, T=1, seed 0, carrying `--geo_diag_2d 1175.75`.**
- **`fuse32` was deleted, minus its record** (weights + its 36 GB feature tensor). The primary baseline folder holds only `encoder_checkpoint.pth` + `pred_f.pth` — no step checkpoints.
- **Phase marginalization (`--dino_phases 4`) was re-run on the new recipe and is flat again** — that direction is closed on this recipe.
- **The step-ladder probe ran and the answer is a JUMP, not a slide**: the damage happens in the first ~25 steps, which is what turned attention to anchoring phase-1 rather than to weakening phase-2. The step ladder at `..._T1_seed0_phase2_stepladder/` is what every later calibration reads (step 25).
- **A label-free field-quality tool was built and its first answer was negative** (`analysis/correspondence_field_quality.py`).
- **WARNING THAT STILL APPLIES: the older isobbox comparison figures are 4-WAY CONFOUNDED** (mesh + bbox frame + framing + fuse all changed together). Only same-mesh, same-recipe rows are comparable.
- **SHIC-bear**: the whole comparison sits in one table in the archived text; nothing has moved on it since.
- Disk: 361 GB -> 188 GB, 173 GB freed (Tal approved the list).

**2026-09-08 — THE PRE-`sdsquare_fuse16` BASELINE (stride 14 + `squash`, T=0.01) — CONDENSED 2026-09-14 (full text in the archive).** This block described the recipe that the tenth-pod entry above REPLACED; it is kept only as lineage. Do not take a path or a flag from it.
- Key facts that outlived it: **read temperature is part of a recipe** (that baseline was read at 0.01, today everything is read at T=1 and says so); **the seed draw is worth ~1.6-2.4 AUC**; **stride 7 + `gridalign` was promoted on 08-28 and lost when stride was finally isolated on 09-01**; `gridalign` is not optional at stride 7.
- The two feature-path bugs it revolved around (`gridalign` = bug A, `sd_square` = bug B) have their own durable section immediately below.

## THE TWO FEATURE-PATH BUGS — full explanation (durable reference, written 2026-08-28 at Tal's request)

Both were found 2026-08-27, both are geometric misalignments in how 2D features get placed onto the
image, both were measured rather than argued. This section is the "come back to it later and actually
understand it" writeup; the status entry for 2026-08-27 below has the run-by-run narrative.

### Shared background: how a feature grid becomes a per-pixel feature map
DINOv2 ViT-B/14 does not produce one feature per pixel. Its first layer is a convolution with a
**14x14 kernel** applied at **stride 14**, so a 224x224 input becomes a **16x16 grid of tokens**, each
token summarizing one disjoint 14x14 patch. To use these features per-pixel we have to (a) decide
*where in the image each token lives*, and (b) interpolate between them. Bug A is a mistake in (a).
Separately, DINO and SD each produce their own grid from their own preprocessing of the image, and
`fuse_dino_sd` concatenates the two channel-wise, which is only meaningful if the two grids cover the
**same region of the image**. Bug B is a violation of that.

### BUG A — the patch-grid alignment bug (`gridalign`)
**What the code did.** `modules/dino.py::postprocess_features` upscaled the n x n token grid straight
to the 224x224 input frame with `F.interpolate(..., align_corners=False)`. That function spreads n
cells evenly across the output, i.e. it assumes **token i is centred at `(i + 0.5) * 224 / n`**.

**What is actually true.** Token i is the output of a 14x14 kernel applied at stride s, so it sees
input pixels `[i*s, i*s + 14)` and its true centre is **`14/2 + i*s = 7 + i*s`**.

**Why this was never a problem in production.** At the production stride s = 14 we get n = 16, and:
- assumed centre: `(i + 0.5) * 224/16 = 14i + 7`
- true centre: `7 + 14i`

They are **identical**. The bug is invisible for as long as stride == patch size, which was every run
in this project until the stride trick.

**Why it breaks at stride 7.** Now n = 31, and:
- assumed centre: `(i + 0.5) * 224/31 = 7.23i + 3.61`
- true centre: `7 + 7i`

At i = 0 that is 3.61 vs 7.0; at i = 30 it is 220.4 vs 217.0. The error is zero in the middle and
grows with opposite signs toward the two edges — i.e. **the whole feature field is STRETCHED about the
image centre**. Every feature is placed slightly outward of where it belongs, more so near the edges.

**How big.** Impulse test (put a spike in one token, see which pixel it lands on),
`demo/guitar/features_analyze/problem_a_alignment.png`:
| | stride 14 | stride 7 | stride 7, gridalign ON |
|---|---|---|---|
| photo (upscaled to 1080x810) | 0.71 px | **22.20 px** | 2.71 px |
| render targets (upscaled to 64x64) | 0.71 px | **1.99 px** | 0.51 px |
The residual after the fix is the SAME at stride 14 and stride 7 — a uniform half-pixel offset, not a
stretch. That is the signature of a correct fix: the *stretch* is gone, only a constant sub-pixel
convention remains.

**The fix** (`postprocess_features(..., fix_grid_alignment=True, patch_stride=s)`), three steps:
1. Resize the grid to **exactly the extent the token centres span** — from the first centre (7) to the
   last centre (`7 + (n-1)*s`), which is `(n-1)*s + 1` output samples — using `align_corners=True`, so
   the first and last output samples land exactly on the first and last token centres.
2. **Replicate-pad the 7 px margin** on each side. Those margins lie outside the outermost token
   centres, so there is genuinely no information there; repeating the edge value is the honest choice.
3. Everything downstream (crop away the letterbox padding, resize to the original image size) is
   unchanged.
This is correct for **any** stride, and reduces to the old behaviour at s = 14.

**Left OFF by default** so every pre-existing run stays bit-identical — it must be passed explicitly.

**Why it matters, empirically.** Without it, stride 7 is WORSE than the stride-14 baseline on
`feature argmax` (5.7% / AUC 71.7 vs 5.3% / 74.5): the misplacement eats the entire benefit of the
denser grid, and the stride trick would have looked like a failure. With it, stride 7 is the best run
on record on all three metrics. **Note that ZS did not reveal this** — the two branches were a tie at
ZS (soft-snap 1012 vs 995) and clearly different only after phase-2.

### BUG B — SD and DINO were fed different image frames (`sd_square`)
**What the code did.** DINO gets `encoder.preprocess_image`: resize the **longest** side to 224
(preserving aspect ratio), then **zero-pad** to a 224x224 square — a letterbox. SD was fed
`F.interpolate(image, (512, 512))` — the raw image **squashed** to a square, aspect ratio destroyed.

**Why that is wrong.** `fuse_dino_sd` L2-normalizes each side, resizes SD's grid onto DINO's grid, and
concatenates. That is only meaningful if grid cell (i, j) refers to the same place in both. With one
letterboxed and one squashed, it does not.

**How big.** On the 1080x810 photo the object's centroid sat **2.45 of 16 grid columns apart, ~165 px
of the 810 px width**. Because a squash is a linear rescale, the error is a **horizontal stretch**:
near zero at the left edge, worst at the right. Diagnosis figure:
`demo/guitar/features_analyze/dino_sd_poc/dino_vs_sd_overlay_before_fuse.png`.

**Why renders were never affected.** Renders are square, so resize-longest-side + zero-pad and
squash-to-square are the same operation. Verified numerically as bit-identical (0.000e+00) on real
render files — which is why **phase-1 was never retrained for this fix and every render cache stayed
valid**. Only the photo features had to be re-extracted.

**The fix.** `modules/dino_sd_fusion.py::sd_square()` — aspect-preserving resize + zero-pad to
512x512, the same framing DINO gets. `fuse_dino_sd` needed no change. All 6 SD call sites switched.
Result: 165 px -> 1 px (`demo/guitar/features_analyze/dino_sd_aligned/sd_frame_fix_before_after.png`).
Beyond the placement error, this also removes the aspect **distortion** inside SD's own forward pass —
SD no longer sees a stretched guitar.

**Present since** SD was introduced (`309f726`, 2026-08-22). **Tal promoted it on correctness**, not on
a visual win: "visually I see almost no difference... in any case this is the right thing to do."

### Still open in this area
- ~~**SD's noise is unseeded.**~~ **STALE — this was FIXED on 2026-08-28 and the bullet was left
  behind; corrected 2026-09-06 after reading the code.** `modules/dino_sd_fusion.py` seeds BOTH
  sources (the VAE `latent_dist.sample(generator=g)` AND the `randn` diffusion noise) from a
  generator seeded `noise_seed + noise_index`, i.e. per IMAGE INDEX, so a resumed precompute that
  skips cached views draws the same noise as a fresh one. Seeding only the diffusion noise was tried
  first and was NOT enough (still drifted 3.1e-01). Passing `noise_seed=None` restores the old
  unseeded behaviour. Historical A/Bs run before 2026-08-28 are still confounded by this.
- **SUPERSEDED IN PART, 2026-09-06: the visible "block pattern" is NOT this resolution limit.** It
  is a POSITIONAL artifact of DINOv2 locked to the patch grid, invisible in the features and visible
  in SIMILARITY (16.5% swing inside one cell). See the 2026-09-06 entry. The resolution limit below
  is still real and still severe, but it is a different thing.
- **The resolution limit itself is not a bug, but it is severe.** Full size trace of the photo:
  1080x810 -> `ResizeLongestSide(224)` -> 224x168 -> pad -> 224x224 -> 14 px patches -> 16x16 grid,
  only 16x12 valid -> SD's own 32x32 map resized DOWN onto it -> bilinear upsample back to 1080x810.
  At stride 14 one cell covers ~67.5 x 67.5 px and the whole guitar is 192 feature vectors. Stride 7
  improves the sampling to ~34.8 px per cell; raising the input resolution (SD-DINO runs DINOv2 at
  840 px -> a 60x60 grid) is the other lever -- **MEASURED 2026-09-06, see that entry section 4:
  840 raises adjacent-token cosine 0.570 -> 0.739 and cuts the lattice 16.5% -> 11.6%, but at a
  MATCHED photo distance the cosine does NOT improve, i.e. the field is not getting smoother.** Note the two are different mechanisms and
  compose: higher resolution shrinks sampling AND support together (more, smaller, still-disjoint
  cells), lower stride keeps the 14 px support and only samples it more densely (neighbouring cells
  share input, so the field varies smoothly).

---

## Status as of 2026-09-08 (ninth pod) — CONDENSED 2026-09-14 (full text in the archive) — **the fuse 2x2 is CLOSED: `sdsquare_fuse16` wins, and phase-2 CONVERGES every arm to ~4.7% mean error no matter how good its input was.**
Six arms, one code path, read T=1, eval v2, n=100 (AUC snap/argmax/soft, mean err, soft-snap coverage):
| arm | AUC | mean err | cov |
|---|---|---|---|
| **ZS `sdsquare_fuse16`** | **87.9 / 86.2 / 85.7** | **2.7%** | 30.3% |
| ZS `sdsquare_fuse32` | 83.6 / 84.2 / 81.4 | 3.2% | 36.0% |
| ZS `sdsquash_fuse16` | 68.8 / 68.8 / 68.0 | 6.3% | 22.1% |
| P2 `sdsquare_fuse32` T=1 | 76.4 / 77.2 / 74.4 | 4.6% | 41.6% |
| P2 `sdsquare_fuse16` T=1 | 76.3 / 76.7 / 75.0 | 4.7% | 40.0% |
| P2 `sdsquash_fuse16` T=1 | 77.6 / 76.4 / 74.8 | 4.7% | 38.0% |
- **`fuse32` loses** (-4.3 snap/soft, outside the 1.6-2.4 seed floor) — the 2x2 is closed, `sdsquare_fuse16` is the configuration.
- **PHASE-2 CONVERGES EVERYTHING TO ~4.7%**: it rescues the broken arm (6.3% -> 4.7%) and damages both good ones (2.7% -> 4.7%), across three arms and two independently trained phase-1 encoders. **Coverage moves OPPOSITE to accuracy every time** (30.3->40.0, 36.0->41.6, 22.1->38.0). This is still the central unexplained result of the project.
- **NAMING IN USE SINCE THIS POD: `<sd_frame>_<fuse grid>`** — `sdsquare_fuse16` (the recipe), `sdsquash_fuse16` (old baseline), `sdsquare_fuse32`, `sdnopad_fuse32` (was "arm B", confounded by a different phase-1 — do not quote it), `sdsquarerep_fuse16`. Arm A/A'/B are gone. `--fuse_mode common_grid` refuses `--sd_frame squash` by design.
- **`scripts/lib_isobbox_common.sh` dates from here**: one place for mesh/mask/checker/eval-v2 paths, which is why every later queue script sources it.

## Status as of 2026-09-07 (eighth pod, SECOND THREAD) — CONDENSED 2026-09-14 (full text in the archive) — **`squash` measured properly for the first time, and ZS with matched features beats every phase-2 arm ever recorded.**
| arm | mean err | AUC snap/argmax/soft | cov |
|---|---|---|---|
| **ZS sd_square (phase-1 only)** | **2.73%** | **87.9 / 86.2 / 85.7** | 30.3% |
| phase-2 sd_square T=1 | 4.68% | 76.3 / 76.7 / 75.0 | 40.0% |
| phase-2 squash T=1 | 4.75% | 77.6 / 76.4 / 74.8 | 38.0% |
| ZS squash (phase-1 only) | 6.33% | 68.8 / 68.8 / 68.0 | 22.1% |
- **Phase-1 has ALWAYS lived in the `sd_square` frame** (verified in code): renders are square, so feeding the photo as `squash` mismatched the photo side alone.
- **BUG B quantified on the grid production actually concatenates**: corr(SD saliency, DINO saliency) 0.366 under squash vs 0.711 under sd_square, xcorr peak shift +1 cell = +68 px vs 0. Under the production fuse the right ~25% of the photo gets NO SD feature at all.
- **Tal's calls this thread: move to `sd_square`; eval v2 from now on; comparisons isobbox-only; T=1.** The eval did not support the move — it was taken on the alignment figure.

## Status as of 2026-09-07 (eighth pod), POD CLOSING — CONDENSED 2026-09-14 (full text in the archive) — **phase marginalization was built into the production pipeline and measured photo-side: EVERY ARM IS FLAT.**
ZS 67.1->66.9 snap; phase-2 T=1 75.8->75.3 (argmax 73.6->74.4); phase-2 T=0.01 76.6->76.6 (argmax 75.3->75.4). **Tal: documented, not adopted, not reverted.**
- **Tal's design change made it cheap**: SD does not belong inside the phase loop, so it is 1 SD + 4 DINO forwards (~1.13x), not 4+4 (4x). Flag `--dino_phases N` in `analysis/extract_dino_sd_features.py`; identity guard `scripts/check_phase_fuse_identity.py` passes at 0.
- **What it does NOT fix, and it is the half that matters**: the lattice has two sources — (a) a positional term in the raw tokens (content-independent, corr -0.082), which phases DO remove, and (b) genuine neighbour dissimilarity (adjacent tokens at cosine 0.570 with 67.5 px cells), which they do not.
- **Two different papers, Tal asked directly**: the CAUSE is DVT (arXiv 2401.02957); the 4-phase trick is Phase Marginalization (arXiv 2606.08132, zero qualitative figures in the PDF).

## Status as of 2026-09-06 (seventh pod), POD CLOSING — CONDENSED 2026-09-14 (full text in the archive) — **the "block pattern" is NOT an interpolation artifact: it is a positional artifact of DINOv2, locked to the 14 px patch grid, and it lives in SIMILARITY space, not in the features.**
- **The lattice, measured**: inside one cell the token anchor has feature norm +17.2% and the MINIMUM mean cosine (0.4389) vs 0.5024 at the corner — a 16.5% similarity swing within a single cell. Bilinear upsampling is not blocky and is not the cause.
- **DINOv2's tokens are not spatially smooth**: adjacent token pairs sit at cosine **0.570** (random far pairs 0.264, mesh-side 1-ring **0.986**), and `corr(token cosine, mean-RGB distance)` is **-0.082**, i.e. the dissimilarity is not driven by image content. If neighbours were at 0.99 there would be no lattice at all.
- **Resolution helps the symptom, not the cause**: 224 -> 448 -> 840 px raises adjacent cosine 0.570 -> 0.678 -> 0.739 and shrinks the swing 17.2% -> 11.7%, but at MATCHED 67.5 px spacing it barely moves (0.570 -> 0.559 -> 0.519). **`input resolution 840` is still an open, genuinely different lever.**
- **Cause is known in the literature** (DVT) and is NOT the registers problem. A training-free fix (phase marginalization) was built here and taken into production the next pod (see 09-07) — but a control showed most of the gain is reproducible with a 4-tap blur and NO extra forward passes (`analysis/blockpattern_blur_control.py`).
- Tooling, all still present: `analysis/blockpattern_{stages,selfsim,resolution,resolution_viz,phase_marginalize,blur_control}.py`.

## Status as of 2026-09-05 (sixth pod), POD CLOSING — CONDENSED 2026-09-14 (full text in the archive) — **EVAL SET v2 IS LIVE.**
- Tal delivered the re-picked `.pp`; v2 measures **+1.8 / +2.7 / +1.2 AUC** on the same encoder. **v2 numbers are NOT comparable to any v1 number in this file, and v2 is the easier set** — every result written from 09-05 onward is v2, everything before it is v1. Naming: `eval_<tag>_v2.pth` under `demo/guitar/eval_labels/v2_edge_inset/`.
- **The check that makes v2 trustworthy**: the gain sits exactly where the edge labels were pulled inward, not spread across the set.
- Git: the two-week backlog was committed and pushed here. **Pod gotcha, recurs**: a fresh pod has no `github.com` host key and no loaded deploy key.
- Eval figure footers were cut to three lines, deliberately REVERSING the 09-01 full-provenance decision; every path is still stored inside the result file.
- The feature-RKD direction was written up as the durable section above this entry and set down.

## FEATURE-SPACE RKD — the whole direction in one place (durable reference, written 2026-09-05 at Tal's request)

Every attempt to add a **feature-space** relational term next to the spatial RKD loss, what each one
measured, and where the direction stands. Written because the results are scattered across five pod
entries and the one POSITIVE arm is easy to lose.

**SUPERSEDED 2026-09-09 — READ THE ELEVENTH-POD ENTRY AT THE TOP OF THIS FILE BEFORE THIS SECTION.
The standing conclusion below blamed CIRCULARITY; that is now DEMOTED.** Detach was run in BOTH
directions and neither fixed anything, so circularity cannot be the binding constraint — it explains
why the term is *satisfiable* without learning correspondence, not why it never helps. **The measured
answer is REDUNDANCY: the photo features already encode 2D geodesic structure at Spearman -0.82
(`analysis/teacher_geometry_check.py`, 40.96M pairs), so feature-RKD's teacher and spatial-RKD's
teacher are nearly the same teacher.** A symmetry-confusion hypothesis was also tested and REFUTED
(0/2048 centers prefer a geodesically far match). Everything below is still accurate as a record of
what was run and what it cost.

**THE STANDING CONCLUSION (as written 2026-09-05, now superseded — see above): nothing in this
direction has beaten spatial-RKD-alone in a way that survives the seed floor, and the reason was
believed to be CIRCULARITY.** The student's
feature `s(i) = Σ w_k F[v_k]` has two free paths, the weights `w` and the vertex features `F`. Every
feature relation (distance, 3-point angle, 2-point cosine) can be satisfied by reshaping `F` alone,
which does not pin the correspondence. Measured three independent times:
- 2026-08-29, distance term: featD fell -64% with `F` attached, only -4% with `F` detached.
- 2026-09-04, pair-angle attached vs detached: -85% vs -54%, and the detached arm LOST 6.8 AUC.
- 2026-09-04, gradient-path split: cutting the `w` path costs nothing (75.8 -> 76.0); cutting the
  `F` path costs 7 AUC (75.8 -> 69.0). The term is minimized almost entirely through `F`.

### The one arm that ever beat a baseline: argmax student, distance only, beta=0.05
`--feat_student_mode argmax` replaces the soft-mapped student with the single best-matching vertex's
own feature, so the assignment is a discrete index and a pixel's whole gradient lands on ONE vertex —
which removes both halves of the circularity at once. Old mesh, stride14 + squash + T=0.01 + seed 0;
the control IS that baseline (same phase-1, same photo features, same GPU).
| beta | geo snap | feat argmax | soft mean | mean AUC |
|---|---|---|---|---|
| 0 (baseline) | 76.2 | 75.7 | 73.2 | 75.03 |
| **0.05** | **78.0** | **76.2** | **73.8** | **75.98** |
| 0.1 | 75.8 | 74.6 | 72.8 | 74.43 |
| 0.2 | 78.4 | 74.6 | 72.9 | 75.31 |
| 0.5 | 77.4 | 76.3 | 72.0 | 75.21 |
**The only arm ever above baseline on all three metrics** (+1.8 / +0.5 / +0.6). **Do not over-read
it**: only geo snap clears the 1.6-2.4 AUC seed floor, the sweep is NON-MONOTONIC (0.1 below both
0.05 and 0.2), n=100 gives no significance, and it was never repeated on the isobbox mesh.
- Run: `experiments/guitar/encoder_dino_sd_stride14_nosdsquare_featrkd_argmax_dist0.05_ang0_T0.01_seed0_phase2/`;
  step grid at `demo/guitar/runs/rkd_feature/bsb_sd_dino_stride14_nosdsquare_featrkd_argmax_dist0.05_ang0_T0.01_seed0_phase2/step_progression_grid.png`.
  Scripts: `run_stride14_featrkd_argmax_beta_sweep.sh`, `run_featrkd_argmax_ANALYZE_BEST.sh`.
- **TAL'S CALL, 2026-09-05: argmax is NOT the right direction; do not deepen it now.** He holds that
  SOFT is the right student (2026-09-04) and that the fix must come from the loss. The beta=0.05
  result is recorded as the direction's high-water mark, not as a recommendation. **Tal has still
  never seen a render of this arm** — the step grid was the gate and it was never reviewed.

### What was tried, and what each one cost
| variant | student | outcome |
|---|---|---|
| distance (RKD-D), beta 0.05-1.0 | soft | never beat baseline; circularity shown by the detach test |
| distance, beta=0.05 | **argmax** | **+1.8 / +0.5 / +0.6 — the only win** |
| 3-point angle, gamma=0.2 | soft | COLLAPSE: 54.0 / 48.9 / 47.8. Contribution was 10.9x the spatial term |
| 3-point angle, gamma=0.2 | argmax | destroys the run the same way |
| **pairwise cos(center, nbr)**, w=0.01, 10 arms | soft | none beats spatial alone; see 2026-09-04 §8b |
| pairwise + RKD-D, 0.01 each | soft | all three paths DEGENERATE (drift goes negative) |
| pairwise, no spatial term | soft | diverged; featPA ROSE 47%. The spatial term is what prevents degeneration |

### The two durable rules this direction produced
1. **BUDGET THE SUM OF THE FEATURE TERMS, not each weight.** Contribution ratios against the spatial
   term, measured at step 25 of a probe run: 1.19x worked (argmax dist 0.05), 0.70x was neutral
   (pair-angle 0.01), ~1.5x DEGENERATED (angle + RKD-D), 10.9x COLLAPSED (3-point angle 0.2).
   Untried and cheap if this is ever revisited: 0.005 + 0.005 = ~0.75x. **Tal, 2026-09-05: not now,
   maybe later.**
2. **`drift` and `mu_msh_live` are the degeneration alarms.** Every healthy run in this project ends
   at drift +0.50..+0.87 and `mu_msh_live` ~0.90. Negative drift with `mu_msh_live` ~0.65 is
   degeneration, not weak performance — it means the features ended ANTI-correlated with phase-1.
3. **Distinctiveness is not a proxy for correspondence.** The pair-angle term produced the most
   distinctive features ever measured here (meanCos -0.055, effRank 33.5) and bought zero AUC. Always
   quote a RANDOM-gaussian reference next to any meanCos near zero (random: meanCos 0.000, stdCos
   0.026, effRank 1946) — without it, "meanCos ~ 0" reads as noise.

---

## Status as of 2026-09-04 (fifth pod), POD CLOSING — CONDENSED 2026-09-14 (full text in the archive) — **the PAIRWISE feature-angle term (Tal's variant) was built and swept to exhaustion: TEN arms, none beats spatial alone.**
| arm | AUC snap/argmax/soft | cov |
|---|---|---|
| **CONTROL — spatial only** | **75.8 / 73.6 / 73.6** | 38.0% |
| `gradF` (F only, all 16 nbrs) | 76.0 / 71.8 / 71.5 | 29.2% |
| `gradFW` (F + weights) | 75.8 / 71.9 / 70.8 | 31.8% |
| `gradW` (weights only, F detached) | 69.0 / 66.4 / 65.0 | 31.1% |
| `gradW` + close nbrs only | 54.6 / 56.0 / 50.9 | 22.2% |
| `gradF`, **no spatial term at all** | **16.4 / 18.6 / 4.0** | 8.2% |
- **Nothing beats the control** (`gradF`'s +0.2 is inside the seed floor), and **coverage drops in every arm**. Weight was derived, not picked (the raw term is 70x the spatial loss, so 0.01 puts it at 0.70x).
- **The substantive result is the gradient path**: cutting the WEIGHT path costs nothing, cutting the FEATURE path is catastrophic. The no-spatial run collapsing to 16.4 shows the feature terms cannot carry correspondence alone — they only ride on it.
- **Two directions CLOSED by Tal here**: close-neighbours-only, and the pairwise-angle term itself.
- **`demo/guitar` was reorganized** (107 top-level entries -> 16, grouped by kind). **Full old->new mapping in `demo/guitar/PATHS_MOVED.md`** — use it before hunting for a path. 269 references were rewritten across 144 files rather than symlinked.
- **Disk ceiling raised to 500 GB here** (Tal bought more) — not headroom to fill.
- Eval labels v2 were prepared here (edge labels pulled inward, min edge distance 1 -> 20 px, 57 of 100 moved, `--min_separation` required); the mesh side was delivered 09-05.
- **Naming trap that will recur**: building a run dir from flags in the wrong ORDER does not fail — it silently creates a SECOND folder, splitting one run's outputs in two.

## Status as of 2026-09-03 (fourth pod) — CONDENSED 2026-09-14 (full text in the archive) — **the distinctiveness loss on the new mesh is NOT `mu`, and phase-2's distinctiveness gain has largely vanished; the fuse was investigated three ways and all were rejected.**
**`mu_3d_scale` swept both directions, both far worse than no phase-2 at all** (isobbox, T=1, seed 0): 0.5 -> 51.4/51.8/51.2 AUC, cov 13.7%; **1 (control) -> 75.8/73.6/73.6, cov 38.0%**; 2 -> 37.7/39.6/32.0, cov 14.3% (and 2 never reached its target — a geometric ceiling, so it is not a clean test); ZS for reference 67.1/66.1/65.6.
- **Why mu could not have been the cause (arithmetic, done before the sweep)**: under `--geodesic` both normalizers are fixed geodesic diameters. `mu_2D` = 1171.65 px is a pure photo+mask property. `mu_3D` moved 1.90258 -> 2.05450, but +10.8% of that is the bbox-vs-centroid FRAME, which cancels in `d_3D/mu_3D`; only -2.5% of real geometry survives (~`mu_3d_scale 0.975`).
- **A mesh-side change that is NOT mu and still matters**: mean pairwise geodesic fell -9.7% while the diameter moved -2.5%, because the OLD mesh held ~41% of its vertices in the headstock. **Every vertex-weighted statistic shifted for that reason alone** — cross-mesh feature statistics are indicative, never clean.
- **Distinctiveness measured** (mesh-side mean cosine of 4 query vertices, lower = more distinctive): OLD ZS 0.646 -> OLD T=1 **0.003**; NEW ZS 0.674 -> NEW T=1 0.592, NEW T=0.01 0.622. The two ZS rows are close, so **the divergence is created in phase-2, not inherited**: phase-2 raises distinctiveness on both meshes, but the SIZE of the gain collapsed on the new one.
- **T=0.5 is a genuine interior distinctiveness optimum** (mean cos 0.443) **and is not the eval winner** (T=0.01 is, at 76.6/75.3). **Distinctiveness and AUC anti-correlate across the sweep** — this is the concrete form of Tal's complaint that the eval does not capture what he looks at. Tal's final call that pod: **T=1 on the new mesh** (back-projection), T=0.5 kept only as the distinctiveness reference.
- **Derived-`mu` follow-up (0.99/0.95/0.9, and later 0.75/0.8/0.85): all rejected by Tal.** `mu=0.95` measured the most distinctive features of any arm (0.417) at no AUC cost and was still rejected on the visual gate. Drift moved non-monotonically across this tiny knob (0.336/0.211/0.660/0.445), which says the optimization landscape is rough and single-seed rankings here are unsafe.
- **FUSE: three framings built and trained (`sd_square` zero-pad, `sd_square` replicate-pad, `aspect_nopad`+`common_grid 32`), all rejected — Tal: stay with `squash`** (reversed four days later, see 09-07).
  - **THE MEASUREMENT TRAP, do not repeat it: never evaluate fuse alignment on a PADDED grid.** Padded cells agree with padded cells, which made `sd_square` look far better aligned (0.81 vs 0.52); cropped to real content all four framings are identical (0.78).
  - A second claim died in its own test: SD's per-column norm decay near the pad is a plain image-edge effect, not zero-pad contamination (replicate-pad removes the extremes and leaves the real columns unchanged).
- **SHIC comparison started here** (Ye et al., arXiv 2407.18907): their weights + meshes + demo photos are in `demo/shic/`, inference in `analysis/shic_infer_correspondence.py`, and their training code is not public.
  - **Reusable technique: real UV checkerboards on any DensePose-CSE mesh.** SHIC's `.obj` files carry no `vt`, but DensePose publishes per-vertex UV for exactly these meshes (`analysis/fetch_densepose_uv.py`), and vertex correspondence was verified (>94% of edges within 0.1 UV units). Use `--checker_coords uv` ALWAYS with `--split_faces` (the UV-space Sutherland-Hodgman clip), grid 16 = Tal's pick. **Trap: DensePose's GEOMETRY `.pkl` unpickles to all zeros in this env** — apply the UV to SHIC's own geometry by vertex index and skip it.

## Status as of 2026-09-02 (all five entries of that day) — CONDENSED 2026-09-14 (full text in the archive) — **THE MESH WAS REPLACED: `meshes/guitar_isotropic_bboxnorm.obj` (3886v, isotropic, bounding-box-normalized) is the mesh going forward.**
- **The one root cause behind a day of silent breakage: normalization was defined by SAMPLING, not by SHAPE.** `loadmesh` normalized by the VERTEX CENTROID, so a remesh silently moves the frame — the same latent bug surfaced in SEVEN places, all silent. **The fix is a SIDECAR: `<mesh>.normalizer.json`, i.e. the frame is a property of the MESH FILE, not a CLI flag.** Anything that compares across meshes must convert to a common denominator (raw .obj units, reference 1.9026).
- **Result: the new mesh matches the T=1 baseline on every eval metric while raising soft-snap coverage 25.7% -> 40.1%.**
- **T sweep on the new mesh**: T=0.01 best on eval, T=0.1 clearly worse (~4-5 AUC below), T=1 preferred by eye (settled 09-03).
- **DINO-only measured BEST on 2 of 3 metrics** — the matched control says SD buys very little here (same story as 09-01, and see 09-07/09-08 where the framing turned out to be the reason).
- **ZS answered Tal's question**: step-0 looking decent is NOT a remesh effect — phase-1 was always this good.
- `color_mesh_from_knn` batch mode wired in; back-projection spatial-coherence metric added; **137 GB freed** in the big sweep-arm cleanup; three roadmap items closed by Tal.
- **The open thread Tal left at that pod's close became the whole 09-03 entry**: "on the new mesh the features are less distinctive; I suspect the normalization."

## Status as of 2026-09-01 (second pod of the day), POD CLOSING — CONDENSED 2026-09-14 (full text in the archive) — **DINO vs DINO+SD was finally measured: SD buys `feature argmax`, and that is about it.**
- `--dino_only` was added as a real ablation path (not a zeroed SD branch). The 2026-08-20 comparison Tal actually wanted was established by audit to be unrecoverable.
- Eval figures gained full provenance footers here (cut back to three lines on 09-05).
- **Feature-space RKD: the argmax student, distance only, beta=0.05 — the first and only positive signal that direction ever produced.** Full write-up is the durable FEATURE-SPACE RKD section above.
- **SHIC's training code was asked for and does not exist publicly** (still true as of 09-13).

## Status as of 2026-08-31 (second pod) — CONDENSED 2026-09-02 (full text in the archive)
- **`scripts/small_analyze.sh` built** — the ~9 min gate before `full_analyze`, from measured timings
  (step progression 10:30, of which 5:30 was twelve cold starts of `color_mesh_from_knn`).
- **`color_mesh_from_knn` got batch mode** (`--knn_paths`/`--save_dirs`); wired into the scripts
  2026-09-02, see that entry for the measured 7.7x.
- **Convention adopted**: a run's own eval goes in `demo/guitar/bsb_<run>/eval/`, and every
  comparison includes BOTH baselines — a win against only the weaker one is not a win.
- **12 feature-RKD arms on the current recipe: all rejected.** Beta sweep, three normalizers, a
  feature-only arm, both detach directions. Nothing beat the T=1 baseline.
- **CORRECTION recorded here**: this pod found the project's previously-recorded root cause for why
  feature-RKD fails (2026-08-29, the circularity argument) to be **WRONG**. Do not reuse that
  reasoning; the direction was reopened 2026-09-02 with an angle-based, normalizer-free variant.
- **Operational rule, learned the hard way**: wait loops take a PID (`while kill -0 <PID>`), never a
  `pgrep -f` pattern — the waiter's own command line matches the pattern and it waits forever.

---

## Status as of 2026-09-01, POD CLOSING — CONDENSED 2026-09-14 (full text in the archive) — **the baseline was moved BACK to the pre-`sd_square` recipe at stride 14, and two durable measurements came out of it.**
- **Stride was finally isolated and stride 7 does not survive it** — it had been promoted on 08-28 and lost here.
- **THE SEED DRAW IS WORTH 1.6-2.4 AUC on this recipe.** This is the "seed floor" every later entry quotes when it calls a gap meaningless.
- Mesh-side feature space did not explain Tal's visual preference; the T=0.001 arm finished; two explainer diagrams were made for a talk.

## PROTECTED — the T=1 companion of the current baseline (flagged 2026-09-01)

**Do not delete, and do not strip its step checkpoints:
`experiments/guitar/encoder_dino_sd_stride14_nosdsquare_relational_geodesic_mu3dscale1_T1_seed0_phase2/`
and `demo/guitar/runs/oldmesh_sweeps/stride14/bsb_sd_dino_stride14_nosdsquare_T1_seed0_phase2/`.** Tal's call, 2026-09-01: keep
both temperatures of the new baseline side by side. It is the only run on this recipe that differs
from the promoted one in exactly one knob (training + read temperature), which makes it the control
for every future temperature claim here. Comparison images:
`comparison_vs_T0.01/backproj_T1_vs_T0.01_native_readT.png` (each arm at its own read T) and
`comparison_vs_liked_T0.01/backproj_T1_vs_liked.png`.

---

## PROTECTED — the stride-14 SD-ALIGNED run, a recipe Tal may come back to (flagged 2026-08-30)

**Do not delete: `experiments/guitar/encoder_dino_sd_dfd_crossview_sdaligned_relational_geodesic_mu3dscale1_phase2/`
and `demo/guitar/runs/legacy/bsb_sd_dino_dfd_crossview_sdaligned_relational_geodesic_mu3dscale1_phase2/`.**
On 2026-08-30, comparing back-projections, Tal judged this one good and asked that it be kept as a
recipe worth returning to: *"עם SD ALIGN זה כן טוב ... זה מתכון טוב שאולי נחזור אליו בעתיד."*
The image that settled it:
`.../analyze/back_projection/guitar_01_click_270_370_sam_mask_2_backproj_guitar_mesh_checker16_color_soft_snap_k1_side_by_side.png`
(checker16 back-projection through the soft-snap correspondence, k=1). The same file exists under
the pre-`sd_square` run below, and the pair is the cleanest before/after of that fix on disk.

**The recipe**: phase-1 `encoder_dino_sd_dfd_crossview_phase1`; photo features
`demo/guitar/features_analyze/dino_sd_aligned/guitar_01_pix_dino_sd_features_aligned.pth`;
`--geodesic --mu_3d_scale 1 --temperature 1.0`; masks `segment_masks_pixel270_370/`; width/n_classes
2304, 300 iters, lr 1e-4, `--seed 0`; no cyc, no balance. **UNSEEDED** (predates `--train_seed`).
= **stride 14, WITH the `sd_square` fix, WITHOUT stride 7 / `gridalign`.**

**How it differs from the 2026-08-30 baseline — one thing only**: the photo feature path. Baseline
uses stride 7 + `gridalign`; this uses stride 14. Everything else in the two configs is identical
(verified by config diff), and both are T=1 and SD-aligned.
| | geo snap | feat argmax | soft mean | coverage |
|---|---|---|---|---|
| stride 14, SD-aligned (this run) | 77.9 | 76.5 | 75.4 | 1101 (27.3%) |
| stride 7 + gridalign (baseline) | 78.9 | 77.2 | 75.8 | 1064 (26.4%) |
**The gaps are +1.0 / +0.7 / +0.4 AUC, entirely inside the 1.6 AUC noise floor measured 2026-08-30,
and coverage moves the other way.** So stride 7 has never been shown to beat stride 14 outside
noise — it was promoted 2026-08-28 on a gap that looked bigger than it was. That is exactly why
this run is kept. Comparison material already built:
`demo/guitar/runs/oldmesh_sweeps/stride7/bsb_sd_dino_stride7_gridalign_T1_seed0_phase2/comparison_vs_stride14/` and
`demo/guitar/eval_labels/eval_compare_stride14_vs_stride7gridalign.png`.
**Open**: the honest test is a SEEDED stride-14 run on the current recipe (~3 min). Not yet run.

**Also kept, the pre-`sd_square` ancestor**:
`demo/guitar/runs/legacy/bsb_sd_dino_dfd_crossview_relational_geodesic_mu3dscale1_phase2/` (promoted 2026-08-22,
superseded 2026-08-27). Same recipe as the above but on
`dino_sd_poc/guitar_01_pix_dino_sd_features.pth` -- the features from before SD was given the
aspect-preserving frame. Tal decided 2026-08-30 to keep the old runs rather than delete them.

---

## Status as of 2026-08-31, POD CLOSING — CONDENSED 2026-09-14 (full text in the archive) — **`sd_square` was taken off the baseline (Tal's call, later reversed on 09-07) and the whole T sweep was re-run without it.**
- **`--sd_frame squash` was added here**: the old framing became a knob rather than a deleted bug, which is what made the 09-07 reversal a one-flag change.
- **Phase-1 does NOT need retraining for a framing change** — verified, not assumed (renders are square either way).
- **THE READ-TEMPERATURE CONFOUND, the durable finding of that pod**: a run read at a temperature different from the one it trained at is not the same picture. Since then every isobbox eval and back-projection on record is read at T=1, and any figure must say its read T.

## Status as of 2026-08-30 — CONDENSED 2026-09-02 (full text in the archive)
**Its headline conclusion was REVERSED the next day. Do not act on it.** This pod declared the
temperature thread closed with T=1 the winner on a matched-seed sweep (stride 7 + gridalign, seed 0:
T=1 scored 78.9 / 77.2 / 75.8). On 2026-09-01 Tal moved the baseline back to T=0.01 on the
back-projection, explicitly against those numbers, and T=0.01 is the recipe today.
What still holds:
- **The seed noise floor was measured cleanly for the first time**: up to 1.6 AUC / 1.8 pp coverage
  on ONE GPU, from seeding alone. Every comparison in this project is read against it.
- **`drift` is NOT a quality metric** — shown directly, stop treating it as one.
- **Temperature is a READ-time knob that training cannot bake in.**
- **Two independent attempts to explain Tal's preference for the pre-`sd_square` renders both
  FAILED** — a clean double negative, still unexplained.

---

## Status as of 2026-08-29 — CONDENSED 2026-09-02 (full text in the archive)
- **PHASE-2 WAS UNSEEDED TOO.** `phase2/train_relational_loss.py` had no `torch.manual_seed`, and
  the relational loss resampled neighbours off the global RNG every step, so no phase-2 run had ever
  reproduced itself. The 2026-08-28 noise floor had been blamed entirely on SD; part of it was this.
  **The floor is bigger than first recorded: up to 2.0 AUC.** Fixed — `--train_seed` is on every run
  since, and the current baseline is seed 0.
- **A `.detach()` bug in the first feature-RKD implementation collapsed the model**; after fixing it,
  live vs fixed `mu` was inconclusive.
- **This pod's conclusion about WHY feature-space RKD fails (the circularity argument) was later
  shown to be WRONG (2026-08-31, second pod).** It is preserved in the archive only so the mistake
  is traceable — do not reuse the reasoning.
- **The temperature sweep here was non-monotonic: T=0.1 is worse than BOTH its neighbours.** That
  reproduced on the isotropic mesh 2026-09-02 (T=0.1 = 72.3 / 72.0 / 71.0), so it is a real property
  of this recipe, not a one-off.

---

## Status as of 2026-08-28 — CONDENSED 2026-09-02 (full text in the archive)
**Its promotion was later reversed**: stride 7 + `gridalign` was promoted here on Tal's visual
review, and on 2026-09-01 stride was isolated properly and **stride 7 lost**. Stride 14 is current.
What still holds:
- **Naming**: the patch-grid alignment fix is `gridalign` (was "fixA"); on-disk paths keep `fixA`.
  Full mechanism in "THE TWO FEATURE-PATH BUGS" below.
- **`gridalign` is not optional at stride 7** — without it, stride 7 is worse than stride 14.
  **Lesson: ZS is not a sufficient gate for a feature-path change.**
- **SD's two unseeded noise draws were found and seeded** (there were two, not one).
- **Precompute cost, measured on an RTX 2000 Ada**: 15.3 min per 1000 views at stride 14, 16.7 at
  stride 7 — **~80% of it is Stable Diffusion**, which is independent of the stride. The earlier
  "the stride cost 13 minutes" belief was a misread progress bar.
- **The project's first measurement of its own run-to-run noise floor** — as large as the recipe
  differences being promoted on. That framing has held ever since.

---

## Status as of 2026-08-27 — CONDENSED 2026-09-02 (full text in the archive)
- **Two real geometric bugs were found and fixed in the DINO+SD feature path**, both measured rather
  than argued. The durable explanation is its own section below ("THE TWO FEATURE-PATH BUGS") and is
  kept in full; this entry was only the run-by-run narrative.
- **The ViT patch-grid "blockiness" was root-caused**, and the overlapping-patch (stride) trick was
  implemented.
- **The T sweep completed and REVERSED its own previous conclusion**: T=0.01, not T=0.001, is best.
  T=0.01 is still the baseline's training temperature today.

---

## Status as of 2026-08-26 — CONDENSED 2026-09-02 (full text in the archive)
**The evaluation was rebuilt properly this pod, and its design is still the one in use**: three named
metrics (geometric snap / feature argmax / soft mean distance), an acc(eps) curve, and AUC, all in one
figure (`analysis/eval_geodesic_error.py`, `analysis/compare_eval_runs.py`).
- The first three-way comparison ran; T=0.001 beat the baseline on all three.
- **Nothing was statistically significant at n=100, and nothing has been since.** Labeling more
  points — not compute — has been the binding constraint from this pod onward.
- One refinement recorded here that still holds: the 2026-08-25 "the model perfectly cancels any
  sharpening" conclusion was drawn from a single point; with four points the compensation SATURATES.

---

## Status as of 2026-08-25 — CONDENSED 2026-09-02, four same-day entries merged (full text in the archive)
**The project got its first ground-truth number this pod.**
- **Tal hand-labeled all 100 eval points** (`demo/guitar/eval_labels/guitar_picked_points_final.pp`,
  *"היה סיוט לתייג את זה"*) — validated before use: 100 points, names exactly 0..99, no duplicates.
  Joined by `analysis/join_eval_pixel_labels.py` into `pixel_vertex_eval_pairs.pth`. Points were
  renumbered into spatial (serpentine) order before labeling, at Tal's request.
- **GT snap quality on the original mesh**: median 0.0106, mean 0.0152, **max 0.1319** — the join's
  large-max warning was investigated, not ignored. (On the isotropic mesh this improved to mean
  0.0053 / max 0.0102; see the 2026-09-02 entries.)
- **First real number**: current-best DINOv2 recipe, mean geodesic error 4.6% of mesh diameter
  (hard snap) / 5.1% (expected), n=100.
- **The softmax is effectively a no-op** across all 212,549 masked pixels (effective-k median 9.999).
  The near-uniform softmax is what the relational loss actively WANTS, not a defect — this reversed a
  recommendation that was on record. Refined 2026-08-26: the compensation saturates.
- **`analysis/make_run_vs_baseline_comparison.py`** — the reusable baseline-comparison tool. Use it
  rather than writing a new comparison per run.
- **DINOv3 was reviewed and PAUSED** (not parked): ZS 465/4036 (11.52%), phase-2 903/4036 (22.37%),
  both below the DINOv2 baseline. Its phase-1 cache was deleted 2026-09-02 (regenerable).
- Model switch this pod, Tal's call: Sonnet 5 -> Opus 5.

---

## Status as of 2026-08-24 — CONDENSED 2026-09-02, two entries merged (full text in the archive)
**The hand-labeled evaluation set was designed and built this pod** (Tal's own request, not on the
roadmap). 100 pixels chosen by seeded 2D farthest-point sampling over the mask
(`analysis/sample_eval_pixels.py`); Tal then clicked the corresponding vertex for each in MeshLab's
Point Picking tool, saving a `.pp`. That file is still the project's only ground truth, and it is
mesh-independent — it stores raw 3D positions, which is why it survived the 2026-09-02 remesh (see
the coordinate-frame bug in that entry before reusing it on a new mesh).
**Also this pod: DINOv3 was swapped in end to end** — phase-1 + phase-2 + full analysis. Result
903/4036 (22.37%) soft-snap coverage vs the DINOv2 baseline's 1091/4036 (27.03%). Not promoted;
paused 2026-08-25 pending a real metric, and never resumed.

---

## Status as of 2026-08-24, later — item 3 (DINOv3) SCOPED (CONDENSED 2026-08-25; superseded by the EXECUTED entry above)

The scoping entry that preceded execution. Full version (all sourced DINOv3 facts, the grep-verified
patch-size analysis, the gated-access blocker narrative) is in `/workspace/archive/pre-consolidation-2026-08-25/PROJECT_NOTES_full_2026-08-25.md`. Durable points only:
- Current DINO everywhere is **`dinov2_vitl14_reg`** (`DINOWrapper(small=True)`, all 7 call sites), embed
  dim 1024 — which is why `--width`/`--n_classes 2304` = 1280 (SD) + 1024 (DINO-L).
- Loaded from a **local pinned checkout** (`/workspace/.cache/dinov2_git` @ 9c7e324), NOT live `torch.hub`:
  upstream `main` uses Python 3.10+ syntax that breaks under `bsb`'s Python 3.9.
- `dinov3_vitl16` matches at embed dim 1024, so the swap needed **zero architecture changes**; the 14→16
  patch-size change was grep-verified safe (grid size is derived generically everywhere in core code).
- DINOv3 weights are **gated** (Meta license + HF token, Tal-only) and need an isolated env — `bsb`'s
  torch 1.12 / transformers 4.34 cannot load them.
## PARKED directions: item 2 (AnyUp) and item 4 (GeoAware-SC / left-right symmetry) — CONDENSED 2026-08-25

Five full entries (2026-08-23 x3 for AnyUp, 2026-08-23 + 2026-08-22 for GeoAware-SC) were condensed here
on 2026-08-25. **Both directions are hard-parked and were deliberately stopped, not merely out-competed.**
Every detail — full env build recipes and their gotchas, the AnyUp architectural wall and its traceback,
NATTEN's `q_chunk_size` OOM lesson, the 4-way ZS comparison tables, GeoAware-SC's detectron2 build saga,
per-run disk accounting — is preserved verbatim in `/workspace/archive/pre-consolidation-2026-08-25/PROJECT_NOTES_full_2026-08-25.md`. **If either is revisited, read the archive
rather than re-deriving.**

**Item 2 (AnyUp universal feature upsampler) — final results**, all against the current-best baseline
(bilinear both sides, ZS 603/4036, phase-2 **1091/4036**):

| variant | ZS | phase-2 |
|---|---|---|
| AnyUp photo, `use_natten=False` | 405/4036 | 1010/4036 |
| **AnyUp photo, `use_natten=True`** | 455/4036 | **1089/4036 — essentially tied with baseline** |
| AnyUp both sides, `use_natten=False` | 407/4036 | 929/4036 |

Best case only *tied* the baseline, never beat it. Tal consulted Itai and stopped the whole direction.
**Unresolved confound, flagged if ever revisited**: the natten run also fixed ImageNet mean/std
normalization of the guide image, so `use_natten` cannot cleanly get sole credit — the isolating
experiment is `use_natten=False` WITH the corrected normalization. **Kept on disk**: all final
checkpoints, all visual outputs, `/workspace/anyup_repo/` (16MB, real reusable Stage-B scripts).
**Deleted**: ~106GB of reproducible caches + the disposable `anyup` env.

**Item 4 (GeoAware-SC / left-right symmetry)**: approach (A) pretrained backbone run to completion
through phase-2 and parked (Tal: results not good enough). Approach (B), a self-supervised
mirror-pair post-processor, was built and parked (noisy mirror labels on this not-fully-symmetric mesh).
**Kept**: both checkpoints (62MB each) and both visual-review dirs. **Deleted**: the 12GB `geoaware_f`
cache, the env, the repo clone.

**Idea (C), UNTRIED and still live — preserved verbatim because it is the natural next step here**:
test-time-only flip-and-compare, no training. Flip the real query photo, recompute features through the
GeoAware backbone, get a second candidate vertex match; use (B)'s existing geometric mirror-correspondence
to know which vertex is the "flipped" counterpart of a normal-orientation candidate; keep whichever
candidate has higher confidence. Cheaper and structurally closer to the paper's own proven mechanism than
either (A) alone (no disambiguation at all) or (B) alone (bakes possibly-noisy mirror labels into trained
weights) — here mirror-geometry only breaks a per-query tie at inference, so its noise affects one decision
at a time, not the whole learned field. Not started — Tal wants to read the paper in more depth first.

**LEFT-RIGHT SYMMETRY IS A LIVE THREAD, independent of GeoAware-SC being parked** — it is now flagged in
three separate places: (1) `analysis/pca_feature_compare.py --basis independent` shows left/right-symmetric
mesh points collapsing to near-identical colors **in the current best-recipe checkpoint's own feature field**
(`encoder_dino_sd_dfd_crossview_phase1`) — the `--basis shared` default may have been masking this, since it
is pixel-variance-dominated; (2) the sim-heatmap query set deliberately includes a belly-left/belly-right
symmetry probe; (3) the 2026-08-25 eval-metric work found one labeled pixel whose top-10 candidates spanned
**29.7% of the mesh geodesic diameter**, the same signature. **Proposed but never run**: raw cosine
similarity between a known left/right mirror vertex pair on the current checkpoint.
## Recipe lineage, 2026-08-21 → 2026-08-22 (CONDENSED 2026-08-25 — full entries in the archive)

Three pods of promotion/comparison work, all resolved. Full entries (per-step smoothness and coverage
tables, the axis-bug root-cause narrative, the cross-view-batching research against DFD's own repo) are in
`/workspace/archive/pre-consolidation-2026-08-25/PROJECT_NOTES_full_2026-08-25.md`. What still matters:

| date | change | coverage |
|---|---|---|
| 08-21 | **Real axis bug found and fixed** in the promoted recipe's phase-1 loss; DFD (item 5) implemented end-to-end | mixed, neither promoted yet |
| 08-22 | **axisfix promoted** (Tal's call) — a genuine bug fix even though coverage dipped slightly | 931/4036 (23.07%) |
| 08-22 | **DFD cross-view batching promoted — CURRENT RECIPE** (see top of file) | **1091/4036 (27.03%)** |

**Durable points**: the axisfix→DFD-cross-view supersession happened within a single day, so entries
dated before it name whichever checkpoint was current at the time — left as-is by convention.
Tal chose DFD cross-view on the coverage win (best ever recorded) despite a smoothness dip
(-0.591 vs axisfix's -0.693), after visual review. Both superseded checkpoints are KEPT as fallbacks.
The DFD phase-1 mechanism itself is documented in full in the section immediately below — that one is
current recipe, not history.
## DFD barycentric feature distillation (roadmap item 5) — implemented and run end-to-end this
session, not yet promoted. Builds on Tal's own paper read (prior pod was code/repo-only): "take
their distillation process — train the encoder on vertices AND on points between vertices, using
their algorithm" — i.e. query the encoder at continuous barycentric-interpolated surface points
under every rendered pixel, not just the mesh's ~4036 fixed vertices.

**Key mechanism** (fully explained to Tal this session, worth restating precisely since it's easy
to get backwards): today's `train_encoder`/`train_encoder_dino_sd_l2norm.py` paint the network's
*prediction* (`pred_f`, which changes every step) as the mesh's render color and re-render every
step — because turning a per-vertex output into a per-pixel comparable value requires
interpolation, and that interpolation must be redone every step since the thing being interpolated
(`pred_f`) changes every step. Geometry itself (`mesh.vertices`) is constant in *both* the baseline
and DFD — that was never the variable. DFD's swap: paint `mesh.vertices` (constant) as the color
instead, render *once* to get exact per-pixel xyz, then query the encoder directly at each pixel's
own location — no per-vertex-output interpolation step exists anywhere anymore.

**New files, both additive, neither touches any existing file**:
- `modules/barycentric_targets.py` — `encode_random_views_xyz_bary(args)`, one-time xyz-per-pixel
  cache generation (paints `mesh.vertices`, renders via the existing `Renderer.render_views`, same
  `{'model_f','elev','azim'}` schema every cache uses, reuses the existing
  `random_viewing_angles.pt` so it aligns view-for-view with `dino_sd_f/`). Background sentinel
  `2.0` (mesh is bounding-sphere-normalized, real coords always in `[-1,1]`, unlike reusing `1.0`
  which real feature values can land near). Saved to
  `data/guitar/encoder_data_frontcentered_dinosd/xyz_bary_f/224/` (new subdir alongside the
  existing `dino_sd_f/`). Hit and fixed one real circular-import bug in this codebase
  (`modules/mesh.py`/`modules/utils.py` import each other — importing `modules.render` before
  anything pulls in `modules.utils` fails; existing scripts avoid it by accident of import order,
  fixed here by explicit ordering).
- `train_encoder_dfd.py` (repo root) — `EncoderL2Norm` + cosine loss (matches the promoted recipe's
  convention; checked DFD's own repo, `distillation.py`: they use `mse_loss` on L2-normalized
  features, mathematically equivalent up to a constant to cosine loss on unit-norm vectors, so no
  different loss needed). **Pairs the xyz cache and the `dino_sd_f` cache by explicit shared file
  index** (`target_..._f_{i}.pt`), not through `EncoderDataset`'s unordered `glob` — a real footgun
  caught before it caused silent wrong-view-pairing (every existing script gets away with unordered
  glob because it re-renders at each loaded file's own elev/azim every step; this script skips
  rendering entirely, so nothing else would have caught a mismatch). **No render call anywhere in
  the training loop** — both sides are pre-cached. Hit and fixed a second real bug in my own new
  code before training ever ran: `dino_sd_f`'s saved `model_f` keeps `postprocess_features`'s own
  leading dim of 1 (`[1,C,H,W]`), unlike the xyz cache (saved pre-squeezed to `[C,H,W]`) — fixed by
  squeezing in `PairedXYZFeatureDataset.__getitem__`.

**Checkpoints**: `experiments/guitar/encoder_dino_sd_dfd_phase1/`,
`experiments/guitar/encoder_dino_sd_dfd_relational_geodesic_mu3dscale1_phase2/`. Phase-2 needed
**zero new code** — confirmed the existing `train_relational_loss_l2norm.py` monkeypatch pattern
plugs in any `EncoderL2Norm` checkpoint regardless of how phase-1 produced it, just point
`--init_encoder_dir` at the new dir. Resume-gate passed with `max abs diff` **exactly 0.000e+00**
(the cleanest pass of any checkpoint so far), confirming the seeding-then-construct order in the
new script is exactly right.

**Result — beats the axisfix comparison on smoothness and speed, loses on coverage**:

| | buggy (promoted) | axisfix | DFD |
|---|---|---|---|
| ZS/phase-1 soft-snap coverage | 649/4036 (16.1%) | 535/4036 (13.26%) | 620/4036 (15.36%) |
| phase-2 soft-snap coverage | 976/4036 (24.2%) | 931/4036 (23.07%) | **860/4036 (21.31%)** |
| phase-1 smoothness corr | -0.813 | -0.815 | **-0.849 (best)** |
| phase-2 smoothness corr | ~-0.60 (historical) | not measured | **-0.660 (best)** |
| phase-1 wall-clock (3 epochs, 3000 steps) | not measured | ~19 min (renders every step) | **~13 min (zero renders in loop)** |

DFD is clearly the smoothest and fastest-training variant of the three, and the "no render in the
loop" design goal was confirmed empirically (~30% faster than axisfix's otherwise-identical phase-1
loop). But it's the *worst* of the three on phase-2 soft-snap coverage, despite beating axisfix at
ZS — coverage and smoothness may be measuring genuinely different things, not just noise. **Not
promoted this session** — needs Tal's visual review (step-progression grid, 10-panel
analysis_summary, PCA/sim-heatmap sent for both ZS and phase-2) + a decision on which property
(coverage vs. smoothness) matters more for the actual downstream correspondence goal, next pod.

**New analysis scripts this session, all additive**: `scripts/run_sd_dino_l2norm_frontcentered_axisfix_ZS.sh`,
`scripts/run_sd_dino_l2norm_axisfix_relational_geodesic_mu3dscale1_{analysis,full_analyze}.sh`,
`scripts/run_sd_dino_dfd_frontcentered_ZS.sh`,
`scripts/run_sd_dino_dfd_relational_geodesic_mu3dscale1_{analysis,full_analyze}.sh` — all straight
path-substitution copies of the existing L2norm scripts (diffed to confirm nothing else changed),
matching the standard per-run pipeline template (train → step-progression → full-analyze).

**Open follow-up, Tal's explicit ask for next pod's start**: investigate speeding up training
further via cross-view point batching, closer to what DFD's own paper/repo may do — this session's
`train_encoder_dfd.py` deliberately started with the simplest option (one *view's* masked pixels as
one training batch, matching every existing script's per-view-batch convention), per Tal's own call
mid-session ("start with the easy option, switch only if it's too slow/resource-heavy"). Given it
already came out faster than the baseline it replaces (~13 min vs ~19 min for the same 3 epochs),
this wasn't yet needed, but Tal wants it looked at next pod regardless — worth first re-confirming
what DFD's paper/repo actually does here (this session's understanding of "cross-view" batching is
Tal's own recollection from reading the paper, not independently re-verified against
`distillation.py`'s actual batch-construction code this session — check that first).

---

## Recipe lineage, 2026-08-15 → 2026-08-20 (CONDENSED 2026-08-25 — full entries in the archive)

Every entry from this window was resolved and folded into the current recipe. Full blow-by-blow
(each dated entry verbatim, every measurement table, every debugging narrative) is in
`/workspace/archive/pre-consolidation-2026-08-25/PROJECT_NOTES_full_2026-08-25.md`. What still matters:

| date | change | result (soft-snap coverage) |
|---|---|---|
| 08-15 | Fibonacci-lattice phase-1 view sampling built + evaluated | lost to `bsb_retrained`; PARKED |
| 08-16 | **`--frontview_center` bug found and fixed** → `encoder_dino_frontcentered` adopted as init | 744/4036 vs 603 vs 391 |
| 08-17 | Coarse mask hole found+fixed → `segment_masks_pixel270_370/` adopted (see top of file) | — |
| 08-18 | DINO+SD fusion (item 1) Stage 3 trained; **numerical-stability bug found** | — |
| 08-19 | **Norm-inflation traced to phase-1, not phase-2. L2-normalize fix** → smoothness -0.27 → -0.80 | — |
| 08-20 | **SD-DINO L2norm promoted** as default recipe | 976/4036 (24.2%) |

**Durable lessons from this window** (the reason these entries existed at all):
- **L2-normalize the encoder output.** Skipping it inflated feature norms and destroyed vertex-feature
  spatial smoothness at phase-1 — the fix is why `EncoderL2Norm` exists and why every current script uses it.
- **The ZR/ZS puzzle** (fibonacci losing to any Gaussian regardless of center) was investigated across two
  entries; three plausible explanations were tested with real data and **all three ruled out. Still unexplained** —
  if fibonacci/view-sampling is ever revisited, start from the archive rather than re-deriving.
- Naming: "ZS" (zero-shot) replaced "ZR" from 08-18 on; archived entries predating that still say ZR.

## Environment setup

Repo: https://github.com/threedle/bsb/. **Why `/workspace`:** it's a
persistent RunPod network volume; `/` and `/root` are ephemeral and wiped on
pod migration/switch. Everything below was deliberately installed under
`/workspace`.

**To resume on a new pod:**
```bash
source /workspace/activate_bsb.sh
```
This sources conda from `/workspace/miniconda3`, activates the `bsb` env,
sets `PIP_CACHE_DIR` and `TORCH_HOME` under `/workspace/.cache/` (so hub
downloads persist), and cds into `/workspace/bsb`. Sanity check:
```bash
python -c "
import torch, kaolin, open3d, cv2, transformers, numpy
print('torch', torch.__version__, 'cuda:', torch.cuda.is_available())
print('kaolin', kaolin.__version__, 'open3d', open3d.__version__)
print('cv2', cv2.__version__, 'transformers', transformers.__version__)
print('numpy', numpy.__version__)
"
```
Expected: torch 1.12.1+cu113, cuda **True** (on a GPU pod), kaolin 0.14.0,
open3d 0.17.0, cv2 4.8.1, transformers 4.34.0, numpy 1.26.4.

**ALSO CHECK THE GPU ARCH -- `cuda.is_available()` being True is NOT enough.** torch 1.12.1+cu113 compiles up to
**sm_86**, so it runs on Ampere and Ada (A4500 sm_86, RTX 2000 Ada sm_89) and **fails on Blackwell (sm_120: RTX PRO
xxxx Blackwell, RTX 50xx, B200)** with `CUDA error: no kernel image is available for execution on the device` at the
first kernel launch -- after reporting the GPUs as available. So rent Ampere/Ada only, and prove it before launching:
```bash
source /workspace/activate_bsb.sh && python -c "import torch; x=torch.randn(64,64,device='cuda'); print('GPU OK', (x@x).sum().item())"
```
Do not pipe the `source` into anything -- a pipe puts it in a subshell, the env never activates, and `python` resolves
to `/usr/bin/python3` (torch 2.8.0+cu128, Blackwell-capable, **no kaolin**), which makes a broken pod look fine.
Full story in the twenty-sixth-pod entry near the top of this file.

**What's installed (all on `/workspace`, persists across pods):**
Miniconda (`/workspace/miniconda3`) → conda env `bsb` (python 3.9.18) →
`install_environment.sh` run inside it → SAM ViT-H checkpoint at
`bsb/SAM_repo/model_checkpoints/sam_vit_h_4b8939.pth` → demo data
(`images/guitar_01.png`, `meshes/guitar.obj`, `demo/guitar/encoder_dino/`,
`demo/guitar/encoder_sam/`, `decoder_checkpoint.pth` — this last one now
lives in `demo/guitar/bsb_origin/` and `bsb_retrained/`).

**First command on a brand-new `git status` after `source activate_bsb.sh`**
may fail with "dubious ownership" (pod's user ID differs from the volume's
file owner) — fix once per pod:
```bash
git config --global --add safe.directory /workspace/bsb
```

### Known gotchas (already fixed, don't redo unless symptoms reappear)

- **RunPod volume migrations can look stuck but aren't.** If imports fail
  right after a migration event with widespread empty package dirs, that's
  real but resolves on its own — don't reinstall. Check `df -h /workspace`
  and `du -sh /workspace/miniconda3` (plausible size = data exists, still
  syncing) before assuming loss.
- **DINOv2 `main` branch incompatible with Python 3.9** (PEP 604 `X | None`
  type hints, upstream commit `12592a9`, still broken as of last check).
  Fixed by pointing `modules/dino.py`'s `torch.hub.load` calls at a pinned
  local clone: `/workspace/.cache/dinov2_git`, checked out to commit
  `9c7e324` (has the `_reg` backbones, predates the break by ~20 months).
  This fix lives partly **outside** `/workspace/bsb` (the clone), so if a pod
  is recreated from scratch (not just migrated), the whole thing needs
  redoing — clone dinov2, checkout `9c7e324` as branch `py39-compat`, repoint
  `dino.py`. If this pod is just migrated, nothing to do.
- **Torch hub weight cache** relocated to `/workspace/.cache/torch` via
  `TORCH_HOME` in `activate_bsb.sh` — `source='local'` only replaces the code
  fetch; pretrained weights are a separate `load_state_dict_from_url` call
  that still needs `TORCH_HOME` redirected or it re-downloads ~1.1GB every
  pod. Already wired in `activate_bsb.sh`, nothing to do.
- **GitHub push access** (personal fork, `git@github.com:talberger/disc.git`,
  remote `github`): SSH deploy key at `/workspace/.ssh/id_ed25519_github`.
  `/workspace` itself can't hold restrictive file perms (network volume), so
  `activate_bsb.sh` copies the key to `/root/.ssh/` (ephemeral, correct perms)
  every source. Nothing manual needed per pod.
- **`python-pptx` + `libreoffice-impress`/`poppler-utils`** (only needed for
  rendering the phase-2 explainer deck, not core to BSB): `python-pptx` is
  `pip install`ed into the `bsb` conda env (persists). `libreoffice-impress`/
  `poppler-utils` are OS packages (`apt-get`) — do **not** persist, reinstall
  if a deck needs re-previewing: `apt-get update && apt-get install -y
  --no-install-recommends libreoffice-impress poppler-utils`.
- **Running anything under `phase2/` as a plain script breaks imports**
  (2026-08-16 fix, see status above): `python phase2/train_relational_loss.py`
  sets `sys.path[0]` to `phase2/`, not the repo root, so `import modules.x`
  fails. Now fixed inside the file itself (`sys.path.insert` at the top,
  same pattern every `analysis/*.py` script already used) — just run it
  normally from `/workspace/bsb`, no special invocation needed anymore.
- **`pip install accelerate` (unpinned) silently upgrades `torch` to a
  current release** (2026-08-18: pulled `torch==2.8.0`, wiping the pinned
  `torch==1.12.1+cu113`, and bumped `huggingface_hub` to `1.8.0`, breaking
  `tokenizers`/`transformers` compat) — pip's resolver doesn't warn before
  doing this. Recovered via `pip uninstall torch huggingface_hub accelerate
  hf_transfer` then reinstalling the exact pinned versions (`torch==1.12.1+cu113
  --index-url https://download.pytorch.org/whl/cu113`, `huggingface_hub==0.17.3`),
  verified against this file's own sanity-check block. **Any new package
  added to this env from now on: use `--no-deps` or an exact version pin,
  never a bare `pip install <pkg>`** — this old torch/cu113 pin is fragile
  against the modern package ecosystem's default dependency resolution.
  `accelerate` itself was skipped entirely (optional for `diffusers`,
  not worth the risk) rather than re-attempted pinned.

---

## How Tal wants the assistant to work

- **Write technical explanations in English.** Hebrew is fine for short
  conversational exchanges, but anything explanatory — metrics, results,
  interpretation — should be in English; Hebrew ML prose is harder to parse.
  **2026-08-17 refinement**: mixing Hebrew framing with English technical
  content (paths, numbers, lists) in the same message is also hard to read —
  when a message contains any technical content, write the whole message in
  English rather than switching between the two languages within it.
- **THREE MACHINES (Tal, 2026-10-24):** Mac (no GPU: analysis, figures, Obsidian), RunPod pod and Run:ai (GPU). GitHub syncs ONLY code +
  this file; data (`data/ demo/ experiments/`, gitignored) moves separately. **The RunPod volume `DISC` is the master data store** (S3: volume
  `c9sz3m72ye`, EU-RO-1, no pod needed). Mac <- volume: `sync_from_pod.sh` (pod up) or S3. Run:ai <- volume: S3 download INSIDE the workspace
  (key put in temporarily, deleted after; recipe in the 2026-10-24 entry). Run:ai has NO Claude inside: it is driven from the Mac's Claude via
  `runai workspace exec` (VPN on), and the Mac session writes the notes. Small results come back by `exec ... base64`.
- **KEEP REPLIES SHORT (Tal, 2026-10-22):** save words. Give the essentials in a few lines (status, result, what is next) and leave out
  background, repeated context and how you got there. A reply does not have to be very short, just not wordy.
- **SHOWING IMAGES (Tal, 2026-10-20): send them with the `SendUserFile` tool (`display: "render"`), one call per image, with a
  caption saying what the image is** (arm / run, key numbers). Markdown `![](path)` and plain file links do NOT render for Tal
  (VS Code extension) -- he should never have to click a link to see a figure. When comparing, send new and old side by side.
- **OBSIDIAN FROM A POD (Tal, 2026-10-20):** write the note to `workspace_meta/obsidian_inbox/` and COPY its figures next to it
  (embedded `![[file.png]]`), then commit + push. Never only pod paths: the Mac cannot open them (`demo/`, `data/` are gitignored).
  On the Mac, Claude moves the note + images into `~/Documents/DISC` and empties the inbox.
- **SESSION START / END = THE TWO REPO SKILLS (Tal, 2026-10-21):** `/start-work` and `/end-work`
  (`.claude/skills/{start-work,end-work}/SKILL.md`, in git, same steps on the Mac and on a pod). Tal points to them instead of listing the
  steps. A pod needs a one-time link because Tal starts Claude from `/workspace` (done by `/start-work` itself, or by hand:
  `mkdir -p /workspace/.claude && ln -s /workspace/disc/.claude/skills /workspace/.claude/skills`). If the command is not listed, read the
  SKILL.md file and follow it.
- **OBSIDIAN NOTE STYLE (Tal, 2026-10-21): SHORT BULLETS + THE FIGURES, little prose.** Sections Goal / per-test (one or two bullets +
  its figure) / Conclusions / Next. Results as figures whenever there are any. Hebrew in the vault (the Mac's Claude translates inbox notes).
- **Don't use opaque step labels** ("A1/A2/A3"). Name the script or describe
  the step in a few words.
- **Don't hesitate on tool permission prompts** — Tal approves every one.
  Run scripts/experiments directly; narrate what a long run is doing.
- **Keep new outputs separate from old dumps** — phase-2 *inputs* live in
  `demo/guitar/phase2/`; phase-2 *outputs* live in
  `experiments/guitar/<run_name>/` (+ `demo/guitar/bsb_<run_name>/` for
  analysis renders). Never let scripts silently default `--save_dir` etc.
  into a shared folder — every `analysis/*.py` script requires it explicitly.
- **He pushes back on unproven claims and has been right to** (fine-segment
  masks existed in spirit before being built; "lower coverage isn't
  necessarily worse" — the traced-pixel renders, not coverage alone, are
  what settled that; most recently, the `--balance_weight` sweep raised
  coverage but Tal's visual review found it qualitatively worse). Measure
  before concluding, and don't treat one raw metric as the whole story.
- **When archiving/consolidating docs, keep old material in an organized
  location, not just deleted** (this file's own archive is the precedent —
  `/workspace/archive/`).
- **Before deleting or moving anything nontrivial, propose it and wait for
  a go-ahead** — even when the cleanup logic seems obviously safe/reusable
  from a prior precedent. Tal wants to see the specific list first.
- **A run's own evaluation goes in that run's folder** (Tal, 2026-08-31):
  `demo/guitar/bsb_<run_name>/eval/`, not the shared `demo/guitar/eval_labels/` dump. The shared
  directory is for cross-run comparisons Tal asks for explicitly. Default question for a new run is
  "how does it compare to the baseline", so build that comparison into the run's folder without
  being asked -- and compare against **both** current baselines (T=0.01 and its protected T=1
  companion), since a win against only the weaker one is not a win.
- **Give Tal absolute paths** (`/workspace/bsb/demo/...`), not relative markdown links -- he works
  through VS Code and relative links do not open on his side (2026-08-31).
- **SendUserFile upload FAILS (400) for a ~3.7 MB PNG** (2026-09-28): send a downscaled `_view.jpg` copy instead.
- **PRESENTING A RESULT MEANS SHOWING THE IMAGE, NOT A PATH TO IT** (Tal, 2026-09-08: *"אם כבר
  מציגים תוצאות אז במקום path.png פשוט להציג"*). Every figure named in an answer gets sent into the
  conversation itself -- `SendUserFile`, `display: "render"`, one call per figure -- with a short
  "what this shows / what to look for" paragraph as normal message text directly above it, then the
  next paragraph, then the next image. A bare `.../figure.png` line is not a presented result, and
  neither is a link to a page he has to open elsewhere (an Artifact was tried on 2026-09-08 and
  rejected: *"פעם הבאה תציג לי אותן פה פשוט עשינו את זה כל יום כמעט"*). Looking at figures is the
  most frequent action in this project, so anything between him and the picture is friction. Still
  give the absolute path alongside the image, per the rule above -- it is how he opens the file in
  VS Code, it is just not a substitute for showing it.
  **`Read` ON A PNG IS NOT SHOWING IT (learned the hard way 2026-09-12).** `Read` renders the image
  for the ASSISTANT only; in Tal's VS Code extension every tool call collapses into an expandable
  summary row, so all he sees is the path -- which is exactly the failure this rule already forbids
  (*"עד היום הצלחת להציג לי פה את התמונות אבל משום מה היום זה רק מראה path"*). Use `SendUserFile`
  with `display: "render"`. `Read` stays useful for the assistant to LOOK at a figure before
  describing it; it just never counts as presenting it.
- **LVIS EXAMPLE FIGURE = THE v2 LAYOUT (Tal approved 2026-10-05: "save these settings, this is how we do it from now on").** Built by
  `scripts/make_lvis_arm_summary.sh` (-> `analysis/render_lvis_markers_2d.py` + `analysis/make_lvis_summary_figure.py`). Do not change without asking:
  - Top row: crop + GT points | coloured mesh (the colour key; its title on the SAME line as its neighbours) | OURS back-proj (soft-snap) | SHIC back-proj | error table.
  - Table: per-point errors, then ONE "mean error" row with ours AND SHIC under their columns (green = ours closer, red = SHIC). No "context" block, no argmax line (we work with soft-snap).
  - Bottom row: FOUR mesh views chosen per instance for marker visibility; markers = real 3D spheres (GT 0.04, predictions 0.85x), point number on each;
    a sphere hidden by the animal is drawn FADED (alpha 0.38). The marker legend sits at the bottom right, beside the mesh row, with ROUND swatches.
  - Rejected on the way: 3D digit geometry (unreadable), flat 2D discs + dashed rings (front/behind unclear), geodesic label->prediction tubes (clutter), 3 views, ellipse swatches.
- **CROWDING-STUDY FIGURE LAYOUT (Tal approved 2026-10-13, pod 46: "this is how I want to see the rest of the research"):** column 0 = the ORIGINAL training-metric
  paths (no features), then one column per variant; row 1 on the photo, row 2 on the feature PCA, row 3 = cos-similarity heatmap of C and of each neighbour.
  `analysis/plot_2d_feature_geodesic_paths.py --similarity_row`. Send it with `SendUserFile` (load it via ToolSearch if it is not in the tool list), never a bare link.
- **Comparison figures: ONE LONG ROW PER ARM, arms stacked one above the other** -- Tal's phrasing
  when the three ZS arms were compared (2026-09-08), and he confirmed it reads well. Same query in
  the same column all the way down is what makes arms comparable at a glance; a per-arm 2xN grid
  stacked N times is not. `analysis/feature_similarity_heatmap.py --grid_rows 1` produces the strip
  (default stays 2), `analysis/stack_images_nway.py` stacks any number of arms.
- **Name runs by what differs from the default (Tal, 2026-09-10)** -- `fuse16` and `truediag2d` are defaults and are
  not written in demo run names; non-defaults (`fuse32`, `mu0.75`, `anchor...`, `cycv2...`) are.
- **New arms get the SMALL analysis by default (Tal, 2026-09-10)** -- back-projection, PCA, sim heatmap, coverage,
  eval; no mesh renders, no step progression unless asked.
- **Long queues must survive the laptop closing** (Tal leaves with the pod running): launch them detached,
  `setsid nohup <script> >> /workspace/logs/<name>.log 2>&1 < /dev/null &`, not as a session background task.
- **BE CONCISE (Tal, 2026-09-02; reinforced 2026-09-04, 2026-09-07, and TWICE on 2026-09-10 -- "נסה לענות בלי הרבה מלל", "תוכל לקצר קצת את המלל זה הרבה לקרוא" -- so the bar is shorter than
  what was being written even after this rule existed. Lead with the table/number/path; cut framing,
  caveats and interpretation unless asked).** Keep answers short and dense — the conclusion, the numbers,
  the path. No restating the question, no listing options that were not taken, no narrating what
  is about to be run. Tal will ask for expansion where he wants it. Same rule applies to entries
  written into this file.
- ~~REPLY IN HEBREW (Tal, 2026-09-15)~~ ~~REVERSED 2026-09-15 to English~~ **2026-09-16: REPLY IN HEBREW again, and SHORTER** ("תקצר קצת במלל ותרשום בעברית"). Paths/flags/numbers stay as-is. Entries written INTO this file stay in English. **2026-10-04: Tal asked TWICE to have a Hebrew technical answer rewritten in English** -> explanations/results in English, short chat lines in Hebrew, and still SHORT ("תרשום קצת יותר בקצרה"). **2026-10-12 (pod 45): Tal asked to have the English pod-opening summary rewritten in Hebrew ("תרשום בעברית") -> the opening summary and chat replies in HEBREW.** **2026-10-13 (pod 46): Tal asked to have the HEBREW pod-opening summary rewritten in English ("תרשום באנגלית") -> opening summary in ENGLISH (it is technical content); only short chat lines in Hebrew.** **Later the same pod: "אפשר לחזור לעברית" -> back to HEBREW for the rest of the session (tables/paths/flags as-is). He switches per session; follow the latest request, do not argue from older ones.**
- **BEFORE A BIG RUN, ASK WHICH INSTANCES GET FIGURES (Tal, 2026-10-08):** an eval / batch deletes each run dir after scoring, so figures later = retraining (~8.5 min each). Ask once before launch every how many instances (or which) to keep the run dir + build the figures; say the disk cost (~2.2 GB per kept run).
- **SEGMENT MERGE 1.5% ON EVERY RUN (Tal, 2026-10-07):** `--merge_below_frac 0.015` / `MERGE=0.015`, see the 2026-10-07 entry.
- **SHORTER AGAIN (Tal, 2026-10-06, asked 3 times in one day):** one headline line + one small table + the path. No hypotheses, method notes or interpretation unless asked.
- **SHORTER STILL (Tal, 2026-09-15: "קשה לי לקרוא כל כך הרבה")** — a result = 3-4 bullet lines + one small table. No paragraphs of interpretation.
- **"Smooth" back-projection is Tal's VISUAL judgement, not a metric (2026-09-15).** Show the images and let him judge; do not build long automatic chains he did not ask for — he wants to drive the ablation one step at a time.
- ~~Every arm in the squash-smoothness direction: compare vs MAIN AND squash~~ **REPLACED 2026-09-16: compare every new arm vs MAIN (T=0.01) only. Squash is a bug, not a reference.**
- **NEVER `pkill -f <pattern>`** (2026-09-29): it killed the assistant's own shell and missed the run -> two copies of a run wrote to one dir. Kill by PID.
- `setsid nohup ... &` -> `$!` is the setsid wrapper, NOT the run; get the run PID with `ps -eo pid,args | grep [r]un_...`.
- **WATCHER BUG (2026-09-29):** `pgrep -f run_shicbear_mu_lora.sh` inside a watcher matches the WATCHER's own command line -> it never exits.
  Watch the run's PID (`$!` after launch) or the log's DONE marker instead.
- **WATCH EVERY LAUNCHED RUN AND REPORT UNPROMPTED (Tal, 2026-09-15: "אתה אמור לדעת שזה מסיים ולא לחכות שאשאל").**
  Right after a detached launch, start a completion watcher on the log (DONE marker or process exit, plus failure
  patterns) and present results as soon as it fires.
- **POD OPENING = READ, SUMMARIZE IN 3-4 LINES, ASK. RUN NOTHING (Tal, 2026-10-09: "all we wanted was that you go over the project notes, usually half a minute").**
  No env/import timings, no queue, no code reading before he says what to continue with.
- **A LONG RUN MUST NOT DEPEND ON THE ASSISTANT'S SESSION (Tal, 2026-10-11: "why did you not rerun it when it got stuck?"):** start a detached supervisor
  on the pod that restarts it if it dies or hangs (see the 2026-10-11 entry); a watcher inside the chat session dies with the session.
- **ANSWER FIRST, THEN WAIT (Tal, 2026-10-11: "why does it take you so long to respond?"):** never block the chat on a multi-minute test; reply, run it in the background.
- **ONLY TAL CLOSES THE POD.** At the end, update this file and say it is ready; never shut anything down.
- **ASK BEFORE IMPLEMENTING WHEN TERMS ARE AMBIGUOUS.** Tal wants to confirm shared understanding first (e.g. the
  five RKD variants, 2026-09-15) — restate precisely, map to code/flags, wait for his go.
- **Analysis order per run: step progression first, gate, then the rest.**
  After training a new encoder, run ONLY step progression first — never the
  full battery automatically — and wait for Tal's visual review of
  `step_progression_grid.png` before running `full_analyze`/PCA
  compare/similarity heatmap. Same "measure before concluding" discipline as
  everywhere else. See "Standard analysis suite per run" below for the exact
  tools/args at each stage.

---

## Standard analysis suite per run, adopted 2026-08-18

Two-stage, **gated** — do not run stage 2 without Tal's go-ahead on stage 1's
renders, per "How Tal wants the assistant to work" above.

**Stage 1, always immediately after training**: step progression only
(mirror the `run_<run_name>_analysis.sh` pattern, e.g.
`scripts/run_relational_geodesic_mu3dscale1_frontcenteredinit_newmask_analysis.sh`)
→ `demo/guitar/bsb_<run_name>/step_progression_grid.png`. **Stop here and
wait for Tal's visual review** before continuing to stage 2.

**Stage 2, only once Tal says to continue**:
1. `full_analyze` (mirror the `run_<run_name>_full_analyze.sh` pattern) →
   `demo/guitar/bsb_<run_name>/analyze/`. **Always explicitly report the
   soft-snap vertex coverage number in the reply, not just leave it in the
   log** (Tal's explicit ask, 2026-08-18) — `X/4036 vertices (Y%)`, the last
   "vertex coverage" line the `color_mesh_from_soft_mapping.py` step prints
   (soft-snap k=1). Worth reporting the three `pixel_to_vertex_nn.py`
   top-k=1/10/100 coverage numbers alongside it too (also printed during
   this stage) for the fuller picture, same as this file's own historical
   coverage tables above.
   **Thinned 2026-08-18, Tal's call**: the back-projection step only runs
   `color_image_from_knn.py` at k=1 (+ the separate soft-snap k=1 call) —
   the k=10/k=100 side-by-side back-projections were redundant on top of
   those two and got dropped from both existing `run_*_full_analyze.sh`
   scripts. (The unrelated `color_mesh_from_knn.py` k=1/10/100 *mesh*
   colorings earlier in the same script are untouched — only the
   back-projection loop was thinned.) Apply the same thinning to any *new*
   `full_analyze` script written from now on, not just these two.
2. `analysis/pca_feature_compare.py --display both` (shared basis, default)
   → `demo/guitar/features_analyze/<tag>/pca/`.
3. `analysis/feature_similarity_heatmap.py` with a **fixed 4+4 query set**,
   same every run for cross-run comparability (same philosophy as the
   `explicit9` tracked-pixel set above):
   - `--query_pixels 151 94 571 206 820 360 820 740` (headstock, left horn,
     belly-left, belly-right — the last two specifically chosen as a
     symmetry-ambiguity probe, see the 2026-08-18 belly-point findings).
   - `--query_vertices 2760 642 1545 1527` (horn, neck, belly-left,
     belly-right — mirror regions of the pixel queries above, though NOT
     coupled to them — image and mesh queries are independent, no
     pixel<->vertex correspondence implied).
   → `demo/guitar/features_analyze/<tag>/sim_heatmap/simheatmap_grid.png`.

`<tag>` = which encoder/checkpoint is being analyzed (e.g.
`encoder_dino_frontcentered_phase1`,
`encoder_dino_relational_geodesic_mu3dscale1_frontcenteredinit_newmask_phase2`)
— the folder name carries the provenance now, not the filenames (2026-08-18
convention; see `pca_feature_compare.py`/`feature_similarity_heatmap.py`'s
own `path_provenance_tag` usage in `modules/utils.py`).

**Known fixed bug (2026-08-18)**: every `run_*_analysis.sh` step-progression
script's step0 `render_colored_mesh.py` call was missing
`--click_markers_path` (the batched call for steps 25-300 had it, step0's
didn't) — step0 rendered with no colored sphere markers and looked
unrelated to the other steps as a result. Fixed in both
`run_relational_geodesic_mu3dscale1_frontcenteredinit_newmask_analysis.sh`
and its `_resamplecenters` counterpart, and both runs' `step0` re-rendered +
`step_progression_grid.png` rebuilt. Any OTHER still-uninspected
`run_*_analysis.sh` script likely has the same bug — check before trusting
its step0 panel.

---

## Analysis pipeline (current state)

Scripts in `bsb/analysis/`, take `--mask_path` (a SAM mask `.pth`) and
`--save_dir` (both `required=True`, no default, since 2026-08-07 — silent
defaults into a shared folder is exactly what caused a past mess). Run in
this order:

1. **`pixel_coloring.py`** — color every masked pixel. `--mode {pca,position}`:
   `pca` = DINO feature → PCA(3) → RGB; `position` = row/col → R/G (DPC-style
   sanity check independent of learned features).
2. **`pixel_to_vertex_nn.py`** — per masked pixel, cosine similarity against
   every vertex's DINO feature, `top_k=100` by default. `--vertex_features_path`
   is required (no default) — which encoder a run used is never silently picked.
3. **`color_mesh_from_knn.py`** — paint per-pixel colors onto each pixel's
   top-K vertices, similarity-weighted where multiple pixels land on one
   vertex. `--color_mode {pca,position}`. `--use_softmax` exists but was
   measured to have ~no visible effect with `--color_mode position` — left
   off by default.
4. **`color_image_from_knn.py`** — inverse direction: color the mesh first
   (via `mesh_coloring.py`, image-independent), pull colors back onto the
   photo through the same correspondence. `--k` default 1 (sharp/flat); this
   is SHIC's Fig. 6 diagnostic (good correspondence carries a checkerboard
   over as coherent patches).
5. **`mesh_coloring.py`** — image-independent per-vertex coloring, no
   mask/correspondence needed. `--mode {position,pca,checker}`; `checker`
   (cubic-cell checkerboard, maximin-separated palette) is most useful for
   spotting boundary errors. Outputs → `demo/guitar/colored_mesh/`.
6. **`render_colored_mesh.py`** — renders a `.ply` from 3 angles + optional
   side-by-side against a source image. **Slow** (>120s first render, kaolin
   JIT) — always background it. Renders a `.ply`'s own geometry if its vertex
   count doesn't match `--obj_path`. Batch mode (`--ply_paths`/`--save_dirs`,
   comma-separated) builds the mesh/renderer once and loops — use it whenever
   rendering more than one `.ply` (e.g. a full step-progression sweep), it's
   the dominant cost otherwise.
7. **`color_mesh_from_soft_mapping.py`** — geometric nearest-vertex snap
   (not feature-KNN) per masked pixel; prints `vertex coverage: X/N`, the
   metric used throughout this file for cross-run comparison.

Baseline coverage (authors' demo features, not our retrain): 7%/15%/31% at
k=1/10/100, monotonic, deterministic on rerun.

---

## Background / problem framing

- DPC (prior work) was full-to-full shape correspondence. Here it's
  **partial** (a shape doesn't always have a matching image region) — so we
  start with **image → shape**, not shape → image.
- Working assumption: every pixel has *some* corresponding vertex, but
  several pixels may map to the same area, or have no real correspondence.
- Not doing anything at the SEGMENT level for now — SAM is only used for the
  object mask.
- Direction: object features → shape, **soft** decision matching a pixel to
  a *point* on the surface, not necessarily a mesh vertex.
- Optimization is per-shape, not a shared model across shapes.

**Key references:**
- **BSB** (baseline): https://github.com/threedle/bsb
- **SHIC** (Shtedritski/Rupprecht/Vedaldi): https://arxiv.org/abs/2407.18907
  — canonical surface mappings via template-render matching + DINO features,
  worth studying for how they get the *dense* part out of pretrained
  features.
- **Surface-Aware Distilled 3D Semantic Features** (Uzolas/Eisemann/
  Kellnhofer): https://lukas.uzolas.com/SurfaceAware3DFeatures/ — contrastive
  loss disambiguating features far apart on the surface; study for **how
  they fine-tune pretrained features**, compare against `encoder.py`/
  `modules/dino.py`.
- **Relational Knowledge Distillation** (Park et al., CVPR 2019) — the
  formalization behind the current relational_loss recipe: pixels close in
  the photo should map proportionally-close on the mesh, not just closer-
  than-a-threshold. See `modules/relational_loss.py`'s own docstring for the
  full math this project adapted from it (geodesic variant, SHIC-inspired
  normalization).

---

## Git workflow (`/workspace/bsb`)

- `main` = clean, bug-fixed baseline, tag `baseline-fixed` → `a41ce01`.
- `analysis` branch (from that commit) = all our work. `git diff
  baseline-fixed` from `analysis` shows everything added.
- `origin` = upstream `threedle/bsb`, read-only. `github` = personal fork,
  push-able.
- Git identity set **locally** (`.git/config`, persists), not `--global`
  (`~/.gitconfig` is on ephemeral `/root`): `tberger <talberger3@gmail.com>`.
- **2026-09-15: the whole 09-05 → 09-15 backlog was committed and pushed at Tal's request** —
  `d83ec9b`, then the loss-name refactor `16e5b3d` at pod close, both on `analysis` and pushed to
  `github/analysis`; working tree clean. Tal commits
  at END OF DAY, when he asks; don't push on it otherwise.

---

## Experiment / analysis plan (from advisor)

- [x] Exp 0 — sanity check: BSB demo runs.
- [x] Exp 1 — retrain DINO shape encoder for a feature-per-vertex; confirmed
      predicted point changes (fixed a `dataset.py` bug in the process).
- [ ] Exp 2 — segmentor demo with existing SAM checkpoint. Likely
      incidentally covered, not separately confirmed, not blocking.
- [ ] Exp 3 — confirm BSB lands on the correct surface point. Maybe implicit
      in Exp 1, not explicitly confirmed.
- [x] Pixel coloring, Pixel→vertex NN, Mesh coloring — all built and
      verified, see "Analysis pipeline" above.

---

## Other files in this workspace

- `/workspace/archive/pre-consolidation-2026-08-07/` — the three original
  docs the 2026-08-07 consolidation replaced, verbatim.
- `/workspace/archive/pre-consolidation-2026-08-16/PROJECT_NOTES_full_2026-08-16.md`
  — this file's own full pre-trim history (2026-07-26 through 2026-08-15 in
  complete detail: mapping_loss/Phase-2 full spec, relational_loss collapse
  postmortem, every dated status entry, the demo/guitar/bsb/ reorg
  narrative, the old changelog). Go here for anything trimmed above.
- `/workspace/bsb/debug.md` — deep-dive debug log (Hebrew) for the Exp 1
  `'sam_f'`-hardcoding bug. Stale, fix is applied and confirmed.
- `/workspace/bsb/changes_summary.txt` — concise English summary of BSB code
  changes made so far.
- `/workspace/decks/phase2_training_diagram.pptx` — 2-slide explainer deck (block
  diagram + loss mechanics), generator `bsb/phase2/make_phase2_deck.py`.
- `/workspace/decks/phase2_relational_training_diagram.pptx` — relational/geodesic loss
  deck, generator `bsb/phase2/make_phase2_relational_deck.py`.
- `/workspace/decks/phase2_cycle_consistency_diagram.pptx` (+ same-name PNGs, 2026-08-16) —
  cycle-consistency loss deck (hard-snap vs. `--cyc_soft`, both PARKED), generator
  `bsb/phase2/make_phase2_cycle_consistency_deck.py`. Same plain-style convention as the
  other two decks above. **v2, same day, Tal's call**:
  `phase2_cycle_consistency_diagram_bsb_terms.pptx` (+ PNGs, generator
  `bsb/phase2/make_phase2_cycle_consistency_deck_v2.py`) — same content, re-labeled with
  `best_segmentation_buddies.py`'s own vocabulary (forward match / backward match /
  reciprocity score) instead of SHIC's `p(a|b)` notation, which Tal found confusing.
  **Revised twice more same day, Tal's calls, filename unchanged throughout**: (1) no
  BSB/PARKED mentions or red callouts in the slides themselves, "buddy" renamed to
  "reciprocity", verdict/red text removed; (2) deck narrowed to the SOFT (`--cyc_soft`)
  variant ONLY -- the HARD-SNAP branch/comparison was dropped entirely (Tal: we already
  confirmed HARD-SNAP is the one that deviates from SHIC, not worth keeping in the deck),
  and "reciprocity" itself renamed again to "round-trip weight" (still found "reciprocity"
  unfamiliar). Slide 2 now shows the `--cyc_soft` `cyc_weight` sweep (0.01 vs 0.3) alone,
  no hard-vs-soft table. (3) Slide 1's boxes lead with compact formulas
  (`fwd(u,j)`/`bwd(j,v)`/`weight(u,v)`/`geo(u,v)`) instead of full sentences, per Tal's
  request -- less prose, notation does the work. (4) Tal flagged the FORWARD->BACKWARD MATCH
  handoff as unclear (what flows through the arrow? what is `vertex_c`?) -- fixed by using
  the SAME variable `j` in both boxes (was `j` then `c`) plus an explicit connecting label
  and "for each candidate vertex j found above:" in the BACKWARD MATCH box. Also dropped the
  separate `geo(u,v)` box entirely -- it's now just a small caption next to the final loss
  box, per Tal's call ("just leave the mention of using it at the end"). Prefer this version
  going forward.
- `/workspace/decks/phase2_balance_diagram.pptx` (+ same-name PNGs, 2026-08-16) —
  vertex-balance loss deck (`--balance_weight`), generator
  `bsb/phase2/make_phase2_balance_deck.py`. Same plain-style convention. **Revised same
  day** to match the cycle-consistency deck's final style, Tal's explicit request: diagram
  boxes lead with formulas instead of prose, no PARKED language, no red
  callouts/verdict box, external paper citations (Switch Transformer/SwAV) trimmed out of
  the slides themselves. Same filename throughout.

