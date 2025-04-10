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

# --- User Authentication & Data Handling ---
def load_users():
    """Loads user data from the JSON file."""
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                users_data = json.load(f)
            # Ensure essential keys exist for each user upon loading
            for username, data in users_data.items():
                if "password" not in data: # Should always exist if saved correctly
                     users_data[username]["password"] = "" # Or handle error
                if "player_stats" not in data:
                    users_data[username]["player_stats"] = {}
                if "games" not in data: # List to store game histories maybe? (Not fully used yet)
                     users_data[username]["games"] = []
                # Ensure stats dict has default keys for players
                for player, stats in users_data[username].get("player_stats", {}).items():
                     stats.setdefault("games_played", 0)
                     stats.setdefault("games_won", 0) # Consider if this means legs or matches
                     stats.setdefault("legs_won", 0)
                     stats.setdefault("sets_won", 0)
                     stats.setdefault("total_score", 0)
                     stats.setdefault("highest_score", 0)
                     stats.setdefault("total_turns", 0)
                     stats.setdefault("num_busts", 0)
                     stats.setdefault("darts_thrown", 0)

            return users_data
        except json.JSONDecodeError:
            st.error(f"Error reading user data file ({USER_DATA_FILE}). File might be corrupt. Starting fresh.")
            return {}
        except Exception as e:
            st.error(f"An unexpected error occurred loading user data: {e}")
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

# --- Load Users at the start ---
users = load_users()

# --- Initialize Session State (Only Once Per Session) ---
if "app_initialized" not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.current_page = "Login" # Start at login page

    # Game config defaults
    st.session_state.game_mode = 501
    st.session_state.check_out_mode = "Double Out"
    st.session_state.sets_to_play = 1
    st.session_state.set_leg_rule = "First to" # ('First to' or 'Best of')
    st.session_state.check_in_mode = "Straight In" # ('Straight In' or 'Double In') - Not implemented yet
    st.session_state.legs_to_play = 1

    # List to hold players selected for the *next* game
    st.session_state.players_selected_for_game = []

    # Initialize all game runtime states to prevent errors later
    st.session_state.starting_score = 0
    st.session_state.player_scores = {}
    st.session_state.player_legs_won = {}
    st.session_state.player_sets_won = {}
    st.session_state.player_darts_thrown = {}
    st.session_state.player_turn_history = {} # {player: [(score, darts, result), ...]}
    st.session_state.player_last_turn_scores = {} # {player: [shot1, shot2, ...]}
    st.session_state.current_player_index = 0
    st.session_state.current_turn_shots = [] # Input buffer ["T20", "19", "D8"]
    st.session_state.game_over = False
    st.session_state.leg_over = False
    st.session_state.set_over = False
    st.session_state.current_leg = 1
    st.session_state.current_set = 1
    st.session_state.winner = None
    st.session_state.message = "" # For temporary messages
    st.session_state.pending_modifier = None # For Modifier -> Number input

# --- Login / Register Page ---
if not st.session_state.logged_in:
    st.session_state.current_page = "Login" # Force login page if not logged in
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
                    st.warning("Username already exists. Please choose a different one.")
                else:
                    hashed_pw = hash_password(new_password)
                    users[new_username] = {
                        "password": hashed_pw, "player_stats": {}, "games": []
                    }
                    save_users(users)
                    st.success("Registration successful! Please log in.")
    st.stop() # Stop execution here if we are on the login page

# --- Main App Area (Displayed only after successful login) ---

# --- Sidebar ---
st.sidebar.markdown(f"👋 Welcome, **{st.session_state.username}**!")
st.sidebar.markdown("---")
page_options = ["Homepage", "Statistics", "Game"]
can_navigate_to_game = st.session_state.current_page == "Game" and not st.session_state.game_over
try:
     current_page_index = page_options.index(st.session_state.current_page)
except ValueError:
     current_page_index = 0
     st.session_state.current_page = "Homepage"
chosen_page = st.sidebar.radio("Navigation", page_options, index=current_page_index, key="nav_radio")
if chosen_page != st.session_state.current_page and not (st.session_state.current_page == "Game" and not st.session_state.game_over):
     st.session_state.current_page = chosen_page
     st.rerun()
elif chosen_page == "Game" and st.session_state.current_page != "Game":
     st.sidebar.warning("Start a game from the Homepage first!")
     time.sleep(1)
     st.session_state.nav_radio = st.session_state.current_page
     st.rerun()
if st.session_state.current_page == "Game" and not st.session_state.game_over:
     st.sidebar.warning("🎯 Game in progress!")
     if st.sidebar.button("⚠️ Quit Current Game"):
          st.session_state.current_page = "Homepage"
          st.session_state.game_over = True
          st.rerun()
st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.session_state.logged_in = False
        st.session_state.app_initialized = False
        st.rerun()

# --- Page Content Area ---

# --- Homepage Tab Logic ---
if st.session_state.current_page == "Homepage":
    st.title("🎯 Darts Counter Homepage")
    st.markdown(f"Configure your game, **{st.session_state.username}**!")
    game_mode_tabs = st.tabs(["X01 Game Setup", "Cricket (Coming Soon)"])

    with game_mode_tabs[0]: # X01 Tab
        st.subheader("X01 Game Options")

        # --- Game Settings Columns ---
        col1, col2, col3 = st.columns(3)
        with col1:
            points_options = ["101", "201", "301", "401", "501"]
            try: default_points_index = points_options.index(str(st.session_state.get("game_mode", 501)))
            except ValueError: default_points_index = points_options.index("501")
            selected_points = st.selectbox("Points", points_options, index=default_points_index)
            st.session_state.game_mode = int(selected_points)
        with col2:
            checkout_options = ["Straight Out", "Double Out"]
            try: default_checkout_index = checkout_options.index(st.session_state.get("check_out_mode", "Double Out"))
            except ValueError: default_checkout_index = checkout_options.index("Double Out")
            selected_checkout = st.selectbox("Check-Out", checkout_options, index=default_checkout_index)
            st.session_state.check_out_mode = selected_checkout
        with col3:
            sets_options = list(range(1, 12))
            try: default_sets_index = sets_options.index(st.session_state.get("sets_to_play", 1))
            except ValueError: default_sets_index = sets_options.index(1)
            selected_sets = st.selectbox("Sets", sets_options, index=default_sets_index)
            st.session_state.sets_to_play = selected_sets

        col4, col5, col6 = st.columns(3)
        with col4:
            set_leg_options = ["First to", "Best of"]
            try: default_set_leg_index = set_leg_options.index(st.session_state.get("set_leg_rule", "First to"))
            except ValueError: default_set_leg_index = set_leg_options.index("First to")
            selected_set_leg = st.selectbox("Set/Leg Rule", set_leg_options, index=default_set_leg_index)
            st.session_state.set_leg_rule = selected_set_leg
        with col5:
            checkin_options = ["Straight In", "Double In"]
            try: default_checkin_index = checkin_options.index(st.session_state.get("check_in_mode", "Straight In"))
            except ValueError: default_checkin_index = checkin_options.index("Straight In")
            selected_checkin = st.selectbox("Check-In (Not Implemented)", checkin_options, index=default_checkin_index, disabled=True)
            st.session_state.check_in_mode = selected_checkin
        with col6:
            legs_options = list(range(1, 12))
            try: default_legs_index = legs_options.index(st.session_state.get("legs_to_play", 1))
            except ValueError: default_legs_index = legs_options.index(1)
            selected_legs = st.selectbox("Legs (per Set)", legs_options, index=default_legs_index)
            st.session_state.legs_to_play = selected_legs

        st.markdown("---")
        st.subheader("Select Players")
        available_players = []
        current_username = st.session_state.username # Get current user once
        if current_username and current_username in users:
            # Ensure player_stats dict exists safely
            if "player_stats" not in users.get(current_username, {}):
                 users[current_username]["player_stats"] = {}
            available_players = sorted(list(users[current_username].get("player_stats", {}).keys())) # Sort names
        else:
            st.error("Error: Could not retrieve user data for player selection.")

        selected_players_list = st.multiselect(
            "Select players for the game (drag to reorder start)",
            options=available_players,
            default=st.session_state.players_selected_for_game,
            key="multiselect_players"
        )
        st.session_state.players_selected_for_game = selected_players_list

        # --- Corrected "Add New Player" Section (Only one expander) ---
        with st.expander("Add New Player to Saved List"):
            # Use the key 'new_player_name_input' for the text_input widget
            new_player_name_from_input = st.text_input("Enter New Player Name", key="new_player_name_input").strip()

            if st.button("➕ Add New Player to List"):
                if new_player_name_from_input: # Check if something was entered
                    if current_username and current_username in users:
                        # Use the value from the input field for checks and adding
                        if new_player_name_from_input not in users[current_username].get("player_stats", {}):
                            # Add player with initial stats
                            users[current_username]["player_stats"][new_player_name_from_input] = {
                                "games_played": 0, "games_won": 0, "legs_won": 0, "sets_won": 0,
                                "total_score": 0, "highest_score": 0, "total_turns": 0,
                                "num_busts": 0, "darts_thrown": 0
                            }
                            save_users(users) # Save the updated user data
                            st.success(f"Player '{new_player_name_from_input}' added and saved.")
                            # No need to manually clear input field state due to rerun
                            st.rerun() # Rerun to update the multiselect options above
                        else:
                            st.warning(f"Player '{new_player_name_from_input}' already exists in your saved list.")
                    else:
                        # This case should ideally not happen if user is logged in
                        st.error("Error: Could not save player. User data issue.")
                else:
                    st.warning("Please enter a name for the new player.")

        st.markdown("---")

        # --- Start Game Button (Keep as it is) ---
        if st.button("🚀 Start Game", type="primary", use_container_width=True):
            players_to_start = st.session_state.players_selected_for_game
            if not players_to_start: st.warning("⚠️ Please select at least one player.")
            elif not st.session_state.game_mode or st.session_state.game_mode not in [101, 201, 301, 401, 501]: st.warning("⚠️ Please select a valid X01 game mode.")
            else:
                # --- Initialize Game State ---
                st.session_state.current_page = "Game"
                st.session_state.starting_score = st.session_state.game_mode
                # Reset all game variables
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
                st.session_state.game_over = False; st.session_state.leg_over = False; st.session_state.set_over = False
                st.session_state.winner = None; st.session_state.message = ""
                st.session_state.pending_modifier = None # Ensure modifier reset
                st.session_state.state_before_last_turn = None # Ensure undo state reset
                st.success(f"Starting {st.session_state.game_mode} game for: {', '.join(players_to_start)}")
                st.info(f"Playing {st.session_state.set_leg_rule} {st.session_state.sets_to_play} set(s), {st.session_state.set_leg_rule} {st.session_state.legs_to_play} leg(s) per set.")
                time.sleep(1.5)
                st.rerun()

    with game_mode_tabs[1]: # Cricket Tab Placeholder
        st.subheader("Cricket Options")
        st.info("🏏 Cricket game mode is planned for a future update.")

# --- Statistics Tab Logic ---
elif st.session_state.current_page == "Statistics":
    st.title("📊 Personal Statistics")
    st.write(f"Showing stats for user: **{st.session_state.username}**")

    # --- Initialize confirmation state ---
    if "confirm_delete_player" not in st.session_state:
        st.session_state.confirm_delete_player = None # Store name of player pending deletion

    current_username = st.session_state.username
    # Check if user and stats data exist
    if current_username in users and "player_stats" in users.get(current_username, {}):
        player_stats_data = users[current_username]["player_stats"]

        if player_stats_data:
            # --- Display Stats Table (Existing Code) ---
            stats_options = [
                "Games Played", "Games Won", "Legs Won", "Sets Won", "Win Rate (%)",
                "Total Score Thrown", "Avg Score per Turn", "Avg Score per Dart",
                "Highest Score (Turn)", "Total Turns", "Darts Thrown", "Busts"
            ]
            selected_stat = st.selectbox("Select Statistic to Compare", stats_options)

            table_data = []
            for player, stats in player_stats_data.items():
                row = {"Player": player}
                games_played = stats.get("games_played", 0); games_won = stats.get("games_won", 0)
                legs_won = stats.get("legs_won", 0); sets_won = stats.get("sets_won", 0)
                total_score = stats.get("total_score", 0); total_turns = stats.get("total_turns", 0)
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
                    # Sort by player name before displaying
                    df_sorted = df.sort_values(by="Player").set_index("Player")
                    st.dataframe(df_sorted, use_container_width=True)
                except Exception as e:
                    st.error(f"Error displaying statistics table: {e}")
            else:
                st.info("No data available for the selected statistic category.")

            st.markdown("---")
            st.subheader("Visualizations (Placeholder)")
            st.info("Charts and graphs will be added here in the future.")
            # ... (Placeholder for matplotlib plots) ...

            # --- Player Stats Deletion Section ---
            st.markdown("---")
            st.subheader("⚠️ Manage Player Stats")

            players_list = sorted(list(player_stats_data.keys()))

            # --- Selectbox and Button WITHOUT form ---
            player_to_delete = st.selectbox(
                "Select Player to Delete Stats For:",
                players_list,
                index=None, # Start with no selection
                placeholder="Choose a player...",
                key="delete_player_select" # Key is important to potentially reset it
            )

            # Regular button, disable logic depends on selection and confirmation state
            delete_button_disabled = (player_to_delete is None) or (st.session_state.confirm_delete_player == player_to_delete)
            delete_button_label = f"Delete Stats for {player_to_delete}" if player_to_delete else "Delete Stats for Selected Player"

            if st.button(delete_button_label, type="secondary", disabled=delete_button_disabled, key="delete_request_btn"):
                 # This code runs ONLY when the button is clickable AND clicked
                 if player_to_delete: # Should always be true if button wasn't disabled, but check again
                    st.session_state.confirm_delete_player = player_to_delete
                    st.rerun() # Trigger rerun to show confirmation message

            # --- Confirmation Step ---
            if st.session_state.confirm_delete_player:
                # Ensure the confirmation matches the currently selected player in the box
                if player_to_delete == st.session_state.confirm_delete_player:
                    st.warning(f"**Are you sure you want to permanently delete all stats and checkout logs for {st.session_state.confirm_delete_player}?** This cannot be undone.")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("✔️ Yes, Confirm Deletion", type="primary", use_container_width=True, key="confirm_delete_btn"):
                            try:
                                player_name_confirmed = st.session_state.confirm_delete_player
                                del users[current_username]["player_stats"][player_name_confirmed]
                                if "checkout_log" in users[current_username]:
                                     users[current_username]["checkout_log"] = [entry for entry in users[current_username].get("checkout_log", []) if entry.get("player") != player_name_confirmed]
                                save_users(users)
                                st.success(f"Successfully deleted stats for {player_name_confirmed}.")
                                st.session_state.confirm_delete_player = None
                                # Reset selectbox selection by changing its underlying value via key if needed
                                # Setting state variable bound by 'key' to None might not reset Selectbox index=None correctly.
                                # Often just letting the rerun happen after deletion is enough as the player is gone.
                                time.sleep(1)
                                st.rerun()
                            except KeyError:
                                 st.error(f"Could not delete {player_name_confirmed}. Player stats not found.")
                                 st.session_state.confirm_delete_player = None; st.rerun()
                            except Exception as e:
                                 st.error(f"An error occurred: {e}")
                                 st.session_state.confirm_delete_player = None; st.rerun()
                    with col_cancel:
                         if st.button("❌ Cancel", type="secondary", use_container_width=True, key="cancel_delete_btn"):
                             st.session_state.confirm_delete_player = None
                             st.rerun()
                else:
                     # If user changed selection in dropdown *after* clicking delete once, but *before* confirming.
                     # Silently reset the confirmation state.
                     st.session_state.confirm_delete_player = None
                     # The selectbox change should trigger a rerun itself, showing the correct state.

        else: # If player_stats_data is empty
            st.info("No player statistics recorded yet for your profile.")

    else: # If user or player_stats key doesn't exist
        st.warning("Could not load statistics. User data not found or profile has no stats.")

# --- Game Tab Logic ---
elif st.session_state.current_page == "Game":

    # --- Helper Functions (DEFINED AT THE TOP) ---
    def parse_score_input(score_str):
        # ... (Definition bleibt unverändert) ...
        score_str = str(score_str).upper().strip()
        is_double, is_triple, value, is_valid = False, False, 0, True
        try:
            if score_str.startswith("T"):
                if len(score_str) > 1 and score_str[1:].isdigit(): num = int(score_str[1:]); value, is_triple = (num * 3, True) if 1 <= num <= 20 else (0, False); is_valid = (1 <= num <= 20)
                else: is_valid = False
            elif score_str.startswith("D"):
                 if len(score_str) > 1 and score_str[1:].isdigit(): num = int(score_str[1:]); value, is_double = (num * 2, True) if 1 <= num <= 20 or num == 25 else (0, False); is_valid = (1 <= num <= 20 or num == 25)
                 else: is_valid = False
            elif score_str.isdigit():
                num = int(score_str); value = num if 0 <= num <= 20 or num == 25 else 0; is_valid = (0 <= num <= 20 or num == 25)
                if num == 50: st.toast("Enter Bullseye as D25"); is_valid = False; value = 0
            else: is_valid = False
        except ValueError: is_valid = False
        return value, is_double, is_triple, is_valid

    def calculate_turn_total(shots_list):
        # ... (Definition bleibt unverändert) ...
        total, darts_thrown_turn, last_dart_double_flag = 0, 0, False
        parsed_shots_details = []
        if not shots_list: return 0, 0, False, []
        for i, shot_str in enumerate(shots_list):
            value, is_double, _, is_valid = parse_score_input(shot_str)
            if not is_valid: return None, 0, False, []
            total += value; darts_thrown_turn += 1; last_dart_double_flag = is_double
            parsed_shots_details.append({"input": shot_str, "value": value, "is_double": is_double})
        return total, darts_thrown_turn, last_dart_double_flag, parsed_shots_details

    def run_turn_processing(player_name, shots_list):
        # ... (Definition bleibt unverändert - includes logging) ...
        global users; current_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
        current_player_index_before_turn = st.session_state.current_player_index
        score_before_turn = st.session_state.player_scores[player_name]
        st.session_state.state_before_last_turn = { "player_index": current_player_index_before_turn, "player_name": player_name, "score_before": score_before_turn, "darts_thrown_player_before": st.session_state.player_darts_thrown.get(player_name, 0), "current_turn_shots_processed": list(shots_list), "legs_won_before": st.session_state.player_legs_won.get(player_name, 0), "sets_won_before": st.session_state.player_sets_won.get(player_name, 0),}
        calculated_score, darts_thrown_turn, last_dart_double, _ = calculate_turn_total(shots_list)
        if calculated_score is None: st.error("Internal Error during score calculation."); return
        new_score = score_before_turn - calculated_score
        is_bust, is_win, valid_checkout_attempt = False, False, True; turn_result_for_log = "UNKNOWN"
        if new_score < 0 or new_score == 1: turn_result_for_log = "BUST"; st.warning(f"❌ Bust! Score remains {score_before_turn}"); st.session_state.player_scores[player_name] = score_before_turn; st.session_state.message = f"{player_name} Busted!"; st.session_state.player_turn_history[player_name].append((calculated_score, darts_thrown_turn, turn_result_for_log)); st.session_state.player_last_turn_scores[player_name] = list(shots_list); st.session_state.player_darts_thrown[player_name] += darts_thrown_turn; is_bust = True;
        elif new_score == 0:
            if st.session_state.check_out_mode == "Double Out" and not last_dart_double: turn_result_for_log = "BUST (Invalid Checkout)"; st.warning(f"❌ Invalid Checkout! Must finish on a Double. Score remains {score_before_turn}"); st.session_state.player_scores[player_name] = score_before_turn; st.session_state.message = f"{player_name} Invalid Checkout!"; st.session_state.player_turn_history[player_name].append((calculated_score, darts_thrown_turn, turn_result_for_log)); st.session_state.player_last_turn_scores[player_name] = list(shots_list); st.session_state.player_darts_thrown[player_name] += darts_thrown_turn; is_bust, valid_checkout_attempt = True, False;
            else: turn_result_for_log = "WIN"; st.success(f"🎯 Game Shot! {player_name} wins Leg {st.session_state.current_leg}!"); st.session_state.player_scores[player_name] = 0; st.session_state.message = f"{player_name} won Leg {st.session_state.current_leg}!"; st.session_state.player_turn_history[player_name].append((calculated_score, darts_thrown_turn, turn_result_for_log)); st.session_state.player_last_turn_scores[player_name] = list(shots_list); st.session_state.player_darts_thrown[player_name] += darts_thrown_turn; st.session_state.leg_over, is_win = True, True; st.session_state.player_legs_won[player_name] += 1;
        else: turn_result_for_log = "OK"; st.session_state.player_scores[player_name] = new_score; st.session_state.message = f"{player_name} scored {calculated_score}. {new_score} left."; st.session_state.player_turn_history[player_name].append((calculated_score, darts_thrown_turn, turn_result_for_log)); st.session_state.player_last_turn_scores[player_name] = list(shots_list); st.session_state.player_darts_thrown[player_name] += darts_thrown_turn;
        # Logging Check
        is_finish_attempt_score = (2 <= score_before_turn <= 170 and score_before_turn not in BOGIE_NUMBERS_SET) # Use Bogie Set
        if is_finish_attempt_score and turn_result_for_log != "OK":
            try:
                log_entry = {"timestamp": current_time_str, "player": player_name, "score_before": score_before_turn, "shots": list(shots_list), "calculated_score": calculated_score, "result": turn_result_for_log, "last_dart_was_double": last_dart_double if turn_result_for_log == "WIN" else None, "last_dart_str": shots_list[-1] if shots_list else None, "game_mode": st.session_state.game_mode, "leg": st.session_state.current_leg, "set": st.session_state.current_set}
                current_username = st.session_state.username;
                if "checkout_log" not in users[current_username]: users[current_username]["checkout_log"] = []
                users[current_username]["checkout_log"].append(log_entry)
            except Exception as e: st.error(f"Error logging checkout attempt: {e}")
        # Save Stats (including potential logs)
        if player_name in users[st.session_state.username]["player_stats"]:
             stats = users[st.session_state.username]["player_stats"][player_name]
             if is_bust and turn_result_for_log == "BUST": stats["num_busts"] += 1 # Only count 'real' busts
             elif is_bust and turn_result_for_log == "BUST (Invalid Checkout)": stats["num_busts"] += 1 # Count invalid checkout as bust stat too? Or separate? Let's count it.
             elif is_win: stats["legs_won"] += 1; # Increment leg win count
             if is_bust or is_win or turn_result_for_log == "OK": stats["total_turns"] += 1; stats["darts_thrown"] += darts_thrown_turn; stats["total_score"] += calculated_score;
             if calculated_score is not None and calculated_score > stats.get("highest_score", 0): stats["highest_score"] = calculated_score
        save_users(users)
        # Post-Turn Advancement Logic
        num_players_adv = len(st.session_state.players_selected_for_game)
        should_advance_turn = is_bust or is_win or (len(shots_list) == 3)
        if not valid_checkout_attempt and new_score == 0: should_advance_turn = False
        if should_advance_turn:
            index_before_advance = st.session_state.current_player_index
            if st.session_state.state_before_last_turn: st.session_state.state_before_last_turn["player_index"] = index_before_advance
            st.session_state.current_turn_shots = []
            if st.session_state.leg_over:
                 legs_needed = math.ceil((st.session_state.legs_to_play + 1) / 2) if st.session_state.set_leg_rule == "Best of" else st.session_state.legs_to_play
                 if st.session_state.player_legs_won[player_name] >= legs_needed: # Set Win
                      st.session_state.set_over = True; st.session_state.player_sets_won[player_name] += 1; st.success(f"🎉 {player_name} wins Set {st.session_state.current_set}!")
                      if player_name in users[st.session_state.username]["player_stats"]: users[st.session_state.username]["player_stats"][player_name]["sets_won"] += 1; save_users(users)
                      sets_needed = math.ceil((st.session_state.sets_to_play + 1) / 2) if st.session_state.set_leg_rule == "Best of" else st.session_state.sets_to_play
                      if st.session_state.player_sets_won[player_name] >= sets_needed: # Game Win
                           st.session_state.game_over, st.session_state.winner = True, player_name
                           for p in st.session_state.players_selected_for_game:
                               if p in users[st.session_state.username]["player_stats"]: stats_p=users[st.session_state.username]["player_stats"][p]; stats_p["games_played"] += 1;
                               if p == player_name: stats_p["games_won"] += 1
                           save_users(users); st.session_state.state_before_last_turn = None
                      else: # Next Set
                           st.info("Prepare for next Set..."); time.sleep(1.5); st.session_state.current_set += 1; st.session_state.current_leg = 1
                           st.session_state.player_scores = {p: st.session_state.starting_score for p in st.session_state.players_selected_for_game}
                           st.session_state.player_legs_won = {p: 0 for p in st.session_state.players_selected_for_game}; st.session_state.player_last_turn_scores = {p: [] for p in st.session_state.players_selected_for_game}
                           st.session_state.leg_over, st.session_state.set_over = False, False; st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
                           st.session_state.state_before_last_turn = None
                 else: # Next Leg
                      st.info("Prepare for next Leg..."); time.sleep(1.5); st.session_state.current_leg += 1
                      st.session_state.player_scores = {p: st.session_state.starting_score for p in st.session_state.players_selected_for_game}
                      st.session_state.player_last_turn_scores = {p: [] for p in st.session_state.players_selected_for_game}; st.session_state.leg_over = False
                      st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
                      st.session_state.state_before_last_turn = None
            else: # Leg not over, advance player
                 st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
            st.rerun()


    # --- Bogie Numbers Set ---
    BOGIE_NUMBERS_SET = {169, 168, 166, 165, 163, 162, 159}

    # --- Default Preferred Doubles (Temporary for Testing) ---
    # Using your "right side" example + D20/D16 as common ones
    DEFAULT_PREFERRED_DOUBLES = {"D18", "D4", "D13", "D6", "D10", "D15", "D2", "D17", "D3", "D20", "D16", "D8"}

    # --- NEW: Helper Function to get value from throw string ---
    def get_throw_value(throw_str):
        val, _, _, is_valid = parse_score_input(throw_str)
        return val if is_valid else 0 # Return 0 for invalid inputs? Or handle error?

    # --- NEW: Dynamic Checkout Calculation Function ---
    def get_checkouts(target_score, darts_left, max_suggestions=5):
        """ Calculates possible checkout paths ending on a double. """
        if darts_left not in [1, 2, 3] or target_score < 2 or target_score > 170 or target_score in BOGIE_NUMBERS_SET:
            return []

        valid_paths = []

        # --- 1 Dart Left ---
        if darts_left == 1:
            val, is_double, _, is_valid = parse_score_input(f"D{target_score // 2}") # Try the direct double
            if is_valid and val == target_score and is_double:
                return [[f"D{target_score // 2}" if target_score != 50 else "D25"]] # Standard notation D25 for Bull
            else:
                return []

        # --- 2 Darts Left ---
        if darts_left >= 2:
            # Iterate possible first throws (prioritize common setup throws)
            # Singles 1-20, 25; Triples T1-T20
            possible_first_throws = [f"T{i}" for i in range(20, 0, -1)] + \
                                    [str(i) for i in range(20, 0, -1)] + ["25"]

            for throw1 in possible_first_throws:
                val1 = get_throw_value(throw1)
                if val1 < target_score: # Must leave score >= 2 for double out
                    remaining_score1 = target_score - val1
                    # Check if remaining score can be finished with 1 dart (must be a double)
                    one_dart_finish_list = get_checkouts(remaining_score1, 1) # Call recursively for 1 dart
                    if one_dart_finish_list: # If a one-dart finish exists
                        valid_paths.append([throw1, one_dart_finish_list[0][0]])
                        if len(valid_paths) >= max_suggestions: break # Stop if enough found
            # Add direct 2-dart checkouts if any (e.g. T10 D16 for 62) - covered by loop

        # --- 3 Darts Left ---
        if darts_left == 3 and len(valid_paths) < max_suggestions:
             # Iterate possible first throws again
             possible_first_throws_3d = [f"T{i}" for i in range(20, 10, -1)] + \
                                        [str(i) for i in range(20, 10, -1)] + ["25"] + \
                                        [f"T{i}" for i in range(10, 0, -1)] + \
                                        [str(i) for i in range(10, 0, -1)] # Wider range for 3 darts

             for throw1 in possible_first_throws_3d:
                 val1 = get_throw_value(throw1)
                 if val1 < target_score:
                     remaining_score1 = target_score - val1
                     # Now check if remaining_score1 can be finished in 2 darts
                     two_dart_finishes = get_checkouts(remaining_score1, 2, max_suggestions=1) # Find just one 2-dart way is enough
                     if two_dart_finishes:
                         # Prepend throw1 to the found 2-dart finish path
                         full_path = [throw1] + two_dart_finishes[0]
                         if full_path not in valid_paths: # Avoid duplicates
                             valid_paths.append(full_path)
                             if len(valid_paths) >= max_suggestions: break # Stop if enough found
                 if len(valid_paths) >= max_suggestions: break # Stop outer loop too

        return valid_paths


    # --- NEW: Sort checkouts based on preference ---
    def sort_checkouts_by_preference(paths, preferred_doubles):
        """ Sorts checkout paths, putting those ending in preferred doubles first. """
        preferred_paths = []
        other_paths = []
        for path in paths:
            if path: # Ensure path is not empty
                last_dart = path[-1]
                # Check if last dart is a double and is in the preferred set
                if last_dart.startswith("D") and last_dart in preferred_doubles:
                    preferred_paths.append(path)
                else:
                    other_paths.append(path)
        return preferred_paths + other_paths

    # --- Check Game State ---
    if st.session_state.game_over:
        # ... (Game over display code) ...
        st.title("🎉 Game Over! 🎉");
        if st.session_state.winner: st.header(f"🏆 Winner: {st.session_state.winner} 🏆");
        else: st.header("Match finished.");
        st.balloons();
        if st.button("Play Again / New Game Setup", use_container_width=True): st.session_state.current_page = "Homepage"; st.session_state.players_selected_for_game = []; st.rerun();
        st.stop();

    if not st.session_state.players_selected_for_game:
        # ... (No players selected error) ...
        st.error("No players selected. Go to Homepage to start.");
        if st.button("🏠 Back to Homepage", use_container_width=True): st.session_state.current_page = "Homepage"; st.rerun();
        st.stop();

    # --- Game Interface ---
    st.title(f"🎯 Game On: {st.session_state.game_mode} - Set {st.session_state.current_set}/{st.session_state.sets_to_play} | Leg {st.session_state.current_leg}/{st.session_state.legs_to_play}")
    st.caption(f"Mode: {st.session_state.check_out_mode} | Rule: {st.session_state.set_leg_rule}")

    # --- Main Two-Column Layout ---
    left_col, right_col = st.columns([2, 1.2])

    with left_col:
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
                        display_score_val, score_color = actual_score, "black"; is_potential_bust = False; partial_turn_score = 0
                        # --- Live Score Calculation ---
                        if is_current_player and st.session_state.current_turn_shots:
                            partial_turn_score_calc, _, _, _ = calculate_turn_total(st.session_state.current_turn_shots)
                            if partial_turn_score_calc is not None:
                                partial_turn_score = partial_turn_score_calc
                                temp_remaining_score = actual_score - partial_turn_score
                                if temp_remaining_score < 0 or temp_remaining_score == 1: display_score_val, score_color, is_potential_bust = "BUST", "red", True
                                elif temp_remaining_score >= 0: display_score_val = temp_remaining_score
                        st.markdown(f"<h2 style='text-align: center; font-size: 3em; margin-bottom: 0; color: {score_color}; line-height: 1.1;'>{display_score_val}</h2>", unsafe_allow_html=True)

                    with col_stats:
                         # Display Avg/Legs/Sets
                        darts = st.session_state.player_darts_thrown.get(player, 0); history = st.session_state.player_turn_history.get(player, [])
                        total_score_thrown = sum(t[0] for t in history if len(t)>2 and t[2] != "BUST")
                        avg_3_dart = (total_score_thrown / darts * 3) if darts > 0 else 0.00
                        legs = st.session_state.player_legs_won.get(player, 0); sets = st.session_state.player_sets_won.get(player, 0)
                        st.markdown(f"""<div style='text-align: left; font-size: 0.9em; padding-top: 15px;'>📊Avg: {avg_3_dart:.2f}<br>Legs: {legs} | Sets: {sets}</div>""", unsafe_allow_html=True)

                    # Display Current Turn Total
                    turn_total_display = ""
                    if is_current_player and partial_turn_score > 0 and not is_potential_bust: turn_total_display = f"({partial_turn_score} thrown)"
                    st.markdown(f"<p style='text-align: center; font-size: 1.1em; color: blue; margin-bottom: 2px; height: 1.3em;'>{turn_total_display or '&nbsp;'}</p>", unsafe_allow_html=True)

                    # Display Last Turn
                    last_shots = st.session_state.player_last_turn_scores.get(player, []); last_turn_str = " ".join(map(str, last_shots)) if last_shots else "-"
                    last_turn_total, _, _, _ = calculate_turn_total(last_shots) if last_shots else (0,0,False, [])
                    st.markdown(f"<p style='text-align: center; font-size: 0.8em; color: grey; margin-bottom: 2px;'>Last: {last_turn_str} ({last_turn_total or 0})</p>", unsafe_allow_html=True)

                    # --- !! UPDATED Checkout Suggestions Display !! ---
                    if is_current_player and st.session_state.check_out_mode == "Double Out":
                        # Calculate remaining score based on darts already thrown this turn
                        score_at_turn_start = st.session_state.player_scores.get(player, st.session_state.starting_score)
                        current_turn_shots_list = st.session_state.current_turn_shots
                        score_thrown_this_turn, darts_thrown_this_turn, _, _ = calculate_turn_total(current_turn_shots_list)

                        score_remaining_now = score_at_turn_start
                        if score_thrown_this_turn is not None:
                            score_remaining_now -= score_thrown_this_turn

                        darts_left = 3 - darts_thrown_this_turn

                        # Only show suggestions if score is valid and darts are left
                        if darts_left > 0 and 2 <= score_remaining_now <= 170 and score_remaining_now not in BOGIE_NUMBERS_SET:
                            # Get potential checkouts using the new function
                            raw_suggestions = get_checkouts(score_remaining_now, darts_left)

                            # --- Load preferences (using default for now) ---
                            # Later, load from users[st.session_state.username]['preferences']
                            preferred_doubles_set = DEFAULT_PREFERRED_DOUBLES

                            # Sort suggestions based on preference
                            sorted_suggestions = sort_checkouts_by_preference(raw_suggestions, preferred_doubles_set)

                            if sorted_suggestions:
                                display_suggestions_list = []
                                for path in sorted_suggestions[:2]: # Show top 2 sorted suggestions
                                    display_suggestions_list.append(" ".join(path))
                                display_text = " | ".join(display_suggestions_list)
                                st.markdown(f"<p style='text-align: center; font-size: 0.9em; color: green; margin-top: 5px;'>🎯 **Out ({darts_left} Darts): {display_text}**</p>", unsafe_allow_html=True)
                            # else: No suggestions found by algorithm
                                # st.markdown("<p style='text-align: center; font-size: 0.8em; color: orange; margin-top: 5px;'>No common out</p>", unsafe_allow_html=True)

                        elif score_remaining_now in BOGIE_NUMBERS_SET:
                             st.markdown("<p style='text-align: center; font-size: 0.8em; color: red; margin-top: 5px;'>No checkout</p>", unsafe_allow_html=True)
                        # No suggestion shown if score > 170 or < 2 or no darts left

                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        else:
            st.warning("No players in the current game to display scoreboard.")

    with right_col:
        # --- Input Area (in Right Column - unchanged) ---
        if not st.session_state.game_over:
            # ... (Input area code: player name, input display, buttons, grid logic) ...
            # ... (This block remains the same as the last working version) ...
            if st.session_state.players_selected_for_game:
                 current_player_index_safe = st.session_state.current_player_index % len(st.session_state.players_selected_for_game)
                 current_player_name = st.session_state.players_selected_for_game[current_player_index_safe]
            else: current_player_name = "N/A"
            st.markdown(f"**Enter Score for: {current_player_name}**")
            if "pending_modifier" not in st.session_state: st.session_state.pending_modifier = None
            modifier_indicator = ""
            if st.session_state.pending_modifier == "D": modifier_indicator = " [**DBL**]"
            elif st.session_state.pending_modifier == "T": modifier_indicator = " [**TPL**]"
            st.markdown(f"**Input:** `{ ' | '.join(st.session_state.current_turn_shots) }`{modifier_indicator}")
            num_darts_entered = len(st.session_state.current_turn_shots)
            st.caption(f"Dart {num_darts_entered + 1} of 3")
            input_disabled = num_darts_entered >= 3
            compact_button_style = """<style> div[data-testid*="stButton"] > button { margin: 1px 1px !important; padding: 1px 0px !important; height: 38px !important; font-size: 0.9em !important; min-width: 30px !important; } </style>"""
            st.markdown(compact_button_style, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 2px;'></div>", unsafe_allow_html=True)
            cols_action = st.columns(4)
            double_btn_type = "primary" if st.session_state.pending_modifier == "D" else "secondary"
            if cols_action[0].button("🟡 DBL", key="pad_btn_D", help="Set next dart as Double", use_container_width=True, type=double_btn_type, disabled=input_disabled): st.session_state.pending_modifier = None if st.session_state.pending_modifier == "D" else "D"; st.rerun()
            triple_btn_type = "primary" if st.session_state.pending_modifier == "T" else "secondary"
            if cols_action[1].button("🟠 TPL", key="pad_btn_T", help="Set next dart as Triple", use_container_width=True, type=triple_btn_type, disabled=input_disabled): st.session_state.pending_modifier = None if st.session_state.pending_modifier == "T" else "T"; st.rerun()
            if cols_action[2].button("⬅️ Back", key="pad_btn_back", help="Remove last input or clear modifier", use_container_width=True):
                if st.session_state.pending_modifier: st.session_state.pending_modifier = None
                elif st.session_state.current_turn_shots: st.session_state.current_turn_shots.pop()
                st.rerun()
            can_undo = st.session_state.get("state_before_last_turn") is not None
            if cols_action[3].button("↩️ Undo", key="pad_btn_undo", help="Undo last completed turn", use_container_width=True, disabled=not can_undo):
                if st.session_state.state_before_last_turn: state = st.session_state.state_before_last_turn; undo_player_name = state["player_name"]; undo_player_index = state["player_index"]; st.session_state.current_player_index = undo_player_index; st.session_state.player_scores[undo_player_name] = state["score_before"]; st.session_state.player_darts_thrown[undo_player_name] = state["darts_thrown_player_before"];
                if st.session_state.player_turn_history.get(undo_player_name): st.session_state.player_turn_history[undo_player_name].pop(); st.session_state.current_turn_shots = state["current_turn_shots_processed"]; st.session_state.player_last_turn_scores[undo_player_name] = []; st.session_state.leg_over = False; st.session_state.set_over = False; st.session_state.game_over = False; st.session_state.winner = None; st.session_state.player_legs_won[undo_player_name] = state["legs_won_before"]; st.session_state.player_sets_won[undo_player_name] = state["sets_won_before"]; st.session_state.pending_modifier = None; st.session_state.message = f"Undid last turn for {undo_player_name}. Enter correct score."; st.session_state.state_before_last_turn = None; st.rerun()
                else: st.warning("Nothing to undo.")
            st.markdown("<div style='margin-top: 3px;'></div>", unsafe_allow_html=True)
            keypad_numbers = list(range(1, 21)) + [25, 0]; num_cols = 4
            rows_of_numbers = [keypad_numbers[i:i + num_cols] for i in range(0, len(keypad_numbers), num_cols)]
            for row in rows_of_numbers:
                cols = st.columns(num_cols)
                for i, num_val in enumerate(row):
                     if i < len(cols):
                        num_str = str(num_val); is_miss_button = (num_val == 0)
                        if cols[i].button("Miss" if is_miss_button else num_str, key=f"pad_btn_{num_val}", use_container_width=True, disabled=input_disabled):
                            if len(st.session_state.current_turn_shots) < 3:
                                modifier = st.session_state.pending_modifier; final_shot_str = num_str; valid_combination = True
                                if modifier == "T":
                                    if num_val <= 0 or num_val > 20: st.warning("Can only Triple 1-20."); valid_combination = False
                                    else: final_shot_str = "T" + num_str
                                elif modifier == "D":
                                    if num_val <= 0 or (num_val > 20 and num_val != 25): st.warning("Can only Double 1-20 or Bull (25)."); valid_combination = False
                                    else: final_shot_str = "D" + num_str
                                if valid_combination:
                                    st.session_state.current_turn_shots.append(final_shot_str); st.session_state.pending_modifier = None
                                    shots_so_far = st.session_state.current_turn_shots; num_darts_now = len(shots_so_far)
                                    current_score_value, _, _, _ = calculate_turn_total(shots_so_far)
                                    potential_score_after_turn = st.session_state.player_scores[current_player_name] - (current_score_value if current_score_value is not None else 0)
                                    is_potential_win = (potential_score_after_turn == 0)
                                    _, last_dart_double_flag_check, _, _ = parse_score_input(final_shot_str)
                                    is_valid_checkout = (st.session_state.check_out_mode != "Double Out" or last_dart_double_flag_check)
                                    if num_darts_now == 3 or (is_potential_win and is_valid_checkout): run_turn_processing(current_player_name, shots_so_far)
                                    else: st.rerun()
            st.markdown("---")
        else: # If game is over
            st.info("Game has finished. Start a new game from the Homepage.")
        # Display temporary messages (toast)
        if st.session_state.message: st.toast(st.session_state.message); st.session_state.message = ""

# --- Fallback for Unknown Page State ---
elif st.session_state.logged_in:
     st.warning("Invalid page state detected. Returning to Homepage."); st.session_state.current_page = "Homepage"; time.sleep(1); st.rerun()