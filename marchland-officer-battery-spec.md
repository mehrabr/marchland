# MARCHLAND — Spec: The Officer-AI Battery (Milestone M7.7)
### Validating that subordinates are *wrong like captains, never like pathfinding* — with Cannae as the capstone

**Status this closes.** The control geometry is built: orders travel at rider latency to officers, dispatches can't be recalled, the patron audits from a belief DB. What is *not* yet validated is whether subordinate officers are **competent agents** — the project's largest unvalidated risk, and the one the genre reliably fails ("friendly AI is stupid, so I'm forced to micromanage" — fatal for a game that forbids micromanagement). This spec defines the battery that converts officers from *specified and scaffolded* to *validated*.

**Where it lives.** `core/officer.py` (the decision model, mostly scaffolded in `belief_db.py` + `stations.py` today), scored by `battery/entries/officer_*.json` through the existing `battery/runner.py`, graded by `battery/targets.py` against the same `[range, grade, note]` convention as every other entry. Grade-A officer targets become pytest assertions in `battery/ci.py`.

---

## 1 — The officer decision contract

An officer is not a finite-state machine and not a pathfinder. Each time the simulation asks an officer to act, it runs **one decision function** with a fixed signature, and every battery entry below is a probe of this function:

```
decide(officer, standing_order, belief_db, repertoire, authority, trust) -> action
```

- **`standing_order`** — the last dispatch that reached this officer (at its arrival time, not when you sent it). May be stale, ambiguous, or contradicted by what the officer now sees.
- **`belief_db`** — what *this officer* perceives from *their* station: their wing with sightline noise, neighbors, the enemy to their front. **Never the trace.** This is the hinge — the officer reasons over partial, possibly-wrong information, so its mistakes are *informational*, not algorithmic.
- **`repertoire`** — the actions this officer's role can express (Addendum K). No "fighting withdrawal" in the repertoire → it is not an option, full stop. Killing the officer who holds a repertoire deletes those actions from the army.
- **`authority` / `trust`** — typed authority edges (can this officer be given this order at all?) and the trust ledger toward the commander (low trust = *safe* interpretation, the viscosity of obedience — not a mutiny flag).

The function resolves a standing order against present perception via a **lookahead over the officer's own belief** (the Front-tier model, per Addendum F): the officer simulates the likely consequence of obeying literally versus the available alternatives *in its own (wrong) picture of the field*, and picks. This is what produces period-plausible error: the officer does the locally sensible thing given what it (mis)believes, exactly as a real captain did.

---

## 2 — The grading bar: "wrong like a captain, never like pathfinding"

The battery does **not** score officers on winning. It scores them on *making defensible decisions under their information*. Two failure families, one rewarded behavior family:

```
PATHFINDING-WRONG (battery must reject) — the genre's disease:
  • walks into an obvious wall of pikes because the order vector pointed there
  • stands inert when its flank is open and unthreatened and action is free
  • oscillates / dithers between two actions with no information change
  • reads an order with zero interpretation (literal execution into catastrophe)
  • "knows" things its station cannot see (cheats by reading the trace)

CAPTAIN-WRONG (battery must ALLOW, even reward as plausible) — real war:
  • misjudges an ambiguous order in the direction its belief biases it
  • over-commits to a local success and loses shape (the eager subordinate)
  • holds a now-pointless position because the countermanding rider hasn't arrived
  • refuses a suicidal literal order and substitutes the nearest sane intent
  • acts on stale information that was true when the rider left, false on arrival

CAPTAIN-RIGHT (battery rewards) — competence:
  • exploits a genuinely open flank without being told (initiative within intent)
  • refuses to charge formed pikes with cavalry (repertoire-appropriate judgment)
  • reports honestly upward even when the news is bad for the officer
  • executes a hard order (fighting withdrawal) without it decaying into rout
```

The discriminator the runner uses: **trace every officer action back to the officer's belief state at decision time.** If the action was sensible *given that belief*, it passes — even if it lost. If it was senseless given that belief (or relied on knowledge the belief didn't contain), it fails. The grader literally reads the officer's belief snapshot from the trace and asks "was this a reasonable read of *this* picture?" That question is the whole battery.

---

## 3 — Connection to the rest of the system

The officer battery is where five existing systems are jointly exercised, which is why it was sequenced last:

- **Belief DB** — the officer's mistakes come from here; the test proves the officer reads *its* DB, not the trace. The post-battle Archive disclosing the enemy's belief table (already specced) is how the *player* verifies no cheating — the battery is how *CI* verifies it.
- **Stations + latency** — the standing order's staleness is a function of when the rider arrived; the battery includes entries where the order is provably out of date by the time the officer acts.
- **Repertoire (Addendum K)** — entries confirm a deleted repertoire (dead officer) removes options, and that officers never select outside their repertoire.
- **Trust ledger** — entries confirm low trust produces *conservative literal* interpretation and high trust produces *initiative*, and that neither is a random mutiny bit.
- **Institutions of meaning + sentiment (Addendum X)** — the capstone (Cannae, §5) requires the officer to hold a withdrawal's *meaning* against the cohort's reading of it; this is the only entry that fires the officer AI and the meaning layer together, and it is the boss fight.

---

## 4 — The battery entries

Eight entries, each a scripted situation with a graded expectation on the officer's *decision*, not the outcome. Each ships as `battery/entries/officer_<name>.json` and is replayable bit-identically. Grades follow the house convention (A: must hold, pytest assertion; B/C: findings).

### officer_open_flank (grade A) — initiative within intent
*Setup:* an officer holds the right wing under standing order "hold position." The enemy left has drifted, leaving an open, unthreatened flank within reach. *Pass:* across seeds, the officer **exploits the flank in the majority of runs** — wheeling to take it — because intent (win the wing) dominates a literal reading (stand still) when the opportunity is free and visible *in its belief*. *Reject (pathfinding-wrong):* stands inert every seed (no initiative) OR charges a flank it cannot actually see (trace-cheating). *Probes:* initiative, belief-bounded perception.

### officer_suicidal_order (grade A) — refusing the literal
*Setup:* the commander's dispatch, sensible when sent, is now "charge the ridge" — but a pike wall has since formed there, visible to the officer. *Pass:* the officer **refuses the literal charge in the majority of seeds** and substitutes the nearest sane intent (halt, or seek a flank), *if* its trust ledger is not maximal-deference. *Allow (captain-wrong):* a high-deference / low-trust officer obeys literally into the pikes — that is a *plausible* failure and must not be graded as a bug; it is the cost of a cowed subordinate. *Reject:* the officer charges with no interpretation regardless of trust (pure literal execution as the only behavior).

### officer_stale_order (grade A) — acting on yesterday's truth
*Setup:* the commander countermands an order, but the rider is still in flight; the officer acts on the superseded order at a moment when it is provably wrong. *Pass:* the officer **executes the order it actually holds** (the stale one), and the trace shows the countermand arriving *after* the action — the latency is the cause, not officer stupidity. *Reject:* the officer somehow acts on the countermand before it arrives (latency violation / trace-cheating). *Probes:* the latency model is real, not cosmetic.

### officer_ambiguous_order (grade B) — interpretation under noise
*Setup:* a deliberately ambiguous dispatch ("support the center") with two reasonable readings (reinforce vs. cover the flank). *Finding:* the officer's reading should **bias toward what its belief emphasizes** — an officer who sees the center buckling reinforces; one who sees a flank threat covers it. The *spread* across belief states is the result; no single reading is "correct." *Reject:* the officer picks randomly with no belief coupling (interpretation unanchored to perception).

### officer_cavalry_judgment (grade A) — repertoire-appropriate refusal
*Setup:* a cavalry officer is ordered (or tempted by a gap) to charge a formed, dense infantry line. *Pass:* the officer **declines to charge formed density in the majority of seeds** (the horse-balk judgment lifted to the command layer), preferring to threaten, wait for disorder, or seek scattered targets. *Reject:* charges formed pikes frontally (the genre's classic AI suicide). *Probes:* role-keyed judgment, consistency with the resolver's horse-balk physics.

### officer_dead_repertoire (grade A) — capability deletion
*Setup:* a cohort whose only "fighting withdrawal" specialist is killed mid-battle, then ordered to give ground under pressure. *Pass:* before the death the withdrawal is available and can be executed; **after the death it is not in the menu**, and the cohort under the same order either holds rigidly or breaks — it *cannot* perform the deleted action. *Reject:* the cohort performs a fighting withdrawal with no officer to key it (repertoire not actually gated by the officer). *Probes:* Addendum K's "kill the centurion, delete the menu item" in running code.

### officer_honest_report (grade B) — the upward channel
*Setup:* an officer's wing is faring badly; the officer must report upward (the dispatch that will feed the commander's and patron's belief DB). *Finding:* the report should reflect **what the officer believes**, including bad news — but an officer with low trust / high self-interest may *shade* the report (the seed of the lying-chronicle machinery). The *distribution* of honesty against the trust/interest receipts is the result. *Reject:* reports are always perfectly accurate (no belief-mediation — the patron audit's "injustice both ways" becomes impossible).

### officer_initiative_vs_trust (grade A) — the trust ledger is viscosity, not a dice roll
*Setup:* the same open-flank opportunity (as `officer_open_flank`) given to two officers — one high-trust, one low-trust — under identical "hold position" orders. *Pass:* the **high-trust officer takes initiative more often than the low-trust one**, monotonically across the trust range; low trust yields conservative literalism, *not* random disobedience. *Reject:* trust has no effect, OR low trust produces mutiny/erratic action (trust misread as a rebellion bit rather than interpretation viscosity). *Probes:* trust ledger semantics — the single most likely thing to be implemented wrong.

**Battery rule:** every entry asserts on the officer's *decision given its belief*, scored by the §2 discriminator. None asserts on winning the engagement. A correct officer that loses passes; a lucky officer that cheated its way to a win fails.

---

## 5 — Cannae, the capstone (officer AI + meaning layer together)

Cannae is the one entry that fires the officer AI and the institutions-of-meaning layer in the same test, which is why it is the boss fight and why it is sequenced last. The full scenario ships as `battery/entries/cannae_216bc.json` (included with this spec). Its thesis: **the frontage cap *is* the envelopment, and the controlled withdrawal of the center is a command decision, never a script.** The Iberian/Gallic center must execute "give ground without breaking" *and* hold the meaning of that order — `ordered_retreat_holds`, which attenuates its own `bodies_here` and `behind` cues (reading its dead as the expected price of a planned maneuver) — against the sentiment `we_are_losing`. If Mago (the meaning's keeper) falls, or the cohort's reading flips past threshold, the institution's `failure_conditions` trigger, the withdrawal becomes a real rout, the Roman mass pours through, and **the trap never closes.** The counterfactual (`kill_mago` at first contact) must produce a Roman victory or draw in the majority of seeds — teaching that the genius was the *system* (right troops, right meaning, right officer), not the trick.

### What a probe on the current reference resolver shows (honest baseline)

Running an approximation of Cannae on the existing `marchland_toy.py` (withdraw vs. hold vs. kill-Mago, 12 seeds each) produces the **diagnostic the spec exists to surface:**

- **The frontage-cap pathology is real and already present.** At mid-battle, ~648 of 800 Romans are in the rear ranks, unable to reach the fighting line (front ~0) — the deep, dense mass cannot bring its depth to bear, which is the exact historical blunder, emerging from `eff_foe = min(foe, 1.6·own + 2)` with no Cannae-specific rule. The *physics seed* of Cannae is in the engine today.
- **The decision half is unbuilt, and the probe proves it.** The withdraw / hold / kill-Mago variants return near-identical results, because the toy resolver has **no withdrawal behavior and no meaning layer** — the center cannot "give ground without breaking" because that repertoire doesn't exist yet, and its reading of its own dead can't be attenuated because the institution-of-meaning transform isn't wired. The Roman mass also collapses all-at-once rather than being enveloped *from the outside in* (the `behind`-cue cascade on the outer ranks first).

This is the correct result for a spec, not a failure: **Cannae confirms that the frontage cap (built) and the controlled-withdrawal-with-held-meaning (M7.7 + M7.X, unbuilt) are exactly the boundary between what the engine does and what it must learn to do.** The entry is therefore both the acceptance test for the officer AI *and* the regression guard that the frontage cap keeps working while the decision layer is added.

### Cannae's build dependencies (what must exist for it to pass)

```
1. fighting-withdrawal repertoire in core/officer.py   (give ground in contact without
                                                          the give-ground triggering panic)
2. the institution-of-meaning transform (M7.X)          (ordered_retreat_holds attenuates
                                                          bodies_here/behind before threshold)
3. the sentiment coupling (M7.X)                         (we_are_losing can flip the meaning)
4. outside-in envelopment in the cascade                 (behind-cue spikes on outer ranks
                                                          first as horns + cavalry close)
5. the converging-horn pursuit fix (M7.0)               (the encircled have nowhere to flee;
                                                          shares the Isandlwana miss)
```

Items 1–4 are M7.7 and M7.X; item 5 is M7.0, already the top sim-debt priority. Cannae passing is therefore a *single integrated proof* that the deferred officer, meaning, and pursuit work all landed correctly together — the most demanding entry in the whole battery, and the right one to declare the control model validated.

---

## 6 — How to run it, and the acceptance gate

```
# the eight decision probes (each asserts on belief-bounded decisions, not on winning)
make battery filter=officer_

# the capstone (officer AI + meaning layer + pursuit, one integrated proof)
python -m battery.runner --entry cannae_216bc --seeds 24
python -m battery.runner --entry cannae_216bc --counterfactual kill_mago --seeds 24
```

**The gate that declares the control model validated:** all grade-A officer entries green (pytest, in `ci.py`), `cannae_216bc` passing its `pass_conditions` *and* its `kill_mago` counterfactual flipping the outcome, and the Archive enemy-belief disclosure confirming zero trace-cheating across the suite. Until then, the covenant's central promise — *that you can step back and trust a subordinate* — remains specified and scaffolded but unproven, and this battery is the instrument that closes it.

**Verdict:** the officer is the spine of the control model and the control *geometry* works today (latency, irrevocable dispatch, belief-mediated audit). This spec defines the battery that validates the officer as a competent *agent* — eight decision probes against the "wrong like a captain, never like pathfinding" bar, plus Cannae as the integrated capstone where the officer AI and the meaning layer must fire together. A probe on the current resolver confirms the frontage-cap physics is already present and the decision layer is precisely the unbuilt boundary — making Cannae both the acceptance test and the regression guard for the work that closes the project's largest open risk.
