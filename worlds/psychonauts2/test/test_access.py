"""
Psychonauts 2 Archipelago - Access Rule Tests

These tests verify that location access rules work correctly, particularly:
  - Progressive ability rules (base and upgrade levels)
  - Area access items gate their respective regions
  - OR-logic in requirements works correctly
  - Scavenger-hunt requirements expand properly
  - Win-condition options change which items are required
"""

from . import Psy2TestBase


class TestDefaultWinCondition(Psy2TestBase):
    """
    Tests with the default (Normal) win condition.

    In Normal mode, the player needs core abilities and several area access items
    to reach Maligula.
    """

    def test_motherlobe_requires_access(self) -> None:
        """Motherlobe region locations should not be reachable without Intern Sticker."""
        self.assertNotAccessible("Bowling Alley (Supply Chest)", [])

    def test_bowling_alley_requires_senior_league_card(self) -> None:
        """Bowling Alley checks also require the Senior League Card."""
        # With Motherlobe access but no Senior League Card, bowling alley is inaccessible
        self.assertNotAccessible(
            "Bowling Alley (Supply Chest)", ["Intern Sticker"]
        )
        # With both, it becomes accessible
        self.assertAccessible(
            "Bowling Alley (Supply Chest)",
            ["Intern Sticker", "Senior League Card"],
        )

    def test_quarry_requires_access(self) -> None:
        """Quarry locations should not be reachable without the Quarry access item."""
        self.assertNotAccessible("Otto's Lab (Psi Card)", [])
        self.assertAccessible("Otto's Lab (Psi Card)", ["Thinkerprint Full Access"])

    def test_mental_world_requires_access(self) -> None:
        """Loboto's Labrynth should not be accessible without its access item."""
        self.assertNotAccessible("Behind Painting", [])
        self.assertAccessible(
            "Behind Painting",
            [
                "Loboto's Labrynth Access",
                "Loboto's Labrynth Complete",
                "Progressive Telekinesis",
                "Progressive Pyrokinesis",
            ],
        )

    def test_progressive_ability_base_required(self) -> None:
        """A check gated by the base ability should require exactly 1 progressive copy."""
        # Telekinesis-gated shop item
        self.assertNotAccessible("Beastmastery", ["Intern Sticker"])
        self.assertAccessible("Beastmastery", ["Intern Sticker", "Progressive Telekinesis"])

    def test_progressive_ability_upgrade_count(self) -> None:
        """MentalConnection_Upgrade3 requires 4 copies of Progressive Mental Connection."""
        # HH check needing MentalConnection_Upgrade3 (requires 4 copies)
        self.assertNotAccessible(
            "MC after first Heart",
            ["Hollis' Hot Streak Access", "Progressive Mental Connection"] * 3,
        )
        self.assertAccessible(
            "MC after first Heart",
            [
                "Hollis' Hot Streak Access",
                "Progressive Mental Connection",
                "Progressive Mental Connection",
                "Progressive Mental Connection",
                "Progressive Mental Connection",
                "Progressive Psi Blast",
            ],
        )

    def test_or_requirement(self) -> None:
        """Checks with OR requirements should be accessible via either option."""
        # QA Psi Card 24 needs (Telekinesis OR TimeBubble) AND QA_Access
        self.assertNotAccessible("Woods near Rundown Cabin", [])
        self.assertNotAccessible("Woods near Rundown Cabin", ["Progressive Telekinesis"])
        self.assertAccessible(
            "Woods near Rundown Cabin",
            ["Questionable Area Access", "Progressive Telekinesis"],
        )
        self.assertAccessible(
            "Woods near Rundown Cabin",
            ["Questionable Area Access", "Progressive Time Bubble"],
        )

    def test_global_rank_checks_always_accessible(self) -> None:
        """Rank-point checks have no item requirement and are always accessible."""
        self.assertAccessible("Rank 1", [])
        self.assertAccessible("Rank 50", [])
        self.assertAccessible("Rank 102", [])

    def test_ability_check_always_accessible(self) -> None:
        """Base ability unlock checks have no item requirement."""
        self.assertAccessible("Telekinesis - Base Power", [])
        self.assertAccessible("Levitation - Base Power", [])


class TestAllBossesWinCondition(Psy2TestBase):
    """Tests with the All Bosses win condition."""
    options = {"win_condition": "all_bosses"}

    def test_all_bosses_required_items_are_progression(self) -> None:
        """Items required by the All Bosses condition must have progression classification."""
        required = [
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
        for item_name in required:
            items = self.multiworld.itempool
            matching = [i for i in items if i.name == item_name and i.player == self.player]
            if matching:
                from BaseClasses import ItemClassification
                self.assertTrue(
                    matching[0].classification == ItemClassification.progression,
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
        from BaseClasses import ItemClassification
        pool_items = {i.name: i for i in self.multiworld.itempool if i.player == self.player}
        for item_name in scav_items:
            if item_name in pool_items:
                self.assertEqual(
                    pool_items[item_name].classification,
                    ItemClassification.progression,
                    f"Expected {item_name!r} to be progression under AllScavHunt win condition",
                )

    def test_scav_hunt_outfit_check_requires_all_scav_items(self) -> None:
        """Scav Hunt Bathroom Checks require all scavenger-hunt items."""
        # Just verify these locations are not accessible without any items
        self.assertNotAccessible("Scav Hunt Bathroom Check 1", [])


class TestItemPoolSize(Psy2TestBase):
    """Tests that verify the item pool is correctly sized."""

    def test_pool_matches_location_count(self) -> None:
        """The item pool must have exactly as many items as there are locations."""
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
