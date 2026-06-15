"""MARCHLAND core: march model v2 (Day Layer).

Three ACOUP-critique loops:
  Loop 1 — water (no local water = cannot go there; carrying collapses range)
  Loop 2 — consumption-vs-capacity (train eats; forage is swept area x density x season)
  Loop 3 — constants registry split (A=bodies, B=transport, C=geography, D=institutions)

Universal pipeline; culture enters as data via scenario dicts.
"""
import numpy as np
from .constants import GRAIN_KG, WATER_KG, SPEED, DAYLIGHT, THIRST_K, MODES


# Default scenario values (Class C/D receipts — overridden per scenario)
_DEFAULTS = dict(
    rest_every=0, roads=1, road_quality=1.0, forage=True, dispersal=0.25,
    screen_miles=8, land_density=14, season='dry', season_factor=1.0,
    stock_days=8, stock_cap_days=10, water_ok=1.0, heat=1.0, weather=1.0,
    disease_env=1.0, officers=0.85, camp_quality=0.8, home_pull=0.5,
    pay_arrears=0.0, desert_share=0.5, cohesion0=0.8, fat0=0.1, max_days=60,
)


def scenario(**kw):
    """Build a march scenario dict from defaults, overriding with kw."""
    s = dict(_DEFAULTS); s.update(kw); return s


def run_march(scn, seed):
    r = np.random.default_rng(seed)
    N = scn['start']; sick=0; strag=0; des=0; dead=0
    coh = scn['cohesion0']; fat = scn['fat0']
    carriers = dict(scn['carriers'])
    stock = scn['stock_days'] * (N*GRAIN_KG + sum(MODES[m]['eat']*n for m,n in carriers.items()))
    water_carried = scn.get('water_carry_days', 1.0)
    dry_streak = 0
    miles=0.0; day=0; log=[]
    while miles < scn['distance'] and day < scn['max_days']:
        day += 1
        eff = max(N - sick - strag, 0)
        rest = scn['rest_every'] and day % scn['rest_every'] == 0
        # need vs capacity vs intake
        animal_eat = sum(MODES[m]['eat']*n for m,n in carriers.items())
        if scn['season'] == 'green' and not rest:
            animal_eat *= 0.6
        need = eff*GRAIN_KG + animal_eat
        intake = 0.0
        if day % scn.get('depot_every', 10**6) == 0:
            intake += need * scn.get('depot_days', 0)
        if scn['forage'] and not rest:
            swept = scn['screen_miles']*2 * (scn['pace'] * scn['dispersal'] + 4)
            avail = swept * scn['land_density'] * 1000 * scn['season_factor']
            intake += min(avail * 0.10, need*1.6) * (0.5+0.5*coh)
        stock = min(stock + intake - need, need*scn['stock_cap_days'])
        starving = stock < 0
        # water
        dry = r.random() > scn['water_ok']
        if dry:
            dry_streak += 1
            if dry_streak > water_carried:
                lost = r.binomial(eff, min(THIRST_K*scn['heat'],0.5))
                dead += lost; N -= lost
                fat = min(1.0, fat+0.10)
        else: dry_streak = 0
        # column physics
        vcap = min(MODES[m]['vcap'] for m,n in carriers.items() if n>0) if carriers else SPEED
        col = N/1000*0.20 + sum(MODES[m]['col']*n for m,n in carriers.items())/1.0
        clear_h = col/scn['roads'] / vcap
        usable = max(DAYLIGHT - clear_h, 4.0)
        cap = usable * min(vcap, SPEED) * scn['road_quality']
        grazing_tax = 0.85 if (scn['season']=='green' and any(m in ('pack','ox','wagon') for m in carriers)) else 1.0
        done = 0 if rest else min(scn['pace'], cap) * grazing_tax
        congested = (not rest) and scn['pace'] > cap + 0.5
        # fatigue and cohesion
        hard = max(done/13.0, 0.6)
        fat = float(np.clip(fat + (0 if rest else 0.025*hard**2) + (0.03 if starving else 0)
                            - (0.06 if rest else 0.015), 0, 1))
        coh -= (0.030 if done > 14 else 0) + 0.025*scn['dispersal'] \
               + (0.05 if (starving and r.random()<0.7) else 0) + scn.get('rumor_pressure',0)*0.005
        camp_q = scn['camp_quality']*(0.5 if congested else 1.0)*(0.6 if scn.get('harassed') else 1.0)*(0.7 if dry else 1.0)
        coh = float(np.clip(coh + (0.10 if rest else 0.035*camp_q*scn['officers']), 0, 1))
        # outflows: stragglers, deserters, disease
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
