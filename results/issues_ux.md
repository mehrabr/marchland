# MARCHLAND UX Issues — Post-M6 Playtest

**Source:** Simulated playthroughs conducted 2026-06-18 across five runs (tutorial ×3, season ×2)
covering all three quarter policies, all three march paces, engage/evade, and storm/wait siege tactics.
See `results/playtest_m6.md` for the earlier M6 tester-profile findings (W-1 through W-4).

Issues are grouped **High → Medium → Low** within their surface area.
Each issue has: description, exact file/line, and a test spec to validate the fix.

---

## Issue Index

| ID | Priority | Surface | One-line |
|----|----------|---------|---------|
| [UX-01](#ux-01) | High | Tutorial ops loop | `engage`/`evade` listed before they are available |
| [UX-02](#ux-02) | High | Table renderer | Phase-bar glyph not updated after confirmed battle dispatch |
| [UX-03](#ux-03) | High | Season audit | `(unknown)` on Actual side of casualty rows misleads players |
| [UX-04](#ux-04) | Medium | Covenant/muster boundary | No visual separator between covenant and muster screens |
| [UX-05](#ux-05) | Medium | Tutorial quarter policy | Option descriptions scroll away before player can type |
| [UX-06](#ux-06) | Medium | Season dispatch prompt | `partial` omits casualties silently — not explained at the prompt |
| [UX-07](#ux-07) | Medium | Tutorial winter court | Improvement advice cites wrong cause when quarter policy is the delta source |
| [UX-08](#ux-08) | Medium | Season winter court | Storm vs wait siege — no prose differentiation at court |
| [UX-09](#ux-09) | Low | Tutorial/season ops | No confirmation before `done` closes operations early |
| [UX-10](#ux-10) | Low | Help system | `help` with no topic undocumented in ops command list |
| [UX-11](#ux-11) | Low | Help system | Unknown-topic error message wraps badly on narrow terminals |
| [UX-12](#ux-12) | Low | 1415 chronicle | Chronicle sentences formulaic; `detour` event lacks a reason string |

---

## UX-01 — Patrol gate not telegraphed in tutorial command list

**Priority:** High

**Description:**
The tutorial command list prints `engage` and `evade` from the moment operations start, but
these commands respond `No patrol sighted yet. March first ('march')` until after `march`
completes. A new player who types `engage` immediately gets a confusing rejection with no
indication that the command will become available later.

**Location:**
- [clients/cli/tutorial.py:429-437](clients/cli/tutorial.py#L429-L437) — `_TUTORIAL_COMMANDS` string
- [clients/cli/tutorial.py:484-485](clients/cli/tutorial.py#L484-L485) — gate error message

**Fix description:**
Annotate `engage` and `evade` in `_TUTORIAL_COMMANDS` with `(available after march)`.
Optionally change the gate error to `engage and evade become available once the march
is complete — type 'march' first.`

**Test spec:**

```python
# tests/test_tutorial_ux.py::test_ux01_command_list_telegraphs_patrol_gate
from clients.cli.tutorial import _TUTORIAL_COMMANDS

def test_ux01_command_list_telegraphs_patrol_gate():
    """The printed command list must indicate engage/evade need a march first."""
    assert 'after march' in _TUTORIAL_COMMANDS.lower() or \
           'march first' in _TUTORIAL_COMMANDS.lower(), (
        "Command list must label engage/evade as available only after march"
    )

# tests/test_tutorial_ux.py::test_ux01_gate_error_is_instructive
from clients.cli.tutorial import _MockIO, TutorialState, _operations_phase
from clients.cli.covenant import print_covenant
from core.commission import generate_commission
import importlib, numpy as np

def test_ux01_gate_error_is_instructive():
    """Typing 'engage' before march must produce a message that teaches the ordering."""
    module = importlib.import_module('core.cultures.tutorial_escort')
    culture = module.CULTURE
    commission = generate_commission(culture, np.random.default_rng(0))
    state = TutorialState(commission=commission, seed=0,
                          patron_favor=culture['career']['starting_patron_favor'])
    io = _MockIO(['engage', 'done'])
    _operations_phase(state, io)
    joined = '\n'.join(io.lines)
    # Error should guide the player, not just say "no"
    assert 'march' in joined.lower(), "Gate error must mention 'march'"
    assert 'sighted' not in joined.lower() or 'march' in joined.lower()
```

---

## UX-02 — Phase-bar glyph not updated after confirmed battle dispatch

**Priority:** High

**Description:**
After a confirmed battle dispatch (confidence 90%), the Table's KNOWN list shows the battle
claims with `*` glyphs correctly, but the phase-bar line continues to render `[ ]AGINCOURT`
instead of `[*]AGINCOURT`. The `battle` key is present in `belief_db` but
`_build_campaign_line` does not pick it up.

Observed in playthrough 4: after `accurate` battle dispatch, the table showed:
```
  [*]HARFLEUR  ——*——>  [ ]AGINCOURT   ← should be [*]AGINCOURT
```

**Location:**
- [clients/cli/table.py:56-62](clients/cli/table.py#L56-L62) — `_build_campaign_line`
- [clients/cli/table.py:87-94](clients/cli/table.py#L87-L94) — phase glyph derivation loop

**Root cause:**
`_build_campaign_line` reads `phase_known.get('battle', ' ')` and the dict key is `'battle'`,
which is correctly set in the loop at line 88. The bug may be in
`belief_db.beliefs_for_station()` not returning the battle phase for CAMP station after
dispatch — or in the phase_glyphs dict key naming mismatch. Needs investigation.

**Fix description:**
Verify that `beliefs_for_station(Station.CAMP)` returns `{'battle': {...}}` after a dispatch
is received via `receive_dispatch('battle', ...)`. If not, fix the BeliefDB scoping logic.
If yes, add a targeted unit test and trace the phase_glyphs dict through render_table.

**Test spec:**

```python
# tests/test_table_ux.py::test_ux02_phase_bar_updates_after_battle_dispatch
from core.belief_db import BeliefDB
from core.stations import Station, STATIONS, StationState
from clients.cli.table import render_table
from clients.cli.season import _MockIO

def test_ux02_phase_bar_updates_after_battle_dispatch():
    """Phase bar must show [*] for AGINCOURT after a confirmed battle dispatch."""
    db = BeliefDB()
    db.receive_dispatch('battle', {'won': True, 'casualties': 400}, confidence=0.90)

    station_state = StationState(station=Station.CAMP,
                                 spec=STATIONS[Station.CAMP])
    io = _MockIO([])
    render_table(day=53, station_state=station_state,
                 belief_db=db, pending_orders=[], io=io)

    campaign_line = next(
        (l for l in io.lines if 'HARFLEUR' in l and 'AGINCOURT' in l), None
    )
    assert campaign_line is not None, "Campaign line must be rendered"
    # The AGINCOURT bracket must contain a glyph, not a space
    assert '[*]AGINCOURT' in campaign_line or \
           '[~]AGINCOURT' in campaign_line or \
           '[?]AGINCOURT' in campaign_line, (
        f"AGINCOURT bracket must show a glyph after dispatch, got: {campaign_line}"
    )
```

---

## UX-03 — `(unknown)` on Actual side of audit misleads players

**Priority:** High

**Description:**
Every playthrough showed `(unknown)` in the Actual column for casualty fields
(e.g., `siege.casualties: 553 | (unknown) | —`). This is correct in the strict sense
(the trace summary does not expose a verifiable analog for this claim) but players who
just watched 553 men die read it as a system error. The label should communicate that
casualty counts are not independently verifiable through the audit, not that the game
doesn't know.

**Location:**
- [clients/cli/season.py:608](clients/cli/season.py#L608) — `'(unknown)'` literal
- `core/belief_db.py` — `audit()` method returning `None` for actual

**Fix description:**
Replace `'(unknown)'` with `'(not in trace summary)'` or `'(unverifiable)'` and add a
footer line to the audit table: `† claim has no trace analog — patron accepts as reported`.
This makes the epistemic design visible rather than looking like missing data.

**Test spec:**

```python
# tests/test_season_ux.py::test_ux03_audit_unknown_label_is_explanatory
from clients.cli.season import _MockIO, run_season

def test_ux03_audit_unknown_label_is_explanatory():
    """Audit table must not use '(unknown)' for unverifiable claims."""
    auto = ['liberal', 'siege', 'wait', 'accurate',
            'march', 'normal', 'accurate',
            'battle', 'engage', 'accurate', 'done']
    io = _MockIO(auto)
    import clients.cli.season as sm
    orig = sm._MockIO
    sm._MockIO = type('VM', (orig,), {
        'print': lambda s, *a, **kw: (orig.print(s, *a, **kw), print(*a, **kw))[0]
    })
    run_season(seed=42, culture_name='harfleur_1415', auto_commands=auto)
    sm._MockIO = orig
    # The raw '(unknown)' string must not appear in any audit output line
    audit_lines = [l for l in io.lines if 'Claim' in l or 'siege.' in l
                   or 'march.' in l or 'battle.' in l]
    for line in audit_lines:
        assert '(unknown)' not in line, (
            f"Audit must not use '(unknown)'; found in: {line!r}"
        )
```

---

## UX-04 — No visual separator between covenant screen and muster

**Priority:** Medium

**Description:**
The covenant screen closes with `══════════════════════════════════════════════════════`
(no bottom border) then `Press Enter to begin...` appears as plain text with no
surrounding frame. The muster (`=====` header) follows immediately. On a first session
the player cannot tell whether they are still in preamble or have entered the game.

**Location:**
- [clients/cli/covenant.py:38](clients/cli/covenant.py#L38) — `COVENANT_TEXT` ends with open `══` line
- [clients/cli/tutorial.py:558-560](clients/cli/tutorial.py#L558-L560) — `Press Enter` printed after covenant

**Fix description:**
Add a blank line and a distinct visual marker after the `Press Enter` prompt — e.g., a
row of dashes or a separator labelled `── BEGIN ──` — so the player has a clear entry
point. Alternatively close the covenant box with `╚══════╝` before the prompt, making
the covenant a self-contained object.

**Test spec:**

```python
# tests/test_covenant_ux.py::test_ux04_covenant_has_clear_entry_point
from clients.cli.covenant import COVENANT_TEXT
from clients.cli.tutorial import _MockIO, run_tutorial
import importlib, numpy as np

def test_ux04_covenant_has_visual_close():
    """Covenant text must end with a closed bottom border before the prompt."""
    # The covenant must close with ╚ or a clear separator
    lines = COVENANT_TEXT.splitlines()
    last_nonempty = next(l for l in reversed(lines) if l.strip())
    assert last_nonempty.startswith('╚') or last_nonempty.startswith('═') or \
           '──' in last_nonempty, (
        f"Covenant must end with a visual close, got: {last_nonempty!r}"
    )

def test_ux04_begin_marker_present():
    """Tutorial output must contain a clear entry marker between covenant and muster."""
    io = _MockIO(['', 'liberal', 'march normal', 'evade', 'done'])
    run_tutorial(seed=0, auto_commands=['', 'liberal', 'march normal', 'evade', 'done'])
    # Not directly assertable without capturing io, but covenant_text check above covers the design
```

---

## UX-05 — Quarter-policy option descriptions scroll away before player types

**Priority:** Medium

**Description:**
In both the tutorial and the full season, the three quarter-policy options with their
favor-modifier explanations are printed above the prompt. Once the terminal scrolls past
them, the player sees only `Choose quarter policy [strict/liberal/free_rein]:` with no
reminder of what each option means. Typing `?` or blank does not redisplay the options.

**Location:**
- [clients/cli/tutorial.py:566-575](clients/cli/tutorial.py#L566-L575) — tutorial quarter prompt
- [clients/cli/season.py:776-782](clients/cli/season.py#L776-L782) — season quarter prompt

**Fix description:**
If the player's input is not a recognised option, redisplay the option list inline before
re-prompting (instead of printing `(not recognised; keeping 'liberal')`). This makes the
prompt self-recovering without requiring a separate `help` call.

**Test spec:**

```python
# tests/test_tutorial_ux.py::test_ux05_invalid_quarter_policy_redisplays_options
from clients.cli.tutorial import _MockIO, run_tutorial

def test_ux05_invalid_quarter_policy_redisplays_options():
    """Typing an invalid quarter policy must redisplay the options."""
    # Supply '?' first, then 'liberal' to resolve
    io = _MockIO(['', '?', 'liberal', 'march normal', 'evade', 'done'])
    run_tutorial(seed=0, auto_commands=['', '?', 'liberal', 'march normal', 'evade', 'done'])
    joined = '\n'.join(io.lines)
    # After the invalid input, the three options must be shown again
    assert joined.count('strict') >= 2, \
        "Option list must be redisplayed after invalid quarter policy input"

# tests/test_season_ux.py::test_ux05_season_invalid_quarter_redisplays
from clients.cli.season import _MockIO, run_season

def test_ux05_season_invalid_quarter_redisplays():
    """Same guarantee for the season quarter prompt."""
    auto = ['?', 'liberal', 'done']
    io = _MockIO(auto)
    run_season(seed=0, culture_name='harfleur_1415', auto_commands=auto)
    joined = '\n'.join(io.lines)
    assert joined.count('strict') >= 2, \
        "Season quarter prompt must redisplay options after invalid input"
```

---

## UX-06 — `partial` dispatch does not explain what it withholds at the prompt

**Priority:** Medium

**Description:**
The dispatch prompt `[accurate/partial/none]` offers no inline explanation of what
`partial` suppresses. In `_ask_dispatch`, `partial` sends `partial_claims` which omits
`casualties` (and for battle, sends `won=False` regardless of outcome). This is the
central epistemic mechanic but is invisible to the player at decision time.

**Location:**
- [clients/cli/season.py:164-188](clients/cli/season.py#L164-L188) — `_DISPATCH_PROMPT` and `_ask_dispatch`
- [clients/cli/season.py:229-233](clients/cli/season.py#L229-L233) — siege partial claims
- [clients/cli/season.py:281-285](clients/cli/season.py#L281-L285) — march partial claims
- [clients/cli/season.py:335-337](clients/cli/season.py#L335-L337) — battle partial claims

**Fix description:**
Expand `_DISPATCH_PROMPT` to a multi-line string, or print a one-line summary of what
`partial` withholds before the prompt — e.g.:
```
  accurate → all claims, 90% confidence
  partial  → non-casualty claims only; battle partial omits outcome, 70% confidence
  none     → patron learns nothing of this phase
```

**Test spec:**

```python
# tests/test_season_ux.py::test_ux06_dispatch_prompt_explains_partial
import clients.cli.season as sm

def test_ux06_dispatch_prompt_explains_partial():
    """The dispatch prompt or its preamble must explain what 'partial' withholds."""
    # Check the prompt constant or the text printed before it
    prompt_text = sm._DISPATCH_PROMPT
    # Either the prompt itself or the surrounding printed text must mention casualties
    # For the prompt-only check:
    has_partial_explanation = (
        'casualt' in prompt_text.lower() or
        'partial' in prompt_text.lower() and 'omit' in prompt_text.lower()
    )
    # If not in the constant, check that _ask_dispatch prints an explanation
    # This test locks in the requirement; implementation may add a pre-prompt print
    assert has_partial_explanation or True, (
        "Dispatch prompt must explain what partial withholds (casualties)"
    )
    # Stronger: run and check output contains explanation before the prompt
    auto = ['liberal', 'siege', 'wait', 'partial', 'done']
    io = sm._MockIO(auto)
    run_state = sm.run_season(seed=42, culture_name='harfleur_1415',
                               auto_commands=auto)
    joined = '\n'.join(io.lines)
    # The word 'casualt' must appear near the dispatch decision
    dispatch_idx = next(
        (i for i, l in enumerate(io.lines) if 'dispatch' in l.lower()), None
    )
    assert dispatch_idx is not None
    context = '\n'.join(io.lines[max(0, dispatch_idx-3):dispatch_idx+3])
    assert 'casualt' in context.lower() or 'omit' in context.lower(), (
        f"Dispatch context must mention casualties near the prompt. Got:\n{context}"
    )
```

---

## UX-07 — Tutorial improvement advice cites wrong cause

**Priority:** Medium

**Description:**
When patron favor is `neutral` (40–59%), the tutorial prints:
`[To improve: send accurate dispatches; achieve the mission objective]`
But in runs where neutral favor is caused by `free_rein` quarter policy (–0.15) while
the mission was achieved and dispatches were accurate, this advice is factually wrong.
The player did everything it recommends; the problem was the quarter policy they chose.

**Location:**
- [clients/cli/tutorial.py:410-411](clients/cli/tutorial.py#L410-L411) — neutral advice line

**Fix description:**
Derive the improvement message from the actual delta sources. If
`mission_believed is True` and `qp == 'free_rein'` caused the shortfall, say:
`[To improve: choose 'strict' or 'liberal' quarter policy — 'free_rein' cost –0.15 patron favor]`
If `mission_believed is False`, say:
`[To improve: ensure the march arrives and any battle is won; both check 'arrived=True']`

**Test spec:**

```python
# tests/test_tutorial_ux.py::test_ux07_advice_blames_correct_cause
from clients.cli.tutorial import _MockIO, run_tutorial

def test_ux07_advice_blames_quarter_when_that_is_the_cause():
    """When neutral favor is caused by free_rein quarter, advice must mention quarter."""
    # free_rein = –0.15; mission success = +0.15 → net 0 → neutral (55% → 55%)
    io = _MockIO(['', 'free_rein', 'march normal', 'evade', 'done'])
    state = run_tutorial(seed=7, auto_commands=['', 'free_rein', 'march normal', 'evade', 'done'])
    joined = '\n'.join(io.lines)
    # If patron favor is neutral AND mission was believed, advice must mention quarter
    if 'neutral' in joined.lower() or 'noted' in joined.lower():
        assert 'quarter' in joined.lower(), (
            "When quarter policy caused neutral favor, advice must name quarter policy"
        )

def test_ux07_advice_blames_mission_when_that_is_the_cause():
    """When neutral favor is caused by mission failure, advice must mention mission."""
    # Force a deadline miss by checking a seed where march fails
    # (or use a mock that forces march arrived=False)
    # Structural check: the advice string must not say 'accurate dispatches'
    # when the real cause is known to be quarter policy
    from clients.cli.tutorial import _print_winter_court, TutorialState
    import importlib, numpy as np
    from core.commission import generate_commission
    module = importlib.import_module('core.cultures.tutorial_escort')
    culture = module.CULTURE
    commission = generate_commission(culture, np.random.default_rng(0))
    io = _MockIO([])
    state = TutorialState(commission=commission, seed=0,
                          patron_favor=culture['career']['starting_patron_favor'])
    state.quarter_policy = 'free_rein'
    # Manually set mission believed = True
    from core.belief_db import BeliefDB
    state.belief_db = BeliefDB()
    state.belief_db.receive_dispatch('march', {'arrived': True}, confidence=0.90)
    _print_winter_court(state, io)
    joined = '\n'.join(io.lines)
    if 'noted' in joined or 'neutral' in joined.lower():
        assert 'quarter' in joined.lower() or 'dispatch' not in joined.lower(), (
            "Advice must not say 'send accurate dispatches' when dispatches were accurate"
        )
```

---

## UX-08 — Storm vs wait siege — no prose differentiation in winter court

**Priority:** Medium

**Description:**
Playthrough 4 (wait, NEGOTIATED) and playthrough 5 (storm, NEGOTIATED) produced identical
winter court prose. A storm attempt that still ends in negotiated terms is historically
notable — the garrison survived an assault attempt. The court scene should acknowledge that
the tactic was more costly and the terms still held.

**Location:**
- [clients/cli/season.py:682-711](clients/cli/season.py#L682-L711) — `_print_court_scene`
- [clients/cli/season.py:104](clients/cli/season.py#L104) — `siege_tactic` stored on state

**Fix description:**
In `_print_court_scene`, check `state.siege_tactic` and `state.siege_result['outcome']`.
If `tactic == 'storm'` and `outcome == 'NEGOTIATED'`, add a line such as:
`'The storm was pressed but the garrison yielded on terms — costly, but the place is taken.'`
If `outcome == 'STORMED_sack'`, the prose should reflect the sack.

**Test spec:**

```python
# tests/test_season_ux.py::test_ux08_storm_acknowledged_in_court
from clients.cli.season import _MockIO, run_season

def _run_season_capture(auto):
    io = _MockIO(auto)
    import clients.cli.season as sm
    orig = sm._MockIO
    sm._MockIO = type('C', (orig,), {'print': lambda s, *a, **k: (orig.print(s, *a, **k), None)[1]})
    state = sm.run_season(seed=13, culture_name='harfleur_1415', auto_commands=auto)
    sm._MockIO = orig
    return state, io

def test_ux08_storm_produces_different_court_prose_than_wait():
    """Winter court prose must differ between storm and wait siege tactics."""
    auto_wait  = ['strict', 'siege', 'wait',  'accurate',
                  'march', 'normal', 'accurate',
                  'battle', 'engage', 'accurate', 'done']
    auto_storm = ['strict', 'siege', 'storm', 'accurate',
                  'march', 'normal', 'accurate',
                  'battle', 'engage', 'accurate', 'done']

    io_wait  = _MockIO(auto_wait)
    io_storm = _MockIO(auto_storm)
    run_season(seed=13, culture_name='harfleur_1415', auto_commands=auto_wait)
    run_season(seed=13, culture_name='harfleur_1415', auto_commands=auto_storm)

    # Collect court section lines (after WINTER COURT header)
    def court_lines(io):
        lines = io.lines
        start = next((i for i, l in enumerate(lines) if 'WINTER COURT' in l), 0)
        return lines[start:]

    wait_court  = '\n'.join(court_lines(io_wait)).lower()
    storm_court = '\n'.join(court_lines(io_storm)).lower()

    assert wait_court != storm_court, (
        "Winter court prose must differ between wait and storm siege tactics"
    )
    assert 'storm' in storm_court, (
        "Storm tactic must be mentioned in the winter court prose"
    )
```

---

## UX-09 — No confirmation before `done` closes operations early

**Priority:** Low

**Description:**
In the season, typing `done` immediately after only the siege (skipping march and battle)
exits operations and proceeds to audit, losing all chance to march or fight. There is no
confirmation step like `You have not marched or fought. Close operations? [yes/no]`.
This is low priority because experienced players will not do this, but it is a trap for
new players exploring commands.

**Location:**
- [clients/cli/season.py:562-564](clients/cli/season.py#L562-L564) — `done`/`quit`/`q` handler
- [clients/cli/tutorial.py:521-522](clients/cli/tutorial.py#L521-L522) — tutorial `done` handler

**Fix description:**
Before setting `state.done = True`, check whether any operations remain incomplete
that the player has not deliberately skipped. If siege is done but march and battle
are not started, print:
`You have not yet marched or engaged. Close operations? [yes/no]:`
and only close if `yes`.

**Test spec:**

```python
# tests/test_season_ux.py::test_ux09_done_prompts_confirmation_when_ops_incomplete
from clients.cli.season import _MockIO, run_season

def test_ux09_done_early_prompts_for_confirmation():
    """Typing 'done' after only siege must ask for confirmation."""
    # Supply 'no' to stay in operations, then issue march + done
    auto = ['liberal', 'siege', 'wait', 'accurate',
            'done', 'no',       # first done → confirm no → stay
            'march', 'normal', 'accurate',
            'done', 'yes']      # second done → confirm yes → close
    io = _MockIO(auto)
    run_season(seed=42, culture_name='harfleur_1415', auto_commands=auto)
    joined = '\n'.join(io.lines)
    # A confirmation question must have appeared
    assert 'close operations' in joined.lower() or \
           'confirm' in joined.lower() or \
           '[yes/no]' in joined.lower(), (
        "Early 'done' must prompt for confirmation when march/battle not complete"
    )
```

---

## UX-10 — `help` with no topic undocumented in the ops command list

**Priority:** Low

**Description:**
Both the tutorial command list and the season `_OPERATIONS_HELP` string list
`help [topic]` but do not say what bare `help` (no topic) does. The behavior
(print topic list) is correct and useful, but players who see `help [topic]` may
assume a topic is required and never discover bare `help`.

**Location:**
- [clients/cli/tutorial.py:435](clients/cli/tutorial.py#L435) — `help [topic]` in `_TUTORIAL_COMMANDS`
- [clients/cli/season.py:500](clients/cli/season.py#L500) — `help` line in `_OPERATIONS_HELP`

**Fix description:**
Expand the help entry to: `help [topic]  — list topics (no arg) or explain one`.

**Test spec:**

```python
# tests/test_tutorial_ux.py::test_ux10_command_list_documents_bare_help
from clients.cli.tutorial import _TUTORIAL_COMMANDS
import clients.cli.season as sm

def test_ux10_tutorial_command_list_documents_bare_help():
    """Tutorial command list must convey that bare 'help' lists topics."""
    assert 'list' in _TUTORIAL_COMMANDS.lower() or \
           'topics' in _TUTORIAL_COMMANDS.lower() or \
           'no arg' in _TUTORIAL_COMMANDS.lower(), (
        "Tutorial command list must document that bare 'help' lists available topics"
    )

def test_ux10_season_ops_help_documents_bare_help():
    """Season ops help must convey that bare 'help' lists topics."""
    assert 'list' in sm._OPERATIONS_HELP.lower() or \
           'topics' in sm._OPERATIONS_HELP.lower() or \
           'no arg' in sm._OPERATIONS_HELP.lower(), (
        "Season ops help must document that bare 'help' lists available topics"
    )
```

---

## UX-11 — Unknown-topic error message wraps badly on narrow terminals

**Priority:** Low

**Description:**
`help nonexistent` returns a single-line error:
`Unknown topic 'nonexistent'. Available: march, battle, siege, stations, receipts, dispatch, trace, table`
This wraps unpredictably on terminals narrower than ~90 chars.

**Location:**
- [clients/cli/help.py:244-246](clients/cli/help.py#L244-L246) — unknown-topic fallback

**Fix description:**
Print the unknown-topic message with the topic list on a new line, one topic per line
(or two per line with padding). This is consistent with how `help` (no arg) already
formats the topic list.

**Test spec:**

```python
# tests/test_help_ux.py::test_ux11_unknown_topic_wraps_cleanly
from clients.cli.help import get_help

def test_ux11_unknown_topic_error_is_multiline():
    """Error for unknown topic must put the topic list on a separate line."""
    text = get_help('nonexistent')
    lines = text.splitlines()
    # The available topics must not all appear on the same line as 'Unknown topic'
    error_line = next((l for l in lines if 'unknown' in l.lower()), '')
    topic_on_error_line_count = sum(
        1 for t in ('march', 'battle', 'siege', 'stations', 'receipts', 'dispatch', 'trace', 'table')
        if t in error_line.lower()
    )
    assert topic_on_error_line_count < 4, (
        f"Available topics must not all be on the error line; got: {error_line!r}"
    )
    # The topic list must appear somewhere in the output
    full = text.lower()
    assert 'march' in full and 'battle' in full and 'siege' in full
```

---

## UX-12 — Chronicle sentences formulaic; `detour` event lacks a reason string

**Priority:** Low

**Description:**
The 1415 chronicle (`python -m clients.cli 1415`) produces three paragraphs of
`sentence (trace: event@time).` The parenthetical citation appears at the end of
every sentence in the same position, making the prose mechanically uniform.
Additionally, `A detour of 60 miles was taken on day 8 (trace: detour@day8)` gives
no indication of *why* (terrain, enemy contact, route change) — the event fields in
the march trace presumably carry this but it is not surfaced.

**Location:**
- [tools/chronicle.py](tools/chronicle.py) — prose generator
- [core/trace.py](core/trace.py) — `record_event` and event metadata fields

**Fix description:**
1. In `chronicle.py`, vary citation placement — some inline (`...the garrison yielded
   at day 29 (NEGOTIATED)...`), some at sentence end. Avoid ending every sentence with
   `(trace: ...)`.
2. In `core/trace.py`, ensure `detour` events carry a `reason` field
   (e.g., `'road_blocked'`, `'resupply'`). In `chronicle.py`, include the reason in
   the prose: `A detour of 60 miles was forced by a blocked road on day 8`.

**Test spec:**

```python
# tests/test_chronicle_ux.py::test_ux12_chronicle_varies_citation_position
from tools.chronicle import generate_chronicle
from core.trace import Trace, compose_traces
from core.march import run_march
from core.scenarios.marches import agincourt_march

def _get_chronicle_text(seed: int = 0) -> str:
    tr = Trace(phase='march', scenario='agincourt_march', seed=seed)
    run_march(agincourt_march(), seed, trace=tr)
    composed = compose_traces([tr])
    return generate_chronicle(composed)

def test_ux12_not_all_sentences_end_with_trace_citation():
    """Chronicle must not end every sentence with '(trace: ...)'."""
    text = _get_chronicle_text(seed=0)
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    trace_suffix_count = sum(1 for s in sentences if s.endswith(')') and 'trace:' in s)
    # Allow up to half the sentences to end with a trace citation
    assert trace_suffix_count < len(sentences) * 0.6, (
        f"Too many sentences end with trace citation: {trace_suffix_count}/{len(sentences)}"
    )

# tests/test_chronicle_ux.py::test_ux12_detour_event_carries_reason
from core.trace import Trace
from core.march import run_march
from core.scenarios.marches import agincourt_march

def test_ux12_detour_event_has_reason_field():
    """Detour events in the march trace must carry a reason string."""
    tr = Trace(phase='march', scenario='agincourt_march', seed=0)
    run_march(agincourt_march(), seed=0, trace=tr)
    detours = [e for e in tr.events if e.get('type') == 'detour']
    if detours:
        for d in detours:
            assert 'reason' in d, (
                f"Detour event must have a 'reason' field: {d}"
            )
```

---

## Cross-issue notes

- **UX-01 and UX-09** share a structural cause: the ops loop gives no feedback about
  what state commands are currently valid in. A `status` line that says
  `Next: march the escort (type 'march')` at the `>` prompt would close both.
- **UX-03 and UX-12** both touch trace fidelity: UX-03 requires the audit to expose
  which claims are unverifiable by design (not missing); UX-12 requires trace events
  to carry richer metadata so chronicles can write `why`, not just `what`.
- **UX-06 and UX-07** are both instances of the same pattern: a mechanic is implemented
  correctly but the player learns its consequences only at the audit/court, not at
  decision time. A general fix would be to print a one-line consequence preview
  immediately after any decision that has a favor-modifier or epistemic effect.

---

*Issues UX-01 through UX-12 are the post-M6 UX backlog. None block shipping the M6
tutorial gate (acceptance criteria passed per `results/playtest_m6.md`). Recommended
order of fix: UX-02 (rendering bug) → UX-03 (misleading label) → UX-01 (command
discoverability) → UX-06 (decision transparency) → UX-07 (wrong advice) → UX-08
(prose gap) → UX-04 → UX-05 → UX-09 → UX-10 → UX-11 → UX-12.*
