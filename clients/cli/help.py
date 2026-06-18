"""MARCHLAND in-game help system (M6).

Topic-based help explaining mechanics in plain language,
citing which receipt changes which outcome.

Usage (in-game):
    help               — list topics
    help march         — march model receipts
    help battle        — BP-Lattice resolver
    help siege         — siege clock
    help stations      — command station mechanics
    help receipts      — full receipt class taxonomy
    help dispatch      — patron belief and dispatch
    help trace         — the omniscient record
    help table         — information-state rendering

Usage (programmatic):
    from clients.cli.help import show_help, get_help
    show_help('march', io=my_io)
    text = get_help('receipts')
"""
from typing import Optional

_TOPICS = {
    'march': """\
MARCH — moving the army
──────────────────────────────────────────────────────────
The march model runs each day: distance covered, supply consumed,
water found, men lost to thirst / disease / desertion / straggling.

Receipts that change outcomes:
  pace (B)          → miles per day target; capped by road width + carrier speed
  stock_days (C)    → days of food on hand; starvation raises fatigue, kills stragglers
  water_ok (C)      → P(water found) each night; dry streaks kill (THIRST_K = 0.06/day)
  officers (D)      → competence multiplier; lower = more stragglers per hard day
  fat0 (C)          → starting fatigue; carried from a prior siege or march
  cohesion0 (C)     → starting cohesion; falls under stress, recovers on rest days

The speed of feet is a Class A constant: SPEED = 2.5 mph.
No army on foot has averaged faster over a week. This is not a tunable value.

The march arrives when miles_covered >= distance before max_days.
Fatigue on arrival carries into the opening hazard of any subsequent battle.\
""",

    'battle': """\
BATTLE — the BP-Lattice resolver
──────────────────────────────────────────────────────────
Agents (1 ~ 10 men) occupy a grid. Each tick (~2 seconds), they sense local
foe density and may open a casualty or rout event. No attack/defense stats —
only receipts and position.

Receipts that change outcomes:
  armor (B)         → scales P(casualty | opening); armor=0.80 gives ~27% vs 45%
  ranged, ammo (B)  → archers fire at ADVANCE phase; ammo limits total volleys
  belief (C)        → rout threshold; low belief = men break on fewer appraisal cues
  fat0 (C)          → starting fatigue; fat_amp=2.0 amplifies the opening hazard
  disc (E)          → volley discipline; controls volley spread
  err (E)           → targeting error; higher = more spread

Phase machine (M1):
  ADVANCE    → cohorts close to contact range
  CONTACT    → melee; hazard accumulates each tick
  REFORMING  → assault waves pull back; fatigue recovers; rank-relief fires

Casualties concentrate in the pursuit after the break (post-break deaths >> pre-break).
Pre-break deaths ≤ ~10% is a battery target across all scenarios.

Appraisal cues that trigger rout: own dead on ground, own routing nearby,
combat-load exposure, foe flanking, own fatigue, leader lost, fear field.\
""",

    'siege': """\
SIEGE — the clock
──────────────────────────────────────────────────────────
The siege clock ticks daily. Disease, supply, and honor are the drivers.

Receipts that change outcomes:
  guns_rate (B)       → days to reach a practicable breach; faster with artillery
  camp_factor (D)     → camp sanitation multiplier; scales daily disease hazard
  sea_supply (C)      → supply by sea; 1.0 = full sea supply, cuts starvation risk
  town_food_days (C)  → garrison food reserve; longer = later surrender
  relief_day (C)      → day a relief column appears; if before fall, outcome = RELIEVED

Outcomes:
  NEGOTIATED        → garrison surrenders on terms (honor satisfied)
  STORMED_sack      → breach taken by storm; garrison sacked
  RELIEVED          → relief column arrived before fall
  ABANDONED_supply  → besieger runs out of supply
  ONGOING           → season ends with siege unresolved

Disease hazard: dis_base=0.0012/man/day, growing with weeks encamped.
The garrison may yield once a breach is practicable or after 28 creditable days.\
""",

    'stations': """\
STATIONS — where your body is
──────────────────────────────────────────────────────────
No eye without a body. Your information is scoped to your station.
You see what your station's body can see — nothing more.

  CAMP        latency 2 days   lottery 0.0%/day   dispatch view only
  HILL        latency 1 day    lottery 0.2%/day   landscape view
  KNOT        latency 0 days   lottery 1.0%/day   sightlines
  FRONT_RANK  latency 0 days   lottery 5.0%/day   nearby units

Latency: orders issued from CAMP arrive at the cohort 2 days later.
         The pending rider's ETA is visible in the Table.

Lottery: each day at HILL+, a small chance the commander takes a wound.
         Leader-risk. History's commanders died at the front.

Information sources and what each station can see:
  dispatch     → all stations (riders report back to camp)
  landscape    → HILL, KNOT, FRONT_RANK
  sightlines   → KNOT, FRONT_RANK
  nearby_units → FRONT_RANK only

'station knot' — move to KNOT, paying travel days and rolling the lottery.\
""",

    'receipts': """\
RECEIPTS — what every number is and how to change it
──────────────────────────────────────────────────────────
Every number that differs between forces answers: what in-world action
changes it? If it cannot be changed by an action, it should not exist.

Receipt classes:
  A — bodies (every human, every era; identical across all forces)
      e.g., lam0=0.0008 base hazard; SPEED=2.5mph; THIRST_K=0.06/day
      Changing a Class A constant requires a battery run + note in results/.

  B — technology (equipment, transport; receipts at muster)
      e.g., armor=0.80, ranged=1, ammo=8, wagon carriers
      Changed by equipping differently at commission. Frozen once the march begins.

  C — campaign state (fatigue, supply, belief; built up over the season)
      e.g., fat0, stock_days, water_ok, belief
      Changed by how you campaign. A hard march raises fat0 for the next battle.

  D — institutions (officers, pay, doctrine, quarter policy)
      e.g., officers=0.90, pay_arrears, quarter_policy
      Changed by institutional choices (who you hire, how you pay, how you quarter).

  E — trained capacities (drill, ammo handling, rank-relief)
      e.g., err=0.85, disc, relief_roles
      Carry over from prior seasons. Cannot be built in a single campaign.

The game has no quality coefficient. There is no per-cohort 'quality' stat
that differs between forces without a Class A–E receipt grounding it.
Type 'help march', 'help battle', or 'help siege' for per-model receipt lists.\
""",

    'dispatch': """\
DISPATCH — what your patron knows
──────────────────────────────────────────────────────────
The patron's belief DB is built from riders you send, not from the trace.
Beliefs diverge from ground truth whenever dispatches are absent or partial.

Dispatch options (after each operation):
  accurate → all claims sent; confidence 90%
  partial  → non-casualty claims only; confidence 70%
  none     → patron receives no account of this phase

At the audit, patron beliefs are compared to the trace ground truth:
  match  → patron's account agrees with what happened
  DIFFER → patron believes something different from the trace
  —      → trace has no verifiable analog for this claim

The winter court is judged from the patron's belief_db, not the trace.
If you send no dispatch after a battle, the patron cannot credit victory —
even if you won. This is the game's epistemic gap.

'history is easy to explain; the chronicle is a source with sympathies, not a fact'\
""",

    'trace': """\
TRACE — the omniscient record
──────────────────────────────────────────────────────────
The trace is the only omniscient object in the game. It records every:
  death  → {t, agent_id, cause, killer_cohort, location}
           cause: 'melee' | 'volley' | 'pursuit' | 'thirst' | 'disease' | 'assault'
  rout   → {t, agent_id, appraisal cues at the moment of breaking}
  event  → horse_balk, side_broke, ammo_starved, detour, arrived, thirst, disease

Chronicles cite the trace. Every prose statement that says "the left horse
shied" must trace to a horse_balk event with time T and location. No fabrication.

The trace is not shown during play — it is ground truth beneath the belief_db.
The patron never reads it. You can inspect it after a session:
  python tools/chronicle.py <trace.json>
  python -m clients.cli 1415 --out-dir traces/

Every battle replays bit-identically from (inputs, seed). The trace is the
certificate of reproducibility.\
""",

    'table': """\
TABLE — the information state
──────────────────────────────────────────────────────────
The Table renders what your station can currently see.
Information glyphs:

  *  confirmed   (nearby_units source, confidence ≥ 0.90)
  ~  scouted     (sightlines source, confidence 0.70–0.89)
  ?  rumoured    (dispatch source, confidence < 0.70)
  .  stale       (believed but not recently updated)

The phase bar at the top shows each phase with a glyph:
  [siege ?] → [march ~] → [battle *]
  meaning: siege = rumoured, march = scouted, battle = confirmed.

Pending orders (riders in transit) appear as:
  → besiege Harfleur (ETA: day 3)

Type 'table' at any time to refresh the Table view.
Your station determines which sources are visible (see 'help stations').\
""",
}

_TOPIC_LIST = "\n".join(
    f"  {k:<12} — {_TOPICS[k].splitlines()[0].replace('──────────────────────────────────────────────────────────', '').strip()}"
    for k in _TOPICS
)


def get_help(topic: Optional[str] = None) -> str:
    """Return help text for a topic, or the topic list if topic is None/empty."""
    if not topic or not topic.strip():
        return (
            "Available help topics:\n"
            + _TOPIC_LIST
            + "\n\nType 'help <topic>' for details."
        )
    key = topic.strip().lower()
    if key in _TOPICS:
        return _TOPICS[key]
    # Prefix match
    matches = [k for k in _TOPICS if k.startswith(key)]
    if len(matches) == 1:
        return _TOPICS[matches[0]]
    if matches:
        return f"Did you mean: {', '.join(sorted(matches))}?"
    return (
        f"Unknown topic '{topic}'.\n"
        f"Available: {', '.join(_TOPICS.keys())}"
    )


def show_help(topic: Optional[str] = None, io=None) -> None:
    """Print help for a topic. io must have a .print() method; defaults to stdout."""
    text = get_help(topic)
    if io is None:
        print(text)
    else:
        io.print(text)
