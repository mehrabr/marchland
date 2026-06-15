# MARCHLAND — Addendum R: Answering the Review
### The four critiques resolved — with code where code was owed

**Extends:** Addendum Q's red-team review, whose four corrections are here discharged: (1) the validation battery now carries source-criticism; (2) the universalism doctrine is reframed; (3) **the siege got its battery before the renderer got a dollar**; (4) wrong dossiers are specified. Critique 3 demanded experiments, so most of this addendum is experimental record: a new siege-clock model validated against Harfleur 1415, and an assault battery run on the existing lattice engine.

---

## 1 — The siege battery (critique 3)

### 1a. The clock: Harfleur 1415

A new module (`siege_clock.py`, ~110 lines) models the operational siege as the dual-clock race the literature describes: the besieger's disease and supply clock against the town's hunger and wall clock, ending — as most sieges did — in the **summons-and-terms negotiation**: the garrison yields honorably once a breach is practicable or a creditable duration has passed, *if* relief looks hopeless within the customary window, striking the conditional-surrender pact the period's siege law expected. Harfleur is the validation target because it is the canonical conditional surrender (terms struck 18 September: yield on the 22nd absent relief) *and* because it produced the army our validated Agincourt scenario already simulates — the battery now covers the campaign end to end.

Inputs are receipts only: 11,500 besiegers, sea supply (no starvation clock for Henry), twelve great guns against strong walls, and a camp factor of 2.2 for the marshes and August heat that made the dysentery. Class A siege constants were calibrated once and frozen.

**Results (100 seeds):** negotiated surrender in 87%, at a median of day 38 (range 36–47) against the historical ~35; besieger unfit (dead + sick) median 27%, inside the 15–35% band the contested sources span; storms launched in 13% of seeds, only under extreme disease pressure — a flagged tension with the historical no-storm, recorded in the calibration file rather than tuned away. **The counterfactual:** a French relief army arriving day 25 flips the ensemble to 100% RELIEVED — the storm threshold is never reached by then, so the model's Henry faces what the real one feared: fight a field battle early or lift the siege. The siege clock produces the strategic geometry of 1415 from receipts.

### 1b. The assault battery: ladders, breaches, hunger

Four scenarios on the existing lattice engine (one toy agent = 10 men; 400 garrison vs 2,000 stormers; 12 seeds each): escalade (six ladder frontages) and practicable breach (one 24m rubble gap), each against a fresh garrison and a starved one (fatigue 0.55, belief 0.55 — five weeks of siege written into class C).

| variant | carried | repulsed | t(carry) med | stormer dead | garrison dead |
|---|---|---|---|---|---|
| escalade vs fresh | **0/12** | 12/12 | — | 490 | 60 |
| escalade vs starved | 5/12 | 7/12 | 224s | 500 | 70 |
| breach vs fresh | 2/12 | 10/12 | 128s | 220 | 55 |
| breach vs starved | 5/12 | 7/12 | 96s | **110** | 45 |

The ordering is monotone on both axes: hunger raises the carry rate (0→5 of 12 on ladders), and the breach collapses the *cost* of attacking (490 stormer dead on ladders vs 110 at the rubble) while carrying faster when it carries at all. Escalade against an alert garrison fails twelve times in twelve at an 8:1 casualty exchange — the engine's restatement of why escalades were acts of desperation, and why the hunger clock, not the ladder, was the siege's real weapon.

### 1c. What the engine forced us to learn

The assault scenarios refused to work until five mechanics existed, and the refusals are the findings. The wall had to become a **contact filter**, not just a movement barrier (early runs had men fighting through stone, smearing the assault into a wall-length trickle). Stormers had to **funnel** — clamped men sidling along the wall toward the nearest ladder, because an assault is a queueing problem before it is a fight. The garrison had to **man the threatened points** — a deployment fact, not a stat; random placement left empty ladder lanes and instant farce. Carrying the wall needed an **operational adjudication** (three hundred stormers standing inside decides the position; the urban fight beyond is another scenario's problem). And the finding that produced the correct ordering all by itself: **rubble denies formation to both sides.** A breach doesn't merely remove the rampart's cover from the defenders — no one forms ranks on a collapsed wall, so the cover term dies for attacker and defender alike, and the breach fight becomes the mutual-exposure slaughter the sources describe. The wall's military value was never an elevation bonus; it was *formation geometry*, and a practicable breach deletes geometry for everyone standing in it. That single rule is why stormable did not mean cheap, and why the forlorn hope was named honestly.

### 1d. The regrade catches the designer

One target failed as graded: breach-vs-starved carried 5/12 against a "carried in the majority" expectation. Before patching the engine, the new method (§2) requires auditing the *target* — and the target turns out to be the designer's folk-history. At Badajoz the practicable breaches were never carried; every assault into them was massacred, and the town fell by escalade elsewhere. The literature's actual pattern is that breaches were *cheaper and more frequent* routes to a carry, not reliable ones — which is what the table shows. The calibration file now records both readings: the naive target (failed) and the Badajoz-informed one (passed), with the lesson attached: **source-criticism cuts both ways, and the first historiography it corrected was ours.**

---

## 2 — Source-graded calibration (critique 1)

Every battery target now carries three fields: a **range** (never a point), a **source grade** (A: securely attested; B: well-supported pattern claim; C: contested numbers or literary convention), and a note on where the target comes from. The full battery, re-graded and re-scored against the existing results:

| scenario | target | grade | achieved | verdict |
|---|---|---|---|---|
| Isandlwana | Zulu victory | A | ✓ | pass |
| Isandlwana | ammo starves before break | A | 16/16 | pass |
| Isandlwana | defender dead 50–90% | B | 40% | **miss (real)** |
| Isandlwana | Zulu losses 5–20% | C | 10% | pass |
| Agincourt | English victory | A | ✓ | pass |
| Agincourt | French losses 4,000–11,000 | C | 4,435 | pass |
| Agincourt | English dead 112–600 | C | 450 | pass |
| Agincourt | asymmetry ≥ 5:1 | B | 11:1 | pass |
| Hastings | Norman victory | A | ✓ | pass |
| Hastings | contested (loser wins 20–50% of seeds) | **C** | 0% | tension, re-scoped |
| Hastings | pre-break deaths ≤ 10% | B | 20% | **miss (real)** |
| Hastings | Harold falls late | A | 7/12 | pass |
| Harfleur | negotiated absent relief | A | 87% | pass |
| Harfleur | duration 30–40 days | A | 38 | pass |
| Harfleur | besieger unfit 15–35% | C | 27% | pass |
| Harfleur | storm rare/none | A | 13% | tension, flagged |

Two re-scorings matter. **Agincourt is upgraded to a full pass:** the English-dead figure that Addendum E reported as "high" sits comfortably inside the C-grade range once the range is honest about how contested the chronicle numbers are. And **Hastings' famous miss splits in two:** the "near-run" expectation was always a C-grade target — a literary convention of partisan sources (and the phrase itself is Wellington's, about the wrong millennium) — so the engine's 12/12 is recorded as *tension with a weak target*, not failure; while the casualty-shape violation (20% dead before the break, against the B-grade pattern that casualties concentrate after collapse) survives regrading as a real miss. Phase pacing therefore remains mandatory — but now for the defensible reason, which is exactly what the method is for. Isandlwana's kill-share miss also survives: the annihilation is securely attested, and our pursuit still under-delivers it.

---

## 3 — The universalism clause, rewritten (critique 2)

The design-bible paragraph, replacing every prior statement of the doctrine:

> *Class A constants are identical for every human in the simulation. This is a **normative commitment with empirical costs**, not a discovered fact. The physiological floor (fatigue curves, wound tables) is well-supported; the appraisal layer — what frightens, what steadies, how panic moves — is a theory of mind whose universality is a live question in the psychological literature, and our universalism there is a modeling* choice*, made because the alternative (per-people psychological coefficients) reintroduces, through the back door, the essentialism this project exists to refuse, with historiographical costs we judge worse than the empirical ones we accept. The costs are real: a universal appraisal substrate renders cultural difference entirely through receipts and may flatten differences that were neither receipts nor essences. We take that loss knowingly, we name it here, and the receipts audit polices the commitment without pretending it is culture-free — it makes the substrate's assumptions* uniform*, which is a different thing from making them true.*

---

## 4 — Wrong dossiers (critique 4)

The rupture system's diagnosis dossier gains a `truth_alignment` field, and the launch slate gains its worked example from the battery we already own. **Post-Isandlwana Britain:** the trace says dispersion and ammunition logistics — the line too thin, the supply point too far from the flanks, exactly what 16 of 16 seeds show. The court's dossier factions say otherwise, as the real one did: the ammunition-box-screws story (a quartermaster's myth with a long historiographical afterlife), native treachery, the dead Pulleine's incompetence — each faction's diagnosis protecting someone's institution, none quite matching the certificates. The player who reads the Archive can back the unpopular true reform (close-order doctrine, ammunition distribution) against the court's preferred one; the player who doesn't will fortify the wrong lesson and meet the consequence at the next test. Mechanically: each dossier faction is a reform package with a license discount and a `truth_alignment` score against the trace; the discount and the truth are independent axes, and the gap between them is the scenario's teeth. Institutions reform around the lesson they can afford — now the player gets to be the one who can't afford the right one.

---

**Verdict:** all four critiques discharged — three in design and documentation, the central one in running code: the siege battery exists, passes 7 of 8 graded targets with two flagged tensions, and contributed the rubble finding to the core model. The build order's renderer line remains unspent. **Punchlist:** carry the rubble rule and contact-filter wall into the engine spec proper; promote `siege_clock` parameters into the class A registry with the same freeze discipline; wire the relief-counterfactual into the Harfleur rupture scenario; apply the graded-calibration format retroactively to every future battery entry; ship the Isandlwana wrong-dossier as the rupture slate's tutorial-adjacent example.
