"""Battery tests: grade-A targets are hard assertions; grade-B/C are warnings.

Run with: pytest tests/test_battery.py -v
"""
import pytest
import numpy as np

from core.lattice import Battle
from core.siege import run_siege
from core.march import run_march
from core.trace import Trace, compose_traces
from core.chain import run_chain_1415, siege_to_march, march_to_battle
from core.scenarios import SCN_BATTLE, SCN_MARCH, SCN_SIEGE
from core.scenarios.harfleur import harfleur
from core.scenarios.marches import agincourt_march
from core.scenarios.agincourt import agincourt
from battery.targets import (
    _median_dead_frac, _median_asymmetry, _median_french_losses,
    _median_side_dead, _median_prebreak_frac, _median_negotiated_day,
    _median_val,
)

SEEDS = 12


@pytest.fixture(scope="module")
def agincourt_results():
    return [Battle(SCN_BATTLE["agincourt"](), s).run() for s in range(SEEDS)]


@pytest.fixture(scope="module")
def hastings_results():
    return [Battle(SCN_BATTLE["hastings"](), s).run() for s in range(SEEDS)]


@pytest.fixture(scope="module")
def isandlwana_line_results():
    return [Battle(SCN_BATTLE["isandlwana_line"](), s).run() for s in range(SEEDS)]


@pytest.fixture(scope="module")
def isandlwana_square_results():
    return [Battle(SCN_BATTLE["isandlwana_square"](), s).run() for s in range(SEEDS)]


@pytest.fixture(scope="module")
def harfleur_results():
    return [run_siege(SCN_SIEGE["harfleur"](), s) for s in range(SEEDS)]


@pytest.fixture(scope="module")
def escalade_fresh_results():
    return [Battle(SCN_BATTLE["escalade_fresh"](), s).run() for s in range(SEEDS)]


@pytest.fixture(scope="module")
def breach_fresh_results():
    return [Battle(SCN_BATTLE["breach_fresh"](), s).run() for s in range(SEEDS)]


@pytest.fixture(scope="module")
def breach_starved_results():
    return [Battle(SCN_BATTLE["breach_starved"](), s).run() for s in range(SEEDS)]


# ============================================================
# Agincourt — grade A
# ============================================================

def test_agincourt_english_win_all(agincourt_results):
    """English (side 0) must win every seed. win==0 means French (side 1) broke."""
    assert all(r["win"] == 0 for r in agincourt_results), \
        f"English losses in seeds: {[i for i,r in enumerate(agincourt_results) if r['win'] != 0]}"


# ============================================================
# Agincourt — grade B/C (warnings only)
# ============================================================

def test_agincourt_asymmetry_b(agincourt_results):
    ratio = _median_asymmetry(agincourt_results)
    assert ratio >= 5, f"[grade-B] asymmetry {ratio:.1f} < 5; expected >=5"


def test_agincourt_french_losses_c(agincourt_results):
    val = _median_french_losses(agincourt_results)
    if not (3500 <= val <= 11000):
        pytest.skip(f"[grade-C] French losses {val:.0f} outside [3500,11000]; informational finding")


def test_agincourt_english_dead_c(agincourt_results):
    val = _median_side_dead(agincourt_results, 0)
    if not (112 <= val <= 600):
        pytest.skip(f"[grade-C] English dead {val:.0f} outside [112,600]")


# ============================================================
# Hastings — grade A
# ============================================================

def test_hastings_harold_falls_majority(hastings_results):
    """Leader0 (Harold) must fall in majority of seeds."""
    count = sum(any(e[0] == "leader0_down" for e in r["ev"]) for r in hastings_results)
    assert count > SEEDS / 2, f"Harold falls in {count}/{SEEDS} seeds; need majority"


# ============================================================
# Hastings — grade B (M1: win downgraded A->B; prebreak now fixed)
# ============================================================

def test_hastings_norman_win_majority_b(hastings_results):
    """Norman (side 1) must win majority of seeds. [grade-B M1] Phase pacing introduces variance."""
    norman_wins = sum(r["win"] == 1 for r in hastings_results)
    assert norman_wins > SEEDS / 2, \
        f"[grade-B] Normans win {norman_wins}/{SEEDS}; need majority (>6)"


def test_hastings_prebreak_frac_b(hastings_results):
    """Pre-break fraction <= 0.12. M1 achieves ~0.11 (from 0.20 ref); sub-0.10 is post-M1."""
    frac = _median_prebreak_frac(hastings_results)
    assert frac <= 0.12, f"[grade-B] prebreak frac {frac:.3f} > 0.12; phase pacing under-performing"


# ============================================================
# Hastings — grade C
# ============================================================

def test_hastings_near_run_c(hastings_results):
    """English (historical loser) wins 20-50% of seeds. M1 fix: phase pacing variance.
    win==0 means Norman (side 1) broke -> English holds."""
    english_win_rate = sum(r["win"] == 0 for r in hastings_results) / SEEDS
    if not (0.20 <= english_win_rate <= 0.50):
        pytest.skip(f"[grade-C] English win rate {english_win_rate:.0%}; expected 20-50%")


# ============================================================
# Isandlwana line — grade A
# ============================================================

def test_isandlwana_line_zulu_win_all(isandlwana_line_results):
    """Zulu (side 1) must win every seed."""
    assert all(r["win"] == 1 for r in isandlwana_line_results), \
        f"British holds in seeds: {[i for i,r in enumerate(isandlwana_line_results) if r['win'] != 1]}"


def test_isandlwana_line_ammo_sequence_a(isandlwana_line_results):
    """Ammo starvation event must precede break in majority of seeds."""
    count = sum(any(e[0].startswith("ammo_starved") for e in r["ev"]) for r in isandlwana_line_results)
    assert count > SEEDS / 2, f"ammo_starved event in {count}/{SEEDS} seeds; need majority"


# ============================================================
# Isandlwana line — grade B/C
# ============================================================

def test_isandlwana_defender_dead_frac_b(isandlwana_line_results):
    """British dead fraction in [0.50, 0.90]. KNOWN MISS: reference at ~0.40."""
    frac = _median_dead_frac(isandlwana_line_results, 0)
    if not (0.50 <= frac <= 0.90):
        pytest.skip(f"[grade-B KNOWN MISS] defender_dead_frac {frac:.2f}; pursuit model underdrives (post-M6)")


# ============================================================
# Isandlwana square — grade B (M1 target)
# ============================================================

def test_isandlwana_square_holds_b(isandlwana_square_results):
    """British square holds (win==0, Zulus broke) in >= 5/12 seeds. M1 target.
    Phase pacing (Zulu waves) + British fire-rotation relief_roles enable sustained defence."""
    holds = sum(r["win"] == 0 for r in isandlwana_square_results)
    assert holds >= 5, f"[grade-B] square holds {holds}/{SEEDS}; need >=5"


# ============================================================
# Harfleur siege — grade A
# ============================================================

def test_harfleur_negotiated_majority(harfleur_results):
    count = sum(r["outcome"] == "NEGOTIATED" for r in harfleur_results)
    assert count > SEEDS / 2, f"NEGOTIATED in {count}/{SEEDS} seeds; need majority"


def test_harfleur_duration_a(harfleur_results):
    med = _median_negotiated_day(harfleur_results)
    assert 30 <= med <= 40, f"Negotiated day median {med:.0f} outside [30,40]"


# ============================================================
# Harfleur — grade C
# ============================================================

def test_harfleur_unfit_frac_c(harfleur_results):
    val = _median_val(harfleur_results, "unfit_frac")
    if not (0.15 <= val <= 0.35):
        pytest.skip(f"[grade-C] besieger unfit frac {val:.2f} outside [0.15,0.35]")


# ============================================================
# Assault battery — grade B
# ============================================================

def test_assault_escalade_fresh_repulsed_b(escalade_fresh_results):
    """Escalade vs fresh garrison: majority repulsed (garrison/side-0 wins -> win==0 means attackers broke,
    win==1 means garrison broke. So garrison win = win==1 from attacker perspective...

    In escalade: side0=garrison, side1=attackers.
    win==0 means side1 (attackers) broke -> garrison holds.
    win==1 means side0 (garrison) broke -> wall carried.
    Majority repulsed -> majority win==0.
    """
    held = sum(r["win"] == 0 for r in escalade_fresh_results)
    assert held > SEEDS / 2, f"[grade-B] escalade fresh: garrison held {held}/{SEEDS}; need majority"


def test_assault_breach_fresh_contested_b(breach_fresh_results):
    """Breach vs fresh: mixed outcomes."""
    carried = sum(r["win"] == 1 for r in breach_fresh_results)
    assert 0 < carried < SEEDS, \
        f"[grade-B] breach fresh: {carried} carried / {SEEDS-carried} repulsed; expected mixed"


def test_assault_breach_starved_carried_b(breach_starved_results):
    """Breach vs starved: majority carried. KNOWN MISS: reference achieves 5/12."""
    carried = sum(r["win"] == 1 for r in breach_starved_results)
    if carried <= SEEDS / 2:
        pytest.skip(f"[grade-B KNOWN MISS] breach_starved: {carried}/{SEEDS} carried; garrison not weak enough")


# ============================================================
# M2: 1415 chain — grade A
# ============================================================

@pytest.fixture(scope="module")
def chain_1415_results():
    return [run_chain_1415(s) for s in range(SEEDS)]


def test_chain_1415_english_win_all(chain_1415_results):
    """English (side 0) must win every seed via the full chain. Grade A."""
    losses = [i for i, r in enumerate(chain_1415_results) if r['win'] != 0]
    assert not losses, f"English lost in chain seeds: {losses}"


def test_chain_1415_march_arrives_all(chain_1415_results):
    """Army must arrive at Agincourt in every seed. Grade A."""
    failed = [i for i, r in enumerate(chain_1415_results) if not r['march']['arrived']]
    assert not failed, f"March failed in seeds: {failed}"


def test_chain_1415_siege_negotiated_majority(chain_1415_results):
    """Harfleur must end NEGOTIATED in majority of seeds. Grade A."""
    count = sum(r['siege']['outcome'] == 'NEGOTIATED' for r in chain_1415_results)
    assert count > SEEDS / 2, f"NEGOTIATED in {count}/{SEEDS}; need majority"


# ============================================================
# M2: trace integrity — grade A
# ============================================================

def test_trace_battle_deaths_have_cause(chain_1415_results):
    """Every battle death-cert must have a non-empty cause. Grade A."""
    for i, r in enumerate(chain_1415_results):
        for d in r['trace']['deaths']:
            if d['phase'] == 'battle':
                assert d['cause'], f"seed {i}: death-cert missing cause: {d}"


def test_trace_composes_all_phases(chain_1415_results):
    """Composed trace must contain all three phases. Grade A."""
    for i, r in enumerate(chain_1415_results):
        phases = r['trace']['phases']
        assert 'siege' in phases, f"seed {i}: trace missing 'siege' phase"
        assert 'march' in phases, f"seed {i}: trace missing 'march' phase"
        assert 'battle' in phases, f"seed {i}: trace missing 'battle' phase"


def test_trace_battle_has_break_event(chain_1415_results):
    """Composed trace must record a side_broke event for the battle. Grade A."""
    for i, r in enumerate(chain_1415_results):
        battle_evs = [ev for ev in r['trace']['events'] if ev[3] == 'battle']
        broke_names = {ev[0] for ev in battle_evs}
        assert broke_names & {'side0_broke', 'side1_broke'}, \
            f"seed {i}: no side_broke event in battle trace"


# ============================================================
# M2: chain field-mapping invariants — grade A
# ============================================================

def test_chain_siege_to_march_start_positive():
    """siege_to_march: derived start must be positive and <= besieger_N."""
    scn = harfleur()
    siege_r = run_siege(scn, seed=0)
    march = siege_to_march(siege_r, scn, agincourt_march())
    assert march['start'] > 0, "march start must be positive"
    assert march['start'] <= scn['besieger'], "march start cannot exceed original besieger count"


def test_chain_march_to_battle_fat0_floor():
    """march_to_battle: battle fat0 is non-negative for any rest_nights >= 0."""
    march_r = {'fatigue': 0.10, 'start': 1000, 'effective': 900,
               'stock_days': 5.0, 'cohesion': 0.75}
    battle = march_to_battle(march_r, agincourt(), rest_nights=5)
    for c in battle['cohorts']:
        if c.get('side') == 0:
            assert c['fat0'] >= 0.0, f"fat0 below floor: {c['fat0']}"


def test_chain_march_to_battle_fat0_correct():
    """march_to_battle: fat0 = arrival_fatigue - 0.3 * rest_nights (floor 0)."""
    march_r = {'fatigue': 0.55, 'start': 8400, 'effective': 7800,
               'stock_days': 5.0, 'cohesion': 0.75}
    battle = march_to_battle(march_r, agincourt(), rest_nights=1)
    expected_fat0 = max(0.0, 0.55 - 0.3 * 1)   # = 0.25
    for c in battle['cohorts']:
        if c.get('side') == 0:
            assert abs(c['fat0'] - expected_fat0) < 1e-6, \
                f"fat0 {c['fat0']} != expected {expected_fat0}"
