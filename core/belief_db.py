"""MARCHLAND core: patron belief database.

The patron's belief state is updated only by rider dispatches — they do not
witness the trace directly. Beliefs therefore diverge from ground truth
whenever dispatches are absent, partial, or misleading.

M4 extension: beliefs carry a source tag ('dispatch' | 'landscape' | 'sightlines'
| 'nearby_units') so that beliefs_for_station() can filter to what the
commander's body can actually see.

Schema: {phase: {claim: (value, confidence, source)}}
  phase      — 'siege' | 'march' | 'battle'
  claim      — e.g. 'outcome', 'day', 'casualties', 'won'
  value      — the believed value
  confidence — float in [0, 1]; 1.0 = rider arrived fresh; lower = rumour/partial
  source     — how this belief was acquired (see SOURCE_VISIBILITY in stations.py)
"""
from typing import Any, Dict, Optional, Tuple

from .stations import Station, station_can_see


class BeliefDB:
    """Patron's belief state; updated by rider dispatches or direct observation."""

    def __init__(self):
        # {phase: {claim: (value, confidence, source)}}
        self._beliefs: Dict[str, Dict[str, Tuple[Any, float, str]]] = {}

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
            self._beliefs[phase][claim] = (value, confidence, 'dispatch')

    def observe(self, phase: str, claims: Dict[str, Any],
                source: str) -> None:
        """Record a direct observation (landscape, sightlines, or nearby_units).

        Confidence is derived from the source type:
          landscape   — 0.75  (broad positional view, no fine detail)
          sightlines  — 0.85  (cohort-level, noise on numbers)
          nearby_units — 0.95 (immediate vicinity, clear but narrow)

        Observations only overwrite an existing belief if they have equal or
        higher confidence, so a fresh rider's dispatch is not downgraded by a
        stale landscape scan.
        """
        CONFIDENCE: Dict[str, float] = {
            'landscape':    0.75,
            'sightlines':   0.85,
            'nearby_units': 0.95,
        }
        conf = CONFIDENCE.get(source, 0.60)
        if phase not in self._beliefs:
            self._beliefs[phase] = {}
        for claim, value in claims.items():
            existing = self._beliefs[phase].get(claim)
            if existing is None or conf >= existing[1]:
                self._beliefs[phase][claim] = (value, conf, source)

    # ------------------------------------------------------------------
    # Read path: query beliefs

    def get(self, phase: str, claim: str) -> Optional[Tuple[Any, float]]:
        """Return (value, confidence) or None if the patron has no belief."""
        entry = self._beliefs.get(phase, {}).get(claim)
        if entry is None:
            return None
        return (entry[0], entry[1])   # strip source, preserve public API

    def believed(self, phase: str, claim: str, default: Any = None) -> Any:
        """Return only the believed value (not confidence), or default."""
        entry = self.get(phase, claim)
        return entry[0] if entry is not None else default

    def phases_with_beliefs(self):
        return list(self._beliefs.keys())

    def beliefs_for_station(self, station: Station) -> Dict[str, Dict[str, Tuple[Any, float]]]:
        """Return beliefs visible from the given command station.

        Filters claims by their source against the station's information_set.
        Returns {phase: {claim: (value, confidence)}} — same shape as get().
        """
        result: Dict[str, Dict[str, Tuple[Any, float]]] = {}
        for phase, claims in self._beliefs.items():
            visible: Dict[str, Tuple[Any, float]] = {}
            for claim, (value, conf, source) in claims.items():
                if station_can_see(station, source):
                    visible[claim] = (value, conf)
            if visible:
                result[phase] = visible
        return result

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
        for phase, claims in self._beliefs.items():
            phase_truth = trace_summary.get(phase, {})
            for claim, (believed, confidence, _source) in claims.items():
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
                for claim, (v, c, _s) in claims.items()
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
