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


def sprout_plant():
    """Background job: a new plant sprouts and joins the collection."""
    species, emoji = random.choice(SPECIES)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO plants (species, emoji) VALUES (%s, %s)",
            (species, emoji),
        )
