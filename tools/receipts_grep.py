"""Receipts grep: scans scenario and culture data files for quality coefficients.

Fails (exit 1) if any numeric per-cohort field is found that varies between
cohorts of the same side without a receipt — i.e., a hidden quality stat.

M7.3 — Two additional audit rules (Bret's law + Olleus's law):
  (a) Bret's law: any institution_of_meaning with empty failure_conditions
      fails the build. A meaning with no destruction path is an essence.
      The test fixture that deliberately violates this stays in CI permanently.
  (b) Olleus's law: any sentiment.transmission term referencing a quantity
      not in the TRACKED_RECEIPTS registry fails the build. No free
      contagion constants.

Forbidden field name patterns:
  quality, morale_bonus, strength_modifier, coeff, modifier

Usage:
    python -m tools.receipts_grep          # scans core/scenarios/ and core/cultures/
    python -m tools.receipts_grep --fix    # not implemented; violations must be fixed manually
"""
import ast, sys, re
from pathlib import Path

FORBIDDEN = re.compile(
    r'''\b(quality|morale_bonus|strength_modifier|coeff|modifier)\b['"]?\s*[=:]''',
    re.IGNORECASE,
)

# M7.3 (Bret's law): meaning with no failure_conditions
# Detects: 'failure_conditions': [] or 'failure_conditions': ()
_MEANING_EMPTY_FAILURE = re.compile(
    r"""['"]failure_conditions['"]\s*:\s*(\[\s*\]|\(\s*\))""",
    re.IGNORECASE,
)

# M7.3 (Olleus's law): tracked receipts registry — any transmission term not here fails
TRACKED_RECEIPTS = frozenset({
    'idle', 'hunger', 'arrears', 'bond', 'disease', 'officers', 'cohesion',
    # march model C/D receipts already tracked
    'water_ok', 'heat', 'weather', 'home_pull', 'pay_arrears',
    'disease_env', 'camp_quality', 'rumor_pressure',
})

# Detect sentiment transmission block: 'transmission': {'<key>': <float>}
# We look for any key inside a transmission dict
_TRANSMISSION_BLOCK = re.compile(
    r"""['"]transmission['"]\s*:\s*\{([^}]*)\}""",
    re.DOTALL | re.IGNORECASE,
)
_DICT_KEY = re.compile(r"""['"](\w+)['"]\s*:""")

SCAN_DIRS = [
    Path("core/scenarios"),
    Path("core/cultures"),
]


def scan_file(path: Path) -> list[tuple[int, str]]:
    violations = []
    text = path.read_text()
    lines = text.splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if FORBIDDEN.search(line):
            violations.append((i, line.rstrip(), 'quality-coeff'))

    # M7.3a (Bret's law): meaning with empty failure_conditions
    for m in _MEANING_EMPTY_FAILURE.finditer(text):
        lineno = text[:m.start()].count('\n') + 1
        violations.append((lineno,
                            lines[lineno-1].rstrip() if lineno <= len(lines) else m.group(),
                            'empty-failure-conditions'))

    # M7.3b (Olleus's law): sentiment transmission terms not in TRACKED_RECEIPTS
    for m in _TRANSMISSION_BLOCK.finditer(text):
        block = m.group(1)
        lineno = text[:m.start()].count('\n') + 1
        for km in _DICT_KEY.finditer(block):
            key = km.group(1)
            if key not in TRACKED_RECEIPTS:
                violations.append((lineno,
                                   f"  transmission term '{key}' not in TRACKED_RECEIPTS",
                                   'unanchored-transmission'))

    return violations


def main():
    any_violation = False
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        for path in sorted(d.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            hits = scan_file(path)
            if hits:
                any_violation = True
                for lineno, text, rule in hits:
                    label = {
                        'quality-coeff':          'VIOLATION[quality-coeff]',
                        'empty-failure-conditions': 'VIOLATION[M7.3a-bret]',
                        'unanchored-transmission':  'VIOLATION[M7.3b-olleus]',
                    }.get(rule, 'VIOLATION')
                    print(f"{label}  {path}:{lineno}  {text.strip()}")

    if any_violation:
        print("\nFAIL: receipts violations found. Remove them or add a receipt.")
        sys.exit(1)
    else:
        print("receipts-check: OK (no quality coefficients or audit violations found)")


if __name__ == "__main__":
    main()
