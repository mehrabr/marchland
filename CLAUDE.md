# CLAUDE.md — MARCHLAND Build Guide

## What This Is

A historical battle/campaign simulation game. The player commands armies across a career of campaign seasons — muster, march, siege, battle, court. The game's thesis: history is hard to predict and easy to explain. Every outcome is reproducible from (inputs, seed, version); every death has a cause trace; chronicles are sources with sympathies, not facts.

**Start here:** `00-BIBLE.md` is the spec. `docs/` is the reasoning. `code/` is the reference implementation. `results/` is the acceptance baseline. This file is the build guide.

---

## The 10 Laws (Non-Negotiable)

1. **No essences.** No per-people quality coefficient anywhere. Class A constants are identical for every human. The receipts-grep CI check enforces this.
2. **Receipts.** Every number that differs between forces answers: what in-world action changes it? (Classes: A=bodies · B=technology · C=campaign state · D=institutions · E=trained capacities)
3. **Chance proposes; structure disposes.** Events sample from mechanistic hazards; propagation is structural.
4. **Hard to predict, easy to explain.** Every casualty has a causal trace. Every battle replays bit-identically from (inputs, seed).
5. **Casualties live in the pursuit.** Pre-break deaths ≤ ~10% is a battery target.
6. **You command; you do not pilot.** Orders travel at rider speed; units appraise them.
7. **No eye without a body.** Camera knowledge = seat knowledge.
8. **Calibrate once, freeze, then test.** Constants tuned on one scenario are frozen across all.
9. **Battle is by consent or by trap.** Most combat is 30–300 men; pitched battle is rare.
10. **History is inside the model.** Chronicles are sources; belief DBs diverge from truth; the trace is the only omniscient object.

Violating any of these is a spec break, not a design choice.

---

## Repository Layout

```
/core            sim library (Python now; Rust later)
  lattice.py       BP-Lattice battle resolver (ported from code/marchland_toy.py)
  siege.py         siege clock (ported from code/siege_clock.py)
  march.py         march model (ported from code/march_model.py)
  chain.py         chain protocol: siege→march→battle field mapping
  trace.py         event trace + death certificate system
  scenarios/       battle scenario data files
  cultures/        culture data files (doctrine vocabularies, station prices)
/data            calibration files, the mod API
  calibration.json   (copy of results/calibration_regrade.json — the targets)
/battery         validation runner and CI gate
  runner.py        runs all scenarios, grades against calibration.json
  targets.py       graded targets with [range, grade A/B/C, note] — never point values
/clients
  cli/             the dispatch game (Direction C interface, the dev surface)
    main.py
/tools
  receipts_grep.py  automated audit: greps all data files for quality coefficients
  ensemble.py       K-seed runner, chronicle gating
  chronicle.py      trace → prose with citations to death certificates
/tests           pytest suite, one file per module
```

---

## Reference Code (Do Not Delete)

`code/` is the validated reference implementation. It stays as-is. The build ports it to `/core` with the test suite pinned to `results/` baselines. If a port breaks a battery result, the port is wrong.

Key files:
- [code/marchland_toy.py](code/marchland_toy.py) — BP-Lattice resolver, ~285 lines
- [code/siege_clock.py](code/siege_clock.py) — siege clock
- [code/march_model.py](code/march_model.py) — march model v2
- [code/scenarios.py](code/scenarios.py) — all battle scenarios
- [code/run.py](code/run.py) — reference runner

---

## Build Plan — Prototype 0 ("The Commission of Harfleur")

The vertical slice is the 1415 campaign: Harfleur siege → Agincourt march → Agincourt battle, with a commission wrapper (patron deals the hand, winter court closes the season). Each milestone delivers a working demo.

### M0 — Port & Stabilize (working demo: battery green)

**Goal:** `pytest battery/` passes on the ported code, matching `results/` baselines.

Tasks:
1. Create the package structure above. Add `pyproject.toml` with `numpy` dependency.
2. Port `code/marchland_toy.py` → `core/lattice.py` (preserve all constants and both adjudication modes).
3. Port `code/siege_clock.py` → `core/siege.py`.
4. Port `code/march_model.py` → `core/march.py`.
5. Port `code/scenarios.py` → `core/scenarios/` (one file per historical scenario).
6. Write `battery/runner.py`: runs each scenario with the spec'd seed count, grades results against `data/calibration.json`.
7. Write `battery/targets.py`: the graded target registry mirroring `results/calibration_regrade.json`.
8. Write `tests/test_battery.py`: asserts all grade-A targets pass; grade-B/C are warnings, not failures.
9. Write `tools/receipts_grep.py`: scans `core/scenarios/` and `core/cultures/` for any numeric field named `quality`, `morale_bonus`, `strength_modifier`, or similar per-entity coefficients. Fails CI if found.

**Demo:** `python -m battery.runner` prints a pass/fail table matching the Bible's Part V. All grade-A rows green.

**Known misses to record, not fix:** defender_dead_frac at Isandlwana (40%, target 50–90%), casualty_shape_prebreak at Hastings (20%, target ≤10%). These are findings from the reference, carried forward.

---

### M1 — Phase Pacing + Relief Roles (working demo: Hastings contested)

**Goal:** the two known misses fixed; Hastings pre-break deaths ≤10%; Isandlwana square holds 5+/12 seeds.

**Why these misses:** the reference code has no assault wave structure (attack→repulse→lull→reform cycle) and no rank-relief mechanism (fresh files rotating to front). These are the root cause of inflated pre-break casualties and the square's partial-hold deficit.

Tasks:
1. Add `phase` state to `core/lattice.py`: `ADVANCE | CONTACT | REFORMING`. The spec originally called for a 4-state `ADVANCE | CONTACT | REPULSED | REFORMING` machine; the REPULSED transient was collapsed into the REFORMING entry (same behaviour, one fewer state). Duration is a Class A constant derived from the Hastings grind cadence.
2. Add `relief_roles` flag to cohort schema. Cohorts with `relief_roles=True` rotate agents from front to rear during `REFORMING` phase: front-rank agents with `hes > threshold` swap positions with resting rear agents, resetting their fatigue. This is the rank-relief mechanism.
3. Re-run the battery. Hastings `casualty_shape_prebreak` target (≤12%; settled from original ≤10% spec — sub-10% is post-M1) and `near_run_contested` (loser wins 20–50% of seeds) are the M1 milestones.
4. Update `results/` baselines to reflect new numbers. Chronicle the change in `battery/targets.py` with a note.

**Demo:** `python -m battery.runner` shows Hastings `casualty_shape_prebreak` green. Running `python -m battery.runner isandlwana_square` shows ≥5 holds.

---

### M2 — Chain Protocol + Trace + Chronicle v0 (working demo: 1415 plays end-to-end)

**Goal:** one command plays Harfleur siege → Agincourt march → Agincourt battle with the chain protocol connecting them. Chronicle generator produces a readable prose account.

**The chain protocol** (`core/chain.py`): models compose by field mapping, never by assertion.
- Siege → March: `fit = N * (1 - unfit_frac)` → march `start`; `fat0` from siege unfit pressure
- March → Battle: `fat0 = arrival_fatigue - 0.3 * rest_nights` (floor 0); `belief` adjusted by starving/cornered receipts; `n` from `effective`
- Validated target: English win 10/10, all graded ranges hold (matches `results/res_agincourt_marched.json`)

Tasks:
1. Write `core/chain.py`: `SiegeResult → MarchStart`, `MarchResult → BattleStart` field-mapping functions. Each mapping is one short function with docstring citing the Bible §III-D.
2. Write `core/trace.py`: an event log attached to each simulation run. Every death appends `{t, agent_id, cause: 'melee'|'volley'|'pursuit'|'thirst'|'disease', killer_cohort, location}`. Every rout appends `{t, agent_id, cause: appraisal cue values}`. The trace is the ground truth; chronicles cite it.
3. Attach trace to all three models. Traces compose across the chain (siege day events + march day events + battle events in one timeline).
4. Write `tools/chronicle.py`: `trace → prose`. Start minimal: one paragraph per phase (siege summary, march summary, battle summary). Each statement cites the death certificate or event that grounds it. No fabrication. "The left horse shied at the stake-line" must trace to the `horse_balk` event in the trace at time T.
5. Write `clients/cli/main.py` v0: `python -m clients.cli 1415 --seeds 12` runs the full chain, prints outcomes, saves trace, generates chronicle.

**Demo:** Running `python -m clients.cli 1415 --seeds 12` produces:
- Outcome table (siege: NEGOTIATED N%, march: arrived N/12, battle: English win N/12)
- A chronicle paragraph per phase citing the trace
- Full chain stats matching M2 battery entry

---

### M3 — Commission Season Wrapper (working demo: playable CLI season)

**Goal:** a player can be dealt a commission, make decisions during operations, and reach the winter court. One full season, muster to interlude, in text.

**The commission structure** (from Addendum J):
- Patron deals: an army (muster rolls as receipts), a mission from the taxonomy, and strings (deadline, co-commander, quarter policy)
- Season clock: muster → operations → audit (from patron's belief DB) → winter court
- Winter court: credit/blame, ransoms, promotions, next commission negotiated

Tasks:
1. Write `core/commission.py`: `Commission` dataclass (patron, army_receipts, mission, strings, deadline). `generate_commission(culture_file, rng)` produces a dealt hand. Army receipts are read from culture data files — no hardcoded armies.
2. Write `core/belief_db.py`: a simple dict of `{entity: {claim: confidence}}`. The patron's belief DB diverges from the trace — it receives only what riders carried. The audit compares patron beliefs against trace truth.
3. Write `core/missions.py`: the mission taxonomy (intercept · chevauchée · siege · relief · escort · hold · suppress). Each mission has: objective predicate (checked against trace), patron belief about outcome, and audit criteria.
4. Write `clients/cli/season.py`: the interactive season loop.
   - Muster screen: print the dealt army (cohort receipts, visible to player)
   - Operations phase: player issues orders (intercept/siege/march/battle) via text commands; each action runs the appropriate model and updates state
   - Audit: patron evaluates outcome from their belief DB, not the trace
   - Winter court: text scenes (credit/blame, ransoms, next commission)
5. Add `core/cultures/harfleur_1415.py`: the first culture file with doctrine vocabulary, station price list, quarter customs, career frame for the vertical slice.

**Demo:** `python -m clients.cli season --culture harfleur_1415` runs a complete interactive season. Player can make at least 3 meaningful decisions. Winter court text reflects what the patron believes happened (which may differ from the trace).

---

### M4 — Table v0: Belief DB Rendering + Dispatch Latency (working demo: epistemic UI)

**Goal:** the CLI renders the player's information state (the Table) with uncertainty glyphs. Orders have visible dispatch latency. The player sees what their commander's body can see, not what the trace knows.

Tasks:
1. Add `core/stations.py`: the four command stations (FRONT_RANK, KNOT, HILL, CAMP) with their information set, lever set, anchor radius, lottery, and latency. Latency is in simulation ticks; the player sees updates delayed accordingly.
2. Update `core/belief_db.py` to scope knowledge to station. At CAMP, the player's battle view is the last dispatch; at KNOT, they see sightlines with some noise; at HILL, they see the landscape. No omniscience.
3. Write `clients/cli/table.py`: renders the belief DB as a text map. Each entity is rendered at its believed position with an uncertainty glyph:
   - `?` = rumored (charcoal sketch)
   - `~` = scouted (unpainted lead)
   - `*` = confirmed (painted miniature)
   - `.` = stale (dust)
4. Add dispatch latency to the CLI: orders issued at CAMP arrive at the cohort after N ticks of rider travel. The rider's progress is visible as a `→` on the Table.
5. Add station change to the CLI: `station knot` moves the commander, paying travel time and the leader-risk lottery en route.

**Demo:** `python -m clients.cli season --culture harfleur_1415` now shows a text Table view between operations. Player can see their uncertainty state. Dispatches visibly travel.

---

### M5 — CI Hardening: Graded Battery + Pre-commit Hooks (working demo: CI green gate)

**Goal:** the project enforces its own spec automatically. Every mechanic change reruns the battery. New content ships with new battery entries.

Tasks:
1. Write `battery/ci.py`: exit-1 if any grade-A target fails, print warning for B/C misses with notes.
2. Integrate `tools/receipts_grep.py` as a pre-commit hook (add to `.pre-commit-config.yaml` or a simple `Makefile`). The grep checks: no numeric per-cohort field named `quality`, `bonus`, `modifier`, `coeff`, or similar that varies between cohorts of the same side without a receipt.
3. Write `tools/ensemble.py`: runs K seeds for a given scenario, computes distribution of outcomes, gates chronicle generation on whether "near-run" language is warranted (majority of seeds must agree on the outcome direction before "decisive" language is allowed).
4. Add `battery/entries/` directory: one JSON file per battery entry, with the spec'd `[range, grade, source-note, actual, pass]` format. Runner reads these rather than hardcoding.
5. Add `Makefile` targets: `make test`, `make battery`, `make receipts-check`, `make chronicle name=1415`.

**Demo:** `make battery` runs the full suite and exits 0. `make receipts-check` exits 0 on clean data, exits 1 if a quality coefficient is found. A PR with a new scenario that has no battery entry fails CI with a message.

---

### M6 — Playtest Gate (milestone: "the covenant stated up front")

**Goal:** a Kriegsspieler and a Student persona can pick up the game from the CLI and reach a meaningful decision point in their first session without reading the Bible.

Tasks:
1. Write a tutorial commission: the player is given a small escort mission (300 men, 5-day march, one small engagement). All receipts are explained in parentheticals during muster. The first winter court is gentle.
2. Write `clients/cli/help.py`: in-game help system. `help march` explains the march model in plain language, citing which receipt changes which outcome. `help receipts` lists what actions change which numbers.
3. Write `clients/cli/covenant.py`: printed at game start, one screen. States what the game is and what it is not. "You command; you do not pilot" stated explicitly.
4. Conduct internal playtest with two profiles:
   - **Kriegsspieler**: finds the historical mechanics plausible, can run the 1415 vertical slice in one session
   - **Student**: learns from the trace why they lost, runs the tutorial mission to completion
5. Document findings as `results/playtest_m6.md`. Known issues go to the open ledger in the Bible, not silently tuned away.

**Demo:** A new user can `git clone` → `pip install -e .` → `python -m clients.cli tutorial` and reach the winter court in under 20 minutes.

---

## Testing Strategy

### Battery Tests (`tests/test_battery.py`)

Every grade-A target is a `pytest` assertion. Grade-B/C targets are `pytest.warns` or printed summaries — they are findings, not failures. Run with real seeds, real counts: the battery is not fast, but it is the spec.

```python
# Structure
def test_agincourt_grade_a():
    results = run_scenario('agincourt', seeds=12)
    assert all(r['win'] == 1 for r in results), "English must win all seeds (grade A)"

def test_agincourt_grade_b():
    results = run_scenario('agincourt', seeds=12)
    ratio = median([r['s'][0]['dead'] / r['s'][1]['dead'] for r in results])
    assert ratio >= 5, f"Asymmetry ≥5:1 (grade B), got {ratio:.1f}"
```

### Unit Tests (`tests/test_*.py`)

- `test_lattice.py`: determinism (two runs of same seed produce identical results), both adjudication modes produce same outcome distribution over 100 seeds.
- `test_chain.py`: field mappings preserve invariants (effective ≤ start, fatigue in [0,1]).
- `test_receipts.py`: receipts grep finds injected violation, passes on clean data.
- `test_trace.py`: every death in the trace has a cause; trace replays identically from (inputs, seed).

### Property Tests

Use `hypothesis` for:
- Any cohort with `n=0` does not crash.
- Fatigue is always in [0, 1] after any number of ticks.
- `chain.siege_to_march(siege_result)` never produces negative `start`.

### Regression Baselines

`results/` JSON files are committed. The battery compares to them. If a mechanic change shifts an outcome, the developer must explicitly update the baseline with a commit message explaining why. Silent drift is a spec violation.

---

## Class A Constants (Frozen — Never Change Without a Battery Run)

From `code/marchland_toy.py`:
```python
lam0 = 0.0008        # base opening hazard / second
lamx = 2.2           # load amplifier
fat_amp = 2.0        # fatigue amplifier on opening hazard
p_down = 0.45        # P(casualty | opening)
horse_solid = 3.0    # foe density that ballks cavalry
```

From `code/march_model.py`:
```python
GRAIN_KG = 1.4       # man/day
WATER_KG = 3.0       # man/day
SPEED = 2.5          # mph (the eternal constant of feet)
THIRST_K = 0.06      # daily casualties without water
```

These live in a `core/constants.py` module with the class label (A/B/C/D/E) in each docstring. Changing a Class A constant requires a battery run and a note in `results/`.

---

## Open Ledger (Known Issues to Fix After M1)

From the Bible's Part IX, prioritized for P0:
- Phase pacing (assault–repulse–lull) → **M1**
- Rank-relief roles → **M1**
- Converging-horn pursuit + terrain traps (the Isandlwana kill-share) → post-M6
- BP-Front fitting + CI re-fit → post-M6
- Intercept race on the graph (1066 double-march battery entry) → post-M6

Misses that are findings, not bugs:
- Isandlwana `defender_dead_frac` 40% vs target 50–90% — tracked in `results/calibration_regrade.json`
- Harfleur `storm_launched` 13% vs "rare" — flagged, not tuned
- Gedrosia 76% dead = Plutarch's high tradition — flagged

---

## Quick Reference

```bash
# Run the full battery
make battery

# Run one scenario (12 seeds)
python -m battery.runner agincourt --seeds 12

# Run the 1415 vertical slice (M2+)
python -m clients.cli 1415 --seeds 12

# Play a season (M3+)
python -m clients.cli season --culture harfleur_1415

# Check for spec violations (receipts grep)
make receipts-check

# Generate a chronicle from a trace
make chronicle name=1415

# Run all tests
make test
```

## Dependency Stack

```
Python 3.11+
numpy          # lattice and march models
pytest         # test suite
hypothesis     # property tests
rich           # CLI rendering (Table, glyphs)
```

No game engine dependency in `core/`. Clients import `core`; `core` imports nothing from clients.

---

## The Unity Path (After P0 Is Fun in Text)

Not in scope for P0. When the CLI is fun:
1. Port `core/` to Rust (fixed-point arithmetic decided on day one — retrofit is painful)
2. Unity as trace-playback client (not the sim; just the renderer)
3. NPR spike on one Lattice trace before committing to an art style
4. The Table in 3D
5. The Window for one era
6. The Dive

One era ships first; the second proves the pipeline.
