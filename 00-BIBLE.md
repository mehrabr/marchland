# MARCHLAND — The Design Bible
### The complete buildable specification. Everything in this document is backed by a design addendum (docs/) and, where marked ▣, by running validated code (code/, results/).

**How to use this in a Claude Code project:** this document is the spec; the addenda are the reasoning; the code is the reference implementation of three subsystems; the results are the acceptance baselines. Start at Part VIII (the build plan), keep Part V (the battery) green at all times, and treat Part I as non-negotiable.

---

## PART I — THE LAWS

1. **No essences.** No per-people or per-unit quality coefficient may exist anywhere. Class A constants are identical for every human (a normative commitment with named empirical costs — Addendum R §3). An automated audit greps every data file for violations. The loaded-dice test: a probability becomes a stat the moment the dice are loaded differently per people.
2. **Receipts.** Every number that differs between forces must answer: *what in-world action would change you?* Drill-days, calories, armor purchased, bonds formed, roads built. (Constants registry classes: A bodies · B technology · C campaign/geography state · D institutions/customs · E trained capacities/priors.)
3. **Chance proposes; structure disposes.** Events are sampled from mechanistic hazards; whether they propagate is determined by structure. The ensemble (K seeds) measures distance-to-criticality; chronicle language ("a near-run thing") is gated on seed splits.
4. **Hard to predict, easy to explain.** Every casualty carries a causal trace (the death certificate). Every battle replays bit-identically from (inputs, seed). The Archive can answer *why* for anything.
5. **Casualties live in the pursuit.** Formations fail by percolation (coverage losing its giant component), not attrition-to-zero; pre-break deaths ≤ ~10% is a battery target.
6. **You command; you do not pilot.** Orders travel at rider speed to banners; repertoires gate what can be ordered; units appraise orders. The covenant goes on the box.
7. **No eye without a body; no body without an era.** Camera knowledge = seat knowledge. Omniscience is legitimate only over your own beliefs (the Table) or over history (the Archive).
8. **Calibrate once, freeze, then test.** Constants tuned on one scenario are frozen across all others; only B/C/D/E receipts and geometry vary per scenario. Battery targets carry [range, source-grade A/B/C, note] — never point values (Addendum R §2).
9. **Battle is by consent or by trap.** Most campaign combat is small (30–300 men); pitched battle is rare punctuation the player mostly *prepares*.
10. **The writing of history is inside the model.** Chronicles are sources with sympathies; belief DBs diverge from truth; the patron audits from their beliefs. The trace is the only omniscient object, and it is locked in the Archive.

---

## PART II — ARCHITECTURE

**One model, three tiers** (Addendum F): BP-**Field** (1 agent = 1 man; attention arcs, bond graphs — offline lab + flagship set-pieces) / BP-**Lattice** ▣ (1 agent ≈ 5–10 men; density fields — the workhorse, every fought battle) / BP-**Front** (fitted response curves — skirmishes, AI lookahead; re-fitted in CI from Lattice ensembles whenever mechanics change). Tiers share state variables, not just outcomes (`enemy_bearing_spread` is one number at three radii: a soldier's panic, a wing's envelopment, an operational encirclement). The Day Layer ▣ (march/siege clocks) and the campaign graph sit above, exchanging state through the chain protocol (Part III-D).

**Headless core + clients.** The simulation is an engine-agnostic library (target: Rust; reference: Python in code/). Determinism: per-agent RNG substreams; replay = (inputs, seed, sim-version); deterministic mode = hazard accumulation with **separate streams per event type** and quasi-random placement (shared accumulators alias catastrophically — Addendum E §3). Clients are trace players: CLI first, Unity/Unreal later (Part VII).

**Proposed Claude Code repo layout:**
```
/core        sim library: lattice, siege, march, chain, trace
/data        culture files, scenarios, calibration (the mod API)
/battery     validation runner; CI gate — must stay green
/clients/cli the dispatch game (Direction C interface, dev surface)
/tools       receipts-grep, ensemble runner, chronicle generator
```

---

## PART III — THE MODELS (frozen constants; reference code in code/)

### III-A. BP-Lattice battle resolver ▣ (`marchland_toy.py`; Addenda B, D, E, R)
Grid-density approximation; 2m cells, 2s ticks; 9-cell smoothed fields per side (standing, routing, persistent dead-piles decaying ×0.985/tick).

```
CLASS A (frozen):
λ_opening = 0.0008/s · err · (1 + 2.0·fatigue) · (1 + 2.2·load)
load      = clip( eff_foe/own − 1 − cover, 0, 2.5 )
eff_foe   = min(foe, 1.6·own + 2)            # frontage cap: excess presses, not fights
cover     = clip((own−1)·0.35, 0, 1.2)·rubble + cover_bonus(terrain)·(¬breach)
            rubble: breach bands ×0.4 for BOTH sides (no ranks on rubble)
P(down|opening) = 0.45 · (1 − 0.8·armor)
volley    : p_hit = 0.008·(1−0.9·armor)·(1−0.5·prone)·range_falloff; suppress ×5
appraisal : cue = 3.2·clip(bodies_here/6) + 2.4·clip(routers_here/4) + 0.9·load
            + 2.6·clip(behind/4)·(¬allround) + 1.0·fatigue + 1.4·banner_lost
            + 0.8·display_pressure − 1.1·belief − 0.3·cover
            flee when cue > threshold_i; thresholds one universal spread 1.0–2.2
fatigue   : +0.0035/s engaged (+again over crowd_cap); −0.0008/s resting
horses    : balk vs foe-density ≥ 3 (formed line = solid obstacle); penetrate scattered
break     : standing < 45% of side  OR  wall carried (≥300 stormers standing inside)
pursuit   : 0.02·intensity/s vs caught routers; capture by quarter custom (cap_p)
rout speed: 3.0·(1−0.6·fat)·mud·(1−0.4·armor)   # armor in mud is a death trap
```
Mechanics inventory: stakes; mud bands; walls as **contact filters** with gates (ladders keep rampart cover; breaches strip it); gate funneling; halt-inside; supply points with distance-decay resupply (`exp(−d/d0)`); delayed cohorts; feints tempting `disc<0.35`; leader-risk lottery when local density thins; all-round flag (square drill) zeroing the behind term. **Known misses to fix first (Part IX):** phase pacing (assault–repulse–lull), rank-relief roles, converging-horn pursuit.

### III-B. Siege clock ▣ (`siege_clock.py`; Addendum R)
Day ticks. Besieger disease `0.0012·(1+0.55·week)·camp_factor` races town hunger and breach progress; **summons-and-terms**: garrison strikes a conditional-surrender pact (yield in 8 days absent relief) once breach practicable OR 28 honorable days OR stores <10, if relief >21 days out; besieger storms only under clock pressure (breach cost 18% of effectives; no-breach 45%). Outcomes: NEGOTIATED / STORMED+sack / RELIEVED / ABANDONED.

### III-C. March model v2 ▣ (`march_model.py`; Addenda S, T)
Day ticks; the army versus entropy. Registry: **A** grain 1.4kg · water 3kg · 2.5mph · 10h light · thirst 0.06/day·heat · straggle 0.004·(pace/13)^2.2·(1+1.5fat)·weather·(×3 starving) · desert 0.0015·home_pull·(1+3·arrears)·(0.5+dispersal)·(2−coh) · disease 0.0009·env. **B** mode table {porter 30kg/1.4 · pack 100/6 · ox 540/12 @2mph · wagon 550/22, col 0.0125 mi ea}. **C** land density, season factor, water_ok, roads, heat. **D** officers (regather 0.55·officers·camp_q nightly), depot schedules, desert_share, discipline. The spine: `need = men·1.4 + Σ carrier.eat·(0.6 if green)` vs `intake = depots + min(swept·density·season·0.10, need·1.6)·(0.5+0.5·coh)`; column physics gate pace (clearing hours off daylight); **pace buys time with order**; desertion needs a destination; dry streaks beyond carried water kill in days.

### III-D. The chain protocol ▣ (Addendum S §3)
Models compose by field mapping, never by assertion: siege → `fit = N·(1−unfit_frac)` → march `start`; march → battle: `fat0 = arrival_fatigue − 0.3·rest_nights` (floor 0), `belief` adjusted by starving/cornered receipts, `n` from `effective`. Validated end-to-end on 1415: Harfleur (87% negotiated, 27% unfit) → 17-day march (7,771 effective, fat 0.55) → Agincourt with the march's bill (English win 10/10, all graded ranges hold).

---

## PART IV — SCHEMAS (the data layer is the mod API)

**Culture file:** doctrine vocabulary (closed condition/action sets; rule lists as ordered data — Addendum A); role list with repertoire keys (no file-closer role → no line relief, greyed out; killing officers deletes menu items — Addendum K); station price list (Front Rank / Knot / Hill / Camp: each a tuple of information set, lever set, anchor radius, lottery, latency, legitimacy price — Addendum J); authority edge types + succession rules (institutional promotes · kinship passes with a shudder · charismatic dangles · purchased — Addendum K); initiative norm (act-then-report ↔ ask-then-act); quarter customs (cap_p); career frame (commission generator parameters); tech four-layer entries (knowledge/kit/institution/license with per-layer diffusion clocks — Addendum O); art-language pack reference.

**Officer node:** role · authority_in (typed) · priors (class E, from record) · bonds (anchor = relationships) · record (the file; there is no character sheet) · trust ledger about the commander (low trust = safe interpretation, not a mutiny bit) · succession rule. Orders are **interpreted against the recipient's belief DB**, never the sender's (Balaclava is a standing possibility, not a script).

**Scenario file:** geometry + cohort receipts only (the receipts grep runs here). **Calibration file:** every target = `[range, grade A|B|C, source-note]`; see `results/calibration_regrade.json`.

---

## PART V — THE VALIDATION BATTERY ▣ (CI gate; results/ holds baselines)

| entry | targets (grade) | status |
|---|---|---|
| Isandlwana line (16 seeds) | Zulu win (A) ✓ · ammo-starves-before-break (A) 16/16 ✓ · defender dead 50–90% (B) **40% MISS** · Zulu loss 5–20% (C) ✓ |
| Isandlwana square | flips distribution (A, paper) ✓ — holds 5/12, survives 2.6×; full hold needs relief roles |
| Agincourt (12) | English win (A) ✓ · French 4–11k incl. 1,270 prisoners *with no surrender rule* (C) ✓ · English 112–600 (C) 450 ✓ · ≥5:1 (B) 11:1 ✓ |
| Hastings (12) | Norman win (A) ✓ · "near-run" (C — Wellington's phrase, wrong millennium) 0%: tension, re-scoped · pre-break ≤10% (B) **20% MISS → phase pacing** · Harold falls (A) 7/12 ✓ |
| Harfleur siege (100) | negotiated (A) 87% ✓ · 30–40 days (A) 38 ✓ · unfit 15–35% (C) 27% ✓ · storm rare (A) 13%: flagged |
| Assault battery (12 ea) | escalade-vs-fresh repulsed (B) 12/12 ✓ · breach-vs-starved 5/12 — the *target* corrected by Badajoz (breaches were cheaper, not reliable) · fresh→starved monotone ✓ |
| Marches (100 ea) | Agincourt 17d/17 ✓ · Danube 35d, 3.6% wastage ✓ · 1812 62% pre-battle loss (C 45–65) ✓ · Gedrosia 76% dead = Plutarch's high tradition, flagged · Sherman 24d, 4.2% ✓ |
| Chain 1415 | siege→march→battle closes; corrected English fatigue still passes ✓ |

Rule: every mechanic change reruns the battery; new content ships with new entries; misses are findings, recorded, never tuned away silently.

---

## PART VI — GAME DESIGN

**The frame:** the commission season (Addendum J) — a patron deals an army (muster rolls as cards, receipts visible), a mission (intercept · chevauchée · siege · relief · escort · hold · suppress = the historicity tests), strings (deadlines, co-commanders, imposed quarter policy); muster → operations → audit (from the patron's *belief DB* — injustice both ways) → winter court (credit/blame, ransoms incl. the player's own body, promotions, next commission). Career: fame, scars, aging (Front Rank pricier yearly), named staff, the memoir auto-compiled from chronicles. **Rupture starts** (Addendum Q): *pick a wound* — Cannae · post-Agincourt France · Jena (Krümper caps) · Manzikert (the failed rebuild) · post-Isandlwana (the wrong-dossier tutorial: ammo-box myth vs the trace) · alt-history **promoted from validated seeds** ("the square held in 5 of 12 worlds; you live in one"). Guards: rebuilds ossify (scars), rivals rebuild (Red Queen), dossiers can be wrong (license discount ⊥ truth_alignment).

**The loops** (Addendum M): triage (proposals at rider latency; *ignore* is a verb) · plan-poker (staff forecast vs Archive truth = information about your marshal) · dealt-hand season · legacy · the meta-loop (the game teaches by trace; study is a verb). **The judgment of men:** promotion/assignment as the mastery axis — files not numbers; FM's loop + the ground truth FM can't have (ensembles score your attribution errors); culture prices promotability (honors vs offices vs purchase); competence ⊥ promotability is the gameplay. **Progression** (Addendum O): no tree; victory→standing→license→reform→capability; knowledge leaks (deserters carry blueprints), kit copies in seasons, institutions endure, the honest no is content; the Maurice endgame: author a doctrine, found a school, watch it diffuse.

**Adjudication** (Addendum E): stochastic micro + ensemble-median presentation (default) · deterministic hazard mode (opt-in; stream separation + quasi-random placement mandatory) · matrix/argument ledger (Direction C's voice). Officers propose via Front-tier lookahead; the AI reasons in the world's own physics.

---

## PART VII — PRESENTATION (Addenda H, I, U)

**The Table:** the belief DB as a living miniature world, the command surface at every zoom. **Uncertainty as finish:** rumor = charcoal sketch → scouted = unpainted lead → confirmed = painted miniature → stale = dust. Orders are physical (pieces slid, notes sealed, rider miniatures crossing the table = latency visible). **The Window:** seat-locked 3D in the era's art (Bayeux 1066 · byōbu/ukiyo-e Sengoku · engraving 1879); render LOD mirrors sim tiers (skeletal near / instanced crowds mid / painted density far — gold-leaf clouds are literal fog); sound is the honest real-time channel. **The Dive:** lean into the Table and fall into the miniature, blooming into the Window *only where knowledge permits* — the trailer and the thesis in four seconds. **The Archive:** post-battle free camera, death certificates clickable, the ensemble slider, the two-layer truth (the tapestry's arrow vs the trace's sword). Laws: no floating bars ever; the chronicle lies like sources; "near-run" only when seeds agree. Stations render as scene templates (the VN layer = the staff arguing the matrix ledger in faces).

---

## PART VIII — THE BUILD PLAN

**Prototype 0 — Claude Code, CLI, the 1415 vertical slice** ("the Commission of Harfleur"):
M0 port code/ into /core with tests pinned to results/ baselines (regression green).
M1 the two surviving misses: phase pacing (assault waves, lulls, re-forming) + relief roles; re-run battery — *Hastings becoming contested and the square holding are the milestones.*
M2 chain runner: one command plays siege→march→battle with the protocol fields; chronicle generator v0 (trace → prose with citations to certificates).
M3 the commission wrapper: dealt hand, the season clock, the audit from a belief DB, winter court as text scenes; opportunity feed (officer proposals via a stub Front tier).
M4 the Table v0 in text/2D: belief DB rendering with uncertainty-as-finish glyphs; dispatch latency visible.
M5 graded-battery CI + receipts grep as pre-commit; ensemble runner with chronicle gating.
M6 playtest gate: Kriegsspieler + Student personas; the covenant stated up front.

**The Unity path** (after P0 is fun in text): Rust core port (fixed-point decision day one; sim-version pinned replays) → Unity as trace-playback client → NPR spike (motion-coherence test on a Lattice trace) *before* renderer scoping → the Table in 3D → the Window for one era → the Dive. One era ships first; the second proves the pipeline.

---

## PART IX — OPEN LEDGER

Engine: phase pacing · relief/rotation roles · converging-horn pursuit + terrain traps (the Isandlwana kill-share) · BP-Front fitting + CI re-fit · intercept race on the graph (1066 double-march battery entry) · sack state + forage circuits (L-spec) · depletion-while-static as the burn clock · green-fodder season gate · riverine/rail mode rows · rupture mechanics (catastrophe-as-license, doctrine shock, scars) · wounded/escort, quarter signals, ransom objects in-engine · horse agents at Field tier. Product: chronicle prose quality bar · idle-tension playtests · aging that bites · the multi-vocal Archive · battery published with its historiography. Hard engineering: cross-platform determinism · replay version pinning · the crush degradation mode.

*The archive's docs/ folder holds the complete reasoning (main doc + Addenda A–U); code/ the reference implementations; results/ the baselines this bible's claims cite.*
