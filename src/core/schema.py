"""
Schema mapping for FIFA DB v8 tables, columns, positions, and teams.
Maps 4-character shortnames to human-readable names and categories matching FC 25 Live Editor.
"""

TABLE_NAMES = {
    "CZUM": "Player Attributes & Stats",
    "RrqT": "Edited Player Names & Commentary",
    "mDGw": "Teams & Club Profiles",
    "lyxL": "Team Formations & Rosters",
    "ONtg": "Player Biometrics & Models",
    "kISL": "Stadium Names & Home Venues",
    "sloG": "Stadium Geometry & Lighting",
    "DFeB": "Team-Stadium Assignments",
    "SPTx": "PlayStyles & Gameplay Perks",
    "AGmV": "Player Contracts & Financials",
    "ijbM": "Leagues & Domestic Divisions",
    "hCEv": "Nations & International Federations",
    "vGSz": "Nationalities & Country Codes",
    "GdtI": "League-Team Tournament Links",
    "qdZF": "Default Team Sheets & Lineups",
    "onMQ": "Match Tactics & Instructions",
    "Vmkr": "Head Coaches & Managers",
    "GiKo": "Global Transfer Network Scouts",
    "zFhW": "Career Manager Profile",
    "xgkO": "Match Officials & Referees",
    "ubBA": "Club Rivalries & Derbies",
    "qsGz": "Youth Academy Prospects",
    "eqXx": "Transfer History & Records",
    "dMwM": "Player Cards & Tiers",
    "bqIi": "Competitions & Cup Tournaments",
    "bneD": "Season Calendar & Fixtures",
    "YNEf": "Team Captains & Set-Piece Roles",
    "VZEn": "Match Weather & Climate Conditions",
    "RMfq": "Boots & Footwear Catalog",
    "QqjW": "Team Kits & Jersey Designs",
    "GPlh": "Special Player Traits",
    "ySyc": "Gameplay Match Settings",
    "yYtg": "Club Board Expectations & Goals",
    "yAGl": "League Standings & Table Points",
    "uxUO": "Player Form & Sharpness",
    "qmil": "Youth Academy Infrastructure",
    "nQVU": "Player Loans & Agreements",
    "nVuT": "Transfer Market Restrictions & Bans",
    "ZrAO": "Manager Salary & Compensation",
    "YOKt": "Career Mode User Profiles",
    "VHaB": "Stadium Seating & Stands",
    "Qxjv": "Goalpost Nets & Styling",
    "CxJp": "Trophies & Silverware Showcase",
    "zIOu": "Sponsorships & Commercial Partners",
    "nhky": "Match Balls & Ball Models",
    "mMQM": "Custom Tactical Presets",
    "brHl": "News Feed Articles & Media",
    "Zeam": "Career Inbox & Notifications",
    "UlaA": "End-of-Season Awards & Accolades",
    "QMqB": "Season Statistics & Records",
    "MsTi": "In-Game Match Events",
    "Knen": "Advanced Player Performance Metrics",
    "ImNE": "Tournament Group Stage Tables",
    "HeDf": "Player Physical Injuries & Status",
    "Hrbq": "Player Potential Growth Engine",
    "FMpz": "Player Morale & Squad Happiness",
    "AqBt": "Squad Chemistry Links & Synergy",
    "nrFl": "Player 3D Face & Head Assets",
    "nhXl": "Squad Shirt Numbers",
    "kgGh": "Calculated Overall Ratings",
    "fMpR": "Commentator Call Names",
    "fGwQ": "Home Crowd Chants & Atmosphere",
    "YBgI": "Pitchside Advertising Boards",
    "WFUF": "Club Banners & Ultras Flags",
    "TKgq": "Manager Wardrobe & Outfits",
    "SWFH": "Trainer Prompts & Gameplay Hints",
    "SizI": "Goal Net Colors & Mesh Types",
    "PViY": "User Gameplay Preferences",
    "OIcD": "Stadium Audio Acoustics",
    "LbKk": "Custom Training Balls",
    "IePu": "Goalkeeper Glove Models",
    "DbIl": "Special Matchday Events",
    "xuka": "Season Fixture Calendar",
    "tfLS": "Tactical Substitutions",
    "rIsB": "Squad Delta & Transfer Links",
    "esAj": "Global Engine Database Constants",
}

TABLE_CATEGORIES = {
    # 👥 Players & Attributes
    "CZUM": "👥 Players & Attributes",
    "RrqT": "👥 Players & Attributes",
    "ONtg": "👥 Players & Attributes",
    "SPTx": "👥 Players & Attributes",
    "AGmV": "👥 Players & Attributes",
    "dMwM": "👥 Players & Attributes",
    "GPlh": "👥 Players & Attributes",
    "uxUO": "👥 Players & Attributes",
    "nrFl": "👥 Players & Attributes",
    "nhXl": "👥 Players & Attributes",
    "kgGh": "👥 Players & Attributes",
    "HeDf": "👥 Players & Attributes",
    "Hrbq": "👥 Players & Attributes",
    "FMpz": "👥 Players & Attributes",
    "qsGz": "👥 Players & Attributes",
    "qmil": "👥 Players & Attributes",
    "nQVU": "👥 Players & Attributes",

    # 🛡️ Teams & Rosters
    "mDGw": "🛡️ Teams & Rosters",
    "lyxL": "🛡️ Teams & Rosters",
    "qdZF": "🛡️ Teams & Rosters",
    "onMQ": "🛡️ Teams & Rosters",
    "ubBA": "🛡️ Teams & Rosters",
    "YNEf": "🛡️ Teams & Rosters",
    "QqjW": "🛡️ Teams & Rosters",
    "mMQM": "🛡️ Teams & Rosters",
    "tfLS": "🛡️ Teams & Rosters",
    "AqBt": "🛡️ Teams & Rosters",
    "DFeB": "🛡️ Teams & Rosters",

    # 🏟️ Stadiums & Venues
    "kISL": "🏟️ Stadiums & Venues",
    "sloG": "🏟️ Stadiums & Venues",
    "VHaB": "🏟️ Stadiums & Venues",
    "Qxjv": "🏟️ Stadiums & Venues",
    "SizI": "🏟️ Stadiums & Venues",
    "OIcD": "🏟️ Stadiums & Venues",
    "YBgI": "🏟️ Stadiums & Venues",
    "WFUF": "🏟️ Stadiums & Venues",
    "fGwQ": "🏟️ Stadiums & Venues",

    # 🏆 Competitions & Leagues
    "ijbM": "🏆 Competitions & Leagues",
    "bqIi": "🏆 Competitions & Leagues",
    "GdtI": "🏆 Competitions & Leagues",
    "yAGl": "🏆 Competitions & Leagues",
    "ImNE": "🏆 Competitions & Leagues",
    "CxJp": "🏆 Competitions & Leagues",
    "bneD": "🏆 Competitions & Leagues",
    "xuka": "🏆 Competitions & Leagues",
    "QMqB": "🏆 Competitions & Leagues",
    "UlaA": "🏆 Competitions & Leagues",

    # 🌍 Nations & Geography
    "hCEv": "🌍 Nations & Geography",
    "vGSz": "🌍 Nations & Geography",

    # 👔 Managers & Staff
    "Vmkr": "👔 Managers & Staff",
    "zFhW": "👔 Managers & Staff",
    "ZrAO": "👔 Managers & Staff",
    "TKgq": "👔 Managers & Staff",
    "GiKo": "👔 Managers & Staff",

    # ⚽ Matchday & Equipment
    "nhky": "⚽ Matchday & Equipment",
    "RMfq": "⚽ Matchday & Equipment",
    "IePu": "⚽ Matchday & Equipment",
    "LbKk": "⚽ Matchday & Equipment",
    "VZEn": "⚽ Matchday & Equipment",
    "ySyc": "⚽ Matchday & Equipment",
    "DbIl": "⚽ Matchday & Equipment",
    "MsTi": "⚽ Matchday & Equipment",
    "xgkO": "⚽ Matchday & Equipment",
    "fMpR": "⚽ Matchday & Equipment",

    # ⚙️ Engine, Rules & System
    "YOKt": "⚙️ Engine, Rules & System",
    "yYtg": "⚙️ Engine, Rules & System",
    "zIOu": "⚙️ Engine, Rules & System",
    "brHl": "⚙️ Engine, Rules & System",
    "Zeam": "⚙️ Engine, Rules & System",
    "Knen": "⚙️ Engine, Rules & System",
    "SWFH": "⚙️ Engine, Rules & System",
    "PViY": "⚙️ Engine, Rules & System",
    "nVuT": "⚙️ Engine, Rules & System",
    "eqXx": "⚙️ Engine, Rules & System",
    "rIsB": "⚙️ Engine, Rules & System",
    "esAj": "⚙️ Engine, Rules & System",
}

CATEGORY_LIST = [
    "📁 All Categories (76 tables)",
    "👥 Players & Attributes (17 tables)",
    "🛡️ Teams & Rosters (11 tables)",
    "🏟️ Stadiums & Venues (9 tables)",
    "🏆 Competitions & Leagues (10 tables)",
    "🌍 Nations & Geography (2 tables)",
    "👔 Managers & Staff (5 tables)",
    "⚽ Matchday & Equipment (10 tables)",
    "⚙️ Engine, Rules & System (12 tables)"
]

TABLE_SAFETY_CONFIG = {
    # 🟢 SAFE TABLES
    "CZUM": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Player attributes & skills. Safe to edit ratings directly."},
    "RrqT": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Custom names & commentary links. Safe to customize."},
    "kISL": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Stadium and home venue names. Safe to edit text."},
    "QqjW": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Team kits, colors, and jersey styles. Safe to customize."},
    "SPTx": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "PlayStyles and gameplay perks. Safe to edit."},
    "RMfq": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Boots catalog and player footwear assignments. Safe to edit."},
    "fMpR": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Commentator audio call names. Safe to edit."},
    "nhky": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Match ball models and textures. Safe to edit."},
    "fGwQ": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Crowd chants and stadium audio atmosphere. Safe to edit."},
    "YBgI": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Pitchside sponsor boards. Safe to customize."},
    "WFUF": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Club ultras banners and stadium flags. Safe to edit."},
    "dMwM": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Player cards and tier borders. Safe to customize."},
    "qsGz": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Youth academy prospects and potential. Safe to edit."},
    "ONtg": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Player body biometrics (height, weight, body type). Safe to edit."},
    "nhXl": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Squad shirt jersey numbers. Safe to customize."},
    "HeDf": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Player physical injuries and recovery days. Safe to edit."},
    "uxUO": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Match sharpness and player form. Safe to edit."},
    "FMpz": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Squad happiness and morale. Safe to edit."},
    "IePu": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Goalkeeper glove models. Safe to edit."},
    "LbKk": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Training pitch balls. Safe to edit."},
    "VZEn": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Match weather conditions and climate. Safe to edit."},
    "xgkO": {"level": "SAFE", "badge": "🟢 SAFE", "desc": "Referee and match official profiles. Safe to edit."},

    # 🔴 HIGH RISK TABLES
    "rIsB": {"level": "DANGEROUS", "badge": "🔴 HIGH RISK", "desc": "Squad delta and raw memory pointers. Modifying can corrupt superstar clubs or crash saves!"},
    "esAj": {"level": "DANGEROUS", "badge": "🔴 HIGH RISK", "desc": "Global EA FC engine constants. Modifying can cause immediate game crashes on launch!"},
    "sloG": {"level": "DANGEROUS", "badge": "🔴 HIGH RISK", "desc": "Stadium 3D geometry coordinates. Modifying raw vertex offsets may distort 3D models."},
    "AqBt": {"level": "DANGEROUS", "badge": "🔴 HIGH RISK", "desc": "Engine chemistry links and memory hashes. Modifying can cause engine crashes."},
    "SizI": {"level": "DANGEROUS", "badge": "🔴 HIGH RISK", "desc": "Goalpost 3D net mesh vertex arrays. Modifying can cause graphics glitches."},
    "Knen": {"level": "DANGEROUS", "badge": "🔴 HIGH RISK", "desc": "Advanced engine telemetry metrics. High-risk internal references."},
}

def get_table_display_name(sname: str) -> str:
    """Returns human-readable table name or shortname."""
    return TABLE_NAMES.get(sname, f"Table_{sname}")

def get_table_category(sname: str) -> str:
    """Returns human-readable category for a table."""
    return TABLE_CATEGORIES.get(sname, "⚙️ Engine, Rules & System")

def get_table_safety_info(sname: str) -> dict:
    """Returns safety level, badge, and description for a table."""
    if sname in TABLE_SAFETY_CONFIG:
        return TABLE_SAFETY_CONFIG[sname]
    return {
        "level": "CAUTION",
        "badge": "🟡 CAUTION",
        "desc": f"Relational table '{get_table_display_name(sname)}'. Modifying row values requires valid foreign key references."
    }

def is_column_id_or_key(table_sname: str, col_sname: str) -> bool:
    """Detects if a column is a primary key, foreign key, or critical pointer."""
    # Special known ID columns in EA FC
    if col_sname in ("eyGK", "GFLI", "wDHM", "mCXg", "ykFq", "OblE", "JMld", "vjla", "jIcz", "WLKn", "STID", "eqId", "idFG", "IDgE", "zoID", "nKiD", "MUiD", "eIDC", "TIDs"):
        return True
    name = COLUMN_NAMES.get(col_sname, col_sname).lower()
    return any(k in name for k in ["id", "code", "team", "player", "nation", "league", "stadium", "manager", "captain"])

def get_column_safety_warning(table_sname: str, col_sname: str, col_type: int, bit_size: int) -> str:
    """Returns a safety warning message for a specific column if applicable."""
    if is_column_id_or_key(table_sname, col_sname):
        return "⚠️ Primary Key / ID: Modifying this ID breaks relationships across other tables and may corrupt save files!"
    if bit_size > 32:
        return "⚠️ Large Bitmask / Binary Blob: Modifying raw bits directly may cause engine instability."
    if col_type == 3 and bit_size == 1:
        return "ℹ️ Flag / Boolean Field: 0 = Disabled, 1 = Enabled."
    return ""

def validate_column_value(col_type: int, bit_size: int, val: any) -> tuple:
    """Validates user input value against column type and bit width. Returns (is_valid, error_msg)."""
    if col_type == 0:  # String
        return True, ""
    if col_type == 4:  # Float
        try:
            float(val)
            return True, ""
        except Exception:
            return False, f"Must be a valid floating-point number (got '{val}')"
    # Integer / Bitfield
    try:
        ival = int(val)
    except Exception:
        return False, f"Must be a valid integer number (got '{val}')"
    if ival < 0:
        return False, f"Negative numbers ({ival}) not supported in unsigned bitfields"
    max_val = (1 << bit_size) - 1
    if ival > max_val:
        return False, f"Value {ival:,} exceeds maximum allowed {max_val:,} for {bit_size}-bit field! Value would corrupt adjacent columns."
    return True, ""

POSITION_NAMES = {
    -1: "None",
    0: "GK",
    1: "SW",
    2: "RWB",
    3: "RB",
    4: "RCB",
    5: "CB",
    6: "LCB",
    7: "LB",
    8: "LWB",
    9: "RDM",
    10: "CDM",
    11: "LDM",
    12: "RM",
    13: "RCM",
    14: "CM",
    15: "LCM",
    16: "LM",
    17: "RAM",
    18: "CAM",
    19: "LAM",
    20: "RF",
    21: "CF",
    22: "LF",
    23: "RW",
    24: "RS",
    25: "ST",
    26: "LS",
    27: "LW",
}

def get_position_name(pos_code: int) -> str:
    return POSITION_NAMES.get(pos_code, f"POS_{pos_code}")

# Top EA Sports FC Club Names mapping
TEAM_NAMES = {
    1: "Arsenal",
    2: "Aston Villa",
    3: "Blackburn Rovers",
    4: "Bolton Wanderers",
    5: "Chelsea",
    7: "Everton",
    8: "Fulham",
    9: "Leeds United",
    10: "Liverpool",
    11: "Manchester United",
    12: "Middlesbrough",
    13: "Newcastle United",
    14: "Manchester City",
    15: "Southampton",
    17: "Nottingham Forest",
    18: "Tottenham Hotspur",
    19: "West Ham United",
    21: "Bayern München",
    22: "Borussia Dortmund",
    23: "Borussia Mönchengladbach",
    24: "Eintracht Frankfurt",
    28: "Hamburger SV",
    29: "Hertha BSC",
    31: "1. FC Köln",
    32: "Bayer 04 Leverkusen",
    34: "FC Schalke 04",
    36: "VfB Stuttgart",
    38: "SV Werder Bremen",
    44: "Juventus",
    45: "Inter",
    46: "Lazio",
    47: "AC Milan",
    48: "Napoli",
    52: "AS Roma",
    54: "Fiorentina",
    55: "Atalanta",
    59: "Bologna",
    65: "Torino",
    70: "Bordeaux",
    71: "Olympique Lyonnais",
    72: "Olympique de Marseille",
    73: "Paris Saint-Germain",
    74: "AS Monaco",
    75: "LOSC Lille",
    76: "Stade Rennais",
    79: "FC Nantes",
    81: "OGC Nice",
    85: "RC Lens",
    166: "Ajax",
    178: "Feyenoord",
    189: "PSV Eindhoven",
    234: "FC Porto",
    236: "SL Benfica",
    237: "Sporting CP",
    240: "Atlético de Madrid",
    241: "FC Barcelona",
    242: "Real Betis",
    243: "Real Madrid",
    244: "Real Sociedad",
    248: "Valencia CF",
    250: "Villarreal CF",
    252: "Athletic Club",
    260: "Sevilla FC",
    280: "Celtic",
    282: "Rangers",
    310: "Dinamo Zagreb",
    325: "Galatasaray",
    326: "Fenerbahçe",
    327: "Beşiktaş",
    695: "Al Hilal",
    698: "Al Nassr",
    111099: "Al Ittihad",
    112260: "Al Ahli",
    112658: "Inter Miami CF",
    1369: "Argentina",
    1370: "Brazil",
    1318: "England",
    1335: "France",
    1337: "Germany",
    1343: "Italy",
    1357: "Netherlands",
    1360: "Portugal",
    1362: "Spain"
}

def get_team_name(team_id: int) -> str:
    return TEAM_NAMES.get(team_id, f"Team #{team_id}")

# Common column name mappings for key tables
COLUMN_NAMES = {
    # Players / Player Attributes
    "XjDq": "overallrating",
    "ZoOK": "vision",
    "aReg": "positioning",
    "kerE": "finishing",
    "nmgT": "crossing",
    "UERs": "aggression",
    "dXNv": "interceptions",
    "kqda": "interceptions_alt",
    "SJKz": "standingtackle",
    "NrcP": "preferredposition1",
    "wDHM": "playerid",
    "iKqs": "skillmoves",
    "WVsa": "weakfoot",
    "WMtm": "stadiumname",
    "eyGK": "playerid",
    "GFLI": "playerid_alt",
    "OblE": "captainid",
    "jLuE": "skillmoves_alt",
    "KpQF": "weakfootabilitytypecode",
    "YFaA": "overallrating_legacy",
    "RRQB": "potential",
    "XsFD": "acceleration",
    "HfYD": "sprintspeed",
    "CsyD": "shotpower",
    "AGsE": "longshots",
    "CsBG": "volleys",
    "xrSG": "penalties",
    "PqtG": "positioning_legacy",
    "wWzG": "vision_legacy",
    "nbJH": "crossing_legacy",
    "wGOH": "freekickaccuracy",
    "mpuH": "shortpassing",
    "eYFI": "longpassing",
    "YCnI": "curve",
    "jlQJ": "agility",
    "vJjJ": "balance",
    "nJjJ": "jumping",
    "uGEA": "stamina",
    "onGA": "strength",
    "HEDC": "reactions",
    "oQQC": "aggression_legacy",
    "CkYD": "composure",
    "KAOA": "playername",
    "mCXg": "teamid",
    "JMld": "firstnameid",
    "vjla": "lastnameid",
    "jIcz": "playername",
    "fwCQ": "stadiumname",
    "JFiY": "jerseynumber",
    "dGNm": "position",
    "DmlS": "stadium_data",
    "LGsF": "teamname",
    "ykFq": "playerid",
    "CEZz": "team_formation_data",
}

def get_column_display_name(c_sname: str) -> str:
    return COLUMN_NAMES.get(c_sname, c_sname)
