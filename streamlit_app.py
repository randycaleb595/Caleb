import base64
import hashlib
import html
import json

import requests
import streamlit as st

NEXUS = "https://nexusai123.base44.app/functions"
DEFAULT_TARGET = "German"
TIMEOUT = 180

LANGUAGE_GROUPS = {
    "East & Central Africa": [
        "Kiswahili", "Luganda", "Runyankole", "Rukiga", "Rutooro", "Runyoro",
        "Lusoga", "Lugbara", "Acholi", "Langi", "Ateso", "Karamojong",
        "Kupsabiny", "Lumasaba", "Samia", "Alur", "Japadhola", "Kumam",
        "Lugwere", "Kinyarwanda", "Kirundi", "Lingala", "Somali", "Amharic",
        "Tigrinya", "Oromo", "Dinka", "Nuer",
    ],
    "Rest of Africa": [
        "Hausa", "Yoruba", "Igbo", "Fulfulde", "Wolof", "Bambara", "Twi",
        "Ewe", "Ga", "Zulu", "Xhosa", "Afrikaans", "Shona", "Ndebele",
        "Setswana", "Sesotho", "Sepedi", "Tsonga", "Venda", "Swati",
        "Chichewa", "Bemba", "Tonga", "Lozi", "Malagasy", "Kikuyu", "Luo",
        "Kamba", "Kalenjin", "Maasai",
    ],
    "Europe": [
        "English", "French", "German", "Spanish", "Portuguese", "Italian",
        "Dutch", "Russian", "Ukrainian", "Belarusian", "Polish", "Czech",
        "Slovak", "Hungarian", "Romanian", "Bulgarian", "Greek", "Croatian",
        "Serbian", "Bosnian", "Slovenian", "Macedonian", "Albanian",
        "Estonian", "Latvian", "Lithuanian", "Finnish", "Swedish",
        "Norwegian", "Danish", "Icelandic", "Irish", "Scottish Gaelic",
        "Welsh", "Breton", "Basque", "Catalan", "Galician", "Maltese",
        "Luxembourgish", "Yiddish", "Esperanto",
    ],
    "Middle East & Central Asia": [
        "Arabic", "Hebrew", "Persian (Farsi)", "Dari", "Pashto",
        "Kurdish (Kurmanji)", "Kurdish (Sorani)", "Turkish", "Azerbaijani",
        "Armenian", "Georgian", "Kazakh", "Kyrgyz", "Uzbek", "Turkmen",
        "Tajik", "Uyghur",
    ],
    "South Asia": [
        "Hindi", "Urdu", "Bengali", "Punjabi", "Gujarati", "Marathi", "Tamil",
        "Telugu", "Kannada", "Malayalam", "Sinhala", "Nepali", "Assamese",
        "Odia", "Kashmiri", "Sindhi", "Dhivehi", "Dzongkha",
    ],
    "East & Southeast Asia": [
        "Chinese (Simplified)", "Chinese (Traditional)", "Cantonese",
        "Japanese", "Korean", "Mongolian", "Vietnamese", "Thai", "Lao",
        "Khmer", "Burmese", "Indonesian", "Malay", "Javanese", "Sundanese",
        "Filipino", "Cebuano", "Tetum", "Hmong",
    ],
    "Pacific & the Americas": [
        "Hawaiian", "Māori", "Samoan", "Tongan", "Fijian", "Chamorro",
        "Quechua", "Aymara", "Guaraní", "Nahuatl", "Haitian Creole",
        "Papiamento", "Jamaican Patois", "Inuktitut",
    ],
}

ALL_LANGUAGES = [lang for group in LANGUAGE_GROUPS.values() for lang in group]
SOURCE_LANGUAGES = ["Auto-detect"] + ALL_LANGUAGES

st.set_page_config(page_title="DEUSCHEFY", page_icon="GHP", layout="centered")

THEME = """
<style>
/* ---------- canvas ---------- */
.stApp, [data-testid="stAppViewContainer"] { background:
  radial-gradient(ellipse at 20% 50%, rgba(240,169,61,.05) 0%, transparent 50%),
  radial-gradient(ellipse at 80% 20%, rgba(46,184,160,.05) 0%, transparent 50%), #0A1614 !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background:#0B1A17 !important; border-right:1px solid rgba(240,169,61,.15); }
.block-container { padding-top: 1.4rem; }

/* ---------- text ---------- */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p, label,
[data-testid="stCaptionContainer"] { color:#EDE7DA; }
[data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"] { color:#94A8A2; font-size:.78rem; }
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 { color:#F0A93D; letter-spacing:.04em; }
[data-testid="stMarkdownContainer"] em { color:#C8D6D1; }
[data-testid="stMarkdownContainer"] code { color:#F0A93D; background:rgba(240,169,61,.10); }
[data-testid="stSpinner"] p { color:#94A8A2; }

/* ---------- inputs ---------- */
[data-baseweb="select"] > div, [data-baseweb="input"] input, textarea,
[data-testid="stFileUploaderDropzone"], [data-testid="stAudioInput"] {
  background:#0F1D1A !important; border-color:#2B4340 !important; color:#EDE7DA !important; }
[data-baseweb="select"] svg { fill:#94A8A2; }
[data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] ul {
  background:#0F1D1A !important; border:1px solid #2B4340 !important; }
[data-baseweb="popover"] li, [data-baseweb="popover"] [role="option"] { color:#EDE7DA !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] [aria-selected="true"] {
  background:rgba(240,169,61,.14) !important; }
[data-testid="stFileUploaderDropzone"] { padding:.55rem .7rem; }
[data-testid="stFileUploaderDropzone"] span, [data-testid="stFileUploaderDropzone"] small { color:#94A8A2 !important; }
[data-testid="stFileUploaderDropzone"] button {
  background:transparent !important; color:#F0A93D !important; border:1px solid rgba(240,169,61,.45) !important; }
[data-testid="stChatInput"], [data-testid="stChatInput"] > div,
[data-testid="stChatInputTextArea"] {
  background:#0F1D1A !important; border-color:#2B4340 !important; color:#EDE7DA !important; }
[data-testid="stChatInput"] textarea { color:#EDE7DA !important; }
[data-testid="stChatInput"] textarea::placeholder { color:#6C807B !important; }

/* ---------- buttons ---------- */
.stButton > button { background:transparent; color:#94A8A2; border:1px solid #2B4340;
  border-radius:8px; min-height:0; padding:.25rem .7rem; }
.stButton > button p { font-size:.75rem; }
.stButton > button:hover { color:#F0A93D; border-color:rgba(240,169,61,.5); background:rgba(240,169,61,.06); }
.stButton > button:disabled { color:#6C807B; border-color:#22332F; }
[class*="st-key-opt_"] button { width:100%; justify-content:flex-start; text-align:left; }
[class*="st-key-opt_"] button p { color:#EDE7DA; font-size:.8rem; }

/* ---------- panels ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
  border:1px solid #2B4340 !important; border-radius:12px; background:rgba(15,29,26,.6); }
hr { border-color:rgba(240,169,61,.15); }
pre { background:#0F1D1A !important; border:1px solid #2B4340; }

/* ---------- brand + bubbles ---------- */
.dfy-brand { color:#F0A93D; font-weight:800; letter-spacing:.3em; }
.dfy-hero { text-align:center; padding:4rem 1rem 3rem; }
.dfy-hero h1 { color:#F0A93D; font-weight:800; letter-spacing:.3em; font-size:2.3rem; margin:0 0 .75rem; }
.dfy-hero p { color:#94A8A2; font-size:.9rem; max-width:28rem; margin:0 auto; }
.dfy-row { display:flex; margin:.3rem 0; }
.dfy-bubble { max-width:85%; padding:.6rem 1rem; border-radius:16px; line-height:1.55;
  font-size:.92rem; color:#EDE7DA; }
.dfy-user { margin-left:auto; background:rgba(240,169,61,.10); border:1px solid rgba(240,169,61,.25);
  border-bottom-right-radius:4px; }
.dfy-de { background:#0F1D1A; border:1px solid #2B4340; border-bottom-left-radius:4px; }
.dfy-label { font-size:.62rem; text-transform:uppercase; letter-spacing:.18em; margin-bottom:.2rem; color:#94A8A2; }
.dfy-user .dfy-label { color:rgba(240,169,61,.7); }
.dfy-kicker { font-size:.62rem; text-transform:uppercase; letter-spacing:.18em; color:#F0A93D; }
.dfy-muted { color:#94A8A2; font-size:.75rem; }
.dfy-error { color:#E5604E; font-size:.78rem; }
</style>
"""
st.markdown(THEME, unsafe_allow_html=True)


# ------------------------------------------------------------- Nexus backend
def call(function, payload):
    """Call one of the Nexus app's backend functions and return its JSON."""
    try:
        res = requests.post(f"{NEXUS}/{function}", json=payload, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise RuntimeError(f"Couldn't reach Nexus: {exc}") from exc

    try:
        data = res.json()
    except ValueError:
        data = {}

    if not res.ok:
        raise RuntimeError(data.get("error") or f"Nexus error {res.status_code}")
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data


def translate_text(text, source, target):
    data = call("translateText", {
        "text": text,
        "source_lang": "auto" if source == "Auto-detect" else source,
        "target_lang": target,
    })
    out = (data.get("translation") or "").strip()
    if not out:
        raise RuntimeError("No translation came back — try again.")
    return out


def explain_translation(text, translation, source, target):
    data = call("explainTranslation", {
        "text": text,
        "translation": translation,
        "source_lang": "auto" if source == "Auto-detect" else source,
        "target_lang": target,
    })
    return data.get("explanation") or "No explanation came back."


def build_quiz(text, translation, source, target, count):
    data = call("generateQuiz", {
        "text": text,
        "translation": translation,
        "source_lang": "auto" if source == "Auto-detect" else source,
        "target_lang": target,
        "count": max(1, int(count)),
    })
    questions = data.get("questions") or []
    if not questions:
        raise RuntimeError("Couldn't build a test for that one — try again.")
    return questions


def speak_text(text, target):
    data = call("speakText", {"text": text, "lang": target})
    url = data.get("audio_url")
    if not url:
        raise RuntimeError("No audio came back — try again.")
    audio = requests.get(url, timeout=TIMEOUT)
    if not audio.ok:
        raise RuntimeError("Couldn't download the audio — try again.")
    return audio.content


def transcribe_audio(raw, mime):
    encoded = base64.b64encode(raw).decode()
    data = call("transcribeAudio", {
        "audio_base64": f"data:{mime or 'audio/wav'};base64,{encoded}",
        "filename": "clip." + (mime.split("/")[-1].split(";")[0] or "wav"),
    })
    text = (data.get("transcript") or "").strip()
    if not text:
        raise RuntimeError("We couldn't hear anything in that clip.")
    return text


# ------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("turns", [])
ss.setdefault("seen_audio", set())
ss.setdefault("error", "")
ss.setdefault("quiz_count", 4)
ss.setdefault("target_lang", DEFAULT_TARGET)
ss.setdefault("source_lang", "Auto-detect")


def reset():
    ss.turns, ss.error = [], ""


def translate(text):
    ss.error = ""
    try:
        with st.spinner(f"Translating to {ss.target_lang}…"):
            out = translate_text(text, ss.source_lang, ss.target_lang)
        ss.turns.append({
            "source": text, "source_lang": ss.source_lang, "target_lang": ss.target_lang,
            "translation": out, "audio": None, "explanation": None, "questions": None,
            "answers": {}, "copy": False, "error": "",
        })
    except Exception as e:
        ss.error = str(e)


def transcribe(f):
    raw = f.getvalue()
    digest = hashlib.md5(raw).hexdigest()
    if digest in ss.seen_audio:
        return ""
    ss.seen_audio.add(digest)
    try:
        with st.spinner("Transcribing your audio…"):
            return transcribe_audio(raw, getattr(f, "type", "") or "audio/wav")
    except Exception as e:
        ss.error = str(e)
        return ""


def act(t, work, field, msg):
    t["error"] = ""
    try:
        with st.spinner(msg):
            t[field] = work()
    except Exception as e:
        t["error"] = str(e)


def turn_payload(t):
    return t["source"], t["translation"], t["source_lang"], t["target_lang"]


# ------------------------------------------------------------- rendering
def bubble(label, text, kind):
    body = html.escape(text).replace("\n", "<br>")
    st.markdown(
        f'<div class="dfy-row"><div class="dfy-bubble dfy-{kind}">'
        f'<div class="dfy-label">{html.escape(label)}</div>{body}</div></div>',
        unsafe_allow_html=True,
    )


def pick(t, qi, oi):
    t["answers"].setdefault(qi, oi)


def render_quiz(i, t):
    qs, ans = t["questions"], t["answers"]
    correct = sum(1 for qi, oi in ans.items() if qs[qi]["answer_index"] == oi)
    with st.container(border=True):
        h = st.columns([3, 1])
        h[0].markdown('<div class="dfy-kicker">Practice test</div>', unsafe_allow_html=True)
        h[1].markdown(f'<div class="dfy-muted" style="text-align:right">{correct} / {len(qs)} correct</div>',
                      unsafe_allow_html=True)
        for qi, q in enumerate(qs):
            st.markdown(f"**{qi + 1}.** {q['question']}")
            picked = ans.get(qi)
            for oi, opt in enumerate(q["options"]):
                mark = ""
                if picked is not None and oi == q["answer_index"]:
                    mark = "✅ "
                elif picked == oi:
                    mark = "❌ "
                st.button(mark + opt, key=f"opt_{i}_{qi}_{oi}", disabled=picked is not None,
                          on_click=pick, args=(t, qi, oi))
            if picked is not None and q.get("explanation"):
                st.markdown(f'<div class="dfy-muted">{html.escape(q["explanation"])}</div>',
                            unsafe_allow_html=True)
        if len(ans) == len(qs):
            msg = ("Perfect score — well done." if correct == len(qs)
                   else f"You got {correct} of {len(qs)}. Ask for a new test to try again.")
            st.markdown(f'<div style="color:#F0A93D;font-size:.8rem">{msg}</div>',
                        unsafe_allow_html=True)


def render_turn(i, t):
    bubble(t["source_lang"], t["source"], "user")
    bubble(t["target_lang"], t["translation"], "de")

    b = st.columns([1.3, 2.1, 1.2, 1, 2.2], gap="small")
    if b[0].button("🔊 Audio ready" if t["audio"] else "🔊 Listen", key=f"listen_{i}") and not t["audio"]:
        act(t, lambda: speak_text(t["translation"], t["target_lang"]), "audio", "Generating audio…")
        st.rerun()
    if b[1].button("💡 Why this translation?", key=f"why_{i}"):
        act(t, lambda: explain_translation(*turn_payload(t)), "explanation", "Explaining…")
        st.rerun()
    if b[2].button("🎓 New test" if t["questions"] else "🎓 Test me", key=f"test_{i}"):
        act(t, lambda: build_quiz(*turn_payload(t), ss.quiz_count), "questions", "Building your test…")
        t["answers"] = {}
        st.rerun()
    if b[3].button("📋 Copy", key=f"copy_{i}"):
        t["copy"] = not t["copy"]
        st.rerun()

    if t["copy"]:
        st.code(t["translation"], language=None)
    if t["audio"]:
        st.audio(t["audio"], format="audio/mp3")
    if t["explanation"]:
        with st.container(border=True):
            st.markdown('<div class="dfy-kicker">Explanation</div>', unsafe_allow_html=True)
            st.markdown(t["explanation"])
    if t["questions"]:
        render_quiz(i, t)
    if t["error"]:
        st.markdown(f'<div class="dfy-error">{html.escape(t["error"])}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------- page
with st.sidebar:
    st.markdown('<div class="dfy-brand" style="font-size:1.25rem;margin-bottom:1rem">DEUTSCHEFY</div>',
                unsafe_allow_html=True)
    st.button("＋ New Translation", on_click=reset, key="new")
    st.selectbox("Translate into", ALL_LANGUAGES,
                 index=ALL_LANGUAGES.index(DEFAULT_TARGET), key="target_lang")
    st.number_input("Questions per test", min_value=1, step=1, key="quiz_count")
    st.markdown('<div class="dfy-muted">Powered by the Nexus backend.</div>', unsafe_allow_html=True)

top = st.columns([6, 1])
top[0].markdown('<div class="dfy-brand" style="text-align:right;font-size:.85rem;padding-top:.35rem">DEUTSCHEFY</div>',
                unsafe_allow_html=True)
if ss.turns:
    top[1].button("Clear", on_click=reset, key="clear")

if not ss.turns:
    st.markdown(
        f'<div class="dfy-hero"><h1>DEUTSCHEFY</h1><p>Type in any of {len(ALL_LANGUAGES)} languages, '
        f"record, or upload audio. Then ask why a translation works the way it does, "
        f"or take a quick test on it.</p></div>",
        unsafe_allow_html=True,
    )

for i, t in enumerate(ss.turns):
    render_turn(i, t)
    st.write("")

# composer
st.divider()
c = st.columns([2, 1, 3])
c[0].selectbox("From", SOURCE_LANGUAGES, key="source_lang")
c[1].markdown(f'<div class="dfy-muted" style="padding-top:2.1rem">To <strong>{ss.target_lang}</strong></div>',
              unsafe_allow_html=True)
a = st.columns(2)
recording = a[0].audio_input("Record audio", key="mic")
upload = a[1].file_uploader("Upload audio", type=["mp3", "wav", "m4a", "ogg", "webm", "mp4"], key="upload")
typed = st.chat_input(f"Type something to translate into {ss.target_lang}...")


def incoming():
    if typed and typed.strip():
        return typed.strip()
    for f in (recording, upload):
        if f:
            text = transcribe(f)
            if text:
                return text
    return ""


new_text = incoming()
if new_text:
    translate(new_text)
    st.rerun()

if ss.error:
    st.markdown(f'<div class="dfy-error">{html.escape(ss.error)}</div>', unsafe_allow_html=True)
