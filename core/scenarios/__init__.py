"""Unified scenario registry. Import SCN_BATTLE, SCN_MARCH, SCN_SIEGE, or SCN_DISSOLUTION.

Chain runners (SCN_CHAIN) live in battery/runner.py to avoid a circular import:
core.chain imports core.scenarios.* which triggers this __init__, which would
re-import core.chain before it has finished loading.

M7.0 additions: carrhae, sphacteria (convergent_horn encirclement scenarios)
M7.5 addition: winter_quarters (dissolution-without-battle scenario)
M7.7 addition: cannae_216bc, cannae_kill_mago (officer AI + meaning layer capstone)
"""
from .agincourt import agincourt, agincourt_marched
from .hastings import hastings, hastings_drilled, hastings_p1, hastings_p2
from .isandlwana import isandlwana_line, isandlwana_square
from .sieges import escalade_fresh, escalade_starved, breach_fresh, breach_starved
from .marches import agincourt_march, danube_1704, niemen_1812, gedrosia_325, sherman_1864
from .harfleur import harfleur, harfleur_relief25
from .carrhae import carrhae
from .sphacteria import sphacteria
from .winter_quarters import winter_quarters
from .cannae import cannae as cannae_216bc, cannae_kill_mago

SCN_BATTLE = dict(
    agincourt=agincourt,
    agincourt_marched=agincourt_marched,
    hastings=hastings,
    hastings_drilled=hastings_drilled,
    hastings_p1=hastings_p1,
    hastings_p2=hastings_p2,
    isandlwana_line=isandlwana_line,
    isandlwana_square=isandlwana_square,
    escalade_fresh=escalade_fresh,
    escalade_starved=escalade_starved,
    breach_fresh=breach_fresh,
    breach_starved=breach_starved,
    carrhae=carrhae,
    sphacteria=sphacteria,
    cannae_216bc=cannae_216bc,
    cannae_kill_mago=cannae_kill_mago,
)

SCN_MARCH = dict(
    agincourt_march=agincourt_march,
    danube_1704=danube_1704,
    niemen_1812=niemen_1812,
    gedrosia_325=gedrosia_325,
    sherman_1864=sherman_1864,
)

SCN_SIEGE = dict(
    harfleur=harfleur,
    harfleur_relief25=harfleur_relief25,
)

SCN_DISSOLUTION = dict(
    winter_quarters=winter_quarters,
)
