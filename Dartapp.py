import streamlit as st
import matplotlib.pyplot as plt
import json
import os

st.set_page_config(page_title="Darts Counter", page_icon="🎯")

# User authentication
USER_DATA_FILE = "user_data.json"

def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

users = load_users()

st.title("🔐 Login to Darts Counter")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    login_tab, register_tab = st.tabs(["Login", "Register"])
    with login_tab:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in users and users[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome back, {username}!")
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
                users[new_username] = {"password": new_password, "games": []}
                save_users(users)
                st.success("Registration successful! Please log in.")

if not st.session_state.logged_in:
    st.stop()

st.title("🎯 Darts Score Counter")

# Game mode selector
game_mode = st.selectbox("Choose Game Mode:", [301, 501])

# Session state setup
if "starting_score" not in st.session_state or st.session_state.starting_score != game_mode:
    st.session_state.starting_score = game_mode
    st.session_state.score = game_mode
    st.session_state.start_of_turn = game_mode
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
    elif new_score == 0:
        st.success("🎯 Finished! (Assuming correct double out)")
        st.session_state.history.append((score_input, "WIN"))
        st.session_state.score = 0
        users[st.session_state.username]["games"].append(st.session_state.history)
        save_users(users)
    else:
        st.session_state.score = new_score
        st.session_state.start_of_turn = new_score
        st.session_state.history.append((score_input, new_score))

# 2. Now show updated remaining score in big font
st.markdown("---")
st.markdown("<h2 style='text-align: center;'>Remaining Points</h2>", unsafe_allow_html=True)
st.markdown(
    f"<h1 style='text-align: center; font-size: 96px; color:#2e86de'>{st.session_state.score}</h1>", 
    unsafe_allow_html=True
)
st.markdown("---")

# Player Statistics
st.markdown("## 📊 Player Statistics")
total_turns = len(st.session_state.history)
valid_scores = [pts for pts, result in st.session_state.history if isinstance(pts, int)]
total_scored = sum(valid_scores)
avg_score = total_scored / total_turns if total_turns > 0 else 0
highest_score = max(valid_scores) if valid_scores else 0
num_busts = sum(1 for _, result in st.session_state.history if result == "BUST")
num_wins = sum(1 for _, result in st.session_state.history if result == "WIN")
win_rate = (num_wins / total_turns) * 100 if total_turns > 0 else 0

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
    users[st.session_state.username]["games"].append(st.session_state.history)
    save_users(users)

# Turn history
with st.expander("📜 Turn History"):
    for i, (pts, result) in enumerate(st.session_state.history[::-1], 1):
        st.write(f"Turn {len(st.session_state.history)-i+1}: -{pts} → {result}")

# Past Games
with st.expander("🗂 Past Games"):
    for gi, game in enumerate(users[st.session_state.username]["games"][:-1], 1):
        st.write(f"Game {gi}:")
        for ti, (pts, result) in enumerate(game, 1):
            st.write(f"  Turn {ti}: -{pts} → {result}")

# Reset
if st.button("🔄 Reset Game"):
    if st.session_state.history:
        users[st.session_state.username]["games"].append(st.session_state.history)
        save_users(users)
    st.session_state.clear()
    st.rerun()
