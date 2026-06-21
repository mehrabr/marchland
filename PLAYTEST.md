# MARCHLAND — Playtest Guide v0.1.0

**Version:** v0.1.0 "The Commission of Harfleur"
**Runtime required:** Python 3.12.x (exact minor required; see note below)

---

## What you're testing

Two things share this release:

**1. The CLI vertical slice** — a full interactive campaign season in the terminal: muster, march, siege, battle, patron audit, winter court. This is the main playtest target.

**2. The Ren'Py vertical slice** (`clients/renpy/`) — a 10-minute single-order engagement prototype. Requires the Ren'Py SDK (see below). Tests one hypothesis: *is command-under-uncertainty compelling in ten minutes?*

The CLI slice is the easier entry point. Start there.

---

## Setup (CLI slice — recommended start)

```bash
# 1. Clone the repo
git clone https://github.com/mehrabr/marchland.git
cd marchland

# 2. Create a Python 3.12 virtual environment
#    (Python 3.12.x required — Ren'Py 8.5.3 bundles 3.12; other minors untested)
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install
pip install -e .

# 4. Run the tutorial (~20 min, recommended first session)
python -m clients.cli tutorial

# 5. Run the full 1415 vertical slice
python -m clients.cli 1415 --seeds 12

# 6. Play a full interactive season
python -m clients.cli season --culture harfleur_1415
```

---

## Python version note

The sim pins `numpy==2.4.6` and uses Python 3.12.x. The `.python-version` file is not present in this release — use `pyenv install 3.12` or the [python.org installer](https://www.python.org/downloads/release/python-3120/) if your system Python is a different version.

Cross-architecture bit-identity (x86 vs Apple Silicon) is **not** guaranteed. Each platform reproduces results identically within itself; don't compare raw numbers across architectures.

---

## What to pay attention to

The playtest spec lives at `docs/marchland-vertical-slice.md`. The short version:

**Does the order feel irrevocable?** You should hesitate before committing. If it feels arbitrary, that's a finding.

**Does the wait read as tension?** Between issuing an order and seeing its effect, is there something to do with that uncertainty? Or is it dead time?

**Does the chronicle→trace reveal recontextualize what happened?** When you see the cause of each death, does it change how you read the outcome? Or does it just decorate what you already knew?

These are the three falsifiable tests. Please note which pass and which fail.

---

## Running the battery (optional — for verification)

```bash
# Confirm all grade-A sim targets pass
python -m battery.ci

# Check for spec violations (receipts grep)
python -m tools.receipts_grep
```

Expected output: `CI GREEN: all grade-A targets pass. Grade-B warnings: 5` (known misses, not bugs — see `results/calibration_regrade.json`).

---

## Ren'Py slice (optional — requires Ren'Py SDK)

The Ren'Py vertical slice is in `clients/renpy/`. To run it:

1. Install [Ren'Py 8.5.3](https://www.renpy.org/latest.html) (exactly — the bundled Python must match 3.12)
2. Point the Ren'Py launcher at `clients/renpy/` as the project directory
3. Launch

The slice runs a single Agincourt engagement (seed 42 by default). It demonstrates the command-under-uncertainty loop in visual novel form: Table with uncertainty glyphs, one officer contact report, one irrevocable order, outcome, chronicle, trace reveal.

---

## Known issues in this release

From the open ledger (not bugs, findings from the reference implementation):

| Item | Status |
|---|---|
| Isandlwana `defender_dead_frac` 40% vs target 50–90% | Known miss, fix post-M6 (pursuit model underdrives kill-share) |
| Harfleur `storm_launched` 13% vs "rare" | Flagged, not tuned |
| Sphacteria Spartan `dead_frac` target 70%+ | M7.0 partial fix; encirclement fires need full landing party |
| Cannae Mago `roman_win` counterfactual | Post-M7.7 (requires lattice fighting_withdrawal wiring) |

All grade-A sim targets pass. These are grade-B findings that are tracked, not hidden.

---

## Feedback

Please note:
- Which of the three falsifiable tests passed/failed
- Any number or outcome that surprised you (good or bad)
- `help receipts` and `help trace` in-game if anything is unexplained — if those don't answer it, that's a finding too

The chronicle is auto-generated from the trace. If a chronicle sentence feels wrong or unsupported, note which one — it means the trace event it cites is either missing or misfired.
