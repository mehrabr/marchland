"""Scenario inputs: only class B/C/D/E receipts + geometry. No quality coefficients.

Sphacteria 425 BC — Athenian encirclement of the Spartan garrison on the island.

Historical: ~420 Spartiate hoplites stranded on a narrow island after a storm
cut off their fleet. Athenian and Messenian light troops (psiloi + archers)
land from multiple sides and systematically strip the Spartan advantage:
  - The hoplite phalanx cannot form proper ranks (rocky terrain, brush fires)
  - Messenian guides know the terrain; Spartans are blinded by smoke
  - Sustained ranged harassment drives Spartan casualties past morale threshold
  - 292 Spartiate dead; 120 survivors surrender (unprecedented)

Receipts:
  Side 0 (Spartans, side=0):
    hold=1, allround=1: disciplined rear-guard fighting in broken terrain
    belief=0.95: Spartiates' training and shame-culture (D receipt: agoge)
    disc=0.95: agoge discipline (E receipt: years of training)
    armor=0.8: full bronze panoply (B receipt: state-issued)
    err=0.55: legendary formation drill (E receipt)
    fat0=0.25: days cut off, water scarce (C receipt: siege state)
    relief_roles=1: files rotate in agoge-trained lochoi (E receipt)

  Side 1 (Athenians + Messenians):
    ranged=1: archers + javelin men (B receipt: bows + xyston)
    allround=1: dispersed encircling attack from island perimeter
    belief=0.75: motivated but not elite (C receipt: political cause)
    armor=0.05: light-armed psiloi (B receipt: minimal protection)
    err=1.10: less disciplined volley (E receipt)
    disc=0.60: democratic assembly troops

M7.0 battery target: convergent_horn=True enables encirclement.
Expected: Athenians win majority; Spartan dead fraction 50-75% (historical ~70%).
"""


def sphacteria():
    co = []

    # Spartan garrison — compact all-round defensive knot
    co.append(dict(
        side=0, n=42, x=(330, 470), y=(220, 380),
        hold=1, allround=1,
        err=0.55, armor=0.8, belief=0.95, disc=0.95,
        fat0=0.25, relief_roles=1,
    ))

    # Athenian archers and hoplites — main frontal pressure
    co.append(dict(
        side=1, n=90, x=(560, 700), y=(150, 450),
        ranged=1, evade=1, allround=1,
        err=1.10, armor=0.05, belief=0.75, disc=0.60,
        fat0=0.05, ammo=12,
    ))

    # Messenian guides — secondary encircling force from north
    co.append(dict(
        side=1, n=50, x=(350, 500), y=(480, 580),
        advdir=-1,  # approach from the north (y-axis flip)
        ranged=1, evade=1,
        err=1.05, armor=0.05, belief=0.80, disc=0.65,
        fat0=0.08, ammo=10,
    ))

    # Athenian naval landing — completes encirclement from behind
    co.append(dict(
        side=1, n=40, x=(80, 160), y=(200, 400),
        advdir=+1, delay=400,   # delayed beach landing
        ranged=1, evade=1,
        err=1.15, armor=0.05, belief=0.70, disc=0.55,
        fat0=0.10, ammo=8,
    ))

    return dict(
        field=(800, 600),
        cohorts=co,
        range={1: 100},           # javelin + short bow (B receipt)
        break_frac={0: 0.55, 1: 0.60},  # Spartans hold until 55% gone (historical shame-threshold)
        pursuit_intensity={1: 0.8, 0: 0.1},
        cap_p={0: 0.30},          # 120 survivors captured (B: surrender is possible when surrounded)
        convergent_horn=True,     # M7.0: encirclement kill bonus
        horn_kill_multiplier=2.0, # island geometry concentrates fire
    )
