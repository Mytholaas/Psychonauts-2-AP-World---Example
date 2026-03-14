"""
Psychonauts 2 Archipelago - Access Rules

This module translates the Item_Required strings from the check CSV into
Archipelago access-rule functions (``CollectionState → bool``).

Requirement string grammar (informal):
  - Comma-separated tokens are ANDed together.
  - A token containing " or " is an OR between two alternatives.
  - A token that starts with "or " (preceded by a comma in the original CSV)
    is an OR alternative that is merged with the *previous* token.
  - "All_ScavHunt_Items" expands to requiring all 16 scavenger-hunt items.
  - "NULL" or empty string means no requirement.

Item-key normalisation:
  - "Thought_Tuner" → "ThoughtTuner" (CSV naming inconsistency)
  - "PyroKinesis"   → "Pyrokinesis"  (typo in the check CSV)
  - Progressive-group CSV keys are mapped to their progressive display names
    (e.g. "MentalConnection_Upgrade3" → "Progressive Mental Connection" count 4)

Progressive ability / equipment rules:
  For progressive items the rule checks ``state.has(name, player, count)``
  where count is the 1-based position within the four-tier group:
    base ability    → count 1
    _Upgrade1       → count 2
    _Upgrade2       → count 3
    _Upgrade3       → count 4
"""

from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING
from worlds.generic.Rules import set_rule, add_rule

if TYPE_CHECKING:
    from BaseClasses import CollectionState, MultiWorld
    from . import Psy2World

from .items import (
    ALL_PROGRESSIVE_GROUPS,
    SCAV_HUNT_DISPLAY_NAMES,
    csv_key_to_display_name,
)

# ---------------------------------------------------------------------------
# Requirement-key normalisation
# ---------------------------------------------------------------------------

# Fixes for naming inconsistencies between the check CSV and the item CSV.
_KEY_CORRECTIONS: Dict[str, str] = {
    "Thought_Tuner": "ThoughtTuner",  # check CSV uses underscore; item CSV is camelCase
    "PyroKinesis":   "Pyrokinesis",   # capital K typo in some check CSV rows
}

# How many copies of a progressive item each upgrade level requires.
# base ability = 1 copy found, _Upgrade1 = 2 copies found, …
_PROGRESSIVE_COUNTS: Dict[str, Tuple[str, int]] = {
    # Telekinesis
    "Telekinesis":               ("Progressive Telekinesis", 1),
    "Telekinesis_Upgrade1":      ("Progressive Telekinesis", 2),
    "Telekinesis_Upgrade2":      ("Progressive Telekinesis", 3),
    "Telekinesis_Upgrade3":      ("Progressive Telekinesis", 4),
    # Psi Blast
    "PsiBlast":                  ("Progressive Psi Blast", 1),
    "PsiBlast_Upgrade1":         ("Progressive Psi Blast", 2),
    "PsiBlast_Upgrade2":         ("Progressive Psi Blast", 3),
    "PsiBlast_Upgrade3":         ("Progressive Psi Blast", 4),
    # Pyrokinesis (also accept the typo variant)
    "Pyrokinesis":               ("Progressive Pyrokinesis", 1),
    "PyroKinesis":               ("Progressive Pyrokinesis", 1),
    "Pyrokinesis_Upgrade1":      ("Progressive Pyrokinesis", 2),
    "Pyrokinesis_Upgrade2":      ("Progressive Pyrokinesis", 3),
    "Pyrokinesis_Upgrade3":      ("Progressive Pyrokinesis", 4),
    # Levitation
    "Levitation":                ("Progressive Levitation", 1),
    "Levitation_Upgrade1":       ("Progressive Levitation", 2),
    "Levitation_Upgrade2":       ("Progressive Levitation", 3),
    "Levitation_Upgrade3":       ("Progressive Levitation", 4),
    # Clairvoyance
    "Clairvoyance":              ("Progressive Clairvoyance", 1),
    "Clairvoyance_Upgrade1":     ("Progressive Clairvoyance", 2),
    "Clairvoyance_Upgrade2":     ("Progressive Clairvoyance", 3),
    "Clairvoyance_Upgrade3":     ("Progressive Clairvoyance", 4),
    # Mental Connection
    "MentalConnection":          ("Progressive Mental Connection", 1),
    "MentalConnection_Upgrade1": ("Progressive Mental Connection", 2),
    "MentalConnection_Upgrade2": ("Progressive Mental Connection", 3),
    "MentalConnection_Upgrade3": ("Progressive Mental Connection", 4),
    # Time Bubble
    "TimeBubble":                ("Progressive Time Bubble", 1),
    "TimeBubble_Upgrade1":       ("Progressive Time Bubble", 2),
    "TimeBubble_Upgrade2":       ("Progressive Time Bubble", 3),
    "TimeBubble_Upgrade3":       ("Progressive Time Bubble", 4),
    # Projection
    "Projection":                ("Progressive Projection", 1),
    "Projection_Upgrade1":       ("Progressive Projection", 2),
    "Projection_Upgrade2":       ("Progressive Projection", 3),
    "Projection_Upgrade3":       ("Progressive Projection", 4),
    # Equipment progressives
    "MindsEyelets":    ("Progressive Carry Capacity", 1),
    "Expandolier":     ("Progressive Carry Capacity", 2),
    "FluffPockets":    ("Progressive Fluff Pouch", 1),
    "JumboFluffPouch": ("Progressive Fluff Pouch", 2),
    "PsifoldWallet":   ("Progressive Wallet", 1),
    "AstralWallet":    ("Progressive Wallet", 2),
}


def _normalize_key(key: str) -> str:
    """Apply CSV naming corrections to a single item key."""
    return _KEY_CORRECTIONS.get(key, key)


# ---------------------------------------------------------------------------
# Single-token rule builder
# ---------------------------------------------------------------------------

CollectionRule = Callable[["CollectionState"], bool]


def _rule_for_key(key: str, player: int) -> CollectionRule:
    """
    Return a CollectionRule for a single normalised item key.

    Handles progressive items (by count), the All_ScavHunt_Items macro, and
    plain items.
    """
    key = _normalize_key(key)

    # ── Scavenger-hunt macro ─────────────────────────────────────────────────
    if key == "All_ScavHunt_Items":
        # Require all 16 scavenger-hunt collectibles.
        items = list(SCAV_HUNT_DISPLAY_NAMES)
        return lambda state, items=items, p=player: all(
            state.has(name, p) for name in items
        )

    # ── Progressive item ─────────────────────────────────────────────────────
    if key in _PROGRESSIVE_COUNTS:
        prog_name, count = _PROGRESSIVE_COUNTS[key]
        return lambda state, n=prog_name, c=count, p=player: state.has(n, p, c)

    # ── Plain item ───────────────────────────────────────────────────────────
    # Use the display name from the item table when available; otherwise use
    # the raw key (which may correspond to an Important item whose display name
    # equals the key, e.g. "Motherlobe_Access").
    display = csv_key_to_display_name.get(key, key)
    return lambda state, name=display, p=player: state.has(name, p)


# ---------------------------------------------------------------------------
# Requirement-string parser
# ---------------------------------------------------------------------------

def _parse_token(token: str, player: int) -> CollectionRule:
    """
    Parse a single comma-separated token and return a CollectionRule.

    Tokens may contain " or " to express alternatives between plain keys or
    compound "A and B" expressions.  Example:
        "TimeBubble or Levitation"
        "TimeBubble or Levitation and Levitation_Upgrade2"
    """
    token = token.strip()

    if " or " not in token:
        return _rule_for_key(token, player)

    # Build one rule per OR branch.
    branches: List[CollectionRule] = []
    for branch in token.split(" or "):
        branch = branch.strip()
        if " and " in branch:
            # Compound AND within an OR branch
            sub_rules = [_rule_for_key(k.strip(), player) for k in branch.split(" and ")]
            rule: CollectionRule = lambda state, sr=sub_rules: all(r(state) for r in sr)
        else:
            rule = _rule_for_key(branch, player)
        branches.append(rule)

    return lambda state, br=branches: any(r(state) for r in br)


def make_rule(requirement_str: str, player: int) -> Optional[CollectionRule]:
    """
    Convert an Item_Required string from the check CSV into a CollectionRule.

    Returns None when there is no requirement (NULL or empty string), which
    the caller can treat as "always accessible".

    Comma-separated tokens are ANDed together.  A token that begins with
    "or " is merged into the *previous* token as an additional OR branch
    (the CSV sometimes encodes complex OR/AND expressions this way):

        "TimeBubble, or Levitation and Levitation_Upgrade2, Cassie_Access"
        →  (TimeBubble OR (Levitation AND Levitation_Upgrade2)) AND Cassie_Access
    """
    if not requirement_str or requirement_str.upper() == "NULL":
        return None

    # Split by comma, then handle the "or X" continuation syntax.
    raw_tokens = [t.strip() for t in requirement_str.split(",")]

    # Merge "or …" continuations into the preceding token so they end up in
    # the same OR expression.
    merged: List[str] = []
    for token in raw_tokens:
        if token.startswith("or ") and merged:
            merged[-1] = merged[-1] + " or " + token[3:]
        else:
            merged.append(token)

    # Build a list of sub-rules that must ALL be satisfied (AND semantics).
    rules: List[CollectionRule] = [_parse_token(t, player) for t in merged if t]

    if not rules:
        return None
    if len(rules) == 1:
        return rules[0]
    return lambda state, rs=rules: all(r(state) for r in rs)


# ---------------------------------------------------------------------------
# Apply rules to the world
# ---------------------------------------------------------------------------

def set_rules(world: "Psy2World") -> None:
    """
    Assign access rules to every randomised location in the world.

    Each location's rule is derived from its Item_Required field in the CSV.
    Region-entry rules (area-access items) are set separately in __init__.py;
    the rule set here therefore strips the area-access token and only adds the
    *remaining* requirements as a location-level rule.

    The Maligula victory location's rule is also set here because it depends
    on the player's chosen win condition.
    """
    from .locations import REGION_ACCESS_ITEM, victory_location
    from .options import WinCondition
    from .items import WIN_CONDITION_REQUIRED_ITEMS, csv_key_to_display_name

    multiworld: "MultiWorld" = world.multiworld
    player: int = world.player

    # Map region name → area-access item display name for quick lookup.
    region_access_display: Dict[str, Optional[str]] = {}
    for region_name, access_key in REGION_ACCESS_ITEM.items():
        if access_key is None:
            region_access_display[region_name] = None
        else:
            region_access_display[region_name] = csv_key_to_display_name.get(
                access_key, access_key
            )

    # ── Per-location rules ───────────────────────────────────────────────────
    for loc_data in world.all_location_data:
        req_str = loc_data.requirements

        # Strip the area-access key from the requirement string so it is not
        # double-checked (the region entrance already handles it).
        area_access = REGION_ACCESS_ITEM.get(loc_data.region)
        if area_access and req_str:
            # Remove the area-access token (and any leading/trailing commas)
            tokens = [t.strip() for t in req_str.split(",") if t.strip() != area_access]
            req_str = ", ".join(tokens)

        rule = make_rule(req_str, player)
        if rule is not None:
            location = multiworld.get_location(loc_data.name, player)
            set_rule(location, rule)

    # ── Victory location rule (Maligula fight) ───────────────────────────────
    _set_victory_rule(world, player)


def _set_victory_rule(world: "Psy2World", player: int) -> None:
    """
    Set the access rule for the Maligula fight (victory) event location.

    The rule combines:
      1. GNG_Access (the fight always takes place in Green Needle Gulch).
      2. All items required by the player's chosen win condition.
    """
    from .items import WIN_CONDITION_REQUIRED_ITEMS, csv_key_to_display_name
    from .options import WinCondition
    from .locations import victory_location

    win_cond_value: int = world.options.win_condition.value
    win_cond_map = {
        WinCondition.option_normal:                "WinCondition_Normal",
        WinCondition.option_all_bosses:            "WinCondition_AllBosses",
        WinCondition.option_all_scav_hunt:         "WinCondition_AllScavHunt",
        WinCondition.option_scav_hunt_and_maligula:"WinCondition_ScavHunt_and_Maligula",
    }
    col = win_cond_map[win_cond_value]
    required_display_names: List[str] = WIN_CONDITION_REQUIRED_ITEMS.get(col, [])

    # Build a list of individual has() checks.
    gng_display = csv_key_to_display_name.get("GNG_Access", "GNG_Access")
    required_items: List[str] = [gng_display] + [
        n for n in required_display_names if n != gng_display
    ]

    # Resolve progressive items: if the win condition lists a raw ability key,
    # convert it to the appropriate progressive check.
    checks: List[CollectionRule] = []
    for display in required_items:
        # Check if this display name is the base of a progressive group
        if display in (
            "Progressive Telekinesis", "Progressive Psi Blast",
            "Progressive Pyrokinesis", "Progressive Levitation",
            "Progressive Clairvoyance", "Progressive Mental Connection",
            "Progressive Time Bubble", "Progressive Projection",
            "Progressive Carry Capacity", "Progressive Fluff Pouch",
            "Progressive Wallet",
        ):
            # Require at least the base level (1 copy)
            checks.append(
                lambda state, n=display, p=player: state.has(n, p, 1)
            )
        else:
            checks.append(
                lambda state, n=display, p=player: state.has(n, p)
            )

    if checks:
        combined: CollectionRule = lambda state, cs=checks: all(c(state) for c in cs)
        victory_loc = world.multiworld.get_location(
            victory_location.name, player
        )
        set_rule(victory_loc, combined)
