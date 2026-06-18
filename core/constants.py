"""MARCHLAND constants registry.

Class labels:
  A = bodies (every human, every era — never change without a battery run)
  B = transport technology (receipts; mixable)
  C = campaign state (fatigue, belief, stock)
  D = institutions (doctrine, officers, pay)
  E = trained capacities (drill error, ammo handling)

Changing any Class A constant requires a battery run and a note in results/.
"""

# ---- Battle: Class A (bodies) ----
BATTLE_A = dict(
    lam0=0.0008,      # A: base opening hazard / second
    lamx=2.2,         # A: load amplifier
    fat_amp=2.0,      # A: fatigue amplifier on opening hazard
    fat_melee=0.0035, # A: fatigue gain per tick in contact
    fat_move=0.0006,  # A: fatigue gain per tick moving
    fat_mud=4.0,      # A: mud fatigue multiplier
    fat_rec=0.0008,   # A: fatigue recovery per tick when stationary
    p_down=0.45,      # A: P(casualty | opening)
    hes=16.0,         # A: hesitation duration (seconds)
    horse_solid=3.0,  # A: foe density that balks cavalry
    # M1: phase pacing (assault-wave cycle)
    repulse_contact_s=200.0,  # A: seconds in contact before attacker repulse trigger
    reforming_s=360.0,        # A: attacker REFORMING duration (seconds)
    defender_reform_s=240.0,  # A: defender lull REFORMING duration (seconds)
    fat_reform_bonus=0.004,   # A: extra fatigue recovery per tick during REFORMING
    relief_fat_restore=0.12,  # A: fatigue reduction per rank-swap at REFORMING entry
    cavalry_reach_s=80.0,       # A: seconds in reach before cavalry withdraws to reform
    cavalry_reform_s=120.0,     # A: cavalry REFORMING duration (seconds)
    reform_retreat_spd=0.25,    # A: assault-wave infantry retreat speed (world-units/s) during REFORMING
    w=dict(
        downs=3.2,    # A: appraisal weight — own dead on ground
        rout=2.4,     # A: appraisal weight — own routing nearby
        expose=0.9,   # A: appraisal weight — combat load exposure
        behind=2.6,   # A: appraisal weight — foe flanking
        fat=1.0,      # A: appraisal weight — own fatigue
        banner=1.4,   # A: appraisal weight — leader lost
        press=0.8,    # A: appraisal weight — fear field
    ),
)

BATTLE_DT = 2.0  # A: tick size in seconds

# ---- Siege: Class A ----
SIEGE_A = dict(
    dis_base=0.0012,         # A: per-man/day disease hazard, week 1, decent camp
    dis_week=0.55,           # A: hazard growth per week encamped
    breach_storm_cost=0.18,  # A: expected assault losses, practicable breach
    nobreach_storm_cost=0.45,# A: expected assault losses, no breach
    honor_breach=1.0,        # A: garrison may yield with honor once breach practicable
    honor_days=28,           # A: or after a creditable duration
    relief_window=8,         # A: days of grace garrison asks (send to your king)
)

# ---- March: Class A (bodies) ----
GRAIN_KG = 1.4   # A: man/day staple equivalent
WATER_KG = 3.0   # A: man/day; carrying it triples the load
SPEED    = 2.5   # A: mph, the eternal constant of feet
DAYLIGHT = 10.0  # A: usable marching hours per day (baseline)
THIRST_K = 0.06  # A: per-man/day casualties once dry beyond carried water

# ---- March: Class B (transport technology) ----
MODES = dict(
    porter=dict(load=30,  eat=1.4,  vcap=2.5, col=0.001),
    pack  =dict(load=100, eat=6.0,  vcap=2.5, col=0.003),
    ox    =dict(load=540, eat=12.0, vcap=2.0, col=0.012),
    wagon =dict(load=550, eat=22.0, vcap=2.5, col=0.0125),
)
