"""Scenario inputs: only class B/C/D/E receipts + geometry. No quality coefficients."""


def escalade(garrison_fat=0.05, garrison_belief=0.8,
             gates=((70,74),(105,109),(140,144),(175,179),(210,214),(245,249)), per_gate=5):
    co = []
    gd = dict(side=0, hold=1, cover_bonus=1.0, err=0.9, armor=0.35,
              belief=garrison_belief, disc=0.7, fat0=garrison_fat)
    used = 0
    for g in gates:
        co.append(dict(n=per_gate, x=(144,150), y=(g[0]-2, g[1]+2), **gd)); used += per_gate
    co.append(dict(n=max(40-used, 6), x=(144,150), y=(60,240), **gd))  # thin watch + reserve
    co.append(dict(side=1, n=200, x=(210,260), y=(40,260), err=1.0, armor=0.35,
                   belief=0.65, disc=0.5, fat0=0.10, crowd_cap=8))
    return dict(field=(300,300), cohorts=co, break_frac=0.45, carry_n=30,
                wall=(150, list(gates), 0),
                pursuit_intensity={0:0.5, 1:0.9}, cap_p={})


def escalade_fresh():
    return escalade(0.05, 0.8)


def escalade_starved():
    return escalade(0.55, 0.55)


def breach(garrison_fat, garrison_belief):
    return escalade(garrison_fat, garrison_belief, gates=((130,154,'breach'),), per_gate=14)


def breach_fresh():
    return breach(0.05, 0.8)


def breach_starved():
    return breach(0.55, 0.55)
