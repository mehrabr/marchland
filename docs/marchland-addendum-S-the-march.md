# MARCHLAND — Addendum S: The March, and the State of the Project
### What's next as a product, what's next as a simulation — and the Day Layer begun: the army versus entropy, measured

**Extends:** everything; un-parks Addendum L. **Brief:** stocktake on both axes, then the invitation accepted — the campaign march built and validated: the daily fight to hold an army together, the discipline bleed, the paths taken and refused. The headline result is at §3: the 1415 campaign now runs **end to end through three validated models** — Harfleur's siege clock into the march model into the Agincourt battle — with receipts flowing through every joint.

---

## 0 — The stocktake

**As a product, next is the vertical slice, and this addendum chose it.** The 1415 chain is the slice: one commission (the Harfleur campaign), playable in the CLI — siege, march, battle, chronicle, audit — because it is the one campaign where every system underneath is already validated. Around it: the chronicle/memoir generator prototyped against the chain's traces (it's load-bearing narrative software, per M); the covenant one-pager (*you command, you do not pilot*) as marketing canon; and persona playtests of the CLI season, Kriegsspieler and Student first. The renderer line stays unspent, per R.

**As a simulation, next is the two real misses, then the connective tissue.** Phase pacing and relief roles (the surviving B-grade failures: Hastings' casualty shape, the square's partial hold), the Isandlwana pursuit/encirclement gap, then BP-Front fitting from the now-larger ensemble library, then the rupture mechanics (P/Q) — in that order, every change re-run against the graded battery. The Day Layer slots in *now* because the chain demanded it: the battle scenarios were consuming arrival states nothing was producing.

---

## 1 — The march model: entropy with receipts

`march_model.py` (~170 lines, day ticks): the army as a structure that **dissolves a little every day and is gathered back every night**, with the gap between dissolution and gathering as the campaign's true ledger. Three outflows — stragglers (pace, fatigue, weather, hunger), deserters (somewhere to go, something owed, a way out), the sick (the environment, the season, the starvation multiplier) — against one inflow: the camp tick, where officer capacity and camp quality regather what the day shed. Column physics gate everything upstream: men plus train make column-miles, column-miles over road-lanes make clearing hours, and what's left of the daylight is the day's real reach — so a big army on one road *cannot* hurry, and ordering it to produces congestion, late camps, and a degraded gathering tick: **pace buys time with order**, the model's one-line thesis.

Two receipts the model surfaced that deserve naming. **Desertion needs a destination:** the rate runs on `home_pull`, and an English army deep in hostile Picardy has nowhere to leak to — desertion there is just capture with extra steps — which is why Henry's small force held together at rates that would be fantasy in friendly country, and why Marlborough, marching through allied Germany with home behind him, bled more *deserters* than Henry despite bleeding almost nothing else. And **starvation is an order solvent before it is a killer** (the Wellington line, mechanized): the hungry day triples the straggle rate and gnaws cohesion before anyone dies of it.

---

## 2 — The experiments (100 seeds each)

| scenario | days (hist.) | arrival effective | strag/desert/dead/sick | fatigue | cohesion |
|---|---|---|---|---|---|
| **Agincourt march** (8,400; 260mi w/ Somme detour; shadowed; forage; wet) | 17 (17) | 7,771 | 168 / 160 / 383 / 66 | 0.55 | 0.40 |
| **Danube 1704** (21,000; 250mi; depots; rest days) | 35 (~35) | 20,343 | 7 / 416 / 166 / 190 | 0.00 | 1.00 |
| **Niemen 1812** (286,000; 520mi; land too thin; typhus) | 65 | 170,182 | 4,642 / 98,989 / 20,095 / 8,863 | 0.26 | 0.00 |
| **Agincourt, unshadowed** (counterfactual: easy pace, rest days) | 29 | 7,705 | 166 / 164 / 386 / 106 | 0.30 | 0.90 |

**Agincourt:** seventeen days against the historical seventeen, with the Somme detour as a path event (the fords held against you; the march upstream — the brief's "struggle to find the right paths," in its 1415 form). Arrival strength 7,771 sits inside the contested 6,000–9,000 band. Arrival *order* is the interesting number: cohesion 0.40 — strung out, wet, hungry — which is the operational channel, not the belief channel; the army that re-dressed its line overnight and stood at dawn was running on the receipts the march can't touch (cornered, fed on purpose the last day, led). The two-channel split from Addendum B earning its keep at a new zoom.

**The Danube:** Marlborough's famous order reproduced from its famous receipts — staged depots, deliberate pace, rest days, full officer capacity — total wastage 2.8%, cohesion 1.0, fatigue zero. Entropy held to nearly nothing because every term in the entropy equation was *paid for in advance*, which is precisely the historical claim about that march.

**1812:** the entropy catastrophe at scale — 40% of the central mass gone before any major battle, the loss dominated by the straggler-deserter continuum (the marauder bands of the literature) with disease second and combat nowhere, cohesion at zero by Smolensk. The model's Grande Armée arrives at Borodino-strength having fought no one, which is the Minard graph's left half, generated from receipts: too many men for the land, roads too few, officers too thin.

**The counterfactual triangle:** unshadowed Henry arrives at cohesion 0.90 and fatigue 0.30 — and twelve days late. Fresher, later, against a French concentration that history would have made larger. *Pace, order, time*: the march model's whole decision space is choosing which corner to sacrifice, and the player's daily verb is exactly the brief's phrase — the fight against entropy, waged with rest days, road choices, and provosts.

---

## 3 — The chain: one campaign, three models, closed

The showpiece. **Siege:** Harfleur falls by negotiated terms at median day 38, the besieger 27% unfit — output: ~8,400 fit men. **March:** those men cover the 260 detoured miles in 17 days, arriving 7,771 effective at fatigue 0.55, one rest night bringing the battle-day start to ~0.25. **Battle:** the Agincourt scenario re-run with the march's bill (`agincourt_marched`: English fat0 0.25 instead of the original, generous 0.05) — **English win 10/10**, English dead 470 (vs 450 fresh: the march cost twenty more men at the line), French losses 4,315 including 1,185 prisoners, all inside the graded ranges.

Two things to say about that result. First, the campaign **closes**: every joint passes its own battery, and the numbers flow — no scenario file asserts a state another model didn't produce. Second, the chain *audited us*: the original battle scenario's fresh English were an unearned kindness, and the corrected version still passing means the validation survives its own supply chain. The 1415 commission is, as of this addendum, a playable physics from the first gun before Harfleur to the last prisoner at Agincourt — which is why §0 names it the vertical slice.

---

## 4 — Finding and avoiding: the next module, scoped

The brief's third clause — the struggle to find or avoid enemies — is in the model today only as authored path events (the Somme). The honest next module is the **intercept race**: two columns on a shared road graph, each trading pace against order against intelligence, with contact probability emerging from strand overlap and scouting spend — the Day Layer's marriage to the belief DB. Validation candidates already on the shelf: the 1415 Somme race itself (Boucicaut's shadowing force, run as the *other* player), and 1066's double race (Stamford Bridge north, then the Channel coast south) as the stress case where one army runs the entropy triangle twice in a month. Scoped, not built: it needs the campaign graph substrate, which is the vertical slice's next milestone anyway.

---

**Verdict:** the Day Layer is open and earning — the march model passes three historical ensembles and a counterfactual, contributes the pace-order-time triangle as the campaign's core decision space, and closes the first end-to-end campaign in the project's history. **Punchlist:** intercept-race module on the graph substrate; sack state and forage circuits (still L-spec, unbuilt); wire `march_model` outputs as the standard producer of battle-scenario class C fields; promote march constants into the class A registry under freeze discipline; Stamford–Hastings double-march as the next battery entry; the 1415 vertical slice declared and scheduled.
