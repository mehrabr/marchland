## MARCHLAND — Ren'Py init: Layer 1 bridge import and rollback config.
##
## Integration spec §4, §7.
## Process model: Model A (in-process import). numpy 2.4.6 vendored via cp312 wheel.
## To switch to Model B (subprocess), replace the init python block with IPC plumbing
## and remove the numpy vendor step — the layer contract is identical either way.

init python:
    ## Import the Layer 2 adapter. Nothing numpy-shaped crosses this boundary.
    from clients.renpy.bridge import (
        run_chain,
        run_operation,
        run_slice_battle,
        save_capsule_from_state,
        capsule_to_dict,
        belief_view_for_table,
        trace_for_archive,
        SaveCapsule,
    )

    ## Suppress quit-confirmation dialog — Ren'Py 8.5.3 layout.yesno_prompt missing
    config.quit_action = Quit(confirm=False)
    ## Patch missing SDK method so any residual confirm path also doesn't crash
    if not hasattr(layout, 'yesno_prompt'):
        layout.yesno_prompt = lambda *a, **kw: True

    ## Rollback partition (spec §7):
    ## Block rollback globally — the "blunt instrument". The precise tool is
    ## renpy.block_rollback() at each commitment point in marchland.rpy.
    ## Re-enable per-label in the Archive layer only (scrub IS the mechanic there).
    config.rollback_enabled = False

    ## Season state: a plain SaveCapsule. Never store sim objects here.
    capsule = None
