import streamlit as st

st.set_page_config(page_title="Darts Counter", page_icon="🎯")

st.title("🎯 Darts Score Counter")

# Game mode selector
game_mode = st.selectbox("Choose Game Mode:", [301, 501])

# Session state setup
if "starting_score" not in st.session_state or st.session_state.starting_score != game_mode:
    st.session_state.starting_score = game_mode
    st.session_state.score = game_mode
    st.session_state.start_of_turn = game_mode
    st.session_state.history = []

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

# Reset
if st.button("🔄 Reset Game"):
    st.session_state.starting_score = game_mode
    st.session_state.score = game_mode
    st.session_state.start_of_turn = game_mode
    st.session_state.history = []
    st.success("Game reset!")
