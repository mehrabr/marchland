## Custom style definitions for MARCHLAND.
## Ren'Py resolves "table_header" by looking for parent style "header"; these
## explicit definitions short-circuit that chain and set appearance directly.

init -1:
    style header is text:
        size 20
        bold True
        color "#e8e0d0"

    style table_header is header:
        size 18
        bold True
        color "#d4c89a"

    style table_phase is text:
        size 14
        bold True
        color "#a09070"

    style table_entry is text:
        size 13
        color "#c8c0b0"

    style archive_header is header:
        size 20
        bold True
        color "#d4c89a"

    style archive_subheader is text:
        size 16
        bold True
        color "#b8a880"

    style archive_event is text:
        size 12
        color "#b0a890"

    style archive_count is text:
        size 14
        bold True
        color "#c8b870"

    style archive_death is text:
        size 12
        color "#c07060"

    style chronicle_body is text:
        size 14
        color "#d0c8b8"
        line_spacing 6

    style slice_confirmed is text:
        size 13
        color "#88cc88"

    style slice_scouted is text:
        size 13
        color "#aaaaee"

    style slice_rumored is text:
        size 13
        color "#ddaa44"

    style slice_table_note is text:
        size 11
        color "#888878"
        italic True
