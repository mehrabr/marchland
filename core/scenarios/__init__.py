"""Unified scenario registry. Import SCN_BATTLE, SCN_MARCH, or SCN_SIEGE."""
from .agincourt import agincourt, agincourt_marched
from .hastings import hastings, hastings_drilled, hastings_p1, hastings_p2
from .isandlwana import isandlwana_line, isandlwana_square
from .sieges import escalade_fresh, escalade_starved, breach_fresh, breach_starved
from .marches import agincourt_march, danube_1704, niemen_1812, gedrosia_325, sherman_1864
from .harfleur import harfleur, harfleur_relief25

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
