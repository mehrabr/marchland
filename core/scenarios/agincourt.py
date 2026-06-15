"""Scenario inputs: only class B/C/D/E receipts + geometry. No quality coefficients."""


def agincourt():
    co = []
    co.append(dict(side=0, n=100, x=(140,150), y=(80,180), hold=1, err=0.75, armor=0.9,
                   belief=0.85, disc=0.8, fat0=0.05))                                # English MAA: harness, cornered+led (C)
    co.append(dict(side=0, n=250, x=(135,155), y=(10,80),  hold=1, ranged=1, ammo=12,
                   err=0.85, armor=0.15, belief=0.85, disc=0.6, fat0=0.05))          # archers south wedge
    co.append(dict(side=0, n=250, x=(135,155), y=(180,250), hold=1, ranged=1, ammo=12,
                   err=0.85, armor=0.15, belief=0.85, disc=0.6, fat0=0.05))          # archers north wedge
    co.append(dict(side=1, n=120, x=(560,620), y=(20,240), mounted=1, armor=0.5,
                   belief=0.7, err=0.9, fat0=0.05))                                  # French cavalry wings
    co.append(dict(side=1, n=450, x=(560,640), y=(60,200), err=0.95, armor=0.9,
                   belief=0.7, fat0=0.10, crowd_cap=7))                              # 1st battle dismounted (crowding)
    co.append(dict(side=1, n=450, x=(640,700), y=(60,200), delay=700, err=0.95,
                   armor=0.85, belief=0.65, fat0=0.10, crowd_cap=7))                 # 2nd battle
    return dict(field=(700,260), cohorts=co, range={0:170}, stakes_x=170,
                mud=(190,520), break_frac=0.45,
                pursuit_intensity={0:0.45, 1:0.8}, cap_p={1:0.6})


def agincourt_marched():
    """Agincourt after the full march from Harfleur — one night's rest applied."""
    s = agincourt()
    for c in s['cohorts']:
        if c['side']==0: c['fat0'] = 0.25
    return s
