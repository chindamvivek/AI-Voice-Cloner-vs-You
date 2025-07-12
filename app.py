import streamlit as st
import os
from utils import synthesize_text, record_to_text, record_from_mic, save_score, get_leaderboard, clear_leaderboard
import random
from pathlib import Path

# Create temp directory
Path("temp_audio").mkdir(exist_ok=True)

# Set up Streamlit
st.set_page_config(page_title="🎙️ AI Voice Cloner vs You", layout="centered")
st.title("🎙️ AI Voice Cloner vs You")

st.markdown("Speak or upload your voice. Can AI mimic you so well that you can't tell?")

# Session state init
for key in ['real_path', 'ai_path', 'transcribed_text', 'guess_ready', 'guess_submitted',
            'correct_count', 'total_rounds', 'options', 'voices', 'last_uploaded_file']:
    if key not in st.session_state:
        st.session_state[key] = None if key not in ['correct_count', 'total_rounds'] else 0

# Input method
method = st.radio("Choose input method:", ["🎤 Record with Mic", "📁 Upload WAV File"])

# -------- 1. Handle Audio Input --------
if method == "📁 Upload WAV File":
    uploaded_file = st.file_uploader("Upload your voice sample (WAV)", type=["wav"], key="file_uploader")
    if uploaded_file and st.session_state.get("last_uploaded_file") != uploaded_file.name:
        st.session_state.real_path = "temp_audio/real.wav"
        with open(st.session_state.real_path, "wb") as f:
            f.write(uploaded_file.read())

        # 🔄 Reset game state ONLY on new file
        for key in ['options', 'voices', 'guess_submitted', 'guess_ready']:
            st.session_state[key] = None if key != 'guess_submitted' else False

        st.session_state.last_uploaded_file = uploaded_file.name

elif method == "🎤 Record with Mic":
    if st.button("🎙️ Start Recording"):
        st.session_state.real_path = record_from_mic()
        st.success("🎤 Recording done!")

        # 🔄 Reset game state
        for key in ['options', 'voices', 'guess_submitted', 'guess_ready']:
            st.session_state[key] = None if key != 'guess_submitted' else False

# -------- 2. Transcribe and Synthesize --------
if st.session_state.real_path and not st.session_state.guess_submitted and not st.session_state.guess_ready:
    st.audio(st.session_state.real_path, format="audio/wav")

    st.session_state.transcribed_text = record_to_text(st.session_state.real_path)
    st.write(f"📝 Transcribed: '{st.session_state.transcribed_text}'")

    if not st.session_state.transcribed_text.strip() or len(st.session_state.transcribed_text.strip()) < 3:
        st.error("❗ No valid speech detected. Please try again with a clearer or longer recording.")
    else:
        try:
            st.session_state.ai_path = "temp_audio/ai.wav"
            synthesize_text(st.session_state.transcribed_text, st.session_state.ai_path)
            st.session_state.guess_ready = True
        except RuntimeError as e:
            st.error(str(e))
            st.session_state.guess_ready = False

# -------- 3. Play Game and Guess --------
if st.session_state.guess_ready:

    # ✅ Shuffle once and store in session state
    if not st.session_state.options:
        st.session_state.options = ["A", "B"]
        random.shuffle(st.session_state.options)
        st.session_state.voices = {
            st.session_state.options[0]: st.session_state.real_path,
            st.session_state.options[1]: st.session_state.ai_path
        }

    st.subheader("🔊 Listen and Guess")
    for label in st.session_state.options:
        st.audio(st.session_state.voices[label], format="audio/wav")
        st.markdown(f"Voice {label}")

    guess = st.radio("🤔 Which is your real voice?", st.session_state.options, key="guess_choice")
    user_name = st.text_input("Enter your name to save score", key="name_input")

    if st.button("🔍 Submit Guess", disabled=st.session_state.guess_submitted):
        correct_label = [k for k, v in st.session_state.voices.items() if v == st.session_state.real_path][0]
        is_correct = guess == correct_label
        st.session_state.total_rounds += 1

        if is_correct:
            st.session_state.correct_count += 1
            st.success(f"✅ Correct! {guess} was your real voice.")
        else:
            st.error(f"❌ Wrong! {guess} was AI. Your real voice was {correct_label}.")

        st.session_state.guess_submitted = True

        if user_name.strip():
            save_score(user_name.strip(), st.session_state.correct_count, st.session_state.total_rounds)
            st.success("✅ Score saved to leaderboard!")

# -------- 4. Show Current Score --------
if st.session_state.total_rounds > 0:
    st.markdown(f"### 🎯 Your Score: **{st.session_state.correct_count} / {st.session_state.total_rounds}**")

# -------- 5. Leaderboard and Admin --------
st.markdown("---")
st.subheader("🏆 Leaderboard")

leaderboard = get_leaderboard()
if leaderboard:
    for entry in leaderboard[::-1]:  # Latest first
        st.write(f"👤 {entry['name']} — {entry['correct']}/{entry['total']} correct")
else:
    st.info("No scores yet. Be the first!")

# -------- 6. Admin: Clear and Browse Leaderboard --------
st.markdown("---")
st.subheader("🛠 Admin Tools")

col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ Clear Leaderboard"):
        clear_leaderboard()
        st.success("Leaderboard cleared.")

with col2:
    with st.expander("📂 View Raw Leaderboard File"):
        if leaderboard:
            st.json(leaderboard)
        else:
            st.info("No data in leaderboard yet.")
