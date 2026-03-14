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
    MALIGULA_ACCESS_ITEM_NAME,
    OUTFIT_ITEM_KEYS,
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
    STORY_COMPLETE_EVENTS,
)
from .options import Psy2Options, WinCondition, StartingOutfit
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
          1. Determine which outfit the player starts with (from options) and
             which outfit display name to exclude from the pool.
          2. Exclude Melee - Base Power from the pool (it is always precollected).
          3. Start with the base pool from the CSV (respecting Max_Quantity),
             skipping the chosen starting outfit and Melee base.
          4. Promote items required by the chosen win condition to Required
             (ItemClassification.progression).
          5. Pad or trim the pool to exactly match the number of randomised
             locations, using weighted junk filler.

        Both the starting outfit and Melee are pushed as precollected items so
        that access rules referencing them are satisfied from the start.
        """
        # Determine which outfit CSV key the player is starting with.
        starting_outfit_idx = self.options.starting_outfit.value
        starting_outfit_key = OUTFIT_ITEM_KEYS[starting_outfit_idx]
        starting_outfit_display = csv_key_to_display_name.get(
            starting_outfit_key, starting_outfit_key
        )

        # Display name for Melee base (always precollected).
        melee_display = csv_key_to_display_name.get("Melee", "Melee - Base Power")

        # Names of items to precollect instead of placing in the pool.
        precollected_displays = {starting_outfit_display, melee_display}

        required_names = set(self._get_required_item_names())
        target_count = len(all_randomised_locations)

        items: List[Psy2Item] = []
        for display_name, default_classification in base_item_pool:
            # Items precollected as start inventory are not placed in the pool.
            if display_name in precollected_displays:
                continue
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

        # Precollect the starting outfit and Melee so they are in the player's
        # inventory from the first moment of the seed.
        for display_name in precollected_displays:
            precollected_item = self._create_item_with_classification(
                display_name,
                item_classifications.get(display_name, ItemClassification.filler),
            )
            self.multiworld.push_precollected(precollected_item)

    def get_filler_item_name(self) -> str:
        """Return a random junk item name for pool padding.

        Weights are proportional to each item's desirability as filler.
        Psitanium currency variants (25/50/100) are included alongside the
        existing consumable junk items (PsiCore, PsiPop, DreamFluff).
        """
        # filler_item_names order: PsiCore, PsiPop, DreamFluff,
        #                          Psitanium x25, Psitanium x50, Psitanium x100
        weights = [11, 8, 3, 8, 5, 3]
        # Guard against the list being shorter than expected (e.g. in tests)
        w = weights[: len(filler_item_names)]
        return self.random.choices(filler_item_names, weights=w, k=1)[0]

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

        # Create StoryComplete event locations in the Global region.
        # Each fires when the player holds the corresponding mental-world access
        # item, making the locked StoryComplete event item available for rules.
        global_region = created_regions["Global"]
        for item_key, event_loc_name, access_key in STORY_COMPLETE_EVENTS:
            event_loc = Psy2Location(self.player, event_loc_name, None, global_region)
            access_display = csv_key_to_display_name.get(access_key, access_key)
            event_loc.access_rule = (
                lambda state, n=access_display, p=self.player: state.has(n, p)
            )
            global_region.locations.append(event_loc)

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
        Place all event items and configure the win condition.

        Events placed:
          - Maligula Complete  → victory location (Green Needle Gulch)
          - {World} Complete   → 13 StoryComplete event locations (Global region)
        """
        # ── Victory event ────────────────────────────────────────────────────
        victory_item = Psy2Item(
            VICTORY_ITEM_NAME,
            ItemClassification.progression,
            None,   # Events have no numeric ID
            self.player,
        )
        victory_loc = self.multiworld.get_location(victory_location.name, self.player)
        victory_loc.place_locked_item(victory_item)

        # ── StoryComplete events ─────────────────────────────────────────────
        # Each mental world's completion fires an event so that rules requiring
        # e.g. "Loboto_StoryComplete" can be satisfied via state.has().
        for item_key, event_loc_name, _access_key in STORY_COMPLETE_EVENTS:
            display_name = csv_key_to_display_name.get(item_key, item_key)
            event_item = Psy2Item(
                display_name,
                ItemClassification.progression,
                None,
                self.player,
            )
            event_loc = self.multiworld.get_location(event_loc_name, self.player)
            event_loc.place_locked_item(event_item)

        # ── Win condition ─────────────────────────────────────────────────────
        # The seed is beaten when the player collects the victory event item.
        self.multiworld.completion_condition[self.player] = lambda state: state.has(
            VICTORY_ITEM_NAME, self.player
        )

    # ---------------------------------------------------------------------------
    # Slot data (sent to the game client)
    # ---------------------------------------------------------------------------

    def fill_slot_data(self) -> Dict[str, Any]:
        """
        Return data that the Psychonauts 2 AP mod client will use at runtime.

        win_condition    – integer value of the chosen WinCondition option
        required_items   – list of item display names that must be obtained
        starting_outfit  – display name of the outfit the player starts with
        death_link       – whether death-link is enabled
        """
        col = _WIN_COND_TO_COL.get(
            self.options.win_condition.value, "WinCondition_Normal"
        )
        starting_outfit_key = OUTFIT_ITEM_KEYS[self.options.starting_outfit.value]
        starting_outfit_display = csv_key_to_display_name.get(
            starting_outfit_key, starting_outfit_key
        )
        return {
            "win_condition": self.options.win_condition.value,
            "required_items": WIN_CONDITION_REQUIRED_ITEMS.get(col, []),
            "starting_outfit": starting_outfit_display,
            "death_link": bool(self.options.death_link.value),
        }
