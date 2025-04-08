import streamlit as st

# Set page title
st.title("🎯 Darts Score Counter (501 Game)")

# Explanation
with st.expander("📘 How to Play"):
    st.markdown("""
    - Start with **501 points**.
    - Enter the **total score of your 3 darts** each turn.
    - You **must finish on a double** to win.
    - Going **below 0** or ending on **1** is a **bust**, and your score resets to the start of that turn.
    """)

# Initialize session state
if "score" not in st.session_state:
    st.session_state.score = 501
if "start_of_turn" not in st.session_state:
    st.session_state.start_of_turn = 501
if "history" not in st.session_state:
    st.session_state.history = []

# Display current score
st.subheader(f"Current Score: {st.session_state.score}")

# Input for current turn
score_input = st.number_input("Enter total score for this turn (0–180):", min_value=0, max_value=180, step=1)

# Submit button
if st.button("Submit Turn"):
    start = st.session_state.score
    new_score = start - score_input

    # Check for bust conditions
    if new_score < 0 or new_score == 1:
        st.warning("❌ Bust! Score resets to start of this turn.")
        st.session_state.score = st.session_state.start_of_turn
    elif new_score == 0:
        st.success("🎉 You win! Finished on a double (assumed).")
        st.session_state.history.append((score_input, "WIN"))
        st.session_state.score = 501
        st.session_state.start_of_turn = 501
    else:
        st.session_state.score = new_score
        st.session_state.start_of_turn = new_score
        st.session_state.history.append((score_input, new_score))

# Show history
with st.expander("📜 Turn History"):
    for i, (scored, result) in enumerate(st.session_state.history[::-1], 1):
        st.write(f"Turn {len(st.session_state.history)-i+1}: -{scored} → {result}")

# Reset button
if st.button("🔄 Reset Game"):
    st.session_state.score = 501
    st.session_state.start_of_turn = 501
    st.session_state.history = []
    st.success("Game reset!")

