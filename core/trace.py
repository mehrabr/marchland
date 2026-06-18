"""MARCHLAND core: event trace and death certificate system.

Every death appends a DeathCert {t, agent_id, cause, killer_cohort, location}.
Every rout appends a RoutEvent {t, agent_id, appraisal}.
Traces compose across the chain (siege + march + battle in one timeline).
The trace is the ground truth; chronicles cite it.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DeathCert:
    t: float
    agent_id: int
    cause: str          # 'melee' | 'volley' | 'pursuit' | 'thirst' | 'disease' | 'assault'
    killer_cohort: Optional[int]
    location: Optional[Tuple]   # (x, y) for battle; None for population models


@dataclass
class RoutEvent:
    t: float
    agent_id: int
    appraisal: Dict[str, float]  # cue values at rout moment (side, cohort, fat, cue)


@dataclass
class Trace:
    phase: str      # 'siege' | 'march' | 'battle'
    scenario: str
    seed: int
    deaths: List[DeathCert] = field(default_factory=list)
    routs: List[RoutEvent] = field(default_factory=list)
    events: List[Tuple] = field(default_factory=list)  # (name, t, kw_dict)

    def record_death(self, t: float, agent_id: int, cause: str,
                     killer_cohort: Optional[int] = None,
                     location: Optional[Tuple] = None) -> None:
        self.deaths.append(DeathCert(t, agent_id, cause, killer_cohort, location))

    def record_rout(self, t: float, agent_id: int, appraisal: Dict[str, float]) -> None:
        self.routs.append(RoutEvent(t, agent_id, appraisal))

    def record_event(self, name: str, t: float, **kw) -> None:
        self.events.append((name, t, kw))

    def to_dict(self) -> Dict[str, Any]:
        return dict(
            phase=self.phase,
            scenario=self.scenario,
            seed=self.seed,
            deaths=[dict(t=d.t, agent_id=d.agent_id, cause=d.cause,
                        killer_cohort=d.killer_cohort, location=d.location)
                   for d in self.deaths],
            routs=[dict(t=r.t, agent_id=r.agent_id, appraisal=r.appraisal)
                  for r in self.routs],
            events=[(e[0], e[1], e[2]) for e in self.events],
        )


def compose_traces(traces: List[Trace]) -> Dict[str, Any]:
    """Merge phase traces into a single timeline dict for chronicle generation."""
    all_deaths, all_routs, all_events = [], [], []
    for tr in traces:
        all_deaths.extend([
            dict(t=d.t, agent_id=d.agent_id, cause=d.cause,
                 killer_cohort=d.killer_cohort, location=d.location, phase=tr.phase)
            for d in tr.deaths
        ])
        all_routs.extend([
            dict(t=r.t, agent_id=r.agent_id, appraisal=r.appraisal, phase=tr.phase)
            for r in tr.routs
        ])
        all_events.extend([(ev[0], ev[1], ev[2], tr.phase) for ev in tr.events])
    return dict(
        phases=[tr.phase for tr in traces],
        scenarios=[tr.scenario for tr in traces],
        seed=traces[0].seed if traces else None,
        deaths=all_deaths,
        routs=all_routs,
        events=all_events,
    )
