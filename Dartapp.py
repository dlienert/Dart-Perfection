import streamlit as st
import matplotlib.pyplot as plt # Keep for future stats visualizations
import json
import os
import hashlib
import pandas as pd
import time
import math # Needed for ceiling function in set/leg logic

# --- Configuration ---
USER_DATA_FILE = "user_data.json"
st.set_page_config(page_title="Darts Counter", page_icon="🎯", layout="wide")

# --- Default Preferred Doubles & Constants ---
DEFAULT_PREFERRED_DOUBLES = {"D18", "D4", "D13", "D6", "D10", "D15", "D2", "D17", "D3", "D20", "D16", "D8"}
ALL_POSSIBLE_DOUBLES = sorted([f"D{i}" for i in range(1, 21)] + ["D25"], key=lambda x: int(x[1:]))
BOGIE_NUMBERS_SET = {169, 168, 166, 165, 163, 162, 159}

# --- User Authentication & Data Handling ---
def load_users():
    """Loads user data from the JSON file."""
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                users_data = json.load(f)
            # Ensure essential keys exist for each user and player upon loading
            for username, data in users_data.items():
                data.setdefault("password", "")
                player_stats_dict = data.setdefault("player_stats", {})
                data.setdefault("games", [])
                data.setdefault("checkout_log", [])
                # Ensure stats and preferences dict has default keys for players
                for player, stats in player_stats_dict.items():
                     stats.setdefault("games_played", 0)
                     stats.setdefault("games_won", 0)
                     stats.setdefault("legs_won", 0)
                     stats.setdefault("sets_won", 0)
                     stats.setdefault("total_score", 0)
                     stats.setdefault("highest_score", 0)
                     stats.setdefault("total_turns", 0)
                     stats.setdefault("num_busts", 0)
                     stats.setdefault("darts_thrown", 0)
                     stats.setdefault("preferred_doubles", []) # Ensure exists per player
            return users_data
        except json.JSONDecodeError:
            st.error(f"Error reading {USER_DATA_FILE}. Starting fresh.")
            return {}
        except Exception as e:
            st.error(f"Error loading user data: {e}")
            return {}
    return {}

def save_users(users_data):
    """Saves the current user data dictionary to the JSON file."""
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(users_data, f, indent=4)
    except Exception as e:
        st.error(f"Failed to save user data: {e}")

def hash_password(password):
    """Hashes the password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- Load Users ---
users = load_users()

# --- Initialize Session State ---
if "app_initialized" not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.current_page = "Login"
    st.session_state.game_mode = 501
    st.session_state.check_out_mode = "Double Out"
    st.session_state.sets_to_play = 1
    st.session_state.set_leg_rule = "First to"
    st.session_state.check_in_mode = "Straight In"
    st.session_state.legs_to_play = 1
    st.session_state.players_selected_for_game = []
    st.session_state.starting_score = 0
    st.session_state.player_scores = {}
    st.session_state.player_legs_won = {}
    st.session_state.player_sets_won = {}
    st.session_state.player_darts_thrown = {}
    st.session_state.player_turn_history = {}
    st.session_state.player_last_turn_scores = {}
    st.session_state.current_player_index = 0
    st.session_state.current_turn_shots = []
    st.session_state.game_over = False
    st.session_state.leg_over = False
    st.session_state.set_over = False
    st.session_state.current_leg = 1
    st.session_state.current_set = 1
    st.session_state.winner = None
    st.session_state.message = ""
    st.session_state.pending_modifier = None
    st.session_state.state_before_last_turn = None
    st.session_state.confirm_delete_player = None
    st.session_state.player_to_edit_prefs = None # Initialize if needed

# --- Login / Register Page ---
if not st.session_state.logged_in:
    st.session_state.current_page = "Login"
    st.title("🔐 Welcome to Darts Counter")
    login_tab, register_tab = st.tabs(["Login", "Register"])
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            login_button = st.form_submit_button("Login", use_container_width=True)
            if login_button:
                # Check password safely using .get()
                hashed_input_pw = hash_password(password)
                if username in users and users[username].get("password") == hashed_input_pw:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.current_page = "Homepage"
                    st.session_state.players_selected_for_game = []
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    with register_tab:
         with st.form("register_form"):
            new_username = st.text_input("New Username", key="reg_user").strip()
            new_password = st.text_input("New Password", type="password", key="reg_pass")
            reg_button = st.form_submit_button("Register", use_container_width=True)
            if reg_button:
                if not new_username or not new_password:
                    st.warning("Username and password cannot be empty.")
                elif new_username in users:
                    st.warning("Username already exists.")
                else:
                    hashed_pw = hash_password(new_password)
                    # Initialize new user entry correctly
                    users[new_username] = {
                        "password": hashed_pw,
                        "player_stats": {},
                        "games": [],
                        "checkout_log": []
                        # No top-level preferred_doubles here
                    }
                    save_users(users)
                    st.success("Registration successful! Please log in.")
    st.stop()

# --- Main App Area ---
# --- Sidebar ---
st.sidebar.markdown(f"👋 **{st.session_state.username}**!")
st.sidebar.markdown("---")
page_options = ["Homepage", "Statistics", "Game", "⚙️ Settings"]
can_navigate_to_game = st.session_state.current_page == "Game" and not st.session_state.game_over
try:
    current_page_index = page_options.index(st.session_state.current_page)
except ValueError:
    current_page_index = 0
    st.session_state.current_page = "Homepage"
# Disable radio navigation while game is active and not over
nav_disabled = st.session_state.current_page == "Game" and not st.session_state.game_over
chosen_page = st.sidebar.radio(
    "Navigation",
    page_options,
    index=current_page_index,
    key="nav_radio",
    disabled=nav_disabled
)

# Handle navigation selection
if chosen_page != st.session_state.current_page:
    # Allow navigation away only if not in an active game
    if not nav_disabled:
        st.session_state.current_page = chosen_page
        st.rerun()
    else:
        # If disabled, reset the radio button visually if possible
        # (May still show selection briefly due to Streamlit limitations)
        st.sidebar.warning("Finish or Quit current game first!")
# Handle direct navigation attempt to Game page when not started
elif chosen_page == "Game" and st.session_state.current_page != "Game":
     st.sidebar.warning("Start game from Homepage first!")
     time.sleep(1)


if st.session_state.current_page == "Game" and not st.session_state.game_over:
    st.sidebar.warning("🎯 Game in progress!")
    if st.sidebar.button("⚠️ Quit Current Game"):
        st.session_state.current_page = "Homepage"
        st.session_state.game_over = True
        st.session_state.current_turn_shots = []
        st.session_state.pending_modifier = None
        st.rerun()
st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
        # Clear all session state keys upon logout
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.logged_in = False
        st.session_state.app_initialized = False # Allow re-init on next load
        st.rerun()

# --- Page Content Area ---

# --- Homepage Tab Logic ---
if st.session_state.current_page == "Homepage":
    st.title("🎯 Darts Counter Homepage")
    st.markdown(f"Configure game, **{st.session_state.username}**!")
    game_mode_tabs = st.tabs(["X01 Setup", "Cricket (Soon)"])
    with game_mode_tabs[0]:
        st.subheader("X01 Options")
        # --- Game Settings Columns (Multi-line) ---
        col1, col2, col3 = st.columns(3)
        with col1:
            points_options = ["101", "201", "301", "401", "501"]
            try:
                default_points_index = points_options.index(str(st.session_state.get("game_mode", 501)))
            except ValueError:
                default_points_index = points_options.index("501")
            selected_points = st.selectbox("Points", points_options, index=default_points_index)
            st.session_state.game_mode = int(selected_points)
        with col2:
            checkout_options = ["Straight Out", "Double Out"]
            try:
                default_checkout_index = checkout_options.index(st.session_state.get("check_out_mode", "Double Out"))
            except ValueError:
                default_checkout_index = checkout_options.index("Double Out")
            selected_checkout = st.selectbox("Check-Out", checkout_options, index=default_checkout_index)
            st.session_state.check_out_mode = selected_checkout
        with col3:
            sets_options = list(range(1, 12))
            try:
                default_sets_index = sets_options.index(st.session_state.get("sets_to_play", 1))
            except ValueError:
                default_sets_index = sets_options.index(1)
            selected_sets = st.selectbox("Sets", sets_options, index=default_sets_index)
            st.session_state.sets_to_play = selected_sets

        col4, col5, col6 = st.columns(3)
        with col4:
            set_leg_options = ["First to", "Best of"]
            try:
                default_set_leg_index = set_leg_options.index(st.session_state.get("set_leg_rule", "First to"))
            except ValueError:
                default_set_leg_index = set_leg_options.index("First to")
            selected_set_leg = st.selectbox("Set/Leg Rule", set_leg_options, index=default_set_leg_index)
            st.session_state.set_leg_rule = selected_set_leg
        with col5:
            checkin_options = ["Straight In", "Double In"]
            try:
                default_checkin_index = checkin_options.index(st.session_state.get("check_in_mode", "Straight In"))
            except ValueError:
                default_checkin_index = checkin_options.index("Straight In")
            selected_checkin = st.selectbox("Check-In (N/I)", checkin_options, index=default_checkin_index, disabled=True)
            st.session_state.check_in_mode = selected_checkin
        with col6:
            legs_options = list(range(1, 12))
            try:
                default_legs_index = legs_options.index(st.session_state.get("legs_to_play", 1))
            except ValueError:
                 default_legs_index = legs_options.index(1)
            selected_legs = st.selectbox("Legs/Set", legs_options, index=default_legs_index)
            st.session_state.legs_to_play = selected_legs

        # --- Player Selection / Add Player ---
        st.markdown("---")
        st.subheader("Players")
        available_players = []
        current_username_hp = st.session_state.username
        if current_username_hp and current_username_hp in users:
            player_stats_dict_hp = users[current_username_hp].setdefault("player_stats", {})
            available_players = sorted(list(player_stats_dict_hp.keys()))
        else:
            st.error("Error: Could not retrieve user data.")

        selected_players_list = st.multiselect(
            "Select players for game (incl. yourself if playing!)",
            options=available_players,
            default=st.session_state.players_selected_for_game,
            key="multiselect_players"
        )
        st.session_state.players_selected_for_game = selected_players_list

        with st.expander("Add / Manage Players"):
            st.write("Add new players (including yourself) to track stats & set preferences.")
            new_player_name_from_input = st.text_input("New Player Name", key="new_player_name_input").strip()
            if st.button("➕ Add Player"):
                if new_player_name_from_input:
                    if current_username_hp and current_username_hp in users:
                        player_stats_dict_add = users[current_username_hp].setdefault("player_stats", {})
                        if new_player_name_from_input not in player_stats_dict_add:
                            player_stats_dict_add[new_player_name_from_input] = {
                                "games_played": 0, "games_won": 0, "legs_won": 0, "sets_won": 0,
                                "total_score": 0, "highest_score": 0, "total_turns": 0,
                                "num_busts": 0, "darts_thrown": 0, "preferred_doubles": [] # Add prefs list
                            }
                            save_users(users)
                            st.success(f"Player '{new_player_name_from_input}' added.")
                            st.rerun()
                        else:
                            st.warning(f"Player '{new_player_name_from_input}' already exists.")
                    else:
                        st.error("Error saving player.")
                else:
                    st.warning("Please enter a name.")
            st.caption("Edit preferences or delete players in '⚙️ Settings'.")

        st.markdown("---")

        # --- Start Game Button ---
        if st.button("🚀 Start Game", type="primary", use_container_width=True):
            players_to_start = st.session_state.players_selected_for_game
            if not players_to_start:
                st.warning("⚠️ Select players.")
            elif not st.session_state.game_mode or st.session_state.game_mode not in [101, 201, 301, 401, 501]:
                st.warning("⚠️ Select X01 mode.")
            else: # Initialize Game State (Expanded)
                st.session_state.current_page = "Game"
                st.session_state.starting_score = st.session_state.game_mode
                st.session_state.player_scores = {p: st.session_state.starting_score for p in players_to_start}
                st.session_state.player_legs_won = {p: 0 for p in players_to_start}
                st.session_state.player_sets_won = {p: 0 for p in players_to_start}
                st.session_state.player_darts_thrown = {p: 0 for p in players_to_start}
                st.session_state.player_turn_history = {p: [] for p in players_to_start}
                st.session_state.player_last_turn_scores = {p: [] for p in players_to_start}
                st.session_state.current_player_index = 0
                st.session_state.current_turn_shots = []
                st.session_state.current_leg = 1
                st.session_state.current_set = 1
                st.session_state.game_over = False
                st.session_state.leg_over = False
                st.session_state.set_over = False
                st.session_state.winner = None
                st.session_state.message = ""
                st.session_state.pending_modifier = None
                st.session_state.state_before_last_turn = None
                st.success(f"Starting {st.session_state.game_mode}...")
                st.info(f"Playing {st.session_state.set_leg_rule} {st.session_state.sets_to_play} set(s)...")
                time.sleep(1.5)
                st.rerun()
    with game_mode_tabs[1]:
        st.subheader("Cricket")
        st.info("🏏 Planned.")

# --- Statistics Tab Logic ---
elif st.session_state.current_page == "Statistics":
    st.title("📊 Personal Statistics")
    st.write(f"Stats for account: **{st.session_state.username}**")
    if "confirm_delete_player" not in st.session_state:
        st.session_state.confirm_delete_player = None
    current_username_stats = st.session_state.username
    # Use .get() for safer access
    if current_username_stats in users and "player_stats" in users.get(current_username_stats, {}):
        player_stats_data = users[current_username_stats]["player_stats"]
        if player_stats_data:
            # --- Stats Display Table (Expanded) ---
            stats_options = ["Games Played", "Games Won", "Legs Won", "Sets Won", "Win Rate (%)", "Total Score Thrown", "Avg Score per Turn", "Avg Score per Dart", "Highest Score (Turn)", "Total Turns", "Darts Thrown", "Busts"]
            selected_stat = st.selectbox("Select Statistic:", stats_options)
            table_data = []
            for player, stats in player_stats_data.items():
                row = {"Player": player}
                games_played = stats.get("games_played", 0)
                games_won = stats.get("games_won", 0)
                legs_won = stats.get("legs_won", 0)
                sets_won = stats.get("sets_won", 0)
                total_score = stats.get("total_score", 0)
                total_turns = stats.get("total_turns", 0)
                darts_thrown = stats.get("darts_thrown", 0)

                if selected_stat == "Games Played":
                    row["Value"] = games_played
                elif selected_stat == "Games Won":
                    row["Value"] = games_won
                elif selected_stat == "Legs Won":
                    row["Value"] = legs_won
                elif selected_stat == "Sets Won":
                    row["Value"] = sets_won
                elif selected_stat == "Win Rate (%)":
                    row["Value"] = f"{(games_won / games_played * 100):.2f}" if games_played > 0 else "0.00"
                elif selected_stat == "Total Score Thrown":
                    row["Value"] = total_score
                elif selected_stat == "Avg Score per Turn":
                    row["Value"] = f"{(total_score / total_turns):.2f}" if total_turns > 0 else "0.00"
                elif selected_stat == "Avg Score per Dart":
                    row["Value"] = f"{(total_score / darts_thrown):.2f}" if darts_thrown > 0 else "0.00"
                elif selected_stat == "Highest Score (Turn)":
                    row["Value"] = stats.get("highest_score", 0)
                elif selected_stat == "Total Turns":
                    row["Value"] = total_turns
                elif selected_stat == "Darts Thrown":
                    row["Value"] = darts_thrown
                elif selected_stat == "Busts":
                    row["Value"] = stats.get("num_busts", 0)
                table_data.append(row)

            if table_data:
                try:
                    df = pd.DataFrame(table_data)
                    df_sorted = df.sort_values(by="Player").set_index("Player")
                    st.dataframe(df_sorted, use_container_width=True)
                except Exception as e:
                    st.error(f"Error displaying table: {e}")
            else:
                st.info("No data for selected statistic.")
            st.markdown("---")
            st.subheader("Visualizations (Placeholder)")
            st.info("Charts coming soon.")

            # Deletion logic moved to Settings page
            # st.markdown("---"); st.subheader("⚠️ Manage Player Stats"); ...

        else:
            st.info("No player stats recorded yet.")
    else:
        st.warning("Could not load stats.")

# --- Settings Page Logic ---
elif st.session_state.current_page == "⚙️ Settings":
    st.title("⚙️ Settings & Player Management")
    st.write(f"Manage players and preferences for account: **{st.session_state.username}**")
    st.markdown("---")

    current_username = st.session_state.username
    # Ensure user exists and has player_stats key before proceeding
    if current_username not in users or "player_stats" not in users.get(current_username, {}):
        st.error("User data not found or player stats missing. Please re-login or add players on Homepage.")
        st.stop() # Stop execution for this page if data is missing

    # Safely get player_stats dictionary
    player_stats_dict = users[current_username].setdefault("player_stats", {})
    players_list = sorted(list(player_stats_dict.keys()))

    tab_prefs, tab_delete = st.tabs(["🎯 Set Preferences", "🗑️ Delete Player"])

    with tab_prefs:
        st.subheader("Set Preferred Double Outs")
        st.write("Select preferred doubles for checkout suggestions for each player.")

        if not players_list:
            st.warning("No players added yet. Add players on the Homepage.")
        else:
            # Select Player to Edit
            player_to_edit = st.selectbox(
                "Select Player to Edit Preferences:",
                players_list,
                key="edit_prefs_player_select",
                index=None,
                placeholder="Choose player..."
            )

            # --- Initialize variable BEFORE potentially using it ---
            current_preferences_formatted = [] # Default to empty list

            # --- Calculate actual prefs only if a player is selected ---
            if player_to_edit:
                # Load current preferences safely using .get()
                current_prefs = player_stats_dict.get(player_to_edit, {}).get('preferred_doubles', [])
                # Ensure loaded preferences are valid doubles before displaying
                current_preferences_formatted = [pref for pref in current_prefs if pref in ALL_POSSIBLE_DOUBLES]

            # --- Disable multiselect and button if no player is chosen ---
            input_disabled = (player_to_edit is None)

            # Display multiselect using the initialized/calculated preferences
            selected_doubles = st.multiselect(
                f"Select preferred doubles for **{player_to_edit or '...'}**:", # Handle label if None
                options=ALL_POSSIBLE_DOUBLES,
                default=current_preferences_formatted,
                key=f"pref_doubles_multiselect_{player_to_edit or 'none'}", # Unique key part
                disabled=input_disabled
            )

            # Display Save button, disable if needed
            save_button_label = f"Save Preferences for {player_to_edit}" if player_to_edit else "Save Preferences"
            if st.button(save_button_label, type="primary", key=f"save_prefs_{player_to_edit or 'none'}", disabled=input_disabled):
                 # Check again if player_to_edit is valid before saving
                if player_to_edit:
                    # Ensure player still exists and stats dict is there before saving
                    if player_to_edit in users[current_username].get("player_stats", {}):
                         users[current_username]["player_stats"][player_to_edit]['preferred_doubles'] = selected_doubles
                         save_users(users)
                         st.success(f"Preferences saved for {player_to_edit}!")
                         time.sleep(1)
                         # No rerun usually needed here, state is saved
                    else:
                         st.error("Player not found, could not save preferences (maybe deleted?).")
                # else: Button should be disabled if player_to_edit is None

    with tab_delete:
        st.subheader("Delete Player Data")
        st.warning("⚠️ Deleting a player removes all their stats and checkout logs permanently!")

        if not players_list:
            st.info("No players to delete.")
        else:
            # Initialize confirmation state if needed
            if "confirm_delete_player" not in st.session_state:
                st.session_state.confirm_delete_player = None

            player_to_delete = st.selectbox(
                "Select Player to Delete:",
                players_list,
                index=None,
                placeholder="Choose player...",
                # Use a unique key to avoid conflict with other selectbox
                key="delete_player_select_settings_tab"
            )

            # Logic for delete button (without form)
            delete_button_disabled = (player_to_delete is None) or (st.session_state.confirm_delete_player == player_to_delete)
            delete_button_label = f"Delete {player_to_delete}" if player_to_delete else "Delete Player..."

            if st.button(delete_button_label, type="secondary", disabled=delete_button_disabled, key="settings_delete_request_btn"):
                 if player_to_delete:
                    st.session_state.confirm_delete_player = player_to_delete
                    st.rerun() # Rerun to show confirmation

            # Confirmation Step
            if st.session_state.confirm_delete_player:
                # Check if the player selected for confirmation still exists and matches dropdown
                if player_to_delete == st.session_state.confirm_delete_player:
                    st.error(f"**Confirm Deletion of {st.session_state.confirm_delete_player}?**") # Use error styling for confirmation
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("✔️ Yes, DELETE Player Data", type="primary", use_container_width=True, key="settings_confirm_delete_btn"):
                            try:
                                player_name_confirmed = st.session_state.confirm_delete_player
                                # Check if player actually exists before deleting
                                if player_name_confirmed in users[current_username]["player_stats"]:
                                    del users[current_username]["player_stats"][player_name_confirmed] # Delete player entry
                                    # Filter logs
                                    if "checkout_log" in users[current_username]:
                                         users[current_username]["checkout_log"] = [
                                             e for e in users[current_username].get("checkout_log", [])
                                             if e.get("player") != player_name_confirmed
                                         ]
                                    save_users(users)
                                    st.success(f"Deleted {player_name_confirmed}.")
                                else:
                                     st.error(f"Player {player_name_confirmed} not found (maybe already deleted).")

                                st.session_state.confirm_delete_player = None
                                # Resetting selectbox state is hard, rerun updates the list
                                time.sleep(1)
                                st.rerun() # Refresh page
                            except Exception as e:
                                st.error(f"An error occurred during deletion: {e}")
                                st.session_state.confirm_delete_player = None
                                st.rerun()
                    with col_cancel:
                         if st.button("❌ Cancel", type="secondary", use_container_width=True, key="settings_cancel_delete_btn"):
                             st.session_state.confirm_delete_player = None
                             st.rerun()
                else:
                    # If selection changed after clicking delete once - reset confirmation silently
                    st.session_state.confirm_delete_player = None

    st.markdown("---")


# --- Game Tab Logic ---
elif st.session_state.current_page == "Game":

    # --- Helper Functions (Fully Expanded) ---
    def parse_score_input(score_str):
        score_str = str(score_str).upper().strip()
        is_double = False
        is_triple = False
        value = 0
        is_valid = True
        try:
            if score_str.startswith("T"):
                if len(score_str) > 1 and score_str[1:].isdigit():
                    num = int(score_str[1:])
                    if 1 <= num <= 20:
                        value = num * 3
                        is_triple = True
                    else:
                        is_valid = False
                else:
                    is_valid = False
            elif score_str.startswith("D"):
                 if len(score_str) > 1 and score_str[1:].isdigit():
                    num = int(score_str[1:])
                    if 1 <= num <= 20 or num == 25:
                        value = num * 2
                        is_double = True
                    else:
                        is_valid = False
                 else:
                    is_valid = False
            elif score_str.isdigit():
                num = int(score_str)
                if 0 <= num <= 20 or num == 25:
                    value = num
                elif num == 50:
                    st.toast("Use D25")
                    is_valid = False
                    value = 0
                else:
                    is_valid = False
            else:
                is_valid = False
        except ValueError:
            is_valid = False
        return value, is_double, is_triple, is_valid

    def get_throw_value(throw_str):
        value, _, _, is_valid = parse_score_input(throw_str)
        if is_valid:
            return value
        else:
            return 0 # Return 0 for invalid format

    def calculate_turn_total(shots_list):
        total = 0
        darts_thrown_turn = 0
        last_dart_double_flag = False
        parsed_shots_details = []
        if not shots_list:
            return 0, 0, False, []

        for i, shot_str in enumerate(shots_list):
            value, is_double, _, is_valid = parse_score_input(shot_str)
            if not is_valid:
                return None, 0, False, [] # Signal error if parse fails
            total += value
            darts_thrown_turn += 1
            last_dart_double_flag = is_double
            parsed_shots_details.append({"input": shot_str, "value": value, "is_double": is_double})

        return total, darts_thrown_turn, last_dart_double_flag, parsed_shots_details

    def run_turn_processing(player_name, shots_list):
        """Processes the end of a turn: updates scores, stats, logs, and determines next state."""
        global users
        current_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
        current_player_index_before_turn = st.session_state.current_player_index
        score_before_turn = st.session_state.player_scores[player_name]

        # Store state BEFORE processing for potential UNDO
        st.session_state.state_before_last_turn = {
            "player_index": current_player_index_before_turn,
            "player_name": player_name,
            "score_before": score_before_turn,
            "darts_thrown_player_before": st.session_state.player_darts_thrown.get(player_name, 0),
            "current_turn_shots_processed": list(shots_list),
            "legs_won_before": st.session_state.player_legs_won.get(player_name, 0),
            "sets_won_before": st.session_state.player_sets_won.get(player_name, 0),
        }

        calculated_score, darts_thrown_turn, last_dart_double, _ = calculate_turn_total(shots_list)

        if calculated_score is None:
            st.error("Internal Error: Score calculation failed during turn processing.")
            st.session_state.state_before_last_turn = None # Invalidate undo state on error
            return # Stop processing this turn

        new_score = score_before_turn - calculated_score
        is_bust = False
        is_win = False
        valid_checkout_attempt = True
        turn_result_for_log = "UNKNOWN"

        # --- Determine Turn Result (Expanded) ---
        # 1. Check Bust
        if new_score < 0 or new_score == 1:
            turn_result_for_log = "BUST"
            st.warning(f"❌ Bust! Score remains {score_before_turn}")
            st.session_state.player_scores[player_name] = score_before_turn
            st.session_state.message = f"{player_name} Busted!"
            st.session_state.player_turn_history.setdefault(player_name, []).append((calculated_score, darts_thrown_turn, turn_result_for_log))
            st.session_state.player_last_turn_scores[player_name] = list(shots_list)
            st.session_state.player_darts_thrown[player_name] = st.session_state.player_darts_thrown.get(player_name, 0) + darts_thrown_turn
            is_bust = True

        # 2. Check Win
        elif new_score == 0:
            # Check if checkout attempt is valid based on game rules
            if st.session_state.check_out_mode == "Double Out" and not last_dart_double:
                # Invalid Double Out -> Treat as Bust
                turn_result_for_log = "BUST (Invalid Checkout)"
                st.warning(f"❌ Invalid Checkout! Must finish on a Double. Score remains {score_before_turn}")
                st.session_state.player_scores[player_name] = score_before_turn
                st.session_state.message = f"{player_name} Invalid Checkout!"
                st.session_state.player_turn_history.setdefault(player_name, []).append((calculated_score, darts_thrown_turn, turn_result_for_log))
                st.session_state.player_last_turn_scores[player_name] = list(shots_list)
                st.session_state.player_darts_thrown[player_name] = st.session_state.player_darts_thrown.get(player_name, 0) + darts_thrown_turn
                is_bust = True # Treat as bust for turn advancement
                valid_checkout_attempt = False # Mark attempt as invalid
            else:
                # Valid Win
                turn_result_for_log = "WIN"
                st.success(f"🎯 Game Shot! {player_name} wins Leg {st.session_state.current_leg}!")
                st.session_state.player_scores[player_name] = 0 # Set score to 0
                st.session_state.message = f"{player_name} won Leg {st.session_state.current_leg}!"
                st.session_state.player_turn_history.setdefault(player_name, []).append((calculated_score, darts_thrown_turn, turn_result_for_log))
                st.session_state.player_last_turn_scores[player_name] = list(shots_list)
                st.session_state.player_darts_thrown[player_name] = st.session_state.player_darts_thrown.get(player_name, 0) + darts_thrown_turn
                st.session_state.leg_over = True # Signal leg end
                is_win = True # Mark turn as a winning turn
                # Increment leg count in session state for immediate display/checks
                st.session_state.player_legs_won[player_name] = st.session_state.player_legs_won.get(player_name, 0) + 1

        # 3. Regular Score Update
        else:
            turn_result_for_log = "OK"
            st.session_state.player_scores[player_name] = new_score
            st.session_state.message = f"{player_name} scored {calculated_score}."
            st.session_state.player_turn_history.setdefault(player_name, []).append((calculated_score, darts_thrown_turn, turn_result_for_log))
            st.session_state.player_last_turn_scores[player_name] = list(shots_list)
            st.session_state.player_darts_thrown[player_name] = st.session_state.player_darts_thrown.get(player_name, 0) + darts_thrown_turn

        # --- Detailed Logging for Checkouts / Busts under 171 ---
        is_finish_attempt_score = (2 <= score_before_turn <= 170 and score_before_turn not in BOGIE_NUMBERS_SET)
        if is_finish_attempt_score and turn_result_for_log != "OK":
            try:
                log_entry = {
                    "timestamp": current_time_str,
                    "player": player_name,
                    "score_before": score_before_turn,
                    "shots": list(shots_list),
                    "calculated_score": calculated_score,
                    "result": turn_result_for_log,
                    "last_dart_was_double": last_dart_double if turn_result_for_log == "WIN" else None,
                    "last_dart_str": shots_list[-1] if shots_list else None,
                    "game_mode": st.session_state.game_mode,
                    "leg": st.session_state.current_leg,
                    "set": st.session_state.current_set
                }
                current_username_log = st.session_state.username
                # Safely append to log list, creating if necessary
                log_list = users[current_username_log].setdefault("checkout_log", [])
                log_list.append(log_entry)
            except Exception as e:
                st.error(f"Log Error: {e}")

        # --- Update Persistent Stats ---
        current_username = st.session_state.username # Define for consistency
        # Ensure player exists in stats before updating
        if player_name in users.get(current_username, {}).get("player_stats", {}):
            stats = users[current_username]["player_stats"][player_name]
            # Use .get() with default 0 for safe incrementing
            if is_bust and turn_result_for_log.startswith("BUST"):
                 stats["num_busts"] = stats.get("num_busts", 0) + 1
            # Legs/Sets won stats are updated during advancement checks below
            if is_bust or is_win or turn_result_for_log == "OK": # If turn completed (even if bust)
                stats["total_turns"] = stats.get("total_turns", 0) + 1
                stats["darts_thrown"] = stats.get("darts_thrown", 0) + darts_thrown_turn
                # Only add score if not a bust
                if not is_bust and calculated_score is not None:
                    stats["total_score"] = stats.get("total_score", 0) + calculated_score
            # Update highest score if applicable
            if calculated_score is not None and calculated_score > stats.get("highest_score", 0):
                 stats["highest_score"] = calculated_score
        # Save users data once after all potential updates for the turn
        save_users(users)

        # --- Post-Turn Advancement Logic (EXPANDED) ---
        num_players_adv = len(st.session_state.players_selected_for_game)
        # Turn advances if bust, win, or 3 darts thrown, EXCEPT on invalid checkout bust
        should_advance_turn = (is_bust or is_win or (len(shots_list) == 3))
        # Override advance if it was an invalid checkout bust
        if not valid_checkout_attempt and new_score == 0:
            should_advance_turn = False
            st.warning("Correct score and try checkout again.") # Keep message

        if should_advance_turn:
            index_before_advance = st.session_state.current_player_index
            # Final update to undo state's index before advancing
            if st.session_state.state_before_last_turn:
                st.session_state.state_before_last_turn["player_index"] = index_before_advance

            # Clear the input buffer FIRST
            st.session_state.current_turn_shots = []

            # Check if the leg ended (implies a valid WIN occurred)
            if st.session_state.leg_over:
                legs_needed = math.ceil((st.session_state.legs_to_play + 1) / 2) if st.session_state.set_leg_rule == "Best of" else st.session_state.legs_to_play
                # Check if this leg win results in winning the Set
                if st.session_state.player_legs_won.get(player_name, 0) >= legs_needed:
                    st.session_state.set_over = True
                    st.session_state.player_sets_won[player_name] = st.session_state.player_sets_won.get(player_name, 0) + 1
                    st.success(f"🎉 {player_name} wins Set {st.session_state.current_set}!")
                    # Save set win stat persistently
                    if player_name in users[current_username]["player_stats"]:
                        users[current_username]["player_stats"][player_name]["sets_won"] = users[current_username]["player_stats"][player_name].get("sets_won",0)+1
                        save_users(users) # Save after updating set stat

                    # Check if this set win results in winning the Game
                    sets_needed = math.ceil((st.session_state.sets_to_play + 1) / 2) if st.session_state.set_leg_rule == "Best of" else st.session_state.sets_to_play
                    if st.session_state.player_sets_won.get(player_name, 0) >= sets_needed:
                        st.session_state.game_over = True
                        st.session_state.winner = player_name
                        # Update final game stats for all players
                        for p in st.session_state.players_selected_for_game:
                             if p in users[current_username]["player_stats"]:
                                 stats_p=users[current_username]["player_stats"][p]
                                 stats_p["games_played"] = stats_p.get("games_played", 0) + 1
                                 if p == player_name:
                                     stats_p["games_won"] = stats_p.get("games_won", 0) + 1
                        save_users(users) # Save final game stats
                        st.session_state.state_before_last_turn = None # Cannot undo after game over
                        # Don't advance player index or clear state here, game over screen handles it

                    else: # Set over, but Game not over -> Start Next Set
                        st.info("Prepare for next Set...")
                        time.sleep(1.5)
                        st.session_state.current_set += 1
                        st.session_state.current_leg = 1
                        st.session_state.player_scores = {p: st.session_state.starting_score for p in st.session_state.players_selected_for_game}
                        st.session_state.player_legs_won = {p: 0 for p in st.session_state.players_selected_for_game}
                        st.session_state.player_last_turn_scores = {p: [] for p in st.session_state.players_selected_for_game}
                        st.session_state.leg_over = False
                        st.session_state.set_over = False
                        st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
                        st.session_state.state_before_last_turn = None # Clear undo state on set transition

                else: # Leg over, but Set not over -> Start Next Leg
                    st.info("Prepare for next Leg...")
                    time.sleep(1.5)
                    st.session_state.current_leg += 1
                    st.session_state.player_scores = {p: st.session_state.starting_score for p in st.session_state.players_selected_for_game}
                    st.session_state.player_last_turn_scores = {p: [] for p in st.session_state.players_selected_for_game}
                    st.session_state.leg_over = False
                    # Alternate starting player
                    st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
                    st.session_state.state_before_last_turn = None # Clear undo state on leg transition

            else: # Leg not over, just advance player
                st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
                # Keep undo state available when just switching players

            # Rerun AFTER all advancement logic is complete
            st.rerun()
        # else: Turn did not advance (e.g., invalid checkout), allow correction without rerun here


    # --- Checkout Calculation Function ---
    @st.cache_data(ttl=3600) # Cache results
    def get_checkouts(target_score, darts_left, max_suggestions=5):
        # ... (Definition unchanged - expanded) ...
        if darts_left not in [1, 2, 3] or target_score < 2 or target_score > 170 or target_score in BOGIE_NUMBERS_SET:
            return []
        valid_paths = []
        throws_priority = ( [f"T{i}" for i in range(20, 0, -1)] +
                           [f"D{i}" for i in range(20, 0, -1)] + ["D25"] +
                           [str(i) for i in range(20, 0, -1)] + ["25"] )
        # --- 1 Dart Left ---
        if darts_left == 1:
            if (target_score <= 40 and target_score % 2 == 0) or target_score == 50:
                double = f"D{target_score // 2}" if target_score != 50 else "D25"
                return [[double]]
            else:
                return []
        # --- 2 Darts Left ---
        if darts_left >= 2:
            for throw1 in throws_priority:
                val1 = get_throw_value(throw1)
                if 0 < val1 < target_score and (target_score - val1) >= 2:
                    remaining_score1 = target_score - val1
                    one_dart_finish_list = get_checkouts(remaining_score1, 1)
                    if one_dart_finish_list:
                         path = [throw1, one_dart_finish_list[0][0]]
                         if path not in valid_paths:
                             valid_paths.append(path)
                             if len(valid_paths) >= max_suggestions:
                                 break
            if len(valid_paths) >= max_suggestions or darts_left == 2:
                 return valid_paths[:max_suggestions]
        # --- 3 Darts Left ---
        if darts_left == 3:
             for throw1 in throws_priority:
                 val1 = get_throw_value(throw1)
                 if 0 < val1 <= target_score - 4:
                     remaining_score1 = target_score - val1
                     two_dart_finishes = get_checkouts(remaining_score1, 2, max_suggestions=1)
                     if two_dart_finishes:
                         full_path = [throw1] + two_dart_finishes[0]
                         if full_path not in valid_paths:
                              valid_paths.append(full_path)
                              if len(valid_paths) >= max_suggestions:
                                  break
                 if len(valid_paths) >= max_suggestions:
                     break
        return valid_paths[:max_suggestions]

    # --- Setup Shot Calculation Function ---
    def get_setup_shot(current_score):
        # ... (Definition unchanged) ...
        preferred_leaves = [32, 40, 16, 8, 36, 20, 4, 50, 24, 12, 6, 10, 18, 2, 28, 34];
        for target_leave in preferred_leaves:
            needed_score = current_score - target_leave
            if 1 <= needed_score <= 20 or needed_score == 25:
                if target_leave >= 2: return f"Setup: {needed_score} (leaves {target_leave})";
        for single_hit in range(20, 0, -1):
            if current_score > single_hit and (current_score - single_hit) > 1:
                 return f"Setup: {single_hit} (leaves {current_score - single_hit})";
        return None

    def sort_checkouts_by_preference(paths, preferred_doubles):
        # ... (Definition unchanged) ...
        preferred_paths = []; other_paths = [];
        for path in paths:
            if path and path[-1].startswith("D") and path[-1] in preferred_doubles:
                preferred_paths.append(path);
            else:
                other_paths.append(path);
        return preferred_paths + other_paths;

    # --- Check Game State ---
    if st.session_state.game_over:
        st.title("🎉 Game Over!")
        if st.session_state.winner:
            st.header(f"🏆 Winner: {st.session_state.winner} 🏆")
        else:
            st.header("Match finished.")
        st.balloons()
        if st.button("Play Again / New Game Setup", use_container_width=True):
            st.session_state.current_page = "Homepage"
            st.session_state.players_selected_for_game = []
            st.rerun()
        st.stop()

    if not st.session_state.players_selected_for_game:
         st.error("No players selected.")
         if st.button("🏠 Back to Homepage", use_container_width=True):
             st.session_state.current_page = "Homepage"
             st.rerun()
         st.stop()

    # --- Game Interface ---
    st.title(f"🎯 Game On: {st.session_state.game_mode} - Set {st.session_state.current_set}/{st.session_state.sets_to_play} | Leg {st.session_state.current_leg}/{st.session_state.legs_to_play}")
    st.caption(f"Mode: {st.session_state.check_out_mode} | Rule: {st.session_state.set_leg_rule}")

    # --- Main Two-Column Layout ---
    left_col, right_col = st.columns([2, 1.2])

    with left_col:
        # --- Scoreboard Display ---
        st.subheader("Scores")
        num_players = len(st.session_state.players_selected_for_game)
        if num_players > 0:
            for i, player in enumerate(st.session_state.players_selected_for_game):
                is_current_player = (i == st.session_state.current_player_index)
                border_style = "border: 3px solid #FF4B4B; padding: 5px 8px; border-radius: 5px; background-color: #FFF0F0;" if is_current_player else "border: 1px solid #ccc; padding: 5px 8px; border-radius: 5px;"
                with st.container():
                    st.markdown(f"<div style='{border_style}'>", unsafe_allow_html=True)
                    st.markdown(f"<h5 style='text-align: center; margin-bottom: 5px; margin-top: 0;'>{'▶️ ' if is_current_player else ''}{player}</h5>", unsafe_allow_html=True)
                    col_score, col_stats = st.columns([2, 3])
                    with col_score:
                        actual_score = st.session_state.player_scores.get(player, st.session_state.starting_score)
                        display_score_val, score_color = actual_score, "black"; is_potential_bust = False; partial_turn_score = 0;
                        if is_current_player and st.session_state.current_turn_shots:
                            partial_turn_score_calc, _, _, _ = calculate_turn_total(st.session_state.current_turn_shots)
                            if partial_turn_score_calc is not None:
                                partial_turn_score = partial_turn_score_calc
                                temp_remaining_score = actual_score - partial_turn_score
                                if temp_remaining_score < 0 or temp_remaining_score == 1:
                                    display_score_val, score_color, is_potential_bust = "BUST", "red", True
                                elif temp_remaining_score >= 0:
                                    display_score_val = temp_remaining_score
                        st.markdown(f"<h2 style='text-align: center; font-size: 3em; margin-bottom: 0; color: {score_color}; line-height: 1.1;'>{display_score_val}</h2>", unsafe_allow_html=True)
                    with col_stats:
                        darts = st.session_state.player_darts_thrown.get(player, 0)
                        history = st.session_state.player_turn_history.get(player, [])
                        total_score_thrown = sum(t[0] for t in history if len(t)>2 and t[2] != "BUST")
                        avg_3_dart = (total_score_thrown / darts * 3) if darts > 0 else 0.00
                        legs = st.session_state.player_legs_won.get(player, 0)
                        sets = st.session_state.player_sets_won.get(player, 0)
                        st.markdown(f"""<div style='text-align: left; font-size: 0.9em; padding-top: 15px;'>📊Avg: {avg_3_dart:.2f}<br>Legs: {legs} | Sets: {sets}</div>""", unsafe_allow_html=True)

                    turn_total_display = ""
                    if is_current_player and partial_turn_score > 0 and not is_potential_bust:
                         turn_total_display = f"({partial_turn_score} thrown)"
                    st.markdown(f"<p style='text-align: center; font-size: 1.1em; color: blue; margin-bottom: 2px; height: 1.3em;'>{turn_total_display or '&nbsp;'}</p>", unsafe_allow_html=True)
                    last_shots = st.session_state.player_last_turn_scores.get(player, [])
                    last_turn_str = " ".join(map(str, last_shots)) if last_shots else "-"
                    last_turn_total, _, _, _ = calculate_turn_total(last_shots) if last_shots else (0,0,False, [])
                    st.markdown(f"<p style='text-align: center; font-size: 0.8em; color: grey; margin-bottom: 2px;'>Last: {last_turn_str} ({last_turn_total or 0})</p>", unsafe_allow_html=True)

                    # --- !! UPDATED HIERARCHICAL Checkout / Setup Suggestions Display !! ---
                    suggestion_text = None
                    if is_current_player and st.session_state.check_out_mode == "Double Out":
                        score_at_turn_start_disp = st.session_state.player_scores.get(player, st.session_state.starting_score)
                        current_turn_shots_list_disp = st.session_state.current_turn_shots
                        score_thrown_this_turn_disp, darts_thrown_this_turn_disp, _, _ = calculate_turn_total(current_turn_shots_list_disp)

                        if score_thrown_this_turn_disp is not None:
                            score_remaining_now_disp = score_at_turn_start_disp - score_thrown_this_turn_disp
                            darts_left_disp = 3 - darts_thrown_this_turn_disp

                            if darts_left_disp > 0 and score_remaining_now_disp >= 2:
                                found_suggestion = False
                                # --- Check Hierarchy ---
                                # 1. Check for 1-Dart Finish
                                if darts_left_disp >= 1 and score_remaining_now_disp <= 50 and score_remaining_now_disp not in BOGIE_NUMBERS_SET:
                                    checkouts_1 = get_checkouts(score_remaining_now_disp, 1)
                                    if checkouts_1:
                                        suggestion_text = f"<p style='text-align: center; font-size: 0.9em; color: #008000; font-weight: bold; margin-top: 5px;'>🎯 **Out: {checkouts_1[0][0]}** (1D)</p>"
                                        found_suggestion = True

                                # 2. Check for 2-Dart Finish
                                if not found_suggestion and darts_left_disp >= 2 and score_remaining_now_disp <= 110 and score_remaining_now_disp not in BOGIE_NUMBERS_SET:
                                    checkouts_2 = get_checkouts(score_remaining_now_disp, 2, max_suggestions=3)
                                    if checkouts_2:
                                        current_username_sugg = st.session_state.username
                                        player_prefs_list = users.get(current_username_sugg, {}).get("player_stats", {}).get(player, {}).get('preferred_doubles', [])
                                        preferred_doubles_set = set(player_prefs_list) if player_prefs_list else DEFAULT_PREFERRED_DOUBLES
                                        sorted_suggestions = sort_checkouts_by_preference(checkouts_2, preferred_doubles_set)
                                        display_text = " | ".join([" ".join(path) for path in sorted_suggestions[:2]])
                                        suggestion_text = f"<p style='text-align: center; font-size: 0.9em; color: green; margin-top: 5px;'>🎯 **Out: {display_text}** (2D)</p>"
                                        found_suggestion = True

                                # 3. Check for 3-Dart Finish
                                if not found_suggestion and darts_left_disp == 3 and score_remaining_now_disp <= 170 and score_remaining_now_disp not in BOGIE_NUMBERS_SET:
                                    checkouts_3 = get_checkouts(score_remaining_now_disp, 3, max_suggestions=3)
                                    if checkouts_3:
                                        current_username_sugg = st.session_state.username
                                        player_prefs_list = users.get(current_username_sugg, {}).get("player_stats", {}).get(player, {}).get('preferred_doubles', [])
                                        preferred_doubles_set = set(player_prefs_list) if player_prefs_list else DEFAULT_PREFERRED_DOUBLES
                                        sorted_suggestions = sort_checkouts_by_preference(checkouts_3, preferred_doubles_set)
                                        display_text = " | ".join([" ".join(path) for path in sorted_suggestions[:2]])
                                        suggestion_text = f"<p style='text-align: center; font-size: 0.9em; color: green; margin-top: 5px;'>🎯 **Out: {display_text}** (3D)</p>"
                                        found_suggestion = True

                                # 4. Suggest Setup Shot
                                if not found_suggestion and darts_left_disp == 1 and score_remaining_now_disp > 1 and score_remaining_now_disp not in BOGIE_NUMBERS_SET:
                                    setup_suggestion = get_setup_shot(score_remaining_now_disp)
                                    if setup_suggestion:
                                        suggestion_text = f"<p style='text-align: center; font-size: 0.9em; color: orange; margin-top: 5px;'>🔧 **{setup_suggestion}**</p>"
                                        found_suggestion = True

                                # 5. Handle Bogie Numbers
                                if not found_suggestion and score_remaining_now_disp in BOGIE_NUMBERS_SET:
                                     suggestion_text = "<p style='text-align: center; font-size: 0.8em; color: red; margin-top: 5px;'>No checkout</p>"
                                     found_suggestion = True

                    # Display the suggestion text or a placeholder
                    if suggestion_text:
                        st.markdown(suggestion_text, unsafe_allow_html=True)
                    else:
                        # Maintain space only if suggestions could potentially appear
                        if is_current_player and st.session_state.check_out_mode == "Double Out" and score_at_turn_start_disp >= 2:
                           st.markdown("<p style='height: 1.9em; margin-top: 5px; margin-bottom: 0;'></p>", unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True) # Close player div
                st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True) # Space between players
        else:
            st.warning("No players in game.")

    with right_col:
        # --- Input Area (Expanded - No Semicolons) ---
        if not st.session_state.game_over:
            current_player_name = "N/A"
            if st.session_state.players_selected_for_game:
                # Ensure index is valid before accessing list
                 if len(st.session_state.players_selected_for_game) > 0:
                     current_player_index_safe = st.session_state.current_player_index % len(st.session_state.players_selected_for_game)
                     current_player_name = st.session_state.players_selected_for_game[current_player_index_safe]

            st.markdown(f"**Enter Score for: {current_player_name}**")

            if "pending_modifier" not in st.session_state:
                st.session_state.pending_modifier = None
            modifier_indicator = ""
            if st.session_state.pending_modifier == "D":
                 modifier_indicator = " [**DBL**]"
            elif st.session_state.pending_modifier == "T":
                 modifier_indicator = " [**TPL**]"
            st.markdown(f"**Input:** `{ ' | '.join(st.session_state.current_turn_shots) }`{modifier_indicator}")
            num_darts_entered = len(st.session_state.current_turn_shots)
            st.caption(f"Dart {num_darts_entered + 1} of 3")
            input_disabled = num_darts_entered >= 3

            compact_button_style = """<style> div[data-testid*="stButton"] > button { margin: 1px 1px !important; padding: 1px 0px !important; height: 38px !important; font-size: 0.9em !important; min-width: 30px !important; } </style>"""
            st.markdown(compact_button_style, unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom: 2px;'></div>", unsafe_allow_html=True)
            cols_action = st.columns(4)
            double_btn_type = "primary" if st.session_state.pending_modifier == "D" else "secondary"
            if cols_action[0].button("🟡 DBL", key="pad_btn_D", help="Set Double", use_container_width=True, type=double_btn_type, disabled=input_disabled):
                st.session_state.pending_modifier = None if st.session_state.pending_modifier == "D" else "D"
                st.rerun()
            triple_btn_type = "primary" if st.session_state.pending_modifier == "T" else "secondary"
            if cols_action[1].button("🟠 TPL", key="pad_btn_T", help="Set Triple", use_container_width=True, type=triple_btn_type, disabled=input_disabled):
                st.session_state.pending_modifier = None if st.session_state.pending_modifier == "T" else "T"
                st.rerun()
            if cols_action[2].button("⬅️ Back", key="pad_btn_back", help="Remove last", use_container_width=True):
                if st.session_state.pending_modifier:
                    st.session_state.pending_modifier = None
                elif st.session_state.current_turn_shots:
                    st.session_state.current_turn_shots.pop()
                st.rerun()
            can_undo = st.session_state.get("state_before_last_turn") is not None
            if cols_action[3].button("↩️ Undo", key="pad_btn_undo", help="Undo last turn", use_container_width=True, disabled=not can_undo):
                if st.session_state.state_before_last_turn:
                    state = st.session_state.state_before_last_turn
                    undo_player_name = state["player_name"]
                    undo_player_index = state["player_index"]
                    # Restore state values
                    st.session_state.current_player_index = undo_player_index
                    st.session_state.player_scores[undo_player_name] = state["score_before"]
                    st.session_state.player_darts_thrown[undo_player_name] = state["darts_thrown_player_before"]
                    # Simple history removal
                    if st.session_state.player_turn_history.get(undo_player_name):
                         st.session_state.player_turn_history[undo_player_name].pop()
                    # Restore input buffer
                    st.session_state.current_turn_shots = state["current_turn_shots_processed"]
                    # Clear displays/flags
                    st.session_state.player_last_turn_scores[undo_player_name] = []
                    st.session_state.leg_over = False
                    st.session_state.set_over = False
                    st.session_state.game_over = False
                    st.session_state.winner = None
                    st.session_state.player_legs_won[undo_player_name] = state["legs_won_before"]
                    st.session_state.player_sets_won[undo_player_name] = state["sets_won_before"]
                    st.session_state.pending_modifier = None
                    st.session_state.message = f"Undid turn."
                    st.session_state.state_before_last_turn = None # Consume undo state
                    st.rerun()
                else:
                    st.warning("Nothing to undo.")

            st.markdown("<div style='margin-top: 3px;'></div>", unsafe_allow_html=True)
            keypad_numbers = list(range(1, 21)) + [25, 0]
            num_cols = 4
            rows_of_numbers = [keypad_numbers[i:i + num_cols] for i in range(0, len(keypad_numbers), num_cols)]
            for row in rows_of_numbers:
                cols = st.columns(num_cols)
                for i, num_val in enumerate(row):
                     if i < len(cols):
                        num_str = str(num_val)
                        is_miss_button = (num_val == 0)
                        button_text = "Miss" if is_miss_button else num_str
                        if cols[i].button(button_text, key=f"pad_btn_{num_val}", use_container_width=True, disabled=input_disabled):
                            if len(st.session_state.current_turn_shots) < 3:
                                modifier = st.session_state.pending_modifier
                                final_shot_str = num_str
                                valid_combination = True
                                if modifier == "T":
                                    if num_val <= 0 or num_val > 20:
                                        st.warning("T only 1-20")
                                        valid_combination = False
                                    else:
                                        final_shot_str = "T" + num_str
                                elif modifier == "D":
                                    if num_val <= 0 or (num_val > 20 and num_val != 25):
                                        st.warning("D only 1-20, 25")
                                        valid_combination = False
                                    else:
                                        final_shot_str = "D" + num_str

                                if valid_combination:
                                    st.session_state.current_turn_shots.append(final_shot_str)
                                    st.session_state.pending_modifier = None
                                    shots_so_far = st.session_state.current_turn_shots
                                    num_darts_now = len(shots_so_far)
                                    # Need player name for score lookup and processing call
                                    current_player_name_for_calc = "N/A"
                                    if st.session_state.players_selected_for_game:
                                        if len(st.session_state.players_selected_for_game) > 0: # Check list not empty
                                            idx_safe = st.session_state.current_player_index % len(st.session_state.players_selected_for_game)
                                            current_player_name_for_calc = st.session_state.players_selected_for_game[idx_safe]

                                    if current_player_name_for_calc != "N/A":
                                        current_score_value, _, _, _ = calculate_turn_total(shots_so_far)
                                        if current_score_value is not None: # Check calculation success
                                            potential_score_after_turn = st.session_state.player_scores[current_player_name_for_calc] - current_score_value
                                            is_potential_win = (potential_score_after_turn == 0)
                                            # Check checkout validity of THIS dart
                                            _, last_dart_double_flag_check, _, _ = parse_score_input(final_shot_str)
                                            is_valid_checkout = (st.session_state.check_out_mode != "Double Out" or last_dart_double_flag_check)

                                            # Process turn if 3 darts OR valid win
                                            if num_darts_now == 3 or (is_potential_win and is_valid_checkout):
                                                run_turn_processing(current_player_name_for_calc, shots_so_far)
                                                # run_turn_processing handles rerun
                                            else:
                                                st.rerun() # Rerun to update live score etc.
                                        else:
                                            st.error("Score calc error after input.") # Handle calculation error
                                    else:
                                         st.error("Current player error.") # Handle case player name unknown
            st.markdown("---")

        else: # If game is over
            st.info("Game over. Start new game.")
        if st.session_state.message:
            st.toast(st.session_state.message)
            st.session_state.message = ""

# --- Fallback for Unknown Page State ---
elif st.session_state.logged_in:
     st.warning("Invalid page state.")
     st.session_state.current_page = "Homepage"
     time.sleep(1)
     st.rerun()