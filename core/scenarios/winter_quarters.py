"""Scenario inputs for winter quarters dissolution (M7.5).

An army of 4,000 men sits in winter quarters on a siege line — unpaid,
under-supplied, idle for 60 days. No combat occurs. The army dissolves
through tracked receipts: idle + hunger + arrears drive desertion and
disease faster than cohesion recovers. Sentiment field amplifies this.

Battery target: effective_frac < 0.50 (army loses more than half its
strength without a single battle — demonstrating armies break between
battles, the genre's historical truth).

Receipts:
  pay_arrears=1.0: paymaster has not arrived (D receipt)
  home_pull=0.85: winter + siege stagnation amplifies homeward pull (C receipt)
  disease_env=2.5: wet siege camp conditions (C receipt: camp quality)
  forage=False: winter; no food in the surrounding fields (C receipt: season)
  stock_days=8: 8 days of supplies at march model
  officers=0.55: officers demoralized (D receipt: pay arrears cascade)
  rumor_pressure=12: high idle-time rumor mill (C receipt: idle days)
"""
from ..march import scenario as march_scenario


def winter_quarters():
    """Return a march scenario dict configured for winter quarters dissolution."""
    return march_scenario(
        start=4000,
        distance=9999,        # unreachable objective — army sits still
        pace=0.0,             # no marching pace (stationary camp)
        rest_every=1,         # every day is a rest day (idle)
        forage=False,         # no foraging in winter siege (C receipt: season)
        stock_days=8,         # 8 days of initial supply
        stock_cap_days=10,
        water_ok=0.85,        # siege conditions; wells not always clean
        pay_arrears=1.0,      # fully unpaid (D receipt: paymaster absent)
        home_pull=0.85,       # strong pull home in winter (C receipt)
        disease_env=2.5,      # wet siege camp (C receipt: camp quality below 0.5)
        camp_quality=0.40,    # poor camp (C receipt)
        officers=0.55,        # officer authority degraded (D receipt: arrears)
        cohesion0=0.70,       # army starts moderately cohesive
        fat0=0.15,            # some accumulated fatigue from siege work
        rumor_pressure=12,    # idle-time rumor mill (C receipt: idle days)
        season='dry',
        season_factor=0.3,    # winter: reduced land density
        carriers={'ox': 4},   # minimal supply train
        max_days=60,          # one winter season
        num_cohorts=4,        # for sentiment field
        officer_authority=0.55,
    )
