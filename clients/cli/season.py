"""MARCHLAND CLI: interactive season loop (M3/M4/M7.A).

Usage:
    python -m clients.cli season [--culture harfleur_1415] [--seed N]

One full campaign season: arrival → operations → audit → winter court.
The player makes at least 4 meaningful decisions; the patron's winter court
assessment is drawn from their belief_db (dispatches only), not the trace.

M4 additions:
  - StationState tracks the commander's position (CAMP / HILL / KNOT / FRONT_RANK)
  - PendingOrder models dispatch latency for orders issued from CAMP
  - 'station <dest>' command moves the commander, paying travel time and lottery
  - 'wait [N]' command advances the season clock, processing matured orders
  - 'table' command prints the campaign Table at any time
  - After each completed operation the Table is shown automatically

M7.A additions (Addendum Y — scene-based event-driven turns):
  - Command begins by ARRIVAL at camp, not by muster summons. The opening scene
    stars a subordinate briefing from their (fallible, divergent) belief DB.
  - 'hold' command: advance to the NEXT DECISION-POINT EVENT at current station.
    Time compresses in the cut — no fixed-interval ticking surfaced to the player.
  - 'move <dest>' command: alias for station-change; transit time passes and the
    player arrives with a DIFFERENT vantage and belief DB.
  - Issuing an order and advancing time are now SEPARATE ACTS. An order pushes
    onto the in-flight queue; it does NOT advance the clock. The player then
    chooses hold (news arrives at this station) or move (ride to a new vantage).
  - Decision-point events: officer_requests_orders, contact_report,
    order_outcome_lands, deadline_approaching, sentiment_threshold.
    The loop runs until one of these fires, then renders the scene.
  - M7.A.4: every scene consequence traces to a sim event (not a script constant).

Inject 'auto_commands' for non-interactive/test use.  In auto mode, dispatch
latency is bypassed (instant_orders=True) so tests are not affected by time
mechanics.
"""
import sys
import importlib
import numpy as np
from dataclasses import dataclass, field
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
from core.stations import Station, STATIONS, StationState
from clients.cli.inspect import (
    Inspector, captain_eye, muster_hint, dispatch as inspect_dispatch,
)
from core.scenarios.harfleur import harfleur
from core.scenarios.marches import agincourt_march
from core.scenarios.agincourt import agincourt
from clients.cli.table import render_table


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
# Pending order

@dataclass
class PendingOrder:
    """An order queued for dispatch-latency delivery."""
    command: str          # the raw command string that was deferred
    eta_day: int          # season day on which the order arrives at the cohort
    label: str            # human-readable description shown in the Table


# ------------------------------------------------------------------
# Season state

class SeasonState:
    """Holds all mutable season state; passed between phases."""

    def __init__(self, commission: Commission, seed: int,
                 instant_orders: bool = False):
        self.commission = commission
        self.seed = seed
        self.belief_db = BeliefDB()
        self.inspector = Inspector()
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

        # M4 additions
        self.station_state: StationState = StationState()
        self.pending_orders: List[PendingOrder] = []
        # instant_orders=True bypasses dispatch latency (auto_commands / test mode)
        self.instant_orders: bool = instant_orders

        # M7.A: decision-point event queue and scene log
        # Each entry: (day, event_type, description)
        # event_types: officer_requests_orders, contact_report, order_outcome_lands,
        #              deadline_approaching, sentiment_threshold, dawn_before_battle
        self.decision_events: List[tuple] = []
        self.scene_log: List[str] = []   # M7.A.4: all scene outcomes (for VN discipline test)

    def elapsed(self, days: int):
        self.day += days
        # M7.A.1: check deadline decision-point
        deadline = self.commission.strings['deadline_days']
        if self.day >= deadline - 3 and not any(
            e[1] == 'deadline_approaching' for e in self.decision_events
        ):
            self.decision_events.append(
                (self.day, 'deadline_approaching',
                 f"Day {self.day}: deadline is {deadline - self.day} days away.")
            )

    def record_decision_event(self, event_type: str, description: str) -> None:
        """M7.A.1: register a decision-point event in the queue."""
        self.decision_events.append((self.day, event_type, description))

    def record_scene_outcome(self, outcome: str) -> None:
        """M7.A.4: log a scene outcome. Used to verify VN discipline (no scripted outcomes)."""
        self.scene_log.append(f"day={self.day} station={self.station.value}: {outcome}")

    @property
    def station(self) -> Station:
        return self.station_state.station

    def _queue_or_run(self, command: str, label: str, run_fn) -> bool:
        """Either run immediately or queue as a PendingOrder.

        Returns True if the command ran immediately, False if queued.
        """
        latency = 0 if self.instant_orders else self.station_state.latency_days
        if latency == 0:
            run_fn()
            return True
        eta = self.day + latency
        self.pending_orders.append(PendingOrder(command=command, eta_day=eta, label=label))
        return False

    def _flush_matured_orders(self, io: '_IO') -> None:
        """Execute any pending orders whose ETA has arrived."""
        still_pending = []
        for po in self.pending_orders:
            if self.day >= po.eta_day:
                io.print(f"  [Order delivered] {po.label}")
                self._dispatch_command(po.command, io)
            else:
                still_pending.append(po)
        self.pending_orders = still_pending

    def _dispatch_command(self, cmd: str, io: '_IO') -> None:
        """Run a deferred command that has just been delivered."""
        if cmd == 'siege':
            _run_siege_op(self, io)
        elif cmd == 'march':
            _run_march_op(self, io)
        elif cmd == 'battle':
            _run_battle_op(self, io)


# ------------------------------------------------------------------
# Quarter policy prompt helpers (extracted for testability)

def _print_quarter_options(io: _IO) -> None:
    """The three quarter policies, stated as worldly consequences (no figures)."""
    io.print("  strict     The men will grumble at the tight rein — but your patron")
    io.print("             will hear you kept good order, and think the better of you.")
    io.print("  liberal    The custom of the age. Contribution taken, not plundered.")
    io.print("  free_rein  The men will love you for it. Your patron will not.")


def _ask_quarter_policy(commission: 'Commission', culture: Dict, io: _IO) -> str:
    """Prompt for quarter policy, redisplaying options on invalid input.

    Returns the chosen policy string.
    """
    io.print("  Quarter policy options:")
    _print_quarter_options(io)
    io.print()
    while True:
        raw = io.input("Choose quarter policy [strict/liberal/free_rein]: ").strip().lower()
        if raw in ('strict', 'liberal', 'free_rein'):
            apply_quarter_policy(commission, raw)
            return raw
        if not raw:
            return commission.strings['quarter_policy']
        io.print("  (Not recognised — choose from:)")
        _print_quarter_options(io)
        io.print()


# ------------------------------------------------------------------
# Dispatch helpers

_DISPATCH_PROMPT = (
    "Send dispatch to patron? [accurate/partial/none]: "
)

_DISPATCH_EXPLANATION = """\
  Dispatch options:
    accurate → all claims sent, 90% confidence (casualties included)
    partial  → non-casualty claims only; battle partial omits outcome (70% confidence)
    none     → patron learns nothing of this phase"""


def _ask_dispatch(state: SeasonState, phase: str, io: _IO,
                  full_claims: Dict[str, Any],
                  partial_claims: Optional[Dict[str, Any]] = None) -> None:
    """Ask player how to report this phase; update belief_db accordingly."""
    io.print(_DISPATCH_EXPLANATION)
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
# Core operation runners (no IO prompts — called after latency resolves)

def _run_siege_op(state: SeasonState, io: _IO) -> None:
    """Execute the siege operation. Called immediately or after latency."""
    if state.siege_result is not None:
        return   # already done

    tactic = state.siege_tactic or 'wait'
    scn = harfleur()
    if tactic == 'storm':
        scn = dict(scn, storm_threshold=0.15)

    tr = Trace(phase='siege', scenario='harfleur', seed=state.seed)
    result = run_siege(scn, state.seed, trace=tr)
    state.siege_result = result
    state.trace_phases.append(tr)
    state.elapsed(result['day'])

    vocab = state.commission.culture['doctrine_vocab']['victory_terms']
    outcome_label = vocab.get(result['outcome'], result['outcome'])
    io.print(f"  Harfleur {outcome_label} on day {result['day']}.")
    # The cost, spoken in the world; the figures go behind 'explain'/'ledger'.
    if result['unfit_frac'] >= 0.25:
        io.print("  The siege came dear without a blow struck: the camp sickness")
        io.print("  thinned the host, and many will not be fit to march.")
    elif result['dead'] or result['sick']:
        io.print("  Some were lost to the flux in the wet camps, but the host holds together.")
    state.inspector.set_explain("the siege", [
        f"outcome {result['outcome']} on day {result['day']} (siege clock: disease, supply, honour)",
        f"besieger dead {result['dead']:,}; sick {result['sick']:,}; unfit fraction {result['unfit_frac']:.1%}",
        "the unfit fraction carries forward as starting fatigue for the march",
    ])
    if state.inspector.ledger:
        state.inspector.render_explain(io)

    # Station-aware observation: HILL/KNOT can see results directly
    if state.station in (Station.HILL, Station.KNOT):
        source = 'sightlines' if state.station == Station.KNOT else 'landscape'
        state.belief_db.observe('siege', {
            'outcome': result['outcome'],
            'day': result['day'],
        }, source=source)

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
    render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)


def _run_march_op(state: SeasonState, io: _IO) -> None:
    """Execute the march operation. Called immediately or after latency."""
    if state.march_result is not None:
        return

    pace = state.march_pace or 'normal'

    if state.siege_result is not None:
        march_scn = siege_to_march(state.siege_result, harfleur(), agincourt_march())
    else:
        march_scn = agincourt_march()

    if pace == 'push':
        march_scn = dict(march_scn, pace=march_scn.get('pace', 15.5) * 1.20,
                         fat0=min(1.0, march_scn.get('fat0', 0.20) + 0.05))
    elif pace == 'rest':
        march_scn = dict(march_scn,
                         rest_every=max(1, march_scn.get('rest_every', 0) or 4),
                         fat0=max(0.0, march_scn.get('fat0', 0.20) - 0.05))

    tr = Trace(phase='march', scenario='agincourt_march', seed=state.seed)
    result = run_march(march_scn, state.seed, trace=tr)
    state.march_result = result
    state.trace_phases.append(tr)
    state.elapsed(result['days'])

    if result['arrived']:
        io.print(f"  The host came through to Agincourt in {result['days']} days.")
    else:
        io.print(f"  After {result['days']} days the host had not made Agincourt — the road beat it.")
    weary = result['fatigue'] > 0.30
    io.print("  They came to the field footsore"
             + (" and hard-used — they will not be at their best." if weary else ", but in order."))
    state.inspector.set_explain("the march", [
        f"arrived={result['arrived']} in {result['days']} days; {result['effective']:,} effectives came through",
        f"fatigue on arrival {result['fatigue']:.1%}; it amplifies the opening hazard of the battle (fat_amp=2.0)",
        f"supply remaining {result['stock_days']:.1f} days",
    ])
    if state.inspector.ledger:
        state.inspector.render_explain(io)

    if state.station in (Station.HILL, Station.KNOT):
        source = 'sightlines' if state.station == Station.KNOT else 'landscape'
        state.belief_db.observe('march', {
            'arrived': result['arrived'],
            'day': result['days'],
        }, source=source)

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
    render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)


def _run_battle_op(state: SeasonState, io: _IO) -> None:
    """Execute the battle operation. Called immediately or after latency."""
    if state.battle_result is not None:
        return

    choice = state.battle_choice or 'engage'
    if choice == 'withdraw':
        io.print("  The army turns aside; no battle is joined.")
        state.battle_result = {'win': -1, 'withdrew': True, 's': [{}, {}]}
        _ask_dispatch(state, 'battle', io,
                      full_claims={'won': False, 'withdrew': True},
                      partial_claims={'won': False})
        render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)
        return

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
    s0, s1 = result['s'][0], result['s'][1]
    if result['win'] == 0:
        io.print("  The day is yours. The French array broke and was ridden down;")
        io.print("  the dead lay thick, and far more of theirs than of ours.")
    elif result['win'] == 1:
        io.print("  The day is lost. Your line gave way, and the field is theirs.")
    else:
        io.print("  The fight was broken off undecided.")
    state.inspector.set_explain("the battle", [
        f"winner: {winner}",
        f"English dead {s0['dead']:,}; French dead {s1['dead']:,}",
        "casualties concentrate in the pursuit of the broken side (casualties live in the pursuit)",
    ])
    if state.inspector.ledger:
        state.inspector.render_explain(io)

    if state.station in (Station.HILL, Station.KNOT, Station.FRONT_RANK):
        source = {
            Station.KNOT: 'sightlines',
            Station.HILL: 'landscape',
            Station.FRONT_RANK: 'nearby_units',
        }[state.station]
        state.belief_db.observe('battle', {
            'won': (result['win'] == 0),
        }, source=source)

    won = (result['win'] == 0)
    full_claims = {
        'won': won,
        'casualties': s0['dead'],
        'enemy_dead': s1['dead'],
    }
    partial_claims = {'won': won}
    _ask_dispatch(state, 'battle', io, full_claims, partial_claims)
    render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)


# ------------------------------------------------------------------
# Operations: player-facing command handlers (with prompts)

def _op_siege(state: SeasonState, io: _IO) -> None:
    """Handle the 'siege' command."""
    if state.siege_result is not None:
        io.print("  (Harfleur already reduced.)")
        return
    if any(po.command == 'siege' for po in state.pending_orders):
        io.print("  (Siege order already dispatched — rider en route.)")
        return

    io.print()
    io.print("--- Siege of Harfleur ---")

    tactic = io.input(
        "Wait for terms or press for storm? [wait/storm]: "
    ).strip().lower()
    if tactic not in ('wait', 'storm'):
        tactic = 'wait'
    state.siege_tactic = tactic

    def _do_siege():
        _run_siege_op(state, io)

    ran = state._queue_or_run('siege', 'besiege Harfleur', _do_siege)
    if not ran:
        latency = state.station_state.latency_days
        io.print(f"  Order dispatched from {state.station_state.spec.label}. "
                 f"Rider arrives in {latency} days (ETA: day {state.day + latency}).")
        render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)


def _op_march(state: SeasonState, io: _IO) -> None:
    """Handle the 'march' command."""
    if state.march_result is not None:
        io.print("  (March already completed.)")
        return
    if any(po.command == 'march' for po in state.pending_orders):
        io.print("  (March order already dispatched — rider en route.)")
        return

    io.print()
    io.print("--- March to Agincourt ---")

    pace = io.input(
        "Set march pace [normal/push/rest]: "
    ).strip().lower()
    if pace not in ('normal', 'push', 'rest'):
        pace = 'normal'
    state.march_pace = pace

    def _do_march():
        _run_march_op(state, io)

    ran = state._queue_or_run('march', 'march to Agincourt', _do_march)
    if not ran:
        latency = state.station_state.latency_days
        io.print(f"  Order dispatched from {state.station_state.spec.label}. "
                 f"Rider arrives in {latency} days (ETA: day {state.day + latency}).")
        render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)


def _op_battle(state: SeasonState, io: _IO) -> None:
    """Handle the 'battle' command."""
    if state.battle_result is not None:
        io.print("  (Battle already fought.)")
        return
    if any(po.command == 'battle' for po in state.pending_orders):
        io.print("  (Battle order already dispatched — rider en route.)")
        return

    io.print()
    io.print("--- Battle of Agincourt ---")

    choice = io.input(
        "Engage the French array or withdraw? [engage/withdraw]: "
    ).strip().lower()
    if choice not in ('engage', 'withdraw'):
        choice = 'engage'
    state.battle_choice = choice

    def _do_battle():
        _run_battle_op(state, io)

    ran = state._queue_or_run('battle', 'engage the French', _do_battle)
    if not ran:
        latency = state.station_state.latency_days
        io.print(f"  Order dispatched from {state.station_state.spec.label}. "
                 f"Rider arrives in {latency} days (ETA: day {state.day + latency}).")
        render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)


def _op_station(state: SeasonState, io: _IO, dest_name: str) -> None:
    """Handle the 'station <dest>' command."""
    # Normalise destination
    dest_map = {
        'camp':       Station.CAMP,
        'hill':       Station.HILL,
        'knot':       Station.KNOT,
        'front':      Station.FRONT_RANK,
        'front_rank': Station.FRONT_RANK,
        'frontrank':  Station.FRONT_RANK,
    }
    dest = dest_map.get(dest_name.lower())
    if dest is None:
        valid = ', '.join(dest_map.keys())
        io.print(f"  Unknown station '{dest_name}'. Valid: {valid}")
        return

    current = state.station_state.station
    if dest == current:
        io.print(f"  Already at {STATIONS[current].label}.")
        return

    rng = np.random.default_rng(state.seed + state.day * 31)
    event = state.station_state.move_to(dest, rng, state.day)

    state.elapsed(event['cost_days'])
    spec = STATIONS[dest]
    io.print(f"  Moved from {event['from']} to {event['to']} "
             f"({event['cost_days']} day(s) travel).")

    if event['hit']:
        io.print(f"  ! Leader-risk lottery fired en route — commander takes a wound.")
        io.print(f"    (Injuries this season: {state.station_state.lottery_injuries})")
        state.patron_favor = max(0.0, state.patron_favor - 0.05)

    io.print(f"  Now at {spec.label}: {spec.description}")
    render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)


def _op_wait(state: SeasonState, io: _IO, days_str: str) -> None:
    """Handle the 'wait [N]' command — advance N days and flush matured orders."""
    try:
        days = max(1, int(days_str)) if days_str.strip() else 1
    except ValueError:
        days = 1

    io.print(f"  Waiting {days} day(s)...")
    state.elapsed(days)
    state.station_state.days_at_station += days
    state._flush_matured_orders(io)
    render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)


def _op_hold(state: SeasonState, io: _IO) -> None:
    """M7.A.2: HOLD — advance to the next decision-point event at current station.

    Time compresses in the cut: the player waits at their current station
    while riders travel and the sim advances. The next scene renders when
    a decision-point event fires (order resolved, report arrives, etc.).
    """
    # Determine how far to advance: to the next matured order or 1 day
    if state.pending_orders:
        next_eta = min(po.eta_day for po in state.pending_orders)
        days_to_advance = max(1, next_eta - state.day)
        io.print(f"  Holding at {STATIONS[state.station].label} "
                 f"— advancing {days_to_advance} day(s) to next rider arrival...")
    else:
        days_to_advance = 1
        io.print(f"  Holding at {STATIONS[state.station].label} — advancing 1 day...")

    state.elapsed(days_to_advance)
    state.station_state.days_at_station += days_to_advance
    state._flush_matured_orders(io)

    # Surface any pending decision-point events
    unread_events = [e for e in state.decision_events if not getattr(e, '_shown', False)]
    for ev in unread_events:
        io.print(f"  [Decision point — {ev[1]}] {ev[2]}")

    render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)


def _op_move(state: SeasonState, io: _IO, dest_name: str) -> None:
    """M7.A.2: MOVE — ride to a new station (station change as deliberate time-spend).

    Transit time passes; the player arrives at the new vantage with a different
    belief DB. Any in-flight orders continue resolving on their own clock.
    The rider carrying your last order may already have arrived by the time you
    do — or may arrive after.
    """
    # Delegate to the existing station handler (same mechanics, different framing)
    _op_station(state, io, dest_name)


# ------------------------------------------------------------------
# Status / help

_OPERATIONS_HELP = """
Available commands:
  siege          — besiege Harfleur (decision: wait for terms or storm?)
  march          — march to Agincourt (decision: normal / push / rest?)
  battle         — engage the French army (decision: engage or withdraw?)
  hold           — M7.A: advance to next decision-point event at current station
  move <dest>    — M7.A: ride to a new station (CAMP/HILL/KNOT/FRONT_RANK)
  station <dest> — same as move; legacy command
  wait [N]       — advance N days (default 1); delivers queued orders
  table          — show the campaign Table
  status         — show elapsed days and operation results
  inspect <thing>— open the door on a cohort's or favor's figures
  explain        — why the last outcome went as it did
  ledger [on|off]— show figures alongside the prose (default off)
  done           — conclude operations and proceed to audit
  help [topic]   — list topics (no arg) or explain one

M7.A note: issuing an order (siege/march/battle) and advancing time (hold/move/wait)
are separate acts. An order goes into the in-flight queue immediately; time only
advances when you choose hold, move, or wait.
"""


def _print_status(state: SeasonState, io: _IO) -> None:
    io.print(f"  Season day: {state.day} / {state.commission.strings['deadline_days']}")
    io.print(f"  Station: {STATIONS[state.station].label}")
    if state.siege_result:
        io.print(f"  Siege:  {state.siege_result['outcome']} day {state.siege_result['day']}")
    if state.march_result:
        io.print(f"  March:  {'arrived' if state.march_result['arrived'] else 'failed'} "
                 f"day {state.march_result['days']}")
    if state.battle_result:
        win = state.battle_result.get('win')
        io.print(f"  Battle: {'English' if win == 0 else 'French' if win == 1 else 'withdrew'}")
    if state.pending_orders:
        io.print(f"  Pending: {len(state.pending_orders)} order(s) in transit")


def _operations_phase(state: SeasonState, io: _IO) -> None:
    io.print()
    io.print("=" * 55)
    io.print("  OPERATIONS")
    io.print("=" * 55)
    io.print("  Type a command ('help' for list).")
    io.print()

    # Show Table at the start of operations
    render_table(state.day, state.station_state, state.belief_db, state.pending_orders, io=io)

    while not state.done:
        deadline = state.commission.strings['deadline_days']
        if state.day >= deadline:
            io.print(f"  Deadline reached ({state.day} days). Operations close.")
            break

        # Flush any matured pending orders before reading next command
        state._flush_matured_orders(io)

        raw = io.input("> ").strip().lower()
        parts = raw.split()
        cmd = parts[0] if parts else ''
        arg = parts[1] if len(parts) > 1 else ''

        if cmd == 'siege':
            _op_siege(state, io)
        elif cmd == 'march':
            _op_march(state, io)
        elif cmd == 'battle':
            _op_battle(state, io)
        elif cmd == 'hold':
            # M7.A.2: HOLD — advance to next decision-point event
            _op_hold(state, io)
        elif cmd == 'move':
            # M7.A.2: MOVE — ride to new station (time-spend choice)
            if not arg:
                arg = io.input("Destination [camp/hill/knot/front_rank]: ").strip().lower()
            _op_move(state, io, arg)
        elif cmd == 'station':
            # Accept 'station knot' (arg inline) OR 'station' then read dest
            if not arg:
                arg = io.input("Destination station [camp/hill/knot/front_rank]: ").strip().lower()
            _op_station(state, io, arg)
        elif cmd == 'wait':
            _op_wait(state, io, arg)
        elif cmd == 'table':
            render_table(state.day, state.station_state, state.belief_db,
                         state.pending_orders, io=io)
        elif cmd == 'status':
            _print_status(state, io)
        elif cmd in ('inspect', 'explain', 'ledger'):
            inspect_dispatch(cmd, arg, state.commission, state.inspector, io)
        elif cmd in ('done', 'quit', 'q'):
            ops_incomplete = (
                state.siege_result is not None and state.march_result is None
            ) or (
                state.march_result is not None and state.battle_result is None
            )
            if ops_incomplete:
                if state.march_result is None:
                    io.print("  You have not yet marched or engaged. Close operations? [yes/no]:")
                else:
                    io.print("  You have not yet engaged in battle. Close operations? [yes/no]:")
                answer = io.input("> ").strip().lower()
                if answer not in ('yes', 'y'):
                    continue
            io.print("  Operations concluded.")
            state.done = True
        elif cmd == 'help':
            if arg:
                from clients.cli.help import show_help
                show_help(arg, io)
            else:
                io.print(_OPERATIONS_HELP)
                io.print(
                    "  For mechanic details: help march | help battle | help siege\n"
                    "  | help stations | help receipts | help dispatch | help trace | help table"
                )
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

    mission_believed = patron_believes_success(state.commission.mission,
                                               state.belief_db)
    mission_actual = evaluate_mission(state.commission.mission, ts)

    findings = state.belief_db.audit(ts)
    if findings:
        io.print(f"  {'Claim':<25} {'Believed':<18} {'Actual':<18} {'Match'}")
        io.print("  " + "-" * 70)
        for key, f in findings.items():
            b = str(f['believed'])
            a = str(f['actual']) if f['actual'] is not None else '(not in trace summary)'
            m = _match_glyph(f['match'])
            io.print(f"  {key:<25} {b:<18} {a:<18} {m}")
        if any(f['actual'] is None for f in findings.values()):
            io.print("  † claim has no trace analog — patron accepts as reported")
    else:
        io.print("  No dispatches received — patron has no account of operations.")
    io.print()

    mission_spec = MISSIONS.get(state.commission.mission, {})
    obj_label = mission_spec.get('objective_label', state.commission.mission)

    if mission_believed:
        io.print(f"  Patron believes: {obj_label} — ACHIEVED.")
    else:
        io.print(f"  Patron believes: {obj_label} — not achieved.")

    if mission_actual != mission_believed:
        io.print("  (The trace tells a different story — patron does not know.)")

    qp = state.quarter_policy
    qc = state.commission.culture['quarter_customs'].get(qp, {})
    quarter_delta = qc.get('patron_favor_mod', 0.0)
    mission_delta = 0.15 if mission_believed else -0.10

    base = state.patron_favor
    state.patron_favor = max(0.0, min(1.0, base + quarter_delta + mission_delta))
    # The arithmetic lives behind 'inspect favor' — not on the wall.
    state.inspector.set_favor(base, mission_delta, quarter_delta,
                              state.patron_favor, mission_believed)


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

    credit_label = _credit_label(favor, thresholds, favor_labels)

    io.print(f"  {patron} receives your account at court.")
    io.print()

    _print_court_scene(state, io, credit_label, favor)
    _print_ransoms(state, io, career)

    io.print()
    if favor >= thresholds.get('favor', 0.60):
        io.print(f"  You are offered a commission for the next season.")
    elif favor >= thresholds.get('neutral', 0.40):
        io.print(f"  Your service is noted. A commission may come — in time.")
    else:
        io.print(f"  {patron} is silent on the matter of next season.")

    # Standing, spoken in the world; the reckoning is behind 'inspect favor'.
    io.print()
    io.print(f"  The season is closed. In {patron}'s regard you stand as a "
             f"man of {credit_label}.")
    if state.inspector.ledger:
        io.print()
        state.inspector.render_favor(io)
    else:
        io.print("  (type 'inspect favor' to see the reckoning behind his regard)")


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

    # Siege tactic prose: storm vs wait differentiation
    if state.siege_result:
        siege_outcome = state.siege_result.get('outcome', '')
        if state.siege_tactic == 'storm' and siege_outcome == 'NEGOTIATED':
            io.print("  The storm was pressed but the garrison yielded on terms"
                     " — costly, but the place is taken.")
        elif state.siege_tactic == 'storm' and siege_outcome == 'STORMED_sack':
            io.print("  The place was taken by storm. The sack will trouble some at court.")

    if qc.get('note'):
        io.print(f"  [{qc['note']}]")


def _print_ransoms(state: SeasonState, io: _IO, career: Dict) -> None:
    if state.battle_result and state.battle_result.get('win') == 0:
        fr_dead = state.battle_result['s'][1].get('dead', 0)
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
# M7.A.3: Arrival-to-take-command opening scene

def _arrival_scene(commission: Commission, culture: Dict, io: _IO) -> None:
    """M7.A.3: Command begins by arriving at camp, not by receiving a summons.

    A subordinate (the camp sergeant-at-arms) briefs from their OWN belief DB:
    partial, contested, possibly stale. The opening question is always
    'wait for reinforcements or commit what we have?' — the real decision.
    The muster summary follows as supporting detail, not the opening act.

    This is the officer-AI showcase: the briefing officer may downplay a siege
    difficulty or oversell a threat, because they reason from their belief DB,
    not the trace. The player's first task is reading their own staff.
    """
    patron = commission.patron
    era = culture.get('era', '1415')

    io.print()
    io.print("=" * 55)
    io.print(f"  ARRIVAL AT CAMP — {era.upper()}")
    io.print("=" * 55)
    io.print()
    io.print(f"  You ride in with your guard at dusk.")
    io.print(f"  The camp sergeant-at-arms meets you at the tent.")
    io.print()

    # Subordinate briefing (from their belief DB — fallible)
    # The sergeant knows the army's composition but may not know current enemy state
    mission = commission.mission
    army_n = sum(c.get('n', 0) * 10 for c in commission.army_cohorts if isinstance(c, dict))
    army_n = army_n or commission.strings.get('army_size', 3000)

    io.print("  [SERGEANT'S BRIEFING — from camp dispatch, not ground truth]")
    io.print()
    io.print(f"  'The men are mustered, my lord. {army_n:,} effectives on roll'")
    io.print(f"  '— though the muster clerk's count runs a week old.'")
    io.print()

    if mission in ('siege',):
        io.print(f"  'Harfleur's garrison sent word they'll hold to the last.'")
        io.print(f"  'Our scouts say the walls are sound — but the scouts'")
        io.print(f"  'haven't been inside. I wouldn't stake my life on it.'")
    elif mission in ('escort', 'relief'):
        io.print(f"  'The road north is clear as of three days ago.'")
        io.print(f"  'Three days is a long time in enemy country.'")
    else:
        io.print(f"  'The enemy's dispositions are uncertain. Riders went out'")
        io.print(f"  'at dawn — we expect word tomorrow, God willing.'")

    io.print()
    io.print(f"  Deadline: {commission.strings['deadline_days']} days.")
    io.print(f"  Patron: {patron}")
    io.print()
    io.print(f"  The first decision is yours: commit now, or wait for clearer word.")
    io.print()


# ------------------------------------------------------------------
# Public entry point

def run_season(culture_name: str = 'harfleur_1415', seed: int = 0,
               auto_commands: Optional[List[str]] = None) -> 'SeasonState':
    """Run one interactive season and return the final SeasonState.

    If auto_commands is supplied, the season runs non-interactively (for tests)
    and dispatch latency is bypassed (instant_orders=True).
    """
    module = importlib.import_module(f"core.cultures.{culture_name}")
    culture = module.CULTURE

    rng = np.random.default_rng(seed)
    commission = generate_commission(culture, rng)

    instant = auto_commands is not None
    io: _IO = _MockIO(auto_commands) if auto_commands is not None else _IO()
    state = SeasonState(commission, seed, instant_orders=instant)

    # ------------------------------------------------------------------
    # M7.A.3: Arrival-to-take-command opening (replaces bare muster summary)
    _arrival_scene(commission, culture, io)

    # Muster details follow the arrival scene as supporting information —
    # a captain's eye on the men, not a spreadsheet. The figures live behind
    # 'inspect <cohort>' (and 'ledger on' for the grognard who wants them inline).
    io.print("=" * 55)
    io.print(f"  COMMISSION — you take the measure of your men")
    io.print("=" * 55)
    io.print(f"  From {commission.patron}. Mission: {commission.mission.upper()}.")
    io.print()
    for c in commission.army_cohorts:
        if not isinstance(c, dict):
            continue
        io.print(f"  {captain_eye(c)}")
        io.print(f"    {muster_hint(c)}")
    io.print()
    io.print("  (Every figure behind these men is a receipt — 'inspect <cohort>'")
    io.print("   opens the door, 'help receipts' states the doctrine, 'ledger on'")
    io.print("   keeps the figures alongside the prose.)")
    io.print()
    io.print(f"  Deadline: {commission.strings['deadline_days']} days.  "
             f"Quarter policy: {commission.strings['quarter_policy']} (negotiable).")
    io.print()

    # Decision 1: quarter policy
    _ask_quarter_policy(commission, culture, io)
    state.quarter_policy = commission.strings['quarter_policy']
    qc = culture['quarter_customs'][state.quarter_policy]
    io.print(f"  Quarter policy set to '{state.quarter_policy}': {qc['note']}")

    # M7.A.1: register first decision-point event
    state.record_decision_event('officer_requests_orders',
                                'Sergeant awaits your first operational order.')
    state.record_scene_outcome(f"arrival: commission={commission.mission}, "
                               f"army_size={commission.strings.get('army_size', '?')}")

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
