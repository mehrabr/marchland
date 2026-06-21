# MARCHLAND — Code Audit Spec v2

*Supersedes v1. Re-audited after commit `47f8bc7` ("ci: GitHub Actions workflow; pin Python 3.14 and numpy==2.4.6; relative import fixes"), 2026-06-20. Findings below were verified by reading the changed files, not the commit message.*

**Status in one line:** The genuinely-broken bucket from v1 is **closed** — F2, F3, F4, R6, R2 are done, several better than asked, and the docs were hardened against future drift. F1 is **substantially** done but two pieces stop one step short of self-proof. One new test reintroduces a form-over-substance pattern; the CI is configured to float the interpreter it is meant to pin. Remaining work is a short, cheap punch list — not a refactor.

---

## ✅ §1 — RESOLVED by this push

- **[DONE] F2 — break-model claim.** `README.md` no longer claims "percolation / giant component." It now reads "fractional-standing break… a formation breaks when its standing strength falls below its `break_frac` threshold," which matches `core/lattice.py`.
- **[DONE] F3 — dead `hypothesis` dependency.** `hypothesis` is now imported and used in `tests/test_properties.py`. (Quality caveat: one of the three tests is not really property-based — see N1.)
- **[DONE] F4 — docs reconciliation.** All five edits landed: honest reproducibility envelope in both `README.md` and `CLAUDE.md` (Law 4); no-essences claim softened to "enforces forbidden field names… per-cohort scalars are authored with an in-world justification comment"; `code/` reframed as "frozen historical prototype… `core/` has diverged (M1+)"; officer annotated as a spike everywhere it appears. **Plus** the **Documentation Sync Rule** was added to `CLAUDE.md` verbatim — the single most valuable line in the push, because it stops the drift recurring.
- **[DONE] R6 — CI.** `.github/workflows/ci.yml` runs `receipts-check → make test → make battery` on push/PR. The battery is finally load-bearing. (Config gaps — see N3.)
- **[DONE] R2 — officer model.** Took the honest documentation path (v1 option b) and did it well: the module docstring opens "DESIGN SPIKE, not wired into simulation," states it has no callers in `lattice.py`/`chain.py`/`season.py`, and names the exact integration step. Candid in a way most codebases never manage.
- **[DONE] Cleanliness.** Relative-import inconsistency fixed in `core/officer.py`, `core/belief_db.py`, `core/scenarios/winter_quarters.py`.

---

## 🟡 §2 — PARTIAL / FINISH THESE (the punch list)

Small and cheap. These are the gap between "looks done" and "is done."

**[PARTIAL] F1 — reproducibility.** The core is correct: exact pins (`numpy==2.4.6`, `rich~=15.0`, `requires-python==3.14.*`), a committed golden hash on **seed-0 stochastic** (`tests/test_reproducibility.py`, `det=False` — the right oracle), an honest envelope in the docstring, and a self-documenting regeneration procedure. Two gaps remain:
- **F1-a — the tripwire has never been shown to trip.** CI runs a single numpy, so the gate that proves the pin is load-bearing doesn't exist. *Fix:* add a fail-soft matrix — `numpy: [2.4.6, 2.5.0]` where the off-pin leg is allowed to fail — so a future stream change is **seen** before it bites. Do not mark F1 fully closed until the hash has demonstrably flipped for the right reason.
- **F1-b — scope is one path.** The hash covers Agincourt-battle only; it does not cover the chain (siege→march→battle), meaning/horn, or sentiment dissolution. *Fix:* extend to one canonical run of the full chain — the path players actually traverse.

**[NEW] N1 — `test_properties.py` n=0 test is a unit test in property clothing.** `@given(n=st.integers(min_value=0, max_value=0))` with `max_examples=3` generates exactly one value (0) three times — the property-test decorator explores a space of size one. This is the v1 form-over-substance pattern (R5) reappearing inside the fix for the form-over-substance finding. *Fix:* widen to `st.integers(0, 5)` (strictly better — it also catches an off-by-one at n=1), or demote it to an honest `def test_zero_agent_cohort()` with no decorator.

**[NEW] N2 — property tests can crash on their own success.** Both the fatigue test and the n=0 test reduce over `b.fat[b.alive]` every tick. If `b.alive.sum()` ever hits zero (mutual annihilation before either side's break flag is set — reachable precisely because the fatigue test sweeps `fat0` up to 1.0 across 20 seeds), `.min()`/`.max()` on the empty slice raises `ValueError`. Hypothesis is built to find that corner. *Fix:* guard with `if b.alive.any():` before the reductions. Two lines.

**[NEW] N3 — CI floats the interpreter it is meant to pin.** `python-version: "3.14"` + `allow-prereleases: true` can resolve to a 3.14 release candidate or a free-threaded `cp314t` build with no matching numpy wheel → pip builds numpy from source against the runner's BLAS → the dev's local golden hash mismatches CI for reasons unrelated to the code. `runs-on: ubuntu-latest` floats the runner image on top of that. **Credit:** numpy 2.4.6 *does* ship `cp314` manylinux wheels with OpenBLAS bundled (verified, 21 cp314 wheels), so on **stable** 3.14 the pin genuinely fixes the BLAS and the envelope is sound — the flag is the gratuitous part, buying nothing (3.14 is released) while reintroducing the exact risk F1 closes. *Fix:* drop `allow-prereleases: true`, pin `runs-on: ubuntu-24.04`, and surface the reproducibility test as its own named CI step so a failure is immediately legible.

---

## 🔵 §3 — STILL OPEN (carried from v1; deferred against the "is it fun in text" gate)

Deferring these remains correct. Listed so they are not lost.

- **[GATED] R8 — retire `det=True`.** Still correctly gated on **F1-a**: do not delete the deterministic mode until seed-0 stochastic is proven stable across ≥2 numpy versions. Once F1-a lands, R8 unblocks and pays directly into R1 (fewer hot-loop branches).
- **[OPEN] R1 — `Battle.tick()` god-method** (`core/lattice.py`, ~244 lines). Extract named private methods over the shared arrays, single pass, no copies. Organizational, not architectural.
- **[OPEN] R3 — `code/` as oracle.** The *docs* were reframed (done, in F4). The *mechanism* — running `code/` as a golden-output oracle the battery diffs `core/` against — is not built. Optional; the reframing alone removed the misleading claim.
- **[OPEN] R4 — scattered Class D/E constants** (`officer.py`, `sentiment.py`, `meaning.py`). Centralize into `constants.py` and extend the sensitivity harness to sweep them.
- **[OPEN] R5 — derivation layer.** Now honestly *documented* as authored-not-derived (good). The actual functions (`err_from_drill_days`, `fat0_from_calories`, `belief_from_pay_state`) remain future work. **Watch item (Bret):** re-open immediately if anyone hand-tunes `err`/`belief` to pass a battery target.
- **[OPEN] R7 — per-tick Python loops** (`_update_phases`, meaning transform, per-death `_kill` loop). Scaling cliffs; vectorize before scaling agent/cohort counts or porting to Rust.
- **[OPEN, minor] Test-environment pinning.** `pytest`/`hypothesis` are unpinned, so the *test* environment isn't reproducible (doesn't affect sim outcomes, only test/flake behavior). Also: `test_properties.py` hardcodes the `0.5` clip ceiling (couples test to a constant) and imports inside a function body. Low priority.

---

## ✅ §4 — KEEP (still true; preserve as-is)

Carried from v1 and still valid: **P1** `core/trace.py` (single source of truth, done right), **P2** `core/chain.py` (composition by field-mapping), **P3** `core/constants.py` (labeled, frozen-by-convention), **P4** receipts discipline + `receipts_grep` + Bret/Olleus laws, **P5** the headless `core/` ↔ clients boundary (verified clean), **P6** test breadth + the honest-miss ledger, **P7** docs/design coherence + `season.py` decomposition.

New this push, worth preserving as habits:
- **The Documentation Sync Rule** in `CLAUDE.md` — institutionalizes anti-drift. Keep it and enforce it in review.
- **The officer spike annotation** — the right model for every not-yet-wired module: state plainly that it has no callers and name the integration step. Reuse this pattern.
- **Committing the audit spec into the repo** and the golden-hash test's self-documenting regeneration header — both make the project legible to its future self.

---

## Priority order

1. **N3 + F1-a** — fix CI (drop `allow-prereleases`, pin `ubuntu-24.04`, fail-soft `numpy: [2.4.6, 2.5.0]` matrix, named reproducibility step). Makes the pin actually enforced and proves the tripwire. Cheap, high-leverage.
2. **N1 + N2** — the two two-line test fixes. Stop "looks-done" from substituting for "is-done."
3. **F1-b** — extend the golden hash to one canonical chain run, so reproducibility covers the path players traverse. Then F1 closes.
4. **R8** — retire `det=True`; unblocked once F1-a lands.
5. **R2 integration, R1, R4, R5, R7** — against the fun gate; if the loop isn't fun yet, these wait.

*Standing dissent, kept on the record:*
- **Bret** — the n=0 test (N1) is a small instance of the pattern this whole audit exists to catch: a thing that *looks* validated but isn't. Two lines to fix, but treat it as a smell — watch whether "looks-done" keeps substituting for "is-done" in the next pushes.
- **Sloane** — until the hash is checked against a second numpy (F1-a), "reproducible" is a belief backed by a test that has never failed for the right reason. Don't mark F1 closed until the tripwire has demonstrably tripped.
- **Reza** — exact-patch pinning forfeits automatic security/bugfix patches; once the matrix gate is trusted to *catch* a stream change, revisit loosening `numpy==2.4.6` to `>=2.4.6,<2.5`. Let the test be the guard, not only the pin.
- **Tomas** — all of §2 is polish on a clean response. The dev cleared the genuinely-broken bucket faithfully; the highest-value next move is wiring the officer or playtesting the loop, not extending the punch list. Don't let a tidy response pull focus back to tidying.

**Sharpest true thing (unchanged in spirit from the analysis):** the dev closed the broken bucket faithfully and even hardened the docs against future drift — but the two fixes that matter most each stop one step short of self-proof: the reproducibility tripwire has never been shown to trip, and the CI meant to enforce the pin is configured to float the interpreter underneath it. The work is right; the proof that it's right is the part still missing.
