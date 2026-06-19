# MARCHLAND

A historical battle and campaign simulation. You command armies across career seasons — muster, march, siege, battle, winter court. Every outcome replays bit-identically from the same seed. Every death has a cause you can read.

---

## The thesis

**History is hard to predict and easy to explain.**

Three consequences that shape everything in this game:

1. **No quality coefficients.** No per-people or per-unit quality modifier exists anywhere. Every difference between forces must have a *receipt* — a changeable in-world fact (drill-days, calories, armor purchased, roads built, bonds formed). An automated audit enforces this on every data file. The loaded-dice test: a probability becomes a stat the moment the dice are loaded differently per people.

2. **Every death has a cause.** The simulation keeps a trace: every casualty records time, killer, cause (`melee · volley · pursuit · thirst · disease`), and location. Every rout records the appraisal cues that triggered it. The trace is the only omniscient object in the game; everything else — your Table, your patron's belief DB, the chronicle — is a partial view.

3. **You command; you do not pilot.** Orders travel at rider speed. Your men appraise them against what *they* can see. You cannot undo a dispatch once the rider departs. Your patron evaluates your campaign from their belief DB — which is built from what your dispatches told them, not from what the trace records.

---

## Quickstart

```bash
git clone <repo>
cd marchland
pip install -e .

# Tutorial mission: 300-man escort, 5-day march, one engagement (~20 min)
python -m clients.cli tutorial

# 1415 vertical slice: Harfleur → Agincourt across 12 seeds
python -m clients.cli 1415 --seeds 12

# Full interactive season
python -m clients.cli season --culture harfleur_1415
```

**Requirements:** Python 3.11+, numpy, rich

---

## Gameplay loop

A season runs in four acts:

```
Muster  →  Operations  →  Patron Audit  →  Winter Court
```

**Muster.** Your patron deals you a commission: an army (cohort receipts, visible to you), a mission from the taxonomy (`intercept · chevauchée · siege · relief · escort · hold · suppress`), and strings (deadline, co-commander, imposed quarter policy). The army's receipts explain every number — why this cohort holds longer, why that one breaks faster.

**Operations.** You issue orders. Each operation runs the appropriate simulation model:
- *March*: the Day Layer — column physics, water, food, straggle, desertion. Pace buys time with order.
- *Siege*: the dual-clock model — besieger disease races town hunger and breach progress. Summons-and-terms decides the outcome; the garrison has its own calculus.
- *Battle*: the BP-Lattice resolver — density fields, appraisal cues, percolation failure. Formations break when their coverage loses its giant component, not when they hit zero.

**Patron Audit.** Your patron evaluates the campaign from their belief DB. They know what your riders told them. If a dispatch was wrong, late, or lost, the audit reflects that — injustice both ways.

**Winter Court.** Credit, blame, ransoms (including your own body), promotions. Your next commission is negotiated here. The chronicle auto-compiles from the season's trace.

---

## Core concepts

### Receipts

A receipt is a changeable in-world fact that explains why a number is what it is. Drill-days determine cohort endurance. Calories determine march survivability. Armor is purchased. Roads are built or cut. No number may differ between forces without a receipt. `help receipts` at any in-game prompt lists all of them.

### The trace

Every simulation run produces a trace: a timeline of events with causes. Deaths are death certificates — time, cause, killer cohort, location. Routs record the appraisal cue values that crossed the threshold. The trace is the ground truth the game never surfaces directly. The chronicle cites it; the patron's belief DB approximates it. `help trace` explains how to read one.

### The Table

Your information surface. The Table renders your belief DB — what your command station's body can see, at the latency of your last dispatch. Entities appear with uncertainty glyphs:

```
?   rumored    (charcoal sketch)
~   scouted    (unpainted lead)
*   confirmed  (painted miniature)
.   stale      (dust)
```

Dispatches travel as visible rider pieces. You see your information state, not the ground truth.

### Stations

Where your body sits determines what you know and what levers you hold:

| Station | Sees | Latency |
|---|---|---|
| Front Rank | Your immediate surroundings | None — you are there |
| Knot | Your wing, with noise | Sightlines |
| Hill | Landscape overview | Scout reports |
| Camp | Last dispatch | Rider travel time |

Moving between stations costs time and runs the leader-risk lottery.

### The chronicle

After a battle or season, the chronicle generator produces a prose account — one paragraph per phase, each statement grounded in a trace event. The chronicle lies like sources do: a chronicler with sympathies will emphasize what their vantage saw. "The left horse shied at the stake-line" must trace to a `horse_balk` event at time T, or it does not appear.

---

## Architecture

```
/core            sim library (no engine dependency)
  lattice.py       BP-Lattice battle resolver
  siege.py         siege clock (dual clocks, summons-and-terms)
  march.py         march model (column physics, entropy flows)
  chain.py         chain protocol: siege → march → battle field mappings
  trace.py         event log + death certificate system
  stations.py      command station definitions and latency model
  commission.py    commission generator
  belief_db.py     patron and player belief databases
  missions.py      mission taxonomy and objective predicates
  cultures/        culture data files (doctrine, station prices, career frame)
  scenarios/       battle scenario data files

/battery         validation runner and CI gate
  runner.py        runs all scenarios, grades against calibration.json
  targets.py       graded target registry [range, grade A/B/C, note]
  entries/         one JSON file per battery entry
  ci.py            exit-1 on grade-A failures; warn on B/C

/clients
  cli/             the dispatch game (text interface)
    main.py          entry point: tutorial / 1415 / season
    season.py        interactive season loop
    tutorial.py      tutorial mission with parenthetical receipts
    table.py         Table renderer with uncertainty glyphs
    covenant.py      covenant screen (printed once at game start)
    help.py          in-game help: `help march`, `help receipts`, `help trace`

/tools
  receipts_grep.py  CI audit: fails if quality coefficients found in data files
  ensemble.py       K-seed runner; gates "near-run" chronicle language on seed splits
  chronicle.py      trace → prose with citations

/code            validated reference implementation (do not delete)
  marchland_toy.py  original BP-Lattice resolver
  siege_clock.py    original siege clock
  march_model.py    original march model v2

/results         acceptance baselines the battery compares against
/data            calibration.json (the target file for battery grading)
```

**The rule:** `core/` imports nothing from `clients/`. Clients are trace players; the sim is headless.

---

## Dev commands

```bash
make test            # pytest suite
make battery         # full validation battery (must stay green)
make receipts-check  # spec violation audit (exits 1 if quality coefficients found)
make chronicle name=1415   # run chain and print chronicle
```

### Validation battery

Every grade-A target is a pytest assertion. Grade-B/C targets are printed as findings, not failures. Every mechanic change must rerun the battery. New scenarios ship with new battery entries.

Current known misses (open ledger, not bugs):
- `Isandlwana defender_dead_frac`: 40% vs target 50–90% — needs converging-horn pursuit
- `Hastings pre-break deaths`: resolved at M1; baseline updated
- `Harfleur storm_launched`: 13% vs "rare" — flagged, not tuned

### Constants

Class A constants in `core/constants.py` are frozen. Changing one requires a battery run and a note in `results/`. They are identical for every human — this is Law 1.

---

## Going deeper

- [00-BIBLE.md](00-BIBLE.md) — the complete buildable specification: all 10 Laws, architecture, frozen constants, schemas, the battery, full game design, presentation, and the milestone plan
- [01-essay-the-peasants-who-wouldnt-run.md](01-essay-the-peasants-who-wouldnt-run.md) — the argument for why this approach to historical simulation
- [docs/](docs/) — twenty-one design addenda (A–U), the reasoning behind each system
- [code/](code/) — the validated reference implementation, the porting targets for `core/`
- [results/](results/) — acceptance baselines with source grades and notes on every miss
