"""Tutorial skirmish scenario: English escort vs French blocking force.

A French column contests the Ardres road. The English escort (200 agents,
representing ~2000 men) has archers on both flanks and men-at-arms in the
centre. The French (150 agents, ~1500 men) advance down the road without
missile cover.

At the engine's standard scale (1 agent ≈ 10 men), this is a real engagement,
not a border skirmish. It is "small" only relative to full pitched battles
like Agincourt (2000+ agents per side). Teaching scenario — not registered in
the battery (no historical calibration target exists for this encounter).

Class B receipts: armor, longbow ammo
Class C receipts: fat0 (fatigue carried from the march)
Class E receipts: volley discipline (err)
"""


def tutorial_skirmish(fat0: float = 0.05):
    """Road engagement, English escort vs French blocking force.

    fat0 is the starting fatigue for English troops; passed from the march result.
    """
    co = []

    # English men-at-arms — center, hold
    co.append(dict(
        side=0, n=100, x=(60, 100), y=(50, 180),
        hold=1, err=0.75, armor=0.80,
        belief=0.80, disc=0.75, fat0=fat0,
        # B: partial harness (armor=0.80)
        # C: committed escort (belief=0.80, hold)
    ))
    # English archers — south flank
    co.append(dict(
        side=0, n=50, x=(50, 90), y=(0, 50),
        hold=1, ranged=1, ammo=8,
        err=0.85, armor=0.15, belief=0.80, disc=0.60, fat0=fat0,
        # B: longbow, 8 sheaves; E: trained volley (err=0.85)
    ))
    # English archers — north flank
    co.append(dict(
        side=0, n=50, x=(50, 90), y=(180, 230),
        hold=1, ranged=1, ammo=8,
        err=0.85, armor=0.15, belief=0.80, disc=0.60, fat0=fat0,
        # B: longbow, 8 sheaves; E: trained volley (err=0.85)
    ))
    # French blocking force — lighter armor, lower belief (patrol, not pitched army)
    co.append(dict(
        side=1, n=150, x=(380, 450), y=(30, 200),
        err=0.90, armor=0.50, belief=0.65, fat0=0.10,
        # B: mixed armor (armor=0.50)
        # C: lower belief (0.65) — road force, not battle-hardened line
    ))

    return dict(
        field=(500, 230),
        cohorts=co,
        range={0: 160},             # English archers fire within 160 x-units
        break_frac=0.40,
        pursuit_intensity={0: 0.30, 1: 0.55},
    )
