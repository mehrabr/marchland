"""MARCHLAND core: operational siege clock (day ticks).

Dual-clock model: besieger's disease/supply clock races the town's hunger/wall clock.
Summons-and-terms negotiation (conditional surrender) is the usual historical ending.
Class A constants frozen; scenario inputs are receipts (guns, marsh camp, sea supply).
"""
import numpy as np
from .constants import SIEGE_A as A


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
        b_dead += r.binomial(new_sick, 0.25)
        eff = bN - b_sick - b_dead
        # besieger supply clock
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
        # summons and terms — the usual ending
        honor_ok = breach >= A['honor_breach'] or day >= A['honor_days'] or stock < 10
        relief_hopeless = (relief_day is None) or (relief_day - day > 21)
        if honor_ok and relief_hopeless and terms_day is None and r.random() < 0.22:
            terms_day = day + A['relief_window']
            log.append(('terms_struck', day))
        if terms_day and day >= terms_day:
            outcome = ('NEGOTIATED', day); break
        # besieger storm decision
        pressure = (b_sick+b_dead)/bN + scn.get('season_pressure',0)*week/10
        cost = A['breach_storm_cost'] if breach >= 1.0 else A['nobreach_storm_cost']
        if breach >= 1.0 and pressure > scn['storm_threshold'] and terms_day is None:
            dead = int(eff*cost*r.uniform(0.7,1.3))
            b_dead += dead
            if r.random() < 0.85:
                outcome = ('STORMED_sack', day); break
            else:
                breach = 0.4; log.append(('assault_repulsed', day))
    if outcome is None: outcome = ('ONGOING', day)
    unfit = b_sick + b_dead
    return dict(outcome=outcome[0], day=outcome[1], dead=int(b_dead),
                sick=int(b_sick), unfit_frac=round(unfit/bN,3),
                breach=round(min(breach,1.0),2), log=log[:4])
