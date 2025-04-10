import streamlit as st
import matplotlib.pyplot as plt
import json
import os
import hashlib
import streamlit as st
import pandas as pd 

st.set_page_config(page_title="Darts Counter", page_icon="🎯")

# User authentication
USER_DATA_FILE = "user_data.json"

def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            users = json.load(f)
            # Sicherstellen, dass jeder Benutzer ein 'player_stats'-Feld hat
            for username, data in users.items():
                if "player_stats" not in data:
                    users[username]["player_stats"] = {}
            return users
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.current_page = "login"  # Startseite ist der Login
    st.session_state.game_mode = 0

if not st.session_state.logged_in:
    if st.session_state.current_page == "login":
        st.title("🔐 Login to Darts Counter")
        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if username in users and users[username]["password"] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.current_page = "homepage"  # Nach Login zur Homepage
                    st.markdown(f"👋 Welcome, **{st.session_state.username}**!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        with register_tab:
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            if st.button("Register"):
                if new_username in users:
                    st.warning("Username already exists. Please choose a different one.")
                elif new_username.strip() == "":
                    st.warning("Username cannot be empty.")
                else:
                    users[new_username] = {"password": hash_password(new_password), "games": []}
                    save_users(users)
                    st.session_state.current_page = "login"  # Nach Registrierung zurück zum Login
                    st.success("Registration successful! Please log in.")
    st.stop()
main_tabs = st.tabs(["Homepage", "Statistics", "Game"]) # Hier erstellen wir die Haupt-Tabs

with main_tabs[0]: # Homepage Tab
    if st.session_state.current_page == "homepage":
        st.title(f"🎯 Darts Counter")
        game_mode_tabs = st.tabs(["X01", "Cricket"])

        with game_mode_tabs[0]: # X01 Tab
            st.subheader("X01 Options")

            col1, col2, col3 = st.columns(3)
            with col1:
                # Punkte Dropdown (numerisch sortiert)
                points_options = ["101", "201", "301", "401", "501"] # Füge hier weitere Optionen hinzu, falls gewünscht
                points_options.sort(key=int) # Sortiere die Liste numerisch
                selected_points = st.selectbox("Points", points_options, index=points_options.index("501") if "501" in points_options else 0)
                if selected_points:
                    st.session_state.game_mode = int(selected_points) # Speichere die ausgewählte Punktzahl

            with col2:
                # Check-Out Dropdown mit "Straight Out" und "Double Out"
                checkout_options = ["Straight Out", "Double Out"]
                selected_checkout = st.selectbox("Check-Out", checkout_options, index=1 if "Double Out" in checkout_options else 0) # Standardmässig Double Out
                st.session_state.check_out_mode = selected_checkout

            with col3:
                # Sets Dropdown (1 bis 21)
                sets_options = list(range(1, 22))
                selected_sets = st.selectbox("Sets", sets_options, index=0) # Standardmässig 1
                st.session_state.sets_to_play = selected_sets

            col4, col5, col6 = st.columns(3)
            with col4:
                # Set/Leg Dropdown
                set_leg_options = ["First to", "Best of"]
                selected_set_leg = st.selectbox("Set/Leg", set_leg_options, index=0) # Standardmässig First to
                st.session_state.set_leg_rule = selected_set_leg

            with col5:
                # Check-In Dropdown
                checkin_options = ["Straight In", "Double In"]
                selected_checkin = st.selectbox("Check-In", checkin_options, index=0) # Standardmässig Straight In
                st.session_state.check_in_mode = selected_checkin

            with col6:
                # Legs Dropdown (1 bis 21)
                legs_options = list(range(1, 22))
                selected_legs = st.selectbox("Legs", legs_options, index=0) # Standardmässig 1
                st.session_state.legs_to_play = selected_legs

            if st.button("Start Game"):
                if st.session_state.game_mode == 0: # Sicherstellen, dass ein Spielmodus gewählt wurde
                    st.warning("Please select a game mode.")
                elif st.session_state.game_mode in [101, 201, 301, 401, 501]:
                    st.session_state.current_page = "game"
                    st.session_state.active_tab_index = 2 # Zum Game-Tab wechseln
                    st.session_state.current_players = list(st.session_state.players) # Speichere die Spielerliste für das aktuelle Spiel
                    st.rerun()

            st.markdown("---")
            st.subheader("Players")

            if "players" not in st.session_state:
                st.session_state.players = []

            player_name = st.text_input("Enter Player Name:")
            if st.button("➕ Add Player"):
                if player_name and player_name not in st.session_state.players:
                    st.session_state.players.append(player_name)
                    st.success(f"Player '{player_name}' added to game.")
                    # Speichere den Spieler in den persistenten Daten
                    if st.session_state.username and st.session_state.username in users:
                        if player_name not in users[st.session_state.username]["player_stats"]:
                            users[st.session_state.username]["player_stats"][player_name] = {
                                "games_played": 0,
                                "games_won": 0,
                                "total_score": 0,
                                "highest_score": 0,
                                "total_turns": 0,
                                "num_busts": 0,
                                # Füge hier weitere Statistiken hinzu, die du speichern möchtest
                            }
                            save_users(users) # Speichere die aktualisierten Benutzerdaten
                elif player_name in st.session_state.players:
                    st.warning("Player name already exists in this game.")
                elif not player_name:
                    st.warning("Please enter a player name.")

            if st.session_state.players:
                st.subheader("Current Players:")
                for index, player in enumerate(st.session_state.players):
                    col_player, col_remove = st.columns([3, 1])
                    with col_player:
                        st.write(f"- {player}")
                    with col_remove:
                        if st.button("🗑️", key=f"remove_{player}"):
                            st.session_state.players.pop(index)
                            st.rerun()

with main_tabs[1]: # Statistics Tab
    st.title("📊 Personal Statistics")
    if st.session_state.username in users and "player_stats" in users[st.session_state.username]:
        player_stats = users[st.session_state.username]["player_stats"]
        if player_stats:
            # Dropdown zur Auswahl der Statistik
            stats_options = ["Games Played", "Games Won", "Win Rate", "Total Score", "Average Score", "Highest Score", "Total Turns", "Busts"]
            selected_stat = st.selectbox("Select Statistic", stats_options)

            # Tabellendaten (bleibt gleich)
            table_data = []
            for player, stats in player_stats.items():
                row = {"Player": player}
                if selected_stat == "Games Played":
                    row["Value"] = stats.get("games_played", 0)
                elif selected_stat == "Games Won":
                    row["Value"] = stats.get("games_won", 0)
                elif selected_stat == "Win Rate":
                    games_played = stats.get("games_played", 0)
                    games_won = stats.get("games_won", 0)
                    win_rate = (games_won / games_played) * 100 if games_played > 0 else 0
                    row["Value"] = f"{win_rate:.2f}%"
                elif selected_stat == "Total Score":
                    row["Value"] = stats.get("total_score", 0)
                elif selected_stat == "Average Score":
                    total_score = stats.get("total_score", 0)
                    total_turns = stats.get("total_turns", 0)
                    avg_score = total_score / total_turns if total_turns > 0 else 0
                    row["Value"] = f"{avg_score:.2f}"
                elif selected_stat == "Highest Score":
                    row["Value"] = stats.get("highest_score", 0)
                elif selected_stat == "Total Turns":
                    row["Value"] = stats.get("total_turns", 0)
                elif selected_stat == "Busts":
                    row["Value"] = stats.get("num_busts", 0)
                table_data.append(row)

            # Zeige die Daten als Tabelle an
            if table_data:
                df = pd.DataFrame(table_data)
                st.dataframe(df)
            else:
                st.info("No player statistics available yet.")

            st.markdown("---")
            st.subheader("Visualizations")

            if player_stats:
                player_names = list(player_stats.keys())

                # Balkendiagramm für Games Played
                games_played = [stats.get("games_played", 0)]

with main_tabs[2]: # Game Tab
    if st.session_state.current_page == "game":
        if "score" not in st.session_state:
            st.session_state.score = st.session_state.starting_score if "starting_score" in st.session_state else 0
        st.title(f"🎯 {st.session_state.game_mode}, Double Out, First to 1 Set 1 Leg") # Angepasster Titel

        if "current_players" in st.session_state and st.session_state.current_players:
            num_players = len(st.session_state.current_players)
            if "current_player_index" not in st.session_state:
                st.session_state.current_player_index = 0

            current_player = st.session_state.current_players[st.session_state.current_player_index % num_players]
            st.subheader(f"Player: {current_player}")

            # Session state setup für das Spiel (wird nur ausgeführt, wenn current_page == "game")
            if "starting_score" not in st.session_state or st.session_state.starting_score != st.session_state.game_mode:
                st.session_state.starting_score = st.session_state.game_mode
                st.session_state.score = st.session_state.starting_score
                st.session_state.start_of_turn = st.session_state.starting_score
                st.session_state.history = users[st.session_state.username]["games"][-1] if users[st.session_state.username]["games"] else []
                # Initialisierung der Player-Scores und anderer Variablen
                st.session_state.player_scores = {player: st.session_state.starting_score for player in st.session_state.current_players}
                st.session_state.player_sets_won = {player: 0 for player in st.session_state.current_players}
                st.session_state.player_legs_won = {player: 0 for player in st.session_state.current_players}
                st.session_state.player_averages = {player: 0.00 for player in st.session_state.current_players}

            # 1. Handle input first
            score_input = st.number_input(f"Enter total score for this turn ({current_player}):", min_value=0, max_value=180, step=1)
            submit_turn = st.button("Submit Turn", key="submit_turn_button")

            if submit_turn:
                start = st.session_state.score
                new_score = start - score_input

                if new_score < 0 or new_score == 1:
                    st.warning(f"❌ Bust for {current_player}! Score resets to start of this turn.")
                    st.session_state.score = st.session_state.start_of_turn
                    st.session_state.history.append((score_input, "BUST"))
                    # Statistik-Update für Spieler mit Bust
                    if st.session_state.username in users and st.session_state.current_players:
                        if current_player in users[st.session_state.username]["player_stats"]:
                            users[st.session_state.username]["player_stats"][current_player]["games_played"] += 1
                            save_users(users)
                elif new_score == 0:
                    st.success(f"🎯 {current_player} Finished! (Assuming correct double out)")
                    st.session_state.history.append((score_input, "WIN"))
                    st.session_state.score = 0
                    users[st.session_state.username]["games"].append(st.session_state.history)
                    # Statistik-Update für Gewinner
                    if st.session_state.username in users and st.session_state.current_players:
                        if current_player in users[st.session_state.username]["player_stats"]:
                            users[st.session_state.username]["player_stats"][current_player]["games_played"] += 1
                            users[st.session_state.username]["player_stats"][current_player]["games_won"] += 1
                            save_users(users)
                    save_users(users)
                else:
                    st.session_state.score = new_score
                    st.session_state.start_of_turn = new_score
                    st.session_state.history.append((score_input, new_score))
                    # Statistik-Update für jeden gültigen Zug
                    if st.session_state.username in users and st.session_state.current_players:
                        if current_player in users[st.session_state.username]["player_stats"]:
                            users[st.session_state.username]["player_stats"][current_player]["total_score"] += score_input
                            users[st.session_state.username]["player_stats"][current_player]["total_turns"] += 1
                            if score_input > users[st.session_state.username]["player_stats"][current_player]["highest_score"]:
                                users[st.session_state.username]["player_stats"][current_player]["highest_score"] = score_input
                            save_users(users)

                st.session_state.current_player_index += 1 # Nächster Spieler

        else:
            st.info("Please add players on the Homepage before starting the game.")

        # 2. Now show updated remaining score in big font
        st.markdown("---")
        st.markdown("<h2 style='text-align: center;'>Remaining Points</h2>", unsafe_allow_html=True)
        st.markdown(
            f"<h1 style='text-align: center; font-size: 96px; color:#2e86de'>{st.session_state.score}</h1>",
            unsafe_allow_html=True
        )
        st.markdown("---")

        # Keypad (vereinfacht für den Anfang)
        col_keypad1, col_keypad2, col_keypad3 = st.columns(3)
        with col_keypad1:
            st.button("7")
            st.button("4")
            st.button("1")
            st.button("0")
        with col_keypad2:
            st.button("8")
            st.button("5")
            st.button("2")
            st.button("Double")
        with col_keypad3:
            st.button("9")
            st.button("6")
            st.button("3")
            st.button("Triple")

        score_input_str = st.text_input("Enter Score:", key="score_input")

        if st.button("🏠 Back to Homepage"):
            st.session_state.current_page = "homepage"
            st.rerun()