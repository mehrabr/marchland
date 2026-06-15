"""Siege scenario for Harfleur 1415. Class B/C/D receipts only."""


def harfleur(relief=None):
    return dict(
        besieger=11500, garrison=400, town_food_days=55,
        guns_rate=0.034,        # 12 great guns vs strong walls: ~30d to practicable (B receipt)
        camp_factor=2.2,        # marshy ground, August heat, shellfish (C receipt)
        sea_supply=True, relief_day=relief, storm_threshold=0.30,
        season_pressure=1.0, max_days=70,
    )


def harfleur_relief25():
    return harfleur(relief=25)
