# MARCHLAND — Milestone M7: The Meaning Layer & The Moving Army
### A Claude Code build phase integrating Addendum X with the panel's standing priorities

**Context.** Prototype 0 (the 1415 vertical slice, M0–M6) is built and on GitHub: the headless `core/`, the graded `battery/`, the dispatch `clients/cli/`, the `receipts_grep` audit. The README's open ledger shows M1 closed (Hastings baseline updated) with the converging-horn pursuit and the Harfleur storm flag still open. M7 is the next coherent phase. It does **not** start the Rust port — the panel was explicit that the port is the smaller job and must come *after* the design stops moving, and this milestone moves the design. M7 stays in Python, where iteration is cheap and the battery is the oracle.

---

## What M7 builds, in dependency order

### M7.0 — Clear the deferred sim debt first (it's load-bearing for everything after)
The panel merged two ledger items into one top priority: **the converging-horn pursuit fix and the steppe gap are the same hole** — both are weak kill-while-fleeing geometry. Build the pursuit/encirclement mechanic (closes the live `Isandlwana defender_dead_frac` miss, 40% → target 50–90%), then add **Carrhae** and **Sphacteria** as battery entries on the *frozen* constants. If the frozen constants can't produce Carrhae, the universality claim is provincial and we say so in `results/`. *Acceptance: Isandlwana kill-share enters target band; Carrhae and Sphacteria graded (pass or recorded miss).*

### M7.1 — The sensitivity harness (Olleus's non-optional)
`tools/sensitivity.py`: perturb every `core/constants.py` class-A value ±30%, re-run the full battery, emit a **load-bearing-vs-decorative table** — which results survive which perturbations. Wire into CI as a report (not a gate). *Acceptance: the table publishes; any battery pass that exists only at the fitted value is demoted to a flagged tension — including, per Olleus's conditional dissent, an honest verdict on whether the cue weights or the percolation geometry is doing the work.*

### M7.2 — The interpretation layer (Addendum X §2)
Insert the meaning transform between raw cues and the frozen universal threshold in `core/lattice.py` (`raw cues → transform → frozen threshold`). Add `core/meaning.py` (institution-of-meaning objects with `transform`, `carried_by`, `failure_conditions`, `break_effect`). Couple to officer death in `core/stations.py`/the officer model: killing a meaning's keeper severs it. *Acceptance: a cohort's reading of identical cues differs by data file alone, the substrate constants unchanged; a battery scenario where killing the cadre-officer measurably shifts the cohort's break point.*

### M7.3 — The two audit rules (Bret's law + Olleus's law, in code)
Extend `tools/receipts_grep.py`: **(a)** any `institution_of_meaning` with empty `failure_conditions` fails the build (the destroy-it test — Bret's standing watch that this is where essentialism re-enters years from now, enforced now); **(b)** any `sentiment.transmission` term referencing a quantity not in the tracked-receipts registry fails the build (no free contagion constants). *Acceptance: a deliberately-essentialist test fixture (a meaning with no failure condition) fails CI; a deliberately-unanchored sentiment fails CI.*

### M7.4 — The sentiment field (Addendum X §3)
`core/sentiment.py`: a scalar penetration field per cohort over the existing social/authority graph, ticked at campaign-day resolution by neighbor-coupling, every transmission term reusing march-model receipts (idle, hunger, arrears, bond) and resisted by intact officer authority; seeded by events (a pointless loss, a paid wage, a miracle, a won fight). Couples to M7.2: sentiment is the *transition* that flips the meaning *state*. *Acceptance: the winter-quarters battery entry below.*

### M7.5 — The battery entry that proves it: dissolution without a battle
A new `battery/entries/` scenario: a season of winter quarters / idle siege lines, unpaid, that **breaks an army without a single battle** — sentiment spreading from a seed through idle-hungry-unpaid channels until cohorts cross into desertion and rout-readiness. This is the genre's blind spot made a test (Bret's anchor: armies break between battles). *Acceptance: the army's effective strength and cohesion collapse on the historical pattern, driven only by tracked receipts, no combat events in the trace.*

### M7.6 — Render it on the Table (Dana's legibility requirement; Vikram's mitigation)
Extend `clients/cli/table.py`: sentiment renders as a visible field spreading across the player's own cohorts, in the same uncertainty grammar (true mood may require a present, trusted officer's report). Expose the levers as season verbs: dispatch an officer to counter a rumor, seed *follow-a-winner* with a small victory, pay arrears, rest the idle unit, break up a rotted cohort. *Acceptance: a player can watch a mood turn and intervene before it spreads — the system is steerable, not a hidden debuff.*

### M7.7 — The officer-AI battery (the panel's product crux — pulled forward)
Marcus + Dana reframed this from robustness chore to *the fun mechanism*: the dispatch-and-wait loop is only good if the subordinate is intelligent. `battery/entries/` scenarios scoring the officer model: does a flank commander refuse a suicidal order, exploit an open flank unprompted, misread an ambiguous dispatch in a *period-plausible* way (not a pathfinding way)? The officer reasons via Front-tier lookahead over its **own belief DB**, never the truth; its mistakes come from bad information. Expose the enemy's belief table in the post-battle Archive so "the AI plays under the covenant" is *verifiable*. *Acceptance: the officer-AI battery is green against the "wrong like a captain, never like pathfinding" bar; the tutorial is reframed to star this officer (a character hook, not a spreadsheet).*

---

## Sequencing & what M7 explicitly does NOT do

Order: **M7.0 → M7.1 → (M7.2, M7.3 together) → M7.4 → M7.5 → M7.6 → M7.7.** The deferred sim debt (7.0) and the harness (7.1) come first because every later claim is measured against the battery and the harness tells us which constants the new layers may safely lean on. The meaning layer (7.2) and its guards (7.3) ship together — never the transform without the audit that keeps it honest. The officer-AI battery (7.7) is last only because it is large and self-contained, not least in importance; the panel rated it co-critical with 7.0.

M7 does **not**: start the Rust port (after design freeze — panel consensus); regenerate baselines in fixed-point (that's the port's first task, not now); build the Window/NPR (the slice graduates to a 2D Table first, per Addendum U). Keep `core/` importing nothing from `clients/`; keep Python as the reference oracle indefinitely.

---

## The standing dissents M7 carries (not resolved — tracked)
- **Vikram:** every true-but-invisible system that overrides player intent widens the soul/buyer gap; M7.6's legibility mitigates but does not close it. *Watch: playtest whether sentiment reads as "agency" or as "my unit won't obey."*
- **Bret:** the meaning layer is where essentialism will re-enter years out via a rushed culture file; M7.3a enforces the destroy-it test in code, but the audit must never be weakened. *Watch: the test fixture stays in CI permanently.*
- **Olleus (conditional):** if M7.1's table shows the headline passes are insensitive to the cue weights, credit the percolation geometry, not the weights, in the docs. *Watch: M7.1 output rewrites the relevant claim honestly.*
- **Sarris:** even this layer cannot capture every institution of meaning; some differences in organized fear were neither essences nor receipts. *Watch: the layer is documented as a better approximation, not a solution.*

**The phase in one line:** make the army a population of beliefs in motion — meaning as the state, sentiment as the transition, the Table as the place the player steers it — after first paying the sim debt the panel said was secretly the same hole, and before the port the panel said must wait.
