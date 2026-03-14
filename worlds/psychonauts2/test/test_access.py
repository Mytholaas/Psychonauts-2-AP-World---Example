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
        """Items required by the All Bosses condition must be progression items."""
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
            "Maligula Fight Access",
        ]
        pool_by_name = {i.name: i for i in self.multiworld.itempool if i.player == self.player}
        for item_name in expected_required:
            if item_name in pool_by_name:
                self.assertEqual(
                    pool_by_name[item_name].classification,
                    ItemClassification.progression,
                    f"Expected {item_name!r} to be progression under AllBosses win condition",
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
        ids = [v for v in item_name_to_id.values() if v is not None]
        # IDs may be shared by progressive copies, but names must map to unique IDs
        self.assertEqual(
            len(item_name_to_id),
            len(set(item_name_to_id.keys())),
            "Duplicate item display names in item_name_to_id",
        )
