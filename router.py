import streamlit as st
import os
import base64
import time
import json
from PIL import Image

# 1. Sidetittel, layout og miniatyrlogo i nettleserfanen
AVATAR_PATH = "OctaCore_icon.png"
MAIN_LOGO_PATH = "OctaCore_logo_transparent_white_text.jpg"

st.set_page_config(
    page_title="OctaCore AI",
    page_icon=AVATAR_PATH if os.path.exists(AVATAR_PATH) else "🤖",
    layout="centered"
)

HISTORY_FILE = "octacore_chat_history.json"
MAX_CONTEXT_MESSAGES = 20  # Maks antall meldinger i kontekst (10 samtalerunder)

# 2. Hjelpefunksjoner for permanent fil-lagring
def last_inn_historikk():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def lagre_historikk(data):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Kunne ikke lagre til fil: {e}")

# 3. API-nøkler og klientsjekk
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY")

client_gemini = None
client_openai = None
client_anthropic = None

if GEMINI_API_KEY:
    try:
        from google import genai
        client_gemini = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        pass

if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        client_openai = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        pass

if ANTHROPIC_API_KEY:
    try:
        from anthropic import Anthropic
        client_anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
    except Exception:
        pass

# 4. Bakgrunnsbilde via Base64
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

bg_base64 = get_base64_image("Svart lædertekstur med uendelighetssymboler.png")

if bg_base64:
    st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-image: url('data:image/png;base64,{bg_base64}');
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
    """, unsafe_allow_html=True)

# 5. Global CSS-styling for et strømlinjeformet grensesnitt
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: rgba(15, 18, 23, 0.97) !important;
    }
    /* Nullstiller unødvendig luft i toppen av sidepanelet så logoen spretter opp */
    [data-testid="stSidebarUserContent"] {
        padding-top: 0.5rem !important;
    }
    [data-testid="stChatMessage"] {
        background-color: rgba(22, 27, 34, 0.65) !important;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        margin-bottom: 10px;
        backdrop-filter: blur(10px);
    }
    .stSidebar .stButton>button {
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important;
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #c9d1d9 !important;
        margin-bottom: 4px !important;
        font-size: 0.85rem !important;
        padding: 0.4rem 0.75rem !important;
    }
    .stSidebar .stButton>button:hover {
        background-color: rgba(255, 255, 255, 0.06) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: #ffffff !important;
    }
    .model-tag {
        font-size: 0.72rem;
        color: #8b949e;
        margin-top: 6px;
        font-style: italic;
    }
    .model-tag-gemini { color: #4285F4; }
    .model-tag-openai { color: #10a37f; }
    .model-tag-anthropic { color: #d97706; }
    div[data-testid="stTextInput"] input {
        background-color: rgba(22, 27, 34, 0.8) !important;
        color: #c9d1d9 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 6. Menneskelig Systeminstruks
DEFAULT_SYSTEM = (
    "Du er OctaCore AI, en eksklusiv, dypt reflektert og menneskelig AI-partner utviklet av OctaCore. "
    "Du skal ALDRI svare i form av stive, upersonlige rapporter eller generiske 'IT-konsulent'-evalueringer. "
    "Unngå unaturlig opplisting og standardiserte fraser som 'Styrker i koden' eller 'Mulige forbedringer' med mindre du blir eksplisitt bedt om en formell rapport. "
    "Snakk i stedet som en levende, skarp og engasjert samtalepartner og teknologipartner. "
    "Når du diskuterer kode, oppgaver eller konsepter, skal du drøfte, reflektere, bruke et flytende hverdagsuttrykk "
    "og ha en naturlig dialog på feilfri norsk. Vis personlighet, dybde og situasjonsforståelse. "
    "Kombiner den intellektuelle tyngden til ChatGPT med den varme, flytende og emosjonelt intelligente sjelen til Gemini."
)

# 7. Strømlinjeformede streaming-funksjoner med kontekststøtte
def bygg_meldingsliste(messages, ny_prompt):
    """Begrenser kontekst til MAX_CONTEXT_MESSAGES og bygger meldingsliste."""
    historikk = messages[-(MAX_CONTEXT_MESSAGES - 1):] if len(messages) > MAX_CONTEXT_MESSAGES else messages[:]
    alle = [{"role": m["role"], "content": m["content"]} for m in historikk]
    alle.append({"role": "user", "content": ny_prompt})
    return alle

def stream_openai(meldinger, system_instruks):
    if not client_openai:
        raise Exception("OpenAI ikke klar.")
    api_meldinger = [{"role": "system", "content": system_instruks}] + meldinger
    stream = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=api_meldinger,
        temperature=0.7,
        stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

def stream_gemini(meldinger, system_instruks):
    if not client_gemini:
        raise Exception("Gemini ikke klar.")
    
    from google import genai
    contents_input = []
    for m in meldinger:
        role_label = "user" if m["role"] == "user" else "model"
        contents_input.append(genai.types.Content(
            role=role_label,
            parts=[genai.types.Part.from_text(text=m["content"])]
        ))
        
    response_stream = client_gemini.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=contents_input,
        config={
            "system_instruction": system_instruks,
            "temperature": 0.7
        }
    )
    for chunk in response_stream:
        if chunk.text:
            yield chunk.text

def stream_anthropic(meldinger, system_instruks):
    if not client_anthropic:
        raise Exception("Anthropic ikke klar.")
    with client_anthropic.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system_instruks,
        messages=meldinger,
        temperature=0.7
    ) as stream:
        for text in stream.text_stream:
            yield text

# 8. Initialiser app-tilstand
if "all_chats" not in st.session_state:
    st.session_state.all_chats = last_inn_historikk()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "rename_id" not in st.session_state:
    st.session_state.rename_id = None

# 9. INTEGRERT SIDEBAR (Tvinger logoen stabilt på topp med Base64-innbaking for å hindre element-hopping)
with st.sidebar:
    logo_base64 = get_base64_image(MAIN_LOGO_PATH)
    if logo_base64:
        st.markdown(
            f'<div style="text-align: center; margin-bottom: 15px;">'
            f'<img src="data:image/jpeg;base64,{logo_base64}" style="width: 100%; max-width: 260px; height: auto;">'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.title("OctaCore AI")

    st.markdown("---")

    if st.button("➕ Start ny samtale", type="primary", use_container_width=True):
        st.session_state.current_chat_id = None
        st.session_state.rename_id = None
        st.rerun()

    st.markdown("<br><b>🗂️ Dine samtaler:</b>", unsafe_allow_html=True)

    if not st.session_state.all_chats:
        st.caption("Ingen lagrede samtaler ennå.")
    else:
        for chat_id in sorted(st.session_state.all_chats.keys(), reverse=True):
            title = st.session_state.all_chats[chat_id]["title"]
            is_active = chat_id == st.session_state.current_chat_id

            if st.session_state.rename_id == chat_id:
                ny_tittel = st.text_input("Nytt navn:", value=title, key=f"rename_{chat_id}")
                col_ok, col_avbryt = st.columns(2)
                with col_ok:
                    if st.button("✅", key=f"ok_{chat_id}"):
                        st.session_state.all_chats[chat_id]["title"] = ny_tittel.strip() or title
                        lagre_historikk(st.session_state.all_chats)
                        st.session_state.rename_id = None
                        st.rerun()
                with col_avbryt:
                    if st.button("❌", key=f"avbryt_{chat_id}"):
                        st.session_state.rename_id = None
                        st.rerun()
            else:
                col_btn, col_rename, col_del = st.columns([6, 1, 1])
                with col_btn:
                    label = f"{'👉 ' if is_active else ''}💬 {title}"
                    if st.button(label, key=f"btn_{chat_id}"):
                        st.session_state.current_chat_id = chat_id
                        st.session_state.rename_id = None
                        st.rerun()
                with col_rename:
                    if st.button("✏️", key=f"ren_{chat_id}", help="Gi ny tittel"):
                        st.session_state.rename_id = chat_id
                        st.rerun()
                with col_del:
                    if st.button("🗑", key=f"del_{chat_id}", help="Slett denne samtalen"):
                        del st.session_state.all_chats[chat_id]
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                        lagre_historikk(st.session_state.all_chats)
                        st.rerun()

    st.markdown("---")
    if st.button("🗑️ Slett alle samtaler", type="secondary", use_container_width=True):
        st.session_state.all_chats = {}
        st.session_state.current_chat_id = None
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        st.rerun()

    st.markdown("---")
    st.subheader("⚙️ Innstillinger")

    octa_name = st.text_input("Gi din Octa et navn:", value="OctaCore")
    octa_persona = st.selectbox(
        "Velg primærfokus:",
        ["Balansert (Varm & Reflektert)", "Teknisk arkitekt / Seniorutvikler", "Kreativ sparringspartner"]
    )
    custom_instructions = st.text_area(
        "Personlige instrukser:",
        placeholder="F.eks. 'Svar alltid strukturert'...",
        height=80
    )

# 10. Hovedskjerm - Helt ren uten unødvendige titler eller gamle undertitler
# 11. Hent aktiv samtalehistorikk
active_id = st.session_state.current_chat_id
if active_id and active_id in st.session_state.all_chats:
    messages = st.session_state.all_chats[active_id]["messages"]
else:
    messages = []

# 12. Rendring av historisk chat-logg med miniatyr-logo som avatar
for message in messages:
    avatar_to_use = AVATAR_PATH if (message["role"] == "assistant" and os.path.exists(AVATAR_PATH)) else None
