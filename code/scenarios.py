"""Scenario inputs: only class B/C/D/E receipts + geometry. No quality coefficients."""

def isandlwana_line():
    # 1:10. British thin extended line, ammo point at camp; Zulu horns. Side0=British(+x facing... holds), Side1=Zulu adv -x
    co = []
    co.append(dict(side=0, n=69, x=(196,204), y=(120,480), hold=1, ranged=1, ammo=8,
                   err=0.7, armor=0.0, belief=0.75, disc=0.7, fat0=0.05))           # 24th + colonials: drilled, paid (E,C receipts)
    co.append(dict(side=0, n=66, x=(186,194), y=(60,150), hold=1, err=1.4, armor=0.0,
                   belief=0.35, disc=0.2, fat0=0.05))                               # NNC: untrained, 1/10 firearms, weak cause-bond (receipts)
    co.append(dict(side=1, n=900, x=(620,700), y=(170,430), err=0.8, belief=0.85,
                   evade=1, fat0=0.10, crowd_cap=14, disc=0.6))                     # chest (veterans: drilled repertoire)
    co.append(dict(side=1, n=600, x=(640,720), y=(380,580), err=0.85, belief=0.85,
                   evade=1, fat0=0.10, crowd_cap=14, disc=0.5))                     # left horn
    co.append(dict(side=1, n=300, x=(620,700), y=(20,140), err=0.85, belief=0.85,
                   evade=1, fat0=0.12, crowd_cap=14, disc=0.5))                     # right horn
    co.append(dict(side=1, n=160, x=(30,70), y=(100,500), advdir=+1, delay=600,
                   err=0.85, belief=0.85, evade=1, fat0=0.15, disc=0.5))            # encircling horn tip arrives behind (scripted sweep, as the paper scripted vectors)
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

def agincourt():
    co = []
    co.append(dict(side=0, n=100, x=(140,150), y=(80,180), hold=1, err=0.75, armor=0.9,
                   belief=0.85, disc=0.8, fat0=0.05))                                # English MAA: harness, cornered+led (C receipts)
    co.append(dict(side=0, n=250, x=(135,155), y=(10,80),  hold=1, ranged=1, ammo=12,
                   err=0.85, armor=0.15, belief=0.85, disc=0.6, fat0=0.05))          # archers south wedge
    co.append(dict(side=0, n=250, x=(135,155), y=(180,250), hold=1, ranged=1, ammo=12,
                   err=0.85, armor=0.15, belief=0.85, disc=0.6, fat0=0.05))          # archers north wedge
    co.append(dict(side=1, n=120, x=(560,620), y=(20,240), mounted=1, armor=0.5,
                   belief=0.7, err=0.9, fat0=0.05))                                  # French cavalry wings
    co.append(dict(side=1, n=450, x=(560,640), y=(60,200), err=0.95, armor=0.9,
                   belief=0.7, fat0=0.10, crowd_cap=7))                              # 1st battle dismounted (command chaos -> crowding receipts)
    co.append(dict(side=1, n=450, x=(640,700), y=(60,200), delay=700, err=0.95,
                   armor=0.85, belief=0.65, fat0=0.10, crowd_cap=7))                 # 2nd battle
    return dict(field=(700,260), cohorts=co, range={0:170}, stakes_x=170,
                mud=(190,520), break_frac=0.45,
                pursuit_intensity={0:0.45, 1:0.8}, cap_p={1:0.6})

def hastings(fyrd_disc=0.22):
    co = []
    co.append(dict(side=0, n=100, x=(330,340), y=(150,250), hold=1, err=0.75, armor=0.8,
                   belief=0.8, disc=0.9, fat0=0.05))                                  # huscarls
    co.append(dict(side=0, n=600, x=(320,345), y=(40,360), hold=1, err=1.3, armor=0.45,
                   belief=0.75, disc=fyrd_disc, fat0=0.15))                           # fyrd (marched from Stamford: C receipt)
    co.append(dict(side=1, n=150, x=(520,560), y=(80,320), ranged=1, ammo=8, hold=1,
                   err=0.9, armor=0.3, belief=0.75, fat0=0.05))                       # Norman archers
    co.append(dict(side=1, n=350, x=(480,540), y=(60,340), err=0.9, armor=0.5,
                   belief=0.78, fat0=0.05, crowd_cap=12))                             # Norman foot
    co.append(dict(side=1, n=250, x=(560,620), y=(60,340), mounted=1, armor=0.6,
                   belief=0.78, err=0.85, fat0=0.05))                                 # Norman cavalry
    return dict(field=(700,400), cohorts=co, range={1:150}, mud=(360,470),
                feints=[(900,0),(1800,0)], leader_risk={0:(12.0,0.003,4000)},
                break_frac=0.45, pursuit_intensity={1:0.85, 0:0.3}, cap_p={0:0.15})

def hastings_drilled(): return hastings(fyrd_disc=0.8)
def hastings_p1():
    s = hastings(); s['cohorts'][1]['n'] = 601; return s
def hastings_p2():
    s = hastings(); s['cohorts'][0]['x'] = (331,341); return s

def escalade(garrison_fat=0.05, garrison_belief=0.8,
             gates=((70,74),(105,109),(140,144),(175,179),(210,214),(245,249)), per_gate=5):
    co = []
    gd = dict(side=0, hold=1, cover_bonus=1.0, err=0.9, armor=0.35,
              belief=garrison_belief, disc=0.7, fat0=garrison_fat)
    used = 0
    for g in gates:                       # the garrison mans the threatened points
        co.append(dict(n=per_gate, x=(144,150), y=(g[0]-2, g[1]+2), **gd)); used += per_gate
    co.append(dict(n=max(40-used, 6), x=(144,150), y=(60,240), **gd))   # thin watch + reserve
    co.append(dict(side=1, n=200, x=(210,260), y=(40,260), err=1.0, armor=0.35,
                   belief=0.65, disc=0.5, fat0=0.10, crowd_cap=8))
    return dict(field=(300,300), cohorts=co, break_frac=0.45, carry_n=30,
                wall=(150, list(gates), 0),
                pursuit_intensity={0:0.5, 1:0.9}, cap_p={})

def escalade_fresh(): return escalade(0.05, 0.8)
def breach(garrison_fat, garrison_belief):
    return escalade(garrison_fat, garrison_belief, gates=((130,154,'breach'),), per_gate=14)
def breach_fresh(): return breach(0.05, 0.8)
def breach_starved(): return breach(0.55, 0.55)
def escalade_starved(): return escalade(0.55, 0.55)

def agincourt_marched():
    s = agincourt()
    for c in s['cohorts']:
        if c['side']==0: c['fat0'] = 0.25     # the march's bill, after one night's rest
    return s

SCN = dict(agincourt_marched=agincourt_marched, escalade_fresh=escalade_fresh, escalade_starved=escalade_starved, breach_fresh=breach_fresh, breach_starved=breach_starved, isandlwana_line=isandlwana_line, isandlwana_square=isandlwana_square,
           agincourt=agincourt, hastings=hastings, hastings_drilled=hastings_drilled, hastings_p1=hastings_p1, hastings_p2=hastings_p2)
