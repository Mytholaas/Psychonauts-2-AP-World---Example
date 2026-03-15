# Psychonauts 2 Archipelago Randomizer

An [Archipelago](https://archipelago.gg) multiworld randomizer for
[Psychonauts 2](https://store.steampowered.com/app/607080/) (PC / Game Pass).

---

## 📥 Quick Download

> **Just want to play?  Everything you need is in the [`releases/`](releases/) folder.**

| File | Purpose |
|------|---------|
| [`releases/psychonauts2.apworld`](releases/psychonauts2.apworld) | Install into `Archipelago/custom_worlds/` |
| [`releases/Psychonauts2_Player.yaml`](releases/Psychonauts2_Player.yaml) | Edit your name & options, then upload when generating a seed |

---

## 🚀 Quick Start

1. **Install Archipelago** from <https://github.com/ArchipelagoMW/Archipelago/releases>
2. **Copy** `releases/psychonauts2.apworld` → `Archipelago/custom_worlds/`
3. **Edit** `releases/Psychonauts2_Player.yaml` — at minimum set your `name`
4. **Install the Psychonauts 2 AP Mod** (see [Setup Guide](worlds/psychonauts2/docs/setup_en.md))
5. **Generate a seed** at <https://archipelago.gg> using your edited YAML
6. **Connect** by filling in `ap_config.json` in your game folder and launching Psychonauts 2

---

## 🎮 What Does the Randomizer Do?

607 collectible locations across all of Psychonauts 2 are shuffled into the multiworld
item pool.  This includes Psi Cards, Supply Chests, Psy Challenge Markers, Scavenger Hunt
items, Figment Milestones, Memory Vaults, Nuggets of Wisdom, shop items, rank rewards,
and more.

### Win Conditions

| Option | Description |
|--------|-------------|
| `normal` | Obtain core abilities and key area access items, then defeat Maligula |
| `all_bosses` | Obtain all 8 psychic abilities, complete 4 boss mental worlds, defeat Maligula |
| `all_scav_hunt` | Collect all 16 scavenger-hunt items, then defeat Maligula |
| `scav_hunt_and_maligula` | Scavenger-hunt items unlock Maligula's fight, then defeat her |

### Player Options (YAML)

| Option | Values | Default |
|--------|--------|---------|
| `win_condition` | `normal` / `all_bosses` / `all_scav_hunt` / `scav_hunt_and_maligula` | `normal` |
| `starting_outfit` | `normal_outfit` / `tried_and_true` / `circus_skivvies` / `suit` | `normal_outfit` |
| `include_shop_items` | `true` / `false` | `true` |
| `death_link` | `true` / `false` | `false` |

---

## 🛠 Mod Requirements

The randomizer requires the **Psychonauts 2 AP Mod** which runs on
[UE4SS (Unreal Engine 4 Scripting System)](https://github.com/UE4SS-RE/RE-UE4SS/releases).

The mod files are in the [`mod/Psychonauts2AP/`](mod/Psychonauts2AP/) folder of this
repository.  Full installation steps are in the
[Setup Guide](worlds/psychonauts2/docs/setup_en.md).

---

## 📂 Repository Structure

```
releases/                   ← Download files for players (apworld + yaml)
mod/Psychonauts2AP/         ← UE4SS Lua mod (install into game's Mods/ folder)
worlds/psychonauts2/        ← Archipelago world source code
  __init__.py               ← Main world class
  items.py                  ← Item definitions (loaded from CSV)
  locations.py              ← Location definitions (loaded from CSV)
  options.py                ← Player YAML options
  rules.py                  ← Access rules
  data/                     ← CSV data files
  docs/                     ← Setup guide and game documentation
  test/                     ← Automated tests
ap_config.json              ← Connection config template (copy to game folder)
UE4SS-settings.ini          ← UE4SS config (copy to game folder)
```

---

## 📖 Documentation

- [Setup Guide](worlds/psychonauts2/docs/setup_en.md) — full installation walkthrough
- [Game Info](worlds/psychonauts2/docs/en_Psychonauts%202.md) — what is randomized and how
- [Mod Requirements](worlds/psychonauts2/docs/UE4_MOD_REQUIREMENTS.md) — UE4SS mod details
