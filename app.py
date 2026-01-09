import streamlit as st
import csv
import random
import os
import datetime
import io
import pathlib

# ==================================================
# Utilities
# ==================================================
def read_csv(path_or_file):
    if hasattr(path_or_file, "read"):
        content = path_or_file.getvalue().decode("utf-8-sig")
        return list(csv.reader(io.StringIO(content)))
    else:
        with open(path_or_file, encoding="utf-8-sig") as f:
            return list(csv.reader(f))

def append_csv(path, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, encoding="utf-8-sig", mode="a", newline="") as f:
        csv.writer(f).writerow(row)

def now_str():
    return datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')

def highlight_entry(idx, entry):
    output = []
    for i, word in enumerate(entry):
        if i == idx:
            output.append(f"<b><u>{word}</u></b>")
        else:
            output.append(word)
    return " ".join(output)

# ==================================================
# Session state (只建壳，不填内容)
# ==================================================
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.questions = []
    st.session_state.current_idx = 0
    st.session_state.mistakes = []
    st.session_state.mistake_file = ""
    st.session_state.mode = ""
    st.session_state.show_answer = -1

# ==================================================
# Sidebar: CSV Selection
# ==================================================
st.sidebar.title("CSV Selection")
repo_dir = pathlib.Path(__file__).parent
csv_choice = st.sidebar.radio(
    "Choose CSV source",
    ["Use Vocabulary CSV", "Use Verb CSV", "Upload My Own CSV"]
)

uploaded_file = None
if csv_choice == "Upload My Own CSV":
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type="csv")

# ==================================================
# Sidebar: Training Settings
# ==================================================
st.sidebar.title("Training Settings")
mode_choice = st.sidebar.radio("Training type", ["Vocabulary", "Verb Conjugation"])
extreme = st.sidebar.checkbox("Extreme mode", value=True)
record_mistake = st.sidebar.checkbox("Record mistakes", value=False)
auto_review = st.sidebar.checkbox("Automatically review mistakes", value=True)
font_size = st.sidebar.slider("Font size", 30, 100, 60)
shuffle_questions = st.sidebar.checkbox("Shuffle questions", value=True)
num_questions = st.sidebar.number_input(
    "Number of questions to use (0 = all)", min_value=0, value=0, step=1
)

# ==================================================
# Start Training 按钮
# ==================================================
if not st.session_state.initialized:
    st.markdown("### Ready when you are.")
    start = st.button("▶ Start Training")

    if start:
        # --------- CSV 选择 ---------
        if csv_choice == "Upload My Own CSV":
            if uploaded_file is None:
                st.error("Please upload a CSV file first.")
                st.stop()
            data = read_csv(uploaded_file)
        else:
            default_csv_map = {
                "Use Vocabulary CSV": repo_dir / "data/greek_vocabulary_edited.csv",
                "Use Verb CSV": repo_dir / "data/greek_verb_form_edited.csv"
            }
            chosen_csv_path = default_csv_map[csv_choice]
            if not chosen_csv_path.exists():
                st.error(f"Default CSV not found: {chosen_csv_path}")
                st.stop()
            data = read_csv(str(chosen_csv_path))

        # --------- 根据训练模式初始化 questions ---------
        if mode_choice == "Vocabulary":
            st.session_state.mode = "vocab"
            questions = data.copy()
            if shuffle_questions:
                random.shuffle(questions)
            if num_questions > 0:
                questions = questions[:num_questions]
            st.session_state.questions = questions
            folder = "training_results"
        else:
            questions = []
            conj_indices = range(1, 7)
            for entry in data:
                valid_forms = [i for i in conj_indices if entry[i] != "—"]
                for i in valid_forms:
                    questions.append((i, entry))
            if shuffle_questions:
                random.shuffle(questions)
            if num_questions > 0:
                questions = questions[:num_questions]
            st.session_state.questions = questions
            st.session_state.mode = "verb"
            folder = "training_results_verb"

        os.makedirs(folder, exist_ok=True)
        st.session_state.mistake_file = f"{folder}/{now_str()}_mistakes.csv"
        st.session_state.current_idx = 0
        st.session_state.mistakes = []
        st.session_state.show_answer = -1
        st.session_state.initialized = True

        st.rerun()

    st.stop()

# ==================================================
# Main Trainer Display
# ==================================================
q_idx = st.session_state.current_idx

if q_idx >= len(st.session_state.questions):
    if auto_review and st.session_state.mistakes:
        st.info("Reviewing mistakes...")
        st.session_state.questions = st.session_state.mistakes.copy()
        st.session_state.current_idx = 0
        st.session_state.mistakes = []
        st.session_state.show_answer = -1
        st.rerun()
    else:
        st.success("Training session completed!")
        if record_mistake:
            st.write(f"Mistakes saved to: {st.session_state.mistake_file}")
        st.stop()

# ----------------------
# Vocabulary Mode
# ----------------------
if st.session_state.mode == "vocab":
    entry = st.session_state.questions[q_idx]
    question = entry[0].split(",")[0] if extreme else entry[0]

    st.markdown(
        f"<div style='font-size:{font_size}px; line-height:1.3;'>"
        f"{q_idx+1}/{len(st.session_state.questions)} — Q: {question}"
        f"</div>",
        unsafe_allow_html=True
    )

    if st.session_state.show_answer == q_idx:
        st.markdown(
            f"<div style='font-size:{font_size}px;'>"
            f"A: {entry[2]}"
            f"</div>",
            unsafe_allow_html=True
        )

# ----------------------
# Verb Mode
# ----------------------
else:
    idx, entry = st.session_state.questions[q_idx]
    st.markdown(
        f"<div style='font-size:{font_size}px; line-height:1.3;'>"
        f"{q_idx+1}/{len(st.session_state.questions)} — Form: {entry[idx]}"
        f"</div>",
        unsafe_allow_html=True
    )

    if st.session_state.show_answer == q_idx:
        st.markdown(
            f"<div style='font-size:{font_size}px;'>"
            f"{highlight_entry(idx, entry)}"
            f"</div>",
            unsafe_allow_html=True
        )

# ==================================================
# Bottom Buttons
# ==================================================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("✅ Correct"):
        st.session_state.current_idx += 1
        st.session_state.show_answer = -1
        st.rerun()

with col2:
    if st.button("❌ Wrong"):
        item = st.session_state.questions[q_idx]
        if record_mistake:
            append_csv(st.session_state.mistake_file, item)
        st.session_state.mistakes.append(item)
        st.session_state.current_idx += 1
        st.session_state.show_answer = -1
        st.rerun()

with col3:
    if st.button("🔍 Show Full Entry"):
        st.session_state.show_answer = q_idx
        st.rerun()

