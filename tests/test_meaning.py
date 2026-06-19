"""Tests for core/meaning.py — institution-of-meaning interpretation layer (M7.2)."""
import pytest
from core.meaning import (
    InstitutionOfMeaning, MeaningTransform, MeaningState,
    build_meaning_state,
)


def _honor_meaning():
    return InstitutionOfMeaning(
        id='honor_in_death',
        carried_by='veteran_cadre',
        transform=MeaningTransform(
            scale_factors={'downs': 0.6, 'rout': 0.8},
            impulse_terms={'expose': -0.2},
        ),
        failure_conditions=['cadre_officer_killed', 'pay_arrears > 3'],
        break_effect=MeaningTransform(),  # identity: raw cues after break
    )


# ---------------------------------------------------------------------------
# InstitutionOfMeaning

class TestInstitutionOfMeaning:
    def test_requires_failure_conditions(self):
        with pytest.raises(ValueError, match="failure_conditions must not be empty"):
            InstitutionOfMeaning(
                id='bad', carried_by='nobody',
                transform=MeaningTransform(),
                failure_conditions=[],    # EMPTY — must fail
            )

    def test_active_by_default(self):
        m = _honor_meaning()
        assert m.active is True

    def test_break_deactivates(self):
        m = _honor_meaning()
        m.break_meaning()
        assert m.active is False

    def test_active_transform_scales_cues(self):
        m = _honor_meaning()
        raw = {'downs': 1.0, 'rout': 0.5, 'expose': 0.8}
        tx = m.current_transform()
        result = tx.apply(raw)
        assert abs(result['downs'] - 0.6) < 1e-6
        assert abs(result['rout'] - 0.4) < 1e-6
        assert abs(result['expose'] - 0.6) < 1e-6

    def test_broken_meaning_uses_break_effect(self):
        m = _honor_meaning()
        m.break_meaning()
        raw = {'downs': 1.0, 'rout': 0.5}
        tx = m.current_transform()
        result = tx.apply(raw)
        # break_effect is identity → unchanged
        assert abs(result['downs'] - 1.0) < 1e-6
        assert abs(result['rout'] - 0.5) < 1e-6

    def test_unknown_cues_pass_through(self):
        m = _honor_meaning()
        raw = {'fat': 0.3, 'unknown_cue': 0.9}
        result = m.current_transform().apply(raw)
        assert abs(result['fat'] - 0.3) < 1e-6
        assert abs(result['unknown_cue'] - 0.9) < 1e-6


# ---------------------------------------------------------------------------
# MeaningState

class TestMeaningState:
    def _make_state(self):
        return MeaningState({
            0: [dict(
                id='honor_in_death',
                carried_by='veteran_cadre',
                transform={'scale_factors': {'downs': 0.6}, 'impulse_terms': {}},
                failure_conditions=['cadre_killed'],
            )],
            1: [dict(
                id='follow_a_winner',
                carried_by='paymaster',
                transform={'scale_factors': {'fat': 0.7}, 'impulse_terms': {}},
                failure_conditions=['paymaster_absent'],
            )],
        })

    def test_cohort_0_transform_applied(self):
        ms = self._make_state()
        cues = {'downs': 1.0, 'fat': 0.5}
        result = ms.transform_cues(0, cues)
        assert abs(result['downs'] - 0.6) < 1e-6
        assert abs(result['fat'] - 0.5) < 1e-6  # no scale for fat in cohort 0

    def test_cohort_1_transform_applied(self):
        ms = self._make_state()
        cues = {'downs': 1.0, 'fat': 0.5}
        result = ms.transform_cues(1, cues)
        assert abs(result['downs'] - 1.0) < 1e-6  # no scale for downs in cohort 1
        assert abs(result['fat'] - 0.35) < 1e-6

    def test_unknown_cohort_returns_unchanged(self):
        ms = self._make_state()
        cues = {'downs': 1.0}
        result = ms.transform_cues(99, cues)
        assert result == {'downs': 1.0}

    def test_sever_carrier_breaks_meaning(self):
        ms = self._make_state()
        broken = ms.sever_carrier('veteran_cadre')
        assert 'honor_in_death' in broken
        assert ms.active_count() == 1  # only follow_a_winner still active

    def test_sever_unknown_carrier_no_op(self):
        ms = self._make_state()
        broken = ms.sever_carrier('nobody')
        assert broken == []
        assert ms.active_count() == 2


# ---------------------------------------------------------------------------
# build_meaning_state

class TestBuildMeaningState:
    def test_returns_none_if_no_meanings(self):
        scn = {'cohorts': []}
        assert build_meaning_state(scn) is None

    def test_builds_from_scenario(self):
        scn = {
            'meanings': {
                0: [dict(
                    id='test',
                    carried_by='officer',
                    transform={'scale_factors': {'downs': 0.5}, 'impulse_terms': {}},
                    failure_conditions=['officer_dead'],
                )]
            }
        }
        ms = build_meaning_state(scn)
        assert ms is not None
        cues = ms.transform_cues(0, {'downs': 1.0})
        assert abs(cues['downs'] - 0.5) < 1e-6


# ---------------------------------------------------------------------------
# Integration: meaning transform in Battle (M7.2 hook in lattice)

class TestMeaningInBattle:
    def test_battle_runs_with_meaning(self):
        from core.lattice import Battle
        from core.scenarios.agincourt import agincourt

        scn = agincourt()
        # Add a meaning to English (cohort 0) — death as honor
        scn['meanings'] = {
            0: [dict(
                id='english_resolve',
                carried_by='english_commanders',
                transform={
                    'scale_factors': {'downs': 0.7, 'rout': 0.8},
                    'impulse_terms': {},
                },
                failure_conditions=['leaders_all_fallen'],
            )]
        }
        r = Battle(scn, seed=42).run()
        assert r['win'] in (0, 1, -1)

    def test_meaning_severs_on_leader_call(self):
        from core.lattice import Battle
        from core.scenarios.agincourt import agincourt

        scn = agincourt()
        scn['meanings'] = {
            1: [dict(
                id='french_honor',
                carried_by='french_constable',
                transform={'scale_factors': {'expose': 0.5}, 'impulse_terms': {}},
                failure_conditions=['constable_falls'],
            )]
        }
        b = Battle(scn, seed=1)
        broken = b.sever_meaning_carrier('french_constable')
        assert 'french_honor' in broken
