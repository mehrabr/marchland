# Ren'Py Debug Spec — MARCHLAND v0.1.0

Generated from: `renpy.sh --lint` + source audit + live run (SDK 8.5.3.26051504, macOS arm64)
Errors log prior to latest commit captured in `clients/renpy/errors.txt` and `traceback.txt`.

---

## How to use this spec

Each bug has:
- **Severity**: CRASH | LOGIC | ASSET | LINT
- **File + line**: exact location
- **Symptom**: what the player sees
- **Root cause**: why it happens
- **Fix**: the exact change to make
- **Test**: how to verify it's gone

Work top-to-bottom: CRASH bugs block all others from being testable.

---

## Bug 1 — CRASH: Spurious `}` in `the_table` string interpolation

**File:** [clients/renpy/game/marchland.rpy:234](clients/renpy/game/marchland.rpy#L234)

**Symptom:** Any time the `station_scene` label runs (i.e. after the quarter policy choice),
Ren'Py calls `the_table` screen. The screen crashes with:
```
ValueError: Single '}' encountered in format string
```
This crashes before the Table renders, blocking the entire turn loop.

**Root cause:** The format spec `:.0%}` mixes Python f-string syntax (`{x:.0%}`) with
Ren'Py interpolation syntax (`[x:.0%]`). The `}` after `%` is not valid inside Ren'Py's
`[...]` interpolation and is passed to Python's `format()` as part of the spec string,
which rejects it.

```rpy
## BROKEN — line 234
text "[entry['glyph']] [claim]: [entry['value']] ([entry['confidence']:.0%}])" style "table_entry"
```

**Fix:** Remove the spurious `}`:
```rpy
text "[entry['glyph']] [claim]: [entry['value']] ([entry['confidence']:.0%])" style "table_entry"
```

**Test:** Launch the full-season flow (`label start`), choose any quarter policy, confirm
the Table screen displays without an exception.

---

## Bug 2 — LOGIC: `SetVariable` with dotted attribute name ignores siege tactic choice

**File:** [clients/renpy/game/marchland.rpy:246-247](clients/renpy/game/marchland.rpy#L246)

**Symptom:** Player selects "Press for storm (costly)" in the siege tactic screen, but the
siege always runs as `tactic='wait'`. The storm threshold is never applied.

**Root cause:** Ren'Py's `SetVariable(name, value)` calls `setattr(renpy.store, name, value)`.
When `name = "capsule.siege_tactic"`, Python's `setattr` sets a literal attribute named
`"capsule.siege_tactic"` (a string with a dot) on the store object — it does **not** resolve
the dotted path to `renpy.store.capsule.siege_tactic`. The capsule's attribute remains `None`.

`commit_order("siege")` then reads `capsule.siege_tactic or 'wait'`, which is always `'wait'`.

```rpy
## BROKEN — lines 246-247
textbutton "Wait for terms (patient)" action [SetVariable("capsule.siege_tactic", "wait"), Return()]
textbutton "Press for storm (costly)"  action [SetVariable("capsule.siege_tactic", "storm"), Return()]
```

**Fix:** Use `Function(setattr, capsule, 'siege_tactic', value)` to set the attribute directly,
or restructure the screen to use a `python:` block via a `Use`-compatible pattern.
The simplest correct form uses `SetField`:

```rpy
textbutton "Wait for terms (patient)" action [SetField(capsule, "siege_tactic", "wait"), Return()]
textbutton "Press for storm (costly)"  action [SetField(capsule, "siege_tactic", "storm"), Return()]
```

(`SetField(obj, field_name, value)` is the Ren'Py action for `obj.field_name = value`.)

**Test:** Run the season flow, choose "Press for storm". Confirm `capsule.siege_tactic == 'storm'`
after the screen returns (add a temp `$ renpy.notify(capsule.siege_tactic)` to verify), and
that the siege runs with the storm threshold applied (faster resolution, higher attrition).

---

## Bug 3 — LOGIC: `SetVariable` ignores march pace choice

**File:** [clients/renpy/game/marchland.rpy:258-260](clients/renpy/game/marchland.rpy#L258)

**Symptom:** All three pace buttons ("Normal", "Push hard", "Rest every 4 days") produce
identical march outcomes. `capsule.march_pace` is always `None`; march runs at default pace.

**Root cause:** Same as Bug 2 — `SetVariable("capsule.march_pace", ...)` does not set
the attribute on the capsule object.

```rpy
## BROKEN — lines 258-260
textbutton "Normal pace"               action [SetVariable("capsule.march_pace", "normal"), Return()]
textbutton "Push hard (more attrition)" action [SetVariable("capsule.march_pace", "push"),   Return()]
textbutton "Rest every 4 days"         action [SetVariable("capsule.march_pace", "rest"),   Return()]
```

**Fix:**
```rpy
textbutton "Normal pace"               action [SetField(capsule, "march_pace", "normal"), Return()]
textbutton "Push hard (more attrition)" action [SetField(capsule, "march_pace", "push"),   Return()]
textbutton "Rest every 4 days"         action [SetField(capsule, "march_pace", "rest"),   Return()]
```

**Test:** Choose "Push hard". Confirm `capsule.march_result` shows higher `fat0` or attrition
than a "Normal pace" run at the same seed.

---

## Bug 4 — LOGIC: `SetVariable` ignores battle choice

**File:** [clients/renpy/game/marchland.rpy:271-272](clients/renpy/game/marchland.rpy#L271)

**Symptom:** Choosing "Withdraw" has no effect — the battle always runs as `battle_choice='engage'`
and a full engagement is simulated. The withdraw path (`run_operation` early-return with
`withdrew=True`) is never reached.

**Root cause:** Same as Bugs 2 and 3.

```rpy
## BROKEN — lines 271-272
textbutton "Engage"    action [SetVariable("capsule.battle_choice", "engage"),   Return()]
textbutton "Withdraw"  action [SetVariable("capsule.battle_choice", "withdraw"), Return()]
```

**Fix:**
```rpy
textbutton "Engage"    action [SetField(capsule, "battle_choice", "engage"),   Return()]
textbutton "Withdraw"  action [SetField(capsule, "battle_choice", "withdraw"), Return()]
```

**Test:** Choose "Withdraw". Confirm `capsule.battle_result.get('withdrew') == True` and
the winter court scene runs without a full engagement in the trace.

---

## Bug 5 — ASSET: `bg_camp` image not defined

**File:** [clients/renpy/game/marchland.rpy:29](clients/renpy/game/marchland.rpy#L29)

**Symptom:** In development mode, the scene background is gray/magenta placeholder.
In a release build without developer mode, Ren'Py will log an error; the scene shows black.

**Root cause:** `scene bg_camp` references an image tag `bg_camp` with no corresponding
image definition, file, or `image` statement anywhere in the project.

**Fix (minimal — placeholder):** Add a solid-color image definition:
```rpy
## In marchland.rpy or a new images.rpy
image bg_camp = Solid("#1a1a2e")
image bg_court = Solid("#2e1a1a")
```

**Fix (proper):** Add background art files `game/images/bg_camp.png` and `game/images/bg_court.png`
and let Ren'Py's auto-image system find them.

**Test:** `renpy.sh clients/renpy --lint` should no longer report `'bg_camp' is not an image`.

---

## Bug 6 — ASSET: `bg_court` image not defined

**File:** [clients/renpy/game/marchland.rpy:207](clients/renpy/game/marchland.rpy#L207)

Same as Bug 5 but for the winter court scene. Fix and test identically.

---

## Bug 7 — ASSET: `bg_hill` image not defined

**File:** [clients/renpy/game/slice.rpy:48](clients/renpy/game/slice.rpy#L48)

**Symptom:** The slice opens with a gray/magenta background instead of the hill scene.

**Root cause:** `scene bg_hill` references an undefined image.

**Fix (minimal):**
```rpy
## In slice.rpy or a new images.rpy
image bg_hill = Solid("#2e3a2e")
```

**Test:** `renpy.sh clients/renpy --lint` no longer reports `'bg_hill' is not an image`.
Opening the slice shows a colored background, not a Ren'Py error placeholder.

---

## Bug 8 — ASSET: `captain neutral` sprite not defined

**File:** [clients/renpy/game/slice.rpy:57](clients/renpy/game/slice.rpy#L57)

**Symptom:** `show captain neutral at left` shows a Ren'Py "missing image" placeholder
(or nothing). The officer contact report lacks any visual presence.

**Root cause:** No `image captain neutral` definition and no `game/images/captain/neutral.png`
file exists. Ren'Py requires either a file on disk or an explicit `image` statement.

**Fix (minimal):**
```rpy
image captain neutral = Solid("#444444", xsize=120, ysize=300)
```

**Fix (proper):** Add `game/images/captain/neutral.png` with a portrait sprite.

**Test:** `renpy.sh clients/renpy --lint` no longer reports `'captain neutral' is not an image`.
Running the slice shows a visible placeholder or sprite at the officer contact report beat.

---

## Bug 9 — LINT: Screens missing `()` parameter list

**File:** [clients/renpy/game/marchland.rpy:238, 250, 263, 299](clients/renpy/game/marchland.rpy#L238)

**Symptom:** `renpy.sh --lint` warns:
```
The screen tactic_menu has not been given a parameter list.
This can be fixed by writing 'screen tactic_menu():' instead.
```
(Same for `pace_menu`, `battle_menu`, `hud_dismiss`.)

**Root cause:** Ren'Py 8.5.3 lint enforces explicit `()` on screens with no parameters.
No runtime effect; these are style/lint failures only.

**Fix:** Add `()` to all four screen headers:
```rpy
screen tactic_menu():
screen pace_menu():
screen battle_menu():
screen hud_dismiss():
```

**Test:** `renpy.sh clients/renpy --lint` produces zero parameter-list warnings.

---

## Summary table

| # | Severity | File | Line(s) | One-line description |
|---|----------|------|---------|----------------------|
| 1 | CRASH | marchland.rpy | 234 | `:.0%}` → `:.0%]` in table interpolation |
| 2 | LOGIC | marchland.rpy | 246–247 | `SetVariable` can't set capsule attrs; tactic lost |
| 3 | LOGIC | marchland.rpy | 258–260 | Same — march pace choice always ignored |
| 4 | LOGIC | marchland.rpy | 271–272 | Same — battle/withdraw choice always ignored |
| 5 | ASSET | marchland.rpy | 29 | `bg_camp` undefined |
| 6 | ASSET | marchland.rpy | 207 | `bg_court` undefined |
| 7 | ASSET | slice.rpy | 48 | `bg_hill` undefined |
| 8 | ASSET | slice.rpy | 57 | `captain neutral` undefined |
| 9 | LINT | marchland.rpy | 238,250,263,299 | Screens missing `()` parameter list |

**Fix order:** 1 (unblocks all testing) → 2–4 (logic, test with same seed) → 5–8 (asset stubs) → 9 (lint clean)

---

## Previously fixed (do not re-open)

These appeared in `clients/renpy/errors.txt` / `traceback.txt` (captured before commit `a8bc92a`)
and are now resolved:

| Fixed in | What | Where |
|----------|------|-------|
| `a8bc92a` | Menu choices missing trailing `:` before python blocks | `slice.rpy:66,70,74,97,101` |
| `a8bc92a` | `build.Package(...)` → removed; replaced with `build.classify(...)` | `options.rpy:35` |
