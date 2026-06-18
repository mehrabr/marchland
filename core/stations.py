"""MARCHLAND core: command station model.

Four stations define the commander's information set, lever set, risk, and
order latency. Moving between stations costs travel time and runs the
leader-risk lottery.

§ Law 7: "No eye without a body" — the player sees what their station's
body can see, not what the trace knows.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet


class Station(str, Enum):
    """Commander station, ordered from safest/least-informed to most exposed."""
    CAMP       = 'CAMP'
    HILL       = 'HILL'
    KNOT       = 'KNOT'
    FRONT_RANK = 'FRONT_RANK'


@dataclass(frozen=True)
class StationSpec:
    label: str
    description: str
    information_set: FrozenSet[str]   # sources this station can access
    lever_set: FrozenSet[str]         # valid order types at this station
    anchor_radius_km: float           # movement radius of the station anchor point
    lottery_per_day: float            # P(leader casualty event) per day at station
    latency_days: int                 # days for orders to travel from station to cohorts
    travel_days_from_camp: int        # days to reach this station from CAMP


STATIONS: Dict[Station, StationSpec] = {
    Station.CAMP: StationSpec(
        label='Camp',
        description='Pavilion command. Dispatches only; full lever set; no lottery.',
        information_set=frozenset({'dispatches'}),
        lever_set=frozenset({'siege', 'march', 'battle', 'withdraw', 'dispatch', 'parley'}),
        anchor_radius_km=0.0,
        lottery_per_day=0.000,
        latency_days=2,
        travel_days_from_camp=0,
    ),
    Station.HILL: StationSpec(
        label='Hill',
        description='Vantage point. Landscape view; low lottery.',
        information_set=frozenset({'dispatches', 'landscape'}),
        lever_set=frozenset({'siege', 'march', 'battle', 'withdraw', 'dispatch', 'parley'}),
        anchor_radius_km=0.5,
        lottery_per_day=0.002,
        latency_days=1,
        travel_days_from_camp=1,
    ),
    Station.KNOT: StationSpec(
        label='Command Knot',
        description='Mounted among the horse. Sightlines with noise; direct command; moderate lottery.',
        information_set=frozenset({'dispatches', 'landscape', 'sightlines'}),
        lever_set=frozenset({'siege', 'march', 'battle', 'withdraw', 'dispatch', 'parley',
                             'reinforce', 'redirect'}),
        anchor_radius_km=1.5,
        lottery_per_day=0.010,
        latency_days=0,
        travel_days_from_camp=1,
    ),
    Station.FRONT_RANK: StationSpec(
        label='Front Rank',
        description='Fighting with the men. Immediate vicinity only; limited levers; high lottery.',
        information_set=frozenset({'nearby_units'}),
        lever_set=frozenset({'melee', 'rally', 'hold'}),
        anchor_radius_km=3.0,
        lottery_per_day=0.050,
        latency_days=0,
        travel_days_from_camp=2,
    ),
}

# Sources visible at each station: a station sees claims from any source in
# its information_set, plus dispatches are always visible everywhere except
# FRONT_RANK (riders can reach CAMP/HILL/KNOT).
_DISPATCH_STATIONS = frozenset({Station.CAMP, Station.HILL, Station.KNOT})
_LANDSCAPE_STATIONS = frozenset({Station.HILL, Station.KNOT})
_SIGHTLINE_STATIONS = frozenset({Station.KNOT})
_NEARBY_STATIONS    = frozenset({Station.FRONT_RANK, Station.KNOT})

SOURCE_VISIBILITY: Dict[str, FrozenSet[Station]] = {
    'dispatch':    _DISPATCH_STATIONS,
    'landscape':   _LANDSCAPE_STATIONS,
    'sightlines':  _SIGHTLINE_STATIONS,
    'nearby_units': _NEARBY_STATIONS,
}


def station_can_see(station: Station, source: str) -> bool:
    """Return True if the given station can access claims from this source."""
    visible = SOURCE_VISIBILITY.get(source, frozenset())
    return station in visible


@dataclass
class StationState:
    """Tracks the commander's current station and accumulated lottery outcomes."""
    station: Station = Station.CAMP
    days_at_station: int = 0
    lottery_injuries: int = 0   # count of leader-risk events suffered this season

    def move_to(self, target: Station, rng, season_day: int) -> dict:
        """Move the commander to target station.

        Pays travel-time cost in days and rolls the leader-risk lottery for each
        day of travel. Returns an event dict describing what happened.
        """
        if target == self.station:
            return {'moved': False, 'cost_days': 0, 'hit': False, 'season_day': season_day}

        src_spec = STATIONS[self.station]
        tgt_spec = STATIONS[target]

        # Travel cost = distance in travel_days_from_camp (minimum 1 day)
        cost_days = max(1, abs(tgt_spec.travel_days_from_camp - src_spec.travel_days_from_camp))

        # Lottery: use whichever station is more dangerous
        lottery_rate = max(src_spec.lottery_per_day, tgt_spec.lottery_per_day)
        hit = False
        for _ in range(cost_days):
            if rng.random() < lottery_rate:
                self.lottery_injuries += 1
                hit = True
                break

        self.station = target
        self.days_at_station = 0
        return {
            'moved': True,
            'cost_days': cost_days,
            'hit': hit,
            'season_day': season_day,
            'from': src_spec.label,
            'to': tgt_spec.label,
        }

    @property
    def spec(self) -> StationSpec:
        return STATIONS[self.station]

    @property
    def latency_days(self) -> int:
        return STATIONS[self.station].latency_days
