"""
Psychonauts 2 Archipelago - Location Definitions

All check locations are loaded from the CSV data file.  Each row becomes one
Archipelago location except for the Maligula fight check, which is handled as
an event location (Victory) in __init__.py.

Location ID base: 7_802_462
"""

import csv
import os
from typing import Dict, List, Optional, Set, Tuple
from BaseClasses import Location, Region

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOCATION_ID_BASE: int = 7_802_462
"""Starting numeric ID for all Psychonauts 2 location IDs."""

_DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")

# This check is handled as the victory event; it receives no randomised item.
VICTORY_LOCATION_KEY: str = "Maligula_check"
VICTORY_LOCATION_NAME: str = "Interact with Astralathe for Maligula fight"

# ---------------------------------------------------------------------------
# Region / area definitions
# ---------------------------------------------------------------------------

# Maps the Location column in the check CSV to the corresponding Archipelago
# region name.  "Global" checks (rank points, ability unlocks) live in a region
# that requires no area-access item to enter.
AREA_TO_REGION: Dict[str, str] = {
    "Motherlobe":               "Motherlobe",
    "Quarry":                   "Quarry",
    "Questionable Area":        "Questionable Area",
    "Green Needle Gulch":       "Green Needle Gulch",
    "Shop":                     "Shop",
    "Loboto's Labrynth":        "Loboto's Labrynth",
    "Hollis' Classroom":        "Hollis' Classroom",
    "Hollis' Hot Streak":       "Hollis' Hot Streak",
    "Compton's Cookoff":        "Compton's Cookoff",
    "Psi King's Sensorium":     "Psi King's Sensorium",
    "Ford's Follicles":         "Ford's Follicles",
    "Strike City":              "Strike City",
    "Cruller's Correspondence": "Cruller's Correspondence",
    "Tomb of the Sharkophagus": "Tomb of the Sharkophagus",
    "Bob's Bottles":            "Bob's Bottles",
    "Cassie's Collection":      "Cassie's Collection",
    "Lucrecia's Lament":        "Lucrecia's Lament",
    "Fatherland Follies":       "Fatherland Follies",
    "Global":                   "Global",
}

# The item key that grants entry to each region (used when building region
# connections in __init__.py).  None means always accessible.
REGION_ACCESS_ITEM: Dict[str, Optional[str]] = {
    "Motherlobe":               "Motherlobe_Access",
    "Quarry":                   "Quarry_Access",
    "Questionable Area":        "QA_Access",
    "Green Needle Gulch":       "GNG_Access",
    "Shop":                     "Motherlobe_Access",
    "Loboto's Labrynth":        "Loboto_Access",
    "Hollis' Classroom":        "HC_Access",
    "Hollis' Hot Streak":       "HH_Access",
    "Compton's Cookoff":        "Compton_Access",
    "Psi King's Sensorium":     "PsiKing_Access",
    "Ford's Follicles":         "Ford_Access",
    "Strike City":              "StrikeCity_Access",
    "Cruller's Correspondence": "Cruller_Access",
    "Tomb of the Sharkophagus": "Tomb_Access",
    "Bob's Bottles":            "Bob_Access",
    "Cassie's Collection":      "Cassie_Access",
    "Lucrecia's Lament":        "Lucy_Access",
    "Fatherland Follies":       "Nick_Access",
    "Global":                   None,
}

# ---------------------------------------------------------------------------
# Location data
# ---------------------------------------------------------------------------

class Psy2Location(Location):
    """An Archipelago location belonging to Psychonauts 2."""
    game = "Psychonauts 2"


class LocationData:
    """Lightweight record holding the static data for one check location."""

    __slots__ = ("location_id", "name", "region", "check_key", "requirements")

    def __init__(
        self,
        location_id: Optional[int],
        name: str,
        region: str,
        check_key: str,
        requirements: str,
    ) -> None:
        self.location_id: Optional[int] = location_id
        self.name: str = name
        self.region: str = region
        self.check_key: str = check_key
        # Raw Item_Required string from the CSV; parsed later by rules.py.
        self.requirements: str = requirements


def _type_suffix_from_check_key(check_key: str) -> str:
    """
    Derive a short, human-readable type label from a check key.

    Used to disambiguate location names that appear multiple times in the CSV
    (e.g. the same physical location having both a Psi Card and a Supply Chest).
    """
    key_lower = check_key.lower()
    # Figment-percentage milestones encode the percentage in the key
    for pct in ("20", "40", "60", "80", "100"):
        if f"_{pct}percent" in key_lower:
            return f"{pct}% Figments"
    # Ordered from most specific to most general so the right label is chosen
    type_map = [
        ("psychallengeMarkers", "Psy Challenge Marker"),
        ("psychallengemarkers", "Psy Challenge Marker"),
        ("psicard",             "Psi Card"),
        ("supplychests",        "Supply Chest"),
        ("supplykey",           "Supply Key"),
        ("nugget",              "Nugget of Wisdom"),
        ("ham",                 "Half-a-Mind"),
        ("memoryvault",         "Memory Vault"),
        ("dufflebag_tag",       "Dufflebag Tag"),
        ("dufflebag",           "Dufflebag"),
        ("steamertrunk_tag",    "Steamer Trunk Tag"),
        ("steamertrunk",        "Steamer Trunk"),
        ("suitcase_tag",        "Suitcase Tag"),
        ("suitcase",            "Suitcase"),
        ("hatbox_tag",          "Hatbox Tag"),
        ("hatbox",              "Hatbox"),
    ]
    for fragment, label in type_map:
        if fragment in key_lower:
            return label
    return check_key  # Fallback: use the raw key


def _load_location_data() -> Tuple[
    Dict[str, LocationData],  # check_key → LocationData
    Dict[str, int],           # location_name → location_id
]:
    """
    Parse the check CSV and return all location records.

    Location display names are guaranteed to be unique.  When the CSV contains
    duplicate Name values the type of check is appended in parentheses, e.g.
    "Bowling Alley (Supply Chest)" and "Bowling Alley (Psy Challenge Marker)".
    """
    path = os.path.join(_DATA_DIR, "Psychonauts_2_Check_List.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    # First pass: count how many times each base Name appears
    from collections import Counter
    name_frequency: Dict[str, int] = Counter(row["Name"] for row in rows)

    by_key: Dict[str, LocationData] = {}
    name_to_id: Dict[str, int] = {}

    for row in rows:
        check_key: str = row["Check"]
        base_name: str = row["Name"]
        area: str = row["Location"]
        region: str = AREA_TO_REGION.get(area, "Global")
        requirements: str = row["Item_Required"].strip()
        index: int = int(row["Index"])

        # Make the display name unique when the base name is shared
        if name_frequency[base_name] > 1:
            suffix = _type_suffix_from_check_key(check_key)
            display_name = f"{base_name} ({suffix})"
        else:
            display_name = base_name

        if check_key == VICTORY_LOCATION_KEY:
            # Victory event – no randomised ID
            loc_id: Optional[int] = None
        else:
            loc_id = LOCATION_ID_BASE + index
            name_to_id[display_name] = loc_id

        by_key[check_key] = LocationData(
            location_id=loc_id,
            name=display_name,
            region=region,
            check_key=check_key,
            requirements=requirements,
        )

    return by_key, name_to_id


# Built once at import time
location_data_by_key: Dict[str, LocationData]
location_name_to_id: Dict[str, int]

location_data_by_key, location_name_to_id = _load_location_data()

# Convenience list of all non-event LocationData objects (used for pool sizing)
all_randomised_locations: List[LocationData] = [
    loc for loc in location_data_by_key.values() if loc.location_id is not None
]

# The single event location
victory_location: LocationData = location_data_by_key[VICTORY_LOCATION_KEY]
