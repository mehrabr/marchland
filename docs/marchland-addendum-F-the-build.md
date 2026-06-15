# MARCHLAND — Addendum F: The Build
### Choosing among our own options, and the shape of the actual software

**Extends:** Addenda A–E. **Brief:** five documents have accumulated more design than any one game can ship. This addendum inventories the real choice space, makes recommendations, and answers the engineering question directly: which of these systems is the flexible one, and what can feasibly be built as the core software of a strategy video game.

---

## 1 — What we are actually choosing between

The project holds three kinds of options, and they are often discussed as if they competed when they don't.

**Resolver fidelities.** BP-Field (every man an agent with attention arcs and bond edges — Sher Khan's vision, the Scogings–Hawick lineage), BP-Lattice (the grid-density approximation the toy implemented — coverage as local density, contagion as visible routers and bodies), and BP-Front (the cheap 1D operational resolver from Addendum A, *fitted* to ensembles of the richer tiers rather than designed from intuition).

**Adjudication modes.** Stochastic micro with the ensemble-median presented as the umpire's ruling; deterministic hazard accumulation for canonical, replay-perfect histories; the matrix-style argument ledger for the dispatch register. Addendum E settled their relationship: one engine, three interfaces.

**Campaign directions.** A (the Walking City), B (the Spider's Web), C (the King's Post). The main document framed these as alternative games to choose between.

The recommendation that organizes everything else: **stop treating any of these as alternatives.** The fidelities are zoom levels of one model; the adjudication modes are presentation layers over one engine; the campaign directions are a substrate, a systems layer, and an interface that stack. The flexible system isn't one of the options — it's the architecture that holds them in a single consistent vocabulary.

---

## 2 — One model, three tiers

The strongest empirical lesson from Addendum E was not that the toy reproduced battles. It was *what the misses were made of*. Where the toy failed (the square's partial hold, Hastings' grind), the missing ingredient was never resolution — it was a **mechanism** (rank relief, phase pacing). The grid-density coarsening, one agent for ten men, no explicit bond graph: none of it cost us the outcome, the internal sequence, the casualty asymmetry, or the counterfactual flip. Mechanisms carry the load; resolution decorates it.

That finding licenses the tiered architecture:

| | **BP-Field** | **BP-Lattice** | **BP-Front** |
|---|---|---|---|
| unit of simulation | one agent = one man; arcs, bond edges | one agent = ~5–10 men; density fields | a front segment; fitted response curves |
| cost per battle | high (offline-friendly) | low (real-time at scale) | trivial (microseconds) |
| role in the game | laboratory + flagship set-pieces | **the workhorse**: every fought battle | cloud-edge skirmishes; AI lookahead; forecasts |
| can discover new dynamics | yes | partially | **no — by construction** |
| validated against | history (the battery) | history (Addendum E) + Field ensembles | Lattice ensembles (the fitting pipeline) |
| failure mode | perf, debugging at 60k agents | misses mechanisms below its floor | silently stale when tiers above change |

The contract between tiers is the discipline that makes this one model rather than three: **tiers share state variables, not just outcomes.** `enemy_bearing_spread` is the worked example — the same number read at three radii is a soldier's panic, a wing's envelopment, and an operational encirclement. Fatigue, supply, belief, and the bond/cohesion summary all cross tiers the same way. A battle can therefore *change tier mid-fight* (the player zooms into a flank; the cloud-edge skirmish escalates into something worth full resolution) by handing state across, not by translating between unrelated games.

The fitting pipeline (Addendum A §6) is what keeps Front honest: it is re-fitted, in CI, against Lattice ensembles every time a mechanism lands. Front is not a design; it is a *compression*, and compressions must be recompressed when the source changes. The day Front's curves are hand-tweaked to "feel right" is the day the tabletop ancestor gets back in.

**Recommendation:** Lattice is the core product surface. Field is the offline laboratory (where relief drills, the crush, and the spacing experiments get studied honestly) and the renderer's flagship moments. Front is plumbing — and, crucially, the AI's imagination: the opponent evaluates which opportunities to sponsor by running thousands of Front-tier forecasts, which means the AI reasons with the same model the world runs on, just compressed. No cheating layer to write, no rubber-band morale for the AI to exploit, and the AI's "judgment" inherits every receipt.

---

## 3 — The campaign stack: substrate, layer, interface

The same de-confliction applies upstairs. Direction B is not a game competing with A and C; it is the **substrate** — the road graph, the seasonal supply field, the belief database, battle-by-consent, and the opportunity feed were all specified as shared infrastructure in the main document's §4 before any direction used them. Direction A is a **systems layer** on that substrate: camps, entrenchments, the burn clock, and the muster are node-state mechanics on B's graph; the Walking City is what a concentrated cloud *is* when you look at it standing still. Direction C is an **interface**: the epistemic game of dispatches and stale reports is a way of *presenting* the substrate's belief DB, and it costs almost nothing once the belief DB exists — which it must anyway, because fog of war was never optional.

So the stack ships in this order: B's substrate (the world), A's layer (the army as a living object on it), C's interface (how much truth the player is allowed). And C has a second job nobody planned: it is the **CLI-first development surface.** A dispatch game is playable in plain text the day the substrate runs, months before a renderer exists. The entire campaign can be designed, tuned, and playtested as an epistolary terminal game — which suits the project's ethos and removes the single biggest schedule risk in strategy development, which is waiting on graphics to find out whether the game is any good.

---

## 4 — The software shape

What gets built, concretely:

```
sim core (Rust or C#/Burst; headless library, no engine dependency)
├── world graph + supply field + belief DB        (substrate, Direction B)
├── army/camp objects, burn clocks, muster        (layer, Direction A)
├── resolver tiers: Front / Lattice / Field       (one schema, three floors)
├── seeded determinism: per-agent RNG substreams,
│   replay = (inputs, seed); det mode w/ stream
│   separation + quasi-random placement           (Addendum E, mandatory)
├── trace system: every event causally tagged →
│   death certificates, chronicle generator       (first-class, not logging)
└── data schema: doctrines, receipts, customs as
    versioned files; receipts-audit grep in CI    (the moddability surface)

presentation (separate processes/clients)
├── CLI / dispatch client (Direction C)           ← ships first, is the dev tool
├── 2D operational map client
└── 3D battle renderer (last, optional at MVP)
```

Three properties of this shape do the flexibility work. The **headless core** means the simulation is a library: the CLI client, the eventual renderer, the validation battery, the AI's lookahead, and a modder's experiment harness are all just callers. The **data schema** means a new culture or century is a content drop that must pass the receipts audit, not a code branch — the closed condition/action vocabularies from Addendum A are the modding API, and the historical battery doubles as the content pipeline's acceptance test (every shipped culture comes with the battles that validate it). The **trace system** means the chronicle, the post-battle explanation, the matrix-mode ledger, and the debugging tools are one subsystem; "hard to predict, easy to explain" becomes a feature you build once and surface four ways.

---

## 5 — Feasibility, with numbers

The toy is the existence proof at the low end: ~2,000 agents, full battle histories in seconds per run, in *interpreted Python on one core*. The reference paper ran 20,000+ agents with per-agent rules on 2012 workstation hardware. Commercial strategy titles have shipped real-time battles with tens of thousands of animated agents for two decades. A compiled Lattice tier with spatial hashing is O(N) per tick with small constants; 50–100k agents at simulation rates well above real time is established territory on a modern desktop CPU, before GPU compute is even considered. The Field tier at 20–60k agents is heavier (O(N·k) neighbor work, the bond graph) but it runs offline and in set-pieces, where a 30Hz target on 8 cores is a reasonable engineering estimate rather than a research bet.

The honest cost center is **ensembles**. The adjudicated interface wants K=16–64 seeds per committed battle. Mitigations, in order of value: ensembles run at Lattice tier even when the player will watch a Field-tier rendering (the tiers share variables — the forecast doesn't need the decoration); they run headless and faster than real time; they amortize into the deployment phase (the umpire deliberates while the player arranges the line); and most of the campaign's combat is 30–300 men at the cloud's edges, where a 64-seed ensemble is milliseconds. The flagship pitched battle with a full ensemble is a loading-screen moment, and the design can afford it because the design makes pitched battles *rare*.

The adversarial perf case remains the crush — thousands of agents in one cell — and the mitigation remains the one from Addendum C: a crowd-field degradation mode that the engine enters deliberately, which is also the *correct physics* for Cannae conditions, where individual agency genuinely collapsed.

---

## 6 — The road not taken

There is a cheaper build: keep the presentation layer — chronicles, receipts language, the dispatch interface — and run a conventional stat engine underneath it. It would ship a year sooner and it would be a lie at the exact load-bearing joint. Addendum E's results are the rebuttal in data: the ammunition-before-break ordering at Isandlwana, the prisoners emerging from mud and fatigue at Agincourt with no surrender rule, the square flipping a distribution via a single drill flag — these are *sequences and counterfactuals*, the two things a stat table cannot produce and the two things the entire project exists to produce. A stat core under a mechanistic costume forfeits the thesis while keeping its expenses. If the budget ever forces that trade, the correct move is to cut scope (fewer cultures, smaller battles), never fidelity of mechanism.

---

## 7 — Risks, honestly

Cross-platform determinism is real engineering (floating-point divergence breaks replays and lockstep multiplayer; the answer is fixed-point math or strict-IEEE discipline in the core, decided on day one, painful to retrofit). Content authoring is the hidden cost of the receipts doctrine — every culture needs researched drill-days, gear economics, and customs, which is the game's promise and its budget line; the schema makes it data, not cheap. The Front tier will drift stale without CI re-fitting, and a stale Front quietly corrupts the AI's judgment. And the design risk above all of them: player agency is deliberately sparse at battle time, so the game lives or dies on making *preparation legible* — the forecast, the chronicle, and the opportunity feed are not UI chrome, they are the actual game surface, and they deserve the polish budget a conventional title would spend on unit-response barks.

---

## 8 — Build order, revised

1. **Port the toy to the compiled core** (Lattice tier, both adjudication modes, traces, substreams). The validation battery from Addendum E is the acceptance suite; it must stay green.
2. **Land the two mechanisms the experiments ordered:** rank relief and phase pacing. Re-run the battery; Hastings becoming a near-run thing is the milestone.
3. **Fit BP-Front** from Lattice ensembles; stand up the CI re-fitting loop.
4. **Substrate (B):** graph world, supply field, belief DB, battle-by-consent, opportunity feed — playable in the CLI as a dispatch game (C's interface arrives here for free).
5. **Layer (A):** camps, burn clocks, muster, the two-cities standoff.
6. **Field tier** as the offline laboratory; promote it to flagship set-pieces when perf allows.
7. **Renderer last.** By then the game has been fun in a terminal for a year, or the project has learned it cheaply.

**Verdict:** the flexible system is the tiered single-model architecture — Lattice at its center, receipts as its content format, the trace as its voice — and it is feasible as core software on the strength of a 520-line Python toy that already did the hard part slowly. Everything else is engineering.
