# MARCHLAND

A historical battle and campaign simulation. You command armies across career seasons — muster, march, siege, battle, winter court. Every outcome replays from the same seed within the pinned runtime (`numpy==2.4.6`, same CPU architecture). Every death has a cause you can read.

---

## The thesis

**History is hard to predict and easy to explain.**

Three consequences that shape everything in this game:

1. **No quality coefficients.** No per-people or per-unit quality modifier exists anywhere. Every difference between forces must have a *receipt* — a changeable in-world fact (drill-days, calories, armor purchased, roads built, bonds formed). An automated audit (`make receipts-check`) enforces forbidden field names on every data file; per-cohort scalars (`err`, `belief`, `disc`) are authored with an in-world justification comment in each scenario file. The loaded-dice test: a probability becomes a stat the moment the dice are loaded differently per people.

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

**Requirements:** Python 3.14.x, numpy==2.4.6, rich~=15.0

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
- *Battle*: the BP-Lattice resolver — density fields, appraisal cues, fractional-standing break. A formation breaks when its standing strength falls below its `break_frac` threshold, triggering pursuit.

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
  lattice.py       BP-Lattice battle resolver (M7.0: convergent horn; M7.2: meaning hook)
  siege.py         siege clock (dual clocks, summons-and-terms)
  march.py         march model (column physics, entropy flows)
  chain.py         chain protocol: siege → march → battle field mappings
  trace.py         event log + death certificate system
  stations.py      command station definitions and latency model
  commission.py    commission generator
  belief_db.py     patron and player belief databases
  missions.py      mission taxonomy and objective predicates
  meaning.py       institution-of-meaning interpretation layer (M7.2)
  sentiment.py     sentiment drift field + dissolution runner (M7.4/M7.5)
  officer.py       officer model with belief-DB-driven decisions (M7.7 — design spike, not yet wired into simulation)
  cultures/        culture data files (doctrine, station prices, career frame)
  scenarios/       battle scenario data files (incl. carrhae, sphacteria, winter_quarters)

/battery         validation runner and CI gate
  runner.py        runs all scenarios, grades against calibration.json
  targets.py       graded target registry [range, grade A/B/C, note]
  entries/         one JSON file per battery entry
  ci.py            exit-1 on grade-A failures; warn on B/C

/clients
  cli/             the dispatch game (text interface)
    main.py          entry point: tutorial / 1415 / season
    season.py        interactive season loop (M7.A: scene-based, HOLD/MOVE)
    tutorial.py      tutorial mission with parenthetical receipts
    table.py         Table renderer: uncertainty glyphs + sentiment field (M7.6)
    covenant.py      covenant screen (printed once at game start)
    help.py          in-game help: `help march`, `help receipts`, `help trace`
  renpy/           Ren'Py visual novel client
    bridge.py        Layer 2 adapter — the only thing that crosses sim→skin
    game/
      init.rpy       Ren'Py init: bridge import + global rollback config
      marchland.rpy  full season loop (siege → march → battle)
      slice.rpy      vertical slice entry point (label slice_start)

/tools
  receipts_grep.py  CI audit: quality coefficients + meaning/sentiment audit rules (M7.3)
  sensitivity.py    class-A constant perturbation harness (M7.1)
  ensemble.py       K-seed runner; gates "near-run" chronicle language on seed splits
  chronicle.py      trace → prose with citations

/code            frozen historical prototype (candidate golden-output oracle)
  marchland_toy.py  original BP-Lattice resolver (diverged from core/ at M1+)
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
make sensitivity     # class-A constant perturbation report (M7.1; never a gate)
```

### Validation battery

Every grade-A target is a pytest assertion. Grade-B/C targets are printed as findings, not failures. Every mechanic change must rerun the battery. New scenarios ship with new battery entries.

**Current status: 14/14 grade-A targets green.**

Current known misses (open ledger, not bugs):
- `Isandlwana line defender_dead_frac`: ~40% vs target 50–90% — convergent horn fires at Carrhae/Sphacteria; Isandlwana line still needs terrain-trap pursuit (post-M7)
- `Sphacteria spartan_dead_frac`: lower end of range; light-troop ranged dynamics need BP-Front fitting
- `Assault breach_vs_starved_carried`: garrison not weak enough without caloric collapse mechanic
- `Harfleur storm_launched`: 13% vs "rare" — flagged, not tuned

### Constants

Class A constants in `core/constants.py` are frozen. Changing one requires a battery run and a note in `results/`. They are identical for every human — this is Law 1.

---

## Ren'Py client and the vertical slice

The Ren'Py client (`clients/renpy/`) is a visual novel skin over the same headless sim. Nothing in `core/` knows Ren'Py exists. The integration has three layers:

```
Layer 3  game/*.rpy         scenes, menus, screens, rollback config
Layer 2  bridge.py          plain serializable dicts — the only thing that crosses
Layer 1  core/              sim, RNG, battery — imports nothing from Ren'Py
```

Every public function in `bridge.py` returns plain Python types (dicts, lists, ints, strs, floats). No numpy scalars, no sim objects. Ren'Py pickles save state from `SaveCapsule`; battles reconstruct from their seed rather than persisting RNG state. The bridge test suite (`tests/test_renpy_bridge.py`, 99 assertions) verifies layer isolation, numpy transience, and JSON serializability.

**Model A (recommended):** vendor numpy 2.4.6 (`cp312` wheel) into Ren'Py's bundled Python 3.12 interpreter and `import core.chain` inside `init python:`. Re-pin to 3.12 and re-bless golden hashes. **Model B (fallback):** run the sim as a subprocess, exchange JSON over a pipe — bit-identical to CI but requires IPC plumbing. The layer contract is identical either way.

### Vertical slice — "One Order, One Battle, One Truth"

**Entry point:** `label slice_start` in `clients/renpy/game/slice.rpy`.

The slice is a falsifiable experiment, not a demo. **Hypothesis under test:** *command-under-uncertainty — partial knowledge, one irrevocable order delayed by geography, living with the consequence, a record you must see through — is compelling in ten minutes.*

The loop in seven steps (spec: `docs/marchland-vertical-slice.md`):

1. **Table** — three belief markers: `*` your line (confirmed), `~` enemy column (scouted, 2h old), `?` horse beyond the wood (rumored). The cavalry is the crux.
2. **Contact report** — captain portrait; one brief, two unknowns.
3. **Irrevocable order** — three choices; `renpy.block_rollback()` fires on commit:
   - *Hold the ridge* — stakes active, cavalry balks (`horse_balk` event fires, chronicled)
   - *Refuse — withdraw over the bridge* — no battle, trace holds an absence
   - *Offer open battle* — stakes absent, cavalry rides through
4. **In-flight wait** — HOLD on the Hill (wider view, latency 1) or MOVE to the Knot (latency 0, leader-risk lottery). Not dead time: the order is already irrevocable.
5. **Headless battle** — `run_slice_battle(seed, order)` in the bridge; deterministic from `(scenario, seed)`.
6. **Chronicle** — the tapestry's prose: sympathetic emphasis, correct outcome, wrong mechanism.
7. **Reveal** — toggle to the raw death-certs. Pursuit deaths outnumber pre-break deaths. The captain died in the ditch, after the line was already gone. The chronicle's drama was imprecise about the mechanism. **Hard to predict, easy to explain, recorded imperfectly.**

It **passes** if a naive playtester hesitates before committing, reacts to the outcome, and re-reads at the toggle. It **fails** if the order feels arbitrary, the wait reads as dead time, or the scrub reads as a gimmick. Failure means the core loop needs rethinking before building the season, the officer integration, or a line of art — and that is the entire value of the slice.

---

## M7 features (current milestone)

### Convergent-horn pursuit (M7.0)

When a scenario sets `convergent_horn: true`, fugitives caught between lateral foe columns take an amplified kill rate during pursuit. This closes the Isandlwana dead-fraction miss at Carrhae and Sphacteria. Two new scenarios: **Carrhae 53BC** (horse-archer encirclement) and **Sphacteria 425BC** (Spartan garrison surrounded by light troops).

### Sensitivity harness (M7.1)

`python -m tools.sensitivity` perturbs every class-A constant ±30% and re-runs the battery. Outputs a *load-bearing vs decorative* table: load-bearing constants fail at least one grade-A target when perturbed; decorative ones don't. Wired as `make sensitivity` (report only — never a CI gate).

### Institution-of-meaning (M7.2)

`core/meaning.py` — a cohort's reading of events depends on what institution it belongs to (oath, paymaster, officer cadre). A meaning **transforms raw appraisal cues** before they reach the universal threshold — never changing the threshold itself. Meanings have `failure_conditions` (required non-empty — Bret's law enforces this in code). When the carrier falls, the meaning breaks and the cohort reverts to raw cues.

### Audit rules (M7.3)

`tools/receipts_grep.py` now enforces two additional rules:
- **Bret's law**: any meaning with `failure_conditions: []` fails CI (an essence cannot be destroyed; a meaning without a destruction path is an essence).
- **Olleus's law**: any sentiment transmission term not in `TRACKED_RECEIPTS` fails CI (no free contagion constants — all spread must trace to a march-model receipt).

### Sentiment drift (M7.4/M7.5)

`core/sentiment.py` — a scalar penetration field spreading across cohorts at campaign-day resolution. Transmission only from registered receipts: `idle, hunger, arrears, bond, disease, officers, cohesion`. Sentiment is the *transition function* — it changes which institution a cohort inhabits; the institution changes how events are read; the universal threshold is never touched.

**Dissolution-without-battle** (M7.5): the `winter_quarters` scenario drives an army to <50% effective strength through unpaid idle quartering alone. No combat events fire. Battery grade-A.

### Scene-based turns (M7.A)

The season loop now runs on **decision-point events** rather than fixed intervals:
- `hold` — advance to the next decision-point event (order outcome, rider arrives, deadline imminent)
- `move <dest>` — ride to a new station; transit time passes and your vantage changes
- Issuing an order and advancing time are **separate acts** — an order pushes onto the in-flight queue; time only advances when you choose `hold`, `move`, or `wait`
- Command begins with an **arrival scene**: a subordinate briefs from their own (fallible, partial) belief DB before you see the muster summary

### Sentiment on the Table (M7.6)

The Table renderer shows the sentiment field for your own cohorts with the same uncertainty grammar as other beliefs:

```
!  flipped  (meaning may be broken)
▲  high     (spreading fast)
~  present  (seed established)
?  rumoured (early trace)
·  clear    (no penetration)
```

Intervention levers shown alongside: `dispatch_officer`, `pay_arrears`, `rest_idle`, `small_victory`, `break_up`.

### Officer model (M7.7) — design spike

`core/officer.py` — subordinate commanders reason from their own belief DB, not from the trace or HQ's view. Three behaviors are battery-verified in isolation, but the module has no callers in the simulation yet — it does not yet change battle outcomes. Integration (`Battle state → officer belief DB → process_order → cohort action`) is the next step.
- **refuses suicidal**: holds when believed foe density ≥ 4.0 regardless of order received
- **exploits flank**: initiates a flank action when their belief DB shows foe coverage < 20%
- **misreads dispatch**: interprets "advance when favorable" as "advance now" when their (possibly wrong) belief DB shows conditions favorable

---

## Going deeper

- [00-BIBLE.md](docs/00-BIBLE.md) — the complete buildable specification: all 10 Laws, architecture, frozen constants, schemas, the battery, full game design, presentation, and the milestone plan
- [01-essay-the-peasants-who-wouldnt-run.md](docs/01-essay-the-peasants-who-wouldnt-run.md) — the argument for why this approach to historical simulation
- [docs/marchland-vertical-slice.md](docs/marchland-vertical-slice.md) — vertical slice spec: hypothesis, ruthless scope, 7-step walkthrough, build order, pass/fail criteria
- [docs/marchland-renpy-integration.md](docs/marchland-renpy-integration.md) — Ren'Py integration architecture: three-layer contract, Model A/B, save discipline, rollback partition
- [docs/](docs/) — twenty-one design addenda (A–U), the reasoning behind each system
- [code/](code/) — a frozen historical prototype; `core/` has diverged (M1+) and is now the canonical implementation
- [results/](results/) — acceptance baselines with source grades and notes on every miss
