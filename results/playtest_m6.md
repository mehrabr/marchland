# Playtest Report — M6 Tutorial Gate

**Milestone:** M6 — Playtest Gate  
**Scenario:** `python -m clients.cli tutorial` — escort of Sir William Brandon, autumn 1415  
**Tester profiles:** Kriegsspieler, Student  
**Date completed:** 2026-06-18  

---

## What Was Tested

The tutorial runs: covenant → annotated muster → quarter policy decision → march pace decision → patrol encounter (engage or evade) → winter court with explicit explanation.

Two profiles ran through the tutorial independently:

- **Kriegsspieler**: knows medieval warfare and logistics; tests plausibility of mechanics
- **Student**: new to the game; tests whether receipts are legible and decisions feel meaningful

---

## Profile 1: Kriegsspieler

### Run: normal pace, engage, accurate dispatches

**Muster screen:** Receipt notes on armor, belief, and volley discipline were read and found plausible. The parenthetical format (`armor=0.80 → P(casualty | opening) ≈ 27% vs 45% unarmored`) is the right level of detail — not a formula dump, not a vague label.

**Quarter policy:** The distinction between `strict` / `liberal` / `free_rein` and their patron-favor modifiers is historically legible. The custom of the age framing holds.

**March pace:** The `push` pace modifier (+20% miles/day, +5% fat0) was found mechanically plausible but the explanation in the tutorial lacked a concrete "why" — specifically, the connection between fatigue and the opening hazard amplifier (`fat_amp=2.0`) should be stated. **Finding [W-1].**

**Engagement:** The displayed death counts are at the 1 agent ≈ 10 men scale (~2000 English vs ~1500 French). The Kriegsspieler noted this is not really a "small skirmish" — it is a moderately-sized road engagement. The framing as "patrol" is a slight mismatch with the displayed numbers.

**Winter court:** The explicit WHY explanation (`[WHY patron credits success: dispatch carried 'arrived=True'; escort objective_predicate = ...]`) was positively received. No ambiguity about why the patron was pleased.

**Overall:** Reached winter court in approximately 12 minutes (command entry included). The 20-minute goal is comfortably met.

**Kriegsspieler verdict:** Plausible. The receipt explanations are correct and the chain (march fatigue → battle opening hazard) is legible to someone who knows the underlying model.

---

## Profile 2: Student

### Run: normal pace, evade, liberal policy

**Covenant screen:** "You command; you do not pilot." landed well. The bullets ("You cannot undo a decision once the rider departs") were legible without prior game knowledge.

**Muster screen:** The parenthetical receipt notes were helpful but dense. A student reading `err=0.85 (E) → disciplined volley; err is spread not accuracy` without prior context may not grasp "spread not accuracy." The note is technically correct but the implication (higher err = worse? better?) requires a follow-on sentence. **Finding [W-2].**

**Quarter policy:** The three choices with their favor modifiers were clear. The Student chose `liberal` without prompting. The note printed after the choice (`Controlled contribution; the custom of the age.`) confirmed the decision.

**March decision:** "push / rest / normal" was clear. The Student chose `rest` expecting explicitly gentler treatment. The rest pace produced slightly lower fatigue and a longer march. The explanation of *why* (`rest day every 3rd; men arrive fresher, takes longer`) was adequate.

**Evade path:** The evade mechanic worked correctly (1 extra day). The WHY note `[WHY no battle entry: evading means no trace battle phase...]` was too technical for a Student player — it's useful for the Kriegsspieler but may confuse a newcomer. **Finding [W-3].**

**Winter court:** The explicit patronal assessment was the strongest element for the Student profile. The favor calculation printed inline (`base 0.55 + mission credit (+0.15) + quarter 0.00 = 0.70`) gave the Student a clear causal account of the outcome.

**Student verdict:** Reached the winter court in approximately 14 minutes. No blocking confusion. One point of unclear language (W-2).

---

## Findings

### Blocking issues (none)

No blocking issue was encountered on either profile. Both runs completed muster → operations → winter court without ambiguity about what command to type next.

### Warnings (non-blocking, logged to open ledger)

**[W-1] March fatigue → battle opening hazard not explained in tutorial.**  
The tutorial says "push pace = men arrive tired" but does not cite the `fat_amp=2.0` amplifier that makes this mechanically consequential. A one-line addition in `_do_march()` would close this: "fatigue amplifies the opening hazard (fat_amp=2.0)".  
*Status: documented; fix trivial; not blocking.*

**[W-2] Volley `err` note is ambiguous for new players.**  
`err=0.85 → disciplined volley; err is spread not accuracy` needs a second sentence: "higher err means tighter volley spread around the target row." Without this, a student might infer that `err=1.0` is "perfect."  
*Status: documented; fix trivial; not blocking.*

**[W-3] WHY notes in the evade path are too technical for the Student profile.**  
The `[WHY no battle entry: evading means no trace battle phase; the escort mission predicate checks only 'march arrived' when no battle exists]` note explains the mission predicate correctly but uses terminology the Student has not yet encountered (trace, battle phase, predicate). Consider gating this text behind a `help trace` call rather than printing it inline.  
*Status: documented; consider moving to help text.*

**[W-4] Tutorial skirmish is not truly small.**  
The engagement scenario (200 English agents × 10 = ~2000 men vs 150 French × 10 = ~1500 men) is described in the tutorial as a "blocking force" but is materially larger than the "one small engagement" in the M6 spec. This is a consequence of the BP-Lattice engine requiring a minimum viable agent count (~100+ per side) for rout dynamics to fire. Smaller forces produce win=-1 (no break) because density effects cannot accumulate.  
*Root cause:* The engine is calibrated for engagements of hundreds to thousands of agents (historical battles). A true "skirmish" of 30 vs 15 agents would require separate small-engagement mechanics.  
*Status: logged to open ledger. Not a tutorial blocker — the engagement resolves decisively and the receipts lesson is intact. Post-M6.*

---

## Open Ledger Additions

These findings are added to the open ledger, not silently tuned away:

| Issue | Root Cause | Priority |
|-------|------------|----------|
| Tutorial skirmish agent scale (W-4) | BP-Lattice calibrated for large forces; small-engagement regime not implemented | post-M6 |
| March fatigue WHY note missing (W-1) | Tutorial text omits fat_amp citation | trivial, any PR |
| Volley err note ambiguous (W-2) | "spread not accuracy" needs a positive example | trivial, any PR |
| Evade WHY note too technical (W-3) | Technical trace terminology in a student-facing note | low, post-M6 |

---

## M6 Acceptance Criteria — Result

| Criterion | Result |
|-----------|--------|
| Kriegsspieler reaches winter court in one session | PASS (~12 min) |
| Student reaches winter court in under 20 minutes | PASS (~14 min) |
| All receipts explained at muster | PASS (parenthetical notes on every cohort) |
| Covenant printed at game start | PASS (`print_covenant` called before muster) |
| "You command; you do not pilot." present in covenant | PASS (exact phrase) |
| Help system available at any prompt | PASS (`help <topic>` in tutorial loop and season loop) |
| Winter court explains WHY patron is pleased/displeased | PASS (explicit WHY blocks in `_print_winter_court`) |
| No quality coefficient in tutorial culture file | PASS (receipts-grep clean) |
| Battery CI green | PASS (10/10 grade-A targets) |
| No blocking confusion on either profile | PASS |

---

## Next Steps

Known issues W-1, W-2, W-3 are trivial text fixes. W-4 (small-engagement regime) is a post-M6 design task. None block shipping the tutorial.
