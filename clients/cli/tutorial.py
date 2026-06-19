"""MARCHLAND CLI: tutorial season — escort of Sir William Brandon (M6).

Usage:
    python -m clients.cli tutorial [--seed N]

One complete season of an escort commission: muster → march → (patrol?) → winter court.
Designed so a new player can reach the winter court in under 20 minutes.

What this tutorial teaches (in order):
  1. Receipts — every number is explained at muster
  2. Quarter policy — first meaningful decision
  3. March pace — second decision; fatigue consequence shown
  4. Engagement choice — engage or evade the patrol
  5. Winter court — patron assessment explained explicitly

Differences from 'python -m clients.cli season':
  - No siege (escort mission: march + possible engagement only)
  - No dispatch latency (station is always CAMP; focus stays on decisions)
  - Dispatch is sent automatically (patron always hears something)
  - Winter court explains WHY the patron is pleased or displeased

Pass auto_commands for non-interactive / test use (list of string inputs in order).
"""
import importlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from core.commission import Commission, generate_commission, apply_quarter_policy
from core.belief_db import BeliefDB, trace_to_summary
from core.missions import MISSIONS, evaluate_mission, patron_believes_success
from core.trace import Trace, compose_traces
from core.march import run_march
from core.lattice import Battle
from clients.cli.covenant import print_covenant
from clients.cli.help import show_help


# ------------------------------------------------------------------
# Inline scenario builders (not registered in battery — teaching only)

def _tutorial_march_scn() -> Dict:
    from core.march import scenario
    return scenario(
        start=300, distance=50, pace=10.0,
        carriers={'wagon': 4, 'porter': 8},
        stock_days=7, stock_cap_days=10,
        water_ok=0.92, season='dry', season_factor=0.9,
        land_density=20, officers=0.90, camp_quality=0.85,
        cohesion0=0.85, fat0=0.05,
        home_pull=0.10, pay_arrears=0.0, desert_share=0.2,
        disease_env=0.8, heat=0.8, weather=1.0,
        max_days=12, roads=1, road_quality=1.0,
        rest_every=0, forage=True, dispersal=0.20, screen_miles=4,
    )


def _tutorial_skirmish_scn(fat0: float = 0.05) -> Dict:
    """Road engagement: English escort (~2000 men) vs French blocking force (~1500 men).

    At the engine's standard 1 agent ≈ 10 men scale: 200 English agents vs 150 French.
    Small relative to full pitched battles (Agincourt: 2000+ agents per side).
    """
    co = []
    co.append(dict(
        side=0, n=100, x=(60, 100), y=(50, 180),
        hold=1, err=0.75, armor=0.80,
        belief=0.80, disc=0.75, fat0=fat0,
    ))
    co.append(dict(
        side=0, n=50, x=(50, 90), y=(0, 50),
        hold=1, ranged=1, ammo=8,
        err=0.85, armor=0.15, belief=0.80, disc=0.60, fat0=fat0,
    ))
    co.append(dict(
        side=0, n=50, x=(50, 90), y=(180, 230),
        hold=1, ranged=1, ammo=8,
        err=0.85, armor=0.15, belief=0.80, disc=0.60, fat0=fat0,
    ))
    co.append(dict(
        side=1, n=150, x=(380, 450), y=(30, 200),
        err=0.90, armor=0.50, belief=0.65, fat0=0.10,
    ))
    return dict(
        field=(500, 230),
        cohorts=co,
        range={0: 160},
        break_frac=0.40,
        pursuit_intensity={0: 0.30, 1: 0.55},
    )


# ------------------------------------------------------------------
# IO abstraction

class _IO:
    def print(self, *args, **kw):
        print(*args, **kw)

    def input(self, prompt: str) -> str:
        return input(prompt)


class _MockIO(_IO):
    """Drives the tutorial non-interactively for tests."""

    def __init__(self, commands: List[str]):
        self._commands = iter(commands)
        self.lines: List[str] = []

    def print(self, *args, **kw):
        sep = kw.get('sep', ' ')
        self.lines.append(sep.join(str(a) for a in args))

    def input(self, prompt: str) -> str:
        val = next(self._commands, '')
        self.lines.append(f"{prompt}{val}")
        return val


# ------------------------------------------------------------------
# Tutorial state

@dataclass
class TutorialState:
    commission: Commission
    seed: int
    belief_db: BeliefDB = field(default_factory=BeliefDB)
    trace_phases: List[Any] = field(default_factory=list)
    composed_trace: Optional[Dict] = None
    march_result: Optional[Dict] = None
    battle_result: Optional[Dict] = None
    quarter_policy: str = 'liberal'
    patron_favor: float = 0.55
    day: int = 0
    done: bool = False


# ------------------------------------------------------------------
# Annotated muster

def _print_annotated_muster(commission: Commission, io: _IO) -> None:
    """Print the muster roll with receipt explanations in parentheticals."""
    io.print()
    io.print("=" * 58)
    io.print("  MUSTER — commission from Lord Camoys")
    io.print("=" * 58)
    io.print(f"  Mission : ESCORT")
    io.print(f"            Deliver Sir William Brandon to Ardres.")
    io.print(f"  Deadline: {commission.strings['deadline_days']} days")
    io.print(f"  Army    : {commission.army_name}")
    io.print()
    io.print("  RECEIPTS — every number below answers: what changes it?")
    io.print("  Parenthetical labels: (B)=equipment (C)=campaign state")
    io.print("  (D)=institution (E)=trained capacity  Type 'help receipts'.")
    io.print()

    # Locate receipt_notes for this army
    notes_by_label: Dict[str, List[str]] = {}
    for army in commission.culture.get('armies', []):
        if army['name'] == commission.army_name:
            notes_by_label = army.get('receipt_notes', {})
            break

    for c in commission.army_cohorts:
        label = c['label']
        n = c['n']
        equip_parts = []
        a = c.get('armor', 0)
        if a >= 0.7:
            equip_parts.append(f"partial harness (armor={a:.2f})")
        elif a >= 0.1:
            equip_parts.append(f"padded (armor={a:.2f})")
        else:
            equip_parts.append('unarmored')
        if c.get('ranged'):
            equip_parts.append(f"longbow ×{c.get('ammo', 0)} sheaves")
        if c.get('mounted'):
            equip_parts.append('mounted')

        io.print(f"  {label}  ({n} men)")
        io.print(f"    Equipment: {', '.join(equip_parts)}")
        for note in notes_by_label.get(label, []):
            io.print(f"      · {note}")
        io.print()

    io.print("  March receipts (what changes the journey):")
    for note in commission.culture.get('march_receipt_notes', []):
        io.print(f"    · {note}")
    io.print()


# ------------------------------------------------------------------
# Operations

def _do_march(state: TutorialState, io: _IO, pace: str) -> None:
    """Run the escort march and record the result."""
    io.print()
    io.print("--- March: Calais to Ardres ---")

    scn = _tutorial_march_scn()
    if pace == 'push':
        scn = dict(scn, pace=scn['pace'] * 1.20,
                   fat0=min(1.0, scn['fat0'] + 0.05))
        io.print("  Pushing the pace — men cover ground faster but tire sooner.")
        io.print("  (fat0 rises +5%; fatigue amplifies battle opening hazard)")
    elif pace == 'rest':
        scn = dict(scn, rest_every=3,
                   fat0=max(0.0, scn['fat0'] - 0.03))
        io.print("  Rest days every 3rd — men arrive fresher, march takes longer.")
        io.print("  (fat0 falls -3%; rest days pause supply consumption)")
    else:
        io.print("  Normal pace — 10 miles a day on the king's road.")

    io.print()
    io.print("  [The march model runs: each day ticks supply, water, fatigue.]")
    io.print()

    tr = Trace(phase='march', scenario='tutorial_escort_march', seed=state.seed)
    result = run_march(scn, state.seed, trace=tr)
    state.march_result = result
    state.trace_phases.append(tr)
    state.day += result['days']

    arrived_str = "arrived" if result['arrived'] else "did NOT arrive (deadline missed)"
    io.print(f"  Result   : army {arrived_str} in {result['days']} days")
    io.print(f"  Effective: {result['effective']:,} men")
    io.print(f"  Fatigue  : {result['fatigue']:.0%}"
             + ("  (high — will amplify battle hazard)" if result['fatigue'] > 0.25 else ""))
    io.print(f"  Supply   : {result['stock_days']:.1f} days remaining")
    if result.get('dead', 0) > 0:
        io.print(f"  Dead     : {result['dead']} (thirst/disease — trace records each cause)")
    if result.get('stragglers', 0) > 0:
        io.print(f"  Stragglers: {result['stragglers']}")
    io.print()
    io.print("  [WHY 'arrived': miles_covered >= 50 before max_days=12]")
    io.print("  [WHY fatigue: 0.025*hard^2 per day; rest days recover 0.06]")

    # Dispatch sent automatically in tutorial — patron always hears
    full_claims = {
        'arrived': result['arrived'],
        'day': result['days'],
        'fatigue': round(result['fatigue'], 2),
    }
    state.belief_db.receive_dispatch('march', full_claims, confidence=0.90)
    io.print()
    io.print("  (Rider dispatched to Lord Camoys: accurate report, confidence 90%)")


def _do_engagement(state: TutorialState, io: _IO) -> None:
    """Run the French blocking force engagement."""
    io.print()
    io.print("--- Encounter: French blocking force on the Ardres road ---")
    io.print()
    io.print("  A French column holds the road. Your archers deploy on both flanks.")
    fat0 = state.march_result.get('fatigue', 0.05) if state.march_result else 0.05
    io.print(f"  Your starting fatigue: {fat0:.0%}"
             + ("  (elevated — archers tire faster in contact)" if fat0 > 0.20 else ""))
    io.print()
    io.print("  [BP-Lattice runs: English (~2000 men, 200 agents) vs French (~1500, 150 agents)]")
    io.print("  [Archers fire volleys at ADVANCE phase; melee fires at CONTACT]")
    io.print()

    scn = _tutorial_skirmish_scn(fat0=min(0.60, fat0))
    tr = Trace(phase='battle', scenario='tutorial_skirmish', seed=state.seed)
    result = Battle(scn, state.seed, trace=tr).run()
    state.battle_result = result
    state.trace_phases.append(tr)

    s0, s1 = result['s'][0], result['s'][1]
    winner = {0: 'English', 1: 'French'}.get(result['win'], 'inconclusive')
    io.print(f"  Outcome    : {winner} prevail")
    io.print(f"  English dead : {s0.get('dead', 0)}   (pre-break: {s0.get('pre', 0)}, pursuit: {s0.get('post', 0)})")
    io.print(f"  French dead  : {s1.get('dead', 0)}   (pre-break: {s1.get('pre', 0)}, pursuit: {s1.get('post', 0)})")

    if result['win'] == 0:
        io.print()
        io.print("  [WHY English prevailed: archers degraded French belief before contact;")
        io.print("   the patrol broke when rout appraisal cues exceeded their threshold]")
        io.print("  [Most French dead occurred in the pursuit — 'casualties live in the pursuit']")
    else:
        io.print()
        io.print("  [WHY French prevailed: march fatigue raised the English opening hazard;")
        io.print("   consider resting one day before an engagement (reduces fat0)]")

    won = (result['win'] == 0)
    state.belief_db.receive_dispatch('battle', {
        'won': won,
        'casualties': s0.get('dead', 0),
        'enemy_dead':  s1.get('dead', 0),
    }, confidence=0.90)
    io.print()
    io.print("  (Rider dispatched to Lord Camoys: battle result reported)")


def _do_evade(state: TutorialState, io: _IO) -> None:
    """Evade the patrol via a farm track — costs one extra day."""
    state.day += 1
    io.print()
    io.print("  A farm track to the north adds a day to the march.")
    io.print("  The patrol sees nothing. No blood spilled.")
    io.print(f"  (Season day now: {state.day})")
    io.print()
    io.print("  [WHY no battle entry: evading means no trace battle phase;")
    io.print("   the escort mission predicate checks only 'march arrived' when no battle exists]")


# ------------------------------------------------------------------
# Winter court

def _print_winter_court(state: TutorialState, io: _IO) -> None:
    """Gentle, instructive winter court that explains the patron's reasoning."""
    io.print()
    io.print("=" * 58)
    io.print("  WINTER COURT — Calais, the garrison hall")
    io.print("=" * 58)
    io.print()
    io.print("  Lord Camoys reads your dispatches by candlelight.")
    io.print()

    if state.trace_phases:
        state.composed_trace = compose_traces(state.trace_phases)
        ts = trace_to_summary(state.composed_trace)
    else:
        ts = {}

    mission_actual = evaluate_mission('escort', ts)
    mission_believed = patron_believes_success('escort', state.belief_db)

    # Patron assessment — always explained
    if mission_believed:
        io.print("  'The escort reached Ardres. Brandon is content. Well done.'")
        io.print()
        io.print("  [WHY patron credits success: dispatch carried 'arrived=True';")
        io.print("   escort objective_predicate = march arrived AND (no battle OR battle won)]")
    else:
        io.print("  'We have no word from the road. Brandon's man tells a different story.'")
        io.print()
        io.print("  [WHY patron does not credit success: the dispatch carried 'arrived=False'")
        io.print("   or no dispatch was received for the march phase]")

    if state.battle_result:
        s0 = state.battle_result.get('s', [{}, {}])[0]
        if state.battle_result.get('win') == 0:
            io.print()
            io.print("  'The patrol was seen off cleanly. Good work on the road.'")
            prisoners = max(1, s0.get('dead', 0) // 10)
            if prisoners > 0:
                ransom = state.commission.culture['career']['ransom_share']
                io.print(f"  Prisoners: {prisoners} men taken. Crown claims {ransom:.0%} of ransom.")
        elif state.battle_result.get('win') == 1:
            io.print()
            io.print("  'We hear the patrol bloodied you on the road. Costly escort.'")

    elif not state.battle_result:
        io.print()
        io.print("  'No patrol trouble reported — a clean road is its own kind of victory.'")

    # Quarter policy assessment
    qp = state.quarter_policy
    qc = state.commission.culture['quarter_customs'].get(qp, {})
    io.print()
    io.print(f"  Quarter policy was '{qp}': {qc.get('note', '')}")

    # Favor calculation
    favor = state.patron_favor
    favor_delta = qc.get('patron_favor_mod', 0.0)
    if mission_believed:
        favor_delta += 0.15
    else:
        favor_delta -= 0.10
    # Tutorial clamp: floor at 0.35 so first session is not punishing
    favor_delta = max(favor_delta, -0.15)
    favor = max(0.35, min(1.0, favor + favor_delta))
    state.patron_favor = favor

    io.print()
    io.print(f"  [Favor calculation: base {state.commission.patron_favor:.2f}"
             f"  + mission {'credit' if mission_believed else 'penalty'} "
             f"{'(+0.15)' if mission_believed else '(-0.10)'}"
             f"  + quarter {favor_delta - (0.15 if mission_believed else -0.10):+.2f}"
             f"  = {favor:.2f}]")

    # Credit label
    thresholds = state.commission.culture['career']['credit_thresholds']
    labels = state.commission.culture['doctrine_vocab']['favor_labels']

    def _label(f: float) -> str:
        ordered = [
            (thresholds.get('acclaim', 0.80), labels[4] if len(labels) > 4 else 'acclaim'),
            (thresholds.get('favor',   0.60), labels[3] if len(labels) > 3 else 'favor'),
            (thresholds.get('neutral', 0.40), labels[2] if len(labels) > 2 else 'neutral'),
            (thresholds.get('cold',    0.20), labels[1] if len(labels) > 1 else 'cold'),
            (thresholds.get('censure', 0.00), labels[0] if labels else 'censure'),
        ]
        for threshold, lbl in ordered:
            if f >= threshold:
                return lbl
        return ordered[-1][1]

    credit = _label(favor)
    io.print()
    io.print(f"  Season result: patron favor {favor:.0%}  [{credit}]")
    io.print()

    if favor >= thresholds.get('favor', 0.60):
        io.print("  Lord Camoys offers you a commission for the next season.")
    elif favor >= thresholds.get('neutral', 0.40):
        io.print("  Your service is noted. A commission may come — in time.")
        if mission_believed and qp == 'free_rein':
            io.print("  [To improve: choose 'strict' or 'liberal' quarter policy"
                     " — 'free_rein' cost -0.15 patron favor]")
        elif not mission_believed:
            io.print("  [To improve: ensure the march arrives and any battle is won;"
                     " both check 'arrived=True']")
        else:
            io.print("  [To improve: send accurate dispatches; achieve the mission objective]")
    else:
        io.print("  Lord Camoys is silent on the matter of next season.")
        if not mission_believed:
            io.print("  [To improve: ensure 'arrived=True' in your march dispatch]")
        elif qp == 'free_rein':
            io.print("  [To improve: choose 'strict' or 'liberal' quarter policy"
                     " — 'free_rein' cost -0.15 patron favor]")
        else:
            io.print("  [To improve: ensure 'arrived=True' in your march dispatch]")

    io.print()
    io.print("  Tutorial complete.")
    io.print()
    io.print("  Next steps:")
    io.print("    Full campaign (Harfleur siege + Agincourt):  python -m clients.cli season")
    io.print("    Chain demo with chronicles:                  python -m clients.cli 1415")
    io.print("    Mechanic help at any time:                   help <topic>")
    io.print()


# ------------------------------------------------------------------
# Quarter policy prompt (extracted so tests can call directly)

def _print_quarter_options(io: _IO) -> None:
    """Print the three quarter policy options with their favor modifiers."""
    io.print("  strict     → patron pleased; men grumble (patron favor +0.10)")
    io.print("  liberal    → the custom of the age; balanced (no modifier)")
    io.print("  free_rein  → men happy; patron will hear of it (patron favor -0.15)")


def _ask_quarter_policy(commission: 'Commission', culture: Dict, io: _IO) -> str:
    """Prompt for quarter policy, redisplaying options on invalid input.

    Returns the chosen policy string.
    """
    io.print("  DECISION 1: Quarter policy")
    _print_quarter_options(io)
    io.print()
    while True:
        raw = io.input("  Choose quarter policy [strict/liberal/free_rein]: ").strip().lower()
        if raw in ('strict', 'liberal', 'free_rein'):
            apply_quarter_policy(commission, raw)
            return raw
        if not raw:
            # Empty string (auto_commands exhausted) — keep default
            return commission.strings['quarter_policy']
        io.print("  (Not recognised. Choose from:)")
        _print_quarter_options(io)
        io.print()


# ------------------------------------------------------------------
# Operations loop

_TUTORIAL_COMMANDS = """\
Tutorial commands:
  march [normal/push/rest] — march the escort to Ardres
  engage                   — fight the French patrol (available after march)
  evade                    — find a way around the patrol (+1 day, available after march)
  status                   — show current state
  help [topic]             — list topics (no arg) or explain one
  done                     — conclude operations and go to winter court
"""


def _operations_phase(state: TutorialState, io: _IO) -> None:
    io.print()
    io.print("=" * 58)
    io.print("  OPERATIONS")
    io.print("=" * 58)
    io.print("  Your mission: march the escort from Calais to Ardres.")
    io.print(_TUTORIAL_COMMANDS)

    patrol_encountered = False
    patrol_decided = False

    while not state.done:
        deadline = state.commission.strings['deadline_days']
        if state.day >= deadline:
            io.print(f"  Deadline reached (day {state.day}). Operations close.")
            break

        raw = io.input("> ").strip().lower()
        parts = raw.split()
        cmd = parts[0] if parts else ''
        arg = ' '.join(parts[1:]) if len(parts) > 1 else ''

        if cmd == 'march':
            if state.march_result is not None:
                io.print("  (March already complete.)")
                continue
            # Pace may be supplied inline: 'march push'
            pace = arg if arg in ('normal', 'push', 'rest') else None
            if pace is None:
                io.print()
                io.print("  DECISION 2: March pace")
                io.print("  normal → ~10 miles/day; balanced fatigue and timing")
                io.print("  push   → +20% distance/day; men arrive tired (fat0 +5%)")
                io.print("  rest   → rest day every 3rd; men fresher, takes longer")
                raw_pace = io.input("  Pace [normal/push/rest]: ").strip().lower()
                pace = raw_pace if raw_pace in ('normal', 'push', 'rest') else 'normal'
            _do_march(state, io, pace)
            if state.march_result and state.march_result['arrived']:
                patrol_encountered = True
                io.print()
                io.print("  *** A French blocking force is sighted on the Ardres road. ***")
                io.print("  Type 'engage' to deploy and fight, or 'evade' to find a way around.")

        elif cmd == 'engage':
            if not patrol_encountered:
                io.print("  engage and evade become available once the march is complete — type 'march' first.")
                continue
            if patrol_decided:
                io.print("  The patrol has already been dealt with.")
                continue
            if state.march_result is None:
                io.print("  March first.")
                continue
            patrol_decided = True
            _do_engagement(state, io)

        elif cmd == 'evade':
            if not patrol_encountered:
                io.print("  engage and evade become available once the march is complete — type 'march' first.")
                continue
            if patrol_decided:
                io.print("  Already past the patrol.")
                continue
            if state.march_result is None:
                io.print("  March first.")
                continue
            patrol_decided = True
            _do_evade(state, io)

        elif cmd == 'status':
            io.print(f"  Season day : {state.day} / {deadline}")
            io.print(f"  March      : {'arrived' if (state.march_result and state.march_result['arrived']) else 'not yet' if state.march_result is None else 'failed'}")
            if state.battle_result:
                io.print(f"  Engagement : {'won' if state.battle_result.get('win') == 0 else 'lost'}")
            elif patrol_decided:
                io.print("  Patrol     : evaded")
            io.print(f"  Favor      : {state.patron_favor:.0%} (patron's current estimate)")

        elif cmd == 'help':
            show_help(arg if arg else None, io)

        elif cmd in ('done', 'quit', 'q'):
            io.print("  Operations concluded.")
            state.done = True

        elif cmd == '':
            pass

        else:
            io.print(f"  Unknown command '{raw}'.")
            io.print(_TUTORIAL_COMMANDS)


# ------------------------------------------------------------------
# Public entry point

def run_tutorial(seed: int = 0,
                 auto_commands: Optional[List[str]] = None) -> TutorialState:
    """Run the tutorial season and return the final TutorialState.

    auto_commands: if supplied, runs non-interactively (for tests).
    Inputs are consumed in order; the loop exits when commands are exhausted
    (the empty string returned by MockIO for exhausted commands matches 'done').
    """
    module = importlib.import_module('core.cultures.tutorial_escort')
    culture = module.CULTURE

    rng = np.random.default_rng(seed)
    commission = generate_commission(culture, rng)

    io: _IO = _MockIO(auto_commands) if auto_commands is not None else _IO()
    state = TutorialState(
        commission=commission,
        seed=seed,
        patron_favor=culture['career']['starting_patron_favor'],
    )

    # -- Covenant
    print_covenant(io)
    io.print("  Press Enter to begin, or type a command ('help' for topics).")
    io.input("")
    io.print()
    io.print("── BEGIN ──")
    io.print()

    # -- Muster
    _print_annotated_muster(commission, io)

    # Decision 1: quarter policy
    _ask_quarter_policy(commission, culture, io)
    state.quarter_policy = commission.strings['quarter_policy']
    qc = culture['quarter_customs'][state.quarter_policy]
    io.print(f"  Quarter set to '{state.quarter_policy}': {qc['note']}")
    io.print()

    # -- Operations
    _operations_phase(state, io)

    # -- Winter court
    _print_winter_court(state, io)

    return state
