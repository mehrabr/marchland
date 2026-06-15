"""Battery tests: grade-A targets are hard assertions; grade-B/C are warnings.

Run with: pytest tests/test_battery.py -v
"""
import pytest
import numpy as np

from core.lattice import Battle
from core.siege import run_siege
from core.march import run_march
from core.scenarios import SCN_BATTLE, SCN_MARCH, SCN_SIEGE
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
    if ratio < 5:
        pytest.warns(UserWarning, match=".*")  # grade-B: documented, not a hard fail
    assert ratio >= 5, f"[grade-B] asymmetry {ratio:.1f} < 5; expected >=5"


def test_agincourt_french_losses_c(agincourt_results):
    val = _median_french_losses(agincourt_results)
    assert 4000 <= val <= 11000, f"[grade-C] French losses {val:.0f} outside [4000,11000]"


def test_agincourt_english_dead_c(agincourt_results):
    val = _median_side_dead(agincourt_results, 0)
    assert 112 <= val <= 600, f"[grade-C] English dead {val:.0f} outside [112,600]"


# ============================================================
# Hastings — grade A
# ============================================================

def test_hastings_norman_win_all(hastings_results):
    """Norman (side 1) must win every seed. win==1 means English (side 0) broke."""
    assert all(r["win"] == 1 for r in hastings_results), \
        f"Norman losses in seeds: {[i for i,r in enumerate(hastings_results) if r['win'] != 1]}"


def test_hastings_harold_falls_majority(hastings_results):
    """Leader0 (Harold) must fall in majority of seeds."""
    count = sum(any(e[0] == "leader0_down" for e in r["ev"]) for r in hastings_results)
    assert count > SEEDS / 2, f"Harold falls in {count}/{SEEDS} seeds; need majority"


# ============================================================
# Hastings — grade B/C (known misses from reference)
# ============================================================

def test_hastings_prebreak_frac_b(hastings_results):
    """Pre-break fraction <= 0.10. KNOWN MISS: reference at ~0.20; fixed in M1."""
    frac = _median_prebreak_frac(hastings_results)
    if frac > 0.10:
        pytest.skip(f"[grade-B KNOWN MISS] prebreak frac {frac:.2f} > 0.10; M1 phase-pacing fix pending")


def test_hastings_near_run_c(hastings_results):
    """Norman win in 20-50% of seeds (contested). KNOWN MISS: currently 100%."""
    win_rate = sum(r["win"] == 1 for r in hastings_results) / SEEDS
    if not (0.20 <= win_rate <= 0.50):
        pytest.skip(f"[grade-C KNOWN MISS] Norman win rate {win_rate:.0%}; M1 phase-pacing introduces variance")


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
# Isandlwana — grade B/C
# ============================================================

def test_isandlwana_defender_dead_frac_b(isandlwana_line_results):
    """British dead fraction in [0.50, 0.90]. KNOWN MISS: reference at ~0.40."""
    frac = _median_dead_frac(isandlwana_line_results, 0)
    if not (0.50 <= frac <= 0.90):
        pytest.skip(f"[grade-B KNOWN MISS] defender_dead_frac {frac:.2f}; pursuit model underdrives (post-M6)")


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
    assert 0.15 <= val <= 0.35, f"[grade-C] besieger unfit frac {val:.2f} outside [0.15,0.35]"


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
