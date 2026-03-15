# Psychonauts 2 Archipelago Multiworld Setup Guide

## Required Software

- [Psychonauts 2](https://store.steampowered.com/app/607080/) (PC / Game Pass version)
- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) (the server and client tools)
- [UE4SS Experimental](https://github.com/UE4SS-RE/RE-UE4SS/releases) (Unreal Engine 4 Scripting System)
- Psychonauts 2 Archipelago Mod (from this repository — see installation steps below)

---

## Installation Steps

### 1 – Install UE4SS

UE4SS is the Unreal Engine 4 scripting framework that runs the mod.

1. Download the latest **experimental** release of UE4SS from
   <https://github.com/UE4SS-RE/RE-UE4SS/releases>.
2. Extract the archive.  You will get several files including `UE4SS.dll`,
   `UE4SS.pdb`, `dwmapi.dll`, `UE4SS-settings.ini`, and a `Mods` folder.
3. Copy **all** of these files and folders into the Psychonauts 2 game root
   (the folder that contains `Psychonauts2.exe` or the Game Pass launcher).
4. Replace the `UE4SS-settings.ini` that came with UE4SS with the one from
   this repository.  The repository version pins UE4SS to Unreal Engine 4.26
   so it resolves the correct object offsets for Psychonauts 2.

> **Windows Store / Game Pass users:** The game executable may be in a different
> location (e.g. `C:\XboxGames\Psychonauts 2\Content\Psychonauts2.exe`).
> Place UE4SS files next to that executable.

### 2 – Install the Psychonauts 2 Archipelago Mod

1. In the game root, locate (or create) the `Mods` folder that UE4SS uses.
2. Copy the `mod/Psychonauts2AP` folder from this repository into `Mods`:

   ```
   Psychonauts2/
   ├── Psychonauts2.exe
   ├── UE4SS.dll
   ├── UE4SS-settings.ini
   ├── ap_config.json          ← copy from this repo root
   └── Mods/
       └── Psychonauts2AP/     ← copy from mod/ in this repo
           ├── enabled.txt
           └── Scripts/
               ├── main.lua
               ├── archipelago.lua
               ├── items.lua
               ├── locations.lua
               ├── config.lua
               └── save.lua
   ```

3. Copy `ap_config.json` from the repository root into the game root folder
   (next to `Psychonauts2.exe`).

### 3 – Configure Your Connection (`ap_config.json`)

Edit `ap_config.json` in the game folder to match your Archipelago session:

```json
{
  "server": "archipelago.gg:38281",
  "slot_name": "YourName",
  "password": ""
}
```

| Field | Description |
|-------|-------------|
| `server` | Hostname and port of the Archipelago server (e.g. `"myserver.com:38281"`) |
| `slot_name` | Your player name exactly as entered when the seed was generated |
| `password` | Room password if the host set one; leave `""` for none |

> If `ap_config.json` does not exist when the game starts, the mod will create
> an example file automatically.  Edit it and restart the game.

### 4 – Configure Your Player YAML

Generate a template YAML from the Archipelago website or use the following
minimal example:

```yaml
name: YourName
game: Psychonauts 2
Psychonauts 2:
  win_condition: normal          # normal | all_bosses | all_scav_hunt | scav_hunt_and_maligula
  starting_outfit: normal_outfit # normal_outfit | tried_and_true | circus_skivvies | suit
  include_shop_items: true
  death_link: false
```

Save the YAML and upload it when creating your multiworld seed.

### 5 – Generate or Join a Seed

- **Hosting a game**: Upload all player YAML files to the Archipelago website and generate
  a seed.  Start the Archipelago server with the resulting `.archipelago` file.
- **Joining a game**: Obtain the server address and port from the host, then update
  your `ap_config.json` accordingly.

### 6 – Launch Psychonauts 2 with the Mod

1. Start Psychonauts 2 normally.
2. UE4SS will automatically inject itself (via the `dwmapi.dll` proxy) and load
   the Psychonauts2AP mod from the `Mods` folder.
3. The mod reads `ap_config.json`, connects to the Archipelago server, and
   begins the randomiser session.
4. Load or start a save.  The mod will synchronise your collected items and
   sent checks with the server automatically.

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
| Mod not loading | Verify `UE4SS.dll` and `dwmapi.dll` are in the game root, `UE4SS-settings.ini` has `ModLoading=1`, and `Mods/Psychonauts2AP/enabled.txt` exists. |
| Cannot connect to server | Check `ap_config.json` for the correct server address, slot name, and password. |
| ap_config.json not found | The mod creates an example on first run — edit it and restart the game. |
| Items not being sent/received | Ensure the Archipelago server is running.  The UE4SS console (enable via `DebugConsoleEnabled=1` in `UE4SS-settings.ini`) shows `[AP] Connected` on success. |
| Stuck with no accessible checks | Use Smelling Salts to return to a hub area and look for accessible checks there. |
| Game crashes on startup | Make sure you are using the UE4SS *experimental* release and that `UE4SS-settings.ini` pins `MajorVersion=4 MinorVersion=26`. |
| DeathLink kills are not received | Ensure `death_link: true` is set in your YAML and the session was generated with that setting. |

### Reading the UE4SS Console

Enable the debug console by setting `DebugConsoleEnabled=1` in `UE4SS-settings.ini`.
The mod prints status messages prefixed with `[AP]`:

| Message | Meaning |
|---------|---------|
| `[AP] Config loaded — server=… slot=…` | `ap_config.json` was read successfully |
| `[AP] TCP connected to …` | TCP socket connected; waiting for server response |
| `[AP] Connected as … (slot …)` | Authenticated with the AP server |
| `[AP] Check completed: … (id=…)` | A location check was sent to the server |
| `[AP] Granting item: … (id=…)` | An item received from another player is being applied |
| `[AP] Disconnected from server.` | Connection lost; will retry automatically |
