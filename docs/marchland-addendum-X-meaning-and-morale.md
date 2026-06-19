# MARCHLAND — Addendum X: Meaning, and Morale That Moves
### Institutions of meaning as an interpretation layer; sentiment drift as its transition function; both rendered on the Table

**Extends:** B (the two-channel morale model), K (officers as keepers of repertoire), S/T (the march model's idleness/hunger/arrears state), U (the Table). **Origin:** Sarris's standing dissent from the panel — that a universal appraisal substrate cannot represent the *institutions of meaning* that organized fear and cohesion differently across cultures — promoted from a named loss to a built layer, coupled with a second idea: an army's mentality as something that *drifts* across a season as sentiment spreads through the ranks. The panel's verdict: these are not two systems but one — **meaning is the state, sentiment-spread is the transition, the Table is where the player steers it** — adopted under guards strict enough to keep essentialism out.

---

## 1 — The problem this closes

The receipts doctrine models the *body* — fatigue, wounds, calories, the cues a soldier's senses report ("corpses near me," "men running behind me"). What it cannot currently model is what those cues *mean*. When a volley line takes casualties, the universal appraisal function reads the cue and tests it against a frozen threshold. But identical casualties meant different things in different armies — *the saints have abandoned us*, or *the expected price this regiment always pays*, or *a shame that demands a charge to wipe it out* — and no soldier in those three cases was braver than another. The difference is not in the body and not in a quality coefficient. It is in the **interpretation that sits between the event and the appraisal**, and it was built and maintained by institutions: cults, veteran cadres, sworn oaths, the reliability of a paymaster.

Addendum B's belief channel (`−1.1·belief` in the cue equation) was the thin version of this — one scalar knob. Addendum X replaces the knob with a layer.

---

## 2 — Institutions of meaning: an interpretation layer, not a quantity

**The architecture (Olleus's form).** An institution of meaning is a **mapping that transforms cue values before they reach the universal appraisal threshold** — never a number added to morale. The frozen, universal cue equation is unchanged; what changes is that its *inputs* pass through a cohort's current interpretation first:

```
raw cues  →  [institution-of-meaning transform]  →  transformed cues  →  UNIVERSAL threshold  →  appraisal
```

So a cohort whose dead are read as *the price of honor* has its `bodies_here` cue *attenuated* (and may gain a counter-impulse toward advance); a cohort whose dead are read as *abandonment by the saints* has the same cue *amplified*. Same corpses, same universal threshold underneath, different transform on the way in. The substrate stays species-universal — Law 1 intact — and the culture lives entirely in the transform. This is the hinge: **culture varies the interpretation of the inputs, never the machine that judges them.**

**The guard that keeps it from becoming "martial races" (Bret's law).** The genre laundered essentialism for forty years by letting "Culture X is aggressive" hide inside a +2. A meaning transform is the exact door that essence could walk back through — "Culture X reads its dead as shame and charges" re-derives "Culture X is aggressive" with more letters. The law that stops it, enforced in the receipts audit *in code*:

> **An institution of meaning is legitimate only if (a) it traces to a built institution with its own receipts — a cult with priests, a veteran cadre with names, an oath with a swearing-date, a paymaster with a ledger — and (b) it has failure conditions: states of the world that break it. If a meaning holds no matter what happens, it is an essence and the audit rejects the data file. The test is: _can you destroy it?_ An essence you cannot destroy; an institution of meaning you can.**

You destroy one by killing the cadre that carried it (Marcus's point: officer death now severs meaning, not just repertoire — the cohort that read its dead as honor *because he kept that reading* now reads them as merely dead), by breaking the oath, by missing the paydays until the saints stop paying dividends, by the sentiment drift of §3 flipping it. A meaning with no destruction path fails the audit exactly as a quality coefficient fails the loaded-dice grep.

---

## 3 — Sentiment drift: the transition function

**The idea.** An army's mentality is not a fixed lookup table a culture carries in; it is a *population of beliefs in motion*. A sentiment — *this campaign is cursed*, *we haven't been paid*, *the general spends us like water*, or the good ones, *we are the lucky regiment*, *we follow a winner* — **starts somewhere, spreads at a rate through the ranks, and changes what the army is by the time it reaches the field.** It is the dynamic half of §2: institutions of meaning are the standing interpretations brought in; sentiment drift is how those interpretations *change across the season*. A veteran cadre reads death as honor in week one; a string of pointless losses spreads the counter-sentiment *this is not honor, this is waste*; the meaning **flips** by week eight, and the same volley that would have triggered a vengeful charge now triggers a rout.

**The model (Priya's cheap form; Olleus's anchoring law).** Sentiment is a **field over the cohort graph**, not a simulation of individual opinions — a few scalar penetration levels per cohort (how far has *cursed campaign* spread into this unit), updated by neighbor-coupling on the *existing* social/authority graph each campaign-day tick. The same density-field trick the Lattice already uses, lifted to the social graph and run at day resolution. Individual opinion-agents buy nothing the field doesn't capture.

The non-negotiable constraint: **every transmission term reuses an already-tracked receipt. No new free constants.** This is what keeps it from being SIR epidemiology with an unanchored contagion coefficient — the exact unanchored-psychology error the project exists to refuse. The channels, each already a tracked quantity:

```
spread accelerates with:   idleness        (march model already tracks camp/idle days — the rumor mill)
                           hunger          (march model's starvation, already an order-solvent — now a sentiment-solvent)
                           arrears          (pay_arrears, already in the desertion term)
                           bond proximity   (the social graph's existing edges)
spread is resisted by:     officer authority intact and actively countering (the authority graph of Addendum K)
seeding events:            a pointless loss, a broken promise, a miracle, a won fight, a paid wage
```

**Why this is historically right (Bret's anchor).** Armies did not dissolve from combat; they dissolved in *winter quarters*, in *sieges*, on *long idle marches without pay* — precisely the idle-hungry-unpaid states the channels name. The mutiny on the Spanish Road, the legions that changed sides in the civil wars, the armies of 1917: sentiment spread fastest exactly where men sat still, hungry, unpaid, and talking. A transmission function driven by idleness, arrears, and proximity reproduces, without being told to, the genre's biggest blind spot — **the army breaks between the battles, not in them** — which is the one thing a campaign-season game above all others should capture.

---

## 4 — The coupling, and the Table (Dana's resolution)

The two ideas compose into one loop:

```
institutions of meaning  =  the STATE      (how this cohort currently reads events)
sentiment drift          =  the TRANSITION (how that reading changes, day by day, driven by receipts)
the battle appraisal     =  the READOUT    (transformed cues meet the universal threshold)
```

And the player must *see and steer it*, or it becomes merely a second invisible system telling them "no" (Vikram's standing dissent — the legibility requirement is the mitigation). **Sentiment renders on the Table** exactly as enemy positions do: the army's mentality is a visible field spreading across your own cohorts, with the same uncertainty grammar (you may not know a unit's true mood without a present, trusted officer reporting it). Managing the spread becomes a **primary verb of the season**, with levers that are all existing systems pointed at the field: dispatch a trusted officer to counter a rumor (authority vs transmission), win a small fight to seed *we follow a winner*, pay the arrears, rest the idle unit before the rumor mill turns it, break up a cohort whose meaning has rotted before it infects its neighbors. The Table already renders belief with charcoal-to-painted finish; now it also renders sentiment, and the season's drama is watching the mood turn while you still have time to act.

---

## 5 — Schema (the data layer carries it; the audit guards it)

```
institution_of_meaning:
  id, carried_by         # role/cadre/cult/oath/paymaster — the receipt for WHY this meaning exists
  transform              # cue → cue mapping (e.g. bodies_here ×0.6, +advance_impulse)
  failure_conditions     # REQUIRED, non-empty — states that break it; empty = audit rejects the file
  break_effect           # what the cohort reads instead once broken (often: the raw, untransformed cue)

sentiment:
  id, valence            # e.g. cursed_campaign (−), follow_a_winner (+)
  affects                # which meaning(s) it strengthens or flips
  transmission           # weights over EXISTING receipts only: {idle, hunger, arrears, bond, ...}
                         #   audit rejects any transmission term not backed by a tracked quantity
  seed_events            # what plants it (a pointless loss, a paid wage, a miracle)
  counter                # what an officer with authority can do against it
```

The receipts audit (`receipts_grep`, already CI) gains two rules: **a meaning with an empty `failure_conditions` fails the build** (Bret's destroy-it test, enforced in code — the single most likely place for essentialism to re-enter the project years from now, per his standing watch); and **a `transmission` term referencing any quantity not in the tracked-receipts registry fails the build** (Olleus's no-free-constants law). Both go in the sensitivity harness like everything else.

---

**Verdict:** Sarris's loss becomes a layer rather than an apology — culture enters as the interpretation of cues, never as a coefficient over them, with a destruction test that keeps the substrate honest; and the army's mentality becomes a contagion field driven entirely by receipts the march model already tracks, reproducing the historical truth that armies break between battles, rendered on the Table as a steerable primary verb. Meaning is the state; sentiment is the transition; the player watches the mood turn. **Punchlist:** the interpretation-layer transform between raw cues and the frozen threshold · officer-death severs-meaning coupling · the sentiment field over the cohort graph at day resolution · the two new receipts-audit rules (failure-conditions-required, transmission-receipts-only) · sentiment rendered on the Table with intervention levers · a meaning/sentiment battery entry (a season that breaks an army without a battle — the winter-quarters dissolution) · the whole layer fed through the sensitivity harness.
