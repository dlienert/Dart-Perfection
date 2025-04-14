import streamlit as st
import matplotlib.pyplot as plt # Keep for future stats visualizations
import json
import os
import hashlib
import pandas as pd
import time
import math # Needed for ceiling function in set/leg logic
import requests #for API requests
import random

# API for motivational quotes
def get_motivational_quote():
    try:
        # Using a different API as zenquotes.io might require keys or have limits
        response = requests.get("https://api.quotable.io/random?tags=motivation|inspiration")
        if response.status_code == 200:
            data = response.json()
            return f"\"{data['content']}\" — {data['author']}"
        else:
            # Fallback quotes if API fails
            fallbacks = [
                "Stay motivated and keep going!",
                "Every dart thrown is progress.",
                "Focus on the board, one dart at a time.",
                "Persistence pays off in darts.",
                "Aim high, throw straight!"
            ]
            return random.choice(fallbacks)
    except Exception as e:
        # More specific fallback for network or other errors
        fallbacks = [
            "Stay positive, aim true!",
            "Keep practicing, improvement follows.",
            "Believe in your throw!"
        ]
        return random.choice(fallbacks)

# --- Language Translation Setup ---

# Define translation dictionary for app text (Expanded with new/missing keys)
translations = {
    "welcome": {"de": "Willkommen bei Darts Counter", "en": "Welcome to Darts Counter"},
    "login": {"de": "Anmelden", "en": "Login"},
    "register": {"de": "Registrieren", "en": "Register"},
    "username": {"de": "Benutzername", "en": "Username"},
    "password": {"de": "Passwort", "en": "Password"},
    "invalid_login": {"de": "Ungültiger Login oder Passwort.", "en": "Invalid username or password."},
    "empty_credentials": {"de": "Bitte Benutzername und Passwort eingeben.", "en": "Please enter username and password."},
    "user_exists": {"de": "Benutzername existiert bereits.", "en": "Username already exists."},
    "start_game": {"de": "Spiel starten", "en": "Start Game"},
    "logout": {"de": "Abmelden", "en": "Logout"},
    "players": {"de": "Spieler", "en": "Players"},
    "score": {"de": "Punktestand", "en": "Score"},
    "statistics": {"de": "Statistiken", "en": "Statistics"},
    "settings": {"de": "Einstellungen", "en": "Settings"},
    "game": {"de": "Spiel", "en": "Game"},
    "navigation": {"de": "Navigation", "en": "Navigation"},
    "homepage": {"de": "Startseite", "en": "Homepage"},
    "select_language": {"de": "Sprache wählen", "en": "Select Language"},
    "selected_language": {"de": "Gewählte Sprache:", "en": "Selected Language:"},
    "players_selected": {"de": "Spieler ausgewählt", "en": "Players selected"},
    "start_game_button": {"de": "🎯 Spiel starten", "en": "🎯 Start Game"},
    "configure_game": {"de": "Spiel konfigurieren,", "en": "Configure game,"},
    "finish_quit_game": {"de": "Spiel beenden/verlassen um zu navigieren.", "en": "Finish/Quit game to navigate."},
    "start_game_homepage": {"de": "Starte ein Spiel auf der Startseite.", "en": "Start a game from the Homepage."},

    # Homepage - Game Setup
    "x01_setup": {"de": "X01 Einstellungen", "en": "X01 Setup"},
    "cricket_soon": {"de": "Cricket (bald)", "en": "Cricket (soon)"},
    "x01_options": {"de": "X01 Optionen", "en": "X01 Options"},
    "x01_mode": {"de": "X01 Modus", "en": "X01 Mode"}, # Changed label
    "check_out_mode": {"de": "Checkout", "en": "Checkout"}, # Changed label
    "sets_to_win": {"de": "Gewinnsätze", "en": "Sets to Win"}, # Changed label
    "leg_set_rule": {"de": "Leg/Set Regel", "en": "Leg/Set Rule"}, # Changed label
    "check_in_mode": {"de": "Checkin", "en": "Checkin"}, # Changed label
    "legs_per_set": {"de": "Legs pro Satz", "en": "Legs per Set"}, # Changed label
    "select_players_for_game": {"de": "Spieler für das Spiel auswählen (inkl. dich selbst, falls du mitspielst!)", "en": "Select players for game (incl. yourself if playing!)"},
    "add_manage_players": {"de": "Spieler hinzufügen / verwalten", "en": "Add / Manage Players"},
    "add_new_player_info": {"de": "Neue Spieler hinzufügen, um Statistiken zu verfolgen & Einstellungen festzulegen.", "en": "Add new players (including yourself) to track stats & set preferences."},
    "new_player_name": {"de": "Neuer Spielername", "en": "New Player Name"},
    "add_player_button": {"de": "➕ Spieler hinzufügen", "en": "➕ Add Player"},
    "edit_delete_in_settings": {"de": "Präferenzen bearbeiten oder Spieler löschen in '⚙️ Einstellungen'.", "en": "Edit preferences or delete players in '⚙️ Settings'."},
    "warning_select_players": {"de": "⚠️ Spieler auswählen.", "en": "⚠️ Select players."},
    "warning_select_x01_mode": {"de": "⚠️ X01 Modus auswählen.", "en": "⚠️ Select X01 mode."},

    # Game Page
    "game_on": {"de": "Spiel läuft", "en": "Game On"},
    "set": {"de": "Satz", "en": "Set"},
    "leg": {"de": "Leg"},
    "mode": {"de": "Modus", "en": "Mode"},
    "rule": {"de": "Regel", "en": "Rule"},
    "enter_score_for": {"de": "Punkte eingeben für:", "en": "Enter score for:"},
    "dart": {"de": "Dart", "en": "Dart"},
    "double": {"de": "Doppel", "en": "Double"},
    "triple": {"de": "Triple", "en": "Triple"},
    "back": {"de": "Zurück", "en": "Back"},
    "undo": {"de": "Rückgängig", "en": "Undo"},
    "miss": {"de": "Fehler", "en": "Miss"},
    "remove_last": {"de": "Letzten entfernen", "en": "Remove last"},
    "set_double": {"de": "Doppel setzen", "en": "Set Double"},
    "set_triple": {"de": "Triple setzen", "en": "Set Triple"},
    "undo_last_turn": {"de": "Letzten Wurf rückgängig", "en": "Undo last turn"},
    "game_over_start_new": {"de": "Spiel vorbei. Neues Spiel starten.", "en": "Game over. Start new game."},
    "invalid_page_state": {"de": "Ungültiger Seitenstatus.", "en": "Invalid page state."},
    "game_in_progress": {"de": "🎯 Spiel läuft!", "en": "🎯 Game in progress!"},
    "end_game_early": {"de": "⚠️ Spiel beenden", "en": "⚠️ End Game Early"}, # Changed label for quit button
    "back_to_homepage": {"de": "🏠 Zurück zur Startseite", "en": "🏠 Back to Homepage"},
    "no_players_in_game_warning": {"de": "Keine Spieler im Spiel ausgewählt.", "en": "No players selected for game."},
    "input_indicator": {"de": "Eingabe:", "en": "Input:"},
    "double_indicator": {"de": "[**DBL**]", "en": "[**DBL**]"},
    "triple_indicator": {"de": "[**TPL**]", "en": "[**TPL**]"},
    "scores_header": {"de": "Spielstände", "en": "Scores"},
    "avg_short": {"de": "Avg", "en": "Avg"},
    "legs_short": {"de": "Legs", "en": "Legs"},
    "sets_short": {"de": "Sätze", "en": "Sets"},
    "last_turn_short": {"de": "Letzte", "en": "Last"},
    "out_suggestion": {"de": "🎯 **Out:**", "en": "🎯 **Out:**"},
    "setup_suggestion": {"de": "🔧 **Setup:**", "en": "🔧 **Setup:**"},
    "one_dart_suffix": {"de": "(1D)", "en": "(1D)"},
    "two_dart_suffix": {"de": "(2D)", "en": "(2D)"},
    "three_dart_suffix": {"de": "(3D)", "en": "(3D)"},
    "no_checkout_bogie": {"de": "Kein Checkout", "en": "No checkout"},
    "toast_use_d25": {"de": "Benutze D25", "en": "Use D25"},
    "toast_invalid_modifier_T": {"de": "T nur 1-20", "en": "T only 1-20"},
    "toast_invalid_modifier_D": {"de": "D nur 1-20, 25", "en": "D only 1-20, 25"},
    "toast_bust": {"de": "❌ Bust! Punktestand bleibt", "en": "❌ Bust! Score remains"},
    "toast_invalid_checkout": {"de": "❌ Ungültiger Checkout! Muss auf Doppel enden. Punktestand bleibt", "en": "❌ Invalid Checkout! Must finish on a Double. Score remains"},
    "toast_game_shot_leg": {"de": "🎯 Game Shot!", "en": "🎯 Game Shot!"}, # Player name and leg will be added
    "toast_wins_leg": {"de": "gewinnt Leg", "en": "wins Leg"}, # Player name and leg number will be added
    "toast_player_busted": {"de": "Busted!", "en": "Busted!"}, # Player name added
    "toast_player_invalid_checkout": {"de": "Ungültiger Checkout!", "en": "Invalid Checkout!"}, # Player name added
    "toast_player_scored": {"de": "erzielte", "en": "scored"}, # Player name and score added
    "toast_log_error": {"de": "Log Fehler:", "en": "Log Error:"},
    "toast_undid_turn": {"de": "Zug rückgängig gemacht.", "en": "Undid turn."},
    "toast_nothing_to_undo": {"de": "Nichts zum Rückgängigmachen.", "en": "Nothing to undo."},
    "toast_prepare_next_set": {"de": "Bereite dich auf den nächsten Satz vor...", "en": "Prepare for next Set..."},
    "toast_prepare_next_leg": {"de": "Bereite dich auf das nächste Leg vor...", "en": "Prepare for next Leg..."},
    "toast_player_wins_set": {"de": "gewinnt Satz", "en": "wins Set"}, # Player name and set number will be added
    "game_over_title": {"de": "🎉 Spiel vorbei!", "en": "🎉 Game Over!"},
    "game_over_winner_header": {"de": "🏆 Gewinner:", "en": "🏆 Winner:"},
    "game_over_no_winner": {"de": "Match beendet.", "en": "Match finished."},
    "game_over_player_overview": {"de": "📸 Spielerübersicht", "en": "📸 Player Overview"},
    "game_over_sets_won": {"de": "Sätze gewonnen:", "en": "Sets Won:"},
    "game_over_legs_won": {"de": "Legs gewonnen:", "en": "Legs Won:"},
    "game_over_total_score": {"de": "Gesamtpunktzahl:", "en": "Total Score:"},
    "game_over_play_again": {"de": "Nochmal spielen / Neues Spiel einrichten", "en": "Play Again / New Game Setup"},
    "internal_error_score_calc": {"de": "Interner Fehler: Punktberechnung fehlgeschlagen.", "en": "Internal Error: Score calculation failed."},
    "correct_score_try_again": {"de": "Korrigiere die Eingabe und versuche den Checkout erneut.", "en": "Correct score and try checkout again."},


    # Statistics Page
    "personal_statistics": {"de": "Persönliche Statistiken", "en": "Personal Statistics"},
    "select_statistic": {"de": "Statistik auswählen:", "en": "Select Statistic:"},
    "stats_for_account": {"de": "Statistiken für Konto:", "en": "Stats for account:"},
    "no_data_selected_stat": {"de": "Keine Daten für gewählte Statistik.", "en": "No data for selected statistic."},
    "visualizations_placeholder": {"de": "Visualisierungen (Diagramme)", "en": "Visualizations (Charts)"},
    "charts_coming_soon": {"de": "Diagramme folgen bald.", "en": "Charts coming soon."}, # Consider removing if charts implemented
    "motivation_booster": {"de": "🏆 Motivations-Boost", "en": "🏆 Motivation Booster"},
    "get_new_quote": {"de": "🔄 Neuen Spruch holen", "en": "🔄 Get New Quote"},
    "games_played": {"de": "Spiele gespielt", "en": "Games Played"},
    "games_won": {"de": "Spiele gewonnen", "en": "Games Won"},
    "legs_won": {"de": "Legs gewonnen", "en": "Legs Won"},
    "sets_won": {"de": "Sätze gewonnen", "en": "Sets Won"},
    "win_rate": {"de": "Gewinnrate (%)", "en": "Win Rate (%)"},
    "total_score": {"de": "Gesamtpunktzahl (Stats)", "en": "Total Score (Stats)"}, # Differentiate if needed
    "avg_score_turn": {"de": "Avg. Punkte / Aufnahme", "en": "Avg Score / Turn"},
    "avg_score_dart": {"de": "Avg. Punkte / Dart", "en": "Avg Score / Dart"},
    "highest_score": {"de": "Höchste Aufnahme", "en": "Highest Score (Turn)"},
    "total_turns": {"de": "Aufnahmen gesamt", "en": "Total Turns"},
    "darts_thrown": {"de": "Darts geworfen", "en": "Darts Thrown"},
    "busts": {"de": "Busts", "en": "Busts"},
    "error_displaying_table": {"de": "Fehler beim Anzeigen der Tabelle", "en": "Error displaying table"},
    "no_data_for_statistic": {"de": "Keine Daten für diese Statistik.", "en": "No data for this statistic."}, # Duplicate? Keep one
    "no_player_stats_yet": {"de": "Noch keine Spielerstatistiken vorhanden.", "en": "No player statistics available yet."},
    "could_not_load_stats": {"de": "Statistiken konnten nicht geladen werden.", "en": "Could not load statistics."},
    "no_player_stats_recorded": {"de": "Noch keine Spielerstatistiken erfasst.", "en": "No player stats recorded yet."},

    # Settings Page
    "settings_title": {"de": "⚙️ Einstellungen & Spieler-Verwaltung", "en": "⚙️ Settings & Player Management"},
    "manage_players_prefs": {"de": "Verwalte Spieler und Einstellungen für Konto:", "en": "Manage players and preferences for account:"},
    "set_preferences": {"de": "🎯 Einstellungen festlegen", "en": "🎯 Set Preferences"},
    "delete_player": {"de": "🗑️ Spieler löschen", "en": "🗑️ Delete Player"},
    "set_preferred_double_outs": {"de": "Bevorzugte Doppel für Checkouts & Avatare festlegen", "en": "Set Preferred Double Outs & Avatars"}, # Updated
    "select_player_edit_prefs": {"de": "Wähle Spieler für Einstellungen:", "en": "Select Player to Edit Preferences:"},
    "save_preferences": {"de": "Einstellungen speichern", "en": "Save Preferences"},
    "delete_player_data": {"de": "Spielerdaten löschen", "en": "Delete Player Data"},
    "delete_warning": {"de": "⚠️ Löschen entfernt alle Statistiken und Checkout-Logs dauerhaft!", "en": "⚠️ Deleting removes all stats and checkout logs permanently!"},
    "no_players_added": {"de": "Noch keine Spieler hinzugefügt.", "en": "No players added yet."},
    "player_deleted_success": {"de": "Spieler erfolgreich gelöscht.", "en": "Player deleted successfully."},
    "confirm_deletion": {"de": "Bestätigung für Löschen von", "en": "Confirm Deletion of"},
    "yes_delete": {"de": "✔️ Ja, Spieler löschen", "en": "✔️ Yes, DELETE Player Data"},
    "cancel": {"de": "❌ Abbrechen", "en": "❌ Cancel"},
    "add_players_homepage": {"de": "Spieler auf der Startseite hinzufügen.", "en": "Add players on the Homepage."},
    "no_players_delete": {"de": "Keine Spieler zum Löschen vorhanden.", "en": "No players to delete."},
    "language_settings": {"de": "🌐 Spracheinstellungen", "en": "🌐 Language Settings"},
    "select_new_avatar": {"de": "Wähle deinen neuen Account-Avatar", "en": "Select your new account avatar"},
    "choose_new_avatar": {"de": "Wähle deinen neuen Avatar:", "en": "Choose your new avatar:"},
    "preview": {"de": "Vorschau", "en": "Preview"},
    "save_avatar_choice": {"de": "Avatar-Auswahl speichern", "en": "Save Avatar Choice"},
    "avatar_updated_success": {"de": "✅ Avatar erfolgreich aktualisiert!", "en": "✅ Avatar updated successfully!"},
    "change_account_avatar": {"de": "🧩 Account-Avatar ändern", "en": "🧩 Change Account Avatar"},
    "user_data_error": {"de": "Benutzerdaten nicht gefunden oder Spielerstatistiken fehlen. Bitte neu anmelden oder Spieler auf der Startseite hinzufügen.", "en": "User data not found or player stats missing. Please re-login or add players on Homepage."},
    "select_avatar_for_player": {"de": "Wähle Avatar für", "en": "Select avatar for"},
    "choose_emoji_caption": {"de": "Wähle ein Emoji, um diesen Spieler in Spielen und Statistiken darzustellen 📊🎯", "en": "Choose an emoji to represent this player in games and stats 📊🎯"},
    "select_preferred_doubles_for": {"de": "Wähle bevorzugte Doppel für", "en": "Select preferred doubles for"},
    "save_prefs_button_label": {"de": "Einstellungen speichern für", "en": "Save Preferences for"},
    "prefs_saved_success": {"de": "Einstellungen gespeichert für", "en": "Preferences saved for"},
    "player_not_found_error": {"de": "Spieler nicht gefunden, Einstellungen konnten nicht gespeichert werden (vielleicht gelöscht?).", "en": "Player not found, could not save preferences (maybe deleted?)."},
    "select_player_to_delete": {"de": "Wähle Spieler zum Löschen:", "en": "Select Player to Delete:"},
    "delete_button_label": {"de": "Lösche", "en": "Delete"}, # Player name added
    "confirm_delete_error": {"de": "Bestätige Löschen von", "en": "Confirm Deletion of"}, # Player name added
    "deleted_success_message": {"de": "Gelöscht:", "en": "Deleted:"}, # Player name added
    "player_already_deleted_error": {"de": "Spieler nicht gefunden (vielleicht schon gelöscht).", "en": "Player not found (maybe already deleted)."},
    "deletion_error": {"de": "Ein Fehler ist beim Löschen aufgetreten:", "en": "An error occurred during deletion:"},
    "choose_player_placeholder": {"de": "Spieler auswählen...", "en": "Choose player..."},
}


# Define helper function to fetch translation based on session state
def t(key):
    """Returns the translation for a given key based on selected language."""
    lang = st.session_state.get("language", "en")  # Default to English
    # Fallback chain: specific lang -> english -> key itself
    return translations.get(key, {}).get(lang, translations.get(key, {}).get("en", key))

#page mapping for stable navigation
page_map = {
    "Homepage": "homepage",
    "Statistics": "statistics",
    "Game": "game",
    "Settings": "settings",
}
reverse_page_map = {v: k for k, v in page_map.items()}

# --- Configuration ---
USER_DATA_FILE = "user_data.json"
st.set_page_config(page_title="Darts Counter", page_icon="🎯", layout="wide")

# --- Default Preferred Doubles & Constants ---
DEFAULT_PREFERRED_DOUBLES = {"D16", "D8", "D20", "D18", "D4", "D2", "D1", "D12", "D6", "D10", "D5", "D25"} # Example set
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
                data.setdefault("avatar_choice", "avataaars_hero1") # Default avatar if missing
                player_stats_dict = data.setdefault("player_stats", {})
                data.setdefault("games", []) # Consider if this is used, might be legacy
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
                    stats.setdefault("preferred_doubles", []) # Ensure list exists
                    stats.setdefault("avatar", "🎯") # Default emoji avatar
                    # Ensure avatar_url consistency (might be overkill if always generated)
                    stats.setdefault("avatar_url", f"https://api.dicebear.com/8.x/avataaars/png?seed={player}")

            return users_data
        except json.JSONDecodeError:
            st.error(f"Error reading {USER_DATA_FILE}. File might be corrupted. Starting fresh if possible, or check file.")
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
# Initialize only if the app hasn't been initialized in this session yet
if "app_initialized" not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.language = "en" # Default language
    st.session_state.current_page = page_map.get("Homepage", "homepage") # Default page
    # Game settings defaults
    st.session_state.game_mode = 501
    st.session_state.check_out_mode = "Double Out"
    st.session_state.sets_to_play = 1
    st.session_state.set_leg_rule = "First to"
    st.session_state.check_in_mode = "Straight In" # Default Check-in
    st.session_state.legs_to_play = 1
    st.session_state.players_selected_for_game = []
    # In-game state defaults (reset before each game)
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
    st.session_state.message = "" # For toasts/feedback
    st.session_state.pending_modifier = None # For D/T input
    st.session_state.state_before_last_turn = None # For undo functionality
    st.session_state.confirm_delete_player = None # For settings page delete confirmation
    st.session_state.player_to_edit_prefs = None # For settings page edit selection

# --- Login / Register Page ---
if not st.session_state.logged_in:
    st.session_state.current_page = page_map.get("Homepage", "homepage") # Force homepage view when logged out
    st.title(f"🔐 {t('welcome')}")

    login_tab, register_tab = st.tabs([t("login"), t("register")])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input(t("username"), key="login_user")
            password = st.text_input(t("password"), type="password", key="login_pass")
            login_button = st.form_submit_button(t("login"), use_container_width=True)

            if login_button:
                hashed_input_pw = hash_password(password)
                # Safely check user and password
                if username in users and users[username].get("password") == hashed_input_pw:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.current_page = page_map.get("Homepage", "homepage")
                    st.session_state.players_selected_for_game = [] # Reset selected players on login
                    # Re-initialize necessary states if needed, or rely on initial check
                    st.session_state.app_initialized = True # Mark as initialized
                    st.rerun()
                else:
                    st.error(t("invalid_login"))

    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input(t("username"), key="reg_user").strip()
            new_password = st.text_input(t("password"), type="password", key="reg_pass")

            # Avatar Selection
            st.markdown(f"### {t('select_new_avatar')}")
            avatar_styles = ["avataaars", "bottts", "croodles", "identicon", "pixel-art"] # Example styles
            avatar_seeds = ["Hero", "Champ", "Legend", "Master", "Bullseye"] # Example seeds
            avatar_options = []
            # Use a limited, consistent set of options for registration/settings
            for style, seed in zip(avatar_styles[:5], avatar_seeds[:5]): # Limit to 5 pairs
                 # Generate SVG URLs for better quality display
                 avatar_url = f"https://api.dicebear.com/8.x/{style}/svg?seed={seed}"
                 avatar_options.append((f"{style}_{seed}", avatar_url))

            selected_avatar_key = st.radio(
                t("choose_new_avatar"),
                options=[option[0] for option in avatar_options],
                format_func=lambda x: x.split("_")[1].capitalize(), # Show seed name
                horizontal=True,
                key="reg_avatar_select"
            )

            # Find the URL for the selected avatar to display preview
            selected_avatar_url_preview = ""
            for name, url in avatar_options:
                if name == selected_avatar_key:
                    selected_avatar_url_preview = url
                    break
            if selected_avatar_url_preview:
                 st.image(selected_avatar_url_preview, width=120, caption=t("preview"))

            reg_button = st.form_submit_button(t("register"), use_container_width=True)
            if reg_button:
                if not new_username or not new_password:
                    st.warning(t("empty_credentials"))
                elif new_username in users:
                    st.warning(t("user_exists"))
                else:
                    hashed_pw = hash_password(new_password)
                    users[new_username] = {
                        "password": hashed_pw,
                        "avatar_choice": selected_avatar_key, # Save the chosen avatar key
                        "player_stats": {}, # Initialize empty player stats
                        "games": [],
                        "checkout_log": []
                    }
                    save_users(users)
                    st.success(t("registration_successful_login")) # Use a specific translation key
                    # Consider auto-login or just prompt
    st.stop() # Stop execution here if not logged in

# --- Main App Area (Only runs if logged in) ---

# --- Sidebar ---
st.sidebar.markdown(f"👋 **{st.session_state.username}**!")
# Display current user's chosen avatar
current_user_data = users.get(st.session_state.username, {})
user_avatar_choice = current_user_data.get("avatar_choice", "avataaars_Hero") # Default if missing
user_avatar_style, user_avatar_seed = user_avatar_choice.split("_")
user_avatar_url_sidebar = f"https://api.dicebear.com/8.x/{user_avatar_style}/svg?seed={user_avatar_seed}" # Use SVG
st.sidebar.image(user_avatar_url_sidebar, width=80)
st.sidebar.markdown("---")

# Page Navigation Radio Buttons
page_options = list(page_map.keys())

# Determine current page index for radio button default
try:
    visible_page_name = reverse_page_map.get(st.session_state.current_page, "Homepage")
    current_page_index = list(page_map.keys()).index(visible_page_name)
except ValueError:
    current_page_index = 0 # Default to Homepage index if something is wrong
    st.session_state.current_page = page_map.get("Homepage", "homepage") # Reset internal state too

# Disable navigation radio buttons if a game is in progress and not over
nav_disabled = st.session_state.current_page == "game" and not st.session_state.game_over

# Check if navigation target needs to be pre-set (e.g., after starting game)
if "nav_target" in st.session_state:
    # Set the key for the radio button widget directly
    st.session_state["nav_radio"] = st.session_state.pop("nav_target") # Remove the temporary target

# Render Navigation Radio
chosen_page_visible_name = st.sidebar.radio(
    t("navigation"),
    page_options,
    index=current_page_index,
    key="nav_radio", # Use a consistent key
    disabled=nav_disabled
)

# Convert chosen visible name back to internal page key
internal_chosen_page = page_map.get(chosen_page_visible_name, "homepage")

# Handle page change logic
if internal_chosen_page != st.session_state.current_page:
    if not nav_disabled:
        st.session_state.current_page = internal_chosen_page
        st.rerun() # Rerun to load the new page content
    else:
        # If nav is disabled, show a warning instead of changing page
        st.sidebar.warning(t("finish_quit_game"))
# Handle direct navigation attempt to Game page when not started (edge case)
elif chosen_page_visible_name == "Game" and st.session_state.current_page != "game":
     st.sidebar.warning(t("start_game_homepage"))
     # Prevent navigation by resetting to current page if needed (might cause loop without care)
     # Or simply do nothing, the warning should suffice

# Sidebar actions specific to the Game page
if st.session_state.current_page == "game" and not st.session_state.game_over:
    st.sidebar.warning(t("game_in_progress"))
    # Renamed "Quit" button to "End Game Early"
    if st.sidebar.button(t("end_game_early")): # Using translation key
        # Logic to end game early (same as original quit logic)
        st.session_state.current_page = page_map.get("Homepage", "homepage") # Go back home
        st.session_state.game_over = True # Mark game as over (will show game over screen briefly on home?)
        st.session_state.current_turn_shots = [] # Clear any pending shots
        st.session_state.pending_modifier = None
        st.session_state.winner = None # No winner declared on quit
        # Consider resetting more game state if needed, or let homepage handle it
        st.rerun()

st.sidebar.markdown("---")
# Logout Button
if st.sidebar.button(t("logout")):
        # Clear session state more thoroughly on logout
        logged_in_user = st.session_state.username # Keep track for potential save?
        keys_to_keep = ["app_initialized"] # Maybe keep language? Depends on preference
        for key in list(st.session_state.keys()):
             if key not in keys_to_keep:
                 del st.session_state[key]
        # Explicitly set logged_out status and reset critical flags
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.current_page = page_map.get("Homepage", "homepage")
        # Reset other states that should not persist across logins
        st.session_state.players_selected_for_game = []
        st.session_state.game_over = True # Ensure any lingering game state is cleared visually

        st.rerun() # Rerun to go back to login screen

# --- Page Content Area ---

# --- Homepage ---
if st.session_state.current_page == "homepage":
    st.title(f"🎯 {t('homepage')}")
    st.markdown(f"{t('configure_game')} **{st.session_state.username}**!")

    game_mode_tabs = st.tabs([t("x01_setup"), t("cricket_soon")])

    with game_mode_tabs[0]: # X01 Setup Tab
        st.subheader(t("x01_options"))

        # --- Game Settings Columns ---
        col1, col2, col3 = st.columns(3)
        with col1:
            points_options = ["101", "201", "301", "401", "501"] # Common order
            try:
                default_points_index = points_options.index(str(st.session_state.get("game_mode", 501)))
            except ValueError:
                default_points_index = points_options.index("501")
            selected_points = st.selectbox(
                t("x01_mode"), # Using new translation key
                points_options,
                index=default_points_index,
                key="sb_game_mode"
            )
            st.session_state.game_mode = int(selected_points)

        with col2:
            checkout_options = ["Double Out", "Straight Out"]
            try:
                default_checkout_index = checkout_options.index(st.session_state.get("check_out_mode", "Double Out"))
            except ValueError:
                default_checkout_index = checkout_options.index("Double Out")
            selected_checkout = st.selectbox(
                t("check_out_mode"), # Using new translation key
                checkout_options,
                index=default_checkout_index,
                key="sb_checkout_mode"
            )
            st.session_state.check_out_mode = selected_checkout

        with col3:
            sets_options = list(range(1, 12)) # 1 to 11 sets
            try:
                default_sets_index = sets_options.index(st.session_state.get("sets_to_play", 1))
            except ValueError:
                default_sets_index = sets_options.index(1)
            selected_sets = st.selectbox(
                t("sets_to_win"), # Using new translation key
                sets_options,
                index=default_sets_index,
                key="sb_sets"
            )
            st.session_state.sets_to_play = selected_sets

        col4, col5, col6 = st.columns(3)
        with col4:
            set_leg_options = ["First to", "Best of"]
            try:
                default_set_leg_index = set_leg_options.index(st.session_state.get("set_leg_rule", "First to"))
            except ValueError:
                default_set_leg_index = set_leg_options.index("First to")
            selected_set_leg = st.selectbox(
                t("leg_set_rule"), # Using new translation key
                set_leg_options,
                index=default_set_leg_index,
                key="sb_set_leg_rule"
            )
            st.session_state.set_leg_rule = selected_set_leg

        with col5:
            checkin_options = ["Straight In", "Double In"]
            try:
                default_checkin_index = checkin_options.index(st.session_state.get("check_in_mode", "Straight In"))
            except ValueError:
                default_checkin_index = checkin_options.index("Straight In")
            selected_checkin = st.selectbox(
                t("check_in_mode"), # Using new translation key
                checkin_options,
                index=default_checkin_index,
                key="sb_checkin_mode",
                disabled=False # <<< CHANGED: Enabled selection
            )
            st.session_state.check_in_mode = selected_checkin

        with col6:
            legs_options = list(range(1, 12)) # 1 to 11 legs per set
            try:
                default_legs_index = legs_options.index(st.session_state.get("legs_to_play", 1))
            except ValueError:
                default_legs_index = legs_options.index(1)
            selected_legs = st.selectbox(
                t("legs_per_set"), # Using new translation key
                legs_options,
                index=default_legs_index,
                key="sb_legs"
            )
            st.session_state.legs_to_play = selected_legs

        # --- Player Selection / Add Player ---
        st.markdown("---")
        st.subheader(t("players"))
        available_players = []
        current_username_hp = st.session_state.username
        if current_username_hp and current_username_hp in users:
            # Use setdefault to ensure player_stats exists
            player_stats_dict_hp = users[current_username_hp].setdefault("player_stats", {})
            available_players = sorted(list(player_stats_dict_hp.keys()))
        else:
            st.error(t("user_data_error")) # More specific error

        selected_players_list = st.multiselect(
            t("select_players_for_game"),
            options=available_players,
            default=st.session_state.get("players_selected_for_game", []), # Use .get for safety
            key="multiselect_players"
        )
        # Update session state immediately after selection
        st.session_state.players_selected_for_game = selected_players_list

        with st.expander(t("add_manage_players")):
            st.write(t("add_new_player_info"))
            new_player_name_from_input = st.text_input(t("new_player_name"), key="new_player_name_input").strip()

            if st.button(t("add_player_button")):
                if new_player_name_from_input:
                    if current_username_hp and current_username_hp in users:
                        # Ensure 'player_stats' exists before trying to add to it
                        player_stats_dict_add = users[current_username_hp].setdefault("player_stats", {})
                        if new_player_name_from_input not in player_stats_dict_add:
                            # Add player with default stats and avatar
                            player_stats_dict_add[new_player_name_from_input] = {
                                "games_played": 0, "games_won": 0, "legs_won": 0, "sets_won": 0,
                                "total_score": 0, "highest_score": 0, "total_turns": 0,
                                "num_busts": 0, "darts_thrown": 0, "preferred_doubles": [],
                                "avatar": "🎯", # Default emoji avatar
                                # Generate a consistent avatar URL based on name
                                "avatar_url": f"https://api.dicebear.com/8.x/initials/svg?seed={new_player_name_from_input}" # Use initials
                            }
                            save_users(users)
                            st.success(f"Player '{new_player_name_from_input}' added.")
                            # Clear input field after adding
                            st.rerun() # Refresh to update multiselect options
                        else:
                            st.warning(f"Player '{new_player_name_from_input}' already exists.")
                    else:
                        st.error("Error saving player: User not found.")
                else:
                    st.warning("Please enter a name.")
            st.caption(t("edit_delete_in_settings"))

        st.markdown("---")

        # --- Start Game Button ---
        if st.button(t("start_game_button"), type="primary", use_container_width=True):
            players_to_start = st.session_state.players_selected_for_game
            # Validate selections
            if not players_to_start:
                st.warning(t("warning_select_players"))
            elif not st.session_state.game_mode or st.session_state.game_mode not in [101, 201, 301, 401, 501]:
                st.warning(t("warning_select_x01_mode"))
            else:
                # Initialize game state
                st.session_state.starting_score = st.session_state.game_mode
                st.session_state.player_scores = {p: st.session_state.starting_score for p in players_to_start}
                st.session_state.player_legs_won = {p: 0 for p in players_to_start}
                st.session_state.player_sets_won = {p: 0 for p in players_to_start}
                st.session_state.player_darts_thrown = {p: 0 for p in players_to_start}
                st.session_state.player_turn_history = {p: [] for p in players_to_start}
                st.session_state.player_last_turn_scores = {p: [] for p in players_to_start}
                st.session_state.current_player_index = 0 # Player 1 starts
                st.session_state.current_turn_shots = []
                st.session_state.current_leg = 1
                st.session_state.current_set = 1
                st.session_state.game_over = False
                st.session_state.leg_over = False
                st.session_state.set_over = False
                st.session_state.winner = None
                st.session_state.message = ""
                st.session_state.pending_modifier = None
                st.session_state.state_before_last_turn = None # Reset undo state

                # Navigate to Game page
                st.session_state.current_page = page_map.get("Game", "game")
                # Set navigation target for sidebar radio button sync
                st.session_state.nav_target = reverse_page_map.get("game", "Game")
                st.rerun() # Rerun to switch page and sync nav

    with game_mode_tabs[1]: # Cricket Tab Placeholder
        st.subheader("Cricket")
        st.info("🏏 Planned.")


# --- Statistics Page ---
elif st.session_state.current_page == "statistics":
    st.title(f"📊 {t('personal_statistics')}")
    st.write(f"{t('stats_for_account')} **{st.session_state.username}**")

    # Motivation Booster (API-powered with refresh button)
    st.markdown("---")
    st.subheader(t("motivation_booster"))

    # Use session state to store the quote to avoid re-fetching on every interaction
    if "motivational_quote" not in st.session_state:
        st.session_state.motivational_quote = get_motivational_quote()

    # Display the current quote
    st.info(st.session_state.motivational_quote)

    # Refresh button to get a new quote
    if st.button(t("get_new_quote")):
        st.session_state.motivational_quote = get_motivational_quote()
        st.rerun() # Refresh the page to show the new quote

    st.markdown("---")
    st.subheader(t("player_stats_header")) # Add this key to translations if needed

    current_username_stats = st.session_state.username
    # Safely access player stats
    if current_username_stats in users and "player_stats" in users.get(current_username_stats, {}):
        player_stats_data = users[current_username_stats]["player_stats"]
        if player_stats_data:
            # Prepare data for DataFrame
            data_for_df = []
            for player, stats in player_stats_data.items():
                games_played = stats.get("games_played", 0)
                games_won = stats.get("games_won", 0)
                total_score = stats.get("total_score", 0)
                total_turns = stats.get("total_turns", 0)
                darts_thrown = stats.get("darts_thrown", 0)

                win_rate = (games_won / games_played * 100) if games_played > 0 else 0
                avg_score_turn = (total_score / total_turns) if total_turns > 0 else 0
                avg_score_dart = (total_score / darts_thrown) if darts_thrown > 0 else 0

                data_for_df.append({
                    t("player"): player,
                    t("games_played"): games_played,
                    t("games_won"): games_won,
                    t("legs_won"): stats.get("legs_won", 0),
                    t("sets_won"): stats.get("sets_won", 0),
                    t("win_rate"): f"{win_rate:.2f}%",
                    t("total_score"): total_score,
                    t("avg_score_turn"): f"{avg_score_turn:.2f}",
                    t("avg_score_dart"): f"{avg_score_dart:.2f}",
                    t("highest_score"): stats.get("highest_score", 0),
                    t("total_turns"): total_turns,
                    t("darts_thrown"): darts_thrown,
                    t("busts"): stats.get("num_busts", 0)
                })

            if data_for_df:
                try:
                    df = pd.DataFrame(data_for_df)
                    df = df.set_index(t("player")) # Set player name as index
                    st.dataframe(df, use_container_width=True)

                    # --- Visualizations ---
                    st.markdown("---")
                    st.subheader(t("visualizations_placeholder"))

                    # Check if data exists before plotting
                    if not df.empty:
                        # Ensure numeric types for plotting, converting formatted strings back if needed
                        df_plot = pd.DataFrame.from_dict(player_stats_data, orient='index').fillna(0)
                        df_plot['win_rate'] = df_plot.apply(lambda row: (row['games_won'] / row['games_played']) * 100 if row['games_played'] > 0 else 0, axis=1)
                        df_plot['avg_score_per_turn'] = df_plot.apply(lambda row: (row['total_score'] / row['total_turns']) if row['total_turns'] > 0 else 0, axis=1)

                        col1, col2 = st.columns(2)
                        with col1:
                            fig1, ax1 = plt.subplots()
                            df_plot['games_played'].plot(kind='bar', ax=ax1, color='skyblue')
                            ax1.set_title(t("games_played"))
                            ax1.set_ylabel(t("games"))
                            ax1.set_xlabel(t("player"))
                            plt.xticks(rotation=45, ha='right')
                            plt.tight_layout()
                            st.pyplot(fig1)

                            fig3, ax3 = plt.subplots()
                            df_plot['avg_score_per_turn'].plot(kind='bar', ax=ax3, color='orange')
                            ax3.set_title(t("avg_score_turn"))
                            ax3.set_ylabel(t("avg_short") + " " + t("score"))
                            ax3.set_xlabel(t("player"))
                            plt.xticks(rotation=45, ha='right')
                            plt.tight_layout()
                            st.pyplot(fig3)

                        with col2:
                            fig2, ax2 = plt.subplots()
                            df_plot['win_rate'].plot(kind='bar', ax=ax2, color='lightgreen')
                            ax2.set_title(t("win_rate"))
                            ax2.set_ylabel(t("win_rate"))
                            ax2.set_xlabel(t("player"))
                            ax2.yaxis.set_major_formatter(plt.FuncFormatter('{:.0f}%'.format))
                            plt.xticks(rotation=45, ha='right')
                            plt.tight_layout()
                            st.pyplot(fig2)

                            fig4, ax4 = plt.subplots()
                            df_plot['highest_score'].plot(kind='bar', ax=ax4, color='salmon')
                            ax4.set_title(t("highest_score"))
                            ax4.set_ylabel(t("score"))
                            ax4.set_xlabel(t("player"))
                            plt.xticks(rotation=45, ha='right')
                            plt.tight_layout()
                            st.pyplot(fig4)

                        # Single column chart for darts thrown
                        fig5, ax5 = plt.subplots()
                        df_plot['darts_thrown'].plot(kind='bar', ax=ax5, color='purple')
                        ax5.set_title(t("darts_thrown"))
                        ax5.set_ylabel(t("darts"))
                        ax5.set_xlabel(t("player"))
                        plt.xticks(rotation=45, ha='right')
                        plt.tight_layout()
                        st.pyplot(fig5)

                    else:
                         st.info(t("no_player_stats_recorded"))

                except Exception as e:
                    st.error(f"{t('error_displaying_table')}: {e}")
            else:
                st.info(t("no_data_for_statistic")) # Or player stats?
        else:
            st.info(t("no_player_stats_yet"))
    else:
        st.warning(t("could_not_load_stats"))


# --- Settings Page ---
elif st.session_state.current_page == "settings":
    st.title(t("settings_title"))
    st.write(f"{t('manage_players_prefs')} **{st.session_state.username}**")
    st.markdown("---")

    # Language Settings Expander
    with st.expander(t("language_settings")):
        # Determine current language index
        current_lang_code = st.session_state.get("language", "en")
        lang_options = ["en", "de"]
        try:
            current_lang_index = lang_options.index(current_lang_code)
        except ValueError:
            current_lang_index = 0 # Default to English if state is somehow invalid

        selected_lang_code = st.selectbox(
            t("select_language"),
            options=lang_options,
            index=current_lang_index,
            format_func=lambda x: "English" if x == "en" else "Deutsch",
            key="lang_select_settings"
        )
        # Update language if changed
        if selected_lang_code != current_lang_code:
            st.session_state.language = selected_lang_code
            st.success("✅ Language updated!")
            time.sleep(0.5) # Brief pause for feedback
            st.rerun()

    # Account Avatar Expander
    with st.expander(t("change_account_avatar")):
        st.markdown(f"### {t('select_new_avatar')}")

        # Use the same consistent avatar options as registration
        avatar_styles = ["avataaars", "bottts", "croodles", "identicon", "pixel-art"]
        avatar_seeds = ["Hero", "Champ", "Legend", "Master", "Bullseye"]
        avatar_options_settings = []
        for style, seed in zip(avatar_styles[:5], avatar_seeds[:5]):
            avatar_url = f"https://api.dicebear.com/8.x/{style}/svg?seed={seed}"
            avatar_options_settings.append((f"{style}_{seed}", avatar_url))

        # Get current avatar to set default for radio
        current_user_avatar_key = users.get(st.session_state.username, {}).get("avatar_choice", avatar_options_settings[0][0])
        try:
             default_avatar_index = [opt[0] for opt in avatar_options_settings].index(current_user_avatar_key)
        except ValueError:
             default_avatar_index = 0 # Default to first if current is somehow invalid

        selected_avatar_key_settings = st.radio(
            t("choose_new_avatar"),
            options=[option[0] for option in avatar_options_settings],
            index=default_avatar_index,
            format_func=lambda x: x.split("_")[1].capitalize(),
            horizontal=True,
            key="settings_avatar_select"
        )

        # Show preview
        selected_avatar_url_settings_preview = ""
        for name, url in avatar_options_settings:
             if name == selected_avatar_key_settings:
                 selected_avatar_url_settings_preview = url
                 break
        if selected_avatar_url_settings_preview:
             st.image(selected_avatar_url_settings_preview, width=120, caption=t("preview"))

        # Save button
        if st.button(t("save_avatar_choice"), key="save_account_avatar_settings"):
            if st.session_state.username in users:
                users[st.session_state.username]["avatar_choice"] = selected_avatar_key_settings
                save_users(users)
                st.success(t("avatar_updated_success"))
                time.sleep(1)
                st.rerun() # Rerun to update sidebar image immediately
            else:
                st.error("User not found, cannot save avatar.")


    st.markdown("---") # Separator

    # --- Player Preferences and Deletion ---
    current_username_settings = st.session_state.username
    # Ensure user and player_stats exist before accessing
    if current_username_settings not in users or "player_stats" not in users.get(current_username_settings, {}):
        st.error(t("user_data_error"))
        st.stop() # Stop rendering this part if data is missing

    # Safely get player_stats dictionary
    player_stats_dict_settings = users[current_username_settings].setdefault("player_stats", {})
    players_list_settings = sorted(list(player_stats_dict_settings.keys()))

    if not players_list_settings:
         st.warning(t("no_players_added"))
         st.info(t("add_players_homepage"))
    else:
        tab_prefs, tab_delete = st.tabs([t("set_preferences"), t("delete_player")])

        # --- Preferences Tab ---
        with tab_prefs:
            st.subheader(t("set_preferred_double_outs")) # Updated title
            # st.write("Select preferred doubles and an emoji avatar for each player.") # Already in subheader

            # Select Player to Edit
            player_to_edit = st.selectbox(
                t("select_player_edit_prefs"),
                players_list_settings,
                key="edit_prefs_player_select",
                index=None, # No default selection
                placeholder=t("choose_player_placeholder")
            )

            if player_to_edit:
                # --- Load current settings for the selected player ---
                player_data_edit = player_stats_dict_settings.get(player_to_edit, {})
                current_prefs_list = player_data_edit.get('preferred_doubles', [])
                # Filter prefs to ensure they are valid doubles before displaying
                current_preferences_formatted = [pref for pref in current_prefs_list if pref in ALL_POSSIBLE_DOUBLES]
                current_avatar_emoji = player_data_edit.get("avatar", "🎯") # Default emoji

                # --- Avatar Emoji Selection ---
                emoji_options = ["🎯", "🔥", "🎉", "💥", "👑", "⚡", "🥇", "😎", "🚀", "💡", "⭐", "👍"] # Expanded options
                try:
                    current_emoji_index = emoji_options.index(current_avatar_emoji)
                except ValueError:
                    current_emoji_index = 0 # Default to first emoji

                selected_avatar_emoji = st.selectbox(
                    f"{t('select_avatar_for_player')} **{player_to_edit}**:",
                    emoji_options,
                    index=current_emoji_index,
                    key=f"avatar_emoji_select_{player_to_edit}" # Unique key per player
                )
                st.caption(t("choose_emoji_caption"))

                # --- Preferred Doubles Selection ---
                selected_doubles = st.multiselect(
                    f"{t('select_preferred_doubles_for')} **{player_to_edit}**:",
                    options=ALL_POSSIBLE_DOUBLES,
                    default=current_preferences_formatted,
                    key=f"pref_doubles_multiselect_{player_to_edit}", # Unique key per player
                )

                # --- Save Button ---
                if st.button(f"{t('save_prefs_button_label')} {player_to_edit}", type="primary", key=f"save_prefs_{player_to_edit}"):
                    # Re-check player exists before saving (paranoid check)
                    if player_to_edit in users[current_username_settings].get("player_stats", {}):
                        users[current_username_settings]["player_stats"][player_to_edit]['preferred_doubles'] = selected_doubles
                        users[current_username_settings]["player_stats"][player_to_edit]["avatar"] = selected_avatar_emoji
                        save_users(users)
                        st.success(f"{t('prefs_saved_success')} {player_to_edit}!")
                        time.sleep(1)
                        # No rerun needed usually, changes are saved. Can add if state needs refresh.
                    else:
                        st.error(t("player_not_found_error"))
            else:
                 # Show placeholder text if no player is selected
                 st.info("Select a player above to edit their preferences.")


        # --- Delete Player Tab ---
        with tab_delete:
            st.subheader(t("delete_player_data"))
            st.warning(t("delete_warning"))

            # Initialize confirmation state if needed
            if "confirm_delete_player" not in st.session_state:
                st.session_state.confirm_delete_player = None

            player_to_delete = st.selectbox(
                t("select_player_to_delete"),
                players_list_settings, # Use the list derived for settings
                index=None, # No default selection
                placeholder=t("choose_player_placeholder"),
                key="delete_player_select_settings_tab" # Unique key
            )

            # Button to initiate deletion confirmation
            delete_button_disabled = (player_to_delete is None) or (st.session_state.confirm_delete_player == player_to_delete)
            delete_button_label = f"{t('delete_button_label')} {player_to_delete}" if player_to_delete else f"{t('delete_button_label')}..."

            if st.button(delete_button_label, type="secondary", disabled=delete_button_disabled, key="settings_delete_request_btn"):
                 if player_to_delete:
                     st.session_state.confirm_delete_player = player_to_delete
                     st.rerun() # Rerun to show confirmation controls

            # Confirmation Step Display (if a player is pending confirmation)
            if st.session_state.confirm_delete_player:
                # Only show confirmation if the currently selected player matches the one pending confirmation
                if player_to_delete == st.session_state.confirm_delete_player:
                    st.error(f"**{t('confirm_delete_error')} {st.session_state.confirm_delete_player}?**")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button(t("yes_delete"), type="primary", use_container_width=True, key="settings_confirm_delete_btn"):
                            try:
                                player_name_confirmed = st.session_state.confirm_delete_player
                                # Final check if player exists before deleting
                                if player_name_confirmed in users[current_username_settings]["player_stats"]:
                                    del users[current_username_settings]["player_stats"][player_name_confirmed] # Delete stats entry
                                    # Also remove from checkout logs if they exist
                                    if "checkout_log" in users[current_username_settings]:
                                        users[current_username_settings]["checkout_log"] = [
                                            entry for entry in users[current_username_settings].get("checkout_log", [])
                                            if entry.get("player") != player_name_confirmed
                                        ]
                                    save_users(users)
                                    st.success(f"{t('deleted_success_message')} {player_name_confirmed}.")
                                else:
                                    st.error(t("player_already_deleted_error"))

                                st.session_state.confirm_delete_player = None # Reset confirmation state
                                time.sleep(1)
                                st.rerun() # Refresh page to update player lists
                            except Exception as e:
                                st.error(f"{t('deletion_error')} {e}")
                                st.session_state.confirm_delete_player = None
                                st.rerun()
                    with col_cancel:
                         if st.button(t("cancel"), type="secondary", use_container_width=True, key="settings_cancel_delete_btn"):
                              st.session_state.confirm_delete_player = None # Reset confirmation state
                              st.rerun() # Rerun to hide confirmation controls
                else:
                     # If selection changed after clicking delete once, reset confirmation silently
                     st.session_state.confirm_delete_player = None
                     # No rerun needed here, the confirmation section just won't render


# --- Game Page ---
elif st.session_state.current_page == "game":

    # --- Game Helper Functions (Keep expanded as requested) ---
    def parse_score_input(score_str):
        """Parses dart input string (e.g., '20', 'D18', 'T19', '0') into value and modifiers."""
        score_str = str(score_str).upper().strip()
        is_double = False
        is_triple = False
        value = 0
        is_valid = True # Assume valid initially
        try:
            if score_str.startswith("T"):
                if len(score_str) > 1 and score_str[1:].isdigit():
                    num = int(score_str[1:])
                    if 1 <= num <= 20:
                        value = num * 3
                        is_triple = True
                    else: is_valid = False # Triple only 1-20
                else: is_valid = False # Invalid format like "T" or "Txx"
            elif score_str.startswith("D"):
                 if len(score_str) > 1 and score_str[1:].isdigit():
                     num = int(score_str[1:])
                     if 1 <= num <= 20 or num == 25: # Double can be 1-20 or 25 (Bull)
                         value = num * 2
                         is_double = True
                     else: is_valid = False # Invalid double number
                 else: is_valid = False # Invalid format like "D" or "Dxx"
            elif score_str.isdigit():
                num = int(score_str)
                if 0 <= num <= 20 or num == 25: # Single 0-20 or 25 (Outer Bull)
                    value = num
                    # Handle 50 explicitly entered - guide user to D25
                    if num == 50:
                         st.toast(t("toast_use_d25"), icon="💡")
                         is_valid = False # Treat direct 50 as invalid input here
                         value = 0 # Reset value
                else: is_valid = False # Single number out of range
            else:
                is_valid = False # Not T, D, or digit

        except ValueError: # Handle potential int() conversion errors
            is_valid = False

        return value, is_double, is_triple, is_valid

    def get_throw_value(throw_str):
        """Utility to quickly get just the numeric value of a parsed throw."""
        value, _, _, is_valid = parse_score_input(throw_str)
        return value if is_valid else 0 # Return 0 if the format was invalid

    def calculate_turn_total(shots_list):
        """Calculates total score, darts thrown, and if last dart was double from a list of shot strings."""
        total = 0
        darts_thrown_turn = 0
        last_dart_double_flag = False
        parsed_shots_details = [] # Could be used for detailed logging later

        if not shots_list: # Handle empty list case
            return 0, 0, False, []

        for i, shot_str in enumerate(shots_list):
            value, is_double, is_triple, is_valid = parse_score_input(shot_str)
            if not is_valid:
                # If any shot string is invalid, the turn total is considered invalid.
                return None, darts_thrown_turn, False, parsed_shots_details # Signal error

            total += value
            darts_thrown_turn += 1
            # Only the *last* shot determines if the turn ended on a double
            last_dart_double_flag = is_double
            parsed_shots_details.append({"input": shot_str, "value": value, "is_double": is_double, "is_triple": is_triple})

        return total, darts_thrown_turn, last_dart_double_flag, parsed_shots_details

    def run_turn_processing(player_name, shots_list):
        """Processes the end of a turn: updates scores, stats, logs, and determines next state."""
        global users # Allow modification of the global user data
        current_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
        current_player_index_before_turn = st.session_state.current_player_index
        score_before_turn = st.session_state.player_scores.get(player_name, 0) # Use .get for safety

        # --- Store state BEFORE processing for potential UNDO ---
        # Create a deep copy if complex objects are involved, though basic types are fine here
        st.session_state.state_before_last_turn = {
            "player_index": current_player_index_before_turn,
            "player_name": player_name,
            "score_before": score_before_turn,
            "darts_thrown_player_before": st.session_state.player_darts_thrown.get(player_name, 0),
            "current_turn_shots_processed": list(shots_list), # Copy the list
            "legs_won_before": st.session_state.player_legs_won.get(player_name, 0),
            "sets_won_before": st.session_state.player_sets_won.get(player_name, 0),
            # Add other relevant states if needed for perfect undo (e.g., current leg/set numbers)
            "current_leg_before": st.session_state.current_leg,
            "current_set_before": st.session_state.current_set,
        }

        # --- Calculate Turn Outcome ---
        calculated_score, darts_thrown_turn, last_dart_double, _ = calculate_turn_total(shots_list)

        # Handle calculation error (e.g., if an invalid shot string somehow got processed)
        if calculated_score is None:
            st.error(t("internal_error_score_calc"))
            st.session_state.state_before_last_turn = None # Invalidate undo state on error
            return # Stop processing this turn

        new_score = score_before_turn - calculated_score
        is_bust = False
        is_win = False
        valid_checkout_attempt = True # Assume valid unless proven otherwise
        turn_result_for_log = "UNKNOWN" # For detailed logging

        # --- Determine Turn Result ---
        # 1. Check for Bust (Score < 0 or exactly 1)
        if new_score < 0 or new_score == 1:
            is_bust = True
            turn_result_for_log = "BUST"
            st.toast(f"{t('toast_bust')} {score_before_turn}", icon="❌")
            # Score remains unchanged on bust
            st.session_state.player_scores[player_name] = score_before_turn
            st.session_state.message = f"{player_name} {t('toast_player_busted')}"

        # 2. Check for Exact Zero (Potential Win)
        elif new_score == 0:
            # Check validity based on checkout mode
            if st.session_state.check_out_mode == "Double Out" and not last_dart_double:
                # Invalid Double Out -> Treat as Bust
                is_bust = True # Set bust flag for advancement logic
                valid_checkout_attempt = False # Mark attempt as invalid
                turn_result_for_log = "BUST (Invalid Checkout)"
                st.toast(f"{t('toast_invalid_checkout')} {score_before_turn}", icon="❌")
                st.session_state.player_scores[player_name] = score_before_turn # Score remains
                st.session_state.message = f"{player_name} {t('toast_player_invalid_checkout')}"
            else:
                # Valid Win!
                is_win = True
                turn_result_for_log = "WIN"
                st.toast(f"{t('toast_game_shot_leg')} {player_name} {t('toast_wins_leg')} {st.session_state.current_leg}!", icon="🎯")
                st.session_state.player_scores[player_name] = 0 # Set score to 0
                st.session_state.message = f"{player_name} {t('toast_wins_leg')} {st.session_state.current_leg}!"
                st.session_state.leg_over = True # Signal leg end
                # Increment leg count in session state immediately for checks
                st.session_state.player_legs_won[player_name] = st.session_state.player_legs_won.get(player_name, 0) + 1
                 # Update persistent leg win stats
                if player_name in users.get(st.session_state.username, {}).get("player_stats", {}):
                    users[st.session_state.username]["player_stats"][player_name]["legs_won"] = users[st.session_state.username]["player_stats"][player_name].get("legs_won", 0) + 1
                    # No immediate save here, save after all stats potentially updated

        # 3. Regular Score Update (Neither Bust nor Win)
        else:
            turn_result_for_log = "OK"
            st.session_state.player_scores[player_name] = new_score
            st.session_state.message = f"{player_name} {t('toast_player_scored')} {calculated_score}."

        # --- Update Turn History and Last Turn Display ---
        # Append regardless of bust/win/ok, but log includes result type
        st.session_state.player_turn_history.setdefault(player_name, []).append((calculated_score, darts_thrown_turn, turn_result_for_log))
        st.session_state.player_last_turn_scores[player_name] = list(shots_list) # Store shots for display

        # --- Update Persistent Player Stats ---
        current_username_stats_update = st.session_state.username
        # Safely access the specific player's stats dictionary
        player_stats_ptr = users.get(current_username_stats_update, {}).get("player_stats", {}).get(player_name)

        if player_stats_ptr: # Check if player stats dict exists
            # Increment busts if applicable
            if is_bust and turn_result_for_log.startswith("BUST"):
                 player_stats_ptr["num_busts"] = player_stats_ptr.get("num_busts", 0) + 1

            # Increment turns and darts thrown if turn was valid (not an internal calc error)
            if turn_result_for_log != "UNKNOWN": # i.e., turn processed ok/bust/win
                player_stats_ptr["total_turns"] = player_stats_ptr.get("total_turns", 0) + 1
                player_stats_ptr["darts_thrown"] = player_stats_ptr.get("darts_thrown", 0) + darts_thrown_turn

            # Add score to total only if it wasn't a bust
            if not is_bust and calculated_score is not None:
                player_stats_ptr["total_score"] = player_stats_ptr.get("total_score", 0) + calculated_score

            # Update highest score if this turn was higher
            if calculated_score is not None and calculated_score > player_stats_ptr.get("highest_score", 0):
                player_stats_ptr["highest_score"] = calculated_score

            # Legs/Sets won stats updated during advancement checks below

        # --- Detailed Logging for Checkouts / Busts on Finish Attempts ---
        # Log if score was in finish range (excluding bogies) AND it was a win or bust
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
                log_list = users[current_username_stats_update].setdefault("checkout_log", [])
                log_list.append(log_entry)
            except Exception as e:
                st.error(f"{t('toast_log_error')} {e}")

        # --- Save User Data Once After All Turn Updates ---
        save_users(users)

        # --- Post-Turn Advancement Logic ---
        num_players_adv = len(st.session_state.players_selected_for_game)
        # Turn advances if bust, win, or 3 darts thrown, *unless* it was an invalid checkout attempt
        should_advance_turn = (is_bust or is_win or (len(shots_list) == 3))

        # Override: Don't advance turn if it was an invalid checkout (score became 0 but not with double)
        # This allows the player to correct their input for the *same* turn.
        if not valid_checkout_attempt and new_score == 0:
            should_advance_turn = False
            st.warning(t("correct_score_try_again")) # Prompt user

        if should_advance_turn:
            index_before_advance = st.session_state.current_player_index # Store index before changing it
            # Update the undo state with the index *before* advancing
            if st.session_state.state_before_last_turn:
                st.session_state.state_before_last_turn["player_index"] = index_before_advance

            # Clear the input buffer for the next player/turn
            st.session_state.current_turn_shots = []
            st.session_state.pending_modifier = None # Clear D/T modifier

            # --- Check for Leg/Set/Game End ---
            if st.session_state.leg_over: # Implies a valid WIN occurred
                # Determine legs needed based on rule
                if st.session_state.set_leg_rule == "Best of":
                    legs_needed = math.ceil((st.session_state.legs_to_play + 1) / 2)
                else: # "First to"
                    legs_needed = st.session_state.legs_to_play

                # Check if this leg win results in winning the Set
                if st.session_state.player_legs_won.get(player_name, 0) >= legs_needed:
                    st.session_state.set_over = True
                    st.session_state.player_sets_won[player_name] = st.session_state.player_sets_won.get(player_name, 0) + 1
                    st.success(f"🎉 {player_name} {t('toast_player_wins_set')} {st.session_state.current_set}!")
                    # Update persistent set win stat
                    if player_name in users[current_username_stats_update]["player_stats"]:
                         users[current_username_stats_update]["player_stats"][player_name]["sets_won"] = users[current_username_stats_update]["player_stats"][player_name].get("sets_won",0)+1
                         save_users(users) # Save after set win update

                    # Check if this set win results in winning the Game
                    if st.session_state.set_leg_rule == "Best of":
                         sets_needed = math.ceil((st.session_state.sets_to_play + 1) / 2)
                    else: # "First to"
                         sets_needed = st.session_state.sets_to_play

                    if st.session_state.player_sets_won.get(player_name, 0) >= sets_needed:
                        # --- GAME OVER ---
                        st.session_state.game_over = True
                        st.session_state.winner = player_name
                        st.session_state.state_before_last_turn = None # Cannot undo after game over

                        # Update final game stats (played/won) for all participants
                        for p in st.session_state.players_selected_for_game:
                             player_stats_final = users.get(current_username_stats_update, {}).get("player_stats", {}).get(p)
                             if player_stats_final:
                                 player_stats_final["games_played"] = player_stats_final.get("games_played", 0) + 1
                                 if p == player_name: # Increment wins only for the winner
                                     player_stats_final["games_won"] = player_stats_final.get("games_won", 0) + 1
                        save_users(users) # Save final game stats

                        # Don't advance player index or clear state here, game over screen handles it
                        st.rerun() # Rerun to show Game Over screen

                    else:
                        # --- SET OVER, but Game Not Over -> Start Next Set ---
                        st.toast(t("toast_prepare_next_set"), icon="⏳")
                        time.sleep(1.5)
                        st.session_state.current_set += 1
                        st.session_state.current_leg = 1 # Reset leg counter for new set
                        # Reset scores and leg wins for the new set
                        st.session_state.player_scores = {p: st.session_state.starting_score for p in st.session_state.players_selected_for_game}
                        st.session_state.player_legs_won = {p: 0 for p in st.session_state.players_selected_for_game}
                        st.session_state.player_last_turn_scores = {p: [] for p in st.session_state.players_selected_for_game} # Clear last turn display
                        st.session_state.leg_over = False # Reset flags
                        st.session_state.set_over = False
                        # Alternate starting player for the new set (player after the one who won the last leg starts)
                        st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
                        st.session_state.state_before_last_turn = None # Clear undo state on set transition

                else:
                    # --- LEG OVER, but Set Not Over -> Start Next Leg ---
                    st.toast(t("toast_prepare_next_leg"), icon="⏳")
                    time.sleep(1.5)
                    st.session_state.current_leg += 1
                    # Reset scores for the new leg
                    st.session_state.player_scores = {p: st.session_state.starting_score for p in st.session_state.players_selected_for_game}
                    st.session_state.player_last_turn_scores = {p: [] for p in st.session_state.players_selected_for_game} # Clear last turn display
                    st.session_state.leg_over = False # Reset flag
                    # Alternate starting player for the new leg
                    st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
                    st.session_state.state_before_last_turn = None # Clear undo state on leg transition

            else:
                # --- Leg Not Over, Just Advance Player ---
                st.session_state.current_player_index = (index_before_advance + 1) % num_players_adv
                # Keep undo state available when just switching players

            # Rerun AFTER all advancement logic (if game not over) is complete
            if not st.session_state.game_over:
                 st.rerun()
        # else: Turn did not advance (e.g., invalid checkout), allow correction without rerun here


    # --- Checkout Calculation Function (Cached) ---
    @st.cache_data(ttl=3600) # Cache results for an hour
    def get_checkouts(target_score, darts_left, max_suggestions=3): # Default to 3 suggestions
        """Calculates possible checkout paths for a given score and darts remaining."""
        # Basic validation
        if darts_left not in [1, 2, 3] or target_score < 2 or target_score > 170 or target_score in BOGIE_NUMBERS_SET:
            return [] # No checkout possible or needed

        valid_paths = []
        # Define throw priorities (Try higher value triples/doubles first) - customize as needed
        throws_priority = (
            [f"T{i}" for i in range(20, 14, -1)] + # T20-T15
            [f"D{i}" for i in range(20, 0, -1)] + ["D25"] + # All Doubles + Bull
            [str(i) for i in range(20, 0, -1)] + ["25"] + # All Singles + Outer Bull
            [f"T{i}" for i in range(14, 0, -1)] # Lower Triples T14-T1
        )

        # --- 1 Dart Left ---
        if darts_left == 1:
            # Must be a double (<=40 and even) or D25 (50)
            if (target_score <= 40 and target_score % 2 == 0) or target_score == 50:
                double = f"D{target_score // 2}" if target_score != 50 else "D25"
                return [[double]] # Return list containing a list with the single dart
            else:
                return [] # Cannot finish in 1 dart

        # --- 2 Darts Left ---
        # Iterate through possible first darts
        if darts_left >= 2:
            for throw1 in throws_priority:
                val1 = get_throw_value(throw1)
                # Check if first throw leaves a valid 1-dart finish
                if 0 < val1 < target_score: # Must score less than target
                     remaining_score1 = target_score - val1
                     # Check if the remainder can be finished with 1 dart (which must be a double)
                     one_dart_finish_list = get_checkouts(remaining_score1, 1) # Recursive call
                     if one_dart_finish_list: # If a 1-dart finish exists
                         # Construct the 2-dart path
                         path = [throw1, one_dart_finish_list[0][0]] # [first_throw, required_double]
                         # Avoid duplicates if different throw orders yield same path (less likely here)
                         if path not in valid_paths:
                             valid_paths.append(path)
                             # Stop if we have enough suggestions
                             if len(valid_paths) >= max_suggestions: break
            # If only 2 darts available, return paths found so far
            if darts_left == 2:
                 return valid_paths[:max_suggestions]
            # If 3 darts available, continue to 3-dart logic if not enough paths found yet
            if len(valid_paths) >= max_suggestions:
                 return valid_paths[:max_suggestions]


        # --- 3 Darts Left ---
        # Iterate through possible first darts
        if darts_left == 3:
             for throw1 in throws_priority:
                 val1 = get_throw_value(throw1)
                 # Check if first throw leaves a possible 2-dart finish score
                 # Target must be at least 2 (D1) after first throw
                 if 0 < val1 <= target_score - 2:
                     remaining_score1 = target_score - val1
                     # Find possible 2-dart finishes for the remainder
                     # Ask for only 1-2 suggestions here to limit combinations explored
                     two_dart_finishes = get_checkouts(remaining_score1, 2, max_suggestions=2)
                     if two_dart_finishes:
                         # Combine first throw with the found 2-dart finishes
                         for finish2dart in two_dart_finishes:
                             full_path = [throw1] + finish2dart # [throw1, throw2, double_finish]
                             if full_path not in valid_paths:
                                 valid_paths.append(full_path)
                                 if len(valid_paths) >= max_suggestions: break # Stop outer loop too
                     if len(valid_paths) >= max_suggestions: break # Stop outer loop
             # Return up to max_suggestions found 3-dart paths
             return valid_paths[:max_suggestions]

        # Should not be reached if logic is correct, but return empty list as fallback
        return []


    # --- Setup Shot Calculation Function ---
    def get_setup_shot(current_score):
        """Suggests a single shot to leave a preferred double, if no direct finish is viable."""
        # Define preferred leave scores (often doubles or scores easily leading to doubles)
        # Customize this list based on common strategies or preferences
        preferred_leaves = [32, 40, 16, 8, 36, 24, 4, 50, 20, 10, 12, 18, 6, 2] # D16, D20, D8, D4, D18, D12, D2, Bull, D10, D5, D6, D9, D3, D1

        # Try to hit a single that leaves a preferred double
        for target_leave in preferred_leaves:
            needed_score = current_score - target_leave
            # Check if the needed score is a single valid hit (1-20 or 25)
            if (1 <= needed_score <= 20 or needed_score == 25):
                # Ensure we are actually setting up (needed score > 0) and leave is valid
                if needed_score > 0 and target_leave >= 2:
                    # Suggest hitting the single 'needed_score'
                    return f"{needed_score} ({t('leaves_short')} {target_leave})" # Use translation key

        # Fallback: If no preferred leave is reachable with one single, suggest hitting highest possible single? (Less common strategy)
        # Or simply return None if no simple setup found.
        # Example: Suggest hitting 20 if score > 40?
        # if current_score > 40:
        #     return f"20 ({t('leaves_short')} {current_score - 20})"

        return None # No simple setup shot found

    def sort_checkouts_by_preference(paths, preferred_doubles_set):
        """Sorts checkout paths, prioritizing those ending on preferred doubles."""
        if not preferred_doubles_set: # If no preferences set, return original order
            return paths

        preferred_paths = []
        other_paths = []
        for path in paths:
            # Check if path is valid and ends with a double string
            if path and isinstance(path[-1], str) and path[-1].startswith("D"):
                if path[-1] in preferred_doubles_set:
                    preferred_paths.append(path)
                else:
                    other_paths.append(path)
            else: # Path doesn't end with a double? Add to others.
                other_paths.append(path)
        return preferred_paths + other_paths


    # --- Check Game State ---
    if st.session_state.game_over:
        st.title(t("game_over_title"))
        if st.session_state.winner:
            st.header(f"🏆 {t('game_over_winner_header')} {st.session_state.winner} 🏆")
        else:
            st.header(t("game_over_no_winner")) # e.g., if ended early
        st.balloons()

        st.markdown("---")
        st.subheader(t("game_over_player_overview"))

        current_username_gameover = st.session_state.username
        player_stats_gameover = users.get(current_username_gameover, {}).get("player_stats", {})
        selected_players_gameover = st.session_state.get("players_selected_for_game", []) # Get list safely

        if selected_players_gameover:
             # Dynamic columns based on number of players
             cols = st.columns(len(selected_players_gameover))

             for idx, player in enumerate(selected_players_gameover):
                 with cols[idx]:
                     player_data = player_stats_gameover.get(player, {})
                     # Use player-specific emoji avatar if available
                     avatar_emoji = player_data.get("avatar", "🎯")
                     st.markdown(f"<p style='font-size: 40px; text-align: center;'>{avatar_emoji}</p>", unsafe_allow_html=True)
                     st.markdown(f"**<p style='text-align: center;'>{player}</p>**", unsafe_allow_html=True)
                     st.markdown(f"{t('game_over_sets_won')} {st.session_state.player_sets_won.get(player, 0)}")
                     st.markdown(f"{t('game_over_legs_won')} {st.session_state.player_legs_won.get(player, 0)}")
                     # Calculate score from history (more accurate than final score if game ended mid-leg)
                     history = st.session_state.player_turn_history.get(player, [])
                     total_score_in_game = sum(t[0] for t in history if len(t)>2 and not t[2].startswith("BUST")) # Sum non-bust scores
                     st.markdown(f"{t('game_over_total_score')} {total_score_in_game}")
        else:
             st.warning("No player data found for game summary.")


        if st.button(t("game_over_play_again"), use_container_width=True, type="primary"):
            # Reset essential game states for a new game setup on homepage
            st.session_state.players_selected_for_game = [] # Clear selected players
            st.session_state.game_over = True # Keep game over conceptually until new game starts
            # Navigate back to homepage
            st.session_state.current_page = page_map.get("Homepage", "homepage")
            st.session_state.nav_target = reverse_page_map.get("homepage", "Homepage") # Sync sidebar
            st.rerun()
        st.stop() # Stop execution here after game over screen

    # --- Check if Players are Selected ---
    if not st.session_state.players_selected_for_game:
         st.error(t("no_players_in_game_warning"))
         if st.button(t("back_to_homepage"), use_container_width=True):
             st.session_state.current_page = page_map.get("Homepage", "homepage")
             st.session_state.nav_target = reverse_page_map.get("homepage", "Homepage")
             st.rerun()
         st.stop() # Stop if no players

    # --- Game Interface ---
    st.title(f"🎯 {t('game_on')}: {st.session_state.game_mode} - {t('set')} {st.session_state.current_set}/{st.session_state.sets_to_play} | {t('leg')} {st.session_state.current_leg}/{st.session_state.legs_to_play}")
    st.caption(f"{t('mode')}: {st.session_state.check_out_mode} ({st.session_state.check_in_mode}) | {t('rule')}: {st.session_state.set_leg_rule}")

    # --- REMOVED Motivational Quote During Game ---
    # quote = get_motivational_quote()
    # st.markdown(f"💡 **Motivation Boost:** _{quote}_")

    # --- Main Two-Column Layout ---
    left_col, right_col = st.columns([2, 1.2]) # Adjusted column ratio slightly

    with left_col:
        # --- Scoreboard Display ---
        st.subheader(t("scores_header"))
        num_players = len(st.session_state.players_selected_for_game)
        if num_players > 0:
            current_player_index_safe = st.session_state.current_player_index % num_players # Ensure index is valid

            for i, player in enumerate(st.session_state.players_selected_for_game):
                is_current_player = (i == current_player_index_safe)
                # Get player-specific avatar emoji
                player_data = users.get(st.session_state.username, {}).get("player_stats", {}).get(player, {})
                avatar_emoji = player_data.get("avatar", "🎯") # Default

                # Highlight current player
                border_style = "border: 3px solid #FF4B4B; padding: 10px 10px; border-radius: 8px; background-color: #FFF0F0; margin-bottom: 10px;" if is_current_player else "border: 1px solid #ccc; padding: 10px 10px; border-radius: 8px; margin-bottom: 10px;"
                with st.container():
                    st.markdown(f"<div style='{border_style}'>", unsafe_allow_html=True)

                    # Player Header (Avatar + Name)
                    st.markdown(f"""
                        <div style='display: flex; align-items: center; margin-bottom: 5px;'>
                            <span style='font-size: 28px; margin-right: 10px;'>{avatar_emoji}</span>
                            <h5 style='margin: 0; font-weight: bold;'>{player} {'▶️' if is_current_player else ''}</h5>
                        </div>
                    """, unsafe_allow_html=True)

                    col_score, col_stats_checkout = st.columns([1, 1]) # Split area below name

                    with col_score:
                        # Display current score, potentially adjusted by throws this turn
                        actual_score = st.session_state.player_scores.get(player, st.session_state.starting_score)
                        display_score_val = actual_score
                        score_color = "black"
                        is_potential_bust = False
                        partial_turn_score = 0

                        # If it's the current player's turn and they've thrown darts
                        if is_current_player and st.session_state.current_turn_shots:
                            partial_turn_score_calc, _, _, _ = calculate_turn_total(st.session_state.current_turn_shots)
                            if partial_turn_score_calc is not None:
                                partial_turn_score = partial_turn_score_calc
                                temp_remaining_score = actual_score - partial_turn_score
                                # Check for potential bust based on throws so far
                                if temp_remaining_score < 0 or temp_remaining_score == 1:
                                    display_score_val = "BUST"
                                    score_color = "red"
                                    is_potential_bust = True
                                elif temp_remaining_score >= 0:
                                    display_score_val = temp_remaining_score # Show potential score remaining

                        # Display the main score
                        st.markdown(f"<h2 style='text-align: center; font-size: 3.5em; margin-bottom: 0; margin-top: 5px; color: {score_color}; line-height: 1.1;'>{display_score_val}</h2>", unsafe_allow_html=True)

                        # Display score thrown this turn if applicable
                        turn_total_display = ""
                        if is_current_player and partial_turn_score > 0 and not is_potential_bust:
                            turn_total_display = f"({partial_turn_score} {t('thrown')})" # Add translation if needed
                        # Use a non-breaking space for consistent height when empty
                        st.markdown(f"<p style='text-align: center; font-size: 1.1em; color: blue; margin-bottom: 2px; height: 1.3em;'>{turn_total_display or '&nbsp;'}</p>", unsafe_allow_html=True)

                    with col_stats_checkout:
                         # Display Avg, Legs, Sets
                         darts = st.session_state.player_darts_thrown.get(player, 0)
                         history = st.session_state.player_turn_history.get(player, [])
                         # Calculate total score only from non-busted turns in history
                         total_score_thrown_hist = sum(t[0] for t in history if len(t)>2 and not t[2].startswith("BUST"))
                         avg_3_dart = (total_score_thrown_hist / darts * 3) if darts > 0 else 0.00
                         legs = st.session_state.player_legs_won.get(player, 0)
                         sets = st.session_state.player_sets_won.get(player, 0)
                         st.markdown(f"""
                             <div style='text-align: left; font-size: 1.2em; padding-top: 5px;'>
                                 📊{t('avg_short')}: {avg_3_dart:.2f}<br>
                                 🦵{t('legs_short')}: {legs} | 🏆{t('sets_short')}: {sets}
                             </div>
                             """, unsafe_allow_html=True)

                         # Display Last Turn's Score
                         last_shots = st.session_state.player_last_turn_scores.get(player, [])
                         last_turn_str = " ".join(map(str, last_shots)) if last_shots else "-"
                         last_turn_total, _, _, _ = calculate_turn_total(last_shots) if last_shots else (0,0,False, [])
                         last_turn_total_val = last_turn_total if last_turn_total is not None else 0
                         st.markdown(f"<p style='text-align: left; font-size: 0.8em; color: grey; margin-bottom: 2px;'>{t('last_turn_short')}: {last_turn_str} ({last_turn_total_val})</p>", unsafe_allow_html=True)


                         # --- Checkout / Setup Suggestions ---
                         suggestion_html = ""
                         if is_current_player and st.session_state.check_out_mode == "Double Out":
                             score_at_turn_start_disp = st.session_state.player_scores.get(player, st.session_state.starting_score)
                             current_turn_shots_list_disp = st.session_state.current_turn_shots
                             score_thrown_this_turn_disp, darts_thrown_this_turn_disp, _, _ = calculate_turn_total(current_turn_shots_list_disp)

                             # Ensure calculation was successful before proceeding
                             if score_thrown_this_turn_disp is not None:
                                 score_remaining_now_disp = score_at_turn_start_disp - score_thrown_this_turn_disp
                                 darts_left_disp = 3 - darts_thrown_this_turn_disp

                                 # Only show suggestions if darts remain and score is possible to finish
                                 if darts_left_disp > 0 and score_remaining_now_disp >= 2:
                                     found_suggestion = False
                                     # 1. Check for 1-Dart Finish
                                     if darts_left_disp >= 1 and score_remaining_now_disp <= 50 and score_remaining_now_disp not in BOGIE_NUMBERS_SET:
                                         checkouts_1 = get_checkouts(score_remaining_now_disp, 1)
                                         if checkouts_1:
                                             suggestion_html = f"<p style='font-size: 0.9em; color: #006400; font-weight: bold; margin: 5px 0 0 0;'>{t('out_suggestion')} {checkouts_1[0][0]} {t('one_dart_suffix')}</p>"
                                             found_suggestion = True

                                     # 2. Check for 2-Dart Finish
                                     if not found_suggestion and darts_left_disp >= 2 and score_remaining_now_disp <= 110 and score_remaining_now_disp not in BOGIE_NUMBERS_SET:
                                         checkouts_2 = get_checkouts(score_remaining_now_disp, 2)
                                         if checkouts_2:
                                             current_username_sugg = st.session_state.username
                                             player_prefs_list = users.get(current_username_sugg, {}).get("player_stats", {}).get(player, {}).get('preferred_doubles', [])
                                             preferred_doubles_set = set(player_prefs_list) if player_prefs_list else DEFAULT_PREFERRED_DOUBLES
                                             sorted_suggestions = sort_checkouts_by_preference(checkouts_2, preferred_doubles_set)
                                             display_text = " | ".join([" → ".join(path) for path in sorted_suggestions[:2]]) # Show top 2, use arrow
                                             suggestion_html = f"<p style='font-size: 0.9em; color: green; margin: 5px 0 0 0;'>{t('out_suggestion')} {display_text} {t('two_dart_suffix')}</p>"
                                             found_suggestion = True

                                     # 3. Check for 3-Dart Finish
                                     if not found_suggestion and darts_left_disp == 3 and score_remaining_now_disp <= 170 and score_remaining_now_disp not in BOGIE_NUMBERS_SET:
                                         checkouts_3 = get_checkouts(score_remaining_now_disp, 3)
                                         if checkouts_3:
                                             current_username_sugg = st.session_state.username
                                             player_prefs_list = users.get(current_username_sugg, {}).get("player_stats", {}).get(player, {}).get('preferred_doubles', [])
                                             preferred_doubles_set = set(player_prefs_list) if player_prefs_list else DEFAULT_PREFERRED_DOUBLES
                                             sorted_suggestions = sort_checkouts_by_preference(checkouts_3, preferred_doubles_set)
                                             display_text = " | ".join([" → ".join(path) for path in sorted_suggestions[:2]]) # Show top 2, use arrow
                                             suggestion_html = f"<p style='font-size: 0.9em; color: darkgreen; margin: 5px 0 0 0;'>{t('out_suggestion')} {display_text} {t('three_dart_suffix')}</p>"
                                             found_suggestion = True

                                     # --- MODIFIED: Only suggest setup if score <= 170 ---
                                     # 4. Suggest Setup Shot (Only if score is <= 170 and no finish found)
                                     if not found_suggestion and darts_left_disp == 1 and 1 < score_remaining_now_disp <= 170 and score_remaining_now_disp not in BOGIE_NUMBERS_SET:
                                         setup_suggestion = get_setup_shot(score_remaining_now_disp)
                                         if setup_suggestion:
                                             suggestion_html = f"<p style='font-size: 0.9em; color: orange; margin: 5px 0 0 0;'>{t('setup_suggestion')} {setup_suggestion}</p>"
                                             found_suggestion = True

                                     # 5. Handle Bogie Numbers
                                     if not found_suggestion and score_remaining_now_disp in BOGIE_NUMBERS_SET:
                                          suggestion_html = f"<p style='font-size: 0.8em; color: red; margin: 5px 0 0 0;'>{t('no_checkout_bogie')}</p>"
                                          found_suggestion = True

                         # Display the suggestion HTML or a placeholder for alignment
                         st.markdown(suggestion_html or "<p style='height: 1.5em; margin: 5px 0 0 0;'></p>", unsafe_allow_html=True) # Placeholder keeps space


                    st.markdown("</div>", unsafe_allow_html=True) # Close player container div

        else:
            st.warning(t("no_players_in_game_warning")) # Should not happen if check at start works


    with right_col:
        # --- Input Area ---
        if not st.session_state.game_over:
            current_player_name_input = "N/A"
            # Ensure players list and index are valid
            if st.session_state.players_selected_for_game and len(st.session_state.players_selected_for_game) > 0:
                 current_player_index_input_safe = st.session_state.current_player_index % len(st.session_state.players_selected_for_game)
                 current_player_name_input = st.session_state.players_selected_for_game[current_player_index_input_safe]

            st.markdown(f"**{t('enter_score_for')} {current_player_name_input}**")

            # Display current shots entered for the turn
            modifier_indicator = ""
            if st.session_state.pending_modifier == "D":
                 modifier_indicator = f" {t('double_indicator')}"
            elif st.session_state.pending_modifier == "T":
                 modifier_indicator = f" {t('triple_indicator')}"
            st.markdown(f"**{t('input_indicator')}** `{ ' | '.join(st.session_state.current_turn_shots) }`{modifier_indicator}")

            num_darts_entered = len(st.session_state.current_turn_shots)
            st.caption(f"{t('dart')} {num_darts_entered + 1} / 3")
            input_disabled = num_darts_entered >= 3 # Disable input after 3 darts

            # --- Input Buttons ---
            # Style for more compact buttons
            compact_button_style = """
                <style>
                    div[data-testid*="stButton"] > button {
                        margin: 2px 2px !important; /* More space than before */
                        padding: 2px 4px !important; /* Minimal padding */
                        height: 42px !important; /* Taller */
                        font-size: 1em !important; /* Slightly larger font */
                        min-width: 40px !important; /* Ensure minimum width */
                        border-radius: 5px !important; /* Softer edges */
                    }
                </style>
            """
            st.markdown(compact_button_style, unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True) # Space before actions
            # Action Buttons (Double, Triple, Back, Undo)
            cols_action = st.columns(4)
            double_btn_type = "primary" if st.session_state.pending_modifier == "D" else "secondary"
            if cols_action[0].button(f"D", key="pad_btn_D", help=t('set_double'), use_container_width=True, type=double_btn_type, disabled=input_disabled):
                st.session_state.pending_modifier = None if st.session_state.pending_modifier == "D" else "D"
                st.rerun()
            triple_btn_type = "primary" if st.session_state.pending_modifier == "T" else "secondary"
            if cols_action[1].button(f"T", key="pad_btn_T", help=t('set_triple'), use_container_width=True, type=triple_btn_type, disabled=input_disabled):
                st.session_state.pending_modifier = None if st.session_state.pending_modifier == "T" else "T"
                st.rerun()
            if cols_action[2].button(f"⬅️", key="pad_btn_back", help=t('remove_last'), use_container_width=True): # Simpler Back icon
                if st.session_state.pending_modifier: # Clear modifier first
                    st.session_state.pending_modifier = None
                elif st.session_state.current_turn_shots: # Remove last shot if no modifier pending
                    st.session_state.current_turn_shots.pop()
                st.rerun()
            can_undo = st.session_state.get("state_before_last_turn") is not None # Check if undo state exists
            if cols_action[3].button(f"↩️", key="pad_btn_undo", help=t('undo_last_turn'), use_container_width=True, disabled=not can_undo): # Simpler Undo icon
                if st.session_state.state_before_last_turn:
                    state = st.session_state.state_before_last_turn
                    undo_player_name = state["player_name"]
                    undo_player_index = state["player_index"]

                    # Restore state values from the saved dictionary
                    st.session_state.current_player_index = undo_player_index
                    st.session_state.player_scores[undo_player_name] = state["score_before"]
                    st.session_state.player_darts_thrown[undo_player_name] = state["darts_thrown_player_before"]
                    st.session_state.player_legs_won[undo_player_name] = state["legs_won_before"]
                    st.session_state.player_sets_won[undo_player_name] = state["sets_won_before"]
                    st.session_state.current_leg = state["current_leg_before"]
                    st.session_state.current_set = state["current_set_before"]

                    # Simple history removal (remove last entry for the player)
                    if st.session_state.player_turn_history.get(undo_player_name):
                         st.session_state.player_turn_history[undo_player_name].pop()

                    # Restore input buffer to what was processed
                    st.session_state.current_turn_shots = state["current_turn_shots_processed"]

                    # Clear flags and displays that might be incorrect after undo
                    st.session_state.player_last_turn_scores[undo_player_name] = [] # Clear 'last turn' display
                    st.session_state.leg_over = False
                    st.session_state.set_over = False
                    st.session_state.game_over = False
                    st.session_state.winner = None
                    st.session_state.pending_modifier = None # Clear any pending D/T
                    st.session_state.message = t("toast_undid_turn") # Provide feedback

                    st.session_state.state_before_last_turn = None # Consume undo state - can only undo once per turn
                    st.rerun()
                else:
                    st.warning(t("toast_nothing_to_undo")) # Should be disabled, but good fallback

            st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True) # Space before number pad

            # Number Pad (Keypad)
            keypad_numbers = list(range(1, 21)) + [25, 0] # Standard dart numbers + Bull + Miss
            num_cols = 4 # Arrange in 4 columns
            rows_of_numbers = [keypad_numbers[i:i + num_cols] for i in range(0, len(keypad_numbers), num_cols)]

            for row in rows_of_numbers:
                cols = st.columns(num_cols)
                for i, num_val in enumerate(row):
                    if i < len(cols): # Ensure we don't try to access non-existent column
                        num_str = str(num_val)
                        is_miss_button = (num_val == 0)
                        button_text = t('miss') if is_miss_button else num_str
                        # Use unique key for each button based on its value
                        if cols[i].button(button_text, key=f"pad_btn_num_{num_val}", use_container_width=True, disabled=input_disabled):
                            # Process number press only if less than 3 darts thrown
                            if len(st.session_state.current_turn_shots) < 3:
                                modifier = st.session_state.pending_modifier
                                final_shot_str = num_str
                                valid_combination = True

                                # Apply modifier if active and valid for the number
                                if modifier == "T":
                                    if num_val <= 0 or num_val > 20:
                                        st.toast(t("toast_invalid_modifier_T"), icon="⚠️")
                                        valid_combination = False
                                    else: final_shot_str = "T" + num_str
                                elif modifier == "D":
                                    if num_val <= 0 or (num_val > 20 and num_val != 25):
                                        st.toast(t("toast_invalid_modifier_D"), icon="⚠️")
                                        valid_combination = False
                                    else: final_shot_str = "D" + num_str

                                # If the combination is valid, add shot and check turn end
                                if valid_combination:
                                    st.session_state.current_turn_shots.append(final_shot_str)
                                    st.session_state.pending_modifier = None # Clear modifier after use

                                    shots_so_far = st.session_state.current_turn_shots
                                    num_darts_now = len(shots_so_far)

                                    # Get current player name safely for processing
                                    current_player_name_for_calc = "N/A"
                                    if st.session_state.players_selected_for_game:
                                        if len(st.session_state.players_selected_for_game) > 0:
                                            idx_safe = st.session_state.current_player_index % len(st.session_state.players_selected_for_game)
                                            current_player_name_for_calc = st.session_state.players_selected_for_game[idx_safe]

                                    if current_player_name_for_calc != "N/A":
                                        # Check potential score *after* this dart
                                        current_score_value, _, _, _ = calculate_turn_total(shots_so_far)
                                        if current_score_value is not None:
                                            potential_score_after_turn = st.session_state.player_scores.get(current_player_name_for_calc, 0) - current_score_value
                                            is_potential_win = (potential_score_after_turn == 0)
                                            # Check if *this specific dart* is a valid finishing double if needed
                                            _, last_dart_double_flag_check, _, is_valid_parse = parse_score_input(final_shot_str)
                                            is_valid_checkout_dart = True # Assume valid for Straight Out
                                            if st.session_state.check_out_mode == "Double Out" and is_potential_win:
                                                 is_valid_checkout_dart = last_dart_double_flag_check

                                            # Process the turn if 3 darts thrown OR it's a valid win
                                            if num_darts_now == 3 or (is_potential_win and is_valid_checkout_dart):
                                                 run_turn_processing(current_player_name_for_calc, shots_so_far)
                                                 # run_turn_processing handles rerun internally
                                            else:
                                                 st.rerun() # Rerun to update display after each valid dart
                                        # else: Handle potential score calculation error (shouldn't happen with parse check)
                                    # else: Handle error if current player name unknown (shouldn't happen)
            st.markdown("---") # Separator at end of input area

        else: # If game is over (should be caught earlier, but safe fallback)
            st.info(t('game_over_start_new'))

        # Display toast messages if any
        if st.session_state.message:
            # Use st.toast for non-blocking feedback
            st.toast(st.session_state.message)
            st.session_state.message = "" # Clear message after displaying

# --- Fallback for Unknown Page State (if logged in but page invalid) ---
elif st.session_state.logged_in:
     st.warning(t('invalid_page_state'))
     st.info("Redirecting to Homepage...")
     st.session_state.current_page = page_map.get("Homepage", "homepage")
     st.session_state.nav_target = reverse_page_map.get("homepage", "Homepage")
     time.sleep(1)
     st.rerun()

# --- Final Check (If somehow reached end without being logged in or rendering a page) ---
# This shouldn't normally happen due to the login check at the start.
# else:
#     st.error("Application error: Invalid state.")