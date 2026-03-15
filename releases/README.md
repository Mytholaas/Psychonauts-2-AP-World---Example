# Psychonauts 2 Archipelago – Downloads

This folder contains the two files you need to play Psychonauts 2 in an Archipelago multiworld.

---

## 📥 Files

### `psychonauts2.apworld`

The Archipelago world definition file.  Install it by placing it in the `custom_worlds`
folder inside your Archipelago installation:

```
Archipelago/
└── custom_worlds/
    └── psychonauts2.apworld   ← put it here
```

Restart the Archipelago Launcher after copying the file.

---

### `Psychonauts2_Player.yaml`

Your player configuration file.  Open it in any text editor and change at minimum:

| Field | What to change |
|-------|---------------|
| `name` | Your player name (must be unique in the multiworld) |
| `win_condition` | `normal` / `all_bosses` / `all_scav_hunt` / `scav_hunt_and_maligula` |
| `starting_outfit` | `normal_outfit` / `tried_and_true` / `circus_skivvies` / `suit` |
| `include_shop_items` | `true` (607 locations) or `false` (559 locations) |
| `death_link` | `false` (recommended) or `true` |

Upload the edited YAML to the Archipelago website when generating your seed.

---

## 🚀 Quick Start

1. **Download** `psychonauts2.apworld` → copy to `Archipelago/custom_worlds/`
2. **Download** `Psychonauts2_Player.yaml` → edit your name & options
3. **Upload** the YAML to <https://archipelago.gg> to generate a seed
4. **Install** the Psychonauts 2 AP Mod (see the full setup guide below)
5. **Connect** using `ap_config.json` in your game folder

For full installation instructions see [docs/setup_en.md](../worlds/psychonauts2/docs/setup_en.md)
or the [repository README](../README.md).
