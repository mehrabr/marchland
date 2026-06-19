"""March scenario inputs: class B/C/D receipts. No quality coefficients."""
from ..march import scenario


def agincourt_march():
    return scenario(
        start=8400, distance=200, pace=15.5, carriers={'wagon':60,'pack':200},
        land_density=14, season_factor=0.7, stock_days=8, weather=1.5,
        officers=0.85, camp_quality=0.7, home_pull=0.05, pay_arrears=0.2,
        desert_share=0.3, cohesion0=0.75, fat0=0.20,
        rumor_pressure=1.0, detours=[(8,60,'road_blocked')], max_days=22,
    )


def danube_1704():
    return scenario(
        start=21000, distance=250, pace=9.5, rest_every=4, roads=2,
        carriers={'wagon':1700}, forage=False, depot_every=4, depot_days=5,
        stock_days=6, dispersal=0.05, disease_env=0.9, officers=1.0,
        camp_quality=1.0, home_pull=0.5, desert_share=0.8,
        cohesion0=0.85, fat0=0.05, max_days=45,
    )


def niemen_1812():
    return scenario(
        start=286000, distance=520, pace=11.0, roads=3, road_quality=0.8,
        carriers={'wagon':9000}, land_density=10, season='dry', season_factor=0.8,
        stock_days=24, dispersal=0.5, screen_miles=15, weather=1.4,
        disease_env=2.6, officers=0.55, camp_quality=0.5,
        home_pull=0.7, pay_arrears=0.3, desert_share=0.6, fat0=0.05, max_days=78,
    )


def gedrosia_325():
    return scenario(
        start=40000, distance=460, pace=12.0, carriers={'pack':3000},
        land_density=0.6, season_factor=0.4, stock_days=10, water_ok=0.62,
        water_carry_days=1.5, heat=1.5, weather=1.3, disease_env=1.2,
        officers=0.7, camp_quality=0.5, home_pull=0.05, desert_share=0.1,
        cohesion0=0.8, fat0=0.15, max_days=70,
    )


def sherman_1864():
    return scenario(
        start=62000, distance=285, pace=12.0, roads=4, road_quality=1.0,
        carriers={'wagon':2500}, land_density=22, season_factor=1.1, stock_days=20,
        dispersal=0.6, screen_miles=25, officers=0.95, camp_quality=0.95,
        home_pull=0.3, desert_share=0.7, cohesion0=0.9, fat0=0.05, max_days=40,
    )
