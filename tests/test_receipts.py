"""Tests for tools/receipts_grep.py.

Verifies that the receipts grep:
  - passes on clean scenario/culture files
  - detects injected quality coefficients
  - detects strength_modifier and morale_bonus patterns
"""
import textwrap
import pytest
from pathlib import Path
from tools.receipts_grep import scan_file, FORBIDDEN


# ── helpers ──────────────────────────────────────────────────────────────────

def _write_temp(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "test_scenario.py"
    p.write_text(textwrap.dedent(content))
    return p


# ── clean-file tests ──────────────────────────────────────────────────────────

def test_clean_file_no_violations(tmp_path):
    path = _write_temp(tmp_path, """
        COHORT = {"side": 0, "n": 6000, "fat0": 0.1, "horse": True}
        SCENARIO = {"name": "agincourt", "cohorts": [COHORT]}
    """)
    assert scan_file(path) == []


def test_comment_line_skipped(tmp_path):
    path = _write_temp(tmp_path, """
        # quality = 1.5  (not used here — Law 1)
        COHORT = {"side": 0, "n": 6000}
    """)
    assert scan_file(path) == [], "Comment-only lines must not trigger violation"


def test_real_scenarios_clean():
    """No violations in the committed scenario files."""
    from tools.receipts_grep import SCAN_DIRS
    any_found = False
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        for path in sorted(d.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            hits = scan_file(path)
            if hits:
                any_found = True
                for lineno, text in hits:
                    print(f"  VIOLATION {path}:{lineno}: {text.strip()}")
    assert not any_found, "Real scenario/culture files contain quality coefficients — spec violation"


# ── violation-detection tests ─────────────────────────────────────────────────

def test_detects_quality_field(tmp_path):
    path = _write_temp(tmp_path, """
        COHORT = {"side": 0, "n": 6000, "quality": 1.5}
    """)
    hits = scan_file(path)
    assert hits, "Expected violation for 'quality' field"
    assert any("quality" in text for _, text in hits)


def test_detects_morale_bonus(tmp_path):
    path = _write_temp(tmp_path, """
        COHORT = {"morale_bonus": 0.2, "n": 500}
    """)
    hits = scan_file(path)
    assert hits, "Expected violation for 'morale_bonus'"


def test_detects_strength_modifier(tmp_path):
    path = _write_temp(tmp_path, """
        stats = {"strength_modifier": 1.3}
    """)
    hits = scan_file(path)
    assert hits, "Expected violation for 'strength_modifier'"


def test_detects_coeff(tmp_path):
    path = _write_temp(tmp_path, """
        UNIT = {"coeff": 0.9, "side": 1}
    """)
    hits = scan_file(path)
    assert hits, "Expected violation for 'coeff'"


def test_detects_modifier_standalone(tmp_path):
    path = _write_temp(tmp_path, """
        params = {"modifier": 1.1}
    """)
    hits = scan_file(path)
    assert hits, "Expected violation for 'modifier'"


def test_violation_reports_line_number(tmp_path):
    content = "x = 1\ny = {'quality': 2}\nz = 3\n"
    path = tmp_path / "scn.py"
    path.write_text(content)
    hits = scan_file(path)
    assert hits, "Expected a violation"
    lineno, _ = hits[0]
    assert lineno == 2, f"Expected violation on line 2, got {lineno}"


def test_multiple_violations_all_reported(tmp_path):
    path = _write_temp(tmp_path, """
        A = {"quality": 1.0}
        B = {"morale_bonus": 0.1}
    """)
    hits = scan_file(path)
    assert len(hits) >= 2, f"Expected >=2 violations, got {len(hits)}"
