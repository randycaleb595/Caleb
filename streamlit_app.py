import streamlit as st
import requests
import base64

APP_DOMAIN = "https://nexusai123.base44.app"
TRANSLATE_URL = f"{APP DOMAIN.com}/functions/translateText"
TRANSCRIBE_URL = f"{APP_DOMAIN.com}/functions/transcribeAudio"
SPEAK_URL = f"{APP_DOMAIN.com}/functions/speakText"

LANGUAGES = [
    "Auto-detect", "Kiswahili", "English", "French", "Chinese", "Arabic",
    "German", "Spanish", "Portuguese", "Hindi", "Russian", "Japanese",
    "Korean", "Italian", "Dutch", "Turkish", "Luganda", "Amharic",
    "Yoruba", "Zulu",
]

st.set_page_config(page_title="Ceasura Tutor — Kiswahili Translator", page_icon="🟢", layout="wide")

st.markdown("""
<style>
  html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #000000 !important; color: #ffffff;
  }
  [data-testid="stSidebar"] { background-color: #080808 !important; }
  [data-testid="stSidebar"] * { color: #ffffff; }
  h1, h2, h3 { color: #00FF00 !important; }
  .stButton>button { background: #00FF00; color: #000; font-weight: 700; border: none; border-radius: 8px; }
  .stButton>button:hover { filter: brightness(1.1); }
  .stTextArea>div>div>textarea, .stTextInput>div>div>input {
    background: #0a0a0a !important; border: 1px solid #00FF0033 !important;
    color: #fff !important; border-radius: 12px;
  }
  .stTabs [data-baseweb="tab-list"] { gap: 8px; }
  .stTabs [data-baseweb="tab"] { color: #ffffff60; }
  .stTabs [aria-selected="true"] { color: #00FF00 !important; }
</style>
""", unsafe_allow_html=True)

# --- Session state init ---
if "history" not in st.session_state: st.session_state.history = []
if "source_lang" not in st.session_state: st.session_state.source_lang = "Auto-detect"
if "target_lang" not in st.session_state: st.session_state.target_lang = "Kiswahili"
if "src_text" not in st.session_state: st.session_state.src_text = ""
if "translation_result" not in st.session_state: st.session_state.translation_result = ""
if "audio_url" not in st.session_state: st.session_state.audio_url = ""
if "transcript" not in st.session_state: st.session_state.transcript = ""

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("## 🟢 CEASURA TUTOR")
    st.markdown("<small style='color:#00FF0080'>KISWAHILI TRANSLATOR</small>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("➕ New Translation", use_container_width=True):
        st.session_state.src_text = ""
        st.session_state.translation_result = ""
        st.session_state.audio_url = ""
        st.session_state.transcript = ""
        st.rerun()
    st.markdown("---")
    if st.session_state.history:
        st.markdown("#### 🕘 Recent")
        for i, h in enumerate(st.session_state.history):
            if st.button(h["source"][:42], key=f"h{i}", use_container_width=True):
                st.session_state.src_text = h["source"]
                st.session_state.translation_result = h["target"]
                st.session_state.audio_url = ""
                st.session_state.source_lang = h["source_lang"]
                st.session_state.target_lang = h["target_lang"]
                st.rerun()

# ===================== MAIN (stacked, centered) =====================
st.markdown("<h1 style='text-align:center;color:#00FF00;letter-spacing:0.3em'>CEASURA TUTOR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#00FF0080'>Any language ⇄ Kiswahili · with audio</p>", unsafe_allow_html=True)

_, main_col, _ = st.columns([1, 2.5, 1])

with main_col:
    # Language selectors
    lcol1, lcol2 = st.columns(2)
    with lcol1:
        st.selectbox("From", LANGUAGES, key="source_lang")
    with lcol2:
        st.selectbox("To", [l for l in LANGUAGES if l != "Auto-detect"], key="target_lang")

    st.markdown("")

    # Tabbed input
    tab1, tab2 = st.tabs(["✍️ Type text", "🎤 Upload audio"])

    with tab1:
        st.text_area("Text to translate", height=150, key="src_text",
                     placeholder="Type text to translate...", label_visibility="collapsed")

    with tab2:
        audio_file = st.audio_input("Record from mic", key="rec_audio")
        uploaded = st.file_uploader("Or upload a file",
                     type=["wav", "mp3", "webm", "m4a", "ogg", "flac"], key="up_audio")
        if st.session_state.transcript:
            st.markdown(f"<div style='background:#0a0a0a;border:1px solid #00FF0033;border-radius:12px;padding:10px;color:#00FF00;font-size:12px'><b>Transcript:</b> {st.session_state.transcript}</div>", unsafe_allow_html=True)

    st.markdown("")

    # Translate button
    if st.button("🌐 Translate", use_container_width=True, type="primary"):
        text_to_translate = ""
        audio_bytes = None

        if uploaded is not None:
            audio_bytes = uploaded.getvalue()
        elif audio_file is not None:
            audio_bytes = audio_file.getvalue()

        if audio_bytes:
            b64 = base64.b64encode(audio_bytes).decode()
            data_url = f"data:audio/wav;base64,{b64}"
            with st.spinner("🎙️ Transcribing audio..."):
                try:
                    r = requests.post(TRANSCRIBE_URL, json={"audio_base64": data_url, "filename": "audio.wav"}, timeout=120)
                    if r.status_code == 200:
                        text_to_translate = r.json().get("transcript", "")
                        st.session_state.transcript = text_to_translate
                    else:
                        st.error(f"Transcription failed (HTTP {r.status_code})")
                except Exception as e:
                    st.error(f"Transcription error: {e}")
        else:
            text_to_translate = st.session_state.src_text.strip()

        if not text_to_translate:
            st.warning("Please enter text or upload audio to translate.")
        else:
            with st.spinner("🌐 Translating..."):
                try:
                    resp = requests.post(TRANSLATE_URL, json={
                        "text": text_to_translate,
                        "source_lang": "auto" if st.session_state.source_lang == "Auto-detect" else st.session_state.source_lang,
                        "target_lang": st.session_state.target_lang,
                    }, timeout=120)
                    if resp.status_code == 200:
                        translation = resp.json().get("translation", "")
                        st.session_state.translation_result = translation
                        st.session_state.audio_url = ""
                        st.session_state.history.insert(0, {
                            "source": text_to_translate, "target": translation,
                            "source_lang": st.session_state.source_lang,
                            "target_lang": st.session_state.target_lang,
                        })
                        st.session_state.history = st.session_state.history[:30]
                        st.rerun()
                    else:
                        st.error(f"❌ HTTP {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"❌ {e}")

    st.markdown("---")

    # Output section
    if st.session_state.translation_result:
        st.markdown("#### 📝 Translation")
        st.markdown(
            f"<div style='background:#0a0a0a;border:1px solid #00FF0033;border-radius:12px;padding:16px;color:#fff;font-size:15px;line-height:1.6'>{st.session_state.translation_result}</div>",
            unsafe_allow_html=True)

        st.markdown("")
        if st.button("🔊 Listen to translation", use_container_width=True):
            with st.spinner("🔊 Generating audio... (this can take ~30s)"):
                try:
                    sr = requests.post(SPEAK_URL, json={
                        "text": st.session_state.translation_result,
                        "lang": st.session_state.target_lang,
                    }, timeout=120)
                    if sr.status_code == 200:
                        st.session_state.audio_url = sr.json().get("audio_url", "")
                        st.rerun()
                    else:
                        st.error(f"Audio failed (HTTP {sr.status_code})")
                except Exception as e:
                    st.error(f"Audio error: {e}")

        if st.session_state.audio_url:
            st.markdown("")
            st.audio(st.session_state.audio_url, format="audio/mp3")
    else:
        st.markdown("<p style='text-align:center;color:#ffffff30'>Translation appears here...</p>", unsafe_allow_html=True)
