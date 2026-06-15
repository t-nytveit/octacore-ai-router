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
            background-color: rgba(15, 18, 23, 0.9) !important;
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
        raise Exception("OpenAI-klient ikke konfigurert.")
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
        raise Exception("Gemini-klient ikke konfigurert.")
    response = client_gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"system_instruction": system_instruks}
    )
    return response.text

def prøv_anthropic(prompt, system_instruks):
    if not client_anthropic:
        raise Exception("Anthropic-klient ikke konfigurert.")
    kwargs = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }
    if system_instruks:
        kwargs["system"] = system_instruks
    response = client_anthropic.messages.create(**kwargs)
    return response.content[0].text


# 5. --- SIDEBAR: SKREDDERSY DIN OCTACORE OCTA ---
with st.sidebar:
    if os.path.exists("OctaCore_logo_transparent_white_text.jpg"):
        st.image("OctaCore_logo_transparent_white_text.jpg", use_container_width=True)
    else:
        st.title("OctaCore AI")
        
    st.markdown("---")
    st.subheader("💎 Konfigurer din Octa")
    
    # Endret terminologi fra Gem til Octa
    octa_name = st.text_input("Gi din Octa et navn:", value="OctaCore Core")
    octa_persona = st.selectbox(
        "Velg primærfokus:",
        ["Balansert (Miks av Gemini & ChatGPT)", "Teknisk arkitekt / Seniorutvikler", "Kreativ sparringspartner"]
    )
    
    custom_instructions = st.text_area(
        "Personlige instrukser for denne Octaen:",
        placeholder="F.eks. 'Hjelp meg å organisere hverdagen', 'Svar alltid strukturert'...",
        height=100
    )
    
    st.markdown("---")
    st.caption(f"Aktiv profil: {octa_name}")


# 6. --- HOVEDSKJERM ---
if os.path.exists("OctaCore_ Elegant design og teknologi.png"):
    st.image("OctaCore_ Elegant design og teknologi.png", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

user_prompt = st.text_area(
    f"Hva kan {octa_name} løse for deg i dag?", 
    placeholder="Skriv din oppgave eller ditt spørsmål her...",
    height=120,
    key="user_prompt"
)

col_btn, _ = st.columns([1, 4])
with col_btn:
    kjor_knapp = st.button("Fyr løs 🚀", type="primary")


# 7. --- SKJULT SMART-RUTER MED AUTOMATISK RESEVE (FAILOVER) ---
if kjor_knapp:
    if not user_prompt.strip():
        st.warning("Vennligst skriv inn en melding først.")
    else:
        # Bygg systeminstruksen basert på Octa-konfigurasjonen
        final_system_instruction = DEFAULT_SYSTEM
        if octa_persona == "Teknisk arkitekt / Seniorutvikler":
            final_system_instruction += " Fokuser ekstremt tungt på nøyaktig kode, back-end arkitektur og beste praksis."
        elif octa_persona == "Kreativ sparringspartner":
            final_system_instruction += " Vær utforskende, kom med innovative ideer og tenk utenfor boksen."
            
        if custom_instructions.strip():
            final_system_instruction += f" Ytterligere brukerinstruks: {custom_instructions}"

        with st.spinner(f"{octa_name} behandler forespørselen..."):
            svar_endelig = None
            feilmeldinger = []

            # Trinn 1: Definer rekkefølgen motorene skal forsøkes basert på oppgaven
            # Hvis det handler om koding eller teknisk fokus, prioriterer vi OpenAI -> Anthropic -> Gemini
            if "kode" in user_prompt.lower() or "arkitektur" in user_prompt.lower() or octa_persona == "Teknisk arkitekt / Seniorutvikler":
                rekkefølge = [("OpenAI", prøv_openai), ("Anthropic Claude", prøv_anthropic), ("Google Gemini", prøv_gemini)]
            else:
                # Standard oppsett: Gemini -> OpenAI -> Anthropic
                rekkefølge = [("Google Gemini", prøv_gemini), ("OpenAI", prøv_openai), ("Anthropic Claude", prøv_anthropic)]

            # Trinn 2: Kjør gjennom rekkefølgen til en av dem leverer
            for navn, motor_funksjon in rekkefølge:
                try:
                    svar_endelig = motor_funksjon(user_prompt, final_system_instruction)
                    if svar_endelig:
                        break # Vi har et gyldig svar, avbryt loopen!
                except Exception as e:
                    feilmeldinger.append(f"{navn} feilet.")
                    continue # Prøv neste motor i rekken automatisk

            # Trinn 3: Hvis alt mot formodning feilet, gi en kontrollert melding
            if not svar_endelig:
                svar_endelig = "OctaCore AI opplever for øyeblikket høy trafikk på sine ruter-noder. Vennligst sjekk API-saldoene dine eller prøv igjen om et øyeblikk."

            # Presenter det ferdige, strømlinjeformede svaret
            st.markdown("---")
            st.markdown(f"### ✨ Svar fra {octa_name}")
            st.markdown(svar_endelig)
