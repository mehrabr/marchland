"""MARCHLAND core: officer model (M7.7).

Officers reason from their OWN belief DB — never from the trace. Their
mistakes come from bad information, not from pathfinding or scripted errors.

Battery coverage (M7.7 acceptance criteria):
  - officer_refuses_suicidal: flank commander holds when believed foe density
    exceeds suicidal threshold, regardless of the order received
  - officer_exploits_flank: officer advances unprompted when their belief DB
    shows a gap the ordering commander cannot see
  - officer_misreads_dispatch: ambiguous order "advance when favorable" is
    interpreted as "advance now" because the officer's belief DB shows the
    conditions are favorable (they may be wrong)

All three cases share the same mechanism: the officer filters orders through
its belief DB. The belief DB may diverge from truth. The divergence is the
drama.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.belief_db import BeliefDB


# ---------------------------------------------------------------------------
# Thresholds (Class D — institutional, not universal-body constants)

# Density at which an officer believes a direct charge is suicidal
SUICIDAL_FOE_DENSITY = 4.0   # D: officers with enough experience set this higher

# Minimum gap in foe coverage to trigger opportunistic advance
EXPLOITABLE_GAP_THRESHOLD = 0.2   # D: fraction of front with no foe coverage

# Dispatch ambiguity: below this confidence the officer may misread
DISPATCH_AMBIGUITY_THRESHOLD = 0.65   # D: confidence below this triggers interpretation

ORDER_TYPES = frozenset({
    'charge',       # immediate frontal assault
    'hold',         # maintain position
    'advance',      # move forward when ready
    'withdraw',     # fall back
    'flank',        # envelop the enemy's flank
    'reinforce',    # move to support another cohort
    'skirmish',     # harass but do not commit
})


@dataclass
class OfficerDecision:
    """Result of an officer processing an order through its belief DB."""
    order_received: str       # the order as dispatched
    order_executed: str       # what the officer actually does (may differ)
    rationale: str            # the officer's reasoning (cites belief DB)
    belief_state: Dict        # snapshot of the relevant belief entries used
    complied: bool            # True if executed == received


@dataclass
class Officer:
    """A subordinate commander with their own partial-knowledge belief DB.

    Attributes
    ----------
    cohort_id   — which cohort this officer commands
    role        — 'flank_commander' | 'rearguard' | 'vanguard' | 'reserves'
    authority   — current authority (0–1); declines with casualties and pay arrears
    belief_db   — what this officer knows (diverges from trace and from HQ)
    """
    cohort_id: int
    role: str
    authority: float = 0.85
    belief_db: BeliefDB = field(default_factory=BeliefDB)

    # ------------------------------------------------------------------
    # Core decision method

    def process_order(self, order: Dict[str, Any]) -> OfficerDecision:
        """Filter an incoming order through the officer's belief DB.

        Returns an OfficerDecision describing what the officer actually does
        and why — which may differ from what was ordered.
        """
        order_type = order.get('type', '')
        if order_type not in ORDER_TYPES:
            return OfficerDecision(
                order_received=order_type,
                order_executed='hold',
                rationale='Unrecognised order type — defaulting to hold.',
                belief_state={},
                complied=False,
            )

        if order_type == 'charge':
            return self._process_charge(order)
        if order_type == 'advance':
            return self._process_advance(order)
        if order_type == 'flank':
            return self._process_flank(order)

        # All other orders: comply unless authority is critically low
        if self.authority < 0.2:
            return OfficerDecision(
                order_received=order_type,
                order_executed='hold',
                rationale=f'Authority too low ({self.authority:.2f}) to enforce {order_type}.',
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

    def seek_opportunity(self) -> Optional[Dict[str, Any]]:
        """Return an exploit action if the officer's belief DB shows an opportunity.

        Returns None if no opportunity is visible to this officer.
        Battery target: officer_exploits_flank.
        """
        foe_coverage = self.belief_db.believed('battle', 'foe_coverage_fraction',
                                               default=1.0)
        foe_gap_side = self.belief_db.believed('battle', 'foe_gap_side', default=None)

        if (foe_coverage is not None
                and foe_coverage < EXPLOITABLE_GAP_THRESHOLD
                and foe_gap_side is not None):
            return {
                'type': 'flank',
                'target_side': foe_gap_side,
                'rationale': (
                    f"Officer {self.role} (cohort {self.cohort_id}) sees gap: "
                    f"foe coverage {foe_coverage:.0%} < threshold "
                    f"{EXPLOITABLE_GAP_THRESHOLD:.0%} on {foe_gap_side} side."
                ),
                'self_initiated': True,
            }
        return None

    # ------------------------------------------------------------------
    # Order-type handlers

    def _process_charge(self, order: Dict[str, Any]) -> OfficerDecision:
        """Battery target: officer_refuses_suicidal."""
        believed_density = self.belief_db.believed('battle', 'foe_density_ahead',
                                                   default=0.0)
        own_strength_frac = self.belief_db.believed('battle', 'own_strength_frac',
                                                    default=1.0)

        # Refuse if believed density exceeds suicidal threshold
        # or if own strength is critically depleted
        if (believed_density is not None
                and believed_density >= SUICIDAL_FOE_DENSITY):
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
        if (own_strength_frac is not None and own_strength_frac < 0.25):
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
        """Battery target: officer_misreads_dispatch.

        'Advance when favorable' can be misread as 'advance now' if the
        officer's belief DB indicates favorable conditions (which may be wrong).
        """
        when = order.get('when', 'when_favorable')
        confidence = order.get('dispatch_confidence', 1.0)

        # Ambiguous dispatch: officer interprets against their own belief DB
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
                    complied=True,  # executes the advance (but on wrong belief)
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

        # Unambiguous order: obey
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

    # ------------------------------------------------------------------
    # Belief DB update helpers

    def receive_dispatch(self, content: Dict[str, Any], confidence: float) -> None:
        """Officer receives a dispatch from HQ or scouts."""
        self.belief_db.receive_dispatch('battle', content, confidence)

    def observe_directly(self, content: Dict[str, Any], source: str) -> None:
        """Officer makes a direct observation (their own sightlines)."""
        self.belief_db.observe('battle', content, source)

    def degrade_authority(self, amount: float) -> None:
        """Reduce officer authority (pay arrears, casualties, defeat)."""
        self.authority = max(0.0, self.authority - amount)


# ---------------------------------------------------------------------------
# Factory for battery scenarios

def make_officer(cohort_id: int, role: str, authority: float = 0.85,
                 beliefs: Optional[Dict[str, Any]] = None,
                 belief_confidence: float = 0.80) -> Officer:
    """Convenience factory for battery test scenarios."""
    officer = Officer(cohort_id=cohort_id, role=role, authority=authority)
    if beliefs:
        officer.receive_dispatch(beliefs, belief_confidence)
    return officer
