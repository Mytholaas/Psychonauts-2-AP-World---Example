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
    trigger Maligula_Access, then defeat Maligula.

  WinCondition_AllScavHunt
    Collect all 16 scavenger-hunt items, then defeat Maligula.

  WinCondition_ScavHunt_and_Maligula
    Collect all 16 scavenger-hunt items to trigger Maligula_Access, then
    defeat Maligula.

Starting outfit
  One of four outfits is chosen to be pre-equipped at the start of the seed.
  The remaining three outfits are randomised into the world as items.
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
        Compton's Cookoff, Bob's Bottles, and Cassie's Collection, trigger
        Maligula Access, and defeat Maligula.

    All Scav Hunt
        Collect all 16 scavenger-hunt collectibles, then defeat Maligula.

    Scav Hunt and Maligula
        Collect all 16 scavenger-hunt collectibles (this triggers Maligula
        Access automatically), then defeat Maligula.
    """
    display_name = "Win Condition"
    option_normal = 0
    option_all_bosses = 1
    option_all_scav_hunt = 2
    option_scav_hunt_and_maligula = 3
    default = 0


class StartingOutfit(Choice):
    """
    Choose which outfit Raz starts the seed already wearing.

    The chosen outfit is placed in Raz's starting inventory.  The remaining
    three outfits are shuffled into the randomised item pool.

    Normal Outfit
        The default look Raz wears at the start of the normal game.

    Tried and True
        The classic Psychonauts 1 outfit.

    Circus Skivvies
        Raz's circus performance costume.

    Suit
        A sharp-looking formal suit.
    """
    display_name = "Starting Outfit"
    option_normal_outfit = 0
    option_tried_and_true = 1
    option_circus_skivvies = 2
    option_suit = 3
    default = 0


@dataclass
class Psy2Options(PerGameCommonOptions):
    win_condition: WinCondition
    starting_outfit: StartingOutfit
    death_link: DeathLink
