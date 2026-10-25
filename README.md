# FC 25 Squad Editor

A standalone desktop application for reading, visualizing, editing, and repacking **EA SPORTS FC 25 Squads save files**. Built with a clean, dark-mode Dear ImGui-inspired interface matching `Launcher.exe`.

---

## 🚀 How to Run

You can launch the editor directly by double-clicking the standalone executable:

```
dist\FC25_Squad_Editor.exe
```

*(No Python installation, web browser, or local server required.)*

To run or develop from source using the virtual environment:
```powershell
.\venv\Scripts\python.exe main.py
```

To recompile the standalone executable at any time:
```powershell
.\venv\Scripts\python.exe build_exe.py
```

---

## ✨ Features

### 1. 🛡️ Automatic Load-Time Safety Backup
- The exact moment you click **"Open Squads"** and load a file, the application **immediately creates a duplicate copy in the exact same folder**:
  ```
  Squads20261023213623126.backup_YYYYMMDD_HHMMSS
  ```
- Your original squad file is always protected against corruptions or accidental edits.

### 2. ⚽ Players Category (with Full Club Mappings & Live Editor Options)
- **Real Club & Roster Association**: Ingests official EA ratings data mapped to the save file's 808 clubs (`lyxL`) and transfer delta (`rIsB`). Superstars and regular players (Mbappé -> Real Madrid, Haaland -> Man City, Rodri -> Man City, Bellingham -> Real Madrid, Messi -> Inter Miami) show their true clubs instead of "Free Agent".
- **⭐ PlayStyles & PlayStyles+ Picker**: Full interactive grid supporting all **34 FC 25 PlayStyles** and **6 Career Traits** with 3 selectable tiers:
  - `None` (0)
  - `Regular (+)` (1)
  - `PlayStyle+ (++)` (2)
  - Quick action presets: *Clear All*, *All Regular (+)*, *All Gold (++)*, *⚡ Meta Superstar Preset*.
  - Real-time bitmask calculation for `trait1`, `trait2`, `icontrait1`, and `icontrait2`.
- **🎯 Roles & FC IQ**: Tactical role assignments (Roles 1–5) matching EA FC 25 tactical engine.
- **Biographical & Secondary Positions**: Primary position plus `preferredposition2`, `preferredposition3`, `preferredposition4`, jersey number, contract expiration year, and retirement status.
- **Physical & Technical Attributes**: Sliders (1–99) and numerical boxes for Pace, Shooting, Passing, Dribbling, Defending, Physicality, Skill Moves (1–5 ★), Weak Foot (1–5 ★), and **⚡ Prime 99 Boost**.
- **Appearance & Accessories**: Kit tuck style, sleeve length, fit style, sock height, boots type, and goalkeeper glove model.
- **Save Player Changes**: Instantly commits updated bitfields to memory.

### 3. 🛡️ Teams Category
- Search and browse all 808 clubs and national teams decoded with proper UTF-8 names.
- Active player rosters, roster count, stadium name, and team ID.
- One-click transfer management.

### 4. 🗄️ Full Database Editor (All 76 Tables)
- Access and edit **everything in the database**:
  - `CZUM` (*playerattributes* — 393 columns, ~27,000 players)
  - `mDGw` (*teams* — 310 columns)
  - `ONtg` (*players* profiles — 63 columns)
  - `kISL` (*teamplayerlinks* lineup rosters — 261 columns)
  - `RrqT` (*editedplayernames* — 17 columns)
  - ...and all remaining 71 tables!
- Paginated table browser with search and filtering.
- **Record Field Inspector**: Click any record to inspect and edit every individual field with type-safe controls.

### 5. 💾 Exact Native File Format Export
- **"Save Squads"**: Overwrites the loaded squads file with updated bitfields.
- **"Save As..."**: Exports to a new file name or directory (e.g. `Documents\FC 25\settings\`).
- Repacks into the **exact native Frostbite container (`FBCHUNKS\x01\x00`)** carrying the valid `DB\x00\x08` FIFA DB v8 payload so the game loads your edited squad natively without error.
