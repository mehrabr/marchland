# MARCHLAND — Vertical Slice: "One Order, One Battle, One Truth"

*The smallest end-to-end cut through all three layers (sim → trace → Ren'Py) that is also a real, representative ~10-minute play experience. Companion to the audit spec (v2), the UI spec, and the Ren'Py integration architecture. This slice exists to answer one question — **is the loop fun?** — and, second, to prove the integration works for real.*

---

## 0. The experiment (read this first)

A vertical slice is not a demo. It is a falsifiable test, and it must be allowed to **fail**.

**Hypothesis under test:** *Command-under-uncertainty — partial and contradictory knowledge, a single irrevocable order delayed by geography, living with the consequence, and a record you must see through — is compelling in ten minutes.*

**It PASSES** if a naive playtester, with no explanation:
- hesitates before committing the order (the irrevocability is *felt*, not just stated);
- is surprised or vindicated by the outcome relative to how they read the rumor;
- has an audible "oh—" at the chronicle→trace scrub (the record *recontextualizes*, it doesn't just decorate).

**It FAILS / signals a pivot** if:
- the order feels arbitrary (knowledge too thin to reason with, or too clear to agonize over);
- the wait reads as dead time rather than tension;
- the scrub reads as a gimmick rather than a re-framing of what they thought happened.

If it fails, you have spent the *minimum* to learn the core loop needs rethinking **before** building the season, the officer integration, or a line of art. That is the entire value. Do not pad the slice to make it pass.

---

## 1. Scope — ruthless

**IN (the one loop):** one engagement, approached and resolved, from one-to-two stations, ending in the chronicle/trace reveal.

| In scope | Out of scope (explicitly) |
|---|---|
| 2 stations: the Hill (latency 1), the Knot (latency 0) | The full station map; FRONT_RANK; the Window |
| 1 belief Table: 3 markers, uncertainty-as-glyph | Painted miniatures, the sand-table fidelity |
| 1 decision point: a contact report + 1 officer portrait | The officer *model* (`officer.py`) — stays a spike |
| 3 order choices → 1 battle parameter | The opportunity feed, multi-order juggling |
| 1 in-flight order + HOLD/MOVE wait | Multiple concurrent orders, the season economy |
| 1 headless battle (Agincourt, seeded) | Multiple battles, sieges, the full chain* |
| 1 chronicle + 1 trace-scrub reveal | Sentiment/dissolution, winter court, culture variation |
| Save/load (free), rollback-blocking | Replayability tuning, balance, content breadth |

*The full `run_chain_1415` works and adds nice arrival-fatigue texture; use a **single battle** for the slice to minimize moving parts, and upgrade to the chain only if the single battle proves fun.

---

## 2. The walkthrough (the player's ten minutes)

1. **Open on the Hill.** The Table screen shows your belief, rendered as finish: your line `*` (confirmed), an enemy column on the ridge `~` (scouted, 2h old), and a body of horse beyond the wood `?` (rumored). The Hill's latency is 1 — orders take a day to land. The rumor is the crux: *do you believe the cavalry is there?*
2. **The officer asks.** A portrait, a line of dialogue — the captain reports the contact and requests orders. (One sprite, one background. This is the VN idiom doing what it does best.)
3. **You commit an order** (dialogue menu, irrevocable):
   - *Hold the ridge* — stand and receive.
   - *Refuse — withdraw over the bridge* — decline battle (a different consequence; the burn clock and the chronicle's opinion move).
   - *Offer open battle* — accept on the open ground, flank exposed to the maybe-cavalry.
   Each choice sets exactly **one battle parameter** (reuse `agincourt.py`; the order decides whether the French cavalry cohort is present on your flank, or your posture). The cavalry *is* real — the slice quietly punishes ignoring the rumor and rewards accounting for it.
4. **The order goes in flight.** It queues as a `PendingOrder` (eta = today+1) and `renpy.block_rollback()` fires — you cannot rewind and unmake it. Then you choose **how to wait**: HOLD on the Hill, or MOVE to the Knot (latency 0, closer — but you trade the Hill's wider view). Either advances the season clock to the order's arrival.
5. **The battle resolves headless.** The sim runs (seeded, deterministic); a trace is produced. It renders as the **morning-after chronicle** via `generate_chronicle(trace)` — sympathetic prose: *"The line held under the arrow-storm until the enemy horse swept the flank and broke them; the captain fell sword in hand at the front."*
6. **The reveal — scrub to the trace.** Toggle from chronicle to the trace timeline (the DeathCerts). Casualties were *light* until the break; the break came from fatigue-percolation, and most deaths fell in the **pursuit, after** the line was already gone; the captain died by a sword in the rear, in the ditch, long after the front "held." The chronicle's drama was wrong about the *mechanism* and the *captain's death*. The thesis lands in one toggle: **hard to predict, easy to explain, recorded imperfectly.**
7. **Consequence + save.** The outcome — and whether your read of the rumor was right — carries forward as one state change. The game saves. You learn what the rumor cost you.

---

## 3. What each layer does (reuse vs. new)

| Piece | Layer | Status |
|---|---|---|
| Seeded battle resolution → trace | 1 (`core/`) | **Reuse** — `Battle(scn, seed).run()` |
| Trace: deaths (cause/location/time), routs, win | 2 | **Reuse** — already serializable |
| `generate_chronicle(trace)` | 1 (`tools/`) | **Reuse** — exists, used by the CLI |
| Stations + latency | 1 | **Reuse** — `stations.py` |
| `PendingOrder`, season clock, decision points | 1 | **Reuse** — `season.py` |
| Belief view for the Table | 1/2 | **Reuse** — `belief_db.py` |
| Save / load / text history / self-voicing | Ren'Py | **Free** |
| Ren'Py project + integration glue | 3 | **New** — Model A import or B subprocess (see integration doc) |
| The Table screen (3 glyphs + labels) | 3 | **New, small** — a `screen` block |
| 1–2 station scenes (background + 1 portrait) | 3 | **New, small** |
| Order menu → `PendingOrder` + 1 battle param | 3 + thin glue | **New, small** |
| HOLD/MOVE wait → `season.advance()` | 3 + glue | **New, small** |
| Chronicle view (prose) | 3 | **New, small** — render existing output |
| Trace/scrub view (timeline toggle) | 3 | **New** — the reveal UI |
| `renpy.block_rollback()` on commit | 3 | **New, one line** |
| 3.12 re-pin + re-bless golden hashes | 1/CI | **One-time** (Model A only) |

**The only optional new *core* work:** if you want the chronicle to diverge *factually* (the tapestry's arrow vs. the trace's sword) rather than by *emphasis* (the horse vs. the percolation), add a thin `chronicle_bias()` layer. The slice does **not** need it — emphasis-divergence is more on-thesis and already emerges from summary-vs-detail. Leave it out of the slice.

---

## 4. Build order — walking skeleton first

Build the thinnest end-to-end thread, then add layers. Step 1 alone validates the entire integration architecture.

1. **The pipe.** A Ren'Py button → `Battle(agincourt, seed=0).run()` → print `win` + `generate_chronicle(trace)` on screen. No Table, no choices. *Proves: Model A/B works, numpy runs inside/beside Ren'Py, the 3.12 re-pin holds, the trace crosses the boundary.* This is the riskiest integration moment — do it first.
2. **The reveal.** Add the chronicle↔trace toggle: same trace, two views (prose vs. DeathCert timeline). *Proves: the thesis payoff renders.*
3. **The command surface.** Add the Table screen (belief glyphs) and the officer decision-point scene. *Proves: the belief DB reads as finish; the VN idiom carries the report.*
4. **The irrevocable order.** Add the 3-choice menu → `PendingOrder` + the one battle parameter + `block_rollback()`. *Proves: a felt, permanent choice changes the outcome.*
5. **The wait.** Add HOLD/MOVE → `season.advance()` → the clock and station switch. *Proves: latency reads as tension, not dead time.*
6. **Playtestable polish.** One portrait, one background, legible text, the save working. **Then put it in front of someone who has never seen it and run §0.**

Each step is independently runnable; if you stall, you stall with a working previous step.

---

## 5. Reading the result

- **Technical success** (binary, easy): a fresh player completes the loop; the battle resolves deterministically; the trace renders both ways; the order cannot be rewound; save/load works. If §0's *technical* bar passes, the integration architecture is proven and Model A/B is the right call.
- **Experiential success** (the real test, §0): runs **3–5 naive playtesters**, watch for the three "pass" tells and the three "fail" tells. Don't ask "was it fun?" — watch whether they *hesitate*, whether they *react* to the outcome, whether they *re-read* at the scrub. Their hesitation is the data.
- **The decision it unlocks:** pass → the loop is worth scaling; *now* the season, the officer integration, and the art are justified investments. Fail → pivot the loop now, having spent days, not months — and having touched none of the expensive surfaces.

---

## 6. What this slice deliberately does NOT prove

So expectations are honest. It says nothing about: season-scale pacing and fatigue of attention; whether the officer *model* is fun once wired; multi-culture variation; sentiment/dissolution and the winter court; the campaign economy and ransoms; long-term replayability; or art direction. It tests **one loop and one question.** Every other open item from the panels remains open by design — this is the probe that tells you whether they're worth answering.

---

*An execution plan, not an implementation. The simulation core, the chronicle generator, and the validation battery already exist in the repository; this slice wires the thinnest representative path through them and a Ren'Py skin, to find out — cheaply — whether the game underneath is fun.*
