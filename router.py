import streamlit as st
import os
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


# 3. --- AVANSERT OCTACORE STYLING (CSS Injection) ---
# Vi henter lærteksturen din og bruker den som fast bakgrunn, og lager elegante glasspaneler.
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
    /* Global skrifttype og bakgrunn med lærtekstur */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Montserrat', sans-serif;
        background-image: url('app/static/Svart lædertekstur med uendelighetssymboler.png');
        background-size: cover;
        background-attachment: fixed;
        color: #e4e6eb;
    }
    
    /* Gjør sidepanelet semitransparent og elegant */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 12, 16, 0.85) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Overskrifter og titler */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
        color: #ffffff !important;
    }
    
    /* Tekstområder (Inputs) */
    textarea {
        background-color: rgba(22, 27, 34, 0.7) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        backdrop-filter: blur(4px);
    }
    textarea:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 10px rgba(88, 166, 255, 0.2) !important;
    }
    
    /* Hovedknapp (Fyr løs) - Eksklusiv OctaCore Blå med glød */
    .stButton>button {
        background: linear-gradient(135deg, #1f6feb 0%, #104ba3 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(31, 111, 235, 0.3) !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(31, 111, 235, 0.5) !important;
        background: linear-gradient(135deg, #388bfd 0%, #1f6feb 100%) !important;
    }
    
    /* Modellpaneler med Glassmorfisme-effekt og farget topplinje */
    .glass-card {
        background: rgba(22, 27, 34, 0.65);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(255, 255, 255, 0.15);
    }
    
    /* Branding striper for hver modell */
    .brand-line {
        height: 4px;
        width: 40px;
        border-radius: 2px;
        margin-bottom: 0.8rem;
    }
    .gemini-line { background-color: #4285F4; box-shadow: 0 0 8px #4285F4; }
    .openai-line { background-color: #10a37f; box-shadow: 0 0 8px #10a37f; }
    .anthropic-line { background-color: #d97706; box-shadow: 0 0 8px #d97706; }
    
    .model-title {
        font-weight: 600;
        font-size: 1.15rem;
        color: #ffffff;
        margin-bottom: 0.2rem;
    }
    .model-sub {
        font-size: 0.8rem;
        color: #8b949e;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)


# 4. --- SIDEBAR (Logo & Status) ---
with st.sidebar:
    # Last inn og vis OctaCore-logoen i sidepanelet hvis den eksisterer
    try:
        logo_img = Image.open("OctaCore_logo_transparent_white_text.jpg")
        st.image(logo_img, use_column_width=True)
    except:
        st.title("OctaCore AI")
        
    st.markdown("<br>", unsafe_allow_html=False)
    st.markdown("### 🔑 System Status")
    st.markdown("---")
    
    # Mer elegante statusindikatorer
    st.write("🔹 **Google Gemini:**", "🟢 Aktiv" if client_gemini else "🔴 Utilgjengelig")
    st.write("🔹 **OpenAI:**", "🟢 Aktiv" if client_openai else "🔴 Utilgjengelig")
    st.write("🔹 **Anthropic Claude:**", "🟢 Aktiv" if client_anthropic else "🔴 Utilgjengelig")


# 5. --- HOVEDSIDE HIERARKI ---
st.title("OctaCore AI Trio Router")
st.markdown("<p style='color: #8b949e; font-size: 1.1rem; margin-top: -15px;'>Fler-modell distribusjon for avansert analyse</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Inndatafelt i en ren kontainer
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

# Sentreknapp og oppsett
col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    kjor_knapp = st.button("Fyr løs 🚀", type="primary")

st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)

# 6. --- GENERERING OG GLASSMORFISK VISNING ---
if kjor_knapp:
    if not user_prompt.strip():
        st.warning("Vennligst skriv inn en prompt før du kjører.")
    else:
        # Tre kolonner for resultatene
        kol_gemini, kol_openai, kol_anthropic = st.columns(3)
        
        # COLUMN 1: Google Gemini
        with kol_gemini:
            st.markdown("""
                <div class="glass-card">
                    <div class="brand-line gemini-line"></div>
                    <div class="model-title">Google Gemini</div>
                    <div class="model-sub">gemini-2.5-flash</div>
                </div>
            """, unsafe_allow_html=True)
            with st.spinner("Analyserer via Gemini..."):
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
            with st.spinner("Analyserer via OpenAI..."):
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
            with st.spinner("Analyserer via Claude..."):
                svar_anthropic = generer_anthropic(user_prompt, system_prompt)
                st.markdown(svar_anthropic)
