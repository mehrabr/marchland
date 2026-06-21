## MARCHLAND — Ren'Py game script: turn loop and rollback partition.
##
## Integration spec §7 (rollback partition) and §8 (turn loop).
##
## Layer discipline:
##   - Menu choices produce strings (tactic/pace/choice). These are player data.
##   - run_operation() is the only call that touches the sim. It returns plain dicts.
##   - capsule holds all persistent state. It must be a SaveCapsule (serializable).
##   - renpy.block_rollback() fires at every committed order (spec §7).
##   - Rollback is re-enabled ONLY in the archive_scene label (spec §7, Archive layer).
##
## The sim is called once per operation and discarded. Battles reconstruct from seed.


## ---------------------------------------------------------------------------
## Start: new game entry point

label start:
    python:
        capsule = SaveCapsule(seed=0, culture_name="harfleur_1415")

    jump arrival_scene


## ---------------------------------------------------------------------------
## Arrival scene: the campaign opens at camp (spec §8, M7.A.3 pattern)

label arrival_scene:
    scene bg_camp

    "You ride in with your guard at dusk. The camp sergeant-at-arms meets you at the tent."
    ""
    "Sergeant: 'The men are mustered, my lord. Effectives on roll — though the clerk's count runs a week old.'"
    "Sergeant: 'Harfleur\\'s garrison sent word they\\'ll hold to the last. Our scouts say the walls are sound — but the scouts haven\\'t been inside.'"
    ""
    "The first decision is yours: commit now, or wait for clearer word."

    ## Decision 1: quarter policy
    menu:
        "Set quarter policy before operations."

        "Strict — men grumble, patron pleased (+favor).":
            python:
                capsule.quarter_policy = 'strict'
        "Liberal — controlled contribution, balanced.":
            python:
                capsule.quarter_policy = 'liberal'
        "Free rein — men content, patron wary (-favor).":
            python:
                capsule.quarter_policy = 'free_rein'

    ## Quarter choice is a preference, not an operation — no block_rollback here.
    ## The order commitment block_rollback fires when ops begin (spec §7).

    jump station_scene


## ---------------------------------------------------------------------------
## Station scene: the core turn loop (spec §8)

label station_scene:
    ## 1. Render the Table from current belief state
    call screen the_table(belief=belief_view_for_table(capsule.belief_db_dict, capsule.station))

    ## 2. Player picks an order as a dialogue choice
    menu:
        "Besiege Harfleur." if capsule.siege_result is None:
            call screen tactic_menu
            ## commit_order pushes onto the in-flight queue and blocks rollback
            call commit_order("siege")

        "March to Agincourt." if capsule.siege_result is not None and capsule.march_result is None:
            call screen pace_menu
            call commit_order("march")

        "Engage the French." if capsule.march_result is not None and capsule.battle_result is None:
            call screen battle_menu
            call commit_order("battle")

        "Ride to the hill [change station].":
            python:
                capsule.station = 'HILL'
            ## Station change is movement, not commitment — no block_rollback
            jump station_scene

        "Return to camp.":
            python:
                capsule.station = 'CAMP'
            jump station_scene

        "Open the Archive [review chronicle].":
            call archive_scene

    ## 3. Advance the clock — separate act (M7.A: order and time are distinct)
    ## After the committed order runs, check for season completion
    python:
        all_done = (
            capsule.siege_result is not None and
            capsule.march_result is not None and
            capsule.battle_result is not None
        )

    if all_done:
        jump winter_court_scene
    else:
        jump station_scene


## ---------------------------------------------------------------------------
## Commit order: the irrevocable-order pattern (spec §7)
##
## Every committed order:
##   1. Runs the sim (Layer 1 call via bridge)
##   2. Updates the capsule with the serializable result
##   3. Calls renpy.block_rollback() — the order cannot be recalled
##
## "You command; you do not pilot." (Law 6)

label commit_order(order):
    python:
        if order == "siege":
            op_result = run_operation(
                'siege', capsule.seed,
                tactic=capsule.siege_tactic or 'wait',
            )
            capsule.siege_result = op_result['result']
            capsule.trace_dicts.append(op_result['trace'])

        elif order == "march":
            op_result = run_operation(
                'march', capsule.seed,
                siege_result=capsule.siege_result,
                pace=capsule.march_pace or 'normal',
            )
            capsule.march_result = op_result['result']
            capsule.trace_dicts.append(op_result['trace'])

        elif order == "battle":
            op_result = run_operation(
                'battle', capsule.seed,
                march_result=capsule.march_result,
                battle_choice=capsule.battle_choice or 'engage',
            )
            capsule.battle_result = op_result['result']
            capsule.trace_dicts.append(op_result['trace'])

        ## Block rollback: the order is now in flight; the past is closed.
        renpy.block_rollback()

    return


## ---------------------------------------------------------------------------
## Archive scene: chronicle scrub — rollback IS the mechanic here (spec §7)
##
## Post-battle: two renderings of one Layer-2 trace.
## The tapestry's arrow (chronicle prose) vs. the trace's sword (raw events).
## "You cannot rewind the war; you can re-read it."

label archive_scene:
    python:
        ## Re-enable rollback for the Archive — scrubbing is intentional here
        config.rollback_enabled = True

        ## Build the archive view from all accumulated trace dicts
        import json
        composed = {
            'phases': [],
            'scenarios': [],
            'seed': capsule.seed,
            'deaths': [],
            'routs': [],
            'events': [],
        }
        for td in capsule.trace_dicts:
            phase = td.get('phase', '')
            composed['phases'].append(phase)
            composed['scenarios'].append(td.get('scenario', ''))
            for d in td.get('deaths', []):
                composed['deaths'].append(dict(d, phase=phase))
            for r in td.get('routs', []):
                composed['routs'].append(dict(r, phase=phase))
            for ev in td.get('events', []):
                composed['events'].append((ev[0], ev[1], ev[2], phase))

        archive = trace_for_archive(composed)

    call screen archive_screen(archive=archive)

    ## On return from Archive, close rollback again — operations resume
    python:
        config.rollback_enabled = False

    return


## ---------------------------------------------------------------------------
## Winter court scene

label winter_court_scene:
    python:
        won = (
            capsule.battle_result is not None and
            capsule.battle_result.get('win') == 0
        )

    scene bg_court

    if won:
        "The patron receives your account at court. The field is yours. A commission awaits next season."
    else:
        "The patron is silent on the matter of next season. The season closes."

    "Season ended."
    return


## ---------------------------------------------------------------------------
## Screens

screen the_table(belief):
    ## Renders the player's belief state as a text Table (spec §7, M4 Table screen).
    ## belief: {phase: {claim: {value, confidence, glyph}}} from belief_view_for_table()
    frame:
        xalign 0.05
        yalign 0.05
        xsize 400
        vbox:
            spacing 6
            text "THE TABLE" style "table_header"
            for phase, claims in belief.items():
                text "[phase]:" style "table_phase"
                for claim, entry in claims.items():
                    text "[entry['glyph']] [claim]: [entry['value']] ([entry['confidence']:.0%}])" style "table_entry"
    use hud_dismiss


screen tactic_menu:
    ## Siege tactic choice — feeds capsule.siege_tactic before commit_order("siege")
    frame:
        xalign 0.5
        yalign 0.5
        vbox:
            spacing 10
            text "Siege of Harfleur — choose your approach:"
            textbutton "Wait for terms (patient)" action [SetVariable("capsule.siege_tactic", "wait"), Return()]
            textbutton "Press for storm (costly)"  action [SetVariable("capsule.siege_tactic", "storm"), Return()]


screen pace_menu:
    ## March pace choice — feeds capsule.march_pace before commit_order("march")
    frame:
        xalign 0.5
        yalign 0.5
        vbox:
            spacing 10
            text "March to Agincourt — set pace:"
            textbutton "Normal pace"          action [SetVariable("capsule.march_pace", "normal"), Return()]
            textbutton "Push hard (more attrition)" action [SetVariable("capsule.march_pace", "push"),   Return()]
            textbutton "Rest every 4 days"    action [SetVariable("capsule.march_pace", "rest"),   Return()]


screen battle_menu:
    ## Battle choice — feeds capsule.battle_choice before commit_order("battle")
    frame:
        xalign 0.5
        yalign 0.5
        vbox:
            spacing 10
            text "The French array is before you:"
            textbutton "Engage"    action [SetVariable("capsule.battle_choice", "engage"),   Return()]
            textbutton "Withdraw"  action [SetVariable("capsule.battle_choice", "withdraw"), Return()]


screen archive_screen(archive):
    ## Archive scrub: two-column view. Left: chronicle events. Right: raw trace.
    ## Rollback is enabled here — the player scrubs by rewinding through the history.
    frame:
        xfill True
        yfill True
        vbox:
            spacing 4
            text "ARCHIVE — seed [archive['seed']]" style "archive_header"
            hbox:
                spacing 20
                vbox:
                    xsize 500
                    text "Chronicle" style "archive_subheader"
                    for ev in archive['events']:
                        text "[ev['phase']] t=[ev['t']]: [ev['name']]" style "archive_event"
                vbox:
                    xsize 400
                    text "Deaths: [len(archive['deaths'])]  Routs: [archive['rout_count']]" style "archive_count"
                    for d in archive['deaths'][:20]:
                        text "[d['phase']] t=[d['t']]: [d['cause']]" style "archive_death"
            textbutton "Return" action Return()


screen hud_dismiss:
    textbutton "Continue" action Return() xalign 0.5 yalign 0.95
