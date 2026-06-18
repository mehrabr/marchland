"""Battery CI gate: exit 1 if any grade-A target fails or any target is missing an entry.

Rules:
  - Every key in TARGETS must have a corresponding entry in battery/entries/*.json.
    A PR that adds a new scenario target without an entry JSON fails CI.
  - Any grade-A target that does not pass causes exit 1.
  - Grade-B misses are printed as warnings; grade-C are informational.

Usage:
    python -m battery.ci            # 12 seeds
    python -m battery.ci --seeds 50
"""
import argparse, sys
from battery.runner import grade_all, load_entries, print_table
from battery.targets import TARGETS


def check_entry_coverage() -> list[str]:
    """Return TARGETS keys that have no entry in battery/entries/."""
    entries = load_entries()
    return [key for key in TARGETS if key not in entries]


def main() -> None:
    ap = argparse.ArgumentParser(description="MARCHLAND battery CI gate")
    ap.add_argument("--seeds", type=int, default=12)
    args = ap.parse_args()

    # Coverage check — fast, runs before the battery.
    missing = check_entry_coverage()
    if missing:
        print("CI FAIL: the following targets have no entry in battery/entries/:")
        for key in sorted(missing):
            print(f"  missing: {key}")
        print("\nAdd a JSON entry for each target to battery/entries/<scenario>.json")
        print("Format: {\"target.key\": [range_desc, grade, source_note, actual, pass]}")
        sys.exit(1)

    entries = load_entries()

    rows, a_failures = grade_all(args.seeds)
    print_table(rows)

    # Grade-B warnings with source notes from entry JSON.
    b_warns = [(key, grade, status, err, desc)
               for key, grade, status, err, desc in rows
               if grade == "B" and status == "warn"]
    if b_warns:
        print("Grade-B warnings (findings, not failures):")
        for key, *_ in b_warns:
            entry = entries.get(key, [])
            note = entry[2] if len(entry) > 2 else ""
            print(f"  [{key}]  {note}")
        print()

    a_total = sum(1 for _, g, *_ in rows if g == "A")
    a_pass  = sum(1 for _, g, s, *_ in rows if g == "A" and s == "PASS")
    b_count = len(b_warns)

    print(f"Grade-A: {a_pass}/{a_total} pass  |  Grade-B warnings: {b_count}")

    if a_failures:
        print(f"\nCI FAIL: {a_failures} grade-A target(s) did not pass.")
        sys.exit(1)

    print("CI GREEN: all grade-A targets pass.")
    sys.exit(0)


if __name__ == "__main__":
    main()
