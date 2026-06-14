import streamlit as st
import os
import base64
from PIL import Image

# 1. Konfigurer siden aller først
st.set_page_config(
    page_title="OctaCore AI Router",
    page_icon="🤖",
    layout="wide"
)

# 2. Hent API-nøkler trygt fra Streamlit Secrets
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY")

# Initialiserer klienter
client_gemini = None
client_openai = None
client_anthropic = None

if GEMINI_API_KEY:
    try:
        from google import genai
        client_gemini = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.sidebar.error(f"Kunne ikke lade Gemini: {e}")

if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        client_openai = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        st.sidebar.error(f"Kunne ikke lade OpenAI: {e}")

if ANTHROPIC_API_KEY:
    try:
        from anthropic import Anthropic
        client_anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
    except Exception as e:
        st.sidebar.error(f"Kunne ikke lade Anthropic: {e}")

# Funksjoner for å kalle modellene
def generer_gemini(prompt, system_instruks):
    if not client_gemini:
        return "Gemini API-nøkkel mangler eller klienten feilet."
    try:
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"system_instruction": system_instruks} if system_instruks else None
        )
        return response.text
    except Exception as e:
        return f"Feil under Gemini-generering: {e}"

def generer_openai(prompt, system_instruks):
    if not client_openai:
        return "OpenAI API-nøkkel mangler eller klienten feilet."
    try:
        meldinger = []
        if system_instruks:
            meldinger.append({"role": "system", "content": system_instruks})
        meldinger.append({"role": "user", "content": prompt})
        
        response = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=meldinger
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Feil under OpenAI-generering: {e}"

def generer_anthropic(prompt, system_instruks):
    if not client_anthropic:
        return "Anthropic API-nøkkel mangler eller klienten feilet."
    try:
        kwargs = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_instruks:
            kwargs["system"] = system_instruks
            
        response = client_anthropic.messages.create(**kwargs)
        return response.content[0].text
    except Exception as e:
        return f"Feil under Anthropic-generering: {e}"


# 3. --- BASE64 ENCODING FOR SIKKER BAKGRUNN ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

bg_base64 = get_base64_image("Svart lædertekstur med uendelighetssymboler.png")

# Bygg bakgrunns-CSS basert på om bildet finnes eller ikke
if bg_base64:
    bg_style = f"background-image: url('data:image/png;base64,{bg_base64}'); background-size: cover; background-attachment: fixed;"
else:
    bg_style = "background-color: #0b0c10;"

# 4. --- AVANSERT OCTACORE STYLING ---
st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
    /* Global styling og lærbakgrunn */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        font-family: 'Montserrat', sans-serif;
        {bg_style}
        color: #e4e6eb;
    }}
    
    /* Gjør sidepanelet semitransparent og mørkt */
    [data-testid="stSidebar"] {{
        background-color: rgba(10, 12, 16, 0.88) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }}
    
    /* Input-felter */
    textarea {{
        background-color: rgba(20, 24, 30, 0.75) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        backdrop-filter: blur(5px);
    }}
    
    /* Primærknapp med OctaCore signaturglow */
    .stButton>button {{
        background: linear-gradient(135deg, #1f6feb 0%, #104ba3 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2.2rem !important;
        font-weight: 600 !important;
        font-family: 'Montserrat', sans-serif;
        box-shadow: 0 4px 15px rgba(31, 111, 235, 0.25) !important;
        transition: all 0.25s ease !important;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(31, 111, 235, 0.45) !important;
        background: linear-gradient(135deg, #388bfd 0%, #1f6feb 100%) !important;
    }}
    
    /* Glassmorfiske paneler for AI-svarene */
    .glass-card {{
        background: rgba(18, 22, 28, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }}
    
    /* Profilstriper på kortene */
    .brand-line {{
        height: 4px;
        width: 45px;
        border-radius: 2px;
        margin-bottom: 0.8rem;
    }}
    .gemini-line {{ background-color: #4285F4; box-shadow: 0 0 10px rgba(66, 133, 244, 0.5); }}
    .openai-line {{ background-color: #10a37f; box-shadow: 0 0 10px rgba(16, 163, 127, 0.5); }}
    .anthropic-line {{ background-color: #d97706; box-shadow: 0 0 10px rgba(217, 119, 6, 0.5); }}
    
    .model-title {{
        font-weight: 600;
        font-size: 1.2rem;
        color: #ffffff;
    }}
    .model-sub {{
        font-size: 0.85rem;
        color: #8b949e;
        margin-bottom: 0.5rem;
    }}
    </style>
""", unsafe_allow_html=True)


# 5. --- SIDEBAR INITIALISERING ---
with st.sidebar:
    # Henter logoen lokalt fra mappen
    if os.path.exists("OctaCore_logo_transparent_white_text.jpg"):
        st.image("OctaCore_logo_transparent_white_text.jpg", use_container_width=True)
    else:
        st.title("OctaCore AI")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🔑 System Status")
    st.markdown("---")
    st.write("🔹 **Google Gemini:**", "🟢 Aktiv" if client_gemini else "🔴 Av")
    st.write("🔹 **OpenAI:**", "🟢 Aktiv" if client_openai else "🔴 Av")
    st.write("🔹 **Anthropic Claude:**", "🟢 Aktiv" if client_anthropic else "🔴 Av")


# 6. --- BRUKERGRENSESNITT ---
st.title("OctaCore AI Trio Router")
st.markdown("<p style='color: #8b949e; font-size: 1.1rem; margin-top: -15px;'>Fler-modell distribusjon for avansert analyse</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.container():
    system_prompt = st.text_area(
        "⚙️ Systeminstruksjoner (Valgfritt):", 
        placeholder="Definer oppførsel, tone eller begrensninger for AI-modellene...",
        key="system_prompt"
    )
    
    user_prompt = st.text_area(
        "💬 Skriv inn din prompt eller oppgave:", 
        placeholder="Hva ønsker du at OctaCore skal løse for deg i dag?",
        height=120,
        key="user_prompt"
    )

col_btn1, _ = st.columns([1, 5])
with col_btn1:
    kjor_knapp = st.button("Fyr løs 🚀", type="primary")

st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)


# 7. --- GENERERING OG VISNING ---
if kjor_knapp:
    if not user_prompt.strip():
        st.warning("Vennligst skriv inn en prompt før du kjører.")
    else:
        kol_gemini, kol_openai, kol_anthropic = st.columns(3)
        
        # COLUMN 1: Gemini
        with kol_gemini:
            st.markdown("""
                <div class="glass-card">
                    <div class="brand-line gemini-line"></div>
                    <div class="model-title">Google Gemini</div>
                    <div class="model-sub">gemini-2.5-flash</div>
                </div>
            """, unsafe_allow_html=True)
            with st.spinner("Tenker..."):
                svar_gemini = generer_gemini(user_prompt, system_prompt)
                st.markdown(svar_gemini)
                
        # COLUMN 2: OpenAI
        with kol_openai:
            st.markdown("""
                <div class="glass-card">
                    <div class="brand-line openai-line"></div>
                    <div class="model-title">OpenAI</div>
                    <div class="model-sub">gpt-4o-mini</div>
                </div>
            """, unsafe_allow_html=True)
            with st.spinner("Tenker..."):
                svar_openai = generer_openai(user_prompt, system_prompt)
                st.markdown(svar_openai)
                
        # COLUMN 3: Anthropic Claude
        with kol_anthropic:
            st.markdown("""
                <div class="glass-card">
                    <div class="brand-line anthropic-line"></div>
                    <div class="model-title">Anthropic Claude</div>
                    <div class="model-sub">claude-sonnet-4-6</div>
                </div>
            """, unsafe_allow_html=True)
            with st.spinner("Tenker..."):
                svar_anthropic = generer_anthropic(user_prompt, system_prompt)
                st.markdown(svar_anthropic)
