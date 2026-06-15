# MARCHLAND — Addendum C: The Walkthrough and Three Stress Tests
### One fight, examined for bias, scale, and flexibility

**Extends:** Addendum B (BP-Lattice). Contents: §1 a worked example of two medieval units fighting under the statless engine; §2 the example audited for biases Devereaux has criticized that survive in it; §3 performance analysis at battle scale; §4 the cross-cultural build test — an ibutho against an ashigaru company; §5 the punchlist of engine changes these tests force.

---

## 1. The fight: Wexcombe levy vs. the Earl's serjeants

Two units, defined entirely in residue classes (Addendum B) — note what is *absent*: no attack, no defense, no leadership, no morale value anywhere.

```
WEXCOMBE LEVY (78 men)              EARL'S SERJEANTS (60 men)
B  spears 2.2m, round shields,      B  spears 2.4m, kite shields,
   jacks; helmets ~1 in 3              mail + gambeson, helmets
C  fed (home district), fresh,      C  fed, 9 days on the road,
   serving by obligation               wages current
D  shield wall (loose order);       D  shield wall (close order);
   no file roles, no relief,           file leaders & closers,
   rally point = the church           relief swap, rally-on-banner,
   they can see from here              horn signals
E  high error-under-load (no        E  low error-under-load
   drill-days); green priors           (140 drill-days); priors
                                       from two prior fields
bonds: dense kin/village clusters   bonds: uniform drill-made edges
   (strong, brittle to grief)          + edges to the captain
```

**Phase 1 — Approach (ticks 0–300).** Both lattices form. The levy's loose order means each man's left/right arcs are only partially neighbor-covered; their big round shields make up some of it as self-coverage. Appraisal across both lines is quiet: every cue reads safe — covered arcs, file-mates present, banner (or church tower) visible, no rearward flow. The serjeants advance in step (class D: drilled cadence keeps the lattice intact while moving — the levy advancing would shed coverage; standing, it sheds none, so it stands).

**Phase 2 — Contact pulses (ticks 300–900).** Front ranks engage. One agent's frame, mid-fight:

```
L31 "Hob," tick 412
  arcs: F threat ×1 (attended 1.0), self-shield
        L covered (L30)   R covered (L32)   B covered (rank 2)
  exposure: ~0   →  fighting at human baseline
  act: melee_press → recoil exchange, fatigue +
```

This is the engine's normal state and the brief's "ideal scenario": one man, one opponent, everything else delegated to the formation. At baseline, both sides generate openings at the same human rate. The difference accrues at the margins: the serjeants' drilled error-rate means fewer self-made openings as fatigue climbs, and their mail converts torso wounds to bruises (class B zone physics). Nine minutes in, the ledger is unspectacular and historically shaped: levy 5 dead, 11 hurt; serjeants 2 dead, 7 hurt. Nobody has won anything.

**Phase 3 — The tear (ticks ~900–1050).** L32 goes down. Instantly, mechanically:

```
L31 "Hob," tick 921
  arcs: R now UNCOVERED + threat (unattended, 0.3 peripheral)
  exposure: 0.7/s and climbing → opening probability rising
  appraisal: file-mate down (kin edge — cousin), banner visible,
             no rearward flow yet
  act: melee_press, but edge_back pressure accruing
```

Hob's problem is no longer his opponent; it is the arc nobody covers. The levy has no file-closer (class D absence), so when the man behind L32's gap edges rearward, no role exists whose job is to stand in that path. Two ranks back, the dead man's brother takes a grief shock through a kin edge — the levy's bond type is strong and brittle, exactly as built. The serjeants' captain, performing the lattice-repair role, rotates a fresh man into his own line's worst spot (relief swap, class D); the levy has no such verb.

**Phase 4 — Percolation (ticks ~1050–1150).** Seepage on the levy left crosses into cascade: edging men become a rearward flow, the flow is an observable fact, the fact propagates along bond edges faster than any spear. The coverage graph's left third loses connection to the banner cluster — union-find reports the giant component gone. The chronicle writes *the Wexcombe men broke from the left*, and means it as a statement about graph connectivity. Note what did **not** happen: no morale meter crossed zero; seventy individual appraisals tipped, in a spatial order a replay can show you.

**Phase 5 — Pursuit (ticks 1150+).** Serjeants' doctrine gates pursuit (`target_routing → pursue`, with drilled pursuit-discipline keeping half the line dressed — the file closers' last job). Running men have uncovered backs by definition. Final ledger: levy — 5 dead in the fight, 21 in the flight, the rest dispersed toward the church and recoverable; serjeants — 2 dead, 7 wounded. Pre-break losses ~6%, killing concentrated after collapse: the casualty-shape test passes, and the result matches Devereaux's account of where battle deaths actually lived.

**The receipts check.** Why did the serjeants win? Query the engine: 140 drill-days (error rate, relief verb, closers), mail (zone conversion), manufactured bonds (no grief brittleness), wages current. Every cause purchasable. Run the counterfactual — same serjeants after five foodless days (class C) — and the fatigue curves cross at minute six, the relief swaps slow, and Wexcombe plausibly holds its ground. Nothing about *who these men are* decided anything; everything about *what was done to and for them* did.

---

## 2. Stress test one: biases the example still carries

The walkthrough above passes the receipts audit, and it is still biased — in ways Devereaux has written about. Auditing our own demo:

**2.1 The pitched-battle frame itself.** The example is two consenting formed bodies on open ground — the rarest kind of pre-modern fighting and the kind state armies are best at. Devereaux's Universal Warrior series makes the point that the set-piece battle is only one face of war beside the raid, the ambush, and the skirmish, and that for many non-state societies raiding *was* war. An engine demonstrated only on set-pieces quietly defines military worth as set-piece performance — a civilizational thumb on the scale. The campaign layer already generates the other faces (foraging parties bounced, night raids on camps, convoy ambushes); the *resolver's* validation suite must run them too, not just the duel of lines. Added below as the raid test.

**2.2 The crypto-Hanson risk — the big one.** Devereaux's hoplite series notes that the orthodox model of close-packed shock infantry descends from Hanson's *Western Way of War*, a thesis his series spends its length complicating. Our lattice engine makes coverage density the central good — which, unexamined, *hard-codes Hanson into physics*: the densest shield wall becomes the apex of war by construction, and every loose-order system (Zulu, Numidian, steppe, peltast) becomes a worse phalanx rather than a different solution. The counter-mechanics must genuinely work, not merely exist: refusal of contact (speed against a lattice that cannot catch you), ranged threat (an attended threat you can never strike imposes exposure-like strain), evasion doctrines, terrain tears, and logistics-into-battle. Two acceptance tests pin this down: Sphacteria — Devereaux notes the achievements of light infantry there against hoplites — where javelin-armed troops must beat a phalanx by refusing its fight; and Isandlwana, already in our suite, where the loose-order army wins by encirclement and ammunition geometry. If close order wins *everything*, the engine is broken in Hanson's direction and ships nowhere.

**2.3 Universals from a narrow corpus.** Our class A "human constants" — attention budgets, primalization, the appraisal cue list — were assembled from Devereaux's evidence base (Greco-Roman, Civil War, WWI France) plus cognition literature. Devereaux himself scopes his claims to the broader Mediterranean where he knows the sources; we should match that humility. Class A values ship with provenance notes and a standing rule: when sources from another tradition show different collapse behavior, the model response is to find the *institutional cause* (the Zulu loins-reserve seated facing away from the battle is appraisal-input management, not a courage delta) — never a per-culture coefficient. The fix for a narrow corpus is more receipts, not more essences.

**2.4 The fair fight.** Equal-ish numbers, mutual consent, flat ground. Historical commanders spent their craft *avoiding* exactly this. Already solved at the campaign layer (battle-by-consent), but demos teach designers what "normal" is — so the documentation's canonical example should eventually be an asymmetric one.

**2.5 The visible field is all men under arms.** The campaign community — drivers, servants, wives, the foraged peasantry — exists in our supply model and then vanishes when swords come out. The baggage-as-supply-object brings part of it back; the example didn't show it. At minimum the camp and its people belong on the engagement map as the thing pursuit sacks, because that is where the post-collapse violence historically went.

**2.6 Material progressivism.** Receipts protect against racial essence but not against tech-ladder essence — "mail wins" can become the new "Romans win." Guard: no strictly-better equipment in class B. Mail costs heat and silver; pikes cost terrain and agility; matchlocks cost weather (§4). Every item is a trade, so equipment differences read as *adaptations to circumstances*, not rungs.

---

## 3. Stress test two: performance at scale

Per-tick cost model, N agents, k local neighbors, two-phase synchronous update:

```
spatial hash rebuild            O(N)
neighbor + coverage arcs        O(N·k)      k ≈ 6–12 in order
appraisal (c ≈ 10 cues)         O(N·c)
melee pairing / openings        O(N_engaged)
bond contagion                  event-driven, O(active edges)
lattice connectivity            union-find rebuild per unit per
                                ~10 ticks, O(N α(N)) — negligible
```

At 60k agents (a Towton-sized field) this is a few million simple ops per tick — milliseconds in Rust, comfortable in vectorized NumPy, unviable in a naive Python loop. The CLI target survives easily *headless*. The genuine bottlenecks are elsewhere:

**The crush.** The adversarial case is the historically catastrophic one: when a formation compresses (Cannae's center, a bridge, a gate), local density spikes, k explodes from ~8 toward 30+, and O(N·k) concentrates exactly where the simulation is most interesting. Mitigation with a happy property: cap per-cell occupancy and switch over-dense regions to an aggregate *crowd-field* mode — pressure and casualties computed on the field, individual agency suspended. Fidelity degrades precisely where individual agency historically vanished; men in a crush are not making decisions, and neither should their agents.

**Line-of-sight cues.** "Banner visible" as raycasting is the classic ABM killer. Replace with broadcast fields: a banner emits presence over a radius attenuated by local crowd density and terrain class — O(N), no rays, and arguably *more* honest about what a man in rank three actually perceives (a sense of the standard, not a sightline).

**Decremental connectivity.** Union-find handles merging, not splitting, and battle is mostly splitting. Exact dynamic connectivity is research-grade machinery we don't need: full recompute per unit on a 10-tick cadence is microseconds and the cascade dynamics are slower than that. Buy the simple thing.

**Routing crowds.** Post-percolation, everyone moves at once — cache-hostile but computationally trivial (flee vectors, no pathfinding worth the name).

**Ensembles are the real bill.** One battle is cheap; the architecture's promises (fitting BP-Front, the ensemble-honesty test, AI lookahead) want hundreds of seeded runs. That is where compute lives. Mitigations in order: coarse agent ratio (1:10) for ensemble duty; embarrassingly parallel seeds across cores; and the deferred BP-Front model as the AI's rollout engine once fitted. Determinism constraint: seed-stable ordering under parallelism — two-phase commit gives it, threading inside a phase must preserve it.

---

## 4. Stress test three: build an ibutho and an ashigaru company

The flexibility question: can the schema express two systems from different continents and centuries with **no new essences and minimal new code**? Build sheets first, strains after.

```
ZULU IBUTHO (Shakan system, c. 600 men)
B  iklwa (short stabbing spear, ~0.4m blade reach), isihlangu
   (large hide shield: big self-coverage, light), 2–3 throwing
   spears, no armor, barefoot
C  fed from the king's herds; arrives fast-march conditioned
D  ARMY choreography: horns-of-the-ox (chest/horns/loins role
   assignment by regiment seniority); open-order running
   advance; encirclement doctrine; controlled prone under
   missile fire (the Isandlwana paper's mechanic, native here);
   loins reserve held seated, facing away from the field
E  superb error-rates within its repertoire (run + close +
   stab); conditioning earned through years in the ikhanda;
   priors by regiment age
bonds  AGE-SET edges: the amabutho system deliberately cuts
   across kinship, binding a cohort from across the kingdom —
   manufactured cohesion at state scale, plus a strong belief-
   channel edge to the king
doctrine sketch:
   [ missiles_incoming & in_open      -> evade_prone,
     enemy_inside_reach               -> melee_press,
     has_javelin & enemy_in_range(jv) -> throw,
     friend_crowding                  -> spread,
     *                                -> run_to_horn_station ]
```

```
ASHIGARU YARI COMPANY (Sengoku, c. 300 + optional 50 teppō)
B  nagae-yari pike 4.5–5.6m; okegawa-dō / tatami armor (torso
   zones), jingasa; option: matchlock teppō + powder train
   (class B note: matchlocks degrade in rain — weather is a
   receipt, not a die roll)
C  fed and paid in rice by han logistics; seasonal conscripts
D  close-order pike hedge (kneel/level by rank), sashimono and
   banner system, drum–horn–conch signal vocabulary, officer
   scaffold (ko-gashira per ~30 men), volley rotation if teppō
E  moderate drill-days (campaign-season drilling); variable
   priors
bonds  village clusters + OFFICER edges + a pay-chest edge
   (the Antwerp lever exists here)
doctrine sketch:
   [ enemy_inside_reach  -> melee_press(sidearm),
     enemy_at_point      -> pike_press,
     order_hold          -> hold_dress,
     *                   -> seek_anchor ]
```

Both sheets were written without touching engine code, and neither contains a quality number — the amabutho's famous discipline is an *institution* (class D + manufactured bonds), the ashigaru's volleys are a *repertoire*, and that is the test passing in the large. Now the honest strains it surfaced:

**4.1 Reach bands — required code.** A 0.4m stabbing spear against a 5.6m pike exposes that `enemy_adjacent` / `enemy_in_range` is too coarse. Melee needs explicit bands — *beyond the point / at the point / inside the point* — and a `close_past_point` transition resolved by the openings physics (you get inside a pike through an opening, exactly as Romans and Swiss did; once inside, the pike is firewood and the sidearm rules). This single addition also explains, for free, why pike blocks need flank guards and why they shatter when the tide turns (main doc validation shape #2). It is the first invocation of Addendum A's closure discipline: a real design-review event, vocabulary genuinely extended. The system worked; the queue is real.

**4.2 A taxonomy gap: trained bodies.** Zulu running endurance is neither class C (campaign state) nor class E as written (learned *calibrations*). Lifelong conditioning is a trained capacity with an institutional receipt — years of ikhanda life. Fix: widen class E to *trained capacities, physical and cognitive, with institutional provenance*. The anti-essence property holds: any population given the institution gets the capacity; the engine stores the years, not the race.

**4.3 Army-level choreography.** The horns-of-the-ox is a pre-planned multi-unit scheme with roles assigned by seniority; the ashigaru side answers with a real-time signal vocabulary. Both demand the battle-plan layer the main doc sketched (per-wing plans, signals through the command model) to be specified for *named army-level repertoires*. Not new philosophy — new spec work this test forces onto the schedule.

**4.4 Missing appraisal cues.** Shield-drumming, war cries, and above all *perceived encirclement* — the sight of the horns closing — are appraisal inputs our cue list lacks. Add `display_pressure` and `enemy_bearing_spread` (cheap: the angular spread of enemy masses around you; when it passes ~180° the oldest fear in infantry history switches on). Encirclement panic becomes emergent perception, not a surrounded-flag.

**4.5 Who wins?** The right answer is the engine's: *it depends, legibly*. Open ground and open flanks feed the horns; a narrow frontage with anchored ends feeds the hedge; rain silences the teppō (class B); a long approach march starves whoever's class C is thinner; and if the teppō fire from a supply point, ammunition geometry — Isandlwana's decisive variable — is in play again. A fixed answer would mean a bias; a sensitivity list means the receipts audit is passing.

---

## 5. Punchlist forced by this addendum

Engine: reach bands + `close_past_point`; crowd-field degradation mode for crushes; banner/signal broadcast fields replacing LOS; cadenced union-find connectivity; appraisal cues `display_pressure`, `enemy_bearing_spread`; class E widened to trained capacities with provenance.
Spec: army-level plan/signal layer for named choreographies (horns-of-ox, volley rotation).
Validation: add the **raid test** (ambush on a foraging party — the resolver must handle non-consensual, asymmetric shapes) and the **Sphacteria test** (light troops beat a phalanx by refusal of contact); retain Isandlwana as the anti-Hanson guarantee.
Process: first confirmed use of the closed-vocabulary design-review path — record it as precedent.
