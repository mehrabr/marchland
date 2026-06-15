"""MARCHLAND Day Layer v2: the march model after three ACOUP-critique loops.
Loop 1 added water (no local water = you cannot go there; carrying it collapses range).
Loop 2 added the consumption-vs-capacity equation (the train eats; forage is swept
area x density x season; standing still depletes the radius).
Loop 3 split the constants registry: A = bodies, B = transport technology,
C = geography/season, D = institutions. Universal pipeline; culture enters as data.
"""
import numpy as np, json, sys

# ---- class A: bodies (every human, every era) ----
GRAIN_KG = 1.4        # man/day staple equivalent
WATER_KG = 3.0        # man/day; carrying it triples the load
SPEED    = 2.5        # mph, the eternal constant of feet
DAYLIGHT = 10.0
THIRST_K = 0.06       # per-man/day casualties once dry beyond carried water

# ---- class B: transport technology (receipts; mixable) ----
MODES = dict(            # net payload kg, own consumption kg/day (food+hard fodder), speed cap mph
    porter=dict(load=30,  eat=1.4,  vcap=2.5, col=0.001),
    pack  =dict(load=100, eat=6.0,  vcap=2.5, col=0.003),   # grazes when green & time allows
    ox    =dict(load=540, eat=12.0, vcap=2.0, col=0.012),   # 2 mph, 5 effective hours
    wagon =dict(load=550, eat=22.0, vcap=2.5, col=0.0125),  # ACW: ~80 wagons to the mile   # two horses + driver
)

def run_march(scn, seed):
    r = np.random.default_rng(seed)
    N = scn['start']; sick=0; strag=0; des=0; dead=0
    coh = scn['cohesion0']; fat = scn['fat0']
    carriers = dict(scn['carriers'])             # {'wagon': 800, ...}
    stock = scn['stock_days'] * (N*GRAIN_KG + sum(MODES[m]['eat']*n for m,n in carriers.items()))
    water_carried = scn.get('water_carry_days', 1.0)
    dry_streak = 0
    miles=0.0; day=0; log=[]
    while miles < scn['distance'] and day < scn['max_days']:
        day += 1
        eff = max(N - sick - strag, 0)
        rest = scn['rest_every'] and day % scn['rest_every'] == 0
        # ---- the equation: need vs capacity vs intake
        animal_eat = sum(MODES[m]['eat']*n for m,n in carriers.items())
        if scn['season'] == 'green' and not rest:
            animal_eat *= 0.6                    # grazing offsets, at the cost of march time
        need = eff*GRAIN_KG + animal_eat
        intake = 0.0
        if day % scn.get('depot_every', 10**6) == 0:
            intake += need * scn.get('depot_days', 0)
        if scn['forage'] and not rest:
            swept = scn['screen_miles']*2 * (scn['pace'] * scn['dispersal'] + 4)
            avail = swept * scn['land_density'] * 1000 * scn['season_factor']
            intake += min(avail * 0.10, need*1.6) * (0.5+0.5*coh)   # 10% take on the move; order helps
        stock = min(stock + intake - need, need*scn['stock_cap_days'])
        starving = stock < 0
        # ---- water: no local water means you cannot go there unless you carry it
        dry = r.random() > scn['water_ok']
        if dry:
            dry_streak += 1
            if dry_streak > water_carried:
                lost = r.binomial(eff, min(THIRST_K*scn['heat'],0.5))
                dead += lost; N -= lost
                fat = min(1.0, fat+0.10)
        else: dry_streak = 0
        # ---- column physics: the slowest mode and the longest tail govern
        vcap = min(MODES[m]['vcap'] for m,n in carriers.items() if n>0) if carriers else SPEED
        col = N/1000*0.20 + sum(MODES[m]['col']*n for m,n in carriers.items())/1.0
        clear_h = col/scn['roads'] / vcap
        usable = max(DAYLIGHT - clear_h, 4.0)
        cap = usable * min(vcap, SPEED) * scn['road_quality']
        grazing_tax = 0.85 if (scn['season']=='green' and any(m in ('pack','ox','wagon') for m in carriers)) else 1.0
        done = 0 if rest else min(scn['pace'], cap) * grazing_tax
        congested = (not rest) and scn['pace'] > cap + 0.5
        # ---- fatigue & cohesion
        hard = max(done/13.0, 0.6)
        fat = float(np.clip(fat + (0 if rest else 0.025*hard**2) + (0.03 if starving else 0)
                            - (0.06 if rest else 0.015), 0, 1))
        coh -= (0.030 if done > 14 else 0) + 0.025*scn['dispersal'] \
               + (0.05 if (starving and r.random()<0.7) else 0) + scn.get('rumor_pressure',0)*0.005
        camp_q = scn['camp_quality']*(0.5 if congested else 1.0)*(0.6 if scn.get('harassed') else 1.0)*(0.7 if dry else 1.0)
        coh = float(np.clip(coh + (0.10 if rest else 0.035*camp_q*scn['officers']), 0, 1))
        # ---- the three outflows
        s_rate = 0.004*(max(done,6)/13)**2.2*(1+1.5*fat)*scn['weather']*(3.0 if starving else 1)*(1.5 if dry_streak else 1)
        new_s = r.binomial(eff, min(s_rate,0.5)); strag += new_s
        strag -= r.binomial(strag, 0.55*scn['officers']*camp_q)
        lost = r.binomial(strag, 0.18); strag -= lost
        des += int(lost*scn['desert_share']); dead += lost - int(lost*scn['desert_share'])
        d_rate = 0.0015*scn['home_pull']*(1+3*scn['pay_arrears'])*(0.5+scn['dispersal'])*(3.0 if starving else 1)*(2-coh)
        nd = r.binomial(eff, min(d_rate,0.3)); des += nd; N -= nd
        hz = 0.0009*scn['disease_env']*(1.6 if starving else 1)
        ns = r.binomial(eff, min(hz,0.3)); sick += ns
        dead += r.binomial(ns,0.2); sick = max(sick - int(ns*0.2) - r.binomial(max(sick,0),0.06), 0)
        for ev_day, extra in scn.get('detours', []):
            if day == ev_day: scn['distance'] += extra; log.append(('detour',day,extra))
        miles += done
    return dict(arrived=miles>=scn['distance'], days=day, start=scn['start'],
                effective=int(max(N-sick-strag-dead,0)), sick=int(sick), stragglers=int(strag),
                deserted=int(des), dead=int(dead), fatigue=round(fat,2), cohesion=round(coh,2),
                stock_days=round(float(stock/max(N*GRAIN_KG,1)),1), log=log[:3])

D = dict(rest_every=0, roads=1, road_quality=1.0, forage=True, dispersal=0.25, screen_miles=8,
         land_density=14, season='dry', season_factor=1.0, stock_days=8, stock_cap_days=10,
         water_ok=1.0, heat=1.0, weather=1.0, disease_env=1.0, officers=0.85, camp_quality=0.8,
         home_pull=0.5, pay_arrears=0.0, desert_share=0.5, cohesion0=0.8, fat0=0.1, max_days=60)

def S(**kw):
    s = dict(D); s.update(kw); return s

def agincourt_march(): return S(start=8400, distance=200, pace=15.5, carriers={'wagon':60,'pack':200},
    land_density=14, season_factor=0.7, stock_days=8, weather=1.5, officers=0.85, camp_quality=0.7,
    home_pull=0.05, pay_arrears=0.2, desert_share=0.3, cohesion0=0.75, fat0=0.20,
    rumor_pressure=1.0, detours=[(8,60)], max_days=22)
def danube_1704(): return S(start=21000, distance=250, pace=9.5, rest_every=4, roads=2,
    carriers={'wagon':1700}, forage=False, depot_every=4, depot_days=5, stock_days=6,
    dispersal=0.05, disease_env=0.9, officers=1.0, camp_quality=1.0, home_pull=0.5,
    desert_share=0.8, cohesion0=0.85, fat0=0.05, max_days=45)
def niemen_1812(): return S(start=286000, distance=520, pace=11.0, roads=3, road_quality=0.8,
    carriers={'wagon':9000}, land_density=10, season='dry', season_factor=0.8, stock_days=24,
    dispersal=0.5, screen_miles=15, weather=1.4, disease_env=2.6, officers=0.55, camp_quality=0.5,
    home_pull=0.7, pay_arrears=0.3, desert_share=0.6, fat0=0.05, max_days=78)
def gedrosia_325(): return S(start=40000, distance=460, pace=12.0, carriers={'pack':3000},
    land_density=0.6, season_factor=0.4, stock_days=10, water_ok=0.62, water_carry_days=1.5,
    heat=1.5, weather=1.3, disease_env=1.2, officers=0.7, camp_quality=0.5, home_pull=0.05,
    desert_share=0.1, cohesion0=0.8, fat0=0.15, max_days=70)
def sherman_1864(): return S(start=62000, distance=285, pace=12.0, roads=4, road_quality=1.0,
    carriers={'wagon':2500}, land_density=22, season_factor=1.1, stock_days=20, dispersal=0.6,
    screen_miles=25, officers=0.95, camp_quality=0.95, home_pull=0.3, desert_share=0.7,
    cohesion0=0.9, fat0=0.05, max_days=40)

SCN = dict(agincourt_march=agincourt_march, danube_1704=danube_1704, niemen_1812=niemen_1812,
           gedrosia_325=gedrosia_325, sherman_1864=sherman_1864)

if __name__ == '__main__':
    name = sys.argv[1]; seeds = int(sys.argv[2]) if len(sys.argv)>2 else 100
    out = [run_march(SCN[name](), s) for s in range(seeds)]
    json.dump(out, open(f'/home/claude/res_march_{name}.json','w'))
    print(name, 'arrived %d/%d  days med %d' % (sum(o['arrived'] for o in out), len(out),
          np.median([o['days'] for o in out])))
    for k in ['effective','sick','stragglers','deserted','dead']:
        print('  %-10s med %6d' % (k, np.median([o[k] for o in out])))
    print('  fatigue %.2f  cohesion %.2f  stock_days %.1f' % tuple(
        np.median([[o['fatigue'],o['cohesion'],o['stock_days']] for o in out], axis=0)))
