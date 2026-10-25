import os
import csv
import sys
from typing import Dict, List, Tuple, Any, Optional

try:
    from core.backup import create_load_backup, list_folder_backups
    from core.fbchunks import FBChunksContainer
    from core.db_codec import FIFADatabase, DBTable, DBColumn, get_bits, set_bits
    from core.schema import get_table_display_name, get_column_display_name, get_position_name, get_team_name, TEAM_NAMES, POSITION_NAMES
except ImportError:
    from src.core.backup import create_load_backup, list_folder_backups
    from src.core.fbchunks import FBChunksContainer
    from src.core.db_codec import FIFADatabase, DBTable, DBColumn, get_bits, set_bits
    from src.core.schema import get_table_display_name, get_column_display_name, get_position_name, get_team_name, TEAM_NAMES, POSITION_NAMES

def get_base_dir() -> str:
    """Returns application directory whether running as script or frozen PyInstaller exe."""
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return getattr(sys, "_MEIPASS")
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SquadsSession:
    """
    High-level manager for an active FC 25 Squads save file.
    Coordinates backup creation, container parsing, table manipulation, exact export,
    and metadata indexing with 25,000+ real players and clubs.
    """
    def __init__(self):
        self.filepath: Optional[str] = None
        self.backup_path: Optional[str] = None
        self.container = FBChunksContainer()
        self.db = FIFADatabase()
        self.is_loaded = False
        
        # High-level entity caches
        self.players_lookup: Dict[int, Dict[str, Any]] = {}
        self.players_cache: List[Dict[str, Any]] = []
        self.teams_cache: List[Dict[str, Any]] = []
        self.team_rosters: Dict[int, List[int]] = {}
        self.user_transfers: Dict[int, int] = {}

        # Pre-load player presets from Live Editor database
        self._load_player_presets()

    def _load_player_presets(self):
        """Loads and merges cards.csv and base_players.csv from Live Editor presets."""
        base_dir = get_base_dir()
        
        # Check multiple search locations for player_presets
        search_dirs = [
            os.path.join(getattr(sys, "_MEIPASS", ""), "player_presets"),
            os.path.join(base_dir, "player_presets"),
            os.path.join(base_dir, "FC25LEv25.4.2", "player_presets"),
            os.path.join(os.getcwd(), "FC25LEv25.4.2", "player_presets"),
            os.path.join(os.getcwd(), "player_presets"),
            os.path.join(os.path.dirname(sys.executable), "player_presets"),
            os.path.join(os.path.dirname(sys.executable), "FC25LEv25.4.2", "player_presets"),
        ]
        
        presets_dir = None
        for d in search_dirs:
            if os.path.exists(os.path.join(d, "cards.csv")):
                presets_dir = d
                break
                
        if not presets_dir:
            return

        cards_path = os.path.join(presets_dir, "cards.csv")
        base_path = os.path.join(presets_dir, "base_players.csv")
        
        # 1. Ingest cards.csv (all 26,219 cards with real human names)
        if os.path.exists(cards_path):
            try:
                with open(cards_path, "r", encoding="utf-8") as f:
                    for r in csv.DictReader(f):
                        try:
                            pid = int(r.get("playerid", 0))
                            if pid <= 0: continue
                            # Prefer Normal/base card versions for primary identity
                            if pid not in self.players_lookup or r.get("revision") == "Normal":
                                self.players_lookup[pid] = {
                                    "playerid": pid,
                                    "name": r.get("name", f"Player #{pid}"),
                                    "overall": int(r.get("overallrating", 60)),
                                    "potential": int(r.get("overallrating", 60)),
                                    "pos_code": int(r.get("preferredposition1", -1)),
                                    "weak_foot": int(r.get("weakfootabilitytypecode", 3)),
                                    "skills": int(r.get("skillmoves", 3)),
                                    "height": 182,
                                    "weight": 77,
                                    "foot": "Right",
                                    "teamid": 0,
                                    "club": "Free Agent",
                                    "stats": r
                                }
                        except Exception:
                            continue
            except Exception:
                pass

        # 2. Merge base_players.csv (all 141 physical & technical attributes)
        if os.path.exists(base_path):
            try:
                with open(base_path, "r", encoding="utf-8") as f:
                    for r in csv.DictReader(f):
                        try:
                            pid = int(r.get("playerid", 0))
                            if pid <= 0: continue
                            if pid in self.players_lookup:
                                p = self.players_lookup[pid]
                                p["potential"] = int(r.get("potential", p["overall"]))
                                p["height"] = int(r.get("height", 182))
                                p["weight"] = int(r.get("weight", 77))
                                p["foot"] = "Left" if r.get("preferredfoot") == "1" else "Right"
                                for k, v in r.items():
                                    if k not in p["stats"] or not p["stats"][k]:
                                        p["stats"][k] = v
                            else:
                                name = r.get("commonname") or r.get("surname") or f"Player #{pid}"
                                ovr = int(r.get("overallrating", 60))
                                pot = int(r.get("potential", ovr))
                                pos = int(r.get("preferredposition1", -1))
                                self.players_lookup[pid] = {
                                    "playerid": pid,
                                    "name": name,
                                    "overall": ovr,
                                    "potential": pot,
                                    "pos_code": pos,
                                    "weak_foot": int(r.get("weakfootabilitytypecode", 3)),
                                    "skills": int(r.get("skillmoves", 3)),
                                    "height": int(r.get("height", 182)),
                                    "weight": int(r.get("weight", 77)),
                                    "foot": "Left" if r.get("preferredfoot") == "1" else "Right",
                                    "teamid": 0,
                                    "club": "Free Agent",
                                    "stats": r
                                }
                        except Exception:
                            continue
            except Exception:
                pass

        # 3. Ingest player_clubs.json (real clubs, leagues, nations, and playstyles for 17,737+ players)
        clubs_dirs = [
            presets_dir,
            os.path.join(getattr(sys, "_MEIPASS", ""), "player_presets"),
            os.path.join(base_dir, "player_presets"),
            os.path.join(base_dir, "FC25LEv25.4.2", "player_presets"),
            os.path.join(os.getcwd(), "player_presets"),
            os.path.join(os.getcwd(), "FC25LEv25.4.2", "player_presets"),
        ]
        clubs_path = None
        for cd in clubs_dirs:
            if cd and os.path.exists(os.path.join(cd, "player_clubs.json")):
                clubs_path = os.path.join(cd, "player_clubs.json")
                break
        if clubs_path and os.path.exists(clubs_path):
            try:
                import json
                with open(clubs_path, "r", encoding="utf-8") as f:
                    clubs_map = json.load(f)
                for pid_str, cdata in clubs_map.items():
                    pid = int(pid_str)
                    if pid in self.players_lookup:
                        p = self.players_lookup[pid]
                        tid = cdata.get("teamid", 0)
                        cname = cdata.get("club", "Free Agent")
                        if tid > 0 or cname != "Free Agent":
                            p["teamid"] = tid
                            p["club"] = cname
                        p["league"] = cdata.get("league", "")
                        p["nation_name"] = cdata.get("nation", "")
                        p["alt_positions"] = cdata.get("alt_pos", "")
                        p["playstyles_str"] = cdata.get("playstyles", "")
            except Exception:
                pass

    def load_squads_file(self, filepath: str) -> Tuple[bool, str]:
        """
        Loads a squads file.
        IMPORTANT: Immediately creates a duplicate safety copy in the same directory.
        """
        try:
            # 1. Immediate Safety Duplicate in same directory
            self.backup_path, backup_msg = create_load_backup(filepath)
            
            # 2. Parse Frostbite Container & inner DB
            db_payload = self.container.load(filepath)
            self.db.parse(db_payload)
            self.filepath = filepath
            self.is_loaded = True
            
            # 3. Populate all 808 real team names from table lyxL
            lyxl = self.db.tables_map.get("lyxL")
            if lyxl and "IOSv" in lyxl.columns_map:
                col_tname = lyxl.columns_map["IOSv"]
                for rec in lyxl.records:
                    tid = int.from_bytes(rec[:2], "little")
                    tname = col_tname.decode_value(rec)
                    if tid > 0 and tname:
                        TEAM_NAMES[tid] = tname

            # 4. Index high-level entities
            self._build_indexes()
            
            status = f"Loaded {len(self.db.tables)} tables. {backup_msg}"
            return True, status
        except Exception as e:
            return False, f"Failed to load squads file: {str(e)}"

    def save_squads_file(self, target_filepath: Optional[str] = None) -> Tuple[bool, str]:
        """
        Repacks and exports the current database into the exact native FBCHUNKS format.
        """
        if not self.is_loaded:
            return False, "No squads file loaded."
            
        save_path = target_filepath or self.filepath
        if not save_path:
            return False, "No target filepath specified."
            
        try:
            rebuilt_db = self.db.serialize()
            total_written = self.container.repack(rebuilt_db, save_path)
            self.filepath = save_path
            return True, f"Successfully exported {total_written:,} bytes to: {os.path.basename(save_path)}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def _build_indexes(self):
        """Indexes Players and Teams for rapid search and high-level editing."""
        self.players_cache.clear()
        self.teams_cache.clear()
        self.team_rosters.clear()
        
        # 1. Map team player rosters from rIsB (active save transfer delta)
        risb = self.db.tables_map.get("rIsB")
        czum = self.db.tables_map.get("CZUM")
        
        # 2. Extract Stadium Names from kISL
        # In FIFA/FC 25, record r_idx in kISL maps 1:1 to team record r_idx in lyxL
        stadium_names: Dict[int, str] = {}
        kisl = self.db.tables_map.get("kISL")
        if kisl and "fwCQ" in kisl.columns_map:
            col_sname = kisl.columns_map["fwCQ"]
            for r_idx, rec in enumerate(kisl.records):
                try:
                    sname = col_sname.decode_value(rec)
                    if sname:
                        stadium_names[r_idx] = sname.lstrip("_").strip()
                except Exception:
                    pass

        czum_player_rows: Dict[int, int] = {}
        if czum:
            for r_idx, rec in enumerate(czum.records):
                try:
                    pid = get_bits(rec, 356, 18)
                    if pid > 0:
                        czum_player_rows[pid] = r_idx
                except Exception:
                    pass

        # 3. Build Players Cache
        # Ingest from self.players_lookup (all 25,369 players with real official clubs)
        for pid, pdata in self.players_lookup.items():
            if pid in self.user_transfers:
                tid = self.user_transfers[pid]
                club_name = get_team_name(tid)
            else:
                tid = pdata.get("teamid", 0)
                club_name = pdata.get("club") or (get_team_name(tid) if tid > 0 else "Free Agent")

            # Add to team roster
            if tid > 0:
                if tid not in self.team_rosters:
                    self.team_rosters[tid] = []
                self.team_rosters[tid].append(pid)

            risb_row = None
            czum_row = czum_player_rows.get(pid)
            ovr = pdata["overall"]
            pot = pdata["potential"]
            pos_code = pdata["pos_code"]

            # If present in active squads CZUM, read live database values
            if czum and czum_row is not None and czum_row < len(czum.records):
                rec = czum.records[czum_row]
                db_ovr = get_bits(rec, 877, 7)
                db_pot = get_bits(rec, 159, 7)
                db_pos = get_bits(rec, 441, 7)
                if db_ovr > 0:
                    ovr = db_ovr
                if db_pot > 0:
                    pot = db_pot
                if db_pos >= 0:
                    pos_code = db_pos

            club_name = get_team_name(tid) if tid > 0 else (pdata.get("club") or "Free Agent")
            pos_name = get_position_name(pos_code)
            
            stats = pdata.get("stats", {})
            b_day = 1
            b_mon = 1
            bdate_str = str(stats.get("birthdate", ""))
            if "-" in bdate_str:
                parts = bdate_str.split("-")
                try:
                    if len(parts) >= 3:
                        b_mon = int(parts[1])
                        b_day = int(parts[2])
                except Exception:
                    pass
            
            try:
                nat_id = int(stats.get("nationality", 0))
            except Exception:
                nat_id = 0
                
            try:
                age_val = int(stats.get("age", 25))
            except Exception:
                age_val = 25
                
            try:
                is_ret = int(stats.get("isretiring", 0))
            except Exception:
                is_ret = 0
            
            entry = {
                "playerid": pid,
                "name": pdata["name"],
                "overall": ovr,
                "potential": pot,
                "position": pos_name,
                "pos_code": pos_code,
                "club": club_name,
                "teamid": tid,
                "nationality": nat_id,
                "age": age_val,
                "birth_day": b_day,
                "birth_month": b_mon,
                "isretiring": is_ret,
                "foot": pdata.get("foot", "Right"),
                "skills": pdata.get("skills", 3),
                "weak_foot": pdata.get("weak_foot", 3),
                "height": pdata.get("height", 182),
                "weight": pdata.get("weight", 77),
                "stats": stats,
                "czum_row_idx": czum_row,
                "risb_row_idx": risb_row,
                "row_index": len(self.players_cache),
                "table_sname": "CZUM"
            }
            self.players_cache.append(entry)

        # Sort players by overall rating descending so superstars appear first
        self.players_cache.sort(key=lambda p: (p["overall"], p["potential"]), reverse=True)
        for idx, p in enumerate(self.players_cache):
            p["cache_index"] = idx

        # 4. Build Teams Cache from lyxL (all 808 authentic clubs with real stadiums)
        lyxl = self.db.tables_map.get("lyxL")
        indexed_teams = set()

        if lyxl and "IOSv" in lyxl.columns_map:
            col_tname = lyxl.columns_map["IOSv"]
            for r_idx, rec in enumerate(lyxl.records):
                try:
                    tid = int.from_bytes(rec[:2], "little")
                    tname = col_tname.decode_value(rec)
                    if tid > 0 and tname and tid not in indexed_teams:
                        roster = self.team_rosters.get(tid, [])
                        stadium_name = stadium_names.get(r_idx) or f"{tname} Stadium"
                        self.teams_cache.append({
                            "teamid": tid,
                            "name": tname,
                            "stadium": stadium_name,
                            "roster_count": len(roster),
                            "roster": roster,
                            "table_sname": "lyxL",
                            "row_index": r_idx
                        })
                        indexed_teams.add(tid)
                except Exception:
                    pass

        # Sort teams by roster size (top active teams first) then alphabetically
        self.teams_cache.sort(key=lambda t: (t["roster_count"] > 0, t["roster_count"], t["name"]), reverse=True)

    def update_player_attribute(self, player_id: int, attr_key: str, new_val: Any) -> bool:
        """Updates a player's attribute in memory cache and directly into the active database records."""
        # Synchronize players_lookup
        if player_id in self.players_lookup:
            pl = self.players_lookup[player_id]
            pl.setdefault("stats", {})[attr_key] = str(new_val)
            if attr_key == "overallrating":
                pl["overall"] = int(new_val)
            elif attr_key == "potential":
                pl["potential"] = int(new_val)
            elif attr_key == "skillmoves":
                pl["skills"] = int(new_val)
            elif attr_key == "weakfootabilitytypecode":
                pl["weak_foot"] = int(new_val)
            elif attr_key == "preferredposition1":
                pl["pos_code"] = int(new_val)
            elif attr_key == "teamid":
                pl["teamid"] = int(new_val)
                pl["club"] = get_team_name(int(new_val))

        for p in self.players_cache:
            if p["playerid"] == player_id:
                p["stats"][attr_key] = str(new_val)
                if attr_key == "overallrating":
                    p["overall"] = int(new_val)
                elif attr_key == "potential":
                    p["potential"] = int(new_val)
                elif attr_key == "skillmoves":
                    p["skills"] = int(new_val)
                elif attr_key == "weakfootabilitytypecode":
                    p["weak_foot"] = int(new_val)
                elif attr_key == "preferredposition1":
                    p["pos_code"] = int(new_val)
                    p["position"] = get_position_name(int(new_val))
                elif attr_key == "teamid":
                    p["teamid"] = int(new_val)
                    p["club"] = get_team_name(int(new_val))

                # Write directly to active CZUM database record if present:
                czum_row = p.get("czum_row_idx")
                czum = self.db.tables_map.get("CZUM")
                if czum and czum_row is not None and czum_row < len(czum.records):
                    czum_col_map = {
                        "overallrating": "XjDq",
                        "vision": "ZoOK",
                        "positioning": "aReg",
                        "finishing": "kerE",
                        "crossing": "nmgT",
                        "aggression": "UERs",
                        "interceptions": "dXNv",
                        "standingtackle": "SJKz",
                        "preferredposition1": "NrcP",
                        "preferredposition2": "ypBQ",
                        "preferredposition3": "kqda",
                        "preferredposition4": "aReg",
                        "skillmoves": "iKqs",
                        "weakfootabilitytypecode": "WVsa",
                        "acceleration": "XsFD",
                        "sprintspeed": "HfYD",
                        "shotpower": "CsyD",
                        "longshots": "AGsE",
                        "volleys": "CsBG",
                        "penalties": "xrSG",
                        "freekickaccuracy": "wGOH",
                        "shortpassing": "mpuH",
                        "longpassing": "eYFI",
                        "curve": "YCnI",
                        "agility": "jlQJ",
                        "stamina": "uGEA",
                        "strength": "onGA",
                        "reactions": "HEDC",
                        "composure": "CkYD",
                        "potential": "RRQB",
                        "trait1": "juxV",
                        "icontrait1": "OjQY",
                        "trait2": "vTpl",
                        "icontrait2": "HqUh"
                    }
                    col_sn = czum_col_map.get(attr_key)
                    if col_sn and col_sn in czum.columns_map:
                        try:
                            col = czum.columns_map[col_sn]
                            col.encode_value(czum.records[czum_row], int(new_val))
                        except Exception:
                            pass

                # Update team transfer in rIsB table:
                if attr_key == "teamid":
                    self.transfer_player(player_id, int(new_val))

                return True
        return False

    def transfer_player(self, player_id: int, new_team_id: int) -> bool:
        """Transfers player to a new team in active squad database and updates rosters."""
        self.user_transfers[player_id] = new_team_id
        club_name = get_team_name(new_team_id) if new_team_id > 0 else "Free Agent"
        if player_id in self.players_lookup:
            self.players_lookup[player_id]["teamid"] = new_team_id
            self.players_lookup[player_id]["club"] = club_name

        for p in self.players_cache:
            if p["playerid"] == player_id:
                old_team = p["teamid"]
                p["teamid"] = new_team_id
                p["club"] = club_name
                
                # Update team_rosters
                if old_team in self.team_rosters and player_id in self.team_rosters[old_team]:
                    self.team_rosters[old_team].remove(player_id)
                if new_team_id > 0:
                    if new_team_id not in self.team_rosters:
                        self.team_rosters[new_team_id] = []
                    if player_id not in self.team_rosters[new_team_id]:
                        self.team_rosters[new_team_id].append(player_id)
                        
                # Update team cache counts
                for t in self.teams_cache:
                    if t["teamid"] == old_team:
                        t["roster_count"] = len(self.team_rosters.get(old_team, []))
                    elif t["teamid"] == new_team_id:
                        t["roster_count"] = len(self.team_rosters.get(new_team_id, []))
                        
                # Physically persist into rIsB transfer table
                risb = self.db.tables_map.get("rIsB")
                if risb:
                    risb_row = p.get("risb_row_idx")
                    if risb_row is not None and risb_row < len(risb.records):
                        set_bits(risb.records[risb_row], 0, 18, new_team_id)
                    else:
                        # Find first empty slot in rIsB
                        target_row = None
                        for idx, rec in enumerate(risb.records):
                            if get_bits(rec, 18, 18) == 0:
                                target_row = idx
                                break
                        if target_row is not None:
                            set_bits(risb.records[target_row], 18, 18, player_id)
                            set_bits(risb.records[target_row], 0, 18, new_team_id)
                            p["risb_row_idx"] = target_row
                        else:
                            new_rec = bytearray(risb.rec_size)
                            set_bits(new_rec, 18, 18, player_id)
                            set_bits(new_rec, 0, 18, new_team_id)
                            risb.records.append(new_rec)
                            risb.written_records = len(risb.records)
                            p["risb_row_idx"] = len(risb.records) - 1
                return True
        return False

    def update_table_cell(self, sname: str, row_idx: int, col_sname: str, new_val: Any) -> bool:
        """Directly writes a value into any column of any record in the active database."""
        tbl = self.db.tables_map.get(sname)
        if not tbl or row_idx >= len(tbl.records):
            return False
            
        col = tbl.columns_map.get(col_sname)
        if not col:
            return False
            
        try:
            col.encode_value(tbl.records[row_idx], new_val)
            return True
        except Exception:
            return False

    def clone_table_row(self, sname: str, row_idx: int) -> bool:
        """Clones an existing row in a database table."""
        tbl = self.db.tables_map.get(sname)
        if not tbl or row_idx >= len(tbl.records):
            return False
        cloned = bytearray(tbl.records[row_idx])
        tbl.records.append(cloned)
        tbl.written_records = len(tbl.records)
        return True

    def delete_table_row(self, sname: str, row_idx: int) -> bool:
        """Deletes a row from a database table."""
        tbl = self.db.tables_map.get(sname)
        if not tbl or row_idx >= len(tbl.records):
            return False
        del tbl.records[row_idx]
        tbl.written_records = len(tbl.records)
        return True

    def add_table_row(self, sname: str) -> bool:
        """Adds a new blank row into a database table."""
        tbl = self.db.tables_map.get(sname)
        if not tbl:
            return False
        new_row = bytearray(tbl.rec_size)
        tbl.records.append(new_row)
        tbl.written_records = len(tbl.records)
        return True

    def get_table_names_list(self) -> List[Tuple[str, str, int]]:
        """Returns list of (sname, display_name, record_count) for all 76 tables."""
        res = []
        for tbl in self.db.tables:
            disp = get_table_display_name(tbl.sname)
            res.append((tbl.sname, disp, len(tbl.records)))
        return res

    def get_table(self, sname: str) -> Optional[DBTable]:
        return self.db.tables_map.get(sname)
