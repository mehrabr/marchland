"""MARCHLAND CLI: the inspection surface — keeping the door (M-presentation).

The covenant promises the game will always explain every number when you ask.
That inspectability is load-bearing for the anti-essentialism thesis: the
receipts being auditable is HOW the game proves it isn't loading the dice
per-people. So the rule is not 'delete the numbers' — it is: the numbers live
behind a door, not on the wall.

Default presentation is human and historical (the captain's eye). Three verbs
pull the curtain for the player who wants to audit:

  inspect <thing>   the receipts behind a cohort or a favor score — the figures,
                    each tagged with its class [B/C/D/E] and what changes it
  explain           why the last outcome went as it did — the mechanics, the
                    cues that fired, the phase structure (the old [WHY] content)
  ledger on|off     a global toggle. 'on' makes the inspector verbose and
                    inline-adjacent (the grognard's mode); default 'off' is
                    human narration with inspect/explain available but never
                    volunteered (the new-player's mode). One switch serves both.

This is a render-layer module only. It reads receipts and trace facts that
already exist; it computes no simulation.
"""
from typing import Any, Dict, List, Optional


# ------------------------------------------------------------------
# Receipt class taxonomy (presentation labels only)

_CLASS_LABEL = {
    'A': 'bodies',
    'B': 'equipment',
    'C': 'campaign',
    'D': 'institution',
    'E': 'trained',
}

_RECEIPTS_FOOTER = (
    "Every figure here is a receipt — a changeable in-world fact. Nothing "
    "differs between forces without one. This is how you check the dice."
)


# ------------------------------------------------------------------
# Inspector — holds the deferred inspection content for a session

class Inspector:
    """Carries what the narration deliberately withheld, for on-demand recall.

    `ledger` (default False) is the global toggle between the two registers.
    `explain_lines` holds the mechanical account of the LAST outcome (the old
    [WHY] / [BP-Lattice] content). `favor_breakdown` holds the favor arithmetic.
    """

    def __init__(self) -> None:
        self.ledger: bool = False
        self.explain_lines: List[str] = []
        self.explain_subject: Optional[str] = None
        self.favor_breakdown: Optional[Dict[str, Any]] = None

    # -- recording (called by the operation runners) --

    def set_explain(self, subject: str, lines: List[str]) -> None:
        self.explain_subject = subject
        self.explain_lines = list(lines)

    def set_favor(self, base: float, mission_delta: float,
                  quarter_delta: float, total: float,
                  mission_credit: bool) -> None:
        self.favor_breakdown = dict(
            base=base, mission_delta=mission_delta, quarter_delta=quarter_delta,
            total=total, mission_credit=mission_credit,
        )

    # -- rendering --

    def render_explain(self, io) -> None:
        if not self.explain_lines:
            io.print("  (Nothing to explain yet — no outcome has resolved.)")
            return
        if self.explain_subject:
            io.print(f"  Why it went as it did — {self.explain_subject}:")
        for line in self.explain_lines:
            io.print(f"    {line}")

    def render_favor(self, io) -> None:
        b = self.favor_breakdown
        if not b:
            io.print("  (No favor reckoning yet — the season has not been judged.)")
            return
        io.print("  The reckoning behind your patron's regard:")
        io.print(f"    start            {b['base']:.2f}")
        credit = 'mission credit' if b['mission_credit'] else 'mission penalty'
        io.print(f"    {credit:<16} {b['mission_delta']:+.2f}")
        io.print(f"    quarter          {b['quarter_delta']:+.2f}")
        io.print(f"    {'=' * 22}")
        io.print(f"    standing         {b['total']:.2f}   [each a receipt — type 'help receipts']")


# ------------------------------------------------------------------
# Captain's-eye muster prose (the default surface)

def _count_words(n: int) -> str:
    """A rough period count phrase for a body of men: 'Two hundred'."""
    from tools.chronicle import _spell_cardinal, _cap
    if n <= 0:
        return "no"
    if n % 100 == 0 and n < 1000:
        return _cap(_spell_cardinal(n))
    if n >= 100:
        rounded = int(round(n / 10.0) * 10)
        return _cap(_spell_cardinal(rounded))
    return _cap(_spell_cardinal(n))


def captain_eye(cohort: Dict[str, Any]) -> str:
    """A captain's-eye sentence for a cohort — what they ARE, not their figures.

    Reads the same receipts the inspector exposes, but speaks them in the world:
    'well-harnessed — they'll take a blow that would fell a lighter man'.
    """
    label = cohort.get('label', 'men').lower()
    n = cohort.get('n', 0)

    armor = cohort.get('armor', 0.0)
    if armor >= 0.7:
        harness = "well-harnessed"
    elif armor >= 0.4:
        harness = "in half-armour"
    elif armor >= 0.1:
        harness = "lightly armed"
    else:
        harness = "near unarmoured"

    clauses: List[str] = []
    if armor >= 0.7:
        clauses.append("they'll take a blow that would fell a lighter man")
    elif armor < 0.1:
        clauses.append("a hard blow will tell on them")

    if cohort.get('ranged'):
        clauses.append("they'll empty their sheaves into a foe before he can come to grips")
    if cohort.get('mounted'):
        clauses.append("they ride, and want open ground")
    if cohort.get('hold'):
        clauses.append("they'll hold their ground rather than break ranks to chase a beaten foe")

    if not clauses:
        clauses.append("steady enough in their place")

    body = "; and ".join(clauses)
    return f"{_count_words(n)} {label}, {harness} — {body}."


def muster_hint(cohort: Dict[str, Any]) -> str:
    """The single un-volunteered pointer to the door."""
    token = cohort.get('label', 'them').lower()
    return f"(type 'inspect {token}' to see what makes them so)"


# ------------------------------------------------------------------
# The door opened — cohort receipts with class tags

def _cohort_receipt_lines(cohort: Dict[str, Any]) -> List[str]:
    """The figures behind a cohort, each tagged with its receipt class."""
    out: List[str] = []

    def tag(cls: str) -> str:
        return f"[{cls}: {_CLASS_LABEL[cls]}]"

    armor = cohort.get('armor')
    if armor is not None:
        # Presentation approximation of P(casualty | opening): ~27% at armor 0.80,
        # 45% bare. Same gloss the muster used to print on the wall.
        cas = int(round(45 * (1 - 0.5 * armor)))
        out.append(f"armor {armor:.2f}   — partial harness; ~{cas}% casualty per opening vs 45% bare   {tag('B')}")

    if cohort.get('ranged'):
        ammo = cohort.get('ammo', 0)
        out.append(f"longbow ×{ammo}  — looses volleys at range before contact; ammo caps the storm   {tag('B')}")

    if cohort.get('mounted'):
        out.append(f"mounted     — horse; balks at a solid stake-line, wants open ground            {tag('B')}")

    belief = cohort.get('belief')
    if belief is not None:
        out.append(f"belief {belief:.2f}  — hold unless the appraisal cues exceed their threshold        {tag('C')}")

    fat0 = cohort.get('fat0')
    if fat0:
        out.append(f"fatigue {fat0:.2f} — carried from the road; amplifies the opening hazard            {tag('C')}")

    if cohort.get('hold'):
        out.append(f"hold        — stand ground; do not pursue into the rout                       {tag('D')}")

    disc = cohort.get('disc')
    if disc is not None:
        out.append(f"discipline {disc:.2f} — tightness of the volley under load                          {tag('E')}")

    return out


def render_cohort_inspect(commission, subject: str, io) -> bool:
    """Open the door on one cohort's receipts. Returns False if not found."""
    cohorts = getattr(commission, 'army_cohorts', []) or []
    subject_norm = subject.strip().lower()

    match = None
    for c in cohorts:
        if not isinstance(c, dict):
            continue
        label = str(c.get('label', '')).lower()
        if subject_norm and (subject_norm == label or subject_norm in label
                             or label.startswith(subject_norm)):
            match = c
            break

    if match is None:
        labels = [str(c.get('label', '?')).lower() for c in cohorts if isinstance(c, dict)]
        io.print(f"  No cohort '{subject}'. Try: {', '.join(labels)}  (or 'favor')")
        return False

    io.print(f"  {match.get('label', 'Cohort')} · {match.get('n', 0)}")
    for line in _cohort_receipt_lines(match):
        io.print(f"    {line}")
    io.print(f"    {_RECEIPTS_FOOTER}")
    return True


# ------------------------------------------------------------------
# Command dispatch — used by both tutorial and season ops loops

def handle_inspect(commission, inspector: Inspector, arg: str, io) -> None:
    subject = (arg or '').strip().lower()
    if subject in ('favor', 'favour'):
        inspector.render_favor(io)
        return
    if not subject:
        cohorts = getattr(commission, 'army_cohorts', []) or []
        labels = [str(c.get('label', '?')).lower() for c in cohorts if isinstance(c, dict)]
        io.print("  Inspect what? " + ", ".join(labels + ['favor']))
        return
    render_cohort_inspect(commission, subject, io)


def handle_explain(inspector: Inspector, io) -> None:
    inspector.render_explain(io)


def handle_ledger(inspector: Inspector, arg: str, io) -> None:
    val = (arg or '').strip().lower()
    if val in ('on', 'verbose', 'true'):
        inspector.ledger = True
        io.print("  Ledger on — the figures ride alongside the prose from here.")
    elif val in ('off', 'false'):
        inspector.ledger = False
        io.print("  Ledger off — human narration; the door stays shut until you ask.")
    else:
        state = 'on' if inspector.ledger else 'off'
        io.print(f"  Ledger is {state}. Use 'ledger on' or 'ledger off'.")


# Set of command verbs the ops loops should route here.
INSPECT_VERBS = frozenset({'inspect', 'explain', 'ledger'})


def dispatch(cmd: str, arg: str, commission, inspector: Inspector, io) -> bool:
    """Route an inspection verb. Returns True if `cmd` was an inspection verb."""
    if cmd == 'inspect':
        handle_inspect(commission, inspector, arg, io)
        return True
    if cmd == 'explain':
        handle_explain(inspector, io)
        return True
    if cmd == 'ledger':
        handle_ledger(inspector, arg, io)
        return True
    return False
