"""Interface web du chatbot (Streamlit >= 1.47).  Lancer : streamlit run app.py"""

from urllib.parse import quote

import streamlit as st

import db
from core import ACCEPTED_EXTENSIONS, file_to_part, get_client, stream_reply, transcribe

BOT_NAME = "AI ChatBot"
NAVY = "#14213D"
AMBER = "#F2A61F"

LANGUAGES = {
    "Automatique": None,
    "Francais": "francais",
    "Arabe": "arabe",
    "Darija": "darija marocaine",
    "English": "english",
    "Espanol": "espagnol",
}

SUGGESTIONS = {
    "Expliquer un concept": "Peux-tu m'expliquer un concept ? Demande-moi lequel.",
    "Traduire un texte": "Je veux traduire un texte. Demande-moi le texte et la langue cible.",
    "Aide en programmation": "J'ai besoin d'aide en programmation. Demande-moi le sujet.",
}

# Logo : bulle de discussion ambre avec ondes sonores (texte + voix)
LOGO_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
    f"<path d='M22 6H42A14 14 0 0 1 56 20V34A14 14 0 0 1 42 48H32L20 58V48H22"
    f"A14 14 0 0 1 8 34V20A14 14 0 0 1 22 6Z' fill='{AMBER}'/>"
    f"<g stroke='{NAVY}' stroke-width='5' stroke-linecap='round'>"
    "<line x1='19' y1='23' x2='19' y2='31'/><line x1='27' y1='17' x2='27' y2='37'/>"
    "<line x1='35' y1='20' x2='35' y2='34'/><line x1='43' y1='24' x2='43' y2='30'/>"
    "</g></svg>"
)
LOGO_URI = "data:image/svg+xml," + quote(LOGO_SVG)

st.set_page_config(page_title=BOT_NAME, page_icon=LOGO_URI, layout="centered")

CSS = """
<style>
:root {color-scheme: light;}
footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {display: none;}
.stApp, [data-testid="stAppViewContainer"] {background: #F7F7F4; color: __NAVY__;}
[data-testid="stHeader"] {background: transparent;}
.block-container, [data-testid="stMainBlockContainer"] {
    max-width: 760px; padding: 2.5rem 1rem 9rem 1rem;
}
.stApp [data-testid="stMarkdownContainer"] * {color: __NAVY__;}

/* ---------- Barre laterale (bleu nuit) ---------- */
[data-testid="stSidebar"] {background: __NAVY__; border-right: none;}
.stApp [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {color: #E8ECF4;}
.stApp [data-testid="stSidebar"] h2, .stApp [data-testid="stSidebar"] h3,
.stApp [data-testid="stSidebar"] h2 *, .stApp [data-testid="stSidebar"] h3 * {
    font-size: .74rem; text-transform: uppercase; letter-spacing: .09em;
    color: #8F9BB5 !important; font-weight: 600;
}
.brand {
    font-family: Georgia, "Times New Roman", serif; font-size: 1.35rem;
    display: flex; align-items: center; gap: .6rem; color: #fff;
}
.brand svg {width: 30px; height: 30px;}

[data-testid="stSidebar"] .stButton > button {
    border-radius: 10px; border: 1px solid transparent; background: transparent;
    justify-content: flex-start; transition: all .15s ease;
}
[data-testid="stSidebar"] .stButton > button p {color: #E8ECF4 !important;}
[data-testid="stSidebar"] .stButton > button:hover {background: #1F2F52; border-color: #1F2F52;}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #243760; border-color: #243760;
}
.st-key-newchat button {
    background: __AMBER__ !important; border-color: __AMBER__ !important;
    justify-content: center !important;
}
.st-key-newchat button p {color: __NAVY__ !important; font-weight: 600;}
.st-key-newchat button:hover {filter: brightness(1.06);}

[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #1F2F52; border-color: #2E4170;
}
[data-testid="stSidebar"] [data-baseweb="select"] * {color: #E8ECF4 !important;}
[data-testid="stSidebar"] [data-baseweb="select"] svg {fill: #E8ECF4;}

/* ---------- Accueil ---------- */
.welcome {text-align: center; margin: 12vh 0 1.5rem 0;}
.welcome svg {width: 56px; height: 56px;}
.greet {
    font-family: Georgia, "Times New Roman", serif; font-size: 2.3rem;
    font-weight: 400; letter-spacing: -0.01em; color: __NAVY__; margin-top: .7rem;
}
.sub {color: #6B7590; margin-top: .4rem;}

[class*="st-key-sugg_"] button {
    border-radius: 999px; padding: .5rem 1rem; background: #fff;
    border: 1px solid #D9DCE3; transition: all .15s ease;
}
[class*="st-key-sugg_"] button p {color: __NAVY__ !important;}
[class*="st-key-sugg_"] button:hover {border-color: __AMBER__; background: #FFF8E8;}

/* ---------- Messages ---------- */
[data-testid="stChatMessage"] {background: transparent; padding: .6rem 0; gap: .9rem;}

[data-testid="stChatMessageAvatarAssistant"] {
    background: transparent url("__LOGO__") center / 90% no-repeat; border-radius: 0;
}
[data-testid="stChatMessageAvatarAssistant"] > * {display: none;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
    [data-testid="stChatMessageContent"] {
    font-family: Georgia, "Times New Roman", serif; font-size: 1.04rem; line-height: 1.65;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
    [data-testid="stChatMessageContent"] * {font-family: inherit;}

[data-testid="stChatMessageAvatarUser"] {display: none;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stChatMessageContent"] {
    background: __NAVY__; border-radius: 18px; padding: .7rem 1.2rem;
    width: fit-content; max-width: 80%;
}
.stApp [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stChatMessageContent"] * {color: #fff;}

/* ---------- Zone de saisie (texte + fichiers + micro) ---------- */
[data-testid="stBottom"], [data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {background: #F7F7F4 !important;}
[data-testid="stBottomBlockContainer"] {max-width: 760px; padding: 0 1rem 1.5rem 1rem;}
[data-testid="stChatInput"] {
    background: #fff !important; border: 1px solid #D9DCE3 !important;
    border-radius: 26px; box-shadow: 0 4px 20px rgba(20, 33, 61, .08);
}
[data-testid="stChatInput"]:focus-within {border-color: __AMBER__ !important;}
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] div[data-baseweb] {
    background: #fff !important; border: none !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important; color: __NAVY__ !important;
    -webkit-text-fill-color: __NAVY__ !important; caret-color: __AMBER__;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #8A93A8 !important; -webkit-text-fill-color: #8A93A8 !important; opacity: 1;
}
[data-testid="stChatInput"] button {color: __NAVY__ !important;}
[data-testid="stChatInput"] button svg {fill: currentColor;}
[data-testid="stChatInput"] button:hover {background: #EEF0F5 !important;}
[data-testid="stChatInputSubmitButton"] {
    background: __AMBER__ !important; color: __NAVY__ !important; border-radius: 50%;
}
[data-testid="stChatInputSubmitButton"]:hover {filter: brightness(1.06);}
</style>
"""
st.markdown(
    CSS.replace("__NAVY__", NAVY).replace("__AMBER__", AMBER).replace("__LOGO__", LOGO_URI),
    unsafe_allow_html=True,
)

db.init_db()


@st.cache_resource
def client():
    return get_client()


try:
    client()
except RuntimeError as exc:
    st.error(str(exc))
    st.info(
        "Cree un fichier `.env` dans le meme dossier que `app.py` avec la ligne "
        "`GEMINI_API_KEY=ta_vraie_cle`, puis arrete (Ctrl+C) et relance l'app."
    )
    st.stop()

# ---------- Etat de session ----------
ss = st.session_state
ss.setdefault("conv_id", None)
pending = ss.pop("pending", None)

convs = db.list_conversations()
if ss.conv_id is None or ss.conv_id not in {c["id"] for c in convs}:
    ss.conv_id = convs[0]["id"] if convs else db.create_conversation()
    convs = db.list_conversations()

# ---------- Barre laterale ----------
with st.sidebar:
    st.markdown(f'<div class="brand">{LOGO_SVG}{BOT_NAME}</div>', unsafe_allow_html=True)
    st.write("")
    if st.button("Nouvelle conversation", key="newchat", use_container_width=True):
        ss.conv_id = db.create_conversation()
        st.rerun()

    st.subheader("Conversations")
    for c in convs:
        kind = "primary" if c["id"] == ss.conv_id else "secondary"
        if st.button(c["title"][:30], key=f"conv_{c['id']}", type=kind,
                     use_container_width=True):
            ss.conv_id = c["id"]
            st.rerun()

    st.subheader("Langue")
    lang_label = st.selectbox("Langue des reponses", list(LANGUAGES),
                              label_visibility="collapsed")
    lang = LANGUAGES[lang_label]

    st.write("")
    col1, col2 = st.columns(2)
    if col1.button("Vider", use_container_width=True):
        db.clear_messages(ss.conv_id)
        st.rerun()
    if col2.button("Supprimer", use_container_width=True):
        db.delete_conversation(ss.conv_id)
        ss.conv_id = None
        st.rerun()

# ---------- Accueil / historique ----------
history = db.get_messages(ss.conv_id)
if not history and not pending:
    st.markdown(
        f"""
        <div class="welcome">
          {LOGO_SVG}
          <div class="greet">Bonjour, comment puis-je t'aider ?</div>
          <div class="sub">Ecris, parle avec le micro ou joins un fichier avec le trombone.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(len(SUGGESTIONS))
    for col, (label, prompt) in zip(cols, SUGGESTIONS.items()):
        if col.button(label, key=f"sugg_{label}", use_container_width=True):
            ss.pending = prompt
            st.rerun()

for m in history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- Saisie : texte + fichiers + micro, dans la meme barre ----------
submission = st.chat_input(
    "Ecris ton message...",
    accept_file="multiple",
    file_type=ACCEPTED_EXTENSIONS,
    accept_audio=True,
)

user_text, files, audio = "", [], None
if submission:
    user_text = (submission.text or "").strip()
    files = list(submission.files or [])
    audio = submission.audio
elif pending:
    user_text = pending

used_audio = False
if audio is not None:
    with st.spinner("Transcription du message vocal..."):
        try:
            spoken = transcribe(client(), audio.getvalue(), "audio/wav")
            user_text = f"{user_text}\n{spoken}".strip() if user_text else spoken
            used_audio = True
        except Exception as exc:
            st.error(f"Erreur de transcription : {exc}")

if files and not user_text:
    user_text = "Analyse ce fichier et fais-en un resume."

if user_text:
    attachments, names = [], []
    for f in files:
        try:
            attachments.append(file_to_part(f.name, f.getvalue()))
            names.append(f.name)
        except ValueError as exc:
            st.warning(str(exc))

    shown = user_text
    if used_audio:
        shown = f"[Message vocal] {shown}"
    if names:
        shown += "\n\n_Fichiers : " + ", ".join(names) + "_"

    with st.chat_message("user"):
        st.markdown(shown)

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(
                stream_reply(client(), history, user_text, attachments, lang)
            )
        except Exception as exc:
            reply = None
            st.error(f"Erreur API : {exc}")

    if reply:
        db.add_message(ss.conv_id, "user", shown)
        db.add_message(ss.conv_id, "assistant", reply)
        if not history:
            db.rename_conversation(ss.conv_id, user_text[:40])
        st.rerun()