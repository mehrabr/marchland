"""Tutorial march scenario: escort from Calais to Ardres, autumn 1415.

300 men on good roads with adequate supply. A manageable five-day march
for teaching the march model — designed to arrive without drama.

Class B receipts: wagon+porter transport, king's road quality
Class C receipts: 7 days stock, good water, dry season, fresh troops
Class D receipts: competent officers, small camp
"""
from ..march import scenario


def tutorial_escort_march():
    """Small escort march: 300 men, 50 miles, ~5 days on the king's road."""
    return scenario(
        start=300,
        distance=50,
        pace=10.0,            # B: road-limited escort pace (~10 miles/day)
        carriers={'wagon': 4, 'porter': 8},   # B: small supply train
        stock_days=7,         # C: 7 days of grain and fodder in hand
        stock_cap_days=10,
        water_ok=0.92,        # C: Norman roads, frequent wells
        season='dry',
        season_factor=0.9,
        land_density=20,      # C: Norman countryside — adequate forage
        officers=0.90,        # D: competent centenar in charge
        camp_quality=0.85,    # D: small force, easy to camp
        cohesion0=0.85,       # C: fresh retinue, no prior campaign stress
        fat0=0.05,            # C: starting fresh
        home_pull=0.10,       # D: men are away from home but not far
        pay_arrears=0.0,      # D: paid at commission start
        desert_share=0.2,
        disease_env=0.8,      # C: autumn, no summer heat
        heat=0.8,
        weather=1.0,
        max_days=12,          # hard cap; 5 days normal, 12 days = deadline
        roads=1,
        road_quality=1.0,     # B: the king's road; no mud
        rest_every=0,
        forage=True,
        dispersal=0.20,
        screen_miles=4,
    )
