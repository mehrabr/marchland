"""Culture data file: Harfleur 1415 — the Commission of Harfleur.

Doctrine vocabulary, station price list, quarter customs, and career frame
for the English 1415 Normandy vertical slice. Class B/C/D receipts only.
Army receipts are the ground truth available to the player at muster.
No per-entity quality coefficients (receipts-grep enforced).
"""

CULTURE = {
    'name': 'harfleur_1415',
    'era': '1415 Normandy campaign',
    'patron': 'Henry V',

    # How this culture names its formations and outcomes (D receipt: institutions)
    'doctrine_vocab': {
        'cohort_names': {
            'maa': 'Men-at-arms',
            'archer': 'Archers',
            'mounted': 'Mounted retinue',
            'militia': 'Garrison militia',
        },
        'rank_labels': ['vintenar', 'centenar', 'captain'],
        'victory_terms': {
            'NEGOTIATED': 'rendered on terms',
            'STORMED_sack': 'taken by storm',
            'RELIEVED': 'relieved',
            'ABANDONED_supply': 'raised for supply',
            'ONGOING': 'still sitting',
        },
        'favor_labels': ['censure', 'cold shoulder', 'neutral', 'favor', 'acclaim'],
    },

    # Cost in patron influence-points to occupy each command station (D receipt: institutions)
    'station_prices': {
        'CAMP':       0,
        'KNOT':       1,
        'HILL':       2,
        'FRONT_RANK': 4,
    },

    # Quarter policy effects on campaign state (C receipts: campaign state modifiers)
    'quarter_customs': {
        'strict': {
            'army_morale_mod': -0.05,
            'patron_favor_mod': +0.10,
            'note': 'No pillage; town folk unmolested; patron content.',
        },
        'liberal': {
            'army_morale_mod': 0.00,
            'patron_favor_mod': 0.00,
            'note': 'Controlled contribution; the custom of the age.',
        },
        'free_rein': {
            'army_morale_mod': +0.10,
            'patron_favor_mod': -0.15,
            'note': 'Full plunder; men content but patron wary of the account.',
        },
    },

    # Career frame for this vertical slice (D receipt: institutions)
    'career': {
        'frame': 'retinue captain under the crown',
        'starting_patron_favor': 0.50,   # neutral start
        'winter_court_venue': 'Calais',
        'ransom_share': 0.33,            # share of prisoners' ransom the crown claims
        'season_deadline': 90,           # days for the full Harfleur→Agincourt chain
        'credit_thresholds': {
            'acclaim':  0.80,
            'favor':    0.60,
            'neutral':  0.40,
            'cold':     0.20,
            'censure':  0.00,
        },
    },

    # This commission is specifically a siege; pool is singular for the vertical slice.
    'missions_pool': ['siege'],

    # Army compositions: receipts the player reads at muster.
    # Each army is a possible dealt hand. No quality coefficients.
    'armies': [
        {
            'name': "Retinue of Sir Thomas Erpingham",
            'cohorts': [
                {
                    'label': 'Men-at-arms',
                    'side': 0, 'n': 100,
                    'x': (140, 150), 'y': (80, 180),
                    'hold': 1, 'err': 0.75, 'armor': 0.9,
                    'belief': 0.85, 'disc': 0.8, 'fat0': 0.05,
                    # B: full harness (armor=0.9); C: cornered+led (belief=0.85)
                },
                {
                    'label': 'Archers (south wedge)',
                    'side': 0, 'n': 250,
                    'x': (135, 155), 'y': (10, 80),
                    'hold': 1, 'ranged': 1, 'ammo': 12,
                    'err': 0.85, 'armor': 0.15, 'belief': 0.85,
                    'disc': 0.6, 'fat0': 0.05,
                    # B: longbow, 12 sheaves; E: trained volley discipline (err=0.85)
                },
                {
                    'label': 'Archers (north wedge)',
                    'side': 0, 'n': 250,
                    'x': (135, 155), 'y': (180, 250),
                    'hold': 1, 'ranged': 1, 'ammo': 12,
                    'err': 0.85, 'armor': 0.15, 'belief': 0.85,
                    'disc': 0.6, 'fat0': 0.05,
                },
            ],
        },
    ],
}
