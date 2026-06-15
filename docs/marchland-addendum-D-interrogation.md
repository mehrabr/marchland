# MARCHLAND — Addendum D: The Interrogation Loop
### How a soldier is defeated, and ten harder questions after that

**Extends:** Addenda A–C. **Method:** the brief asked for a standing loop — pose the question that would break the model, answer it, log the verdict, repeat. Verdicts: **PASS** (model holds as designed), **CHANGE** (model holds, code/spec must move), **OPEN** (unresolved, tracked). The loop ends by assembling the whole stack — campaign to spear-point — into the game the first message asked for.

---

## Q1 — How is a soldier defeated? Is there a formula?

There is a formula, and it is short. Per agent *i*, per tick:

```
load(i)  = Σ over threats: presence × arc_uncovered × unattended
λ(i)     = λ₀ · h_fat(f_i) · h_err(ε_i, load)  +  λ_x · load(i)

           λ₀, λ_x, h-curves : class A — identical for every human
           f_i  : fatigue (class C position on a class A curve)
           ε_i  : error-under-load (class E — receipts: drill-days)

P(opening this tick) = 1 − exp(−λ(i)·Δt)        ← sampled, seeded

given an opening exploited by attacker j:
   band   : j's weapon reach vs distance (class B physics)
   zone   : struck zone ~ presented-area distribution
            (posture, shield arc — geometry, not a roll-to-hit)
   result : zone armor (class B) → deflect | bruise | wound |
            disable | kill,  with kill ≪ disable ≪ wound ≪ nothing
```

A soldier is defeated when an **opening** — a discrete event with a cause: a recoil, a stumble, a guard dropped by fatigue, attention pulled to an uncovered arc — is exploited through a reach band into a body zone whose material gives way. Most exchanges produce nothing. Most somethings are recoils. Deaths are rare, and every one carries a full causal trace the replay can print:

> *L32, t=921: right arc uncovered since L33's recoil at t=884; exposure 0.7/s for 37s; opening (attention split); thrust, inside-band, left thigh, unarmored (no mail purchased — class B receipt); disabling wound; bled out t=1140.*

**Verdict: PASS.** Random in occurrence, exhaustively explained in mechanism — the historum criterion pushed down to the individual grain.

---

## Q2 — Isn't that probability a stat in hiding?

The accusation deserves a precise test, because it is half right. A probability *can* be a stat: it is one the moment the dice are loaded differently per people. *Total War's* melee-attack value is exactly that — an asymmetric loading of the hit dice, attached to a faction, with no receipt.

What makes λ₀ not a stat is that it satisfies both clauses of Addendum B's design law. It is **uniform** — the same dice for every human who has ever lived; a Zulu, a serjeant, and an ashigaru at equal exposure, fatigue, and error-state generate openings at the identical rate. And every **modulator** of the rate carries a receipt: exposure traces to lattice geometry, fatigue to the campaign's calories and miles, error-under-load to drill-days an institution paid for. Run the audit question — *what in-world action would change you?* — and λ₀ answers "nothing; this is the human body," which is precisely the answer class A constants are licensed to give, and the only parameters licensed to give it.

The discipline to keep: any time a designer reaches for a per-unit multiplier on λ — "elite guards should just be *deadlier*" — that is the tabletop ancestor knocking. The deadliness must be bought (armor zones, error rates, reach, position) or it does not exist.

**Verdict: PASS**, with a standing tripwire: λ may never acquire a per-unit or per-culture coefficient. The receipts audit (Addendum B, test 5) already covers this; extend it to grep the data files.

---

## Q3 — Why sample at all? Wouldn't a deterministic model be purer?

Two deterministic alternatives exist and both are worse.

*Expectation propagation* — no dice, fractional casualties flowing as rates — is what Lanchester equations do, and it is smoothness poison: a lattice near collapse is a threshold system, and thresholds need discrete shocks to trip. 0.4 of a man cannot fall and tear a hole; the cascade machinery starves. (It also resurrects the health bar in liquid form: the unit "loses 3% per second," which is the grind we abolished.)

*Full deterministic micro-simulation* — resolving every footfall — is the historum author's free-2D trap with the lights on: false precision about millisecond dynamics nobody can validate. Below our floor (≈1.5m, ≈seconds), who lives is governed by a stone underfoot, a gust, a deflection of one centimeter — deterministic chaos at a grain no engine should pretend to know. **Sampling from a calibrated distribution is the honest representation of causes below the simulation floor.** A soldier's death is random the way weather is random.

The engineering discipline that keeps this auditable: seeded determinism with **per-agent RNG substreams**, so one seed yields one exact history regardless of thread scheduling, every battle replays bit-identically, and every death certificate is reproducible.

**Verdict: CHANGE** — per-agent substreams added to the spec (Addendum A had a global seed; that breaks under parallelism).

---

## Q4 — Can one random death really decide a battle? Should it?

Yes, sometimes — and that is the model behaving correctly, not noise winning. The lattice spends most of a fight far from criticality: a death tears coverage locally, neighbors and file-closers repair it, the structure absorbs the shock. The serjeants in Addendum C ate two deaths and never wobbled. Near the critical region — fatigue high, reserves spent, edges frayed — the same single death propagates. **Chance proposes; structure disposes.** Which tear opens is sampled; whether tears propagate is determined by everything the players and the campaign did beforehand.

This is also where the honesty machinery earns its keep. The ensemble runs (Addendum A §6) measure how close a given battle sat to the transition: a fight the loser wins in 40 of 100 seeds *was* a near-run thing and the chronicle may say so; a fight they win in 2 of 100 was decided before the first spear, whatever the survivors believed. The game can represent both the participants' experience of fortune and the historian's view of structure — and keep them distinct, which is more than most history books manage.

**Verdict: PASS.** Sensitivity to single events near criticality is the phenomenon, not a bug in it.

---

## Q5 — If the floor is dice, where is the player's agency?

Everywhere above the floor — which is to say, exactly where Devereaux locates the real general's agency. List the levers against his job description: choice of *whether* (battle-by-consent, a campaign-layer verb); choice of *ground* (terrain anchors, frontage width, what's behind you); *condition* (the campaign wrote every class C value — fed men against marched-out men is a decision made weeks earlier); *deployment and plan* (who stands where, per-wing doctrine, where the reserve waits); *timing of commitment* (the few big mid-battle decisions); *presence* (the general's body as the strongest appraisal anchor, placeable once). Nothing on this list is a dice roll, and together they set the distance-to-criticality that Q4's dice then explore.

What the player conspicuously cannot do is puppet the men — and the same architecture that grants agency upward denies it downward. Orders travel at rider speed to *anchors*, not agents; repertoires gate what can be ordered at all; appraisal lets units decline the insane and the culturally illegible (Total Generalship II, made executable). This closes the exploit surface in the same motion: kiting, murder-hole micro, and sacrificial-bait tricks all require puppet control the command model refuses to provide. The anti-cheese system and the historical-command system are one system.

**Verdict: PASS.**

---

## Q6 — How does an arrow kill a man with no attack stat?

By not aiming at him. Massed archery in this engine is area physics: a volley defines a beaten zone; agents inside it are sampled by **presented area** — posture, shield arc, packing density — through range-dependent energy into zone materials. The archer never duels anyone; the sky samples a crowd. Out of this falls, with no further rules: shields-up advances (trading exposure for speed and vision), the suppression behavior the Isandlwana paper proved out (our `evade_prone`), why dense formations eat more arrows per volley but unformed crowds panic worse (appraisal under display_pressure with no lattice to lean on), and why armor turned the longbow's killing into bruising at distance — Agincourt's dead were made less by arrow-through-plate than by mud (fatigue physics), funneling (crowd density), and horses (Q7) thrashing through their own side's lattice. Ammunition stays a physical object at a supply point, so the archery duel is logistics wearing feathers.

**Verdict: PASS**, one spec note: the beaten-zone sampler is new geometry code (cheap — it is the crowd-field machinery from Addendum C §3 pointed downward).

---

## Q7 — How does cavalry break infantry without a charge bonus?

By admitting the second species into class A. A charge is two appraisal systems meeting: the men's and the **horses'**. Horses are agents with their own universal constants, and the relevant one is that a horse will not impale itself into what it perceives as a solid obstacle. A formed, braced, points-out line *is* a solid obstacle; horses balk, swerve, flow down the face — the charge becomes a noisy, terrifying non-event, which is the historical record of cavalry against steady squares and pike hedges. A line that flinches — and the flinch is the men's appraisal under `display_pressure`, `enemy_bearing_spread`, ground-shake noise, the sight of mass at speed — opens seams, and through seams horses will go, and then mass × velocity does what physics says to men from the side and behind.

So the oldest rock-paper-scissors edge in gaming — cavalry beats wavering infantry, spears beat cavalry — re-derives as a *chicken race between two nervous systems*, with the destrier's willingness to press close a trained capacity (class E for horses; receipts: years and oats) and the warhorse itself a class B economic object the campaign had to afford. No charge bonus exists; courage of horses and men is the entire mechanic.

**Verdict: CHANGE** — horse agents enter the spec; class A generalizes to *species*-universal constants. Cost is modest (simple policies, big bodies) and the payoff is the whole mounted layer.

---

## Q8 — Doesn't human universalism erase the famous knight?

It erases his *essence* and keeps his *receipts*, and the receipts turn out to be the whole legend. A man in full harness has a transformed wound table: against levy spears, almost no zone gives way, so λ-openings against him mostly resolve to *deflect* — he can stand in places no one else can stand, which is what the chronicles actually describe. His error-under-load is a lifetime of purchased training; his warhorse is Q7's physics; his visible person is an appraisal anchor for everyone whose arc he covers. The badass test (Addendum B) still holds — strip the harness and put four average men around him in the open and he dies like anyone — but inside the system that paid for him, he is exactly as decisive as the sources say. And he comes with a medieval-true failure mode: that armor *signals ransom*. Which opens Q9.

**Verdict: PASS.**

---

## Q9 — What do the wounded, the surrendering, and the captured do?

Three mechanics the loop forced, all cheap and all load-bearing:

**The wounded are contagion vectors, not subtracted hit points.** A disabled man is a coverage hole *and* an exit visa: helping a stricken comrade rearward is the one socially legitimate way to leave a battle line, so each casualty emits an **escort affordance** along bond edges. Kin-bonded levies bleed two extra men per casualty; drilled units with designated bearers and file-closers bleed none. The rearward trickle of wounded and helpers is itself an appraisal cue for everyone who watches it pass. The oldest morale leak in military history, as a graph operation.

**Surrender is an appraisal output, not a defeat animation.** When `enemy_bearing_spread` passes encirclement, no exit path reads open, and a *quarter signal* is being offered, yielding enters the policy menu — gated by class D customs (what quarter conventions exist between these forces) and the belief channel (men who expect massacre fight cornered, the most dangerous appraisal state in the engine, and the mechanical reason commanders left golden bridges).

**Prisoners are campaign objects.** Harness signals wealth; wealth gets captured, not killed. Ransoms flow into the opportunity feed — *Sir X taken at the ford; his ransom stands at 300 marks* — paying the pay-chest that holds the bond edges together. Killing prisoners is an act with belief-channel and allegiance consequences the campaign layer prices. The medieval prisoner economy stops being flavor text and becomes revenue with a moral ledger.

**Verdict: CHANGE** — escort affordances, quarter signals, ransom objects into the spec.

---

## Q10 — How does the campaign reach down into a fight, and the fight back up?

This is where the original two seeds — the mobile city and the probability cloud — stop being a separate game above the resolver and become its boundary conditions.

**Downward writes (campaign → battle):**

```
supply field (§4.3)      → calories → every f_i starting position
march history            → footsore, sick lists, stragglers absent
pay state                → bond edges to captain/chest: tension
muster composition       → WHO is here: 40-day men whose term
                           expires mid-siege simply begin leaving
                           (belief-channel event, not desertion roll)
the camp (Direction A)   → ON the field: earthworks = terrain
                           coverage anchors; baggage = the ammo
                           and water supply objects; followers =
                           what pursuit reaches; "defend the camp"
                           = defend your own class C for tomorrow
the cloud (Direction B)  → battle as an ARRIVAL PROBLEM: forces
                           reach the field over hours along the
                           local subgraph; most "battles" are
                           30-man scuffles over a granary at the
                           cloud's edges (the resolver is cheap at
                           small N — this is its bread and butter)
the belief DB (Dir. C)   → deployment against where you THINK
                           they are; the chronicle you read after
                           may be wrong
```

**Upward writes (battle → campaign):**

```
dispersal ≠ destruction  → Bull Run reform: a broken side whose
                           belief channel held re-coalesces on the
                           road graph over days; "stack wiped" is
                           abolished as a concept
wounded                  → cart-loads that slow the host, eat the
                           stockpile, and die or recover by class
                           A curves the camp's conditions modulate
torn bond edges          → a village that lost its men: allegiance
                           and recruitment in that node, changed
priors (class E)         → survivors are veterans now; the army
                           that held learns it can hold
loot, ransoms, banners   → pay chests, opportunity feed, belief
captured ground          → the engagement context resolves into
                           main-doc §4.6 postures: who holds the
                           crossing tonight
```

And one unification worth flagging because it fell out unplanned: **`enemy_bearing_spread` is the same variable at every zoom.** At agent scale it is the soldier's perception of being surrounded; at engagement scale it is a wing's envelopment; at cloud scale it is the operational encirclement of Direction B's road-graph battles. The Zulu horns and the LoGH pincer and the panic of one man at the end of a torn file are one number measured at three radii. The campaign ideas don't just carry into this zoom — they were always this zoom, integrated.

**Verdict: PASS**, and this is the section that makes it a *game*: the campaign is where battles are won, the battle is where the campaign's choices are audited, in public, with spears.

---

## Q11 — After all this machinery: is it still a game? Assemble it.

One loop, end to end, as the player lives it:

You muster the host late (the rye was not in), so the cloud forms thin and the 40-day clocks are already running. You move as a distribution down two road-strands; the chronicle brings rumors of their vanguard at the ford — *six days old, rumor-grade*. You concentrate — fist clenched, burn clock lit — and reach the ford to find their camp already ditched on the far bank: Direction A's two-cities problem. Four days of forage raids and bridge skirmishes (the resolver running dozens of tiny lattice fights) while your stockpile counts down. Their teppō wagons sit far from the water; you offer battle in rain. They decline; their term-men start walking home; on the sixth morning their lattice has to come to you or starve, across mud, into bearing-spread. You hold the reserve until the replay will later show you should have, or shouldn't. The chronicle — which is all you ever saw — says *a near-run thing*, and for once the ensemble agrees.

Every clause of that paragraph is a system already specified in these documents, and the two original campaign sketches are both present: the army as walking city (the camps, the works, the burn clock) and the army as probability cloud (the strands, the rumors, the arrival problem). The synthesis the project promised holds at the bottom of the stack: **Sher Khan's vision** — every soldier an agent running role-conditioned rules — is the substrate, with his rulesets become data; **the historum rebuttal** is honored in the closed schema and receipts; **Devereaux's critiques** are each load-bearing mechanics now — the omniscient general (Q5), the logistics that decide battles before they start (Q10), morale as two channels of real people (Addendum B), casualties that live in the pursuit (Q1, C§1), sieges as hunger (main doc §5), and no essence anywhere a colonial-era coefficient could hide (Q2's tripwire).

**Verdict: PASS — ship the prototype plan.**

---

## Punchlist from this loop

Engine: per-agent RNG substreams; beaten-zone volley sampler; horse agents (class A generalized to species-universal); escort-affordance emission on casualties; quarter-signal + surrender policy path; ransom/prisoner objects bridging to the opportunity feed; death-certificate trace as a first-class queryable artifact.
Process: receipts-audit extended with an automated grep — no per-unit or per-culture coefficient may touch λ, ever.
Open items carried: crowd-field/volley sampler unification; the spacing-experiment writeup; BP-Front fitting once ensembles exist.

The loop stays open by design. Next questions queued: night and weather as perception physics; disease as the campaign's true killer (it killed more than battle did — does our class C do it justice?); naval and river fights on the same lattice; and what the chronicle generator owes the truth.
