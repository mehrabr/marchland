# MARCHLAND — Milestone M7, Revised: Scene-Time First, Then Meaning
### Addendum Y reorders M7 — the client's time model is foundational and must land before the meaning/sentiment layer renders on top of it

**Why a revision.** M7 (the meaning layer & the moving army) was scoped against the existing real-time-with-pause client. Addendum Y changes what the client's loop *is* — event-driven turns, the in-flight order queue, arrival-to-take-command. That is foundational: the sentiment field (M7.4) and its Table rendering (M7.6) surface *at decision points* and are *steered between scenes*, so the scene/event loop must exist before they can render correctly. The meaning work doesn't change; its *substrate client* does. Hence a new **M7.A** inserted ahead of the meaning milestones, and small amendments to two later ones.

---

## M7.A — The scene-based client (NEW; lands first, before M7.2)

Rebuild the CLI client's loop from real-time-with-pause to **event-driven turns** (Addendum Y §4). This is a *client* change only — `core/` is untouched (it already emits the timestamped event trace; M7.A teaches the client to stop at the consequential ones).

- **M7.A.1 — the decision-point stopping rule.** Define the decision-point event set (officer requests orders · contact/scout report · sentiment threshold · terms offered · dawn-before-battle · order outcome lands · deadline). The client advances `core/` until the first such event, renders it as a scene, takes input, resumes. *Acceptance: a season plays as a sequence of consequential scenes with time compressed in the cuts — no fixed-interval ticking surfaced to the player.*
- **M7.A.2 — the in-flight order queue (the decoupling).** Issuing an order pushes it onto a queue with `arrival_time = now + rider_latency`; it does **not** advance time. Advancing time is a separate act: **HOLD** (advance to the next decision-point event at the current station) or **MOVE** (advance across transit time; the player's station and belief-DB vantage switch to the new scene). Orders are delivered to recipients *at their arrival_time, interpreted against the recipient's belief DB*, and their outcomes become pending decision-point events. *Acceptance: a player can issue an order, then choose to hold for news or ride to a new vantage; the order resolves on rider-latency's clock independent of that choice; multiple in-flight orders can stack and surface each at its own moment; an order can still be in flight (unresolved) when the player arrives at a new scene.*
- **M7.A.3 — arrival-to-take-command as the default opening.** A command begins by arriving at camp with the guard, briefed by close officers against *their* (fallible, divergent) belief DBs, belief initialized to the camp's partial knowledge — never the trace. The wait-or-march choice is the first decision. Dispatch-from-afar becomes an advanced station. *Acceptance: the tutorial opens on the arrival scene starring a subordinate's briefing (the panel's "star a subordinate, not a spreadsheet"); reuses the belief-DB divergence already built.*
- **M7.A.4 — the VN-over-sim discipline, enforced.** Scene decision-tree branches are *queries to the live model*; no branch may carry a pre-authored outcome. *Acceptance: a test that every scene consequence traces to a sim event, not a script constant (the same shape as the chronicle's "must trace to an event" rule).*

---

## The meaning milestones, unchanged in substance, re-anchored on M7.A

M7.0 (the merged pursuit/steppe sim debt), M7.1 (sensitivity harness), M7.2 (the interpretation layer), M7.3 (the two audit rules), M7.5 (the dissolution-without-battle battery), and M7.7 (the officer-AI battery) are **unchanged** — they are core/battery work that doesn't depend on the client's time model. Two are amended:

- **M7.4 (the sentiment field) — amended:** the field still ticks at campaign-day resolution over the cohort graph, but its **player-facing surfacing now happens at decision points** via M7.A (a sentiment crossing a threshold *is* a decision-point event that stops the advance and renders a scene). *Added acceptance: a spreading sentiment interrupts the scene flow at the moment it crosses a threshold, presenting the player a scene with intervention levers — not a number ticking in a corner.*
- **M7.6 (render sentiment on the Table) — amended:** sentiment renders on the Table *within scenes*, and the intervention levers (dispatch a trusted officer, seed follow-a-winner, pay arrears, rest the idle unit, break up a rotted cohort) are issued **as in-flight orders through the M7.A queue** — so countering a rumor is itself an order that travels, lands on its own clock, and may arrive too late. *Added acceptance: the player can watch a mood turn across scenes and dispatch a counter that is itself subject to latency — steering sentiment uses the same decoupled order mechanic as everything else.*

---

## Revised sequence

```
M7.A  scene-based client            (NEW — foundational; the loop the rest renders in)
  ↓
M7.0  pursuit fix + steppe battery  (the merged sim debt; top sim priority)
M7.1  sensitivity harness           (load-bearing-vs-decorative table)
  ↓
M7.2  interpretation layer ┐ together — never the transform
M7.3  the two audit rules  ┘ without the guard
  ↓
M7.4  sentiment field               (surfaces at decision points, via M7.A)
M7.5  dissolution-without-battle battery entry
M7.6  sentiment on the Table        (levers issued as in-flight orders, via M7.A)
  ↓
M7.7  officer-AI battery            (large, self-contained; co-critical, sequenced last)
```

**Still explicitly NOT in M7:** the Rust port (after design freeze — and M7.A/X are design motion, so the freeze is *further* out now, correctly); fixed-point baseline regeneration (the port's first task); the Window/NPR (the 2D Table graduates first). `core/` keeps importing nothing from `clients/`; M7.A proves that boundary's worth — a foundational pacing change that touches only the client.

---

## Standing dissents carried into the revision
- **Vikram (further narrowed):** scene-based time answers the dead-time objection; only the Window-fidelity-attracts-pilots worry remains, now the *sole* surviving form of his dissent.
- **Priya (watch, sharpened by M7.A):** the inter-scene jump can hide a performance cliff — a single HOLD or MOVE may silently advance weeks of campaign sim across many cohorts with the sentiment field live. *Profile the cut, not just the battle tick* — this is now a named M7.A acceptance risk, not a someday-concern.
- **Bret, Sarris, Olleus (from M7, unchanged):** the destroy-it CI fixture is permanent; the meaning layer is documented as approximation not solution; the sensitivity table rewrites the cue-weight claim honestly if the geometry turns out to do the work.

**The revision in one line:** the client becomes a scene engine over the live simulation — stopping at consequence, decoupling the order from the wait, opening on arrival — *before* the meaning layer and the moving army render inside it, because they were always going to be experienced scene by scene, steered by orders that travel.
