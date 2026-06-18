"""Culture data file: Tutorial Escort — Calais to Ardres, autumn 1415.

A small escort commission: deliver Sir William Brandon's retinue from
Calais to the muster at Ardres. One road, five days, a possible encounter.
Used by 'python -m clients.cli tutorial'.

Non-standard fields used only by tutorial.py:
  army['receipt_notes']       — per-cohort receipt annotations for annotated muster
  culture['march_receipt_notes'] — march model receipt annotations

These are ignored by the core commission system (which reads only army['cohorts']).
No quality coefficients. Receipts-grep enforced.
"""

CULTURE = {
    'name': 'tutorial_escort',
    'era': '1415 Normandy, autumn',
    'patron': 'Lord Camoys',

    'doctrine_vocab': {
        'cohort_names': {
            'maa':    'Men-at-arms',
            'archer': 'Archers',
        },
        'rank_labels': ['vintenar', 'centenar', 'captain'],
        'victory_terms': {
            'NEGOTIATED':       'rendered on terms',
            'STORMED_sack':     'taken by storm',
            'RELIEVED':         'relieved',
            'ABANDONED_supply': 'raised for supply',
            'ONGOING':          'still sitting',
        },
        'favor_labels': ['censure', 'cold shoulder', 'neutral', 'favor', 'acclaim'],
    },

    'station_prices': {
        'CAMP':       0,
        'HILL':       1,
        'KNOT':       2,
        'FRONT_RANK': 3,
    },

    'quarter_customs': {
        'strict': {
            'army_morale_mod':  -0.05,
            'patron_favor_mod': +0.10,
            'note': 'No pillage; town folk unmolested; patron content.',
        },
        'liberal': {
            'army_morale_mod':  0.00,
            'patron_favor_mod': 0.00,
            'note': 'Controlled contribution; the custom of the age.',
        },
        'free_rein': {
            'army_morale_mod':  +0.10,
            'patron_favor_mod': -0.15,
            'note': 'Full plunder; men content but patron wary of the account.',
        },
    },

    'career': {
        'frame': 'retinue captain under Lord Camoys',
        'starting_patron_favor': 0.55,   # slight advantage: tutorial is gentle
        'winter_court_venue': 'Calais, the garrison hall',
        'ransom_share': 0.33,
        'season_deadline': 12,           # 12 days for a 5-day march + patrol buffer
        'credit_thresholds': {
            'acclaim':  0.80,
            'favor':    0.60,
            'neutral':  0.40,
            'cold':     0.20,
            'censure':  0.00,
        },
    },

    'missions_pool': ['escort'],

    'armies': [
        {
            'name': "Escort for Sir William Brandon",
            'cohorts': [
                {
                    'label': 'Men-at-arms',
                    'side': 0, 'n': 200,
                    'x': (30, 60), 'y': (30, 120),
                    'hold': 1, 'err': 0.75, 'armor': 0.80,
                    'belief': 0.80, 'disc': 0.75, 'fat0': 0.05,
                    # B: partial harness (armor=0.80)
                    # C: committed escort (belief=0.80, hold)
                },
                {
                    'label': 'Archers (south)',
                    'side': 0, 'n': 50,
                    'x': (20, 55), 'y': (0, 30),
                    'hold': 1, 'ranged': 1, 'ammo': 8,
                    'err': 0.85, 'armor': 0.15, 'belief': 0.80,
                    'disc': 0.60, 'fat0': 0.05,
                    # B: longbow, 8 sheaves; E: trained volley (err=0.85)
                },
                {
                    'label': 'Archers (north)',
                    'side': 0, 'n': 50,
                    'x': (20, 55), 'y': (120, 150),
                    'hold': 1, 'ranged': 1, 'ammo': 8,
                    'err': 0.85, 'armor': 0.15, 'belief': 0.80,
                    'disc': 0.60, 'fat0': 0.05,
                    # B: longbow, 8 sheaves; E: trained volley (err=0.85)
                },
            ],
            # receipt_notes: tutorial.py uses these for annotated muster display only.
            # Not part of the core commission schema; ignored outside tutorial.py.
            'receipt_notes': {
                'Men-at-arms': [
                    'armor=0.80 (B) → P(casualty | opening) ≈ 27% vs 45% unarmored',
                    'belief=0.80 (C) → men hold unless 3 of 5 appraisal cues fire',
                    'hold=1 (D) → cohort stands ground; does not advance into pursuit',
                ],
                'Archers (south)': [
                    'ranged=1, ammo=8 sheaves (B) → volleys fire at ADVANCE phase',
                    'armor=0.15 (B) → nearly unarmored in close combat; stay behind the men-at-arms',
                    'err=0.85 (E) → disciplined volley; err is spread not accuracy',
                ],
                'Archers (north)': [
                    'ranged=1, ammo=8 sheaves (B) → volleys fire at ADVANCE phase',
                    'armor=0.15 (B) → nearly unarmored in close combat; stay behind the men-at-arms',
                    'err=0.85 (E) → disciplined volley; err is spread not accuracy',
                ],
            },
        },
    ],

    # march_receipt_notes: tutorial.py uses these to annotate the muster.
    # Not part of the core commission schema.
    'march_receipt_notes': [
        "pace=10 miles/day (B) → road-speed-limited escort on the king's road",
        'stock_days=7 (C) → 7 days grain and fodder; plenty for 5 days + buffer',
        'water_ok=0.92 (C) → 92% of nights find good water; dry nights tax fatigue',
        'officers=0.90 (D) → competent centenar; fewer stragglers on hard days',
        'fat0=0.05 (C) → troops start fresh; fatigue accumulates with miles and hunger',
    ],
}
