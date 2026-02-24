import streamlit as st
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import base64
import os
import hashlib
import html

# =========================================================
# ♣ BLACK CLOVER WORKOUT — RIR Edition (8 semanas + perfis)
# =========================================================

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Black Clover Workout", page_icon="♣️", layout="centered", initial_sidebar_state="collapsed")

# --- 2. FUNÇÕES VISUAIS (Fundo e CSS) ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

def set_background(png_file):
    bin_str = get_base64(png_file)
    if not bin_str:
        return
    st.markdown(f"""
    <style>
    .stApp {{
        background: transparent;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        filter: blur(4px) brightness(0.5);
        z-index: -1;
    }}
    .stApp::after {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: rgba(20, 20, 20, 0.85);
        z-index: -1;
    }}
    header {{ background: transparent !important; }}
    </style>
    """, unsafe_allow_html=True)

# Aplica o fundo (verifique se 'banner.png' existe na pasta)
set_background('banner.png')


# --- 2.1 Feedback tátil/sonoro (descanso concluído) ---
def trigger_rest_done_feedback():
    """Tenta vibrar e emitir um beep curto quando o descanso termina (mobile/browser permitting)."""
    try:
        components.html(
            """
            <script>
            (function () {
              try {
                if (window.navigator && navigator.vibrate) {
                  navigator.vibrate([120, 50, 120]);
                }
                const AC = window.AudioContext || window.webkitAudioContext;
                if (!AC) return;
                const ctx = new AC();
                const now = ctx.currentTime;
                function beep(freq, start, dur){
                  const o = ctx.createOscillator();
                  const g = ctx.createGain();
                  o.type = "sine";
                  o.frequency.value = freq;
                  g.gain.setValueAtTime(0.0001, now + start);
                  g.gain.exponentialRampToValueAtTime(0.05, now + start + 0.01);
                  g.gain.exponentialRampToValueAtTime(0.0001, now + start + dur);
                  o.connect(g); g.connect(ctx.destination);
                  o.start(now + start);
                  o.stop(now + start + dur + 0.02);
                }
                beep(880, 0.00, 0.12);
                beep(1174, 0.16, 0.14);
              } catch (e) {}
            })();
            </script>
            """,
            height=0,
            width=0,
        )
    except Exception:
        pass


def scroll_to_dom_id(dom_id: str, behavior: str = "smooth"):
    """Tenta fazer scroll suave até um elemento da app (mobile-friendly)."""
    try:
        did = html.escape(str(dom_id or ""), quote=True)
        beh = "smooth" if str(behavior).lower() == "smooth" else "auto"
        components.html(
            f"""
            <script>
            (function() {{
              try {{
                const target = parent.document.getElementById('{did}') || document.getElementById('{did}');
                if (!target) return;
                target.scrollIntoView({{ behavior: '{beh}', block: 'start' }});
              }} catch (e) {{}}
            }})();
            </script>
            """,
            height=0,
            width=0,
        )
    except Exception:
        pass


def _latest_set_summary_from_df_last(df_last: pd.DataFrame):
    if df_last is None or not isinstance(df_last, pd.DataFrame) or df_last.empty:
        return ""
    try:
        row = df_last.iloc[-1]
        w = row.get('Peso (kg)')
        r = row.get('Reps')
        rr = row.get('RIR')
        if pd.isna(w) and pd.isna(r) and pd.isna(rr):
            return ""
        try:
            w_txt = f"{float(w):.1f}".rstrip('0').rstrip('.')
        except Exception:
            w_txt = str(w) if w is not None else "—"
        try:
            r_txt = str(int(float(r)))
        except Exception:
            r_txt = str(r) if r is not None else "—"
        try:
            rr_txt = f"{float(rr):.1f}".rstrip('0').rstrip('.')
        except Exception:
            rr_txt = str(rr) if rr is not None else "—"
        return f"Último set: {w_txt} kg × {r_txt} @ RIR {rr_txt}"
        return ""
    except Exception:
        return ""


def render_progress_compact(done_n: int, total_n: int):
    total_n = max(1, int(total_n or 0))
    done_n = max(0, min(total_n, int(done_n or 0)))
    pct = done_n / total_n
    rem = total_n - done_n
    state_cls = 'end' if rem <= 2 else ('mid' if done_n > 0 else 'start')
    pct_txt = int(round(pct * 100))
    st.markdown(
        f"""
        <div id='exercise-progress-anchor' class='bc-progress-wrap'>
          <div class='bc-progress-label'>Progresso do treino: {done_n}/{total_n} exercícios <span>{pct_txt}%</span></div>
          <div class='bc-progress-track'>
            <div class='bc-progress-fill {state_cls}' style='width:{pct*100:.1f}%'></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- 3. CSS DA INTERFACE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
        color: #E0E0E0;
    }
    h1, h2, h3 {
        color: #8C1D2C !important;
        font-family: 'Cinzel', serif !important;
        text-shadow: 0 1px 10px rgba(0,0,0,.35);
        text-transform: uppercase;
    }
    /* ABAS (TABS) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(30, 30, 30, 0.6);
        padding: 10px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: rgba(50, 50, 50, 0.7);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 6px;
        color: #CCC;
        font-family: 'Cinzel', serif;
        backdrop-filter: blur(5px);
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(139, 0, 0, 0.9) !important;
        color: #E8E2E2 !important;
        border: 1px solid #8C1D2C !important;
        box-shadow: 0 6px 18px rgba(140, 29, 44, 0.22);
    }
    /* CARTÕES EXPANSÍVEIS */
    .streamlit-expanderHeader {
        background-color: rgba(45, 45, 45, 0.8) !important;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #FFF !important;
        font-family: 'Cinzel', serif;
    }
    .streamlit-expanderContent {
        background-color: rgba(30, 30, 30, 0.6) !important;
        border-radius: 0 0 8px 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: rgba(0, 0, 0, 0.4) !important;
        color: white !important;
        border: 1px solid #555 !important;
        border-radius: 5px;
    }
    /* Botões */
    div.stButton > button:first-child {
        background: linear-gradient(180deg, #5B1020 0%, #1A090D 100%);
        color: #E8E2E2;
        border: 1px solid #8C1D2C;
        font-family: 'Cinzel', serif;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 16px rgba(140, 29, 44, 0.28);
    }
    </style>
""", unsafe_allow_html=True)

# --- CSS mobile-first (telemóvel) ---
st.markdown("""
<style>
/* Toques maiores e leitura melhor */
div.stButton > button,
button[kind],
[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"]{
  min-height: 46px;
  border-radius: 10px !important;
}
[data-testid="stMetric"]{
  background: rgba(20,20,20,0.35);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
  padding: 8px 10px;
}
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label,
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label,
[data-testid="stNumberInput"] label{
  font-size: 0.95rem !important;
}
[data-testid="stNumberInput"] input{
  text-align: center;
}
div[data-testid="stExpander"]{
  border-radius: 12px;
}

div[data-testid="stExpander"]{
  background: rgba(14,14,14,0.34);
  border: 1px solid rgba(255,255,255,0.06);
  backdrop-filter: blur(8px);
}


/* Compactar topo (evita gap grande entre header e tabs) */
h1, .bc-main-title{ margin-top: 0 !important; margin-bottom: 0.2rem !important; }
[data-testid="stCaptionContainer"]{ margin-top: 0 !important; margin-bottom: 0.25rem !important; }
div[data-testid="stTabs"]{ margin-top: 0.1rem !important; }

/* Mobile */
@media (max-width: 768px){
  .block-container{
    padding-top: 0.65rem !important;
    padding-left: 0.7rem !important;
    padding-right: 0.7rem !important;
    padding-bottom: 1rem !important;
  }

  h1{ font-size: 1.35rem !important; line-height: 1.2 !important; }
  h2{ font-size: 1.1rem !important; line-height: 1.2 !important; }
  h3{ font-size: 0.95rem !important; line-height: 1.2 !important; }

  .stTabs [data-baseweb="tab-list"]{
    gap: 6px;
    padding: 6px;
    overflow-x: auto;
    flex-wrap: nowrap;
    scrollbar-width: thin;
  }
  .stTabs [data-baseweb="tab"]{
    min-width: 118px;
    height: 42px;
    padding: 0 8px;
    font-size: 0.78rem;
  }

  section[data-testid="stSidebar"]{
    width: min(92vw, 380px) !important;
  }

  [data-testid="stMetricLabel"]{
    font-size: 0.75rem !important;
  }
  [data-testid="stMetricValue"]{
    font-size: 1rem !important;
  }

  .stMarkdown p, .stCaption{
    font-size: 0.9rem !important;
  }

  /* Tabela mais legível em mobile */
  [data-testid="stDataFrame"]{
    font-size: 0.82rem;
  }
}
</style>
""", unsafe_allow_html=True)

# --- CSS de polimento (mobile-first) ---
st.markdown("""
<style>
:root{
  --bc-glass: rgba(18,18,18,.62);
  --bc-line: rgba(255,255,255,.07);
  --bc-accent: rgba(140,29,44,.38);
  --bc-gold: #E8E2E2;
  --bc-accent-strong: #8C1D2C;
  --bc-accent-soft: rgba(140,29,44,.22);
}
.app-bottom-safe{ height: 118px; }
.bc-hero{
  background: linear-gradient(180deg, rgba(22,22,22,.78), rgba(14,14,14,.78));
  border: 1px solid var(--bc-line);
  border-radius: 14px;
  padding: 10px 12px;
  margin: 4px 0 10px 0;
  box-shadow: 0 10px 28px rgba(0,0,0,.24);
}
.bc-hero-title{ color:#fff; font-weight:700; margin-bottom:8px; font-size:.95rem; }
.bc-chip-wrap{ display:flex; flex-wrap:wrap; gap:6px; }
.bc-chip{
  display:inline-flex; align-items:center; gap:5px;
  border:1px solid var(--bc-line);
  background: rgba(255,255,255,.025);
  border-radius: 999px;
  padding: 3px 8px;
  font-size: .78rem;
  color:#EDEDED;
}
.bc-chip.gold{ border-color: rgba(140,29,44,.32); color: var(--bc-gold); }
.bc-chip.red{ border-color: rgba(140,29,44,.32); }
.bc-chip.green{ border-color: rgba(80,220,140,.28); }
.bc-ex-meta{
  background: rgba(255,255,255,.025);
  border:1px solid var(--bc-line);
  border-radius: 12px;
  padding: 8px 10px;
  margin-bottom: 8px;
}
.bc-ex-name{ font-weight:700; color:#fff; margin-bottom:6px; line-height:1.2; }
.bc-ex-pills{ display:flex; flex-wrap:wrap; gap:6px; }
.bc-pill{
  background: rgba(0,0,0,.18);
  border:1px solid var(--bc-line);
  border-radius: 999px;
  padding: 2px 8px;
  font-size: .75rem;
}
.bc-float-bar{
  position: fixed;
  left: 8px; right: 8px;
  z-index: 9998;
  border-radius: 14px;
  backdrop-filter: blur(8px);
  border:1px solid rgba(255,255,255,.10);
  text-align:center;
  box-shadow: 0 8px 20px rgba(0,0,0,.30);
}
.bc-float-footer{
  bottom: calc(8px + env(safe-area-inset-bottom));
  background: rgba(12,12,12,.84);
  border-color: rgba(140,29,44,.25);
  padding: 8px 12px;
  font-size: 12px;
}
.bc-float-status{
  bottom: calc(54px + env(safe-area-inset-bottom));
  background: rgba(18,18,18,.90);
  padding: 8px 10px;
  font-size: 12px;
}
[data-testid='stNumberInput'] button{ min-width: 34px !important; }
[data-testid='stProgressBar'] > div > div{ border-radius: 999px !important; }
@media (max-width: 768px){
  .bc-hero{ padding: 10px; }
  .bc-chip{ font-size: .74rem; }
  .bc-pill{ font-size: .72rem; }
  .app-bottom-safe{ height: 126px; }
}

.bc-main-title{
  margin: 0 0 4px 0;
  padding: 0;
  font-family: 'Cinzel', serif;
  font-weight: 900;
  text-transform: uppercase;
  color: #8C1D2C;
  text-shadow: 0 1px 10px rgba(0,0,0,.35);
  font-size: clamp(1.95rem, 5.6vw, 2.7rem);
  line-height: 1.05;
  letter-spacing: .02em;
  background: transparent !important;
}
@media (max-width: 768px){
  .bc-main-title{ font-size: 1.85rem; }
}

</style>
""", unsafe_allow_html=True)

# --- Ajustes finos das tabs (remove espaço vazio) ---
st.markdown("""
<style>
div[data-testid="stTabs"] [data-baseweb="tab-list"]{
  min-height: 0 !important;
  height: auto !important;
  align-items: center !important;
  padding-bottom: 6px !important;
  margin-bottom: 0 !important;
}
div[data-testid="stTabs"] [data-baseweb="tab-panel"],
div[data-testid="stTabs"] div[role="tabpanel"]{
  padding-top: .35rem !important;
  margin-top: 0 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* =========================
   SIDEBAR: Grimório PRO
   ========================= */
section[data-testid="stSidebar"]{
  background: rgba(10,10,10,0.62) !important;
  border-right: 1px solid rgba(140,29,44,0.35) !important;
  backdrop-filter: blur(12px);
}
section[data-testid="stSidebar"] > div{ padding-top: 10px !important; }

/* “Selo” do topo */
.sidebar-seal{
  position: relative;
  padding: 14px 14px 12px 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(20,20,20,0.75), rgba(10,10,10,0.55));
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0 14px 30px rgba(0,0,0,0.35);
  margin: 8px 10px 12px 10px;
}
.sidebar-seal::before{
  content: "♣";
  position: absolute;
  right: 14px;
  top: 10px;
  font-size: 22px;
  color: rgba(176, 126, 136, 0.85);
  text-shadow: 0 0 12px rgba(140, 29, 44, 0.22);
}
.sidebar-seal-title{
  font-family: 'Cinzel', serif;
  font-weight: 900;
  letter-spacing: .12em;
  color: #E8E2E2;
  text-shadow: 0 0 14px rgba(140, 29, 44, 0.22);
  margin: 0;
}
.sidebar-seal-sub{
  margin: 6px 0 0 0;
  color: rgba(224,224,224,0.85);
  font-size: 12px;
}

/* Cards */
.sidebar-card{
  background: rgba(20,20,20,0.55);
  border: 1px solid rgba(255,255,255,0.08);
  border-left: 3px solid rgba(140, 29, 44, 0.78);
  padding: 12px 12px;
  border-radius: 16px;
  box-shadow: 0 10px 22px rgba(0,0,0,0.35);
  margin: 0 10px 12px 10px;
}
.sidebar-card h3{
  font-family: 'Cinzel', serif;
  color: #E8E2E2 !important;
  letter-spacing: .08em;
  margin: 0 0 6px 0;
  text-shadow: 0 0 10px rgba(140,29,44,0.18);
}

/* Divisor “runa” */
.rune-divider{
  margin: 10px 0 8px 0;
  height: 1px;
  border: none;
  background: linear-gradient(90deg, transparent, rgba(140,29,44,0.65), transparent);
  position: relative;
}
.rune-divider::after{
  content: "✦";
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  top: -10px;
  font-size: 12px;
  color: rgba(232,226,226,0.82);
  text-shadow: 0 0 10px rgba(140,29,44,0.22);
  background: rgba(10,10,10,0.60);
  padding: 0 8px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.08);
}

/* Inputs e selects na sidebar */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea{
  background: rgba(0,0,0,0.35) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  color: #fff !important;
  border-radius: 12px !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div{
  background: rgba(0,0,0,0.35) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 12px !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"]{
  background: rgba(0,0,0,0.18);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 10px;
}

/* Scrollbar */
section[data-testid="stSidebar"] ::-webkit-scrollbar { width: 10px; }
section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
  background: rgba(140,29,44,0.35);
  border-radius: 999px;
}
section[data-testid="stSidebar"] ::-webkit-scrollbar-track {
  background: rgba(0,0,0,0.15);
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
/* Polimento extra (toque mobile + animações) */
* { -webkit-tap-highlight-color: transparent; }
@media (hover: none){
  div.stButton > button:hover {
    transform: none !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.30) !important;
  }
}
@media (prefers-reduced-motion: reduce){
  * { scroll-behavior: auto !important; }
  div.stButton > button { transition: none !important; }
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
/* Compact mode (visual only) */
.rune-divider{display:none !important;}
.block-container{
  padding-top: 0.45rem !important;
  padding-bottom: 0.7rem !important;
}
@media (max-width: 768px){
  .block-container{
    padding-top: 0.4rem !important;
    padding-left: 0.55rem !important;
    padding-right: 0.55rem !important;
    padding-bottom: 0.75rem !important;
  }
}
div[data-testid="stVerticalBlock"]{ gap: .35rem !important; }
div[data-testid="stTabs"] [data-baseweb="tab-list"]{
  padding: 6px !important;
  gap: 6px !important;
  margin-bottom: 0 !important;
}
.stTabs [data-baseweb="tab"]{
  height: 42px !important;
  min-height: 42px !important;
}
div[data-testid="stTabs"] div[role="tabpanel"]{
  padding-top: .2rem !important;
}
div[data-testid="stExpander"]{ margin: 0 0 6px 0 !important; }
.streamlit-expanderHeader{ min-height: 42px !important; padding-top: 6px !important; padding-bottom: 6px !important; }
.streamlit-expanderContent{ padding-top: 4px !important; }
[data-testid="stMetric"]{ padding: 6px 8px !important; }
section[data-testid="stSidebar"] > div{ padding-top: 6px !important; }
.sidebar-seal{
  margin: 6px 8px 8px 8px !important;
  padding: 10px 12px 9px 12px !important;
  border-radius: 14px !important;
}
.sidebar-seal-sub{ margin-top: 3px !important; }
.sidebar-card{
  margin: 0 8px 8px 8px !important;
  padding: 9px 10px !important;
  border-radius: 13px !important;
}
.sidebar-card h3{ margin: 0 0 4px 0 !important; font-size: .88rem !important; }
section[data-testid="stSidebar"] div[role="radiogroup"]{ padding: 6px !important; border-radius: 12px !important; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{ margin: 0 !important; }
section[data-testid="stSidebar"] [data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-testid="stRadio"],
section[data-testid="stSidebar"] [data-testid="stCheckbox"]{ margin-bottom: .1rem !important; }
p{ margin-bottom: .35rem !important; }
.app-bottom-safe{ height: 98px !important; }

/* treino progress + chips */
.bc-progress-wrap{ margin: .55rem 0 .5rem 0; }
.bc-progress-label{ font-size:.92rem; color:#EAE6E6; display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:6px; }
.bc-progress-label span{ color:#B9B1B1; font-size:.80rem; }
.bc-progress-track{ width:100%; height:8px; border-radius:999px; background:rgba(255,255,255,.10); overflow:hidden; border:1px solid rgba(255,255,255,.06); }
.bc-progress-fill{ height:100%; border-radius:999px; transition:width .18s ease; background:linear-gradient(90deg, rgba(70,130,255,.75), rgba(70,130,255,.95)); }
.bc-progress-fill.mid{ background:linear-gradient(90deg, rgba(141,29,44,.70), rgba(141,29,44,.95)); }
.bc-progress-fill.end{ background:linear-gradient(90deg, rgba(173,28,48,.82), rgba(204,52,73,.98)); box-shadow:0 0 10px rgba(173,28,48,.25); }

.bc-serie-badge{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: .32rem .70rem;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,.10);
  background: rgba(120, 20, 35, .18);
  color: #f3f4f6;
  font-size: 1.0rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: .2px;
  margin: .15rem 0 .35rem 0;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.03);
}
.bc-last-chip{ margin: 0 0 1rem 0; padding: .35rem .55rem; border-radius: 999px; display:inline-flex; align-items:center; gap:6px; font-size:.86rem; color:#EDE9E9; border:1px solid rgba(255,255,255,.10); background:rgba(255,255,255,.04); }
.bc-final-summary{ margin: .5rem 0 .45rem 0; padding: .65rem .75rem; border-radius: 14px; border:1px solid rgba(140,29,44,.35); background:linear-gradient(180deg, rgba(140,29,44,.12), rgba(255,255,255,.02)); }
.bc-final-summary .ttl{ font-weight:700; color:#F0ECEC; margin-bottom:3px; }
.bc-final-summary .sub{ color:#CFC9C9; font-size:.88rem; }
</style>
""", unsafe_allow_html=True)

# --- 4. CONEXÃO E DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

SCHEMA_COLUMNS = [
    "Data","Perfil","Dia","Bloco","Plano_ID",
    "Exercício","Peso","Reps","RIR","Notas",
    "Aquecimento","Mobilidade","Cardio","Tendões","Core","Cooldown",
    "XP","Streak","Checklist_OK"
]

PROFILES_WORKSHEET = "Perfis"
PROFILES_COLUMNS = ["Perfil","Criado_em","Plano_ID","Ativo"]
PROFILES_BACKUP_PATH = "offline_profiles.csv"


BACKUP_PATH = "offline_backup.csv"
DATA_CACHE_SECONDS = 45
PROFILES_CACHE_SECONDS = 300

def _service_account_email():
    try:
        return st.secrets.get("connections", {}).get("gsheets", {}).get("credentials", {}).get("client_email", None)
    except Exception:
        return None

def _save_offline_backup(df: pd.DataFrame):
    try:
        df.to_csv(BACKUP_PATH, index=False, encoding="utf-8")
        return True
    except Exception:
        return False

def _load_offline_backup() -> pd.DataFrame:
    if os.path.exists(BACKUP_PATH):
        try:
            df = pd.read_csv(BACKUP_PATH, dtype=str, keep_default_na=False)
            # garantir schema
            for c in SCHEMA_COLUMNS:
                if c not in df.columns:
                    df[c] = None
            return df[SCHEMA_COLUMNS]
        except Exception:
            return pd.DataFrame(columns=SCHEMA_COLUMNS)
    return pd.DataFrame(columns=SCHEMA_COLUMNS)


def _save_offline_profiles(df: pd.DataFrame):
    try:
        df.to_csv(PROFILES_BACKUP_PATH, index=False, encoding="utf-8")
        return True
    except Exception:
        return False

def _load_offline_profiles() -> pd.DataFrame:
    if os.path.exists(PROFILES_BACKUP_PATH):
        try:
            df = pd.read_csv(PROFILES_BACKUP_PATH, dtype=str, keep_default_na=False)
            for c in PROFILES_COLUMNS:
                if c not in df.columns:
                    df[c] = None
            return df[PROFILES_COLUMNS]
        except Exception:
            return pd.DataFrame(columns=PROFILES_COLUMNS)
    return pd.DataFrame(columns=PROFILES_COLUMNS)

def _conn_read_worksheet(worksheet: str) -> pd.DataFrame:
    """Tenta ler uma worksheet específica. Se a lib não suportar worksheet=, levanta."""
    return _retry(lambda: conn.read(ttl="0", worksheet=worksheet), tries=2)

def _conn_update_worksheet(df: pd.DataFrame, worksheet: str):
    """Tenta atualizar uma worksheet específica. Se a lib não suportar worksheet=, levanta."""
    return _retry(lambda: conn.update(data=df, worksheet=worksheet), tries=2)

def get_profiles_df(force_refresh: bool = False):
    """Perfis ficam na worksheet 'Perfis'. Se não existir / sem permissão, faz fallback.
    Usa cache em sessão para evitar bater no limite de reads no mobile (timer faz muitos reruns).
    """
    try:
        if not force_refresh:
            _pf = st.session_state.get("_profiles_cache_df")
            _pf_ts = float(st.session_state.get("_profiles_cache_ts", 0.0) or 0.0)
            _ok = st.session_state.get("_profiles_cache_ok")
            _err = st.session_state.get("_profiles_cache_err", "")
            if isinstance(_pf, pd.DataFrame) and (time.time() - _pf_ts) < PROFILES_CACHE_SECONDS:
                return _pf.copy(), bool(_ok), str(_err or "")
    except Exception:
        pass

    try:
        dfp = _conn_read_worksheet(PROFILES_WORKSHEET)
        if dfp is None or dfp.empty:
            dfp = pd.DataFrame(columns=PROFILES_COLUMNS)
        for c in PROFILES_COLUMNS:
            if c not in dfp.columns:
                dfp[c] = None
        dfp = dfp[PROFILES_COLUMNS].copy()
        # limpa duplicados / vazios
        dfp["Perfil"] = dfp["Perfil"].astype(str).str.strip()
        dfp = dfp[dfp["Perfil"] != ""]
        dfp = dfp.drop_duplicates(subset=["Perfil"], keep="last")
        _save_offline_profiles(dfp)
        try:
            st.session_state["_profiles_cache_df"] = dfp.copy()
            st.session_state["_profiles_cache_ts"] = time.time()
            st.session_state["_profiles_cache_ok"] = True
            st.session_state["_profiles_cache_err"] = ""
        except Exception:
            pass
        return dfp, True, ""
    except Exception as e:
        # fallback offline
        dfp_off = _load_offline_profiles()
        try:
            st.session_state["_profiles_cache_df"] = dfp_off.copy()
            st.session_state["_profiles_cache_ts"] = time.time()
            st.session_state["_profiles_cache_ok"] = False
            st.session_state["_profiles_cache_err"] = f"{e}"
        except Exception:
            pass
        if dfp_off is not None and not dfp_off.empty:
            return dfp_off, False, f"{e}"
        return pd.DataFrame(columns=PROFILES_COLUMNS), False, f"{e}"

def save_profiles_df(dfp: pd.DataFrame):
    try:
        _conn_update_worksheet(dfp[PROFILES_COLUMNS], PROFILES_WORKSHEET)
        _save_offline_profiles(dfp[PROFILES_COLUMNS])
        try:
            st.session_state["_profiles_cache_df"] = dfp[PROFILES_COLUMNS].copy()
            st.session_state["_profiles_cache_ts"] = time.time()
            st.session_state["_profiles_cache_ok"] = True
            st.session_state["_profiles_cache_err"] = ""
        except Exception:
            pass
        return True, ""
    except Exception as e:
        _save_offline_profiles(dfp[PROFILES_COLUMNS])
        try:
            st.session_state["_profiles_cache_df"] = dfp[PROFILES_COLUMNS].copy()
            st.session_state["_profiles_cache_ts"] = time.time()
            st.session_state["_profiles_cache_ok"] = False
            st.session_state["_profiles_cache_err"] = str(e)
        except Exception:
            pass
        return False, str(e)

def get_plan_id_for_profile(perfil: str, dfp: pd.DataFrame):
    if dfp is not None and not dfp.empty:
        row = dfp[dfp["Perfil"].astype(str) == str(perfil)]
        if not row.empty:
            pid = str(row.iloc[0].get("Plano_ID", "")).strip()
            if pid:
                return pid
    return "Base"

def _retry(fn, tries=3):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            last = e
            # backoff simples (rate limit / falhas transitórias)
            time.sleep(0.6 * (2 ** i))
    raise last

def safe_read_sheet() -> pd.DataFrame:
    try:
        df = _retry(lambda: conn.read(ttl="0"), tries=2)
        if df is None or df.empty:
            return pd.DataFrame(columns=SCHEMA_COLUMNS)
        return df
    except Exception:
        # fallback offline (evita app morrer)
        return _load_offline_backup()

def safe_update_sheet(df: pd.DataFrame):
    # tenta gravar na Sheet; se falhar, guarda backup local e devolve erro
    try:
        _retry(lambda: conn.update(data=normalize_for_save(df)), tries=2)
        # espelha também localmente para não perder histórico se a Sheet cair depois
        _save_offline_backup(normalize_for_save(df))
        return True, ""
    except Exception as e:
        _save_offline_backup(normalize_for_save(df))
        return False, str(e)



def _cell_to_gsheet(v):
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    return str(v)

def _gsheets_cfg():
    try:
        return st.secrets.get("connections", {}).get("gsheets", {})
    except Exception:
        return {}

def _append_offline_backup_rows(df: pd.DataFrame, file_name: str = "offline_backup.csv"):
    try:
        df = normalize_for_save(df)
        header = not os.path.exists(file_name)
        df.to_csv(file_name, mode="a", index=False, header=header)
    except Exception:
        pass

def try_sync_offline_backup_to_sheet():
    """Tenta sincronizar linhas do backup local para a Google Sheet (append)."""
    if not os.path.exists(BACKUP_PATH):
        return False, "Sem backup local.", 0
    try:
        dfb = pd.read_csv(BACKUP_PATH, dtype=str, keep_default_na=False)
    except Exception as e:
        return False, str(e), 0
    if dfb is None or dfb.empty:
        return False, "Backup vazio.", 0
    for c in SCHEMA_COLUMNS:
        if c not in dfb.columns:
            dfb[c] = None
    dfb = dfb[SCHEMA_COLUMNS]
    ok, err = safe_append_rows(dfb)
    if ok:
        try:
            os.remove(BACKUP_PATH)
        except Exception:
            pass
        return True, "", len(dfb)
    return False, err, len(dfb)


def _is_lower_exercise(ex_name: str) -> bool:
    ex = str(ex_name).lower()
    lower_keys = [
        "leg press", "deadlift", "rdl", "hip thrust", "glúteo", "glute", "split squat",
        "bulgarian", "panturrilha", "calf", "flexora", "curl", "abd", "back extension",
        "nordic", "agach", "squat", "step-back"
    ]
    return any(k in ex for k in lower_keys)


def _rep_top_from_range(rep_str: str) -> int:
    s = str(rep_str).strip().replace(" ", "")
    if "-" in s:
        try:
            return int(float(s.split("-")[-1]))
        except Exception:
            return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def _double_progression_ready(last_df: pd.DataFrame | None, rep_range: str, rir_target_num: float):
    """Critério simples: todas as séries no topo da faixa e RIR >= alvo-0.5."""
    if last_df is None or last_df.empty:
        return False
    topo = _rep_top_from_range(rep_range)
    if topo <= 0 or "Reps" not in last_df.columns:
        return False
    reps = pd.to_numeric(last_df["Reps"], errors="coerce")
    if reps.isna().any() or len(reps) == 0:
        return False
    if not bool((reps >= topo).all()):
        return False
    if "RIR" in last_df.columns:
        rirs = pd.to_numeric(last_df["RIR"], errors="coerce")
        if not rirs.isna().all():
            try:
                if float(rirs.mean()) < float(rir_target_num) - 0.5:
                    return False
            except Exception:
                pass
    return True


def _prefill_sets_from_last(i, item, df_last, peso_sug, reps_low, rir_target_num):
    series_n = int(item.get("series", 0))
    pesos = []
    reps_list = []
    rirs = []
    if df_last is not None and not df_last.empty:
        pesos = pd.to_numeric(df_last.get("Peso (kg)"), errors="coerce").tolist() if "Peso (kg)" in df_last.columns else []
        reps_list = pd.to_numeric(df_last.get("Reps"), errors="coerce").tolist() if "Reps" in df_last.columns else []
        rirs = pd.to_numeric(df_last.get("RIR"), errors="coerce").tolist() if "RIR" in df_last.columns else []
    for s in range(series_n):
        if s < len(pesos) and pd.notna(pesos[s]):
            st.session_state[f"peso_{i}_{s}"] = float(pesos[s])
        elif peso_sug > 0:
            st.session_state[f"peso_{i}_{s}"] = float(peso_sug)
        if s < len(reps_list) and pd.notna(reps_list[s]):
            st.session_state[f"reps_{i}_{s}"] = int(reps_list[s])
        else:
            st.session_state[f"reps_{i}_{s}"] = int(reps_low)
        if s < len(rirs) and pd.notna(rirs[s]):
            st.session_state[f"rir_{i}_{s}"] = float(rirs[s])
        else:
            st.session_state[f"rir_{i}_{s}"] = float(rir_target_num)


def safe_append_rows(df_rows: pd.DataFrame):
    """Append (seguro para uso simultâneo) em vez de reescrever a sheet inteira.
    Se falhar, grava em offline_backup.csv.
    - Faz retry automático (erros transitórios / quota).
    - Garante/migra header da sheet para o schema atual.
    """
    df_rows = normalize_for_save(df_rows)

    def _get_ws():
        # Reutiliza worksheet em sessão para reduzir reads (quota do Google Sheets é baixa)
        try:
            ws_cached = st.session_state.get("_gs_ws_cache")
            if ws_cached is not None:
                return ws_cached
        except Exception:
            pass

        client = getattr(conn, "_client", None)
        if client is None:
            client = getattr(getattr(conn, "client", None), "_client", None)
        if client is None:
            raise RuntimeError("Não foi possível obter cliente gspread (append).")

        cfg = _gsheets_cfg()
        spreadsheet = cfg.get("spreadsheet") or cfg.get("spreadsheet_url") or cfg.get("url")
        worksheet = cfg.get("worksheet")

        if not spreadsheet:
            raise RuntimeError("Configuração gsheets sem 'spreadsheet' (URL ou key).")

        sh = client.open_by_url(spreadsheet) if "http" in str(spreadsheet) else client.open_by_key(str(spreadsheet))
        ws = sh.worksheet(worksheet) if worksheet else sh.sheet1
        try:
            st.session_state["_gs_ws_cache"] = ws
        except Exception:
            pass
        return ws

    def _ensure_header_schema(ws):
        try:
            cached_header = st.session_state.get("_gs_header_cache")
            if isinstance(cached_header, list) and cached_header:
                return cached_header
        except Exception:
            pass

        header = [str(x).strip() for x in ws.row_values(1)]
        if not header:
            ws.update("A1", [SCHEMA_COLUMNS])
            try:
                st.session_state["_gs_header_cache"] = list(SCHEMA_COLUMNS)
            except Exception:
                pass
            return list(SCHEMA_COLUMNS)

        # Migração automática do header sem perder colunas antigas
        header_clean = [h for h in header if str(h).strip() != ""]
        missing = [c for c in SCHEMA_COLUMNS if c not in header_clean]
        if missing:
            merged = header_clean + missing
            ws.update("A1", [merged])
            try:
                st.session_state["_gs_header_cache"] = merged
            except Exception:
                pass
            return merged
        try:
            st.session_state["_gs_header_cache"] = header_clean
        except Exception:
            pass
        return header_clean

    try:
        ws = _get_ws()
        header = _ensure_header_schema(ws)

        rows_to_append = []
        for _, r in df_rows.iterrows():
            rows_to_append.append([_cell_to_gsheet(r.get(col, "")) for col in header])

        # Retry para erros transitórios (429 / 5xx / timeouts)
        last_err = None
        for attempt in range(3):
            try:
                if hasattr(ws, "append_rows"):
                    ws.append_rows(rows_to_append, value_input_option="RAW")
                else:
                    for values in rows_to_append:
                        ws.append_row(values, value_input_option="RAW")
                _append_offline_backup_rows(df_rows)  # mantém backup local incremental
                return True, ""
            except Exception as e:
                last_err = e
                # pequeno backoff para quota/transitório
                time.sleep(0.8 * (attempt + 1))

        raise last_err if last_err else RuntimeError("Falha desconhecida ao fazer append.")
    except Exception as e:
        # nunca perder treino
        _append_offline_backup_rows(df_rows)
        try:
            st.session_state.pop("_gs_ws_cache", None)
            st.session_state.pop("_gs_header_cache", None)
        except Exception:
            pass

        # Fallback final: tenta reescrever via conn.update (menos ideal para concorrência, mas evita bloqueio)
        try:
            df_full = get_data()
            df_final = pd.concat([df_full, df_rows], ignore_index=True)
            conn.update(data=normalize_for_save(df_final))
            return True, ""
        except Exception:
            pass

        return False, str(e)


def _to_bool(x):
    s = str(x).strip().lower()
    return s in ["true","1","yes","y","sim"]

def get_data(force_refresh: bool = False):
    """Lê a sheet e garante schema (migração RPE->RIR e Alongamento->Mobilidade).
    Se a Google Sheet falhar, usa um backup local (offline_backup.csv).
    Usa cache curta em sessão para reduzir quota de reads no Google Sheets.
    """
    try:
        if not force_refresh:
            _dfc = st.session_state.get("_df_cache_data")
            _ts = float(st.session_state.get("_df_cache_ts", 0.0) or 0.0)
            if isinstance(_dfc, pd.DataFrame) and (time.time() - _ts) < DATA_CACHE_SECONDS:
                return _dfc.copy()
    except Exception:
        pass

    df = safe_read_sheet()
    try:
        if df is None:
            df = pd.DataFrame()
        df = df.copy()

        # migrações de colunas antigas
        if "RPE" in df.columns and "RIR" not in df.columns:
            df["RIR"] = df["RPE"]
        if "Alongamento" in df.columns and "Mobilidade" not in df.columns:
            df["Mobilidade"] = df["Alongamento"]

        # garantir schema
        for c in SCHEMA_COLUMNS:
            if c not in df.columns:
                df[c] = None
        df = df[SCHEMA_COLUMNS]

        try:
            st.session_state["_df_cache_data"] = df.copy()
            st.session_state["_df_cache_ts"] = time.time()
        except Exception:
            pass
        return df
    except Exception:
        try:
            _df = pd.DataFrame(columns=SCHEMA_COLUMNS)
            st.session_state["_df_cache_data"] = _df.copy()
            st.session_state["_df_cache_ts"] = time.time()
            return _df
        except Exception:
            return pd.DataFrame(columns=SCHEMA_COLUMNS)




# --- 4.1 HELPERS DE DADOS / XP / HISTÓRICO ---
def _parse_num_list(v):
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        out=[]
        for x in v:
            try:
                if pd.isna(x):
                    continue
            except Exception:
                pass
            sx = str(x).strip().replace(',', '.')
            if sx == '':
                continue
            try:
                out.append(float(sx))
            except Exception:
                pass
        return out
    s = str(v).strip()
    if s == '' or s.lower() == 'nan':
        return []
    # prioridade: separador de listas é vírgula; decimal pode vir com ponto.
    parts = [x.strip() for x in s.split(',')]
    out=[]
    for x in parts:
        if x == '':
            continue
        x = x.replace(';', '').strip()
        try:
            out.append(float(x))
        except Exception:
            try:
                out.append(float(x.replace(',', '.')))
            except Exception:
                pass
    return out


def _join_num_list(vals, decimals=1):
    out=[]
    for v in list(vals or []):
        try:
            fv=float(v)
        except Exception:
            continue
        if decimals == 0:
            out.append(str(int(round(fv))))
        else:
            txt=f"{fv:.{decimals}f}".rstrip('0').rstrip('.')
            if txt == '-0': txt='0'
            out.append(txt)
    return ','.join(out)


def normalize_for_save(df: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame() if df is None else df.copy()
    for c in SCHEMA_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[SCHEMA_COLUMNS].copy()

    bool_cols = ["Aquecimento","Mobilidade","Cardio","Tendões","Core","Cooldown","Checklist_OK"]
    for c in bool_cols:
        df[c] = df[c].apply(lambda x: True if str(x).strip().lower() in ['true','1','yes','sim'] else (False if str(x).strip().lower() in ['false','0','no','não','nao'] else x))

    # normalizar colunas de listas
    for c in ["Peso","Reps","RIR"]:
        def _norm_cell(x):
            if isinstance(x, (list, tuple)):
                if c == 'Reps':
                    return _join_num_list(x, decimals=0)
                return _join_num_list(x, decimals=1)
            try:
                if pd.isna(x):
                    return ''
            except Exception:
                pass
            return str(x)
        df[c] = df[c].apply(_norm_cell)

    # datas em dd/mm/aaaa
    if 'Data' in df.columns:
        def _norm_date(x):
            try:
                if pd.isna(x):
                    return datetime.date.today().strftime('%d/%m/%Y')
            except Exception:
                pass
            sx=str(x).strip()
            if not sx:
                return datetime.date.today().strftime('%d/%m/%Y')
            dt = pd.to_datetime(sx, dayfirst=True, errors='coerce')
            if pd.notna(dt):
                return dt.strftime('%d/%m/%Y')
            return sx
        df['Data'] = df['Data'].apply(_norm_date)

    # evitar NaN para gravação
    return df.where(pd.notnull(df), None)


def checklist_xp(req: dict, justificativa: str = ""):
    req = req or {}
    keys = [k for k in ["aquecimento","mobilidade","cardio","tendoes","core","cooldown"] if bool(req.get(f"{k}_req", False))]
    total = len(keys)
    done = sum(1 for k in keys if bool(req.get(k, False)))
    ok = (done >= total) if total > 0 else True
    just_ok = bool(str(justificativa or '').strip())

    # XP por exercício (mantido simples e estável)
    xp = 10 + done * 2
    if ok:
        xp += 4
    elif just_ok:
        xp += 2
    xp = int(max(0, min(30, xp)))
    return xp, (ok or just_ok)


def _unique_profile_dates(df: pd.DataFrame, perfil: str):
    if df is None or df.empty or 'Perfil' not in df.columns:
        return []
    d = df[df['Perfil'].astype(str) == str(perfil)].copy()
    if d.empty or 'Data' not in d.columns:
        return []
    dt = pd.to_datetime(d['Data'], dayfirst=True, errors='coerce').dropna().dt.date.unique().tolist()
    dt = sorted(dt)
    return dt


def get_last_streak(df: pd.DataFrame, perfil: str) -> int:
    dates = _unique_profile_dates(df, perfil)
    if not dates:
        return 0
    streak = 1
    cur = dates[-1]
    seen = set(dates)
    while True:
        prev = cur - datetime.timedelta(days=1)
        if prev in seen:
            streak += 1
            cur = prev
        else:
            break
    return streak


def _compute_streak_if_add_today(df: pd.DataFrame, perfil: str, day: datetime.date) -> int:
    dates = set(_unique_profile_dates(df, perfil))
    dates.add(day)
    if day not in dates:
        return 0
    streak = 1
    cur = day
    while (cur - datetime.timedelta(days=1)) in dates:
        cur = cur - datetime.timedelta(days=1)
        streak += 1
    return streak


def get_historico_detalhado(df: pd.DataFrame, perfil: str, ex: str):
    if df is None or df.empty:
        return None, 0.0, 2.0, '—'
    d = df.copy()
    d = d[(d['Perfil'].astype(str) == str(perfil)) & (d['Exercício'].astype(str) == str(ex))]
    if d.empty:
        return None, 0.0, 2.0, '—'
    d['_dt'] = pd.to_datetime(d['Data'], dayfirst=True, errors='coerce')
    d = d.sort_values('_dt', ascending=False, na_position='last')
    row = d.iloc[0]
    pesos = _parse_num_list(row.get('Peso'))
    reps = _parse_num_list(row.get('Reps'))
    rirs = _parse_num_list(row.get('RIR'))
    n = max(len(pesos), len(reps), len(rirs))
    if n == 0:
        return None, 0.0, 2.0, str(row.get('Data', '—'))
    # broadcast simples quando uma lista tem só 1 valor
    def _get(arr, i):
        if not arr:
            return None
        if len(arr) == 1:
            return arr[0]
        return arr[i] if i < len(arr) else None
    recs=[]
    for i in range(n):
        recs.append({
            'Série': i+1,
            'Peso (kg)': _get(pesos, i),
            'Reps': _get(reps, i),
            'RIR': _get(rirs, i),
        })
    df_last = pd.DataFrame(recs)
    peso_medio = float(pd.to_numeric(df_last['Peso (kg)'], errors='coerce').dropna().mean() or 0.0)
    rir_vals = pd.to_numeric(df_last['RIR'], errors='coerce').dropna()
    rir_medio = float(rir_vals.mean()) if not rir_vals.empty else 2.0
    data_ultima = str(row.get('Data', '—'))
    return df_last, peso_medio, rir_medio, data_ultima


def sugerir_carga(peso_medio: float, rir_medio: float, rir_alvo_num: float, passo_up: float = 0.025, passo_down: float = 0.05):
    try:
        p = float(peso_medio)
    except Exception:
        return 0.0
    if p <= 0:
        return 0.0
    try:
        rm = float(rir_medio)
    except Exception:
        rm = float(rir_alvo_num)
    try:
        rt = float(rir_alvo_num)
    except Exception:
        rt = 2.0

    # Se o RIR foi alto demais, sobe; se ficou baixo demais, baixa um pouco.
    if rm >= rt + 0.75:
        p = p * (1.0 + float(passo_up))
    elif rm <= rt - 0.75:
        p = p * (1.0 - float(passo_down))
    # arredonda ao 0.5 mais próximo para facilitar no ginásio
    p = round(p * 2) / 2.0
    return max(0.0, float(p))


def salvar_sets_agrupados(perfil, dia, bloco, ex, lista_sets, req, justificativa=""):
    """Grava um exercício (várias séries agregadas numa linha). Retorna True/False."""
    lista_sets = list(lista_sets or [])
    if not lista_sets:
        return False

    # anti-duplo-toque simples (mobile)
    try:
        payload_sig = f"{perfil}|{dia}|{bloco}|{ex}|{[(round(float(s.get('peso',0)),2), int(s.get('reps',0)), round(float(s.get('rir',0)),1)) for s in lista_sets]}"
        sig = hashlib.sha1(payload_sig.encode('utf-8')).hexdigest()
        now_ts = time.time()
        if st.session_state.get('_last_save_sig') == sig and (now_ts - float(st.session_state.get('_last_save_sig_ts', 0))) < 4.0:
            st.session_state['last_save_status'] = 'warn_duplicate'
            return False
        st.session_state['_last_save_sig'] = sig
        st.session_state['_last_save_sig_ts'] = now_ts
    except Exception:
        pass

    req = req or {}
    justificativa = str(justificativa or '').strip()
    xp, checklist_ok = checklist_xp(req, justificativa)

    today = datetime.date.today()
    data_str = today.strftime('%d/%m/%Y')
    # NÃO forçar leitura da Google Sheet no momento do save (evita 429 durante o treino em mobile)
    df_now = st.session_state.get("_df_cache_data")
    if not isinstance(df_now, pd.DataFrame):
        try:
            df_now = _load_offline_backup()
        except Exception:
            df_now = pd.DataFrame(columns=SCHEMA_COLUMNS)
    streak = _compute_streak_if_add_today(df_now, str(perfil), today)

    pesos = [float(s.get('peso', 0) or 0) for s in lista_sets]
    repss = [int(float(s.get('reps', 0) or 0)) for s in lista_sets]
    rirs  = [float(s.get('rir', 0) or 0) for s in lista_sets]

    row = {
        'Data': data_str,
        'Perfil': str(perfil),
        'Dia': str(dia),
        'Bloco': str(bloco),
        'Plano_ID': str(st.session_state.get('plano_id_sel', 'Base')),
        'Exercício': str(ex),
        'Peso': _join_num_list(pesos, decimals=1),
        'Reps': _join_num_list(repss, decimals=0),
        'RIR': _join_num_list(rirs, decimals=1),
        'Notas': justificativa,
        'Aquecimento': bool(req.get('aquecimento', False)),
        'Mobilidade': bool(req.get('mobilidade', False)),
        'Cardio': bool(req.get('cardio', False)),
        'Tendões': bool(req.get('tendoes', False)),
        'Core': bool(req.get('core', False)),
        'Cooldown': bool(req.get('cooldown', False)),
        'XP': int(xp),
        'Streak': int(streak),
        'Checklist_OK': bool(checklist_ok),
    }
    df_row = pd.DataFrame([row], columns=SCHEMA_COLUMNS)
    ok, err = safe_append_rows(df_row)

    # atualiza cache local em sessão para evitar reads imediatas à API
    try:
        if ok:
            _cached = st.session_state.get('_df_cache_data')
            if isinstance(_cached, pd.DataFrame):
                st.session_state['_df_cache_data'] = pd.concat([_cached, df_row], ignore_index=True)
                st.session_state['_df_cache_ts'] = time.time()
    except Exception:
        pass

    if ok:
        st.session_state['last_save_status'] = 'ok'
        st.session_state['last_save_error_msg'] = ''
        return True
    else:
        st.session_state['last_save_status'] = 'error'
        st.session_state['last_save_error_msg'] = str(err or '')
        if err:
            # mensagem curta; evita stacktrace no mobile
            msg = 'Falha ao gravar na Google Sheet. Ficou em backup local e podes sincronizar depois.'
            if '429' in str(err) or 'RATE_LIMIT' in str(err):
                msg += ' (Quota de leituras do Google Sheets excedida. Espera ~1 min.)'
            st.warning(msg)
        return False


def calcular_rank(xp_total: int, streak_max: int, checklist_rate: float):
    xp_total = int(xp_total or 0)
    streak_max = int(streak_max or 0)
    checklist_rate = float(checklist_rate or 0.0)
    score = xp_total + (streak_max * 40) + (checklist_rate * 400)
    if score >= 5000 or (xp_total >= 2500 and checklist_rate >= 0.9):
        return '💎 PLATINA', 'Consistência de elite'
    if score >= 2500:
        return '🥇 OURO', 'Muito consistente'
    if score >= 1000:
        return '🥈 PRATA', 'Boa base criada'
    return '🥉 BRONZE', 'A construir consistência'


def add_calendar_week(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=list(df.columns) + ['Data_dt','Semana_ID']) if isinstance(df, pd.DataFrame) else pd.DataFrame()
    out = df.copy()
    out['Data_dt'] = pd.to_datetime(out['Data'], dayfirst=True, errors='coerce')
    out = out.dropna(subset=['Data_dt']).copy()
    if out.empty:
        return out
    iso = out['Data_dt'].dt.isocalendar()
    out['ISO_Ano'] = iso['year'].astype(int)
    out['ISO_Semana'] = iso['week'].astype(int)
    out['Semana_ID'] = out['ISO_Ano'].astype(str) + '-W' + out['ISO_Semana'].astype(str).str.zfill(2)
    return out


def series_count_row(row):
    reps = [r for r in _parse_num_list(row.get('Reps')) if r > 0]
    return int(len(reps))


def tonnage_row(row):
    pesos = _parse_num_list(row.get('Peso'))
    reps = _parse_num_list(row.get('Reps'))
    if not pesos or not reps:
        return 0.0
    if len(pesos) == 1 and len(reps) > 1:
        pesos = pesos * len(reps)
    n = min(len(pesos), len(reps))
    return float(sum(max(0.0, float(pesos[i])) * max(0.0, float(reps[i])) for i in range(n)))


def avg_rir_row(row):
    rirs = _parse_num_list(row.get('RIR'))
    if not rirs:
        return 0.0
    return float(sum(rirs) / len(rirs))


def best_1rm_row(row):
    pesos = _parse_num_list(row.get('Peso'))
    reps = _parse_num_list(row.get('Reps'))
    if not pesos or not reps:
        return 0.0
    if len(pesos) == 1 and len(reps) > 1:
        pesos = pesos * len(reps)
    n = min(len(pesos), len(reps))
    best = 0.0
    for i in range(n):
        w = float(pesos[i])
        r = float(reps[i])
        if w <= 0 or r <= 0:
            continue
        # Epley (simples). Para reps muito altas fica pouco fiável, mas serve como tendência.
        est = w * (1.0 + min(r, 15.0)/30.0)
        if est > best:
            best = est
    return float(best)


# --- PLANO (8 semanas) ---
def semana_label(w):
    if w in [1,2,3]:
        return f"Semana {w} — Construção"
    if w == 4:
        return "Semana 4 — DELOAD"
    if w in [5,6,7]:
        return f"Semana {w} — Construção 2"
    return "Semana 8 — DELOAD / Refresh"

def is_deload(week):
    return week in [4,8]

def is_intensify_hypertrophy(week):
    return week in [3,7]

def rir_alvo(item_tipo, bloco, week):
    if bloco == "ABC":
        return "2"
    if bloco == "Força":
        return "2–3"
    if bloco == "Hipertrofia":
        if is_deload(week):
            return "3–4"
        if is_intensify_hypertrophy(week):
            return "1" if item_tipo == "composto" else "0–1"
        return "2" if item_tipo == "composto" else "1–2"
    return "—"

def rir_alvo_num(item_tipo, bloco, week):
    s = rir_alvo(item_tipo, bloco, week)
    if "–" in s:
        a,b = s.split("–")
        try:
            return (float(a)+float(b))/2
        except Exception:
            return 2.0
    try:
        return float(s)
    except Exception:
        return 2.0

def tempo_exec(item_tipo):
    return "2–0–1" if item_tipo == "composto" else "3–0–1"

def descanso_recomendado_s(item_tipo, bloco):
    if bloco == "Força":
        return 180
    if bloco == "ABC":
        return 75
    if item_tipo == "composto":
        return 120
    return 60

treinos_base = {
    "Segunda — UPPER FORÇA": {
        "bloco": "Força",
        "sessao": "75–95 min",
        "protocolos": {"tendoes": True, "core": False, "cardio": True, "cooldown": True},
        "exercicios": [
            {"ex":"Supino com pausa (1s no peito)", "series":4, "reps":"4-5", "tipo":"composto"},
            {"ex":"Barra fixa com peso (pegada neutra)", "series":4, "reps":"4-6", "tipo":"composto"},
            {"ex":"Remada apoiada / chest-supported", "series":3, "reps":"5-6", "tipo":"composto"},
            {"ex":"DB OHP neutro (sentado, encosto)", "series":3, "reps":"6", "tipo":"composto"},
            {"ex":"Elevação lateral (polia unilateral)", "series":3, "reps":"12-15", "tipo":"isolado"},
            {"ex":"Face pull", "series":2, "reps":"15-20", "tipo":"isolado"},
        ]
    },
    "Terça — LOWER FORÇA": {
        "bloco": "Força",
        "sessao": "75–95 min",
        "protocolos": {"tendoes": False, "core": True, "cardio": False, "cooldown": True},
        "exercicios": [
            {"ex":"Trap Bar Deadlift (ou Deadlift)", "series":4, "reps":"3-5", "tipo":"composto"},
            {"ex":"Bulgarian Split Squat (passo longo)", "series":3, "reps":"5-6", "tipo":"composto"},
            {"ex":"Hip Thrust (barra)", "series":4, "reps":"5", "tipo":"composto"},
            {"ex":"Nordic (amplitude controlada)", "series":3, "reps":"5-6", "tipo":"isolado"},
            {"ex":"Panturrilha em pé (pesado)", "series":3, "reps":"6-8", "tipo":"isolado"},
        ]
    },
    "Quarta — DESCANSO (Fisio em casa)": {
        "bloco": "Fisio",
        "sessao": "12–20 min",
        "protocolos": {"tendoes": False, "core": True, "cardio": False, "cooldown": False},
        "exercicios": []
    },
    "Quinta — UPPER HIPERTROFIA (costas/ombros/braços)": {
        "bloco": "Hipertrofia",
        "sessao": "75–95 min",
        "protocolos": {"tendoes": True, "core": False, "cardio": True, "cooldown": True},
        "exercicios": [
            {"ex":"Puxada na polia (pegada neutra)", "series":3, "reps":"8-12", "tipo":"composto"},
            {"ex":"Remada baixa (pausa 1s com ombro baixo)", "series":4, "reps":"8-12", "tipo":"composto"},
            {"ex":"Pulldown braço reto (straight-arm)", "series":3, "reps":"12-15", "tipo":"isolado"},
            {"ex":"Elevação lateral (halter/polia)", "series":4, "reps":"12-20", "tipo":"isolado"},
            {"ex":"Rear delt machine / reverse pec deck", "series":3, "reps":"15-20", "tipo":"isolado"},
            {"ex":"Rosca inclinado (halter)", "series":3, "reps":"10-12", "tipo":"isolado"},
            {"ex":"Tríceps corda (ou barra V se cotovelo)", "series":3, "reps":"12-15", "tipo":"isolado"},
        ]
    },
    "Sexta — LOWER HIPERTROFIA (glúteo dominante)": {
        "bloco": "Hipertrofia",
        "sessao": "90–110 min",
        "protocolos": {"tendoes": False, "core": True, "cardio": False, "cooldown": True},
        "exercicios": [
            {"ex":"Hip Thrust", "series":4, "reps":"8-10", "tipo":"composto"},
            {"ex":"Leg Press (pés altos e abertos)", "series":3, "reps":"10-12", "tipo":"composto"},
            {"ex":"RDL (halter/barra até neutro perfeito)", "series":3, "reps":"8-10", "tipo":"composto"},
            {"ex":"Back extension 45° (glúteo bias)", "series":3, "reps":"12-15", "tipo":"isolado"},
            {"ex":"Abdução máquina", "series":4, "reps":"15-25", "tipo":"isolado"},
            {"ex":"Panturrilha sentado", "series":3, "reps":"12-15", "tipo":"isolado"},
        ]
    },
    "Sábado — UPPER HIPERTROFIA (peito/ombros + estabilidade)": {
        "bloco": "Hipertrofia",
        "sessao": "90–110 min",
        "protocolos": {"tendoes": True, "core": False, "cardio": True, "cooldown": True},
        "exercicios": [
            {"ex":"Supino inclinado (halter)", "series":4, "reps":"8-10", "tipo":"composto"},
            {"ex":"Máquina convergente de peito", "series":3, "reps":"10-12", "tipo":"composto"},
            {"ex":"Crossover na polia (alto → baixo)", "series":3, "reps":"12-15", "tipo":"isolado"},
            {"ex":"Elevação lateral (myo-reps opcional)", "series":3, "reps":"15-20", "tipo":"isolado"},
            {"ex":"Rear delt (cabo/máquina)", "series":3, "reps":"15-20", "tipo":"isolado"},
            {"ex":"Remada leve apoiada (saúde escapular)", "series":2, "reps":"12", "tipo":"isolado"},
            {"ex":"Bíceps (cabo)", "series":2, "reps":"12-15", "tipo":"isolado"},
            {"ex":"Tríceps overhead cabo (amplitude curta)", "series":2, "reps":"12-15", "tipo":"isolado"},
        ]
    },
    "Domingo — DESCANSO (caminhada leve)": {
        "bloco": "Fisio",
        "sessao": "opcional",
        "protocolos": {"tendoes": False, "core": False, "cardio": True, "cooldown": False},
        "exercicios": []
    },
}

# --- PLANO INEIX (A/B/C 3x por semana — RIR 2 fixo, descanso 60–90s) ---
treinos_ineix_gym = {
    "Treino A — Glúteo/Posterior (Ginásio)": {
        "bloco": "ABC",
        "sessao": "45–70 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": False, "cooldown": True},
        "exercicios": [
            {"ex":"Leg press (pés altos)", "series":3, "reps":"10-12", "tipo":"composto"},
            {"ex":"Flexora (leg curl)", "series":3, "reps":"12-15", "tipo":"isolado"},
            {"ex":"Abdução de lado / cabo (por perna)", "series":3, "reps":"15-25", "tipo":"isolado"},
            {"ex":"Hip thrust com barra", "series":3, "reps":"8-12", "tipo":"composto"},
            {"ex":"Prancha (segundos)", "series":3, "reps":"20-40", "tipo":"isolado"},
        ]
    },
    "Treino B — Costas/Postura + Core (Ginásio)": {
        "bloco": "ABC",
        "sessao": "45–70 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": False, "cooldown": True},
        "exercicios": [
            {"ex":"Puxada na polia", "series":3, "reps":"10-12", "tipo":"composto"},
            {"ex":"Remada sentada", "series":3, "reps":"10-12", "tipo":"composto"},
            {"ex":"Face pull", "series":3, "reps":"12-15", "tipo":"isolado"},
            {"ex":"Chest press (leve)", "series":2, "reps":"10-12", "tipo":"composto"},
            {"ex":"Dead bug (reps por lado)", "series":3, "reps":"8-12", "tipo":"isolado"},
            {"ex":"Wall slides", "series":2, "reps":"8-12", "tipo":"isolado"},
        ]
    },
    "Treino C — Glúteo + Cardio Z2 (Ginásio)": {
        "bloco": "ABC",
        "sessao": "50–80 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": True, "cooldown": True},
        "exercicios": [
            {"ex":"Leg press (leve)", "series":3, "reps":"12-15", "tipo":"composto"},
            {"ex":"Flexora (leg curl)", "series":3, "reps":"12-15", "tipo":"isolado"},
            {"ex":"Abdução de lado / cabo (por perna)", "series":2, "reps":"20-30", "tipo":"isolado"},
            {"ex":"Puxada na polia", "series":2, "reps":"10-12", "tipo":"composto"},
        ]
    },
}

treinos_ineix_casa = {
    "Treino A — Glúteo/Posterior (Casa)": {
        "bloco": "ABC",
        "sessao": "35–60 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": False, "cooldown": True},
        "exercicios": [
            {"ex":"Ponte glúteo", "series":4, "reps":"12-20", "tipo":"composto"},
            {"ex":"Ponte unilateral (por perna)", "series":3, "reps":"8-12", "tipo":"composto"},
            {"ex":"Abdução de lado (por perna)", "series":3, "reps":"15-25", "tipo":"isolado"},
            {"ex":"Box squat (sofá) — sem dor", "series":3, "reps":"8-12", "tipo":"composto"},
            {"ex":"Prancha (segundos)", "series":3, "reps":"20-40", "tipo":"isolado"},
        ]
    },
    "Treino B — Costas/Postura + Core (Casa)": {
        "bloco": "ABC",
        "sessao": "35–60 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": False, "cooldown": True},
        "exercicios": [
            {"ex":"Flexão inclinada", "series":4, "reps":"6-15", "tipo":"composto"},
            {"ex":"Superman com puxada", "series":3, "reps":"10-15", "tipo":"isolado"},
            {"ex":"Anjos invertidos", "series":3, "reps":"10-15", "tipo":"isolado"},
            {"ex":"Wall slides", "series":3, "reps":"8-12", "tipo":"isolado"},
            {"ex":"Dead bug (reps por lado)", "series":3, "reps":"8-12", "tipo":"isolado"},
        ]
    },
    "Treino C — Circuito (Casa)": {
        "bloco": "ABC",
        "sessao": "35–60 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": True, "cooldown": True},
        "exercicios": [
            {"ex":"Ponte glúteo", "series":3, "reps":"12-20", "tipo":"composto"},
            {"ex":"Step-back curtinho (por perna) OU Box squat", "series":3, "reps":"8-12", "tipo":"composto"},
            {"ex":"Flexão inclinada", "series":3, "reps":"8-15", "tipo":"composto"},
            {"ex":"Marcha rápida (segundos)", "series":3, "reps":"30-45", "tipo":"isolado"},
            {"ex":"Prancha (segundos)", "series":3, "reps":"20-40", "tipo":"isolado"},
        ]
    },
}

treinos_ineix = {"Ginásio": treinos_ineix_gym, "Casa": treinos_ineix_casa}

PLANOS = {"Base": treinos_base, "INEIX_ABC_v1": treinos_ineix}

def gerar_treino_do_dia(dia, week, treinos_dict=None):
    treinos_dict = treinos_dict or treinos_base
    cfg = treinos_dict.get(dia, None)
    if not cfg:
        return {"bloco":"—","sessao":"","protocolos":{}, "exercicios":[]}
    bloco = cfg["bloco"]
    treino_final = []
    for item in cfg["exercicios"]:
        novo = dict(item)
        if is_deload(week) and bloco in ["Força","Hipertrofia"]:
            base_series = int(item["series"])
            if item["tipo"] == "composto":
                novo["series"] = max(2, int(round(base_series*0.6)))
            else:
                novo["series"] = max(1, int(round(base_series*0.6)))
        if week == 7 and bloco == "Hipertrofia" and item["tipo"] == "composto":
            novo["nota_semana"] = "Semana 7: 1ª série como TOP SET (RIR 1) + restantes back-off controlado."
        novo["rir_alvo"] = rir_alvo(item["tipo"], bloco, week)
        novo["tempo"] = tempo_exec(item["tipo"])
        novo["descanso_s"] = descanso_recomendado_s(item["tipo"], bloco)
        treino_final.append(novo)
    return {"bloco": bloco, "sessao": cfg["sessao"], "protocolos": cfg["protocolos"], "exercicios": treino_final}

# --- 6. INTERFACE SIDEBAR ---
st.sidebar.markdown("""
<div class="sidebar-seal">
  <h2 class="sidebar-seal-title">♣ GRIMÓRIO</h2>
  <p class="sidebar-seal-sub">Disciplina • Força • Hipertrofia</p>
</div>
""", unsafe_allow_html=True)

df_all = get_data()

# PERFIL
def _reset_daily_state():
    """Reseta checklists e inputs do dia quando muda Perfil/Semana/Dia (evita checks marcados por defeito)."""
    prefixes = ("chk_", "peso_", "reps_", "rir_", "rest_", "ineix_", "pt_")
    for k in list(st.session_state.keys()):
        if any(str(k).startswith(p) for p in prefixes):
            try:
                del st.session_state[k]
            except Exception:
                pass

st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
st.sidebar.markdown("<h3>👤 Perfil</h3>", unsafe_allow_html=True)

df_profiles, profiles_ok, profiles_err = get_profiles_df()

# lista de perfis (preferencialmente da worksheet Perfis)
perfis = []
if df_profiles is not None and not df_profiles.empty:
    perfis = sorted(df_profiles["Perfil"].dropna().astype(str).str.strip().unique().tolist())
else:
    # fallback: inferir do histórico (sem criar linhas fake)
    perfis = sorted([p for p in df_all["Perfil"].dropna().astype(str).unique().tolist() if p.strip() != ""])
    if not profiles_ok:
        st.sidebar.caption("⚠️ Para guardar perfis sem sujar o histórico, cria uma aba chamada **Perfis** na tua Google Sheet (e partilha com o service account).")

if not perfis:
    perfis = ["Principal"]

perfil_sel = st.sidebar.selectbox(
    "Perfil",
    perfis,
    index=0,
    key="perfil_sel",
    on_change=_reset_daily_state
)

# plano do perfil (preparado para ter planos diferentes no futuro)
plano_id_sel = get_plan_id_for_profile(perfil_sel, df_profiles) if df_profiles is not None else "Base"
if str(perfil_sel).strip().lower() == "ineix":
    plano_id_sel = "INEIX_ABC_v1"
if plano_id_sel not in PLANOS:
    plano_id_sel = "Base"
st.session_state["plano_id_sel"] = plano_id_sel
st.sidebar.caption(f"Plano ativo: **{plano_id_sel}**")
# UI móvel limpa: esconder utilitários de plano/perfis/Google Sheets (funcionam em background)
_ok_conn, _err_conn = True, ""
try:
    _ = conn.read(ttl="0")
except Exception as _e:
    _ok_conn, _err_conn = False, str(_e)

bk_df = _load_offline_backup()
pass  # sidebar divider removido

# SEMANA (8) — só para o plano Base (8 semanas)
is_ineix = (st.session_state.get("plano_id_sel","Base") == "INEIX_ABC_v1")
if not is_ineix:
    st.sidebar.markdown("<h3>🧭 Periodização (8 semanas)</h3>", unsafe_allow_html=True)
    semana_sel = st.sidebar.radio(
        "Semana do ciclo:",
        list(range(1,9)),
        format_func=semana_label,
        index=0,
        key="semana_sel",
        on_change=_reset_daily_state,
    )
    semana = semana_sel
    pass  # sidebar divider removido
else:
    # Plano Ineix (A/B/C) não usa periodização 8 semanas
    semana = 1
    pass  # sidebar divider removido

# DIA
# Plano ativo (preparado para suportar planos diferentes por perfil)
plan_id_active = st.session_state.get("plano_id_sel", "Base")
plan_obj = PLANOS.get(plan_id_active, treinos_base)

# Se for o plano Ineix, escolhe "Ginásio" vs "Casa" e usa o sub-plano certo
if plan_id_active == "INEIX_ABC_v1" and isinstance(plan_obj, dict):
    ineix_local = st.sidebar.radio("Local de treino", ["Ginásio","Casa"], key="ineix_local", horizontal=True, on_change=_reset_daily_state)
    treinos_dict = plan_obj.get(ineix_local, plan_obj.get("Ginásio", treinos_ineix_gym))
else:
    treinos_dict = plan_obj

dia = st.sidebar.selectbox("Treino", list(treinos_dict.keys()), index=0, key="dia_sel", on_change=_reset_daily_state)
st.sidebar.caption(f"⏱️ Sessão-alvo: **{treinos_dict[dia]['sessao']}**")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# FLAGS
st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
st.sidebar.markdown("<h3>🩺 Sinais do corpo</h3>", unsafe_allow_html=True)
dor_joelho = st.sidebar.checkbox("Dor no joelho (pontiaguda)", help="Se for dor pontiaguda/articular, a app sugere substituições (não é para ‘aguentar’).")
dor_cotovelo = st.sidebar.checkbox("Dor no cotovelo", help="Se o cotovelo estiver a reclamar, a app sugere variações mais amigáveis (ex.: pushdown barra V, amplitude menor).")
dor_ombro = st.sidebar.checkbox("Dor no ombro", help="Se o ombro estiver sensível, a app sugere ajustes (pega neutra, inclinação menor, sem grind).")
dor_lombar = st.sidebar.checkbox("Dor na lombar", help="Se a lombar estiver a dar sinal, a app sugere limitar amplitude e usar mais apoio/variações seguras.")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Modo mobile permanente (sem toggles na sidebar)
st.session_state["ui_compact_mode"] = False
st.session_state["ui_pure_mode"] = True
st.session_state["ui_show_last_table"] = True
st.session_state["ui_show_rules"] = True

def sugestao_articular(ex):
    if dor_joelho and ("Bulgarian" in ex or "Leg Press" in ex):
        return "Joelho: encurta amplitude / mais controlo. Dor pontiaguda = troca variação hoje."
    if dor_cotovelo and "Tríceps" in ex:
        return "Cotovelo: pushdown barra V, amplitude menor, excêntrico 3–4s."
    if dor_ombro and ("OHP" in ex or "Supino" in ex or "inclinado" in ex.lower()):
        return "Ombro: pega neutra, inclinação menor, sem grind."
    if dor_lombar and ("Deadlift" in ex or "RDL" in ex or "Remada" in ex):
        return "Lombar: limita amplitude ao neutro perfeito / usa mais apoio."
    return ""

# --- 7. CABEÇALHO ---
st.markdown("<div class='bc-main-title'>♣️Black Clover Training♣️</div>", unsafe_allow_html=True)
st.caption("A minha magia é não desistir 🗡️🖤")

try:
    _pl = st.session_state.get("plano_id_sel", "Base")
    _footer = f"{perfil_sel} • {dia} • {_pl}"
    st.markdown(f"""
    <div class='bc-float-bar bc-float-footer'>
      <span style='color:#E8E2E2;'>♣</span> {_footer}
    </div>
    """, unsafe_allow_html=True)
except Exception:
    pass

# --- 8. CORPO PRINCIPAL ---
tab_treino, tab_historico, tab_ranking = st.tabs(["🔥 Treino", "📊 Histórico", "🏅 Ranking"])

with tab_treino:
    pure_workout_mode = bool(st.session_state.get("ui_pure_mode", True))
    show_rules = (not pure_workout_mode) or bool(st.session_state.get("ui_show_rules", False))

    def _queue_auto_rest(seconds:int, ex_name:str=""):
        try:
            secs = max(1, int(seconds))
        except Exception:
            secs = 60
        st.session_state["rest_auto_seconds"] = secs
        st.session_state["rest_auto_from"] = str(ex_name or "")
        st.session_state["rest_auto_end_ts"] = float(time.time()) + float(secs)
        st.session_state["rest_auto_run"] = True
        st.session_state["rest_auto_notified"] = False
        st.session_state["scroll_to_rest_timer"] = True

    if st.session_state.get("rest_auto_run", False):
        st.markdown("<div id='rest-timer-anchor'></div>", unsafe_allow_html=True)
        total_rest = int(st.session_state.get("rest_auto_seconds", 60) or 60)
        ex_rest = str(st.session_state.get("rest_auto_from", ""))
        end_ts = float(st.session_state.get("rest_auto_end_ts", float(time.time()) + total_rest))
        rem_float = end_ts - float(time.time())
        rem = int(rem_float) if rem_float.is_integer() else int(rem_float) + (1 if rem_float > 0 else 0)
        rem = max(0, rem)
        elapsed = max(0, total_rest - rem)

        label = f"⏱️ Descanso • {ex_rest}" if ex_rest else "⏱️ Descanso"
        st.info(label)
        if bool(st.session_state.pop("scroll_to_rest_timer", False)):
            scroll_to_dom_id("rest-timer-anchor")
        ctm1, ctm2, ctm3, ctm4 = st.columns([1.7,1,1,1])
        ctm1.metric("Descanso", f"{rem}s")
        if ctm2.button("⏭️ -15s", key="rest_skip15", width='stretch', disabled=(rem <= 0)):
            novo_fim = max(float(time.time()), float(st.session_state.get("rest_auto_end_ts", end_ts)) - 15.0)
            st.session_state["rest_auto_end_ts"] = novo_fim
            st.rerun()
        if ctm3.button("⏭️ Total", key="rest_skip_all", width='stretch', disabled=(rem <= 0)):
            st.session_state["rest_auto_end_ts"] = float(time.time())
            st.rerun()
        if ctm4.button("⏹️ Parar", key="rest_stop", width='stretch', disabled=(rem <= 0)):
            st.session_state["rest_auto_run"] = False
            st.rerun()
        st.progress(min(1.0, elapsed / max(1, total_rest)), text=f"{elapsed}s / {total_rest}s")

        if rem <= 0:
            st.success("Descanso concluído ✅")
            if not bool(st.session_state.get("rest_auto_notified", False)):
                st.toast("Descanso concluído ✅")
                trigger_rest_done_feedback()
                st.session_state["rest_auto_notified"] = True
            st.session_state["rest_auto_run"] = False
        else:
            time.sleep(1)
            st.rerun()
    if show_rules:
        with st.expander("📜 Regras rápidas do plano"):
            if st.session_state.get("plano_id_sel","Base") == "INEIX_ABC_v1":
                st.markdown("""
**Plano Ineix (A/B/C 3x/sem):**  
**Intensidade:** RIR **2** em todas as séries (sem falhar).  
**Descanso:** **60–90s** (use o slider se precisares).  
**Tempo:** Compostos 2–0–1 | Isoladores 3–0–1  
Dor articular pontiaguda = troca variação no dia.
""")
            else:
                st.markdown("""
**Força (compostos):** RIR 2–3 sempre.  
**Hipertrofia:** RIR 2; semanas 3 e 7 → RIR 1 (isoladores podem 0–1).  
**Deload (sem 4 e 8):** -40 a -50% séries, -10 a -15% carga, RIR 3–4.  

**Tempo:** Compostos 2–0–1 | Isoladores 3–0–1  
**Descanso:** Força 2–4 min | Hiper compostos 90–150s | Isoladores 45–90s  
Dor articular pontiaguda = troca variação no dia.
""")
    elif pure_workout_mode:
        st.caption("Modo treino puro ativo: foco total no treino.")

    cfg = gerar_treino_do_dia(dia, semana, treinos_dict=treinos_dict)
    bloco = cfg["bloco"]

    _plano = str(st.session_state.get("plano_id_sel", "Base"))
    _local = str(st.session_state.get("ineix_local", "")) if _plano == "INEIX_ABC_v1" else ""
    _week_txt = "RIR 2 fixo" if _plano == "INEIX_ABC_v1" else semana_label(semana)
    _sessao_alvo = str(cfg.get("sessao", treinos_dict.get(dia, {}).get("sessao", "")))
    st.markdown(
        f"""
        <div class='bc-hero'>
          <div class='bc-hero-title'>📍 {html.escape(str(perfil_sel))} • {html.escape(str(dia))}</div>
          <div class='bc-chip-wrap'>
            <span class='bc-chip gold'>📘 {html.escape(_plano)}</span>
            <span class='bc-chip'>🧱 {html.escape(str(bloco))}</span>
            <span class='bc-chip'>🕒 Sessão {html.escape(_sessao_alvo)}</span>
            <span class='bc-chip red'>🎯 {html.escape(_week_txt)}</span>
            {f"<span class='bc-chip green'>📍 {html.escape(_local)}</span>" if _local else ""}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    prot = cfg["protocolos"]

    pure_nav_key = None
    pure_idx = 0
    if pure_workout_mode and bloco != "Fisio" and len(cfg.get("exercicios", [])) > 0:
        ex_names = [str(it.get("ex","")) for it in cfg["exercicios"]]
        pure_nav_key = f"pt_idx::{perfil_sel}::{st.session_state.get('plano_id_sel','Base')}::{dia}::{semana}"
        if pure_nav_key not in st.session_state:
            st.session_state[pure_nav_key] = 0
        max_idx = max(0, len(ex_names)-1)
        try:
            st.session_state[pure_nav_key] = int(st.session_state.get(pure_nav_key, 0))
        except Exception:
            st.session_state[pure_nav_key] = 0
        st.session_state[pure_nav_key] = max(0, min(max_idx, st.session_state[pure_nav_key]))
        pure_idx = int(st.session_state[pure_nav_key])

        def _set_pure_idx(_ix:int):
            _ix = max(0, min(max_idx, int(_ix)))
            st.session_state[pure_nav_key] = _ix
            st.session_state[f"pt_pick_{pure_nav_key}"] = _ix
            st.session_state["scroll_to_ex_nav"] = True

        st.session_state.setdefault(f"pt_pick_{pure_nav_key}", pure_idx)
        # garante que o select acompanha navegação automática/botões
        st.session_state[f"pt_pick_{pure_nav_key}"] = int(st.session_state.get(pure_nav_key, pure_idx))

        _done_ex = 0
        for _ix, _it in enumerate(cfg["exercicios"]):
            _done_key = f"pt_done::{perfil_sel}::{dia}::{_ix}"
            try:
                _done_val = int(st.session_state.get(_done_key, 0) or 0)
            except Exception:
                _done_val = 0
            if _done_val >= int(_it.get("series", 0) or 0):
                _done_ex += 1
        render_progress_compact(_done_ex, len(cfg["exercicios"]))

        st.markdown("<div id='exercise-nav-anchor'></div>", unsafe_allow_html=True)
        nav1, nav2, nav3 = st.columns([1,2,1])
        if nav1.button("← Anterior", key=f"pt_prev_{dia}", width='stretch', disabled=(pure_idx <= 0)):
            _set_pure_idx(pure_idx - 1)
            st.rerun()
        _picked = nav2.selectbox(
            "Exercício atual",
            list(range(len(ex_names))),
            index=int(st.session_state.get(f"pt_pick_{pure_nav_key}", pure_idx)),
            format_func=lambda ix: f"{ix+1}/{len(ex_names)} • {ex_names[ix]}",
            key=f"pt_pick_{pure_nav_key}",
            label_visibility="collapsed"
        )
        try:
            pure_idx = int(_picked)
        except Exception:
            pure_idx = int(st.session_state.get(pure_nav_key, 0))
        pure_idx = max(0, min(max_idx, pure_idx))
        st.session_state[pure_nav_key] = pure_idx
        if nav3.button("Seguinte →", key=f"pt_next_{dia}", width='stretch', disabled=(pure_idx >= max_idx)):
            _set_pure_idx(pure_idx + 1)
            st.rerun()
        if bool(st.session_state.pop("scroll_to_ex_nav", False)):
            scroll_to_dom_id("exercise-current-anchor")
        try:
            _pt_pending = st.session_state.get(f"pt_sets::{perfil_sel}::{dia}::{pure_idx}", [])
            if not isinstance(_pt_pending, list):
                _pt_pending = []
            done_now = len(_pt_pending)
        except Exception:
            done_now = 0
        total_series_cur = int(cfg["exercicios"][pure_idx]["series"])
        serie_txt = "Concluído ✅" if done_now >= total_series_cur else f"Série {done_now+1}/{total_series_cur}"
        st.markdown(f"""
        <div class='bc-float-bar bc-float-status'>
          <b style='color:#E8E2E2;'>Ex {pure_idx+1}/{len(ex_names)}</b> · {html.escape(ex_names[pure_idx])} · {serie_txt}
        </div>
        """, unsafe_allow_html=True)

    def _get_req_state_from_session():
        return {
            "aquecimento_req": True,
            "mobilidade_req": True,
            "cardio_req": bool(prot.get("cardio", False)),
            "tendoes_req": bool(prot.get("tendoes", False)),
            "core_req": bool(prot.get("core", False)),
            "cooldown_req": bool(prot.get("cooldown", True)),
            "aquecimento": bool(st.session_state.get("chk_aquecimento", False)),
            "mobilidade": bool(st.session_state.get("chk_mobilidade", False)),
            "cardio": bool(st.session_state.get("chk_cardio", False)),
            "tendoes": bool(st.session_state.get("chk_tendoes", False)),
            "core": bool(st.session_state.get("chk_core", False)),
            "cooldown": bool(st.session_state.get("chk_cooldown", False)),
        }

    req = _get_req_state_from_session()
    justificativa = str(st.session_state.get("chk_justif", "") or "")
    _save_status = st.session_state.get("last_save_status")
    if _save_status == "error":
        _save_err_msg = str(st.session_state.get("last_save_error_msg", "") or "")
        msg = "Último exercício não foi para a Google Sheet (ficou em backup local)."
        if ("429" in _save_err_msg) or ("RATE_LIMIT" in _save_err_msg):
            msg += " Quota do Google Sheets excedida (espera ~1 min)."
        st.warning(msg)
    elif _save_status == "ok":
        st.caption("✅ Último exercício guardado na Google Sheet.")
    elif _save_status == "warn_duplicate":
        st.caption("⚠️ Toque duplicado bloqueado (não gravou de novo).")

    pass  # divider removed

    if bloco == "Fisio":
        st.subheader("🏠 Fisio / Recuperação")
        if "Quarta" in dia:
            st.markdown("""
**12–20 min (opcional):**
- Bird dog 2×6/lado (pausa 2s)
- Side plank 2×30–45s (+1 lado fraco)
- McGill curl-up 2×8–10 (pausa 2s)
- Dead hang 2×20–30s
- Respiração 90/90 2 min
- Caminhada 15–30 min
""")
        else:
            st.markdown("Caminhada leve + mobilidade.")
    else:

        if bloco in ["Força","Hipertrofia"]:
            if semana in [2,6]:
                st.info("Progressão: +1 rep por série OU +2,5–5% carga mantendo o RIR alvo.")
            if semana in [4,8]:
                st.warning("DELOAD: menos séries e mais leve. Técnica e tendões em 1º lugar.")
            if semana == 7 and bloco == "Hipertrofia":
                st.info("Semana 7: TOP SET (RIR 1) + back-off controlado nos compostos.")
        df_now = df_all.copy() if isinstance(df_all, pd.DataFrame) else get_data()
        for i,item in enumerate(cfg["exercicios"]):
            if pure_workout_mode and pure_nav_key is not None and i != pure_idx:
                continue
            ex = item["ex"]
            rir_target_str = item["rir_alvo"]
            rir_target_num = rir_alvo_num(item["tipo"], bloco, semana)

            df_last, peso_medio, rir_medio, data_ultima = get_historico_detalhado(df_now, perfil_sel, ex)

            passo_up = 0.05 if ("Deadlift" in ex or "Leg Press" in ex or "Hip Thrust" in ex) else 0.025
            peso_sug = sugerir_carga(peso_medio, rir_medio, rir_target_num, passo_up, 0.05)

            reps_low = int(str(item["reps"]).split("-")[0]) if "-" in str(item["reps"]) else int(float(item["reps"]))

            with st.expander(f"{i+1}. {ex}", expanded=(i==0 or (pure_workout_mode and pure_nav_key is not None and i == pure_idx))):
                if pure_workout_mode and pure_nav_key is not None and i == pure_idx:
                    st.markdown("<div id='exercise-current-anchor'></div>", unsafe_allow_html=True)
                st.markdown(f"**Meta:** {item['series']}×{item['reps']}   •  **RIR alvo:** {rir_target_str}")
                st.caption(f"⏱️ Tempo {item['tempo']} · Descanso ~{item['descanso_s']}s")

                _last_chip = _latest_set_summary_from_df_last(df_last)
                if _last_chip:
                    st.markdown(f"<div class='bc-last-chip'>⏮️ {_last_chip}</div>", unsafe_allow_html=True)

                if pure_workout_mode and pure_nav_key is not None:
                    done_key = f"pt_done::{perfil_sel}::{dia}::{i}"
                    series_key = f"pt_sets::{perfil_sel}::{dia}::{i}"
                    pending_sets = st.session_state.get(series_key, [])
                    if not isinstance(pending_sets, list):
                        pending_sets = []
                    done_series = len(pending_sets)
                    total_series = int(item["series"])
                    done_series = max(0, min(total_series, done_series))
                    st.progress(done_series / max(1, total_series), text=f"Séries feitas: {done_series}/{total_series}")
                    if st.button("↺ Reset séries", key=f"pt_reset_{i}", width='stretch'):
                        st.session_state[series_key] = []
                        st.session_state[done_key] = 0
                        st.rerun()

                art = sugestao_articular(ex)
                if art:
                    st.warning(art)
                if item.get("nota_semana"):
                    st.info(item["nota_semana"])

                ui_compact = bool(st.session_state.get("ui_compact_mode", True))
                ui_show_last_table = bool(st.session_state.get("ui_show_last_table", False))

                if df_last is not None:
                    st.markdown(f"📜 **Último registo ({data_ultima})**")
                    st.caption(f"Último: peso médio ~ {peso_medio:.1f} kg | RIR médio ~ {rir_medio:.1f}")
                    if (not ui_compact) or ui_show_last_table:
                        st.dataframe(df_last, hide_index=True, width='stretch')
                else:
                    st.caption("Sem registos anteriores para este exercício (neste perfil).")

                if _double_progression_ready(df_last, item['reps'], rir_target_num):
                    inc = 5 if _is_lower_exercise(ex) else 2
                    st.success(f"✅ Progressão dupla: bateste o topo da faixa. Próxima sessão: tenta **+{inc} kg** (ou mínimo disponível).")

                if peso_sug > 0:
                    with st.popover("🎯 Sugestão de carga"):
                        st.markdown(f"**Carga sugerida (média):** {peso_sug} kg")
                        st.caption("Se o RIR fugir do alvo, ajusta na hora. Técnica primeiro.")

                pre1, pre2 = st.columns(2)
                if pre1.button("↺ Usar último", key=f"pref_last_{i}", width='stretch'):
                    _prefill_sets_from_last(i, item, df_last, peso_sug, reps_low, rir_target_num)
                    st.rerun()
                if pre2.button("🎯 Usar sugestão", key=f"pref_sug_{i}", width='stretch'):
                    _prefill_sets_from_last(i, item, None, peso_sug, reps_low, rir_target_num)
                    st.rerun()

                if pure_workout_mode and pure_nav_key is not None:
                    series_key = f"pt_sets::{perfil_sel}::{dia}::{i}"
                    pending_sets = st.session_state.get(series_key, [])
                    if not isinstance(pending_sets, list):
                        pending_sets = []
                    total_series = int(item["series"])
                    current_s = len(pending_sets)

                    if pending_sets:
                        st.caption("Séries já lançadas neste exercício:")
                        try:
                            _df_pending = pd.DataFrame(pending_sets)
                            _df_pending.index = [f"S{ix+1}" for ix in range(len(_df_pending))]
                            st.dataframe(_df_pending, width='stretch')
                        except Exception:
                            pass

                    if current_s < total_series:
                        kg_step = 5.0 if _is_lower_exercise(ex) else 2.0
                        s = current_s
                        with st.form(key=f"form_pure_{i}_{s}"):
                            st.markdown(f'<div class="bc-serie-badge">Série {s+1}/{total_series}</div>', unsafe_allow_html=True)
                            default_peso = float(peso_sug) if peso_sug > 0 else 0.0
                            if pending_sets:
                                try:
                                    default_peso = float(pending_sets[-1].get("peso", default_peso) or default_peso)
                                except Exception:
                                    pass
                            peso = st.number_input(
                                f"Kg • S{s+1}", min_value=0.0,
                                value=float(default_peso), step=float(kg_step), key=f"peso_{i}_{s}"
                            )
                            rcol1, rcol2 = st.columns(2)
                            reps = rcol1.number_input(
                                f"Reps • S{s+1}", min_value=0, value=int(reps_low), step=1, key=f"reps_{i}_{s}"
                            )
                            rir = rcol2.number_input(
                                f"RIR • S{s+1}", min_value=0.0, max_value=6.0,
                                value=float(rir_target_num), step=0.5, key=f"rir_{i}_{s}"
                            )

                            is_last = (s == total_series - 1)
                            is_last_ex = (i == len(cfg["exercicios"]) - 1)
                            if is_last and is_last_ex:
                                btn_label = "Guardar última série + terminar"
                            elif is_last:
                                btn_label = "Guardar última série + avançar"
                            else:
                                btn_label = "Guardar série + descanso"
                            submitted = st.form_submit_button(btn_label, width='stretch')
                            if submitted:
                                novos_sets = list(pending_sets) + [{"peso": peso, "reps": reps, "rir": rir}]
                                st.session_state[series_key] = novos_sets
                                st.session_state[f"rest_{i}"] = int(item["descanso_s"])

                                if is_last:
                                    ok_gravou = salvar_sets_agrupados(perfil_sel, dia, bloco, ex, novos_sets, req, justificativa)
                                    if ok_gravou:
                                        st.session_state[series_key] = []
                                        try:
                                            st.session_state[f"pt_done::{perfil_sel}::{dia}::{i}"] = int(item["series"])
                                        except Exception:
                                            pass
                                        if is_last_ex:
                                            st.session_state["session_finished_flash"] = True
                                            st.success("Último exercício guardado. Treino pronto ✅")
                                        else:
                                            _set_pure_idx(min(len(cfg["exercicios"]) - 1, i + 1))
                                            _queue_auto_rest(int(item["descanso_s"]), ex)
                                            st.success("Exercício guardado. A seguir…")
                                        time.sleep(0.35)
                                        st.rerun()
                                else:
                                    _queue_auto_rest(int(item["descanso_s"]), ex)
                                    st.rerun()
                    else:
                        st.success("Exercício concluído.")
                        if st.button("Tentar guardar agora", key=f"pt_retry_save_{i}", width='stretch'):
                            ok_gravou = salvar_sets_agrupados(perfil_sel, dia, bloco, ex, pending_sets, req, justificativa)
                            if ok_gravou:
                                st.session_state[series_key] = []
                                try:
                                    st.session_state[f"pt_done::{perfil_sel}::{dia}::{i}"] = int(item["series"])
                                except Exception:
                                    pass
                                is_last_ex2 = (i == len(cfg["exercicios"]) - 1)
                                if is_last_ex2:
                                    st.session_state["session_finished_flash"] = True
                                    st.success("Último exercício guardado. Treino pronto ✅")
                                else:
                                    _set_pure_idx(min(len(cfg["exercicios"]) - 1, i + 1))
                                    _queue_auto_rest(int(item["descanso_s"]), ex)
                                    st.success("Exercício guardado. A seguir…")
                                time.sleep(0.35)
                                st.rerun()
                else:
                    lista_sets = []
                    with st.form(key=f"form_{i}"):
                        kg_step = 5.0 if _is_lower_exercise(ex) else 2.0
                        for s in range(item["series"]):
                            st.markdown(f"### Série {s+1}")
                            peso = st.number_input(f"Kg • S{s+1}", min_value=0.0,
                                                   value=float(peso_sug) if peso_sug>0 else 0.0,
                                                   step=float(kg_step), key=f"peso_{i}_{s}")
                            rcol1, rcol2 = st.columns(2)
                            reps = rcol1.number_input(f"Reps • S{s+1}", min_value=0, value=int(reps_low),
                                                      step=1, key=f"reps_{i}_{s}")
                            rir = rcol2.number_input(f"RIR • S{s+1}", min_value=0.0, max_value=6.0,
                                                     value=float(rir_target_num), step=0.5, key=f"rir_{i}_{s}")
                            lista_sets.append({"peso":peso,"reps":reps,"rir":rir})

                        if st.form_submit_button("💾 Gravar exercício", width='stretch'):
                            ok_gravou = salvar_sets_agrupados(perfil_sel, dia, bloco, ex, lista_sets, req, justificativa)
                            if ok_gravou:
                                if pure_workout_mode and pure_nav_key is not None:
                                    try:
                                        st.session_state[f"pt_done::{perfil_sel}::{dia}::{i}"] = int(item["series"])
                                    except Exception:
                                        pass
                                    _set_pure_idx(min(len(cfg["exercicios"]) - 1, i + 1))
                                st.success("Exercício gravado!")
                                time.sleep(0.4)
                                st.rerun()

        pass  # divider removed

        if prot.get("tendoes", False):
            with st.expander("🦾 Protocolo de tendões (8–12 min)"):
                st.markdown("""
**Isométricos**
- Tríceps isométrico na polia: 2×30–45s  
- External rotation isométrico: 2×30s/lado  
- (Joelho) Spanish squat: 2–3×30–45s  

**Excêntricos**
- Wrist extension excêntrico: 2×12 (3–4s descida)  
- Tibial raises: 2×15–20
""")
        if prot.get("core", False):
            with st.expander("🧱 Core escoliose (6–10 min)"):
                st.markdown("""
- McGill curl-up 2×8–10 (pausa 2s)
- Side plank 2×25–40s (+1 série lado fraco)
- Bird dog 2×6–8/lado (pausa 2s)
- Suitcase carry 2×20–30m/lado (se houver espaço)
""")

        st.markdown("### Checklist da sessão")

        req = _get_req_state_from_session()

        c1, c2 = st.columns(2)
        c1.checkbox(
            "🔥 Aquecimento",
            value=False,
            key="chk_aquecimento",
            help="Marca se fizeste o aquecimento (ex.: 4–5 min leves + ramp-up do primeiro exercício)."
        )
        c2.checkbox(
            "🧘 Mobilidade",
            value=False,
            key="chk_mobilidade",
            help="Marca se fizeste mobilidade/ativação (ombros, anca, escápulas)."
        )

        c3, c4 = st.columns(2)
        c3.checkbox(
            "🏃 Cardio Zona 2",
            value=False,
            key="chk_cardio",
            disabled=(not req.get("cardio_req", False)),
            help="Marca se fizeste cardio Zona 2 (ritmo em que ainda consegues falar)."
        )
        c4.checkbox(
            "🦾 Tendões",
            value=False,
            key="chk_tendoes",
            disabled=(not req.get("tendoes_req", False)),
            help="Marca se fizeste o protocolo de tendões (isométricos + excêntricos)."
        )

        c5, c6 = st.columns(2)
        c5.checkbox(
            "🧱 Core escoliose",
            value=False,
            key="chk_core",
            disabled=(not req.get("core_req", False)),
            help="Marca se fizeste o core anti-rotação (McGill curl-up, side plank, bird dog, suitcase carry)."
        )
        c6.checkbox(
            "😮‍💨 Cool-down",
            value=False,
            key="chk_cooldown",
            help="Marca se fizeste o cool-down (respiração 90/90 + alongamentos leves)."
        )

        st.caption("ℹ️ Checklist do que fizeste hoje. As caixas cinzentas não estão previstas para este dia/plano.")

        req = _get_req_state_from_session()
        justificativa = ""
        xp_pre, ok_checklist = checklist_xp(req, justificativa="")
        if not ok_checklist:
            st.info("Falta algum item obrigatório? Podes justificar para não perder XP.")
            justificativa = st.text_input("Justificativa", value=str(st.session_state.get("chk_justif", "")), key="chk_justif")
        else:
            # mantém o campo disponível no estado, sem mostrar ruído extra
            st.session_state.setdefault("chk_justif", str(st.session_state.get("chk_justif", "") or ""))
            justificativa = str(st.session_state.get("chk_justif", "") or "")
        xp_pre, ok_checklist = checklist_xp(req, justificativa=justificativa)

        df_now = get_data()
        streak_atual = get_last_streak(df_now, perfil_sel)

        m1,m2,m3 = st.columns(3)
        m1.metric("XP previsto", f"{xp_pre}")
        m2.metric("Checklist", "✅ Completo" if ok_checklist else "⚠️ Incompleto")
        m3.metric("Streak", f"{streak_atual}")

        # resumo final (aparece quando todos os exercícios estão concluídos)
        _done_ex_final = 0
        for _ix, _it in enumerate(cfg.get("exercicios", [])):
            try:
                _dv = int(st.session_state.get(f"pt_done::{perfil_sel}::{dia}::{_ix}", 0) or 0)
            except Exception:
                _dv = 0
            if _dv >= int(_it.get("series", 0) or 0):
                _done_ex_final += 1
        _total_ex_final = len(cfg.get("exercicios", []))
        _all_done = (_total_ex_final > 0 and _done_ex_final >= _total_ex_final)
        if _all_done:
            st.markdown(
                f"""
                <div class='bc-final-summary'>
                  <div class='ttl'>✅ Treino pronto</div>
                  <div class='sub'>Exercícios concluídos: <b>{_done_ex_final}/{_total_ex_final}</b> · Sessão alvo: <b>{html.escape(str(_sessao_alvo))}</b> · XP previsto: <b>{xp_pre}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if bool(st.session_state.pop("session_finished_flash", False)):
                st.toast("Treino concluído ✅")

        req_keys = [k for k in ["aquecimento","mobilidade","cardio","tendoes","core","cooldown"] if req.get(f"{k}_req", False)]
        done_req = sum(1 for k in req_keys if req.get(k, False))
        total_req = max(1, len(req_keys))
        st.progress(done_req/total_req, text=f"Checklist obrigatório: {done_req}/{total_req}")

        _finish_label = "✅ Terminar treino" if not _all_done else "✅ Terminar treino (concluído)"
        if st.button(_finish_label, type="primary"):
            st.balloons()
            time.sleep(1.2)
            st.rerun()

with tab_historico:
    st.header("Histórico do perfil 📊")

    df = get_data()
    dfp = df[df["Perfil"].astype(str) == str(perfil_sel)].copy()

    # ignora linhas de setup de perfis
    dfp = dfp[dfp["Bloco"].astype(str).str.lower() != "setup"]

    if dfp.empty:
        st.info("Ainda sem registos neste perfil.")
    else:
        # Filtros (mobile-first: empilhados)
        dias_opts = sorted(dfp["Dia"].dropna().astype(str).unique().tolist())
        blocos_opts = sorted(dfp["Bloco"].dropna().astype(str).unique().tolist())

        dias_filtrados = st.multiselect("Dia", dias_opts, default=[])
        blocos_filtrados = st.multiselect("Bloco", blocos_opts, default=[])
        ex_opts = sorted(dfp["Exercício"].dropna().astype(str).unique().tolist()) if "Exercício" in dfp.columns else []
        ex_filtro = st.multiselect("Exercício", ex_opts, default=[])

        datas_dt = pd.to_datetime(dfp["Data"], dayfirst=True, errors="coerce").dropna()
        if not datas_dt.empty:
            dmin = datas_dt.min().date()
            dmax = datas_dt.max().date()
            intervalo = st.date_input("Datas", value=(dmin, dmax))
            try:
                if isinstance(intervalo, (list, tuple)) and len(intervalo) == 2:
                    di, df_ = intervalo[0], intervalo[1]
                    dfp["_Data_dt"] = pd.to_datetime(dfp["Data"], dayfirst=True, errors="coerce")
                    dfp = dfp.dropna(subset=["_Data_dt"])
                    dfp = dfp[(dfp["_Data_dt"].dt.date >= di) & (dfp["_Data_dt"].dt.date <= df_)]
                    dfp = dfp.drop(columns=["_Data_dt"])
            except Exception:
                pass

        if dias_filtrados:
            dfp = dfp[dfp["Dia"].astype(str).isin([str(x) for x in dias_filtrados])]
        if blocos_filtrados:
            dfp = dfp[dfp["Bloco"].astype(str).isin([str(x) for x in blocos_filtrados])]
        if ex_filtro:
            dfp = dfp[dfp["Exercício"].astype(str).isin([str(x) for x in ex_filtro])]

        if dfp.empty:
            st.info("Sem registos com esses filtros.")
            st.stop()

        xp_total = int(pd.to_numeric(dfp["XP"], errors="coerce").fillna(0).sum())
        streak_max = int(pd.to_numeric(dfp["Streak"], errors="coerce").fillna(0).max())
        checklist_rate = float(dfp["Checklist_OK"].apply(_to_bool).mean())
        rank, subtitulo = calcular_rank(xp_total, streak_max, checklist_rate)

        a,b,c = st.columns(3)
        a.metric("🏅 Rank Atual", rank)
        b.metric("✨ XP Total", xp_total)
        c.metric("✅ Checklist", f"{checklist_rate*100:.0f}%")
        st.caption(f"Status: **{subtitulo}** | 🔥 Streak Máx: **{streak_max}** dias")

        pass  # divider removed

        dfw_all = add_calendar_week(dfp)
        if not dfw_all.empty:
            # coluna derivada necessária para PRs (evita KeyError)
            dfw_all["1RM Estimado"] = dfw_all.apply(best_1rm_row, axis=1)
        if dfw_all.empty:
            st.warning("Há registos, mas sem datas válidas (esperado: dd/mm/aaaa).")
        else:
            semanas = sorted(dfw_all["Semana_ID"].unique())
            semana_sel = st.selectbox("Seleciona a semana (ISO):", semanas, index=len(semanas)-1)

            dfw = dfw_all[dfw_all["Semana_ID"] == semana_sel].copy()
            dfw["Séries"] = dfw.apply(series_count_row, axis=1)
            dfw["Tonnage"] = dfw.apply(tonnage_row, axis=1)
            dfw["RIR_médio"] = dfw.apply(avg_rir_row, axis=1)
            dfw["1RM Estimado"] = dfw.apply(best_1rm_row, axis=1)

            k1,k2,k3 = st.columns(3)
            k1.metric("Séries na Semana", f"{int(dfw['Séries'].sum())}")
            k2.metric("Tonnage na Semana", f"{float(dfw['Tonnage'].sum()):.0f} kg")
            k3.metric("RIR Médio (linhas)", f"{float(dfw['RIR_médio'].mean() if len(dfw) else 0.0):.1f}")

            pass  # divider removed

            st.subheader("📌 Volume por Bloco (semana)")
            vol_bloco = dfw.groupby("Bloco")["Séries"].sum().sort_values(ascending=False)
            st.bar_chart(vol_bloco)

            st.subheader("⚠️ Índice de Fadiga (simples)")
            dfw["Fadiga"] = dfw["Séries"] * (4 - dfw["RIR_médio"].clip(lower=0, upper=4))
            fadiga = float(dfw["Fadiga"].sum())
            st.metric("Fadiga (Σ Séries × (4−RIR))", f"{fadiga:.1f}")
            if fadiga >= 90 or float(dfw["RIR_médio"].mean()) <= 1.2:
                st.warning("Esforço alto. Se sono/stress estiverem maus: considera deload / mantém RIR mais alto.")
            else:
                st.success("Sinais OK. Mantém progressão e técnica.")

            pass  # divider removed

            st.subheader("🏆 PRs por Exercício (1RM Estimado)")
            best_hist = dfw_all.groupby("Exercício")["1RM Estimado"].max()
            best_week = dfw.groupby("Exercício")["1RM Estimado"].max()
            prs = []
            for ex, val_week in best_week.items():
                val_hist = float(best_hist.get(ex, 0))
                if val_week > 0 and abs(val_week - val_hist) < 1e-9:
                    prs.append((ex, val_week))
            if prs:
                st.success("Novos PRs detetados nesta semana:")
                st.dataframe(pd.DataFrame(prs, columns=["Exercício","1RM Estimado (PR)"]), hide_index=True, width='stretch')
            else:
                st.info("Sem PRs nesta semana.")

            pass  # divider removed

            st.subheader("📈 Progressão de Força (1RM Estimado)")
            lista_exercicios = sorted(dfw_all["Exercício"].dropna().astype(str).unique())
            filtro_ex = st.selectbox("Escolhe um Exercício:", lista_exercicios)
            df_chart = dfw_all[dfw_all["Exercício"].astype(str) == str(filtro_ex)].copy()
            df_chart["1RM Estimado"] = df_chart.apply(best_1rm_row, axis=1)
            df_chart = df_chart.sort_values("Data_dt")

            st.line_chart(df_chart, x="Data_dt", y="1RM Estimado")

            st.markdown("### Registos filtrados")
            st.dataframe(
                df_chart.sort_values("Data_dt", ascending=False)[
                    ["Data","Dia","Bloco","Exercício","Peso","Reps","RIR","XP","Checklist_OK","Notas"]
                ],
                width='stretch', hide_index=True
            )


with tab_ranking:
    st.header("Ranking de perfis 🏅")

    rank_window = st.selectbox("Período do ranking", ["Total", "30 dias", "90 dias"], index=0)

    df_rank_all = get_data().copy()
    # ignora linhas de setup/ruído
    df_rank_all = df_rank_all[df_rank_all["Bloco"].astype(str).str.lower() != "setup"]
    df_rank_all = df_rank_all[df_rank_all["Dia"].astype(str).str.lower() != "setup"]
    df_rank_all = df_rank_all[df_rank_all["Exercício"].astype(str).str.lower() != "setup"]

    if rank_window != "Total" and not df_rank_all.empty:
        dias = 30 if rank_window == "30 dias" else 90
        df_rank_all["_dt"] = pd.to_datetime(df_rank_all["Data"], dayfirst=True, errors="coerce")
        cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=dias)
        df_rank_all = df_rank_all[df_rank_all["_dt"] >= cutoff].drop(columns=["_dt"], errors="ignore")

    if df_rank_all.empty:
        st.info("Ainda não há registos suficientes para criar ranking.")
    else:
        rows = []
        for perfil, d in df_rank_all.groupby("Perfil"):
            d = d.copy()
            xp_total = int(pd.to_numeric(d["XP"], errors="coerce").fillna(0).sum())
            streak_max = int(pd.to_numeric(d["Streak"], errors="coerce").fillna(0).max()) if "Streak" in d.columns else 0
            checklist_rate = float(d["Checklist_OK"].apply(_to_bool).mean()) if "Checklist_OK" in d.columns else 0.0
            sessoes = int(d[["Data","Dia"]].drop_duplicates().shape[0])

            tier, subt = calcular_rank(xp_total, streak_max, checklist_rate)
            tier_ord = {"💎 PLATINA": 4, "🥇 OURO": 3, "🥈 PRATA": 2, "🥉 BRONZE": 1}.get(tier, 0)

            score = float(xp_total) + float(streak_max)*50.0 + float(checklist_rate)*500.0 + float(sessoes)*10.0

            rows.append({
                "Perfil": str(perfil),
                "Tier": tier,
                "Score": round(score, 1),
                "XP Total": xp_total,
                "Streak Máx": streak_max,
                "Checklist %": round(checklist_rate*100, 0),
                "Sessões": sessoes,
                "_tier_ord": tier_ord
            })

        rank_df = pd.DataFrame(rows)
        rank_df = rank_df.sort_values(["_tier_ord", "Score", "XP Total"], ascending=[False, False, False]).drop(columns=["_tier_ord"])
        rank_df.insert(0, "Posição", range(1, len(rank_df)+1))

        # pódio (empilhado para ficar legível em mobile)
        top3 = rank_df.head(3)
        if not top3.empty:
            if len(top3) >= 1:
                st.metric("🥇 #1", top3.iloc[0]["Perfil"], f"{top3.iloc[0]['Tier']} • {top3.iloc[0]['XP Total']} XP")
            if len(top3) >= 2:
                st.metric("🥈 #2", top3.iloc[1]["Perfil"], f"{top3.iloc[1]['Tier']} • {top3.iloc[1]['XP Total']} XP")
            if len(top3) >= 3:
                st.metric("🥉 #3", top3.iloc[2]["Perfil"], f"{top3.iloc[2]['Tier']} • {top3.iloc[2]['XP Total']} XP")

        st.dataframe(
            rank_df[["Posição","Perfil","Tier","Score","XP Total","Streak Máx","Checklist %","Sessões"]],
            width='stretch',
            hide_index=True
        )

        st.caption("Score = XP + (Streak×50) + (Checklist×500) + (Sessões×10). Isto é só para ranking — não muda o teu treino.")


# espaço de segurança para barras flutuantes (mobile)
st.markdown("<div class='app-bottom-safe'></div>", unsafe_allow_html=True)



