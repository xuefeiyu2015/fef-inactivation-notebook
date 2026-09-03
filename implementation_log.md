# Implementation log

## 2026-09-03 — Initial version: converter + student Colab notebook

Created the project from scratch (the folder was empty).

### Added

- **`convert-mat-to-npz.py`** — one-time local converter. Reads the three
  sessions with `scipy.io.loadmat` and writes `np.savez_compressed` `.npz` files
  into `Data/FEF_Inactivation_OHLab/colab_npz/`. Measured: 131 MB → 23.8 MB,
  103 MB → 18.2 MB, 36 MB → 6.1 MB; an `.npz` reloads in about 0.1 s.

  Eye traces are stored as NaN-padded `(trials, samples)` arrays plus
  `eye_n_samples`, rather than pre-aligned, so the notebook can still teach
  alignment. The NaN padding costs almost nothing once compressed.

  The converter resolves the two shape traps of the old format — the leading unit
  dimension of `SpikeTimeData`, and the trial-number column in
  `TargetLoc` / `TargetPolarLoc` — so the student never meets them.

- **`fef-inactivation-colab.ipynb`** — 82 cells (43 markdown, 39 code) covering
  the experiment, loading, the variables, event codes, eye-trace alignment,
  saccade detection, the saccade parameters, spike rasters/PSTHs, and 14
  exploration questions with starter stubs.

- **`README.md`** — setup instructions and the verification table.

### Decisions

- Written for a student new to Python: plain functions, explicit `for` loops, no
  classes, and only libraries Colab ships with (numpy, scipy, matplotlib,
  pandas). `compute_*` functions stay pure and `plot_*` functions only draw what
  they are handed.
- `pandas` is used solely to print summary tables, never to carry the analysis,
  so the student only has to learn one data structure (the numpy array).
- The detector's per-trial results are returned as a dictionary of numpy arrays
  rather than a DataFrame or an object, for the same reason.

### Problems found and fixed

- **`savgol_filter` crashes on NaN.** MATLAB's `smoothdata(..., 'omitnan')`
  tolerates missing samples; scipy raises
  `ValueError: array must not contain infs or NaNs`. Aligned eye traces carry NaN
  wherever the window runs past the end of the recording (16 trials in 102325,
  4 in 110725), so `Adams110725_FRAC` failed outright. Added `smooth_trace()`,
  which smooths only the contiguous real span and returns NaN for a trial with a
  gap in the middle. Costs one trial versus MATLAB (1716 vs 1717 detected).

- **Phase labels drawn before the data.** `plot_session_course` read
  `ax.get_ylim()` before plotting, so the labels landed at the bottom of the
  figure. Reordered to draw the data first, then add headroom and place the
  labels inside the top of the axes; legend moved to `loc="best"` so it does not
  collide with them.

### Corrections to `Program_Matlab_Local/Temp/CLAUDE.md`

Both verified by direct measurement; that doc has not been updated.

1. `Adams110725FEFInactivation_FRAC.mat` is **not** a re-saved copy of the 102325
   recording, as its final section claims. It now differs in trial count
   (1337 vs 1740), target geometry (15° horizontal vs 20° diagonal), hemifield
   codes (80/81 vs 102/105), spike count (135,670 vs 47,659) and internal
   `FileName`. The doc describes an older export of that file.
2. The known-good firing rates (15.7 / 7.2 / 10.0 spikes/s) are **go-cue-aligned**,
   though the prose says firing-rate windows are target-onset-aligned. The
   target-onset `[-200, 0]` window gives 5.2 / 3.4 / 3.6 spikes/s instead. Both
   figures were reproduced exactly in Python.

### Verification

- All three sessions execute top to bottom under
  `jupyter nbconvert --execute` with zero errors. `Adams110725_OneDR` has only
  two injection phases and produces a two-phase table without special-casing.
- Detector output regression-checked against MATLAB on `Adams102325_FRAC`:
  RT leftward 98/102/104 ms and peak velocity leftward 1489/1431/1425 deg/s match
  exactly; RT rightward 116/150/112 vs 116/152/114 and peak velocity rightward
  1480/1379/949 vs 1480/1379/951 differ only through the one-trial NaN
  difference above.
- Every figure inspected visually. The detection-check figure puts onset and
  offset markers exactly on the position step and speed peak.

### Open item

`DATA_URLS` in the notebook still holds `PASTE_LINK_HERE` placeholders; the three
`.npz` files need hosting and their links pasting in. Until then the notebook
runs via `USE_LOCAL_FILE = True`.

## 2026-09-03 — Published to GitHub with a Colab badge

### Added

- **`.gitignore`** — excludes `*.npz` and `*.mat`, so the data stays out of git
  history and a clone stays at ~120 KB.
- Repository published at
  [`xuefeiyu2015/fef-inactivation-notebook`](https://github.com/xuefeiyu2015/fef-inactivation-notebook)
  (public), with an **Open in Colab** badge at the top of the README.
- The three `.npz` files attached to the **`data-v1`** release rather than
  committed. The notebook's `DATA_URLS` now points at those release assets and is
  pre-filled, so the student has nothing to configure.

### Changed

- **Download is now pure Python** (`urllib.request.urlretrieve`) instead of
  `!wget`. `wget` is not installed on stock macOS or Windows, and the `!` shell
  magic only works inside a notebook — `urlretrieve` works everywhere and reads
  more plainly for a beginner. The unused Google Drive / `gdown` branch was
  dropped along with it.
- **`convert-mat-to-npz.py` no longer hardcodes a home-directory path.** It reads
  `FEF_DATA_DIR` from the environment, defaulting to `./FEF_Inactivation_OHLab`,
  so no personal path is published in a public repo.

### Note on the repository

`/Users/xuefeiyu` is itself a git repository (branch `main`, no remote, no
`.gitignore`, 0 tracked files). This project was given its **own** repository
inside `SurfinInactivationScript/` rather than being committed to that one — a
`git add -A` from the home folder would stage `.ssh/`, `.claude.json` and the
whole Library. The home repo was left untouched.

### Verification

- All three release URLs return HTTP 200 and the downloaded `.npz` loads in numpy.
- The published notebook was executed **unmodified, in an empty directory**,
  exactly as a student receives it: it downloaded the data from the release and
  ran all 82 cells with 0 errors and 11 figures in 28 seconds, reproducing
  1716/1740 saccades detected and the expected RT table.

## 2026-09-03 — Every exploration question now answers with a figure

Requested change: the questions in section 10 reported results as printed numbers.
Plots show the size of an effect and the spread around it; a printed median hides
both. The notebook went from 11 figures to **31**.

### Added — a small charting toolkit in section 8, reused by every question

- **`compute_bootstrap_ci`** — resamples the trials 1000 times to get a 95% range
  for a median, so every bar carries an honest error bar.
- **`compute_summary_by_phase`** — generalised. It used to hardcode a split by
  saccade direction; it now takes `phases` and `groups` as two lists of
  `(name, mask)` pairs, so the same function splits by phase and direction, phase
  and object value, or early against late trials. Q2 uses that last form.
- **`compute_proportion_by_phase`** — percentages (detection rate, anticipation
  rate) returned in the same row shape, so one plotting function draws either.
- **`plot_summary_by_phase`** — the workhorse grouped bar chart with error bars,
  value labels and trial counts. Most questions are now two lines.
- `DIRECTION_GROUPS`, `VALUE_GROUPS`, `ALL_TRIALS` as ready-made masks.

### Added — per-question figures

| Q | Figure |
|---|---|
| 1 | value-split bars + overlaid RT distributions |
| 2 | early-vs-late bars (reusing `phases` for time blocks) + session course |
| 3 | detection-rate bars |
| 4 | every measure as a percentage of its own "before" value, on one axis |
| 5 | landing-error bars + one endpoint scatter per phase, with spread |
| 6 | anticipation-rate bars |
| 7 | raw main-sequence scatter beside amplitude-binned medians |
| 8 | the two PSTH alignments overlaid, with peak height and latency marked |
| 9 | firing-rate bars + one PSTH per injection phase |
| 10 | firing rate against RT, one panel per phase, with a binned trend line |
| 11 | `analyse_session()` runs the whole pipeline on all three sessions, one panel each |
| 13 | change from "before" to every later phase, with bootstrap ranges |
| 14 | detector-setting sweep: median RT and detection rate against `velocity_threshold` |

`analyse_session` in Q11 is the capstone — it wraps the pipeline the student has
just built step by step into one function, which is also what makes a
three-session comparison possible.

### Problems found and fixed

- **Bar value labels were struck through by their own error bars.** The label was
  drawn at the bar top; it is now drawn above the upper error-bar cap.
- **Legends overlapped the bars.** `plot_summary_by_phase` now adds 30% headroom
  and pins the legend to the upper right.
- **Q13 compared the wrong pair of phases.** It contrasted "before" against the
  last phase only, but the RT effect lives in "before to during" — so the figure
  contradicted the text telling the student what to look for. It now compares
  "before" against every later phase. The result is now unmistakable: rightward
  changes by +35 ms with a 95% range of [26, 46] that clears zero, while leftward
  straddles zero.
- A `%%` in a title with no `%` operator applied would have rendered literally.

### Verification

Executed end to end again: **0 errors, 31 figures**, on a clean run that downloaded
all three sessions from the release. Every figure inspected visually. The section 8
regression numbers are unchanged (1716/1740 detected; RT leftward 98/102/104).

## 2026-09-03 — Restructured section 10 into a project with a stated goal

Requested change: the difficulty-graded "Level 1–4" questions did not read as a
project. Reorganised around one goal and four steps, following the structure and
the analyses already worked out in the MATLAB script.

> **Goal: investigate how reward value shapes the effect of FEF inactivation.**

### New structure

Sections renumbered; the notebook is now 1–12 with the project as section 12.

- **Section 8 trimmed.** It kept the parameter explanations, the detector
  validation (angle error, landing points, main sequence) and the summary toolkit,
  but the *result* figures (RT and peak velocity by phase) moved into the project —
  the student now produces them. The toolkit is demonstrated on **amplitude**
  instead, deliberately: the target never moved, so amplitude is a control, and
  seeing what "no effect" looks like is how you learn to recognise a real one.
- **Section 9 (new) — more behavioural measures**, ported from the MATLAB:
  - `compute_endpoint_errors` — signed **radial** (+ past target / − undershoot)
    and **tangential** error in a per-trial target-centred frame, rather than a
    plain distance, which cannot cancel and hides which way the eye missed
  - `compute_endpoint_scatter` — 2-D standard distance, a group property, so
    accuracy and precision stay separate measures
  - `compute_gaze_hold` — port of `GazeOnTarget_Old.m`, with censoring and the
    at-ceiling check, plus the ceiling-immune `held_to_offset` binary
  - everything assembled into `behaviour` and `valid_for` dictionaries
- **Section 11 (new) — statistics**: `compare_two_groups` (Mann-Whitney, chosen
  because RT is not bell-shaped), `compare_change`, and `compare_interaction`
  (permutation test on the difference of differences).
- **Section 12 — the project**: goal, four steps, a worked template per step,
  `TODO`s for the rest, and a report outline with the known limitations named.

### What the MATLAB script settled

Reading `GazeOnTarget_Old.m` and `LoadAndVisulizeData_Old.m` changed three choices
that would otherwise have been wrong:

- **Gaze window 7°, not 5°.** At 5° only about three quarters of compliant trials
  are captured, and the misses are not random — post-injection saccades land
  further off centre, so a tight window scores an inaccurate-but-compliant hold as
  broken and manufactures a shorter hold exactly where the drug makes saccades
  least accurate. Measured here: 5° gave 97.8% on-target, 7° gives **99.7%**.
- **Radial/tangential error rather than absolute distance.**
- **Split the longest phase in half** (`compute_phase_blocks`), since the drug
  keeps changing inside a 1120-trial "after" phase.

### Problems found and fixed

- **The gaze window must be aligned separately, and long.** The hold is ~824 ms and
  starts ~150 ms after the GO cue, while the RT window ends at +600 ms — measured
  there, **96.2% of holds are censored**. Re-aligned at +1800 ms: 0.1% censored.
- **Extending the shared window broke saccade detection** (1716 → 1554), because a
  longer window catches later blinks and `smooth_trace` discards any trace with a
  mid-gap. Fixed by decoupling: detection keeps the ±600 ms *smoothed* product,
  gaze uses a separate long *raw* product — it only asks "is the eye near the
  target", which needs no smoothing.
- **The permutation test reported `p = 0`.** No permutation test can show that;
  with 2000 shuffles the smallest honest value is 1/2001. Now uses (count+1)/(n+1)
  and prints `p < 0.001`.
- **Ambiguous sign in comparison output.** "good 858, bad 728, difference −130"
  invites the wrong reading. Now prints "difference (bad object minus good object)".
- **Step 3's guidance presupposed a result the data contradicts.** The text said
  the effect "should be absent" on the intact side. It is not: on this session the
  value×phase interaction is *stronger* on the intact side (p < 0.001, −46 ms) than
  on the affected side (p = 0.031, −20 ms). Rewritten so the control is run and
  read **first**, with an explicit outcome for "both sides show it — this is a
  session effect, not an inactivation effect, and saying so is the result."

### Verification

Executed end to end: **0 errors, 16 figures** (fewer by design — the student now
produces the rest). Detector numbers unchanged (1716/1740). Gaze: 99.7% on target,
0.1% censored, 5.4% at ceiling, median hold 824 ms.

## 2026-09-03 — Fixed the rank-test worked example

The worked example for `compare_two_groups` compared leftward against rightward
saccades before the injection. That comparison is not meaningful — it contrasts two
different directions rather than anything about the manipulation, and any
difference reflects target geometry, not the drug.

Replaced with **reaction time across the injection phases**, all three pairwise
comparisons:

| Comparison | Median difference | p |
|---|---|---|
| before → during | +20.0 ms | < 0.001 |
| before → after | +3.0 ms | 0.50 |
| during → after | −17.0 ms | < 0.001 |

That tells the real story — RT rises during the injection and returns afterwards —
and gives three teaching points the old example could not:

- **a null result carrying information**: before vs after is "not distinguishable",
  which here means *recovery*, not *nothing found*
- **multiple comparisons**: three phases produce three tests, and a reader cannot
  judge a p-value without knowing how many were run
- **pooling versus splitting**: pooled across directions the change is +20 ms;
  Step 1 splits it into +35 ms on one side and +3.5 ms on the other. What to pool
  is a scientific choice, not a formatting one.

### Also added: why the interaction needs its own test

A Mann-Whitney test compares two samples; an interaction is a question about four,
so no single Mann-Whitney can produce it. Section 11 now spells out the tempting
shortcut and why it is invalid — running the test separately per group and
comparing the verdicts ("p < 0.001 here, p = 0.68 there, therefore they differ")
is a well-known fallacy: +35 ms at p = 0.001 and +30 ms at p = 0.06 are nearly the
same effect with opposite verdicts, decided by group size alone. Mann-Whitney does
every two-group comparison in the project; the permutation test does the
interaction.

### Build fix

An escaped-newline slip put a literal line break inside a string literal, so the
cell failed to parse at run time. `assemble.py` now **compiles every code cell**
before writing the notebook (blanking `!` magic lines first) and refuses to write
if any cell would not parse, so this class of bug cannot reach the notebook again.

### Verification

0 errors, 16 figures, detector numbers unchanged.

## 2026-09-03 — Added the ANOVA route to the interaction; corrected an overstatement

Question raised: why can the interaction not be handled with pairwise comparisons
plus a p-value correction, or with an ANOVA? Tested both empirically rather than
arguing from theory.

### ANOVA — the objection was right

A two-way ANOVA (phase × direction) has an interaction term that tests exactly
this, and on this session all three routes agree:

| Method | Interaction |
|---|---|
| Two-way ANOVA on raw RT | F = 31.7, p < 0.001 |
| ANOVA on ranks | F = 36.5, p < 0.001 |
| Permutation test on medians | +31.5 ms, p = 0.0002 |

The previous wording implied the permutation test was necessary. It is a **choice**.
Section 11 now says so, adds `compare_interaction_anova` (statsmodels, guarded by
try/except and pre-installed on Colab), and runs it alongside the permutation test
so the student sees both agree. The three reasons given for defaulting to the
permutation test are now honest ones:

1. every figure in the notebook plots a **median**; an ANOVA tests **means**, and
   testing one while plotting the other invites a report where the figure and the
   statistic disagree
2. RT fails normality (Shapiro-Wilk p = 4e-07) and the four cells fail equal
   variance (Levene p = 0.025) — with ~150 trials per cell the ANOVA survives this,
   as the agreement above shows, but it has to be *checked*
3. the permutation test reports the effect in **milliseconds**; `F = 31.7` does not
   say whether the extra slowing was 3 ms or 30 ms

### P-value correction — this one does not work, and the reason is specific

A correction addresses a different problem: inflated false positives across a
family of tests. Applied to the two separate per-direction tests it turns
p = 1.2e-18 and p = 0.68 into 2.4e-18 and 1.0 — still two numbers, neither an
estimate of how much *more* one group changed. The failure is not that the
p-values are too generous; it is that the contrast was never computed, and no
correction can produce an estimate of a quantity that was not measured.

### Verification

0 errors, 16 figures. The notebook's ANOVA reports F = 31.7, p < 0.001, matching
the standalone calculation.

## 2026-09-03 — Fixed the y-limits and the smoothing on the session-course plots

Question raised: why is the y-axis on figure 1.1 so large? Two separate bugs, both
real.

### 1. The axis was scaled to the most extreme trial

`plot_session_course` let matplotlib autoscale, so the axis was set by the raw
per-trial scatter. For the firing rate that scatter runs 0–115 spikes/s while the
signal (the smoothed line) lives between 3.6 and 44.8, and the 99th percentile is
70 — so a handful of trials stretched the axis to ~130 and squashed the line into
the bottom third of the figure.

The limits are now taken from the **smoothed lines plus the 1st–99th percentile of
the raw points**, so the line is always fully visible and a few outliers cannot
dominate. The docstring says plainly that a few extreme points may then sit outside
the visible range. Figure 1.1's axis went from 0–130 to 0–85.

### 2. A running median of a firing rate draws a staircase

A rate measured in a 200 ms window can only be 0, 5, 10, 15 ... spikes/s — you
cannot have half a spike. A running median of numbers taking only a few values
snaps to those values: across the whole session the running median produced just
**13 distinct values**, versus 179 for a running mean. The line was a visible
staircase.

Worse, the comment in Step 1.1 already claimed `smooth_method="mean"` was being
used. That parameter did not exist — the advice was carried over from the MATLAB
but never implemented, so the comment described behaviour the code did not have.

`compute_running_median` is now `compute_running_average` with a `method`
argument ("median" by default, "mean" for rates), `plot_session_course` passes it
through, and Step 1.1 actually uses `method="mean"`. The student is invited to
switch it back to "median" once to see the difference.

**This mattered scientifically, not just cosmetically.** With the axis fixed and
the line smoothed, the neuron's response is now visibly dropping from about 22 to
about 5 spikes/s during the injection and partially recovering afterwards — the
Step 1.1 result, which the previous figure hid.

### Verification

0 errors, 16 figures. Both session-course figures inspected and clearly improved.

## 2026-09-03 — Compensation moved into Step 1; Step 3 rebuilt around the value gap

Three corrections, all structural.

### 1. The compensation question belongs to Step 1, not the extension

"Does the deficit shrink while the FEF is inactivated?" is about the inactivation
alone — no reward, no object value — so it is now **Step 1.3**, the closing question
of the first step. The Step 4 extension no longer owns it; it now asks the narrower
question of whether *predictability* would speed compensation up, using the Step 1.3
answer as the baseline to beat.

Two things Step 1.3 has to teach, because both are traps:

- **Measure the deficit, not the raw RT.** Both directions get faster late in this
  session as the monkey anticipates the go cue more, so a falling rightward RT is
  not recovery. The rightward-minus-leftward difference cancels it.
- **Washout and compensation look identical in the behaviour.** The recorded neuron
  is the only handle: if firing recovers in step with behaviour it is washout; if
  behaviour recovers while the neuron is still suppressed it is compensation. The
  figure plots both time courses on twin axes so the *shapes* can be compared.

Measured on this session, the two shapes clearly differ — the neuron recovers
steadily (22.6 → 13.3 → 14.1 → 22.0 spikes/s) while the behavioural deficit bounces
(+18 → +49 → +12 → +42 ms).

### 2. Step 3 rebuilt around the good-minus-bad gap

The old version compared good against bad within each side and then eyeballed the
control. The quantity now tracked throughout is the **value gap**, and the question
is how that gap differs between sides across phases — a three-way interaction, with
the unaffected side inside the measurement rather than bolted on. Anything that
moves the value gap for reasons unrelated to the drug (a progressively less thirsty
monkey caring less about reward size) shifts both sides and cancels.

Split into three sub-steps: **3.1** look at the gaps (per side, per block, plus
their difference), **3.2** test them, **3.3** decompose — did the good trials get
worse or the bad trials get better? 3.3 is where the interpretation lives and is
the part usually skipped.

`compare_three_way_anova` added to section 11. The signed gap is kept rather than
`|gap|`, because on this session one side's gap **flips sign**, which an absolute
value would hide.

The result is genuinely awkward and the text says so: the three-way term is **not**
significant before→during (F = 0.93, p = 0.33) but **is** before→after
(F = 12.21, p < 0.001) — while the basic deficit runs the other way, large during
and gone after. The value effect appears where the inactivation effect has faded,
which points at time in the session rather than the drug.

### 3. Two-dimensional endpoint maps

2-D plotting was never introduced. Section 9 now has `compute_endpoint_heatmap` /
`plot_endpoint_heatmaps` (ported from `computeEndpointHeatmap`), introduced with
the three things that decide whether such a picture is honest: **percentages not
counts** (the phases have 300 vs 1120 trials, and raw counts would make "before"
look empty), **one shared colour scale**, and **square panels**. Used in the project
as Step 1.2b across the finer blocks.

Also added `plot_measure_panel` — six measures × two directions × four blocks on
one page, which is the compensation summary for Step 1. It shows immediately that
RT's between-direction gap closes while peak velocity's stays open.

### Removed

The closing "Writing it up", "Two habits", "Where to look if something breaks" and
"Credit" sections — this is not a report exercise. The notebook now ends with the
Step 4 extension. Dangling references to a report were cleaned up.

### Verification

0 errors, 20 figures. Section numbering runs 1–12 with Steps 1.1, 1.2, 1.2b, 1.3,
2, 3, 4. Every new figure inspected.

## 2026-09-03 — Step 2 restricted to the baseline

Step 2 was splitting by injection phase as well as object value, which pre-empted
Step 3 and muddled its own purpose. Its job is only to establish **what reward
value does to this monkey's behaviour normally**, so it now uses the
**before-injection trials only**, and says explicitly that everything about the
injection interacting with value belongs to Step 3.

No new machinery was needed. `compute_summary_by_phase` takes any two lists of
`(name, mask)` pairs, so Step 2 hands it **direction** as the first factor and
**object value** as the second, and restricts the whole thing with one line:

```python
baseline = injection_phases[0][1]
valid = valid_for[measure] & baseline
```

Splitting by direction is kept even though both sides are intact here, and it
immediately earns its place: at baseline the gaze-hold value gap is **+283 ms on
the left but only +28 ms on the right**. A value effect that already differs
between the sides before any drug is something Step 3 has to take into account
rather than discover halfway through, so Step 2 now says so.

A new TODO closes the step by asking the student to write down the size of the
baseline value effect for each measure — that list is exactly what Step 3 then asks
whether the injection changed. And a measure with no baseline value effect cannot
show the injection changing that effect, which makes a null here informative rather
than a failure.

### Fixed

`plot_distributions_by_group` was defined inside the old Level-1 question cell and
was lost when that section was replaced, so Step 2 raised `NameError`. It now lives
in the section 8 toolkit with the other plotting helpers, and is listed in the
project's toolkit summary along with `plot_endpoint_heatmaps`.

### Verification

0 errors, 21 figures.

## 2026-09-03 — Made the three-way test agree with the figure above it

Question raised: what is the three-way ANOVA actually doing — are four phases being
tested? No, and the confusion was caused by a genuine inconsistency in the notebook.

**What it does.** Each call is one **2 × 2 × 2** ANOVA. Every trial carries three
labels — phase, side (left/right), object value (good/bad) — and the three-way
interaction term is the quantity of interest:

```
[ gap(right, later) - gap(right, before) ] - [ gap(left, later) - gap(left, before) ]
                                                          where gap = good - bad
```

Two levels per factor is deliberate: it makes that term a single readable number.
Passing four phases at once runs fine and gives F = 7.63, p = 4.6e-05, but a 3-df
omnibus only says "the value gap behaves differently on the two sides *somewhere*"
— not where, and not in which direction. So the baseline block is compared against
each later block in turn.

**The inconsistency.** Figure 3.1 used `phase_blocks` (four blocks, the long
"after" phase split in half) while the test underneath used `injection_phases`
(three phases, pairwise). Reading the figure and then the test, they appeared to be
about different things — because they were. The test now uses `phase_blocks` too,
so the picture and the statistic describe the same comparisons.

**It also improves the result.** Splitting the "after" phase shows the three-way
term growing monotonically rather than as one lump:

| Comparison | F | p |
|---|---|---|
| before vs during | 0.93 | 0.33 |
| before vs after, 1st half | 6.10 | 0.014 |
| before vs after, 2nd half | 16.33 | < 0.001 |

That monotonic rise is much stronger evidence for the interpretation the section
already argues: a quantity that climbs steadily from the first block to the last is
following **time in the session**, because the drug goes up and comes back down.
The guidance now points at the shape of these F values as the decisive clue, and
the output notes that three tests were run, not one.

`compare_three_way_anova`'s docstring now spells out the design, the formula for
what the three-way term measures, and why to keep each factor at two levels.

### Build note

The compile check added earlier caught an escaped-newline slip in this edit before
the notebook was written. It did its job.

### Verification

0 errors, 21 figures.

## 2026-09-03 — Three-way test rebuilt as one model: omnibus plus corrected contrasts

Question raised: why not put all four phases in one ANOVA and use multiple
comparisons to find which phase changed? That is the better design, and the
notebook now does it.

### What was wrong with the previous version

Three separate 2 × 2 × 2 ANOVAs, one per phase pair. Two real problems:

- **No Type I control.** Three independent tests, uncorrected.
- **The noise estimate threw away data.** Each pairwise model estimated its own
  residual variance from only the two blocks involved (df 604–846), rather than
  pooling across the session (df 1700).

### What it does now

One model over all four blocks, then the standard two-stage read:

1. **Omnibus three-way term** (3 df) as the gatekeeper — F = 7.63, p < 0.001.
   `describe_three_way` refuses to print contrasts if it fails, with the line
   "Not significant -- stop here. Do not go fishing in the contrasts."
2. **Per-block contrasts, Holm-corrected**, read straight off the same model.

The one refinement on the suggestion: the post-hoc is **interaction contrasts**,
not Tukey on cell means. With 4 × 2 × 2 = 16 cells, Tukey would return 120 pairwise
comparisons, nearly all irrelevant. Coding the model with the baseline as the
reference level makes the three-way coefficients *already* the three comparisons
of interest, so they are read directly.

**Verified numerically** that each coefficient equals the hand-computed contrast:

| Block | Hand-computed | Model coefficient |
|---|---|---|
| during | +14.4 | +14.4 |
| after, 1st half | +39.1 | +39.1 |
| after, 2nd half | +75.5 | +75.5 |

### Why this is better, beyond correctness

The contrasts come out **in milliseconds**. An F value says something happened; it
never says how big or which way. The output now reads +14.4, +39.1, +75.5 ms, which
shows the monotonic growth directly and is the thing worth quoting.

### It changed a conclusion

Under the old uncorrected pairwise version, "before vs after, 1st half" was
significant at p = 0.014. With the pooled error term and Holm correction it is
p = 0.026 raw, **0.053 corrected — not significant**. Only the last block survives.
The previous version was overstating.

`compare_three_way_anova` is replaced by `compare_three_way` + `describe_three_way`.
Callers must list the **reference level first** in each factor's list, which is
documented and is what makes "gap" mean good minus bad and the side contrast mean
right minus left.

### Verification

0 errors, 21 figures.
