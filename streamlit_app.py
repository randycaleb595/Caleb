import os
import json
import io
import streamlit as st
import google.generativeai as genai
from gtts import gTTS

# ------------------------------------------------------------
# Config / secrets
# ------------------------------------------------------------
# Set this in your environment:
# export GEMINI_API_KEY="your_key_here"
# or in Streamlit secrets, then read it from st.secrets
# Recommended: use environment variables in production.
# DO NOT hardcode API keys in the source file.

if "GEMINI_API_KEY" not in os.environ:
    st.error("Missing GEMINI_API_KEY. Set it in your environment before running this app.")
    st.stop()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

TEXT_MODEL = "gemini-1.5-flash"
AUDIO_MODEL = "gemini-1.5-pro"  # Works for audio input if supported by your SDK/backend
TARGET = "German"

SOURCES = ["Auto-detect", "English", "French", "Spanish", "Portuguese", "Chinese", "Arabic"]

# ------------------------------------------------------------
# Theme
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def safe_call_gemini(prompt, model=TEXT_MODEL, json_mode=False):
    try:
        generation_config = None
        if json_mode:
            try:
                generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
            except AttributeError:
                generation_config = {"response_mime_type": "application/json"}

        response = genai.GenerativeModel(model).generate_content(
            prompt,
            generation_config=generation_config
        )

        text = getattr(response, "text", None)
        if text is None:
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    parts = []
                    for part in candidate.content.parts:
                        parts.append(getattr(part, "text", ""))
                    text = "".join(parts)
        return (text or "").strip()
    except Exception as e:
        st.warning(f"Gemini request failed: {e}")
        return ""

def translate_text(text, src):
    src_clause = "Detect the source language automatically." if src == "Auto-detect" else f"Source language: {src}."
    prompt = (
        f"{src_clause} Translate the following text into {TARGET}. "
        f"Return ONLY the {TARGET} translation, no notes, no romanization, no extra text.\n\n"
        f"Text: {text}"
    )
    return safe_call_gemini(prompt)

def explain_translation(text, translation, src):
    explain_lang = "the source language" if src != "Auto-detect" else "the original language of the input"
    prompt = (
        f"A learner asked to translate this text into {TARGET}:\n"
        f"Original: {text}\n{TARGET} translation: {translation}\n\n"
        f"Write a concise, friendly explanation in {explain_lang} of WHY this {TARGET} translation "
        "works — cover key grammar, word order, articles/cases, and any idioms. "
        "Use Markdown with short headings and bullet points. Keep it under 220 words."
    )
    return safe_call_gemini(prompt)

def parse_json_list(raw):
    if raw is None:
        return []
    text = str(raw).strip()

    # If the model wrapped the JSON in Markdown fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to extract a JSON array if the model added commentary
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass

    return []

def generate_quiz(text, translation, src):
    explain_lang = "the source language" if src != "Auto-detect" else "the original language of the input"
    prompt = (
        f"Original: {text}\n{TARGET} translation: {translation}\n"
        f"Create 4 multiple-choice questions in {explain_lang} that test the grammar and vocabulary "
        f"used in this {TARGET} translation. Each question has exactly 4 options. "
        "Return JSON: a list of objects {question, options:[4 strings], correct:0-3}. "
        "No extra commentary."
    )

    raw = safe_call_gemini(prompt, json_mode=True)
    data = parse_json_list(raw)
    if isinstance(data, list):
        return data[:4]
    return []

def transcribe_audio(audio_bytes, mime):
    try:
        response = genai.GenerativeModel(AUDIO_MODEL).generate_content(
            [
                {"mime_type": mime, "data": audio_bytes},
                "Transcribe this audio accurately. Output only the transcript, no commentary."
            ]
        )
        text = getattr(response, "text", None)
        if text is None and hasattr(response, "candidates"):
            text = response.candidates[0].content.parts[0].text
        return (text or "").strip()
    except Exception as e:
        st.warning(f"Audio transcription failed: {e}")
        return ""

def speak_german(text):
    buf = io.BytesIO()
    try:
        gTTS(text, lang="de").write_to_fp(buf)
        return buf.getvalue()
    except Exception as e:
        st.warning(f"Text-to-speech failed: {e}")
        return b""

# ------------------------------------------------------------
# State
# ------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.markdown('<div class="dfy-header">DEUTSCHEFY</div>', unsafe_allow_html=True)

# source selector
src = st.selectbox("Source language", SOURCES, index=0, label_visibility="collapsed")

# input area
col_text, col_audio = st.columns([4, 1])
with col_text:
    user_text = st.text_area(
        "Text",
        height=72,
        label_visibility="collapsed",
        placeholder="Type here, or record / upload audio below…"
    )
with col_audio:
    recorded = st.audio_input("Record")

uploaded = st.file_uploader(
    "Or upload audio",
    type=["mp3", "wav", "m4a", "ogg", "webm"],
    label_visibility="collapsed"
)

submit = st.button("Translate")

# ------------------------------------------------------------
# Submit handler
# ------------------------------------------------------------
def add_message(query, src_lang):
    translation = translate_text(query, src_lang)
    if not translation:
        st.warning("Translation failed. Please try again or check your API key/model access.")
        return

    st.session_state.messages.append({
        "query": query,
        "src": src_lang,
        "translation": translation,
        "explanation": None,
        "quiz": None,
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

# ------------------------------------------------------------
# Feed
# ------------------------------------------------------------
for i, m in enumerate(st.session_state.messages):
    st.markdown('<div class="dfy-label">You</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="dfy-bubble-user">{m["query"]}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="dfy-label">{TARGET}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="dfy-bubble-de">{m["translation"]}</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🔊 Listen", key=f"listen-{i}"):
            audio_bytes = speak_german(m["translation"])
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")

    with c2:
        if st.button("💡 Why?", key=f"why-{i}"):
            if not m["explanation"]:
                m["explanation"] = explain_translation(m["query"], m["translation"], m["src"])

    with c3:
        if st.button("✅ Test me", key=f"quiz-{i}"):
            if not m["quiz"]:
                m["quiz"] = generate_quiz(m["query"], m["translation"], m["src"])

    if m.get("explanation"):
        with st.expander("Why this translation?", expanded=True):
            st.markdown(m["explanation"])

    if m.get("quiz"):
        with st.expander("Practice test", expanded=True):
            for q_idx, q in enumerate(m["quiz"][:4]):
                st.markdown(f"**Q{q_idx+1}. {q.get('question', '')}**")
                opts = q.get("options", [])
                correct = q.get("correct", 0)

                chosen = st.radio(
                    f"options-{i}-{q_idx}",
                    opts,
                    index=None,
                    label_visibility="collapsed",
                    key=f"radio-{i}-{q_idx}"
                )

                if chosen is not None:
                    if opts.index(chosen) == correct:
                        st.success("Correct ✅")
                    else:
                        st.error(f"Not quite — answer: {opts[correct]}")

            if st.button("Close test", key=f"close-{i}"):
                m["quiz"] = None
                st.rerun() if hasattr(st, "rerun") else None

    st.markdown('<hr class="dfy-divider">', unsafe_allow_html=True)
