# FEF Inactivation — a Python notebook for exploring monkey eye movements and FEF neurons

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/xuefeiyu2015/fef-inactivation-notebook/blob/main/fef-inactivation-colab.ipynb)

**Click the badge above to open the notebook in Google Colab.** Nothing needs
installing and the data downloads itself — just run the cells from the top.

There is also a **worked-solutions version** with every `TODO` answered:
[![Open Solutions In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/xuefeiyu2015/fef-inactivation-notebook/blob/main/fef-inactivation-colab-SOLUTIONS.ipynb)

A teaching notebook for a real monkey neurophysiology dataset: eye movements and
single-neuron recordings from the **frontal eye field (FEF)**, recorded before,
during and after the FEF was temporarily silenced with muscimol.

It is written for someone new to Python — plain functions, explicit `for` loops,
no classes, and only libraries that Colab already ships with. Results are shown as
plots rather than printed numbers, with bootstrap error bars wherever a comparison
is being made.

## The project

The notebook is a **project**, not a tour. Sections 1–11 build the tools; section 12
is the project the student carries out and writes up.

> **Goal: investigate how reward value shapes the effect of FEF inactivation.**
> Does silencing the FEF damage saccades to a valuable object as much as saccades
> to a worthless one?

| Step | Question |
|---|---|
| 1 | What does the inactivation do at all? The neuron, the behaviour, the 2-D endpoint maps, and whether the deficit **compensates** as the session goes on |
| 2 | Does reward value change the behaviour? |
| 3 | **Does inactivation hurt good and bad objects differently?** Tracked as the good-minus-bad gap on each side, tested as a three-way interaction, then decomposed |
| 4 | Extension (design exercise): what if value were predictable from location? |

Each step gives one measure worked end to end as a template, then `TODO` cells for
the rest. Every measure is computed for the student — they choose what to plot and
what to compare.

## What the notebook covers

1. The experiment and the task
2. Getting and loading the data
3. The main variables, and the traps hiding in them
4. Event codes, and sorting trials into conditions
5. Aligning eye traces to the GO cue
6. **Detecting saccades from the eye trace**, with a visual check
7. The saccade parameters, and validation figures (main sequence, landing points)
8. More behavioural measures: radial/tangential endpoint error, endpoint scatter,
   2-D endpoint density maps, gaze hold on the object, anticipation
9. The neuron: rasters and PSTHs, target-aligned versus saccade-aligned
10. Statistics: group comparison, change, the two-way **interaction** (permutation
    and ANOVA), and a three-way model with an omnibus test plus Holm-corrected
    contrasts
11. The project itself

## The data

Three sessions, published as release assets and downloaded by the notebook
automatically. To analyse a different one, change a single line — `SESSION` —
near the top and re-run.

| Session | Task | Trials | Targets | Injection phases | Size |
|---|---|---|---|---|---|
| `Adams102325_FRAC` | Fractal object directed saccade | 1740 | 20° up-left / down-right | before / during / after | 23.8 MB |
| `Adams110725_FRAC` | Fractal object directed saccade | 1337 | 15° left / right | before / during / after | 18.2 MB |
| `Adams110725_OneDR` | One-direction-rewarded | 470 | 15° left / right | before / during only | 6.1 MB |

Each `.npz` holds the eye traces, event codes and times, spike times, target
positions and injection condition for that session. Every time in the dataset is
in **milliseconds from the start of its own trial**, which is what makes aligning
eye traces and spikes a plain subtraction.

## Running it outside Colab

Set `USE_LOCAL_FILE = True` and point `LOCAL_FOLDER` at a folder holding the
`.npz` files. Needs numpy, scipy, matplotlib and pandas.

## Repository contents

| File | Who runs it | What it does |
|---|---|---|
| `fef-inactivation-colab.ipynb` | the student, on Colab | the teaching notebook |
| `fef-inactivation-colab-SOLUTIONS.ipynb` | the instructor | the same notebook with every project `TODO` worked through |
| `convert-mat-to-npz.py` | the maintainer, once | packs raw OHLab `.mat` sessions into the `.npz` files |
| `implementation_log.md` | — | dated record of changes |

The `.npz` and `.mat` files are deliberately not committed — they are attached to
the [`data-v1` release](../../releases/tag/data-v1) instead, so cloning this repo
stays fast.

## Regenerating the data files (maintainer)

```bash
python convert-mat-to-npz.py
```

Reads the three sessions from the local `FEF_Inactivation_OHLab` data folder and
writes `.npz` files into `colab_npz/`. Then attach them to a release:

```bash
gh release create data-v2 colab_npz/*.npz --title "Session data v2"
```

...and update `RELEASE` in the notebook's setup cell to point at the new tag.

The converter resolves the two shape traps of the old OHLab format so the student
never meets them: the leading *unit* dimension of `SpikeTimeData`
(`1 x nSpikes x nTrials`), and the trial-number column at index 0 of dimension 1
in `TargetLoc` / `TargetPolarLoc`. `Data.BehaviorSummary` and `Data.ParaLib` are
MATLAB `containers.Map` objects that scipy cannot read at all, so they are not
carried over — which means the counts of *incorrect* trials are not available
here. Only correct trials are in these files.

## Verification

The notebook's saccade detector is a Python port of the lab's MATLAB `RT_Old.m`
and reproduces its numbers on `Adams102325_FRAC`:

| Measure | Notebook | MATLAB |
|---|---|---|
| Saccades detected | 1716 / 1740 (98.6%) | 1717 / 1740 (98.7%) |
| Median amplitude | 19.4° (targets at 20°) | 19.6° |
| Median direction error | 3.1° | 3.3° |
| Within 30° of target | 100% | 100% |
| Median RT, leftward (before/during/after) | 98 / 102 / 104 ms | 98 / 102 / 104 ms |
| Median RT, rightward | 116 / 150 / 112 ms | 116 / 152 / 114 ms |
| Median peak velocity, rightward | 1480 / 1379 / 949 deg/s | 1480 / 1379 / 951 deg/s |

The one-trial difference is NaN handling: MATLAB's `smoothdata(..., 'omitnan')`
tolerates missing samples inside a trace, while scipy's `savgol_filter` refuses to
run on them, so the notebook skips those trials rather than inventing values
across the gap.

All three sessions execute top to bottom without errors, including
`Adams110725_OneDR`, which has only two injection phases and therefore exercises
the generic phase handling.


