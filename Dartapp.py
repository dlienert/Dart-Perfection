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
            # Ensure essential keys exist for each user upon loading
            for username, data in users_data.items():
                data.setdefault("password", "")
                data.setdefault("player_stats", {})
                data.setdefault("games", [])
                data.setdefault("checkout_log", [])
                data.setdefault("preferred_doubles", [])
                # Ensure stats dict has default keys for players
                for player, stats in data.get("player_stats", {}).items():
                     stats.setdefault("games_played", 0)
                     stats.setdefault("games_won", 0)
                     stats.setdefault("legs_won", 0)
                     stats.setdefault("sets_won", 0)
                     stats.setdefault("total_score", 0)
                     stats.setdefault("highest_score", 0)
                     stats.setdefault("total_turns", 0)
                     stats.setdefault("num_busts", 0)
                     stats.setdefault("darts_thrown", 0)
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
                if username in users and users[username]["password"] == hash_password(password):
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
                    users[new_username] = {
                        "password": hashed_pw, "player_stats": {}, "games": [],
                        "checkout_log": [], "preferred_doubles": []
                    }
                    save_users(users)
                    st.success("Registration successful! Please log in.")
    st.stop()

# --- Main App Area ---
# --- Sidebar ---
st.sidebar.markdown(f"👋 Welcome, **{st.session_state.username}**!")
st.sidebar.markdown("---")
page_options = ["Homepage", "Statistics", "Game", "⚙️ Settings"]
can_navigate_to_game = st.session_state.current_page == "Game" and not st.session_state.game_over
try:
    current_page_index = page_options.index(st.session_state.current_page)
except ValueError:
    current_page_index = 0
    st.session_state.current_page = "Homepage"
nav_disabled = st.session_state.current_page == "Game" and not st.session_state.game_over
chosen_page = st.sidebar.radio("Navigation", page_options, index=current_page_index, key="nav_radio", disabled=nav_disabled)
if nav_disabled and chosen_page != "Game":
    st.sidebar.warning("Finish or Quit current game first!")
elif chosen_page != st.session_state.current_page:
    st.session_state.current_page = chosen_page
    st.rerun()
elif chosen_page == "Game" and st.session_state.current_page != "Game":
    st.sidebar.warning("Start game first!")
    time.sleep(1)
    # Try to reset radio selection without rerunning immediately if possible
    # st.session_state.nav_radio = st.session_state.current_page # This might cause issues itself
    # A proper fix might involve callbacks on the radio button if direct nav prevention is needed.
    # For now, the warning is the main feedback.

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
    st.markdown(f"Configure your game, **{st.session_state.username}**!")
    game_mode_tabs = st.tabs(["X01 Game Setup", "Cricket (Coming Soon)"])
    with game_mode_tabs[0]:
        st.subheader("X01 Game Options")
        # --- CORRECTED Game Settings Columns (Multi-line) ---
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
            # Ensure player_stats dict exists safely using .get()
            if "player_stats" not in users.get(current_username_hp, {}):
                 users[current_username_hp]["player_stats"] = {}
            available_players = sorted(list(users[current_username_hp].get("player_stats", {}).keys()))
        else:
            st.error("Error: Could not retrieve user data.")

        selected_players_list = st.multiselect(
            "Select players for game (drag to reorder start)",
            options=available_players,
            default=st.session_state.players_selected_for_game,
            key="multiselect_players"
        )
        st.session_state.players_selected_for_game = selected_players_list

        with st.expander("Add New Player to Saved List"):
            new_player_name_from_input = st.text_input("New Player Name", key="new_player_name_input").strip()
            if st.button("➕ Add Player"):
                if new_player_name_from_input:
                    if current_username_hp and current_username_hp in users:
                        if new_player_name_from_input not in users[current_username_hp].get("player_stats", {}):
                            users[current_username_hp]["player_stats"][new_player_name_from_input] = {
                                "games_played": 0, "games_won": 0, "legs_won": 0, "sets_won": 0,
                                "total_score": 0, "highest_score": 0, "total_turns": 0,
                                "num_busts": 0, "darts_thrown": 0
                            }
                            save_users(users)
                            st.success(f"Player '{new_player_name_from_input}' added.")
                            st.rerun() # Refresh lists
                        else:
                            st.warning(f"Player '{new_player_name_from_input}' already exists.")
                    else:
                        st.error("Error saving player.")
                else:
                    st.warning("Please enter a name.")
        st.markdown("---")

        # --- Start Game Button ---
        if st.button("🚀 Start Game", type="primary", use_container_width=True):
            players_to_start = st.session_state.players_selected_for_game
            if not players_to_start:
                st.warning("⚠️ Select players.")
            elif not st.session_state.game_mode or st.session_state.game_mode not in [101, 201, 301, 401, 501]:
                st.warning("⚠️ Select X01 mode.")
            else:
                # Initialize Game State (Expanded)
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
    st.write(f"Stats for user: **{st.session_state.username}**")
    if "confirm_delete_player" not in st.session_state:
        st.session_state.confirm_delete_player = None
    current_username_stats = st.session_state.username
    if current_username_stats in users and "player_stats" in users.get(current_username_stats, {}):
        player_stats_data = users[current_username_stats]["player_stats"]
        if player_stats_data:
            # --- CORRECTED Stats Display Loop (Multi-line) ---
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

                if selected_stat == "Games Played": row["Value"] = games_played
                elif selected_stat == "Games Won": row["Value"] = games_won
                elif selected_stat == "Legs Won": row["Value"] = legs_won
                elif selected_stat == "Sets Won": row["Value"] = sets_won
                elif selected_stat == "Win Rate (%)": row["Value"] = f"{(games_won / games_played * 100):.2f}" if games_played > 0 else "0.00"
                elif selected_stat == "Total Score Thrown": row["Value"] = total_score
                elif selected_stat == "Avg Score per Turn": row["Value"] = f"{(total_score / total_turns):.2f}" if total_turns > 0 else "0.00"
                elif selected_stat == "Avg Score per Dart": row["Value"] = f"{(total_score / darts_thrown):.2f}" if darts_thrown > 0 else "0.00"
                elif selected_stat == "Highest Score (Turn)": row["Value"] = stats.get("highest_score", 0)
                elif selected_stat == "Total Turns": row["Value"] = total_turns
                elif selected_stat == "Darts Thrown": row["Value"] = darts_thrown
                elif selected_stat == "Busts": row["Value"] = stats.get("num_busts", 0)
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

            # --- Player Stats Deletion Section (Corrected try-except structure) ---
            st.markdown("---")
            st.subheader("⚠️ Manage Player Stats")
            players_list = sorted(list(player_stats_data.keys()))
            player_to_delete = st.selectbox(
                "Select Player to Delete Stats For:", players_list, index=None,
                placeholder="Choose...", key="delete_player_select"
            )
            delete_button_disabled = (player_to_delete is None) or (st.session_state.confirm_delete_player == player_to_delete)
            delete_button_label = f"Delete Stats for {player_to_delete}" if player_to_delete else "Delete Stats..."

            if st.button(delete_button_label, type="secondary", disabled=delete_button_disabled, key="delete_request_btn"):
                 if player_to_delete:
                     st.session_state.confirm_delete_player = player_to_delete
                     st.rerun()

            if st.session_state.confirm_delete_player:
                if player_to_delete == st.session_state.confirm_delete_player:
                    st.warning(f"**Delete all stats & logs for {st.session_state.confirm_delete_player}?** Cannot be undone.")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("✔️ Yes, Confirm", type="primary", use_container_width=True, key="confirm_delete_btn"):
                             # --- CORRECTED try-except structure ---
                            try:
                                player_name_confirmed = st.session_state.confirm_delete_player
                                # Step 1: Delete stats
                                del users[current_username_stats]["player_stats"][player_name_confirmed]
                                # Step 2: Filter logs
                                if "checkout_log" in users[current_username_stats]:
                                     users[current_username_stats]["checkout_log"] = [
                                         e for e in users[current_username_stats].get("checkout_log", [])
                                         if e.get("player") != player_name_confirmed
                                     ]
                                # Step 3: Save changes
                                save_users(users)
                                # Step 4: Success message and state reset
                                st.success(f"Deleted {player_name_confirmed}.")
                                st.session_state.confirm_delete_player = None
                                st.session_state.delete_player_select = None # Try resetting selectbox key state
                                time.sleep(1)
                                st.rerun()
                            except KeyError:
                                st.error(f"Could not delete {st.session_state.confirm_delete_player}. Not found.")
                                st.session_state.confirm_delete_player = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"An error occurred: {e}")
                                st.session_state.confirm_delete_player = None
                                st.rerun()
                    with col_cancel:
                         if st.button("❌ Cancel", type="secondary", use_container_width=True, key="cancel_delete_btn"):
                             st.session_state.confirm_delete_player = None
                             st.rerun()
                else:
                    # Selection changed, reset confirmation silently
                    st.session_state.confirm_delete_player = None

        else:
            st.info("No player stats recorded yet.")
    else:
        st.warning("Could not load stats.")


# --- Settings Page Logic ---
elif st.session_state.current_page == "⚙️ Settings":
    st.title("⚙️ User Settings")
    st.write(f"Settings for user: **{st.session_state.username}**")
    st.markdown("---")
    st.subheader("🎯 Preferred Double Outs")
    st.write("Select preferred doubles for suggestions.")

    current_username_settings = st.session_state.username
    # Load current preferences safely using .get()
    current_preferences = users.get(current_username_settings, {}).get('preferred_doubles', [])
    # Ensure loaded preferences are valid doubles
    current_preferences_formatted = [pref for pref in current_preferences if pref in ALL_POSSIBLE_DOUBLES]

    selected_doubles = st.multiselect(
        "Select preferred doubles:",
        options=ALL_POSSIBLE_DOUBLES,
        default=current_preferences_formatted,
        key="pref_doubles_multiselect"
    )

    if st.button("Save Preferences", type="primary"):
        if current_username_settings in users:
            # Ensure user dict structure exists if needed
            users.setdefault(current_username_settings, {})
            users[current_username_settings]['preferred_doubles'] = selected_doubles
            save_users(users)
            st.success("Preferences saved!")
            time.sleep(1)
            # Optionally rerun if other parts of the page need immediate update
            # st.rerun()
        else:
            st.error("Error saving: User not found.")
    st.markdown("---")


# --- Game Tab Logic ---
elif st.session_state.current_page == "Game":

    # --- Helper Functions ---
    def parse_score_input(score_str):
        # ... (Expanded, corrected return) ...
        score_str = str(score_str).upper().strip(); is_double, is_triple, value, is_valid = False, False, 0, True;
        try:
            if score_str.startswith("T"):
                if len(score_str) > 1 and score_str[1:].isdigit(): num = int(score_str[1:]); value, is_triple = (num * 3, True) if 1 <= num <= 20 else (0, False); is_valid = (1 <= num <= 20)
                else: is_valid = False
            elif score_str.startswith("D"):
                 if len(score_str) > 1 and score_str[1:].isdigit(): num = int(score_str[1:]); value, is_double = (num * 2, True) if 1 <= num <= 20 or num == 25 else (0, False); is_valid = (1 <= num <= 20 or num == 25)
                 else: is_valid = False
            elif score_str.isdigit():
                num = int(score_str); value = num if 0 <= num <= 20 or num == 25 else 0; is_valid = (0 <= num <= 20 or num == 25)
                if num == 50: st.toast("Use D25"); is_valid = False; value = 0
            else: is_valid = False
        except ValueError: is_valid = False
        return value, is_double, is_triple, is_valid # Correct return placement

    def calculate_turn_total(shots_list):
        # ... (Expanded, corrected return) ...
        total, darts_thrown_turn, last_dart_double_flag = 0, 0, False; parsed_shots_details = [];
        if not shots_list: return 0, 0, False, [];
        for i, shot_str in enumerate(shots_list):
            value, is_double, _, is_valid = parse_score_input(shot_str);
            if not is_valid: return None, 0, False, []; # Signal error if parse fails
            total += value; darts_thrown_turn += 1; last_dart_double_flag = is_double; parsed_shots_details.append({"input": shot_str, "value": value, "is_double": is_double});
        return total, darts_thrown_turn, last_dart_double_flag, parsed_shots_details; # Return after loop

    def run_turn_processing(player_name, shots_list):
        # ... (run_turn_processing code expanded to multiple lines) ...
        global users
        current_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
        current_player_index_before_turn = st.session_state.current_player_index
        score_before_turn = st.session_state.player_scores[player_name]
        st.session_state.state_before_last_turn = {
            "player_index": current_player_index_before_turn, "player_name": player_name,
            "score_before": score_before_turn,
            "darts_thrown_player_before": st.session_state.player_darts_thrown.get(player_name, 0),
            "current_turn_shots_processed": list(shots_list),
            "legs_won_before": st.session_state.player_legs_won.get(player_name, 0),
            "sets_won_before": st.session_state.player_sets_won.get(player_name, 0),
        }
        calculated_score, darts_thrown_turn, last_dart_double, _ = calculate_turn_total(shots_list)
        if calculated_score is None:
            st.error("Internal Error score calc.")
            return
        new_score = score_before_turn - calculated_score
        is_bust, is_win, valid_checkout_attempt = False, False, True
        turn_result_for_log = "UNKNOWN"

        # 1. Check Bust
        if new_score < 0 or new_score == 1:
            turn_result_for_log = "BUST"
            st.warning(f"❌ Bust! Score remains {score_before_turn}")
            st.session_state.player_scores[player_name] = score_before_turn
            st.session_state.message = f"{player_name} Busted!"
            st.session_state.player_turn_history[player_name].append((calculated_score, darts_thrown_turn, turn_result_for_log))
            st.session_state.player_last_turn_scores[player_name] = list(shots_list)
            st.session_state.player_darts_thrown[player_name] += darts_thrown_turn
            is_bust = True

        # 2. Check Win
        elif new_score == 0:
            if st.session_state.check_out_mode == "Double Out" and not last_dart_double:
                turn_result_for_log = "BUST (Invalid Checkout)"
                st.warning(f"❌ Invalid Checkout! Score remains {score_before_turn}")
                st.session_state.player_scores[player_name] = score_before_turn
                st.session_state.message = f"{player_name} Invalid Checkout!"
                st.session_state.player_turn_history[player_name].append((calculated_score, darts_thrown_turn, turn_result_for_log))
                st.session_state.player_last_turn_scores[player_name] = list(shots_list)
                st.session_state.player_darts_thrown[player_name] += darts_thrown_turn
                is_bust, valid_checkout_attempt = True, False
            else: # Valid Win
                turn_result_for_log = "WIN"
                st.success(f"🎯 Leg {st.session_state.current_leg} Won!")
                st.session_state.player_scores[player_name] = 0
                st.session_state.message = f"{player_name} won Leg!"
                st.session_state.player_turn_history[player_name].append((calculated_score, darts_thrown_turn, turn_result_for_log))
                st.session_state.player_last_turn_scores[player_name] = list(shots_list)
                st.session_state.player_darts_thrown[player_name] += darts_thrown_turn
                st.session_state.leg_over, is_win = True, True
                # Increment leg count in session state for immediate display
                st.session_state.player_legs_won[player_name] = st.session_state.player_legs_won.get(player_name, 0) + 1


        # 3. Regular Score Update
        else:
            turn_result_for_log = "OK"
            st.session_state.player_scores[player_name] = new_score
            st.session_state.message = f"{player_name} scored {calculated_score}."
            st.session_state.player_turn_history[player_name].append((calculated_score, darts_thrown_turn, turn_result_for_log))
            st.session_state.player_last_turn_scores[player_name] = list(shots_list)
            st.session_state.player_darts_thrown[player_name] += darts_thrown_turn

        # --- Logging Check ---
        is_finish_attempt_score = (2 <= score_before_turn <= 170 and score_before_turn not in BOGIE_NUMBERS_SET)
        if is_finish_attempt_score and turn_result_for_log != "OK":
            try:
                log_entry = {
                    "timestamp": current_time_str, "player": player_name, "score_before": score_before_turn,
                    "shots": list(shots_list), "calculated_score": calculated_score, "result": turn_result_for_log,
                    "last_dart_was_double": last_dart_double if turn_result_for_log == "WIN" else None,
                    "last_dart_str": shots_list[-1] if shots_list else None, "game_mode": st.session_state.game_mode,
                    "leg": st.session_state.current_leg, "set": st.session_state.current_set
                }
                current_username_log = st.session_state.username
                if "checkout_log" not in users[current_username_log]:
                    users[current_username_log]["checkout_log"] = []
                users[current_username_log]["checkout_log"].append(log_entry)
            except Exception as e:
                st.error(f"Log Error: {e}")

        # --- Save Stats ---
        if player_name in users[st.session_state.username]["player_stats"]:
            stats = users[st.session_state.username]["player_stats"][player_name]
            # Update stats based on turn result
            if is_bust and turn_result_for_log.startswith("BUST"):
                 stats["num_busts"] = stats.get("num_busts", 0) + 1
            if is_win: # Increment legs_won stat only on win
                 stats["legs_won"] = stats.get("legs_won", 0) + 1
            if is_bust or is_win or turn_result_for_log == "OK": # Common updates for any valid turn end
                stats["total_turns"] = stats.get("total_turns", 0) + 1
                stats["darts_thrown"] = stats.get("darts_thrown", 0) + darts_thrown_turn
                stats["total_score"] = stats.get("total_score", 0) + (calculated_score if calculated_score is not None else 0)
            if calculated_score is not None and calculated_score > stats.get("highest_score", 0):
                 stats["highest_score"] = calculated_score
        save_users(users) # Save after all updates for the turn

        # --- Post-Turn Advancement ---
        num_players_adv = len(st.session_state.players_selected_for_game)
        should_advance_turn = is_bust or is_win or (len(shots_list) == 3)
        if not valid_checkout_attempt and new_score == 0:
            should_advance_turn = False

        if should_advance_turn:
            index_before_advance = st.session_state.current_player_index
            if st.session_state.state_before_last_turn:
                st.session_state.state_before_last_turn["player_index"] = index_before_advance
            st.session_state.current_turn_shots = []

            if st.session_state.leg_over:
                legs_needed = math.ceil((st.session_state.legs_to_play + 1) / 2) if st.session_state.set_leg_rule == "Best of" else st.session_state.legs_to_play
                if st.session_state.player_legs_won.get(player_name, 0) >= legs_needed: # Set Win check
                    st.session_state.set_over = True
                    st.session_state.player_sets_won[player_name] = st.session_state.player_sets_won.get(player_name, 0) + 1
                    st.success(f"🎉 {player_name} wins Set {st.session_state.current_set}!")
                    if player_name in users[st.session_state.username]["player_stats"]:
                        users[st.session_state.username]["player_stats"][player_name]["sets_won"] = users[st.session_state.username]["player_stats"][player_name].get("sets_won",0)+1
                        save_users(users) # Save set win stat
                    sets_needed = math.ceil((st.session_state.sets_to_play + 1) / 2) if st.session_state.set_leg_rule == "Best of" else st.session_state.sets_to_play
                    if st.session_state.player_sets_won.get(player_name, 0) >= sets_needed: # Game Win check
                        st.session_state.game_over = True
                        st.session_state.winner = player_name
                        for p in st.session_state.players_selected_for_game:
                            if p in users[st.session_state.username]["player_stats"]:
                                stats_p=users[st.session_state.username]["player_stats"][p]
                                stats_p["games_played"] = stats_p.get("games_played", 0) + 1
                                if p == player_name:
                                     stats_p["games_won"] = stats_p.get("games_won", 0) + 1
                        save_users(users)
                        st.session_state.state_before_last_turn = None # Cannot undo after game over
                    else: # Next Set prep
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
                        st.session_state.state_before_last_turn = None # Clear undo on set transition
                else: # Next Leg prep
                    st.info("Prepare for next Leg...")
                    time.sleep(1.5)
                    st.session_state.current_leg += 1
                    st.session_state.player_scores = {p: st.session_state.starting_score for p in st.session_state.players_selected_for_game}
                    st.session_state.player_last_turn_scores = {p: [] for p in st.session_state.players_selected_for_game}
                    st.session_state.leg_over = False
                    st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
                    st.session_state.state_before_last_turn = None # Clear undo on leg transition
            else: # Leg not over, just advance player
                st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
                # Keep undo state

            st.rerun() # Rerun happens after state changes

    # --- NEW Checkout Calculation Function ---
    @st.cache_data(ttl=3600) # Cache results
    def get_checkouts(target_score, darts_left, max_suggestions=5):
        # ... (get_checkouts function definition - expanded, multi-line) ...
        if darts_left not in [1, 2, 3] or target_score < 2 or target_score > 170 or target_score in BOGIE_NUMBERS_SET:
            return []

        valid_paths = []
        throws_priority = (
            [f"T{i}" for i in range(20, 0, -1)] +
            [f"D{i}" for i in range(20, 0, -1)] + ["D25"] +
            [str(i) for i in range(20, 0, -1)] + ["25"]
        )

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


    def sort_checkouts_by_preference(paths, preferred_doubles):
        # ... (sort function definition - expanded, multi-line) ...
        preferred_paths = []
        other_paths = []
        for path in paths:
            if path and path[-1].startswith("D") and path[-1] in preferred_doubles:
                preferred_paths.append(path)
            else:
                other_paths.append(path)
        return preferred_paths + other_paths

    # --- Game Interface ---
    st.title(f"🎯 Game On: {st.session_state.game_mode} - Set {st.session_state.current_set}/{st.session_state.sets_to_play} | Leg {st.session_state.current_leg}/{st.session_state.legs_to_play}")
    st.caption(f"Mode: {st.session_state.check_out_mode} | Rule: {st.session_state.set_leg_rule}")

    # --- Main Two-Column Layout ---
    left_col, right_col = st.columns([2, 1.2])

    with left_col:
        # --- Scoreboard Display (Expanded - No Semicolons) ---
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
                                if temp_remaining_score < 0 or temp_remaining_score == 1: display_score_val, score_color, is_potential_bust = "BUST", "red", True
                                elif temp_remaining_score >= 0: display_score_val = temp_remaining_score
                        st.markdown(f"<h2 style='text-align: center; font-size: 3em; margin-bottom: 0; color: {score_color}; line-height: 1.1;'>{display_score_val}</h2>", unsafe_allow_html=True) # 3em Score
                    with col_stats:
                        darts = st.session_state.player_darts_thrown.get(player, 0); history = st.session_state.player_turn_history.get(player, []); total_score_thrown = sum(t[0] for t in history if len(t)>2 and t[2] != "BUST"); avg_3_dart = (total_score_thrown / darts * 3) if darts > 0 else 0.00; legs = st.session_state.player_legs_won.get(player, 0); sets = st.session_state.player_sets_won.get(player, 0);
                        st.markdown(f"""<div style='text-align: left; font-size: 0.9em; padding-top: 15px;'>📊Avg: {avg_3_dart:.2f}<br>Legs: {legs} | Sets: {sets}</div>""", unsafe_allow_html=True)

                    turn_total_display = ""
                    if is_current_player and partial_turn_score > 0 and not is_potential_bust: turn_total_display = f"({partial_turn_score} thrown)"
                    st.markdown(f"<p style='text-align: center; font-size: 1.1em; color: blue; margin-bottom: 2px; height: 1.3em;'>{turn_total_display or '&nbsp;'}</p>", unsafe_allow_html=True)
                    last_shots = st.session_state.player_last_turn_scores.get(player, []); last_turn_str = " ".join(map(str, last_shots)) if last_shots else "-"; last_turn_total, _, _, _ = calculate_turn_total(last_shots) if last_shots else (0,0,False, []);
                    st.markdown(f"<p style='text-align: center; font-size: 0.8em; color: grey; margin-bottom: 2px;'>Last: {last_turn_str} ({last_turn_total or 0})</p>", unsafe_allow_html=True)

                    # --- Checkout Suggestions Display ---
                    if is_current_player and st.session_state.check_out_mode == "Double Out":
                        score_at_turn_start_disp = st.session_state.player_scores.get(player, st.session_state.starting_score)
                        current_turn_shots_list_disp = st.session_state.current_turn_shots
                        score_thrown_this_turn_disp, darts_thrown_this_turn_disp, _, _ = calculate_turn_total(current_turn_shots_list_disp)
                        score_remaining_now_disp = score_at_turn_start_disp - (score_thrown_this_turn_disp if score_thrown_this_turn_disp is not None else 0)
                        darts_left_disp = 3 - darts_thrown_this_turn_disp

                        if darts_left_disp > 0 and 2 <= score_remaining_now_disp <= 170 and score_remaining_now_disp not in BOGIE_NUMBERS_SET:
                            raw_suggestions = get_checkouts(score_remaining_now_disp, darts_left_disp, max_suggestions=5)
                            current_username_sugg = st.session_state.username
                            user_prefs_list = users.get(current_username_sugg, {}).get('preferred_doubles', [])
                            preferred_doubles_set = set(user_prefs_list) if user_prefs_list else DEFAULT_PREFERRED_DOUBLES
                            sorted_suggestions = sort_checkouts_by_preference(raw_suggestions, preferred_doubles_set)

                            if sorted_suggestions:
                                display_suggestions_list = [" ".join(path) for path in sorted_suggestions[:2]]
                                display_text = " | ".join(display_suggestions_list)
                                st.markdown(f"<p style='text-align: center; font-size: 0.9em; color: green; margin-top: 5px;'>🎯 Out ({darts_left_disp}D): {display_text}</p>", unsafe_allow_html=True)
                        elif score_remaining_now_disp in BOGIE_NUMBERS_SET:
                             st.markdown("<p style='text-align: center; font-size: 0.8em; color: red; margin-top: 5px;'>No checkout</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True) # Close player div
                st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True) # Space between players
        else:
            st.warning("No players in game.")

    with right_col:
        # --- Input Area (Expanded - No Semicolons) ---
        if not st.session_state.game_over:
            if st.session_state.players_selected_for_game:
                 current_player_index_safe = st.session_state.current_player_index % len(st.session_state.players_selected_for_game)
                 current_player_name = st.session_state.players_selected_for_game[current_player_index_safe]
            else:
                 current_player_name = "N/A"

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
                    # Simple history removal (might need adjustment if history format changes)
                    if st.session_state.player_turn_history.get(undo_player_name):
                        st.session_state.player_turn_history[undo_player_name].pop()
                    # Restore input buffer
                    st.session_state.current_turn_shots = state["current_turn_shots_processed"]
                    # Clear related displays/flags
                    st.session_state.player_last_turn_scores[undo_player_name] = []
                    st.session_state.leg_over = False
                    st.session_state.set_over = False
                    st.session_state.game_over = False
                    st.session_state.winner = None
                    st.session_state.player_legs_won[undo_player_name] = state["legs_won_before"]
                    st.session_state.player_sets_won[undo_player_name] = state["sets_won_before"]
                    st.session_state.pending_modifier = None
                    st.session_state.message = f"Undid turn for {undo_player_name}."
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
                                    if num_val <= 0 or num_val > 20: st.warning("T only for 1-20"); valid_combination = False
                                    else: final_shot_str = "T" + num_str
                                elif modifier == "D":
                                    if num_val <= 0 or (num_val > 20 and num_val != 25): st.warning("D only for 1-20, 25"); valid_combination = False
                                    else: final_shot_str = "D" + num_str

                                if valid_combination:
                                    st.session_state.current_turn_shots.append(final_shot_str)
                                    st.session_state.pending_modifier = None
                                    shots_so_far = st.session_state.current_turn_shots
                                    num_darts_now = len(shots_so_far)
                                    # Check potential score AFTER this dart
                                    current_score_value, _, _, _ = calculate_turn_total(shots_so_far)
                                    potential_score_after_turn = st.session_state.player_scores[current_player_name] - (current_score_value if current_score_value is not None else 0)
                                    is_potential_win = (potential_score_after_turn == 0)
                                    # Check checkout validity of THIS dart if it's potentially winning
                                    _, last_dart_double_flag_check, _, _ = parse_score_input(final_shot_str)
                                    is_valid_checkout = (st.session_state.check_out_mode != "Double Out" or last_dart_double_flag_check)

                                    # Process turn if 3 darts OR valid win
                                    if num_darts_now == 3 or (is_potential_win and is_valid_checkout):
                                        run_turn_processing(current_player_name, shots_so_far) # Handles rerun internally
                                    else:
                                        st.rerun() # Rerun to update live score etc.
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