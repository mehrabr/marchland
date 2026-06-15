# MARCHLAND — Addendum E: The Umpire and the Dice
### Non-random adjudication, and the engine's first contact with real battles

**Extends:** Addenda A–D. **Brief:** explore how professional military wargames decide outcomes without (or beyond) dice — the proctor-judge tradition — and then put the toy engine on the table: run known historical battles and see whether the statless model reproduces them. Part 1 is the adjudication research and three implementable non-random modes. Part 2 is the experimental record, hits and misses both. Part 3 is what happened when we actually turned the dice off.

---

## Part 1 — How the proctor-judges do it

The tradition splits in 1876, and the split has been oscillating ever since.

**Rigid Kriegsspiel.** Reisswitz's 1824 game resolved everything by dice and loss tables — chance given "its due influence" as apparent insurance against umpire partiality. By about 1870 the failure mode was institutional: umpires, often very senior officers, spent the game leafing through volumes and ruling on fine legal points — clerks to the tables. Worse, as play got competitive the rules tightened, tactical reality sank under the rule book, and games sometimes produced results that defied military logic. The rules were auditable and the rules were wrong.

**Free Kriegsspiel.** Verdy du Vernois's *Beitrag zum Kriegsspiel* (1876) abolished the rulebook and most of the dice. The umpire collects the players' moves exactly as before, then renders a considered professional opinion on the outcome, drawn from his own knowledge of war. One published variant of the method shows the whole spectrum in a sentence: the umpire judges the situation, assigns odds, and rolls a single d6 — or uses no dice at all. Judgment first; variance as an optional knob on top of it.

**The decay problem.** Practitioners observing both Prussian history and modern navies report the same arc: professional-judgment adjudication works for roughly the first five to ten years after a war, while the umpires personally know what combat does. As that cohort ages out of the umpire chair, the push for written rules and combat-results tables returns. Expert judgment is a depleting institutional resource. Free Kriegsspiel doesn't fail on contact with the enemy; it fails on contact with retirement.

**Matrix games.** Chris Engle's 1988 form structures the judgment instead of replacing it. A player states an action and arguments for why it succeeds; others raise counterarguments; the umpire weighs the ledger, assigns probabilities to outcomes, and usually lets dice pick the branch. Adjudication can run by consensus, by umpire ruling, or dice-weighted — the published guidance treats these as interchangeable settings on one machine. The move that matters for MARCHLAND: the matrix game forces the factor ledger into the open. The umpire's reasoning stops being a private hunch and becomes a listable, contestable thing.

**The wheel's latest turn.** Modern computerized combat models are rigid Kriegsspiel again — the tables compiled into algorithms and hidden behind a user interface. The rules came back; they just stopped being readable. Which closes the loop on a hundred and fifty years of oscillation: *rules that defy military logic* on one side, *judgment that defies audit and retires with its owner* on the other.

### Where BP-Lattice sits

The historum thread ran this same oscillation in miniature — free-form judgment doesn't scale, per-matchup rules don't generalize, dice-on-tables feel false. Our answer, stated in the adjudication tradition's terms: **rigid adjudication whose rules are a mechanistic causal model with published receipts.** We automated the expert umpire and published his reasoning. The death certificate (Addendum D, Q1) is the umpire explaining a ruling; the receipts audit is the players checking his impartiality; the ensemble is his "considered opinion" with the consideration shown. The engine escapes the rigid pathology not by hiding the rules but by making them causal, and escapes the free pathology because this umpire's expertise is a versioned data file, not a colonel who retires.

That framing yields three concrete non-random modes, all cheap because the substrate already exists:

**Mode 1 — Deterministic hazard accumulation.** Every sampled event becomes accumulate-and-fire: an agent's opening fires when its integrated hazard ∫λ·dt crosses 1; volleys deliver their expected casualties with fractional remainders carried forward. No dice anywhere in the engine; every run of the same inputs is bit-identical. This is first-passage resolution — the Poisson process replaced by its own clock. What it buys and what it costs were measured, not guessed; Part 3 has the numbers.

**Mode 2 — The adjudicated interface (ensemble-modal).** Keep the stochastic micro. Run K seeds. Present the *median history* as the ruling, and keep the spread for the chronicle's honesty — "a near-run thing" is only ever said when the seed split says so. This is Verdy's umpire industrialized: he considers the situation (the ensemble is the consideration), states the expected outcome, and can show his work on demand. The player who wants a single authoritative answer gets one; the historian mode underneath stays honest.

**Mode 3 — The argument ledger, for Direction C.** In the dispatch game, engagements arrive as written reports anyway. Resolve them by printing the factor ledger as an umpire's reasoning: the arguments for (your receipts — fresher men, the ford, the harness), the arguments against (theirs), the ruling, and the odds it was given. Mechanically identical to Mode 2 underneath; presentationally it is a matrix game the machine plays against itself, in the epistolary register that direction wants.

**Recommendation:** stochastic micro with Mode 2 presentation as the shipping default; Mode 1 as an opt-in ruleset for competitive play and replay-perfect saves; Mode 3 as Direction C's native voice. **Verdict: CHANGE** — the three modes enter the spec, with the Part 3 engineering constraints attached to Mode 1.

---

## Part 2 — The engine meets four battles

### What was actually built

BP-Lattice/toy: a 1:10-scale, grid-density approximation of the Addendum B–C spec, ~520 lines of vectorized NumPy. One agent stands for ten men. Coverage is approximated by local friendly density rather than per-agent attention arcs; cohesion contagion by locally *visible* routers and bodies rather than explicit bond graphs; the Isandlwana encircling sweep is a scripted movement vector, exactly as the source paper scripted its regimental vectors. These coarsenings are declared, not hidden — the toy tests whether the *mechanisms* carry the load, not whether the full spec is finished.

Calibration discipline, borrowed from the Isandlwana paper: class A constants were tuned on smoke runs, then **frozen across all five scenarios.** The scenarios differ only in class B/C/D/E receipts and geometry. The frozen species-universal set:

```
lam0      = 0.0008 /s        opening hazard at zero load (every human)
lamx      = 2.2              exposure multiplier per unit local outnumber
frontage  : eff_foe = min(foe, 1.6·own + 2)   (excess attackers press, not fight)
p_down    = 0.45 · (1 − 0.8·armor)            opening → man down
volley    : p_hit = 0.008·(1 − 0.9·armor)·(1 − 0.5·prone)·range_falloff
            suppression breadth = 5 × p_hit
appraisal : cue = 3.2·clip(bodies_here/6) + 2.4·clip(routers_here/4)
            + 0.9·load + 2.6·behind·(¬all-round) + 1.0·fatigue
            + 1.4·banner_lost + 0.8·display_pressure − 1.1·belief − cover
body piles persist (decay 0.985/tick); flee thresholds: one universal
human spread, 1.0–2.2, identical distribution for every cohort
```

No quality coefficient exists anywhere in the scenario files; the receipts grep passes. Differences entered the runs only as: drill (error-under-load 0.7 for British regulars ↔ 1.4 for the NNC ↔ 1.3 for the fyrd), gear (armor 0.9 full harness ↔ 0.45 shield-wall coverage ↔ 0.0 no kit), campaign state (the fyrd starts at fatigue 0.15, off the Stamford Bridge march), cause-bonds (belief 0.85 for Zulu on home soil ↔ 0.35 for the pressed NNC), and doctrine flags (evade-prone, all-round square, hold-ground, pursuit discipline, feint repertoires).

### The scoreboard

| scenario | seeds | result | loser breaks (median s, range) | loser losses pre/post/captured | victor losses |
|---|---|---|---|---|---|
| Isandlwana, extended line | 16 | Zulu 16/16 | 598 (558–690) | 355 / 185 / 0 of 1,350 | 1,950 of 19,600 |
| Isandlwana, square (counterfactual) | 12 | Zulu 7/12 — **square holds 5/12** | 1,540 (1,082–2,562) | 250 / 20 / 0 of 690 | 1,705 of 19,000 |
| Agincourt | 12 | English 12/12 | 2,091 | 2,040 / 1,125 / 1,270 of 10,200 | 450 of 6,000 |
| Hastings | 12 | Norman 12/12 | 991 (902–1,026) | 1,425 / 545 / 40 of 7,000 | 685 of 7,500 |
| Hastings, drilled fyrd (counterfactual) | 12 | Norman 12/12 | 1,635 (902–2,344) | 1,800 / 425 / 5 of 7,000 | 880 of 7,500 |

### Reading the four battles

**Isandlwana, line — outcome, sequence, and asymmetry all land.** The Zulu win every seed, but the result that matters is *order*: in 16 of 16 seeds the far flank's ammunition starves before the line breaks. The supply-point distance decay produced the paper's signature failure sequence — fire holds the chest at range, the flank farthest from the camp runs dry first, suppression lifts there, and the rush comes through the silent stretch — without any rule that says so. Median Zulu losses are 10% of engaged, the historical band. The miss: total British and NNC dead come to 540 of 1,350 (40%) against the historical ~76% annihilation. Our routers escape the field too easily, because the encirclement is one scripted cohort instead of converging horns and there is no Fugitives' Drift terrain trap behind the camp. The historical kill happened in the pursuit; our pursuit underperforms, and the trace says exactly where.

**Isandlwana, square — the counterfactual flips, and the experiment found a missing mechanic.** Same constants, one drill flag (all-round facing) and the ammunition inside the perimeter. The distribution flips: in 5 of 12 seeds the square holds outright; in the other seven it survives 2.6× longer than the line and dies at half the casualties. The paper's counterfactual was stronger — their Zulu abandon the assault entirely. The diagnosis is the best result in this addendum: what the toy lacks is **rank relief** — fresh men rotating into the fighting ring while the ring's fatigue resets — which Addendum B already specified and the toy never implemented. Without rotation the perimeter's fatigue integrates monotonically and the square eventually erodes. The experiment independently rediscovered a mechanic the theory had already ordered. That is the validation loop doing its job.

**Agincourt — the mud fights, the prisoners emerge.** English win 12 of 12. French total losses run ~4,435 of 10,200, of which 1,270 are *taken prisoner* in the press — and there is no surrender rule in the toy; the captures emerge from routing into deep mud at ~0.8 fatigue in harness, where flight speed collapses below the pursuers' walk. A third of French losses fall after cohesion fails, matching the casualty-shape law. The arrows kill few men in plate (armor gates the volley sampler hard) but suppress and channel; what decides the melee is that French men-at-arms arrive at the English line averaging 0.8 fatigue, and λ's fatigue amplification does the rest — which is the modern historiography of the battle in one mechanism. English dead at 450 sit high against the chronicle range (the debate spans roughly 112–600) but order-correct against an enemy of 10,200.

**Hastings — the one we fail, and the failure is diagnostic.** Normans win 12 of 12; history says near-run thing, all day, decided late. Three misses, one root. First, English pre-break deaths are 20% of the army — violating our own law that casualties concentrate after collapse. Second, the break comes after ~17 minutes of continuous contact in an implausibly tight band (902–1,026s): too fast, too certain. Third, the counterfactual — drilling the fyrd so the feigned retreats tempt no one — extends survival 65% and triples the outcome spread but never flips a single seed. The shared root: **the toy fights one continuous contact, and the real day was paced** — assault, repulse, lull, re-form, again. Without lulls there is no fatigue recovery, no re-dressing of the line, no phase structure for fortune to live in; continuous hazard integration grinds the lighter-armored side down with near-certainty. The pieces that should matter all fire (Harold falls to the late-volley lottery in 7 of 12 seeds; the feint→pursuit→cavalry-penetration chain works mechanically); the *rhythm* is missing. Phase pacing goes on the punchlist as a first-class mechanic, not a patch.

**Across the board.** The engine classifies Agincourt and Isandlwana-line as structure-decided (no seed dissents), the square as genuinely contested (5/12 against 7/12), and Hastings as structure-decided when it should be contested. Two of the three "this was decided beforehand" calls match the historiography; the third is a measured, diagnosed miss. For a 520-line toy running frozen universal constants, the shape of that scoreboard is the argument: receipts plus geometry plus one shared human hazard already reproduce outcomes, internal sequences, casualty asymmetries, and a counterfactual flip — and where they don't, the causal trace says why, in mechanism, not in vibes.

---

## Part 3 — Turning the dice off

Mode 1 was implemented and run against Hastings. Three findings, one of them a failure worth keeping.

**The aliasing failure.** The first deterministic build shared a single hazard accumulator across event types, and the result was phase-locked nonsense: the death-check stream's large increments drove the opening stream's threshold crossings, event types entrained each other, and one army marched through an entire battle taking *exactly zero* casualties. The lesson generalizes: **dice don't just inject variance; they decorrelate.** Remove them and every periodicity in the system starts talking to every other. The fixes — separate accumulator streams per event type, and quasi-random (golden-ratio) initial placement so identical agents don't fire in lockstep — are now mandatory engineering for Mode 1, written into the spec.

**The canonical history, delivered.** With those fixes, deterministic Hastings produces a sane single adjudication (break at t=1,812; Norman dead 1,380), and repeat runs are bit-identical. Replay-perfect saves, no luck disputes, one authoritative ruling — the property the mode promised.

**Variance relocates; it does not die.** Perturbing the inputs by one fyrd file — 601 agents instead of 600, in an army of 1,450 — moves army-level Norman casualties 6.5% and the break time by eight seconds. Moving the English line one meter moves casualties 4%. In stochastic mode that same sensitivity is absorbed into seed variance and reported honestly as a distribution; in deterministic mode it surfaces as knife-edge dependence on initial conditions nobody can perceive. The dice were never the source of unpredictability — the criticality was (Addendum D, Q4). Which settles the recommendation: Mode 1 alone is one sample wearing a judge's robe. It is honest only with Mode 2's ensemble wrapped around any claim about what was *likely* — which is, historically, exactly what a free-Kriegsspiel umpire was: a single deterministic rollout of one expert's internal model, authoritative in tone, unaudited in variance.

---

## Punchlist

Engine: phase-pacing/assault-wave mechanic with disengagement and re-forming (the Hastings root cause); rank relief and rotation (the square's missing piece, spec'd in Addendum B); converging-horn pursuit and terrain traps (the Isandlwana kill-share gap); adjudication Modes 1–3 with stream separation and quasi-random placement as hard requirements; the ensemble runner formalized, with chronicle language ("a near-run thing") gated on seed splits.
Process: the receipts grep ran green across all five scenario files — no quality coefficient entered, none was needed.
Carried open: BP-Front fitting against these ensembles; the spacing experiment; wounded/escort and quarter mechanics (Addendum D) not yet in the toy.

Next battles queued for the harness once relief and pacing land: Sphacteria (the anti-Hanson test — light infantry refusing contact should beat hoplites without ever forming a line), Cannae (does the crush emerge from converging frontage caps), and a winter raid at 30 agents a side (the resolver earning its keep at the scale most of the campaign's fighting actually happens).
