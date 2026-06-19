"""Tests for tools/sensitivity.py — M7.1 class-A constant perturbation harness.

These tests are smoke tests only: the full run_sensitivity() is expensive (all
constants × ±delta × seeds × all targets) and belongs in CI as a report,
not in the default pytest suite. We verify:
  - _collect_class_a() returns a non-empty dict of scalars
  - _apply_perturbation() and _restore() round-trip correctly
  - print_table() does not crash on empty and non-empty findings
  - A 1-constant × 1-seed smoke test produces consistent output
"""
import pytest
import core.constants as constants_module
from tools.sensitivity import (
    _collect_class_a,
    _apply_perturbation,
    _restore,
    print_table,
)


# ---------------------------------------------------------------------------
# _collect_class_a

class TestCollectClassA:
    def test_returns_nonempty_dict(self):
        entries = _collect_class_a()
        assert isinstance(entries, dict)
        assert len(entries) > 0

    def test_all_values_are_scalars(self):
        entries = _collect_class_a()
        for name, val in entries.items():
            assert isinstance(val, (int, float)), (
                f"Expected scalar for {name!r}, got {type(val)}"
            )

    def test_includes_battle_a_constants(self):
        entries = _collect_class_a()
        # At least one BATTLE_A constant should appear
        battle_keys = [k for k in entries if k.startswith('BATTLE_A.')]
        assert len(battle_keys) > 0

    def test_includes_march_constants(self):
        entries = _collect_class_a()
        assert 'GRAIN_KG' in entries
        assert 'WATER_KG' in entries
        assert 'SPEED' in entries

    def test_no_non_numeric_values(self):
        entries = _collect_class_a()
        for name, val in entries.items():
            assert not isinstance(val, (str, list, dict)), (
                f"{name!r} has non-scalar type {type(val)}"
            )


# ---------------------------------------------------------------------------
# _apply_perturbation and _restore round-trip

class TestApplyAndRestore:
    def test_grain_kg_round_trips(self):
        original = constants_module.GRAIN_KG
        _apply_perturbation('GRAIN_KG', original, 1.30)
        assert abs(constants_module.GRAIN_KG - original * 1.30) < 1e-9
        _restore('GRAIN_KG', original)
        assert abs(constants_module.GRAIN_KG - original) < 1e-9

    def test_water_kg_round_trips(self):
        original = constants_module.WATER_KG
        _apply_perturbation('WATER_KG', original, 0.70)
        assert abs(constants_module.WATER_KG - original * 0.70) < 1e-9
        _restore('WATER_KG', original)
        assert abs(constants_module.WATER_KG - original) < 1e-9

    def test_battle_a_scalar_round_trips(self):
        # Find a BATTLE_A scalar key
        entries = _collect_class_a()
        scalar_keys = [k for k in entries if k.startswith('BATTLE_A.') and '.' == k[8:].count('.') * 0 + k.count('.') - 1]
        battle_flat = [k for k in entries if k.startswith('BATTLE_A.') and k.count('.') == 1]
        assert len(battle_flat) > 0, "No flat BATTLE_A scalars found"
        name = battle_flat[0]
        base_val = entries[name]
        key = name.split('.')[1]
        original_in_dict = constants_module.BATTLE_A[key]
        _apply_perturbation(name, base_val, 1.20)
        assert abs(constants_module.BATTLE_A[key] - base_val * 1.20) < 1e-9
        _restore(name, base_val)
        assert abs(constants_module.BATTLE_A[key] - original_in_dict) < 1e-9

    def test_restore_identity(self):
        """_restore with factor=1.0 should be a no-op."""
        original = constants_module.SPEED
        _restore('SPEED', original)
        assert constants_module.SPEED == original


# ---------------------------------------------------------------------------
# print_table

class TestPrintTable:
    def test_empty_findings(self, capsys):
        print_table([])
        captured = capsys.readouterr()
        assert 'SENSITIVITY REPORT' in captured.out

    def test_load_bearing_findings(self, capsys):
        findings = [
            {
                'constant': 'BATTLE_A.lam0',
                'perturbation': '+30%',
                'target': 'agincourt.win',
                'baseline_pass': True,
                'perturbed_pass': False,
                'classification': 'load-bearing',
            },
        ]
        print_table(findings)
        captured = capsys.readouterr()
        assert 'LOAD-BEARING' in captured.out
        assert 'agincourt.win' in captured.out

    def test_decorative_findings(self, capsys):
        findings = [
            {
                'constant': 'GRAIN_KG',
                'perturbation': '-30%',
                'target': 'hastings.win',
                'baseline_pass': True,
                'perturbed_pass': True,
                'classification': 'decorative',
            },
        ]
        print_table(findings)
        captured = capsys.readouterr()
        assert 'SENSITIVITY REPORT' in captured.out

    def test_mixed_findings(self, capsys):
        findings = [
            {
                'constant': 'BATTLE_A.fat_amp',
                'perturbation': '+30%',
                'target': 'agincourt.win',
                'baseline_pass': True,
                'perturbed_pass': False,
                'classification': 'load-bearing',
            },
            {
                'constant': 'GRAIN_KG',
                'perturbation': '+30%',
                'target': 'agincourt.win',
                'baseline_pass': True,
                'perturbed_pass': True,
                'classification': 'decorative',
            },
        ]
        print_table(findings)
        captured = capsys.readouterr()
        assert 'Total findings: 2' in captured.out


# ---------------------------------------------------------------------------
# Smoke: 1-constant, 1-seed perturbation run

class TestSensitivitySmoke:
    def test_single_constant_perturbation_does_not_crash(self):
        """Perturb SPEED ±30% with 1 seed; verify the harness completes."""
        from battery.runner import run_scenario
        from battery.targets import TARGETS

        const_name = 'SPEED'
        base_val = constants_module.SPEED
        findings = []

        for factor, label in [(1.30, '+30%'), (0.70, '-30%')]:
            _apply_perturbation(const_name, base_val, factor)
            # Run one fast march scenario (1 seed)
            try:
                results = run_scenario('agincourt_march', seeds=1)
                pass_result = True  # didn't crash
            except Exception:
                pass_result = False
            finally:
                _restore(const_name, base_val)
            findings.append({'constant': const_name, 'perturbation': label, 'passed': pass_result})

        assert all(f['passed'] for f in findings), f"Perturbation crashed: {findings}"

    def test_collect_and_restore_all_constants(self):
        """Collect all class-A constants and verify they can be perturbed and restored."""
        entries = _collect_class_a()
        for name, base_val in list(entries.items())[:5]:   # first 5 only for speed
            _apply_perturbation(name, base_val, 1.10)
            _restore(name, base_val)
        # After restore, all should be at original value
        entries_after = _collect_class_a()
        for name, base_val in list(entries.items())[:5]:
            assert abs(entries_after[name] - base_val) < 1e-9, (
                f"{name}: expected {base_val}, got {entries_after[name]}"
            )
