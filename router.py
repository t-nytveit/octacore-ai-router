"""
router.py
=========
OctaCore AI Trio Router - v6.0
"""

from __future__ import annotations

import asyncio
import logging
import streamlit as st
from dotenv import load_dotenv
import os
from datetime import datetime
from PIL import Image
import sqlite3

# ---------------------------------------------------------------------------
# Konfigurasjon og database-oppsett
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("octacore_router")

load_dotenv()

# Hent API-nøkler (støtter både lokal .env og Streamlit Secrets på nett)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")

GEMINI_MODEL = "gemini-2.5-flash"
OPENAI_MODEL = "gpt-4o"
DB_FILE = "router_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            prompt TEXT,
            mode TEXT,
            has_image INTEGER,
            draft TEXT,
            critique TEXT,
            final_answer TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(prompt: str, mode: str, has_image: bool, draft: str, critique: str, final_answer: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO history (timestamp, prompt, mode, has_image, draft, critique, final_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, prompt, mode, 1 if has_image else 0, draft, critique, final_answer))
    conn.commit()
    conn.close()

def get_history_from_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, prompt, mode, has_image, draft, critique, final_answer FROM history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    history_list = []
    for row in rows:
        history_list.append({
            "time": row[0],
            "prompt": row[1],
            "mode": row[2],
            "has_image": bool(row[3]),
            "draft": row[4],
            "critique": row[5],
            "final": row[6]
        })
    return history_list

def clear_db_history():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history")
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------------------------
# Klient-builder og asynkrone API-kall
# ---------------------------------------------------------------------------
def _build_clients():
    from anthropic import AsyncAnthropic
    from google import genai
    from openai import AsyncOpenAI
    
    if not GEMINI_API_KEY or not OPENAI_API_KEY:
        st.error("Mangler API-nøkler! Sjekk miljøvariablene eller Secrets-oppsettet ditt.")
        st.stop()
    
    return AsyncAnthropic(api_key=ANTHROPIC_API_KEY or "dummy"), genai.Client(api_key=GEMINI_API_KEY), AsyncOpenAI(api_key=OPENAI_API_KEY)

async def generate_draft_with_claude(client, model_id: str, prompt: str, image_bytes: bytes | None = None) -> str:
    content = []
    if image_bytes:
        import base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": base64_image}
        })
    content.append({"type": "text", "text": prompt})
    response = await client.messages.create(model=model_id, max_tokens=2048, messages=[{"role": "user", "content": content}])
    return "\n".join([block.text for block in response.content if getattr(block, "type", None) == "text"]).strip()

async def generate_draft_with_gemini(client, prompt: str, pil_image: Image.Image | None = None) -> str:
    contents = [prompt]
    if pil_image: contents.append(pil_image)
    response = await client.aio.models.generate_content(model=GEMINI_MODEL, contents=contents)
    return (response.text or "").strip()

async def generate_critique(client, prompt: str, draft: str) -> str:
    from google.genai import types
    critique_prompt = (
        "Du er OctaCore QA-Engine. Sjekk dette utkastet opp mot live standarder for utdaterte metoder eller logiske feil per 2026:\n\n"
        f"Oppgave: {prompt}\n\nUtkast:\n{draft}\n\nSvar i en kortfattet, strukturert punktliste."
    )
    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL, contents=critique_prompt,
        config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
    )
    return (response.text or "").strip()

async def generate_synthesis(client, prompt: str, draft: str, critique: str) -> str:
    synthesis_prompt = (
        f"Du er OctaCore Core Architect. Perfeksjoner utkastet basert på QA-kritikken.\n\nHovedoppdrag: {prompt}\n\n"
        f"Utkast:\n{draft}\n\nKritikk:\n{critique}\n\nLever KUN ferdig, produksjonsklar kode uten prat."
    )
    response = await client.chat.completions.create(model=OPENAI_MODEL, messages=[{"role": "user", "content": synthesis_prompt}])
    return (response.choices[0].message.content or "").strip()

# ---------------------------------------------------------------------------
# Streamlit Grensesnitt med OctaCore Custom Branding (CSS)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="OctaCore AI Trio Router", page_icon="⚡", layout="wide")

# Skreddersydd CSS-design for OctaCore Tech-profil
st.markdown("""
    <style>
    /* Hovedbakgrunn og skrifttype */
    .stApp {
        background-color: #0f111a;
        color: #e4e6eb;
    }
    /* Sidemeny styling */
    section[data-testid="stSidebar"] {
        background-color: #161925 !important;
        border-right: 1px solid #23283d;
    }
    /* Knapper og interaksjon */
    div.stButton > button:first-child {
        background-color: #00e676 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        border: none !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #00b359 !important;
        box-shadow: 0 0 12px #00e676;
    }
    /* Tekstfelt */
    textarea {
        background-color: #1e2235 !important;
        color: #ffffff !important;
        border: 1px solid #3d4465 !important;
    }
    /* Trinn-bokser */
    .step-card {
        background-color: #161925;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #00d2ff;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_markdown_allowed=True)

# --- SIDEMENY ---
st.sidebar.markdown("<h2 style='color: #00e676; margin-bottom: 0;'>OctaCore</h2>", unsafe_markdown_allowed=True)
st.sidebar.markdown("<p style='color: #888; font-size: 0.9rem;'>AI CORE MANAGEMENT v6.0</p>", unsafe_markdown_allowed=True)

pipeline_mode = st.sidebar.radio(
    "Velg Prosesseringsmodus:",
    ("Full Trekløver (Claude -> Gemini -> OpenAI)", "Test-modus (Gemini -> OpenAI -> OpenAI)"),
    index=1
)

uploaded_file = st.sidebar.file_uploader("Multimodal Inndata (Skjermbilder / Logger)", type=["png", "jpg", "jpeg"])

if st.sidebar.button("Nullstill Systemlogg 🗑️"):
    clear_db_history()
    st.sidebar.success("Database tømt!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("<span style='color: #00e676;'>●</span> System: Operational", unsafe_markdown_allowed=True)

# --- HOVEDPANEL ---
st.markdown("<h1 style='color: #ffffff; font-weight: 800;'>⚡ OctaCore AI Trio Router</h1>", unsafe_markdown_allowed=True)
st.write("Internt back-end-verktøy for agentisk ruting, sanntids kvalitetssikring og kode-syntetisering.")

pil_image = None
image_bytes = None
if uploaded_file:
    image_bytes = uploaded_file.getvalue()
    pil_image = Image.open(uploaded_file)
    st.sidebar.image(pil_image, caption="Lastet opp bildekontekst", use_container_width=True)

user_prompt = st.text_area(
    "Angi systeminstruksjoner eller lim inn back-end-problematikk:", 
    height=130, 
    placeholder="Skriv oppgaven din her..."
)

if st.button("Kjør Arkitektur-Pipeline"):
    if not user_prompt and not uploaded_file:
        st.warning("Vennligst oppgi inndata (tekst eller bilde) før du starter.")
    else:
        anthropic_client, genai_client, openai_client = _build_clients()
        st.info("Initiert asynkron pipeline... Behandler agenter.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📝 Trinn 1: Første Utkast")
            draft_box = st.empty()
            draft_box.warning("Venter...")
        with col2:
            st.markdown("### 🔍 Trinn 2: Live QA (Grounding)")
            critique_box = st.empty()
            critique_box.warning("Venter...")
            
        st.markdown("---")
        st.markdown("### 🏆 Trinn 3: Endelig OctaCore-Syntese")
        final_box = st.empty()
        final_box.warning("Venter på endelig godkjenning...")
        
        async def run_pipeline():
            try:
                if "Full Trekløver" in pipeline_mode:
                    draft = await generate_draft_with_claude(anthropic_client, claude_version, user_prompt, image_bytes)
                    label = "Claude Sonnet"
                else:
                    draft = await generate_draft_with_gemini(genai_client, user_prompt, pil_image)
                    label = "Gemini Flash"
                
                draft_box.markdown(f"**[{label}]**\n\n{draft}")
                
                critique = await generate_critique(genai_client, user_prompt, draft)
                critique_box.markdown(critique)
                
                final = await generate_synthesis(openai_client, user_prompt, draft, critique)
                final_box.code(final, language="python")
                
                save_to_db(
                    prompt=user_prompt if user_prompt else "[Bildeanalyse]",
                    mode=pipeline_mode,
                    has_image=uploaded_file is not None,
                    draft=draft,
                    critique=critique,
                    final_answer=final
                )
                st.success("Pipeline fullført! Kjøringen lagret permanent i systemloggen.")
                st.rerun()
                
            except Exception as e:
                st.error(f"Kritisk systemfeil under kjøring: {str(e)}")

        asyncio.run(run_pipeline())

# --- VEDVARENDE HISTORIKK LOGG ---
db_history = get_history_from_db()
if db_history:
    st.markdown("<br><h3 style='color: #00e676;'>🗄️ Systemlogg (Persistent SQLite)</h3>", unsafe_markdown_allowed=True)
    for item in db_history:
        title = f"⏱️ [{item['time']}] {item['prompt'][:70]}..."
        if item.get("has_image"): title += " 🖼️"
        
        with st.expander(title):
            st.write(f"**System Prompt:** {item['prompt']}")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Trinn 1: Utkast**")
                st.text(item['draft'])
            with c2:
                st.markdown("**Trinn 2: QA-Rapport**")
                st.info(item['critique'])
            st.markdown("**Trinn 3: Syntetisert løsning**")
            st.code(item['final'], language="python")