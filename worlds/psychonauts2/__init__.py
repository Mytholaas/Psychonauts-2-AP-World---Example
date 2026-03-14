"""
Psychonauts 2 Archipelago World

This module implements the Archipelago randomiser for Psychonauts 2.

Game overview
    Psychonauts 2 is a 3D platformer published by Double Fine in 2021.  Raz
    returns as a Psychonaut intern and must explore a series of surreal mental
    worlds to uncover a conspiracy within the agency.

Randomiser overview
    Checks
        The 607 randomised check locations cover Psi Cards, Supply Chests,
        Supply Keys, Psy Challenge Markers, outfit items, scavenger-hunt
        collectibles, figment milestones, Memory Vaults, Nuggets of Wisdom,
        Half-a-Minds, Dufflebags, Steamer Trunks, shop items, rank-up rewards,
        psychic-ability unlocks, and mental-world story completions.

    Items
        Items include psychic abilities (as progressive bundles), inventory
        upgrades (progressive), area-access passes, mental-world access items,
        story-completion tokens, scavenger-hunt collectibles, rank-point tokens,
        costume pieces, and junk consumables.

    Progressive abilities
        Each of the eight psychic abilities (Telekinesis, Psi Blast,
        Pyrokinesis, Levitation, Clairvoyance, Mental Connection, Time Bubble,
        Projection) is split into four progressive copies.  Finding any copy
        always grants the *next* upgrade tier.

    Progressive equipment
        Mind's Eyelets / Expandolier, Fluff Pockets / Jumbo Fluff Pouch, and
        Psifold Wallet / Astral Wallet each become two progressive copies.

    Win conditions
        Four win conditions are available (see options.py).  The chosen
        condition determines which items are classified as Required (progression)
        and what the player must accomplish to win.

    Victory
        The victory event is the "Interact with Astralathe for Maligula fight"
        location in Green Needle Gulch.  Reaching it (and defeating Maligula)
        satisfies the win condition.

Mod compatibility
    This world is designed for use with the Psychonauts 2 Archipelago mod.
    The mod runs on Unreal Engine 4 and makes the following changes relevant
    to game logic:
      - Mental Connection is not required in the Collective Unconscious.
      - Players always start with at least one mental world and one hub area
        unlocked (they spawn in the Collective Unconscious).
      - Smelling Salts can be used to exit any mental world or the Collective
        Unconscious, routing the player to an available hub area.
"""

import os
from typing import Any, ClassVar, Dict, List, Optional, TYPE_CHECKING

from BaseClasses import Tutorial, ItemClassification, Region, Entrance
from worlds.AutoWorld import World, WebWorld
from worlds.generic.Rules import set_rule

from .items import (
    Psy2Item,
    item_name_to_id,
    item_classifications,
    filler_item_names,
    base_item_pool,
    csv_key_to_display_name,
    WIN_CONDITION_REQUIRED_ITEMS,
    VICTORY_ITEM_NAME,
)
from .locations import (
    Psy2Location,
    location_name_to_id,
    location_data_by_key,
    all_randomised_locations,
    victory_location,
    AREA_TO_REGION,
    REGION_ACCESS_ITEM,
    LocationData,
)
from .options import Psy2Options, WinCondition
from .rules import set_rules

if TYPE_CHECKING:
    from BaseClasses import CollectionState, MultiWorld


# ---------------------------------------------------------------------------
# WebWorld (metadata shown on the Archipelago website)
# ---------------------------------------------------------------------------

class Psy2WebWorld(WebWorld):
    theme = "grass"
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to setting up the Psychonauts 2 Archipelago randomiser "
            "and the companion Unreal Engine 4 mod.",
            "English",
            "setup_en.md",
            "setup/en",
            ["Psychonauts 2 AP Community"],
        )
    ]


# ---------------------------------------------------------------------------
# Win-condition → CSV column mapping
# ---------------------------------------------------------------------------

_WIN_COND_TO_COL: Dict[int, str] = {
    WinCondition.option_normal:                 "WinCondition_Normal",
    WinCondition.option_all_bosses:             "WinCondition_AllBosses",
    WinCondition.option_all_scav_hunt:          "WinCondition_AllScavHunt",
    WinCondition.option_scav_hunt_and_maligula: "WinCondition_ScavHunt_and_Maligula",
}


# ---------------------------------------------------------------------------
# Main World class
# ---------------------------------------------------------------------------

class Psy2World(World):
    """
    Psychonauts 2 randomiser.

    Locations: 607 randomised checks + 1 victory event (Maligula fight).
    Items:     A pool matching the number of randomised locations, built from
               the item CSV with progressive replacements and filler padding.
    """

    game = "Psychonauts 2"
    web = Psy2WebWorld()

    options_dataclass = Psy2Options
    options: Psy2Options

    item_name_to_id: ClassVar[Dict[str, int]] = {
        k: v for k, v in item_name_to_id.items() if v is not None
    }
    location_name_to_id: ClassVar[Dict[str, int]] = location_name_to_id

    # Expose location data to the rules module via an instance attribute.
    all_location_data: List[LocationData]

    # ---------------------------------------------------------------------------
    # Item creation
    # ---------------------------------------------------------------------------

    def _get_required_item_names(self) -> List[str]:
        """
        Return the list of item display names that become Required
        (progression) for the chosen win condition.
        """
        col = _WIN_COND_TO_COL.get(self.options.win_condition.value, "WinCondition_Normal")
        return WIN_CONDITION_REQUIRED_ITEMS.get(col, [])

    def create_item(self, name: str) -> Psy2Item:
        """Create a single Psy2Item by display name."""
        classification = item_classifications.get(name, ItemClassification.filler)
        return Psy2Item(name, classification, item_name_to_id.get(name), self.player)

    def _create_item_with_classification(
        self, name: str, classification: ItemClassification
    ) -> Psy2Item:
        """Create a Psy2Item with an overridden classification (e.g., Required)."""
        return Psy2Item(name, classification, item_name_to_id.get(name), self.player)

    def create_items(self) -> None:
        """
        Build the item pool for this player's world.

        Steps:
          1. Start with the base pool from the CSV (respecting Max_Quantity).
          2. Promote items required by the chosen win condition to Required
             (ItemClassification.progression).
          3. Pad or trim the pool to exactly match the number of randomised
             locations, using weighted junk filler.
        """
        required_names = set(self._get_required_item_names())
        target_count = len(all_randomised_locations)

        items: List[Psy2Item] = []
        for display_name, default_classification in base_item_pool:
            if display_name in required_names:
                classification = ItemClassification.progression
            else:
                classification = default_classification
            items.append(
                Psy2Item(
                    display_name,
                    classification,
                    item_name_to_id.get(display_name),
                    self.player,
                )
            )

        # Pad the pool with weighted filler until it matches location count.
        while len(items) < target_count:
            filler_name = self.get_filler_item_name()
            items.append(self.create_item(filler_name))

        # If there are somehow more items than locations, trim the excess.
        # (This should not normally happen with the current CSV data.)
        if len(items) > target_count:
            items = items[:target_count]

        for item in items:
            self.multiworld.itempool.append(item)

    def get_filler_item_name(self) -> str:
        """Return a random junk item name for pool padding."""
        # Weighted selection: PsiCore appears most often since it has the
        # highest Max_Quantity in the CSV (11), followed by PsiPop (8) and
        # DreamFluff (3).
        weights = [11, 8, 3]
        return self.random.choices(filler_item_names, weights=weights, k=1)[0]

    # ---------------------------------------------------------------------------
    # Region and location creation
    # ---------------------------------------------------------------------------

    def create_regions(self) -> None:
        """
        Create one Archipelago Region per game area and connect them to Menu.

        Hub regions (Motherlobe, Quarry, Questionable Area, Green Needle Gulch)
        and mental-world regions all require their respective access items to
        enter.  The Global region (rank points, ability checks) requires no
        access item.

        All 607 randomised check locations and the single victory event
        location are created and assigned to their regions.
        """
        # Build the set of all region names present in the data
        region_names = set(AREA_TO_REGION.values())

        # Create all regions (including Menu as the starting point)
        created_regions: Dict[str, Region] = {}
        menu_region = Region("Menu", self.player, self.multiworld)
        created_regions["Menu"] = menu_region
        self.multiworld.regions.append(menu_region)

        for rname in region_names:
            region = Region(rname, self.player, self.multiworld)
            created_regions[rname] = region
            self.multiworld.regions.append(region)

        # Connect Menu → each area region with the appropriate access rule.
        for region_name, access_key in REGION_ACCESS_ITEM.items():
            target = created_regions.get(region_name)
            if target is None:
                continue
            entrance = Entrance(self.player, f"To {region_name}", menu_region)
            menu_region.exits.append(entrance)
            entrance.connect(target)

            if access_key is not None:
                # The display name for the access item
                access_display = csv_key_to_display_name.get(access_key, access_key)
                entrance.access_rule = (
                    lambda state, name=access_display, p=self.player: state.has(name, p)
                )

        # Populate locations in each region.
        self.all_location_data = []
        for loc_data in all_randomised_locations:
            region = created_regions.get(loc_data.region, created_regions["Global"])
            location = Psy2Location(
                self.player,
                loc_data.name,
                loc_data.location_id,
                region,
            )
            region.locations.append(location)
            self.all_location_data.append(loc_data)

        # Create the victory event location in Green Needle Gulch (or Global
        # as fallback if GNG region does not exist).
        gng_region = created_regions.get("Green Needle Gulch", created_regions["Global"])
        victory_loc = Psy2Location(
            self.player,
            victory_location.name,
            None,  # Event: no numeric ID
            gng_region,
        )
        gng_region.locations.append(victory_loc)

    # ---------------------------------------------------------------------------
    # Rules
    # ---------------------------------------------------------------------------

    def set_rules(self) -> None:
        """Apply all location access rules and the victory condition rule."""
        set_rules(self)

    def generate_basic(self) -> None:
        """
        Place the Victory event item at the Maligula fight location and
        configure the goal condition.
        """
        # Create and place the victory event.
        victory_item = Psy2Item(
            VICTORY_ITEM_NAME,
            ItemClassification.progression,
            None,   # Events have no numeric ID
            self.player,
        )
        victory_loc = self.multiworld.get_location(victory_location.name, self.player)
        victory_loc.place_locked_item(victory_item)

        # The win condition is satisfied when the player has collected the
        # victory event item.
        self.multiworld.completion_condition[self.player] = lambda state: state.has(
            VICTORY_ITEM_NAME, self.player
        )

    # ---------------------------------------------------------------------------
    # Slot data (sent to the game client)
    # ---------------------------------------------------------------------------

    def fill_slot_data(self) -> Dict[str, Any]:
        """
        Return data that the Psychonauts 2 AP mod client will use at runtime.

        win_condition   – integer value of the chosen WinCondition option
        required_items  – list of item display names that must be obtained
        death_link      – whether death-link is enabled
        """
        col = _WIN_COND_TO_COL.get(
            self.options.win_condition.value, "WinCondition_Normal"
        )
        return {
            "win_condition": self.options.win_condition.value,
            "required_items": WIN_CONDITION_REQUIRED_ITEMS.get(col, []),
            "death_link": bool(self.options.death_link.value),
        }
