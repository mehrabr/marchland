"""Tests for battery/ci.py: entry coverage check.

Validates that the CI gate correctly detects missing entries and that
all current TARGETS have entries.
"""
import pytest
from battery.ci import check_entry_coverage
from battery.runner import load_entries
from battery.targets import TARGETS


def test_all_targets_have_entries():
    """Every key in TARGETS must have a corresponding entry in battery/entries/."""
    missing = check_entry_coverage()
    assert not missing, (
        f"Missing battery entries for: {missing}\n"
        "Add JSON entry to battery/entries/<scenario>.json"
    )


def test_entries_load_without_error():
    """load_entries() must return a non-empty dict with no parse errors."""
    entries = load_entries()
    assert isinstance(entries, dict)
    assert entries, "battery/entries/ must contain at least one JSON file"


def test_entries_format_correct():
    """Each entry must be a 5-element list: [range, grade, source_note, actual, pass]."""
    entries = load_entries()
    for key, value in entries.items():
        assert isinstance(value, list), f"{key}: entry must be a list, got {type(value)}"
        assert len(value) == 5, f"{key}: entry must have 5 elements [range, grade, source_note, actual, pass], got {len(value)}"
        grade = value[1]
        assert grade in ("A", "B", "C"), f"{key}: grade must be A/B/C, got {grade!r}"


def test_entry_grades_match_targets():
    """Grade declared in entry JSON must match the grade in TARGETS."""
    entries = load_entries()
    mismatches = []
    for key, spec in TARGETS.items():
        if key not in entries:
            continue
        entry_grade = entries[key][1]
        targets_grade = spec["grade"]
        if entry_grade != targets_grade:
            mismatches.append(f"{key}: entry={entry_grade!r} targets={targets_grade!r}")
    assert not mismatches, (
        "Grade mismatch between entries JSON and targets.py:\n" +
        "\n".join(f"  {m}" for m in mismatches)
    )


def test_no_extra_entries():
    """Entries JSON should not reference keys absent from TARGETS (stale entries)."""
    entries = load_entries()
    stale = [key for key in entries if key not in TARGETS]
    assert not stale, (
        f"Stale entries in battery/entries/ (not in TARGETS): {stale}\n"
        "Remove them or add matching TARGETS entries."
    )
