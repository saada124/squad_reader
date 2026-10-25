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
        self.base_players_list: List[int] = []
        self.base_players_records: List[Dict[str, Any]] = []
        self.team_squad_roles: Dict[int, Dict[str, int]] = {}
        self.player_jerseys: Dict[int, int] = {}
        self.user_jerseys: Dict[int, int] = {}

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
                            self.base_players_list.append(pid)
                            self.base_players_records.append(r)
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

        # 4. Ingest player_jerseys.json (authentic kit numbers for 17,737+ real players)
        jerseys_path = None
        for jd in clubs_dirs:
            if jd and os.path.exists(os.path.join(jd, "player_jerseys.json")):
                jerseys_path = os.path.join(jd, "player_jerseys.json")
                break
        if jerseys_path and os.path.exists(jerseys_path):
            try:
                import json
                with open(jerseys_path, "r", encoding="utf-8") as f:
                    j_map = json.load(f)
                for pid_str, num in j_map.items():
                    pid = int(pid_str)
                    num_int = int(num)
                    self.player_jerseys[pid] = num_int
                    if pid in self.players_lookup:
                        self.players_lookup[pid].setdefault("stats", {})["jerseynumber"] = str(num_int)
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

        risb_player_rows: Dict[int, int] = {}
        if risb:
            for r_idx, rec in enumerate(risb.records):
                try:
                    pid = get_bits(rec, 18, 18)
                    if pid > 0:
                        risb_player_rows[pid] = r_idx
                        custom_jersey = get_bits(rec, 36, 7)
                        if 1 <= custom_jersey <= 99:
                            self.player_jerseys[pid] = custom_jersey
                            self.user_jerseys[pid] = custom_jersey
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

            risb_row = risb_player_rows.get(pid)
            czum_row = czum_player_rows.get(pid)
            ovr = pdata["overall"]
            pot = pdata["potential"]
            pos_code = pdata["pos_code"]

            # If present in active squads CZUM and RrqT, read live database values
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

                rrqt = self.db.tables_map.get("RrqT")
                if rrqt and czum_row < len(rrqt.records):
                    db_jersey = get_bits(rrqt.records[czum_row], 23, 7)
                    if 1 <= db_jersey <= 99:
                        self.player_jerseys[pid] = db_jersey
                        pdata.setdefault("stats", {})["jerseynumber"] = str(db_jersey)

            club_name = get_team_name(tid) if tid > 0 else (pdata.get("club") or "Free Agent")
            pos_name = get_position_name(pos_code)
            
            stats = pdata.get("stats", {})
            if "jerseynumber" not in stats or not stats["jerseynumber"]:
                stats["jerseynumber"] = str(self.get_player_jersey_number(pid))
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
                elif attr_key == "jerseynumber":
                    try:
                        self.set_player_jersey_number(player_id, int(new_val))
                    except Exception:
                        pass

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
                        
                # Update team cache counts and rosters
                for t in self.teams_cache:
                    if t["teamid"] == old_team:
                        t["roster"] = list(self.team_rosters.get(old_team, []))
                        t["roster_count"] = len(t["roster"])
                    elif t["teamid"] == new_team_id:
                        t["roster"] = list(self.team_rosters.get(new_team_id, []))
                        t["roster_count"] = len(t["roster"])
                        
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

    def get_team_squad_roles(self, team_id: int) -> Dict[str, int]:
        """Returns active squad roles (captain, penalty, free kicks, corners) for a club."""
        if team_id in self.team_squad_roles:
            return self.team_squad_roles[team_id]
            
        roster = self.team_rosters.get(team_id, [])
        if not roster:
            return {}
            
        # Default roles based on player overall ratings
        sorted_pids = sorted(roster, key=lambda pid: self.players_lookup.get(pid, {}).get("overall", 60), reverse=True)
        roles = {
            "captain": sorted_pids[0],
            "penalty": sorted_pids[0],
            "freekick_short": sorted_pids[1] if len(sorted_pids) > 1 else sorted_pids[0],
            "freekick_long": sorted_pids[2] if len(sorted_pids) > 2 else sorted_pids[0],
            "corner_left": sorted_pids[1] if len(sorted_pids) > 1 else sorted_pids[0],
            "corner_right": sorted_pids[2] if len(sorted_pids) > 2 else sorted_pids[0],
        }
        self.team_squad_roles[team_id] = roles
        return roles

    def set_team_squad_roles(self, team_id: int, roles: Dict[str, int]) -> bool:
        """Saves squad roles for a club."""
        self.team_squad_roles[team_id] = roles
        return True

    def get_player_jersey_number(self, player_id: int) -> int:
        """Returns authentic squad jersey number (1-99) for a player."""
        # 1. User manual runtime edit
        if player_id in self.user_jerseys:
            return self.user_jerseys[player_id]

        # 2. In-memory stats
        if player_id in self.players_lookup:
            stats = self.players_lookup[player_id].get("stats", {})
            try:
                num = int(stats.get("jerseynumber", 0))
                if 1 <= num <= 99:
                    return num
            except Exception:
                pass

        # 3. Verified preset jersey map
        if player_id in self.player_jerseys:
            return self.player_jerseys[player_id]

        # 4. Position-based smart fallback (never pseudo-random modulo)
        pos_code = -1
        if player_id in self.players_lookup:
            pos_code = self.players_lookup[player_id].get("pos_code", -1)
        if pos_code == 0:  # GK
            return 1
        elif pos_code in (2, 3):  # RB / RWB
            return 2
        elif pos_code in (7, 8):  # LB / LWB
            return 3
        elif pos_code in (4, 5, 6):  # CB
            return 4
        elif pos_code in (9, 10, 11):  # CDM
            return 6
        elif pos_code in (12, 23):  # RM / RW
            return 7
        elif pos_code in (13, 14, 15):  # CM
            return 8
        elif pos_code in (20, 21, 24, 25, 26):  # ST / CF
            return 9
        elif pos_code in (17, 18, 19):  # CAM
            return 10
        elif pos_code in (16, 27):  # LM / LW
            return 11
        return 10

    def set_player_jersey_number(self, player_id: int, number: int) -> bool:
        """Sets squad jersey number (1-99) for a player and persists directly into rIsB and RrqT."""
        if not (1 <= number <= 99):
            return False
        self.user_jerseys[player_id] = number
        self.player_jerseys[player_id] = number
        if player_id in self.players_lookup:
            self.players_lookup[player_id].setdefault("stats", {})["jerseynumber"] = str(number)
        for p in self.players_cache:
            if p["playerid"] == player_id:
                p.setdefault("stats", {})["jerseynumber"] = str(number)
                
                # Persist to rIsB (active save delta)
                risb = self.db.tables_map.get("rIsB")
                if risb:
                    r_idx = p.get("risb_row_idx")
                    if r_idx is not None and r_idx < len(risb.records):
                        set_bits(risb.records[r_idx], 36, 7, number)
                    else:
                        target_row = None
                        for idx, rec in enumerate(risb.records):
                            if get_bits(rec, 18, 18) == player_id:
                                target_row = idx
                                break
                        if target_row is not None:
                            set_bits(risb.records[target_row], 36, 7, number)
                            p["risb_row_idx"] = target_row
                        else:
                            for idx, rec in enumerate(risb.records):
                                if get_bits(rec, 18, 18) == 0:
                                    target_row = idx
                                    break
                            if target_row is not None:
                                set_bits(risb.records[target_row], 18, 18, player_id)
                                set_bits(risb.records[target_row], 0, 18, p.get("teamid", 0))
                                set_bits(risb.records[target_row], 36, 7, number)
                                p["risb_row_idx"] = target_row
                            else:
                                new_rec = bytearray(risb.rec_size)
                                set_bits(new_rec, 18, 18, player_id)
                                set_bits(new_rec, 0, 18, p.get("teamid", 0))
                                set_bits(new_rec, 36, 7, number)
                                risb.records.append(new_rec)
                                risb.written_records = len(risb.records)
                                p["risb_row_idx"] = len(risb.records) - 1

                # Also update RrqT if czum_row exists
                r_idx = p.get("czum_row_idx")
                rrqt = self.db.tables_map.get("RrqT")
                if rrqt and r_idx is not None and r_idx < len(rrqt.records):
                    set_bits(rrqt.records[r_idx], 23, 7, number)
                break
        return True

    def update_team_stadium(self, team_id: int, new_stadium_name: str) -> bool:
        """Updates home stadium name for a club in memory and in table kISL."""
        clean_name = new_stadium_name.strip()
        if not clean_name:
            return False
        for t in self.teams_cache:
            if t["teamid"] == team_id:
                t["stadium"] = clean_name
                r_idx = t.get("row_index")
                if r_idx is not None:
                    kisl = self.db.tables_map.get("kISL")
                    if kisl and r_idx < len(kisl.records):
                        self.update_table_cell("kISL", r_idx, "fwCQ", clean_name)
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

    def format_table_row_summary(self, table_sname: str, row_idx: int) -> str:
        """Generates an informative, human-readable summary for a specific table row."""
        tbl = self.get_table(table_sname)
        if not tbl or row_idx >= len(tbl.records):
            return f"Row {row_idx:5d}"
            
        rec = tbl.records[row_idx]

        # 1. Player Attributes & Stats (CZUM)
        if table_sname == "CZUM":
            if row_idx < len(self.base_players_list):
                pid = self.base_players_list[row_idx]
                p = self.players_lookup.get(pid)
                b = self.base_players_records[row_idx] if row_idx < len(self.base_players_records) else {}
                pname = p.get("name") if p else f"Player #{pid}"
                club = p.get("club") if p else "Free Agent"
                ovr = b.get("overallrating") or (p.get("overall") if p else 60)
                pot = b.get("potential") or (p.get("potential") if p else ovr)
                pos = get_position_name(p.get("pos_code", -1)) if p else "N/A"
                return f"Row {row_idx:5d} | [{ovr} OVR / {pot} POT] {pname} ({pos}) — {club} (PID: {pid})"

        # 2. Team Formations & Rosters (lyxL)
        elif table_sname == "lyxL":
            col_tname = tbl.columns_map.get("IOSv")
            tid = int.from_bytes(rec[:2], "little")
            tname = col_tname.decode_value(rec) if col_tname else get_team_name(tid)
            kisl = self.db.tables_map.get("kISL")
            stadium = "Default Stadium"
            if kisl and row_idx < len(kisl.records):
                col_s = kisl.columns_map.get("fwCQ")
                if col_s:
                    stadium = col_s.decode_value(kisl.records[row_idx]).lstrip("_").strip()
            roster_len = len(self.team_rosters.get(tid, []))
            return f"Row {row_idx:5d} | [Club] {tname} (ID: {tid}) — Stadium: {stadium} ({roster_len} players)"

        # 3. Stadium Names & Home Venues (kISL)
        elif table_sname == "kISL":
            col = tbl.columns_map.get("fwCQ")
            sname = col.decode_value(rec).lstrip("_").strip() if col else "Default Stadium"
            lyxl = self.db.tables_map.get("lyxL")
            tname = f"Venue #{row_idx}"
            if lyxl and row_idx < len(lyxl.records):
                col_t = lyxl.columns_map.get("IOSv")
                if col_t:
                    tname = col_t.decode_value(lyxl.records[row_idx])
            return f"Row {row_idx:5d} | [Stadium] {sname} — Home Venue of: {tname} (ID: #{row_idx})"

        # 4. Teams & Club Profiles (mDGw)
        elif table_sname == "mDGw":
            tid = int.from_bytes(rec[:2], "little")
            tname = get_team_name(tid)
            form_col = tbl.columns_map.get("MZIF")
            form_name = form_col.decode_value(rec) if form_col else ""
            if form_name:
                return f"Row {row_idx:5d} | [Club Profile] {tname} (ID: {tid}) — Formation: {form_name}"
            return f"Row {row_idx:5d} | [Club Profile] {tname} (ID: {tid})"

        # 5. Player Biometrics (ONtg)
        elif table_sname == "ONtg":
            col_name = tbl.columns_map.get("KAOA")
            pname = col_name.decode_value(rec) if col_name else f"Model #{row_idx}"
            return f"Row {row_idx:5d} | [Biometrics] {pname} (Row #{row_idx})"

        # 6. Leagues (ijbM)
        elif table_sname == "ijbM":
            lid = tbl.columns[0].decode_value(rec) if tbl.columns else row_idx
            return f"Row {row_idx:5d} | [League] League ID #{lid}"

        # 7. Nations (hCEv)
        elif table_sname == "hCEv":
            col = tbl.columns_map.get("mCXg")
            nid = col.decode_value(rec) if col else row_idx
            return f"Row {row_idx:5d} | [Nation] Nation ID #{nid}"

        # 8. Head Coaches & Managers (Vmkr)
        elif table_sname == "Vmkr":
            col = tbl.columns_map.get("fwCQ")
            mname = col.decode_value(rec) if col else f"Manager #{row_idx}"
            return f"Row {row_idx:5d} | [Manager] {mname} (Row #{row_idx})"

        # Generic fallback for all other tables
        summary_cols = []
        for col in tbl.columns[:4]:
            val = col.decode_value(rec)
            col_name = get_column_display_name(col.sname)
            # Check if this value maps to a known team ID
            if "team" in col_name.lower() and isinstance(val, int) and val in TEAM_NAMES:
                summary_cols.append(f"{col_name}: {TEAM_NAMES[val]} ({val})")
            else:
                summary_cols.append(f"{col_name}: {val}")
        return f"Row {row_idx:5d} | " + " | ".join(summary_cols)

    def get_row_entity_header(self, table_sname: str, row_idx: int) -> Optional[str]:
        """Returns entity context header for the Record Inspector."""
        if table_sname == "CZUM" and row_idx < len(self.base_players_list):
            pid = self.base_players_list[row_idx]
            p = self.players_lookup.get(pid)
            if p:
                pos = get_position_name(p.get("pos_code", -1))
                return f"👤 Player: {p['name']} ({pos}) — {p['club']} (PID: {pid} | {p['overall']} OVR)"
        elif table_sname == "lyxL":
            tbl = self.get_table("lyxL")
            if tbl and row_idx < len(tbl.records):
                rec = tbl.records[row_idx]
                tid = int.from_bytes(rec[:2], "little")
                col_t = tbl.columns_map.get("IOSv")
                tname = col_t.decode_value(rec) if col_t else get_team_name(tid)
                kisl = self.get_table("kISL")
                stadium = "Default Stadium"
                if kisl and row_idx < len(kisl.records):
                    col_s = kisl.columns_map.get("fwCQ")
                    if col_s:
                        stadium = col_s.decode_value(kisl.records[row_idx]).lstrip("_").strip()
                roster_len = len(self.team_rosters.get(tid, []))
                return f"🛡️ Club: {tname} (ID: {tid}) — Venue: {stadium} ({roster_len} players)"
        elif table_sname == "kISL":
            tbl = self.get_table("kISL")
            if tbl and row_idx < len(tbl.records):
                col_s = tbl.columns_map.get("fwCQ")
                sname = col_s.decode_value(tbl.records[row_idx]).lstrip("_").strip() if col_s else "Stadium"
                lyxl = self.get_table("lyxL")
                tname = f"Club #{row_idx}"
                if lyxl and row_idx < len(lyxl.records):
                    col_t = lyxl.columns_map.get("IOSv")
                    if col_t:
                        tname = col_t.decode_value(lyxl.records[row_idx])
                return f"🏟️ Stadium: {sname} — Home Venue of: {tname}"
        elif table_sname == "mDGw":
            tbl = self.get_table("mDGw")
            if tbl and row_idx < len(tbl.records):
                tid = int.from_bytes(tbl.records[row_idx][:2], "little")
                return f"🛡️ Club Profile: {get_team_name(tid)} (ID: {tid})"
        return None
