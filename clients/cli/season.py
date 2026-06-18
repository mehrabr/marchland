"""MARCHLAND CLI: interactive season loop (M3).

Usage:
    python -m clients.cli season [--culture harfleur_1415] [--seed N]

One full campaign season: muster → operations → audit → winter court.
The player makes at least 4 meaningful decisions; the patron's winter court
assessment is drawn from their belief_db (dispatches only), not the trace.

Inject 'auto_commands' for non-interactive/test use.
"""
import sys
import importlib
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.commission import Commission, generate_commission, apply_quarter_policy, muster_summary
from core.belief_db import BeliefDB, trace_to_summary
from core.missions import MISSIONS, evaluate_mission, patron_believes_success
from core.trace import Trace, compose_traces
from core.siege import run_siege
from core.march import run_march
from core.lattice import Battle
from core.chain import siege_to_march, march_to_battle
from core.scenarios.harfleur import harfleur
from core.scenarios.marches import agincourt_march
from core.scenarios.agincourt import agincourt


# ------------------------------------------------------------------
# IO abstraction — injectable for tests

class _IO:
    def print(self, *args, **kw):
        print(*args, **kw)

    def input(self, prompt: str) -> str:
        return input(prompt)


class _MockIO(_IO):
    """Drives the season from a pre-supplied command list (for tests)."""

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
# Season state

class SeasonState:
    """Holds all mutable season state; passed between phases."""

    def __init__(self, commission: Commission, seed: int):
        self.commission = commission
        self.seed = seed
        self.belief_db = BeliefDB()
        self.trace_phases: List[Trace] = []
        self.composed_trace: Optional[Dict] = None

        # Results of each operation (set as operations run)
        self.siege_result: Optional[Dict] = None
        self.march_result: Optional[Dict] = None
        self.battle_result: Optional[Dict] = None

        # Player decisions
        self.quarter_policy: str = 'liberal'    # decision 1
        self.siege_tactic: Optional[str] = None # decision 2 — 'wait' | 'storm'
        self.march_pace: Optional[str] = None   # decision 3 — 'normal' | 'push' | 'rest'
        self.battle_choice: Optional[str] = None# decision 4 — 'engage' | 'withdraw'

        # Patron favor accumulator
        self.patron_favor: float = commission.patron_favor

        self.day: int = 0           # elapsed season days
        self.done: bool = False     # player ended operations early

    def elapsed(self, days: int):
        self.day += days


# ------------------------------------------------------------------
# Dispatch helpers

_DISPATCH_PROMPT = (
    "Send dispatch to patron? [accurate/partial/none]: "
)


def _ask_dispatch(state: SeasonState, phase: str, io: _IO,
                  full_claims: Dict[str, Any],
                  partial_claims: Optional[Dict[str, Any]] = None) -> None:
    """Ask player how to report this phase; update belief_db accordingly."""
    choice = io.input(_DISPATCH_PROMPT).strip().lower()
    if choice == 'none':
        io.print("  (No dispatch sent — patron learns nothing of this phase.)")
        return
    if choice == 'partial':
        claims = partial_claims if partial_claims is not None else {
            k: v for k, v in full_claims.items() if k != 'casualties'
        }
        conf = 0.70
    else:
        # accurate or any unrecognised input defaults to accurate
        claims = full_claims
        conf = 0.90

    state.belief_db.receive_dispatch(phase, claims, conf)
    io.print(f"  Rider dispatched ({choice}, confidence {conf:.0%}).")


# ------------------------------------------------------------------
# Operations

def _op_siege(state: SeasonState, io: _IO) -> None:
    """Run the Harfleur siege. Decision 2: wait or storm."""
    if state.siege_result is not None:
        io.print("  (Harfleur already reduced.)")
        return

    io.print()
    io.print("--- Siege of Harfleur ---")

    # Decision 2: siege tactic
    tactic = io.input(
        "Wait for terms or press for storm? [wait/storm]: "
    ).strip().lower()
    if tactic not in ('wait', 'storm'):
        tactic = 'wait'
    state.siege_tactic = tactic

    scn = harfleur()
    if tactic == 'storm':
        # Lower the storm threshold: commander presses for an assault sooner
        scn = dict(scn, storm_threshold=0.15)

    tr = Trace(phase='siege', scenario='harfleur', seed=state.seed)
    result = run_siege(scn, state.seed, trace=tr)
    state.siege_result = result
    state.trace_phases.append(tr)
    state.elapsed(result['day'])

    vocab = state.commission.culture['doctrine_vocab']['victory_terms']
    outcome_label = vocab.get(result['outcome'], result['outcome'])
    io.print(f"  Harfleur {outcome_label} on day {result['day']}.")
    io.print(f"  Besieger dead: {result['dead']:,}  sick: {result['sick']:,}  "
             f"(unfit frac: {result['unfit_frac']:.1%})")

    full_claims = {
        'outcome': result['outcome'],
        'day': result['day'],
        'casualties': result['dead'],
    }
    partial_claims = {
        'outcome': result['outcome'],
        'day': result['day'],
    }
    _ask_dispatch(state, 'siege', io, full_claims, partial_claims)


def _op_march(state: SeasonState, io: _IO) -> None:
    """Run the Agincourt march. Decision 3: normal/push/rest."""
    if state.march_result is not None:
        io.print("  (March already completed.)")
        return

    io.print()
    io.print("--- March to Agincourt ---")

    # Decision 3: march pace
    pace = io.input(
        "Set march pace [normal/push/rest]: "
    ).strip().lower()
    if pace not in ('normal', 'push', 'rest'):
        pace = 'normal'
    state.march_pace = pace

    # Build march scenario; chain from siege if available
    if state.siege_result is not None:
        march_scn = siege_to_march(state.siege_result, harfleur(), agincourt_march())
    else:
        march_scn = agincourt_march()

    if pace == 'push':
        # Increase pace by 20 %, raises fatigue; men arrive sooner but more tired
        march_scn = dict(march_scn, pace=march_scn.get('pace', 15.5) * 1.20,
                         fat0=min(1.0, march_scn.get('fat0', 0.20) + 0.05))
    elif pace == 'rest':
        # One extra rest day; arrive slightly less fatigued
        march_scn = dict(march_scn,
                         rest_every=max(1, march_scn.get('rest_every', 0) or 4),
                         fat0=max(0.0, march_scn.get('fat0', 0.20) - 0.05))

    tr = Trace(phase='march', scenario='agincourt_march', seed=state.seed)
    result = run_march(march_scn, state.seed, trace=tr)
    state.march_result = result
    state.trace_phases.append(tr)
    state.elapsed(result['days'])

    status = "arrived" if result['arrived'] else "did not arrive"
    io.print(f"  Army {status} in {result['days']} days.")
    io.print(f"  Effective: {result['effective']:,}  Fatigue: {result['fatigue']:.1%}  "
             f"Stock remaining: {result['stock_days']:.1f} days")

    full_claims = {
        'arrived': result['arrived'],
        'day': result['days'],
        'fatigue': round(result['fatigue'], 2),
        'casualties': result.get('dead', 0) + result.get('strag', 0),
    }
    partial_claims = {
        'arrived': result['arrived'],
        'day': result['days'],
    }
    _ask_dispatch(state, 'march', io, full_claims, partial_claims)


def _op_battle(state: SeasonState, io: _IO) -> None:
    """Run the Agincourt battle. Decision 4: engage or withdraw."""
    if state.battle_result is not None:
        io.print("  (Battle already fought.)")
        return

    io.print()
    io.print("--- Battle of Agincourt ---")

    # Decision 4: engage or withdraw
    choice = io.input(
        "Engage the French array or withdraw? [engage/withdraw]: "
    ).strip().lower()
    if choice not in ('engage', 'withdraw'):
        choice = 'engage'
    state.battle_choice = choice

    if choice == 'withdraw':
        io.print("  The army turns aside; no battle is joined.")
        state.battle_result = {'win': -1, 'withdrew': True,
                               's': [{}, {}]}
        # Patron learns of the withdrawal via dispatch
        _ask_dispatch(state, 'battle', io,
                      full_claims={'won': False, 'withdrew': True},
                      partial_claims={'won': False})
        return

    # Build battle scenario; chain from march if available
    if state.march_result is not None:
        battle_scn = march_to_battle(state.march_result, agincourt(), rest_nights=1)
    else:
        battle_scn = agincourt()
    battle_scn['marching_side'] = 0

    tr = Trace(phase='battle', scenario='agincourt', seed=state.seed)
    result = Battle(battle_scn, state.seed, trace=tr).run()
    state.battle_result = result
    state.trace_phases.append(tr)

    winner = {0: 'English', 1: 'French'}.get(result['win'], 'unknown')
    io.print(f"  Battle concluded: {winner} won.")
    s0, s1 = result['s'][0], result['s'][1]
    io.print(f"  English dead: {s0['dead']:,}  French dead: {s1['dead']:,}")

    won = (result['win'] == 0)
    full_claims = {
        'won': won,
        'casualties': s0['dead'],
        'enemy_dead': s1['dead'],
    }
    partial_claims = {'won': won}
    _ask_dispatch(state, 'battle', io, full_claims, partial_claims)


_OPERATIONS_HELP = """
Available commands:
  siege     — besiege Harfleur (decision: wait for terms or storm?)
  march     — march to Agincourt (decision: normal / push / rest?)
  battle    — engage the French army (decision: engage or withdraw?)
  status    — show elapsed days and operation results so far
  done      — conclude operations and proceed to audit
  help      — show this message
"""


def _print_status(state: SeasonState, io: _IO) -> None:
    io.print(f"  Season day: {state.day} / {state.commission.strings['deadline_days']}")
    if state.siege_result:
        io.print(f"  Siege:  {state.siege_result['outcome']} day {state.siege_result['day']}")
    if state.march_result:
        io.print(f"  March:  {'arrived' if state.march_result['arrived'] else 'failed'} "
                 f"day {state.march_result['days']}")
    if state.battle_result:
        win = state.battle_result.get('win')
        io.print(f"  Battle: {'English' if win == 0 else 'French' if win == 1 else 'withdrew'}")


def _operations_phase(state: SeasonState, io: _IO) -> None:
    io.print()
    io.print("=" * 55)
    io.print("  OPERATIONS")
    io.print("=" * 55)
    io.print("  Type a command ('help' for list).")
    io.print()

    while not state.done:
        deadline = state.commission.strings['deadline_days']
        if state.day >= deadline:
            io.print(f"  Deadline reached ({state.day} days). Operations close.")
            break

        raw = io.input("> ").strip().lower()
        cmd = raw.split()[0] if raw else ''

        if cmd == 'siege':
            _op_siege(state, io)
        elif cmd == 'march':
            _op_march(state, io)
        elif cmd == 'battle':
            _op_battle(state, io)
        elif cmd == 'status':
            _print_status(state, io)
        elif cmd in ('done', 'quit', 'q'):
            io.print("  Operations concluded.")
            state.done = True
        elif cmd == 'help':
            io.print(_OPERATIONS_HELP)
        elif cmd == '':
            pass
        else:
            io.print(f"  Unknown command '{raw}'. Type 'help' for list.")


# ------------------------------------------------------------------
# Audit

def _audit_phase(state: SeasonState, io: _IO) -> None:
    io.print()
    io.print("=" * 55)
    io.print("  AUDIT")
    io.print("=" * 55)
    io.print(f"  {state.commission.patron} reads the dispatches.")
    io.print()

    if state.trace_phases:
        state.composed_trace = compose_traces(state.trace_phases)
        ts = trace_to_summary(state.composed_trace)
    else:
        ts = {}

    # Patron evaluates from belief_db (not from trace)
    mission_believed = patron_believes_success(state.commission.mission,
                                               state.belief_db)
    mission_actual = evaluate_mission(state.commission.mission, ts)

    # Detailed audit findings
    findings = state.belief_db.audit(ts)
    if findings:
        io.print(f"  {'Claim':<25} {'Believed':<18} {'Actual':<18} {'Match'}")
        io.print("  " + "-" * 70)
        for key, f in findings.items():
            b = str(f['believed'])
            a = str(f['actual']) if f['actual'] is not None else '(unknown)'
            m = _match_glyph(f['match'])
            io.print(f"  {key:<25} {b:<18} {a:<18} {m}")
    else:
        io.print("  No dispatches received — patron has no account of operations.")
    io.print()

    # Patron's verdict on mission
    mission_spec = MISSIONS.get(state.commission.mission, {})
    obj_label = mission_spec.get('objective_label', state.commission.mission)

    if mission_believed:
        io.print(f"  Patron believes: {obj_label} — ACHIEVED.")
    else:
        io.print(f"  Patron believes: {obj_label} — not achieved.")

    if mission_actual != mission_believed:
        io.print("  (The trace tells a different story — patron does not know.)")

    # Adjust patron favor
    qp = state.quarter_policy
    qc = state.commission.culture['quarter_customs'].get(qp, {})
    favor_delta = qc.get('patron_favor_mod', 0.0)
    if mission_believed:
        favor_delta += 0.15
    else:
        favor_delta -= 0.10

    state.patron_favor = max(0.0, min(1.0, state.patron_favor + favor_delta))


def _match_glyph(match) -> str:
    if match is True:
        return 'match'
    if match is False:
        return 'DIFFER'
    return '—'


# ------------------------------------------------------------------
# Winter court

def _winter_court_phase(state: SeasonState, io: _IO) -> None:
    io.print()
    io.print("=" * 55)
    io.print("  WINTER COURT")
    io.print(f"  {state.commission.culture['career']['winter_court_venue']}")
    io.print("=" * 55)
    io.print()

    patron = state.commission.patron
    favor = state.patron_favor
    career = state.commission.culture['career']
    thresholds = career['credit_thresholds']
    favor_labels = state.commission.culture['doctrine_vocab']['favor_labels']

    # Determine credit level from patron_favor
    credit_label = _credit_label(favor, thresholds, favor_labels)

    io.print(f"  {patron} receives your account at court.")
    io.print()

    # Credit/blame scene
    _print_court_scene(state, io, credit_label, favor)

    # Ransoms (if any prisoners taken in battle)
    _print_ransoms(state, io, career)

    # Next commission
    io.print()
    if favor >= thresholds.get('favor', 0.60):
        io.print(f"  You are offered a commission for the next season.")
    elif favor >= thresholds.get('neutral', 0.40):
        io.print(f"  Your service is noted. A commission may come — in time.")
    else:
        io.print(f"  {patron} is silent on the matter of next season.")

    io.print()
    io.print(f"  Season closed. Patron favor: {favor:.0%}  [{credit_label}]")


def _print_court_scene(state: SeasonState, io: _IO,
                       credit_label: str, favor: float) -> None:
    patron = state.commission.patron
    mission = state.commission.mission
    mission_spec = MISSIONS.get(mission, {})
    obj_label = mission_spec.get('objective_label', mission)

    believed_success = patron_believes_success(mission, state.belief_db)
    qp = state.quarter_policy
    qc = state.commission.culture['quarter_customs'].get(qp, {})

    if credit_label in ('acclaim', 'favor'):
        io.print(f"  {patron} commends the {obj_label}.")
        if qp == 'strict':
            io.print(f"  The towns speak well of your quarter — this is noted.")
        elif qp == 'free_rein':
            io.print(f"  Some murmur of excess in the quarter, but the outcome speaks.")
    elif credit_label == 'neutral':
        io.print(f"  {patron} acknowledges the season's service.")
        if not believed_success:
            io.print(f"  The {obj_label} falls short of the commission's terms.")
    else:
        io.print(f"  {patron} is displeased.")
        if not believed_success:
            io.print(f"  The {obj_label} was not achieved by the patron's account.")
        if qp == 'free_rein':
            io.print(f"  Complaints of excess quarter have reached the court.")

    if qc.get('note'):
        io.print(f"  [{qc['note']}]")


def _print_ransoms(state: SeasonState, io: _IO, career: Dict) -> None:
    if state.battle_result and state.battle_result.get('win') == 0:
        # English victory → prisoners taken
        fr_dead = state.battle_result['s'][1].get('dead', 0)
        # Crude estimate: ~10 % of French dead were captured (noble prisoners)
        prisoners = max(1, fr_dead // 10)
        ransom_share = career.get('ransom_share', 0.33)
        io.print()
        io.print(f"  Prisoners: {prisoners} notable men-at-arms taken.")
        io.print(f"  Crown's ransom claim ({ransom_share:.0%}) deducted from your quarter.")


# ------------------------------------------------------------------
# Credit label lookup

def _credit_label(favor: float, thresholds: Dict, labels: List[str]) -> str:
    ordered = [
        ('acclaim',  thresholds.get('acclaim',  0.80), labels[4] if len(labels) > 4 else 'acclaim'),
        ('favor',    thresholds.get('favor',    0.60), labels[3] if len(labels) > 3 else 'favor'),
        ('neutral',  thresholds.get('neutral',  0.40), labels[2] if len(labels) > 2 else 'neutral'),
        ('cold',     thresholds.get('cold',     0.20), labels[1] if len(labels) > 1 else 'cold'),
        ('censure',  thresholds.get('censure',  0.00), labels[0] if labels else 'censure'),
    ]
    for _, threshold, label in ordered:
        if favor >= threshold:
            return label
    return ordered[-1][2]


# ------------------------------------------------------------------
# Public entry point

def run_season(culture_name: str = 'harfleur_1415', seed: int = 0,
               auto_commands: Optional[List[str]] = None) -> SeasonState:
    """Run one interactive season and return the final SeasonState.

    If auto_commands is supplied, the season runs non-interactively (for tests).
    """
    # Load culture
    module = importlib.import_module(f"core.cultures.{culture_name}")
    culture = module.CULTURE

    rng = np.random.default_rng(seed)
    commission = generate_commission(culture, rng)

    io: _IO = _MockIO(auto_commands) if auto_commands is not None else _IO()
    state = SeasonState(commission, seed)

    # ------------------------------------------------------------------
    # Muster phase
    io.print()
    io.print("=" * 55)
    io.print(f"  COMMISSION OF HARFLEUR, {culture['era'].upper()}")
    io.print("=" * 55)
    io.print()
    io.print(muster_summary(commission))
    io.print()
    io.print("  Strings:")
    io.print(f"    Deadline:       {commission.strings['deadline_days']} days")
    io.print(f"    Quarter policy: {commission.strings['quarter_policy']} (negotiable)")
    io.print()

    # Decision 1: quarter policy
    policy_raw = io.input(
        "Choose quarter policy [strict/liberal/free_rein]: "
    ).strip().lower()
    if policy_raw in ('strict', 'liberal', 'free_rein'):
        apply_quarter_policy(commission, policy_raw)
    else:
        io.print(f"  (Unrecognised policy '{policy_raw}'; keeping 'liberal'.)")
    state.quarter_policy = commission.strings['quarter_policy']
    qc = culture['quarter_customs'][state.quarter_policy]
    io.print(f"  Quarter policy set to '{state.quarter_policy}': {qc['note']}")

    # ------------------------------------------------------------------
    # Operations phase
    _operations_phase(state, io)

    # ------------------------------------------------------------------
    # Audit
    _audit_phase(state, io)

    # ------------------------------------------------------------------
    # Winter court
    _winter_court_phase(state, io)

    return state
