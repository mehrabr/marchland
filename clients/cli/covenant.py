"""MARCHLAND covenant — printed once at game start.

One screen. States what the game is and what it is not.
The phrase 'You command; you do not pilot.' is the game's first law.
"""

COVENANT_TEXT = """\
╔══════════════════════════════════════════════════════════╗
║         MARCHLAND — what this game is                   ║
╚══════════════════════════════════════════════════════════╝

  You command; you do not pilot.

  Your orders travel at rider speed. Your men appraise them
  against what they can see. History is hard to predict and
  easy to explain: every death has a cause in the trace;
  every battle replays bit-identically from the same seed.

  This is not a god-game.
    · You cannot see the whole field.
    · You cannot undo a decision once the rider departs.
    · Your patron believes what your dispatches tell them —
      not what the trace records.

  This game will never:
    · Invent a quality difference between forces that lacks
      a receipt (a changeable in-world fact).
    · Let you see what your station's body cannot see.
    · Make the chronicle say something the trace does not
      ground with an event and a time.

  This game will always:
    · Explain every number when you ask.
      Type  help receipts  at any prompt.
    · Show you the cause of every death, if you look.
      Type  help trace     at any prompt.

══════════════════════════════════════════════════════════"""


def print_covenant(io=None) -> None:
    """Print the covenant. io must have a .print() method; defaults to stdout."""
    if io is None:
        print(COVENANT_TEXT)
    else:
        io.print(COVENANT_TEXT)
