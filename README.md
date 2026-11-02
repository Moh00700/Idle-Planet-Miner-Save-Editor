# 🪐 Idle Planet Miner Save Editor

A small, dependency-free Python script that edits the `playerInfo.dat` save file of the
mobile/PC game **Idle Planet Miner** (a .NET BinaryFormatter file). Change currencies,
unlock planets and resources, set upgrade levels, flip any true/false flag, and more.

> ⚠️ **Unofficial fan tool.** Not affiliated with the game's developers. For single-player
> use on your own save. Editing saves may break your game or trigger anti-cheat if the game
> syncs online. **Always back up your original save first.** 💾

## ✨ Features

- 🛡️ Edits values **in place**: file size and structure stay identical, so the save stays valid
- 🎯 Set any value for **each individual resource / planet**, or fill a whole list at once
- ✅ Edit true/false flags (planet unlocked, recipe unlocked, tutorials, ads disabled, ...)
- 🔍 `--dump` shows every field in the save; `--export` writes an editable JSON template
- 🐍 No installation of packages needed. Pure Python 3 standard library

## 📦 Install

You need **Python 3.8+** ([python.org/downloads](https://www.python.org/downloads/)).

```bash
git clone https://github.com/<your-username>/idle-planet-miner-save-editor.git
cd idle-planet-miner-save-editor
```

No `pip install` is required. (Or just download `edit_save.py` on its own.)

## 📂 Find your save file

Locate `playerInfo.dat`, then **copy it somewhere safe as a backup**.

| Platform | Typical location |
|---|---|
| 🤖 Android | `Android/data/<game package>/files/` (may need a file manager that can browse `Android/data`) |
| 🪟 Windows (Steam) | `%USERPROFILE%\AppData\LocalLow\<developer>\Idle Planet Miner\` |
| 🍎 iOS | Not directly accessible without a backup tool |

(Exact folders vary by version and store. Search your device for `playerInfo.dat`.)

## 🚀 Usage

Copy `playerInfo.dat` next to the script, then:

```bash
# 1. Apply the built-in settings (a "max everything" preset) -> playerInfo_modded.dat
python3 edit_save.py playerInfo.dat

# 2. Choose the output name
python3 edit_save.py playerInfo.dat my_new_save.dat

# 3. Look at everything in your save
python3 edit_save.py playerInfo.dat --dump

# 4. Export your current values to a JSON file you can edit
python3 edit_save.py playerInfo.dat --export my_config.json

# 5. Apply your edited JSON
python3 edit_save.py playerInfo.dat out.dat --config my_config.json
```

On Windows use `python` instead of `python3`.

🎮 Then **close the game**, replace the game's `playerInfo.dat` with the modded file
(keeping the original name), and start the game. Running offline the first time is safest.

## 🎛️ Customizing values

### 📝 Option A: edit the `SETTINGS` block at the top of `edit_save.py`

```python
SCALARS = {
    'cash': 1e25,
    'darkMatter': 1_000_000,
    'disableAdsUnlockedBool': True,
}
ARRAYS = {
    'planetUnlocked': True,                  # every slot
    'resourceCount': {0: 5_000_000, 31: 250},# only slots 0 and 31
    'miningSpeedLevel': [100, 50, None],     # per-slot list (None = leave alone)
}
```

### 🗂️ Option B: edit a JSON file

Run `--export my_config.json`, open it in a text editor, change values, and apply with
`--config`. In JSON use lowercase `true` / `false`. Arrays can be a full list, or an
object like `{"0": 500, "31": 42}` to change only some slots.
See [`examples/max_config.json`](examples/max_config.json) for the preset used by default.

💡 **Slot numbers start at 0.** The save does not store names, so slot N means "the Nth planet /
resource in the game's internal order". Change one slot and check in-game to learn the mapping.

## 🔧 What can be edited

| Field | Meaning |
|---|---|
| 💰 `cash`, `credits` | Money (double) |
| 💎 `darkMatter`, `energyCell`, `holoBolts`, `prestigeCurrency`, `tokens` | Premium / prestige currencies |
| 🧩 `drillFragments`, `transportFragments`, `synthFragments`, `remoteFragments`, `moduleRerollCurrency` | Module currencies |
| 🌍 `planetUnlocked` (79) | Planet unlock flags |
| ⛏️ `miningSpeedLevel`, `speedLevel`, `cargoLevel` (79) | Per-planet upgrade levels |
| 🪨 `resourceDiscovered`, `resourceCount` (120) | Resource flags and stock |
| 🏗️ `projectAvailableBool`, `projectUnlockedBool` (260) | Projects |
| 🔥 `recipeUnlocked`, `craftRecipeUnlocked`, and `alternate...` | Smelting/crafting recipes |
| 🏭 `smeltersUnlocked`, `craftersUnlocked`, `maxSlots` | Machine and manager-slot counts |
| 🚫 `disableAdsUnlockedBool` | "Disable ads" flag |
| 📖 `tutorialCompleteBool1..7`, `dialogueShownSavebool` | Tutorial progress |

Use `--dump` to discover other fields; any plain number/bool field or primitive array can
be added to `SCALARS` / `ARRAYS` by name.

## 🚧 Known limits

- Managers, relics, modules, station projects and prestige rewards are not edited by default
  (they depend on linked data such as names and classes).
- Level caps are unknown. If a planet misbehaves, lower the level.
- If the game updates its save format, the script may need changes. It reads the layout from
  the file itself, so small updates usually still work.
- Not every record type of the .NET format is supported; unsupported saves raise a clear error.

## 🩺 Troubleshooting

- ❌ **`not a class record` / `unsupported record`**: the file isn't a `playerInfo.dat` from this game or version.
- ☁️ **Game shows old values / resets**: it may be syncing from the cloud. Disable cloud save / go offline.
- 📢 **Ads still show**: the purchase may be re-verified with the store. Try offline.

