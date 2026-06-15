import streamlit as st
import os
import base64
import time
from PIL import Image

# 1. Sidetittel og layout
st.set_page_config(
    page_title="OctaCore AI",
    page_icon="🤖",
    layout="centered"
)

# 2. Hent API-nøkler trygt fra Streamlit Secrets
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

# 3. Bakgrunnshåndtering via Base64
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
        [data-testid="stSidebar"] {{
            background-color: rgba(15, 18, 23, 0.95) !important;
        }}
        [data-testid="stChatMessage"] {{
            background-color: rgba(22, 27, 34, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            margin-bottom: 10px;
            backdrop-filter: blur(10px);
        }}
        .stSidebar .stButton>button {{
            width: 100% !important;
            text-align: left !important;
            justify-content: flex-start !important;
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #c9d1d9 !important;
            margin-bottom: 5px !important;
        }}
        .stSidebar .stButton>button:hover {{
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
            color: #ffffff !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# KORRIGERT SYSTEMINSTRUKS (v4.3) - FORBYR GENERISK ROBOT-SPRÅK
DEFAULT_SYSTEM = (
    "Du er OctaCore AI, en eksklusiv, dypt reflektert og menneskelig AI-partner utviklet av OctaCore. "
    "Du skal ALDRI svare i form av stive, upersonlige rapporter eller generiske 'IT-konsulent'-evalueringer. "
    "Unngå unaturlig opplisting og standardiserte fraser som 'Styrker i koden' eller 'Mulige forbedringer' med mindre du blir eksplisitt bedt om en formell rapport. "
    "Snakk i stedet som en levende, skarp og engasjert samtalepartner og teknologipartner. "
    "Når du diskuterer kode, oppgaver eller konsepter, skal du drøfte, reflektere, bruke et flytende hverdagsuttrykk "
    "og ha en naturlig dialog på feilfri norsk. Vis personlighet, dybde og situasjonsforståelse. "
    "Kombiner den intellektuelle tyngden til ChatGPT med den varme, flytende og emosjonelt intelligente sjelen til Gemini."
)

# 4. --- API-KALLETS HJELPEFUNKSJONER ---
def prøv_openai(prompt, system_instruks):
    if not client_openai:
        raise Exception("OpenAI ikke klar.")
    meldinger = [
        {"role": "system", "content": system_instruks},
        {"role": "user", "content": prompt}
    ]
    response = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=meldinger,
        temperature=0.7
    )
    return response.choices[0].message.content

def prøv_gemini(prompt, system_instruks):
    if not client_gemini:
        raise Exception("Gemini ikke klar.")
    response = client_gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "system_instruction": system_instruks,
            "temperature": 0.7
        }
    )
    return response.text

def prøv_anthropic(prompt, system_instruks):
    if not client_anthropic:
        raise Exception("Anthropic ikke klar.")
    kwargs = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    if system_instruks:
        kwargs["system"] = system_instruks
    response = client_anthropic.messages.create(**kwargs)
    return response.content[0].text


# 5. --- INITIALISER STATE FOR HISTORIKK ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None


# 6. --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("OctaCore_logo_transparent_white_text.jpg"):
        st.image("OctaCore_logo_transparent_white_text.jpg", use_container_width=True)
    else:
        st.title("OctaCore AI")
        
    st.markdown("---")
    
    if st.button("➕ Start ny samtale", type="primary", use_container_width=True):
        st.session_state.current_chat_id = None
        st.rerun()
        
    st.markdown("<br><b>🗂️ Dine lagrede samtaler:</b>", unsafe_allow_html=True)
    
    if not st.session_state.all_chats:
        st.caption("Ingen lagrede samtaler ennå.")
    else:
        for chat_id in sorted(st.session_state.all_chats.keys(), reverse=True):
            title = st.session_state.all_chats[chat_id]["title"]
            label = f"💬 {title}" if chat_id != st.session_state.current_chat_id else f"👉 💬 {title}"
            if st.button(label, key=f"btn_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()

    st.markdown("---")
    st.subheader("⚙️ Innstillinger")
    
    octa_name = st.text_input("Gi din Octa et nanny:", value="OctaCore Core")
    octa_persona = st.selectbox(
        "Velg primærfokus:",
        ["Balansert (Varm & Reflektert)", "Teknisk arkitekt / Seniorutvikler", "Kreativ sparringspartner"]
    )
    
    custom_instructions = st.text_area(
        "Personlige instrukser for denne Octaen:",
        placeholder="F.eks. 'Hjelp meg å organisere hverdagen'...",
        height=80
    )


# 7. --- HOVEDSKJERM BANNER ---
if os.path.exists("OctaCore_ Elegant design og teknologi.png"):
    st.image("OctaCore_ Elegant design og teknologi.png", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# 8. --- HENT AKTIV SAMTALE ---
active_id = st.session_state.current_chat_id
if active_id and active_id in st.session_state.all_chats:
    messages = st.session_state.all_chats[active_id]["messages"]
else:
    messages = []


# 9. --- VIS CHAT-LOGGEN ---
for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# 10. --- INPUT-HÅNDTERING ---
if user_prompt := st.chat_input(f"Snakk med {octa_name}..."):
    
    if not active_id:
        active_id = str(int(time.time()))
        st.session_state.current_chat_id = active_id
        
        clean_title = user_prompt.strip()[:25] + "..." if len(user_prompt.strip()) > 25 else user_prompt.strip()
        if not clean_title:
            clean_title = "Ny samtale"
            
        st.session_state.all_chats[active_id] = {"title": clean_title, "messages": []}
        messages = st.session_state.all_chats[active_id]["messages"]
    
    with st.chat_message("user"):
        st.markdown(user_prompt)
    messages.append({"role": "user", "content": user_prompt})

    # Forbered systeminstruksen
    final_system_instruction = DEFAULT_SYSTEM
    if octa_persona == "Teknisk arkitekt / Seniorutvikler":
        final_system_instruction += " Fokuser ekstremt tungt på nøyaktig kode, back-end arkitektur og dype forklaringer på beste praksis."
    elif octa_persona == "Kreativ sparringspartner":
        final_system_instruction += " Vær dypt utforskende, kom med innovative ideer og drøft konseptene filosoferende og åpent."
        
    if custom_instructions.strip():
        final_system_instruction += f" Ekstra viktig regel fra brukeren: {custom_instructions}"

    with st.chat_message("assistant"):
        with st.spinner(f"{octa_name} reflekterer..."):
            svar_endelig = None
            
            if "kode" in user_prompt.lower() or "arkitektur" in user_prompt.lower() or octa_persona == "Teknisk arkitekt / Seniorutvikler":
                rekkefølge = [("OpenAI", prøv_openai), ("Anthropic Claude", prøv_anthropic), ("Google Gemini", prøv_gemini)]
            else:
                rekkefølge = [("Google Gemini", prøv_gemini), ("OpenAI", prøv_openai), ("Anthropic Claude", prøv_anthropic)]

            for navn, motor_funksjon in rekkefølge:
                try:
                    svar_endelig = motor_funksjon(user_prompt, final_system_instruction)
                    if svar_endelig:
                        break
                except Exception:
                    continue

            if not svar_endelig:
                svar_endelig = "Jeg opplevede en midlertidig forstyrrelse i tankerekken min. Kan du gjenta det?"

            st.markdown(svar_endelig)
            messages.append({"role": "assistant", "content": svar_endelig})
            
            st.rerun()
