# MARCHLAND — Ren'Py Integration Architecture

*A thin-integration sketch for the solo-developer path. Sits beside `marchland-audit-spec-v2.md` and the UI spec. Goal: keep the simulation a pinned, separately-tested package, use Ren'Py as a trace-consuming skin, and resolve the determinism, save, and rollback frictions on day one rather than discovering them later.*

**The one-sentence shape:** the sim computes, the trace is the contract, Ren'Py renders. Nothing in the sim knows Ren'Py exists; nothing in Ren'Py touches numpy.

---

## 1. The three layers

```
┌──────────────────────────────────────────────────────────────┐
│  LAYER 3 — Ren'Py (the skin)                                   │
│  scenes · dialogue · menus · the Table screen · save/load ·    │
│  self-voicing · the Archive scrub. Imports Layer 1; reads      │
│  only traces. Stores only serializable state.                  │
└───────────────▲──────────────────────────┬───────────────────┘
                │  trace dict (JSON-able)   │  (seed, scenario, order)
┌───────────────┴──────────────────────────▼───────────────────┐
│  LAYER 2 — THE TRACE (the contract)                            │
│  plain dicts: death certs (+location), rout events, belief     │
│  state, pending-order queue, season clock. The ONLY thing      │
│  that crosses the boundary. Already JSON-serializable (the     │
│  golden-hash test proves it).                                  │
└───────────────▲──────────────────────────┬───────────────────┘
                │  results                  │  inputs + seed
┌───────────────┴──────────────────────────▼───────────────────┐
│  LAYER 1 — sim package `core/` (pinned, headless, tested)      │
│  numpy · RNG · lattice/chain · stations · belief_db ·          │
│  sentiment · the battery. Imports NOTHING from Ren'Py.         │
│  Same package CI tests. Reproducibility lives here.            │
└──────────────────────────────────────────────────────────────┘
```

**The rule that makes this safe** is the one the codebase already enforces: `core/` imports nothing upward. Today it imports nothing from `clients/`; tomorrow it imports nothing from Ren'Py either. Ren'Py is just a new client. The trace is the contract — exactly as designed.

---

## 2. Division of responsibility

| Concern | Owner | Notes |
|---|---|---|
| Simulation, RNG, determinism, battery | **Layer 1 (`core/`)** | Unchanged. The thing CI tests is the thing that ships. |
| Belief DB, stations, pending-order queue, sentiment | **Layer 1** | Already implemented (`stations.py`, `belief_db.py`, `season.py`). |
| The trace (deaths, routs, events, belief state) | **Layer 2** | Plain dicts. Never wrap numpy in it. |
| Scenes, backgrounds, sprites, music, transitions | **Layer 3 (Ren'Py)** | Native idiom. |
| Dialogue, menus, the order conceit | **Layer 3** | A menu choice → a `PendingOrder`. |
| The Table (belief-as-miniatures) | **Layer 3** | A custom `screen`, driven by Layer-2 belief state. |
| Save / load / text history / accessibility | **Ren'Py, free** | Self-voicing satisfies the spec's accessibility goal. |
| Chronicle-vs-trace scrub | **Layer 3 (Archive)** | Two renderings of one Layer-2 trace. |
| Live battle animation ("the Window") | **nobody — out of scope** | Ren'Py can't; the design already declined it. |

---

## 3. The trace is the contract

Everything crossing from sim to skin is a plain, serializable dict. This is not new work — `run_chain_1415(seed)['trace']` already returns exactly this, and the golden-hash test serializes it with `json.dumps(..., sort_keys=True, default=str)`. The discipline to keep:

- **Out of the sim:** the trace dict, the belief-DB state, the pending-order queue, the season clock — all plain Python.
- **Never out of the sim:** numpy arrays, the `Battle` object, RNG objects. They stay inside Layer 1 and die when the call returns.

This is why the project's "the trace is the only omniscient object" philosophy pays off here: the boundary it implies is exactly the boundary Ren'Py needs.

---

## 4. Process model — pick one

**Model A — in-process import (recommended for solo simplicity).**
Vendor numpy 2.4.6 (cp312 wheel) into Ren'Py's bundled interpreter via its package path, then `import core.chain` inside an `init python:` block. Ren'Py 8.5.3 is Python 3.12 and numpy 2.4.6 ships cp312 wheels with bundled OpenBLAS, so this works without a port.
*Consequence:* the **shipped reproducibility envelope becomes 3.12**, so re-pin and re-bless (§6).

**Model B — subprocess isolation (the determinism-purist's fallback).**
Bundle the sim as its own pinned Python (3.14 / numpy 2.4.6 — exactly what CI tests), run it as a subprocess, and exchange JSON traces over a pipe. Ren'Py never imports numpy.
*Consequence:* the shipped sim is **bit-identical to CI with no re-bless**, at the cost of IPC plumbing and shipping a second interpreter.

> **Recommendation:** start with **A** — the re-pin to 3.12 is cheap and 3.12 was the "safe middle" the v1 spec already favored. Keep **B** in your pocket for two triggers: numpy-in-Ren'Py bundling proves fiddly, or you later need the shipped sim provably identical to CI (e.g. shared replays). The layer split is identical either way — only the transport changes — so choosing wrong is reversible.

---

## 5. The save-state contract

Ren'Py saves via pickle (wrapped as RevertableObjects) and rolls back game state. Two consequences drive the rules below.

**Persist (all serializable):** trace dicts, belief-DB state, the pending-order queue, the season clock, the player's choices, and **the seed**.

**Never persist:** numpy arrays, `Battle`/sim objects, or RNG state. To resume a battle, **re-run from the saved `(scenario, seed)`** — the sim is deterministic, so the state reconstructs exactly. Persisting the seed instead of the RNG object is both smaller and more correct.

This keeps saves tiny and rollback cheap, and it leans on the determinism you already built rather than fighting Ren'Py's pickler.

---

## 6. The 3.12 re-pin (only if Model A)

Concrete deltas to `pyproject.toml` and CI:

```toml
requires-python = "==3.12.*"          # was ==3.14.*  — match Ren'Py 8.5.3's bundled Python
dependencies = [
    "numpy==2.4.6",                   # unchanged — cp312 wheels exist, OpenBLAS bundled
    "rich~=15.0",
]
```

- **Re-bless both golden hashes** (`GOLDEN_HASH`, `CHAIN_GOLDEN_HASH`) under the 3.12 / cp312 runtime — different interpreter and numpy build means the committed hashes from 3.14 will not match.
- **Point the CI matrix's Python at 3.12** so CI tests what ships. Keep the fail-soft off-pin numpy leg, and fix its coordinate per the last review: target `numpy==2.5.0rc1` (the newest that actually exists) until 2.5.0 final ships, so the cross-version tripwire checks a real, different stream instead of 404-ing.
- Model B skips all of this — CI stays 3.14, because the subprocess sim *is* the 3.14 package.

---

## 7. Rollback partition — a day-one task, not polish

Ren'Py's signature feature (rewind) directly contradicts the irrevocable-order law. Partition it:

- **Live command layer → block rollback.** After the player commits an order, prevent rewinding past the commitment:

```renpy
label commit_order(order):
    python:
        season.queue_order(order)        # Layer 1: pushes onto the in-flight queue
        renpy.block_rollback()           # the order cannot be recalled — enforce it
    return
```

  (Globally, `config.rollback_enabled = False` is the blunt instrument; `renpy.block_rollback()` per-commitment is the precise one and preserves rewind for non-committal UI navigation.)

- **Archive layer → rollback *is* the mechanic.** Post-battle, re-enable scrubbing and bind it to the chronicle-vs-trace toggle: the same Layer-2 trace, rendered two ways (the tapestry's arrow vs. the trace's sword). You cannot rewind the war; you can re-read it.

If this isn't done on day one, the default rewind silently lets a playtester undo a lost battle, and the game's central law quietly breaks without an error.

---

## 8. The turn loop (the call pattern)

```renpy
label station_scene(station):
    # 1. Render the Table from current belief state (Layer 2 → a Ren'Py screen)
    call screen the_table(belief=season.belief_view(station))

    # 2. Player picks an order as a dialogue choice
    menu:
        "Hold the ridge.":
            call commit_order("hold_ridge")     # → queue + block_rollback
        "Ride to the hill.":
            $ season.move_station("HILL")        # switches vantage + belief DB

    # 3. Advance the clock — separate act; matured orders resolve on geography's clock
    $ event = season.advance()                   # Layer 1 steps; returns next decision point

    # 4. Jump to the scene the event names (officer report, contact, outcome landing)
    jump expression event.scene
```

Battles are a call into Layer 1 (`run_chain_1415` / `Battle.run()`), returning a trace that the Archive renders as chronicle — never animated. The station model, the pending-order queue, and the decision-point events this loop relies on **already exist in `season.py`**; Ren'Py is rendering them, not inventing them.

---

## 9. Day-one checklist

- [ ] Layer split enforced: `core/` imports nothing from Ren'Py; Ren'Py touches no numpy (the trace is the only contract).
- [ ] Pick **Model A** (in-process, re-pin 3.12) or **Model B** (subprocess, keep 3.14). Default A.
- [ ] If A: re-pin `requires-python==3.12.*`, re-bless both golden hashes, point CI Python at 3.12.
- [ ] Fix the off-pin CI leg coordinate to `numpy==2.5.0rc1` (carried from the last review).
- [ ] Keep numpy **transient**: run sim → extract serializable trace → discard sim objects.
- [ ] Persist only serializable state **plus the seed**; reconstruct battles by re-running, never by pickling sim objects.
- [ ] `renpy.block_rollback()` on every committed order; rollback/scrub re-enabled only in the Archive.
- [ ] Confirm the few *parametric* orders (which ford, which wing, how long to hold) fit menu choices; build a custom screen for any that don't.
- [ ] Accept the ceiling: no animated battle Window. The chronicle/Archive surface is the battle view.

---

*This is an integration sketch, not an implementation. The simulation core, validation battery, and reference code live in the project repository; the audit spec (v2) and UI spec are its companions.*
