import streamlit as st
import os
import base64
import time
import json

# 1. Sidetittel, layout og miniatyrlogo
AVATAR_PATH = "OctaCore_icon.png"
MAIN_LOGO_PATH = "OctaCore_logo_transparent_white_text.png"
HERO_LOGO_PATH = "OctaCore_ Elegant design og teknologi.png"
BG_PATH = "Svart lædertekstur med uendelighetssymboler.png"

st.set_page_config(
    page_title="OctaCore AI",
    page_icon=AVATAR_PATH if os.path.exists(AVATAR_PATH) else "🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

HISTORY_FILE = "octacore_chat_history.json"
MAX_CONTEXT_MESSAGES = 20


# 2. Hjelpefunksjoner
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


def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None


# 3. API-nøkler
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


# 4. Bakgrunn
bg_base64 = get_base64_image(BG_PATH)

if bg_base64:
    st.markdown(f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(rgba(5, 7, 12, 0.60), rgba(5, 7, 12, 0.82)),
                url('data:image/png;base64,{bg_base64}');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }}

        [data-testid="stHeader"] {{
            background: rgba(5, 7, 12, 0.20) !important;
            backdrop-filter: blur(14px);
        }}
        </style>
    """, unsafe_allow_html=True)


# 5. Premium CSS
st.markdown("""
<style>
.block-container {
    max-width: 980px !important;
    padding-top: 2rem !important;
    padding-bottom: 7rem !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(9, 11, 16, 0.98), rgba(16, 18, 25, 0.96)) !important;
    border-right: 1px solid rgba(255, 215, 120, 0.10);
}

[data-testid="stSidebarNav"] {
    display: none !important;
}

[data-testid="stSidebarUserContent"] {
    padding-top: 0.8rem !important;
}

.octa-hero {
    margin: 0 auto 2rem auto;
    padding: 2.2rem 2rem 1.7rem 2rem;
    text-align: center;
    border-radius: 30px;
    background: linear-gradient(145deg, rgba(10, 13, 20, 0.88), rgba(29, 32, 42, 0.62));
    border: 1px solid rgba(255, 215, 120, 0.20);
    box-shadow:
        0 0 60px rgba(255, 196, 64, 0.08),
        0 20px 60px rgba(0, 0, 0, 0.40),
        inset 0 0 40px rgba(255, 255, 255, 0.035);
    backdrop-filter: blur(18px);
}

.octa-hero-logo {
    width: min(440px, 86%);
    filter: drop-shadow(0 0 28px rgba(255, 196, 64, 0.24));
}

.octa-subtitle {
    margin-top: 0.3rem;
    color: rgba(255,255,255,0.72);
    font-size: 1rem;
    letter-spacing: 0.02em;
}

.octa-badges {
    margin-top: 1.25rem;
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.octa-badges span {
    padding: 0.4rem 0.78rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.065);
    border: 1px solid rgba(255,255,255,0.11);
    color: rgba(255,255,255,0.84);
    font-size: 0.78rem;
    box-shadow: inset 0 0 16px rgba(255,255,255,0.025);
}

[data-testid="stChatMessage"] {
    border-radius: 24px !important;
    padding: 1.05rem 1.15rem !important;
    margin-bottom: 1rem !important;
    background: rgba(12, 15, 21, 0.76) !important;
    border: 1px solid rgba(255,255,255,0.085) !important;
    box-shadow: 0 16px 42px rgba(0,0,0,0.26);
    backdrop-filter: blur(16px);
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li {
    color: rgba(255,255,255,0.92) !important;
    font-size: 1.02rem !important;
    line-height: 1.65 !important;
}

[data-testid="stChatMessage"] code {
    color: #ffd166 !important;
    background-color: rgba(0, 0, 0, 0.42) !important;
    padding: 0.18rem 0.38rem !important;
    border-radius: 6px !important;
}

[data-testid="stChatMessage"] pre {
    background-color: rgba(0, 0, 0, 0.50) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

.model-tag {
    display: inline-block;
    margin-top: 0.55rem;
    padding: 0.32rem 0.7rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.065);
    border: 1px solid rgba(255,255,255,0.09);
    font-size: 0.74rem;
    font-weight: 600;
    font-style: normal !important;
    letter-spacing: 0.01em;
}

.model-tag-gemini { color: #7db7ff !important; }
.model-tag-openai { color: #62e6a8 !important; }
.model-tag-anthropic { color: #ffbd72 !important; }

.stSidebar .stButton>button {
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    background: rgba(255,255,255,0.035) !important;
    border: 1px solid rgba(255,255,255,0.075) !important;
    color: rgba(255,255,255,0.82) !important;
    margin-bottom: 0.35rem !important;
    font-size: 0.86rem !important;
    padding: 0.48rem 0.78rem !important;
    border-radius: 13px !important;
}

.stSidebar .stButton>button:hover {
    background: rgba(255, 215, 120, 0.09) !important;
    border-color: rgba(255, 215, 120, 0.24) !important;
    color: #ffffff !important;
}

.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #d6a93d, #fff1a6) !important;
    color: #0b0d12 !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 14px !important;
    box-shadow: 0 10px 28px rgba(214, 169, 61, 0.22);
}

div[data-testid="stTextInput"] input,
textarea,
div[data-baseweb="select"] {
    background-color: rgba(16, 19, 27, 0.86) !important;
    color: rgba(255,255,255,0.90) !important;
    border-radius: 13px !important;
}

[data-testid="stChatInput"] {
    background: rgba(8, 10, 15, 0.86) !important;
    border-top: 1px solid rgba(255,255,255,0.06);
    backdrop-filter: blur(18px);
}

[data-testid="stChatInput"] textarea {
    border-radius: 999px !important;
    border: 1px solid rgba(255, 215, 120, 0.18) !important;
    background: rgba(16, 19, 27, 0.94) !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)


# 6. Hero
def render_hero():
    logo_base64 = get_base64_image(HERO_LOGO_PATH) or get_base64_image(MAIN_LOGO_PATH)

    if logo_base64:
        st.markdown(f"""
        <div class="octa-hero">
            <img src="data:image/png;base64,{logo_base64}" class="octa-hero-logo">
            <div class="octa-subtitle">
                Din private AI-partner. Bygget på OpenAI, Gemini og Claude.
            </div>
            <div class="octa-badges">
                <span>GPT</span>
                <span>Gemini</span>
                <span>Claude</span>
                <span>Smart Router</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# 7. Systeminstruks
DEFAULT_SYSTEM = (
    "Du er OctaCore AI, en eksklusiv, dypt reflektert og menneskelig AI-partner utviklet av OctaCore. "
    "Du skal ALDRI svare i form av stive, upersonlige rapporter eller generiske 'IT-konsulent'-evalueringer. "
    "Unngå unaturlig opplisting og standardiserte fraser som 'Styrker i koden' eller 'Mulige forbedringer' med mindre du blir eksplisitt bedt om en formell rapport. "
    "Snakk i stedet som en levende, skarp og engasjert samtalepartner og teknologipartner. "
    "Når du diskuterer kode, oppgaver eller konsepter, skal du drøfte, reflektere, bruke et flytende hverdagsuttrykk "
    "og ha en naturlig dialog på feilfri norsk. Vis personlighet, dybde og situasjonsforståelse. "
    "Kombiner den intellektuelle tyngden til ChatGPT med den varme, flytende og emosjonelt intelligente sjelen til Gemini."
)


# 8. Kontekst og streaming
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

    stream = client_anthropic.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system_instruks,
        messages=meldinger,
        temperature=0.7
    )

    with stream as s:
        for text in s.text_stream:
            yield text


# 9. Smart modellruter
def velg_modellrekkefolge(prompt, persona):
    tekst = prompt.lower()

    tekniske_ord = [
        "kode", "python", "java", "javascript", "html", "css", "script", "skript",
        "bug", "feil", "feilmelding", "api", "database", "sql", "streamlit",
        "arkitektur", "backend", "frontend", "github", "klasse", "funksjon",
        "router", "app", "terminal", "requirements", "json"
    ]

    kreativ_ord = [
        "ide", "idé", "konsept", "navn", "design", "tekst", "historie",
        "markedsføring", "presentasjon", "skriv", "utkast", "strategi",
        "visuelt", "layout", "logo", "premium"
    ]

    if persona == "Teknisk arkitekt / Seniorutvikler" or any(o in tekst for o in tekniske_ord):
        return [
            ("OpenAI (gpt-4o-mini)", stream_openai),
            ("Anthropic (claude-sonnet-4-6)", stream_anthropic),
            ("Google Gemini (gemini-2.5-flash)", stream_gemini),
        ]

    if any(o in tekst for o in kreativ_ord):
        return [
            ("Google Gemini (gemini-2.5-flash)", stream_gemini),
            ("Anthropic (claude-sonnet-4-6)", stream_anthropic),
            ("OpenAI (gpt-4o-mini)", stream_openai),
        ]

    return [
        ("Google Gemini (gemini-2.5-flash)", stream_gemini),
        ("OpenAI (gpt-4o-mini)", stream_openai),
        ("Anthropic (claude-sonnet-4-6)", stream_anthropic),
    ]


# 10. Session state
if "all_chats" not in st.session_state:
    st.session_state.all_chats = last_inn_historikk()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "rename_id" not in st.session_state:
    st.session_state.rename_id = None


# 11. Sidebar
with st.sidebar:
    if os.path.exists(MAIN_LOGO_PATH):
        st.image(MAIN_LOGO_PATH, use_container_width=True)
    else:
        st.title("OctaCore AI")

    st.markdown("---")

    if st.button("➕ Start ny samtale", type="primary", use_container_width=True):
        st.session_state.current_chat_id = None
        st.session_state.rename_id = None
        st.rerun()

    st.markdown("<br><b>🗂️ Dine samtaler</b>", unsafe_allow_html=True)

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
                    label = f"{'● ' if is_active else ''}💬 {title}"
                    if st.button(label, key=f"btn_{chat_id}"):
                        st.session_state.current_chat_id = chat_id
                        st.session_state.rename_id = None
                        st.rerun()

                with col_rename:
                    if st.button("✎", key=f"ren_{chat_id}", help="Gi ny tittel"):
                        st.session_state.rename_id = chat_id
                        st.rerun()

                with col_del:
                    if st.button("×", key=f"del_{chat_id}", help="Slett denne samtalen"):
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
        [
            "Balansert (Varm & Reflektert)",
            "Teknisk arkitekt / Seniorutvikler",
            "Kreativ sparringspartner"
        ]
    )

    custom_instructions = st.text_area(
        "Personlige instrukser:",
        placeholder="F.eks. 'Svar alltid strukturert'...",
        height=80
    )

    st.markdown("---")
    feil_logg_container = st.container()


# 12. Aktiv samtale
active_id = st.session_state.current_chat_id

if active_id and active_id in st.session_state.all_chats:
    messages = st.session_state.all_chats[active_id]["messages"]
else:
    messages = []


# 13. Vis hero hvis ingen meldinger
if not messages:
    render_hero()


# 14. Vis historisk chat
for message in messages:
    avatar_to_use = AVATAR_PATH if (message["role"] == "assistant" and os.path.exists(AVATAR_PATH)) else None

    with st.chat_message(message["role"], avatar=avatar_to_use):
        st.markdown(message["content"])

        if message["role"] == "assistant" and "model" in message:
            modell = message["model"]
            css = "model-tag-gemini" if "Gemini" in modell else (
                "model-tag-openai" if "OpenAI" in modell else "model-tag-anthropic"
            )
            st.markdown(
                f'<div class="model-tag {css}">⚡ {modell}</div>',
                unsafe_allow_html=True
            )


# 15. Dynamisk systeminstruks
def bygg_system_instruks():
    instruks = DEFAULT_SYSTEM

    if octa_persona == "Teknisk arkitekt / Seniorutvikler":
        instruks += " Fokuser tungt på nøyaktig kode, arkitektur og beste praksis."

    elif octa_persona == "Kreativ sparringspartner":
        instruks += " Vær utforskende, kom med innovative ideer og drøft konseptene åpent og filosofisk."

    if custom_instructions.strip():
        instruks += f" Ekstra regel fra brukeren: {custom_instructions}"

    return instruks


# 16. Chat-input og respons
if user_prompt := st.chat_input(f"Snakk med {octa_name}..."):

    tving_omstart_for_tittel = False

    if not active_id:
        active_id = str(int(time.time()))
        st.session_state.current_chat_id = active_id

        clean_title = user_prompt.strip()[:28] + "…" if len(user_prompt.strip()) > 28 else user_prompt.strip()

        st.session_state.all_chats[active_id] = {
            "title": clean_title or "Ny samtale",
            "messages": []
        }

        messages = st.session_state.all_chats[active_id]["messages"]
        tving_omstart_for_tittel = True

    with st.chat_message("user"):
        st.markdown(user_prompt)

    messages.append({
        "role": "user",
        "content": user_prompt
    })

    final_system = bygg_system_instruks()
    meldingsliste = bygg_meldingsliste(messages[:-1], user_prompt)
    rekkefølge = velg_modellrekkefolge(user_prompt, octa_persona)

    avatar_to_use = AVATAR_PATH if os.path.exists(AVATAR_PATH) else None

    with st.chat_message("assistant", avatar=avatar_to_use):
        svar_endelig = None
        brukt_modell = None
        feilmeldinger = []

        for modell_navn, stream_fn in rekkefølge:
            try:
                svar_endelig = st.write_stream(stream_fn(meldingsliste, final_system))
                brukt_modell = modell_navn
                break

            except Exception as e:
                feilmeldinger.append(f"⚠️ {modell_navn} feilet: {str(e)}")
                continue

        if not svar_endelig:
            svar_endelig = "Jeg opplevde en midlertidig forstyrrelse. Kan du gjenta det?"
            brukt_modell = "ukjent"
            st.markdown(svar_endelig)

        if brukt_modell and brukt_modell != "ukjent":
            css = "model-tag-gemini" if "Gemini" in brukt_modell else (
                "model-tag-openai" if "OpenAI" in brukt_modell else "model-tag-anthropic"
            )

            st.markdown(
                f'<div class="model-tag {css}">⚡ {brukt_modell}</div>',
                unsafe_allow_html=True
            )

    if feilmeldinger:
        with feil_logg_container:
            for feil in feilmeldinger:
                st.sidebar.warning(feil)

    messages.append({
        "role": "assistant",
        "content": svar_endelig,
        "model": brukt_modell or "ukjent"
    })

    lagre_historikk(st.session_state.all_chats)

    if tving_omstart_for_tittel:
        st.rerun()