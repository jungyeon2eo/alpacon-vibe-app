import random

from db import get_conn

# Peaceful little meadow flora the alpaca discovers while grazing.
SPECIES = [
    ("Daisy", "🌼"),
    ("Tulip", "🌷"),
    ("Sunflower", "🌻"),
    ("Clover", "🍀"),
    ("Blossom", "🌸"),
    ("Fern", "🌿"),
    ("Lotus", "🪷"),
    ("Wheat", "🌾"),
    ("Sprout", "🌱"),
    ("Hibiscus", "🌺"),
]


def sprout_plant(player_id: str):
    """Background job: a new plant sprouts and joins this player's collection."""
    species, emoji = random.choice(SPECIES)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO plants (player_id, species, emoji) VALUES (%s, %s, %s)",
            (player_id, species, emoji),
        )
