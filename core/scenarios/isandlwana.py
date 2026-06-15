"""Scenario inputs: only class B/C/D/E receipts + geometry. No quality coefficients."""


def isandlwana_line():
    # 1:10. British thin extended line, ammo point at camp; Zulu horns.
    # Side0=British (+x facing, holds), Side1=Zulu advancing -x
    co = []
    co.append(dict(side=0, n=69, x=(196,204), y=(120,480), hold=1, ranged=1, ammo=8,
                   err=0.7, armor=0.0, belief=0.75, disc=0.7, fat0=0.05))   # 24th + colonials: drilled, paid (E,C)
    co.append(dict(side=0, n=66, x=(186,194), y=(60,150), hold=1, err=1.4, armor=0.0,
                   belief=0.35, disc=0.2, fat0=0.05))                        # NNC: untrained, weak cause-bond
    co.append(dict(side=1, n=900, x=(620,700), y=(170,430), err=0.8, belief=0.85,
                   evade=1, fat0=0.10, crowd_cap=14, disc=0.6))              # chest (veterans)
    co.append(dict(side=1, n=600, x=(640,720), y=(380,580), err=0.85, belief=0.85,
                   evade=1, fat0=0.10, crowd_cap=14, disc=0.5))              # left horn
    co.append(dict(side=1, n=300, x=(620,700), y=(20,140), err=0.85, belief=0.85,
                   evade=1, fat0=0.12, crowd_cap=14, disc=0.5))              # right horn
    co.append(dict(side=1, n=160, x=(30,70), y=(100,500), advdir=+1, delay=600,
                   err=0.85, belief=0.85, evade=1, fat0=0.15, disc=0.5))    # encircling horn tip
    return dict(field=(800,600), cohorts=co, range={0:120}, supply_xy=(150,300),
                supply_side=0, supply_d0=100, break_frac=0.5,
                pursuit_intensity={1:1.0, 0:0.2}, cap_p={})


def isandlwana_square():
    co = []
    co.append(dict(side=0, n=69, x=(180,200), y=(280,330), hold=1, ranged=1, ammo=8, allround=1,
                   err=0.7, armor=0.0, belief=0.8, disc=0.8, fat0=0.05))
    co.append(dict(side=1, n=900, x=(620,700), y=(170,430), err=0.8, belief=0.85, evade=1, fat0=0.10, crowd_cap=12, disc=0.6))
    co.append(dict(side=1, n=600, x=(640,720), y=(380,580), err=0.85, belief=0.85, evade=1, fat0=0.10, crowd_cap=12, disc=0.5))
    co.append(dict(side=1, n=300, x=(620,700), y=(20,140), err=0.85, belief=0.85, evade=1, fat0=0.12, crowd_cap=12, disc=0.5))
    co.append(dict(side=1, n=100, x=(30,70), y=(180,420), advdir=+1, delay=600, err=0.85, belief=0.85, evade=1, fat0=0.15, disc=0.5))
    return dict(field=(800,600), cohorts=co, range={0:120}, supply_xy=(190,305),
                supply_side=0, supply_d0=400, break_frac=0.5,
                pursuit_intensity={1:1.0, 0:0.2}, cap_p={})
