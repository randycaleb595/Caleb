import streamlit as st
import requests

APP_DOMAIN = "https://nexusai123.base44.app"
TRANSLATE_URL = f"{APP_DOMAIN}/functions/translateText"

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
</style>
""", unsafe_allow_html=True)

# --- Session state init ---
if "history" not in st.session_state: st.session_state.history = []
if "source_lang" not in st.session_state: st.session_state.source_lang = "Auto-detect"
if "target_lang" not in st.session_state: st.session_state.target_lang = "Kiswahili"
if "src_text" not in st.session_state: st.session_state.src_text = ""
if "translation_result" not in st.session_state: st.session_state.translation_result = ""

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("## 🟢 CEASURA TUTOR")
    st.markdown("<small style='color:#00FF0080'>KISWAHILI TRANSLATOR</small>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("➕ New Translation", use_container_width=True):
        st.session_state.src_text = ""
        st.session_state.translation_result = ""
        st.rerun()
    st.markdown("---")
    if st.session_state.history:
        st.markdown("#### 🕘 Recent")
        for i, h in enumerate(st.session_state.history):
            if st.button(h["source"][:42], key=f"h{i}", use_container_width=True):
                st.session_state.src_text = h["source"]
                st.session_state.translation_result = h["target"]
                st.session_state.source_lang = h["source_lang"]
                st.session_state.target_lang = h["target_lang"]
                st.rerun()

# ===================== MAIN =====================
st.markdown("<h1 style='text-align:center;color:#00FF00;letter-spacing:0.3em'>CEASURA TUTOR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#00FF0080'>Any language ⇄ Kiswahili</p>", unsafe_allow_html=True)

# Language selectors
col1, col2, col3 = st.columns([1, 0.25, 1])
with col1:
    st.selectbox("From", LANGUAGES, key="source_lang")
with col2:
    st.write("")
    st.write("")
    if st.button("⇄", help="Swap languages"):
        cur_src = st.session_state.source_lang
        cur_tgt = st.session_state.target_lang
        st.session_state.source_lang = cur_tgt if cur_tgt != "Auto-detect" else "Kiswahili"
        st.session_state.target_lang = cur_src if cur_src != "Auto-detect" else "Kiswahili"
        st.session_state.src_text, st.session_state.translation_result = st.session_state.translation_result, st.session_state.src_text
        st.rerun()
with col3:
    st.selectbox("To", [l for l in LANGUAGES if l != "Auto-detect"], key="target_lang")

st.markdown("")

# Panels
pcol1, pcol2 = st.columns(2)
with pcol1:
    st.text_area("Text to translate", height=200, key="src_text",
                 placeholder="Type text to translate...", label_visibility="collapsed")
with pcol2:
    st.text_area("Translation", height=200,
                 value=st.session_state.translation_result,
                 placeholder="Translation appears here...", label_visibility="collapsed")

if st.button("Translate", use_container_width=True, type="primary"):
    src = st.session_state.src_text.strip()
    if not src:
        st.warning("Please enter some text to translate.")
    else:
        try:
            resp = requests.post(TRANSLATE_URL, json={
                "text": src,
                "source_lang": "auto" if st.session_state.source_lang == "Auto-detect" else st.session_state.source_lang,
                "target_lang": st.session_state.target_lang,
            }, timeout=120)
            if resp.status_code == 200:
                translation = resp.json().get("translation", "")
                st.session_state.translation_result = translation
                st.session_state.history.insert(0, {
                    "source": src, "target": translation,
                    "source_lang": st.session_state.source_lang,
                    "target_lang": st.session_state.target_lang,
                })
                st.session_state.history = st.session_state.history[:30]
                st.rerun()
            else:
                st.error(f"❌ HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"❌ {e}")
