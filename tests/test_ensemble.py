"""Tests for tools/ensemble.py.

Verifies outcome distribution, language gating, and coverage of all scenario types.
"""
import pytest
from tools.ensemble import run_ensemble, _language_gate, _extract_primary_outcome, _majority


# ── language gate unit tests ──────────────────────────────────────────────────

def test_language_gate_decisive():
    assert _language_gate(0.76) == "decisive"
    assert _language_gate(1.0) == "decisive"


def test_language_gate_likely():
    assert _language_gate(0.70) == "likely"
    assert _language_gate(0.60) == "likely"


def test_language_gate_near_run():
    assert _language_gate(0.55) == "near-run"
    assert _language_gate(0.45) == "near-run"


def test_language_gate_contested():
    assert _language_gate(0.44) == "contested"
    assert _language_gate(0.0) == "contested"


# ── majority helper ───────────────────────────────────────────────────────────

def test_majority_empty():
    outcome, frac = _majority([])
    assert outcome is None
    assert frac == 0.0


def test_majority_unanimous():
    outcome, frac = _majority([0, 0, 0, 0])
    assert outcome == 0
    assert frac == 1.0


def test_majority_split():
    outcome, frac = _majority([0, 0, 1])
    assert outcome == 0
    assert abs(frac - 2 / 3) < 1e-9


# ── extract_primary_outcome ───────────────────────────────────────────────────

def test_extract_battle_outcome():
    assert _extract_primary_outcome({"win": 0}, "battle") == 0
    assert _extract_primary_outcome({"win": 1}, "battle") == 1


def test_extract_march_outcome():
    assert _extract_primary_outcome({"arrived": True}, "march") is True
    assert _extract_primary_outcome({"arrived": False}, "march") is False


def test_extract_siege_outcome():
    r = {"outcome": "NEGOTIATED"}
    assert _extract_primary_outcome(r, "siege") == "NEGOTIATED"


def test_extract_chain_outcome():
    r = {"battle": {"win": 0}}
    assert _extract_primary_outcome(r, "chain") == 0


# ── integration: run_ensemble on real scenarios (fast, 4 seeds) ───────────────

@pytest.mark.parametrize("scn,expected_type", [
    ("agincourt", "battle"),
    ("harfleur", "siege"),
    ("agincourt_march", "march"),
])
def test_ensemble_runs_and_returns_language(scn, expected_type):
    result = run_ensemble(scn, seeds=4)
    assert result["scenario"] == scn
    assert result["scn_type"] == expected_type
    assert result["seeds"] == 4
    assert len(result["results"]) == 4
    assert result["language"] in ("decisive", "likely", "near-run", "contested")
    assert isinstance(result["near_run"], bool)
    assert 0.0 <= result["majority_fraction"] <= 1.0


def test_ensemble_chain_type():
    result = run_ensemble("chain_1415", seeds=2)
    assert result["scn_type"] == "chain"
    assert result["language"] in ("decisive", "likely", "near-run", "contested")


def test_ensemble_unknown_scenario_raises():
    with pytest.raises(ValueError, match="Unknown scenario"):
        run_ensemble("nonexistent_battle_1066", seeds=2)


def test_ensemble_agincourt_decisive():
    """Agincourt should be decisive over a realistic seed count (English always win)."""
    result = run_ensemble("agincourt", seeds=12)
    assert result["majority_fraction"] == 1.0
    assert result["language"] == "decisive"
    assert not result["near_run"]


def test_ensemble_outcome_counts_sum_to_seeds():
    seeds = 6
    result = run_ensemble("agincourt", seeds=seeds)
    assert sum(result["outcome_counts"].values()) == seeds
