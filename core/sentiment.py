"""MARCHLAND core: sentiment drift field (M7.4).

A scalar penetration field per cohort over the social/authority graph, ticked
at campaign-day resolution. Sentiment is the TRANSITION function — it changes
what institutions of meaning the army is in, driven entirely by already-tracked
receipts (Addendum X §3, Olleus's anchoring law).

Architecture:
    institutions of meaning  =  the STATE      (how this cohort reads events)
    sentiment drift          =  the TRANSITION  (how that reading changes daily)
    battle appraisal         =  the READOUT     (transformed cues meet threshold)

Every transmission term reuses a march-model receipt. No free contagion
constants. The channels:

    spread accelerates with:  idle       (idle_days — the rumor mill)
                              hunger     (stock_depleted flag)
                              arrears    (pay_arrears from march model)
                              bond       (existing social graph edges)

    resisted by:              officer authority intact + actively countering

Seeding events:
    pointless_loss  — a fight with no material gain
    broken_promise  — paymaster missed a date
    miracle         — unexpected survival or victory
    won_fight       — a clear local victory
    paid_wage       — arrears cleared

The `M7.3 audit rule: a sentiment.transmission term referencing a quantity not
in TRACKED_RECEIPTS fails receipts-check. The registry below is the authority.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Registry of tracked receipts that may appear in transmission dicts.
# M7.3 audit rule: any transmission term NOT in this set fails CI.
TRACKED_RECEIPTS = frozenset({
    'idle',       # idle_days from SeasonState
    'hunger',     # stock_depleted (bool) from march result
    'arrears',    # pay_arrears from march scenario
    'bond',       # social graph edge weight (0–1 float)
    'disease',    # disease_env from march scenario
    'officers',   # officer authority (0–1, from march scenario)
    'cohesion',   # cohesion from march result
})


@dataclass
class SentimentSpec:
    """Definition of one named sentiment (read from culture/scenario data).

    Attributes
    ----------
    id          — unique identifier, e.g. 'cursed_campaign'
    valence     — '+' (positive) or '-' (negative)
    affects     — list of meaning ids this sentiment can flip
    transmission — {receipt_name: weight} — ONLY keys from TRACKED_RECEIPTS allowed
    seed_events  — event names that plant this sentiment
    counter      — what officer authority action counters it
    """
    id: str
    valence: str                              # '+' | '-'
    affects: List[str] = field(default_factory=list)
    transmission: Dict[str, float] = field(default_factory=dict)
    seed_events: List[str] = field(default_factory=list)
    counter: str = ''

    def __post_init__(self):
        bad = set(self.transmission) - TRACKED_RECEIPTS
        if bad:
            raise ValueError(
                f"Sentiment '{self.id}': transmission terms {bad} are not in "
                "TRACKED_RECEIPTS. Add them to the registry or use a tracked receipt. "
                "(M7.3 Olleus's law: no free contagion constants)"
            )


class SentimentField:
    """Penetration levels per cohort for a set of named sentiments.

    Penetration is a scalar in [0, 1]:
      0 = not present
      1 = fully penetrated (meaning flip threshold likely crossed)

    Usage:
        sf = SentimentField(cohort_ids, sentiment_specs)
        sf.seed('pointless_loss', cause_cohort=2)
        for day in range(60):
            receipts = {idle: ..., hunger: ..., arrears: ..., ...}
            events = sf.tick(receipts)
            for cohort_id, sentiment_id, old_p, new_p in events:
                ...  # surfaced as decision-point events in season loop
    """

    FLIP_THRESHOLD = 0.70   # penetration at which meaning-flip triggers
    DECAY_PER_DAY  = 0.02   # passive decay (entropy toward baseline)
    BASE_SPREAD    = 0.04   # base spread rate per connected cohort

    def __init__(self, cohort_ids: List[int], specs: List[SentimentSpec]):
        self.cohort_ids = cohort_ids
        self.specs: Dict[str, SentimentSpec] = {s.id: s for s in specs}
        # penetration[sentiment_id][cohort_idx] in [0, 1]
        self._penetration: Dict[str, List[float]] = {
            s.id: [0.0] * len(cohort_ids) for s in specs
        }
        # Officer authority per cohort: 0 = no authority, 1 = full authority
        self._authority: List[float] = [1.0] * len(cohort_ids)
        # Social graph: list of (i, j, weight) edges
        self._edges: List[tuple] = []
        # Which meanings have flipped per cohort: {cohort_idx: set of sentiment_ids}
        self._flipped: Dict[int, set] = {i: set() for i in range(len(cohort_ids))}

    def set_edges(self, edges: List[tuple]) -> None:
        """Set social graph edges as (cohort_i, cohort_j, weight)."""
        self._edges = edges

    def set_authority(self, cohort_idx: int, authority: float) -> None:
        self._authority[cohort_idx] = max(0.0, min(1.0, authority))

    # ------------------------------------------------------------------
    # Seeding

    def seed(self, event_name: str, cause_cohort: int = 0,
             initial_penetration: float = 0.25) -> None:
        """Plant a sentiment seeded by the given event_name."""
        idx = self._cohort_to_idx(cause_cohort)
        if idx is None:
            return
        for sid, spec in self.specs.items():
            if event_name in spec.seed_events:
                self._penetration[sid][idx] = min(
                    1.0, self._penetration[sid][idx] + initial_penetration
                )

    # ------------------------------------------------------------------
    # Tick

    def tick(self, receipts: Dict[str, Any]) -> List[tuple]:
        """Advance one campaign day.

        receipts:  {receipt_name: value}  — same names as TRACKED_RECEIPTS
        Returns list of (cohort_id, sentiment_id, old_p, new_p) for cohorts
        that crossed the FLIP_THRESHOLD this tick (decision-point events).
        """
        events = []
        idle_factor   = float(receipts.get('idle', 0))        # days idle this season
        hunger_factor = float(bool(receipts.get('hunger', False)))
        arrears_w     = float(receipts.get('arrears', 0.0))   # 0–1
        bond_strength = float(receipts.get('bond', 0.5))      # edge multiplier
        officer_global= float(receipts.get('officers', 0.85))

        for sid, spec in self.specs.items():
            old_levels = list(self._penetration[sid])

            # Compute effective transmission multiplier from receipts
            tx = spec.transmission
            spread_mult = (
                1.0
                + tx.get('idle', 0.0)    * min(idle_factor / 30.0, 1.0)
                + tx.get('hunger', 0.0)  * hunger_factor
                + tx.get('arrears', 0.0) * arrears_w
                + tx.get('bond', 0.0)    * bond_strength
            )
            spread_mult = max(0.0, spread_mult)

            # Neighbor spread
            new_levels = list(old_levels)
            for (ci, cj, w) in self._edges:
                # Spread from ci → cj and cj → ci proportional to penetration delta
                pi, pj = old_levels[ci], old_levels[cj]
                rate = self.BASE_SPREAD * spread_mult * w
                # Resistance from officer authority
                auth_j = min(self._authority[cj], officer_global)
                auth_i = min(self._authority[ci], officer_global)
                counter_j = tx.get('bond', 0.0) * auth_j * 0.5
                counter_i = tx.get('bond', 0.0) * auth_i * 0.5
                if pi > pj:
                    delta = rate * (pi - pj) * max(0.0, 1.0 - auth_j - counter_j)
                    new_levels[cj] = min(1.0, pj + delta)
                if pj > pi:
                    delta = rate * (pj - pi) * max(0.0, 1.0 - auth_i - counter_i)
                    new_levels[ci] = min(1.0, pi + delta)

            # Passive decay
            auth_avg = (sum(self._authority) / max(len(self._authority), 1))
            decay = self.DECAY_PER_DAY * (1.0 + auth_avg)
            new_levels = [max(0.0, p - decay) for p in new_levels]

            self._penetration[sid] = new_levels

            # Detect threshold crossings → decision-point events
            for idx, (old_p, new_p) in enumerate(zip(old_levels, new_levels)):
                if old_p < self.FLIP_THRESHOLD <= new_p:
                    cohort_id = self.cohort_ids[idx]
                    if sid not in self._flipped[idx]:
                        self._flipped[idx].add(sid)
                        events.append((cohort_id, sid, old_p, new_p))

        return events

    # ------------------------------------------------------------------
    # Counter-intervention

    def apply_counter(self, sentiment_id: str, cohort_idx: int,
                      reduction: float = 0.30) -> None:
        """Officer dispatched to counter a rumor — reduces penetration."""
        if sentiment_id in self._penetration:
            p = self._penetration[sentiment_id]
            p[cohort_idx] = max(0.0, p[cohort_idx] - reduction)

    def counter_all(self, sentiment_id: str, reduction: float = 0.15) -> None:
        """Army-wide counter (paid arrears, rest granted, victory news)."""
        if sentiment_id in self._penetration:
            p = self._penetration[sentiment_id]
            self._penetration[sentiment_id] = [max(0.0, v - reduction) for v in p]

    # ------------------------------------------------------------------
    # Read

    def penetration(self, sentiment_id: str, cohort_idx: int) -> float:
        return self._penetration.get(sentiment_id, [0.0] * len(self.cohort_ids))[cohort_idx]

    def max_penetration(self, sentiment_id: str) -> float:
        levels = self._penetration.get(sentiment_id, [])
        return max(levels) if levels else 0.0

    def cohort_summary(self) -> List[Dict[str, Any]]:
        """Return per-cohort sentiment summary for Table rendering."""
        result = []
        for idx, cid in enumerate(self.cohort_ids):
            row: Dict[str, Any] = {'cohort_id': cid}
            for sid in self.specs:
                row[sid] = round(self._penetration[sid][idx], 3)
            row['authority'] = round(self._authority[idx], 2)
            row['flipped'] = list(self._flipped[idx])
            result.append(row)
        return result

    # ------------------------------------------------------------------

    def _cohort_to_idx(self, cohort_id: int) -> Optional[int]:
        try:
            return self.cohort_ids.index(cohort_id)
        except ValueError:
            return None


# ---------------------------------------------------------------------------
# Winter quarters dissolution runner (M7.5)

def run_dissolution(scn: Dict[str, Any], seed: int) -> Dict[str, Any]:
    """Winter quarters dissolution scenario.

    Runs the army through a stationary season (no movement, no battle)
    with sentiment spreading from idle+hunger+arrears channels.
    No combat events appear in the output.

    Returns a result dict compatible with battery runner expectations.
    """
    import numpy as np
    from core.march import run_march
    from core.trace import Trace

    rng = np.random.default_rng(seed)
    tr = Trace(phase='march', scenario='winter_quarters', seed=seed)

    march_result = run_march(scn, seed, trace=tr)

    # Build sentiment field over cohorts
    cohort_ids = list(range(scn.get('num_cohorts', 4)))
    specs = _default_winter_sentiments()
    sf = SentimentField(cohort_ids, specs)

    # Simple chain graph: each cohort bonds to its neighbors
    edges = [(i, i+1, 0.7) for i in range(len(cohort_ids)-1)]
    sf.set_edges(edges)

    # Authority from march result: authority degrades proportionally with cohesion loss.
    # Officers who can't pay can't counter rumours — authority = cohesion * pay-factor.
    coh = march_result.get('cohesion', 0.5)
    pay_arrears = float(scn.get('pay_arrears', 0.0))
    # Low pay + low cohesion = low officer authority
    officer_authority = coh * max(0.05, 1.0 - pay_arrears * 0.6)
    for idx in range(len(cohort_ids)):
        sf.set_authority(idx, officer_authority)

    # Seed the root sentiment on ALL cohorts proportional to march distress signals.
    # Each cohort starts the winter with the same exposure to rumour (idle army,
    # shared camp). This reflects the mechanism: the rumour mill runs everywhere.
    deserted = march_result.get('deserted', 0)
    start_n = scn.get('start', 1000)
    desertion_frac = deserted / max(start_n, 1)
    base_seed = 0.35 + 0.30 * desertion_frac  # more desertions → stronger seed

    # seed_events for 'cursed_campaign': 'pointless_loss', 'broken_promise'
    # seed_events for 'we_are_abandoned': 'broken_promise', 'paymaster_absent'
    for cid in cohort_ids:
        sf.seed('pointless_loss', cause_cohort=cid, initial_penetration=base_seed)
    if desertion_frac > 0.05:
        for cid in cohort_ids:
            sf.seed('broken_promise', cause_cohort=cid, initial_penetration=0.2)

    # Tick for the duration of the season; track peak penetration across all ticks.
    all_decision_events = []
    days = march_result['days']
    peak_sentiment = sf.max_penetration('cursed_campaign')
    receipts = {
        'idle': float(days),
        'hunger': march_result.get('stock_days', 1.0) <= 0,
        'arrears': pay_arrears,
        'bond': 0.5,
        'officers': officer_authority,
    }
    for day_i in range(days):
        # Re-seed each day from ongoing idle/arrears pressure
        daily_seed = 0.02 * pay_arrears  # daily top-up from unresolved grievance
        if daily_seed > 0:
            for cid in cohort_ids:
                sf.seed('broken_promise', cause_cohort=cid,
                        initial_penetration=daily_seed)
        evs = sf.tick(receipts)
        all_decision_events.extend(evs)
        tick_max = sf.max_penetration('cursed_campaign')
        if tick_max > peak_sentiment:
            peak_sentiment = tick_max

    # Effective dissolution: fraction of original army still present and coherent
    eff = march_result.get('effective', start_n)
    effective_frac = eff / max(start_n, 1)

    # Check no combat events in trace
    combat_events = [e for e in tr.events if e[0] in ('melee', 'volley', 'pursuit', 'cavalry')]

    return dict(
        effective=eff,
        start=start_n,
        effective_frac=round(effective_frac, 3),
        deserted=deserted,
        dead=march_result.get('dead', 0),
        sick=march_result.get('sick', 0),
        days=days,
        cohesion=march_result.get('cohesion', 0.0),
        sentiment_max=round(peak_sentiment, 3),  # peak across season, not final state
        sentiment_summary=sf.cohort_summary(),
        decision_events=all_decision_events,
        combat_events=combat_events,       # must be empty for dissolution scenario
        trace=tr.to_dict(),
    )


def _default_winter_sentiments() -> List[SentimentSpec]:
    return [
        SentimentSpec(
            id='cursed_campaign',
            valence='-',
            affects=['honor_in_death'],
            transmission={'idle': 0.8, 'hunger': 0.6, 'arrears': 1.2, 'bond': 0.5},
            seed_events=['pointless_loss', 'broken_promise'],
            counter='dispatch_trusted_officer',
        ),
        SentimentSpec(
            id='we_are_abandoned',
            valence='-',
            affects=['sworn_oath'],
            transmission={'idle': 0.4, 'arrears': 0.9, 'bond': 0.4},
            seed_events=['broken_promise', 'paymaster_absent'],
            counter='pay_arrears',
        ),
    ]
