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
        [data-testid="stChatMessage"] {{
            background-color: rgba(22, 27, 34, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            margin-bottom: 10px;
            backdrop-filter: blur(10px);
        }}
        </style>
    """, unsafe_allow_html=True)

# EN SPLITTER NY, REFLEKTERT OG MENNESKELIG SYSTEMINSTRUKS (v4.0)
DEFAULT_SYSTEM = (
    "Du er OctaCore AI, en eksklusiv, dypt intelligent og varm AI-assistent utviklet av OctaCore. "
    "Svarene dine skal ALDRI oppleves som enkle, mekaniske robotsvar. "
    "Du skal skrive med en naturlig, reflektert og engasjerende menneskelig tone – akkurat som en dyktig rådgiver og samtalepartner. "
    "Vis situasjonsforståelse og empati der det er naturlig. Når du løser oppgaver eller svarer på spørsmål, "
    "skal du ikke bare spytte ut rådata, men forklare tankegangen din, drøfte nyanser og gi helhetlige, "
    "velformulerte svar med god språklig flyt på feilfri norsk. Kombiner den strukturerte dybden fra ChatGPT "
    "med den levende og emosjonelt intelligente personligheten til Gemini."
)

# 4. --- API-KALLETS HJELPEFUNKSJONER (Med innlagt temperatur på 0.7) ---
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
        temperature=0.7 # Gir mer naturlig og reflektert variasjon i språket
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
            "temperature": 0.7 # Skrur opp kreativitet og flyt hos Gemini
        }
    )
    return response.text

def prøv_anthropic(prompt, system_instruks):
    if not client_anthropic:
        raise Exception("Anthropic ikke klar.")
    kwargs = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1500, # Økt litt så den har plass til å reflektere dypere
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7 # Gir Claude den menneskelige finessen
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
        ["Balansert (Varm & Reflektert)", "Teknisk arkitekt / Seniorutvikler", "Kreativ sparringspartner"]
    )
    
    custom_instructions = st.text_area(
        "Personlige instrukser for denne Octaen:",
        placeholder="F.eks. 'Snakk til meg som en coach', 'Bruk eksempler i svarene'...",
        height=100
    )
    
    st.markdown("---")
    if st.button("Tøm samtalehistorikk 🗑️", type="secondary"):
        st.session_state.messages = []
        st.rerun()


# 6. --- HOVEDSKJERM BANNER ---
if os.path.exists("OctaCore_ Elegant design og teknologi.png"):
    st.image("OctaCore_ Elegant design og teknologi.png", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# 7. --- INITIALISER SAMTALEHISTORIKK ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# 8. --- CHAT-INPUT ---
if user_prompt := st.chat_input(f"Snakk med {octa_name}..."):
    
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    st.session_state.messages.append({"role": "user", "content": user_prompt})

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
            
            # Smart ruting-rekkefølge
            if "kode" in user_prompt.lower() or "arkitektur" in user_prompt.lower() or octa_persona == "Teknisk arkitekt / Seniorutvikler":
                rekkefølge = [("OpenAI", prøv_openai), ("Anthropic Claude", prøv_anthropic), ("Google Gemini", prøv_gemini)]
            else:
                rekkefølge = [("Google Gemini", prøv_gemini), ("OpenAI", prøv_openai), ("Anthropic Claude", prøv_anthropic)]

            # Prøv motorene
            for navn, motor_funksjon in rekkefølge:
                try:
                    svar_endelig = motor_funksjon(user_prompt, final_system_instruction)
                    if svar_endelig:
                        break
                except Exception:
                    continue

            if not svar_endelig:
                svar_endelig = "Jeg opplever en midlertidig forstyrrelse i tankerekken min på grunn av høy trafikk på ruter-nodene. Kan du gjenta det?"

            st.markdown(svar_endelig)
            st.session_state.messages.append({"role": "assistant", "content": svar_endelig})
