# MARCHLAND — Addendum B: Doing Away With Stats
### Iterating toward a combat model with no power scaling

**Extends:** Addendum A (BP-Field) and main doc §8.
**Method:** this addendum is written as the loop the brief asked for — propose, test against the research, find the surviving stat, remove it, repeat. Each iteration ends by naming its own flaw.

---

## Iteration 0 — The audit, and why this matters

After Addendum A, BP-Field still carries five numbers that are ratings rather than measurements: `base_power`, `armor_class`, the `break_threshold` distribution, the unit `morale` meter, and `veterancy`. Every one of them descends from the same ancestor: the tabletop quality coefficient — Kriegsspiel umpire tables, through hex-and-counter combat factors, through D&D, into the video game attack stat. A quality coefficient is an ordinal claim: *these men fight at X% of those men.*

That slot in the data model is not ideologically neutral, because the slot is where the 19th century wrote its race science. Devereaux's Fremen Mirage series traces it directly: martial-race theory in the British imperial military imputed soldierly qualities as essentially genetic — and the roster of supposedly martial races kept changing, because the theory was nonsense describing nothing. The companion tropes fill the rest of the stat card: the hardy barbarian with high attack and low discipline, the decadent easterner with low morale, the savage horde that fights to the last man. Devereaux's Universal Warrior series names the modern form — the Cult of the Badass, the belief that wars are won by *better men* — and his Fremen Mirage conclusion is that this entire family of ideas simply fails to describe actual military success, which belonged overwhelmingly to the logistics, organization, and mobilization of settled states.

Strategy games re-encode all of it every time they ship a faction roster: leadership 36 for the peasant, 70 for the chosen warrior, eastern infantry in the budget tier. And his morale tests show the meter is absurd even on its own terms — a *Total War* peasant mob holds after being rear-charged by a stronger unit while its allies rout and its general dies, fighting on through a third to half its number killed; a *Bannerlord* army stood to 96% casualties; even Paradox's much gentler quarter-to-third loss rates run about triple the historical norm. The meter exists to make the power fantasy legible: grind the bar, spike the bar, collect the rout.

**The design law for everything below:**

> Constants must be human-universal (bodies, materials, cognition). Variables must be circumstantial (equipment, training time, diet, bonds, stakes, fatigue, information). Every number must answer the question *"what in-world action would change you?"* A number with no answer is an essence, and essences are forbidden.

A spear thrust into an unarmored thigh does what it does regardless of who holds the spear. If two armies differ, the simulation must be able to *say why*, in causes a player could in principle alter. That is the whole program. Now the loop.

---

## Iteration 1 — Kill `base_power`: combat as a physics of openings

**Propose.** Delete the pressure-exchange roll. Model the front-rank fight as geometry and timing between bodies: each fighter has weapon reach, a guard, footing, crowding room, and fatigue. Nothing lands through a maintained guard. Strikes land only through **openings**, and openings are *events with causes*: a recoil, a stumble, a guard dropped by exhaustion, a weapon bound or broken, a lapse of attention, a man turning to a second threat. Wound consequences follow material physics — armor as coverage zones with real properties (mail turns a cut into a bruise on covered zones and does nothing for the face), not an abstract class. Kills are rare; recoils are the common currency, exactly as Addendum A's pulse model wanted.

**Analyze.** Two things just happened. First, the offensive baseline became human-universal: at parity of situation, every front-ranker generates threats at roughly the same rate, because human arms move at human speeds. The differences that remain are situational — and the hoplite scholarship confirms the situation dominates. The spacing literature finds a file needs on the order of a meter and a half of width for free weapon-work and maneuvers like the countermarch, while the orthodox close-order phalanx packs files to 45–60cm — a formation that has *traded individual striking room for collective coverage*. Spacing, in other words, is not flavor; it is the dial that sets what a man's body can even do. Our model can now express that trade natively, which no attack stat ever could.

Second, a stat is trying to sneak back in. If "skill" becomes a hidden coefficient on openings-generated-per-second, we have re-invented attack power with extra steps. Hold the line: baseline output is constant; trained men will differ in *error rates under load* — and "load" is the thing we haven't modeled yet.

**The surviving flaw:** combat here is still a sequence of duels. It has no account of why men fight in formations at all, or why the formation, not the man, is the thing that wins. The historical answer is about attention.

---

## Iteration 2 — The attention lattice

**Propose.** This iteration is the project brief's own seed, made mechanical: *officers, spacing, and support narrow a warrior's attention to the soldier ahead of him.* Take that literally as cognition. A human fighting for his life can fully track about one threat in a narrow frontal arc, monitor a second marginally, and nothing else — multiple-object tracking under terror is a universal constant of the species, not a stat. So give every agent:

```
attention:  1.0 budget; full track = 1.0, peripheral = 0.3
arcs:       front / left / right / rear (coarse sectors)
coverage:   per arc, supplied by self (shield, guard) or by
            neighbors' bodies, shields, and weapons, or by the
            rank behind (rear arc), or by terrain (a wall, a river)
exposure:   Σ over threats of (threat presence × arc uncovered ×
            attention not allocated) × time
```

Openings (Iteration 1) now occur at a rate driven by **exposure**. A man with one attended enemy ahead and every other arc covered fights at the human baseline indefinitely (until fatigue). A man with two attackers must split a budget that doesn't split well. A man with a threat in an uncovered arc is generating openings whether or not anyone has swung at him yet.

**Analyze — what this derives for free.** Flanking is lethal with no flank modifier: the end file of an outflanked line simply *has threats in arcs nobody covers*. Gaps kill because a gap is the instantaneous loss of two men's worth of neighbor-coverage. Depth steadies the line because a covered rear arc is the difference between a fighting man and an animal looking over its shoulder — and because the rank behind replaces the front (Iteration 4 will make fatigue the thing being replaced). Solo heroism dies in seconds, as it did: the Cult of the Badass is now mechanically false inside the engine, because four average men *are* the counter to any one man, however trained — his attention budget is the same 1.0.

And the formation itself acquires its true identity: **a formation is an attention prosthetic — a machine for simplifying each man's war to one opponent.** The phalanx and the legion become two engineering solutions to the same problem, which matches the scholarship. Devereaux's blended model of the hoplite phalanx — no rugby-scrum shove, but a shock-oriented shield wall at mostly regular spacing — is, in our terms, a maximal-coverage lattice: dense files, mutual shield coverage, brittle exactly at its edges and at terrain tears. The Roman system is a lattice with *maintenance machinery*: his Missing Infantry-Type piece notes the triplex acies checkerboard's lanes existed not for shooting through but for maneuver — withdrawing the skirmish screen and rotating spent front lines behind fresh ones. Line relief is lattice repair under fire, the hardest drill there is, and it is why the legion needed its dense scaffold of junior officers.

Officers slot in as lattice roles, not aura bonuses: the file leader is the anchor the file dresses on; the file closer physically occupies the seepage path rearward and is a pair of eyes the rear rank knows is there; the centurion is a repair agent who closes gaps and a *visible fact* (next iteration) standing where the line is worst. Spacing becomes a genuine command decision with the real trade: close order buys coverage density and pays in weapon room and maneuver; open order buys reach and speed and pays in exposure. The sim can host the orthodox-heterodox spacing debate as an *experiment* — run the lattice at 45cm and at 90cm files and observe which survives which situations — which is precisely the kind of question a simulation should be for.

**The surviving flaw:** the unit `morale` meter still exists, and it is the biggest essence left — a hit-point pool for courage, the number that lets a designer type *how brave these people are*.

---

## Iteration 3 — Kill the morale meter: two channels and continual appraisal

**Propose.** Devereaux's morale post (Total Generalship IIIc) supplies the replacement architecture outright. The single meter conflates two different forces with different sources, different timescales, and different failure modes:

**Morale** — the slow channel — is belief: that the cause is worthy, that success is possible, that the leaders have a workable plan. It lives on the *campaign layer* and updates from events: pay arrears, plunder shared or hoarded, omens read, a leader's reputation, news of the war, hunger. It gets men to the field. It does not get them through the fight.

**Cohesion** — the fast channel — is the bond structure: who, specifically, you stand beside, and what you owe them. Not a number; a **graph**. Edges are kin, neighbors, drill-mates, sworn men, a captain owed loyalty or wages. McPherson's Civil War formulation (which Devereaux builds on) draws the line exactly: the cause carries men on the march and to the battle; comrades carry them through it.

In battle no meter ticks. Each agent runs **continual appraisal of observable facts**: am I covered? is the man ahead of me still there? can I see the banner? is my file-mate down? are men pushing past me toward the rear? is there noise behind us? Appraisal is weighted through *primalization* — Devereaux: the calculation grows more primal as danger rises, but it never stops — so as exposure climbs, distant considerations (the cause, the plan) fade and proximate ones (the bodies beside me, the path behind me) dominate. Standing, pressing, edging back, and fleeing are **policy outputs of appraisal**, and one man's flight is the next man's observable fact. Breaking is a cascade on the cohesion graph. There is no number anywhere named courage.

**Analyze — test against the historical outcome matrix.** This is where the meter dies on the evidence, because IIIc's case studies are *states a meter cannot represent*:

- *High morale, weak cohesion* → First Bull Run: green, motivated armies collapse in the fight, then **reform afterward** — most of the runners returned to their units within days. Two channels produce this naturally: the bond graph failed under fire; the belief channel was intact, so the campaign layer reassembles the army. One meter cannot make an army that both routs and un-routs.
- *Low morale, high cohesion* → the 1917 French mutinies, or Cold Harbor: units that **hold together and refuse** — they don't flee and don't desert, they decline to attack vigorously, because faith in leaders failed while bonds held. Possible for us because "advance vigor" is a policy output; flatly impossible for a meter whose only failure state is running.
- *Cohesive force, dead belief in the employer* → the Mercenary War, the unpaid Army of Flanders sacking Antwerp: the bond graph holds and **retargets**. Pay arrears attack one specific edge type. The campaign layer's opportunity feed already speaks this language.

The same move fixes the casualty absurdity. Our levy should come apart at single-digit losses when its lattice frays and its neighbors start dying — not grind through a third of its men like a *Total War* tarpit. Devereaux's benchmark: even the gentlest game casualty rates run about triple the real norm, and the real norm puts most of the killing **after** cohesion fails. That is now an emergent prediction the engine must reproduce, not a tuning goal.

**The surviving flaw:** if no one carries a courage number, are all men interchangeable? Where do the real, observed differences between armies live?

---

## Iteration 4 — Differences without essence

**Propose.** Every remaining parameter must carry a **receipt**: a traceable origin in simulated circumstance. The differences are real; the essence is not.

- **Equipment** is economics. The campaign layer bought the mail; mail is mail on every body. An army in armor differs from one without because of silver and supply, not blood.
- **Training** is time spent, converted into three things: *repertoire* (which formations and maneuvers exist at all — line relief, the countermarch, rallying on standards: institutional knowledge, stored as capabilities, not bonuses), *error rate under load* (drilled actions degrade less as exposure rises — the only place "skill" survives, and it is purchased with drill-days), and *artificial cohesion edges* (drill's shared suffering builds a primary group where organic bonds are absent — Devereaux's account of how professional armies manufacture what villages get free).
- **Experience** is appraisal calibration. Veterans hold not because they are braver but because their priors are better: battles are loud, confusing, and survivable, and they have the simulated history to prove it. A green army with a burning cause *is* Bull Run, and now the engine knows why.
- **Bodies** are campaign state. Nutrition, march fatigue, disease — fed by the supply field of main doc §4.3. Endurance curves are species-universal; the *current position on the curve* is what the campaign did to these men.
- **Bonds** are recruitment mode, writing the cohesion graph directly: a village levy arrives with dense organic kin-edges (strong, and brittle in a specific way — when a man's brother dies beside him, edges tear); a drilled retinue has uniform manufactured edges; a mercenary company hangs its edges on the captain and the pay chest.
- **Stakes** are situation: men defending their own valley, pressed men, paid men — entering as appraisal weights tied to facts the campaign layer knows.

The forbidden slot is now simply *gone from the schema*. There is no field where "Gaul = 0.9" can be typed. If one army keeps winning, the engine can be queried for causes — drill-days, mail coverage, full bellies, shorter supply lines — and every cause is a thing the loser could in principle have had. This is the anti–Fremen-Mirage property stated as a data model: hard times do not produce strong men in this engine; they produce hungry men without drill institutions, which is what the record shows.

**Analyze — the honest objection.** *"You've just renamed stats."* Partly conceded, twice already in this project: a general simulator needs parameters; the historum thread settled that. What changed is the parameters' **type**. An attack stat is an ordinal rating of worth with no referent; drill-days, coverage zones, kin-edges, and calorie deficits are measurable quantities with causal histories, and each answers *"what would change you?"* with an action available in the world. The test is operational, and it is also exactly the difference between simulating reality and ranking peoples.

**The surviving flaw:** one last essence is hiding in plain sight — the *unit* itself, an entity that "has" cohesion and "wins" engagements.

---

## Iteration 5 — Kill "the unit wins": endings by structure, not score

**Propose.** The unit stops being an object with attributes and becomes a **pattern**: a lattice of coverage relations (Iteration 2) laid over a graph of bonds (Iteration 3), organized around a banner and a handful of named lattice-roles. "Unit cohesion" is no longer stored; it is *measured* — connectivity of the live lattice — the way temperature is measured from molecules.

An engagement therefore has no win condition and no resolution roll. It ends the way real ones did: one side's lattice **percolates apart**. Local seepage (men edging back; the file-closer's whole job is to stand in its path) crosses a threshold and becomes cascade; coverage losses create exposure, exposure creates flight, flight is a visible fact that propagates along bond edges. When the chronicle writes *the line broke*, the engine means it literally: the coverage graph lost its giant component. Pursuit follows from policy against the newly uncovered backs of running men, and the casualty ledger fills where history says it should — after the break, scaled by the winner's pursuit discipline and horses.

**Analyze.** This finally satisfies the historum criterion at the level of the whole engagement: outcomes are hard to predict (percolation transitions are sharp and sensitive) and easy to explain afterward (the replay shows the tear: a gap at the hedge, the file leader down, the seepage on the left). It also gives Bull Run its second half: a side whose lattice shattered but whose belief channel held can *reform on the campaign layer* — defeat and destruction are different events, as they actually were. And note what quietly already complied: the Isandlwana paper needed no Zulu ferocity stat and no British discipline stat — range physics, reload times, suppression, an ammunition point, and encirclement geometry produced the history. The statless engine is not a speculative departure; it is what our best reference implementation was already doing, extended to the psychology it lacked.

---

## The residue: every number that remains, classified

```
A. Physical constants   — species-universal, measured, identical
                          for all factions: reach, pace, endurance
                          curves, wound physics, attention budget
B. Material properties  — mail, linen, ash spear, yew bow
C. Circumstantial state — fed/starved, fresh/marched-out, paid/owed,
                          dry/soaked: written by the campaign layer
D. Institutional        — repertoires: which maneuvers, formations,
   capabilities           relief drills, signals EXIST for this army
E. Learned calibrations — appraisal priors and error-rates-under-load,
                          earned from simulated drill and battles
F. Ordinal quality      — ABOLISHED. No slot exists.
   coefficients
```

Class A is where we must be most careful and most honest: the attention budget and primalization curve are psychological estimates. But they are estimates about *homo sapiens*, applied uniformly — the one place a universal number is the anti-essentialist choice rather than the lazy one.

---

## Implementation notes: BP-Lattice (revision of BP-Field)

The agent loop becomes: **perceive** (threats by arc; coverage from neighbor lookup) → **appraise** (fast channel over observable facts, weighted by primalization) → **act** (doctrine policy, Addendum A's interpreter — conditions are now perceptual facts) → **physics** (openings from exposure; wounds by zone). The lattice is an explicit graph updated incrementally as agents move; arcs are four coarse sectors; coverage is a neighbor query on the Addendum A spatial hash. Nothing here threatens CLI feasibility — it is bookkeeping, not geometry processing — and the percolation check is a union-find pass, effectively free.

Cut from the schema relative to Addendum A: `base_power`, `armor_class`, `break_threshold`, unit `morale`, scalar `veterancy`. Added: coverage arcs, the bond graph, the belief channel (campaign-side), appraisal weights (class A/E), armor zones (class B), repertoire flags (class D).

**Validation suite v3** adds, on top of v2:

1. **Casualty-shape test:** the losing side's deaths must concentrate after lattice collapse, with pre-break losses in single digits for ordinary engagements — calibrated against Devereaux's "triple the norm" critique rather than against game tradition.
2. **The IIIc matrix:** scripted scenarios must reproduce Bull Run (rout-and-reform), the 1917 mutiny shape (cohesive refusal), and the Antwerp shape (unpaid cohesive force retargets) — three outcomes no single-meter engine can produce.
3. **The spacing experiment:** run identical lattices at 45cm and ~90cm file widths across situations; the engine should *discover* the close-order/open-order tradeoff rather than be told it, and the results should be legible enough to host the actual historiographic debate.
4. **The badass test:** one exceptional individual versus four ordinary men in the open must reliably lose; the same individual as a file leader in a sound lattice must visibly matter. The Cult of the Badass should be false and *leadership* true, in the same engine, for structural reasons.
5. **The receipts audit (continuous):** any persistent win-rate difference between factions must be explicable by querying class B–E causes. If the explanation ever bottoms out in "they're just better," that is a bug with a moral dimension, and it blocks release.

---

## Sources for this addendum

- ACOUP, *Total Generalship IIIc: Morale and Cohesion* — the binary-morale critique and game tests; morale/cohesion as distinct channels (after McPherson, *For Cause and Comrades*); Bull Run, the 1917 mutinies, Cold Harbor, the Mercenary War, Antwerp 1576; casualties concentrated after collapse. https://acoup.blog/2022/07/01/
- ACOUP, *Hoplite Wars* series (2025–26), esp. IIIa/IIIb and the IVa synthesis — the spacing debates (orthodox 45–60cm files, charge-to-collision, shoving othismos vs. heterodox readings) and Devereaux's blended model: no shove, but a shock-focused shield wall at regular spacing. https://acoup.blog/2025/12/05/ and following.
- ACOUP, *Total War's Missing Infantry-Type* — triplex acies lanes as maneuver-and-relief machinery rather than fire lanes; the rarity of true hybrid infantry. https://acoup.blog/2022/04/01/
- ACOUP, *The Fremen Mirage* (esp. IIIb, IV) and *The Universal Warrior* (esp. III) — martial-race theory as scientific racism with a rotating roster; the Cult of the Badass; the failure of "hard times make strong men" as a description of military success. https://acoup.blog/2020/02/14/ , https://acoup.blog/2021/02/19/
- Randall, K., *Hoplite Phalanx Mechanics: Investigation of Footwork, Spacing and Shield Coverage* — ~1.5m file widths required for free weapon-work and countermarching; limited pushing as an integral, bounded element.
- Scogings & Hawick (Addendum A) — the existence proof that physics plus geometry, with no quality coefficients, reproduces a real battle.
