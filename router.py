import streamlit as st
import os
import base64
from PIL import Image

# 1. Sidetittel og layout
st.set_page_config(
    page_title="OctaCore AI",
    page_icon="🤖",
    layout="centered"  # Sentrert for en renere og mer profesjonell profil
)

# 2. API-nøkler
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")

client_gemini = None
client_openai = None

if GEMINI_API_KEY:
    try:
        from google import genai
        client_gemini = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.sidebar.error(f"Feil ved lasting av Gemini: {e}")

if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        client_openai = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        st.sidebar.error(f"Feil ved lasting av OpenAI: {e}")

# 3. Bakgrunnshåndtering via sikker Base64 (Ingen råtekst på skjermen)
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
            background-color: rgba(15, 18, 23, 0.9) !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# Default systeminstruks som kombinerer egenskapene til Gemini og ChatGPT
DEFAULT_SYSTEM = (
    "Du er OctaCore AI, en eksklusiv og avansert AI-assistent utviklet av OctaCore. "
    "Svarene dine skal kombinere den analytiske presisjonen og strukturen fra ChatGPT, "
    "med den dype kontekstforståelsen, flyten og personlige finessen til Gemini. "
    "Fremstå profesjonell, skarp og direkte, uten unødvendig fylltekst."
)

# 4. --- SIDEBAR: SKREDDERSY DIN OCTACORE GEM ---
with st.sidebar:
    if os.path.exists("OctaCore_logo_transparent_white_text.jpg"):
        st.image("OctaCore_logo_transparent_white_text.jpg", use_container_width=True)
    else:
        st.title("OctaCore AI")
        
    st.markdown("---")
    st.subheader("💎 Konfigurer din Gem")
    
    # Her lager brukeren sin egen definerte assistent
    gem_name = st.text_input("Gi din Gem et navn:", value="OctaCore Core")
    gem_persona = st.selectbox(
        "Velg primærfokus:",
        ["Balansert (Miks av Gemini & ChatGPT)", "Teknisk arkitekt / Seniorutvikler", "Kreativ sparringspartner"]
    )
    
    custom_instructions = st.text_area(
        "Personlige instrukser for denne Gemen:",
        placeholder="F.eks. 'Svar alltid kortfattet på norsk' eller 'Fokuser på ren back-end logikk'...",
        height=100
    )
    
    st.markdown("---")
    st.caption(f"Aktiv profil: {gem_name}")

# 5. --- HOVEDSKJERM ---
# Vis det elegante teknologibildet som en banner på topp hvis det finnes
if os.path.exists("OctaCore_ Elegant design og teknologi.png"):
    st.image("OctaCore_ Elegant design og teknologi.png", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Inntasting (Det oppleves mer som en ren chat-boks nå)
user_prompt = st.text_area(
    f"Hva kan {gem_name} løse for deg i dag?", 
    placeholder="Skriv din oppgave eller ditt spørsmål her...",
    height=120,
    key="user_prompt"
)

col_btn, _ = st.columns([1, 4])
with col_btn:
    kjor_knapp = st.button("Fyr løs 🚀", type="primary")

# 6. --- SKJULT RUTERLOGIKK OG FORENT SVAR ---
if kjor_knapp:
    if not user_prompt.strip():
        st.warning("Vennligst skriv inn en melding først.")
    else:
        # Bygg den endelige bakgrunnsinstruksen basert på valgt Gem-oppsett
        final_system_instruction = DEFAULT_SYSTEM
        if gem_persona == "Teknisk arkitekt / Seniorutvikler":
            final_system_instruction += " Fokuser ekstremt tungt på nøyaktig kode, back-end arkitektur og beste praksis."
        elif gem_persona == "Kreativ sparringspartner":
            final_system_instruction += " Vær utforskende, kom med innovative ideer og tenk utenfor boksen."
            
        if custom_instructions.strip():
            final_system_instruction += f" Ytterligere brukerinstruks: {custom_instructions}"

        with st.spinner(f"Genererer svar fra {gem_name}..."):
            # Bakgrunnsruter: Vi bruker OpenAI for strukturerte/tekniske oppgaver, 
            # eller Gemini hvis det er standard/kreative løsninger.
            svar_endelig = ""
            
            if client_openai and ("kode" in user_prompt.lower() or "arkitektur" in user_prompt.lower() or gem_persona == "Teknisk arkitekt / Seniorutvikler"):
                try:
                    meldinger = [
                        {"role": "system", "content": final_system_instruction},
                        {"role": "user", "content": user_prompt}
                    ]
                    response = client_openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=meldinger
                    )
                    svar_endelig = response.choices[0].message.content
                except Exception as e:
                    svar_endelig = f"Feil under OpenAI-prosessering: {e}"
            
            elif client_gemini:
                try:
                    response = client_gemini.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=user_prompt,
                        config={"system_instruction": final_system_instruction}
                    )
                    svar_endelig = response.text
                except Exception as e:
                    svar_endelig = f"Feil under Gemini-prosessering: {e}"
            else:
                svar_endelig = "Ingen aktive KI-klienter tilgjengelig. Sjekk API-nøklene dine i Secrets."

            # Presenter det ferdige, forente svaret i en ren, lekker blokk
            st.markdown("---")
            st.markdown(f"### ✨ Svar fra {gem_name}")
            st.markdown(svar_endelig)
