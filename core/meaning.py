"""MARCHLAND core: institution-of-meaning interpretation layer (M7.2).

An institution of meaning transforms raw cue values BEFORE they reach the
universal appraisal threshold in lattice.py. The substrate constants and
threshold are unchanged; only the inputs differ per cohort.

Architecture (Addendum X §2, Olleus's form):

    raw cues  →  [institution-of-meaning transform]  →  transformed cues
                                                              ↓
                                                    UNIVERSAL threshold → appraisal

A meaning is legitimate only if it:
  (a) traces to a built institution (carried_by: officer/cult/oath/paymaster)
  (b) has non-empty failure_conditions — the audit enforces this in code (M7.3)

An essence cannot be destroyed; an institution of meaning CAN be destroyed
by killing the carrier, missing the paydays, breaking the oath, etc.

Officer death severs a meaning: when the `carried_by` officer is recorded as
down in the trace, the meaning transitions to its break_effect state.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MeaningTransform:
    """Cue-level transform a cohort applies to its raw appraisal inputs.

    scale_factors:  {cue_name: float}  — multiplicative on raw cue value
    impulse_terms:  {cue_name: float}  — additive constant (positive = courage impulse)

    Example: "death as honor" meaning
        scale_factors={'downs': 0.6, 'rout': 0.8}
        impulse_terms={'expose': -0.3}   # aggressive stance counteracts exposure
    """
    scale_factors: Dict[str, float] = field(default_factory=dict)
    impulse_terms: Dict[str, float] = field(default_factory=dict)

    def apply(self, cues: Dict[str, float]) -> Dict[str, float]:
        """Return transformed cue dict. Unknown cue names are left unchanged."""
        result = dict(cues)
        for name, scale in self.scale_factors.items():
            if name in result:
                result[name] = result[name] * scale
        for name, impulse in self.impulse_terms.items():
            if name in result:
                result[name] = result[name] + impulse
        return result


@dataclass
class InstitutionOfMeaning:
    """A cultural/institutional interpretation frame carried by a specific entity.

    Attributes
    ----------
    id              — unique identifier within a scenario/culture
    carried_by      — the institutional entity that maintains this meaning
                      (officer role name | cult | oath label | paymaster ledger)
    transform       — how raw cues are modified while the meaning is active
    failure_conditions — REQUIRED non-empty; states that break this meaning
                       (empty → audit rejects the data file, Law 1 enforcement)
    break_effect    — transform to apply once the meaning is broken
                      (often: identity — the raw, untransformed cue)
    """
    id: str
    carried_by: str
    transform: MeaningTransform
    failure_conditions: List[str]       # MUST be non-empty
    break_effect: Optional[MeaningTransform] = None
    active: bool = True

    def __post_init__(self):
        if not self.failure_conditions:
            raise ValueError(
                f"InstitutionOfMeaning '{self.id}': failure_conditions must not be "
                "empty. A meaning without a destruction path is an essence — "
                "receipts audit (M7.3) enforces this."
            )

    def break_meaning(self) -> None:
        """Transition meaning from active to broken (carrier lost, oath broken, etc.)."""
        self.active = False

    def current_transform(self) -> MeaningTransform:
        """Return the transform to apply given active/broken state."""
        if self.active:
            return self.transform
        if self.break_effect is not None:
            return self.break_effect
        return MeaningTransform()   # identity: no change


# ---------------------------------------------------------------------------
# Cohort-level meaning state tracker

class MeaningState:
    """Tracks active institutions of meaning for each cohort in a battle.

    Usage in lattice.py:
        ms = MeaningState(scn.get('meanings', {}))
        ...
        in tick():
            cues_dict = ms.transform_cues(cohort_idx, cues_dict)
    """

    def __init__(self, meaning_specs: Dict[int, List[Dict[str, Any]]]):
        """
        meaning_specs: {cohort_idx: [meaning_spec_dict, ...]}

        Each meaning_spec_dict has keys:
            id, carried_by, transform: {scale_factors, impulse_terms},
            failure_conditions, break_effect (optional)
        """
        # {cohort_idx: [InstitutionOfMeaning, ...]}
        self._cohort_meanings: Dict[int, List[InstitutionOfMeaning]] = {}
        for cohort_idx, specs in meaning_specs.items():
            self._cohort_meanings[cohort_idx] = [
                _meaning_from_spec(s) for s in specs
            ]

    def transform_cues(self, cohort_idx: int, cues: Dict[str, float]) -> Dict[str, float]:
        """Apply all active meanings for this cohort to the cue dict."""
        meanings = self._cohort_meanings.get(cohort_idx, [])
        for m in meanings:
            cues = m.current_transform().apply(cues)
        return cues

    def sever_carrier(self, carrier_id: str) -> List[str]:
        """Called when an officer/carrier goes down. Breaks any meaning carried by them.

        Returns list of meaning ids that were broken.
        """
        broken = []
        for meanings in self._cohort_meanings.values():
            for m in meanings:
                if m.active and m.carried_by == carrier_id:
                    m.break_meaning()
                    broken.append(m.id)
        return broken

    def active_count(self) -> int:
        return sum(m.active for ml in self._cohort_meanings.values() for m in ml)


# ---------------------------------------------------------------------------
# Builder helpers

def _meaning_from_spec(spec: Dict[str, Any]) -> InstitutionOfMeaning:
    tf_raw = spec.get('transform', {})
    transform = MeaningTransform(
        scale_factors=tf_raw.get('scale_factors', {}),
        impulse_terms=tf_raw.get('impulse_terms', {}),
    )
    be_raw = spec.get('break_effect')
    if be_raw:
        break_effect = MeaningTransform(
            scale_factors=be_raw.get('scale_factors', {}),
            impulse_terms=be_raw.get('impulse_terms', {}),
        )
    else:
        break_effect = None
    return InstitutionOfMeaning(
        id=spec['id'],
        carried_by=spec['carried_by'],
        transform=transform,
        failure_conditions=spec['failure_conditions'],
        break_effect=break_effect,
        active=spec.get('active', True),
    )


def build_meaning_state(scenario: Dict[str, Any]) -> Optional['MeaningState']:
    """Build a MeaningState from the 'meanings' key in a scenario dict.

    Returns None if no meanings are specified (zero overhead path).
    """
    specs = scenario.get('meanings')
    if not specs:
        return None
    return MeaningState(specs)
