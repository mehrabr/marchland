"""MARCHLAND siege clock: operational siege model (day ticks).
Not the Day Layer — a scenario-scale dual-clock model: the besieger's disease/supply
clock races the town's hunger/wall clock, with the summons-and-terms negotiation
(conditional surrender) as the usual ending, per the historical record.
Class A constants frozen; scenario inputs are receipts (guns, marsh camp, sea supply).
"""
import numpy as np, json, sys

A = dict(
    dis_base=0.0012,      # per-man/day disease hazard, week 1, decent camp
    dis_week=0.55,        # hazard growth per week encamped (filth accumulates)
    breach_storm_cost=0.18,# expected assault losses vs practicable breach (fraction)
    nobreach_storm_cost=0.45,
    honor_breach=1.0,     # garrison may yield with honor once breach practicable
    honor_days=28,        # or after a creditable duration
    relief_window=8,      # days of grace garrisons ask for (send to your king)
)

def run_siege(scn, seed):
    r = np.random.default_rng(seed)
    bN = scn['besieger']; gN = scn['garrison']
    b_sick = 0; b_dead = 0
    stock = scn['town_food_days']
    breach = 0.0
    relief_day = scn['relief_day']() if callable(scn['relief_day']) else scn['relief_day']
    terms_day = None; outcome = None; day = 0
    log = []
    while day < scn.get('max_days', 80):
        day += 1
        week = day/7
        # besieger disease clock (marsh camps, summer heat are receipts)
        hz = A['dis_base']*(1+A['dis_week']*week)*scn['camp_factor']
        new_sick = r.binomial(max(bN-b_sick-b_dead,0), min(hz,0.5))
        b_sick += new_sick
        b_dead += r.binomial(new_sick, 0.25)  # case fatality over course
        eff = bN - b_sick - b_dead
        # besieger supply clock (sea-supplied sieges don't starve; land ones may)
        if not scn['sea_supply']:
            scn['besieger_food'] -= 1
            if scn['besieger_food'] <= 0:
                outcome = ('ABANDONED_supply', day); break
        # battery and mining
        breach += scn['guns_rate']*r.uniform(0.7,1.3)*(eff/bN)
        # town hunger
        stock -= 1
        # relief check
        if relief_day is not None and day >= relief_day:
            outcome = ('RELIEVED', day); break
        # --- summons and terms (the usual ending) ---
        # garrison appraisal: yield honorably if breach practicable or starvation near,
        # AND relief looks improbable within the customary window
        honor_ok = breach >= A['honor_breach'] or day >= A['honor_days'] or stock < 10
        relief_hopeless = (relief_day is None) or (relief_day - day > 21)
        if honor_ok and relief_hopeless and terms_day is None and r.random() < 0.22:
            terms_day = day + A['relief_window']   # conditional surrender pact
            log.append(('terms_struck', day))
        if terms_day and day >= terms_day:
            outcome = ('NEGOTIATED', day); break
        # --- besieger storm decision ---
        # storm only under clock pressure: own disease biting or season/relief pressure
        pressure = (b_sick+b_dead)/bN + scn.get('season_pressure',0)*week/10
        cost = A['breach_storm_cost'] if breach >= 1.0 else A['nobreach_storm_cost']
        if breach >= 1.0 and pressure > scn['storm_threshold'] and terms_day is None:
            dead = int(eff*cost*r.uniform(0.7,1.3))
            b_dead += dead
            if r.random() < 0.85:  # practicable breach usually carries
                outcome = ('STORMED_sack', day); break
            else:
                breach = 0.4; log.append(('assault_repulsed', day))
    if outcome is None: outcome = ('ONGOING', day)
    unfit = b_sick + b_dead
    return dict(outcome=outcome[0], day=outcome[1], dead=int(b_dead),
                sick=int(b_sick), unfit_frac=round(unfit/bN,3),
                breach=round(min(breach,1.0),2), log=log[:4])

def harfleur(relief=None):
    return dict(besieger=11500, garrison=400, town_food_days=55,
                guns_rate=0.034,          # 12 great guns vs strong walls: ~30d to practicable
                camp_factor=2.2,          # marshy ground, August heat, shellfish: the receipts
                sea_supply=True, relief_day=relief, storm_threshold=0.30,
                season_pressure=1.0, max_days=70)

if __name__ == '__main__':
    seeds = int(sys.argv[1]) if len(sys.argv)>1 else 100
    variant = sys.argv[2] if len(sys.argv)>2 else 'base'
    scn_f = (lambda: harfleur(relief=25)) if variant=='relief25' else (lambda: harfleur())
    out = [run_siege(scn_f(), s) for s in range(seeds)]
    json.dump(out, open(f'/home/claude/res_siege_{variant}.json','w'))
    oc = {}
    for o in out: oc[o['outcome']] = oc.get(o['outcome'],0)+1
    days = [o['day'] for o in out if o['outcome']=='NEGOTIATED']
    print('harfleur', variant, 'outcomes:', oc)
    if days: print(' negotiated day median %d (range %d-%d)' % (np.median(days), min(days), max(days)))
    print(' besieger unfit median %.0f%%  dead median %d' % (
        100*np.median([o['unfit_frac'] for o in out]), np.median([o['dead'] for o in out])))
