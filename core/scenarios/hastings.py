"""Scenario inputs: only class B/C/D/E receipts + geometry. No quality coefficients."""


def hastings(fyrd_disc=0.22):
    co = []
    co.append(dict(side=0, n=100, x=(330,340), y=(150,250), hold=1, err=0.75, armor=0.8,
                   belief=0.8, disc=0.9, fat0=0.05, relief_roles=1))                  # huscarls (rank-relief: D receipt)
    co.append(dict(side=0, n=600, x=(320,345), y=(40,360), hold=1, err=1.3, armor=0.45,
                   belief=0.75, disc=fyrd_disc, fat0=0.15))                           # fyrd (marched from Stamford: C receipt)
    co.append(dict(side=1, n=150, x=(520,560), y=(80,320), ranged=1, ammo=8, hold=1,
                   err=0.9, armor=0.3, belief=0.75, fat0=0.05))                       # Norman archers
    co.append(dict(side=1, n=350, x=(480,540), y=(60,340), err=0.9, armor=0.5,
                   belief=0.78, fat0=0.05, crowd_cap=12, assault_wave=1))             # Norman foot (assault-wave doctrine: D receipt)
    co.append(dict(side=1, n=250, x=(560,620), y=(60,340), mounted=1, armor=0.6,
                   belief=0.78, err=0.85, fat0=0.05, assault_wave=1))                 # Norman cavalry (charges and reforms: D receipt)
    return dict(field=(700,400), cohorts=co, range={1:150}, mud=(360,470),
                feints=[(900,0),(1800,0)], leader_risk={0:(12.0,0.003,4000)},
                break_frac=0.45, pursuit_intensity={1:0.85, 0:0.3}, cap_p={0:0.15})


def hastings_drilled():
    return hastings(fyrd_disc=0.8)


def hastings_p1():
    s = hastings(); s['cohorts'][1]['n'] = 601; return s


def hastings_p2():
    s = hastings(); s['cohorts'][0]['x'] = (331,341); return s
