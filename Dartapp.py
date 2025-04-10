import streamlit as st
import matplotlib.pyplot as plt
import json
import os
import hashlib

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

        with game_mode_tabs[1]: # Cricket Tab
            st.subheader("Cricket Options")
            st.info("Cricket game mode will be implemented in a future version.")

        st.markdown("---")
        if st.button("Logout"):
            st.session_state.clear()
            st.session_state.rerun()

with main_tabs[1]: # Statistics Tab
    st.title("📊 Personal Statistics")
    if st.session_state.username in users and "player_stats" in users[st.session_state.username]:
        player_stats = users[st.session_state.username]["player_stats"]
        if player_stats:
            for player, stats in player_stats.items():
                st.subheader(f"👤 {player}")
                st.write(f"**Games Played:** {stats['games_played']}")
                st.write(f"**Games Won:** {stats['games_won']}")
                win_rate = (stats['games_won'] / stats['games_played']) * 100 if stats['games_played'] > 0 else 0
                st.write(f"**Win Rate:** {win_rate:.2f}%")
                st.write(f"**Total Score:** {stats['total_score']}")
                avg_score = stats['total_score'] / stats['total_turns'] if stats['total_turns'] > 0 else 0
                st.write(f"**Average Score:** {avg_score:.2f}")
                st.write(f"**Highest Score:** {stats['highest_score']}")
                st.write(f"**Total Turns:** {stats['total_turns']}")
                st.markdown("---")
        else:
            st.info("No player statistics available yet.")
    else:
        st.info("Please log in to see your statistics.")

with main_tabs[2]: # Game Tab
    if st.session_state.current_page == "game":
        col1, col2 = st.columns([8, 1])
        with col1:
            st.title(f"🎯 Darts Score Counter ({st.session_state.game_mode})")
        with col2:
            if st.button("🚪 Logout"):
                st.session_state.clear()
                st.session_state.rerun()

        # Session state setup für das Spiel (wird nur ausgeführt, wenn current_page == "game")
        if "starting_score" not in st.session_state or st.session_state.starting_score != st.session_state.game_mode:
            st.session_state.starting_score = st.session_state.game_mode
            st.session_state.score = st.session_state.starting_score
            st.session_state.start_of_turn = st.session_state.starting_score
            st.session_state.history = users[st.session_state.username]["games"][-1] if users[st.session_state.username]["games"] else []

        # 1. Handle input first
        score_input = st.number_input("Enter total score for this turn:", min_value=0, max_value=180, step=1)
        submit = st.button("Submit Turn")

        if submit:
            start = st.session_state.score
            new_score = start - score_input

            if new_score < 0 or new_score == 1:
                st.warning("❌ Bust! Score resets to start of this turn.")
                st.session_state.score = st.session_state.start_of_turn
                st.session_state.history.append((score_input, "BUST"))
                # Statistik-Update für Spieler mit Bust (nur gespielte Spiele zählen)
                if st.session_state.username in users and st.session_state.current_players:
                    currentPlayer = st.session_state.current_players[-1] # Annahme: Der letzte Spieler, der geworfen hat
                    if currentPlayer in users[st.session_state.username]["player_stats"]:
                        users[st.session_state.username]["player_stats"][currentPlayer]["games_played"] += 1
                        save_users(users)
            elif new_score == 0:
                st.success("🎯 Finished! (Assuming correct double out)")
                st.session_state.history.append((score_input, "WIN"))
                st.session_state.score = 0
                users[st.session_state.username]["games"].append(st.session_state.history)
                # Statistik-Update für Gewinner
                if st.session_state.username in users and st.session_state.current_players:
                    winner = st.session_state.current_players[-1] # Annahme: Der letzte Spieler, der punktet, gewinnt (muss evtl. angepasst werden)
                    if winner in users[st.session_state.username]["player_stats"]:
                        users[st.session_state.username]["player_stats"][winner]["games_played"] += 1
                        users[st.session_state.username]["player_stats"][winner]["games_won"] += 1
                        save_users(users)
                save_users(users)
            else:
                st.session_state.score = new_score
                st.session_state.start_of_turn = new_score
                st.session_state.history.append((score_input, new_score))
                # Statistik-Update für jeden gültigen Zug
                if st.session_state.username in users and st.session_state.current_players:
                    currentPlayer = st.session_state.current_players[-1] # Annahme: Der letzte Spieler, der geworfen hat
                    if currentPlayer in users[st.session_state.username]["player_stats"]:
                        users[st.session_state.username]["player_stats"][currentPlayer]["total_score"] += score_input
                        users[st.session_state.username]["player_stats"][currentPlayer]["total_turns"] += 1
                        if score_input > users[st.session_state.username]["player_stats"][currentPlayer]["highest_score"]:
                            users[st.session_state.username]["player_stats"][currentPlayer]["highest_score"] = score_input
                        save_users(users)

        # 2. Now show updated remaining score in big font
        st.markdown("---")
        st.markdown("<h2 style='text-align: center;'>Remaining Points</h2>", unsafe_allow_html=True)
        st.markdown(
            f"<h1 style='text-align: center; font-size: 96px; color:#2e86de'>{st.session_state.score}</h1>",
            unsafe_allow_html=True
        )
        st.markdown("---")

        def calculate_stats(history):
            total_turns = len(history)
            valid_scores = [pts for pts, result in history if isinstance(pts, int)]
            total_scored = sum(valid_scores)
            avg_score = total_scored / total_turns if total_turns > 0 else 0
            highest_score = max(valid_scores) if valid_scores else 0
            num_busts = sum(1 for _, result in history if result == "BUST")
            num_wins = sum(1 for _, result in history if result == "WIN")
            win_rate = (num_wins / total_turns) * 100 if total_turns > 0 else 0
            return total_turns, total_scored, avg_score, highest_score, num_busts, num_wins, win_rate

        total_turns, total_scored, avg_score, highest_score, num_busts, num_wins, win_rate = calculate_stats(st.session_state.history)

        st.markdown("## 📊 Player Statistics")
        st.write(f"**Total Turns:** {total_turns}")
        st.write(f"**Total Points Scored:** {total_scored}")
        st.write(f"**Average Score per Turn:** {avg_score:.2f}")
        st.write(f"**Highest Score in a Turn:** {highest_score}")
        st.write(f"**Busts:** {num_busts}")
        st.write(f"**Wins:** {num_wins}")
        st.write(f"**Win Rate:** {win_rate:.2f}%")

        # 📈 Visual Insights
        st.markdown("## 📈 Visual Insights")

        # Line chart: Score progression
        score_progression = []
        running_score = st.session_state.starting_score
        for pts, result in st.session_state.history:
            if result == "BUST":
                score_progression.append(running_score)
            elif result == "WIN":
                score_progression.append(0)
            else:
                running_score -= pts
                score_progression.append(running_score)

        st.markdown("### Score Progression Over Turns")
        fig1, ax1 = plt.subplots()
        ax1.plot(range(1, len(score_progression) + 1), score_progression, marker='o')
        ax1.set_xlabel("Turn")
        ax1.set_ylabel("Remaining Score")
        ax1.set_title("Score Progression")
        ax1.grid(True)
        st.pyplot(fig1)

        # Bar chart: Score distribution
        st.markdown("### Turn Score Distribution")
        scored_turns = [pts for pts, result in st.session_state.history if isinstance(pts, int) and result not in ("BUST", "WIN")]
        if scored_turns:
            fig2, ax2 = plt.subplots()
            ax2.hist(scored_turns, bins=range(0, max(scored_turns)+20, 20), edgecolor='black')
            ax2.set_xlabel("Points Scored")
            ax2.set_ylabel("Number of Turns")
            ax2.set_title("Distribution of Scores Per Turn")
            st.pyplot(fig2)
        else:
            st.info("No valid scoring turns yet to display a distribution.")

        # Progress messages
        if st.session_state.score > 170:
            st.info("You're just warming up!")
        elif st.session_state.score > 100:
            st.info("Nice! You’re closing in.")
        elif st.session_state.score > 50:
            st.success("Almost there — stay sharp!")
        elif st.session_state.score > 2:
            st.success("Setup your double!")
        elif st.session_state.score == 2:
            st.warning("You need to hit a double 1 to finish.")
        elif st.session_state.score == 1:
            st.error("Bust! You can't finish on 1 — next turn resets.")
        elif st.session_state.score == 0:
            st.balloons()
            st.success("🎉 You win! Game over.")

        # Turn history
        with st.expander("📜 Turn History"):
            for i, (pts, result) in enumerate(st.session_state.history[::-1], 1):
                st.write(f"Turn {len(st.session_state.history)-i+1}: -{pts} → {result}")

        # Past Games
        with st.expander("🗂 Past Games"):
            for gi, game in enumerate(users[st.session_state.username]["games"][:-1], 1):
                st.markdown(f"**Game {gi}**")
                game_summary = []
                for ti, (pts, result) in enumerate(game, 1):
                    game_summary.append(f"Turn {ti}: -{pts} → {result}")
                st.text("\n".join(game_summary))

        # Reset and Back to Homepage Buttons
        col_reset, col_home = st.columns([1, 1])
        with col_reset:
            if st.button("🔄 Reset Game"):
                if st.session_state.history:
                    users[st.session_state.username]["games"].append(st.session_state.history)
                    save_users(users)
                username = st.session_state.username
                st.session_state.clear()
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.current_page = "game" # Nach Reset wieder im Spiel
                st.session_state.game_mode = st.session_state.starting_score # Behalte den Spielmodus bei
                st.rerun()
        with col_home:
            if st.button("🏠 Zurück zur Homepage"):
                st.session_state.current_page = "homepage"
                st.rerun()