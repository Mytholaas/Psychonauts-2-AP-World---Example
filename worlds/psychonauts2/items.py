"""
Psychonauts 2 Archipelago - Item Definitions

All items are loaded from the CSV data file.  The main transformations are:

  Progressive psychic abilities
    Each ability has a base + 3 upgrades in the CSV.  All four rows are
    collapsed into N copies of "Progressive <Ability>" so that finding *any*
    copy of that item advances the player's ability level by one tier.

  Progressive equipment
    MindsEyelets / Expandolier, FluffPockets / JumboFluffPouch, and
    PsifoldWallet / AstralWallet each become 2 copies of a progressive item
    for the same reason.

  Event items
    Maligula_Complete is the victory event; it has no numeric ID and is never
    placed in the randomised pool.

  Extra items
    Senior_League_Card gates the Motherlobe Bowling Alley but was omitted from
    the item CSV.  It is added here as a Normal (useful) item.

Item ID base: 7_792_462
"""

import csv
import os
from typing import Dict, List, Optional, Set, Tuple
from BaseClasses import Item, ItemClassification

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ITEM_ID_BASE: int = 7_792_462
"""Starting numeric ID for all Psychonauts 2 items."""

_DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# Progressive group mappings
# ---------------------------------------------------------------------------

# Maps each individual CSV item key to the display name of its progressive
# group.  All members of a group share one ID and one display name; the pool
# contains one copy per group member so the player levels up through the group.
PROGRESSIVE_ABILITY_GROUPS: Dict[str, str] = {
    "Telekinesis":               "Progressive Telekinesis",
    "Telekinesis_Upgrade1":      "Progressive Telekinesis",
    "Telekinesis_Upgrade2":      "Progressive Telekinesis",
    "Telekinesis_Upgrade3":      "Progressive Telekinesis",
    "PsiBlast":                  "Progressive Psi Blast",
    "PsiBlast_Upgrade1":         "Progressive Psi Blast",
    "PsiBlast_Upgrade2":         "Progressive Psi Blast",
    "PsiBlast_Upgrade3":         "Progressive Psi Blast",
    "Pyrokinesis":               "Progressive Pyrokinesis",
    "Pyrokinesis_Upgrade1":      "Progressive Pyrokinesis",
    "Pyrokinesis_Upgrade2":      "Progressive Pyrokinesis",
    "Pyrokinesis_Upgrade3":      "Progressive Pyrokinesis",
    "Levitation":                "Progressive Levitation",
    "Levitation_Upgrade1":       "Progressive Levitation",
    "Levitation_Upgrade2":       "Progressive Levitation",
    "Levitation_Upgrade3":       "Progressive Levitation",
    "Clairvoyance":              "Progressive Clairvoyance",
    "Clairvoyance_Upgrade1":     "Progressive Clairvoyance",
    "Clairvoyance_Upgrade2":     "Progressive Clairvoyance",
    "Clairvoyance_Upgrade3":     "Progressive Clairvoyance",
    "MentalConnection":          "Progressive Mental Connection",
    "MentalConnection_Upgrade1": "Progressive Mental Connection",
    "MentalConnection_Upgrade2": "Progressive Mental Connection",
    "MentalConnection_Upgrade3": "Progressive Mental Connection",
    "TimeBubble":                "Progressive Time Bubble",
    "TimeBubble_Upgrade1":       "Progressive Time Bubble",
    "TimeBubble_Upgrade2":       "Progressive Time Bubble",
    "TimeBubble_Upgrade3":       "Progressive Time Bubble",
    "Projection":                "Progressive Projection",
    "Projection_Upgrade1":       "Progressive Projection",
    "Projection_Upgrade2":       "Progressive Projection",
    "Projection_Upgrade3":       "Progressive Projection",
}

PROGRESSIVE_EQUIPMENT_GROUPS: Dict[str, str] = {
    # Inventory-upgrade pairs: lower tier → higher tier, both progressive.
    "MindsEyelets":    "Progressive Carry Capacity",
    "Expandolier":     "Progressive Carry Capacity",
    "FluffPockets":    "Progressive Fluff Pouch",
    "JumboFluffPouch": "Progressive Fluff Pouch",
    "PsifoldWallet":   "Progressive Wallet",
    "AstralWallet":    "Progressive Wallet",
}

# Combined lookup used throughout this module
ALL_PROGRESSIVE_GROUPS: Dict[str, str] = {
    **PROGRESSIVE_ABILITY_GROUPS,
    **PROGRESSIVE_EQUIPMENT_GROUPS,
}

# ---------------------------------------------------------------------------
# Special item constants
# ---------------------------------------------------------------------------

VICTORY_ITEM_NAME: str = "Maligula Complete"
"""Display name of the victory event item placed at the Maligula fight check."""

# CSV keys that become event items (no numeric ID; never randomised).
_EVENT_ITEM_KEYS: Set[str] = {"Maligula_Complete"}

# CSV keys used as weighted filler when the pool needs padding.
FILLER_ITEM_KEYS: List[str] = ["PsiCore", "PsiPop", "DreamFluff"]

# ---------------------------------------------------------------------------
# Forced-progression override
# ---------------------------------------------------------------------------

# In Archipelago, only items with ItemClassification.progression are tracked in
# prog_items (via collect_item / World.collect).  Location access rules rely on
# state.has() which queries prog_items, so any item that appears in a rule MUST
# have the progression classification – regardless of what the CSV says.
#
# The items listed here are either Normal or Junk in the CSV but appear in the
# Item_Required column of the check CSV, meaning state.has() must recognise them.
_FORCED_PROGRESSION_KEYS: frozenset = frozenset({
    # Hub-area access items (Normal in the item CSV)
    "Motherlobe_Access",
    "Quarry_Access",
    "QA_Access",
    # Shop prerequisite (Junk in the item CSV)
    "Otto-Shot",
    # Extra item gating the Bowling Alley (not in the item CSV; added as Normal)
    "Senior_League_Card",
    # The 16 scavenger-hunt collectibles (Normal in the item CSV).
    # They appear in rules via the "All_ScavHunt_Items" macro which expands to
    # one state.has() call per item.
    "DayOldSushi", "EnemySurveillanceDevice", "NamePlaque", "DeckOfCards",
    "AstronautIceCream", "Laserdisc", "UnexplodedBomb", "PsitaniumKnife",
    "Human_Skull", "Novelty_Mug", "Can_of_Corn", "Switchblade_Hatchet",
    "MurderBot", "Beehive", "VikingHelmet", "Mindswarm",
})

# Extra items missing from the CSV but needed for complete rule coverage.
_EXTRA_ITEM_ROWS: List[Dict[str, str]] = [
    {
        "Index":        "558",
        "Item":         "Senior_League_Card",
        "Name":         "Senior League Card",
        "Item_Type":    "Important",   # Gates the Bowling Alley; must be progression
        "Max_Quantity": "1",
    }
]

# ---------------------------------------------------------------------------
# Scavenger-hunt item set
# ---------------------------------------------------------------------------

# The 16 physical scavenger-hunt collectibles.  These are required by the
# WinCondition_AllScavHunt / WinCondition_ScavHunt_and_Maligula options and
# are also referenced by the "All_ScavHunt_Items" requirement in the check CSV.
SCAV_HUNT_ITEM_KEYS: List[str] = [
    "DayOldSushi", "EnemySurveillanceDevice", "NamePlaque", "DeckOfCards",
    "AstronautIceCream", "Laserdisc", "UnexplodedBomb", "PsitaniumKnife",
    "Human_Skull", "Novelty_Mug", "Can_of_Corn", "Switchblade_Hatchet",
    "MurderBot", "Beehive", "VikingHelmet", "Mindswarm",
]

# ---------------------------------------------------------------------------
# Item data loading
# ---------------------------------------------------------------------------

def _classification_from_csv(item_type: str) -> ItemClassification:
    """Map an Item_Type string from the CSV to an Archipelago classification."""
    if item_type == "Important":
        return ItemClassification.progression
    if item_type == "Junk":
        return ItemClassification.filler
    return ItemClassification.useful  # "Normal"


def _item_type_suffix_from_key(item_key: str) -> str:
    """
    Derive a short type label from a CSV item key for disambiguating duplicate
    display names (analogous to _type_suffix_from_check_key in locations.py).
    """
    key_lower = item_key.lower()
    type_map = [
        ("_ham",          "Half-a-Mind"),
        ("_memoryvault",  "Memory Vault"),
        ("_purse_tag",    "Purse Tag"),
        ("_purse",        "Purse"),
        ("_nugget",       "Nugget of Wisdom"),
        ("_steamertrunk", "Steamer Trunk"),
        ("_dufflebag",    "Dufflebag"),
        ("_hatbox",       "Hatbox"),
        ("_suitcase",     "Suitcase"),
    ]
    for fragment, label in type_map:
        if fragment in key_lower:
            return label
    return item_key  # Fallback


def _read_item_rows() -> List[Dict[str, str]]:
    """Return all raw rows from the item CSV plus the hand-crafted extras."""
    path = os.path.join(_DATA_DIR, "Psychonauts_2_Item_List.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows + _EXTRA_ITEM_ROWS


def _build_tables() -> Tuple[
    Dict[str, Optional[int]],   # item_name_to_id
    Dict[str, ItemClassification],  # item_classifications
    List[str],                  # filler_item_names
    List[Tuple[str, ItemClassification]],  # base_item_pool entries
    Dict[str, str],             # csv_key_to_display_name
]:
    """
    Parse the item CSV and build the four primary data structures.

    Returns
    -------
    item_name_to_id
        {display_name: integer_id}.  The victory event maps to None.
    item_classifications
        {display_name: ItemClassification} for every randomised item.
    filler_item_names
        List of display names suitable for pool padding.
    base_item_pool
        Ordered list of (display_name, classification) for each copy of each
        item that belongs in the starting randomised pool.
    csv_key_to_display_name
        {csv_item_key: display_name} used by the rules module to translate
        requirement strings.
    """
    rows = _read_item_rows()

    # First pass: count how many times each base Name appears so we can
    # disambiguate duplicates with a type suffix (same strategy as locations.py).
    from collections import Counter as _Counter
    name_frequency: Dict[str, int] = _Counter(
        row["Name"] for row in rows if row["Item"] not in _EVENT_ITEM_KEYS
    )

    item_name_to_id: Dict[str, Optional[int]] = {}
    item_classifications: Dict[str, ItemClassification] = {}
    filler_item_names: List[str] = []
    base_item_pool: List[Tuple[str, ItemClassification]] = []
    csv_key_to_display: Dict[str, str] = {}

    # Register the victory event with a None ID so the world can reference it.
    item_name_to_id[VICTORY_ITEM_NAME] = None

    for row in rows:
        key: str = row["Item"]

        # ── Victory event: register mapping but skip pool placement ──────────
        if key in _EVENT_ITEM_KEYS:
            csv_key_to_display[key] = VICTORY_ITEM_NAME
            continue

        # ── Determine display name ───────────────────────────────────────────
        if key in ALL_PROGRESSIVE_GROUPS:
            display_name = ALL_PROGRESSIVE_GROUPS[key]
            # Progressive base items carry progression classification regardless
            # of what the CSV says for upgrades (upgrades are listed as Normal).
            classification = ItemClassification.progression
        else:
            base_name = row["Name"]
            # Disambiguate items that share a display name in the CSV
            if name_frequency[base_name] > 1:
                suffix = _item_type_suffix_from_key(key)
                display_name = f"{base_name} ({suffix})"
            else:
                display_name = base_name
            # Honour the forced-progression override first; fall back to CSV type.
            if key in _FORCED_PROGRESSION_KEYS:
                classification = ItemClassification.progression
            else:
                classification = _classification_from_csv(row["Item_Type"])

        csv_key_to_display[key] = display_name

        # ── Determine ID (progressive groups share the first item's index) ───
        if display_name not in item_name_to_id:
            item_id = ITEM_ID_BASE + int(row["Index"])
            item_name_to_id[display_name] = item_id
            item_classifications[display_name] = classification

        # ── Determine how many copies go into the pool ───────────────────────
        qty_str = row.get("Max_Quantity", "")
        if qty_str and qty_str not in ("", "NULL"):
            qty = int(qty_str)
        else:
            # Empty Max_Quantity → singleton (StoryComplete / access items)
            qty = 1

        for _ in range(qty):
            base_item_pool.append((display_name, classification))

        # Collect filler candidates for pool-padding
        if key in FILLER_ITEM_KEYS and display_name not in filler_item_names:
            filler_item_names.append(display_name)

    return (
        item_name_to_id,
        item_classifications,
        filler_item_names,
        base_item_pool,
        csv_key_to_display,
    )


# Build all tables once at import time.
(
    item_name_to_id,
    item_classifications,
    filler_item_names,
    base_item_pool,
    csv_key_to_display_name,
) = _build_tables()


# ---------------------------------------------------------------------------
# Win-condition required-item tables
# ---------------------------------------------------------------------------

def _build_win_condition_tables() -> Tuple[
    Dict[str, List[str]],  # win_condition_required_items
    List[str],             # scav_hunt_display_names
]:
    """
    Load win-condition data and resolve CSV keys to display names.

    Returns
    -------
    win_condition_required_items
        {win_condition_column_name: [display_name, ...]}
        Each list contains all items that must be obtained to satisfy that win
        condition (and which become progression items in the pool).
    scav_hunt_display_names
        Ordered list of display names for the 16 scavenger-hunt collectibles.
    """
    path = os.path.join(_DATA_DIR, "Psychonauts_2_WinConditions.csv")
    with open(path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        columns: Dict[str, List[str]] = {col: [] for col in fieldnames}
        for row in reader:
            for col, val in row.items():
                if val:
                    columns[col].append(val)

    # These entries describe events (fight activation / completion) that are
    # handled by the victory location rule, not by individual item requirements.
    # "Maligula_Complete" is the victory event item and must also be excluded
    # from the required-item list (it is placed as a locked event, not randomised).
    skip_keys: Set[str] = {
        "Maligula_Fight_Access",
        "Maligula_Fight_Complete",
        "Maligula_Complete",
    }

    win_condition_required: Dict[str, List[str]] = {}
    for col, keys in columns.items():
        seen: Set[str] = set()
        resolved: List[str] = []
        for key in keys:
            if key in skip_keys:
                continue
            display = csv_key_to_display_name.get(key, key)
            if display not in seen:
                seen.add(display)
                resolved.append(display)
        win_condition_required[col] = resolved

    # Scav-hunt items
    scav_display: List[str] = [
        csv_key_to_display_name.get(k, k) for k in SCAV_HUNT_ITEM_KEYS
    ]

    return win_condition_required, scav_display


WIN_CONDITION_REQUIRED_ITEMS: Dict[str, List[str]]
SCAV_HUNT_DISPLAY_NAMES: List[str]

WIN_CONDITION_REQUIRED_ITEMS, SCAV_HUNT_DISPLAY_NAMES = _build_win_condition_tables()


# ---------------------------------------------------------------------------
# Item factory
# ---------------------------------------------------------------------------

class Psy2Item(Item):
    """An Archipelago item belonging to Psychonauts 2."""
    game = "Psychonauts 2"
