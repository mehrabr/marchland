"""MARCHLAND scenario: Cannae, 216 BC.

The capstone officer-AI + meaning-layer entry (M7.7).

Thesis: the frontage cap IS the envelopment. The controlled withdrawal of the
center is a command decision, never a script. The Iberian/Gallic center must
hold the MEANING of 'give ground as ordered' against its own reading of
'we are losing' or the withdrawal decays into a rout and the trap never closes.

Cohort layout (x-axis = depth, advancing rightward for Romans):
  side 0 (Romans):       x=[40,120], advancing right
  side 1 (Carthage):     x=[150,175], advancing left (toward Romans)
    center (idx 1):      held by meaning institution 'ordered_retreat_holds'
    African left (idx 2): y=[40,88],  hold firm
    African right (idx 3): y=[212,260], hold firm
    cavalry (idx 4):     delayed entry from right flank (simulates return after routing allied wing)

Meaning layer (already wired in lattice.py via build_meaning_state):
  The center's cues 'downs' and 'behind' are attenuated by 0.55 and 0.7
  respectively while 'ordered_retreat_holds' is active (carried by mago_center).
  When Mago falls, meaning severs → raw cues → panic threshold crossed → rout.

Two scenario variants:
  cannae()          — baseline with meaning active
  cannae_kill_mago() — meaning pre-severed (counterfactual: Mago dies at contact)
"""


def cannae():
    return {
        'field': [320, 300],
        'break_frac': 0.45,

        'cohorts': [
            # idx 0: Roman mass — deep, dense, frontage-capped (the blunder as geometry)
            {
                'side': 0, 'n': 800,
                'x': [40, 120], 'y': [60, 240],
                'err': 0.7, 'armor': 0.4, 'belief': 0.7, 'disc': 0.6, 'fat0': 0.1,
            },
            # idx 1: Iberian/Gallic center — the bowed line that must give ground without breaking
            # officer: mago_center, standing_order: fighting_withdrawal
            # meaning institution keeps cues below threshold while it holds
            {
                'side': 1, 'n': 240,
                'x': [150, 175], 'y': [90, 210],
                'err': 0.85, 'armor': 0.3, 'belief': 0.75, 'disc': 0.8, 'fat0': 0.05,
            },
            # idx 2: African veterans, left flank — fresh, hold firm, wheel inward
            {
                'side': 1, 'n': 180,
                'x': [150, 175], 'y': [40, 88],
                'err': 0.9, 'armor': 0.45, 'belief': 0.8, 'disc': 0.85, 'fat0': 0.0,
                'hold': 1,
            },
            # idx 3: African veterans, right flank — fresh, hold firm, wheel inward
            {
                'side': 1, 'n': 180,
                'x': [150, 175], 'y': [212, 260],
                'err': 0.9, 'armor': 0.45, 'belief': 0.8, 'disc': 0.85, 'fat0': 0.0,
                'hold': 1,
            },
            # idx 4: Carthaginian heavy cavalry — PLACEHOLDER (post-M7.7)
            # The cavalry routed the allied wing and returned to close the rear.
            # KNOWN MISS: the current engine has no "rout wing then envelop" mechanic.
            # Cavalry starting at x>200 with advd=-1 escapes off the left edge before
            # the Roman break. Full implementation requires cavalry-return orders (M7.7).
            # For now: model cavalry as a small aggressive flank force at the edge.
            {
                'side': 1, 'n': 60,
                'x': [150, 175], 'y': [5, 35],
                'mounted': 1,
                'err': 0.85, 'armor': 0.4, 'belief': 0.85, 'disc': 0.7, 'fat0': 0.05,
            },
        ],

        # Meaning layer (M7.2): cohort index 1 (center) carries 'ordered_retreat_holds'.
        # Cue attenuation: 'downs' * 0.55, 'behind' * 0.7 before universal threshold.
        # When mago_center is severed, transform is identity (raw cues = panic faster).
        'meanings': {
            1: [
                {
                    'id': 'ordered_retreat_holds',
                    'carried_by': 'mago_center',
                    'transform': {
                        'scale_factors': {'downs': 0.55, 'behind': 0.7},
                        'impulse_terms': {},
                    },
                    'failure_conditions': [
                        'mago_center killed',
                        'sentiment:we_are_losing > 0.6',
                        'center penetrated > 50%',
                    ],
                    'break_effect': None,
                }
            ]
        },

        # M7.0 convergent horn: encircled Romans (cavalry from rear + flanks closing)
        # take elevated pursuit casualties — the same mechanism as Isandlwana's kill-share.
        'convergent_horn': True,
        'horn_kill_multiplier': 2.5,

        'pursuit_intensity': {0: 0.35, 1: 0.85},
        'cap_p': {0: 0.0, 1: 0.0},
    }


def cannae_kill_mago():
    """Counterfactual: Mago killed at first contact.

    The meaning institution 'ordered_retreat_holds' is pre-severed (not
    included in 'meanings'). The center reads raw cues from contact → panic
    threshold crosses early → center routs → Romans pour through → trap fails.

    Battery gate: Roman victory or draw in majority of seeds.
    Teaches: the genius was the system (right troops + right meaning + right officer),
    not the trick. Kill the keeper of the meaning, lose Cannae.
    """
    scn = cannae()
    # Remove the meaning entirely: center fights (and breaks) on raw cues
    scn['meanings'] = {}
    return scn
