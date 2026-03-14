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
    Maligula_Complete (victory), Maligula_Access (triggered event), and all
    13 StoryComplete keys have no numeric ID and are never placed in the
    randomised pool.  They are placed as locked event items at dedicated event
    locations.

  Starting items
    Melee - Base Power is always precollected; the player starts every seed
    with it.  It is NOT placed in the randomised pool.  Melee upgrades are.

  Starting outfit
    One of four outfits (Normal Outfit, Tried and True, Circus Skivvies, Suit)
    is precollected based on the StartingOutfit YAML option.  The remaining
    three outfits are placed in the randomised pool.

  Extra items
    Senior_League_Card gates the Motherlobe Bowling Alley but was omitted from
    the item CSV.  Normal_Outfit is the player's default look; it is added so
    all four outfits are symmetrically randomisable.  Psitanium x25/50/100 are
    filler-only items used to pad the pool.

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

MALIGULA_ACCESS_ITEM_NAME: str = "Maligula Access"
"""Display name of the Maligula Access event (triggered by win-condition logic)."""

# ---------------------------------------------------------------------------
# Event item keys and display-name overrides
# ---------------------------------------------------------------------------

# CSV item keys that become locked event items (no numeric ID, never randomised).
# StoryComplete events are placed at dedicated event locations in each mental
# world – they fire automatically when the player holds that world's access item.
# Maligula_Access is a triggered event; Maligula_Complete is the victory event.
_EVENT_ITEM_KEYS: Set[str] = {
    "Maligula_Complete",
    "Maligula_Access",
    # Mental-world story completion events (one per mental world):
    "Loboto_StoryComplete",
    "HC_StoryComplete",
    "HH_StoryComplete",
    "Compton_StoryComplete",
    "PsiKing_StoryComplete",
    "Ford_StoryComplete",
    "StrikeCity_StoryComplete",
    "Cruller_StoryComplete",
    "Tomb_StoryComplete",
    "Bob_StoryComplete",
    "Cassie_StoryComplete",
    "Lucy_StoryComplete",
    "Nick_StoryComplete",
}

# Override display names for specific event items (all others use the CSV Name).
_EVENT_ITEM_DISPLAY_NAMES: Dict[str, str] = {
    "Maligula_Complete": VICTORY_ITEM_NAME,
    "Maligula_Access":   MALIGULA_ACCESS_ITEM_NAME,
}

# ---------------------------------------------------------------------------
# Filler item keys
# ---------------------------------------------------------------------------

# CSV keys used as weighted filler when the pool needs padding.
# Psitanium currency variants (25 / 50 / 100) are added via _EXTRA_ITEM_ROWS
# with Max_Quantity "0" so they appear only as padding, never as base-pool items.
FILLER_ITEM_KEYS: List[str] = [
    "PsiCore", "PsiPop", "DreamFluff",
    "Psitanium_25", "Psitanium_50", "Psitanium_100",
]

# ---------------------------------------------------------------------------
# Toggleable-pin classification override
# ---------------------------------------------------------------------------

# These nine pins can be freely equipped and unequipped from within the game
# once the player has obtained them (handled on the UE4 mod side).  Because
# they provide an ongoing, player-controlled benefit they are classified as
# *useful* rather than *filler*, even though they do not gate any checks.
TOGGLEABLE_PIN_KEYS: frozenset[str] = frozenset({
    "GagOrder",
    "PixelPal",
    "FoodForThought",
    "MentalTax",
    "Rainblows",
    "BobbyPin",
    "MentalMagnet",
    "VIPDiscount",
    "Beastmastery",
})

# ---------------------------------------------------------------------------
# Forced-progression override
# ---------------------------------------------------------------------------

# In Archipelago, only items with ItemClassification.progression are tracked in
# prog_items (via collect_item / World.collect).  Location access rules rely on
# state.has() which queries prog_items, so any item that appears in a rule MUST
# have the progression classification – regardless of what the CSV says.
#
# The CSV uses "Important" for helpful items, but that maps to *useful* here
# (see _classification_from_csv).  Every item key that appears as a requirement
# in the check CSV therefore needs an explicit progression override so
# state.has() can recognise it.
_FORCED_PROGRESSION_KEYS: frozenset[str] = frozenset({
    # ── Hub-area access items (Normal in the CSV) ────────────────────────────
    "Motherlobe_Access",
    "Quarry_Access",
    "QA_Access",
    # ── Mental-world access items (Important → useful without override) ──────
    "GNG_Access",
    "Loboto_Access",
    "HC_Access",
    "HH_Access",
    "Compton_Access",
    "PsiKing_Access",
    "Ford_Access",
    "StrikeCity_Access",
    "Cruller_Access",
    "Tomb_Access",
    "Bob_Access",
    "Cassie_Access",
    "Lucy_Access",
    "Nick_Access",
    # ── Non-ability items used directly in check rules ───────────────────────
    "ThoughtTuner",   # Important; gates Psy Challenge Markers / some Psi Cards
    "Melee",          # Important; gates two Motherlobe checks
    "Otto-Shot",      # Junk; gates the Otto-Shop filter items
    # ── Extra item gating the Bowling Alley (added via _EXTRA_ITEM_ROWS) ─────
    "Senior_League_Card",
    # ── Scavenger-hunt collectibles (Normal in the CSV) ──────────────────────
    # Referenced by the "All_ScavHunt_Items" macro in the check CSV.
    "DayOldSushi", "EnemySurveillanceDevice", "NamePlaque", "DeckOfCards",
    "AstronautIceCream", "Laserdisc", "UnexplodedBomb", "PsitaniumKnife",
    "Human_Skull", "Novelty_Mug", "Can_of_Corn", "Switchblade_Hatchet",
    "MurderBot", "Beehive", "VikingHelmet", "Mindswarm",
})

# Extra items missing from the CSV but needed for complete rule / pool coverage.
# Max_Quantity "0" means the item is registered (gets an ID, appears as filler)
# but no copies start in the base pool – it is used only for padding.
_EXTRA_ITEM_ROWS: List[Dict[str, str]] = [
    {
        "Index":        "558",
        "Item":         "Senior_League_Card",
        "Name":         "Senior League Card",
        "Item_Type":    "Normal",   # Forced to progression via _FORCED_PROGRESSION_KEYS
        "Max_Quantity": "1",
    },
    # Psitanium currency – pure junk, used only for pool-padding filler.
    {"Index": "559", "Item": "Psitanium_25",  "Name": "Psitanium x25",  "Item_Type": "Junk", "Max_Quantity": "0"},
    {"Index": "560", "Item": "Psitanium_50",  "Name": "Psitanium x50",  "Item_Type": "Junk", "Max_Quantity": "0"},
    {"Index": "561", "Item": "Psitanium_100", "Name": "Psitanium x100", "Item_Type": "Junk", "Max_Quantity": "0"},
    # The fourth outfit (the default look the player normally starts with).
    # It is added here so all four outfits are symmetrically items in the pool
    # when the player does not choose to start with it equipped.
    {"Index": "562", "Item": "Normal_Outfit", "Name": "Normal Outfit", "Item_Type": "Normal", "Max_Quantity": "1"},
]

# ---------------------------------------------------------------------------
# Outfit items
# ---------------------------------------------------------------------------

# All four outfit CSV keys, in order matching the StartingOutfit option values:
#   0 = Normal_Outfit   (the player's default look)
#   1 = Classic_Outfit  ("Tried and True")
#   2 = Circus_Outfit   ("Circus Skivvies")
#   3 = Suit_Outfit     ("Suit")
OUTFIT_ITEM_KEYS: List[str] = [
    "Normal_Outfit",
    "Classic_Outfit",
    "Circus_Outfit",
    "Suit_Outfit",
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
    """Map an Item_Type string from the CSV to an Archipelago classification.

    "Important" maps to *useful* (helpful but not logically required to win).
    Only items explicitly listed in the active win condition, plus items in
    _FORCED_PROGRESSION_KEYS, receive the *progression* classification.
    """
    if item_type == "Junk":
        return ItemClassification.filler
    # Both "Normal" and "Important" map to useful; progression is applied
    # later via _FORCED_PROGRESSION_KEYS or win-condition promotion.
    return ItemClassification.useful


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
    Dict[str, Optional[int]],          # item_name_to_id
    Dict[str, ItemClassification],     # item_classifications
    List[str],                         # filler_item_names
    List[Tuple[str, ItemClassification]],  # base_item_pool entries
    Dict[str, str],                    # csv_key_to_display_name
    Set[str],                          # shop_item_display_names
]:
    """
    Parse the item CSV and build the primary data structures.

    Returns
    -------
    item_name_to_id
        {display_name: integer_id}.  Event items map to None.
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
    shop_item_display_names
        Set of display names whose Normal_Location is "Shop" in the item CSV.
        Used by __init__.py to filter items out of the pool when
        IncludeShopItems is disabled.
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
    shop_item_display_names: Set[str] = set()

    for row in rows:
        key: str = row["Item"]

        # ── Event items: register name mapping but skip pool placement ────────
        # StoryComplete items and Maligula_Access are placed as locked events
        # at dedicated event locations; Maligula_Complete is the victory event.
        if key in _EVENT_ITEM_KEYS:
            display_name = _EVENT_ITEM_DISPLAY_NAMES.get(key, row["Name"])
            csv_key_to_display[key] = display_name
            if display_name not in item_name_to_id:
                item_name_to_id[display_name] = None  # Events have no numeric ID
            continue

        # ── Determine display name ───────────────────────────────────────────
        if key in ALL_PROGRESSIVE_GROUPS:
            display_name = ALL_PROGRESSIVE_GROUPS[key]
            # All progressive copies share one display name and one ID.
            # They are always progression so the player levels up through them.
            classification = ItemClassification.progression
        else:
            base_name = row["Name"]
            # Disambiguate items that share a display name in the CSV
            if name_frequency[base_name] > 1:
                suffix = _item_type_suffix_from_key(key)
                display_name = f"{base_name} ({suffix})"
            else:
                display_name = base_name
            # Items used in access rules must be progression so state.has()
            # can track them, regardless of their CSV type.
            if key in _FORCED_PROGRESSION_KEYS:
                classification = ItemClassification.progression
            elif key in TOGGLEABLE_PIN_KEYS:
                # Toggleable pins can be freely equipped/unequipped in-game;
                # they are beneficial but never required for progression.
                classification = ItemClassification.useful
            else:
                classification = _classification_from_csv(row["Item_Type"])

        csv_key_to_display[key] = display_name

        # ── Track shop-origin items for optional filtering ───────────────────
        if row.get("Normal_Location") == "Shop":
            shop_item_display_names.add(display_name)

        # ── Determine ID (progressive groups share the first item's index) ───
        if display_name not in item_name_to_id:
            item_id = ITEM_ID_BASE + int(row["Index"])
            item_name_to_id[display_name] = item_id
            item_classifications[display_name] = classification

        # ── Determine how many copies go into the pool ───────────────────────
        qty_str = row.get("Max_Quantity", "")
        # Use explicit "0" to mean zero copies (pool-padding-only items like
        # Psitanium).  Empty / NULL defaults to 1 (singleton).
        if qty_str not in ("", "NULL", None):
            qty = int(qty_str)
        else:
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
        shop_item_display_names,
    )


# Build all tables once at import time.
(
    item_name_to_id,
    item_classifications,
    filler_item_names,
    base_item_pool,
    csv_key_to_display_name,
    SHOP_ITEM_DISPLAY_NAMES,
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

    # Event keys that are handled by the victory rule, not as collectible items.
    # Maligula_Access is a triggered event; the fight and its completion are
    # implicit in the win condition once the player has all required items.
    # Both old ("_Fight_") and corrected names are listed for safety.
    skip_keys: Set[str] = {
        "Maligula_Access",         # correct name – triggered event, not a pool item
        "Maligula_Complete",       # correct name – victory event
        "Maligula_Fight_Access",   # old incorrect name (kept for compatibility)
        "Maligula_Fight_Complete", # old incorrect name (kept for compatibility)
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
