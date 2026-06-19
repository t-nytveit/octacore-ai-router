import streamlit as st
import os
import base64
import time
import json
import concurrent.futures
from datetime import datetime

# ============================================================
# 1. APP-KONFIGURASJON OG FILSTIER
# ============================================================

AVATAR_PATH = "OctaCore_icon.png"
MAIN_LOGO_PATH = "OctaCore_logo_transparent_white_text.png"
HERO_LOGO_PATH = "OctaCore_logo_transparent_white_text.png"
BG_PATH = "Svart lædertekstur med uendelighetssymboler.png"

HISTORY_FILE = "octacore_chat_history.json"
PROFILES_DIR = "profiles"
MAX_CONTEXT_MESSAGES = 20

OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-2.5-flash"
ANTHROPIC_MODEL = "claude-sonnet-4-6"

# Standard bruker – bytt til brukervalg når du får flere
AKTIV_BRUKER = "thomas"

st.set_page_config(
    page_title="OctaCore AI",
    page_icon=AVATAR_PATH if os.path.exists(AVATAR_PATH) else "🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. HJELPEFUNKSJONER
# ============================================================

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
        st.error(f"Kunne ikke lagre historikk: {e}")


def profil_sti(brukernavn):
    return os.path.join(PROFILES_DIR, f"{brukernavn}.json")


def last_inn_profil(brukernavn=AKTIV_BRUKER):
    sti = profil_sti(brukernavn)
    if os.path.exists(sti):
        try:
            with open(sti, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def lagre_profil(profil, brukernavn=AKTIV_BRUKER):
    os.makedirs(PROFILES_DIR, exist_ok=True)
    try:
        profil["sist_oppdatert"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(profil_sti(brukernavn), "w", encoding="utf-8") as f:
            json.dump(profil, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Kunne ikke lagre profil: {e}")


def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None


def bygg_meldingsliste(messages, ny_prompt):
    historikk = messages[-(MAX_CONTEXT_MESSAGES - 1):] if len(messages) > MAX_CONTEXT_MESSAGES else messages[:]
    alle = [{"role": m["role"], "content": m["content"]} for m in historikk]
    alle.append({"role": "user", "content": ny_prompt})
    return alle


def meldinger_til_tekst(meldinger):
    tekst = []
    for m in meldinger:
        rolle = "Bruker" if m["role"] == "user" else "OctaCore"
        tekst.append(f"{rolle}: {m['content']}")
    return "\n\n".join(tekst)


def trygg_json_parse(text):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass
    return None


# ============================================================
# 3. BRUKER-PROFIL, LÆRING OG RATING
# ============================================================

def bygg_profil_instruks(profil):
    if not profil:
        return ""
    deler = []
    navn = profil.get("navn", "")
    if navn:
        deler.append(f"Du snakker med {navn}.")
    fagbakgrunn = profil.get("fagbakgrunn", "")
    if fagbakgrunn:
        deler.append(f"Fagbakgrunn: {fagbakgrunn}.")
    if profil.get("ønsker_komplette_filer"):
        deler.append("Lever ALLTID komplette kodefiler uten forkortelser eller '# resten er uendret'.")
    if profil.get("foretrukket_språk") == "norsk":
        deler.append("Svar alltid på norsk.")
    if profil.get("teknisk_dybde") == "høy":
        deler.append("Gi teknisk dybde og grundige forklaringer.")
    preferanser = profil.get("preferanser", [])
    if preferanser:
        deler.append("Brukerens preferanser: " + ", ".join(preferanser) + ".")
    mønstre = profil.get("lærte_mønstre", {})
    if mønstre.get("foretrekker_fusion_på_kode"):
        deler.append("Brukeren foretrekker Fusion-analyse på kodeoppgaver.")
    if mønstre.get("foretrekker_kort_svar"):
        deler.append("Hold svarene konsise.")
    elif mønstre.get("foretrekker_langt_svar"):
        deler.append("Gi grundige og fullstendige svar.")

    # Legg til rating-innsikt hvis nok data
    scores = profil.get("engine_scores", {})
    beste_engine = None
    beste_snitt = 0
    for engine, data in scores.items():
        if data.get("antall", 0) >= 3 and data.get("snitt", 0) > beste_snitt:
            beste_snitt = data["snitt"]
            beste_engine = engine
    if beste_engine and beste_snitt >= 4.0:
        deler.append(f"Brukeren er mest fornøyd med {beste_engine}-svar (snitt {beste_snitt:.1f}/5).")

    return " ".join(deler)


def oppdater_rating(profil, engine, rating):
    """Lagrer brukerens stjerne-rating for en gitt engine."""
    scores = profil.setdefault("engine_scores", {})
    if engine not in scores:
        scores[engine] = {"total": 0, "antall": 0, "snitt": 0}
    scores[engine]["total"] += rating
    scores[engine]["antall"] += 1
    scores[engine]["snitt"] = round(scores[engine]["total"] / scores[engine]["antall"], 2)
    return profil


def oppdater_profil_etter_svar(profil, task_type, valgt_engine, user_prompt):
    if not profil:
        return profil
    stats = profil.setdefault("statistikk", {})
    stats["totalt_antall_meldinger"] = stats.get("totalt_antall_meldinger", 0) + 1
    stats[f"{task_type}_meldinger"] = stats.get(f"{task_type}_meldinger", 0) + 1
    stats[f"{valgt_engine}_brukt"] = stats.get(f"{valgt_engine}_brukt", 0) + 1

    mønstre = profil.setdefault("lærte_mønstre", {})
    totalt = stats.get("totalt_antall_meldinger", 1)
    kode_meldinger = stats.get("code_meldinger", 0)

    komplett_ord = ["komplett", "hele filen", "fullstendig", "ikke forkort", "vis alt"]
    if any(ord_ in user_prompt.lower() for ord_ in komplett_ord):
        mønstre["ber_ofte_om_komplett_fil"] = True
        profil["ønsker_komplette_filer"] = True

    if totalt >= 5:
        smart_andel = stats.get("smart_fallback_brukt", 0) / totalt
        mønstre["foretrekker_kort_svar"] = smart_andel > 0.8
        mønstre["foretrekker_langt_svar"] = smart_andel < 0.3

    # Lær engine-preferanse basert på rating (kvalitet, ikke frekvens)
    scores = profil.get("engine_scores", {})
    fusion_score = scores.get("fusion", {}).get("snitt", 0)
    fusion_antall = scores.get("fusion", {}).get("antall", 0)
    dual_score = scores.get("dual_review", {}).get("snitt", 0)
    dual_antall = scores.get("dual_review", {}).get("antall", 0)

    # Krev minst 2 ratings før vi lærer – unngår å konkludere for tidlig
    if fusion_antall >= 2:
        mønstre["foretrekker_fusion_på_kode"] = fusion_score >= 4.3
    if dual_antall >= 2:
        mønstre["foretrekker_dual_review_på_kode"] = dual_score >= 4.3

    return profil


def juster_engine_basert_på_profil(valgt_engine, task_type, profil):
    if not profil:
        return valgt_engine
    mønstre = profil.get("lærte_mønstre", {})
    if task_type == "code" and mønstre.get("foretrekker_fusion_på_kode"):
        return "fusion"
    if task_type == "code" and mønstre.get("foretrekker_dual_review_på_kode"):
        return "dual_review"
    return valgt_engine


# ============================================================
# 4. API-KLIENTER
# ============================================================

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
        client_gemini = None

if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        client_openai = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        client_openai = None

if ANTHROPIC_API_KEY:
    try:
        from anthropic import Anthropic
        client_anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
    except Exception:
        client_anthropic = None


# ============================================================
# 5. VISUELL STYLING
# ============================================================

bg_base64 = get_base64_image(BG_PATH)

if bg_base64:
    st.markdown(f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(rgba(5, 7, 12, 0.58), rgba(5, 7, 12, 0.84)),
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
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebarUserContent"] { padding-top: 0.8rem !important; }

.octa-hero {
    margin: 0 auto 2rem auto;
    padding: 2.4rem 2rem 1.8rem 2rem;
    text-align: center;
    border-radius: 30px;
    background: linear-gradient(145deg, rgba(10, 13, 20, 0.72), rgba(29, 32, 42, 0.42));
    border: 1px solid rgba(255, 215, 120, 0.18);
    box-shadow: 0 0 60px rgba(255, 196, 64, 0.07), 0 20px 60px rgba(0,0,0,0.36), inset 0 0 40px rgba(255,255,255,0.028);
    backdrop-filter: blur(18px);
}
.octa-hero-logo {
    width: min(520px, 90%);
    filter: drop-shadow(0 0 18px rgba(255,196,64,0.20)) drop-shadow(0 0 40px rgba(255,196,64,0.12));
}
.octa-subtitle { margin-top: 0.2rem; color: rgba(255,255,255,0.72); font-size: 1rem; letter-spacing: 0.02em; }
.octa-badges { margin-top: 1.25rem; display: flex; justify-content: center; flex-wrap: wrap; gap: 0.55rem; }
.octa-badges span {
    padding: 0.4rem 0.78rem; border-radius: 999px;
    background: rgba(255,255,255,0.065); border: 1px solid rgba(255,255,255,0.11);
    color: rgba(255,255,255,0.84); font-size: 0.78rem;
}

[data-testid="stChatMessage"] {
    border-radius: 24px !important; padding: 1.05rem 1.15rem !important;
    margin-bottom: 1rem !important; background: rgba(12, 15, 21, 0.76) !important;
    border: 1px solid rgba(255,255,255,0.085) !important;
    box-shadow: 0 16px 42px rgba(0,0,0,0.26); backdrop-filter: blur(16px);
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li {
    color: rgba(255,255,255,0.92) !important; font-size: 1.02rem !important; line-height: 1.65 !important;
}
[data-testid="stChatMessage"] code {
    color: #ffd166 !important; background-color: rgba(0,0,0,0.42) !important;
    padding: 0.18rem 0.38rem !important; border-radius: 6px !important;
}
[data-testid="stChatMessage"] pre {
    background-color: rgba(0,0,0,0.50) !important; border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

.model-tag {
    display: inline-block; margin-top: 0.55rem; padding: 0.32rem 0.7rem;
    border-radius: 999px; background: rgba(255,255,255,0.065);
    border: 1px solid rgba(255,255,255,0.09); font-size: 0.74rem; font-weight: 600;
}
.model-tag-gemini { color: #7db7ff !important; }
.model-tag-openai { color: #62e6a8 !important; }
.model-tag-anthropic { color: #ffbd72 !important; }
.model-tag-fusion { color: #fff1a6 !important; border-color: rgba(255,215,120,0.30) !important; }

.profil-tag {
    display: inline-block; margin-top: 0.4rem; padding: 0.28rem 0.65rem;
    border-radius: 999px; background: rgba(255,215,120,0.08);
    border: 1px solid rgba(255,215,120,0.20); color: rgba(255,215,120,0.80) !important;
    font-size: 0.72rem; font-weight: 500;
}

.rating-container {
    display: flex; gap: 0.4rem; margin-top: 0.6rem; align-items: center;
}
.rating-label {
    color: rgba(255,255,255,0.45); font-size: 0.72rem; margin-right: 0.2rem;
}

.stSidebar .stButton>button {
    width: 100% !important; text-align: left !important; justify-content: flex-start !important;
    background: rgba(255,255,255,0.035) !important; border: 1px solid rgba(255,255,255,0.075) !important;
    color: rgba(255,255,255,0.82) !important; margin-bottom: 0.35rem !important;
    font-size: 0.86rem !important; padding: 0.48rem 0.78rem !important; border-radius: 13px !important;
}
.stSidebar .stButton>button:hover {
    background: rgba(255,215,120,0.09) !important;
    border-color: rgba(255,215,120,0.24) !important; color: #ffffff !important;
}
.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #d6a93d, #fff1a6) !important;
    color: #0b0d12 !important; border: none !important; font-weight: 700 !important;
    border-radius: 14px !important; box-shadow: 0 10px 28px rgba(214,169,61,0.22);
}
div[data-testid="stTextInput"] input, textarea, div[data-baseweb="select"] {
    background-color: rgba(16,19,27,0.86) !important;
    color: rgba(255,255,255,0.90) !important; border-radius: 13px !important;
}
[data-testid="stChatInput"] {
    background: rgba(8,10,15,0.86) !important;
    border-top: 1px solid rgba(255,255,255,0.06); backdrop-filter: blur(18px);
}
[data-testid="stChatInput"] textarea {
    border-radius: 999px !important; border: 1px solid rgba(255,215,120,0.18) !important;
    background: rgba(16,19,27,0.94) !important; color: white !important;
}
</style>
""", unsafe_allow_html=True)


def render_hero():
    logo_base64 = get_base64_image(HERO_LOGO_PATH)
    if logo_base64:
        st.markdown(f"""
        <div class="octa-hero">
            <img src="data:image/png;base64,{logo_base64}" class="octa-hero-logo">
            <div class="octa-subtitle">Din private AI-partner Engine. Drevet av OpenAI, Gemini og Claude.</div>
            <div class="octa-badges">
                <span>⚡ Smart Router</span>
                <span>🔍 Dual Review</span>
                <span>🔥 OctaCore Fusion</span>
                <span>🧠 Adaptiv profil</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 6. SYSTEMINSTRUKSER
# ============================================================

DEFAULT_SYSTEM = (
    "Du er OctaCore AI, en eksklusiv, dypt reflektert og menneskelig AI-partner utviklet av OctaCore. "
    "Du skal ALDRI svare i form av stive, upersonlige rapporter eller generiske IT-konsulent-evalueringer. "
    "Snakk som en levende, skarp og engasjert samtalepartner og teknologipartner på feilfri norsk. "
    "Vær konkret, ærlig og nyttig. Når du gir kode, må du prioritere korrekthet over pen formulering."
)

CLASSIFIER_SYSTEM = "Du er OctaCore sin router-klassifiserer. Svar KUN som gyldig JSON uten forklaring."

CLASSIFIER_PROMPT_TEMPLATE = """
Analyser brukerens siste melding og klassifiser oppgaven.

Returner KUN JSON med denne strukturen:
{{
  "task_type": "code|design|writing|strategy|general",
  "complexity": "low|medium|high",
  "recommended_engine": "smart_fallback|dual_review|fusion",
  "reason": "kort forklaring"
}}

Regler:
- code = programmering, debugging, API, database, arkitektur, Streamlit, Python, JavaScript.
- design = UI, UX, logo, layout, visuell fremstilling.
- writing = tekst, e-post, SoMe, formulering.
- strategy = forretningsidé, produktstrategi, arkitekturvalg, roadmap.
- general = vanlig spørsmål eller samtale.
- low/medium/high = kompleksitet.
- Fusion kun ved reelt komplekse oppgaver.

Siste brukerprompt:
{prompt}
"""


# ============================================================
# 7. SKJULTE MODELLKALL
# ============================================================

def kall_openai_skjult(prompt, system_instruks="Du er en teknisk AI-spesialist.", temperature=0.5, max_tokens=None):
    if not client_openai:
        raise Exception("OpenAI er ikke tilgjengelig.")
    kwargs = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "system", "content": system_instruks}, {"role": "user", "content": prompt}],
        "temperature": temperature
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    res = client_openai.chat.completions.create(**kwargs)
    return res.choices[0].message.content


def kall_anthropic_skjult(prompt, system_instruks="Du er en back-end kodeekspert.", temperature=0.5, max_tokens=1800):
    if not client_anthropic:
        raise Exception("Anthropic er ikke tilgjengelig.")
    res = client_anthropic.messages.create(
        model=ANTHROPIC_MODEL, max_tokens=max_tokens, system=system_instruks,
        messages=[{"role": "user", "content": prompt}], temperature=temperature
    )
    return res.content[0].text


def kall_gemini_skjult(prompt, system_instruks="Du er en varm og presis AI-koordinator.", temperature=0.5):
    if not client_gemini:
        raise Exception("Gemini er ikke tilgjengelig.")
    from google import genai
    res = client_gemini.models.generate_content(
        model=GEMINI_MODEL,
        contents=[genai.types.Content(role="user", parts=[genai.types.Part.from_text(text=prompt)])],
        config={"system_instruction": system_instruks, "temperature": temperature}
    )
    return res.text


# ============================================================
# 8. STREAMING-FUNKSJONER
# ============================================================

def stream_openai(meldinger, system_instruks):
    if not client_openai:
        raise Exception("OpenAI er ikke tilgjengelig.")
    stream = client_openai.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": system_instruks}] + meldinger,
        temperature=0.7, stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def stream_gemini(meldinger, system_instruks):
    if not client_gemini:
        raise Exception("Gemini er ikke tilgjengelig.")
    from google import genai
    contents_input = []
    for m in meldinger:
        role_label = "user" if m["role"] == "user" else "model"
        contents_input.append(genai.types.Content(role=role_label, parts=[genai.types.Part.from_text(text=m["content"])]))
    response_stream = client_gemini.models.generate_content_stream(
        model=GEMINI_MODEL, contents=contents_input,
        config={"system_instruction": system_instruks, "temperature": 0.7}
    )
    for chunk in response_stream:
        if chunk.text:
            yield chunk.text


def stream_anthropic(meldinger, system_instruks):
    if not client_anthropic:
        raise Exception("Anthropic er ikke tilgjengelig.")
    stream = client_anthropic.messages.stream(
        model=ANTHROPIC_MODEL, max_tokens=1800,
        system=system_instruks, messages=meldinger, temperature=0.7
    )
    with stream as s:
        for text in s.text_stream:
            yield text


def stream_koordineringsrespons(prompt, final_system, foretrukket="gemini"):
    meldinger = [{"role": "user", "content": prompt}]
    if foretrukket == "gemini":
        rekkefolge = [("Google Gemini", stream_gemini), ("OpenAI", stream_openai), ("Anthropic", stream_anthropic)]
    elif foretrukket == "openai":
        rekkefolge = [("OpenAI", stream_openai), ("Google Gemini", stream_gemini), ("Anthropic", stream_anthropic)]
    else:
        rekkefolge = [("Anthropic", stream_anthropic), ("OpenAI", stream_openai), ("Google Gemini", stream_gemini)]
    siste_feil = None
    for _, fn in rekkefolge:
        try:
            for bit in fn(meldinger, final_system):
                yield bit
            return
        except Exception as e:
            siste_feil = e
            continue
    yield f"Jeg klarte ikke å fullføre koordineringssvaret. Feil: {siste_feil}"


# ============================================================
# 9. ROUTER OG KLASSIFISERING
# ============================================================

def heuristisk_klassifisering(prompt):
    tekst = prompt.lower()
    code_words = ["kode", "python", "java", "javascript", "html", "css", "streamlit", "api", "database", "sql", "bug", "feil", "terminal", "github", "router.py", "funksjon", "klasse", "json"]
    design_words = ["design", "ui", "ux", "layout", "visuelt", "logo", "premium", "nettside", "farger", "ikon", "boble", "grensesnitt"]
    writing_words = ["skriv", "formuler", "omformuler", "tekst", "epost", "innlegg", "annonse", "søknad", "referat"]
    strategy_words = ["strategi", "arkitektur", "produkt", "startup", "roadmap", "forretningsmodell", "lansering", "plattform"]
    if any(w in tekst for w in code_words):
        return {"task_type": "code", "complexity": "medium", "recommended_engine": "dual_review", "reason": "Teknisk oppgave."}
    if any(w in tekst for w in design_words):
        return {"task_type": "design", "complexity": "medium", "recommended_engine": "dual_review", "reason": "Design/UI-oppgave."}
    if any(w in tekst for w in strategy_words):
        return {"task_type": "strategy", "complexity": "high", "recommended_engine": "fusion", "reason": "Strategisk oppgave."}
    if any(w in tekst for w in writing_words):
        return {"task_type": "writing", "complexity": "low", "recommended_engine": "smart_fallback", "reason": "Skriveoppgave."}
    return {"task_type": "general", "complexity": "low", "recommended_engine": "smart_fallback", "reason": "Generell samtale."}


def klassifiser_oppgave(prompt):
    heuristikk = heuristisk_klassifisering(prompt)
    if heuristikk["task_type"] != "general":
        return heuristikk
    classifier_prompt = CLASSIFIER_PROMPT_TEMPLATE.format(prompt=prompt)
    try:
        if client_openai:
            raw = kall_openai_skjult(classifier_prompt, CLASSIFIER_SYSTEM, temperature=0.0, max_tokens=250)
            parsed = trygg_json_parse(raw)
            if parsed:
                return parsed
        if client_gemini:
            raw = kall_gemini_skjult(classifier_prompt, CLASSIFIER_SYSTEM, temperature=0.0)
            parsed = trygg_json_parse(raw)
            if parsed:
                return parsed
    except Exception:
        pass
    return heuristikk


def velg_modellrekkefolge(prompt, persona, classification, profil):
    task_type = classification.get("task_type", "general")
    modellprioritet = profil.get("modellprioritet_kode", "") if profil else ""
    if persona == "Teknisk arkitekt / Seniorutvikler" or task_type == "code":
        if modellprioritet == "anthropic":
            return [("Anthropic (claude-sonnet-4-6)", stream_anthropic), ("OpenAI (gpt-4o-mini)", stream_openai), ("Google Gemini (gemini-2.5-flash)", stream_gemini)]
        return [("OpenAI (gpt-4o-mini)", stream_openai), ("Anthropic (claude-sonnet-4-6)", stream_anthropic), ("Google Gemini (gemini-2.5-flash)", stream_gemini)]
    if task_type in ["design", "writing", "strategy"]:
        return [("Google Gemini (gemini-2.5-flash)", stream_gemini), ("OpenAI (gpt-4o-mini)", stream_openai), ("Anthropic (claude-sonnet-4-6)", stream_anthropic)]
    return [("Google Gemini (gemini-2.5-flash)", stream_gemini), ("OpenAI (gpt-4o-mini)", stream_openai), ("Anthropic (claude-sonnet-4-6)", stream_anthropic)]


def bestem_engine(router_mode, classification):
    if router_mode == "⚡ Rask modus (Smart Fallback)":
        return "smart_fallback"
    if router_mode == "🔍 Dual Review (Kvalitetssikret)":
        return "dual_review"
    if router_mode == "🔥 OctaCore Fusion (Fullt samarbeid)":
        return "fusion"
    return classification.get("recommended_engine", "smart_fallback")


# ============================================================
# 10. ENGINE 1: SMART FALLBACK
# ============================================================

def kjor_smart_fallback(meldingsliste, final_system, user_prompt, octa_persona, classification, profil):
    rekkefolge = velg_modellrekkefolge(user_prompt, octa_persona, classification, profil)
    svar_endelig = None
    brukt_modell = None
    feilmeldinger = []
    for modell_navn, stream_fn in rekkefolge:
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
    return svar_endelig, brukt_modell, feilmeldinger


# ============================================================
# 11. ENGINE 2: DUAL REVIEW
# ============================================================

def stream_dual_review(meldingsliste, final_system, user_prompt, classification):
    task_type = classification.get("task_type", "general")
    kontekst = meldinger_til_tekst(meldingsliste)

    if task_type == "code":
        generator_prompt = f"Du skal løse brukerens tekniske oppgave.\nLever komplett kode. Ikke forkort. Prioriter korrekthet.\n\nSamtalekontekst:\n{kontekst}"
        if client_anthropic:
            utkast = kall_anthropic_skjult(generator_prompt, "Du er en senior back-end utvikler.", temperature=0.35, max_tokens=2200)
            generator = "Claude"
        else:
            utkast = kall_openai_skjult(generator_prompt, "Du er en senior fullstack-utvikler.", temperature=0.35)
            generator = "OpenAI"

        review_prompt = f"Brukeroppgave:\n{user_prompt}\n\nUtkast fra {generator}:\n{utkast}\n\nGjør streng teknisk review. Finn bugs. Valider eller korriger."
        if client_openai:
            review = kall_openai_skjult(review_prompt, "Du er en streng seniorarkitekt og kode-reviewer.", temperature=0.25)
            reviewer = "OpenAI"
        else:
            review = kall_anthropic_skjult(review_prompt, "Du er en streng kode-reviewer.", temperature=0.25, max_tokens=1800)
            reviewer = "Claude"

        koordinator_prompt = f"Du er OctaCore AI.\nVis originalkoden hvis reviewen validerer. Vis korrigert versjon hvis feil funnet.\n\nKontekst:\n{kontekst}\nUtkast fra {generator}:\n{utkast}\nReview fra {reviewer}:\n{review}"
        for bit in stream_koordineringsrespons(koordinator_prompt, final_system, foretrukket="openai"):
            yield bit
    else:
        if client_openai:
            utkast = kall_openai_skjult(f"Lag et solid førsteutkast.\n\nKontekst:\n{kontekst}", "Du er en presis problemløser.", temperature=0.55)
            generator = "OpenAI"
        else:
            utkast = kall_gemini_skjult(f"Lag et solid førsteutkast.\n\nKontekst:\n{kontekst}", "Du er en strategisk AI-partner.", temperature=0.55)
            generator = "Gemini"

        review_prompt = f"Evaluer kritisk:\nOppgave: {user_prompt}\nUtkast: {utkast}\nSe etter: uklarheter, svake argumenter, manglende detaljer."
        if client_anthropic:
            review = kall_anthropic_skjult(review_prompt, "Du er en skarp kritiker.", temperature=0.4)
            reviewer = "Claude"
        else:
            review = kall_openai_skjult(review_prompt, "Du er en skarp kritiker.", temperature=0.4)
            reviewer = "OpenAI"

        koordinator_prompt = f"Du er OctaCore AI. Sy sammen et forbedret sluttresultat.\n\nKontekst:\n{kontekst}\nUtkast fra {generator}:\n{utkast}\nReview fra {reviewer}:\n{review}"
        for bit in stream_koordineringsrespons(koordinator_prompt, final_system, foretrukket="gemini"):
            yield bit


# ============================================================
# 12. ENGINE 3: OCTACORE FUSION
# ============================================================

def stream_fusion(meldingsliste, final_system, user_prompt, classification):
    task_type = classification.get("task_type", "general")
    kontekst = meldinger_til_tekst(meldingsliste)

    if task_type == "code":
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            if client_anthropic:
                futures["claude_code"] = executor.submit(kall_anthropic_skjult, f"Lag den beste tekniske løsningen. Komplett kode.\n\nKontekst:\n{kontekst}", "Du er en senior back-end utvikler.", 0.3, 2600)
            if client_openai:
                futures["openai_arch"] = executor.submit(kall_openai_skjult, f"Analyser brukerens tekniske behov: arkitektur, fallgruver, sikkerhet.\n\nKontekst:\n{kontekst}", "Du er en senior systemarkitekt.", 0.35)
            results = {}
            for key, future in futures.items():
                try:
                    results[key] = future.result(timeout=15)
                except concurrent.futures.TimeoutError:
                    results[key] = f"[{key} svarte ikke innen 15 sekunder – utelatt fra analysen]"
                except Exception as e:
                    results[key] = f"{key} feilet: {e}"

        koordinator_prompt = f"Du er OctaCore AI. Lever sluttresponsen.\nIkke omskriv Claude-koden for stil. Behold hvis ingen feil funnet.\nForklar pedagogisk på norsk.\n\nOppgave: {user_prompt}\nKontekst: {kontekst}\nClaude: {results.get('claude_code', 'ikke tilgjengelig')}\nOpenAI: {results.get('openai_arch', 'ikke tilgjengelig')}"
        for bit in stream_koordineringsrespons(koordinator_prompt, final_system, foretrukket="openai"):
            yield bit

    elif task_type == "design":
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            if client_openai:
                futures["openai_design"] = executor.submit(kall_openai_skjult, f"Lag premium UX/UI-struktur.\n\nKontekst:\n{kontekst}", "Du er en senior UX/UI-arkitekt.", 0.55)
            if client_anthropic:
                futures["claude_critique"] = executor.submit(kall_anthropic_skjult, f"Evaluer designoppgaven: brukervennlighet, enkelhet, fallgruver.\n\nKontekst:\n{kontekst}", "Du er en kritisk produktdesigner.", 0.45, 1800)
            results = {}
            for key, future in futures.items():
                try:
                    results[key] = future.result(timeout=15)
                except concurrent.futures.TimeoutError:
                    results[key] = f"[{key} svarte ikke innen 15 sekunder – utelatt fra analysen]"
                except Exception as e:
                    results[key] = f"{key} feilet: {e}"

        koordinator_prompt = f"Du er OctaCore AI. Sy sammen et premium designforslag.\nOppgave: {user_prompt}\nKontekst: {kontekst}\nOpenAI: {results.get('openai_design', 'ikke tilgjengelig')}\nClaude: {results.get('claude_critique', 'ikke tilgjengelig')}"
        for bit in stream_koordineringsrespons(koordinator_prompt, final_system, foretrukket="gemini"):
            yield bit

    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            if client_anthropic:
                futures["claude"] = executor.submit(kall_anthropic_skjult, f"Gi dyp, kritisk vurdering. Fokuser på risiko og realisme.\n\nKontekst:\n{kontekst}", "Du er en kritisk strateg.", 0.45, 1800)
            if client_openai:
                futures["openai"] = executor.submit(kall_openai_skjult, f"Gi strategisk vurdering: arkitektur, muligheter, neste steg.\n\nKontekst:\n{kontekst}", "Du er en senior produktarkitekt.", 0.45)
            if client_gemini:
                futures["gemini"] = executor.submit(kall_gemini_skjult, f"Gi varm, menneskelig vurdering. Fokuser på brukerens intensjon.\n\nKontekst:\n{kontekst}", "Du er en varm AI-partner.", 0.6)
            results = {}
            for key, future in futures.items():
                try:
                    results[key] = future.result(timeout=15)
                except concurrent.futures.TimeoutError:
                    results[key] = f"[{key} svarte ikke innen 15 sekunder – utelatt fra analysen]"
                except Exception as e:
                    results[key] = f"{key} feilet: {e}"

        koordinator_prompt = f"Du er OctaCore AI. Sy sammen ett helhetlig svar. Ikke tre separate AI-svar.\nOppgave: {user_prompt}\nKontekst: {kontekst}\nClaude: {results.get('claude', 'ikke tilgjengelig')}\nOpenAI: {results.get('openai', 'ikke tilgjengelig')}\nGemini: {results.get('gemini', 'ikke tilgjengelig')}"
        for bit in stream_koordineringsrespons(koordinator_prompt, final_system, foretrukket="gemini"):
            yield bit


# ============================================================
# 13. SESSION STATE
# ============================================================

if "all_chats" not in st.session_state:
    st.session_state.all_chats = last_inn_historikk()
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "rename_id" not in st.session_state:
    st.session_state.rename_id = None
if "bruker_profil" not in st.session_state:
    st.session_state.bruker_profil = last_inn_profil(AKTIV_BRUKER)


# ============================================================
# 14. SIDEBAR
# ============================================================

with st.sidebar:
    if os.path.exists(MAIN_LOGO_PATH):
        st.image(MAIN_LOGO_PATH, use_container_width=True)
    else:
        st.title("OctaCore AI")

    profil = st.session_state.bruker_profil
    if profil.get("navn"):
        stats = profil.get("statistikk", {})
        totalt = stats.get("totalt_antall_meldinger", 0)
        scores = profil.get("engine_scores", {})
        beste = max(scores.items(), key=lambda x: x[1].get("snitt", 0)) if scores else None
        beste_tekst = f" · ⭐ {beste[1]['snitt']:.1f} ({beste[0].replace('_', ' ')})" if beste and beste[1].get("antall", 0) >= 2 else ""
        st.markdown(f'<div class="profil-tag">👤 {profil["navn"]} · {totalt} meldinger{beste_tekst}</div>', unsafe_allow_html=True)

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
                    if st.button("✏️", key=f"ren_{chat_id}", help="Gi ny tittel"):
                        st.session_state.rename_id = chat_id
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{chat_id}", help="Slett"):
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
    st.subheader("🚀 OctaCore Engine")
    router_mode = st.selectbox(
        "Velg prosesseringsnivå:",
        ["🧠 Adaptiv modus (OctaCore velger)", "⚡ Rask modus (Smart Fallback)", "🔍 Dual Review (Kvalitetssikret)", "🔥 OctaCore Fusion (Fullt samarbeid)"],
        help="Adaptiv modus klassifiserer oppgaven automatisk."
    )
    vis_router_info = st.toggle("Vis router-analyse", value=True)

    st.markdown("---")
    st.subheader("⚙️ Innstillinger")
    octa_name = st.text_input("Gi din Octa et navn:", value=profil.get("navn", "OctaCore"))
    octa_persona = st.selectbox("Velg primærfokus:", ["Balansert (Varm & Reflektert)", "Teknisk arkitekt / Seniorutvikler", "Kreativ sparringspartner"])
    custom_instructions = st.text_area("Personlige instrukser:", placeholder="F.eks. 'Svar alltid med fullstendig kode'...", height=80)

    # Rating-oversikt i sidebar
    scores = profil.get("engine_scores", {})
    har_scores = any(v.get("antall", 0) > 0 for v in scores.values())
    if har_scores:
        st.markdown("---")
        st.subheader("📊 Engine-score")
        for engine, data in scores.items():
            if data.get("antall", 0) > 0:
                st.caption(f"{engine.replace('_', ' ').title()}: ⭐ {data['snitt']:.1f} ({data['antall']} ratings)")

    st.markdown("---")
    feil_logg_container = st.container()


# ============================================================
# 15. AKTIV SAMTALE
# ============================================================

active_id = st.session_state.current_chat_id
if active_id and active_id in st.session_state.all_chats:
    messages = st.session_state.all_chats[active_id]["messages"]
else:
    messages = []

if not messages:
    render_hero()


# ============================================================
# 16. VIS HISTORISK CHAT
# ============================================================

for msg_idx, message in enumerate(messages):
    avatar_to_use = AVATAR_PATH if (message["role"] == "assistant" and os.path.exists(AVATAR_PATH)) else None
    with st.chat_message(message["role"], avatar=avatar_to_use):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "model" in message:
            modell = message["model"]
            if "Fusion" in modell or "Dual" in modell or "Council" in modell:
                css = "model-tag-fusion"
            elif "Gemini" in modell:
                css = "model-tag-gemini"
            elif "OpenAI" in modell:
                css = "model-tag-openai"
            else:
                css = "model-tag-anthropic"
            st.markdown(f'<div class="model-tag {css}">⚡ {modell}</div>', unsafe_allow_html=True)

            if message.get("rating"):
                # Allerede ratet – vis stjernen
                st.caption(f"{'⭐' * message['rating']} Din vurdering")
            elif modell != "ukjent":
                # Ikke ratet ennå – vis permanente rating-knapper
                st.caption("Vurder svaret:")
                r_cols = st.columns(5)
                for stjerne in range(1, 6):
                    with r_cols[stjerne - 1]:
                        if st.button(str(stjerne), key=f"rate_{msg_idx}_{stjerne}"):
                            engine_fra_melding = message.get("engine", "smart_fallback")
                            st.session_state.bruker_profil = oppdater_rating(
                                st.session_state.bruker_profil, engine_fra_melding, stjerne
                            )
                            if active_id and active_id in st.session_state.all_chats:
                                st.session_state.all_chats[active_id]["messages"][msg_idx]["rating"] = stjerne
                            lagre_profil(st.session_state.bruker_profil, AKTIV_BRUKER)
                            lagre_historikk(st.session_state.all_chats)
                            st.rerun()


# ============================================================
# 17. SYSTEMINSTRUKS
# ============================================================

def bygg_system_instruks():
    instruks = DEFAULT_SYSTEM
    profil_tillegg = bygg_profil_instruks(st.session_state.bruker_profil)
    if profil_tillegg:
        instruks += " " + profil_tillegg
    if octa_persona == "Teknisk arkitekt / Seniorutvikler":
        instruks += " Fokuser tungt på nøyaktig kode, arkitektur, sikkerhet og beste praksis."
    elif octa_persona == "Kreativ sparringspartner":
        instruks += " Vær utforskende, idérik, varm og konseptuelt sterk."
    if custom_instructions.strip():
        instruks += f" Ekstra regel fra brukeren: {custom_instructions.strip()}"
    return instruks


# ============================================================
# 18. CHAT-INPUT OG ENGINE-KJØRING
# ============================================================

if user_prompt := st.chat_input(f"Snakk med {octa_name}..."):

    tving_omstart_for_tittel = False

    if not active_id:
        active_id = str(int(time.time()))
        st.session_state.current_chat_id = active_id
        clean_title = user_prompt.strip()[:28] + "…" if len(user_prompt.strip()) > 28 else user_prompt.strip()
        st.session_state.all_chats[active_id] = {"title": clean_title or "Ny samtale", "messages": []}
        messages = st.session_state.all_chats[active_id]["messages"]
        tving_omstart_for_tittel = True

    with st.chat_message("user"):
        st.markdown(user_prompt)
    messages.append({"role": "user", "content": user_prompt})

    final_system = bygg_system_instruks()
    meldingsliste = bygg_meldingsliste(messages[:-1], user_prompt)
    classification = klassifiser_oppgave(user_prompt)
    valgt_engine = bestem_engine(router_mode, classification)
    valgt_engine = juster_engine_basert_på_profil(valgt_engine, classification.get("task_type", "general"), st.session_state.bruker_profil)

    kostnad_map = {"smart_fallback": ("lav", "🟢"), "dual_review": ("medium", "🟡"), "fusion": ("høy", "🔴")}
    kostnad_etikett, kostnad_ikon = kostnad_map.get(valgt_engine, ("ukjent", "⚪"))

    if vis_router_info:
        st.caption(f"🧭 Router: `{classification.get('task_type')}` · `{classification.get('complexity')}` · `{valgt_engine}`")
    st.caption(f"{kostnad_ikon} Estimert engine-kostnad: **{kostnad_etikett}**")

    avatar_to_use = AVATAR_PATH if os.path.exists(AVATAR_PATH) else None

    with st.chat_message("assistant", avatar=avatar_to_use):
        svar_endelig = None
        brukt_modell = None
        feilmeldinger = []

        try:
            if valgt_engine == "smart_fallback":
                svar_endelig, brukt_modell, feilmeldinger = kjor_smart_fallback(
                    meldingsliste, final_system, user_prompt, octa_persona, classification, st.session_state.bruker_profil
                )
            elif valgt_engine == "dual_review":
                with st.spinner("🔍 Dual Review: lager utkast og kvalitetssikrer..."):
                    svar_endelig = st.write_stream(stream_dual_review(meldingsliste, final_system, user_prompt, classification))
                brukt_modell = "OctaCore Dual Review"
            elif valgt_engine == "fusion":
                with st.spinner("🔥 OctaCore Fusion: flere eksperter jobber parallelt..."):
                    svar_endelig = st.write_stream(stream_fusion(meldingsliste, final_system, user_prompt, classification))
                brukt_modell = "OctaCore Fusion Council"
            else:
                svar_endelig, brukt_modell, feilmeldinger = kjor_smart_fallback(
                    meldingsliste, final_system, user_prompt, octa_persona, classification, st.session_state.bruker_profil
                )
        except Exception as e:
            feilmeldinger.append(f"⚠️ Engine feilet: {str(e)}")
            try:
                svar_endelig, brukt_modell, fallback_feil = kjor_smart_fallback(
                    meldingsliste, final_system, user_prompt, octa_persona, classification, st.session_state.bruker_profil
                )
                feilmeldinger.extend(fallback_feil)
            except Exception as fallback_error:
                svar_endelig = f"Jeg klarte ikke å fullføre svaret. Feil: {fallback_error}"
                brukt_modell = "ukjent"
                st.markdown(svar_endelig)

        if brukt_modell and brukt_modell != "ukjent":
            if "Fusion" in brukt_modell or "Dual" in brukt_modell or "Council" in brukt_modell:
                css = "model-tag-fusion"
            elif "Gemini" in brukt_modell:
                css = "model-tag-gemini"
            elif "OpenAI" in brukt_modell:
                css = "model-tag-openai"
            else:
                css = "model-tag-anthropic"
            st.markdown(f'<div class="model-tag {css}">⚡ {brukt_modell}</div>', unsafe_allow_html=True)

    if feilmeldinger:
        with feil_logg_container:
            for feil in feilmeldinger:
                st.sidebar.warning(feil)

    messages.append({
        "role": "assistant",
        "content": svar_endelig or "",
        "model": brukt_modell or "ukjent",
        "engine": valgt_engine
    })

    # Stille læring
    st.session_state.bruker_profil = oppdater_profil_etter_svar(
        st.session_state.bruker_profil, classification.get("task_type", "general"), valgt_engine, user_prompt
    )
    lagre_profil(st.session_state.bruker_profil, AKTIV_BRUKER)
    lagre_historikk(st.session_state.all_chats)

    if tving_omstart_for_tittel:
        st.rerun()
