"""F1 reproducibility gate: seed-0 stochastic traces must be bit-identical within the pinned runtime.

Reproducibility envelope: (inputs, seed) within numpy==2.4.6 on the same CPU architecture.
Cross-arch is NOT covered — float reductions (np.exp, sum, median) are libm/BLAS-order-dependent.
These hashes are the tripwires: if the numpy version changes, or an RNG call is reordered,
a hash flips and the change is caught before it silently breaks replay.
"""
import hashlib
import json

from core.scenarios.agincourt import agincourt
from core.lattice import Battle
from core.trace import Trace
from core.chain import run_chain_1415

# Generated on numpy==2.4.6, Python==3.14.*, seed=0 stochastic.
# To regenerate after a deliberate RNG-order change:
#   python3 -c "
#   import hashlib, json
#   from core.scenarios.agincourt import agincourt
#   from core.lattice import Battle
#   from core.trace import Trace
#   scn = agincourt(); trace = Trace(phase='battle', scenario='agincourt', seed=0)
#   b = Battle(scn, seed=0, det=False, trace=trace)
#   while b.bt[0] is None and b.bt[1] is None and b.t < 3600: b.tick()
#   d = trace.to_dict()
#   print(hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest())
#   "
GOLDEN_HASH = "d8f92e97934c409933507209e8365c11f58ec5c7692816f831ec7d34557afe59"


def _run_agincourt_seed0():
    scn = agincourt()
    trace = Trace(phase='battle', scenario='agincourt', seed=0)
    b = Battle(scn, seed=0, det=False, trace=trace)
    while b.bt[0] is None and b.bt[1] is None and b.t < 3600:
        b.tick()
    return trace


def test_seed0_stochastic_golden_hash():
    """Seed-0 stochastic Agincourt must reproduce bit-identically within the pinned runtime."""
    trace = _run_agincourt_seed0()
    d = trace.to_dict()
    h = hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()
    assert h == GOLDEN_HASH, (
        f"Trace hash changed: got {h}\n"
        f"Expected {GOLDEN_HASH}\n"
        "If this is intentional (deliberate RNG-order change or numpy upgrade), "
        "regenerate the hash using the command in this file's header and update GOLDEN_HASH."
    )


def test_seed0_determinism_two_runs():
    """Running seed-0 twice must produce identical traces (within-process determinism)."""
    t1 = _run_agincourt_seed0()
    t2 = _run_agincourt_seed0()
    assert len(t1.deaths) == len(t2.deaths), "Death count differs between runs of same seed"
    for a, b_ in zip(t1.deaths, t2.deaths):
        assert a.t == b_.t and a.agent_id == b_.agent_id and a.cause == b_.cause, (
            f"Death cert mismatch: {a} vs {b_}"
        )


# ---------------------------------------------------------------------------
# F1-b: Full 1415 chain (Harfleur siege → Agincourt march → Agincourt battle)
# Covers the path players actually traverse — single-phase hash covers only one model.
#
# Generated on numpy==2.4.6, Python==3.14.*, seed=0.
# To regenerate after a deliberate RNG-order change:
#   python3 -c "
#   import hashlib, json
#   from core.chain import run_chain_1415
#   result = run_chain_1415(seed=0)
#   h = hashlib.sha256(json.dumps(result['trace'], sort_keys=True, default=str).encode()).hexdigest()
#   print(h)
#   "
CHAIN_GOLDEN_HASH = "c65f2919dfeb062b3c592d13d96e88e288ad64fe4410f0423ac47f352d5667dc"


def test_chain_1415_seed0_golden_hash():
    """Full 1415 chain seed-0 must reproduce bit-identically within the pinned runtime."""
    result = run_chain_1415(seed=0)
    h = hashlib.sha256(
        json.dumps(result['trace'], sort_keys=True, default=str).encode()
    ).hexdigest()
    assert h == CHAIN_GOLDEN_HASH, (
        f"Chain trace hash changed: got {h}\n"
        f"Expected {CHAIN_GOLDEN_HASH}\n"
        "If intentional, regenerate using the command in this file and update CHAIN_GOLDEN_HASH."
    )
