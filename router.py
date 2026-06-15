import streamlit as st
import os
import base64
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
        /* Styling for chat-meldinger for å matche lær-temaet */
        [data-testid="stChatMessage"] {{
            background-color: rgba(22, 27, 34, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            margin-bottom: 10px;
            backdrop-filter: blur(10px);
        }}
        </style>
    """, unsafe_allow_html=True)

# Default systeminstruks (Kombinasjon av egenskapene til Gemini og ChatGPT)
DEFAULT_SYSTEM = (
    "Du er OctaCore AI, en eksklusiv og avansert AI-assistent utviklet av OctaCore. "
    "Svarene dine skal kombinere den analytiske presisjonen og strukturen fra ChatGPT, "
    "med den dype kontekstforståelsen, flyten og personlige finessen til Gemini. "
    "Fremstå profesjonell, skarp og direkte, uten unødvendig fylltekst."
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
        messages=meldinger
    )
    return response.choices[0].message.content

def prøv_gemini(prompt, system_instruks):
    if not client_gemini:
        raise Exception("Gemini ikke klar.")
    response = client_gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"system_instruction": system_instruks}
    )
    return response.text

def prøv_anthropic(prompt, system_instruks):
    if not client_anthropic:
        raise Exception("Anthropic ikke klar.")
    kwargs = {
        "model": "claude-sonnet-4-6", # Din fungerende variant!
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }
    if system_instruks:
        kwargs["system"] = system_instruks
    response = client_anthropic.messages.create(**kwargs)
    return response.content[0].text


# 5. --- SIDEBAR: CONFIG ---
with st.sidebar:
    if os.path.exists("OctaCore_logo_transparent_white_text.jpg"):
        st.image("OctaCore_logo_transparent_white_text.jpg", use_container_width=True)
    else:
        st.title("OctaCore AI")
        
    st.markdown("---")
    st.subheader("💎 Konfigurer din Octa")
    
    octa_name = st.text_input("Gi din Octa et navn:", value="OctaCore Core")
    octa_persona = st.selectbox(
        "Velg primærfokus:",
        ["Balansert (Miks av Gemini & ChatGPT)", "Teknisk arkitekt / Seniorutvikler", "Kreativ sparringspartner"]
    )
    
    custom_instructions = st.text_area(
        "Personlige instrukser for denne Octaen:",
        placeholder="F.eks. 'Hjelp meg å organisere hverdagen'...",
        height=100
    )
    
    # Knapp for å tømme chatten
    st.markdown("---")
    if st.button("Tøm samtalehistorikk 🗑️", type="secondary"):
        st.session_state.messages = []
        st.rerun()


# 6. --- HOVEDSKJERM BANNER ---
if os.path.exists("OctaCore_ Elegant design og teknologi.png"):
    st.image("OctaCore_ Elegant design og teknologi.png", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# 7. --- INITIALISER SAMTALEHISTORIKK (CHAT STATE) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Vis tidligere meldinger i tråden
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# 8. --- EKTE CHAT-INPUT (OPPLEVES SOM GEMINI/CHATGPT) ---
if user_prompt := st.chat_input(f"Spør {octa_name}..."):
    
    # Vis brukerens melding umiddelbart i chatten
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    # Lagre brukerens melding i historikken
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # Forbered systeminstruksen
    final_system_instruction = DEFAULT_SYSTEM
    if octa_persona == "Teknisk arkitekt / Seniorutvikler":
        final_system_instruction += " Fokuser ekstremt tungt på nøyaktig kode, back-end arkitektur og beste praksis."
    elif octa_persona == "Kreativ sparringspartner":
        final_system_instruction += " Vær utforskende, kom med innovative ideer og tenk utenfor boksen."
        
    if custom_instructions.strip():
        final_system_instruction += f" Ytterligere brukerinstruks: {custom_instructions}"

    # Generer svar med animert chat-spinner
    with st.chat_message("assistant"):
        with st.spinner(f"{octa_name} tenker..."):
            svar_endelig = None
            
            # Smart ruting-rekkefølge
            if "kode" in user_prompt.lower() or "arkitektur" in user_prompt.lower() or octa_persona == "Teknisk arkitekt / Seniorutvikler":
                rekkefølge = [("OpenAI", prøv_openai), ("Anthropic Claude", prøv_anthropic), ("Google Gemini", prøv_gemini)]
            else:
                rekkefølge = [("Google Gemini", prøv_gemini), ("OpenAI", prøv_openai), ("Anthropic Claude", prøv_anthropic)]

            # Prøv motorene etter tur
            for navn, motor_funksjon in rekkefølge:
                try:
                    svar_endelig = motor_funksjon(user_prompt, final_system_instruction)
                    if svar_endelig:
                        break
                except Exception:
                    continue

            if not svar_endelig:
                svar_endelig = "OctaCore AI opplever for øyeblikket høy trafikk. Vennligst prøv igjen om et øyeblikk."

            # Skriv ut svaret i chatten og lagre i historikken
            st.markdown(svar_endelig)
            st.session_state.messages.append({"role": "assistant", "content": svar_endelig})
