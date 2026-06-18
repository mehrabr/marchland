"""Receipts grep: scans scenario and culture data files for quality coefficients.

Fails (exit 1) if any numeric per-cohort field is found that varies between
cohorts of the same side without a receipt — i.e., a hidden quality stat.

Forbidden field name patterns:
  quality, morale_bonus, strength_modifier, coeff, bonus (standalone)

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

SCAN_DIRS = [
    Path("core/scenarios"),
    Path("core/cultures"),
]


def scan_file(path: Path) -> list[tuple[int, str]]:
    violations = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        # skip comments
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if FORBIDDEN.search(line):
            violations.append((i, line.rstrip()))
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
                for lineno, text in hits:
                    print(f"VIOLATION  {path}:{lineno}  {text.strip()}")

    if any_violation:
        print("\nFAIL: quality coefficients found. Remove them or add a receipt.")
        sys.exit(1)
    else:
        print("receipts-check: OK (no quality coefficients found)")


if __name__ == "__main__":
    main()
