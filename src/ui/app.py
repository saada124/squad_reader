import os
import sys
import tkinter as tk
from tkinter import filedialog
from typing import Optional, Dict, Any, List

import dearpygui.dearpygui as dpg

try:
    from model.squads_db import SquadsSession
    from core.schema import get_table_display_name, get_column_display_name, get_position_name, get_team_name, POSITION_NAMES, TEAM_NAMES
    from core.backup import list_folder_backups
    from core.playstyles import PLAYSTYLE_CATEGORIES, PLAYSTYLE_MAP, decode_player_playstyles, encode_player_playstyles, get_active_playstyles_summary
except ImportError:
    from src.model.squads_db import SquadsSession
    from src.core.schema import get_table_display_name, get_column_display_name, get_position_name, get_team_name, POSITION_NAMES, TEAM_NAMES
    from src.core.backup import list_folder_backups
    from src.core.playstyles import PLAYSTYLE_CATEGORIES, PLAYSTYLE_MAP, decode_player_playstyles, encode_player_playstyles, get_active_playstyles_summary

class SquadEditorApp:
    def __init__(self):
        self.session = SquadsSession()
        self.selected_player: Optional[Dict[str, Any]] = None
        self.selected_team: Optional[Dict[str, Any]] = None
        self.selected_table_sname: str = "CZUM"
        self.current_table_page: int = 0
        self.page_size: int = 50
        self.selected_record_index: Optional[int] = None
        
        # Filtered lists & Presets
        self.filtered_players: List[Dict[str, Any]] = []
        self.filtered_teams: List[Dict[str, Any]] = []
        self.filter_preset: str = "🌟 All Players"
        self.preset_filter_names = [
            "🌟 All Players",
            "🆓 Free Agents",
            "⚡ Top Superstars (85+)",
            "💎 Wonderkids (POT 85+, Age <= 21)",
            "🇦🇷 Messi Regen",
            "🇵🇹 CR7 Regen",
            "🇫🇷 Benzema Regen",
            "🇵🇱 RL9 Regen",
            "⏳ Retiring Players",
            "🧬 Generated Players"
        ]
        self.filter_pos_category: str = "All"
        self.min_ovr_filter: int = 0

    def run(self):
        dpg.create_context()
        self._setup_theme()
        
        dpg.create_viewport(title="FC 25 Squad Editor v1.0.0 - Full Database & Squad Studio", width=1320, height=860, min_width=1050, min_height=720)
        self._build_ui()
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

    def _setup_theme(self):
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                # Dark slate palette matching Live Editor
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (24, 25, 29, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (30, 32, 38, 255))
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (32, 34, 42, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (50, 54, 65, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (40, 43, 52, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (55, 60, 72, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (65, 72, 88, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (35, 38, 48, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Header, (45, 52, 68, 255))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (58, 68, 90, 255))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (0, 122, 204, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 55, 75, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 75, 105, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 122, 204, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Tab, (32, 35, 44, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (55, 65, 85, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, (0, 122, 204, 255))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (0, 150, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (50, 180, 255, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
        dpg.bind_theme(global_theme)

    def _build_ui(self):
        with dpg.window(tag="primary_window", no_title_bar=True, no_move=True, no_resize=True):
            # Top Control & Status Header
            with dpg.group(horizontal=True):
                dpg.add_text("⚡ FC 25 SQUAD STUDIO", color=(0, 200, 255))
                dpg.add_text("|", color=(100, 100, 100))
                dpg.add_button(label="📁 Open Squads", callback=self._on_click_open)
                dpg.add_button(label="💾 Save Squads", callback=self._on_click_save)
                dpg.add_button(label="💾 Save As...", callback=self._on_click_save_as)
                dpg.add_spacer(width=20)
                dpg.add_text("Ready. Please open a Squads save file.", tag="status_text", color=(180, 180, 180))

            dpg.add_separator()

            # Main Navigation Tabs
            with dpg.tab_bar(tag="main_tab_bar"):
                # TAB 1: PLAYERS
                with dpg.tab(label=" ⚽ Players "):
                    self._build_players_tab()

                # TAB 2: TEAMS
                with dpg.tab(label=" 🛡️ Teams & Clubs "):
                    self._build_teams_tab()

                # TAB 3: FULL DATABASE EDITOR (ALL 76 TABLES)
                with dpg.tab(label=" 🗄️ Database Tables (All 76) "):
                    self._build_database_tab()

                # TAB 4: SAFETY BACKUPS & INFO
                with dpg.tab(label=" ⚙️ Settings & Backups "):
                    self._build_settings_tab()

        dpg.set_primary_window("primary_window", True)

    def _build_players_tab(self):
        with dpg.group(horizontal=True):
            # Left Column: Player Search & Filtering Pane
            with dpg.child_window(width=420):
                dpg.add_text("Search & Filter Players", color=(0, 180, 240))
                
                # Preset Filter Combo
                with dpg.group(horizontal=True):
                    dpg.add_text("Filter:")
                    dpg.add_combo(items=self.preset_filter_names, default_value="🌟 All Players", callback=self._on_change_preset_filter, tag="player_preset_combo", width=340)
                
                # Search Bar with Instant Filter & Clear
                with dpg.group(horizontal=True):
                    dpg.add_input_text(hint="Search player name or ID...", callback=self._on_filter_players, tag="player_search_input", width=350)
                    dpg.add_button(label="✖", callback=self._on_clear_player_search, width=30)
                    
                # Position Category & Min Rating Sliders
                with dpg.group(horizontal=True):
                    dpg.add_text("Pos:")
                    dpg.add_combo(items=["All", "Attackers", "Midfielders", "Defenders", "Goalkeepers"], default_value="All", callback=self._on_change_pos_filter, tag="player_pos_combo", width=140)
                    dpg.add_text("Min OVR:")
                    dpg.add_slider_int(min_value=0, max_value=95, default_value=0, callback=self._on_change_min_ovr, tag="player_min_ovr_slider", width=120)

                dpg.add_separator()
                dpg.add_text("Total Players: 0", tag="player_count_label", color=(150, 150, 150))
                dpg.add_listbox(items=[], num_items=25, tag="players_listbox", callback=self._on_select_player, width=400)

            # Right Column: Player Attribute Inspector & Full Editor
            with dpg.child_window():
                # Color-Coded Header Card
                with dpg.group(horizontal=True):
                    dpg.add_text("[ -- ]", tag="player_badge_ovr", color=(0, 255, 120))
                    dpg.add_text("Select a player from the list to view and edit details.", tag="player_header_name", color=(240, 240, 240))
                dpg.add_text("No player selected", tag="player_sub_header", color=(160, 160, 160))
                dpg.add_separator()

                with dpg.group(tag="player_edit_controls", show=False):
                    with dpg.tab_bar():
                        # TAB 1: CORE BIO, RATINGS, POSITIONS & CLUB
                        with dpg.tab(label=" 📋 Bio & Positions "):
                            dpg.add_spacer(height=5)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Overall Rating:   ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_ovr", width=220)
                                dpg.add_spacer(width=20)
                                dpg.add_text("Potential Rating: ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_pot", width=220)

                            with dpg.group(horizontal=True):
                                dpg.add_text("Club Transfer:    ")
                                dpg.add_combo(items=[], tag="edit_player_club_combo", width=240)
                                dpg.add_button(label="🔄 Transfer Club", callback=self._on_transfer_player, width=130)

                            dpg.add_spacer(height=5)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Player ID:        ")
                                dpg.add_input_int(tag="edit_player_id_display", width=140, readonly=True)
                                dpg.add_spacer(width=20)
                                dpg.add_text("Age: ")
                                dpg.add_input_int(tag="edit_player_age_display", width=80)
                                dpg.add_spacer(width=20)
                                dpg.add_text("Jersey #: ")
                                dpg.add_input_int(tag="edit_player_jersey", width=80)
                                dpg.add_spacer(width=20)
                                dpg.add_checkbox(label="Retiring", tag="edit_player_isretiring")

                            with dpg.group(horizontal=True):
                                dpg.add_text("Preferred Foot:   ")
                                dpg.add_combo(items=["Right", "Left"], default_value="Right", tag="edit_player_foot", width=140)
                                dpg.add_spacer(width=20)
                                dpg.add_text("Primary Position: ")
                                pos_items = [POSITION_NAMES[k] for k in sorted(POSITION_NAMES.keys()) if k >= 0]
                                pos_items_with_none = ["None"] + pos_items
                                dpg.add_combo(items=pos_items, tag="edit_player_pos1", width=140)

                            with dpg.group(horizontal=True):
                                dpg.add_text("Alt Position 1:   ")
                                dpg.add_combo(items=pos_items_with_none, tag="edit_player_pos2", width=140)
                                dpg.add_spacer(width=20)
                                dpg.add_text("Alt Position 2:   ")
                                dpg.add_combo(items=pos_items_with_none, tag="edit_player_pos3", width=140)

                            with dpg.group(horizontal=True):
                                dpg.add_text("Alt Position 3:   ")
                                dpg.add_combo(items=pos_items_with_none, tag="edit_player_pos4", width=140)
                                dpg.add_spacer(width=20)
                                dpg.add_text("Contract Valid:   ")
                                dpg.add_input_int(tag="edit_player_contract", width=140)

                            with dpg.group(horizontal=True):
                                dpg.add_text("Skill Moves (★):  ")
                                dpg.add_slider_int(min_value=1, max_value=5, tag="edit_player_skills", width=180)
                                dpg.add_spacer(width=60)
                                dpg.add_text("Weak Foot (★):    ")
                                dpg.add_slider_int(min_value=1, max_value=5, tag="edit_player_weakfoot", width=180)

                            with dpg.group(horizontal=True):
                                dpg.add_text("Height (cm):      ")
                                dpg.add_input_int(tag="edit_player_height", width=140)
                                dpg.add_spacer(width=100)
                                dpg.add_text("Weight (kg):      ")
                                dpg.add_input_int(tag="edit_player_weight", width=140)

                        # TAB 2: ⭐ PLAYSTYLES & TRAITS SELECTOR (AUTHENTIC FC 25 ENGINE)
                        with dpg.tab(label=" ⭐ PlayStyles & Traits "):
                            dpg.add_spacer(height=5)
                            with dpg.group(horizontal=True):
                                dpg.add_text("⭐ Authentic FC 25 PlayStyles Engine", color=(0, 220, 255))
                                dpg.add_spacer(width=30)
                                dpg.add_text("Active: 0 Gold (++), 0 Silver (+)", tag="player_playstyles_summary_badge", color=(0, 255, 120))

                            dpg.add_text("Pick any of the 34 authentic FC 25 PlayStyles & career traits. Choose None, Regular (+ Silver), or PlayStyle+ (++ Gold Icon).", color=(180, 180, 180))
                            dpg.add_spacer(height=3)

                            # Quick Preset Action Buttons
                            with dpg.group(horizontal=True):
                                dpg.add_button(label="✨ Clear All", callback=self._on_clear_playstyles, width=110)
                                dpg.add_button(label="🥈 All Regular (+)", callback=self._on_all_silver_playstyles, width=130)
                                dpg.add_button(label="🥇 All Gold (++)", callback=self._on_all_gold_playstyles, width=130)
                                dpg.add_button(label="⚡ Meta Superstar Preset", callback=self._on_meta_playstyles, width=170)

                            dpg.add_spacer(height=5)
                            dpg.add_separator()

                            # Scrollable PlayStyles Matrix
                            with dpg.child_window(height=360):
                                for cat_name, ps_items in PLAYSTYLE_CATEGORIES.items():
                                    dpg.add_spacer(height=4)
                                    dpg.add_text(cat_name, color=(0, 210, 255))
                                    dpg.add_separator()
                                    for key, name, group, bit, desc in ps_items:
                                        with dpg.group(horizontal=True):
                                            dpg.add_text(f"{name:18s}", color=(240, 240, 240))
                                            dpg.add_radio_button(
                                                items=["None", "(+) Regular", "(++) PlayStyle+"],
                                                default_value="None",
                                                horizontal=True,
                                                tag=f"ps_radio_{key}",
                                                callback=self._on_update_playstyles_summary
                                            )
                                            dpg.add_spacer(width=10)
                                            dpg.add_text(f"- {desc}", color=(130, 130, 130))

                        # TAB 3: 🎯 ROLES & FC IQ
                        with dpg.tab(label=" 🎯 Roles & FC IQ "):
                            dpg.add_spacer(height=5)
                            dpg.add_text("FC IQ Tactical Roles (New EA SPORTS FC 25 Engine)", color=(0, 220, 255))
                            dpg.add_text("Define player role assignments and role proficiency levels (+ and ++).", color=(180, 180, 180))
                            dpg.add_spacer(height=5)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Tactical Role 1: ")
                                dpg.add_slider_int(min_value=0, max_value=255, tag="edit_player_role1", width=200)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Tactical Role 2: ")
                                dpg.add_slider_int(min_value=0, max_value=255, tag="edit_player_role2", width=200)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Tactical Role 3: ")
                                dpg.add_slider_int(min_value=0, max_value=255, tag="edit_player_role3", width=200)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Tactical Role 4: ")
                                dpg.add_slider_int(min_value=0, max_value=255, tag="edit_player_role4", width=200)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Tactical Role 5: ")
                                dpg.add_slider_int(min_value=0, max_value=255, tag="edit_player_role5", width=200)

                        # TAB 4: PACE & SHOOTING
                        with dpg.tab(label=" Pace & Shooting "):
                            dpg.add_spacer(height=5)
                            dpg.add_text("Pace Attributes", color=(0, 200, 255))
                            with dpg.group(horizontal=True):
                                dpg.add_text("Acceleration:    ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_accel", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Sprint Speed:    ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_sprint", width=220)

                            dpg.add_spacer(height=10)
                            dpg.add_text("Shooting Attributes", color=(0, 200, 255))
                            with dpg.group(horizontal=True):
                                dpg.add_text("Positioning:     ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_pos", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Finishing:       ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_finish", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Shot Power:      ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_shotpwr", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Long Shots:      ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_longshots", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Volleys:         ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_volleys", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Penalties:       ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_penalties", width=220)

                        # TAB 5: PASSING & DRIBBLING
                        with dpg.tab(label=" Passing & Dribbling "):
                            dpg.add_spacer(height=5)
                            dpg.add_text("Passing Attributes", color=(0, 200, 255))
                            with dpg.group(horizontal=True):
                                dpg.add_text("Vision:          ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_vision", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Crossing:        ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_crossing", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Free Kick Acc.:  ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_fk", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Short Passing:   ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_shortpass", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Long Passing:    ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_longpass", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Curve:           ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_curve", width=220)

                            dpg.add_spacer(height=10)
                            dpg.add_text("Dribbling Attributes", color=(0, 200, 255))
                            with dpg.group(horizontal=True):
                                dpg.add_text("Agility:         ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_agility", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Balance:         ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_balance", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Reactions:       ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_reactions", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Ball Control:    ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_ballctrl", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Dribbling:       ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_dribble", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Composure:       ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_composure", width=220)

                        # TAB 6: DEFENDING & PHYSICAL
                        with dpg.tab(label=" Defending & Physical "):
                            dpg.add_spacer(height=5)
                            dpg.add_text("Defending Attributes", color=(0, 200, 255))
                            with dpg.group(horizontal=True):
                                dpg.add_text("Interceptions:   ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_interceptions", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Heading Acc.:    ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_heading", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Def. Awareness:  ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_defawareness", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Standing Tackle: ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_standtackle", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Sliding Tackle:  ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_slidetackle", width=220)

                            dpg.add_spacer(height=10)
                            dpg.add_text("Physical Attributes", color=(0, 200, 255))
                            with dpg.group(horizontal=True):
                                dpg.add_text("Jumping:         ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_jumping", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Stamina:         ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_stamina", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Strength:        ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_strength", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Aggression:      ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_aggression", width=220)

                        # TAB 7: GOALKEEPER
                        with dpg.tab(label=" Goalkeeper "):
                            dpg.add_spacer(height=5)
                            dpg.add_text("Goalkeeper Attributes", color=(0, 200, 255))
                            with dpg.group(horizontal=True):
                                dpg.add_text("GK Diving:       ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_gkdiving", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("GK Handling:     ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_gkhandling", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("GK Kicking:      ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_gkkicking", width=220)
                                dpg.add_spacer(width=30)
                                dpg.add_text("GK Reflexes:     ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_gkreflexes", width=220)
                            with dpg.group(horizontal=True):
                                dpg.add_text("GK Positioning:  ")
                                dpg.add_slider_int(min_value=1, max_value=99, tag="edit_player_gkpos", width=220)

                        # TAB 8: KIT & APPEARANCE (ALL ORIGINAL OPTIONS)
                        with dpg.tab(label=" 👔 Kit & Appearance "):
                            dpg.add_spacer(height=5)
                            dpg.add_text("Player Head & Body Model", color=(0, 200, 255))
                            with dpg.group(horizontal=True):
                                dpg.add_text("Head Asset ID:   ")
                                dpg.add_input_int(tag="edit_player_headasset", width=160)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Body Type:       ")
                                dpg.add_input_int(tag="edit_player_bodytype", width=120)

                            with dpg.group(horizontal=True):
                                dpg.add_text("Hairstyle Code:  ")
                                dpg.add_input_int(tag="edit_player_hairstyle", width=160)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Hair Color:      ")
                                dpg.add_input_int(tag="edit_player_haircolor", width=120)

                            with dpg.group(horizontal=True):
                                dpg.add_text("Skin Tone Code:  ")
                                dpg.add_input_int(tag="edit_player_skintone", width=160)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Eye Color:       ")
                                dpg.add_input_int(tag="edit_player_eyecolor", width=120)

                            dpg.add_spacer(height=10)
                            dpg.add_text("Kit & Accessory Options", color=(0, 200, 255))
                            with dpg.group(horizontal=True):
                                dpg.add_text("Jersey Style:    ")
                                dpg.add_combo(items=["Tucked", "Untucked"], default_value="Untucked", tag="edit_player_jerseystyle", width=160)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Sleeves:         ")
                                dpg.add_combo(items=["Short", "Long"], default_value="Short", tag="edit_player_sleeves", width=120)

                            with dpg.group(horizontal=True):
                                dpg.add_text("Jersey Fit:      ")
                                dpg.add_combo(items=["Normal", "Tight"], default_value="Normal", tag="edit_player_fit", width=160)
                                dpg.add_spacer(width=30)
                                dpg.add_text("Sock Length:     ")
                                dpg.add_combo(items=["Short", "Average", "High"], default_value="Average", tag="edit_player_socklength", width=120)

                            with dpg.group(horizontal=True):
                                dpg.add_text("Shoe Type Code:  ")
                                dpg.add_input_int(tag="edit_player_shoetype", width=160)
                                dpg.add_spacer(width=30)
                                dpg.add_text("GK Glove Code:   ")
                                dpg.add_input_int(tag="edit_player_gkglove", width=120)

                            dpg.add_spacer(height=10)
                            dpg.add_text("Direct Bitmask Monitors (Synced with PlayStyles Tab)", color=(0, 200, 255))
                            with dpg.group(horizontal=True):
                                dpg.add_text("Trait 1:   ")
                                dpg.add_input_text(tag="edit_player_trait1", width=140)
                                dpg.add_spacer(width=15)
                                dpg.add_text("Trait 2:   ")
                                dpg.add_input_text(tag="edit_player_trait2", width=140)
                            with dpg.group(horizontal=True):
                                dpg.add_text("IconTrait1:")
                                dpg.add_input_text(tag="edit_player_icontrait1", width=140)
                                dpg.add_spacer(width=15)
                                dpg.add_text("IconTrait2:")
                                dpg.add_input_text(tag="edit_player_icontrait2", width=140)

                    dpg.add_spacer(height=15)
                    dpg.add_separator()
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="💾 Apply Player Changes", callback=self._on_save_player_changes, width=220)
                        dpg.add_button(label="⚡ Prime 99 Boost", callback=self._on_boost_player, width=160)
                        dpg.add_text("", tag="player_save_feedback", color=(0, 255, 120))

    def _build_teams_tab(self):
        with dpg.group(horizontal=True):
            # Left Column: Teams List Pane
            with dpg.child_window(width=410):
                dpg.add_text("Search Clubs & Teams", color=(0, 180, 240))
                dpg.add_input_text(hint="Search club name or ID...", callback=self._on_filter_teams, tag="team_search_input", width=390)
                dpg.add_separator()
                dpg.add_text("Total Clubs: 0", tag="team_count_label", color=(150, 150, 150))
                dpg.add_listbox(items=[], num_items=28, tag="teams_listbox", callback=self._on_select_team, width=390)

            # Right Column: Team Inspector & Roster
            with dpg.child_window():
                dpg.add_text("Club Inspector", color=(0, 180, 240))
                dpg.add_text("Select a team to view information and squad roster.", tag="team_selected_header", color=(200, 200, 200))
                dpg.add_separator()

                with dpg.group(tag="team_edit_controls", show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Team ID:      ")
                        dpg.add_input_int(tag="edit_team_id", width=140, readonly=True)
                        dpg.add_spacer(width=20)
                        dpg.add_text("Team Name:    ")
                        dpg.add_input_text(tag="edit_team_name", width=260)

                    with dpg.group(horizontal=True):
                        dpg.add_text("🏟️ Stadium:    ")
                        dpg.add_input_text(tag="edit_team_stadium", width=420, readonly=True)

                    dpg.add_spacer(height=10)
                    dpg.add_text("Squad Roster", color=(0, 200, 255))
                    dpg.add_listbox(items=[], num_items=16, tag="team_roster_listbox", width=580)

                    dpg.add_spacer(height=15)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="💾 Apply Team Changes", callback=self._on_save_team_changes, width=180)
                        dpg.add_text("", tag="team_save_feedback", color=(0, 255, 120))

    def _build_database_tab(self):
        with dpg.group():
            with dpg.group(horizontal=True):
                dpg.add_text("Select Table:")
                dpg.add_combo(items=[], tag="db_table_selector", callback=self._on_change_db_table, width=420)
                dpg.add_spacer(width=10)
                dpg.add_button(label="➕ Add Row", callback=self._on_add_row, width=95)
                dpg.add_button(label="📋 Clone Row", callback=self._on_clone_row, width=105)
                dpg.add_button(label="🗑️ Delete Row", callback=self._on_delete_row, width=105)

            dpg.add_spacer(height=5)
            dpg.add_text("Rows: 0 | Columns: 0 | Record Size: 0 bytes", tag="db_table_stats_text", color=(180, 180, 180))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                # Left Pane: Records Grid & Pagination
                with dpg.child_window(width=520):
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="◀ Prev", callback=self._on_prev_page)
                        dpg.add_text("Page 1 of 1", tag="db_pagination_text")
                        dpg.add_button(label="Next ▶", callback=self._on_next_page)
                        dpg.add_spacer(width=20)
                        dpg.add_input_text(hint="Filter rows...", callback=self._on_filter_records, tag="db_record_search_input", width=180)

                    dpg.add_listbox(items=[], num_items=26, tag="db_records_listbox", callback=self._on_select_record, width=500)

                # Right Pane: Detailed Record Column Field Inspector
                with dpg.child_window():
                    dpg.add_text("Record Column Inspector (All Fields)", color=(0, 180, 240))
                    dpg.add_text("Select a row from the left to view and edit column values.", tag="record_inspector_header", color=(200, 200, 200))
                    dpg.add_separator()
                    
                    with dpg.child_window(height=520, tag="record_fields_container"):
                        pass
                        
                    dpg.add_spacer(height=10)
                    with dpg.group(horizontal=True, tag="record_actions_group", show=False):
                        dpg.add_button(label="💾 Save Record Changes", callback=self._on_save_record_changes, width=220)
                        dpg.add_text("", tag="record_save_feedback", color=(0, 255, 120))

    def _build_settings_tab(self):
        with dpg.child_window():
            dpg.add_text("File, Safety & Export Settings", color=(0, 180, 240))
            dpg.add_separator()
            dpg.add_text("Currently Loaded Squads File:")
            dpg.add_text("None", tag="settings_active_file", color=(255, 200, 0))
            dpg.add_spacer(height=10)
            dpg.add_text("Immediate Safety Backup Created in Same Folder:")
            dpg.add_text("None", tag="settings_backup_file", color=(0, 255, 150))
            dpg.add_spacer(height=15)
            dpg.add_text("All Existing Backups in Save Folder:", color=(180, 180, 180))
            dpg.add_listbox(items=[], num_items=8, tag="settings_backups_listbox", width=700)
            dpg.add_spacer(height=20)
            dpg.add_separator()
            dpg.add_text("EA SPORTS FC 25 Database Specifications:")
            dpg.add_text("• Container: Frostbite Engine FBCHUNKS v1 (250-byte chunk header with native GUID).")
            dpg.add_text("• Core Relational Database: FIFA DB v8 (magic 'DB\\x00\\x08', 76 bit-packed relational tables).")
            dpg.add_text("• 100% In-Game Guarantee: Round-trip exports bit-for-byte exact schema for full career/kickoff mode compatibility.")

    # --- File & Session Handlers ---

    def _on_click_open(self):
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Open EA SPORTS FC 25 Squads File",
            filetypes=[("Squads File", "*.*"), ("All Files", "*.*")]
        )
        root.destroy()
        if not path:
            return

        success, msg = self.session.load_squads_file(path)
        if success:
            dpg.set_value("status_text", f"Loaded: {os.path.basename(path)}")
            dpg.set_value("settings_active_file", path)
            dpg.set_value("settings_backup_file", self.session.backup_path or "Created")
            self._update_backups_list()
            self._load_players_list()
            self._load_teams_list()
            self._load_database_tables_dropdown()
            self._populate_club_combo()
        else:
            dpg.set_value("status_text", f"Error: {msg}")

    def _on_click_save(self):
        if not self.session.is_loaded:
            dpg.set_value("status_text", "Error: No squads file loaded.")
            return
        success, msg = self.session.save_squads_file()
        dpg.set_value("status_text", msg)

    def _on_click_save_as(self):
        if not self.session.is_loaded:
            dpg.set_value("status_text", "Error: No squads file loaded.")
            return
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        target = filedialog.asksaveasfilename(
            title="Save EA SPORTS FC 25 Squads File As",
            initialfile=os.path.basename(self.session.filepath or "Squads_Custom"),
            filetypes=[("Squads File", "*.*"), ("All Files", "*.*")]
        )
        root.destroy()
        if not target:
            return
        success, msg = self.session.save_squads_file(target)
        dpg.set_value("status_text", msg)

    def _update_backups_list(self):
        if self.session.filepath:
            folder = os.path.dirname(self.session.filepath)
            backups = list_folder_backups(folder)
            items = [f"{b['filename']} ({b['size_bytes']:,} bytes) - {b['timestamp']}" for b in backups]
            dpg.configure_item("settings_backups_listbox", items=items)

    def _populate_club_combo(self):
        club_items = ["Free Agent"]
        for t in self.session.teams_cache:
            if t["teamid"] > 0:
                club_items.append(f"{t['name']} (ID {t['teamid']})")
        if dpg.does_item_exist("edit_player_club_combo"):
            dpg.configure_item("edit_player_club_combo", items=club_items)

    # --- Players UI Callbacks ---

    def _load_players_list(self):
        self._on_filter_players()

    def _on_change_preset_filter(self, sender, app_data):
        self.filter_preset = app_data
        self._on_filter_players()

    def _on_filter_players(self):
        search_txt = ""
        if dpg.does_item_exist("player_search_input"):
            search_txt = (dpg.get_value("player_search_input") or "").lower().strip()
        pos_cat = self.filter_pos_category
        min_ovr = self.min_ovr_filter
        preset = self.filter_preset

        filtered = []
        for p in self.session.players_cache:
            if min_ovr > 0 and p["overall"] < min_ovr:
                continue

            # Presets copied from Live Editor filters/players
            if "Free Agents" in preset:
                if p["teamid"] not in (0, 111592):
                    continue
            elif "Superstars" in preset:
                if p["overall"] < 85:
                    continue
            elif "Wonderkids" in preset:
                if p["potential"] < 85 or p.get("age", 25) > 21:
                    continue
            elif "Messi Regen" in preset:
                # RW, Nat 52 (Argentina), Potential >= 89, or generated
                if not (p["pos_code"] == 23 and p.get("nationality") == 52 and p["potential"] >= 89):
                    continue
            elif "CR7 Regen" in preset:
                # ST, Nat 38 (Portugal), Potential >= 85, or generated
                if not (p["pos_code"] == 25 and p.get("nationality") == 38 and p["potential"] >= 85):
                    continue
            elif "Benzema Regen" in preset:
                # ST, Nat 18 (France), Potential >= 85
                if not (p["pos_code"] == 25 and p.get("nationality") == 18 and p["potential"] >= 85):
                    continue
            elif "RL9 Regen" in preset:
                # ST, Nat 37 (Poland), Potential >= 85
                if not (p["pos_code"] == 25 and p.get("nationality") == 37 and p["potential"] >= 85):
                    continue
            elif "Retiring" in preset:
                if p.get("isretiring", 0) != 1 and p.get("age", 25) < 35:
                    continue
            elif "Generated" in preset:
                if p["playerid"] < 460000:
                    continue

            # Position filtering
            pos = p["position"]
            if pos_cat == "Attackers" and pos not in ("ST", "RW", "LW", "CF", "RF", "LF", "RS", "LS"):
                continue
            elif pos_cat == "Midfielders" and pos not in ("CAM", "CM", "CDM", "LM", "RM", "RCM", "LCM", "RDM", "LDM", "RAM", "LAM"):
                continue
            elif pos_cat == "Defenders" and pos not in ("CB", "LB", "RB", "LWB", "RWB", "RCB", "LCB", "SW"):
                continue
            elif pos_cat == "Goalkeepers" and pos != "GK":
                continue

            # Search text matching: name or ID
            if search_txt:
                name_match = search_txt in p["name"].lower()
                id_match = search_txt in str(p["playerid"])
                club_match = search_txt in p["club"].lower()
                if not (name_match or id_match or club_match):
                    continue

            filtered.append(p)

        self.filtered_players = filtered
        items = [f"[{p['overall']}] {p['name']} ({p['position']}) - {p['club']}" for p in self.filtered_players]
        if dpg.does_item_exist("players_listbox"):
            dpg.configure_item("players_listbox", items=items)
        if dpg.does_item_exist("player_count_label"):
            dpg.set_value("player_count_label", f"Total Players: {len(self.filtered_players):,} matches")

    def _on_clear_player_search(self):
        dpg.set_value("player_search_input", "")
        self.filter_pos_category = "All"
        self.min_ovr_filter = 0
        self.filter_preset = "🌟 All Players"
        dpg.set_value("player_preset_combo", "🌟 All Players")
        dpg.set_value("player_pos_combo", "All")
        dpg.set_value("player_min_ovr_slider", 0)
        self._on_filter_players()

    def _on_change_pos_filter(self, sender, app_data):
        self.filter_pos_category = app_data
        self._on_filter_players()

    def _on_change_min_ovr(self, sender, app_data):
        self.min_ovr_filter = app_data
        self._on_filter_players()

    def _on_update_playstyles_summary(self):
        gold_count = 0
        silver_count = 0
        states = {}
        for key in PLAYSTYLE_MAP:
            tag = f"ps_radio_{key}"
            if dpg.does_item_exist(tag):
                val = dpg.get_value(tag)
                if "(++)" in val:
                    gold_count += 1
                    states[key] = 2
                elif "(+)" in val:
                    silver_count += 1
                    states[key] = 1
                else:
                    states[key] = 0
        if dpg.does_item_exist("player_playstyles_summary_badge"):
            dpg.set_value("player_playstyles_summary_badge", f"Active: {gold_count} Gold (++), {silver_count} Silver (+)")
            
        # Update raw bitmask monitors
        t1, t2, it1, it2 = encode_player_playstyles(states)
        if dpg.does_item_exist("edit_player_trait1"):
            dpg.set_value("edit_player_trait1", str(t1))
        if dpg.does_item_exist("edit_player_trait2"):
            dpg.set_value("edit_player_trait2", str(t2))
        if dpg.does_item_exist("edit_player_icontrait1"):
            dpg.set_value("edit_player_icontrait1", str(it1))
        if dpg.does_item_exist("edit_player_icontrait2"):
            dpg.set_value("edit_player_icontrait2", str(it2))

    def _on_clear_playstyles(self):
        for key in PLAYSTYLE_MAP:
            tag = f"ps_radio_{key}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, "None")
        self._on_update_playstyles_summary()

    def _on_all_silver_playstyles(self):
        for key in PLAYSTYLE_MAP:
            tag = f"ps_radio_{key}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, "(+) Regular")
        self._on_update_playstyles_summary()

    def _on_all_gold_playstyles(self):
        for key in PLAYSTYLE_MAP:
            tag = f"ps_radio_{key}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, "(++) PlayStyle+")
        self._on_update_playstyles_summary()

    def _on_meta_playstyles(self):
        meta_gold = ["finesse_shot", "quick_step", "anticipate", "technical", "relentless", "incisive_pass"]
        for key in PLAYSTYLE_MAP:
            tag = f"ps_radio_{key}"
            if dpg.does_item_exist(tag):
                if key in meta_gold:
                    dpg.set_value(tag, "(++) PlayStyle+")
                else:
                    dpg.set_value(tag, "(+) Regular")
        self._on_update_playstyles_summary()

    def _on_select_player(self, sender, app_data):
        items = dpg.get_item_configuration("players_listbox")["items"]
        if not items or app_data not in items:
            return
        idx = items.index(app_data)
        if idx >= len(self.filtered_players):
            return

        p = self.filtered_players[idx]
        self.selected_player = p

        # Set color-coded badge
        ovr = p["overall"]
        badge_color = (0, 255, 120) if ovr >= 80 else (120, 255, 80) if ovr >= 70 else (255, 220, 0) if ovr >= 60 else (255, 140, 0) if ovr >= 50 else (255, 50, 50)
        dpg.set_value("player_badge_ovr", f"[ {ovr:2d} ]")
        dpg.configure_item("player_badge_ovr", color=badge_color)

        dpg.set_value("player_header_name", f"{p['name']} (ID: {p['playerid']})")
        dpg.set_value("player_sub_header", f"Club: {p['club']}  |  Position: {p['position']}  |  Foot: {p.get('foot', 'Right')}  |  Skills: {p.get('skills', 3)}★  |  Weak Foot: {p.get('weak_foot', 3)}★")

        stats = p.get("stats", {})
        
        # Populate sliders and fields
        dpg.set_value("edit_player_ovr", ovr)
        dpg.set_value("edit_player_pot", p.get("potential", ovr))
        dpg.set_value("edit_player_id_display", p["playerid"])
        dpg.set_value("edit_player_age_display", p.get("age", 25))
        
        # Club dropdown with all authentic 808 teams
        club_items = ["Free Agent"] + [f"{t['name']} (ID {t['teamid']})" for t in self.session.teams_cache if t['teamid'] > 0]
        dpg.configure_item("edit_player_club_combo", items=club_items)
        club_display = "Free Agent" if p["teamid"] == 0 else f"{p['club']} (ID {p['teamid']})"
        dpg.set_value("edit_player_club_combo", club_display)
        
        dpg.set_value("edit_player_foot", p.get("foot", "Right"))
        if p["position"] in POSITION_NAMES.values():
            dpg.set_value("edit_player_pos1", p["position"])
            
        def _get_pos_name_safe(p_code):
            try:
                code_int = int(p_code)
                return POSITION_NAMES.get(code_int, "None")
            except Exception:
                return "None"

        dpg.set_value("edit_player_pos2", _get_pos_name_safe(stats.get("preferredposition2", -1)))
        dpg.set_value("edit_player_pos3", _get_pos_name_safe(stats.get("preferredposition3", -1)))
        dpg.set_value("edit_player_pos4", _get_pos_name_safe(stats.get("preferredposition4", -1)))

        try:
            jersey_num = int(stats.get("jerseynumber", stats.get("playerjerseynameid", 10)))
        except Exception:
            jersey_num = 10
        dpg.set_value("edit_player_jersey", jersey_num)
        
        try:
            contract_yr = int(stats.get("contractvaliduntil", 2028))
        except Exception:
            contract_yr = 2028
        dpg.set_value("edit_player_contract", contract_yr)
        dpg.set_value("edit_player_isretiring", bool(p.get("isretiring", 0)))

        dpg.set_value("edit_player_skills", int(stats.get("skillmoves", p.get("skills", 3))))
        dpg.set_value("edit_player_weakfoot", int(stats.get("weakfootabilitytypecode", p.get("weak_foot", 3))))
        dpg.set_value("edit_player_height", int(stats.get("height", p.get("height", 182))))
        dpg.set_value("edit_player_weight", int(stats.get("weight", p.get("weight", 77))))

        # Decode and set PlayStyles & Traits
        try:
            t1 = int(stats.get("trait1", 0))
        except Exception:
            t1 = 0
        try:
            t2 = int(stats.get("trait2", 0))
        except Exception:
            t2 = 0
        try:
            it1 = int(stats.get("icontrait1", 0))
        except Exception:
            it1 = 0
        try:
            it2 = int(stats.get("icontrait2", 0))
        except Exception:
            it2 = 0

        ps_states = decode_player_playstyles(t1, t2, it1, it2)
        for key in PLAYSTYLE_MAP:
            tag = f"ps_radio_{key}"
            if dpg.does_item_exist(tag):
                st = ps_states.get(key, 0)
                val_str = "None" if st == 0 else "(+) Regular" if st == 1 else "(++) PlayStyle+"
                dpg.set_value(tag, val_str)
        self._on_update_playstyles_summary()

        # Roles & FC IQ
        dpg.set_value("edit_player_role1", int(stats.get("role1", 0)))
        dpg.set_value("edit_player_role2", int(stats.get("role2", 0)))
        dpg.set_value("edit_player_role3", int(stats.get("role3", 0)))
        dpg.set_value("edit_player_role4", int(stats.get("role4", 0)))
        dpg.set_value("edit_player_role5", int(stats.get("role5", 0)))

        # Pace & Shooting
        dpg.set_value("edit_player_accel", int(stats.get("acceleration", 70)))
        dpg.set_value("edit_player_sprint", int(stats.get("sprintspeed", 70)))
        dpg.set_value("edit_player_pos", int(stats.get("positioning", 70)))
        dpg.set_value("edit_player_finish", int(stats.get("finishing", 70)))
        dpg.set_value("edit_player_shotpwr", int(stats.get("shotpower", 70)))
        dpg.set_value("edit_player_longshots", int(stats.get("longshots", 70)))
        dpg.set_value("edit_player_volleys", int(stats.get("volleys", 70)))
        dpg.set_value("edit_player_penalties", int(stats.get("penalties", 70)))

        # Passing & Dribbling
        dpg.set_value("edit_player_vision", int(stats.get("vision", 70)))
        dpg.set_value("edit_player_crossing", int(stats.get("crossing", 70)))
        dpg.set_value("edit_player_fk", int(stats.get("freekickaccuracy", 70)))
        dpg.set_value("edit_player_shortpass", int(stats.get("shortpassing", 70)))
        dpg.set_value("edit_player_longpass", int(stats.get("longpassing", 70)))
        dpg.set_value("edit_player_curve", int(stats.get("curve", 70)))
        dpg.set_value("edit_player_agility", int(stats.get("agility", 70)))
        dpg.set_value("edit_player_balance", int(stats.get("balance", 70)))
        dpg.set_value("edit_player_reactions", int(stats.get("reactions", 70)))
        dpg.set_value("edit_player_ballctrl", int(stats.get("ballcontrol", 70)))
        dpg.set_value("edit_player_dribble", int(stats.get("dribbling", 70)))
        dpg.set_value("edit_player_composure", int(stats.get("composure", 70)))

        # Defending & Physical
        dpg.set_value("edit_player_interceptions", int(stats.get("interceptions", 60)))
        dpg.set_value("edit_player_heading", int(stats.get("headingaccuracy", 60)))
        dpg.set_value("edit_player_defawareness", int(stats.get("defensiveawareness", 60)))
        dpg.set_value("edit_player_standtackle", int(stats.get("standingtackle", 60)))
        dpg.set_value("edit_player_slidetackle", int(stats.get("slidingtackle", 60)))
        dpg.set_value("edit_player_jumping", int(stats.get("jumping", 70)))
        dpg.set_value("edit_player_stamina", int(stats.get("stamina", 70)))
        dpg.set_value("edit_player_strength", int(stats.get("strength", 70)))
        dpg.set_value("edit_player_aggression", int(stats.get("aggression", 65)))

        # Goalkeeper
        dpg.set_value("edit_player_gkdiving", int(stats.get("gkdiving", 10)))
        dpg.set_value("edit_player_gkhandling", int(stats.get("gkhandling", 10)))
        dpg.set_value("edit_player_gkkicking", int(stats.get("gkkicking", 10)))
        dpg.set_value("edit_player_gkreflexes", int(stats.get("gkreflexes", 10)))
        dpg.set_value("edit_player_gkpos", int(stats.get("gkpositioning", 10)))

        # Appearance & Kit options
        dpg.set_value("edit_player_headasset", int(stats.get("headassetid", 0)))
        dpg.set_value("edit_player_bodytype", int(stats.get("bodytypecode", 0)))
        dpg.set_value("edit_player_hairstyle", int(stats.get("hairstylecode", 0)))
        dpg.set_value("edit_player_haircolor", int(stats.get("haircolorcode", 0)))
        dpg.set_value("edit_player_skintone", int(stats.get("skintonecode", 0)))
        dpg.set_value("edit_player_eyecolor", int(stats.get("eyecolorcode", 0)))
        dpg.set_value("edit_player_jerseystyle", "Untucked" if stats.get("jerseystylecode") == "1" else "Tucked")
        dpg.set_value("edit_player_sleeves", "Long" if stats.get("jerseysleevelengthcode") == "1" else "Short")
        dpg.set_value("edit_player_fit", "Tight" if stats.get("jerseyfit") == "1" else "Normal")
        dpg.set_value("edit_player_socklength", "Short" if stats.get("socklengthcode") == "1" else "High" if stats.get("socklengthcode") == "2" else "Average")
        dpg.set_value("edit_player_shoetype", int(stats.get("shoetypecode", 0)))
        dpg.set_value("edit_player_gkglove", int(stats.get("gkglovetypecode", 0)))

        dpg.configure_item("player_edit_controls", show=True)
        dpg.set_value("player_save_feedback", "")

    def _on_transfer_player(self):
        if not self.selected_player:
            return
        combo_val = dpg.get_value("edit_player_club_combo") or ""
        target_tid = 0
        if "ID" in combo_val:
            try:
                target_tid = int(combo_val.split("ID")[-1].replace(")", "").strip())
            except Exception:
                target_tid = 0
                
        pid = self.selected_player["playerid"]
        self.session.transfer_player(pid, target_tid)
        club_name = get_team_name(target_tid) if target_tid > 0 else "Free Agent"
        self.selected_player["club"] = club_name
        self.selected_player["teamid"] = target_tid
        
        dpg.set_value("player_sub_header", f"Club: {club_name}  |  Position: {self.selected_player['position']}  |  Foot: {self.selected_player.get('foot', 'Right')}")
        dpg.set_value("player_save_feedback", f"✓ Transferred player to {club_name}!")
        self._on_filter_players()
        self._on_filter_teams()

    def _on_save_player_changes(self):
        if not self.selected_player:
            return
        pid = self.selected_player["playerid"]
        stats = self.selected_player.get("stats", {})
        
        # 1. Read core attributes
        ovr = dpg.get_value("edit_player_ovr")
        pot = dpg.get_value("edit_player_pot")
        skills = dpg.get_value("edit_player_skills")
        wf = dpg.get_value("edit_player_weakfoot")
        height = dpg.get_value("edit_player_height")
        weight = dpg.get_value("edit_player_weight")
        
        self.session.update_player_attribute(pid, "overallrating", ovr)
        self.session.update_player_attribute(pid, "potential", pot)
        self.session.update_player_attribute(pid, "skillmoves", skills)
        self.session.update_player_attribute(pid, "weakfootabilitytypecode", wf)
        self.session.update_player_attribute(pid, "height", height)
        self.session.update_player_attribute(pid, "weight", weight)

        # 2. Collect and Encode all 34 PlayStyles & Traits
        ps_states = {}
        for key in PLAYSTYLE_MAP:
            tag = f"ps_radio_{key}"
            if dpg.does_item_exist(tag):
                val = dpg.get_value(tag)
                ps_states[key] = 2 if "(++)" in val else 1 if "(+)" in val else 0
        t1, t2, it1, it2 = encode_player_playstyles(ps_states)

        self.session.update_player_attribute(pid, "trait1", t1)
        self.session.update_player_attribute(pid, "trait2", t2)
        self.session.update_player_attribute(pid, "icontrait1", it1)
        self.session.update_player_attribute(pid, "icontrait2", it2)

        stats["trait1"] = str(t1)
        stats["trait2"] = str(t2)
        stats["icontrait1"] = str(it1)
        stats["icontrait2"] = str(it2)

        # 3. Secondary positions
        def _get_pos_code(pos_str):
            for k, v in POSITION_NAMES.items():
                if v == pos_str:
                    return k
            return -1

        pos1_code = _get_pos_code(dpg.get_value("edit_player_pos1"))
        pos2_code = _get_pos_code(dpg.get_value("edit_player_pos2"))
        pos3_code = _get_pos_code(dpg.get_value("edit_player_pos3"))
        pos4_code = _get_pos_code(dpg.get_value("edit_player_pos4"))

        if pos1_code >= 0:
            self.session.update_player_attribute(pid, "preferredposition1", pos1_code)
        self.session.update_player_attribute(pid, "preferredposition2", pos2_code)
        self.session.update_player_attribute(pid, "preferredposition3", pos3_code)
        self.session.update_player_attribute(pid, "preferredposition4", pos4_code)

        stats["preferredposition2"] = str(pos2_code)
        stats["preferredposition3"] = str(pos3_code)
        stats["preferredposition4"] = str(pos4_code)

        # 4. Roles & FC IQ
        for r_i in range(1, 6):
            if dpg.does_item_exist(f"edit_player_role{r_i}"):
                r_val = dpg.get_value(f"edit_player_role{r_i}")
                self.session.update_player_attribute(pid, f"role{r_i}", r_val)
                stats[f"role{r_i}"] = str(r_val)

        # 5. Jersey, Contract, Retiring
        jersey_num = dpg.get_value("edit_player_jersey")
        contract_yr = dpg.get_value("edit_player_contract")
        is_ret = 1 if dpg.get_value("edit_player_isretiring") else 0
        self.session.update_player_attribute(pid, "jerseynumber", jersey_num)
        self.session.update_player_attribute(pid, "contractvaliduntil", contract_yr)
        self.session.update_player_attribute(pid, "isretiring", is_ret)
        stats["jerseynumber"] = str(jersey_num)
        stats["contractvaliduntil"] = str(contract_yr)
        stats["isretiring"] = str(is_ret)

        # 6. Kit & Appearance
        j_style = 1 if dpg.get_value("edit_player_jerseystyle") == "Untucked" else 0
        s_length = 1 if dpg.get_value("edit_player_sleeves") == "Long" else 0
        j_fit = 1 if dpg.get_value("edit_player_fit") == "Tight" else 0
        sock_val = 1 if dpg.get_value("edit_player_socklength") == "Short" else 2 if dpg.get_value("edit_player_socklength") == "High" else 0
        shoe_val = dpg.get_value("edit_player_shoetype")
        glove_val = dpg.get_value("edit_player_gkglove")

        stats["jerseystylecode"] = str(j_style)
        stats["jerseysleevelengthcode"] = str(s_length)
        stats["jerseyfit"] = str(j_fit)
        stats["socklengthcode"] = str(sock_val)
        stats["shoetypecode"] = str(shoe_val)
        stats["gkglovetypecode"] = str(glove_val)

        # 7. Physical and Technical stats dict
        stat_inputs = [
            ("accel", "acceleration"), ("sprint", "sprintspeed"), ("pos", "positioning"),
            ("finish", "finishing"), ("shotpwr", "shotpower"), ("longshots", "longshots"),
            ("volleys", "volleys"), ("penalties", "penalties"), ("vision", "vision"),
            ("crossing", "crossing"), ("fk", "freekickaccuracy"), ("shortpass", "shortpassing"),
            ("longpass", "longpassing"), ("curve", "curve"), ("agility", "agility"),
            ("balance", "balance"), ("reactions", "reactions"), ("ballctrl", "ballcontrol"),
            ("dribble", "dribbling"), ("composure", "composure"), ("interceptions", "interceptions"),
            ("heading", "headingaccuracy"), ("defawareness", "defensiveawareness"),
            ("standtackle", "standingtackle"), ("slidetackle", "slidingtackle"),
            ("jumping", "jumping"), ("stamina", "stamina"), ("strength", "strength"),
            ("aggression", "aggression"), ("gkdiving", "gkdiving"), ("gkhandling", "gkhandling"),
            ("gkkicking", "gkkicking"), ("gkreflexes", "gkreflexes"), ("gkpos", "gkpositioning")
        ]
        for ui_key, stat_key in stat_inputs:
            tag = f"edit_player_{ui_key}"
            if dpg.does_item_exist(tag):
                val = dpg.get_value(tag)
                self.session.update_player_attribute(pid, stat_key, val)
                stats[stat_key] = str(val)

        dpg.set_value("player_save_feedback", "✓ Saved player attributes, PlayStyles & appearance successfully!")
        self._on_filter_players()

    def _on_boost_player(self):
        if not self.selected_player:
            return
        # Set all attributes to 99
        for key in ["edit_player_ovr", "edit_player_pot", "edit_player_accel", "edit_player_sprint",
                    "edit_player_finish", "edit_player_shotpwr", "edit_player_longshots",
                    "edit_player_volleys", "edit_player_penalties", "edit_player_vision",
                    "edit_player_crossing", "edit_player_fk", "edit_player_shortpass",
                    "edit_player_longpass", "edit_player_curve", "edit_player_agility",
                    "edit_player_balance", "edit_player_reactions", "edit_player_ballctrl",
                    "edit_player_dribble", "edit_player_composure", "edit_player_interceptions",
                    "edit_player_heading", "edit_player_defawareness", "edit_player_standtackle",
                    "edit_player_slidetackle", "edit_player_jumping", "edit_player_stamina",
                    "edit_player_strength", "edit_player_aggression"]:
            if dpg.does_item_exist(key):
                dpg.set_value(key, 99)
        dpg.set_value("edit_player_skills", 5)
        dpg.set_value("edit_player_weakfoot", 5)
        self._on_all_gold_playstyles()
        self._on_save_player_changes()
        dpg.set_value("player_save_feedback", "⚡ Prime 99 & All Gold PlayStyles+ Applied!")

    # --- Teams UI Callbacks ---

    def _load_teams_list(self):
        self._on_filter_teams()

    def _on_filter_teams(self):
        search_txt = ""
        if dpg.does_item_exist("team_search_input"):
            search_txt = (dpg.get_value("team_search_input") or "").lower().strip()
        filtered = []
        for t in self.session.teams_cache:
            if search_txt:
                name_match = search_txt in t["name"].lower()
                id_match = search_txt in str(t["teamid"])
                if not (name_match or id_match):
                    continue
            filtered.append(t)
        self.filtered_teams = filtered
        items = [f"{t['name']} (ID: {t['teamid']}) - {t['roster_count']} players" for t in self.filtered_teams]
        if dpg.does_item_exist("teams_listbox"):
            dpg.configure_item("teams_listbox", items=items)
        if dpg.does_item_exist("team_count_label"):
            dpg.set_value("team_count_label", f"Total Clubs: {len(self.filtered_teams):,} matches")

    def _on_select_team(self, sender, app_data):
        items = dpg.get_item_configuration("teams_listbox")["items"]
        if not items or app_data not in items:
            return
        idx = items.index(app_data)
        if idx >= len(self.filtered_teams):
            return
        t = self.filtered_teams[idx]
        self.selected_team = t

        dpg.set_value("team_selected_header", f"Club: {t['name']} (ID: {t['teamid']})")
        dpg.set_value("edit_team_id", t["teamid"])
        dpg.set_value("edit_team_name", t["name"])
        dpg.set_value("edit_team_stadium", t.get("stadium", "Default Stadium"))

        # Display roster
        roster_items = []
        for pid in t.get("roster", []):
            if pid in self.session.players_lookup:
                p = self.session.players_lookup[pid]
                pos_str = get_position_name(p["pos_code"])
                roster_items.append(f"[{p['overall']}] {p['name']} ({pos_str}) - ID {pid}")
            else:
                roster_items.append(f"Player ID #{pid}")

        dpg.configure_item("team_roster_listbox", items=roster_items)
        dpg.configure_item("team_edit_controls", show=True)
        dpg.set_value("team_save_feedback", "")

    def _on_save_team_changes(self):
        if not self.selected_team:
            return
        new_name = dpg.get_value("edit_team_name")
        self.selected_team["name"] = new_name
        dpg.set_value("team_save_feedback", "✓ Club details updated!")
        self._on_filter_teams()

    # --- Database Editor UI Callbacks ---

    def _load_database_tables_dropdown(self):
        items = [f"{sname} ({get_table_display_name(sname)})" for sname, _, _ in self.session.get_table_names_list()]
        dpg.configure_item("db_table_selector", items=items)
        if items:
            dpg.set_value("db_table_selector", items[0])
            self.selected_table_sname = self.session.db.tables[0].sname
            self._load_db_table(self.selected_table_sname)

    def _on_change_db_table(self, sender, app_data):
        sname = app_data.split(" ")[0].strip()
        self.selected_table_sname = sname
        self.current_table_page = 0
        self._load_db_table(sname)

    def _load_db_table(self, sname: str):
        tbl = self.session.get_table(sname)
        if not tbl:
            return
        dpg.set_value("db_table_stats_text", f"Rows: {len(tbl.records):,} | Columns: {len(tbl.columns)} | Record Size: {tbl.rec_size} bytes")
        self._render_db_records_page()

    def _on_add_row(self):
        tbl = self.session.get_table(self.selected_table_sname)
        if tbl:
            self.session.add_table_row(self.selected_table_sname)
            self._load_db_table(self.selected_table_sname)
            dpg.set_value("record_save_feedback", "✓ New blank row added at end of table!")

    def _on_clone_row(self):
        tbl = self.session.get_table(self.selected_table_sname)
        if tbl and self.selected_record_index is not None:
            self.session.clone_table_row(self.selected_table_sname, self.selected_record_index)
            self._load_db_table(self.selected_table_sname)
            dpg.set_value("record_save_feedback", f"✓ Cloned row #{self.selected_record_index}!")

    def _on_delete_row(self):
        tbl = self.session.get_table(self.selected_table_sname)
        if tbl and self.selected_record_index is not None and len(tbl.records) > 0:
            deleted_idx = self.selected_record_index
            self.session.delete_table_row(self.selected_table_sname, deleted_idx)
            self.selected_record_index = None
            self._load_db_table(self.selected_table_sname)
            dpg.delete_item("record_fields_container", children_only=True)
            dpg.configure_item("record_actions_group", show=False)
            dpg.set_value("db_table_stats_text", f"Rows: {len(tbl.records):,} | Columns: {len(tbl.columns)} | Record Size: {tbl.rec_size} bytes")

    def _render_db_records_page(self):
        tbl = self.session.get_table(self.selected_table_sname)
        if not tbl:
            return

        total_rows = len(tbl.records)
        total_pages = max(1, (total_rows + self.page_size - 1) // self.page_size)
        page = min(self.current_table_page, total_pages - 1)
        self.current_table_page = page

        dpg.set_value("db_pagination_text", f"Page {page + 1} of {total_pages}")

        start_idx = page * self.page_size
        end_idx = min(start_idx + self.page_size, total_rows)

        items = []
        for r_idx in range(start_idx, end_idx):
            rec = tbl.records[r_idx]
            summary_cols = []
            for col in tbl.columns[:3]:
                val = col.decode_value(rec)
                summary_cols.append(f"{col.sname}={val}")
            items.append(f"Row {r_idx:5d}: " + " | ".join(summary_cols))

        dpg.configure_item("db_records_listbox", items=items)
        dpg.configure_item("record_actions_group", show=False)

    def _on_prev_page(self):
        if self.current_table_page > 0:
            self.current_table_page -= 1
            self._render_db_records_page()

    def _on_next_page(self):
        tbl = self.session.get_table(self.selected_table_sname)
        if tbl:
            total_pages = max(1, (len(tbl.records) + self.page_size - 1) // self.page_size)
            if self.current_table_page < total_pages - 1:
                self.current_table_page += 1
                self._render_db_records_page()

    def _on_filter_records(self, sender, app_data):
        self._render_db_records_page()

    def _on_select_record(self, sender, app_data):
        tbl = self.session.get_table(self.selected_table_sname)
        if not tbl or not tbl.records:
            return

        try:
            row_idx = int(app_data.split(":")[0].replace("Row", "").strip())
        except Exception:
            return

        self.selected_record_index = row_idx
        dpg.set_value("record_inspector_header", f"Editing Table '{tbl.sname}' Row #{row_idx}")

        rec = tbl.records[row_idx]
        dpg.delete_item("record_fields_container", children_only=True)

        with dpg.group(parent="record_fields_container"):
            for col in tbl.columns:
                val = col.decode_value(rec)
                disp_name = get_column_display_name(col.sname)
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{disp_name:24s} [{col.sname:4s}] (bits:{col.bit_size:2d}):", color=(200, 200, 200))
                    tag = f"field_edit_{col.sname}"
                    if col.col_type == 0: # String
                        dpg.add_input_text(default_value=str(val), tag=tag, width=280)
                    elif col.col_type == 4: # Float
                        dpg.add_input_float(default_value=float(val), tag=tag, width=200)
                    else: # Int / Bitfield
                        dpg.add_input_int(default_value=int(val), tag=tag, width=200)

        dpg.configure_item("record_actions_group", show=True)
        dpg.set_value("record_save_feedback", "")

    def _on_save_record_changes(self):
        tbl = self.session.get_table(self.selected_table_sname)
        if not tbl or self.selected_record_index is None:
            return

        row_idx = self.selected_record_index
        for col in tbl.columns:
            tag = f"field_edit_{col.sname}"
            if dpg.does_item_exist(tag):
                val = dpg.get_value(tag)
                self.session.update_table_cell(self.selected_table_sname, row_idx, col.sname, val)

        dpg.set_value("record_save_feedback", "✓ Record updated and serialized successfully!")
        self._render_db_records_page()

def main():
    app = SquadEditorApp()
    app.run()

if __name__ == "__main__":
    main()
