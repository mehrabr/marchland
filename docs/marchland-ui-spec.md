# MARCHLAND — Graphical UI Specification
### The Table, the Window, and the Dive

*High-level interface spec, derived from design Addendum U (The Table and the Window) and Addendum Y (Scenes, and the Order in Flight). This is the interface design, not an implementation; the simulation core, validation battery, and reference code live in the repository.*

---

## 1 — The principle

There is a single headless simulation, and the only object inside it that knows everything is the `trace`. Every surface the player touches is a *partial view* of that truth. The interface is built so the player never confuses the two — and so the gap between what is known and what is true becomes the texture of command rather than a failure of presentation.

```
                    Headless simulation core
                 (the only omniscient object: the trace)
                          /            \
              Your belief database     A fixed command seat
              (partial, latent,        (front rank · knot ·
               possibly stale)          hill · camp)
                    |                        |
                THE TABLE                THE WINDOW
            (belief as miniatures,    (the world from the seat,
             uncertainty as finish)    period art, LOD by distance)
                     \                      /
                          THE DIVE
                  (table → window, only where known)
```

One simulation feeds two render surfaces; the Dive bridges them, gated by knowledge.

---

## 2 — The Table — the command surface

Present at every zoom, campaign and battle alike: your belief database rendered as a physical miniature world. It is the primary surface and ships **first**, because it is mostly typography, glyphs, and one animated rider — buildable now as the CLI's 2D graduation.

**Law — uncertainty as finish.** A rumored thing is a charcoal sketch; scouted is unpainted lead; confirmed is a painted miniature; intelligence going stale is dust gathering on the piece. The player learns to feel epistemic confidence as material finish — fog of war as craftsmanship.

```
The Table — Camp station                    day 14 · dawn · latency ~40 min
┌─────────────────────────────────────────┬──────────────────────┐
│ YOUR FIELD, AS YOU BELIEVE IT            │ FINISH = CERTAINTY    │
│                                          │   *  painted          │
│ *  Your vanguard        confirmed, here  │   ~  lead             │
│ ~  Enemy column, ridge  scouted 2h ago   │   ?  charcoal         │
│ ?  Horse, beyond wood   rumored          │   .  dust             │
│ .  Baggage train        stale, 6h unread │                       │
│                                          │ SPEND THE WAIT        │
│ ↗ Rider: "hold the ridge"  ~25 min out   │ [ Hold here ]         │
│                                          │ [ Ride to the hill ↗ ]│
└─────────────────────────────────────────┴──────────────────────┘
You see your information state, not the ground truth. The order is gone —
you cannot recall it; you choose only where to be when it lands.
```

**The order in flight (Addendum Y).** Issuing an order does *not* advance time — it queues a rider with his own travel latency. Advancing time is a separate act: **HOLD** at the current scene to let reports trickle in, or **MOVE** to a new station, which switches your vantage (and your belief DB) while time passes to cover the transit. Either way the order resolves on geography's clock, independent of how you spend the wait — and several orders can be in flight at once, each surfacing at its own arrival moment. You did not just issue an irrevocable order; you decided how to wait for it, and that is irrevocable too.

---

## 3 — The Window — the witness surface

Seat-locked 3D in the era's own visual language, opened only when you are somewhere — the Knot on its hill, the Front Rank's three meters, the Archive's earned free flight. It is the expensive surface and the one that recruits "let me just drive it" buyers, so it ships **second**, after the Table proves the loop.

**Law — no floating bars, ever.** A unit's state reads through banner behavior and posture, not a meter. Render fidelity mirrors the simulation tiers — full figures near the seat, instanced blocks in the middle distance, painted density for the far masses (the style, not a compromise — period battle art always handled crowds as pattern), and gold-leaf cloud for what you cannot see.

```
The Window — Hill station, locked seat                 render LOD by distance

   [ gold cloud over the unknown ]        ← fog = gold-leaf cloud bank
        [ far wing: painted density ]     ← far masses = stylized pattern
   [ mid: instanced block ]               ← middle distance = instanced crowd
   ▲ your guard: full figures, banner high ← near seat = full skeletal figures

   ▲ banner high = cohesion holds    ✕ no health bars    ⊘ seat is fixed
```

---

## 4 — The Dive — the binding grammar

Lean into the Table and the camera falls into the miniature — the painted piece blooming into the Window at that piece's vantage — *available only where your knowledge permits*. You can dive onto your own hill; you cannot dive into a charcoal sketch. The transition itself teaches the game's central law every time it plays, which is why it is also the trailer shot. Post-battle, the Archive unlocks the Window everywhere, with the two-layer truth as the scrub: the era's depiction (the tapestry's arrow) versus the trace (the sword, in the ditch, after the wall broke).

---

## 5 — Engine notes & build order

- **Headless core, engine as client.** The Rust/Python core owns the simulation and the trace; Unity or Unreal is a pure trace-playback client. The renderer never needs deterministic physics, so replays are free and the engine choice is a tooling preference, not a foundation bet.
- **The cost center is the art bible.** The NPR shader stack (ink, hatch, gouache, thread) is built once; each era's visual language needs an art director's year. One era ships first; the second exists to prove the pipeline general.
- **Table first, Window second.** The 2D Table is the CLI's natural graduation and carries the whole loop. The Window follows, gated by the spike below.
- **The spike before the scope.** Before any Window scoping, prove painterly NPR holds together under camera movement (the known hard problem) on a real Lattice trace. Hard-but-shipped, not open research — but it gates the budget.

**UI law throughout.** No floating bars; instruments are diegetic (the sun is the clock, the paper accumulating on the Table is the casualty report); confidence-as-finish replaces every minimap and intel overlay the genre has trained players to expect. Accessibility is built in, not bolted on: banner *shapes* carry faction identity redundantly with color, the truth-audio channel has a captioned sound-picture, and the text core makes screen-reader play achievable.

---

## 6 — The pitch, in one line

Kessen made a movie you could slightly control. This makes a primary source you can stand inside — diegetic miniature command over your beliefs, a seat-locked period-art window on the world, and the knowledge-gated dive between them.
