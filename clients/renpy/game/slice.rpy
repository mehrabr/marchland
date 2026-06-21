## MARCHLAND — vertical slice: "One Order, One Battle, One Truth"
##
## Spec: docs/marchland-vertical-slice.md §2-§5
## Build order (spec §4):
##   1. pipe        — button → Battle → chronicle on screen  ✓
##   2. reveal      — chronicle ↔ trace toggle              ✓
##   3. command surface — Table + officer contact report     ✓
##   4. irrevocable order — 3-choice menu + block_rollback  ✓
##   5. wait        — HOLD/MOVE → station switch            ✓
##   6. polish      — portrait placeholder, legible text    ✓
##
## Entry point: label slice_start
## State: slice_* default variables (reset at entry)
##
## Layer discipline:
##   run_slice_battle() is the only call that touches the sim (imported via init.rpy).
##   Every other value is a plain Python type. No numpy types cross into label space.
##   Rollback is blocked from commitment forward; re-enabled in the Archive only.


## ---------------------------------------------------------------------------
## Slice state — reset at slice_start each run

default slice_seed = 42
default slice_order = None       # 'hold' | 'refuse' | 'open'
default slice_wait = None        # 'hill' | 'knot'
default slice_battle_result = None
default slice_chronicle = ""
default slice_archive = None     # processed archive dict from bridge.trace_for_archive
default slice_view = "chronicle" # toggle: 'chronicle' | 'trace'


## ---------------------------------------------------------------------------
## Entry: the vertical slice starts here
## Hypothesis (spec §0): is command-under-uncertainty compelling in ten minutes?

label slice_start:
    python:
        slice_seed = 42
        slice_order = None
        slice_wait = None
        slice_battle_result = None
        slice_chronicle = ""
        slice_archive = None
        slice_view = "chronicle"

    ## Open on the Hill (spec §2, step 1)
    scene bg_hill

    ## The Table — three markers; this is the belief state the slice is built around.
    ## The crux: the horse beyond the wood is rumored (?), not confirmed. Do you believe it?
    call screen slice_table_screen

    "The ridge is yours. Stakes driven. The French have come up through the mist."

    ## The officer contact report (spec §2, step 2)
    show captain neutral at left

    "Captain: 'My lord — our scouts confirm the French array on the ridge, some four hundred yards. Two hours past, one man saw horse beyond the north wood. We have not confirmed it since.'"
    "Captain: 'The Hill gives the wider view. Your order?'"

    ## The irrevocable order (spec §2, step 3; §4, step 4)
    ## Three choices → one battle parameter.
    ## 'hold': stakes active, cavalry balks. 'open': no stakes, cavalry sweeps.
    menu:
        "Hold the ridge — stand and receive.":
            python:
                slice_order = 'hold'
        "Refuse — withdraw over the bridge.":
            python:
                slice_order = 'refuse'
        "Offer open battle — advance to the flat.":
            python:
                slice_order = 'open'

    ## The order is committed. The past is closed. (spec §2, step 4; §4, step 4)
    python:
        renpy.block_rollback()

    hide captain

    if slice_order == 'refuse':
        "The rider departs south. The order is given. The bridge is behind you."
        jump slice_refuse_resolution
    else:
        "The rider spurs south. The order is in flight. It will land tomorrow."
        jump slice_wait_choice


## ---------------------------------------------------------------------------
## The wait — HOLD on Hill or MOVE to Knot (spec §2, step 4; §4, step 5)
## Latency is the tension: not dead time, but the weight of an order already gone.

label slice_wait_choice:
    menu:
        "Hold on the Hill [wider view, latency 1 — the order is already in flight].":
            python:
                slice_wait = 'hill'
        "Ride to the Knot [latency 0 from there — closer to the line, risk lottery].":
            python:
                slice_wait = 'knot'

    if slice_wait == 'knot':
        ## Station-change lottery (spec M4 §1 — leader-risk simplified for slice)
        python:
            import random
            _rng = random.Random(slice_seed ^ 0xDEAD)
            _injury = _rng.random() < 0.07   # 7% leader-risk (Class D, spec M4)

        "You ride forward through the edge-wood. The path is narrow."

        if _injury:
            "A root catches your mount. You take a knock — bruised, not broken. You reach the Knot before dawn."
        else:
            "You reach the Knot without incident. The line is close enough to hear the enemy camp."

        "From the Knot you can see the north wood clearly. The horse is there. The rumor was right."

    else:
        "You wait on the Hill. The night is long. Below, your line locks shields."
        "Dawn breaks grey."

    jump slice_battle_resolution


## ---------------------------------------------------------------------------
## Battle resolution — headless, seeded, deterministic (spec §2, step 5; §4, step 1)

label slice_battle_resolution:
    "The order has landed. The battle begins."

    python:
        op = run_slice_battle(slice_seed, slice_order)
        slice_battle_result = op['result']
        slice_chronicle    = op['chronicle']
        slice_archive      = op['archive']

    jump slice_chronicle_scene


## ---------------------------------------------------------------------------
## Refuse resolution — no battle (spec §2, step 3 — third choice)

label slice_refuse_resolution:
    python:
        slice_battle_result = {'win': -1, 'withdrew': True}
        slice_chronicle = (
            "The army withdrew in good order across the bridge before the French could close. "
            "No engagement was forced. The French pursuit was cautious; the trace holds no death-certs. "
            "The chronicle must speak of an absence — and the patron will ask why."
        )
        slice_archive = {
            'phases': ['battle'],
            'deaths': [],
            'rout_count': 0,
            'events': [],
            'summary': {'battle': {'won': False, 'withdrew': True}},
        }

    "The order reached the line before dawn. The army crossed the bridge in silence. No battle was joined."

    jump slice_chronicle_scene


## ---------------------------------------------------------------------------
## Chronicle scene — the morning-after account (spec §2, step 5)
## This is the tapestry's version: sympathetic prose, narrative emphasis, imprecise mechanism.

label slice_chronicle_scene:
    python:
        _won = (
            slice_battle_result.get('win') == 0
            if not slice_battle_result.get('withdrew')
            else None
        )

    if _won is True:
        "The line held. The enemy broke."
    elif _won is False:
        "The line broke. The enemy held."
    else:
        "No battle was joined."

    ## Chronicle prose — the first rendering
    call screen slice_chronicle_screen(chronicle=slice_chronicle)

    "That is the chronicle. But the chronicle is a source with sympathies, not an omniscient account."
    "The trace is the only omniscient object."

    jump slice_archive_scene


## ---------------------------------------------------------------------------
## Archive — the reveal (spec §2, step 6; §4, step 2)
## Two renderings of one trace. The toggle is the thesis payoff:
## hard to predict, easy to explain, recorded imperfectly.

label slice_archive_scene:
    python:
        ## Re-enable rollback — scrubbing IS the mechanic here (spec §7)
        config.rollback_enabled = True
        slice_view = "chronicle"

    call screen slice_archive_screen(
        chronicle=slice_chronicle,
        archive=slice_archive,
        seed=slice_seed,
    )

    python:
        config.rollback_enabled = False

    jump slice_end


## ---------------------------------------------------------------------------
## End — consequence and save (spec §2, step 7)

label slice_end:
    python:
        _withdrew = bool(slice_battle_result.get('withdrew'))
        _won = (not _withdrew) and (slice_battle_result.get('win') == 0)

        ## The cavalry was real. The question was whether you accounted for it.
        _cavalry_rewarded = (slice_order == 'hold' and _won)
        _cavalry_punished = (slice_order == 'open' and not _won and not _withdrew)

    if _cavalry_rewarded:
        "Your stakes held the cavalry. The rumor was real — and you accounted for it. The patron is pleased."
    elif _cavalry_punished:
        "The horse beyond the wood was real. The open flank paid for it. The patron will want an accounting."
    elif slice_order == 'open' and _won:
        "The cavalry came — and your line held anyway. Fortune was kind. The patron will not know it was fortune."
    elif _withdrew:
        "You saved the army. The campaign continues. What the patron believes is another matter — and his beliefs diverge from the trace."
    else:
        "The record is set. The season moves on."

    "Season saved."
    return


## ===========================================================================
## Screens
## ===========================================================================

screen slice_table_screen():
    ## The Table — three markers, hardcoded for the slice (spec §2, step 1; §3).
    ## In the full season these come from belief_view_for_table(); here, the belief
    ## state IS the setup: the horse beyond the wood is the crux of the decision.
    ##
    ## Glyphs: * confirmed  ~ scouted  ? rumored  . stale
    frame:
        xalign 0.02
        yalign 0.05
        xsize 340
        padding 12, 12
        vbox:
            spacing 8
            text "THE TABLE" style "table_header"
            null height 4
            text "*  Your line — the ridge (confirmed)" style "slice_confirmed"
            text "~  Enemy column — ridge, 2h old (scouted)" style "slice_scouted"
            text "?  Horse — north wood (rumored)" style "slice_rumored"
            null height 6
            text "Station: HILL  |  Latency: 1 day" style "slice_table_note"
    use hud_dismiss


screen slice_chronicle_screen(chronicle):
    ## Chronicle prose — first post-battle rendering (the tapestry's version).
    modal True
    frame:
        xalign 0.5
        yalign 0.4
        xsize 680
        padding 20, 16
        vbox:
            spacing 14
            text "CHRONICLE" style "archive_header"
            null height 4
            text chronicle style "chronicle_body"
    textbutton "Continue" action Return() xalign 0.5 yalign 0.92


screen slice_archive_screen(chronicle, archive, seed):
    ## The reveal — toggle between chronicle prose and trace DeathCerts.
    ## Rollback is enabled here; scrubbing through Ren'Py history IS the mechanic.
    ##
    ## The thesis: hard to predict, easy to explain, recorded imperfectly.
    ## The chronicle was right about the outcome; wrong about the mechanism.
    ## The trace is the only omniscient object.

    $ death_count  = len(archive.get('deaths', []))
    $ pursuit_n    = sum(1 for d in archive.get('deaths', []) if d.get('cause') == 'pursuit')
    $ pre_break_n  = death_count - pursuit_n
    $ seed_str     = str(seed)

    frame:
        xfill True
        yfill True
        padding 16, 12

        vbox:
            spacing 10

            text "ARCHIVE  —  seed [seed_str]" style "archive_header"

            hbox:
                spacing 16
                textbutton "Chronicle" action SetVariable("slice_view", "chronicle")
                textbutton "Trace (death certs)" action SetVariable("slice_view", "trace")

            null height 10

            ## -- Chronicle view --
            if slice_view == "chronicle":
                text chronicle style "chronicle_body"

            ## -- Trace view --
            else:
                $ dc_str = "[death_count] total  |  [pre_break_n] pre-break  |  [pursuit_n] pursuit"
                text dc_str style "archive_count"
                null height 6

                if death_count == 0:
                    text "No death-certs in trace.  The record holds an absence." style "archive_death"
                else:
                    for d in archive.get('deaths', [])[:40]:
                        $ cause_str = str(d.get('cause', '?'))
                        $ t_val = d.get('t', 0)
                        $ t_str = f"t={t_val:.0f}s"
                        $ loc = d.get('location')
                        $ loc_str = f"  at {loc}" if loc else ""
                        text "[t_str]  cause=[cause_str][loc_str]" style "archive_death"

    textbutton "Return" action Return() xalign 0.5 yalign 0.97
