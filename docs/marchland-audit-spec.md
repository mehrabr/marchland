# MARCHLAND — Code Audit Spec

*Output of an expert deliberation panel (engine architecture, performance, product, infra skepticism, test/maintainability, shipping pragmatism). Three rounds, dissent preserved. Scope: design, performance, optimization, architecture, modularity, cleanliness, expandability.*

**One-line verdict:** Architecture is right and worth preserving; the recurring flaw is *validating systems as isolated units and declaring them shipped before the integration/derivation that makes the claim true*. What is broken **now** is narrow and cheap to fix: the reproducibility guarantee is unenforced, and several front-page claims (bit-identity, percolation break, no-essences) outrun the code.

**Scope note / standing dissent (read first):** This is a P0 vertical slice whose own docs set the bar at "is it fun in text first." If playtests say the loop isn't fun yet, the **REFACTOR** list below should wait — do not gold-plate a hull before knowing it floats. The **FIX NOW** list is cheap and should happen regardless.

---

## ✅ KEEP — praise, preserve as-is

**P1. `core/trace.py` — the single source of truth, done right.**
Clean dataclasses (`DeathCert`, `RoutEvent`, `Trace`), typed, with `to_dict()` and `compose_traces()`. The "only omniscient object" is actually modeled as such, and chronicles/belief-DBs are explicitly partial views of it. This is exemplary; hold it as the reference for code quality elsewhere.

**P2. `core/chain.py` — composition by field-mapping, not assertion.**
`siege_to_march()` / `march_to_battle()` are pure functions: input dict → `deepcopy` → modified scenario, each citing the spec (§III-D), invariants preserved (`max(1, ...)`, `np.clip`). This is the architectural spine and it is correct. The "models compose by field mapping, never by assertion" principle is genuinely realized.

**P3. `core/constants.py` — labeled, documented, frozen-by-convention.**
Class A–E labels in every docstring, units commented, "changing a Class A constant requires a battery run." Where this discipline is applied it is excellent (see R4 for where it isn't).

**P4. Receipts data discipline + `tools/receipts_grep.py` + Bret/Olleus laws.**
Scenario files (`core/scenarios/agincourt.py` etc.) read as legible receipts — every per-cohort number carries an inline in-world justification, no hidden stat blocks. The grep gate, plus Bret's law (no meaning without a failure path) and Olleus's law (no contagion term outside `TRACKED_RECEIPTS`), is a real, enforced, self-auditing constraint most simulations lack. (Substance caveat: see R5.)

**P5. Headless `core/` ↔ trace-playback clients — boundary verified.**
`core/` imports nothing from `clients/` or `tools/` (grep-confirmed). This is the boundary that makes the stated Rust-core / Unity-renderer path actually possible later. Keep it inviolable.

**P6. Test breadth and the honest-miss culture.**
356 test functions; per-subsystem determinism tests; battery-as-spec with graded A/B/C targets and an **open ledger of misses recorded rather than tuned away** (Isandlwana line, Sphacteria, storm_launched). Recording misses instead of fudging constants to hit them is rare and is a cultural asset. (Net coverage gaps: see F3, R6.)

**P7. Documentation/design coherence; `season.py` decomposition.**
The Bible/addenda/README articulate invariants the code mostly honors. Despite being 1014 lines, `clients/cli/season.py` is well-factored into named phase functions (longest ~86 lines) — size is breadth, not a god-module.

---

## ⚠️ REFACTOR — concerning; fix for the future, with the how

**R1. `Battle.tick()` is a 244-line god-method.** — `core/lattice.py:200–443`
It does density grids, movement, cavalry, wall logic, volleys, melee, fatigue, appraisal, the meaning transform, feints, the leader lottery, and break/pursuit in one body. Un-unit-testable; risky to modify.
*How:* extract **named private methods that operate on the shared arrays in place** — `_resolve_phases()`, `_move()`, `_cavalry()`, `_walls()`, `_melee()`, `_appraise()`, `_break_and_pursue()`. **Constraint:** keep it one pass, no defensive array copies — this is organizational, not a re-architecture. Perf must be identical; the win is readability + testability of each stage.

**R2. The Officer model is not wired into the simulation.** — `core/officer.py`
`process_order()` / `seek_opportunity()` / `OfficerDecision` have **no caller** in `lattice.py`, `chain.py`, or `season.py` (grep-confirmed; `season.py` only records the *event name* `'officer_requests_orders'` and has a narrative "showcase" — it never instantiates `Officer`). M7.7 is verified in isolation and inert in play.
*How:* pick one and state it in the README. Either **(a) integrate** — build the path `Battle state → officer belief DB → process_order → action applied to the cohort` so divergence actually changes outcomes; or **(b) relocate** to an explicit `experimental/` (or mark it a design spike in the module docstring) so it stops reading as shipped. Do not leave it ambiguous.

**R3. `code/` vs `core/` have diverged; the "reference implementation" framing is now false.** — `code/marchland_toy.py` (284 lines) vs `core/lattice.py` (557 lines)
`code/` is imported nowhere outside `code/`, and `core/` has mechanics `code/` never had (M1 phases, M7 meaning, convergent horn). "If a port breaks a battery result, the port is wrong" can no longer hold.
*How:* repurpose `code/` as a **golden-output oracle** — run both on the scenarios `code/` still covers and assert `core/` reproduces those baselines in the battery — *or* retire the "do not delete / port target" language. A frozen oracle the battery diffs against is valuable; a museum piece labeled "the truth" is misleading.

**R4. Class D/E constants are scattered outside the registry.** — `core/officer.py:29,32,35`; `core/sentiment.py:96–98`; `core/meaning.py` (class attrs `FLIP_THRESHOLD`, `DECAY_PER_DAY`, `BASE_SPREAD`, `SUICIDAL_FOE_DENSITY`, `EXPLOITABLE_GAP_THRESHOLD`, `DISPATCH_AMBIGUITY_THRESHOLD`)
The stated discipline is "constants live in `constants.py` with a class label." The M7 subsystems broke it, which means the **sensitivity harness never sweeps them** (it perturbs `constants.py` Class-A only) — so these tuning knobs are silently untested for load-bearing-ness.
*How:* move them into `constants.py` (e.g. `OFFICER_D`, `SENTIMENT_D`, `MEANING_D` dicts) with class labels, import from there, and extend the sensitivity harness to perturb D/E too.

**R5. The no-essences law enforces vocabulary, not substance.** — `tools/receipts_grep.py` FORBIDDEN regex vs `core/scenarios/agincourt.py` + `core/lattice.py:304`
`err`, `belief`, `disc` are hand-authored per-cohort scalars; `err` multiplies the opening hazard directly (`lam = A['lam0']*self.err*...`). The "receipt" (drill-days→err, calories→fat0, pay→belief) lives in a **comment**, not a function. The grep bans the names `quality`/`modifier`/`coeff` but not the concept.
*How:* add the missing **derivation layer** — real functions `err_from_drill_days()`, `fat0_from_calories()`, `belief_from_pay_state()` so the number is *computed from a receipt*, not asserted beside one. If that's out of scope for P0, then explicitly document in the README that "scenario authoring is the receipt layer; the grep guards naming only," and soften the stronger claims. **Watch item (Bret's dissent):** if anyone hand-tunes `err` to make a battery target pass, that is a quality coefficient wearing an approved name — re-open this immediately.

**R6. No enforced CI; pre-commit covers almost nothing.** — `.pre-commit-config.yaml` (receipts-grep only, scoped to `core/scenarios|cultures`); no `.github/workflows`
The battery is "the spec" only if something forces it to run. Today the gates are advisory.
*How:* add a GitHub Actions workflow running `make test`, `make battery`, `make receipts-check` on push/PR. Broaden pre-commit (or accept local-only and say so). Add a linter/formatter (ruff) — there is currently no style gate, which partly explains the lattice terseness.

**R7. Python loops inside the hot path — scaling cliffs.** — `core/lattice.py:117–185` (`_update_phases` per-cohort loop every tick), `:328–351` (per-cohort meaning transform every tick), `:507–512` (per-death Python loop in `_kill`)
Fine at current scale (agents ≈ men/10, small cohort count K). They become the bottleneck if agent/cohort counts grow, and they undercut the determinism + perf story for the planned Rust port.
*How:* before scaling up, vectorize the per-cohort phase update (`np.bincount`/segment ops keyed on `ci`) and batch the trace death-writes. Not urgent at P0 sizes; flag it so it's a conscious deferral, not a surprise.

**R8. Retire the `det=True` deterministic mode — gated on F1.** — `core/lattice.py` (`self.det` branches at `:98`, `:357–361`, `:381`, `:384`, `:391`, `:480–486`, `:495`; shadow accumulators `accs`/`facc`/`vacc`)
Two reproducible modes is one too many. `det=True` threads ~10 parallel branch sites through `tick()` — the codebase's most dangerous function — duplicating every sampling decision, and (per F1) it is the *more* float-fragile of the two across machines, so it is the worse canonical trajectory. Once F1 establishes seed-0-stochastic as the oracle, det earns nothing.
*How:* after F1's golden hash is proven stable across ≥2 numpy versions, delete the `det` path and its accumulators; this collapses the branch count in `tick()` and directly serves R1 (the god-method extraction). **Gate (Sloane's dissent, below):** do **not** delete until the stochastic oracle is proven — a reproducibility spine with no canonical trajectory is worse than a redundant mode. Keep `det` until then.

*(Cleanliness, minor:)* import style is mixed — most of `core/` uses relative imports, but `core/officer.py:22`, `core/belief_db.py:20`, and `core/scenarios/winter_quarters.py:21` use absolute `from core....`. Pick one (relative, to match the majority) and lint it.

---

## 🔴 FIX NOW — broken against a core claim, and cheap

**F1. Reproducibility is unenforced, and the deterministic mode is the wrong oracle for it.** — `pyproject.toml` (`numpy`, `rich` unversioned), `core/lattice.py` (`default_rng().random/.uniform/.binomial/.shuffle`; `det=True` float accumulators `accs`/`facc`/`vacc`, e.g. `:101`, `:360`, `:483`)
Law 4 / the README promise replay "bit-identically from (inputs, seed, version)." Two problems. (1) Nothing pins dependencies. (2) The sim's randomness is numpy's `Generator` (`default_rng`), which **by numpy's own policy carries no cross-version stream guarantee** — "as better algorithms evolve the bit stream may change"; the seeded stream holds only "on the same build of numpy, in the same environment, on the same machine." NEP 19's prescription for bit-reproducibility is explicit: *use the exact version of numpy.* So a different `pip install` can silently change `.binomial`/`.uniform`/`.shuffle` outcomes. The `det=True` accumulator path avoids `Generator` but is **more** fragile cross-machine (float-reduction order is BLAS/SIMD-dependent), so it is the worse canonical trajectory, not the better one.

*Fix — do now (cheap):*
1. **Pin exactly.** As of June 2026 the current line is:
   ```toml
   dependencies = [
       "numpy==2.4.6",   # exact: Generator streams are not guaranteed across versions (NEP 19). Avoid 2.4.0 (yanked) and 2.5.0rc (pre-release).
       "rich~=15.0",     # rendering only; never affects a sim outcome — compatible-release pin is fine.
   ]
   requires-python = "==3.12.*"   # record one (2.4.6 supports 3.11–3.14); pick and freeze it.
   ```
2. **Golden-hash test on seed-0 *stochastic* (not `det`).** Run one canonical seed end-to-end, hash the composed trace, commit the hash, assert in CI. Use stochastic because its core is PCG64 — an integer bit generator numpy blesses as the "firmer building block" — whereas `det`'s float accumulators flip an agent at the `a >= 1.0` boundary on any sub-ULP rounding difference. This converts "we believe it's deterministic" into a tripwire.
3. **Gate the hash across ≥2 numpy versions** before trusting the pin — proves the pin is load-bearing and tells you the exact upgrade that would break replay.
4. **State the real envelope** (do not imply universal bit-identity): *reproducible from (inputs, seed) within the pinned runtime, on the same CPU architecture.* Cross-arch is **not** covered — `np.exp` and every `.sum()/.mean()/.median()` reduction in `lattice.py` (e.g. `:454`, `:478`) is libm/BLAS-order-dependent.
5. **New maintenance invariant:** don't change the *shape/order* of an RNG call. numpy reserves different algorithms for different-sized blocks (`rng.random()` ≠ `rng.random(5)`), so refactoring a draw from full-array to masked-subset shifts the stream *even under the pin* — the golden hash is what catches it.

*Game-level follow-through:* the "version" in (inputs, seed, version) must become a **recorded save field that is checked on load** — replaying a save authored under a different numpy must warn/refuse, not silently diverge. Vendor the interpreter+numpy with the game so a player's environment can't drift.

*Demoted (was "schedule"):* fixed-point arithmetic. If pinned-numpy + seed-0-stochastic holds across versions, fixed-point is **not** needed for the single-player prototype. It moves to the Rust-port boundary and becomes mandatory only if you ever claim cross-*platform* bit-identity (shared replays, leaderboards, lockstep netplay) — see the standing dissent.

**F2. README claims a percolation / giant-component break mechanism the code does not implement.** — `README.md:56` ("loses its giant component") vs `core/lattice.py:407` (`stand < bf * m.sum()`, a headcount fraction); "percolation"/"giant component" appear **nowhere** in the code (grep-confirmed).
This is a correctness bug in user-facing docs.
*Fix:* one-line-honest now — correct the README to describe the actual fractional-standing break rule. (Implementing real percolation is a legitimate future feature, but that belongs in REFACTOR, not in a claim made today.)

**F3. `hypothesis` is a declared dependency with zero usage; the promised property tests don't exist.** — `pyproject.toml` deps vs `tests/` (no `@given`, grep-confirmed); CLAUDE.md explicitly promises property tests for `n=0` no-crash, fatigue ∈ [0,1], non-negative `start`.
Misrepresents the test strategy and ships a dead dep.
*Fix:* either remove `hypothesis` from dependencies, or add the three property tests CLAUDE.md already specified (they're small and directly check stated invariants). Removing is two minutes; adding is an hour and closes a real gap.

**F4. Reconcile the README/BIBLE with what the code actually does and claims.** — `README.md`, `00-BIBLE.md`, `CLAUDE.md`
Several headline claims now overstate the implementation. False claims in the front-page docs are a correctness bug; the fixes are mostly one-liners and should ship with F1–F3. Make these edits, each tied to its finding:
- **(a) Reproducibility envelope (→ F1).** Replace "Every outcome replays bit-identically from the same seed" and "(inputs, seed, version)" with the honest statement: *reproducible from (inputs, seed) within the pinned runtime, same CPU architecture.* Name the pin (`numpy==2.4.6`) and the save-version check as the mechanism.
- **(b) Battle-break mechanism (→ F2).** Delete "Formations break when their coverage loses its giant component, not when they hit zero." Describe the actual rule: a formation breaks when standing strength drops below its `break_frac` threshold (a fractional headcount). If percolation is a roadmap goal, label it explicitly as *planned*, not present.
- **(c) No-essences claim (→ R5).** State plainly that `receipts_grep` guards forbidden *field names*, and that per-cohort scalars (`err`, `belief`, `disc`) are currently *authored with a justifying comment*, not *derived from a receipt function*. Soften "no number may differ between forces without a receipt" to match what is actually enforced today.
- **(d) The `/code` directory (→ R3).** Stop describing it as "the validated reference implementation / the porting targets for `core/`" as though `core/` mirrors it. Describe its real status: a frozen historical prototype (and candidate golden-output oracle), now diverged from `core/`.
- **(e) Deterministic mode (→ R8).** When `det=True` is removed, delete its mentions from the README/architecture notes so docs and code stay in sync.
- **Process rule to stop future drift:** add one line to `CLAUDE.md` — *any change to a Law, a frozen constant, the reproducibility envelope, or a named mechanism requires a matching README/BIBLE edit in the same PR.*

---

## Priority order

1. **F1** — pin `numpy==2.4.6` + Python + `rich~=15.0`, golden-hash seed-0 *stochastic*, record+check version in saves. The thesis is unprovable off one machine until this lands.
2. **F2, F3, F4** — cheap correctness done in the same pass: fix the false break-mechanism claim, resolve the dead `hypothesis` dep, and reconcile the README to the honest reproducibility envelope.
3. **R6** (CI) — makes the battery actually load-bearing; it should be what runs the F1 golden hash.
4. **R8** (retire `det=True`) — **gated**: only after F1's stochastic oracle is proven stable across ≥2 numpy versions. Pays directly into R1.
5. **R2** (decide officer: integrate vs. relocate) — stop a feature from reading as shipped while inert.
6. **R1, R4, R5, R3, R7** — schedule against the "is it fun in text" gate; if the loop isn't fun yet, these wait.

*Standing dissent, kept on the record:*
- **Tomas** — everything past F1–F4 + R6 may be premature for a P0 measured on fun; settle whether the game is fun before investing in either rails or chaos.
- **Bret** — until receipts are *computed* (R5), treat the README's stronger no-essences claims with suspicion; re-open immediately if anyone hand-tunes `err`/`belief` to pass a battery target.
- **Sloane** — a pinned `Generator` is reproducible on one machine/build only, which is strictly weaker than the README's claim. Own the RNG (raw PCG64 / fixed-point) by the Rust port at the latest, and keep the docs' claim downgraded until then. Re-open the moment shared replays, leaderboards, or lockstep netplay enter scope — the pin silently fails there.
- **Reza** — exact-patch pinning forfeits automatic security/bugfix patches; once the golden-hash gate is trusted to *catch* a stream change, revisit loosening `numpy==2.4.6` to `>=2.4.6,<2.5`. Let the test be the guard, not only the pin.
