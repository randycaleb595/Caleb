import os
import io
import json
import base64
from datetime import datetime
GEMINI_API_KEY="AQ.Ab8RN6IVERIhwv9TrfZkfuS5R2pmQaI7aNYNkJ3hSEU5Ki_Dkw"
import streamlit as st
import gemini.google as genai
from gtts import gTTS

# ---------------------------------------------------------------- config
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
TEXT_MODEL = "gemini-1.5-flash"
AUDIO_MODEL = "gemini-1.5-pro"  # accepts audio input

SOURCES = ["Auto-detect", "English", "French", "Spanish", "Portuguese", "Chinese", "Arabic"]
TARGET = "German"

# ---------------------------------------------------------------- theme
st.set_page_config(page_title="Deutschefy", page_icon="🇩🇪", layout="centered")

st.markdown(
    """
    <style>
      html, body, [class*="css"] { background:#0A1614; }
      .stApp { background:#0A1614; color:#E8F0EE; }
      .dfy-header {
        text-align:center; padding:.4rem 0 1.1rem;
        font-size:1.55rem; font-weight:800; letter-spacing:.32em;
        color:#F0A93D;
      }
      .dfy-bubble-user {
        background:#13252A; border:1px solid #1f3a3f; border-radius:14px 14px 4px 14px;
        padding:.7rem .9rem; margin:.35rem 0; color:#E8F0EE;
      }
      .dfy-bubble-de {
        background:#16261f; border-left:3px solid #F0A93D; border-radius:12px;
        padding:.7rem .9rem; margin:.35rem 0; color:#F4E7D2; font-size:1.05rem; line-height:1.55;
      }
      .dfy-label { color:#9fb4ad; font-size:.72rem; letter-spacing:.18em; text-transform:uppercase; }
      .dfy-divider { border:0; border-top:1px solid #1f3a3f; margin:.6rem 0; }
      .stTextArea textarea, .stSelectbox div { background:#13252A !important; color:#E8F0EE !important; border-color:#26514f !important; }
      .stButton>button { background:#13252A; color:#F0A93D; border:1px solid #2a4a4f; border-radius:10px; font-weight:600; }
      .stButton>button:hover { background:#1c3a3f; color:#fff; border-color:#F0A93D; }
      .stExpander { background:#10202a; border:1px solid #1f3a3f; border-radius:12px; }
      .stExpander header { color:#F0A93D; font-weight:600; }
      .stRadio label, .stMarkdown, .stText { color:#D8E6E1 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- helpers
def call_gemini(prompt, model=TEXT_MODEL, json_mode=False):
    gen_cfg = {"response_mime_type": "application/json"} if json_mode else None
    resp = genai.GenerativeModel(model).generate_content(
        prompt, generation_config=gen_cfg
    )
    return resp.text


def translate_text(text, src):
    src_clause = "Detect the source language automatically." if src == "Auto-detect" else f"Source language: {src}."
    prompt = (
        f"{src_clause} Translate the following text into {TARGET}. "
        "Return ONLY the {TARGET} translation, no notes, no romanization, no extra text.\n\n"
        f"Text: {text}"
    ).replace("{TARGET}", TARGET)
    return call_gemini(prompt).strip()


def explain_translation(text, translation, src):
    explain_lang = "the source language" if src != "Auto-detect" else "the original language of the input"
    prompt = (
        f"A learner asked to translate this text into {TARGET}:\n"
        f"Original: {text}\n{TARGET} translation: {translation}\n\n"
        f"Write a concise, friendly explanation in {explain_lang} of WHY this {TARGET} translation "
        "works — cover key grammar, word order, articles/cases, and any idioms. "
        "Use Markdown with short headings and bullet points. Keep it under 220 words."
    )
    return call_gemini(prompt).strip()


def generate_quiz(text, translation, src):
    explain_lang = "the source language" if src != "Auto-detect" else "the original language of the input"
    prompt = (
        f"Original: {text}\n{TARGET} translation: {translation}\n"
        f"Create 4 multiple-choice questions in {explain_lang} that test the grammar and vocabulary "
        f"used in this {TARGET} translation. Each question has exactly 4 options. "
        "Return JSON: a list of objects {question, options:[4 strings], correct:0-3}. "
        "No extra commentary."
    )
    raw = call_gemini(prompt, json_mode=True)
    try:
        return json.loads(raw)
    except Exception:
        # fall back: strip code fences if present
        cleaned = raw.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        return json.loads(cleaned)


def transcribe_audio(audio_bytes, mime):
    part = {"mime_type": mime, "data": audio_bytes}
    resp = genai.GenerativeModel(AUDIO_MODEL).generate_content(
        [part, "Transcribe this audio accurately. Output only the transcript, no commentary."]
    )
    return resp.text.strip()


def speak_german(text):
    buf = io.BytesIO()
    gTTS(text, lang="de").write_to_fp(buf)
    return buf.getvalue()

# ---------------------------------------------------------------- state
if "messages" not in st.session_state:
    st.session_state.messages = []  # each: {query, src, translation, audio_url, explanation, quiz, quiz_answers}

# ---------------------------------------------------------------- header
st.markdown('<div class="dfy-header">DEUTSCHEFY</div>', unsafe_allow_html=True)

# source language selector (no subtitle text)
src = st.selectbox("Source language", SOURCES, index=0, label_visibility="collapsed")

# input row: text + audio record + file upload
col_text, col_audio = st.columns([4, 1])
with col_text:
    user_text = st.text_area("Text", height=72, label_visibility="collapsed",
                             placeholder="Type here, or record / upload audio below…")
with col_audio:
    recorded = st.audio_input("Record")

uploaded = st.file_uploader("Or upload audio", type=["mp3", "wav", "m4a", "ogg", "webm"], label_visibility="collapsed")

submit = st.button("Translate")

# ---------------------------------------------------------------- submit
def add_message(query, src_lang):
    translation = translate_text(query, src_lang)
    st.session_state.messages.append({
        "query": query,
        "src": src_lang,
        "translation": translation,
        "explanation": None,
        "quiz": None,
        "quiz_answers": {},
    })

if submit:
    text_to_send = user_text.strip()
    if not text_to_send and (recorded or uploaded):
        with st.spinner("Transcribing audio…"):
            if recorded:
                text_to_send = transcribe_audio(recorded.getvalue(), recorded.type)
            elif uploaded:
                text_to_send = transcribe_audio(uploaded.getvalue(), uploaded.type)
    if text_to_send:
        with st.spinner("Translating…"):
            add_message(text_to_send, src)
        st.rerun() if hasattr(st, "rerun") else None

# ---------------------------------------------------------------- feed
for i, m in enumerate(st.session_state.messages):
    st.markdown('<div class="dfy-label">You</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="dfy-bubble-user">{m["query"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="dfy-label">{TARGET}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="dfy-bubble-de">{m["translation"]}</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔊 Listen", key=f"listen-{i}"):
            st.audio(speak_german(m["translation"]), format="audio/mp3")
    with c2:
        if st.button("💡 Why?", key=f"why-{i}"):
            m["explanation"] = m["explanation"] or explain_translation(m["query"], m["translation"], m["src"])
    with c3:
        if st.button("✅ Test me", key=f"quiz-{i}"):
            m["quiz"] = m["quiz"] or generate_quiz(m["query"], m["translation"], m["src"])

    if m["explanation"]:
        with st.expander("Why this translation?", expanded=True):
            st.markdown(m["explanation"])

    if m["quiz"]:
        with st.expander("Practice test", expanded=True):
            for q_idx, q in enumerate(m["quiz"][:4]):
                st.markdown(f"**Q{q_idx+1}. {q.get('question')}**")
                opts = q.get("options", [])
                correct = q.get("correct", 0)
                chosen = st.radio(f"options-{i}-{q_idx}", opts, index=None, label_visibility="collapsed", key=f"radio-{i}-{q_idx}")
                if chosen is not None:
                    if opts.index(chosen) == correct:
                        st.success("Correct ✅")
                    else:
                        st.error(f"Not quite — answer: {opts[correct]}")
            if st.button("Close test", key=f"close-{i}"):
                m["quiz"] = None
                st.rerun() if hasattr(st, "rerun") else None

    st.markdown('<hr class="dfy-divider">', unsafe_allow_html=True)
