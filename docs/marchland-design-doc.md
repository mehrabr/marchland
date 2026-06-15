# MARCHLAND (working title)
## A design document for an operational medieval warfare simulation

**Status:** exploratory / pre-prototype
**Scope of this doc:** simulation logic and engine architecture only. No graphics. Every system here must function as a text interface — if it can't be played over a teletype, it's out.

This document synthesizes three inputs: two seed concepts (the army as a mobile city; the army as a zone-of-control "probability cloud"), Bret Devereaux's ACOUP critiques of the Total War model of command and logistics, and the Historum thread "Historically inspired battle 'Simulator'" (thread 199886), particularly the exchange around user Sher Khan's dissent from stat-based combat. It proposes a shared simulation substrate, three campaign-layer directions built on it, one shared battle resolver, and a build order.

---

## 1. The assumptions we are discarding

Classic historical strategy games — Total War above all — rest on a stack of assumptions so old they read as genre definitions rather than choices:

1. **The army is a chess piece.** A point-mass that moves freely across terrain and is always exactly where its token is.
2. **The player is a god.** Perfect, real-time information; zero-latency, lossless command of every unit.
3. **Combat is HP attrition plus counters.** Units grind each other's health bars; tactics means matching rock to scissors.
4. **Supply is an upkeep fee.** A gold number subtracted somewhere, with no spatial existence.
5. **Battle is the default interaction.** Two tokens touch, a battle fires. Campaigns produce dozens of pitched battles.
6. **Recruitment is a build menu.** Soldiers are purchased like buildings.
7. **All armies are commanded identically.** A tribal levy and a drilled legion accept the same orders with the same fidelity; "discipline" is a flat stat bonus.

Each of these is contradicted by the historical record, and — more interestingly for us — each one, when removed, leaves behind a *game* rather than a hole.

---

## 2. What the research says

### 2.1 ACOUP: the general's actual job

Devereaux's *Total Generalship* series (Parts I–IIIc) uses Total War as the stand-in for the cultural model of generalship and then dismantles it. His conclusion in IIIc is blunt: the Total War model — active mid-battle command used to engineer favorable unit-on-unit matchups in a rock-paper-scissors tactical economy — was essentially impossible under pre-gunpowder conditions, and for some time after. The general's information arrives late and garbled (Part I: line of sight, dust, runners); his commands move at the speed of a rider or a horn signal and are filtered through cultural expectations about what a commander may even legitimately order (Part II). What drill and officer structure an army has determines its *repertoire* — what maneuvers are physically and socially possible — and Devereaux notes that games almost never vary command-and-control itself: a Gallic warband and a Roman consular army in Rome II are equally puppet-like, and where discipline appears at all it's a flat damage modifier (IIIa, IIIb). Battles, finally, are decided by morale and cohesion, not by mutual extermination (IIIc).

**Design constraints extracted:** generalship is mostly *pre-commitment* (route, supply, ground, deployment, plan, subordinates) plus a tiny budget of slow, unreliable mid-battle interventions. Command-and-control quality should vary the *action space* between factions, not a damage number. Combat resolution must be a cohesion model, not an HP model.

The *Logistics: How Did They Do It* series (Parts I–III) supplies the operational physics. Part I builds the consumption problem: a lean consular-scale army (~19,200 effectives, ~4,000 non-combatants, ~9,800 animals) needs on the order of 62 metric tons of food and fodder per day. Part II establishes that this comes overwhelmingly from the land the army moves through — foraging, requisition, plunder — at terrible cost to the people living there. Part III turns this into operational geometry, and it is the single most game-shaped piece of military history writing I know of:

- **Armies were effectively confined to the road network.** Wagons demand real roads; pathfinding without maps or compasses demands local guides, who navigate by the roads they know. The operational map is not a plane; it is a *spiderweb*, and the main body is stuck to it. Small light columns may use the minor strands.
- **Route viability is a supply calculation.** A moving army sweeps a foraging zone (his model: ~10 miles either side of the march, ~12 miles/day, extracting maybe 10% of what's there). Whether a route can feed the army depends on rural population density, season, army size, and how badly the district has already been stripped.
- **Season is a forcing function.** Post-harvest, his model army can go nearly anywhere settled; by October a third of the countryside's food is gone; wintering in the field demands dense farmland and pre-built stockpiles. Doubling the army doubles the density threshold and deletes routes from the map.

**Design constraints extracted:** the map is a graph, not a grid. Supply is a spatial, seasonal, depletable field. Army size trades directly against operational reach. Time spent stationary is purchased with the surrounding district's food. Dispersal in winter is not a special rule; it should fall out of the model.

### 2.2 Historum thread 199886: the stat war, and how it resolved

The thread's author sets out a manifesto worth adopting wholesale: the simplest possible battle model that produces historically-shaped outcomes — fewest rules, broadest applicability, minimal player involvement, and an explicit rejection of rock-paper-scissors. His test for emergence: cavalry should win on the flanks because of how battles are *modelled*, not because of a "+5 when flanking" tag. His success criterion: outcomes that are hard to predict but easy to explain afterwards, resembling the arrow-diagrams in battle books. His intended use: an auto-resolver for the Paradox-style campaign layer.

Sher Khan's dissent (page 3, post #3866169 and surrounding) attacks the remaining stats from the other side: model no unit numbers at all, simulate every individual as an agent executing a short role-conditioned behavior rule. His worked example is Rorke's Drift as nested loops — per time-round, per agent: a British soldier melees if a Zulu is adjacent, else reloads, else fires at range; the native contingent withdraws from contact; Zulu agents charge in range, spread out, advance. Swap the British for legionaries and you change only the ruleset (throw pilum in range, hold spacing, fall back if unsupported).

The counter-argument that effectively ends the dispute makes two points. First, scalability: a hand-crafted ruleset per opponent-pair is a simulation *of a battle*, not a battle *simulator*. Second, and more fundamental: the behavior tree *is* a stat — "you've just made combat behaviour a stat." Any simulator that can simulate more than one thing needs parameterized unit input; the live question is only *what the parameters describe*.

The author's implementation history (page 4) is a free list of expensive lessons:

- Free 2D agent movement produced logjams and nonsense unless agents were made "smart," which destroys the simplicity budget.
- Tracking morale and cohesion as separate coupled quantities with second-order differential dynamics never produced believable output — untunable and ahistorical.
- The model that clicked: a single dynamic **power** per unit that varies with the unit's own state *and its neighborhood* — an open flank degrades a unit even when nobody is attacking it; an uncommitted reserve standing behind a unit passively strengthens it.

**Design constraints extracted:** parameterize *doctrine and psychology*, not damage, inside a closed universal schema (Sher Khan's behavioral insight, made scalable). Generate outcomes from geometry and context — neighbors, flanks, depth, reserves — never from matchup tags. Avoid free 2D; avoid coupled-DE psychology. Validate against "explainable in hindsight."

### 2.3 The synthesis

The two research threads converge on a single relocation: **the game is not in the battle.** ACOUP moves the general's agency to the operational layer — roads, food, information, and whether battle happens at all. The Historum thread shows the battle itself can be a compact, semi-autonomous resolver whose drama comes from cohesion collapse, not player micro. The two seed concepts (mobile city, probability cloud) are both operational-layer ideas, and they turn out to be the *same* idea observed at two zoom levels: the host is the concentrated limit of the cloud; the cloud is what a host must do in order to eat.

---

## 3. Design pillars

**P1 — The road graph is the world.** Operational maneuver is a finite choice among strands of a spiderweb, with throughput limits and seasonal closures. This is historically honest and, conveniently, the cheapest possible world model for a CLI game.

**P2 — Dispersion is the resting state of armies.** Concentration is a temporary, expensive, deliberate act — a fist you make, swing, and must unclench. The supply model alone enforces this; no special timer is needed.

**P3 — You command what you know, and you know little, late.** Each side acts on a belief database fed by riders, rumor, and scouts. The interface renders beliefs, never ground truth.

**P4 — Battle is an event with consent or compulsion, not a collision callback.** An army that can move and screen can refuse battle. Forcing battle is an operational achievement: pinning against an objective, a river, an empty larder.

**P5 — Combat emerges from cohesion and geometry.** Units break before they die; casualties concentrate in the pursuit; flanks and reserves matter because of where they are, not what tag they carry.

**P6 — Armies are made of people with terms.** Recruitment, supply, and obedience are negotiated with institutions and proud subordinates, mostly via offers the world makes to you.

---

## 4. The shared substrate (engine logic)

All three directions in Sections 5–7 run on this layer. It is deliberately small: five data structures and a daily loop.

### 4.1 World model

```
Node {
  id, name
  type: town | village | abbey | castle | crossing | pass | camp
  population            # drives stores and recruitment
  stores(t)             # current extractable food+fodder, seasonal
  depletion             # 0..1, how stripped the district is
  fortification         # none | walls | castle
  allegiance            # faction sympathy, -1..+1
  garrison[]
}

Edge {
  class: highway | road | path | trail
  wagon_ok: bool        # trails exclude wagons -> excludes a host's main body
  throughput            # men/day that can pass without column penalties
  march_cost(season, weather)
}
```

Pathfinding is Dijkstra with army-dependent admissibility: a host with a wagon train sees a much sparser graph than a flying column, which is exactly the ACOUP picture. Rendering is a gazetteer plus optional ASCII map; the graph *is* the UI.

### 4.2 Time

One campaign tick = one day. All orders resolve simultaneously; the tick ends with a **chronicle** — a generated prose digest of what each side's commander would plausibly know happened. Engagement contexts (4.6) run an inner loop at pulse resolution (~1 hour).

### 4.3 The supply field

Each node's `stores` follows a seasonal curve: spike at harvest, decay through autumn (consumption + storage loss + seed grain returning to the ground), trough in late winter. Calibration comes straight from Devereaux's worked example (≈62t/day for ~19k effectives; ~250kg/person in the countryside post-harvest, falling toward ~175kg by October) before abstracting into a clean unit:

```
daily_need(army)  = men*1 + horses*4 + oxen*6          # supply units (SU)
forage(det, node) = min(node.stores * rate, det.capacity)
rate              = f(cavalry_share, allegiance, depletion, method)
                    # method: purchase | requisition | plunder
                    # plunder: more now, allegiance and future yield collapse
stockpile_cap     = wagons*W + pack_animals*P            # ~14 days for a host
deficit           -> desertion, animal deaths (which shrink stockpile_cap:
                     the death spiral), cohesion damage
```

The consequence the seed concepts asked for arrives free of charge: a concentrated army's `daily_need` exceeds any single district's sustainable yield, so **time-in-place is a burning clock** and dispersion is the only steady state. Bigger armies see fewer viable routes because the density threshold doubles when they do.

### 4.4 Information and belief

Two layers: ground truth tables, and a per-faction belief DB.

```
Belief {
  entity            # army, detachment, convoy, individual
  last_seen: node, timestamp
  est_strength      # noisy, source-dependent
  source: scout | rumor | informant | interrogation | deserter
  confidence
}
```

Reports are physical objects: they travel the graph at rider speed and can be intercepted. Scout detachments roll contact against enemy screens; merchants and travelers produce cheap, unreliable rumor; towns can host paid informants; captured foragers talk. The UI prints only this DB, with age made visible: *"Enemy host — last seen six days past at the Ford of Bex, perhaps two thousand — rumor."* Implementation cost is two tables and a message queue, and it is the single largest break from genre convention per line of code.

### 4.5 Command capacity and orders

The player owns a small daily budget of **command capacity** (riders, literate clerks, the lord's attention). Orders are letters:

```
Order {
  recipient, issued_at
  instruction           # march, hold, forage, screen, concentrate-at-N-by-D
  conditions            # "if the bridge is held, cross; else await word"
  latency = graph_distance / rider_speed
}
```

Subordinates execute the *last order received*, filling gaps with their doctrine and their interests — a proud earl may creatively misread an order to retire. Command-and-control is faction-asymmetric by data, not by modifier: a drilled retinue accepts conditional, multi-clause orders; a feudal levy accepts roughly "follow me." This is ACOUP IIIa/IIIb made mechanical: discipline changes what you can *say*, not how hard you hit.

### 4.6 Contact and battle-by-consent

When opposed forces occupy or adjoin a node, an **engagement context** opens — not a battle. Each side picks a posture: *withdraw, screen, raid, entrench, interdict, offer battle, assault*. Pitched battle occurs only by mutual consent or compulsion. Compulsion means pinning: no retreat edge with adequate throughput, an objective that cannot be abandoned (a besieged town, a fordable river behind), exhausted stockpiles, or genuine surprise. Whether a refusal succeeds is a contest of mobility and screening. This one rule deletes the stack-bump battle and generates, on its own: Fabian shadowing, battles clustering at crossings and sieges, and the historical rarity of pitched battle.

### 4.7 The opportunity feed (recruitment and agency)

Institutions — lords, towns, bishops, mercenary captains, routier bands — hold contracts and generate **proposals** each tick, conditioned on world state:

> *Sir Walter offers sixty lances for forty days, if the host marches by the 12th.*
> *The abbey at Vire will sell nine days' stores — at double the just price.*
> *Captain Vell's company, owed three months' arrears by the enemy, will treat with you.*

The player's verbs here are *sponsor / decline / counter*, and some subordinates act unbidden and present accomplished facts. This generalizes the seed concept's "actions offered by AI, chosen as sponsor" into the game's main interaction model — and doubles as the AI's own interface to every system, which keeps the AI honest (Section 10).

---

## 5. Direction A — THE WALKING CITY (the host as protagonist)

*Formalizes seed concept 1.*

**Fantasy.** You are not a faction. You are the host itself — a city that has torn itself out of the ground and started walking.

**Core loop (one day):** allocate population among roles → move or hold → camp actions → forage and intelligence resolve → chronicle.

**Muster.** The campaign opens with your population dispersed across home nodes, where it is productive (filling the muster stockpile). Calling the host paths contingents toward a rendezvous node over days or weeks. Consumption begins the moment men leave home, and because assembled mouths grow linearly while the rendezvous district's yield is fixed, sustainable days fall as 1/n — the superlinear muster pressure of the seed concept emerges from the supply field with no bespoke rule. Muster too early and you eat the campaign season in camp; too late and the objective is gone.

**The allocation dial** is the central instrument, set daily:

```
population -> { main_body    # combat power; eats the most
               foragers      # SU income; vulnerable; widens footprint
               scouts        # belief quality; screening vs enemy scouts
               pioneers      # improve edges, raise camp works
               garrisons     # left at nodes; holds allegiance + control }
```

Control of territory is exactly the trail of garrisons and forager reach you leave behind — the host drags a shadow of authority, thinning as it stretches.

**The camp as a buildable.** Each stationary day converts time into works (ditch → palisade → bastions → engines) and drill (cohesion for the resolver), while the same days strip the district. Entrenchment turns time into strength while supply turns time into weakness: one legible tension carries the whole midgame.

**Encounters as adjacent cities.** When two hosts close, play zooms to the local subgraph and both camps sit like rival towns a few miles apart — the "siege with two cities" image from the seed concept. The posture verbs from 4.6 expand: interdict their forage roads and starve them out; assault the camp (bloody, desperate); offer battle on chosen ground; night sortie; treat. A real siege is the identical system where one "camp" happens to have stone walls — which quietly delivers historically honest sieges (blockade, negotiation, hunger; storm as the rare last resort) without a siege subsystem.

**Goal grammar.** Scenarios are access objectives with deadlines, not extermination: *hold the bridge through Michaelmas; put the relief column into the citadel; devastate the vale to a tithe of its value; be encamped before the walls of X with stores for thirty days.*

**CLI sketch.** A status block (roster by role, stockpile days, district yield and depletion, works level, weather), an order prompt, the chronicle. One screen.

**Why it's promising:** a single, deeply legible protagonist; city-builder verbs fused to operational movement; the smallest viable slice of the whole vision.
**Risks:** pacing can stall when entrenched (mitigated by depletion making every chair hot); a one-host scope can feel small — which is also why it prototypes well.

---

## 6. Direction B — THE SPIDER'S WEB (the army as a distribution)

*Formalizes seed concept 2.*

**Fantasy.** The army is not anywhere. It is a weather system over the road network, and you are trying to steer weather.

**Representation.** An army is a set of detachments billeted and foraging across nodes, summarized in the UI as a zone with density figures, not forty raw tokens. The zone's size is not a stat: each detachment must sit within forage reach of un-stripped districts, so footprint grows with army size and shrinks where infrastructure is poor. Markets, granaries, and friendly abbeys let density rise locally; a hostile castle is a hole in your zone that eats foraging parties.

**Concentration as a fired weapon.** `concentrate at N by date` collapses the cloud: forage income stops, control lapses, the rear opens, and the 4.3 burn clock runs. After the operation the army must exhale back into dispersion to breathe. The strategic resource this creates is **tempo** — how often you can afford to make a fist — and it is the same resource Legend of the Galactic Heroes operational play runs on: mass, timing, and the cost of being massed.

**Movement.** A dispersed army advances as a front: lead detachments occupy new nodes while the tail strips and follows. Poor country forces the cloud to narrow onto the road — a column, fast to block and slow to pass, because edge throughput makes roads into chokepoints. Stretch the zone for more raiding and supply, and the whole becomes slower to gather and easier to defeat in detail: the seed concept's trade, produced by the substrate.

**The probability cloud is literal.** The enemy never sees your army; their belief DB holds scattered sightings of parties, from which mass and intent must be inferred. Counterplay follows: raid foragers (small fights whose reinforcement timers are simply graph distances), cut the roads between sub-clouds and defeat them in detail, stage false concentrations to make the enemy clench — and starve — for nothing.

**Operational battle.** When clouds interpenetrate, battle is a multi-day affair across the subgraph: columns arrive over hours and days, wings engage on separate fronts, encirclement means physically holding the road nodes behind a concentration. The Section 8 resolver runs per front; the player's decisions are routes, commitment, and timing — never unit micro.

**Why it's promising:** no shipped strategy game represents armies as distributions whose *shape is the strategy*; raids, screens, and reinforcement-timing fall out as systemic consequences rather than scripted features.
**Risks:** legibility (mitigate with named standing sub-commands — *the Vanguard, the Left Forage, the Tail* — and aggressive summarization) and AI competence (Section 10).

---

## 7. Direction C — THE KING'S POST (the dispatch game)

*The direction the research adds: ACOUP's command critique taken as the entire premise.*

**Fantasy.** You are one person at a camp desk. Everything you know arrived by rider. Everything you do leaves by rider.

**Interface.** The whole game is an in-fiction message log: incoming dispatches — timestamped, sourced, mutually contradictory — outgoing letters with conditions and contingencies, and a private map you annotate yourself, which the game never corrects. The simulation runs hidden underneath; subordinates are doctrine-driven agents executing your last instruction through their personality (rash, cautious, ambitious, semi-literate).

**Generalship as ACOUP describes it:** plan the route and the supply; choose where *you* are, since presence is the strongest command signal and you can be in one place; pre-commit contingent orders; decide which reports to believe. When your host fights, you get Part I's experience of battle — dust, a partial view from a hill, runners — and roughly three levers: commit the reserve, signal the pre-arranged maneuver, ride in person to a wavering wing and accept the risk.

**Scoring.** After the campaign, the game replays the *true* history against your annotated map. The delta is the score screen.

This direction works standalone or as the presentation layer over A or B. As a CLI artifact it is nearly free — the belief DB rendered as prose *is* the interface — and it is the most radical subversion in this document: a strategy game that never shows you the board.

**Risks:** sparse feedback frustrates; the report generator carries the entire experience and must be rich, voiced, and occasionally wrong in interesting ways.

---

## 8. The shared battle resolver — THE BREAKING POINT

One resolver serves all three directions, and doubles as the standalone auto-resolver the Historum author wanted for Paradox-style games. It takes the thread's hard-won lessons literally.

**No free 2D.** A battle is one or more **fronts**; a front is a 1D array of segments with flanks at its ends. Units occupy segments in ranks: line, supports, reserve. Operational battles (Direction B) are several fronts pinned to the local subgraph.

**Closed parameter schema** — the resolution of the stat war. Units are described by what they *try to do* and *when they break*, never by attack/defense values:

```
doctrine   { preferred_range, charge_impetus, evade, pursuit_discipline,
             formation_depth, terrain_affinity }
psychology { break_threshold, rally, veterancy, shock_sensitivity }
physique   { base_power, speed, armor_class }      # coarse, few steps
state      { strength, fatigue, order(0-100), ammunition, committed }
```

Sher Khan's behavior-rules live in `doctrine`; the schema being closed and universal is what makes it a simulator rather than one hand-tuned battle.

**The pulse loop** (~10 simulated minutes per pulse):

```
for each pulse:
  approach/skirmish per doctrine (range-keeping, javelin/arrow exchange)
  contact decisions (charge_impetus vs evade; refusals open gaps)
  pressure exchange per engaged segment:
     effective_power = base_power
                       * f(order) * g(fatigue)
                       * flank_security(neighbors)     # open flank degrades
                       * depth_support(reserve behind) # passive boost
                       * terrain(segment)
  order decays under pressure, casualties, threat; recovers in lulls
  break check: order < break_threshold -> rout
     rout floods fear into adjacent segments (cascade)
  if a wing collapses -> pursuit phase:
     majority of all casualties land here, scaled by the winner's
     pursuit_discipline and mounted share
```

`flank_security` and `depth_support` are computed purely from the array neighborhood — the open flank that hurts you while untouched, the reserve that strengthens by standing there. That is the Historum author's working model, adopted unchanged.

**The commander's hand:** deployment, a per-wing plan set before contact, and a small budget of mid-battle interventions whose arrival latency comes from the 4.5 command model. In Direction C, even watching is rationed.

**Validation criterion**, from the thread: the resolver must regenerate the textbook shapes — double envelopment when a longer line wraps, pike blocks invincible until the instant they aren't, cavalry futile frontally and decisive on flanks, opposed river crossings failing — with **no rule that names any of those outcomes**. Hard to predict, easy to explain afterwards.

---

## 9. Comparison and recommendation

| | A — Walking City | B — Spider's Web | C — King's Post | D — Breaking Point |
|---|---|---|---|---|
| Core novelty | city-builder fused to operations; two-camps battles | army as a distribution; shape *is* strategy | epistemics as the whole game | cohesion/geometry resolver, no RPS |
| Engine difficulty | medium | high | low (atop substrate) | low–medium |
| AI difficulty | medium | high | medium (agents are the content) | low (it runs itself) |
| CLI fit | strong | needs summarization craft | perfect — it's epistolary | strong |
| Standalone prototype | 12–20 node corridor, one host | 40-node web, two clouds | one scripted campaign | resolver + scenario files |

**Recommendation: these are not competitors; they are stages of one game,** because the substrate is 70% of the work for any of them and the two seed concepts are one mechanism at two zooms.

**Build order:**

1. **D first, standalone (weeks, not months).** A few hundred lines of Python: pulse loop, parameter schema, scenario files for historical orders of battle. Tune until the validation battles produce their textbook shapes. Best learning-per-line in the whole plan, and immediately useful as a toy.
2. **Substrate + Direction A on a corridor map.** One host, one objective: muster, march, and take the bridge before depletion or winter. Proves the supply clock, the belief DB, and battle-by-consent in the smallest arena.
3. **Layer B's dispersion onto the same map.** The host becomes the concentrated limit of a cloud; A's allocation dial becomes B's zone shape. If the substrate was built honestly, this step is configuration more than code.
4. **Swap the lens to C.** Develop with the god view; ship the fog. The belief-only dispatch interface becomes the default presentation once the systems are trustworthy.

**The historicity acceptance suite** — the prototype passes when all five emerge without scripting:

1. **Fabian test:** shadowing and refusing battle slowly strangles a stronger invader.
2. **Chevauchée test:** a devastation-and-raiding strategy is viable and *forces* the defender to seek battle.
3. **Winter test:** armies that fail to disperse or reach dense quarters by November die of the supply model.
4. **Agincourt test:** a pinned army with exhausted stores must attack on bad ground, and a smaller force can win by choosing that ground.
5. **Siege test:** most sieges end by negotiation or hunger; storming is rare and bloody.

---

## 10. Risks and open questions

**Tuning the supply economy.** Seed constants from Devereaux's worked numbers (62t/day for ~19k effectives; density thresholds of roughly 10/mi² post-harvest rising past 20 for wintering), then abstract to clean supply units once the *behavior* is right. The numbers exist; the risk is curve shape, not data.

**Fun versus friction.** Scarce information and forced dispersion delete the genre's power fantasy. The design bet is that the replacement payoffs — a picture correctly inferred, a concentration that lands on time — hit harder because they are earned. Playtest the frustration boundary before building content.

**AI.** The same-verbs principle is the whole strategy: the AI plays through postures, orders, and the opportunity feed, never through privileged channels. B's cloud AI needs heuristics over density, supply, and graph cuts — not unit micro — which is genuinely easier than RTS AI. C inverts the problem: its subordinate agents aren't opposition, they're the content.

**Scope sinkholes.** Court politics and diplomacy could swallow this design; the opportunity feed delivers most of their flavor for a fraction of their systems. Hold that line.

**Open:** the belief model makes asynchronous play-by-mail multiplayer almost free — worth designing for from the start? What is the supply unit called in fiction? Will players accept (and learn to love) battles they mostly do not control?

---

## 11. Sources

**ACOUP (Bret Devereaux):**
- Total Generalship: Commanding Pre-Modern Armies — Part I: Reports; Part II: Commands; Part IIIa: Discipline; Part IIIb: Officers; Part IIIc: Morale and Cohesion. https://acoup.blog/category/collections/total-generalship/
- Logistics, How Did They Do It — Part I: The Problem; Part II: Foraging; Part III: On the Move. https://acoup.blog/2022/08/12/collections-logistics-how-did-they-do-it-part-iii-on-the-move/

**Historum:** "Historically inspired battle 'Simulator'", thread 199886 — opening manifesto (p.1), the Sher Khan agent-based dissent and the stats-in-disguise rebuttal (p.3, around post #3866169), and the author's implementation retrospective (p.4). https://historum.com/t/historically-inspired-battle-simulator.199886/
*Note: Historum blocks automated access; the thread was reconstructed from substantial search excerpts of pages 1, 3, and 4 rather than full page reads.*

**Seed concepts:** the mobile-city host and the zone-of-control cloud, as supplied in the project brief; Legend of the Galactic Heroes operational battle games as the touchstone for Direction B's engagement feel.
