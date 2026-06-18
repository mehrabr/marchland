"""MARCHLAND core: patron belief database.

The patron's belief state is updated only by rider dispatches — they do not
witness the trace directly. Beliefs therefore diverge from ground truth
whenever dispatches are absent, partial, or misleading.

Schema: {phase: {claim: (value, confidence)}}
  phase    — 'siege' | 'march' | 'battle'
  claim    — e.g. 'outcome', 'day', 'casualties', 'won'
  value    — the believed value
  confidence — float in [0, 1]; 1.0 = rider arrived fresh; lower = rumour/partial
"""
from typing import Any, Dict, Optional, Tuple


class BeliefDB:
    """Patron's belief state; updated only by rider dispatches."""

    def __init__(self):
        self._beliefs: Dict[str, Dict[str, Tuple[Any, float]]] = {}

    # ------------------------------------------------------------------
    # Write path: rider dispatches

    def receive_dispatch(self, phase: str, claims: Dict[str, Any],
                         confidence: float) -> None:
        """Record a rider's dispatch into the patron's belief state.

        confidence: 1.0 = fresh rider, clear account;
                    0.7 = second-hand or partial;
                    0.5 = rumour only.
        """
        if phase not in self._beliefs:
            self._beliefs[phase] = {}
        for claim, value in claims.items():
            # Later dispatches overwrite earlier ones (rider with fresher news)
            self._beliefs[phase][claim] = (value, confidence)

    # ------------------------------------------------------------------
    # Read path: query beliefs

    def get(self, phase: str, claim: str) -> Optional[Tuple[Any, float]]:
        """Return (value, confidence) or None if the patron has no belief."""
        return self._beliefs.get(phase, {}).get(claim)

    def believed(self, phase: str, claim: str, default: Any = None) -> Any:
        """Return only the believed value (not confidence), or default."""
        entry = self.get(phase, claim)
        return entry[0] if entry is not None else default

    def phases_with_beliefs(self):
        return list(self._beliefs.keys())

    # ------------------------------------------------------------------
    # Audit: compare beliefs against trace ground truth

    def audit(self, trace_summary: Dict[str, Any]) -> Dict[str, Dict]:
        """Compare patron beliefs against trace ground truth.

        trace_summary: {phase: {claim: actual_value}} — caller derives this
        from the composed trace (e.g. via _trace_to_summary).

        Returns: {'{phase}.{claim}': {believed, confidence, actual, match}}
          match is True/False if actual is known, None if claim has no trace analog.
        """
        findings: Dict[str, Dict] = {}
        for phase, beliefs in self._beliefs.items():
            phase_truth = trace_summary.get(phase, {})
            for claim, (believed, confidence) in beliefs.items():
                actual = phase_truth.get(claim)
                if actual is None:
                    match = None      # trace has no ground truth for this claim
                elif isinstance(actual, float) and isinstance(believed, float):
                    match = abs(actual - believed) < 0.05
                else:
                    match = (actual == believed)
                findings[f"{phase}.{claim}"] = dict(
                    believed=believed,
                    confidence=confidence,
                    actual=actual,
                    match=match,
                )
        return findings

    def to_dict(self) -> Dict:
        return {
            phase: {
                claim: {'value': v, 'confidence': c}
                for claim, (v, c) in claims.items()
            }
            for phase, claims in self._beliefs.items()
        }


def trace_to_summary(composed_trace: Dict) -> Dict[str, Dict]:
    """Derive a {phase: {claim: value}} ground-truth summary from a composed trace.

    Only claims that the patron might ask about are extracted.
    """
    summary: Dict[str, Dict] = {}

    events = composed_trace.get('events', [])

    # --- Siege ---
    siege_evs = [ev for ev in events if ev[3] == 'siege']
    for ev in siege_evs:
        name, t, kw, _ = ev
        if name in ('NEGOTIATED', 'STORMED_sack', 'RELIEVED',
                    'ABANDONED_supply', 'ONGOING'):
            summary.setdefault('siege', {})['outcome'] = name
            summary['siege']['day'] = int(t)

    # --- March ---
    march_evs = [ev for ev in events if ev[3] == 'march']
    for ev in march_evs:
        name, t, kw, _ = ev
        if name in ('arrived', 'failed'):
            summary.setdefault('march', {})['arrived'] = (name == 'arrived')
            summary['march']['day'] = int(t)
            summary['march']['fatigue'] = round(float(kw.get('fatigue', 0)), 2)

    # --- Battle ---
    battle_evs = [ev for ev in events if ev[3] == 'battle']
    for ev in battle_evs:
        name, t, kw, _ = ev
        if name == 'side0_broke':
            summary.setdefault('battle', {})['won'] = False   # side 0 is the player
        elif name == 'side1_broke':
            summary.setdefault('battle', {})['won'] = True
    # Death certs don't carry side, so per-side casualties cannot be derived from
    # the trace without additional attribution. Dispatch casualties remain unverifiable.

    return summary
