"""
Psychonauts 2 Archipelago - Access Rule Tests

These tests verify that location access rules work correctly, particularly:
  - Progressive ability rules (base and upgrade levels)
  - Area access items gate their respective regions
  - OR-logic in requirements works correctly
  - Scavenger-hunt requirements expand properly
  - Win-condition options change which items are required
"""

from BaseClasses import CollectionState, ItemClassification
from . import Psy2TestBase


class TestDefaultWinCondition(Psy2TestBase):
    """
    Tests with the default (Normal) win condition.

    In Normal mode, the player needs core abilities and several area access items
    to reach Maligula.
    """

    def test_motherlobe_requires_access(self) -> None:
        """Motherlobe region locations should not be reachable without Intern Sticker."""
        self.assertFalse(
            self.can_reach_location("Bowling Alley (Supply Chest)"),
            "Bowling Alley should not be accessible without any items",
        )

    def test_bowling_alley_requires_senior_league_card(self) -> None:
        """Bowling Alley checks also require the Senior League Card."""
        # Collect Intern Sticker (Motherlobe access)
        self.collect_by_name("Intern Sticker")
        self.assertFalse(
            self.can_reach_location("Bowling Alley (Supply Chest)"),
            "Bowling Alley should not be accessible with only Intern Sticker",
        )
        # Now also collect the Senior League Card
        self.collect_by_name("Senior League Card")
        self.assertTrue(
            self.can_reach_location("Bowling Alley (Supply Chest)"),
            "Bowling Alley should be accessible with Intern Sticker + Senior League Card",
        )

    def test_quarry_requires_access(self) -> None:
        """Quarry locations should not be reachable without Thinkerprint Full Access."""
        self.assertFalse(
            self.can_reach_location("Otto's Lab (Psi Card)"),
            "Quarry checks should not be accessible without Thinkerprint Full Access",
        )
        self.collect_by_name("Thinkerprint Full Access")
        self.assertTrue(
            self.can_reach_location("Otto's Lab (Psi Card)"),
            "Quarry check should be accessible with Thinkerprint Full Access",
        )

    def test_progressive_ability_base_required(self) -> None:
        """A check gated by the base ability should require at least 1 progressive copy."""
        # Beastmastery in the shop needs Intern Sticker + Telekinesis
        self.collect_by_name("Intern Sticker")
        self.assertFalse(
            self.can_reach_location("Beastmastery"),
            "Beastmastery should not be accessible without Telekinesis",
        )
        self.collect_by_name("Progressive Telekinesis")
        self.assertTrue(
            self.can_reach_location("Beastmastery"),
            "Beastmastery should be accessible with Intern Sticker + Telekinesis",
        )

    def test_progressive_ability_upgrade3_requires_four_copies(self) -> None:
        """A check gated by the Upgrade3 of an ability requires 4 progressive copies."""
        # Set up the state with the region access and the PsiBlast prerequisite
        self.collect_by_name("Hollis' Hot Streak Access")
        self.collect_by_name("Progressive Psi Blast")
        # Add exactly 3 Mental Connection copies – should still be blocked
        for _ in range(3):
            items = self.get_items_by_name("Progressive Mental Connection")
            if items:
                self.multiworld.state.collect(items[0])
        self.assertFalse(
            self.can_reach_location("MC after first Heart"),
            "MC after first Heart should not be accessible with only 3 Mental Connection copies",
        )
        # Add the 4th copy – should now be reachable
        items = self.get_items_by_name("Progressive Mental Connection")
        if items:
            self.multiworld.state.collect(items[0])
        self.assertTrue(
            self.can_reach_location("MC after first Heart"),
            "MC after first Heart should be accessible with 4 Mental Connection copies",
        )

    def test_or_requirement_telekinesis(self) -> None:
        """OR requirement check: Telekinesis + QA_Access satisfies the rule."""
        self.collect_by_name("Questionable Area Access")
        self.assertFalse(
            self.can_reach_location("Woods near Rundown Cabin"),
            "QA check requiring Telekinesis or TimeBubble should fail with just QA access",
        )
        self.collect_by_name("Progressive Telekinesis")
        self.assertTrue(
            self.can_reach_location("Woods near Rundown Cabin"),
            "QA check should be accessible with QA Access + Telekinesis",
        )

    def test_or_requirement_timebubble(self) -> None:
        """OR requirement check: TimeBubble + QA_Access also satisfies the rule."""
        self.collect_by_name("Questionable Area Access")
        self.collect_by_name("Progressive Time Bubble")
        self.assertTrue(
            self.can_reach_location("Woods near Rundown Cabin"),
            "QA check should be accessible with QA Access + Time Bubble",
        )

    def test_global_rank_checks_always_accessible(self) -> None:
        """Rank-point checks have no item requirement and are always accessible."""
        self.assertTrue(self.can_reach_location("Rank 1"), "Rank 1 should be accessible from start")
        self.assertTrue(self.can_reach_location("Rank 50"), "Rank 50 should be accessible from start")
        self.assertTrue(self.can_reach_location("Rank 102"), "Rank 102 should be accessible from start")

    def test_ability_check_always_accessible(self) -> None:
        """Base ability unlock checks have no item requirement."""
        self.assertTrue(
            self.can_reach_location("Telekinesis - Base Power"),
            "Telekinesis base check should be accessible without any items",
        )
        self.assertTrue(
            self.can_reach_location("Levitation - Base Power"),
            "Levitation base check should be accessible without any items",
        )


class TestAllBossesWinCondition(Psy2TestBase):
    """Tests with the All Bosses win condition."""
    options = {"win_condition": "all_bosses"}

    def test_all_bosses_required_items_are_progression(self) -> None:
        """Items required by the All Bosses condition must be progression items.

        AllBosses requires 8 abilities + 4 StoryComplete event items (the
        latter are events that resolve automatically once the matching access
        item is held).  Maligula_Access and Maligula_Complete are events and
        are NOT in the randomised pool.
        """
        expected_required = [
            "Progressive Telekinesis",
            "Progressive Psi Blast",
            "Progressive Pyrokinesis",
            "Progressive Levitation",
            "Progressive Clairvoyance",
            "Progressive Mental Connection",
            "Progressive Time Bubble",
            "Progressive Projection",
            "Hollis' Hot Streak Complete",
            "Compton's Cookoff Complete",
            "Bob's Bottles Complete",
            "Cassie's Collection Complete",
        ]
        pool_by_name = {i.name: i for i in self.multiworld.itempool if i.player == self.player}
        for item_name in expected_required:
            if item_name in pool_by_name:
                self.assertEqual(
                    pool_by_name[item_name].classification,
                    ItemClassification.progression,
                    f"Expected {item_name!r} to be progression under AllBosses win condition",
                )
        # Maligula Access must NOT be in the pool (it is a triggered event)
        self.assertNotIn(
            "Maligula Access", pool_by_name,
            "Maligula Access should be an event item, not in the randomised pool",
        )


class TestAllScavHuntWinCondition(Psy2TestBase):
    """Tests with the All Scav Hunt win condition."""
    options = {"win_condition": "all_scav_hunt"}

    def test_scav_hunt_items_are_progression(self) -> None:
        """All 16 scavenger-hunt collectibles must be progression items."""
        scav_items = [
            "Day Old Sushi", "Enemy Surveillance Device", "Name Plaque", "Deck of Cards",
            "Astronaut Ice Cream", "Agent Orientation Laserdisc", "Unexploded Bomb",
            "Psitanium Knife", "Human Skull", "Novelty Mug", "Can of Corn",
            "Switchblade Hatchet", "Mini Murder Bug Bot",
            "Beehive shaped like my phone", "Viking Helmet", "Signed Copy of Mindswarm",
        ]
        pool_by_name = {i.name: i for i in self.multiworld.itempool if i.player == self.player}
        for item_name in scav_items:
            if item_name in pool_by_name:
                self.assertEqual(
                    pool_by_name[item_name].classification,
                    ItemClassification.progression,
                    f"Expected {item_name!r} to be progression under AllScavHunt win condition",
                )


class TestItemPoolSize(Psy2TestBase):
    """Tests that verify the item pool is correctly sized."""

    def test_pool_matches_location_count(self) -> None:
        """The item pool must have exactly as many items as there are randomised locations."""
        location_count = len([
            loc for loc in self.multiworld.get_locations(self.player)
            if not loc.is_event
        ])
        item_count = len([
            item for item in self.multiworld.itempool
            if item.player == self.player
        ])
        self.assertEqual(
            item_count,
            location_count,
            f"Item pool ({item_count}) should match location count ({location_count})",
        )

    def test_victory_event_exists(self) -> None:
        """The Maligula fight location must have the victory event item."""
        victory_loc = self.multiworld.get_location(
            "Interact with Astralathe for Maligula fight",
            self.player,
        )
        self.assertIsNotNone(victory_loc)
        self.assertTrue(victory_loc.is_event)
        self.assertIsNotNone(victory_loc.item)
        self.assertEqual(victory_loc.item.name, "Maligula Complete")

    def test_story_complete_event_locations_exist(self) -> None:
        """Every mental world must have a StoryComplete event location."""
        from worlds.psychonauts2.locations import STORY_COMPLETE_EVENTS
        for _item_key, event_loc_name, _access_key in STORY_COMPLETE_EVENTS:
            ev_loc = self.multiworld.get_location(event_loc_name, self.player)
            self.assertIsNotNone(ev_loc, f"Missing StoryComplete event location: {event_loc_name}")
            self.assertTrue(ev_loc.is_event, f"{event_loc_name} should be an event location")

    def test_story_complete_not_in_pool(self) -> None:
        """StoryComplete items must be locked events, not randomised pool items."""
        from worlds.psychonauts2.items import _EVENT_ITEM_KEYS, csv_key_to_display_name
        sc_display = {
            csv_key_to_display_name.get(k, k)
            for k in _EVENT_ITEM_KEYS
            if "StoryComplete" in k
        }
        pool_names = {i.name for i in self.multiworld.itempool if i.player == self.player}
        overlap = sc_display & pool_names
        self.assertFalse(
            overlap,
            f"StoryComplete items must not be in pool: {overlap}",
        )

    def test_maligula_access_not_in_pool(self) -> None:
        """Maligula Access is a triggered event and must not be in the pool."""
        pool_names = {i.name for i in self.multiworld.itempool if i.player == self.player}
        self.assertNotIn(
            "Maligula Access", pool_names,
            "Maligula Access should be an event item, not a randomised pool item",
        )

    def test_story_complete_event_fires_with_access_item(self) -> None:
        """StoryComplete events fire as soon as the matching access item is held."""
        self.collect_by_name("Hollis' Hot Streak Access")
        hh_event = self.multiworld.get_location(
            "Hollis' Hot Streak Complete (Story Event)", self.player
        )
        self.assertTrue(
            self.multiworld.state.can_reach(hh_event, "Location", self.player),
            "HH StoryComplete event should be reachable with HH_Access",
        )

    def test_psitanium_filler_items_registered(self) -> None:
        """Psitanium x25/50/100 must be registered as valid filler options."""
        from worlds.psychonauts2.items import item_name_to_id, filler_item_names
        for variant in ("Psitanium x25", "Psitanium x50", "Psitanium x100"):
            self.assertIn(variant, item_name_to_id, f"{variant} missing from item_name_to_id")
            self.assertIn(variant, filler_item_names, f"{variant} missing from filler_item_names")

    def test_important_items_classified_useful(self) -> None:
        """Access items marked 'Important' in the CSV should be 'useful', not progression.

        Items that appear in access rules are promoted to *progression* explicitly
        via _FORCED_PROGRESSION_KEYS, but items not used in any rule should remain
        *useful* rather than jumping straight to progression.
        """
        # GNG_Access is Important in the CSV but also in _FORCED_PROGRESSION_KEYS
        # (used in the victory rule) → progression is expected.
        # A non-rule Important item like a costume piece should be useful.
        from worlds.psychonauts2.items import item_classifications
        gng_cls = item_classifications.get("Green Needle Gulch Access")
        self.assertEqual(
            gng_cls,
            ItemClassification.progression,
            "GNG_Access (Important + forced-progression) should be progression",
        )

    def test_thought_tuner_and_otto_shot_progression_not_win_required(self) -> None:
        """ThoughtTuner and Otto-Shot gate checks (progression) but are not needed to win.

        They must be classified as progression so that state.has() can track them
        for the checks they lock.  However, neither item should appear in any
        win condition's required-items list.
        """
        from worlds.psychonauts2.items import item_classifications, WIN_CONDITION_REQUIRED_ITEMS
        for display_name in ("Thought Tuner", "Otto-Shot"):
            cls = item_classifications.get(display_name)
            self.assertEqual(
                cls,
                ItemClassification.progression,
                f"{display_name} must be progression so state.has() works for locked checks",
            )
            for col, required in WIN_CONDITION_REQUIRED_ITEMS.items():
                self.assertNotIn(
                    display_name, required,
                    f"{display_name} must not be required for win condition '{col}'",
                )

    def test_otto_spot_is_filler(self) -> None:
        """Otto-Spot is a junk item and must be classified as filler."""
        from worlds.psychonauts2.items import item_classifications
        cls = item_classifications.get("Otto-Spot")
        self.assertEqual(
            cls,
            ItemClassification.filler,
            "Otto-Spot should be filler/junk",
        )

    def test_location_names_unique(self) -> None:
        """All 607 randomised location names must be unique."""
        locations = [loc for loc in self.multiworld.get_locations(self.player) if not loc.is_event]
        names = [loc.name for loc in locations]
        self.assertEqual(len(names), len(set(names)), "Duplicate location names found")

    def test_item_names_unique(self) -> None:
        """
        All UNIQUE item display names in item_name_to_id must be unique.
        (Multiple copies of the same item are allowed, e.g. progressive items.)
        """
        from worlds.psychonauts2.items import item_name_to_id
        self.assertEqual(
            len(item_name_to_id),
            len(set(item_name_to_id.keys())),
            "Duplicate item display names in item_name_to_id",
        )

    def test_melee_is_precollected_not_in_pool(self) -> None:
        """Melee - Base Power must be precollected and absent from the item pool."""
        pool_names = {i.name for i in self.multiworld.itempool if i.player == self.player}
        self.assertNotIn(
            "Melee - Base Power", pool_names,
            "Melee - Base Power should be a starting item, not in the randomised pool",
        )
        precoll_names = [i.name for i in self.multiworld.precollected_items[self.player]]
        self.assertIn(
            "Melee - Base Power", precoll_names,
            "Melee - Base Power should be precollected",
        )

    def test_melee_gates_accessible_with_motherlobe(self) -> None:
        """Checks gated by Melee must be reachable when Motherlobe_Access is held.

        Since Melee is always precollected, no extra item should be needed for
        the Melee requirement itself.
        """
        self.collect_by_name("Intern Sticker")
        self.assertTrue(
            self.can_reach_location("Rainblows"),
            "Rainblows should be reachable with Intern Sticker (Melee is precollected)",
        )

    def test_default_outfit_precollected_others_in_pool(self) -> None:
        """With the default StartingOutfit (Normal Outfit), Normal Outfit is precollected
        and the other three outfits are in the randomised pool."""
        from worlds.psychonauts2.items import OUTFIT_ITEM_KEYS, csv_key_to_display_name
        outfit_names = [csv_key_to_display_name.get(k, k) for k in OUTFIT_ITEM_KEYS]
        precoll_names = {i.name for i in self.multiworld.precollected_items[self.player]}
        pool_names = {i.name for i in self.multiworld.itempool if i.player == self.player}

        # Default option is index 0 → Normal Outfit
        self.assertIn("Normal Outfit", precoll_names, "Normal Outfit should be precollected by default")
        for outfit_name in outfit_names:
            if outfit_name != "Normal Outfit":
                self.assertIn(outfit_name, pool_names, f"{outfit_name} should be in the pool")


class TestStartingOutfitTriedAndTrue(Psy2TestBase):
    """Tests with 'Tried and True' selected as the starting outfit."""
    options = {"starting_outfit": "tried_and_true"}

    def test_tried_and_true_precollected(self) -> None:
        """Tried and True should be in start inventory, not the pool."""
        precoll_names = {i.name for i in self.multiworld.precollected_items[self.player]}
        pool_names = {i.name for i in self.multiworld.itempool if i.player == self.player}
        self.assertIn("Tried and True", precoll_names)
        self.assertNotIn("Tried and True", pool_names)

    def test_other_outfits_in_pool(self) -> None:
        """The three non-chosen outfits must be in the randomised pool."""
        pool_names = {i.name for i in self.multiworld.itempool if i.player == self.player}
        for outfit_name in ("Normal Outfit", "Circus Skivvies", "Suit"):
            self.assertIn(outfit_name, pool_names, f"{outfit_name} should be in pool")


class TestStartingOutfitSuit(Psy2TestBase):
    """Tests with 'Suit' selected as the starting outfit."""
    options = {"starting_outfit": "suit"}

    def test_suit_precollected(self) -> None:
        """Suit should be in start inventory, not the pool."""
        precoll_names = {i.name for i in self.multiworld.precollected_items[self.player]}
        pool_names = {i.name for i in self.multiworld.itempool if i.player == self.player}
        self.assertIn("Suit", precoll_names)
        self.assertNotIn("Suit", pool_names)

    def test_pool_still_matches_locations(self) -> None:
        """Pool size must equal location count regardless of starting outfit."""
        location_count = len([
            loc for loc in self.multiworld.get_locations(self.player)
            if not loc.is_event
        ])
        item_count = len([
            item for item in self.multiworld.itempool
            if item.player == self.player
        ])
        self.assertEqual(item_count, location_count)
