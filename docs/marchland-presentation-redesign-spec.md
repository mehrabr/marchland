# MARCHLAND — Spec: Strip the Scientism (Presentation Redesign)
### Hide the engine's numbers behind a human, historically-accurate surface — without losing the transparency that proves the dice aren't loaded

**Origin.** The panel played the tutorial and the 1415 chain through the CLI and reached unanimous judgment: the *scientism is a presentation bug, not a design feature*. The game shows the player its own source constants — `armor=0.80 (B) → P(casualty | opening) ≈ 27%`, `[BP-Lattice runs: ... 200 agents]`, `(trace: NEGOTIATED@day37)`, `[WHY ...]` brackets. The information is correct; the *register* is a debug overlay. This spec fixes it.

**The non-negotiable constraint (Marcus's covenant point).** The covenant screen *promises* "this game will always explain every number when you ask." That inspectability is **load-bearing for the anti-essentialism thesis** — the receipts being auditable is *how the game proves it isn't loading the dice per-people*. So the rule is not "delete the numbers." It is: **the numbers live behind a door, not on the wall.** Default presentation is human and historical; an inspect command pulls the curtain for the player who wants to audit. Strip them from the narration; keep them reachable.

---

## 1 — The architectural fix (Priya's clean line)

The CLI currently builds strings by **concatenating raw trace events into prose**:

```python
# tools/chronicle.py, current — the citation is built INTO the sentence:
f"...the garrison struck terms (trace: {outcome_name}@day{day})."
```

This is the whole bug in one line. The trace is *already* the structured data (timestamps, causes, counts). The fix is two render paths off the same trace, never concatenated:

```
                          ┌─→  NARRATION path  →  prose, a vantage, NO numbers
   one trace (the truth) ─┤        (answers: "what happened?")
                          └─→  INSPECTION path  →  receipts, certificates, figures, ON DEMAND
                                   (answers: "prove it / explain it")
```

`tools/chronicle.py` stops appending `(trace: ...)` and instead returns prose with the citing event held in a *parallel structure* the inspector can surface — `explain` on any chronicle line shows the grounding event; the line itself never displays it. The `[WHY ...]` and `[BP-Lattice runs: ...]` brackets are developer scaffolding that **should never have reached the player surface** — deleted outright from narration, their content moved behind `explain`/`inspect`.

This is *deletion and gating*, not new simulation work. The sim is untouched; the trace is untouched; only the render layer changes.

---

## 2 — Four leaks, with before/after

### 2a. The muster receipts — a spreadsheet on the wall
```
BEFORE (current tutorial.py):
  Men-at-arms (200 men)
    Equipment: partial harness (armor=0.80)
      · armor=0.80 (B) → P(casualty | opening) ≈ 27% vs 45% unarmored
      · belief=0.80 (C) → men hold unless 3 of 5 appraisal cues fire
      · hold=1 (D) → cohort stands ground; does not advance into pursuit

AFTER (default — a captain's eye):
  Two hundred men-at-arms, well-harnessed — they'll take a blow that
  would fell a lighter man, and they'll hold their ground rather than
  break ranks to chase a beaten foe.

  (type 'inspect men-at-arms' to see what makes them so)

AFTER (inspect men-at-arms — the door opened):
  Men-at-arms · 200
    armor 0.80   — partial harness; ~27% casualty per opening vs 45% bare   [B: equipment]
    belief 0.80  — hold unless 3 of 5 appraisal cues fire                    [C: campaign]
    hold         — stand ground; do not pursue                              [D: institution]
    Every figure here is a receipt — a changeable in-world fact. Nothing
    differs between forces without one. This is how you check the dice.
```

### 2b. The `[WHY ...]` / `[BP-Lattice runs: ...]` brackets — developer scaffolding
```
BEFORE:
  [BP-Lattice runs: English (~2000 men, 200 agents) vs French (~1500, 150 agents)]
  [Archers fire volleys at ADVANCE phase; melee fires at CONTACT]
  Outcome: English prevail
  [WHY English prevailed: archers degraded French belief before contact;
   the patrol broke when rout appraisal cues exceeded their threshold]

AFTER (default):
  The French column held the road. Your archers loosed from both flanks
  as they closed, and the patrol — galled by the arrow-storm before they
  could come to grips — broke and ran.

  (type 'explain' to see why it went as it did)
```
The agent count, the phase labels, the cue-threshold mechanics — all moved behind `explain`. The player in the tent never learns there are "200 agents."

### 2c. The option menus — leaking in the input direction (Sam's catch)
```
BEFORE:
  strict     → patron pleased; men grumble (patron favor +0.10)
  liberal    → the custom of the age; balanced (no modifier)
  free_rein  → men happy; patron will hear of it (patron favor -0.15)

AFTER:
  strict     The men will grumble at the tight rein — but your patron
             will hear you kept good order, and think the better of you.
  liberal    The custom of the age. Contribution taken, not plundered.
  free_rein  The men will love you for it. Your patron will not.
```
The consequence is stated *in the world*; the `+0.10` lives behind the inspector. Numbers on choices break immersion exactly as numbers on outcomes do.

### 2d. The winter court favor arithmetic
```
BEFORE:
  [Favor calculation: base 0.55 + mission credit (+0.15) + quarter +0.00 = 0.70]
  Season result: patron favor 70%

AFTER (default):
  Lord Camoys is pleased. The escort came through, the road was cleared,
  and nothing in your conduct gave him cause to grumble. You stand higher
  in his regard than when the season began.

AFTER (inspect favor):
  0.55 start → +0.15 mission credit → +0.00 quarter → 0.70   [tap any to explain]
```

---

## 3 — The chronicle narrator (the historians' deeper fix)

De-numbering is necessary but not sufficient. Two narrator-level faults the historians flagged:

**Wrong narrator (Sarris).** The current chronicle narrates from the *trace's* omniscient, neutral, timestamped voice — "Side-1 broke at 2164s." But the design's own law is that the chronicle is *written from a vantage with sympathies* (it lies like sources do). The trace is the source material; the chronicle is **written from it**, not **read out of it**. "Side-1" and seconds-timestamps must never appear — the narrator is a person who saw the day from somewhere and was on a side.

**Magnitude must survive (Sarris's caution).** The risk in de-numbering is *over-smoothing* — if every outcome becomes elegant prose, the player loses the visceral "970 French to 390?!" shock that teaches the asymmetry. The prose must therefore still convey *magnitude and shock* in period register: "the dead lay thick," "the better part of a thousand," "far more of theirs than of ours."

**Before / after, the seed-0 chronicle:**

```
BEFORE (current 1415 chronicle output):
  The siege ran 37 days before the garrison struck terms (trace:
  NEGOTIATED@day37). Terms were struck on day 29; the relief window
  expired before relief arrived (trace: terms_struck@day29). Disease in
  the besieger's camp felled 636 men (trace: 37 disease events, total=636).
  [...]
  Arrow volleys accounted for 690 dead (trace: 69 death-certs, cause=volley).
  The opposing cavalry met the stake-line at 78s (trace: horse_balk@78s).
  Melee contact killed 1840 (trace: 184 death-certs, cause=melee/cavalry).
  Pursuit accounted for 40 more (trace: 4 death-certs, cause=pursuit).
  Side-1 broke at 2164s (trace: side1_broke@2164s).
```
```
AFTER (written from the same trace, a vantage voice, magnitude kept):
  Five weeks the town held, until the garrison — sick of waiting on a
  relief that never came — sent out to ask for terms, and on the
  thirty-seventh day the gates were opened. The siege had cost the King's
  army dearly without a blow struck in anger: the bloody flux ran through
  the wet camps and carried off the better part of a thousand men.

  The march that followed was a hard one. Sixteen days the host went, near
  to two hundred and seventy miles, for the fords on the Somme were held
  against them and they were driven far upriver to find a crossing. They
  came to the field footsore and hungry, though disease spared them on the
  road as it had not in the camp.

  Then the arrows did their work — the French came on, and the bowmen
  emptied their sheaves into them, and many fell before ever a sword was
  drawn. The enemy horse came against the stakes and would not face them,
  and shied away. When the lines met, the slaughter was very great, and at
  the last, near the day's end, the French broke and our men pursued them.
  The dead lay thick upon the ground, and far more of theirs than of ours.
```

Every fact in the "after" still traces to an event — the terms on day 37, the disease deaths, the Somme detour, the volleys, the horse balking at the stakes, the late break, the lopsided dead. **The grounding rule is unchanged; only the narrator changed.** `explain` on any sentence still surfaces its event for the auditor. The chronicle is now a *source* — which is what the project always said it was.

---

## 4 — The inspection surface (keeping the door — Marcus + Olleus)

The transparency moves behind three verbs, reachable at any prompt:

```
inspect <thing>   the receipts behind a cohort, a choice, a favor score —
                  the figures, each tagged with its class [B/C/D/E] and what changes it
explain           why the last outcome went as it did — the mechanics,
                  the cues that fired, the phase structure (the old [WHY] content)
help receipts     the standing doctrine: what a receipt is, why no number
                  differs without one, that this is how you check the dice
```

**Unresolved between Marcus and Olleus (preserve):** how *prominent* the inspector is. Marcus wants the numbers *derivable* for epistemic honesty (three menus deep is fine if reachable); Olleus wants them *one keystroke away and comprehensive* for grognard pleasure. Both agree they are **out of the narration**. Recommended resolution: a single global toggle — `ledger on` makes the inspector verbose and inline-adjacent (Olleus's mode); default is `ledger off`, human narration with `inspect`/`explain` available but never volunteered (Marcus's mode). One switch serves both without compromising either, and the default protects the new player.

---

## 5 — The implementation checklist (deletion and gating, not new sim)

```
tools/chronicle.py    stop concatenating "(trace: ...)"; return (prose, citing_event)
                      pairs; rewrite phrase templates into vantage voice with a
                      'side' and sympathies; keep magnitude language; the grounding
                      rule (every sentence → an event) is UNCHANGED
clients/cli/tutorial.py   muster receipts → captain's-eye prose + 'inspect <cohort>';
                          DELETE all [WHY ...] and [BP-Lattice ...] brackets from the
                          player surface; option menus → worldly consequences;
                          favor arithmetic → court prose + 'inspect favor'
clients/cli/season.py     same treatment as tutorial.py for the full season
clients/cli/         add inspect / explain commands + 'ledger on|off' toggle (default off)
clients/cli/help.py       'help receipts' already exists — keep; it is the doctrine door
core/, battery/, trace    UNTOUCHED — the sim, the receipts, the trace, the audit all
                          stay exactly as they are; this is a render-layer change only
tests/test_chronicle_ux.py   update: assert the narration contains NO 'trace:', no
                              'side-1', no bare 's' timestamps, no '→', no class tags;
                              assert 'explain' still surfaces the grounding event;
                              assert magnitude words survive (a lopsided result still
                              reads as lopsided in prose)
```

---

**Verdict.** The scientism is a render-layer leak: the engine showing its work to a player who didn't ask. The fix is two paths off the one trace — human narration by default, full inspection on demand — which strips `armor=0.80`, `[BP-Lattice runs]`, `(trace: ...)`, `[WHY]`, and the favor arithmetic from the surface while keeping every number reachable behind `inspect`/`explain`, because that reachability is how the game proves it never loads the dice. The chronicle is re-narrated from a vantage with sympathies, in period voice, with magnitude preserved so the historical lesson still lands — making it at last the *source* the project always claimed it was. No simulation, trace, or battery code changes; this is entirely the presentation surface. **The game stops explaining itself like a paper and starts speaking like a war.**
