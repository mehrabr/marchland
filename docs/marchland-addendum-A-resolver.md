# MARCHLAND — Addendum A: How combat resolves
### Stat block vs. agents, settled by the Isandlwana paper

**Extends:** §8 (THE BREAKING POINT) of the main design doc.
**Prompted by:** Scogings & Hawick, *An Agent-Based Model of the Battle of Isandlwana*, Proc. 2012 Winter Simulation Conference (uploaded), plus follow-up research on combat ABMs.

---

## 1. The answer

The question "stat block or agents?" dissolves on contact with this paper, because the paper *is* Sher Khan's forum proposal, implemented and published — the rulesets match his sketch almost line for line (British: melee if adjacent, else fire if loaded and in range, else load; NNC: move away, fight if trapped; Zulu: melee, spread, charge, advance on a preset vector). So feasibility is no longer in question: priority-rule agents, one per soldier, 20,000+ of them, reproduced both the outcome and the *stage sequence* of a real battle on 2012 hardware, and then ran a credible counterfactual with frozen parameters.

But the paper also vindicates the historum rebuttal in the same breath. Its rules are bespoke per side and per battle — the British literally have no movement rule, because at Isandlwana they didn't meaningfully move; Zulu operational maneuver is a hand-authored vector per regiment. That is a simulation of *a* battle. And it contains no morale model at all: nobody routs, the NNC's historical flight is faked by a crowding artifact, and the fight ends by annihilation. It works because Isandlwana happens to be one of history's rare true annihilation battles. Run the same engine at Hastings or Agincourt and it fails, because medieval battles are decided by cohesion collapse and most of their killing happens in the pursuit — exactly the phenomena absent here.

**Decision: agents are the substrate; the stat block survives as the data the agents read.** A single universal rule interpreter with a closed vocabulary of conditions and actions; unit "doctrine" becomes an ordered rule list plus numeric parameters, shipped as data files. Sher Khan gets his agents; the rebuttal gets its closed schema; the schema spanning 1879 and 1415 is what makes it a simulator rather than a diorama.

---

## 2. What to take from the paper

**The architecture.** Per tick, per agent: find neighbors, walk the rule list in priority order, first rule whose condition holds fires, possibly nothing fires; compute all, then commit all (synchronous two-phase update); harvest statistics every tick. This is the simplest possible agent brain and it was *enough* — formations, stalls, surges, and the famous Zulu crescent all emerged from it without any rule naming them.

**The performance trick.** Discrete grid coordinates plus a precomputed list of cell offsets sorted by distance; an agent scans outward along this list and stops at the first hit, getting the distance for free from the list entry. Nearest-neighbor search is the classic ABM bottleneck and this kills it. Steal verbatim (a uniform-grid spatial hash is the modern equivalent; either way, 20–50k agents headless is trivial today in NumPy struct-of-arrays or Rust).

**Suppression as proto-morale.** A near-miss drops a Zulu agent prone for 15–20 ticks, during which he executes nothing. This *one rule* generates the entire texture of the assault: the advance stalling at effective rifle range, front ranks down while rear ranks press into them (the crescent bunching that matches eyewitness description), and the surge the moment fire slackens. Lesson: psychological state expressed as *temporary rule paralysis* is cheap and produces pulsed combat for free. Our melee model generalizes it as *recoil/hesitation*.

**Logistics inside the battle.** Ammunition lives at a physical supply point (the camp, rear center); resupply probability decays with distance from it. Consequence: the right flank — farthest from the wagons — starves of ammunition first and collapses first, which is what actually happened. For MARCHLAND this is a gift: the campaign layer's camp and baggage train instantiate *on the battlefield* as supply objects. Direction A's entrenched camp and the resolver are now one continuous system, and "defend the baggage" stops being flavor text.

**The validation method.** Tune until the model reproduces outcome *and* stage sequence; freeze every parameter; then perturb only the initial deployment (their alternative: a tight British square, no NNC) and let the unchanged model speak. Their square scenario fails for the Zulu in a satisfyingly physical way — the smaller perimeter means the regiments interfere with each other and can't bring numbers to bear, and casualties climb to plausible-abandonment levels, as at Rorke's Drift and Ulundi. They close by proposing ensemble perturbation as a way to classify outcomes as *fixed points* versus *fluid*. Adopt all of it (§6 below).

---

## 3. What the paper is missing (our additions)

1. **A psychology layer.** No morale, no rout, no fear contagion, no rally. Required for any battle that isn't an annihilation — i.e., nearly all of ours.
2. **General movement.** Formation-keeping, giving ground, wheeling — not scripted vectors and not the free-2D logjam mess the historum author warned about. Needs one good cohesion mechanism (below).
3. **Melee as a process.** Adjacency exchanges are fine for assegai-vs-bayonet seconds; medieval shock combat needs pulses, fatigue, and depth pressure.
4. **Terrain, fatigue, weapon variety** — all flagged by the authors themselves as future work.

---

## 4. Two agent architectures from the literature, and the hybrid

Research turned up a second canonical lineage besides priority-rule agents: Ilachinski's ISAAC/EINSTein family, the standard model in military operations research. There, each combatant carries a six-component *personality weight vector* — attraction/repulsion toward alive friendlies, alive enemies, injured friendlies, injured enemies, own goal, enemy goal — and moves each tick by minimizing a penalty function over its movement range; successors like MANA swap the goals for waypoints. Note the punchline for our debate: EINSTein's "personality" *is six numbers*. The most agent-y combat model in the literature parameterizes behavior as a small stat vector. The dichotomy was never real.

The two architectures trade off legibility against smoothness:

- **Priority rules** (Isandlwana): discrete, debuggable, read like doctrine on the page. Bad at graded spatial behavior (formation keeping, drift, pressure).
- **Potential fields** (EINSTein): smooth, tunable, natural for movement and cohesion. Opaque to read; everything becomes weight-tuning.

**BP-Field uses both, split by job:** priority rules decide *actions* (fight, fire, load, flee, pursue); a single field term decides *movement* — attraction to the unit's **anchor** (the standard/banner position, itself moved by the unit AI under orders), plus repulsion from crowding and threat. The anchor term is doing triple duty: it is formation-keeping, it is the cohesion geometry (distance-from-anchor feeds morale), and it is the command interface (orders move anchors, never agents).

---

## 5. BP-Field specification

One resolver family, two backends, one unit schema (§8 of the main doc):

```
BP-Front : the 1D segment model. Fast path: campaign autoresolve,
           AI rollouts. O(segments) per pulse.
BP-Field : the agent backend. Witnessed battles, ground truth,
           content authoring. O(agents) per tick.
```

**Calibration pipeline — the key idea of this addendum:** BP-Field ensembles (same scenario, N seeds) generate distributions of outcome, duration, and casualties; BP-Front's constants are then *fit to those distributions* rather than hand-balanced. The agent model is the ground-truth generator; the front model is its learned abstraction. When they disagree, the agent model wins and the front model gets re-fit.

### 5.1 World and scale

Grid, one cell ≈ 1.5m. Agent ratio is a knob: 1 agent = 1 man for set-piece battles, 1 = 10 for fast resolution (the paper's efficiency results say 1:1 at 20k is already cheap; the knob is for ensemble runs). Terrain as per-cell movement/fire modifiers plus anchor-snap features (a hedge, a ditch, a ford — the §4.1 campaign graph's local detail instantiated).

### 5.2 Agent and unit state

```
Agent { pos, unit_id, condition: hale|wounded|down,
        fatigue, hesitation_timer,        # the generalized prone
        status: ranked|pressing|recoiling|routing|pursuing,
        ammo }

Unit  { anchor_pos, banner_up, leader_alive,
        morale (slow meter), order (current instruction),
        doctrine_ruleset_id, psychology_params, physique_params }
```

Agents read unit state; they never receive orders directly. Heterogeneity inside a unit comes from sampling per-agent break thresholds from a distribution — see §5.4 for why this single distribution is a major design lever.

### 5.3 The universal rule interpreter

Closed vocabularies. Adding a condition or action is a design-review event, not a content task — closure is what keeps this a simulator.

```
CONDITIONS: enemy_adjacent, enemy_in_range(r), threat_density(>x),
            friend_crowding, flank_open, anchor_dist(>d), suppressed,
            has_ammo, unit_morale(<m), routing_neighbors(>=k),
            target_routing, terrain_at(self|target)
ACTIONS:    melee_press, fire, load, charge, give_ground, spread,
            close_ranks, seek_anchor, hesitate, flee, pursue, stand
```

A unit's doctrine is an ordered list over this vocabulary plus numbers — a data file. Proof of closure: the paper's three rulesets re-expressed —

```
british_1879:  [enemy_adjacent -> melee_press,
                has_ammo & enemy_in_range(R) -> fire,
                !loaded & has_ammo -> load]
nnc_1879:      [enemy_adjacent & !friend_crowding -> give_ground,
                enemy_adjacent -> melee_press]
zulu_1879:     [enemy_adjacent -> melee_press,
                friend_crowding -> spread,
                enemy_in_range(A) -> charge,
                * -> seek_anchor]        # anchor replaces preset vector
```

— and two medieval entries from the same vocabulary:

```
levy_spear:    [unit_morale(<30) | routing_neighbors(>=3) -> flee,
                enemy_adjacent -> melee_press,
                anchor_dist(>2) -> seek_anchor,
                * -> stand]
men_at_arms:   [enemy_adjacent -> melee_press,
                target_routing & psychology.pursuit_ok -> pursue,
                unit_morale(<12) -> give_ground,
                anchor_dist(>3) -> seek_anchor,
                * -> close_ranks]
longbow:       [enemy_adjacent -> give_ground,
                has_ammo & enemy_in_range(R) -> fire,
                !has_ammo -> seek_anchor]   # arrows live at the baggage
```

Same engine, 1879 and 1415. That is the scalability answer.

### 5.4 The psychology layer (what the paper lacked)

**Unit morale** is a slow meter fed by legible terms: visible casualty *rate*, flank exposure (computed from unit bounding geometry — the historum "open flank degrades you untouched" insight, agentized), banner/leader status, mean fatigue, ground lost, local suppression density, surprise. First-order, threshold-based — deliberately *not* the coupled second-order dynamics the historum author burned weeks on.

**Per-agent break checks** fire when unit morale sags below the agent's personal threshold, sampled per agent. The research gives this distribution teeth: an ABM study of Roman combat found that formations were stabilized disproportionately by a *small fraction of psychologically resilient individuals in the front rank* — the centurion effect — even at merely average skill. So veterancy in MARCHLAND is not a damage bonus; it is the shape of the threshold distribution and where the resilient tail stands. A unit with steel in its first rank holds; the same numbers with the steel scattered do not.

**Contagion and rally.** `routing_neighbors(>=k)` sits in every doctrine's rule list, so flight cascades through contact networks — the rout *is* an emergent epidemic, not a unit-state flag. Rallying requires an anchor: banner up, leader alive, threat density low. Pursuit comes from `target_routing -> pursue` gated by `pursuit_discipline`, and because pursuers kill the defenseless cheaply, the casualty distribution skews into the rout phase on its own — which is the ACOUP IIIc claim, and now a measurable validation target rather than an assertion.

### 5.5 Melee as pulses

Engaged front agents exchange *press* tests each tick. Overwhelmingly the result is recoil — a knockback step plus a `hesitation_timer` (the paper's prone mechanic wearing a gambeson); wounds are uncommon, kills rare. Rear ranks in `pressing` status add forward pressure (the NNC crowding artifact, promoted from bug to mechanic). Fatigue drains with pressing and charging, gates `charge` and `melee_press` effectiveness, and recovers only in disengagement. The emergent texture is pulsed combat: surge, shove, mutual recoil, breathing space, surge — with low casualties until somebody's morale, not body count, gives out.

### 5.6 Output

Headless by default: per-tick stats, phase-transition events. The CLI renders ASCII rasters on demand (the paper's figures are already basically character grids) and the chronicle generator narrates unit state transitions: *the levy on the left gave ground; the banner went down at the ford; flight spread along the hedge.* Deterministic seeds; every battle replayable.

---

## 6. Validation suite v2

0. **The Isandlwana test (new, engine-level).** Before any medieval content: express the paper's published rulesets and order of battle in our vocabulary and reproduce their result — outcome *and* stage sequence (stall at effective range, right-flank ammunition collapse first, center holds longest), then their square counterfactual. It is the best-documented annihilation battle available, the rules are in the literature, and it exercises everything except the psychology layer. A free integration test.
1–5. **The five medieval shapes** (main doc §9) — Fabian, chevauchée, winter, Agincourt, siege — now with two added criteria borrowed from the paper's method:
   - **Stage-sequence fidelity**, not just final outcome.
   - **Frozen-parameter counterfactuals**: tune on one scenario, perturb deployment only, judge plausibility.
6. **Ensemble honesty.** N-seed runs classify each battle as *fixed* or *fluid*; the chronicle may call something a near-run thing only when the distribution agrees. Casualty timing must skew into the pursuit phase for collapse battles.

---

## 7. Revised build order

Main doc §9 said: build BP-Front first. **Reversed.** BP-Field is barely more code than BP-Front (the paper's whole brain is a rule loop and a neighbor search), it doubles as the ground-truth generator, and the Isandlwana test gives it a ready-made first milestone with published answers. BP-Front is deferred until the campaign AI needs cheap rollouts, and is then *fit to* BP-Field ensembles rather than designed.

1. BP-Field core: grid, interpreter, two-phase update, neighbor search. Milestone: Isandlwana reproduced.
2. Psychology layer + melee pulses. Milestone: a levy line that breaks believably; pursuit-skewed casualties.
3. Anchors, terrain, baggage-as-supply-object. Milestone: Agincourt-shaped scenario passes.
4. Campaign substrate integration (main doc §4): engagement contexts hand the resolver a subgraph, postures, and supply states.
5. BP-Front, fit from ensembles, when the AI needs it.

---

## 8. Sources added in this addendum

- Scogings, C. & Hawick, K., *An Agent-Based Model of the Battle of Isandlwana*, Proc. 2012 Winter Simulation Conference (uploaded: cstn-116.pdf). Architecture, neighbor-search optimization, suppression mechanic, ammunition-point logistics, frozen-parameter counterfactual method.
- Ilachinski, A., *Artificial War: Multiagent-Based Simulation of Combat* (World Scientific, 2004); ISAAC/EINSTein lineage — personality-weight-vector agents, penalty-function movement; MANA as waypoint extension. https://www.worldscientific.com/worldscibooks/10.1142/5531
- ABM study of Roman warfare on psychological resilience: small fractions of resilient front-rank individuals (centurions) disproportionately stabilize formations — basis for §5.4's threshold-distribution design.
- *Medieval Warfare on the Grid* (AHRC/EPSRC/JISC, 2007–2011): ABM of the Manzikert campaign's logistics — precedent and reference point for the campaign-layer supply model in main doc §4.3.
- Historum thread 199886, pp. 3–4 (per main doc §2.2): the dissent this addendum resolves.
