"""Scenario inputs: only class B/C/D/E receipts + geometry. No quality coefficients.

Carrhae 53 BC — Parthian horse-archer encirclement of a Roman column.

Historical: Crassus leads ~35,000 Romans into open Mesopotamian steppe.
Parthian cataphracts anchor the center while horse archers encircle and
volley the Roman formation. The Roman square (testudo) holds for hours
until camels resupply the Parthian arrow line. Eventually the square breaks
under relentless arrow fire and the pursuit is devastating.

Receipts explaining each cohort's parameters:
  Side 0 (Romans, side=0):
    hold=1, allround=1: testudo square formation (D receipt: drilled shield-drill)
    belief=0.80: loyal legionary cohort (C receipt: oaths + pay)
    disc=0.90: veteran centurionate discipline (E receipt: drill years)
    armor=0.7: lorica segmentata + scutum (B receipt: issued by state)
    err=0.65: ordered ranks, minimal drill error (E receipt)
    fat0=0.12: day's march in heat before contact (C receipt: travel)
    relief_roles=1: century rotation (D/E receipt: relief-in-ranks doctrine)

  Side 1 (Parthians, side=1):
    mounted=1, ranged=1, evade=1: horse archers (B receipt: Parthian horse)
    ammo=999: resupplied from camel trains (D receipt: supply chain)
    belief=0.80: fighting for king and kin (C receipt)
    armor=0.0: light horse (B receipt: no bronze plate)
    err=0.90: mounted bowmen, inherent accuracy variance (E receipt)

M7.0 battery target: convergent_horn=True to close the circle.
Expected: Parthians win all seeds; Romans take 60-80% casualties (historical ~65%).
"""


def carrhae():
    co = []

    # Roman infantry square — ~10,000 in the field formation
    co.append(dict(
        side=0, n=100, x=(340, 460), y=(200, 400),
        hold=1, allround=1,
        err=0.65, armor=0.7, belief=0.80, disc=0.90,
        fat0=0.12, relief_roles=1,
    ))

    # Parthian cataphracts — heavy cavalry anchor, keeps the square from dispersing
    co.append(dict(
        side=1, n=60, x=(550, 650), y=(250, 350),
        mounted=1, err=0.70, armor=0.6, belief=0.85,
        disc=0.85, fat0=0.05, crowd_cap=10,
    ))

    # Parthian horse archers — main killing mechanism, encircle and volley
    co.append(dict(
        side=1, n=200, x=(560, 700), y=(80, 520),
        mounted=1, ranged=1, evade=1,
        err=0.90, armor=0.0, belief=0.80,
        disc=0.70, fat0=0.05, ammo=999,  # camel resupply (D receipt: logistics)
    ))

    # Parthian encircling horn — closes behind the Roman column
    co.append(dict(
        side=1, n=80, x=(50, 130), y=(150, 450),
        advdir=+1, delay=500,  # arrives after initial contact
        mounted=1, ranged=1, evade=1,
        err=0.90, armor=0.0, belief=0.80,
        disc=0.70, fat0=0.10, ammo=200,
    ))

    return dict(
        field=(800, 600),
        cohorts=co,
        range={1: 160},           # Parthian composite bow (B receipt: superior range)
        break_frac={0: 0.45, 1: 0.60},
        pursuit_intensity={1: 1.2, 0: 0.1},  # Parthian pursuit devastating (D receipt)
        cap_p={0: 0.15},          # some Romans captured (historical ~10,000 captured)
        convergent_horn=True,     # M7.0: encirclement kill bonus
        horn_kill_multiplier=2.5, # convergent bow fire from all sides
    )
