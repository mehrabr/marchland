# MARCHLAND — Addendum Y: Scenes, and the Order in Flight
### Event-driven turns replace real-time; command begins by arrival, not summons; and issuing an order is decoupled from spending the wait

**Extends:** F (the headless core + trace), H/I (the three rooms, the chronicler's eye), J (the stations), and supersedes the real-time-with-pause assumption carried implicitly since Addendum A. **Origin:** the panel's finding that *the project was real-time by inheritance, not by design* — every structural force (the headless event trace, the chronicle's scene form, the primary sources' own compression, the buyer's tolerance, the engine budget) already pointed at scene-based time — plus a refinement from Mehrab that decouples the two things the panel's model had fused: **issuing an order and advancing time are separate acts, and the player chooses how to spend the wait.**

---

## 1 — The pacing model: event-driven turns

The simulation is **not** experienced minute-to-minute. The internal time-step is unchanged physics (the resolver ticks at 2s, the march at 1 day — those never change); what changes is the **player's interaction cadence**, which is now decoupled from the clock. The client runs the sim *between* interaction points and hands control back at **decision-point events** — not at fixed intervals:

```
an officer requests orders        contact is made / scouts report
a sentiment crosses a threshold   terms are offered or demanded
dawn breaks before a battle       a rider arrives with news
an order's outcome lands          a deadline expires
```

These are already events in the trace. The client's loop becomes: **run the sim to the next decision-point event, render that moment as a scene, take the player's input, resume.** The expensive real-time render path becomes *optional* — you stop needing 60fps battle animation as a requirement for play (Priya's load reduction), and the season is experienced as the sources wrote it: scene to scene, the tedium compressed in the cut, the crises dilated (Bret's primary-source form). The pacing model and the chronicle model become the same shape — the memoir the career frame already auto-compiles.

**Different scenes operate different levers at different time-grains.** A council is a pure decision tree (no time passes — choice only). A march leg is a scene that passes *days* and surfaces the entropy levers (pace, road, rest). A battle is a scene that drops to the *fine grain* where the dispatch tension lives. The player moves between control levers by moving between scenes. This is the VN *form* — scene, choice, consequence, next scene — as the **presentation grammar**, with the simulation as the **truth behind every scene** (Priya's guard, load-bearing): decision-tree branches are *queries to the live model*, never pre-authored outcomes. The moment a scene's consequence is scripted rather than simulated, the validated engine has been thrown away for a Telltale game.

---

## 2 — Command begins by arrival, not summons

"Send a summons and wait" was only ever *one configuration* of the three station primitives — **station, latency, belief DB** (Sam's invariant). It is not the natural opening, and it is not even the default. The default way a command begins is now: **you arrive at the camp with your guard and close officers to take command.** Mechanically this is the same three primitives at different values — station becomes `Camp`-present (you are physically there), latency is face-to-face for the officers in the tent and long for everyone in the field, and the belief DB initializes to *whatever the camp currently knows*.

Two things make this *better* than the summons framing, not merely equivalent:

**It is more historically honest (Bret).** A commander arriving to take over did *not* receive ground truth — he received his predecessor's dispositions, his officers' competing accounts, and a map that was wrong. Arrival initializes the belief DB to the *camp's* partial, contested, possibly-stale knowledge — **never the trace.** The "wait for reinforcements or march now" choice is then the real decision, made on bad information: the Roman general taking over a province, the relief commander reaching a siege.

**It is the officer AI's natural showcase (Marcus + Dana).** Instead of you sending intent into the fog, the fog reports *to* you: your close officers brief you against *their* belief DBs — and the officer losing the siege downplays it while the one who wants reinforcements oversells the threat. The first gameplay of a command is *reading your own staff*, which is the character hook the panel said the tutorial must star. Dispatch-from-afar (the Camp-at-distance, play-by-mail seat) is demoted to an *advanced* station you graduate to.

---

## 3 — The order in flight: issuing is decoupled from waiting

This is the refinement that distinguishes the model from every prior version, including the panel's. The panel fused "issue order" with "advance time" — dispatch, time jumps, results appear, atomically. **They are now two separate acts.**

**Issuing an order only queues it.** The rider departs; the order is in flight; it is irrevocable. *Time does not automatically advance.* The order now lives in a **queue of in-flight orders**, each carrying its own arrival time (set by rider-travel latency — geography, not the player, governs when it lands).

**Advancing time is a separate, deliberate player act — and the player chooses how to spend the wait.** Two ways:

```
HOLD at the current scene      stay in the tent; let hours pass; more reports trickle in;
                               commit further orders or wait for news before deciding

MOVE to a new scene            ride to the ridge; change station (Camp → Hill → Knot);
                               time passes to cover the transit, and you arrive seeing
                               the field from a DIFFERENT vantage — a different belief DB
```

Either way, when the player next stops, enough time has elapsed that the order *should* have arrived — so the next scene reveals **whether it was received, and whether it took effect or not.** The latency is in the world; the player's *position during* the latency is the choice.

**Why this is the correct model, point by point:**

- **The order and the time-passage are no longer the same button.** "Pass time" stops meaning *resolve my order* and starts meaning *choose my exposure during the wait.* The order resolves on its own clock (rider latency); the player spends those same minutes however they choose. A commander who waits in the tent and one who rides forward both learn the ridge's fate after the same elapsed time — **but from different vantages, having seen different things en route.**

- **Changing scenes becomes mechanically load-bearing, not cosmetic.** Riding from Camp to Hill mid-wait means you arrive at the next decision point seeing the field differently than if you'd held — and your earlier order may now look wise or catastrophic in light of what the new vantage reveals, *and you still cannot recall it.* The station-change and the order-resolution interleave on **independent clocks** — which is exactly Balaclava: an order issued from one vantage, arriving at another, judged by events the issuer could not see when they sent it.

- **The covenant gets sharper than Marcus's guard left it.** His guard was "scenes can resolve with your order in flight." This adds: *the player chooses the duration and the vantage of the in-flight period.* The no-undo is not merely preserved — the player must *spend the waiting time deliberately*, owning the consequence more completely. You didn't just issue an irrevocable order; you *decided how to wait for it*, and that decision is irrevocable too.

- **Orders' resolutions and scene transitions land on separate clocks, so they can desync — and that's a feature.** You might move to a new scene and arrive *before* the order could have been received (the rider's still out; the scene shows nothing resolved yet, only the wait continuing). Or you hold long enough that *multiple* orders' resolutions stack up. The client tracks a **live queue of in-flight orders, each surfaced at its own arrival moment** — which is the true model of a headquarters: always several orders in flight at different stages, never one dispatch-and-result beat.

---

## 4 — What the client's loop actually does now

```
loop:
  render the current scene from the player's belief DB (with uncertainty finish)
  collect player actions, which are any mix of:
      • issue order(s)      → push onto in-flight queue with arrival_time = now + rider_latency
      • HOLD                → advance sim until the next decision-point event AT THIS STATION
      • MOVE to scene S      → advance sim across transit time; player's station/belief DB ← S
  while advancing:
      run core/ forward; when any in-flight order's arrival_time is reached,
        deliver it to the recipient (interpreted against THEIR belief DB), and
        mark its outcome as a pending decision-point event
      stop at the FIRST decision-point event (an order landing, contact, a threshold, dawn…)
  the scene that renders next is whatever event stopped the advance —
      which may be your order's consequence, or something that happened WHILE you waited
```

`core/` is unchanged — it simulates and emits events. The **client owns the stopping rule** (which events demand a human) and the **in-flight order queue** (the decoupling of issue from resolve). This is the only architectural change Addendum Y requires, and it lives entirely in the client, never the core.

---

## 5 — What this answers and what survives

Adopting scene-based event-driven turns **converts Vikram's central objection into a strength**: his complaint was real-time's *dead time* — watching couriers cross a map, fast-forwarding through nothing. Here the boring waits are *the invisible cut between scenes*, and every scene the player is in is consequential. The difference between a flight simulator (real-time, mostly tedium) and a war movie (scene to scene, all consequence): players who'd never tolerate the former will play the latter. **Surviving dissent:** the no-undo remains (sharpened, §3); and Vikram's *other* worry — that scene-based polish plus Window fidelity recruits buyers who'll want a free-camera "drive it yourself" mode — is untouched by the pacing fix and stays live.

**Verdict:** the project sheds the real-time model it held by inheritance. Time is event-driven and scene-based — the form of the primary source and the chronicle alike. Command begins by *arriving to take it*, briefed by fallible officers, which is more honest than the summons and is the officer AI's showcase. And issuing an order is *decoupled* from spending the wait: orders queue and resolve on geography's clock, while the player separately chooses to hold for news or ride to a new vantage — owning both the order and the manner of waiting for it, neither recallable. **Punchlist:** the client's event-driven loop with the decision-point stopping rule · the in-flight order queue with per-order arrival times and desync surfacing · the arrival-to-take-command opening as the default, dispatch-from-afar as an advanced station · the HOLD / MOVE wait-spending choice with station-change updating the belief DB vantage · scene templates per lever-grain (council = decision tree; march = days; battle = fine grain) · the VN-form-over-live-sim discipline enforced (branches are sim queries, never authored outcomes) · profile the inter-scene jump for the hidden-cost cliff Priya flagged (a single cut may silently run weeks of campaign sim with the sentiment field active).
