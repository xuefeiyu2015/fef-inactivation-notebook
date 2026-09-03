"""
Convert the OHLab FEF-inactivation .mat sessions into small .npz files for Colab.

WHY THIS EXISTS
The raw .mat files are 36-131 MB each, which is painful to move onto Colab every
time a runtime restarts. This script is run ONCE, locally, by the person handing
out the data. It keeps only the fields the student notebook needs and saves them
with np.savez_compressed, which brings a 131 MB session down to about 24 MB.

It also fixes, here rather than in the notebook, the two shape traps of the old
OHLab format:

  1. Data.SpikeTimeData is nUnits x maxSpikes x nTrials -- a 3-D array with a
     leading UNIT dimension, even though these files hold a single unit. Indexing
     it as if it were 2-D silently reads the wrong numbers. We drop that
     dimension and store a plain nTrials x maxSpikes array.

  2. In Data.TargetLoc / TargetPolarLoc / TargetIndex, index 0 of dimension 1 is
     a trial-NUMBER column, not data. The real target sits at index 1. We take
     that column here, so the notebook just gets target_x, target_y, and so on.

Two fields are deliberately NOT carried over: Data.BehaviorSummary and
Data.ParaLib are MATLAB containers.Map objects, which scipy.io.loadmat cannot
read at all (they arrive as opaque blobs). BehaviorSummary is where the counts of
the INCORRECT trials live -- see the note printed at the end of this script.

Usage:
    python convert-mat-to-npz.py

Xuefei Yu, 2026
"""

import os

import numpy as np
import scipy.io as sio

# --- where the .mat files are, and where the .npz files should go -------------
# Override the input folder with the FEF_DATA_DIR environment variable, e.g.
#     FEF_DATA_DIR=~/path/to/FEF_Inactivation_OHLab python convert-mat-to-npz.py
DATA_DIR = os.path.expanduser(os.environ.get("FEF_DATA_DIR", "./FEF_Inactivation_OHLab"))
OUT_DIR = os.path.join(DATA_DIR, "colab_npz")

# The three sessions being handed to the student. The short name on the left is
# what the notebook's SESSION variable uses.
SESSIONS = {
    "Adams102325_FRAC": "Adams102325FEFInactivation_FRAC.mat",
    "Adams110725_FRAC": "Adams110725FEFInactivation_FRAC.mat",
    "Adams110725_OneDR": "Adams110725FEFInactivation_OneDR.mat",
}


def convert_one_session(mat_path):
    """Read one OHLab .mat file and return a dict of plain numpy arrays.

    Computation only -- it does not write anything to disk.
    """
    data = sio.loadmat(mat_path, struct_as_record=False)["Data"][0, 0]

    n_trials = data.EventChannel.shape[0]

    # --- eye traces ----------------------------------------------------------
    # Data.EyeDataRaw is an nTrials x 4 CELL array: column 0 is eye X and column
    # 1 is eye Y, in degrees, one variable-length vector per trial. (Columns 2
    # and 3 are not eye position and are unused.) Trials have different lengths,
    # so we store them in one rectangular array padded with NaN, and keep the
    # real length of each trial alongside it.
    eye_raw = data.EyeDataRaw
    eye_n_samples = np.array([eye_raw[i, 0].size for i in range(n_trials)], dtype=np.int32)
    max_samples = int(eye_n_samples.max())

    eye_x = np.full((n_trials, max_samples), np.nan, dtype=np.float32)
    eye_y = np.full((n_trials, max_samples), np.nan, dtype=np.float32)
    for i in range(n_trials):
        n = eye_n_samples[i]
        eye_x[i, :n] = eye_raw[i, 0].ravel()
        eye_y[i, :n] = eye_raw[i, 1].ravel()

    # --- spikes --------------------------------------------------------------
    # TRAP 1: shape is nUnits x maxSpikes x nTrials. Take unit 0 (the only unit
    # in these files) and transpose so each ROW is one trial. Padding stays NaN.
    spike_times = np.asarray(data.SpikeTimeData[0], dtype=np.float32).T

    # --- targets -------------------------------------------------------------
    # TRAP 2: index 0 of dimension 1 is a trial-number column. The target is [:, 1, :].
    target_x = np.asarray(data.TargetLoc[:, 1, 0], dtype=np.float32)
    target_y = np.asarray(data.TargetLoc[:, 1, 1], dtype=np.float32)
    target_angle = np.asarray(data.TargetPolarLoc[:, 1, 0], dtype=np.float32)
    target_ecc = np.asarray(data.TargetPolarLoc[:, 1, 1], dtype=np.float32)

    return {
        "eye_x": eye_x,
        "eye_y": eye_y,
        "eye_n_samples": eye_n_samples,
        "spike_times": spike_times,
        "event_codes": np.asarray(data.EventChannel, dtype=np.float32),
        "event_times": np.asarray(data.EventTimeChannel, dtype=np.float32),
        "target_x": target_x,
        "target_y": target_y,
        "target_angle": target_angle,
        "target_ecc": target_ecc,
        "injection_condition": np.asarray(data.InjectionCondition.ravel(), dtype=np.float32),
        "eye_bin_width": np.float32(data.EyeBinWidth[0, 0]),
        "session_name": np.str_(str(data.FileName[0])),
        "task_code": np.int32(data.TaskCode[0, 0]),
        "task_type": np.str_(str(data.TaskType[0]).strip()),
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for short_name, file_name in SESSIONS.items():
        mat_path = os.path.join(DATA_DIR, file_name)
        if not os.path.exists(mat_path):
            print(f"SKIPPING {short_name}: {mat_path} not found")
            continue

        print(f"\nConverting {file_name} ...")
        session = convert_one_session(mat_path)

        out_path = os.path.join(OUT_DIR, short_name + ".npz")
        np.savez_compressed(out_path, **session)

        mat_mb = os.path.getsize(mat_path) / 1e6
        npz_mb = os.path.getsize(out_path) / 1e6
        n_trials = session["event_codes"].shape[0]
        n_spikes = int(np.sum(~np.isnan(session["spike_times"])))
        print(f"  {n_trials} trials, {n_spikes} spikes, task {int(session['task_code'])}")
        print(f"  {mat_mb:.0f} MB  ->  {npz_mb:.1f} MB   {out_path}")

    print(
        "\nNOTE: only CORRECT trials are stored in these files. The counts of the\n"
        "broken-fixation / no-fixation / failed-saccade trials live in\n"
        "Data.BehaviorSummary, which is a MATLAB containers.Map and cannot be read\n"
        "by scipy at all, so it is not carried into the .npz. Any RATE computed\n"
        "over trials (above all the anticipation rate) is therefore an\n"
        "underestimate: the trials that anticipated hardest became fixation breaks\n"
        "and were dropped before the file was written."
    )


if __name__ == "__main__":
    main()
