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
MAX_CONTEXT_MESSAGES = 20

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
        .stMain, body, [data-testid="stHeader"] {{
            background-image: url('data:image/png;base64,{bg_base64}') !important;
            background-size: cover !important;
            background-attachment: fixed !important;
            background-position: center !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# 5. Global CSS-styling (Optimalisert lesbarhet og kontrast)
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: rgba(15, 18, 23, 0.97) !important;
    }
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0.5rem !important;
    }
    [data-testid="stChatMessage"] {
        background-color: rgba(22, 27, 34, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        margin-bottom: 10px;
        backdrop-filter: blur(10px);
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span {
        color: #ffffff !important;
        font-size: 1.02rem !important;
        line-height: 1.6 !important;
    }
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3 {
        color: #ffffff !important;
    }
    [data-testid="stChatMessage"] li {
        color: #ffffff !important;
    }
    [data-testid="stChatMessage"] code {
        color: #ff79c6 !important;
        background-color: rgba(0, 0, 0, 0.4) !important;
        padding: 0.2rem 0.4rem !important;
        border-radius: 4px !important;
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
        font-size: 0.75rem;
        margin-top: 8px;
        font-style: italic;
        font-weight: 500;
    }
    .model-tag-gemini { color: #66b2ff !important; }
    .model-tag-openai { color: #5cd699 !important; }
    .model-tag-anthropic { color: #ffb366 !important; }
    div[data-testid="stTextInput"] input {
        background-color: rgba(22, 27, 34, 0.8) !important;
        color: #c9d1d9 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 6. Systeminstruks
DEFAULT_SYSTEM = (
    "Du er OctaCore AI, en eksklusiv, dypt reflektert og menneskelig AI-partner utviklet av OctaCore. "
    "Du skal ALDRI svare i form av stive, upersonlige rapporter eller generiske 'IT-konsulent'-evalueringer. "
    "Unngå unaturlig opplisting og standardiserte fraser som 'Styrker i koden' eller 'Mulige forbedringer' med mindre du blir eksplisitt bedt om en formell rapport. "
    "Snakk i stedet som en levende, skarp og engasjert samtalepartner og teknologipartner. "
    "Når du diskuterer kode, oppgaver eller konsepter, skal du drøfte, reflektere, bruke et flytende hverdagsuttrykk "
    "og ha en naturlig dialog på feilfri norsk. Vis personlighet, dybde og situasjonsforståelse. "
    "Kombiner den intellektuelle tyngden til ChatGPT med den varme, flytende og emosjonelt intelligente sjelen til Gemini."
)

# 7. Kontekstbygging og streaming-funksjoner
def bygg_meldingsliste(messages, ny_prompt):
    historikk = messages[-(MAX_CONTEXT_MESSAGES - 1):] if len(messages) > MAX_CONTEXT_MESSAGES else messages[:]
    alle = [{"role": m["role"], "content": m["content"]} for m in historikk]
    alle.append({"role": "user", "content": ny_prompt})
    return alle

def stream_openai(meldinger, system_instruks):
    if not client_openai:
        raise Exception("OpenAI ikke konfigurert eller mangler API-nøkkel.")
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
        raise Exception("Gemini ikke konfigurert eller mangler API-nøkkel.")
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
        raise Exception("Anthropic ikke konfigurert eller mangler API-nøkkel.")
    with client_anthropic.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system_instruks,
        messages=meldinger,
        temperature=0.