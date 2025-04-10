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
    st.session_state.current_turn_shots = [] # Input buffer [score_str, 'D', 'T', ...]
    st.session_state.game_over = False
    st.session_state.leg_over = False
    st.session_state.set_over = False
    st.session_state.current_leg = 1
    st.session_state.current_set = 1
    st.session_state.winner = None
    st.session_state.message = "" # For temporary messages

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
                    # Clear potentially stale game selection if logging in again
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
                        "password": hashed_pw,
                        "player_stats": {}, # Initialize empty stats
                        "games": []
                    }
                    save_users(users)
                    st.success("Registration successful! Please log in.")
                    # Clear form fields if needed by resetting keys? Might not be necessary with tabs.
    st.stop() # Stop execution here if we are on the login page

# --- Main App Area (Displayed only after successful login) ---

# --- Sidebar ---
st.sidebar.markdown(f"👋 Welcome, **{st.session_state.username}**!")
st.sidebar.markdown("---")

# Page Navigation
page_options = ["Homepage", "Statistics", "Game"]
# Disable 'Game' navigation if not actively in a game or if game is over
can_navigate_to_game = st.session_state.current_page == "Game" and not st.session_state.game_over

# Determine default index based on current page
try:
     current_page_index = page_options.index(st.session_state.current_page)
except ValueError:
     current_page_index = 0 # Default to Homepage if current page is weird
     st.session_state.current_page = "Homepage"

# Use radio buttons for navigation
chosen_page = st.sidebar.radio(
     "Navigation",
     page_options,
     index=current_page_index,
     key="nav_radio"
)

# Update current page based on navigation, except when game is active
if chosen_page != st.session_state.current_page and not (st.session_state.current_page == "Game" and not st.session_state.game_over):
     st.session_state.current_page = chosen_page
     st.rerun()
elif chosen_page == "Game" and st.session_state.current_page != "Game":
     st.sidebar.warning("Start a game from the Homepage first!")
     # Prevent navigating to Game directly if not started
     time.sleep(1) # Let user see message
     st.session_state.nav_radio = st.session_state.current_page # Reset radio selection back
     st.rerun()


# Game Status / Quit Button in Sidebar
if st.session_state.current_page == "Game" and not st.session_state.game_over:
     st.sidebar.warning("🎯 Game in progress!")
     if st.sidebar.button("⚠️ Quit Current Game"):
          # Optional: Ask for confirmation
          st.session_state.current_page = "Homepage"
          st.session_state.game_over = True # Mark game as over
          # Consider resetting game state variables here if needed
          st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
        # Clear session state, log out
        for key in list(st.session_state.keys()):
             del st.session_state[key] # Clear everything
        st.session_state.logged_in = False
        st.session_state.app_initialized = False # Allow re-initialization
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
            try:
                default_points_index = points_options.index(str(st.session_state.get("game_mode", 501)))
            except ValueError: default_points_index = points_options.index("501")
            selected_points = st.selectbox("Points", points_options, index=default_points_index)
            st.session_state.game_mode = int(selected_points)

        with col2:
            checkout_options = ["Straight Out", "Double Out"]
            try:
                default_checkout_index = checkout_options.index(st.session_state.get("check_out_mode", "Double Out"))
            except ValueError: default_checkout_index = checkout_options.index("Double Out")
            selected_checkout = st.selectbox("Check-Out", checkout_options, index=default_checkout_index)
            st.session_state.check_out_mode = selected_checkout

        with col3:
            sets_options = list(range(1, 12)) # Max 11 sets
            try:
                default_sets_index = sets_options.index(st.session_state.get("sets_to_play", 1))
            except ValueError: default_sets_index = sets_options.index(1)
            selected_sets = st.selectbox("Sets", sets_options, index=default_sets_index)
            st.session_state.sets_to_play = selected_sets

        col4, col5, col6 = st.columns(3)
        with col4:
            set_leg_options = ["First to", "Best of"]
            try:
                 default_set_leg_index = set_leg_options.index(st.session_state.get("set_leg_rule", "First to"))
            except ValueError: default_set_leg_index = set_leg_options.index("First to")
            selected_set_leg = st.selectbox("Set/Leg Rule", set_leg_options, index=default_set_leg_index)
            st.session_state.set_leg_rule = selected_set_leg

        with col5:
            checkin_options = ["Straight In", "Double In"]
            try:
                default_checkin_index = checkin_options.index(st.session_state.get("check_in_mode", "Straight In"))
            except ValueError: default_checkin_index = checkin_options.index("Straight In")
            selected_checkin = st.selectbox("Check-In (Not Implemented)", checkin_options, index=default_checkin_index, disabled=True) # Disabled for now
            st.session_state.check_in_mode = selected_checkin

        with col6:
            legs_options = list(range(1, 12)) # Max 11 legs per set
            try:
                default_legs_index = legs_options.index(st.session_state.get("legs_to_play", 1))
            except ValueError: default_legs_index = legs_options.index(1)
            selected_legs = st.selectbox("Legs (per Set)", legs_options, index=default_legs_index)
            st.session_state.legs_to_play = selected_legs

        st.markdown("---")

        # --- Player Selection ---
        st.subheader("Select Players")
        available_players = []
        if st.session_state.username and st.session_state.username in users:
            if "player_stats" not in users[st.session_state.username]:
                users[st.session_state.username]["player_stats"] = {}
            available_players = list(users[st.session_state.username]["player_stats"].keys())
        else:
            st.error("Error: Could not retrieve user data for player selection.")

        selected_players_list = st.multiselect(
            "Select players for the game (drag to reorder start)",
            options=available_players,
            default=st.session_state.players_selected_for_game,
            key="multiselect_players"
        )
        st.session_state.players_selected_for_game = selected_players_list # Update state immediately

        # --- Add New Player Section ---
        with st.expander("Add New Player to Saved List"):
            new_player_name = st.text_input("Enter New Player Name", key="new_player_name_input").strip()
            if st.button("➕ Add New Player to List"):
                if new_player_name:
                    if st.session_state.username and st.session_state.username in users:
                        if new_player_name not in users[st.session_state.username]["player_stats"]:
                            users[st.session_state.username]["player_stats"][new_player_name] = {
                                "games_played": 0, "games_won": 0, "legs_won": 0, "sets_won": 0,
                                "total_score": 0, "highest_score": 0, "total_turns": 0,
                                "num_busts": 0, "darts_thrown": 0
                            }
                            save_users(users)
                            st.success(f"Player '{new_player_name}' added and saved.")
                            st.session_state.new_player_name_input = ""
                            st.rerun()
                        else:
                            st.warning(f"Player '{new_player_name}' already exists.")
                    else:
                        st.error("Error: Could not save player.")
                else:
                    st.warning("Please enter a name.")

        st.markdown("---")

        # --- Start Game Button ---
        if st.button("🚀 Start Game", type="primary", use_container_width=True):
            players_to_start = st.session_state.players_selected_for_game

            if not players_to_start:
                st.warning("⚠️ Please select at least one player.")
            elif not st.session_state.game_mode or st.session_state.game_mode not in [101, 201, 301, 401, 501]:
                 st.warning("⚠️ Please select a valid X01 game mode.")
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
                st.session_state.game_over = False
                st.session_state.leg_over = False
                st.session_state.set_over = False # Add set_over flag
                st.session_state.winner = None
                st.session_state.message = "" # Clear any previous message

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

    if st.session_state.username in users and "player_stats" in users[st.session_state.username]:
        player_stats_data = users[st.session_state.username]["player_stats"]

        if player_stats_data:
            stats_options = [
                "Games Played", "Games Won", "Legs Won", "Sets Won", "Win Rate (%)",
                "Total Score Thrown", "Avg Score per Turn", "Avg Score per Dart",
                "Highest Score (Turn)", "Total Turns", "Darts Thrown", "Busts"
            ]
            selected_stat = st.selectbox("Select Statistic to Compare", stats_options)

            table_data = []
            for player, stats in player_stats_data.items():
                row = {"Player": player}
                games_played = stats.get("games_played", 0)
                games_won = stats.get("games_won", 0) # Assumes 'games_won' refers to matches/games
                legs_won = stats.get("legs_won", 0)
                sets_won = stats.get("sets_won", 0)
                total_score = stats.get("total_score", 0)
                total_turns = stats.get("total_turns", 0)
                darts_thrown = stats.get("darts_thrown", 0)

                if selected_stat == "Games Played": row["Value"] = games_played
                elif selected_stat == "Games Won": row["Value"] = games_won
                elif selected_stat == "Legs Won": row["Value"] = legs_won
                elif selected_stat == "Sets Won": row["Value"] = sets_won
                elif selected_stat == "Win Rate (%)":
                    win_rate = (games_won / games_played * 100) if games_played > 0 else 0
                    row["Value"] = f"{win_rate:.2f}"
                elif selected_stat == "Total Score Thrown": row["Value"] = total_score
                elif selected_stat == "Avg Score per Turn":
                    avg_turn = (total_score / total_turns) if total_turns > 0 else 0
                    row["Value"] = f"{avg_turn:.2f}"
                elif selected_stat == "Avg Score per Dart":
                     # Standard assumption is 3 darts per turn for average, unless exact dart count is tracked
                     avg_dart = (total_score / darts_thrown) if darts_thrown > 0 else 0
                     row["Value"] = f"{avg_dart:.2f}"
                elif selected_stat == "Highest Score (Turn)": row["Value"] = stats.get("highest_score", 0)
                elif selected_stat == "Total Turns": row["Value"] = total_turns
                elif selected_stat == "Darts Thrown": row["Value"] = darts_thrown
                elif selected_stat == "Busts": row["Value"] = stats.get("num_busts", 0)

                table_data.append(row)

            if table_data:
                df = pd.DataFrame(table_data)
                st.dataframe(df.set_index("Player")) # Set Player as index for better view
            else:
                st.info("No player statistics available for the selected category.")

            st.markdown("---")
            st.subheader("Visualizations (Placeholder)")
            st.info("Charts and graphs will be added here in the future.")
            # Example using matplotlib (if needed later)
            # fig, ax = plt.subplots()
            # ax.bar(df['Player'], df['Value']) # Example plot
            # st.pyplot(fig)

        else:
            st.info("No player statistics recorded yet for your profile. Add players and play games!")
    else:
        st.warning("Could not load statistics. User data not found or profile has no stats.")

# --- Game Tab Logic ---
elif st.session_state.current_page == "Game":

    # --- Helper Function to Parse Score String and Calculate Value ---
    # This function now takes a single score string like "T20", "D5", "17", "25", "0"
    # Returns (value, is_double, is_triple, is_valid)
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
                    else: is_valid = False # Invalid triple number
                else: is_valid = False # Malformed triple
            elif score_str.startswith("D"):
                 if len(score_str) > 1 and score_str[1:].isdigit():
                    num = int(score_str[1:])
                    if 1 <= num <= 20 or num == 25: # D25 is Bullseye (50)
                        value = num * 2
                        is_double = True
                    else: is_valid = False # Invalid double number
                 else: is_valid = False # Malformed double
            elif score_str.isdigit():
                num = int(score_str)
                if 0 <= num <= 20 or num == 25: # Single 1-20 or 25 (outer bull)
                    value = num
                # We don't accept 50 directly, must be D25
                elif num == 50: is_valid = False; st.warning("Enter Bullseye as D25")
                else: is_valid = False # Invalid single number
            else:
                is_valid = False # Not T, D, or digit

        except ValueError:
            is_valid = False

        if not is_valid:
            # Optionally provide more specific error messages here or return error type
            pass

        return value, is_double, is_triple, is_valid

    # --- Helper Function to Calculate Total Turn Score from list like ["T20", "19", "D8"] ---
    def calculate_turn_total(shots_list):
        total = 0
        darts_thrown_turn = 0
        last_dart_double_flag = False # Was the *last dart recorded* a double?

        parsed_shots_details = [] # Store details for history/validation: (score_str, value, is_double)

        for i, shot_str in enumerate(shots_list):
            value, is_double, _, is_valid = parse_score_input(shot_str)

            if not is_valid:
                 # This indicates an internal error if invalid data got into shots_list
                 st.error(f"Internal Error: Invalid score '{shot_str}' found in turn list.")
                 return None, 0, False, [] # Signal critical error

            total += value
            darts_thrown_turn += 1
            last_dart_double_flag = is_double # Update based on the current dart
            parsed_shots_details.append({"input": shot_str, "value": value, "is_double": is_double})

        return total, darts_thrown_turn, last_dart_double_flag, parsed_shots_details

    # --- Check Game State ---
    if st.session_state.game_over:
        st.title("🎉 Game Over! 🎉")
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
         st.error("No players selected for the game. Go to Homepage to start.")
         if st.button("🏠 Back to Homepage"):
              st.session_state.current_page = "Homepage"
              st.rerun()
         st.stop()

    # --- Game Interface ---
    st.title(f"🎯 Game On: {st.session_state.game_mode} - Set {st.session_state.current_set}/{st.session_state.sets_to_play} | Leg {st.session_state.current_leg}/{st.session_state.legs_to_play}")
    st.caption(f"Mode: {st.session_state.check_out_mode}, {st.session_state.check_in_mode} | Rule: {st.session_state.set_leg_rule}")

    # --- Scoreboard ---
    st.subheader("Scoreboard")
    num_players = len(st.session_state.players_selected_for_game)
    cols = st.columns(num_players)

    for i, player in enumerate(st.session_state.players_selected_for_game):
        with cols[i]:
            is_current_player = (i == st.session_state.current_player_index)
            border_style = "border: 3px solid #FF4B4B; padding: 10px; border-radius: 5px; background-color: #FFF0F0;" if is_current_player else "border: 1px solid #ccc; padding: 10px; border-radius: 5px;"

            with st.container():
                 st.markdown(f"<div style='{border_style}'>", unsafe_allow_html=True)
                 st.subheader(f"{'▶️ ' if is_current_player else ''}{player}")
                 score = st.session_state.player_scores.get(player, st.session_state.starting_score)
                 st.markdown(f"<h1 style='text-align: center; font-size: 3em; margin-bottom: 0;'>{score}</h1>", unsafe_allow_html=True)

                 last_turn_input_list = st.session_state.player_last_turn_scores.get(player, [])
                 last_turn_str = " ".join(map(str, last_turn_input_list)) if last_turn_input_list else " - "
                 last_turn_total, _, _, _ = calculate_turn_total(last_turn_input_list) if last_turn_input_list else (0,0,False, [])
                 st.markdown(f"<p style='text-align: center; font-size: 0.9em; color: grey;'>Last Turn: {last_turn_str} ({last_turn_total or 0})</p>", unsafe_allow_html=True)

                 darts = st.session_state.player_darts_thrown.get(player, 0)
                 # Correct Average Calculation: Use total score recorded in history (handles busts better)
                 history = st.session_state.player_turn_history.get(player, [])
                 total_score_thrown = sum(turn_info[0] for turn_info in history if turn_info[2] != "BUST") # Sum scores from non-bust turns
                 avg_3_dart = (total_score_thrown / darts * 3) if darts > 0 else 0.00
                 st.markdown(f"<p style='text-align: center; font-size: 0.9em;'>Avg (3-dart): {avg_3_dart:.2f}</p>", unsafe_allow_html=True)

                 legs = st.session_state.player_legs_won.get(player, 0)
                 sets = st.session_state.player_sets_won.get(player, 0)
                 st.markdown(f"<p style='text-align: center; font-size: 0.9em;'>Legs: {legs} | Sets: {sets}</p>", unsafe_allow_html=True)
                 st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- Input Area ---
    current_player_name = st.session_state.players_selected_for_game[st.session_state.current_player_index]
    st.subheader(f"Enter Score for: {current_player_name} (Max 3 darts)")

    # Display current turn input
    st.markdown(f"**Current Turn Input:** `{ ' | '.join(st.session_state.current_turn_shots) }`")
    num_darts_entered = len(st.session_state.current_turn_shots)
    st.caption(f"Dart {num_darts_entered + 1} of 3")

    input_disabled = num_darts_entered >= 3 # Disable number/modifier input if 3 darts entered

    # --- New Keypad Layout based on image ---
    st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True) # Add a little space

    # Number Grid (7 columns)
    keypad_numbers = list(range(1, 21)) + [25] # 1-20 and 25
    num_cols = 7
    rows_of_numbers = [keypad_numbers[i:i + num_cols] for i in range(0, len(keypad_numbers), num_cols)]

    button_style = """
    <style>
    div[data-testid*="stButton"] > button {
        margin: 2px; /* Add small margin between buttons */
        height: 50px; /* Make buttons a bit taller */
        font-size: 1.1em; /* Slightly larger font */
    }
    </style>
    """
    st.markdown(button_style, unsafe_allow_html=True)


    for row in rows_of_numbers:
        cols = st.columns(num_cols)
        for i, num in enumerate(row):
            # Ensure button has a unique key even if number is reused elsewhere
            if cols[i].button(str(num), key=f"pad_btn_{num}", use_container_width=True, disabled=input_disabled):
                if num_darts_entered < 3:
                    st.session_state.current_turn_shots.append(str(num))
                    st.rerun()
                # If > 3 darts, button is disabled, nothing happens

    # Action Row (0, Double, Triple, Backspace) - Below the number grid
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True) # Add space before action row
    cols_action = st.columns(4)

    # Miss (0) Button
    if cols_action[0].button("Miss (0)", key="pad_btn_0", use_container_width=True, disabled=input_disabled):
         if num_darts_entered < 3:
            st.session_state.current_turn_shots.append("0")
            st.rerun()

    # Double Button (Using standard button + Emoji)
    if cols_action[1].button("🟡 DOUBLE", key="pad_btn_D", help="Applies Double to last number (1-20, 25)", use_container_width=True, disabled=input_disabled):
        current_shots = st.session_state.current_turn_shots
        if not current_shots: st.warning("Enter a number first.")
        else:
            last_shot = current_shots[-1]
            if last_shot.startswith("D") or last_shot.startswith("T"): st.warning("Score already modified.")
            elif not last_shot.isdigit(): st.warning("Invalid target for Double.") # Should only be digits 1-20 or 25
            else:
                num = int(last_shot)
                if num <= 0 or (num > 20 and num != 25): st.warning("Can only Double 1-20 or Bull (25).")
                else:
                    current_shots[-1] = "D" + last_shot # Modify last element
                    st.rerun()

    # Triple Button (Using standard button + Emoji)
    if cols_action[2].button("🟠 TRIPLE", key="pad_btn_T", help="Applies Triple to last number (1-20)", use_container_width=True, disabled=input_disabled):
        current_shots = st.session_state.current_turn_shots
        if not current_shots: st.warning("Enter a number first.")
        else:
            last_shot = current_shots[-1]
            if last_shot.startswith("D") or last_shot.startswith("T"): st.warning("Score already modified.")
            elif not last_shot.isdigit(): st.warning("Invalid target for Triple.") # Should only be digits 1-20
            else:
                num = int(last_shot)
                if num <= 0 or num > 20: st.warning("Can only Triple 1-20.")
                else:
                    current_shots[-1] = "T" + last_shot # Modify last element
                    st.rerun()

    # Backspace Button (Using standard button + Emoji)
    # Not easily made red with standard buttons
    if cols_action[3].button("⬅️ Backspace", key="pad_btn_back", help="Remove last entry", use_container_width=True):
        if st.session_state.current_turn_shots:
            st.session_state.current_turn_shots.pop()
            st.rerun()

    st.markdown("---") # Separator before Submit

    # Submit Button (Full width below actions)
    submit_disabled = num_darts_entered == 0 # Disable if no darts entered
    if st.button("Submit Turn", key="pad_btn_submit", use_container_width=True, type="primary", disabled=submit_disabled):
        # --- Process the Turn ---
        # --- Start of Submit Turn Logic ---
        shots_entered = st.session_state.current_turn_shots
        score_before_turn = st.session_state.player_scores[current_player_name]

        # Use the calculation function that handles ["T20", "D5", etc.]
        calculated_score, darts_thrown_turn, last_dart_double, _ = calculate_turn_total(shots_entered)

        if calculated_score is None:
            # This case means calculate_turn_total found an invalid sequence
            # which ideally should be prevented by button logic, but handle defensively
            st.error("Error calculating score from input. Please Backspace and re-enter.")
            # Do not proceed further or change player turn
        else:
            # Score calculation was successful, proceed with game logic
            new_score = score_before_turn - calculated_score
            is_bust = False
            is_win = False

            # 1. Check Bust
            if new_score < 0 or new_score == 1:
                st.warning(f"❌ Bust! Score remains {score_before_turn}")
                st.session_state.player_scores[current_player_name] = score_before_turn # Score doesn't change
                st.session_state.message = f"{current_player_name} Busted!"
                # Record turn history with score attempted
                st.session_state.player_turn_history[current_player_name].append((calculated_score, darts_thrown_turn, "BUST"))
                # Store the actual shots entered for display
                st.session_state.player_last_turn_scores[current_player_name] = list(shots_entered)
                # Darts were thrown even on bust
                st.session_state.player_darts_thrown[current_player_name] += darts_thrown_turn
                is_bust = True
                # Update persistent stats for bust
                if current_player_name in users[st.session_state.username]["player_stats"]:
                    users[st.session_state.username]["player_stats"][current_player_name]["num_busts"] += 1
                    users[st.session_state.username]["player_stats"][current_player_name]["total_turns"] += 1
                    users[st.session_state.username]["player_stats"][current_player_name]["darts_thrown"] += darts_thrown_turn
                    save_users(users)

            # 2. Check Win (only if not busted)
            elif new_score == 0:
                valid_checkout = False
                if st.session_state.check_out_mode == "Double Out":
                    if last_dart_double: valid_checkout = True
                    else:
                        # Invalid checkout (needed Double) - Treat as Bust for this turn
                        st.warning(f"❌ Invalid Checkout! Must finish on a Double. Score remains {score_before_turn}")
                        st.session_state.player_scores[current_player_name] = score_before_turn
                        st.session_state.message = f"{current_player_name} Invalid Checkout!"
                        st.session_state.player_turn_history[current_player_name].append((calculated_score, darts_thrown_turn, "BUST (Invalid Checkout)"))
                        st.session_state.player_last_turn_scores[current_player_name] = list(shots_entered)
                        st.session_state.player_darts_thrown[current_player_name] += darts_thrown_turn
                        is_bust = True # Treat as bust for turn advancement logic
                        # Update persistent stats
                        if current_player_name in users[st.session_state.username]["player_stats"]:
                             users[st.session_state.username]["player_stats"][current_player_name]["num_busts"] += 1
                             users[st.session_state.username]["player_stats"][current_player_name]["total_turns"] += 1
                             users[st.session_state.username]["player_stats"][current_player_name]["darts_thrown"] += darts_thrown_turn
                             save_users(users)
                else: # Straight Out requires no specific last dart
                    valid_checkout = True

                if valid_checkout: # If checkout was valid (or Straight Out)
                    st.success(f"🎯 Game Shot! {current_player_name} wins Leg {st.session_state.current_leg}!")
                    st.session_state.player_scores[current_player_name] = 0
                    st.session_state.message = f"{current_player_name} won Leg {st.session_state.current_leg}!"
                    st.session_state.player_turn_history[current_player_name].append((calculated_score, darts_thrown_turn, "WIN"))
                    st.session_state.player_last_turn_scores[current_player_name] = list(shots_entered)
                    st.session_state.player_darts_thrown[current_player_name] += darts_thrown_turn
                    st.session_state.leg_over = True # Signal leg end
                    is_win = True # Mark turn as a winning turn
                    st.session_state.player_legs_won[current_player_name] += 1 # Increment leg count

                    # Update persistent stats for winner
                    if current_player_name in users[st.session_state.username]["player_stats"]:
                         stats = users[st.session_state.username]["player_stats"][current_player_name]
                         stats["total_score"] += calculated_score # Add final turn score
                         stats["total_turns"] += 1 # Count final turn
                         stats["darts_thrown"] += darts_thrown_turn # Add final darts
                         stats["legs_won"] += 1 # Update persistent leg count
                         if calculated_score > stats.get("highest_score", 0): stats["highest_score"] = calculated_score
                         # Game won/played stats updated when match ends
                         save_users(users)

            # 3. Regular Score Update (if not bust and not win)
            else:
                st.session_state.player_scores[current_player_name] = new_score
                st.session_state.message = f"{current_player_name} scored {calculated_score}. {new_score} left."
                st.session_state.player_turn_history[current_player_name].append((calculated_score, darts_thrown_turn, "OK"))
                st.session_state.player_last_turn_scores[current_player_name] = list(shots_entered)
                st.session_state.player_darts_thrown[current_player_name] += darts_thrown_turn
                # Update persistent stats
                if current_player_name in users[st.session_state.username]["player_stats"]:
                     stats = users[st.session_state.username]["player_stats"][current_player_name]
                     stats["total_score"] += calculated_score
                     stats["total_turns"] += 1
                     stats["darts_thrown"] += darts_thrown_turn
                     if calculated_score > stats.get("highest_score", 0): stats["highest_score"] = calculated_score
                     save_users(users)

            # --- Post-Turn Processing ---
            st.session_state.current_turn_shots = [] # Clear input buffer AFTER processing

            # --- Check Leg/Set/Game End Conditions (only if turn wasn't an invalid checkout bust) ---
            if not (is_bust and not valid_checkout and new_score == 0): # Exclude invalid checkout bust from ending leg prematurely

                if st.session_state.leg_over: # Check if the leg was just won
                    # Determine legs needed based on rule ('Best of' or 'First to')
                    legs_needed = math.ceil((st.session_state.legs_to_play + 1) / 2) if st.session_state.set_leg_rule == "Best of" else st.session_state.legs_to_play

                    # Check if this leg win results in winning the Set
                    if st.session_state.player_legs_won[current_player_name] >= legs_needed:
                         st.session_state.set_over = True # Signal set end
                         st.session_state.player_sets_won[current_player_name] += 1 # Increment set count
                         st.success(f"🎉 {current_player_name} wins Set {st.session_state.current_set}!")
                         # Update persistent set stats
                         if current_player_name in users[st.session_state.username]["player_stats"]:
                              users[st.session_state.username]["player_stats"][current_player_name]["sets_won"] += 1
                              save_users(users)

                         # Determine sets needed for the match
                         sets_needed = math.ceil((st.session_state.sets_to_play + 1) / 2) if st.session_state.set_leg_rule == "Best of" else st.session_state.sets_to_play

                         # Check if this set win results in winning the Game
                         if st.session_state.player_sets_won[current_player_name] >= sets_needed:
                              st.session_state.game_over = True # Signal game end
                              st.session_state.winner = current_player_name # Declare winner
                              # Update overall games played/won stats for all participants
                              for p in st.session_state.players_selected_for_game:
                                   if p in users[st.session_state.username]["player_stats"]:
                                        users[st.session_state.username]["player_stats"][p]["games_played"] += 1
                                        if p == current_player_name: users[st.session_state.username]["player_stats"][p]["games_won"] += 1
                              save_users(users)
                              # No player change, game over screen will show on rerun

                         else: # Set over, but Game not over -> Start Next Set
                              st.info("Prepare for next Set...")
                              time.sleep(1.5) # Pause for user to see message
                              st.session_state.current_set += 1
                              st.session_state.current_leg = 1 # Reset leg counter for new set
                              # Reset scores and leg counts for the new set
                              st.session_state.player_scores = {p: st.session_state.starting_score for p in st.session_state.players_selected_for_game}
                              st.session_state.player_legs_won = {p: 0 for p in st.session_state.players_selected_for_game}
                              st.session_state.player_last_turn_scores = {p: [] for p in st.session_state.players_selected_for_game}
                              st.session_state.leg_over = False # Reset flags
                              st.session_state.set_over = False
                              # Alternate starting player for the new set (simple rotation)
                              st.session_state.current_player_index = (st.session_state.current_player_index + 1) % num_players

                    else: # Leg over, but Set not over -> Start Next Leg
                         st.info("Prepare for next Leg...")
                         time.sleep(1.5) # Pause
                         st.session_state.current_leg += 1
                         # Reset scores for the new leg
                         st.session_state.player_scores = {p: st.session_state.starting_score for p in st.session_state.players_selected_for_game}
                         st.session_state.player_last_turn_scores = {p: [] for p in st.session_state.players_selected_for_game}
                         st.session_state.leg_over = False # Reset flag
                         # Alternate starting player for the new leg (simple rotation)
                         st.session_state.current_player_index = (st.session_state.current_player_index + 1) % num_players

                else: # Leg is not over, just advance to the next player
                    st.session_state.current_player_index = (st.session_state.current_player_index + 1) % num_players

            # Always rerun after processing a submit action to update the UI
            st.rerun()
        # --- End of Submit Turn Logic ---


    # Display temporary messages (like Bust, Score) using toast
    if st.session_state.message:
         st.toast(st.session_state.message)
         st.session_state.message = "" # Clear message after showing

# --- Fallback for Unknown Page State ---
elif st.session_state.logged_in:
     st.warning("Invalid page state detected. Returning to Homepage.")
     st.session_state.current_page = "Homepage"
     time.sleep(1)
     st.rerun()