"""
Psychonauts 2 Archipelago - Player Options

Win-condition options control which items are classified as Required
(progression) when generating the seed and what the player must accomplish to
complete the randomiser.

The four win conditions are:

  WinCondition_Normal
    Obtain key psychic abilities and area-access items, then defeat Maligula.

  WinCondition_AllBosses
    Obtain all eight psychic abilities, complete four specific mental worlds,
    collect the Maligula Fight Access item, then defeat Maligula.

  WinCondition_AllScavHunt
    Collect all 16 scavenger-hunt items, collect the Maligula Fight Access
    item, then defeat Maligula.

  WinCondition_ScavHunt_and_Maligula
    Collect all 16 scavenger-hunt items, then defeat Maligula.
    (Maligula Fight Access is not required as a separate item.)
"""

from dataclasses import dataclass
from Options import Choice, DeathLink, PerGameCommonOptions


class WinCondition(Choice):
    """
    Choose what the player must accomplish to complete the randomiser.

    Normal
        Obtain the key psychic abilities, unlock Green Needle Gulch, Ford's
        Follicles, Strike City, Cruller's Correspondence, and Tomb of the
        Sharkophagus, then defeat Maligula at the Astralathe.

    All Bosses
        Obtain all eight psychic abilities, complete Hollis' Hot Streak,
        Compton's Cookoff, Bob's Bottles, and Cassie's Collection, collect the
        Maligula Fight Access item, and defeat Maligula.

    All Scav Hunt (with Maligula access item)
        Collect all 16 scavenger-hunt collectibles AND the Maligula Fight
        Access item, then defeat Maligula.

    Scav Hunt and Maligula
        Collect all 16 scavenger-hunt collectibles (no separate Maligula
        access item required), then defeat Maligula.
    """
    display_name = "Win Condition"
    option_normal = 0
    option_all_bosses = 1
    option_all_scav_hunt = 2
    option_scav_hunt_and_maligula = 3
    default = 0


@dataclass
class Psy2Options(PerGameCommonOptions):
    win_condition: WinCondition
    death_link: DeathLink
