import streamlit as st
import os

# Sett opp sidetittel og layout aller først
st.set_page_config(
    page_title="OctaCore AI Router",
    page_icon="🤖",
    layout="wide"
)

# Hent API-nøkler trygt fra Streamlit Secrets
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY")

# Initialiserer klienter basert på tilgjengelige nøkler
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
            "model": "claude-3-5-sonnet-latest",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_instruks:
            kwargs["system"] = system_instruks
            
        response = client_anthropic.messages.create(**kwargs)
        return response.content[0].text
    except Exception as e:
        return f"Feil under Anthropic-generering: {e}"

# --- Custom Styling (Mørkt OctaCore-tema) ---
st.markdown("""
    <style>
    .main {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .stButton>button {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #30363d;
        border-color: #8b949e;
        color: #ffffff;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .model-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .gemini-header { color: #4285F4; font-weight: bold; font-size: 1.2rem; }
    .openai-header { color: #10a37f; font-weight: bold; font-size: 1.2rem; }
    .anthropic-header { color: #d97706; font-weight: bold; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

# --- Brukergrensesnitt ---
st.title("🤖 OctaCore AI Trio Router")
st.subheader("Send én prompt samtidig til Gemini, OpenAI og Anthropic")

# Inputfelter
with st.container():
    system_prompt = st.text_area(
        "Systeminstruksjoner (valgfritt - setter oppførsel for AI-ene):", 
        placeholder="F.eks. 'Du er en pirkete seniorutvikler som svarer kort.'",
        key="system_prompt"
    )
    
    user_prompt = st.text_area(
        "Skriv inn din prompt / oppgave her:", 
        placeholder="Hva vil du ha svar på fra de tre modellene?",
        height=150,
        key="user_prompt"
    )

# Knapperad
col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    kjor_knapp = st.button("Fyr løs 🚀", type="primary")

# Generering og visning av resultater
if kjor_knapp:
    if not user_prompt.strip():
        st.warning("Vennligst shrink inn en prompt før du kjører.")
    else:
        # Tre kolonner for de tre modellene
        kol_gemini, kol_openai, kol_anthropic = st.columns(3)
        
        # 1. Gemini
        with kol_gemini:
            st.markdown('<div class="model-box"><span class="gemini-header">Google Gemini</span><br><small>gemini-2.5-flash</small></div>', unsafe_allow_html=True)
            with st.spinner("Gemini tenker..."):
                svar_gemini = generer_gemini(user_prompt, system_prompt)
                st.markdown(svar_gemini)
                
        # 2. OpenAI
        with kol_openai:
            st.markdown('<div class="model-box"><span class="openai-header">OpenAI</span><br><small>gpt-4o-mini</small></div>', unsafe_allow_html=True)
            with st.spinner("OpenAI tenker..."):
                svar_openai = generer_openai(user_prompt, system_prompt)
                st.markdown(svar_openai)
                
        # 3. Anthropic
        with kol_anthropic:
            st.markdown('<div class="model-box"><span class="anthropic-header">Anthropic Claude</span><br><small>claude-3-5-sonnet-latest</small></div>', unsafe_allow_html=True)
            with st.spinner("Claude tenker..."):
                svar_anthropic = generer_anthropic(user_prompt, system_prompt)
                st.markdown(svar_anthropic)

# Statusindikatorer i sidepanelet for å sjekke nøkler
st.sidebar.title("🔑 API Status")
st.sidebar.markdown("---")
st.sidebar.write("Gemini:", "✅ Klar" if client_gemini else "❌ Mangler")
st.sidebar.write("OpenAI:", "✅ Klar" if client_openai else "❌ Mangler")
st.sidebar.write("Anthropic:", "✅ Klar" if client_anthropic else "❌ Mangler")
