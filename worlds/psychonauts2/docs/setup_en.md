# Psychonauts 2 Archipelago Multiworld Setup Guide

## Required Software

- [Psychonauts 2](https://store.steampowered.com/app/607080/) (PC / Game Pass version)
- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) (the server and client tools)
- Psychonauts 2 Archipelago Mod (download from the mod's release page once available)

---

## Installation Steps

### 1 – Install the Psychonauts 2 Archipelago Mod

1. Download the latest release of the Psychonauts 2 AP Mod.
2. Extract the mod archive and copy its contents into the Psychonauts 2 game folder
   (the same folder that contains `Psychonauts2.exe` or the equivalent launcher).
3. The mod installs as an Unreal Engine 4 pak file; no additional tools are required.

### 2 – Configure Your Player YAML

1. Generate a template YAML from the Archipelago website or use the following minimal example:

```yaml
name: YourName
game: Psychonauts 2
Psychonauts 2:
  win_condition: normal        # normal | all_bosses | all_scav_hunt | scav_hunt_and_maligula
  starting_outfit: normal_outfit  # normal_outfit | tried_and_true | circus_skivvies | suit
  death_link: false
```

2. Save the YAML and upload it when creating your multiworld seed.

### 3 – Generate or Join a Seed

- **Hosting a game**: Upload all player YAML files to the Archipelago website and generate
  a seed.  Start the Archipelago server with the resulting `.archipelago` file.
- **Joining a game**: Obtain the server address and port from the host.

### 4 – Launch Psychonauts 2 with the Mod

1. Start Psychonauts 2 normally.  The AP mod will detect the Archipelago client
   configuration file (`ap_config.json`) in the game folder.
2. Edit `ap_config.json` to set your server address, slot name, and password:

```json
{
  "server": "archipelago.gg:12345",
  "slot_name": "YourName",
  "password": ""
}
```

3. When you load or start a new save, the mod will connect to the Archipelago server
   automatically.

---

## Win Conditions

| Option | Description |
|--------|-------------|
| **Normal** | Obtain the core psychic abilities (Telekinesis, Psi Blast, Pyrokinesis, Levitation, Mental Connection, Time Bubble), unlock Green Needle Gulch, Ford's Follicles, Strike City, Cruller's Correspondence, and Tomb of the Sharkophagus, then defeat Maligula. |
| **All Bosses** | Obtain all eight psychic abilities, complete Hollis' Hot Streak, Compton's Cookoff, Bob's Bottles, and Cassie's Collection, trigger Maligula Access, then defeat Maligula. |
| **All Scav Hunt** | Collect all 16 scavenger-hunt items, then defeat Maligula. |
| **Scav Hunt and Maligula** | Collect all 16 scavenger-hunt items (this triggers Maligula Access automatically), then defeat Maligula. |

---

## Starting Outfit

One of four outfits can be selected in the YAML to be pre-equipped at the start of the
seed.  The remaining three outfits are shuffled into the randomised item pool.

| Option | Outfit |
|--------|--------|
| `normal_outfit` *(default)* | Raz's default look from the start of the normal game. |
| `tried_and_true` | The classic Psychonauts 1 outfit. |
| `circus_skivvies` | Raz's circus performance costume. |
| `suit` | A sharp-looking formal suit. |

---

## Progressive Abilities

The eight psychic abilities and three inventory-upgrade pairs work as progressive items:

- **Psychic Abilities** – Telekinesis, Psi Blast, Pyrokinesis, Levitation, Clairvoyance,
  Mental Connection, Time Bubble, Projection each have a base level and three upgrades.
  Finding *any* copy of a progressive ability always grants the next available tier.
- **Carry Capacity** – Mind's Eyelets → Expandolier
- **Fluff Pouch** – Fluff Pockets → Jumbo Fluff Pouch
- **Wallet** – Psifold Wallet → Astral Wallet

---

## Mod Game-Logic Notes

- Players always start with at least one mental world and one hub area (Motherlobe,
  Quarry, Questionable Area, or Green Needle Gulch) already unlocked.
- Players spawn in the Collective Unconscious.
- Mental Connection is *not* required to navigate the Collective Unconscious.
- **Melee** (basic melee attacks) is always available from the start of every seed.
  The three melee upgrades (Dodge Attack, Slap Happy, Shockwave) are randomised items.
- **Smelling Salts** can be used to exit any mental world or the Collective
  Unconscious and will route the player to an available hub area.
  - Preferred exit target: the hub area (Motherlobe or Green Needle Gulch) where the
    player last used the Brain Tumbler, if that area is currently available.
- The Maligula fight is activated by interacting with the Astralathe in Green Needle
  Gulch once all win-condition requirements have been met.
- Hub areas (Motherlobe, Quarry, Questionable Area, Green Needle Gulch) are in their
  post-final-boss state.  Mental worlds are in their first-entry state.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Mod not loading | Verify the pak file is in the correct folder and that mod loading is enabled in game settings. |
| Cannot connect to server | Check `ap_config.json` for correct server address, slot name, and password. |
| Items not being sent/received | Ensure the Archipelago server is running and the game client shows "Connected". |
| Stuck with no accessible checks | Use Smelling Salts to return to a hub area and look for accessible checks there. |
