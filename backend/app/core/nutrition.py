"""
Nutrition Helpers.

Maps textual goals to calorie/protein targets so downstream code can compute
progress against a user's intent without changing the DB schema.
"""
from __future__ import annotations

from typing import Optional, Tuple

# Default targets used when no goal is provided or goal is unrecognized.
DEFAULT_CALORIES = 2200
DEFAULT_PROTEIN_G = 100
DEFAULT_CARBS_G = 275  # ~50% of 2200
DEFAULT_FAT_G = 73     # ~30% of 2200

# Simple mapping of goal keywords to targets (Cal, Pro, Carbs, Fat).
GOAL_PRESETS = {
    "lose weight": (1800, 140, 150, 60),    # High protein, lower carb/fat
    "weight loss": (1800, 140, 150, 60),
    "cutting": (1800, 160, 130, 55),        # Aggressive cut
    "maintain": (2200, 110, 275, 73),
    "maintenance": (2200, 110, 275, 73),
    "gain muscle": (2600, 160, 300, 85),    # Surplus
    "muscle gain": (2600, 160, 300, 85),
    "bulk": (2800, 180, 330, 90),           # Heavy surplus
}


def goal_to_targets(goal: Optional[str]) -> Tuple[int, int, int, int]:
    """
    Return (calories, protein, carbs, fat) targets for a textual goal.

    Args:
        goal: Goal text saved in the user's profile.

    Returns:
        Tuple[int, int, int, int]: A tuple containing targets for:
        (calories, protein_g, carbs_g, fat_g).
    """
    if not goal:
        return DEFAULT_CALORIES, DEFAULT_PROTEIN_G, DEFAULT_CARBS_G, DEFAULT_FAT_G

    normalized = goal.strip().lower()
    # Exact match lookup first
    if normalized in GOAL_PRESETS:
        return GOAL_PRESETS[normalized]

    # Fuzzy contains checks for common words
    if "lose" in normalized or "cut" in normalized:
        return GOAL_PRESETS["lose weight"]
    if "gain" in normalized or "bulk" in normalized:
        return GOAL_PRESETS["gain muscle"]
    if "maintain" in normalized or "maintenance" in normalized:
        return GOAL_PRESETS["maintain"]

    return DEFAULT_CALORIES, DEFAULT_PROTEIN_G, DEFAULT_CARBS_G, DEFAULT_FAT_G