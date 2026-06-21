"""MARCHLAND core: officer model (M7.7) — decision function with trust/repertoire/meaning hooks.

Officers reason from their OWN belief DB — never from the trace. Their
mistakes come from bad information, not from pathfinding or scripted errors.

The decide() contract:
    decide(officer, standing_order, belief_db, repertoire, authority, trust) -> action

Where:
  standing_order — last dispatch that reached this officer (may be stale)
  belief_db      — what THIS officer perceives from THEIR station (never the trace)
  repertoire     — actions this officer's role can express (Addendum K)
  authority      — current authority (0–1); degrades with casualties/arrears
  trust          — viscosity of obedience (0=literal/safe, 1=initiative/interpret)

Battery coverage (M7.7 spec §4 — isolated tests via tests/test_officer.py):
  officer_open_flank        — exploits visible gap when trust ≥ threshold
  officer_suicidal_order    — refuses charge into suicidal density (majority of seeds)
  officer_stale_order       — acts on stale order; countermand arrives after the action
  officer_ambiguous_order   — interpretation biases toward belief state
  officer_cavalry_judgment  — cavalry refuses formed density (horse_solid threshold)
  officer_dead_repertoire   — dead officer cannot execute any action (empty repertoire)
  officer_honest_report     — report reflects belief DB; low trust shades bad news
  officer_initiative_vs_trust — high trust exploits flank monotonically more than low trust
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .belief_db import BeliefDB


# ---------------------------------------------------------------------------
# Order vocabulary

ORDER_TYPES = frozenset({
    'charge',               # immediate frontal assault
    'hold',                 # maintain position
    'advance',              # move forward when ready
    'withdraw',             # fall back (uncontrolled)
    'flank',                # envelop the enemy flank
    'reinforce',            # move to support another cohort
    'skirmish',             # harass but do not commit
    'fighting_withdrawal',  # controlled retreat under contact (Addendum K)
    'hold_then_wheel',      # hold until flank clears, then wheel inward (cavalry/veteran)
    'rout_wing_then_envelop',  # cavalry: rout opposing wing, return to hit rear
})

# ---------------------------------------------------------------------------
# Thresholds (Class D — institutional, not universal-body constants)

# Density at which an officer believes a direct charge is suicidal
SUICIDAL_FOE_DENSITY = 4.0   # D: officers with enough experience set this higher

# Minimum gap in foe coverage to trigger opportunistic advance (base; scaled by trust)
EXPLOITABLE_GAP_THRESHOLD = 0.2   # D: fraction of front with no foe coverage

# Dispatch ambiguity: below this confidence the officer may misread
DISPATCH_AMBIGUITY_THRESHOLD = 0.65   # D: confidence below this triggers interpretation

# Density at which cavalry balk (matches BATTLE_A['horse_solid'])
CAVALRY_FORMED_DENSITY = 3.0   # D: cavalry judgment threshold


# ---------------------------------------------------------------------------
# Decision result

@dataclass
class OfficerDecision:
    """Result of an officer processing an order through its belief DB."""
    order_received: str       # the order as dispatched
    order_executed: str       # what the officer actually does (may differ)
    rationale: str            # the officer's reasoning (cites belief DB)
    belief_state: Dict        # snapshot of the relevant belief entries used
    complied: bool            # True if executed == received


# ---------------------------------------------------------------------------
# Officer

@dataclass
class Officer:
    """A subordinate commander with their own partial-knowledge belief DB.

    Attributes
    ----------
    cohort_id     — which cohort this officer commands
    role          — 'flank_commander' | 'rearguard' | 'vanguard' | 'reserves' | etc.
    authority     — current authority (0–1); declines with casualties and pay arrears
    trust         — viscosity of obedience (0=literal/defers, 1=initiative/interprets)
    repertoire    — frozenset of ORDER_TYPES this officer can execute
    is_dead       — dead officer: no orders can be executed (Addendum K)
    mounted       — cavalry officer: applies horse-balk density judgment
    current_order — last order received (the "standing order")
    belief_db     — what this officer knows (diverges from trace and from HQ)
    """
    cohort_id: int
    role: str
    authority: float = 0.85
    trust: float = 0.70
    repertoire: frozenset = field(default_factory=lambda: frozenset(ORDER_TYPES))
    is_dead: bool = False
    mounted: bool = False
    current_order: Optional[Dict[str, Any]] = None
    belief_db: BeliefDB = field(default_factory=BeliefDB)

    # ------------------------------------------------------------------
    # Lifecycle

    def mark_dead(self) -> None:
        """Officer is down — effective repertoire becomes empty (Addendum K)."""
        self.is_dead = True

    def receive_order(self, order: Dict[str, Any]) -> None:
        """Rider arrives: update standing order."""
        self.current_order = order

    def degrade_authority(self, amount: float) -> None:
        """Reduce officer authority (pay arrears, casualties, defeat)."""
        self.authority = max(0.0, self.authority - amount)

    # ------------------------------------------------------------------
    # Core decision method

    def process_order(self, order: Dict[str, Any]) -> OfficerDecision:
        """Filter an incoming order through the officer's belief DB.

        Dead officers return hold regardless of order.
        Orders not in the officer's repertoire are gated.
        Otherwise, each order type has belief-mediated handling.
        """
        order_type = order.get('type', '')

        # Repertoire gate: dead officer cannot execute anything
        if self.is_dead:
            return OfficerDecision(
                order_received=order_type,
                order_executed='hold',
                rationale='Officer is down — no execution possible (repertoire empty).',
                belief_state={},
                complied=False,
            )

        # Repertoire gate: order not available to this officer's role
        if order_type not in self.repertoire:
            return OfficerDecision(
                order_received=order_type,
                order_executed='hold',
                rationale=(
                    f'Order {order_type!r} not in officer repertoire. '
                    'Holding — cannot substitute what was never learned.'
                ),
                belief_state={},
                complied=False,
            )

        if order_type not in ORDER_TYPES:
            return OfficerDecision(
                order_received=order_type,
                order_executed='hold',
                rationale='Unrecognised order type — defaulting to hold.',
                belief_state={},
                complied=False,
            )

        # Cavalry judgment: applies to mounted officers receiving charge/advance
        if self.mounted and order_type in ('charge', 'advance'):
            cav_decision = self._apply_cavalry_judgment(order_type)
            if cav_decision is not None:
                return cav_decision

        if order_type == 'charge':
            return self._process_charge(order)
        if order_type == 'advance':
            return self._process_advance(order)
        if order_type == 'flank':
            return self._process_flank(order)
        if order_type == 'fighting_withdrawal':
            return self._process_fighting_withdrawal(order)

        # All other orders: comply unless authority is critically low
        if self.authority < 0.2:
            return OfficerDecision(
                order_received=order_type,
                order_executed='hold',
                rationale=f'Authority too low ({self.authority:.2f}) to enforce {order_type!r}.',
                belief_state={},
                complied=False,
            )
        return OfficerDecision(
            order_received=order_type,
            order_executed=order_type,
            rationale='Order received; conditions consistent with execution.',
            belief_state={},
            complied=True,
        )

    def act_on_standing_order(self) -> OfficerDecision:
        """Execute the current standing order (may be stale).

        Battery target: officer_stale_order — the officer MUST act on the
        order it actually holds, even if a countermand was dispatched but
        hasn't arrived yet.
        """
        if self.current_order is None:
            return OfficerDecision(
                order_received='',
                order_executed='hold',
                rationale='No standing order — defaulting to hold.',
                belief_state={},
                complied=False,
            )
        return self.process_order(self.current_order)

    def seek_opportunity(self) -> Optional[Dict[str, Any]]:
        """Return an exploit action if the officer's belief DB shows an opportunity.

        Trust modulates the gap threshold (high trust = exploits smaller gaps).
        Battery targets: officer_exploits_flank, officer_initiative_vs_trust.

        Returns None if:
          - no opportunity is visible in the belief DB
          - officer is dead
          - 'flank' is not in repertoire
        """
        if self.is_dead or 'flank' not in self.repertoire:
            return None

        foe_coverage = self.belief_db.believed('battle', 'foe_coverage_fraction',
                                               default=1.0)
        foe_gap_side = self.belief_db.believed('battle', 'foe_gap_side', default=None)

        # Trust modulates threshold: high trust → exploit smaller gaps (higher threshold)
        # low trust → conservative literalism (lower threshold, needs very obvious gap)
        # threshold = base * (0.5 + trust): trust=1.0→1.5x, trust=0.5→1.0x, trust=0.0→0.5x
        adjusted_threshold = EXPLOITABLE_GAP_THRESHOLD * (0.5 + self.trust)

        if (foe_coverage is not None
                and foe_coverage < adjusted_threshold
                and foe_gap_side is not None):
            return {
                'type': 'flank',
                'target_side': foe_gap_side,
                'rationale': (
                    f"Officer {self.role} (cohort {self.cohort_id}) sees gap: "
                    f"foe coverage {foe_coverage:.0%} < adjusted threshold "
                    f"{adjusted_threshold:.0%} (trust={self.trust:.2f}) on {foe_gap_side} side."
                ),
                'self_initiated': True,
            }
        return None

    def honest_report(self) -> Dict[str, Any]:
        """Generate an upward report from the officer's belief DB.

        Battery target: officer_honest_report.
        Low trust officers shade bad news (under-report losses, over-report gains).
        High trust officers report the believed value faithfully.
        The report is always from belief, never from trace — the patron audit
        depends on this divergence being real and traceable.
        """
        report_beliefs: Dict[str, Dict[str, Any]] = {}
        for phase in self.belief_db.phases_with_beliefs():
            phase_report: Dict[str, Any] = {}
            phase_beliefs = self.belief_db._beliefs.get(phase, {})
            for claim, (value, conf, _src) in phase_beliefs.items():
                reported = value
                # Trust-based shading: low trust shades bad news
                if isinstance(value, float) and self.trust < 0.8:
                    shade = (0.8 - self.trust) * 0.4  # max 32% distortion at trust=0
                    if any(kw in claim for kw in ('dead', 'loss', 'casualty', 'broken')):
                        reported = value * (1.0 - shade)   # under-report bad news
                    elif any(kw in claim for kw in ('won', 'success', 'held', 'routed_foe')):
                        reported = min(1.0, value * (1.0 + shade))  # over-report good
                phase_report[claim] = {
                    'reported': reported,
                    'believed': value,
                    'confidence': conf,
                    'shaded': reported != value,
                }
            if phase_report:
                report_beliefs[phase] = phase_report

        return {
            'officer_id': f'{self.role}_{self.cohort_id}',
            'trust': self.trust,
            'report': report_beliefs,
            'shading_applied': self.trust < 0.8,
        }

    # ------------------------------------------------------------------
    # Belief DB update helpers

    def receive_dispatch(self, content: Dict[str, Any], confidence: float) -> None:
        """Officer receives a dispatch from HQ or scouts."""
        self.belief_db.receive_dispatch('battle', content, confidence)

    def observe_directly(self, content: Dict[str, Any], source: str) -> None:
        """Officer makes a direct observation (their own sightlines)."""
        self.belief_db.observe('battle', content, source)

    # ------------------------------------------------------------------
    # Order-type handlers

    def _apply_cavalry_judgment(self, order_type: str) -> Optional['OfficerDecision']:
        """Cavalry officer refuses charge into formed density (horse_solid threshold).

        Battery target: officer_cavalry_judgment.
        Returns a refusal OfficerDecision if cavalry judgment applies, else None.
        """
        believed_density = self.belief_db.believed('battle', 'foe_density_ahead',
                                                    default=0.0)
        if believed_density is not None and believed_density >= CAVALRY_FORMED_DENSITY:
            return OfficerDecision(
                order_received=order_type,
                order_executed='hold',
                rationale=(
                    f"Cavalry officer {self.role} declines {order_type!r} into formed "
                    f"density {believed_density:.1f} >= horse_solid threshold "
                    f"{CAVALRY_FORMED_DENSITY:.1f}. Threatening, not charging."
                ),
                belief_state={
                    'foe_density_ahead': believed_density,
                    'cavalry_formed_threshold': CAVALRY_FORMED_DENSITY,
                },
                complied=False,
            )
        return None

    def _process_fighting_withdrawal(self, order: Dict[str, Any]) -> OfficerDecision:
        """Controlled retreat under contact without triggering panic.

        Battery target: officer_dead_repertoire (withdrawal absent when officer dead).
        The meaning institution (ordered_retreat_holds) attenuates cues on the lattice side;
        this method validates the officer can authorize the action.
        """
        believed_pressure = self.belief_db.believed('battle', 'foe_density_ahead', default=0.0)
        return OfficerDecision(
            order_received='fighting_withdrawal',
            order_executed='fighting_withdrawal',
            rationale=(
                f"Officer {self.role} authorising fighting withdrawal "
                f"(believed pressure: {believed_pressure:.1f}). "
                "Meaning institution sustains cohesion during give-ground."
            ),
            belief_state={'foe_density_ahead': believed_pressure},
            complied=True,
        )

    def _process_charge(self, order: Dict[str, Any]) -> OfficerDecision:
        """Battery target: officer_refuses_suicidal."""
        believed_density = self.belief_db.believed('battle', 'foe_density_ahead',
                                                   default=0.0)
        own_strength_frac = self.belief_db.believed('battle', 'own_strength_frac',
                                                    default=1.0)

        if (believed_density is not None
                and believed_density >= SUICIDAL_FOE_DENSITY):
            # Trust modulation: very low trust (cowed officer) may comply anyway
            if self.trust < 0.30:
                return OfficerDecision(
                    order_received='charge',
                    order_executed='charge',
                    rationale=(
                        f"Officer {self.role} (trust={self.trust:.2f}) obeys literally into "
                        f"density {believed_density:.1f} — cowed subordinate complies despite "
                        f"suicidal odds (captain-wrong, not pathfinding-wrong)."
                    ),
                    belief_state={'foe_density_ahead': believed_density, 'trust': self.trust},
                    complied=True,
                )
            return OfficerDecision(
                order_received='charge',
                order_executed='hold',
                rationale=(
                    f"Officer {self.role} refuses charge: believed foe density "
                    f"{believed_density:.1f} >= suicidal threshold "
                    f"{SUICIDAL_FOE_DENSITY:.1f}. Holding position."
                ),
                belief_state={
                    'foe_density_ahead': believed_density,
                    'suicidal_threshold': SUICIDAL_FOE_DENSITY,
                },
                complied=False,
            )
        if own_strength_frac is not None and own_strength_frac < 0.25:
            return OfficerDecision(
                order_received='charge',
                order_executed='hold',
                rationale=(
                    f"Officer {self.role} refuses charge: own strength "
                    f"{own_strength_frac:.0%} critically low. Awaiting reinforcement."
                ),
                belief_state={'own_strength_frac': own_strength_frac},
                complied=False,
            )
        return OfficerDecision(
            order_received='charge',
            order_executed='charge',
            rationale='Foe density within acceptable range; executing charge.',
            belief_state={'foe_density_ahead': believed_density},
            complied=True,
        )

    def _process_advance(self, order: Dict[str, Any]) -> OfficerDecision:
        """Battery target: officer_ambiguous_order.

        'Advance when favorable' can be misread as 'advance now' if the
        officer's belief DB indicates favorable conditions (which may be wrong).
        """
        when = order.get('when', 'when_favorable')
        confidence = order.get('dispatch_confidence', 1.0)

        if when == 'when_favorable' and confidence < DISPATCH_AMBIGUITY_THRESHOLD:
            believed_threat = self.belief_db.believed('battle', 'foe_density_ahead',
                                                      default=0.5)
            conditions_favorable = (
                believed_threat is not None and believed_threat < 1.5
            )
            if conditions_favorable:
                return OfficerDecision(
                    order_received='advance',
                    order_executed='advance',
                    rationale=(
                        f"Officer {self.role} reads 'advance when favorable' as "
                        f"'advance now': believed foe density {believed_threat:.1f} "
                        f"< 1.5 — conditions appear favorable (dispatch confidence "
                        f"{confidence:.0%} too low for caution)."
                    ),
                    belief_state={
                        'foe_density_ahead': believed_threat,
                        'dispatch_confidence': confidence,
                        'interpretation': 'advance_now',
                    },
                    complied=True,
                )
            else:
                return OfficerDecision(
                    order_received='advance',
                    order_executed='hold',
                    rationale=(
                        f"Officer {self.role} reads ambiguous dispatch as 'hold': "
                        f"believed foe density {believed_threat:.1f} ≥ 1.5."
                    ),
                    belief_state={
                        'foe_density_ahead': believed_threat,
                        'dispatch_confidence': confidence,
                        'interpretation': 'hold_for_conditions',
                    },
                    complied=False,
                )

        return OfficerDecision(
            order_received='advance',
            order_executed='advance',
            rationale='Clear advance order; executing.',
            belief_state={'dispatch_confidence': confidence},
            complied=True,
        )

    def _process_flank(self, order: Dict[str, Any]) -> OfficerDecision:
        believed_gap = self.belief_db.believed('battle', 'foe_gap_side', default=None)
        if believed_gap is None:
            return OfficerDecision(
                order_received='flank',
                order_executed='advance',
                rationale=(
                    f"Officer {self.role}: no gap visible in belief DB; "
                    f"converting flank order to direct advance."
                ),
                belief_state={'foe_gap_side': None},
                complied=False,
            )
        return OfficerDecision(
            order_received='flank',
            order_executed='flank',
            rationale=f"Gap confirmed on {believed_gap} side; executing flank.",
            belief_state={'foe_gap_side': believed_gap},
            complied=True,
        )


# ---------------------------------------------------------------------------
# Factory for battery scenarios

def make_officer(cohort_id: int, role: str, authority: float = 0.85,
                 trust: float = 0.70,
                 repertoire: Optional[frozenset] = None,
                 mounted: bool = False,
                 is_dead: bool = False,
                 beliefs: Optional[Dict[str, Any]] = None,
                 belief_confidence: float = 0.80) -> Officer:
    """Convenience factory for battery test scenarios."""
    rep = repertoire if repertoire is not None else frozenset(ORDER_TYPES)
    officer = Officer(
        cohort_id=cohort_id,
        role=role,
        authority=authority,
        trust=trust,
        repertoire=rep,
        mounted=mounted,
        is_dead=is_dead,
    )
    if beliefs:
        officer.receive_dispatch(beliefs, belief_confidence)
    return officer
