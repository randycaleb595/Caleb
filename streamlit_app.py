import base64
import hashlib
import html
import requests
import streamlit as st

APP_URL = "https://www.google.com/search?udm=50&aep=11"
TARGET = "German"
SOURCE_LANGUAGES = ["Auto-detect", "English", "French", "Spanish", "Portuguese", "Chinese", "Arabic"]

st.set_page_config(page_title="Deutschefy", page_icon="🇩🇪", layout="centered")

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


# ------------------------------------------------------------- the app's backend (HTTP)
def call(fn, payload):
    r = requests.post(f"{APP_URL}/functions/{fn}", json=payload, timeout=180)
    try:
        data = r.json()
    except ValueError:
        data = {}
    if not r.ok:
        raise RuntimeError(data.get("error") or f"{fn} failed ({r.status_code})")
    return data


def src_code(lang):
    return "auto" if lang == "Auto-detect" else lang


# ------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("turns", [])
ss.setdefault("seen_audio", set())
ss.setdefault("error", "")


def reset():
    ss.turns, ss.error = [], ""


def translate(text):
    ss.error = ""
    try:
        with st.spinner("Translating to German…"):
            res = call("translateText", {"text": text, "source_lang": src_code(ss.source_lang), "target_lang": TARGET})
        ss.turns.append({
            "source": text, "source_lang": ss.source_lang, "translation": res["translation"],
            "audio_url": None, "explanation": None, "questions": None, "answers": {}, "copy": False, "error": "",
        })
    except Exception as e:
        ss.error = str(e)


def transcribe(f):
    raw = f.getvalue()
    digest = hashlib.md5(raw).hexdigest()
    if digest in ss.seen_audio:
        return ""
    ss.seen_audio.add(digest)
    data_url = f"data:{f.type or 'audio/wav'};base64,{base64.b64encode(raw).decode()}"
    try:
        with st.spinner("Transcribing your audio…"):
            text = (call("transcribeAudio", {"audio_base64": data_url, "filename": f.name}).get("transcript") or "").strip()
        if not text:
            ss.error = "We couldn't hear anything in that clip."
        return text
    except Exception as e:
        ss.error = str(e)
        return ""


def act(t, fn, payload, field, msg):
    t["error"] = ""
    try:
        with st.spinner(msg):
            t[field] = call(fn, payload).get(field)
    except Exception as e:
        t["error"] = str(e)


def turn_payload(t):
    return {"text": t["source"], "translation": t["translation"],
            "source_lang": src_code(t["source_lang"]), "target_lang": TARGET}


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
                st.markdown(f'<div class="dfy-muted">{html.escape(q["explanation"])}</div>', unsafe_allow_html=True)
        if len(ans) == len(qs):
            msg = ("Perfect score — well done." if correct == len(qs)
                   else f"You got {correct} of {len(qs)}. Ask for a new test to try again.")
            st.markdown(f'<div style="color:#F0A93D;font-size:.8rem">{msg}</div>', unsafe_allow_html=True)


def render_turn(i, t):
    bubble(t["source_lang"], t["source"], "user")
    bubble(TARGET, t["translation"], "de")

    b = st.columns([1.3, 2.1, 1.2, 1, 2.2], gap="small")
    if b[0].button("🔊 Audio ready" if t["audio_url"] else "🔊 Listen", key=f"listen_{i}") and not t["audio_url"]:
        act(t, "speakText", {"text": t["translation"], "lang": TARGET}, "audio_url", "Generating audio…")
        st.rerun()
    if b[1].button("💡 Why this translation?", key=f"why_{i}"):
        act(t, "explainTranslation", turn_payload(t), "explanation", "Explaining…")
        st.rerun()
    if b[2].button("🎓 New test" if t["questions"] else "🎓 Test me", key=f"test_{i}"):
        act(t, "generateQuiz", {**turn_payload(t), "count": 4}, "questions", "Building your test…")
        t["answers"] = {}
        if not t["questions"] and not t["error"]:
            t["error"] = "Couldn't build a test for that one."
        st.rerun()
    if b[3].button("📋 Copy", key=f"copy_{i}"):
        t["copy"] = not t["copy"]
        st.rerun()

    if t["copy"]:
        st.code(t["translation"], language=None)
    if t["audio_url"]:
        st.audio(t["audio_url"])
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

top = st.columns([6, 1])
top[0].markdown('<div class="dfy-brand" style="text-align:right;font-size:.85rem;padding-top:.35rem">DEUTSCHEFY</div>',
                unsafe_allow_html=True)
if ss.turns:
    top[1].button("Clear", on_click=reset, key="clear")

if not ss.turns:
    st.markdown(
        '<div class="dfy-hero"><h1>DEUTSCHEFY</h1><p>Type, record, or upload audio. Then ask why a '
        "translation works the way it does, or take a quick test on it.</p></div>",
        unsafe_allow_html=True,
    )

for i, t in enumerate(ss.turns):
    render_turn(i, t)
    st.write("")

# composer
st.divider()
c = st.columns([2, 1, 3])
c[0].selectbox("From", SOURCE_LANGUAGES, key="source_lang")
c[1].markdown('<div class="dfy-muted" style="padding-top:2.1rem">To <strong>German</strong></div>',
              unsafe_allow_html=True)
a = st.columns(2)
recording = a[0].audio_input("Record audio", key="mic")
upload = a[1].file_uploader("Upload audio", type=["mp3", "wav", "m4a", "ogg", "webm", "mp4"], key="upload")
typed = st.chat_input("Type something to translate into German...")


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
