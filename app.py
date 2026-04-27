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
import urllib.parse
import re
import random
import unicodedata
import json
from zoneinfo import ZoneInfo

# =========================================================
# ♣ BLACK CLOVER WORKOUT — RIR Edition (perfis + planos)
# =========================================================

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
# --- UI theme knobs (ajusta facilmente) ---
BANNER_BLUR_PX = 1.5
BANNER_BRIGHTNESS = 1.5
CLOVER_OPACITY = 0.06

st.set_page_config(page_title="Black Clover Training APP", page_icon="♣️", layout="centered", initial_sidebar_state="expanded")


# --- FIX iOS/mobile: scroll, zoom e refresh ---
# iPhone faz zoom automático quando inputs têm font-size < 16px; sim, tecnologia moderna, pelos vistos.
st.markdown("""
<style>
html, body, .stApp{
  max-width: 100% !important;
  overflow-x: hidden !important;
  -webkit-text-size-adjust: 100% !important;
  touch-action: pan-y !important;
}
.block-container,
[data-testid="stAppViewContainer"],
[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"]{
  max-width: 100% !important;
  overflow-x: hidden !important;
}
input, textarea, select,
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
[data-baseweb="select"] input,
[data-testid="stDateInput"] input{
  font-size: 16px !important;
  -webkit-text-size-adjust: 100% !important;
}
.stTabs [data-baseweb="tab-list"]{
  overflow-x: auto !important;
  overflow-y: hidden !important;
  -webkit-overflow-scrolling: touch !important;
}
[data-testid="stDataFrame"], iframe{
  max-width: 100% !important;
}
.bc-float-bar{ pointer-events: none; }
.bc-float-bar button,
.bc-float-bar a,
.bc-float-bar input{ pointer-events: auto; }
.bc-rest-track{
  touch-action: pan-y !important;
  overscroll-behavior: auto !important;
}
</style>
""", unsafe_allow_html=True)

# Keep screen awake on mobile (when supported)
st.components.v1.html("""
<script>
(async function(){
  try {
    if (!('wakeLock' in navigator)) return;
    let lock = null;
    async function acquire(){
      try {
        // Some browsers require a user gesture; this may fail silently until the first tap.
        lock = await navigator.wakeLock.request('screen');
      } catch(e) {}
    }

    // Try once on load (works in many browsers).
    await acquire();

    // Fallback: first user interaction.
    let armed = true;
    async function onFirstGesture(){
      if (!armed) return;
      armed = false;
      await acquire();
      window.removeEventListener('pointerdown', onFirstGesture, {capture:true});
      window.removeEventListener('touchstart', onFirstGesture, {capture:true});
    }
    window.addEventListener('pointerdown', onFirstGesture, {capture:true, passive:true});
    window.addEventListener('touchstart', onFirstGesture, {capture:true, passive:true});

    // Re-acquire when returning to the app.
    document.addEventListener('visibilitychange', async () => {
      if (document.visibilityState === 'visible') await acquire();
    });

    // If the lock is released by the system, try to re-acquire on next gesture.
    setInterval(() => {
      try {
        if (lock && lock.released) armed = true;
      } catch(e) {}
    }, 1500);
  } catch(e) {}
})();
</script>
""", height=0)

# --- 2. FUNÇÕES VISUAIS (Fundo e CSS) ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

def _clover_pattern_data_uri():
    """Gera um padrão SVG discreto com trevos para usar como watermark no fundo."""
    try:
        svg = f"""
        <svg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'>
          <g fill='rgba(232,226,226,{CLOVER_OPACITY})' font-family='serif'>
            <text x='16' y='54' font-size='34'>♣</text>
            <text x='138' y='110' font-size='46'>♣</text>
            <text x='56' y='186' font-size='28'>♣</text>
          </g>
        </svg>
        """.strip()
        return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)
    except Exception:
        return ""

def set_background(png_file):
    bin_str = get_base64(png_file)
    if not bin_str:
        return
    clover_uri = _clover_pattern_data_uri()
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
        filter: blur({BANNER_BLUR_PX}px) brightness({BANNER_BRIGHTNESS});
        z-index: -1;
    }}
    .stApp::after {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: rgba(18, 18, 20, 0.90);
        background-image: url("{clover_uri}");
        background-repeat: repeat;
        background-size: 220px 220px;
        background-position: 0 0;
        z-index: -1;
        pointer-events: none;
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



def _enforce_mobile_ui_behaviour():
    """Melhora UX mobile: sidebar aberta por defeito, bloqueia scroll horizontal e evita digitação em selectboxes."""
    try:
        components.html(
            """
            <script>
            (function () {
              try {
                const d = parent.document || document;
                const w = parent.window || window;

                function applyUiLocks(){
                  try {
                    // Selects sem digitação (abre dropdown normal, mas sem teclado / pesquisa por texto)
                    d.querySelectorAll('[data-baseweb="select"] input').forEach((inp) => {
                      try {
                        inp.readOnly = true;
                        inp.setAttribute('readonly', 'readonly');
                        inp.setAttribute('inputmode', 'none');
                        inp.setAttribute('autocomplete', 'off');
                        inp.style.caretColor = 'transparent';
                        inp.style.userSelect = 'none';
                        inp.addEventListener('keydown', (ev) => ev.preventDefault(), { passive:false });
                        inp.addEventListener('beforeinput', (ev) => ev.preventDefault(), { passive:false });
                        inp.addEventListener('paste', (ev) => ev.preventDefault(), { passive:false });
                      } catch (e) {}
                    });

                    // Limpa artefactos vazios na sidebar (cards HTML abertos/fechados sem conteúdo útil)
                    d.querySelectorAll('section[data-testid="stSidebar"] .sidebar-card, section[data-testid="stSidebar"] .sidebar-seal').forEach((el) => {
                      try {
                        const txt = ((el.innerText || '') + '').replace(/\\s+/g, '').trim();
                        const hasWidget = !!el.querySelector('[data-testid], [data-baseweb], input, button, textarea, select, label');
                        const hasContent = !!el.querySelector('h1,h2,h3,h4,p,span,small');
                        const tooSmall = (el.getBoundingClientRect ? el.getBoundingClientRect().height : 0) < 24;
                        if ((!txt && !hasWidget && !hasContent) || (tooSmall && !hasWidget && txt.length <= 1)) {
                          el.style.display = 'none';
                          el.style.margin = '0';
                          el.style.padding = '0';
                          el.style.border = '0';
                          el.style.boxShadow = 'none';
                        }
                      } catch (e) {}
                    });

                    // Sidebar aberta por defeito (faz só uma vez)
                    if (!w.__bc_sidebar_auto_opened_once) {
                      const collapsedBtn = d.querySelector('[data-testid="collapsedControl"] button');
                      if (collapsedBtn) {
                        collapsedBtn.click();
                      }
                      w.__bc_sidebar_auto_opened_once = true;
                    }
                  } catch (e) {}
                }

                applyUiLocks();
                // Reaplica poucas vezes após o render para evitar "lock" de scroll por loop contínuo
                if (!w.__bc_ui_locks_once_seq) {
                  w.__bc_ui_locks_once_seq = true;
                  [300, 900, 1800].forEach(ms => setTimeout(applyUiLocks, ms));
                }
              } catch (e) {}
            })();
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


def _format_ex_select_label(item: dict, ix: int, total: int, bloco: str | None = None, semana: int | None = None) -> str:
    # Nome do exercício: tenta várias chaves (planos diferentes)
    nome = ""
    for k in ("ex", "exercicio", "exercício", "Exercício", "name", "nome", "titulo", "título"):
        try:
            v = item.get(k, "")
        except Exception:
            v = ""
        if v is not None and str(v).strip():
            nome = str(v).strip()
            break
    if not nome:
        nome = "Exercício"

    try:
        sers = int(item.get("series", 0) or 0)
    except Exception:
        sers = 0

    reps = str(item.get("reps", "") or "").strip()

    # RIR esperado: preferir campo do item; senão calcula pelo bloco/semana
    rir_txt = ""
    for k in ("rir_alvo", "rir", "rir_target", "RIR"):
        try:
            v = item.get(k, "")
        except Exception:
            v = ""
        if v is not None and str(v).strip():
            rir_txt = str(v).strip()
            break
    if not rir_txt and bloco and semana is not None:
        try:
            rir_txt = str(rir_alvo(str(item.get("tipo", "") or ""), str(bloco), int(semana)) or "").strip()
        except Exception:
            rir_txt = ""

    # normalizar para formato com hífen
    rir_txt = rir_txt.replace("–", "-").replace("—", "").strip()

    meta_parts: list[str] = []
    if sers > 0:
        if reps:
            meta_parts.append(f"{sers}x{reps}")
        else:
            meta_parts.append(f"{sers} séries")
    elif reps:
        meta_parts.append(reps)
    if rir_txt:
        meta_parts.append(f"RIR {rir_txt}")

    meta = " • ".join(meta_parts)
    if meta:
        return f"{ix+1} • {nome} • {meta}"
    return f"{ix+1} • {nome}"

def _peso_label_para_ex(ex_name: str, serie_idx: int | None = None) -> str:
    """Devolve a label do peso ajustada ao tipo de exercício.

    Usa 'Kg / Lado' para exercícios com halteres/unilateral/alternado/simultâneo,
    e 'Kg' para máquina/polia/cabo. Em exercícios com barra carregada assume
    'Kg / Lado'. O serie_idx é opcional e só entra no sufixo visual (S1, S2, ...).
    """
    try:
        ex = str(ex_name or "").lower()
    except Exception:
        ex = ""

    # Heurística partilhada com o bloco de histórico.
    is_per_side = _is_per_side_exercise(ex)

    base = "Kg / Lado" if is_per_side else "Kg"
    if serie_idx is None:
        return base
    try:
        return f"{base} • S{int(serie_idx)+1}"
    except Exception:
        return base


def _is_per_side_exercise(ex_name: str) -> bool:
    """Heurística para saber se o peso costuma ser por lado (halteres/unilateral/barra carregada)."""
    try:
        ex = str(ex_name or "").lower()
    except Exception:
        ex = ""

    # Por lado: halteres, unilateral/alternado/simultâneo e exercícios de barra carregada.
    is_per_side = any(k in ex for k in [
        "halter", "haltere", "dumbbell", "db ", " db",
        "unilateral", "alternado", "alternada",
        "simultaneo", "simultâneo",
        " barra", "barra ", "barra-", "barra_", "(barra)",
    ])

    # Exceções: barra fixa e máquinas/polias costumam ser carga total da stack/máquina.
    if "barra fixa" in ex:
        is_per_side = False
    if any(k in ex for k in [
        "maquina", "máquina", "polia", "cabo", "landmine"
    ]):
        is_per_side = False
    # Smith / multipower normalmente é barra + discos (o utilizador pediu por lado).
    return is_per_side


# --- 3. CSS DA INTERFACE ---
st.markdown(f"""
<style>
/* Theme knobs to CSS */
.bc-main-title::after{{ color: rgba(232,226,226,{max(0.35, min(1.0, CLOVER_OPACITY*4))}); }}
.bc-hero::before, .bc-ex-meta::before, .bc-progress-wrap::before{{ color: rgba(232,226,226,{CLOVER_OPACITY}); }}
</style>
""", unsafe_allow_html=True)

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

/* UX mobile: teclado nas selectboxes (sem bloquear scroll) */
[data-baseweb="select"] input{
  caret-color: transparent !important;
}

.stAlert{ margin: .85rem 0 1.10rem 0 !important; border-radius: 12px !important; }
div[data-testid="stToast"]{ margin-top:.45rem !important; }
[data-testid="stToast"]{ margin-bottom: 1.0rem !important; }
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
.bc-meta-card{
  background: linear-gradient(180deg, rgba(140,29,44,.20), rgba(20,20,20,.50));
  border: 1px solid rgba(140,29,44,.42);
  border-left: 6px solid rgba(140,29,44,.95);
  border-radius: 14px;
  padding: 12px 12px 11px 12px;
  margin: 6px 0 10px 0;
  box-shadow: 0 12px 26px rgba(140,29,44,.16), 0 12px 26px rgba(0,0,0,.22);
  backdrop-filter: blur(10px);
  position: relative;
  overflow: hidden;
}
.bc-meta-card::before{
  content:"♣";
  position:absolute;
  right: 10px;
  top: 8px;
  font-size: 1.05rem;
  color: rgba(232,226,226,.22);
  text-shadow: 0 0 18px rgba(140,29,44,.18);
  pointer-events:none;
}
.bc-meta-top{
  font-size: 1.02rem;
  font-weight: 900;
  color: #F2F2F2;
  line-height: 1.25;
  letter-spacing: .01em;
}
.bc-meta-sub{
  margin-top: 6px;
  font-size: 0.90rem;
  font-weight: 750;
  color: rgba(232,226,226,.92);
  opacity: .98;
}
@media (max-width: 768px){
  .bc-meta-top{ font-size: 0.98rem; }
  .bc-meta-sub{ font-size: 0.86rem; }
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
.bc-chip, .bc-pill{ position:relative; }
.bc-chip{ padding-left: 16px; }
.bc-pill{ padding-left: 14px; }
.bc-chip::before,
.bc-pill::before{
  content:"♣";
  position:absolute;
  left:6px;
  top:50%;
  transform:translateY(-52%);
  font-size:.62rem;
  color: rgba(176,126,136,0.55);
  pointer-events:none;
}
.bc-pill::before{ left:5px; font-size:.58rem; color: rgba(176,126,136,0.42); }
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
[data-testid='stProgressBar']{ margin: .40rem 0 .90rem 0 !important; }
.bc-rest-track{width:100%; height:10px; border-radius:999px; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.08); overflow:hidden; margin-top:6px; touch-action: pan-y; overscroll-behavior: auto; user-select: none;}
.bc-rest-fill{ height:100%; border-radius:999px; background:linear-gradient(90deg, rgba(140,29,44,.9), rgba(180,60,82,.95)); }
.bc-rest-caption{ font-size:.78rem; color:#E8E2E2; opacity:.95; margin-top:4px; }
@media (max-width: 768px){
  .bc-hero{ padding: 10px; }
  .bc-chip{ font-size: .74rem; }
  .bc-pill{ font-size: .72rem; }
  .app-bottom-safe{ height: 126px; }
}

.bc-main-title{
  position: relative;
  display: inline-block;
  margin: 0 0 4px 0;
  padding: 0;
  font-family: 'Cinzel', serif;
  font-weight: 700;
  text-transform: uppercase;
  color: #8C1D2C;
  text-shadow: 0 1px 10px rgba(0,0,0,.35);
  font-size: clamp(1.5rem, 5.1vw, 3rem);
  line-height: 1.05;
  letter-spacing: .02em;
  background: transparent !important;
}

.bc-main-title::after{
  content:"♣";
  position:absolute;
  right:-27px;
  top:-6px;
  font-size:.72em;
  color: rgba(176,126,136,0.62);
  text-shadow: 0 0 14px rgba(140,29,44,.24);
}
.bc-hero, .bc-ex-meta, .bc-progress-wrap{ position: relative; overflow: hidden; }
.bc-hero::before, .bc-ex-meta::before, .bc-progress-wrap::before{
  content:"♣";
  position:absolute;
  right:8px;
  top:6px;
  font-size:.95rem;
  color: rgba(176,126,136,0.28);
  pointer-events:none;
}
.bc-ex-meta::before{ top:7px; right:10px; font-size:.9rem; }
.bc-progress-wrap::before{ top:2px; right:4px; font-size:.82rem; }

@media (max-width: 768px){
  .bc-main-title{ font-size: 1.62rem; }
}

section[data-testid="stSidebar"] hr{ display:none !important; }
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
.sidebar-card{ position: relative; overflow: hidden; }
.sidebar-card::after{
  content:"♣";
  position:absolute;
  right:10px;
  top:8px;
  font-size:14px;
  color: rgba(176,126,136,0.34);
  pointer-events:none;
}
section[data-testid="stSidebar"] .sidebar-card:empty,
section[data-testid="stSidebar"] .sidebar-seal:empty{
  display:none !important;
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
.bc-progress-wrap{ margin: .85rem 0 .85rem 0; }
.bc-progress-label{ font-size:.92rem; color:#EAE6E6; display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:6px; }
.bc-progress-label span{ color:#B9B1B1; font-size:.80rem; }
.bc-progress-track{ width:100%; height:8px; border-radius:999px; background:rgba(255,255,255,.10); overflow:hidden; border:1px solid rgba(255,255,255,.06); }
.bc-progress-fill{ height:100%; border-radius:999px; transition:width .18s ease; background:linear-gradient(90deg, rgba(70,130,255,.75), rgba(70,130,255,.95)); }
.bc-progress-fill.mid{ background:linear-gradient(90deg, rgba(141,29,44,.70), rgba(141,29,44,.95)); }
.bc-progress-fill.end{ background:linear-gradient(90deg, rgba(173,28,48,.82), rgba(204,52,73,.98)); box-shadow:0 0 10px rgba(173,28,48,.25); }
.bc-last-chip{ margin: 0 0 1rem 0; padding: .35rem .55rem; border-radius: 999px; display:flex; flex-wrap:wrap; align-items:center; gap:8px; font-size:.86rem; color:#EDE9E9; border:1px solid rgba(255,255,255,.10); background:rgba(255,255,255,.04); }
.bc-last-chip .bc-lastset{ opacity: .96; }
.bc-last-chip .bc-tempo{ font-weight: 850; letter-spacing: .02em; border:1px solid rgba(140,29,44,.40); background: rgba(140,29,44,.18); padding: 2px 8px; border-radius: 999px; }

/* aquecimento + mobilidade (mais espaçado, menos destaque) */
.bc-prep-head{
  margin: .65rem 0 1.05rem 0;
  padding: .55rem .75rem;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
}
.bc-prep-title{
  font-family: 'Cinzel', serif;
  letter-spacing: .10em;
  font-weight: 800;
  font-size: .90rem;
  color: rgba(237,231,231,0.92);
  text-transform: uppercase;
}
.bc-prep-sub{
  margin-top: 4px;
  font-size: .82rem;
  color: rgba(236,231,231,0.70);
}
.bc-prep-card{
  padding: .65rem .8rem;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.02);
  margin-bottom: .65rem;
}
.bc-prep-card .t{
  font-weight: 800;
  font-size: 1.00rem;
  letter-spacing: .01em;
  color: rgba(240,236,236,0.94);
}
.bc-prep-card .s{
  margin-top: 4px;
  font-size: .82rem;
  color: rgba(232,226,226,0.68);
}

@media (max-width: 768px){ .bc-last-chip .bc-tempo{ font-size:.90rem; } }

.bc-yami-chip{ margin: .15rem 0 1.35rem 0; padding:.48rem .62rem; border-radius:12px; border:1px solid rgba(255,255,255,.08); background:rgba(255,255,255,.03); color:#EDE8E8; font-size:.88rem; line-height:1.28; }
.bc-yami-chip b{ color:#F2EEEE; font-weight:700; }
.bc-yami-chip .muted{ color:#BEB6B6; }
.bc-yami-chip.y-up{ border-color: rgba(52,211,153,.28); background: rgba(16,185,129,.12); }
.bc-yami-chip.y-up b{ color:#C8F7E8; }
.bc-yami-chip.y-up .muted{ color:#A7EAD6; }
.bc-yami-chip.y-hold{ border-color: rgba(148,163,184,.22); background: rgba(148,163,184,.08); }
.bc-yami-chip.y-hold b{ color:#E8EEF5; }
.bc-yami-chip.y-hold .muted{ color:#C9D2DD; }
.bc-yami-chip.y-down{ border-color: rgba(251,146,60,.28); background: rgba(249,115,22,.12); }
.bc-yami-chip.y-down b{ color:#FFE3C2; }
.bc-yami-chip.y-down .muted{ color:#FFD4A6; }
.bc-yami-chip.y-deload{ border-color: rgba(244,114,182,.26); background: rgba(190,24,93,.12); }
.bc-yami-chip.y-deload b{ color:#FFD3E8; }
.bc-yami-chip.y-deload .muted{ color:#F8C4DF; }
.bc-final-summary{ margin: .5rem 0 .45rem 0; padding: .65rem .75rem; border-radius: 14px; border:1px solid rgba(140,29,44,.35); background:linear-gradient(180deg, rgba(140,29,44,.12), rgba(255,255,255,.02)); }
.bc-final-summary .ttl{ font-weight:700; color:#F0ECEC; margin-bottom:3px; }
.bc-final-summary .sub{ color:#CFC9C9; font-size:.88rem; }
</style>
""", unsafe_allow_html=True)

# --- 4. CONEXÃO E DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

SCHEMA_COLUMNS = [
    "Data","Perfil","Dia","Bloco","Plano_ID",
    "Exercício","Exercício_Key","Peso","Reps","RIR","Notas",
    "Aquecimento","Mobilidade","Cardio","Tendões","Core","Cooldown",
    "XP","Streak","Checklist_OK"
]

PROFILES_WORKSHEET = "Perfis"
PROFILES_COLUMNS = ["Perfil","Criado_em","Plano_ID","Ativo"]
PROFILES_BACKUP_PATH = "offline_profiles.csv"


BACKUP_PATH = "offline_backup.csv"
DATA_CACHE_SECONDS = 45
PROFILES_CACHE_SECONDS = 300

# --- YAMI: estado persistente (coach) ---
YAMI_STATE_PATH = "yami_state.json"

# --- TREINO PURO: persistência de sessão em curso (evita reset quando mobile suspende o browser) ---
INPROGRESS_STATE_PATH = "_inprogress_sessions.json"
INPROGRESS_MAX_AGE_HOURS = 18

def _inprogress_today_key_date() -> str:
    try:
        return datetime.datetime.now(ZoneInfo("Europe/Lisbon")).strftime("%Y-%m-%d")
    except Exception:
        return datetime.datetime.now().strftime("%Y-%m-%d")

def _make_inprogress_key(perfil: str, plano_id: str, dia: str, semana: int, date_iso: str = "") -> str:
    # Key de sessão em curso (NÃO depende da data).
    # A data real fica dentro do payload ("date"), assim podes fazer "terça" na quarta e continuar depois.
    return f"{perfil}||{plano_id}||{dia}||{int(semana)}"

def _make_inprogress_key_legacy(perfil: str, plano_id: str, dia: str, semana: int, date_iso: str) -> str:
    # Compatibilidade com versões antigas (incluíam a data na key).
    return f"{perfil}||{plano_id}||{dia}||{int(semana)}||{date_iso}"

def _active_inprogress_pointer_key(perfil: str, plano_id: str) -> str:
    # Ponteiro para a sessão ativa de um perfil+plano
    return f"active::{perfil}::{plano_id}"

def get_active_inprogress_session(perfil: str, plano_id: str, max_age_hours: int = INPROGRESS_MAX_AGE_HOURS):
    """Devolve (key, payload) da sessão ativa mais recente (se existir e não estiver expirada).
    Usa ponteiro 'active::' quando existir; se não existir, faz scan (compatível com keys antigas).
    """
    try:
        store = _load_inprogress_store()
        now = time.time()
        pkey = _active_inprogress_pointer_key(str(perfil), str(plano_id))

        # 1) Ponteiro explícito
        sk = store.get(pkey)
        if isinstance(sk, str):
            payload = store.get(sk)
            if isinstance(payload, dict):
                ts = float(payload.get("ts", 0) or 0)
                if ts > 0 and (now - ts) <= float(max_age_hours) * 3600.0:
                    return sk, payload

        # 2) Scan por sessão mais recente (ignora ponteiros)
        prefix = f"{perfil}||{plano_id}||"
        best_k, best_p, best_ts = None, None, 0.0
        for k, v in store.items():
            if not isinstance(k, str):
                continue
            if k.startswith("active::"):
                continue
            if not k.startswith(prefix):
                continue
            if not isinstance(v, dict):
                continue
            ts = float(v.get("ts", 0) or 0)
            if ts <= 0:
                continue
            if (now - ts) > float(max_age_hours) * 3600.0:
                continue
            if ts > best_ts:
                best_k, best_p, best_ts = k, v, ts

        if best_k and isinstance(best_p, dict):
            # grava ponteiro para o próximo arranque (melhora restore)
            try:
                store[pkey] = best_k
                _save_inprogress_store(store)
            except Exception:
                pass
            return best_k, best_p

        # 3) Nada ativo
        try:
            if pkey in store:
                del store[pkey]
                _save_inprogress_store(store)
        except Exception:
            pass
        return None, None
    except Exception:
        return None, None

def _load_inprogress_store() -> dict:
    try:
        if os.path.exists(INPROGRESS_STATE_PATH):
            with open(INPROGRESS_STATE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}

def _save_inprogress_store(store: dict) -> bool:
    try:
        tmp = INPROGRESS_STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
        os.replace(tmp, INPROGRESS_STATE_PATH)
        return True
    except Exception:
        return False

def load_inprogress_session(key: str, max_age_hours: int = INPROGRESS_MAX_AGE_HOURS):
    try:
        store = _load_inprogress_store()
        payload = store.get(key)
        if not isinstance(payload, dict):
            return None
        ts = float(payload.get("ts", 0) or 0)
        if ts > 0:
            age_s = time.time() - ts
            if age_s > float(max_age_hours) * 3600.0:
                return None
        return payload
    except Exception:
        return None

def save_inprogress_session(key: str, payload: dict) -> None:
    try:
        store = _load_inprogress_store()

        # limpeza simples (evita crescimento infinito)
        try:
            now = time.time()
            for k in list(store.keys()):
                v = store.get(k)
                if isinstance(v, dict):
                    ts = float(v.get("ts", 0) or 0)
                    if ts and (now - ts) > 72 * 3600:
                        del store[k]
        except Exception:
            pass

        # limpa ponteiros quebrados
        try:
            for k in list(store.keys()):
                if isinstance(k, str) and k.startswith("active::"):
                    v = store.get(k)
                    if isinstance(v, str) and v not in store:
                        del store[k]
        except Exception:
            pass

        # remove snapshots legados para a mesma sessão (chave com data)
        try:
            parts = str(key).split("||")
            if len(parts) >= 4:
                base = "||".join(parts[:4])
                for k in list(store.keys()):
                    if isinstance(k, str) and k.startswith(base + "||"):
                        del store[k]
        except Exception:
            pass

        store[str(key)] = payload

        # Atualiza ponteiro da sessão ativa (perfil+plano)
        try:
            _perfil = str(payload.get("perfil", "") or "")
            _plano = str(payload.get("plano_id", "") or "")
            if _perfil and _plano:
                store[_active_inprogress_pointer_key(_perfil, _plano)] = str(key)
        except Exception:
            pass

        _save_inprogress_store(store)
    except Exception:
        pass

def clear_inprogress_session(key: str) -> None:
    try:
        store = _load_inprogress_store()
        skey = str(key)

        parts = skey.split("||")
        if len(parts) >= 4:
            base = "||".join(parts[:4])

            # apaga a key nova (base) e quaisquer keys antigas que incluam data
            for k in list(store.keys()):
                if not isinstance(k, str):
                    continue
                if k == base or k == skey or k.startswith(base + "||"):
                    try:
                        del store[k]
                    except Exception:
                        pass

            # apaga ponteiro ativo se estiver a apontar para esta sessão
            try:
                pkey = _active_inprogress_pointer_key(parts[0], parts[1])
                pv = store.get(pkey)
                if isinstance(pv, str) and (pv == skey or pv == base or pv.startswith(base + "||")):
                    del store[pkey]
            except Exception:
                pass
        else:
            if skey in store:
                del store[skey]

        _save_inprogress_store(store)
    except Exception:
        pass

def _build_inprogress_payload(perfil: str, dia: str, plano_id: str, semana: int, pure_nav_key: str, n_ex: int) -> dict:
    payload = {
        "ts": time.time(),
        "perfil": str(perfil),
        "dia": str(dia),
        "plano_id": str(plano_id),
        "semana": int(semana),
        "date": _inprogress_today_key_date(),
        "pt_idx": int(st.session_state.get(pure_nav_key, 0) or 0),
        "pt_done": {},
        "pt_sets": {},
        "rest": {},
        "checks": {
            str(k): bool(v)
            for k, v in st.session_state.items()
            if str(k).startswith("chk_")
        },
        "ui": {
            "disable_rest_timer": bool(st.session_state.get("disable_rest_timer", False)),
        },
    }
    for ix in range(int(n_ex)):
        dk = f"pt_done::{perfil}::{dia}::{ix}"
        sk = f"pt_sets::{perfil}::{dia}::{ix}"
        rk = f"rest_{ix}"
        try:
            payload["pt_done"][str(ix)] = int(st.session_state.get(dk, 0) or 0)
        except Exception:
            payload["pt_done"][str(ix)] = 0
        sets = st.session_state.get(sk, [])
        payload["pt_sets"][str(ix)] = sets if isinstance(sets, list) else []
        try:
            payload["rest"][str(ix)] = int(st.session_state.get(rk, 0) or 0)
        except Exception:
            payload["rest"][str(ix)] = 0
    return payload

def _persist_disable_rest_timer_for_active_session(perfil: str, plano_id: str) -> None:
    try:
        skey, payload = get_active_inprogress_session(str(perfil), str(plano_id), INPROGRESS_MAX_AGE_HOURS)
        if not (isinstance(skey, str) and isinstance(payload, dict)):
            return
        ui = payload.get("ui", {}) if isinstance(payload.get("ui", {}), dict) else {}
        ui["disable_rest_timer"] = bool(st.session_state.get("disable_rest_timer", False))
        payload["ui"] = ui
        payload["ts"] = time.time()
        save_inprogress_session(skey, payload)
    except Exception:
        pass

def _apply_inprogress_payload(payload: dict, perfil: str, dia: str, pure_nav_key: str) -> None:
    try:
        st.session_state[pure_nav_key] = int(payload.get("pt_idx", 0) or 0)
    except Exception:
        st.session_state[pure_nav_key] = 0
    try:
        pdone = payload.get("pt_done", {})
        if isinstance(pdone, dict):
            for k, v in pdone.items():
                try:
                    ix = int(k)
                except Exception:
                    continue
                try:
                    st.session_state[f"pt_done::{perfil}::{dia}::{ix}"] = int(v or 0)
                except Exception:
                    st.session_state[f"pt_done::{perfil}::{dia}::{ix}"] = 0
    except Exception:
        pass
    try:
        psets = payload.get("pt_sets", {})
        if isinstance(psets, dict):
            for k, v in psets.items():
                try:
                    ix = int(k)
                except Exception:
                    continue
                if isinstance(v, list):
                    st.session_state[f"pt_sets::{perfil}::{dia}::{ix}"] = v
    except Exception:
        pass
    try:
        prest = payload.get("rest", {})
        if isinstance(prest, dict):
            for k, v in prest.items():
                try:
                    ix = int(k)
                    st.session_state[f"rest_{ix}"] = int(v or 0)
                except Exception:
                    pass
    except Exception:
        pass
    try:
        pchecks = payload.get("checks", {})
        if isinstance(pchecks, dict):
            for k, v in pchecks.items():
                if str(k).startswith("chk_"):
                    st.session_state[str(k)] = bool(v)
    except Exception:
        pass

def _pure_has_any_progress(perfil: str, dia: str, n_ex: int) -> bool:
    try:
        for ix in range(int(n_ex)):
            dk = f"pt_done::{perfil}::{dia}::{ix}"
            sk = f"pt_sets::{perfil}::{dia}::{ix}"
            try:
                if int(st.session_state.get(dk, 0) or 0) > 0:
                    return True
            except Exception:
                pass
            vv = st.session_state.get(sk, [])
            if isinstance(vv, list) and len(vv) > 0:
                return True
    except Exception:
        pass
    try:
        for _k, _v in st.session_state.items():
            if str(_k).startswith("chk_") and bool(_v):
                return True
    except Exception:
        pass
    return False


def _yami_state_default() -> dict:
    return {"profiles": {}}

def _yami_state_load() -> dict:
    try:
        if os.path.exists(YAMI_STATE_PATH):
            with open(YAMI_STATE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("profiles"), dict):
                return data
    except Exception:
        pass
    return _yami_state_default()

def _yami_state_save(state: dict) -> bool:
    try:
        tmp = YAMI_STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, YAMI_STATE_PATH)
        return True
    except Exception:
        return False

def _yami_profile_state(perfil: str) -> dict:
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    prof.setdefault("rir_bias", {})   # {exercicio: bias}
    prof.setdefault("checkins", [])   # list[{date,...}]
    # ciclos/periodização por plano (auto-semana)
    # estrutura: cycles[plano_id] = {"auto": bool, "start": "YYYY-MM-DD"}
    prof.setdefault("cycles", {})
    return prof


def _lisbon_today_date() -> datetime.date:
    try:
        return datetime.datetime.now(ZoneInfo("Europe/Lisbon")).date()
    except Exception:
        return datetime.date.today()


def yami_get_cycle_cfg(perfil: str, plano_id: str) -> dict:
    """Lê configuração de ciclo (auto-semana) do estado persistente do Yami."""
    try:
        prof = _yami_profile_state(perfil)
        cyc = (prof.get("cycles", {}) or {}).get(str(plano_id or "Base"), {}) or {}
        out = {
            "auto": bool(cyc.get("auto", True)),
            "start": str(cyc.get("start", "") or "").strip(),
        }
        # valida ISO simples
        if out["start"]:
            try:
                datetime.date.fromisoformat(out["start"])
            except Exception:
                out["start"] = ""
        return out
    except Exception:
        return {"auto": True, "start": ""}


def yami_set_cycle_cfg(perfil: str, plano_id: str, *, auto: bool | None = None, start_iso: str | None = None) -> bool:
    """Guarda configuração de ciclo (auto-semana) no estado persistente do Yami."""
    try:
        stt = _yami_state_load()
        prof = stt.setdefault("profiles", {}).setdefault(str(perfil), {})
        cycles = prof.setdefault("cycles", {})
        pid = str(plano_id or "Base")
        curr = cycles.get(pid, {}) if isinstance(cycles.get(pid, {}), dict) else {}
        if auto is not None:
            curr["auto"] = bool(auto)
        if start_iso is not None:
            s = str(start_iso or "").strip()
            if s:
                try:
                    datetime.date.fromisoformat(s)
                except Exception:
                    s = ""
            curr["start"] = s
        cycles[pid] = curr
        return _yami_state_save(stt)
    except Exception:
        return False

def yami_get_rir_bias(perfil: str, ex: str) -> float:
    try:
        prof = _yami_profile_state(perfil)
        return float(prof.get("rir_bias", {}).get(str(ex), 0.0))
    except Exception:
        return 0.0

def yami_set_rir_bias(perfil: str, ex: str, bias: float) -> bool:
    try:
        bias = max(-1.0, min(1.0, float(bias)))
        stt = _yami_state_load()
        prof = stt.setdefault("profiles", {}).setdefault(str(perfil), {})
        prof.setdefault("rir_bias", {})[str(ex)] = float(bias)
        return _yami_state_save(stt)
    except Exception:
        return False

def yami_log_checkin(perfil: str, checkin: dict) -> bool:
    try:
        stt = _yami_state_load()
        prof = stt.setdefault("profiles", {}).setdefault(str(perfil), {})
        lst = prof.setdefault("checkins", [])
        d = str(checkin.get("date", ""))
        kept = [x for x in lst if str(x.get("date","")) != d]
        kept.append(checkin)
        kept = sorted(kept, key=lambda x: str(x.get("date","")))[-90:]
        prof["checkins"] = kept
        return _yami_state_save(stt)
    except Exception:
        return False

def yami_compute_readiness(sleep: str, stress: str, doms: int, joint: int) -> dict:
    s_map = {"ruim": -1.0, "ok": 0.0, "top": 1.0}
    st_map = {"baixo": 0.5, "médio": 0.0, "medio": 0.0, "alto": -0.5}
    try:
        sc = float(s_map.get(str(sleep).strip().lower(), 0.0))
        sc += float(st_map.get(str(stress).strip().lower(), 0.0))
        sc += {0: 0.5, 1: 0.0, 2: -0.5, 3: -1.0}.get(int(doms), 0.0)
        sc += {0: 0.0, 1: -0.5, 2: -1.0, 3: -1.5}.get(int(joint), 0.0)
    except Exception:
        sc = 0.0

    if sc <= -2.0:
        adj_pct, adj_rir, label, score_delta = -0.05, +1.0, "Baixa", -0.60
    elif sc <= -1.0:
        adj_pct, adj_rir, label, score_delta = -0.03, +0.5, "Média-baixa", -0.35
    elif sc >= 1.75:
        adj_pct, adj_rir, label, score_delta = +0.02, -0.5, "Alta", +0.20
    elif sc >= 0.75:
        adj_pct, adj_rir, label, score_delta = +0.01, -0.25, "Boa", +0.10
    else:
        adj_pct, adj_rir, label, score_delta = 0.0, 0.0, "Normal", 0.0

    return {
        "score": float(sc),
        "label": str(label),
        "adj_load_pct": float(adj_pct),
        "adj_rir": float(adj_rir),
        "score_delta": float(score_delta),
        "sleep": str(sleep),
        "stress": str(stress),
        "doms": int(doms),
        "joint": int(joint),
    }



# --- YAMI: controlo fino + sinais do corpo (entra na equação) ---
def yami_get_ctrl() -> dict:
    """Knobs do utilizador para o Yami.

    Objetivo: mais controlo sobre peso/reps/RIR sem rebentar o resto da app.
    """
    ctrl = st.session_state.get("yami_ctrl", {}) or {}

    def _get(key: str, default):
        try:
            return st.session_state.get(key, ctrl.get(key, default))
        except Exception:
            return default

    out = {
        "style": str(_get("yami_style", "Normal") or "Normal"),
        "effort_bias": float(_get("yami_effort_bias", 0.0) or 0.0),   # + = mais leve (mais RIR)
        "round_step": float(_get("yami_round_step", 0.5) or 0.5),
        "inc_lower_comp": float(_get("yami_inc_lower_comp", 5.0) or 5.0),
        "inc_comp": float(_get("yami_inc_comp", 2.5) or 2.5),
        "inc_iso": float(_get("yami_inc_iso", 1.0) or 1.0),
        "strict_double_prog": bool(_get("yami_strict_double_prog", False)),
        "pain_blocks_up": bool(_get("yami_pain_blocks_up", True)),
    }

    # limites práticos
    try:
        out["round_step"] = max(0.25, min(5.0, float(out["round_step"])))
    except Exception:
        out["round_step"] = 0.5
    try:
        out["effort_bias"] = max(-1.5, min(2.0, float(out["effort_bias"])))
    except Exception:
        out["effort_bias"] = 0.0
    for k in ("inc_lower_comp", "inc_comp", "inc_iso"):
        try:
            out[k] = max(0.25, min(20.0, float(out[k])))
        except Exception:
            pass

    return out


def yami_style_score_bias(style: str) -> float:
    s = str(style or "").strip().lower()
    if s.startswith("conserv"):
        return -0.35
    if s.startswith("agress"):
        return +0.35
    return 0.0


def yami_body_adjustment_for_ex(ex_name: str) -> dict:
    """Traduz sinais do corpo (checkboxes) em ajustes concretos para o Yami (por exercício)."""
    exl = str(ex_name or "").lower()

    joelho = bool(st.session_state.get("sig_dor_joelho", False))
    cotovelo = bool(st.session_state.get("sig_dor_cotovelo", False))
    ombro = bool(st.session_state.get("sig_dor_ombro", False))
    lombar = bool(st.session_state.get("sig_dor_lombar", False))

    flags: list[str] = []
    adj_rir = 0.0
    adj_pct = 0.0
    score_delta = 0.0
    block_up = False

    def _hit(keys: list[str]) -> bool:
        return any(k in exl for k in keys)

    # Mantém as mesmas heurísticas do bloco de substituições (consistência > criatividade).
    if joelho and _hit(["agach", "squat", "leg press", "bulgarian", "lunge", "extens", "hack", "step", "prensa"]):
        flags.append("joelho")
        adj_rir += 0.5
        adj_pct -= 0.03
        score_delta -= 0.35
        block_up = True

    if ombro and _hit(["ohp", "overhead", "supino", "bench", "inclinado", "press", "dips", "fly", "crossover", "peito"]):
        flags.append("ombro")
        adj_rir += 0.5
        adj_pct -= 0.02
        score_delta -= 0.30
        block_up = True

    if cotovelo and _hit(["tríceps", "triceps", "curl", "bíceps", "biceps", "barra fixa", "pull-up", "chin", "remada", "row", "puxada"]):
        flags.append("cotovelo")
        adj_rir += 0.25
        adj_pct -= 0.02
        score_delta -= 0.25
        block_up = True

    if lombar and _hit(["deadlift", "rdl", "remada", "row", "agach", "squat", "good morning", "hip hinge", "terra"]):
        flags.append("lombar")
        adj_rir += 0.75
        adj_pct -= 0.04
        score_delta -= 0.45
        block_up = True

    # caps (não transformar um checkbox em apocalipse)
    adj_rir = max(0.0, min(2.0, adj_rir))
    adj_pct = max(-0.12, min(0.0, adj_pct))
    score_delta = max(-1.25, min(0.0, score_delta))

    return {
        "flags": list(flags),
        "adj_rir": float(adj_rir),
        "adj_load_pct": float(adj_pct),
        "score_delta": float(score_delta),
        "block_up": bool(block_up),
    }


def _yami_round_step() -> float:
    try:
        return float(yami_get_ctrl().get("round_step", 0.5) or 0.5)
    except Exception:
        return 0.5

def yami_adjust_rir_target(rir_base: float, item: dict, ex_name: str | None = None) -> float:
    try:
        base = float(rir_base)
    except Exception:
        base = 2.0

    ctrl = yami_get_ctrl()

    # prontidão do dia
    read = st.session_state.get("yami_readiness", {}) or {}
    try:
        base += float(read.get("adj_rir", 0.0) or 0.0)
    except Exception:
        pass

    # sinais do corpo (por exercício)
    if ex_name:
        try:
            body = yami_body_adjustment_for_ex(str(ex_name))
            base += float(body.get("adj_rir", 0.0) or 0.0)
        except Exception:
            pass

    # preferência manual (mais controlo)
    try:
        base += float(ctrl.get("effort_bias", 0.0) or 0.0)
    except Exception:
        pass

    # estilo (ligeiro, para não virar um jogo de RPG)
    try:
        s = str(ctrl.get("style", "Normal") or "Normal").lower()
        if s.startswith("conserv"):
            base += 0.25
        elif s.startswith("agress"):
            base -= 0.25
    except Exception:
        pass

    # Política de falha: compostos sem falha → mínimo RIR 1
    if str(item.get("tipo", "")).lower() == "composto":
        base = max(1.0, base)

    base = max(0.0, min(6.0, base))
    return float(round(base * 2) / 2.0)


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


def _rep_low_from_text(rep_str: str) -> int:
    s = str(rep_str).strip()
    nums = re.findall(r"\d+(?:[\.,]\d+)?", s)
    if not nums:
        return 0
    try:
        return int(float(nums[0].replace(",", ".")))
    except Exception:
        return 0


def _rep_top_from_range(rep_str: str) -> int:
    s = str(rep_str).strip().replace(" ", "")
    if "-" in s:
        try:
            return int(float(s.split("-")[-1]))
        except Exception:
            return 0
    # Para esquemas fixos/descendentes (15/12/10/8, 10+M+M, drop), não aplicar progressão dupla automática
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


def _yami_inc_steps(ex: str, item: dict) -> tuple[float, float]:
    """Incrementos típicos (subir/descer) para ajustes intra-sessão.

    Agora usa os knobs do utilizador (Controlo do Yami).
    """
    ctrl = yami_get_ctrl()
    try:
        is_lower = _is_lower_exercise(ex)
    except Exception:
        is_lower = False
    try:
        is_comp = str(item.get("tipo", "")).lower() == "composto"
    except Exception:
        is_comp = True

    try:
        inc_low = float(ctrl.get("inc_lower_comp", 5.0) or 5.0)
    except Exception:
        inc_low = 5.0
    try:
        inc_comp = float(ctrl.get("inc_comp", 2.5) or 2.5)
    except Exception:
        inc_comp = 2.5
    try:
        inc_iso = float(ctrl.get("inc_iso", 1.0) or 1.0)
    except Exception:
        inc_iso = 1.0

    inc = inc_low if (is_lower and is_comp) else (inc_comp if is_comp else inc_iso)
    return float(inc), float(inc)


def _yami_weight_profile_for_item(ex: str, item: dict, peso_base: float, df_last: pd.DataFrame | None = None) -> list[float]:
    """Gera um perfil de peso por série.

    - Se houver último treino com pesos por série, reaproveita as proporções (p.ex. 15/12/10/8 tende a subir).
    - Se for sequência fixa (15/12/10/8) sem histórico por série, estima uma progressão leve.
    - Caso contrário, mantém constante (o ajuste fino fica para a regra intra-sessão).
    """
    try:
        series_n = int(item.get("series", 0) or 0)
    except Exception:
        series_n = 0
    if series_n <= 0:
        return []

    try:
        base = float(peso_base or 0)
    except Exception:
        base = 0.0
    if base <= 0:
        return [0.0 for _ in range(series_n)]

    rep_info = _parse_rep_scheme(str(item.get("reps", "")), series_n)
    kind = str(rep_info.get("kind") or "")

    # 1) Se houver df_last com pesos por série, mantém o padrão (rampa) relativo ao top set.
    #    O 'base' aqui representa o peso de trabalho sugerido (top set). As séries anteriores ficam como rampa.
    try:
        if df_last is not None and (not df_last.empty) and ("Peso (kg)" in df_last.columns):
            last_w = pd.to_numeric(df_last["Peso (kg)"], errors="coerce").tolist()
            last_w = [float(x) for x in last_w[:series_n] if pd.notna(x)]
            if last_w:
                w_max = float(max(last_w))
                if w_max > 0:
                    padded = list(last_w) + [w_max] * max(0, series_n - len(last_w))
                    ratios = [max(0.20, min(1.05, float(w) / w_max)) for w in padded[:series_n]]
                    out = [float(_round_to_nearest(base * ratios[s], _yami_round_step())) for s in range(series_n)]
                    # monotonia não-decrescente (rampa)
                    for j in range(1, len(out)):
                        if out[j] < out[j-1]:
                            out[j] = out[j-1]
                    return out
    except Exception:
        pass

    # 2) Sequência fixa/descendente (15/12/10/8): progressão leve estimada
    if kind == "fixed_seq":
        seq = list(rep_info.get("expected") or [])
        if len(seq) >= series_n:
            try:
                r0 = float(seq[0]) if float(seq[0]) > 0 else float(max(seq))
            except Exception:
                r0 = float(max(seq))
            mults = []
            for r in seq[:series_n]:
                rr = max(1.0, float(r))
                mults.append((r0 / rr) ** 0.35)

            # ajusta para o "base" representar a MÉDIA do bloco (mais robusto quando o base vem de histórico médio)
            try:
                mean_mult = float(sum(mults) / max(1, len(mults)))
            except Exception:
                mean_mult = 1.0
            base_adj = (base / mean_mult) if mean_mult > 0 else base

            out = [float(_round_to_nearest(base_adj * m, _yami_round_step())) for m in mults]
            return out

    # 3) Default: constante (o ajuste série-a-série vem da performance real)
    return [float(_round_to_nearest(base, _yami_round_step())) for _ in range(series_n)]


def _yami_suggest_weight_for_series(
    ex: str,
    item: dict,
    peso_base: float,
    df_last: pd.DataFrame | None,
    pending_sets: list,
    series_index: int,
    rir_target_num: float,
) -> float:
    """Sugere peso PARA A SÉRIE ATUAL (serie_index), ajustando com base na série anterior.

    Isto resolve o problema de "mesmo peso em todas as séries":
    - em 15/12/10/8, gera um perfil com pesos a subir ao longo das séries
    - em range (3–5, 8–12), ajusta a série seguinte com base no RIR/reps reais
    """
    try:
        s_idx = int(series_index)
    except Exception:
        s_idx = 0

    profile = _yami_weight_profile_for_item(ex, item, peso_base, df_last)
    base = float(profile[s_idx]) if (profile and 0 <= s_idx < len(profile)) else float(peso_base or 0)

    # sem dados intra-sessão -> usa perfil/base
    if not pending_sets:
        return float(base)

    # ajusta a partir da série anterior (última registada)
    last = pending_sets[-1] if isinstance(pending_sets, list) and pending_sets else {}
    try:
        last_w = float(last.get("peso", base) or base)
    except Exception:
        last_w = float(base)
    try:
        last_rir = float(last.get("rir", rir_target_num) or rir_target_num)
    except Exception:
        last_rir = float(rir_target_num)
    try:
        last_reps = int(float(last.get("reps", 0) or 0))
    except Exception:
        last_reps = 0

    rep_info = _parse_rep_scheme(str(item.get("reps", "")), int(item.get("series", 0) or 0))
    kind = str(rep_info.get("kind") or "")
    reps_low = int(rep_info.get("low") or 0) if kind in ("range", "fixed", "fixed_seq") else 0
    reps_high = int(rep_info.get("high") or 0) if kind in ("range", "fixed", "fixed_seq") else 0

    inc_up, inc_down = _yami_inc_steps(ex, item)

    # flags locais (evita NameError; usados em micro-steps)
    try:
        is_lower = _is_lower_exercise(ex)
    except Exception:
        is_lower = False
    try:
        is_comp = str(item.get("tipo", "")).lower() == "composto"
    except Exception:
        is_comp = True



    # baseline: usa o perfil previsto (rampa) quando disponível; caso contrário, parte do último peso usado
    sug = float(base) if base > 0 else float(last_w)

    # --- Autoregulação RIR: estimar e1RM pelo set anterior e ajustar para a série atual ---
    # Aproximação simples (Epley) usando "reps até à falha" ≈ reps + RIR.
    # (serve bem para ajustar de forma sensível; não é para "medir" 1RM absoluto).
    target_reps = 0
    try:
        if kind == "fixed_seq":
            seq = list(rep_info.get("expected") or [])
            if 0 <= s_idx < len(seq):
                target_reps = int(float(seq[s_idx]) or 0)
        if target_reps <= 0 and reps_low > 0 and reps_high > 0:
            target_reps = int(reps_high)
        if target_reps <= 0 and reps_low > 0:
            target_reps = int(reps_low)
        if target_reps <= 0:
            target_reps = max(1, int(last_reps) if last_reps > 0 else 1)
    except Exception:
        target_reps = max(1, int(last_reps) if last_reps > 0 else 1)

    def _epley_1rm(w: float, reps_to_fail: float) -> float:
        try:
            w = float(w)
            reps_to_fail = float(reps_to_fail)
        except Exception:
            return 0.0
        if w <= 0 or reps_to_fail <= 0:
            return 0.0
        r = min(15.0, reps_to_fail)  # cap para evitar exageros com reps altas
        return float(w) * (1.0 + (r / 30.0))

    def _weight_from_epley(est_1rm: float, reps_to_fail: float) -> float:
        try:
            est_1rm = float(est_1rm)
            reps_to_fail = float(reps_to_fail)
        except Exception:
            return 0.0
        if est_1rm <= 0 or reps_to_fail <= 0:
            return 0.0
        r = min(15.0, reps_to_fail)
        return float(est_1rm) / (1.0 + (r / 30.0))

    epley_w = 0.0
    if last_w > 0 and last_reps > 0:
        reps_to_fail_last = max(1.0, float(last_reps) + float(last_rir))
        est1rm = _epley_1rm(float(last_w), reps_to_fail_last)
        reps_to_fail_target = max(1.0, float(target_reps) + float(rir_target_num))
        epley_w = _weight_from_epley(est1rm, reps_to_fail_target)

    if epley_w > 0:
        # mistura com o perfil (rampa) para não perder o "desenho" do bloco
        sug = (0.65 * float(epley_w)) + (0.35 * float(sug))

    # ajuste fino por desvio de RIR
    delta_rir = float(last_rir) - float(rir_target_num)

    # micro-steps (mais sensível)
    # micro-passos por tipo (para sugestões mais sensíveis)
    if is_lower and is_comp:
        inc_micro = 2.5
    elif is_comp:
        inc_micro = 1.0
    else:
        inc_micro = 0.5


    # "aquecimento disfarçado" (muitas reps acima do alvo) -> sobe micro
    if reps_high > 0 and last_reps > (reps_high + 1) and last_rir >= float(rir_target_num):
        sug = float(sug) + float(inc_micro)

    # pesado: abaixo das reps mínimas ou RIR abaixo do alvo
    if (reps_low > 0 and last_reps > 0 and last_reps < reps_low) or (delta_rir <= -1.0):
        steps = 2 if delta_rir <= -1.75 else 1
        sug = max(0.0, float(sug) - (steps * float(inc_micro)))
    # folgado: acima do alvo com reps ok
    elif (reps_high <= 0 or last_reps >= max(1, reps_high)) and (delta_rir >= 0.75):
        steps = 2 if delta_rir >= 1.75 else 1
        sug = float(sug) + (steps * float(inc_micro))

    # limites práticos: evita saltos muito grandes série-a-série
    try:
        max_up = max(float(inc_up) * 2.0, float(last_w) * 0.08)
        max_down = max(float(inc_down) * 2.0, float(last_w) * 0.08)
        sug = min(float(last_w) + max_up, max(float(last_w) - max_down, float(sug)))
    except Exception:
        pass

    return float(_round_to_nearest(sug, _yami_round_step()))


def _prefill_sets_from_last(i, item, df_last, peso_sug, reps_default, rir_expect, use_df_exact: bool = True):
    """Preenche valores via payload pendente.

    Importante: não escrever diretamente em keys de widgets depois de eles já existirem no
    mesmo rerun (StreamlitAPIException). Em vez disso, guardamos um payload e aplicamos
    no rerun seguinte, antes dos widgets serem criados.
    """
    series_n = int(item.get("series", 0))
    pesos = []
    reps_list = []
    rirs = []
    if df_last is not None and not df_last.empty:
        pesos = pd.to_numeric(df_last.get("Peso (kg)"), errors="coerce").tolist() if "Peso (kg)" in df_last.columns else []
        reps_list = pd.to_numeric(df_last.get("Reps"), errors="coerce").tolist() if "Reps" in df_last.columns else []
        rirs = pd.to_numeric(df_last.get("RIR"), errors="coerce").tolist() if "RIR" in df_last.columns else []


    ex_name = str(item.get("ex", "") or item.get("exercicio", "") or item.get("Exercício", "") or "")
    try:
        peso_profile = _yami_weight_profile_for_item(
            ex_name,
            item,
            float(peso_sug or 0),
            df_last if (df_last is not None and not df_last.empty) else None,
        )
    except Exception:
        peso_profile = []

    if not peso_profile:
        try:
            peso_profile = [float(peso_sug or 0) for _ in range(series_n)]
        except Exception:
            peso_profile = [0.0 for _ in range(series_n)]

    payload = {"peso": [], "reps": [], "rir": []}
    for s in range(series_n):
        if use_df_exact and s < len(pesos) and pd.notna(pesos[s]):
            payload["peso"].append(float(pesos[s]))
        elif peso_sug > 0:
            payload["peso"].append(float(peso_profile[s] if s < len(peso_profile) else peso_sug))
        else:
            payload["peso"].append(0.0)

        if use_df_exact and s < len(reps_list) and pd.notna(reps_list[s]):
            payload["reps"].append(int(reps_list[s]))
        else:
            payload["reps"].append(int(reps_default))

        if use_df_exact and s < len(rirs) and pd.notna(rirs[s]):
            payload["rir"].append(float(rirs[s]))
        else:
            payload["rir"].append(float(rir_expect))

    st.session_state[f"prefill_payload_{i}"] = payload


def _apply_prefill_payload_if_any(i: int):
    key = f"prefill_payload_{i}"
    payload = st.session_state.get(key)
    if not isinstance(payload, dict):
        return
    pesos = payload.get("peso", []) or []
    reps_list = payload.get("reps", []) or []
    rirs = payload.get("rir", []) or []
    n = max(len(pesos), len(reps_list), len(rirs))
    for s in range(n):
        try:
            if s < len(pesos):
                st.session_state[f"peso_{i}_{s}"] = float(pesos[s])
            if s < len(reps_list):
                st.session_state[f"reps_{i}_{s}"] = int(reps_list[s])
            if s < len(rirs):
                st.session_state[f"rir_{i}_{s}"] = float(rirs[s])
        except Exception:
            pass
    try:
        del st.session_state[key]
    except Exception:
        pass


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
        df = _ensure_exercise_key_column(df)
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
EXERCISE_KEY_STOPWORDS = {
    "a", "o", "as", "os", "de", "do", "da", "dos", "das",
    "na", "no", "nas", "nos", "com", "sem", "e", "ou", "para",
    "por", "ao", "aos", "the", "and", "or"
}

EXERCISE_KEY_TOKEN_MAP = {
    "halteres": "halter",
    "dumbbell": "halter",
    "db": "halter",
    "neutro": "neutra",
    "neutra": "neutra",
    "pegada": "",
    "straight": "braco",
    "arm": "reto",
}

EXERCISE_KEY_ALIAS_PATTERNS = [
    (re.compile(r"\bsupino\s+inclinad[oa]\b.*\bhalter\b"), "supino inclinado halter"),
    (re.compile(r"\bpuxada\b.*\bpolia\b.*\bneutra\b"), "puxada polia neutra"),
    (re.compile(r"\beleva(?:cao|ç[aã]o)\s+lateral\b.*\bpolia\b"), "elevacao lateral polia"),
    (re.compile(r"\beleva(?:cao|ç[aã]o)\s+lateral\b.*\bhalter\b"), "elevacao lateral halter"),
    (re.compile(r"\breverse\s+pec\s+deck\b"), "reverse pec deck"),
    (re.compile(r"\brear\s+delt\b.*\bmachine\b"), "reverse pec deck"),
]


def _strip_accents_text(v: str) -> str:
    try:
        return "".join(
            ch for ch in unicodedata.normalize("NFKD", str(v or ""))
            if not unicodedata.combining(ch)
        )
    except Exception:
        return str(v or "")


def exercise_key(ex_name: str) -> str:
    s = _strip_accents_text(str(ex_name or "")).lower().strip()
    if not s:
        return ""
    s = s.replace("→", " ").replace("->", " ").replace("/", " ")
    s = re.sub(r"[()\[\],;:]+", " ", s)
    s = re.sub(r"[^a-z0-9\s+-]", " ", s)
    s = re.sub(r"\b\d+(?:s)?\b", " ", s)
    tokens = []
    for tok in s.split():
        tok = EXERCISE_KEY_TOKEN_MAP.get(tok, tok)
        tok = str(tok or "").strip()
        if not tok or tok in EXERCISE_KEY_STOPWORDS:
            continue
        if tok.endswith("s") and len(tok) > 4 and tok not in {"legs"}:
            tok = tok[:-1]
        tokens.append(tok)
    norm = re.sub(r"\s+", " ", " ".join(tokens)).strip()
    if not norm:
        return ""
    for patt, repl in EXERCISE_KEY_ALIAS_PATTERNS:
        if patt.search(norm):
            return repl
    return norm


def _ensure_exercise_key_column(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame(columns=SCHEMA_COLUMNS)
    out = df.copy()
    if "Exercício_Key" not in out.columns:
        out["Exercício_Key"] = ""
    try:
        base_ex = out["Exercício"] if "Exercício" in out.columns else pd.Series([""] * len(out), index=out.index)
        curr_key = out["Exercício_Key"].fillna("").astype(str).str.strip()
        mask = curr_key.eq("")
        if mask.any():
            out.loc[mask, "Exercício_Key"] = base_ex.loc[mask].apply(exercise_key)
        else:
            out["Exercício_Key"] = out["Exercício_Key"].apply(exercise_key)
    except Exception:
        try:
            out["Exercício_Key"] = out.get("Exercício", "").apply(exercise_key)
        except Exception:
            out["Exercício_Key"] = ""
    return out


def _exercise_label_map(df: pd.DataFrame) -> dict:
    out = {}
    if df is None or getattr(df, "empty", True):
        return out
    d = _ensure_exercise_key_column(df)
    if d.empty:
        return out
    if "Exercício" not in d.columns:
        return out
    try:
        d["_label_dt"] = pd.to_datetime(d.get("Data"), dayfirst=True, errors="coerce")
    except Exception:
        d["_label_dt"] = pd.NaT
    d = d.sort_values(["_label_dt"], ascending=False, na_position="last")
    for key, grp in d.groupby("Exercício_Key", dropna=False):
        skey = str(key or "").strip()
        if not skey:
            continue
        label = str(grp.iloc[0].get("Exercício", "") or skey).strip() or skey
        out[skey] = label
    return out


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
    df = _ensure_exercise_key_column(df)
    for c in SCHEMA_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[SCHEMA_COLUMNS].copy()
    if 'Exercício' in df.columns:
        df['Exercício'] = df['Exercício'].apply(lambda x: '' if pd.isna(x) else str(x).strip())
    if 'Exercício_Key' in df.columns:
        df['Exercício_Key'] = df.apply(lambda r: exercise_key(r.get('Exercício_Key') or r.get('Exercício')), axis=1)

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
                    return _lisbon_today_date().strftime('%d/%m/%Y')
            except Exception:
                pass
            sx=str(x).strip()
            if not sx:
                return _lisbon_today_date().strftime('%d/%m/%Y')
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
    d = _ensure_exercise_key_column(df)
    ex_key = exercise_key(ex)
    d = d[d['Perfil'].astype(str) == str(perfil)].copy()
    if ex_key:
        d = d[d['Exercício_Key'].astype(str) == str(ex_key)]
    else:
        d = d[d['Exercício'].astype(str) == str(ex)]
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




def _round_to_nearest(x: float, step: float = 0.5) -> float:
    try:
        x = float(x)
        step = float(step)
        if step <= 0:
            return round(x, 2)
        return round(x / step) * step
    except Exception:
        return 0.0


def _parse_rep_scheme(rep_text: str, series_hint: int | None = None) -> dict:
    s = str(rep_text or '').strip()
    s_low = s.lower().replace(' ', '')
    nums = []
    for n in re.findall(r"\d+(?:[\.,]\d+)?", s_low):
        try:
            nums.append(int(float(n.replace(',', '.'))))
        except Exception:
            pass
    out = {
        'raw': s, 'kind': 'special', 'low': 0, 'high': 0, 'expected': [],
        'has_drop': 'drop' in s_low, 'has_mini': '+m' in s_low or 'm+m' in s_low
    }
    if not nums:
        return out

    # Ex.: 4x8+M+M -> ignorar o 4 (series) e usar 8 como alvo principal
    if 'x' in s_low and len(nums) >= 2:
        if series_hint is not None and nums[0] == int(series_hint):
            reps_main = nums[1]
            out.update({'kind': 'fixed', 'low': reps_main, 'high': reps_main, 'expected': [reps_main]})
            return out

    # Faixa clássica 8-12
    if '-' in s_low and len(nums) >= 2 and '/' not in s_low:
        lo, hi = nums[0], nums[1]
        if lo > hi:
            lo, hi = hi, lo
        out.update({'kind': 'range', 'low': lo, 'high': hi, 'expected': [lo, hi]})
        return out

    # Sequência fixa/descendente 15/12/10/8
    if '/' in s_low and len(nums) >= 2 and '(' not in s_low:
        out.update({'kind': 'fixed_seq', 'low': min(nums), 'high': max(nums), 'expected': nums})
        return out

    # Um alvo fixo simples
    if len(nums) == 1:
        out.update({'kind': 'fixed', 'low': nums[0], 'high': nums[0], 'expected': [nums[0]]})
        return out

    # Esquemas especiais (clusters / 4(5/4/3/2/1)) -> usar números apenas como referência leve
    out.update({'kind': 'special', 'low': min(nums), 'high': max(nums), 'expected': nums})
    return out


def _historico_resumos_exercicio(df: pd.DataFrame, perfil: str, ex: str,
                                 bloco: str | None = None,
                                 plano_id: str | None = None) -> list:
    """Resumo histórico por sessão para um exercício.

    Mantém chaves existentes (compat) e adiciona métricas úteis para o Yami:
    - w_work: maior peso do dia
    - tonnage: tonelagem total (peso * reps)
    - e1rm_simple: melhor 1RM estimado (Epley) só com reps
    - e1rm_rir: melhor 1RM estimado (Epley) usando reps + RIR quando existe

    Preferência de escopo para evitar misturar contextos demasiado diferentes:
    1) mesmo Plano_ID + Bloco
    2) mesmo Plano_ID
    3) mesmo exercício no perfil (fallback)
    """
    if df is None or getattr(df, 'empty', True):
        return []
    d = _ensure_exercise_key_column(df)
    if 'Perfil' not in d.columns or 'Exercício' not in d.columns:
        return []
    ex_key = exercise_key(ex)
    d = d[d['Perfil'].astype(str) == str(perfil)].copy()
    if ex_key:
        d = d[d['Exercício_Key'].astype(str) == str(ex_key)].copy()
    else:
        d = d[d['Exercício'].astype(str) == str(ex)].copy()
    if d.empty:
        return []

    has_plan = 'Plano_ID' in d.columns
    has_block = 'Bloco' in d.columns
    plano_id = None if plano_id is None else str(plano_id)
    bloco = None if bloco is None else str(bloco)

    d_scope = d
    try:
        if has_plan and plano_id:
            d_plan_block = d[(d['Plano_ID'].astype(str) == plano_id)].copy()
            if has_block and bloco:
                d_plan_block = d_plan_block[d_plan_block['Bloco'].astype(str) == bloco].copy()
            if len(d_plan_block) >= 2:
                d_scope = d_plan_block
            elif len(d_plan_block) == 1:
                d_plan = d[(d['Plano_ID'].astype(str) == plano_id)].copy()
                d_scope = d_plan if len(d_plan) >= 2 else d_plan_block
            else:
                d_plan = d[(d['Plano_ID'].astype(str) == plano_id)].copy()
                if len(d_plan) >= 2:
                    d_scope = d_plan
                elif has_block and bloco:
                    d_block = d[d['Bloco'].astype(str) == bloco].copy()
                    if len(d_block) >= 2:
                        d_scope = d_block
        elif has_block and bloco:
            d_block = d[d['Bloco'].astype(str) == bloco].copy()
            if len(d_block) >= 2:
                d_scope = d_block
    except Exception:
        d_scope = d

    d = d_scope.copy()
    if d.empty:
        return []
    d['_dt'] = pd.to_datetime(d.get('Data'), dayfirst=True, errors='coerce')
    d = d.sort_values('_dt', ascending=False, na_position='last')

    def _safe_float(x, default=None):
        try:
            if x is None:
                return default
            if isinstance(x, str) and x.strip() == '':
                return default
            fx = float(x)
            try:
                if pd.isna(fx):
                    return default
            except Exception:
                pass
            if fx == float('inf') or fx == float('-inf'):
                return default
            return fx
        except Exception:
            return default

    def _epley_1rm(w: float, reps_to_fail: float) -> float:
        try:
            w = float(w)
            reps_to_fail = float(reps_to_fail)
        except Exception:
            return 0.0
        if w <= 0 or reps_to_fail <= 0:
            return 0.0
        r = min(15.0, reps_to_fail)  # cap para evitar exageros com reps altas
        return float(w) * (1.0 + (r / 30.0))

    out = []
    for _, row in d.iterrows():
        pesos_raw = _parse_num_list(row.get('Peso'))
        reps_raw = _parse_num_list(row.get('Reps'))
        rirs_raw = _parse_num_list(row.get('RIR'))

        pesos_raw = [_safe_float(x, None) for x in pesos_raw]
        reps_raw = [_safe_float(x, None) for x in reps_raw]
        rirs_raw = [_safe_float(x, None) for x in rirs_raw]

        # tamanho real do exercício (broadcast simples para listas com 1 valor)
        n_sets = max(len(pesos_raw), len(reps_raw), len(rirs_raw))
        if n_sets <= 0:
            continue

        def _get(arr, i):
            if not arr:
                return None
            if len(arr) == 1:
                return arr[0]
            return arr[i] if i < len(arr) else None

        pesos = []
        reps = []
        rirs = []
        for i in range(n_sets):
            w = _get(pesos_raw, i)
            r = _get(reps_raw, i)
            rr = _get(rirs_raw, i)
            pesos.append(float(w) if (w is not None and w > 0) else None)
            reps.append(int(round(float(r))) if (r is not None and r > 0) else None)
            rirs.append(float(rr) if (rr is not None) else None)

        pesos_num = [w for w in pesos if isinstance(w, (int, float)) and pd.notna(w) and float(w) > 0]
        reps_num = [r for r in reps if isinstance(r, (int, float)) and pd.notna(r) and float(r) > 0]
        rirs_num = [rr for rr in rirs if isinstance(rr, (int, float)) and pd.notna(rr)]

        peso_medio = float(sum(pesos_num) / len(pesos_num)) if pesos_num else 0.0
        reps_media = float(sum(reps_num) / len(reps_num)) if reps_num else 0.0
        rir_media = float(sum(rirs_num) / len(rirs_num)) if rirs_num else None

        # trabalho (top set) e volume
        w_work = float(max(pesos_num)) if pesos_num else 0.0
        tonnage = 0.0
        for i in range(n_sets):
            w = pesos[i]
            r = reps[i]
            if isinstance(w, (int, float)) and isinstance(r, (int, float)) and w > 0 and r > 0:
                tonnage += float(w) * float(r)

        # e1RM (Epley)
        e1rm_simple = 0.0
        e1rm_rir = 0.0
        for i in range(n_sets):
            w = pesos[i]
            r = reps[i]
            rr = rirs[i]
            if not (isinstance(w, (int, float)) and isinstance(r, (int, float))):
                continue
            if w <= 0 or r <= 0:
                continue

            e1 = _epley_1rm(w, r)
            if e1 > e1rm_simple:
                e1rm_simple = e1

            # se tiver RIR, melhora a estimativa (reps até falha ≈ reps + RIR)
            if isinstance(rr, (int, float)) and pd.notna(rr):
                e1r = _epley_1rm(w, max(1.0, float(r) + float(rr)))
                if e1r > e1rm_rir:
                    e1rm_rir = e1r

        if e1rm_rir <= 0:
            e1rm_rir = e1rm_simple

        out.append({
            'data': row.get('Data', '—'),
            'dt': row.get('_dt'),
            'peso_medio': float(peso_medio),
            'reps_media': float(reps_media),
            'reps_min': int(min([x for x in reps_num if x is not None])) if reps_num else 0,
            'reps_max': int(max([x for x in reps_num if x is not None])) if reps_num else 0,
            'rirs_media': float(rir_media) if rir_media is not None else None,
            'n_sets': int(n_sets),

            # compat
            'pesos': [w for w in pesos_num],
            'reps': [int(x) for x in reps_num],
            'rirs': [float(x) for x in rirs_num],

            # contexto
            'bloco': str(row.get('Bloco', '') or ''),
            'plano_id': str(row.get('Plano_ID', '') or ''),

            # novos sinais
            'w_work': float(w_work),
            'tonnage': float(tonnage),
            'e1rm_simple': float(e1rm_simple),
            'e1rm_rir': float(e1rm_rir),
            'has_rir': bool(len(rirs_num) > 0),
        })
    return out

def yami_coach_sugestao(df_hist: pd.DataFrame, perfil: str, ex: str, item: dict, bloco: str, semana: int, plano_id: str) -> dict:
    """Coach de progressão ('Yami'): sugere carga e explica o porquê, com heurística mais robusta."""
    yami_mode = str(st.session_state.get('yami_mode', 'Brutal'))

    ctrl = yami_get_ctrl()
    rstep = _yami_round_step()

    series_alvo = int(item.get('series', 0) or 0)
    rep_info = _parse_rep_scheme(item.get('reps', ''), series_alvo)
    rir_alvo_base = float(rir_alvo_num(item.get('tipo', ''), bloco, semana) or 2.0)
    rir_alvo_num_ = float(yami_adjust_rir_target(rir_alvo_base, item, ex_name=ex))

    read = st.session_state.get('yami_readiness', {}) or {}
    try:
        read_score_delta = float(read.get('score_delta', 0.0) or 0.0)
        read_adj_pct = float(read.get('adj_load_pct', 0.0) or 0.0)
        read_label = str(read.get('label', 'Normal') or 'Normal')
    except Exception:
        read_score_delta, read_adj_pct, read_label = 0.0, 0.0, 'Normal'

    # sinais do corpo (entra na equação)
    body = yami_body_adjustment_for_ex(str(ex))
    try:
        body_score_delta = float(body.get('score_delta', 0.0) or 0.0)
        body_adj_pct = float(body.get('adj_load_pct', 0.0) or 0.0)
        body_flags = list(body.get('flags', []) or [])
    except Exception:
        body_score_delta, body_adj_pct, body_flags = 0.0, 0.0, []

    total_score_delta = float(read_score_delta) + float(body_score_delta)
    total_adj_pct = float(read_adj_pct) + float(body_adj_pct)
    # bloquear subida de carga quando há sinal relevante (configurável)
    body_block_up = bool(body.get('block_up', False)) and bool(ctrl.get('pain_blocks_up', True))


    hist = _historico_resumos_exercicio(df_hist, perfil, ex, bloco=bloco, plano_id=plano_id)
    latest = hist[0] if hist else None
    prev = hist[1] if len(hist) > 1 else None
    prev2 = hist[2] if len(hist) > 2 else None

    # --- Tendência extra (e1RM EMA) + fase do ciclo (periodização) ---
    n_hist = len(hist)

    # Fase do ciclo (fora do deload explícito): mexe um pouco na agressividade da sugestão
    phase = "build"
    phase_bias = 0.0
    try:
        # GUI: estágio 1-5 (deload é tratado fora)
        if 'GUI_PPLA_ID' in globals() and str(plano_id) == str(GUI_PPLA_ID):
            try:
                _stage = int(gui_stage_week(int(semana))) if 'gui_stage_week' in globals() else None
            except Exception:
                _stage = None
            if _stage == 1:
                phase = "build"
                phase_bias -= 0.10
            elif _stage == 5:
                phase = "push"
                phase_bias += 0.20
        else:
            # Base: semanas de "pico" (mais agressivas) e semanas de reentrada após deload
            try:
                if str(bloco) in ("Hipertrofia", "Força") and ('is_intensify_hypertrophy' in globals()) and bool(is_intensify_hypertrophy(int(semana))):
                    phase = "push"
                    phase_bias += 0.20
            except Exception:
                pass
            try:
                if int(semana) in (1, 5):
                    phase_bias -= 0.08
            except Exception:
                pass
    except Exception:
        phase = "build"
        phase_bias = 0.0

    # EMA de e1RM (quanto mais sessões, mais fundamentada a progressão)
    e1_vals = []
    try:
        for h in list(reversed(hist[:6])):  # oldest -> newest
            v = float(h.get('e1rm_rir', 0.0) or 0.0)
            if v > 0:
                e1_vals.append(v)
    except Exception:
        e1_vals = []

    def _ema(vals, alpha: float = 0.55) -> float:
        try:
            if not vals:
                return 0.0
            e = float(vals[0])
            for x in vals[1:]:
                e = (alpha * float(x)) + ((1.0 - alpha) * e)
            return float(e)
        except Exception:
            return 0.0

    ema_now = _ema(e1_vals, 0.55) if e1_vals else 0.0
    ema_prev = _ema(e1_vals[:-1], 0.55) if len(e1_vals) >= 2 else 0.0
    ema_delta_pct = ((ema_now - ema_prev) / ema_prev) if (ema_prev and ema_prev > 0) else 0.0


    is_lower = _is_lower_exercise(ex)
    is_comp = str(item.get('tipo', '')).lower() == 'composto'

    # Incrementos por tipo (user-controlled)
    try:
        inc_low_comp = float(ctrl.get("inc_lower_comp", 5.0) or 5.0)
    except Exception:
        inc_low_comp = 5.0
    try:
        inc_comp = float(ctrl.get("inc_comp", 2.5) or 2.5)
    except Exception:
        inc_comp = 2.5
    try:
        inc_iso = float(ctrl.get("inc_iso", 1.0) or 1.0)
    except Exception:
        inc_iso = 1.0

    if is_lower and is_comp:
        inc_up = inc_down = inc_low_comp
    elif is_comp:
        inc_up = inc_down = inc_comp
    else:
        inc_up = inc_down = inc_iso

    def _fmt_inc(v: float) -> str:
        return str(int(v)) if float(v).is_integer() else str(v)

    latest_work = float(latest.get('w_work', latest.get('peso_medio', 0)) or 0) if latest else 0.0
    if not latest or float(latest_work) <= 0:
        return {
            'acao': 'Sem base suficiente',
            'peso_sugerido': 0.0,
            'delta': 0.0,
            'confianca': 'baixa',
            'resumo': 'Primeiro regista uma sessão limpa. Depois eu afino isto como deve ser.',
            'razoes': [
                'Sem histórico suficiente neste exercício para inferir tendência real.',
                f'Alvo atual: {item.get("series", "?")} séries • {item.get("reps", "?")} reps • RIR {rir_alvo_num_:.1f}.',
                'Faz a sessão com técnica estável e RIR honesto para eu ler o teu padrão.'
            ]
        }

    p_atual = float(latest.get('w_work', latest.get('peso_medio', 0)) or 0)
    reps_list = list(latest.get('reps', []) or [])
    rirs_list = [float(x) for x in list(latest.get('rirs', []) or []) if x is not None]
    reps_media = float(latest.get('reps_media', 0) or 0)
    rir_media = None if latest.get('rirs_media') is None else float(latest.get('rirs_media'))

    rir_eff = None if rir_media is None else float(rir_media)


    low = int(rep_info.get('low') or 0)
    high = int(rep_info.get('high') or 0)
    rep_kind = str(rep_info.get('kind') or '')
    hit_low_all = bool(reps_list) and (low > 0) and all(int(r) >= low for r in reps_list)
    hit_top_all = bool(reps_list) and (high > 0) and all(int(r) >= high for r in reps_list)
    falhou_min = bool(reps_list) and (low > 0) and any(int(r) < low for r in reps_list)
    sessao_incompleta = series_alvo > 0 and int(latest.get('n_sets', 0) or 0) < series_alvo
    sets_ratio = (int(latest.get('n_sets', 0) or 0) / max(1, series_alvo)) if series_alvo else 1.0

    deload_now = bool(is_deload_for_plan(semana, plano_id))

    reasons = []
    reasons.append(
        f"Último treino ({latest.get('data','—')}): {latest.get('n_sets',0)}/{series_alvo or latest.get('n_sets',0)} séries · top set {p_atual:.1f} kg · média {reps_media:.1f} reps"
        + (f" · RIR {rir_media:.1f}" if rir_media is not None else "")
    )
    if low and high and rep_kind in ('range', 'fixed', 'fixed_seq'):
        reasons.append(f"Alvo técnico: {low if low==high else f'{low}–{high}'} reps por série com RIR ~{rir_alvo_num_:.1f}.")
    elif rep_info.get('raw'):
        reasons.append(f"Esquema do exercício: {rep_info.get('raw')} (peso maior no RIR/tendência).")

    # tendência e consistência (até 3 sessões)
    trend_score = 0.0
    trend_bits = []
    same_load_streak = []
    for h in [latest, prev, prev2]:
        if not h:
            continue
        same_load_streak.append(float(h.get('w_work', h.get('peso_medio', 0)) or 0))
    stable_load = False
    if len(same_load_streak) >= 2:
        stable_load = (max(same_load_streak[:2]) - min(same_load_streak[:2])) <= max(0.5, p_atual * 0.01)

    if prev and float(prev.get('w_work', prev.get('peso_medio', 0)) or 0) > 0:
        p_prev = float(prev.get('w_work', prev.get('peso_medio', 0)) or 0)
        reps_prev = float(prev.get('reps_media', 0) or 0)
        rir_prev = prev.get('rirs_media')
        same_load = abs(p_atual - p_prev) <= max(0.5, p_prev * 0.01)
        if same_load:
            d_reps = reps_media - reps_prev
            d_rir = (float(rir_media) - float(rir_prev)) if (rir_media is not None and rir_prev is not None) else 0.0
            if d_reps >= 0.75:
                trend_score += 1.0
                trend_bits.append(f"mais reps na mesma carga ({d_reps:+.1f})")
            elif d_reps <= -0.75:
                trend_score -= 1.0
                trend_bits.append(f"menos reps na mesma carga ({d_reps:+.1f})")
            if d_rir >= 0.5:
                trend_score += 0.5
                trend_bits.append(f"RIR subiu ({d_rir:+.1f})")
            elif d_rir <= -0.5:
                trend_score -= 0.5
                trend_bits.append(f"RIR caiu ({d_rir:+.1f})")
        else:
            if p_atual > p_prev and reps_media >= reps_prev - 0.5:
                trend_score += 1.0
                trend_bits.append('seguraste reps mesmo após subir carga')
            elif p_atual > p_prev and rir_media is not None and prev.get('rirs_media') is not None and float(rir_media) < float(prev.get('rirs_media')) - 1.0:
                trend_score -= 0.5
                trend_bits.append('a subida de carga cobrou demasiado no RIR')

    # estagnação / sobrecarga persistente
    stall_flag = False
    overload_flag = False
    if len(hist) >= 3:
        trio = hist[:3]
        pesos_trio = [float(h.get('w_work', h.get('peso_medio', 0)) or 0) for h in trio]
        same_load_3 = (max(pesos_trio) - min(pesos_trio)) <= max(0.5, p_atual * 0.01)
        if same_load_3:
            reps_trio = [float(h.get('reps_media', 0) or 0) for h in trio]
            # sem evolução real nas reps e RIR a cair -> sinal de carga alta/fadiga
            if max(reps_trio) - min(reps_trio) < 0.75:
                stall_flag = True
                if all((h.get('rirs_media') is not None and float(h.get('rirs_media')) <= max(0.5, rir_alvo_num_ - 0.5)) for h in trio if h.get('rirs_media') is not None):
                    overload_flag = True

    score = 0.0
    # estilo do Yami (tende a subir mais cedo ou segurar mais)
    try:
        score += float(yami_style_score_bias(ctrl.get('style', 'Normal')))
    except Exception:
        pass

    # fase do ciclo (periodização): micro-inclinação, não magia
    try:
        if abs(float(phase_bias)) > 1e-9:
            score += float(phase_bias)
            if str(phase) == "push":
                reasons.append("Fase do ciclo: semana mais agressiva → micro-subidas podem aparecer mais cedo.")
            elif float(phase_bias) < 0:
                reasons.append("Fase do ciclo: semana de (re)entrada → foco em técnica/consistência.")
    except Exception:
        pass

    if deload_now:
        p_sug = max(0.0, _round_to_nearest(p_atual * 0.88, rstep))
        delta = p_sug - p_atual
        reasons += [
            'Semana de deload detetada neste plano.',
            'Baixar ~10–15% mantém técnica e deixa fadiga/tendões assentar.'
        ]
        return {
            'acao': 'DELOAD (~-12%)',
            'peso_sugerido': p_sug,
            'delta': delta,
            'confianca': 'alta',
            'resumo': 'Hoje não é para provar força. É para afiar técnica e sair melhor do que entraste.',
            'razoes': reasons[:7],
            'score': -3.0,
            'peso_atual': p_atual,
        }

    if sessao_incompleta:
        score -= 0.25
        reasons.append('Sessão anterior incompleta: leitura parcial (vou ser conservador).')
        if sets_ratio < 0.67:
            score -= 0.5
            reasons.append('Menos de 2/3 das séries registadas: confiança baixa para mexer na carga.')

    # Reps vs alvo
    if rep_kind in ('range', 'fixed', 'fixed_seq') and low > 0:
        if falhou_min:
            score -= 2.0
            reasons.append('Ficaste abaixo do mínimo de reps em pelo menos uma série.')
        elif hit_top_all and high > 0:
            score += 2.0
            reasons.append('Bateste o topo da faixa em todas as séries.')
        elif hit_low_all:
            score += 0.75
            reasons.append('Cumpriste o mínimo da faixa em todas as séries.')
    else:
        reasons.append('Esquema especial: a decisão vai apoiar-se mais no RIR e na tendência recente.')


    # RIR vs alvo (usa RIR registado)
    if rir_eff is not None:
        desvio = float(rir_eff) - float(rir_alvo_num_)
        _rir_lbl = f"RIR {float(rir_eff):.1f}"

        if desvio >= 1.25:
            score += 1.25
            reasons.append(f'{_rir_lbl} bem acima do alvo ({rir_alvo_num_:.1f}) → sobra margem real.')
        elif desvio >= 0.5:
            score += 0.5
            reasons.append(f'{_rir_lbl} ligeiramente acima do alvo ({rir_alvo_num_:.1f}).')
        elif desvio <= -1.25:
            score -= 2.0
            reasons.append(f'{_rir_lbl} muito abaixo do alvo ({rir_alvo_num_:.1f}) → pesado demais.')
        elif desvio <= -0.5:
            score -= 0.75
            reasons.append(f'{_rir_lbl} abaixo do alvo ({rir_alvo_num_:.1f}).')

        # Política de falha / proteção de técnica
        if float(rir_eff) <= 0.5:
            score -= 0.75
            reasons.append('Foste demasiado perto da falha; prefiro proteger técnica e recuperação.')
    else:
        reasons.append('Sem RIR registado: eu consigo sugerir, mas com menos precisão.')
        score -= 0.25

    # Consistência intra-sessão (dispersão de reps)
    if len(reps_list) >= 3 and rep_kind in ('range', 'fixed', 'fixed_seq'):
        amp = max(reps_list) - min(reps_list)
        if amp <= 1:
            score += 0.5
            reasons.append('Reps consistentes entre séries (bom sinal de controlo).')
        elif amp >= 4:
            score -= 0.5
            reasons.append('Queda grande de reps entre séries (fadiga alta / carga agressiva).')

    score += trend_score
    if trend_bits:
        reasons.append('Tendência: ' + '; '.join(trend_bits) + '.')

    # Tendência por e1RM (EMA): confirma se estás a subir/descansar ou a descarrilar
    try:
        if float(ema_now) > 0 and float(ema_prev) > 0:
            if float(ema_delta_pct) >= 0.015:
                score += 0.45
                reasons.append(f"Tendência (e1RM): a subir (~{float(ema_delta_pct)*100:+.1f}%).")
            elif float(ema_delta_pct) <= -0.015:
                score -= 0.55
                reasons.append(f"Tendência (e1RM): a cair (~{float(ema_delta_pct)*100:+.1f}%).")
    except Exception:
        pass

    if stall_flag:
        score -= 0.5
        reasons.append('Estagnação recente (2–3 sessões) detectada na mesma carga.')
    if overload_flag:
        score -= 0.75
        reasons.append('Estagnação + RIR baixo recorrente: sinal de fadiga/carga alta.')

    # Prontidão do dia (check-in) — pode inclinar a decisão
    try:
        if abs(float(total_score_delta)) > 1e-9 or abs(float(total_adj_pct)) > 1e-9:
            score += float(total_score_delta)
            reasons.append(f"Contexto hoje: {read_label} (ajuste {float(total_adj_pct)*100:+.0f}% carga).")
            if body_flags:
                reasons.append(f"Sinais do corpo: {', '.join(body_flags)} (mais conservador neste padrão).")
    except Exception:
        pass

    # Proteções para esquemas especiais e sessões incompletas
    if rep_kind == 'special':
        score = max(-1.75, min(1.75, score))
    if sessao_incompleta:
        score = max(-1.25, min(1.0, score))


    # Deload recomendado (fora de semana de deload do plano)
    deload_reco = False
    deload_force = False
    try:
        if overload_flag:
            deload_reco = True
            if str(read_label) in ("Baixa", "Média-baixa") or float(score) <= -2.0:
                deload_force = True
        elif stall_flag and float(score) <= -1.75 and str(read_label) in ("Baixa", "Média-baixa"):
            deload_reco = True
    except Exception:
        deload_reco = False
        deload_force = False

    if deload_reco:
        reasons.append("Sugestão: deload 1 semana → -10% carga e -40–60% séries, mantendo RIR 3–4.")

    # Decisão final (mais granular + micro-ajustes)
    # Ideia: quando o sinal é "pequeno mas real", mexer pouco (microloading) em vez de só 0/+inc_up.
    try:
        inc_micro = max(0.5, float(inc_up) / 2.0)
    except Exception:
        inc_micro = 0.5

    if score >= 2.25:
        acao = f"+{_fmt_inc(inc_up)}kg"
        p_sug = _round_to_nearest(p_atual + inc_up, rstep)
        resumo = 'Boa execução. Vamos subir — sem pressa, mas sem medo.'
    elif score >= 0.6:
        acao = f"+{_fmt_inc(inc_micro)}kg"
        p_sug = _round_to_nearest(p_atual + inc_micro, rstep)
        resumo = 'Margem pequena, mas real. Sobe micro e mantém a técnica limpa.'
    elif score <= -2.25:
        acao = f"Baixa {_fmt_inc(inc_down)}kg"
        p_sug = max(0.0, _round_to_nearest(p_atual - inc_down, rstep))
        resumo = 'Isto está pesado para o alvo de hoje. Regride um passo e volta a construir.'
    elif score <= -0.6:
        # micro-regressão (mais frequente em isoladores; em compostos tende a "manter" antes de baixar)
        if is_comp and score > -1.0:
            acao = 'Mantém carga'
            p_sug = _round_to_nearest(p_atual, rstep)
            resumo = 'Está a apertar. Mantém e garante reps limpas.'
        else:
            acao = f"Baixa {_fmt_inc(inc_micro)}kg"
            p_sug = max(0.0, _round_to_nearest(p_atual - inc_micro, rstep))
            resumo = 'Baixa micro para bater reps/RIR com técnica.'
    else:
        acao = 'Mantém carga'
        p_sug = _round_to_nearest(p_atual, rstep)
        resumo = 'Consolida. Ainda não há sinal limpo para mexer na carga.'

    
    # Guardrails: controlo sobre subir carga
    try:
        # 1) Dupla progressão estrita: só sobe carga quando fecha topo de reps (e RIR não está a mentir)
        if str(acao).startswith('+') and bool(ctrl.get('strict_double_prog', False)):
            can_up = bool(hit_top_all) and (not sessao_incompleta)
            if rir_eff is not None:
                can_up = can_up and (float(rir_eff) >= float(rir_alvo_num_) - 0.25)
            if not can_up:
                acao = 'Mantém carga'
                p_sug = float(_round_to_nearest(p_atual, rstep))
                resumo = 'Dupla progressão: fecha reps limpas primeiro, depois sobe carga.'
        # 2) Sinal do corpo: não subir carga no padrão que está a reclamar
        if bool(body_block_up) and float(p_sug) > float(p_atual):
            acao = 'Mantém (sinal do corpo)'
            p_sug = float(_round_to_nearest(p_atual, rstep))
            resumo = 'Sinal do corpo ativo: hoje é controlo, não é ego.'
    except Exception:
        pass

# Ajuste por prontidão e deload recomendado
    try:
        if deload_force:
            acao = "DELOAD recomendado (-10%)"
            p_sug = max(0.0, _round_to_nearest(p_atual * 0.90, rstep))
            resumo = 'Fadiga alta. Deload curto para voltares a subir com qualidade.'
        else:
            # prontidão: pode "puxar" ligeiramente a carga sugerida
            if abs(float(total_adj_pct)) > 1e-9:
                _pre = float(p_sug)
                _adj = float(_round_to_nearest(float(p_sug) * (1.0 + float(total_adj_pct)), rstep))
                # em dias maus, não deixar subir só por score; em dias bons, permitir micro
                if float(total_adj_pct) < 0:
                    p_sug = min(float(p_sug), float(_adj))
                elif float(total_adj_pct) > 0:
                    p_sug = max(float(p_sug), float(_adj))

                _d2 = float(p_sug) - float(p_atual)
                if abs(_d2) < 0.25:
                    acao = "Mantém carga"
                    p_sug = float(_round_to_nearest(p_atual, rstep))
                elif _d2 > 0:
                    acao = f"+{_fmt_inc(_d2)}kg"
                else:
                    acao = f"Baixa {_fmt_inc(abs(_d2))}kg"

                if abs(float(p_sug) - float(_pre)) >= 0.5:
                    resumo = resumo + f" (prontidão: {read_label})"
    except Exception:
        pass

    # Confiança preliminar para governar guardrails antes do return final
    conf_q = 0.0
    try:
        conf_q += 0.25 if int(n_hist or 0) >= 2 else 0.0
        conf_q += 0.25 if int(n_hist or 0) >= 3 else 0.0
    except Exception:
        pass
    try:
        conf_q += 0.20 if (rir_eff is not None) else 0.0
    except Exception:
        pass
    try:
        conf_q += 0.20 if (not sessao_incompleta and float(sets_ratio) >= 0.85) else 0.0
    except Exception:
        pass
    try:
        conf_q += 0.10 if str(rep_kind) != 'special' else 0.0
    except Exception:
        pass
    conf_q = max(0.0, min(1.0, float(conf_q)))
    try:
        if sessao_incompleta and float(sets_ratio) < 0.67:
            conf_q -= 0.25
        if rir_eff is None:
            conf_q -= 0.10
        if int(n_hist or 0) < 2:
            conf_q -= 0.10
    except Exception:
        pass
    conf_q = max(0.0, min(1.0, float(conf_q)))
    if conf_q >= 0.75 and (prev is not None):
        conf = 'alta'
    elif conf_q >= 0.45:
        conf = 'média'
    else:
        conf = 'baixa'

    # Confiança afeta a agressividade (não é só cosmético)
    try:
        if str(conf) == 'baixa' and ('DELOAD' not in str(acao)):
            # com confiança baixa, o Yami não ganha direito a subir carga
            if float(p_sug) > float(p_atual):
                p_sug = float(_round_to_nearest(p_atual, rstep))
                acao = "Mantém carga"
                resumo = resumo + " (confiança baixa: não subo carga)"
            # e qualquer descida fica limitada a micro-ajuste
            try:
                max_move = float(inc_micro)
            except Exception:
                max_move = 0.5
            cap_dn = float(p_atual) - float(max_move)
            p_cap = float(p_sug)
            if p_cap < cap_dn:
                p_cap = cap_dn
            p_cap = float(_round_to_nearest(p_cap, rstep))

            if abs(float(p_cap) - float(p_sug)) >= 0.25:
                p_sug = float(p_cap)
                dcap = float(p_sug) - float(p_atual)
                if abs(dcap) < 0.25:
                    acao = "Mantém carga"
                    p_sug = float(_round_to_nearest(p_atual, rstep))
                else:
                    acao = f"Baixa {_fmt_inc(abs(dcap))}kg"
                resumo = resumo + " (confiança baixa: mexo pouco)"
    except Exception:
        pass

    # "Porque" (1 linha)
    try:
        if deload_force:
            porque = "Fadiga detectada (estagnação + esforço alto)."
        elif overload_flag:
            porque = "Estagnação recente + esforço alto."
        elif falhou_min:
            porque = "Abaixo do mínimo de reps."
        elif hit_top_all:
            porque = "Topo da faixa batido com margem."
        elif rir_eff is not None:
            if float(rir_eff) <= float(rir_alvo_num_) - 0.5:
                porque = "RIR abaixo do alvo (pesado)."
            elif float(rir_eff) >= float(rir_alvo_num_) + 0.5:
                porque = "RIR acima do alvo (margem)."
            else:
                porque = "Dentro do alvo: consolida."
        else:
            porque = "Sem RIR: conservador."
    except Exception:
        porque = "Consolida."


    # personalidade Yami (estilo Black Clover, sem perder explicação)
    # (frases curtas e variáveis para não ficar repetitivo)
    try:
        seed = int(hashlib.sha1(f"{perfil}|{ex}|{latest.get('data','')}".encode('utf-8')).hexdigest()[:8], 16)
    except Exception:
        seed = 1234
    rnd = random.Random(seed)
    up_lines = [
        "Ultrapassa os limites — com técnica.",
        "Não te percas: sobe com controlo.",
        "Se está leve, faz justiça: mais ferro."
    ]
    hold_lines = [
        "Mantém. O progresso é consistente, não teatral.",
        "Fica. Técnica limpa primeiro.",
        "Consolida. Ainda não há sinal limpo para subir."
    ]
    down_lines = [
        "Controla o ego. Recuar hoje é avançar amanhã.",
        "Baixa. Quero reps sólidas, não sofrimento inútil.",
        "Regride um passo e volta a construir."
    ]
    deload_lines = [
        "Deload. Afia a técnica e sai inteiro.",
        "Hoje é disciplina: menos carga, mais controlo.",
        "Recupera. Amanhã voltas a cortar o mundo."
    ]

    if 'DELOAD' in acao:
        prefix = rnd.choice(deload_lines)
    elif acao.startswith('+'):
        prefix = rnd.choice(up_lines)
    elif 'Baixa' in acao:
        prefix = rnd.choice(down_lines)
    else:
        prefix = rnd.choice(hold_lines)

    # modos (leve diferença de tom)
    if yami_mode.lower().startswith('frio'):
        resumo = prefix + " " + resumo
    elif yami_mode.lower().startswith('deload'):
        resumo = prefix + " " + resumo
    else:  # Brutal/Normal
        resumo = prefix + " " + resumo

    # confiança (não é só um rótulo: vai mandar na agressividade)
    conf_q = 0.0
    try:
        conf_q += 0.25 if int(n_hist or 0) >= 2 else 0.0
        conf_q += 0.25 if int(n_hist or 0) >= 3 else 0.0
    except Exception:
        pass
    try:
        conf_q += 0.20 if (rir_eff is not None) else 0.0
    except Exception:
        pass
    try:
        conf_q += 0.20 if (not sessao_incompleta and float(sets_ratio) >= 0.85) else 0.0
    except Exception:
        pass
    try:
        conf_q += 0.10 if str(rep_kind) != 'special' else 0.0
    except Exception:
        pass
    conf_q = max(0.0, min(1.0, float(conf_q)))

    # penalidades rápidas (dados fracos)
    try:
        if sessao_incompleta and float(sets_ratio) < 0.67:
            conf_q -= 0.25
        if rir_eff is None:
            conf_q -= 0.10
        if int(n_hist or 0) < 2:
            conf_q -= 0.10
    except Exception:
        pass
    conf_q = max(0.0, min(1.0, float(conf_q)))

    if conf_q >= 0.75 and (prev is not None):
        conf = 'alta'
    elif conf_q >= 0.45:
        conf = 'média'
    else:
        conf = 'baixa'

    # reduzir ruído
    reasons = [r for r in reasons if r]
    max_reasons = 7 if conf == 'alta' else 6
    if len(reasons) > max_reasons:
        reasons = reasons[:max_reasons]


    # peso de trabalho (top set) para ramp por série (especialmente em compostos com aquecimento/rampa registados)
    try:
        _w_list = list(latest.get('pesos', []) or [])
        w_work_last = float(max(_w_list)) if _w_list else float(p_atual)
    except Exception:
        w_work_last = float(p_atual)

    # peso de trabalho acompanha a variação sugerida (inclui prontidão)
    try:
        scale = float(p_sug) / float(p_atual) if float(p_atual) > 0 else 1.0
    except Exception:
        scale = 1.0
    if deload_now or deload_force or ('DELOAD' in str(acao)):
        scale = min(scale, 0.92)
    w_work_sug = float(_round_to_nearest(max(0.0, w_work_last * scale), 0.5))

    # Plano de execução (Top set + Back-off) — estrutura para tornar a sugestão acionável
    plan = {}
    try:
        # reps alvo para o top set (heurística simples)
        top_reps = int(high) if int(high or 0) > 0 else (int(low) if int(low or 0) > 0 else 0)
        try:
            if str(rep_kind) == 'fixed_seq':
                seq = list(rep_info.get('expected') or [])
                if seq:
                    top_reps = int(float(seq[-1]) or top_reps)
        except Exception:
            pass
        if top_reps <= 0:
            try:
                top_reps = int(round(float(reps_media))) if float(reps_media) > 0 else 0
            except Exception:
                top_reps = 0

        # drop típico para back-offs (varia por bloco/tipo e por sinais do corpo)
        drop = 0.06
        try:
            bl = str(bloco or '').lower()
            if bl.startswith('for'):      # força
                drop = 0.04 if bool(is_comp) else 0.06
            elif bl.startswith('hip'):    # hipertrofia
                drop = 0.06 if bool(is_comp) else 0.08
            elif bl == 'abc':
                drop = 0.06
        except Exception:
            pass
        try:
            if body_flags:
                drop += 0.02
        except Exception:
            pass
        try:
            if str(read_label) in ("Baixa", "Média-baixa"):
                drop += 0.01
        except Exception:
            pass
        drop = max(0.03, min(0.12, float(drop)))

        back_w = None
        if int(series_alvo or 0) > 1:
            back_w = float(_round_to_nearest(float(w_work_sug) * (1.0 - float(drop)), rstep))

        plan = {
            "phase": str(phase),
            "top_set": {"peso": float(w_work_sug), "reps": (int(top_reps) if int(top_reps or 0) > 0 else None), "rir": float(rir_alvo_num_)},
            "backoff": {"sets": int(max(0, int(series_alvo or 0) - 1)), "peso": (float(back_w) if back_w else None), "drop_pct": float(drop)},
            "rule": "Se falhares reps mínimas ou RIR ficar ~1 abaixo do alvo, baixa micro na próxima série. Se estiver folgado (+1 RIR) com reps ok, sobe micro.",
        }
    except Exception:
        plan = {}

    return {
        'acao': acao,
        'peso_sugerido': float(p_sug),
        'delta': float(p_sug - p_atual),
        'confianca': conf,
        'resumo': resumo,
        'plan': plan,
        'porque': str(porque),
        'razoes': reasons,
        'deload_reco': bool(deload_reco),
        'signals': list(body_flags) if 'body_flags' in locals() else [],
        'adj_total_load_pct': float(total_adj_pct) if 'total_adj_pct' in locals() else float(read_adj_pct),
        'readiness': str(read_label),
        'rir_alvo': float(rir_alvo_num_),
        'score': float(score),
        'peso_atual': float(p_atual),
        'peso_work_last': float(w_work_last),
        'peso_work_sugerido': float(w_work_sug),
    }


def yami_definir_descanso_s(base_s: int, rir_obtido: float | None, rir_alvo: float, reps_obtidas: int | None,
                            reps_low: int | None = None, reps_high: int | None = None,
                            reps_prev: int | None = None, is_composto: bool = True) -> int:
    """Define o descanso (em segundos) para a PRÓXIMA série, em estilo coach.

    A ideia é simples:
    - se a série saiu pesada (RIR baixo / queda grande de reps) -> mais descanso
    - se saiu folgada -> menos descanso (mas sem exageros)
    """
    try:
        base = int(base_s)
    except Exception:
        base = 75
    base = max(45, min(240, base))

    # Defaults seguros
    try:
        rir = float(rir_obtido) if rir_obtido is not None else None
    except Exception:
        rir = None
    try:
        reps = int(reps_obtidas) if reps_obtidas is not None else None
    except Exception:
        reps = None
    try:
        prev = int(reps_prev) if reps_prev is not None else None
    except Exception:
        prev = None

    add = 0
    # pesado demais
    if rir is not None and rir <= max(0.0, rir_alvo - 1.0):
        add += 20 if is_composto else 15
    # muito perto da falha
    if rir is not None and rir <= 0.5:
        add += 15

    # queda de reps intra-sessão
    if reps is not None and prev is not None:
        drop = prev - reps
        if drop >= 3:
            add += 20
        elif drop == 2:
            add += 10

    # falhou reps mínimas
    if reps_low is not None and reps is not None and int(reps_low) > 0 and reps < int(reps_low):
        add += 15

    # folgado demais -> pode reduzir um pouco
    sub = 0
    if rir is not None and rir >= (rir_alvo + 1.25):
        sub += 10
    if reps_high is not None and reps is not None and int(reps_high) > 0 and reps >= int(reps_high) and (rir is None or rir >= rir_alvo):
        sub += 5

    rest = base + add - sub

    # limites práticos
    if is_composto:
        rest = max(60, min(240, rest))
    else:
        rest = max(45, min(180, rest))
    return int(round(rest))


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

    today = _lisbon_today_date()
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
        'Exercício_Key': exercise_key(ex),
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




def _session_block_state_key(block: dict) -> str:
    return f"chk_{str(block.get('key', '')).strip()}"


def _cfg_prep_blocks(cfg: dict) -> list:
    prep = cfg.get("prep", []) if isinstance(cfg, dict) else []
    if isinstance(prep, list) and prep:
        return prep
    return [
        {
            "key": "aquecimento",
            "title": "Aquecimento",
            "duration": "4–5 min",
            "items": ["4–5 min leves na bike/elíptica", "2–4 séries de aproximação do 1.º exercício"],
            "button": "✅ Aquecimento feito",
        },
        {
            "key": "mobilidade",
            "title": "Mobilidade / ativação",
            "duration": "2–4 min",
            "items": ["Ativação específica para ombros/anca/escápulas", "Amplitude limpa antes de meter carga"],
            "button": "✅ Mobilidade feita",
        },
    ]


def _cfg_post_blocks(cfg: dict, prot: dict) -> list:
    post = cfg.get("post", []) if isinstance(cfg, dict) else []
    if isinstance(post, list) and post:
        return post
    prot = prot or {}
    blocks = []
    if bool(prot.get("cardio", False)):
        blocks.append({
            "key": "cardio",
            "title": "Cardio Zona 2",
            "duration": "10–15 min",
            "items": ["Bike, elíptica ou caminhada inclinada", "Ritmo em que ainda consegues falar"],
            "button": "✅ Cardio feito",
        })
    if bool(prot.get("tendoes", False)):
        blocks.append({
            "key": "tendoes",
            "title": "Protocolo de tendões",
            "duration": "6–10 min",
            "items": ["Isométricos + excêntricos com controlo", "Sem pressa, sem heroísmos idiotas"],
            "button": "✅ Protocolo feito",
        })
    if bool(prot.get("core", False)):
        blocks.append({
            "key": "core",
            "title": "Core escoliose",
            "duration": "6–10 min",
            "items": ["McGill curl-up, side plank, bird dog, suitcase carry"],
            "button": "✅ Core feito",
        })
    if bool(prot.get("cooldown", True)):
        blocks.append({
            "key": "cooldown",
            "title": "Cool-down",
            "duration": "2–4 min",
            "items": ["Respiração 90/90 + alongamentos leves"],
            "button": "✅ Cool-down feito",
        })
    return blocks


def _build_session_flow(cfg: dict, prot: dict) -> list:
    flow = []
    for block in _cfg_prep_blocks(cfg):
        flow.append({**dict(block), "kind": "block", "phase": "prep"})
    for ix, item in enumerate(list((cfg or {}).get("exercicios", []) or [])):
        flow.append({
            "kind": "exercise",
            "phase": "main",
            "title": _exercise_ui_label(item),
            "series": int(item.get("series", 0) or 0),
            "ex_index": int(ix),
        })
    for block in _cfg_post_blocks(cfg, prot):
        flow.append({**dict(block), "kind": "block", "phase": "finish"})
    return flow


def _session_flow_item_done(item: dict, perfil: str, dia: str) -> bool:
    if str(item.get("kind", "")) == "exercise":
        ix = int(item.get("ex_index", 0) or 0)
        try:
            done_sets = int(st.session_state.get(f"pt_done::{perfil}::{dia}::{ix}", 0) or 0)
        except Exception:
            done_sets = 0
        return done_sets >= int(item.get("series", 0) or 0)
    return bool(st.session_state.get(_session_block_state_key(item), False))


def _exercise_group_label(item: dict) -> str:
    try:
        return str(item.get("superset", "") or item.get("group_label", "") or "").strip()
    except Exception:
        return ""


def _exercise_pair_note(item: dict) -> str:
    group = _exercise_group_label(item)
    try:
        pair_with = str(item.get("pair_with", "") or "").strip()
    except Exception:
        pair_with = ""
    if group and pair_with:
        return f"{group} com {pair_with}"
    return group


def _exercise_ui_label(item: dict, index: int | None = None) -> str:
    try:
        ex = str(item.get("ex", "Exercício") or "Exercício").strip()
    except Exception:
        ex = "Exercício"
    group = _exercise_group_label(item)
    label = f"{ex} · {group}" if group else ex
    if index is None:
        return label
    return f"{int(index)+1}. {label}"


def _superset_group_indices(cfg: dict, group_label: str) -> list[int]:
    group_label = str(group_label or "").strip()
    if not group_label:
        return []
    out = []
    for _ix, _it in enumerate(list((cfg or {}).get("exercicios", []) or [])):
        if _exercise_group_label(_it) == group_label:
            out.append(int(_ix))
    return out


def _effective_ex_done_count(cfg: dict, perfil: str, dia: str, ex_ix: int, overrides: dict | None = None) -> int:
    try:
        if isinstance(overrides, dict) and int(ex_ix) in overrides:
            return int(overrides[int(ex_ix)] or 0)
    except Exception:
        pass
    try:
        pending = st.session_state.get(f"pt_sets::{perfil}::{dia}::{int(ex_ix)}", [])
        pending_n = len(pending) if isinstance(pending, list) else 0
    except Exception:
        pending_n = 0
    try:
        done_n = int(st.session_state.get(f"pt_done::{perfil}::{dia}::{int(ex_ix)}", 0) or 0)
    except Exception:
        done_n = 0
    try:
        total_n = int(((cfg or {}).get("exercicios", []) or [])[int(ex_ix)].get("series", 0) or 0)
    except Exception:
        total_n = 0
    return max(0, min(max(pending_n, done_n), total_n if total_n > 0 else max(pending_n, done_n)))


def _superset_execution_note(cfg: dict, perfil: str, dia: str, ex_ix: int) -> str:
    try:
        item = ((cfg or {}).get("exercicios", []) or [])[int(ex_ix)]
    except Exception:
        return ""
    group = _exercise_group_label(item)
    indices = _superset_group_indices(cfg, group)
    if len(indices) < 2:
        return ""
    names = []
    rounds = []
    for _ix in indices:
        try:
            _it = cfg["exercicios"][_ix]
            names.append(str(_it.get("ex", "Exercício") or "Exercício"))
            rounds.append(int(_it.get("series", 0) or 0))
        except Exception:
            pass
    if not names:
        return ""
    total_rounds = max(rounds) if rounds else 0
    current_round = _effective_ex_done_count(cfg, perfil, dia, int(ex_ix)) + 1
    if total_rounds > 0:
        current_round = max(1, min(int(current_round), int(total_rounds)))
    seq = " → ".join(names) + " → pausa"
    if total_rounds > 0:
        return f"{group}: ronda {current_round}/{total_rounds} · {seq}"
    return f"{group}: {seq}"


def _superset_nav_after_set(cfg: dict, perfil: str, dia: str, ex_ix: int, overrides: dict | None = None) -> dict:
    exercises = list((cfg or {}).get("exercicios", []) or [])
    ex_ix = int(ex_ix)
    item = exercises[ex_ix] if 0 <= ex_ix < len(exercises) else {}
    group = _exercise_group_label(item)
    indices = _superset_group_indices(cfg, group)
    if len(indices) < 2:
        total = int(item.get("series", 0) or 0)
        done = _effective_ex_done_count(cfg, perfil, dia, ex_ix, overrides)
        ex_complete = done >= total if total > 0 else False
        return {
            "is_superset": False,
            "queue_rest": not ex_complete,
            "next_ix": (min(len(exercises) - 1, ex_ix + 1) if ex_complete and ex_ix < len(exercises) - 1 else ex_ix),
            "group_complete": ex_complete,
            "current_complete": ex_complete,
        }

    counts = {ix: _effective_ex_done_count(cfg, perfil, dia, ix, overrides) for ix in indices}
    totals = {ix: int(exercises[ix].get("series", 0) or 0) for ix in indices}
    current_complete = counts.get(ex_ix, 0) >= totals.get(ex_ix, 0)
    group_complete = all(counts.get(ix, 0) >= totals.get(ix, 0) for ix in indices)
    pos = indices.index(ex_ix)

    next_ix = ex_ix
    if not group_complete:
        for step in range(1, len(indices) + 1):
            cand = indices[(pos + step) % len(indices)]
            if counts.get(cand, 0) < totals.get(cand, 0):
                next_ix = cand
                break
    else:
        next_ix = max(indices)
        if next_ix < len(exercises) - 1:
            next_ix += 1

    queue_rest = (not group_complete) and (pos == len(indices) - 1)
    return {
        "is_superset": True,
        "queue_rest": bool(queue_rest),
        "next_ix": int(next_ix),
        "group_complete": bool(group_complete),
        "current_complete": bool(current_complete),
        "group_indices": list(indices),
        "position": int(pos),
        "order_names": [str(exercises[ix].get("ex", "Exercício") or "Exercício") for ix in indices],
    }


def _session_flow_stats(cfg: dict, prot: dict, perfil: str, dia: str):
    flow = _build_session_flow(cfg, prot)
    total = len(flow)
    done = 0
    pending_ix = None
    for ix, item in enumerate(flow):
        ok = _session_flow_item_done(item, perfil, dia)
        if ok:
            done += 1
        elif pending_ix is None:
            pending_ix = ix
    return flow, done, total, pending_ix


def _persist_current_block_progress_snapshot():
    """Guarda imediatamente o estado dos blocos da sessão em curso.

    Isto evita que o auto-restore mobile volte a meter Aquecimento/Mobilidade a falso
    no rerun seguinte quando ainda não há séries registadas.
    """
    try:
        perfil = str(st.session_state.get("perfil_sel", "") or "")
        plano_id = str(st.session_state.get("plano_id_sel", "Base") or "Base")
        dia = str(st.session_state.get("dia_sel", "") or "")
        try:
            semana = int(st.session_state.get("semana_sel", 1) or 1)
        except Exception:
            semana = 1
        if not perfil or not dia:
            return

        pure_nav_key = f"pt_idx::{perfil}::{plano_id}::{dia}::{semana}"
        curr_cfg = globals().get("cfg", {})
        try:
            n_ex = int(len((curr_cfg or {}).get("exercicios", []) or []))
        except Exception:
            n_ex = 0

        skey, payload = get_active_inprogress_session(perfil, plano_id, INPROGRESS_MAX_AGE_HOURS)
        if isinstance(payload, dict) and isinstance(skey, str):
            checks = payload.get("checks", {}) if isinstance(payload.get("checks", {}), dict) else {}
            checks.update({
                str(k): bool(v)
                for k, v in st.session_state.items()
                if str(k).startswith("chk_")
            })
            payload["checks"] = checks
            payload["ts"] = time.time()
            save_inprogress_session(skey, payload)
            return

        payload = _build_inprogress_payload(perfil, dia, plano_id, int(semana), pure_nav_key, int(n_ex))
        new_key = _make_inprogress_key(perfil, plano_id, dia, int(semana), payload.get("date", _inprogress_today_key_date()))
        save_inprogress_session(new_key, payload)
    except Exception:
        pass


def _render_session_block(block: dict):
    title = str(block.get("title", "Bloco") or "Bloco")
    duration = str(block.get("duration", "") or "").strip()
    items = [str(x).strip() for x in list(block.get("items", []) or []) if str(x).strip()]
    note = str(block.get("note", "") or "").strip()
    state_key = _session_block_state_key(block)
    is_done = bool(st.session_state.get(state_key, False))
    button_label = str(block.get("button", "✅ Marcar como feito") or "✅ Marcar como feito")
    icon = str(block.get("icon", "") or "").strip()

    st.markdown(
        f"""
        <div class='bc-prep-card'>
          <div class='t'>{html.escape((icon + ' ') if icon else '')}{html.escape(title)}</div>
          <div class='s'>{html.escape(duration) if duration else 'Bloco rápido da sessão.'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for entry in items:
        st.markdown(f"- {entry}")
    if note:
        st.caption(note)
    c1, c2 = st.columns([2, 1])
    if is_done:
        c1.success("Concluído ✅")
        if c2.button("↩️ Reabrir", key=f"undo::{state_key}", width='stretch'):
            st.session_state[state_key] = False
            _persist_current_block_progress_snapshot()
            st.rerun()
    else:
        if c1.button(button_label, key=f"done::{state_key}", width='stretch'):
            st.session_state[state_key] = True
            _persist_current_block_progress_snapshot()
            st.rerun()
        c2.caption("Obrigatório" if str(block.get("phase", "")) != "optional" else "Opcional")

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
    return False

GUI_PPLA_ID = "GUI_PPLA_v1"
GUI_BLOCOS = {"PUSH", "PULL", "LEGS", "ARMS"}

BRUNO_OPCAO_1_ID = "BRUNO_4D_RECUP_v1"
BRUNO_OPCAO_2_ID = "BRUNO_4D_SEG_TER_QUA_SEX_v1"
BRUNO_IDS = {BRUNO_OPCAO_1_ID, BRUNO_OPCAO_2_ID}
BRUNO_BLOCOS = {"BRUNO_UPPER", "BRUNO_LOWER"}


def gui_stage_week(week: int) -> int:
    """Mapeia semanas 1-12 para estágio do mesociclo (1-5, 6=deload)."""
    try:
        w = int(week)
    except Exception:
        w = 1
    if w <= 6:
        return w
    if 7 <= w <= 11:
        return w - 6
    return 6

def is_gui_deload_week(week: int) -> bool:
    return int(week) in (6, 12)

def semana_label_gui(week: int) -> str:
    w = int(week)
    stage = gui_stage_week(w)
    if stage == 6:
        return f"Semana {w} — DELOAD"
    if w <= 5:
        return f"Semana {w} — Mesociclo {stage}"
    return f"Semana {w} — Repetição M{stage}"

def semana_label_bruno(week: int) -> str:
    try:
        w = int(week)
    except Exception:
        w = 1
    if w in (1, 2):
        return f"Semana {w} — Teste técnico"
    if w in (3, 4, 5):
        return f"Semana {w} — Progressão"
    return "Semana 6 — DELOAD"


def semana_label_por_plano(week: int, plano_id: str) -> str:
    if plano_id == GUI_PPLA_ID:
        return semana_label_gui(week)
    if plano_id in BRUNO_IDS:
        return semana_label_bruno(week)
    return semana_label(week)


def is_bruno_deload_week(week: int) -> bool:
    try:
        return int(week) == 6
    except Exception:
        return False


def is_deload_for_plan(week: int, plano_id: str) -> bool:
    if plano_id == GUI_PPLA_ID:
        return is_gui_deload_week(week)
    if plano_id in BRUNO_IDS:
        return is_bruno_deload_week(week)
    return is_deload(week)


def rir_alvo(item_tipo, bloco, week):
    if bloco in GUI_BLOCOS:
        return "2–4" if is_gui_deload_week(week) else "2"
    if bloco in BRUNO_BLOCOS:
        if is_bruno_deload_week(week):
            return "3–4"
        try:
            w = int(week)
        except Exception:
            w = 1
        tipo = str(item_tipo or "").lower()
        if w in (1, 2):
            return "2–3" if tipo == "composto" else "1–2"
        return "1–2" if tipo == "composto" else "1"
    if bloco == "ABC":
        return "2"
    if bloco == "Força":
        return "3–4" if is_deload(week) else "2–3"
    if bloco == "Hipertrofia":
        return "3–4" if is_deload(week) else "1–2"
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
    if bloco in GUI_BLOCOS:
        return 75
    if bloco in BRUNO_BLOCOS:
        return 120 if item_tipo == "composto" else 75
    if bloco == "ABC":
        return 75
    if item_tipo == "composto":
        return 120
    return 60


treinos_base = {
    "Segunda — UPPER HIPERTROFIA A": {
        "bloco": "Hipertrofia",
        "sessao": "80–100 min",
        "protocolos": {"tendoes": True, "core": False, "cardio": True, "cooldown": False},
        "prep": [
            {
                "key": "aquecimento",
                "title": "Aquecimento",
                "icon": "🔥",
                "duration": "4 min + mobilidade + 2–3 séries de aproximação",
                "items": [
                    "Elíptica ou bike: 4 min",
                    "Dead hang: 1 x 20–30 s",
                    "Rotação torácica: 1 x 8/lado",
                    "Band pull-aparts: 1 x 15",
                    "Rotação externa leve: 1 x 12–15",
                    "Séries de aproximação do 1.º exercício: 2–3",
                ],
                "button": "✅ Aquecimento feito",
            },
        ],
        "post": [
            {
                "key": "tendoes",
                "title": "Protocolo",
                "icon": "🦾",
                "duration": "Superset protocolo + final",
                "items": [
                    "Superset protocolo:",
                    "Pressdown isométrico: 2 x 30–45 s",
                    "Rotação externa isométrica: 2 x 30 s/lado",
                    "Depois:",
                    "Wrist extension excêntrico: 2 x 12",
                ],
                "button": "✅ Protocolo feito",
            },
            {
                "key": "cardio",
                "title": "Cardio",
                "icon": "🏃",
                "duration": "12–15 min",
                "items": [
                    "Cardio: 12–15 min",
                ],
                "button": "✅ Cardio feito",
            },
        ],
        "exercicios": [
            {"ex":"Remada apoiada no peito", "series":3, "reps":"8-10", "tipo":"composto"},
            {"ex":"Puxada na polia neutra", "series":3, "reps":"10-12", "tipo":"composto"},
            {"ex":"Pulldown unilateral para dorsal", "series":2, "reps":"12-15", "tipo":"isolado"},
            {"ex":"Máquina inclinada convergente", "series":2, "reps":"8-12", "tipo":"composto"},
            {"ex":"Elevação lateral na polia", "series":3, "reps":"12-20", "tipo":"isolado", "superset":"Superset A", "pair_with":"Reverse pec deck"},
            {"ex":"Reverse pec deck", "series":3, "reps":"15-20", "tipo":"isolado", "superset":"Superset A", "pair_with":"Elevação lateral na polia"},
        ]
    },
    "Terça — LOWER HIPERTROFIA": {
        "bloco": "Hipertrofia",
        "sessao": "90–110 min",
        "protocolos": {"tendoes": False, "core": True, "cardio": False, "cooldown": False},
        "prep": [
            {
                "key": "aquecimento",
                "title": "Aquecimento",
                "icon": "🔥",
                "duration": "5 min + ativação + 2–4 séries de aproximação",
                "items": [
                    "Bike: 5 min",
                    "Spanish squat: 2 x 30–45 s",
                    "Glute bridge com pausa: 2 x 10",
                    "Hip hinge drill: 1 x 8",
                    "Séries de aproximação do 1.º exercício: 2–4",
                ],
                "button": "✅ Aquecimento feito",
            },
        ],
        "post": [
            {
                "key": "core",
                "title": "Core em circuito",
                "icon": "🧱",
                "duration": "3 exercícios + final",
                "items": [
                    "McGill curl-up: 2 x 8",
                    "Side plank: 2 x 30–45 s",
                    "Bird dog: 2 x 6/lado",
                    "No fim:",
                    "Suitcase carry: 2 x 20–30 m/lado",
                ],
                "button": "✅ Core feito",
            },
        ],
        "exercicios": [
            {"ex":"Hack squat ou belt squat", "series":3, "reps":"6-10", "tipo":"composto"},
            {"ex":"Hip thrust barra", "series":4, "reps":"8-10", "tipo":"composto"},
            {"ex":"RDL", "series":3, "reps":"8-10", "tipo":"composto"},
            {"ex":"Leg extension", "series":2, "reps":"12-15", "tipo":"isolado", "superset":"Superset A", "pair_with":"Abdução máquina"},
            {"ex":"Abdução máquina", "series":2, "reps":"15-25", "tipo":"isolado", "superset":"Superset A", "pair_with":"Leg extension"},
            {"ex":"Split squat smith viés quad", "series":2, "reps":"10-12/perna", "tipo":"composto", "superset":"Superset B", "pair_with":"Tibial raise"},
            {"ex":"Tibial raise", "series":2, "reps":"15-20", "tipo":"isolado", "superset":"Superset B", "pair_with":"Split squat smith viés quad"},
        ]
    },
    "Quarta — UPPER HIPERTROFIA B": {
        "bloco": "Hipertrofia",
        "sessao": "85–105 min",
        "protocolos": {"tendoes": True, "core": False, "cardio": True, "cooldown": False},
        "prep": [
            {
                "key": "aquecimento",
                "title": "Aquecimento",
                "icon": "🔥",
                "duration": "4 min + ativação + 2–3 séries de aproximação",
                "items": [
                    "Elíptica ou caminhada: 4 min",
                    "Scap push-up: 1 x 10",
                    "Face pull leve: 1 x 15",
                    "Rotação externa leve: 1 x 12–15",
                    "Séries de aproximação do 1.º exercício: 2–3",
                ],
                "button": "✅ Aquecimento feito",
            },
        ],
        "post": [
            {
                "key": "tendoes",
                "title": "Protocolo",
                "icon": "🦾",
                "duration": "Superset protocolo + final",
                "items": [
                    "Superset protocolo:",
                    "Pressdown isométrico: 2 x 30–45 s",
                    "Rotação externa isométrica: 2 x 30 s/lado",
                    "Depois:",
                    "Wrist extension excêntrico: 2 x 12",
                ],
                "button": "✅ Protocolo feito",
            },
            {
                "key": "cardio",
                "title": "Cardio",
                "icon": "🏃",
                "duration": "10–12 min",
                "items": [
                    "Cardio: 10–12 min",
                ],
                "button": "✅ Cardio feito",
            },
        ],
        "exercicios": [
            {"ex":"Supino inclinado com halteres", "series":4, "reps":"6-10", "tipo":"composto"},
            {"ex":"Smith inclinada baixa", "series":3, "reps":"8-10", "tipo":"composto"},
            {"ex":"Crossover baixo para alto", "series":3, "reps":"12-15", "tipo":"isolado"},
            {"ex":"Shoulder press máquina neutra", "series":2, "reps":"8-10", "tipo":"composto"},
            {"ex":"Elevação lateral", "series":3, "reps":"12-20", "tipo":"isolado", "superset":"Superset A", "pair_with":"Rear delt no cabo ou máquina"},
            {"ex":"Rear delt no cabo ou máquina", "series":3, "reps":"15-20", "tipo":"isolado", "superset":"Superset A", "pair_with":"Elevação lateral"},
            {"ex":"Rosca cabo", "series":2, "reps":"10-12", "tipo":"isolado", "superset":"Superset B", "pair_with":"Pressdown corda"},
            {"ex":"Pressdown corda", "series":2, "reps":"12-15", "tipo":"isolado", "superset":"Superset B", "pair_with":"Rosca cabo"},
        ]
    },
    "Quinta — LIVRE": {
        "bloco": "Fisio",
        "sessao": "12–18 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": False, "cooldown": False},
        "recovery_title": "Core / mobilidade",
        "recovery_items": [
            "Respiração 90/90: 2 min",
            "Side plank: 2 x 30–45 s",
            "Bird dog: 2 x 6/lado",
            "Dead hang: 2 x 20–30 s",
            "Alongamento peitoral na porta: 1 x 45 s/lado",
            "Alongamento flexor da anca: 1 x 45 s/lado",
        ],
        "recovery_note": "Dia livre.",
        "exercicios": []
    },
    "Sexta — UPPER FORÇA": {
        "bloco": "Força",
        "sessao": "75–95 min",
        "protocolos": {"tendoes": True, "core": False, "cardio": True, "cooldown": False},
        "prep": [
            {
                "key": "aquecimento",
                "title": "Aquecimento",
                "icon": "🔥",
                "duration": "4 min + ativação + 3–5 séries de aproximação",
                "items": [
                    "Bike ou elíptica: 4 min",
                    "Dead hang: 1 x 20–30 s",
                    "Band pull-aparts: 1 x 15",
                    "Rotação externa leve: 1 x 12–15",
                    "Séries de aproximação do supino: 3–5",
                ],
                "button": "✅ Aquecimento feito",
            },
        ],
        "post": [
            {
                "key": "tendoes",
                "title": "Depois",
                "icon": "🦾",
                "duration": "2 linhas",
                "items": [
                    "Pressdown isométrico: 2 x 30–45 s",
                    "Wrist extension excêntrico: 2 x 12",
                ],
                "button": "✅ Protocolo feito",
            },
            {
                "key": "cardio",
                "title": "Cardio",
                "icon": "🏃",
                "duration": "10–12 min",
                "items": [
                    "Cardio: 10–12 min",
                ],
                "button": "✅ Cardio feito",
            },
        ],
        "exercicios": [
            {"ex":"Supino inclinado baixo com pausa", "series":4, "reps":"4-6", "tipo":"composto"},
            {"ex":"Puxada na polia neutra pesada", "series":4, "reps":"6-8", "tipo":"composto"},
            {"ex":"Remada apoiada pesada", "series":3, "reps":"5-6", "tipo":"composto"},
            {"ex":"Máquina inclinada convergente", "series":3, "reps":"6-8", "tipo":"composto"},
            {"ex":"Face pull", "series":2, "reps":"15-20", "tipo":"isolado", "superset":"Superset leve final", "pair_with":"Rotação externa isométrica"},
            {"ex":"Rotação externa isométrica", "series":2, "reps":"30 s/lado", "tipo":"isolado", "superset":"Superset leve final", "pair_with":"Face pull"},
        ]
    },
    "Sábado — LOWER FORÇA": {
        "bloco": "Força",
        "sessao": "85–105 min",
        "protocolos": {"tendoes": False, "core": True, "cardio": False, "cooldown": False},
        "prep": [
            {
                "key": "aquecimento",
                "title": "Aquecimento",
                "icon": "🔥",
                "duration": "5 min + ativação + 3–5 séries de aproximação",
                "items": [
                    "Bike: 5 min",
                    "Spanish squat: 2 x 30–45 s",
                    "Glute bridge com pausa: 2 x 10",
                    "Hip hinge drill: 1 x 8",
                    "Séries de aproximação do 1.º exercício: 3–5",
                ],
                "button": "✅ Aquecimento feito",
            },
        ],
        "post": [
            {
                "key": "core",
                "title": "Core em circuito",
                "icon": "🧱",
                "duration": "3 exercícios",
                "items": [
                    "McGill curl-up: 2 x 8",
                    "Side plank: 2 x 30–45 s",
                    "Bird dog: 2 x 6/lado",
                ],
                "button": "✅ Core feito",
            },
            {
                "key": "final_lower",
                "title": "Depois",
                "icon": "🏁",
                "duration": "3 linhas",
                "items": [
                    "Suitcase carry: 2 x 20–30 m/lado",
                    "Spanish squat: 2 x 30–45 s",
                    "Tibial raise: 2 x 15–20",
                ],
                "button": "✅ Final feito",
            },
        ],
        "exercicios": [
            {"ex":"Trap bar deadlift", "series":4, "reps":"3-5", "tipo":"composto"},
            {"ex":"Belt squat ou hack squat pesado", "series":4, "reps":"5-6", "tipo":"composto"},
            {"ex":"Hip thrust pesado", "series":3, "reps":"5-6", "tipo":"composto"},
            {"ex":"Leg curl sentado ou lying curl", "series":3, "reps":"6-8", "tipo":"isolado", "superset":"Superset A", "pair_with":"Panturrilha"},
            {"ex":"Panturrilha", "series":3, "reps":"6-10", "tipo":"isolado", "superset":"Superset A", "pair_with":"Leg curl sentado ou lying curl"},
        ]
    },
    "Domingo — DESCANSO": {
        "bloco": "Fisio",
        "sessao": "Descanso",
        "protocolos": {"tendoes": False, "core": False, "cardio": False, "cooldown": False},
        "recovery_title": "Descanso",
        "recovery_items": [
            "Descanso total.",
        ],
        "recovery_note": "Sem treino hoje.",
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

# --- PLANO GUI (PUSH / PULL / LEGS / ARMS com mesociclos 1-5 + deload) ---
# Nota: usamos reps em texto (ex.: 15/12/10/8, 10 + M + M, drop) para respeitar a sheet original.
# A progressão de cargas é manual na app (peso/reps/RIR), e o deload reduz volume automaticamente.
treinos_gui = {
    "Segunda — PUSH": {
        "bloco": "PUSH",
        "sessao": "75–95 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": False, "cooldown": True},
        "exercicios": [
            {"ex":"Rotadores (aquecimento)", "series":3, "reps":"15", "tipo":"isolado"},
            {"ex":"Supino Inclinado (halteres)", "series":4, "reps":"15/12/10/8", "tipo":"composto"},
            {"ex":"Press Ombro (halteres)", "series":4, "reps":"15/12/10/8", "tipo":"composto"},
            {"ex":"Crossover (3s contração)", "series":4, "reps":"5/4/3/2/1*", "tipo":"isolado"},
            {"ex":"Supino (máquina)", "series":2, "reps":"15", "tipo":"composto"},
            {"ex":"Rope Pushdown", "series":2, "reps":"20", "tipo":"isolado"},
            {"ex":"Barra à testa (barra W)", "series":4, "reps":"15/12/10/8", "tipo":"isolado"},
            {"ex":"Prancha (segundos)", "series":4, "reps":"60", "tipo":"isolado"},
            {"ex":"Anjos e demónios", "series":3, "reps":"12", "tipo":"isolado"},
        ]
    },
    "Terça — PULL": {
        "bloco": "PULL",
        "sessao": "75–95 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": False, "cooldown": True},
        "exercicios": [
            {"ex":"Rotadores (aquecimento)", "series":3, "reps":"15", "tipo":"isolado"},
            {"ex":"Puxada (5s entre mini-sets)", "series":3, "reps":"10 + M + M", "tipo":"composto"},
            {"ex":"Remada curvada (barra)", "series":4, "reps":"15/12/10/8", "tipo":"composto"},
            {"ex":"Puxada neutra", "series":4, "reps":"15/12/10/8", "tipo":"composto"},
            {"ex":"Pullover (corda)", "series":3, "reps":"15", "tipo":"isolado"},
            {"ex":"Facepull", "series":3, "reps":"15", "tipo":"isolado"},
            {"ex":"Scott", "series":2, "reps":"20", "tipo":"isolado"},
            {"ex":"Curl martelo (alternado)", "series":4, "reps":"15/12/10/8", "tipo":"isolado"},
            {"ex":"Lombares", "series":3, "reps":"12", "tipo":"isolado"},
        ]
    },
    "Quarta — DESCANSO (mobilidade leve)": {
        "bloco": "Fisio",
        "sessao": "15–30 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": True, "cooldown": False},
        "exercicios": []
    },
    "Quinta — LEGS": {
        "bloco": "LEGS",
        "sessao": "80–110 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": False, "cooldown": True},
        "exercicios": [
            {"ex":"Extensora (aquecimento)", "series":3, "reps":"20", "tipo":"isolado"},
            {"ex":"Lunge (alternado/sem peso)", "series":2, "reps":"60", "tipo":"composto"},
            {"ex":"Prensa", "series":4, "reps":"15/12/10/8", "tipo":"composto"},
            {"ex":"Elevação pélvica", "series":4, "reps":"15/12/10/8", "tipo":"composto"},
            {"ex":"Flexora", "series":4, "reps":"5/4/3/2/1*", "tipo":"isolado"},
            {"ex":"Extensora", "series":4, "reps":"5/4/3/2/1*", "tipo":"isolado"},
            {"ex":"Gémeo (multipower/máquina)", "series":4, "reps":"20/15/12/10", "tipo":"isolado"},
            {"ex":"Leg raise", "series":3, "reps":"20", "tipo":"isolado"},
            {"ex":"Russian twist", "series":3, "reps":"20", "tipo":"isolado"},
        ]
    },
    "Sexta — ARMS": {
        "bloco": "ARMS",
        "sessao": "70–95 min",
        "protocolos": {"tendoes": False, "core": False, "cardio": False, "cooldown": True},
        "exercicios": [
            {"ex":"Elevação LFL (10+10+10)", "series":3, "reps":"10+10+10", "tipo":"isolado"},
            {"ex":"Elevação frontal (simultâneo)", "series":4, "reps":"15/12/10/8", "tipo":"isolado"},
            {"ex":"Elevação lateral", "series":3, "reps":"10", "tipo":"isolado"},
            {"ex":"Pushdown (barra)", "series":4, "reps":"15/12/10/8", "tipo":"isolado"},
            {"ex":"Tríceps francês", "series":3, "reps":"15", "tipo":"isolado"},
            {"ex":"Bíceps curl banco 45 (simultâneo)", "series":3, "reps":"15", "tipo":"isolado"},
            {"ex":"Curl W (barra W)", "series":4, "reps":"15/12/10/8", "tipo":"isolado"},
            {"ex":"Lombares", "series":3, "reps":"12", "tipo":"isolado"},
            {"ex":"Anjos e demónios", "series":3, "reps":"12", "tipo":"isolado"},
        ]
    },
    "Sábado — DESCANSO (caminhada leve)": {
        "bloco": "Fisio",
        "sessao": "opcional",
        "protocolos": {"tendoes": False, "core": False, "cardio": True, "cooldown": False},
        "exercicios": []
    },
    "Domingo — DESCANSO (caminhada leve)": {
        "bloco": "Fisio",
        "sessao": "opcional",
        "protocolos": {"tendoes": False, "core": False, "cardio": True, "cooldown": False},
        "exercicios": []
    },
}

def _apply_gui_week_overrides(cfg: dict, week: int):
    """Aplica as mudanças dos mesociclos (Sem 1-5) e repetição (Sem 7-11)."""
    stage = gui_stage_week(week)
    bloco = str(cfg.get("bloco",""))
    out = []
    for item in cfg.get("exercicios", []):
        it = dict(item)
        exn = str(it.get("ex",""))

        if bloco == "PUSH":
            if exn.startswith("Supino (máquina)"):
                if stage == 1: it.update(series=2, reps="15")
                elif stage == 2: it.update(series=3, reps="15")
                elif stage in (3,4): it.update(series=4, reps="15/12/10/8")
                elif stage == 5: it.update(series=4, reps="15/12/10/8 + drop")
            elif exn.startswith("Rope Pushdown"):
                if stage in (1,2): it.update(series=2, reps="20")
                elif stage == 3: it.update(series=3, reps="15")
                elif stage == 4: it.update(series=4, reps="15")
                elif stage == 5: it.update(series=4, reps="15")

        elif bloco == "PULL":
            if exn.startswith("Puxada (5s entre mini-sets)"):
                if stage in (1,2): it.update(series=3, reps="10 + M + M")
                elif stage >= 3: it.update(series=4, reps="8 + M + M")
            elif exn == "Scott":
                if stage == 1: it.update(series=2, reps="20")
                elif stage == 2: it.update(series=3, reps="15")
                elif stage >= 3: it.update(series=4, reps="15/12/10/8")
            elif exn.startswith("Pullover (corda)") and stage == 5:
                it.update(series=4, reps="15")
            elif exn == "Facepull" and stage == 5:
                it.update(series=4, reps="15")
            elif exn == "Lombares" and stage >= 4:
                it.update(series=4, reps="12")

        elif bloco == "LEGS":
            if exn.startswith("Lunge"):
                if stage in (1,2): it.update(series=2, reps="60")
                elif stage in (3,4): it.update(series=3, reps="60")
                elif stage == 5: it.update(series=4, reps="40")
            elif exn == "Leg raise":
                if stage >= 4: it.update(series=4, reps="20")

        elif bloco == "ARMS":
            if exn == "Elevação lateral":
                if stage == 1: it.update(series=3, reps="10")
                elif stage >= 2: it.update(series=4, reps="10")
            elif exn == "Tríceps francês":
                if stage in (1,2): it.update(series=3, reps="15")
                elif stage >= 3: it.update(series=4, reps="15/12/10/8")
            elif exn.startswith("Bíceps curl banco 45") and stage >= 4:
                it.update(series=4, reps="12")
            elif exn == "Lombares" and stage >= 5:
                it.update(series=4, reps="12")

        out.append(it)

    # Deload (Sem 6 / 12) — reduz volume e remove intensificadores no texto
    if is_gui_deload_week(week) and bloco in GUI_BLOCOS:
        deload = []
        for it in out:
            x = dict(it)
            base_s = int(x.get("series", 1) or 1)
            x["series"] = max(1, int(round(base_s * 0.55)))
            reps_txt = str(x.get("reps", ""))
            reps_txt = reps_txt.replace(" + drop", "")
            if "M + M" in reps_txt:
                reps_txt = reps_txt.split("+")[0].strip()
            x["reps"] = reps_txt
            x["nota_semana"] = "DELOAD: baixa a carga 10–15%, sem falha, técnica limpa (RIR 2–4)."
            deload.append(x)
        out = deload
    else:
        if week >= 7 and bloco in GUI_BLOCOS:
            for it in out:
                it["nota_semana"] = "Repetição do mesociclo: tenta +2,5 kg ou +1–2 reps mantendo técnica."
                break

    return out

def gerar_treino_gui_dia(dia, week):
    cfg = treinos_gui.get(dia, None)
    if not cfg:
        return {"bloco":"—","sessao":"","protocolos":{}, "exercicios":[]}
    bloco = cfg["bloco"]
    treino_final = []
    for item in _apply_gui_week_overrides(cfg, week):
        novo = dict(item)
        novo["rir_alvo"] = rir_alvo(item.get("tipo","isolado"), bloco, week)
        novo["tempo"] = tempo_exec(item.get("tipo","isolado"))
        novo["descanso_s"] = descanso_recomendado_s(item.get("tipo","isolado"), bloco)
        treino_final.append(novo)
    return {"bloco": bloco, "sessao": cfg["sessao"], "protocolos": cfg["protocolos"], "exercicios": treino_final}


# --- Plano Bruno — duas opções 4 dias ---
# Opção 1: seg/ter/sex/sáb (mais recuperável)
# Opção 2: seg/ter/qua/sex (a semana que pediste)
BRUNO_UPPER_A = {
    "bloco": "BRUNO_UPPER",
    "sessao": "60–75 min",
    "protocolos": {"tendoes": True, "core": False, "cardio": True, "cooldown": False},
    "prep": [
        {
            "key": "aquecimento",
            "title": "Aquecimento Upper A",
            "icon": "🔥",
            "duration": "5 min + ombro/escápula + aproximações",
            "items": [
                "Bike ou elíptica: 5 min",
                "Face pull leve: 1 x 15",
                "Rotação externa cabo/banda: 1 x 12–15",
                "2–3 séries de aproximação no primeiro exercício",
            ],
            "button": "✅ Aquecimento feito",
        },
    ],
    "post": [
        {
            "key": "cardio",
            "title": "Cardio zona 2",
            "icon": "🏃",
            "duration": "12–15 min",
            "items": [
                "Bike ou elíptica: 12–15 min em zona 2",
                "Ritmo em que ainda consegues falar frases curtas",
            ],
            "button": "✅ Cardio feito",
        },
        {
            "key": "tendoes",
            "title": "Prehab ombro/cotovelo/pulso",
            "icon": "🦾",
            "duration": "4–6 min",
            "items": [
                "Wrist extension excêntrico: 2 x 12",
                "Rotação externa isométrica: 2 x 30 s/lado",
            ],
            "button": "✅ Prehab feito",
        },
    ],
    "exercicios": [
        {"ex": "Remada apoiada no peito", "series": 3, "reps": "8-10", "tipo": "composto", "descanso_s": 150},
        {"ex": "Puxada neutra na polia", "series": 3, "reps": "8-12", "tipo": "composto", "descanso_s": 120},
        {"ex": "Máquina inclinada convergente", "series": 3, "reps": "8-12", "tipo": "composto", "descanso_s": 120},
        {"ex": "Crossover baixo para alto", "series": 2, "reps": "12-15", "tipo": "isolado", "descanso_s": 75},
        {"ex": "Elevação lateral na polia", "series": 3, "reps": "12-20", "tipo": "isolado", "descanso_s": 75, "superset": "Superset deltoides", "pair_with": "Rear delt no cabo/máquina"},
        {"ex": "Rear delt no cabo/máquina", "series": 2, "reps": "15-20", "tipo": "isolado", "descanso_s": 75, "superset": "Superset deltoides", "pair_with": "Elevação lateral na polia"},
        {"ex": "Rosca cabo punho neutro/semi-supinado", "series": 2, "reps": "10-15", "tipo": "isolado", "descanso_s": 75, "superset": "Superset braços", "pair_with": "Pressdown corda"},
        {"ex": "Pressdown corda", "series": 2, "reps": "12-15", "tipo": "isolado", "descanso_s": 75, "superset": "Superset braços", "pair_with": "Rosca cabo punho neutro/semi-supinado"},
    ],
}

BRUNO_LOWER_A = {
    "bloco": "BRUNO_LOWER",
    "sessao": "60–75 min",
    "protocolos": {"tendoes": False, "core": True, "cardio": False, "cooldown": False},
    "prep": [
        {
            "key": "aquecimento",
            "title": "Aquecimento Lower A",
            "icon": "🔥",
            "duration": "5–8 min + joelho/glúteo + aproximações",
            "items": [
                "Bike: 5 min",
                "Spanish squat: 2 x 30–45 s",
                "Glute bridge com pausa: 1–2 x 10",
                "2–3 séries de aproximação no hack squat",
            ],
            "button": "✅ Aquecimento feito",
        },
    ],
    "post": [
        {
            "key": "core",
            "title": "Core curto",
            "icon": "🧱",
            "duration": "5–8 min",
            "items": [
                "McGill curl-up: 2 x 8/lado",
                "Dead bug: 2 x 8/lado",
                "Sem twists, sem side bends pesados.",
            ],
            "button": "✅ Core feito",
        },
    ],
    "exercicios": [
        {"ex": "Hack squat", "series": 3, "reps": "6-10", "tipo": "composto", "descanso_s": 150},
        {"ex": "Leg press pés médios/baixos", "series": 2, "reps": "10-12", "tipo": "composto", "descanso_s": 120},
        {"ex": "Hip thrust barra/máquina", "series": 3, "reps": "8-12", "tipo": "composto", "descanso_s": 120},
        {"ex": "Leg extension", "series": 2, "reps": "12-15", "tipo": "isolado", "descanso_s": 75},
        {"ex": "Leg curl sentado", "series": 2, "reps": "10-12", "tipo": "isolado", "descanso_s": 75},
        {"ex": "Gémeos máquina", "series": 3, "reps": "8-12", "tipo": "isolado", "descanso_s": 75},
        {"ex": "Tibial raise", "series": 2, "reps": "15-20", "tipo": "isolado", "descanso_s": 60},
    ],
}

BRUNO_UPPER_B = {
    "bloco": "BRUNO_UPPER",
    "sessao": "60–75 min",
    "protocolos": {"tendoes": False, "core": False, "cardio": True, "cooldown": False},
    "prep": [
        {
            "key": "aquecimento",
            "title": "Aquecimento Upper B",
            "icon": "🔥",
            "duration": "5 min + mobilidade torácica/ombro + aproximações",
            "items": [
                "Bike ou elíptica: 4–5 min",
                "Mobilidade torácica rápida",
                "Face pull leve: 1 x 15",
                "Rotação externa leve: 1 x 12–15",
                "2–3 séries de aproximação no supino inclinado",
            ],
            "button": "✅ Aquecimento feito",
        },
    ],
    "post": [
        {
            "key": "cardio",
            "title": "Cardio zona 2 curto",
            "icon": "🏃",
            "duration": "8–12 min",
            "items": [
                "Bike ou elíptica: 8–12 min em zona 2",
                "Se a asma chatear, reduz intensidade.",
            ],
            "button": "✅ Cardio feito",
        },
    ],
    "exercicios": [
        {"ex": "Supino inclinado halteres 20–30°", "series": 3, "reps": "6-10", "tipo": "composto", "descanso_s": 150},
        {"ex": "Smith inclinada baixa com pausa", "series": 2, "reps": "8-10", "tipo": "composto", "descanso_s": 150},
        {"ex": "Remada baixa com apoio", "series": 3, "reps": "8-10", "tipo": "composto", "descanso_s": 120},
        {"ex": "Pulldown unilateral para dorsal", "series": 2, "reps": "12-15", "tipo": "isolado", "descanso_s": 75},
        {"ex": "Shoulder press máquina neutra", "series": 2, "reps": "8-10", "tipo": "composto", "descanso_s": 120},
        {"ex": "Elevação lateral cabo/halter", "series": 3, "reps": "12-20", "tipo": "isolado", "descanso_s": 75, "superset": "Superset deltoides", "pair_with": "Rear delt cabo/máquina"},
        {"ex": "Rear delt cabo/máquina", "series": 2, "reps": "15-20", "tipo": "isolado", "descanso_s": 75, "superset": "Superset deltoides", "pair_with": "Elevação lateral cabo/halter"},
        {"ex": "Rosca inclinada cabo/halter", "series": 2, "reps": "10-15", "tipo": "isolado", "descanso_s": 75, "superset": "Superset braços", "pair_with": "Tríceps corda/barra V"},
        {"ex": "Tríceps corda/barra V", "series": 2, "reps": "10-15", "tipo": "isolado", "descanso_s": 75, "superset": "Superset braços", "pair_with": "Rosca inclinada cabo/halter"},
    ],
}

BRUNO_LOWER_B_RECUP = {
    "bloco": "BRUNO_LOWER",
    "sessao": "75–90 min",
    "protocolos": {"tendoes": False, "core": True, "cardio": False, "cooldown": False},
    "prep": [
        {
            "key": "aquecimento",
            "title": "Aquecimento Lower B",
            "icon": "🔥",
            "duration": "8–10 min + hinge/joelho + aproximações",
            "items": [
                "Bike: 5 min",
                "Hip hinge drill: 1 x 8",
                "Spanish squat: 2 x 30–45 s",
                "Glute bridge: 1 x 10",
                "3–4 séries de aproximação no primeiro exercício",
            ],
            "button": "✅ Aquecimento feito",
        },
    ],
    "post": [
        {
            "key": "core",
            "title": "Core final",
            "icon": "🧱",
            "duration": "3–5 min",
            "items": ["Prancha: 2 x 30–45 s"],
            "button": "✅ Core feito",
        },
    ],
    "exercicios": [
        {"ex": "Trap bar deadlift ou RDL", "series": 3, "reps": "4-6", "tipo": "composto", "descanso_s": 180},
        {"ex": "Hack squat ou belt squat pesado", "series": 3, "reps": "5-8", "tipo": "composto", "descanso_s": 150},
        {"ex": "Hip thrust pesado", "series": 2, "reps": "6-8", "tipo": "composto", "descanso_s": 150},
        {"ex": "Leg curl sentado/deitado", "series": 2, "reps": "8-10", "tipo": "isolado", "descanso_s": 90},
        {"ex": "Abdução máquina", "series": 1, "reps": "15-25", "tipo": "isolado", "descanso_s": 75},
        {"ex": "Gémeos sentado/em pé", "series": 3, "reps": "10-15", "tipo": "isolado", "descanso_s": 75},
        {"ex": "Crunch cabo leve/moderado", "series": 2, "reps": "10-15", "tipo": "isolado", "descanso_s": 75},
    ],
}

BRUNO_LOWER_B_SEG_TER_QUA_SEX = {
    "bloco": "BRUNO_LOWER",
    "sessao": "80–95 min",
    "protocolos": {"tendoes": False, "core": True, "cardio": False, "cooldown": False},
    "prep": BRUNO_LOWER_B_RECUP["prep"],
    "post": [
        {
            "key": "core",
            "title": "Core final",
            "icon": "🧱",
            "duration": "5–8 min",
            "items": [
                "Prancha: 2 x 30–45 s",
                "Bird dog: 2 x 6/lado",
                "Sem side bends, sem twists pesados.",
            ],
            "button": "✅ Core feito",
        },
    ],
    "exercicios": [
        {"ex": "RDL", "series": 3, "reps": "6-8", "tipo": "composto", "descanso_s": 180},
        {"ex": "Hack squat ou belt squat", "series": 3, "reps": "5-8", "tipo": "composto", "descanso_s": 150},
        {"ex": "Hip thrust pesado", "series": 3, "reps": "6-10", "tipo": "composto", "descanso_s": 150},
        {"ex": "Leg curl sentado/deitado", "series": 2, "reps": "8-10", "tipo": "isolado", "descanso_s": 90},
        {"ex": "Leg extension", "series": 2, "reps": "12-15", "tipo": "isolado", "descanso_s": 75},
        {"ex": "Abdução máquina", "series": 2, "reps": "15-25", "tipo": "isolado", "descanso_s": 75},
        {"ex": "Gémeos sentado/em pé", "series": 4, "reps": "8-15", "tipo": "isolado", "descanso_s": 75},
        {"ex": "Crunch cabo moderado", "series": 2, "reps": "10-15", "tipo": "isolado", "descanso_s": 75},
    ],
}

treinos_bruno_opcao_1 = {
    "Segunda — BRUNO UPPER A": BRUNO_UPPER_A,
    "Terça — BRUNO LOWER A": BRUNO_LOWER_A,
    "Sexta — BRUNO UPPER B": BRUNO_UPPER_B,
    "Sábado — BRUNO LOWER B": BRUNO_LOWER_B_RECUP,
}

treinos_bruno_opcao_2 = {
    "Segunda — BRUNO UPPER A": BRUNO_UPPER_A,
    "Terça — BRUNO LOWER A": BRUNO_LOWER_A,
    "Quarta — BRUNO UPPER B": BRUNO_UPPER_B,
    "Sexta — BRUNO LOWER B": BRUNO_LOWER_B_SEG_TER_QUA_SEX,
}

PLANOS = {"Base": treinos_base, "INEIX_ABC_v1": treinos_ineix, GUI_PPLA_ID: treinos_gui, BRUNO_OPCAO_1_ID: treinos_bruno_opcao_1, BRUNO_OPCAO_2_ID: treinos_bruno_opcao_2}

def gerar_treino_do_dia(dia, week, treinos_dict=None, plan_id="Base"):
    if plan_id == GUI_PPLA_ID:
        return gerar_treino_gui_dia(dia, week)
    treinos_dict = treinos_dict or treinos_base
    cfg = treinos_dict.get(dia, None)
    if not cfg:
        return {"bloco":"—","sessao":"","protocolos":{}, "prep": [], "post": [], "exercicios":[]}
    bloco = cfg["bloco"]
    treino_final = []
    for i, item in enumerate(cfg["exercicios"]):
        novo = dict(item)
        if ((plan_id == "Base" and is_deload(week) and bloco in ["Força","Hipertrofia"]) or (plan_id == GUI_PPLA_ID and is_gui_deload_week(week) and bloco in GUI_BLOCOS) or (plan_id in BRUNO_IDS and is_bruno_deload_week(week) and bloco in BRUNO_BLOCOS)):
            base_series = int(item["series"])
            if item["tipo"] == "composto":
                novo["series"] = max(2, int(round(base_series*0.6)))
            else:
                novo["series"] = max(1, int(round(base_series*0.6)))
        novo["rir_alvo"] = rir_alvo(item["tipo"], bloco, week)
        novo["tempo"] = tempo_exec(item["tipo"])
        try:
            novo["descanso_s"] = int(item.get("descanso_s", descanso_recomendado_s(item["tipo"], bloco)) or descanso_recomendado_s(item["tipo"], bloco))
        except Exception:
            novo["descanso_s"] = descanso_recomendado_s(item["tipo"], bloco)
        treino_final.append(novo)
    return {
        "bloco": bloco,
        "sessao": cfg["sessao"],
        "protocolos": cfg["protocolos"],
        "prep": list(cfg.get("prep", []) or []),
        "post": list(cfg.get("post", []) or []),
        "exercicios": treino_final,
    }

# --- 6. INTERFACE SIDEBAR ---
# topo decorativo da sidebar removido (UI mais limpa)

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


def _get_today_weekday_pt():
    """Dia atual em PT (timezone Lisboa), ex.: Segunda, Terça, ..."""
    try:
        now_local = datetime.datetime.now(ZoneInfo("Europe/Lisbon"))
    except Exception:
        now_local = datetime.datetime.now()
    nomes = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    return nomes[now_local.weekday()], now_local.weekday()


def _default_treino_index_for_today(options):
    """Escolhe o treino correspondente ao dia atual; se não existir, pega no próximo treino da semana."""
    if not options:
        return 0
    dia_nome, dia_idx = _get_today_weekday_pt()
    opts = [str(o) for o in options]

    # 1) Match direto por nome do dia no início (Segunda, Terça, ...)
    for i, op in enumerate(opts):
        if op.startswith(dia_nome):
            return i

    # 2) Match por conter o nome do dia (mais flexível)
    for i, op in enumerate(opts):
        if dia_nome in op:
            return i

    # 3) Se os treinos têm dias PT no nome, escolhe o próximo dia disponível a partir de hoje
    ordem = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    dias_presentes = []
    for i, op in enumerate(opts):
        idx = None
        for j, nome in enumerate(ordem):
            if op.startswith(nome) or nome in op:
                idx = j
                break
        dias_presentes.append(idx)

    if any(v is not None for v in dias_presentes):
        for offset in range(1, 8):
            alvo = (dia_idx + offset) % 7
            for i, d_idx in enumerate(dias_presentes):
                if d_idx == alvo:
                    return i

    # 4) Fallback (planos A/B/C etc.): mantém primeiro
    return 0

st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
st.sidebar.markdown("<h3>♣️ Grimório de</h3>", unsafe_allow_html=True)

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
    on_change=_reset_daily_state,
    label_visibility="collapsed",
)

# plano do perfil — agora visível e guardável, porque esconder planos era uma decisão muito "humana"
_PLAN_LABEL_BY_ID = {
    "Base": "Plano 5 dias — ULULU/PPLA atual",
    BRUNO_OPCAO_1_ID: "Bruno Opção 1 — Seg/Ter/Sex/Sáb (mais recuperável)",
    BRUNO_OPCAO_2_ID: "Bruno Opção 2 — Seg/Ter/Qua/Sex",
    GUI_PPLA_ID: "Gui — PPLA/PUSH-PULL-LEGS-ARMS",
    "INEIX_ABC_v1": "Ineix — ABC 3x/sem",
}
_PLAN_ID_BY_LABEL = {v: k for k, v in _PLAN_LABEL_BY_ID.items() if k in PLANOS}
_PLAN_LABELS_ORDER = [
    _PLAN_LABEL_BY_ID[k]
    for k in ["Base", BRUNO_OPCAO_1_ID, BRUNO_OPCAO_2_ID, GUI_PPLA_ID, "INEIX_ABC_v1"]
    if k in PLANOS and k in _PLAN_LABEL_BY_ID
]

def _default_plan_for_profile(_perfil: str) -> str:
    _p = str(_perfil or "").strip().lower()
    if _p == "ineix":
        return "INEIX_ABC_v1"
    if _p == "gui":
        return GUI_PPLA_ID
    if _p == "bruno":
        return BRUNO_OPCAO_2_ID
    return "Base"

def _save_plan_for_profile(_perfil: str, _plan_id: str, _df_profiles: pd.DataFrame):
    try:
        _perfil = str(_perfil or "").strip() or "Principal"
        _plan_id = str(_plan_id or "Base").strip()
        if _plan_id not in PLANOS:
            _plan_id = "Base"

        if _df_profiles is None or not isinstance(_df_profiles, pd.DataFrame):
            _dfp = pd.DataFrame(columns=PROFILES_COLUMNS)
        else:
            _dfp = _df_profiles.copy()

        for _c in PROFILES_COLUMNS:
            if _c not in _dfp.columns:
                _dfp[_c] = ""
        _dfp = _dfp[PROFILES_COLUMNS].copy()
        _dfp["Perfil"] = _dfp["Perfil"].astype(str).str.strip()
        _dfp = _dfp[_dfp["Perfil"] != ""]
        _dfp = _dfp[_dfp["Perfil"].astype(str) != _perfil]

        _new_row = pd.DataFrame([{
            "Perfil": _perfil,
            "Criado_em": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Plano_ID": _plan_id,
            "Ativo": "TRUE",
        }], columns=PROFILES_COLUMNS)
        _dfp = pd.concat([_dfp, _new_row], ignore_index=True)
        return save_profiles_df(_dfp)
    except Exception as _e:
        return False, str(_e)

_stored_plan_id = get_plan_id_for_profile(perfil_sel, df_profiles) if df_profiles is not None else ""
_default_plan_id = _default_plan_for_profile(perfil_sel)
_initial_plan_id = _stored_plan_id if _stored_plan_id in PLANOS else _default_plan_id
if _initial_plan_id not in PLANOS:
    _initial_plan_id = "Base"

_initial_label = _PLAN_LABEL_BY_ID.get(_initial_plan_id, _PLAN_LABEL_BY_ID["Base"])
if _initial_label not in _PLAN_LABELS_ORDER:
    _initial_label = _PLAN_LABEL_BY_ID["Base"]

st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
st.sidebar.markdown("<h3>Plano ativo</h3>", unsafe_allow_html=True)
_plan_label_sel = st.sidebar.selectbox(
    "Plano ativo",
    _PLAN_LABELS_ORDER,
    index=_PLAN_LABELS_ORDER.index(_initial_label),
    key=f"plano_label_sel::{perfil_sel}",
    label_visibility="collapsed",
    on_change=_reset_daily_state,
)
plano_id_sel = _PLAN_ID_BY_LABEL.get(_plan_label_sel, "Base")

if plano_id_sel == "Base":
    st.sidebar.caption("Plano de 5 dias guardado/selecionado.")
elif plano_id_sel in BRUNO_IDS:
    st.sidebar.caption("Plano Bruno novo selecionado. Opção 1 recupera melhor; opção 2 encaixa em Seg/Ter/Qua/Sex.")
else:
    st.sidebar.caption("Plano selecionado para este perfil.")

if st.sidebar.button("💾 Guardar plano neste perfil", key=f"save_plan::{perfil_sel}", width="stretch"):
    _ok_save_plan, _err_save_plan = _save_plan_for_profile(perfil_sel, plano_id_sel, df_profiles)
    if _ok_save_plan:
        st.sidebar.success("Plano guardado neste perfil ✅")
        try:
            df_profiles, profiles_ok, profiles_err = get_profiles_df(force_refresh=True)
        except Exception:
            pass
    else:
        st.sidebar.warning("Não consegui guardar na Google Sheet. Ficou no backup local se a Sheet falhou.")
        if _err_save_plan:
            st.sidebar.caption(str(_err_save_plan)[:220])

st.sidebar.markdown('</div>', unsafe_allow_html=True)

if plano_id_sel not in PLANOS:
    plano_id_sel = "Base"
st.session_state["plano_id_sel"] = plano_id_sel
# UI móvel limpa: esconder utilitários de plano/perfis/Google Sheets (funcionam em background)
_ok_conn, _err_conn = True, ""
try:
    _ = conn.read(ttl="0")
except Exception as _e:
    _ok_conn, _err_conn = False, str(_e)

bk_df = _load_offline_backup()
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


# --- TREINO PURO: se existir sessão em curso (snapshot), força o "Treino" (dia) e a semana,
# para poderes fazer "terça" na quarta e continuar depois sem a app voltar ao dia real.
try:
    st.session_state["_inprogress_active"] = False
    st.session_state.pop("_inprogress_session_key", None)

    _plano_active = str(st.session_state.get("plano_id_sel", "Base"))
    _k_ip, _p_ip = get_active_inprogress_session(perfil_sel, _plano_active, INPROGRESS_MAX_AGE_HOURS)

    if isinstance(_p_ip, dict) and isinstance(_k_ip, str):
        st.session_state["_inprogress_active"] = True
        st.session_state["_inprogress_session_key"] = _k_ip

        try:
            _p_dia = str(_p_ip.get("dia", "") or "")
            if _p_dia:
                st.session_state["dia_sel"] = _p_dia
        except Exception:
            pass

        try:
            _p_sem = int(_p_ip.get("semana", 0) or 0)
            if _p_sem > 0:
                st.session_state["semana_sel"] = _p_sem
        except Exception:
            pass

        try:
            _p_ui = _p_ip.get("ui", {}) if isinstance(_p_ip.get("ui", {}), dict) else {}
            if "disable_rest_timer" in _p_ui:
                st.session_state["disable_rest_timer"] = bool(_p_ui.get("disable_rest_timer", False))
        except Exception:
            pass
except Exception:
    pass


_treino_options = list(treinos_dict.keys())
_idx_today = _default_treino_index_for_today(_treino_options)
_today_option = _treino_options[_idx_today] if _treino_options else None
_manual_day_key = f"manual_treino_day::{perfil_sel}::{plan_id_active}"

if _manual_day_key not in st.session_state:
    st.session_state[_manual_day_key] = False

if ("dia_sel" not in st.session_state) or (st.session_state.get("dia_sel") not in _treino_options):
    try:
        if _today_option is not None:
            st.session_state["dia_sel"] = _today_option
    except Exception:
        pass

st.sidebar.markdown("<h3>Treino</h3>", unsafe_allow_html=True)

_inprogress_locked_day = bool(st.session_state.get("_inprogress_active"))
if not _inprogress_locked_day:
    _manual_day = st.sidebar.toggle(
        "Escolher outro dia",
        value=bool(st.session_state.get(_manual_day_key, False)),
        key=_manual_day_key,
        help="Ativa para fazer, por exemplo, o treino de sábado na quinta.",
    )
    if not _manual_day and _today_option is not None and st.session_state.get("dia_sel") != _today_option:
        st.session_state["dia_sel"] = _today_option
        try:
            _reset_daily_state()
        except Exception:
            pass
else:
    st.session_state[_manual_day_key] = True
    st.sidebar.caption("🔒 Sessão em curso ativa — o dia do treino fica preso até terminares ou fizeres reset do treino.")

dia = st.sidebar.selectbox(
    "Treino",
    _treino_options,
    key="dia_sel",
    on_change=_reset_daily_state,
    label_visibility="collapsed",
    disabled=_inprogress_locked_day,
)
st.sidebar.caption(f"⏱️ Sessão-alvo: **{treinos_dict[dia]['sessao']}**")
st.sidebar.markdown('</div>', unsafe_allow_html=True)


# --- YAMI: prontidão (check-in rápido) ---
st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
st.sidebar.markdown("<h3>Prontidão (Yami)</h3>", unsafe_allow_html=True)

_y_sleep = st.sidebar.radio("Sono", ["Ruim", "OK", "Top"], horizontal=True, key="yami_sleep")
_y_stress = st.sidebar.radio("Stress", ["Baixo", "Médio", "Alto"], horizontal=True, key="yami_stress")
_y_doms = st.sidebar.slider("Dor muscular (DOMS)", 0, 3, value=int(st.session_state.get("yami_doms", 1) or 1), key="yami_doms")
_y_joint = st.sidebar.slider("Dor articular (geral)", 0, 3, value=int(st.session_state.get("yami_joint", 0) or 0), key="yami_joint")

_y_read = yami_compute_readiness(_y_sleep, _y_stress, int(_y_doms), int(_y_joint))
st.session_state["yami_readiness"] = _y_read

_adj_pct_txt = f"{float(_y_read.get('adj_load_pct', 0.0) or 0.0)*100:+.0f}%"
_adj_rir_txt = f"{float(_y_read.get('adj_rir', 0.0) or 0.0):+.1f}"
st.sidebar.caption(f"Yami: **{_y_read.get('label','Normal')}** · Ajuste: **{_adj_pct_txt}** carga · **RIR {_adj_rir_txt}**")


if st.sidebar.button("💾 Guardar check-in", key="yami_save_checkin"):
    _ck = dict(_y_read)
    _ck["date"] = _lisbon_today_date().isoformat()
    yami_log_checkin(perfil_sel, _ck)
    st.sidebar.success("Check-in guardado.")

st.sidebar.markdown('</div>', unsafe_allow_html=True)


# FLAGS
st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
st.sidebar.markdown("<h3>Sinais do corpo</h3>", unsafe_allow_html=True)
dor_joelho = st.sidebar.checkbox("Dor no joelho (pontiaguda)", help="Se for dor pontiaguda/articular, a app sugere substituições (não é para ‘aguentar’).")
dor_cotovelo = st.sidebar.checkbox("Dor no cotovelo", help="Se o cotovelo estiver a reclamar, a app sugere variações mais amigáveis (ex.: pushdown barra V, amplitude menor).")
dor_ombro = st.sidebar.checkbox("Dor no ombro", help="Se o ombro estiver sensível, a app sugere ajustes (pega neutra, inclinação menor, sem grind).")
dor_lombar = st.sidebar.checkbox("Dor na lombar", help="Se a lombar estiver a dar sinal, a app sugere limitar amplitude e usar mais apoio/variações seguras.")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# guardar sinais no session_state (para o Yami usar nas sugestões)
try:
    st.session_state["sig_dor_joelho"] = bool(dor_joelho)
    st.session_state["sig_dor_cotovelo"] = bool(dor_cotovelo)
    st.session_state["sig_dor_ombro"] = bool(dor_ombro)
    st.session_state["sig_dor_lombar"] = bool(dor_lombar)
except Exception:
    pass

try:
    _sig_on = []
    if bool(st.session_state.get("sig_dor_joelho", False)): _sig_on.append("joelho")
    if bool(st.session_state.get("sig_dor_cotovelo", False)): _sig_on.append("cotovelo")
    if bool(st.session_state.get("sig_dor_ombro", False)): _sig_on.append("ombro")
    if bool(st.session_state.get("sig_dor_lombar", False)): _sig_on.append("lombar")
    if _sig_on:
        st.sidebar.caption("⚠️ Sinais ativos: **" + ", ".join(_sig_on) + "**. O Yami vai ser mais conservador nos exercícios que batem aqui.")
except Exception:
    pass



# TIMER
st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
st.sidebar.markdown("<h3>Descanso</h3>", unsafe_allow_html=True)

def _on_disable_rest_timer_change():
    try:
        _persist_disable_rest_timer_for_active_session(perfil_sel, st.session_state.get("plano_id_sel", "Base"))
    except Exception:
        pass

if "disable_rest_timer" not in st.session_state:
    st.session_state["disable_rest_timer"] = True

try:
    disable_rest_timer = st.sidebar.toggle(
        "Sem timer de descanso automático",
        value=bool(st.session_state.get("disable_rest_timer", False)),
        key="disable_rest_timer",
        help="Ligado por defeito. Em vez de contagem automática, aparece uma janela grande com o descanso sugerido, botão OK e fecho automático ao fim de 10 segundos.",
        on_change=_on_disable_rest_timer_change,
    )
except Exception:
    disable_rest_timer = st.sidebar.checkbox(
        "Sem timer de descanso automático",
        value=bool(st.session_state.get("disable_rest_timer", False)),
        key="disable_rest_timer",
        help="Ligado por defeito. Em vez de contagem automática, aparece uma janela grande com o descanso sugerido, botão OK e fecho automático ao fim de 10 segundos.",
        on_change=_on_disable_rest_timer_change,
    )

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# PERIODIZAÇÃO (último na sidebar)
plano_cycle = st.session_state.get("plano_id_sel","Base")
is_ineix = (plano_cycle == "INEIX_ABC_v1")
if not is_ineix:
    cycle_len = 12 if plano_cycle == GUI_PPLA_ID else (6 if plano_cycle in BRUNO_IDS else 8)

    # --- Semana automática (não tens de te lembrar de mexer) ---
    _cyc_cfg = yami_get_cycle_cfg(perfil_sel, plano_cycle)
    _cyc_key = hashlib.md5(f"{perfil_sel}|{plano_cycle}".encode("utf-8")).hexdigest()[:8]
    _auto_week_key = f"auto_week::{_cyc_key}"
    if _auto_week_key not in st.session_state:
        st.session_state[_auto_week_key] = bool(_cyc_cfg.get("auto", True))

    st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.sidebar.markdown("<h3>Periodização</h3>", unsafe_allow_html=True)

    try:
        auto_week = st.sidebar.toggle(
            "Semana automática",
            value=bool(st.session_state.get(_auto_week_key, True)),
            key=_auto_week_key,
            help="Calcula a semana pelo calendário a partir da data de início do ciclo.",
            on_change=_reset_daily_state,
        )
    except Exception:
        auto_week = st.sidebar.checkbox(
            "Semana automática",
            value=bool(st.session_state.get(_auto_week_key, True)),
            key=_auto_week_key,
            help="Calcula a semana pelo calendário a partir da data de início do ciclo.",
            on_change=_reset_daily_state,
        )
    try:
        yami_set_cycle_cfg(perfil_sel, plano_cycle, auto=bool(auto_week))
    except Exception:
        pass

    def _infer_cycle_start_from_history() -> str:
        """Heurística: tenta inferir o início do ciclo olhando para o histórico recente.
        Regra simples: pega na data mais antiga dentro dos últimos 21 dias.
        """
        try:
            dfh = df_all
        except Exception:
            return ""

        if dfh is None or dfh.empty:
            return ""

        try:
            dfh = dfh[
                (dfh["Perfil"].astype(str) == str(perfil_sel)) &
                (dfh["Plano_ID"].astype(str) == str(plano_cycle))
            ].copy()
        except Exception:
            return ""

        if dfh.empty or ("Data" not in dfh.columns):
            return ""

        try:
            dfh["_data_dt"] = pd.to_datetime(dfh["Data"], dayfirst=True, errors="coerce")
            dfh = dfh.dropna(subset=["_data_dt"])
        except Exception:
            return ""

        if dfh.empty:
            return ""

        today = _lisbon_today_date()
        ds = []
        for d in dfh["_data_dt"].dt.date.tolist():
            try:
                if 0 <= (today - d).days <= 21:
                    ds.append(d)
            except Exception:
                pass

        if not ds:
            return ""

        return min(ds).isoformat()

    if bool(auto_week):
        start_iso = str(_cyc_cfg.get("start", "") or "").strip()
        if not start_iso:
            # tenta inferir pelo histórico recente (funciona bem quando estás na semana 2 e esqueceste de mexer)
            start_iso = _infer_cycle_start_from_history()
            if start_iso:
                try:
                    yami_set_cycle_cfg(perfil_sel, plano_cycle, start_iso=start_iso)
                except Exception:
                    pass
        if not start_iso:
            # fallback: assume que hoje é o início (melhor do que inventar)
            start_iso = _lisbon_today_date().isoformat()
            try:
                yami_set_cycle_cfg(perfil_sel, plano_cycle, start_iso=start_iso)
            except Exception:
                pass

        try:
            start_date = datetime.date.fromisoformat(start_iso)
        except Exception:
            start_date = _lisbon_today_date()
            start_iso = start_date.isoformat()
        today = _lisbon_today_date()

        wk = int(((today - start_date).days // 7) + 1)
        wk = max(1, min(int(cycle_len), wk))

        prev = int(st.session_state.get("semana_sel", 1) or 1)
        _lock_week = bool(st.session_state.get("_inprogress_active"))
        if not _lock_week:
            if prev != wk:
                st.session_state["semana_sel"] = wk
                try:
                    _reset_daily_state()
                except Exception:
                    pass
        else:
            # Mantém a semana da sessão em curso (não força o calendário de hoje)
            wk = prev
        semana = int(st.session_state.get("semana_sel", wk) or wk)
        st.sidebar.caption(f"Semana: **{semana}/{cycle_len}** · Início: **{start_iso}**")

        with st.sidebar.expander("Ajustar semana automática", expanded=False):
            _start_key = f"cycle_start::{_cyc_key}"
            _wk_key = f"cycle_week::{_cyc_key}"
            _pending_start_key = f"cycle_pending_start::{_cyc_key}"
            _pending_week_key = f"cycle_pending_week::{_cyc_key}"

            # aplica updates pendentes ANTES dos widgets (Streamlit não deixa mexer no state de um widget depois de criado)
            try:
                if _pending_start_key in st.session_state:
                    _p = st.session_state.get(_pending_start_key)
                    if isinstance(_p, datetime.date):
                        st.session_state[_start_key] = _p
                    else:
                        # tenta converter ISO -> date
                        try:
                            st.session_state[_start_key] = datetime.date.fromisoformat(str(_p))
                        except Exception:
                            pass
                    del st.session_state[_pending_start_key]
                if _pending_week_key in st.session_state:
                    _pw = st.session_state.get(_pending_week_key)
                    try:
                        st.session_state[_wk_key] = int(_pw)
                    except Exception:
                        pass
                    del st.session_state[_pending_week_key]
            except Exception:
                pass

            if _start_key not in st.session_state:
                st.session_state[_start_key] = start_date
            if _wk_key not in st.session_state:
                st.session_state[_wk_key] = int(semana)

            new_start = st.date_input(
                "Início do ciclo",
                value=st.session_state.get(_start_key, start_date),
                key=_start_key,
                help="Se o ciclo começou antes, mete a data certa e a semana ajusta sozinha.",
            )

            # se mudar a data, recalcula e guarda
            try:
                if isinstance(new_start, datetime.date) and new_start.isoformat() != start_iso:
                    yami_set_cycle_cfg(perfil_sel, plano_cycle, start_iso=new_start.isoformat())
                    start_date = new_start
                    start_iso = new_start.isoformat()
                    wk = int(((today - start_date).days // 7) + 1)
                    wk = max(1, min(int(cycle_len), wk))
                    st.session_state["semana_sel"] = wk
                    st.session_state[_wk_key] = wk
            except Exception:
                pass

            cols = st.columns(2)
            with cols[0]:
                target_week = st.number_input(
                    "Hoje é semana",
                    min_value=1,
                    max_value=int(cycle_len),
                    value=int(st.session_state.get(_wk_key, semana) or semana),
                    key=_wk_key,
                )
            with cols[1]:
                if st.button("Aplicar", key=f"cycle_apply::{_cyc_key}"):
                    try:
                        tw = int(target_week)
                    except Exception:
                        tw = int(semana)
                    tw = max(1, min(int(cycle_len), tw))
                    # define start = hoje - (tw-1)*7
                    start2 = today - datetime.timedelta(days=7 * (tw - 1))
                    try:
                        yami_set_cycle_cfg(perfil_sel, plano_cycle, start_iso=start2.isoformat())
                    except Exception:
                        pass
                    # não mexer diretamente no state do date_input (key=_start_key) aqui, senão Streamlit explode.
                    # mete como "pendente" e aplica antes dos widgets no rerun seguinte.
                    st.session_state[_pending_start_key] = start2
                    st.session_state[_pending_week_key] = tw
                    st.session_state["semana_sel"] = tw
                    try:
                        _reset_daily_state()
                    except Exception:
                        pass
                    st.rerun()
    else:
        # modo manual (old-school)
        try:
            _wk_state = int(st.session_state.get("semana_sel", 1) or 1)
        except Exception:
            _wk_state = 1

        if _wk_state < 1 or _wk_state > int(cycle_len):
            st.session_state["semana_sel"] = 1
            _wk_state = 1

        if plano_cycle == GUI_PPLA_ID:
            semana_sel = st.sidebar.radio(
                "Semana do ciclo:",
                list(range(1, 13)),
                format_func=semana_label_gui,
                index=min(max(_wk_state - 1, 0), 11),
                key="semana_sel",
                on_change=_reset_daily_state,
                label_visibility="collapsed",
            )
        elif plano_cycle in BRUNO_IDS:
            semana_sel = st.sidebar.radio(
                "Semana do ciclo:",
                list(range(1, 7)),
                format_func=semana_label_bruno,
                index=min(max(_wk_state - 1, 0), 5),
                key="semana_sel",
                on_change=_reset_daily_state,
                label_visibility="collapsed",
            )
        else:
            semana_sel = st.sidebar.radio(
                "Semana do ciclo:",
                list(range(1, 9)),
                format_func=semana_label,
                index=min(max(_wk_state - 1, 0), 7),
                key="semana_sel",
                on_change=_reset_daily_state,
                label_visibility="collapsed",
            )
        semana = int(semana_sel)

    st.sidebar.markdown('</div>', unsafe_allow_html=True)
else:
    # Plano Ineix (A/B/C) não usa periodização por semanas
    semana = 1




# Modo mobile permanente (sem toggles na sidebar)
st.session_state["ui_compact_mode"] = False
st.session_state["ui_pure_mode"] = True
st.session_state["ui_show_last_table"] = True
st.session_state["ui_show_rules"] = True

def sugestao_articular(ex: str) -> str:
    exs = str(ex or "")
    exl = exs.lower()

    alerts, subs, cues = [], [], []

    if dor_joelho and any(k in exl for k in ["agach", "squat", "leg press", "bulgarian", "lunge", "extens", "hack", "step"]):
        alerts.append("joelho")
        cues += ["ROM só até onde não há dor pontiaguda", "2–3s descida, sem bounce", "joelho segue a linha do pé"]
        subs += ["Belt squat / Hack squat (ROM tolerável)",
                 "Leg press (pés mais altos, amplitude menor)",
                 "Hip thrust / Glute bridge",
                 "Leg curl (posterior)"]

    if dor_ombro and any(k in exl for k in ["ohp", "overhead", "supino", "bench", "inclinado", "press", "dips", "fly"]):
        alerts.append("ombro")
        cues += ["pega neutra quando possível", "amplitude confortável", "sem grind"]
        subs += ["Press máquina (pega neutra) / Halteres neutros",
                 "Floor press / Push-up mãos neutras",
                 "Inclinação menor (se for inclinado)",
                 "Cabo: press unilateral leve"]

    if dor_cotovelo and any(k in exl for k in ["tríceps", "triceps", "curl", "bíceps", "biceps", "barra fixa", "pull-up", "chin", "remada"]):
        alerts.append("cotovelo")
        cues += ["evitar barra reta se irrita", "punho neutro", "excêntrico 3–4s em isoladores"]
        subs += ["Tríceps: corda / barra V",
                 "Bíceps: halteres neutros/martelo / máquina",
                 "Pull: pega neutra e amplitude confortável"]

    if dor_lombar and any(k in exl for k in ["deadlift", "rdl", "remada", "row", "agach", "squat", "good morning", "hip hinge"]):
        alerts.append("lombar")
        cues += ["coluna neutra perfeita; se perde, encurta ROM", "mais apoio hoje", "bracing antes de reps pesadas"]
        subs += ["Remada peito apoiado / máquina",
                 "Hip thrust / Glute bridge (se hinge irrita)",
                 "Leg press / Hack / Belt squat",
                 "Extensão lombar leve (se tolerado)"]

    if not alerts:
        return ""

    def _uniq(seq):
        out, seen = [], set()
        for x in seq:
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        return out

    alerts, subs, cues = _uniq(alerts), _uniq(subs), _uniq(cues)

    msg = []
    msg.append(f"🩹 **Sinais hoje:** {', '.join(alerts)}.")
    if cues:
        msg.append("**Cues:** " + " · ".join(cues[:3]))
    if subs:
        msg.append("**Substituições (hoje):**\n- " + "\n- ".join(subs[:4]))
    msg.append("_Se for dor pontiaguda/articular, troca a variação hoje. Se persistir, reduz volume e procura avaliação._")
    return "\n".join(msg)

# --- 7. CABEÇALHO ---
st.markdown("""
<style>
.bc-header-center{ text-align:center; margin: 2px 0 10px 0; }
.bc-tagline{ margin-top: 2px; font-size: 1rem; color: rgba(232,226,226,0.70); }

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='bc-header-center'>
  <div class='bc-tagline'>Powered by SOHCAHTOA & Ltd.</div>
  <div class='bc-main-title'>Black Clover Training</div>

</div>
""", unsafe_allow_html=True)

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

    def _bc_fmt_mmss(secs: int) -> str:
        try:
            s = max(0, int(secs or 0))
        except Exception:
            s = 0
        m, s2 = divmod(s, 60)
        return f"{m:02d}:{s2:02d}"

    def _bc_fmt_hms(ts: float) -> str:
        try:
            dt = datetime.datetime.fromtimestamp(float(ts), ZoneInfo("Europe/Lisbon"))
        except Exception:
            dt = datetime.datetime.fromtimestamp(float(ts))
        return dt.strftime("%H:%M:%S")

    def _bc_show_rest_info_window(total_s: int, start_ts: float, end_ts: float, ex_name: str = "") -> None:
        """Mostra uma janela grande com o descanso sugerido quando o timer está desligado."""
        try:
            payload = {
                "ex": str(ex_name or ""),
                "mmss": _bc_fmt_mmss(int(total_s or 0)),
                "start": _bc_fmt_hms(float(start_ts)),
                "end": _bc_fmt_hms(float(end_ts)),
            }
            components.html(
                f"""
<script>
(function(){{
  try {{
    const d = parent.document || document;
    const id = 'bc-rest-info-modal';
    const payload = {json.dumps(payload)};
    let ov = d.getElementById(id);
    if (!ov) {{
      ov = d.createElement('div');
      ov.id = id;
      ov.style.position = 'fixed';
      ov.style.inset = '0';
      ov.style.zIndex = '100000';
      ov.style.display = 'flex';
      ov.style.alignItems = 'center';
      ov.style.justifyContent = 'center';
      ov.style.background = 'rgba(0,0,0,0.78)';
      ov.style.backdropFilter = 'blur(9px)';
      ov.style.padding = '18px';
      d.body.appendChild(ov);
    }}

    if (ov.__bcRestCloseTimer) {{
      try {{ clearTimeout(ov.__bcRestCloseTimer); }} catch(e) {{}}
      ov.__bcRestCloseTimer = null;
    }}
    if (ov.__bcRestCountTimer) {{
      try {{ clearInterval(ov.__bcRestCountTimer); }} catch(e) {{}}
      ov.__bcRestCountTimer = null;
    }}

    const title = payload.ex ? ('Descanso • ' + payload.ex) : 'Descanso';
    ov.innerHTML = `
      <div style="width:min(620px, 94vw); border-radius:20px; border:1px solid rgba(255,255,255,0.12); background:linear-gradient(180deg, rgba(20,20,20,0.96), rgba(12,12,12,0.96)); box-shadow:0 22px 44px rgba(0,0,0,0.58); overflow:hidden;">
        <div style="padding:16px 18px; border-bottom:1px solid rgba(255,255,255,0.08); display:flex; align-items:center; justify-content:space-between; gap:10px;">
          <div style="font-weight:900; color:#E8E2E2; letter-spacing:.02em; font-size:18px;">⏱️ ${title}</div>
          <div id="bc-rest-countdown" style="font-size:12px; color:rgba(232,226,226,0.72);">Fecha em 10s</div>
        </div>
        <div style="padding:20px 18px 18px 18px; color:rgba(232,226,226,0.94); text-align:center;">
          <div style="font-size:52px; line-height:1; font-weight:900; color:#FFFFFF; margin:6px 0 10px 0;">${payload.mmss}</div>
          <div style="font-size:14px; opacity:.82; margin-bottom:14px;">Descanso sugerido sem contagem automática.</div>
          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; text-align:left; margin-bottom:16px;">
            <div style="border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:12px 14px; background:rgba(255,255,255,0.03);">
              <div style="opacity:.72; font-size:12px;">Início</div>
              <div style="font-weight:900; font-size:18px;">${payload.start}</div>
            </div>
            <div style="border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:12px 14px; background:rgba(255,255,255,0.03);">
              <div style="opacity:.72; font-size:12px;">Fim estimado</div>
              <div style="font-weight:900; font-size:18px;">${payload.end}</div>
            </div>
          </div>
          <button id="bc-rest-ok" style="min-width:180px; border:1px solid rgba(255,255,255,0.16); background:rgba(140,29,44,0.28); color:#FFF; border-radius:12px; padding:12px 18px; font-size:16px; font-weight:800; cursor:pointer;">OK</button>
        </div>
      </div>
    `;

    function close() {{
      try {{
        if (ov.__bcRestCloseTimer) clearTimeout(ov.__bcRestCloseTimer);
        if (ov.__bcRestCountTimer) clearInterval(ov.__bcRestCountTimer);
      }} catch(e) {{}}
      try {{ ov.remove(); }} catch(e) {{ ov.style.display = 'none'; }}
    }}

    const btn = ov.querySelector('#bc-rest-ok');
    if (btn) btn.onclick = close;
    ov.onclick = (e) => {{ if (e.target === ov) close(); }};

    let secs = 10;
    const lbl = ov.querySelector('#bc-rest-countdown');
    if (lbl) lbl.textContent = `Fecha em ${secs}s`;
    ov.__bcRestCountTimer = setInterval(() => {{
      secs -= 1;
      if (lbl) lbl.textContent = `Fecha em ${Math.max(0, secs)}s`;
      if (secs <= 0) {{
        close();
      }}
    }}, 1000);
    ov.__bcRestCloseTimer = setTimeout(close, 10000);
  }} catch(e) {{}}
}})();
</script>
""",
                height=0,
            )
        except Exception:
            pass



    def _queue_auto_rest(seconds:int, ex_name:str=""):
        try:
            secs = max(1, int(seconds))
        except Exception:
            secs = 60

        # Se o utilizador desligar o timer, não fazemos contagem; mostramos só a info.
        if bool(st.session_state.get("disable_rest_timer", False)):
            start_ts = float(time.time())
            end_ts = float(start_ts) + float(secs)
            st.session_state["rest_info_pending"] = True
            st.session_state["rest_info_total_s"] = int(secs)
            st.session_state["rest_info_start_ts"] = float(start_ts)
            st.session_state["rest_info_end_ts"] = float(end_ts)
            st.session_state["rest_info_ex"] = str(ex_name or "")
            st.session_state["rest_auto_run"] = False
            st.session_state["yami_last_rest_s"] = int(secs)
            return

        start_ts = float(time.time())
        st.session_state["rest_auto_seconds"] = secs
        st.session_state["rest_auto_from"] = str(ex_name or "")
        st.session_state["rest_auto_start_ts"] = float(start_ts)
        st.session_state["rest_auto_end_ts"] = float(start_ts) + float(secs)
        st.session_state["rest_auto_run"] = True
        st.session_state["rest_auto_notified"] = False
        st.session_state["scroll_to_rest_timer"] = True
        st.session_state["yami_last_rest_s"] = secs


    # Timer desligado: se estava a correr, parar contagem ativa e mostrar só a janela com o descanso recomendado.
    if bool(st.session_state.get("disable_rest_timer", False)) and bool(st.session_state.get("rest_auto_run", False)):
        try:
            total_rest = int(st.session_state.get("rest_auto_seconds", 60) or 60)
            end_ts = float(st.session_state.get("rest_auto_end_ts", float(time.time()) + float(total_rest)) or (float(time.time()) + float(total_rest)))
            start_ts = float(st.session_state.get("rest_auto_start_ts", float(end_ts) - float(total_rest)) or (float(end_ts) - float(total_rest)))
            ex_rest = str(st.session_state.get("rest_auto_from", "") or "")
        except Exception:
            total_rest = 60
            start_ts = float(time.time())
            end_ts = float(start_ts) + float(total_rest)
            ex_rest = ""
        st.session_state["rest_info_pending"] = True
        st.session_state["rest_info_total_s"] = int(total_rest)
        st.session_state["rest_info_start_ts"] = float(start_ts)
        st.session_state["rest_info_end_ts"] = float(end_ts)
        st.session_state["rest_info_ex"] = str(ex_rest)
        st.session_state["rest_auto_run"] = False

    # Se houver info pendente (timer desligado), mostra uma janela com horas e mm:ss.
    if bool(st.session_state.get("rest_info_pending", False)):
        try:
            total_rest = int(st.session_state.get("rest_info_total_s", 60) or 60)
            start_ts = float(st.session_state.get("rest_info_start_ts", float(time.time())) or float(time.time()))
            end_ts = float(st.session_state.get("rest_info_end_ts", float(start_ts) + float(total_rest)) or (float(start_ts) + float(total_rest)))
            ex_rest = str(st.session_state.get("rest_info_ex", "") or "")
        except Exception:
            total_rest = 60
            start_ts = float(time.time())
            end_ts = float(start_ts) + float(total_rest)
            ex_rest = ""
        _bc_show_rest_info_window(total_rest, start_ts, end_ts, ex_rest)
        st.session_state["rest_info_pending"] = False

    # Timer normal (contagem)
    if bool(st.session_state.get("rest_auto_run", False)) and (not bool(st.session_state.get("disable_rest_timer", False))):
        st.markdown("<div id='rest-timer-anchor'></div>", unsafe_allow_html=True)
        total_rest = int(st.session_state.get("rest_auto_seconds", 60) or 60)
        ex_rest = str(st.session_state.get("rest_auto_from", ""))
        end_ts = float(st.session_state.get("rest_auto_end_ts", float(time.time()) + total_rest))
        rem_float = end_ts - float(time.time())
        rem = int(rem_float) if rem_float.is_integer() else int(rem_float) + (1 if rem_float > 0 else 0)
        rem = max(0, rem)
        elapsed = max(0, total_rest - rem)

        label = (f"⏱️ Descanso • {ex_rest}" if ex_rest else "⏱️ Descanso") + f"  ·  Yami: {total_rest}s"
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
        _rest_pct = min(1.0, elapsed / max(1, total_rest))
        st.markdown(
            f"<div class='bc-rest-track'><div class='bc-rest-fill' style='width:{_rest_pct*100:.1f}%'></div></div>",
            unsafe_allow_html=True
        )

        if rem <= 0:
            st.success("Descanso concluído ✅")
            if not bool(st.session_state.get("rest_auto_notified", False)):
                st.toast("Descanso concluído ✅")
                trigger_rest_done_feedback()
                st.session_state["rest_auto_notified"] = True
            st.session_state["rest_auto_run"] = False
        else:
            # Não fazer st.rerun() a cada segundo no mobile.
            # O contador atualiza no browser e só volta ao Python quando o utilizador toca num botão.
            components.html(
                f"""
                <div id="bc-live-rest" style="
                    font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
                    color: #E8E2E2;
                    background: rgba(18,18,18,.72);
                    border: 1px solid rgba(255,255,255,.10);
                    border-radius: 12px;
                    padding: 8px 10px;
                    margin-top: 6px;
                    text-align: center;
                    font-weight: 800;
                    font-size: 16px;">
                  Descanso: <span id="bc-live-rest-rem">{rem}</span>s
                </div>
                <script>
                (function() {{
                  try {{
                    const endTs = {float(end_ts) * 1000.0};
                    const total = Math.max(1, {int(total_rest)});
                    const remEl = document.getElementById('bc-live-rest-rem');
                    const box = document.getElementById('bc-live-rest');
                    let notified = false;
                    function tick() {{
                      const rem = Math.max(0, Math.ceil((endTs - Date.now()) / 1000));
                      if (remEl) remEl.textContent = String(rem);
                      try {{
                        const pct = Math.max(0, Math.min(1, (total - rem) / total));
                        const fill = parent.document.querySelector('.bc-rest-fill') || document.querySelector('.bc-rest-fill');
                        if (fill) fill.style.width = (pct * 100).toFixed(1) + '%';
                      }} catch(e) {{}}
                      if (rem <= 0) {{
                        if (box) box.innerHTML = 'Descanso concluído ✅';
                        if (!notified) {{
                          notified = true;
                          try {{ navigator.vibrate && navigator.vibrate([120,50,120]); }} catch(e) {{}}
                        }}
                        clearInterval(window.__bcRestTimerInterval);
                      }}
                    }}
                    if (window.__bcRestTimerInterval) clearInterval(window.__bcRestTimerInterval);
                    tick();
                    window.__bcRestTimerInterval = setInterval(tick, 1000);
                  }} catch(e) {{}}
                }})();
                </script>
                """,
                height=54,
            )

    if show_rules:
        with st.expander("📜 Regras rápidas do plano"):
            _pid_rules = st.session_state.get("plano_id_sel","Base")
            if _pid_rules == "INEIX_ABC_v1":
                st.markdown("""
**Plano Ineix (A/B/C 3x/sem):**  
**Intensidade:** RIR **2** em todas as séries (sem falhar).  
**Descanso:** **60–90s**.  
**Tempo:** Compostos 2–0–1 | Isoladores 3–0–1  
Dor articular pontiaguda = troca variação no dia.
""")
            elif _pid_rules == GUI_PPLA_ID:
                st.markdown(f"""
**Plano Gui (PUSH / PULL / LEGS / ARMS):**  
**Intensidade:** RIR **2** na maior parte do ciclo.  
**Descanso:** **60–90s**.  
**Tempo:** Compostos 2–0–1 | Isoladores 3–0–1  
**Semana atual:** **{semana_label_gui(semana)}**  
**Deload (sem 6 e 12):** ~50–60% das séries, -10 a -15% carga, sem drop / sem M+M, RIR 2–4.
""")
            elif _pid_rules in BRUNO_IDS:
                st.markdown(f"""
**Plano Bruno (4 dias):**  
**Semanas 1–2:** compostos RIR **2–3**; isoladores RIR **1–2**.  
**Semanas 3–5:** progressão; compostos RIR **1–2**; isoladores podem ficar em RIR **1**.  
**Semana atual:** **{semana_label_bruno(semana)}**  
**Deload (sem 6):** -40 a -50% séries, -10 a -15% carga, RIR 3–4.  
**Cardio:** só nos upper. Sem cardio pós-perna.  
**Core:** anti-extensão/estabilidade. Nada de twists/side bends pesados.
""")
            else:
                st.markdown("""
**Força:** RIR 2–3.  
**Hipertrofia:** RIR 1–2.  
**Deload (sem 4 e 8):** -40 a -50% séries, -10 a -15% carga, RIR 3–4.  

**Tempo:** Compostos 2–0–1 | Isoladores 3–0–1  
**Descanso:** Compostos 2–3 min | Isoladores 45–90s  
**Cardio:** só nos dias upper. Sem cardio nos lower.  
Dor articular pontiaguda = troca variação no dia.
""")
    elif pure_workout_mode:
        st.caption("Modo treino puro ativo: foco total no treino.")

    cfg = gerar_treino_do_dia(dia, semana, treinos_dict=treinos_dict, plan_id=st.session_state.get("plano_id_sel","Base"))
    bloco = cfg["bloco"]

    _plano = str(st.session_state.get("plano_id_sel", "Base"))
    _local = str(st.session_state.get("ineix_local", "")) if _plano == "INEIX_ABC_v1" else ""
    _week_txt = "RIR 2 fixo" if _plano == "INEIX_ABC_v1" else semana_label_por_plano(semana, _plano)
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

    treino_exec_tab, treino_tabela_tab = st.tabs(["🎯 Executar", "📋 Tabela do dia"])

    def _build_tabela_treino_dia(_cfg, _perfil, _dia, _bloco, _semana, _df_hist):
        _rows = []
        if not isinstance(_cfg, dict):
            return pd.DataFrame()
        _plan_id = str(st.session_state.get("plano_id_sel", "Base"))
        for _b in _cfg_prep_blocks(_cfg):
            _rows.append({
                "#": "P",
                "Exercício": str(_b.get("title", "Preparação") or "Preparação"),
                "Tipo": "Fluxo",
                "Feitas": "✅" if bool(st.session_state.get(_session_block_state_key(_b), False)) else "⏳",
                "Séries": "—",
                "Reps": "—",
                "RIR": "—",
                "Carga sugerida": "—",
                "Tempo": str(_b.get("duration", "—") or "—"),
                "Descanso": "—",
                "Último registo": "Bloco da sessão",
            })
        for _i, _item in enumerate(list(_cfg.get("exercicios", []) or [])):
            _ex = str(_item.get("ex", "") or "")
            _ex_ui = _exercise_ui_label(_item)
            try:
                _series = int(_item.get("series", 0) or 0)
            except Exception:
                _series = 0
            _reps = str(_item.get("reps", "") or "")
            _rir_txt = str(_item.get("rir_alvo", "") or "")
            _tempo = str(_item.get("tempo", "") or "")
            _tipo = str(_item.get("tipo", "") or "")
            try:
                _desc = int(_item.get("descanso_s", 0) or 0)
            except Exception:
                _desc = 0
            try:
                _done_sets = int(st.session_state.get(f"pt_done::{_perfil}::{_dia}::{_i}", 0) or 0)
            except Exception:
                _done_sets = 0

            try:
                _df_last, _peso_medio, _rir_medio, _data_ultima = get_historico_detalhado(_df_hist, _perfil, _ex)
            except Exception:
                _df_last, _peso_medio, _rir_medio, _data_ultima = pd.DataFrame(), 0.0, None, None

            _ultimo = _latest_set_summary_from_df_last(_df_last) or "—"
            if _data_ultima:
                try:
                    _ultimo = f"{_ultimo} · {_data_ultima}"
                except Exception:
                    pass

            _peso_txt = "—"
            try:
                _yami_tbl = yami_coach_sugestao(_df_hist, _perfil, _ex, _item, _bloco, _semana, _plan_id)
                _peso_sug_tbl = float((_yami_tbl or {}).get('peso_work_sugerido', (_yami_tbl or {}).get('peso_sugerido', 0.0)) or 0.0)
                if _peso_sug_tbl > 0:
                    _peso_txt = f"{_peso_sug_tbl:.1f} kg"
            except Exception:
                _peso_txt = "—"

            _rows.append({
                "#": _i + 1,
                "Exercício": _ex_ui,
                "Tipo": (f"{_tipo} · {_exercise_group_label(_item)}" if _exercise_group_label(_item) else (_tipo or "—")),
                "Feitas": f"{min(_done_sets, _series)}/{_series}" if _series > 0 else str(_done_sets),
                "Séries": _series,
                "Reps": _reps or "—",
                "RIR": _rir_txt or "—",
                "Carga sugerida": _peso_txt,
                "Tempo": _tempo or "—",
                "Descanso": f"{_desc}s" if _desc > 0 else "—",
                "Último registo": _ultimo,
            })
        for _b in _cfg_post_blocks(_cfg, _cfg.get("protocolos", {})):
            _rows.append({
                "#": "F",
                "Exercício": str(_b.get("title", "Fecho") or "Fecho"),
                "Tipo": "Fluxo",
                "Feitas": "✅" if bool(st.session_state.get(_session_block_state_key(_b), False)) else "⏳",
                "Séries": "—",
                "Reps": "—",
                "RIR": "—",
                "Carga sugerida": "—",
                "Tempo": str(_b.get("duration", "—") or "—"),
                "Descanso": "—",
                "Último registo": "Bloco da sessão",
            })
        return pd.DataFrame(_rows)

    with treino_tabela_tab:
        _df_tabela_dia = _build_tabela_treino_dia(cfg, perfil_sel, dia, bloco, semana, df_all.copy() if isinstance(df_all, pd.DataFrame) else get_data())
        if _df_tabela_dia.empty:
            st.info("Sem exercícios para mostrar neste dia.")
        else:
            _tot_ex = int(len(_df_tabela_dia))
            try:
                _tot_series = int(pd.to_numeric(_df_tabela_dia["Séries"], errors="coerce").fillna(0).sum())
            except Exception:
                _tot_series = 0
            try:
                _tot_feitas = int(sum(int(str(x).split('/')[0]) for x in _df_tabela_dia["Feitas"].tolist()))
            except Exception:
                _tot_feitas = 0
            tm1, tm2, tm3 = st.columns(3)
            tm1.metric("Exercícios", f"{_tot_ex}")
            tm2.metric("Séries totais", f"{_tot_series}")
            tm3.metric("Séries feitas", f"{_tot_feitas}")
            st.caption("Vista rápida do treino completo do dia. Atualiza com o plano e com o progresso guardado na sessão.")
            st.dataframe(_df_tabela_dia, hide_index=True, width='stretch')

    with treino_exec_tab:

        pure_nav_key = None
        pure_idx = 0
        if pure_workout_mode and bloco != "Fisio" and len(cfg.get("exercicios", [])) > 0:
            ex_names = [str(it.get("ex","")) for it in cfg["exercicios"]]
            pure_nav_key = f"pt_idx::{perfil_sel}::{st.session_state.get('plano_id_sel','Base')}::{dia}::{semana}"
            # AUTO-RESTORE: em mobile o browser pode suspender e a sessão do Streamlit recomeça (session_state limpa).
            # Se houver snapshot recente para este perfil/dia/plano/semana, restaura progresso e séries pendentes.
            try:
                _plano_active = str(st.session_state.get('plano_id_sel','Base'))
                _ip_key = st.session_state.get("_inprogress_session_key") or _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
                if not _pure_has_any_progress(perfil_sel, dia, len(cfg.get('exercicios', []))):
                    _payload = load_inprogress_session(_ip_key)
                    if isinstance(_payload, dict):
                        _apply_inprogress_payload(_payload, perfil_sel, dia, pure_nav_key)
                        try:
                            st.toast("Sessão restaurada ✅")
                        except Exception:
                            pass
            except Exception:
                pass


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
                # NÃO escrever diretamente no widget key depois do selectbox existir (StreamlitAPIException).
                # Em vez disso, agenda a sincronização para o próximo rerun.
                st.session_state[f"pt_pick_pending_{pure_nav_key}"] = _ix
                st.session_state["scroll_to_ex_nav"] = True

            _pick_key = f"pt_pick_{pure_nav_key}"
            _pick_pending_key = f"pt_pick_pending_{pure_nav_key}"
            if _pick_pending_key in st.session_state:
                try:
                    st.session_state[_pick_key] = int(st.session_state.get(_pick_pending_key, pure_idx))
                except Exception:
                    st.session_state[_pick_key] = int(pure_idx)
                try:
                    del st.session_state[_pick_pending_key]
                except Exception:
                    pass
            else:
                st.session_state.setdefault(_pick_key, pure_idx)
                # sincronização segura ANTES do widget ser instanciado neste rerun
                try:
                    st.session_state[_pick_key] = int(st.session_state.get(pure_nav_key, pure_idx))
                except Exception:
                    st.session_state[_pick_key] = int(pure_idx)

            _done_ex = 0
            for _ix, _it in enumerate(cfg["exercicios"]):
                _done_key = f"pt_done::{perfil_sel}::{dia}::{_ix}"
                try:
                    _done_val = int(st.session_state.get(_done_key, 0) or 0)
                except Exception:
                    _done_val = 0
                if _done_val >= int(_it.get("series", 0) or 0):
                    _done_ex += 1

            _prep_blocks = _cfg_prep_blocks(cfg)
            _post_blocks = _cfg_post_blocks(cfg, prot)
            _flow_items, _flow_done, _flow_total, _flow_pending = _session_flow_stats(cfg, prot, perfil_sel, dia)
            _prep_pending = any(not bool(st.session_state.get(_session_block_state_key(_b), False)) for _b in _prep_blocks)
            _all_ex_done = (_done_ex >= len(cfg["exercicios"])) if len(cfg.get("exercicios", [])) > 0 else True
            _post_pending = _all_ex_done and any(not bool(st.session_state.get(_session_block_state_key(_b), False)) for _b in _post_blocks)

            st.markdown(
                "<div class='bc-prep-head'>"
                "<div class='bc-prep-title'>Fluxo da sessão</div>"
                "<div class='bc-prep-sub'>Preparação, treino principal e fecho da sessão sem deixar peças soltas pelo chão.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            if _flow_pending is not None and 0 <= int(_flow_pending) < len(_flow_items):
                _next_item = _flow_items[int(_flow_pending)]
                _next_title = str(_next_item.get("title", "Próximo passo") or "Próximo passo")
                _next_phase = "Preparação" if (str(_next_item.get("kind", "")) == "block" and str(_next_item.get("phase", "")) == "prep") else ("Fecho da sessão" if str(_next_item.get("kind", "")) == "block" else "Exercício atual")
            else:
                _next_title = "Sessão completa"
                _next_phase = "Treino pronto"
            st.markdown(
                f"<div class='bc-last-chip'><span><b>{html.escape(_next_phase)}</b></span><span class='bc-lastset'>{html.escape(_next_title)}</span></div>",
                unsafe_allow_html=True,
            )
            render_progress_compact(_flow_done, _flow_total)

            if _prep_pending:
                for _b in _prep_blocks:
                    _render_session_block({**dict(_b), "phase": "prep"})
                st.info("Conclui a preparação para desbloquear o treino principal.")
            else:
                st.markdown("<div id='exercise-nav-anchor'></div>", unsafe_allow_html=True)
            _opt_ix = list(range(len(ex_names)))
            _sel_ix = st.selectbox(
                "Exercício atual",
                options=_opt_ix,
                index=int(max(0, min(max_idx, pure_idx))),
                key=_pick_key,
                format_func=lambda _x: _format_ex_select_label(cfg['exercicios'][int(_x)], int(_x), len(ex_names), bloco=str(bloco), semana=int(semana)),
                label_visibility="collapsed",
            )
            try:
                _sel_ix = int(_sel_ix)
            except Exception:
                _sel_ix = int(pure_idx)
            _sel_ix = max(0, min(max_idx, _sel_ix))
            if _sel_ix != int(st.session_state.get(pure_nav_key, pure_idx)):
                st.session_state[pure_nav_key] = _sel_ix
                pure_idx = _sel_ix
                st.session_state["scroll_to_ex_nav"] = True
            else:
                pure_idx = max(0, min(max_idx, int(st.session_state.get(pure_nav_key, pure_idx))))
                st.session_state[pure_nav_key] = pure_idx
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
            _status_left = f"Ex {pure_idx+1}/{len(ex_names)}"
            _status_mid = html.escape(ex_names[pure_idx])
            _status_right = serie_txt
            if _post_pending and _post_blocks:
                _post_open = next((b for b in _post_blocks if not bool(st.session_state.get(_session_block_state_key(b), False))), _post_blocks[0])
                _status_left = "Fecho"
                _status_mid = html.escape(str(_post_open.get("title", "Bloco final") or "Bloco final"))
                _status_right = "Obrigatório"
            st.markdown(f"""
            <div class='bc-float-bar bc-float-status'>
              <b style='color:#E8E2E2;'>{_status_left}</b> · {_status_mid} · {_status_right}
            </div>
            """, unsafe_allow_html=True)

        def _get_req_state_from_session():
            _present_keys = set()
            try:
                for _blk in list(_cfg_prep_blocks(cfg)) + list(_cfg_post_blocks(cfg, prot)):
                    _k = str(_blk.get("key", "") or "").strip().lower()
                    if _k:
                        _present_keys.add(_k)
            except Exception:
                _present_keys = set()
            return {
                "aquecimento_req": "aquecimento" in _present_keys,
                "mobilidade_req": "mobilidade" in _present_keys,
                "cardio_req": "cardio" in _present_keys,
                "tendoes_req": "tendoes" in _present_keys,
                "core_req": "core" in _present_keys,
                "cooldown_req": "cooldown" in _present_keys,
                "aquecimento": bool(st.session_state.get("chk_aquecimento", False)),
                "mobilidade": bool(st.session_state.get("chk_mobilidade", False)),
                "cardio": bool(st.session_state.get("chk_cardio", False)),
                "tendoes": bool(st.session_state.get("chk_tendoes", False)),
                "core": bool(st.session_state.get("chk_core", False)),
                "cooldown": bool(st.session_state.get("chk_cooldown", False)),
            }

        req = _get_req_state_from_session()
        justificativa = ""
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
            st.subheader(f"🏠 {cfg.get('recovery_title', 'Recuperação / mobilidade')}")
            _rec_items = [str(x).strip() for x in list(cfg.get('recovery_items', []) or []) if str(x).strip()]
            if _rec_items:
                for _rit in _rec_items:
                    st.markdown(f"- {_rit}")
            else:
                st.markdown("Caminhada leve + mobilidade.")
            _rec_note = str(cfg.get('recovery_note', '') or '').strip()
            if _rec_note:
                st.caption(_rec_note)
        else:

            if bloco in ["Força","Hipertrofia"]:
                if semana in [2,6]:
                    st.info("Progressão: +1 rep por série OU +2,5–5% carga mantendo o RIR alvo.")
                if semana in [4,8]:
                    st.warning("DELOAD: menos séries e mais leve. Técnica e tendões em 1º lugar.")
            elif bloco in GUI_BLOCOS:
                if is_gui_deload_week(semana):
                    st.warning("DELOAD GUI: ~50–60% das séries, -10 a -15% carga, sem drop e sem mini-sets.")
                elif semana >= 7:
                    st.info("Gui: repetição do mesociclo (semanas 7–11). Tenta +2,5 kg ou +1–2 reps mantendo RIR 2.")
                else:
                    st.info("Gui: progressão semanal da sheet (Mesociclos 1→5). Mantém descanso 60–90s e RIR 2.")
            df_now = df_all.copy() if isinstance(df_all, pd.DataFrame) else get_data()
            for i,item in enumerate(cfg["exercicios"]):
                if pure_workout_mode and pure_nav_key is not None and (_prep_pending or _post_pending or i != pure_idx):
                    continue
                ex = item["ex"]
                rir_target_str = item["rir_alvo"]
                rir_target_num = rir_alvo_num(item["tipo"], bloco, semana)

                df_last, peso_medio, rir_medio, data_ultima = get_historico_detalhado(df_now, perfil_sel, ex)

                passo_up = 0.05 if ("Deadlift" in ex or "Leg Press" in ex or "Hip Thrust" in ex) else 0.025
                plano_atual_id = str(st.session_state.get('plano_id_sel', 'Base'))
                yami = yami_coach_sugestao(df_now, perfil_sel, ex, item, bloco, semana, plano_atual_id)
                peso_sug = float(yami.get('peso_work_sugerido', yami.get('peso_sugerido', 0.0)) or 0.0)
                if peso_sug <= 0:
                    peso_sug = sugerir_carga(peso_medio, rir_medio, float(yami.get('rir_alvo', rir_target_num) or rir_target_num), passo_up, 0.05)

                # RIR esperado hoje (alvo ajustado por prontidão/sinais/estilo/controlo)
                try:
                    rir_expect = float(yami.get('rir_alvo', rir_target_num) or rir_target_num) if isinstance(yami, dict) else float(rir_target_num)
                except Exception:
                    rir_expect = float(rir_target_num)
                try:
                    rir_expect = max(0.0, min(6.0, float(round(float(rir_expect) * 2.0) / 2.0)))
                except Exception:
                    rir_expect = float(rir_target_num)

                rep_info_ui = _parse_rep_scheme(str(item.get("reps", "")), int(item.get("series", 0) or 0))
                reps_low = int(rep_info_ui.get("low") or 0) or 8
                reps_high = int(rep_info_ui.get("high") or 0) or reps_low
                reps_default = int(reps_high) if int(reps_high) > 0 else int(reps_low)


                with st.expander(_exercise_ui_label(item, i), expanded=(i==0 or (pure_workout_mode and pure_nav_key is not None and i == pure_idx))):
                    if pure_workout_mode and pure_nav_key is not None and i == pure_idx:
                        st.markdown("<div id='exercise-current-anchor'></div>", unsafe_allow_html=True)
                    series_txt = str(item.get('series',''))
                    reps_txt = str(item.get('reps',''))
                    _group_lbl = _exercise_group_label(item)
                    meta_line = f"🎯 Meta: {series_txt}×{reps_txt}  •  RIR esperado: {rir_target_str}" + (f"  •  {_group_lbl}" if _group_lbl else "")
                    st.markdown(
                        f"""<div class='bc-meta-card'>
      <div class='bc-meta-top'>{html.escape(meta_line)}</div>
    </div>""",
                        unsafe_allow_html=True
                    )

                    _pair_note = _exercise_pair_note(item)
                    if _pair_note:
                        st.caption(f"↔ {_pair_note}")
                    _superset_note = _superset_execution_note(cfg, perfil_sel, dia, i)
                    if _superset_note:
                        st.info(f"🔁 {_superset_note}")

                    if isinstance(yami, dict) and yami:
                        _y_action = str(yami.get('acao', 'Mantém carga'))
                        _y_resumo = str(yami.get('resumo', '') or '')
                        _ya = _y_action.lower()
                        if "deload" in _ya:
                            _y_cls = "y-deload"
                        elif ("+" in _ya) or ("sobe" in _ya):
                            _y_cls = "y-up"
                        elif ("baixa" in _ya) or ("reduz" in _ya):
                            _y_cls = "y-down"
                        else:
                            _y_cls = "y-hold"
                        ycol1, ycol2 = st.columns([4.8, 1.7], gap="small")
                        _y_conf = str(yami.get('confianca', 'média') or 'média')
                        _y_pq = str(yami.get('porque', '') or '')
                        with ycol1:
                            _pq_html = html.escape(_y_pq) if _y_pq else ""
                            _res_html = html.escape(str(_y_resumo or "")) if _y_resumo else ""
                            _mid = (f"{_pq_html} · " if _pq_html else "")
                            st.markdown(
                                f"<div class='bc-yami-chip {_y_cls}'>🧠 <b>Yami</b> — {_y_action} <span class='muted' style='font-weight:700;'>({_y_conf})</span><br><span class='muted'>{_mid}{_res_html}</span></div>",
                                unsafe_allow_html=True
                            )
                        with ycol2:
                            with st.popover("🧠 Yami explica", width="stretch"):
                                st.markdown(f"**Sugestão do Yami:** {_y_action}")
                                try:
                                    st.caption(
                                        f"Prontidão: {yami.get('readiness','Normal')} · RIR esperado: {float(yami.get('rir_alvo', rir_target_num) or rir_target_num):.1f}" + (f" · Sinais: {', '.join(list(yami.get('signals', []) or []))}" if (yami.get('signals') if isinstance(yami, dict) else None) else "")
                                    )
                                except Exception:
                                    pass
                                if bool(yami.get('deload_reco', False)):
                                    st.warning("Yami: deload recomendado (1 semana) para baixar fadiga e voltar a progredir.")

                                _py = float(yami.get('peso_sugerido', 0) or 0)
                                if _py > 0:
                                    st.caption(f"Carga sugerida: {_py:.1f} kg · Confiança: {yami.get('confianca', 'média')}")
                                    try:
                                        _prof = _yami_weight_profile_for_item(ex, item, float(_py), df_last)
                                    except Exception:
                                        _prof = []
                                    if _prof:
                                        _prof_txt = ' · '.join([f"S{ix+1}:{float(w):.1f}" for ix,w in enumerate(_prof)])
                                        st.caption(f"Por série: {_prof_txt}")
                                else:
                                    st.caption(f"Confiança: {yami.get('confianca', 'média')}")
                                # Plano (Top set + Back-off) — opcional, só aparece quando há base
                                try:
                                    _pl = yami.get('plan', {}) if isinstance(yami, dict) else {}
                                    if isinstance(_pl, dict) and _pl:
                                        _ts = _pl.get('top_set', {}) or {}
                                        _bo = _pl.get('backoff', {}) or {}

                                        try:
                                            _ts_w = float(_ts.get('peso', 0) or 0)
                                        except Exception:
                                            _ts_w = 0.0
                                        _ts_reps = _ts.get('reps', None)
                                        try:
                                            _ts_rir = float(_ts.get('rir', 0) or 0)
                                        except Exception:
                                            _ts_rir = None

                                        if _ts_w > 0:
                                            _ts_reps_txt = f"{int(_ts_reps)} reps" if _ts_reps is not None else "reps alvo"
                                            _ts_rir_txt = f"RIR {_ts_rir:.1f}" if _ts_rir is not None else ""
                                            st.markdown(f"**Plano:** Top set ~{_ts_w:.1f} kg · {_ts_reps_txt} · {_ts_rir_txt}".strip())

                                        try:
                                            _bo_sets = int(_bo.get('sets', 0) or 0)
                                        except Exception:
                                            _bo_sets = 0
                                        try:
                                            _bo_w = float(_bo.get('peso', 0) or 0) if _bo.get('peso', None) is not None else 0.0
                                        except Exception:
                                            _bo_w = 0.0
                                        try:
                                            _drop_pct = float(_bo.get('drop_pct', 0) or 0)
                                        except Exception:
                                            _drop_pct = 0.0

                                        if _bo_sets > 0 and _bo_w > 0:
                                            st.caption(f"Back-off: {_bo_sets}× ~{_bo_w:.1f} kg (drop ~{_drop_pct*100:.0f}%).")

                                        _rule = str(_pl.get('rule', '') or '').strip()
                                        if _rule:
                                            st.caption(_rule)
                                except Exception:
                                    pass
                                for _r in list(yami.get('razoes', []) or []):
                                    st.markdown(f"- {_r}")

                    _last_chip = _latest_set_summary_from_df_last(df_last)
                    if _last_chip:
                        _tempo = str(item.get("tempo", "") or "").strip()
                        try:
                            _descanso_s = int(item.get("descanso_s", 0) or 0)
                        except Exception:
                            _descanso_s = 0
                        _tempo_parts = []
                        if _tempo:
                            _tempo_parts.append(f"⏱️ Tempo {_tempo}")
                        if _descanso_s > 0:
                            _tempo_parts.append(f"Descanso ~{_descanso_s}s")
                        _tempo_txt = " · ".join(_tempo_parts)
                        if _tempo_txt:
                            st.markdown(
                                f"<div class='bc-last-chip'>"
                                f"<span class='bc-lastset'>⏮️ {html.escape(str(_last_chip))}</span>"
                                f"<span class='bc-tempo'>{html.escape(_tempo_txt)}</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f"<div class='bc-last-chip'><span class='bc-lastset'>⏮️ {html.escape(str(_last_chip))}</span></div>",
                                unsafe_allow_html=True,
                            )

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

                    art = sugestao_articular(ex)
                    if art:
                        st.warning(art)
                    if item.get("nota_semana"):
                        st.info(item["nota_semana"])

                    ui_compact = bool(st.session_state.get("ui_compact_mode", True))
                    ui_show_last_table = bool(st.session_state.get("ui_show_last_table", False))

                    def _render_ultimo_registo_block():
                        if df_last is not None:
                            st.markdown(f"📜 **Último registo ({data_ultima})**")
                            _peso_lbl = "kg/lado" if _is_per_side_exercise(ex) else "kg"
                            st.caption(f"Último: peso médio ~ {peso_medio:.1f} {_peso_lbl} | RIR médio ~ {rir_medio:.1f}")
                            if (not ui_compact) or ui_show_last_table:
                                st.dataframe(df_last, hide_index=True, width='stretch')
                        else:
                            st.caption("Sem registos anteriores para este exercício (neste perfil).")

                    def _render_prefill_buttons_block():
                        p1, p2 = st.columns(2)
                        if p1.button("↺ Usar último", key=f"pref_last_{i}", width='stretch'):
                            _prefill_sets_from_last(i, item, df_last, peso_sug, reps_default, rir_expect, use_df_exact=True)
                            st.rerun()
                        if p2.button("🎯 Usar sugestão do Yami", key=f"pref_sug_{i}", width='stretch'):
                            _prefill_sets_from_last(i, item, df_last, peso_sug, reps_default, rir_expect, use_df_exact=False)
                            st.rerun()
                        if pure_workout_mode and pure_nav_key is not None:
                            series_key = f"pt_sets::{perfil_sel}::{dia}::{i}"
                            done_key = f"pt_done::{perfil_sel}::{dia}::{i}"
                            if st.button("↺ Reset séries", key=f"pt_reset_{i}", width='stretch'):
                                st.session_state[series_key] = []
                                st.session_state[done_key] = 0
                                # snapshot (para não perder estado em mobile)
                                try:
                                    _plano_active = str(st.session_state.get('plano_id_sel','Base'))
                                    _ip_key = _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
                                    _payload = _build_inprogress_payload(perfil_sel, dia, _plano_active, int(semana), pure_nav_key, len(cfg.get('exercicios', [])))
                                    save_inprogress_session(_ip_key, _payload)
                                except Exception:
                                    pass
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
                            _apply_prefill_payload_if_any(i)
                            kg_step = 5.0 if _is_lower_exercise(ex) else 2.5
                            s = current_s
                            with st.form(key=f"form_pure_{i}_{s}"):
                                st.markdown(f"### Série {s+1}/{total_series}")
                                default_peso = _yami_suggest_weight_for_series(ex, item, float(peso_sug), df_last, pending_sets, s, float(rir_expect))
                                if default_peso <= 0 and pending_sets:
                                    try:
                                        default_peso = float(pending_sets[-1].get("peso", default_peso) or default_peso)
                                    except Exception:
                                        pass
                                peso = st.number_input(
                                    _peso_label_para_ex(ex, s), min_value=0.0,
                                    value=float(default_peso), step=float(kg_step), key=f"peso_{i}_{s}"
                                )
                                rcol1, rcol2 = st.columns(2)
                                reps = rcol1.number_input(
                                    f"Reps • S{s+1}", min_value=0, value=int(reps_default), step=1, key=f"reps_{i}_{s}"
                                )
                                rir = rcol2.number_input(
                                    f"RIR (esp. {rir_expect:.1f}) • S{s+1}", min_value=0.0, max_value=6.0,
                                    value=float(rir_expect), step=0.5, key=f"rir_{i}_{s}"
                                )

                                is_last = (s == total_series - 1)
                                is_last_ex = (i == len(cfg["exercicios"]) - 1)
                                _nav_preview = _superset_nav_after_set(
                                    cfg, perfil_sel, dia, i,
                                    overrides={int(i): int(current_s + 1)}
                                )
                                if bool(_nav_preview.get("is_superset", False)):
                                    _next_preview_ix = int(_nav_preview.get("next_ix", i) or i)
                                    _next_preview_label = str(cfg["exercicios"][_next_preview_ix].get("ex", "Exercício") or "Exercício") if 0 <= _next_preview_ix < len(cfg.get("exercicios", [])) else "Exercício"
                                    if bool(_nav_preview.get("group_complete", False)):
                                        if _next_preview_ix > i:
                                            btn_label = "Próximo exercício"
                                            _btn_kind = "exercise"
                                        else:
                                            btn_label = "🏁 Terminar treino"
                                            _btn_kind = "finish"
                                    else:
                                        btn_label = f"Próximo do superset · {_next_preview_label}"
                                        _btn_kind = "series"
                                elif not is_last:
                                    btn_label = "Próxima série"
                                    _btn_kind = "series"
                                elif not is_last_ex:
                                    btn_label = "Próximo exercício"
                                    _btn_kind = "exercise"
                                else:
                                    btn_label = "🏁 Terminar treino"
                                    _btn_kind = "finish"
                            
                                # estilo do botão (cores por contexto)
                                try:
                                    if _btn_kind == "series":
                                        _bg, _fg, _bd = "#0B3D2E", "#FFFFFF", "#0B3D2E"
                                        _hover_css = "filter: brightness(1.08);"
                                    elif _btn_kind == "exercise":
                                        _bg, _fg, _bd = "#5B2B82", "#FFFFFF", "#5B2B82"
                                        _hover_css = "filter: brightness(1.08);"
                                    else:
                                        _bg, _fg, _bd = "transparent", "#FF3B30", "#FF3B30"
                                        _hover_css = "background-color: rgba(255, 59, 48, 0.10);"
                                    st.markdown(f"""
                                    <style>
                                    div[data-testid=\"stMarkdownContainer\"]:has(span.bc-nextbtn-marker) + div[data-testid=\"stFormSubmitButton\"] button {
                                        background-color: {_bg} !important;
                                        color: {_fg} !important;
                                        border: 1px solid {_bd} !important;
                                    }
                                    div[data-testid=\"stMarkdownContainer\"]:has(span.bc-nextbtn-marker) + div[data-testid=\"stFormSubmitButton\"] button:hover {
                                        {_hover_css}
                                    }
                                    </style>
                                    <span class=\"bc-nextbtn-marker\"></span>
                                    """, unsafe_allow_html=True)
                                except Exception:
                                    pass
                            
                                submitted = st.form_submit_button(btn_label, width='stretch')
                                if submitted:
                                    novos_sets = list(pending_sets) + [{"peso": peso, "reps": reps, "rir": rir}]
                                    st.session_state[series_key] = novos_sets
                                    st.session_state[f"rest_{i}"] = int(item["descanso_s"])

                                    # snapshot (para não perder estado em mobile)
                                    try:
                                        _plano_active = str(st.session_state.get('plano_id_sel','Base'))
                                        _ip_key = _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
                                        _payload = _build_inprogress_payload(perfil_sel, dia, _plano_active, int(semana), pure_nav_key, len(cfg.get('exercicios', [])))
                                        save_inprogress_session(_ip_key, _payload)
                                    except Exception:
                                        pass

                                    _nav_after = _superset_nav_after_set(
                                        cfg, perfil_sel, dia, i,
                                        overrides={int(i): int(len(novos_sets))}
                                    )
                                    _current_complete = bool(_nav_after.get("current_complete", False)) if bool(_nav_after.get("is_superset", False)) else bool(is_last)
                                    _group_complete = bool(_nav_after.get("group_complete", False)) if bool(_nav_after.get("is_superset", False)) else bool(is_last)
                                    _next_ix_after = int(_nav_after.get("next_ix", min(len(cfg["exercicios"]) - 1, i + 1)) or min(len(cfg["exercicios"]) - 1, i + 1))

                                    if _current_complete:
                                        ok_gravou = salvar_sets_agrupados(perfil_sel, dia, bloco, ex, novos_sets, req, justificativa)
                                        if ok_gravou:
                                            st.session_state[series_key] = []
                                            try:
                                                st.session_state[f"pt_done::{perfil_sel}::{dia}::{i}"] = int(item["series"])
                                            except Exception:
                                                pass

                                    # descanso definido pelo Yami para a PRÓXIMA ronda/série
                                    try:
                                        _prev_reps = int(novos_sets[-2]['reps']) if len(novos_sets) >= 2 else None
                                    except Exception:
                                        _prev_reps = None
                                    _rir_eff = float(rir) if rir is not None else None

                                    _rest_yami = yami_definir_descanso_s(
                                        int(item.get('descanso_s', 75)),
                                        _rir_eff, float(rir_expect),
                                        int(reps), reps_low, (lambda _ri: int(_ri.get('high') or 0) if str(_ri.get('kind') or '') in ('range','fixed','fixed_seq') else None)(_parse_rep_scheme(item.get('reps',''), int(item.get('series',0) or 0))),
                                        _prev_reps,
                                        is_composto=(str(item.get('tipo','')).lower()=='composto')
                                    )

                                    if _current_complete:
                                        try:
                                            _plano_active = str(st.session_state.get('plano_id_sel','Base'))
                                            _ip_key = _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
                                            _payload = _build_inprogress_payload(perfil_sel, dia, _plano_active, int(semana), pure_nav_key, len(cfg.get('exercicios', [])))
                                            save_inprogress_session(_ip_key, _payload)
                                        except Exception:
                                            pass

                                    if bool(_nav_after.get("is_superset", False)):
                                        if _group_complete:
                                            if _next_ix_after > i:
                                                _set_pure_idx(_next_ix_after)
                                                st.success("Superset concluído. A seguir…")
                                            else:
                                                if _post_blocks:
                                                    st.success("Último exercício guardado. Falta fechar a sessão com os blocos finais ✅")
                                                else:
                                                    st.session_state["session_finished_flash"] = True
                                                    st.success("Último exercício guardado. Sessão pronta ✅")
                                        else:
                                            if bool(_nav_after.get("queue_rest", False)):
                                                _queue_auto_rest(int(_rest_yami), str(_exercise_group_label(item) or ex))
                                                try:
                                                    st.toast(f"🔁 Superset: descansa {_rest_yami}s e volta à próxima ronda.")
                                                except Exception:
                                                    pass
                                            else:
                                                try:
                                                    _next_name = str(cfg["exercicios"][_next_ix_after].get("ex", "Exercício") or "Exercício")
                                                    st.toast(f"🔁 Superset: segue para {_next_name} sem pausa.")
                                                except Exception:
                                                    pass
                                            _set_pure_idx(_next_ix_after)

                                    elif _current_complete:
                                        if is_last_ex:
                                            if _post_blocks:
                                                st.success("Último exercício guardado. Falta fechar a sessão com os blocos finais ✅")
                                            else:
                                                st.session_state["session_finished_flash"] = True
                                                st.success("Último exercício guardado. Sessão pronta ✅")
                                        else:
                                            _set_pure_idx(min(len(cfg["exercicios"]) - 1, i + 1))
                                            st.success("Exercício guardado. A seguir…")
                                    else:
                                        _queue_auto_rest(int(_rest_yami), ex)
                                        try:
                                            # comentário curto "ao vivo" (Yami)
                                            if (_rir_eff is not None) and float(_rir_eff) <= max(0.5, float(rir_expect) - 1.0):
                                                st.toast(f"🧠 Yami: Descansa {_rest_yami}s. Isso foi pesado — limpa a próxima.")
                                            elif (_rir_eff is not None) and float(_rir_eff) >= float(rir_expect) + 1.0:
                                                st.toast(f"🧠 Yami: Descansa {_rest_yami}s. Estava folgado — prepara-te para subir.")
                                            else:
                                                st.toast(f"🧠 Yami: Descansa {_rest_yami}s. Mantém a lâmina afiada.")
                                        except Exception:
                                            pass

                                        # Política de falha (aviso rápido em compostos)
                                        try:
                                            if (str(item.get('tipo','')).lower() == 'composto') and (_rir_eff is not None) and float(_rir_eff) <= 0.5:
                                                st.toast("⚠️ Yami: isso foi à falha/quase. Em compostos, mantém 1–3 RIR para técnica e recuperação.")
                                        except Exception:
                                            pass

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
                                        if _post_blocks:
                                            st.success("Último exercício guardado. Falta fechar a sessão com os blocos finais ✅")
                                        else:
                                            st.session_state["session_finished_flash"] = True
                                            st.success("Último exercício guardado. Sessão pronta ✅")
                                    else:
                                        _set_pure_idx(min(len(cfg["exercicios"]) - 1, i + 1))
                                        st.success("Exercício guardado. A seguir…")
                                
                                    try:
                                        _plano_active = str(st.session_state.get('plano_id_sel','Base'))
                                        _ip_key = _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
                                        _payload = _build_inprogress_payload(perfil_sel, dia, _plano_active, int(semana), pure_nav_key, len(cfg.get('exercicios', [])))
                                        save_inprogress_session(_ip_key, _payload)
                                    except Exception:
                                        pass

                                    time.sleep(0.35)
                                    st.rerun()

                        st.markdown("<div style='margin-top:.35rem'></div>", unsafe_allow_html=True)
                        _render_prefill_buttons_block()
                        st.markdown("<div style='margin-top:.2rem'></div>", unsafe_allow_html=True)
                        _render_ultimo_registo_block()
                    else:
                        lista_sets = []
                        _apply_prefill_payload_if_any(i)
                        with st.form(key=f"form_{i}"):
                            kg_step = 5.0 if _is_lower_exercise(ex) else 2.5
                            for s in range(item["series"]):
                                st.markdown(f"### Série {s+1}")
                                peso = st.number_input(_peso_label_para_ex(ex, s), min_value=0.0,
                                                       value=float(peso_sug) if peso_sug>0 else 0.0,
                                                       step=float(kg_step), key=f"peso_{i}_{s}")
                                rcol1, rcol2 = st.columns(2)
                                reps = rcol1.number_input(f"Reps • S{s+1}", min_value=0, value=int(reps_default),
                                                          step=1, key=f"reps_{i}_{s}")
                                rir = rcol2.number_input(f"RIR (esp. {rir_expect:.1f}) • S{s+1}", min_value=0.0, max_value=6.0,
                                                         value=float(rir_expect), step=0.5, key=f"rir_{i}_{s}")
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

                        st.markdown("<div style='margin-top:.35rem'></div>", unsafe_allow_html=True)
                        _render_prefill_buttons_block()
                        st.markdown("<div style='margin-top:.2rem'></div>", unsafe_allow_html=True)
                        _render_ultimo_registo_block()

            pass  # divider removed

            if _all_ex_done and _post_blocks:
                st.markdown(
                    "<div class='bc-prep-head'>"
                    "<div class='bc-prep-title'>Fecho da sessão</div>"
                    "<div class='bc-prep-sub'>Fecha a sessão com o que falta. Não estragues um treino bom por preguiça no último quilómetro.</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                for _b in _post_blocks:
                    _render_session_block({**dict(_b), "phase": "finish"})

            req = _get_req_state_from_session()
            justificativa = ""
            xp_pre, ok_checklist = checklist_xp(req, justificativa="")

            df_now = get_data()
            streak_atual = get_last_streak(df_now, perfil_sel)

            m1,m2,m3 = st.columns(3)
            m1.metric("XP previsto", f"{xp_pre}")
            m2.metric("Checklist", "✅ Completo" if ok_checklist else "⚠️ Incompleto")
            m3.metric("Streak", f"{streak_atual}")

            _flow_items_final, _flow_done_final, _flow_total_final, _flow_pending_final = _session_flow_stats(cfg, prot, perfil_sel, dia)
            _done_ex_final = 0
            for _ix, _it in enumerate(cfg.get("exercicios", [])):
                try:
                    _dv = int(st.session_state.get(f"pt_done::{perfil_sel}::{dia}::{_ix}", 0) or 0)
                except Exception:
                    _dv = 0
                if _dv >= int(_it.get("series", 0) or 0):
                    _done_ex_final += 1
            _total_ex_final = len(cfg.get("exercicios", []))
            _all_done = (_flow_total_final > 0 and _flow_done_final >= _flow_total_final)
            if _all_done:
                st.markdown(
                    f"""
                    <div class='bc-final-summary'>
                      <div class='ttl'>✅ Sessão pronta</div>
                      <div class='sub'>Fluxo concluído: <b>{_flow_done_final}/{_flow_total_final}</b> · Exercícios: <b>{_done_ex_final}/{_total_ex_final}</b> · Sessão alvo: <b>{html.escape(str(_sessao_alvo))}</b> · XP previsto: <b>{xp_pre}</b></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if bool(st.session_state.pop("session_finished_flash", False)):
                    st.toast("Sessão concluída ✅")
            elif _all_ex_done and _post_blocks:
                st.info("Exercícios feitos. Fecha a sessão com os blocos finais obrigatórios.")

            req_keys = [k for k in ["aquecimento","mobilidade","cardio","tendoes","core","cooldown"] if req.get(f"{k}_req", False)]
            done_req = sum(1 for k in req_keys if req.get(k, False))
            total_req = max(1, len(req_keys))
            st.progress(done_req/total_req, text=f"Checklist obrigatório: {done_req}/{total_req}")

            try:
                if pure_workout_mode and pure_nav_key is not None:
                    _plano_active = str(st.session_state.get('plano_id_sel', 'Base'))
                    _ip_key = _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
                    _has_any_mark = _pure_has_any_progress(perfil_sel, dia, len(cfg.get('exercicios', []))) or any(bool(req.get(_k, False)) for _k in ["aquecimento", "mobilidade", "cardio", "tendoes", "core", "cooldown"])
                    if _all_done:
                        clear_inprogress_session(_ip_key)
                    elif _has_any_mark:
                        _payload = _build_inprogress_payload(perfil_sel, dia, _plano_active, int(semana), pure_nav_key, len(cfg.get('exercicios', [])))
                        save_inprogress_session(_ip_key, _payload)
            except Exception:
                pass

            _finish_label = "🏁 Terminar sessão" if not _all_done else "🏁 Terminar sessão (concluída)"
        
            # estilo: Terminar treino (vermelho)
            try:
                st.markdown("""
                <style>
                div[data-testid=\"stMarkdownContainer\"]:has(span.bc-finishbtn-marker) + div[data-testid=\"stButton\"] button {
                    background-color: transparent !important;
                    color: #FF3B30 !important;
                    border: 1px solid #FF3B30 !important;
                }
                div[data-testid=\"stMarkdownContainer\"]:has(span.bc-finishbtn-marker) + div[data-testid=\"stButton\"] button:hover {
                    background-color: rgba(255, 59, 48, 0.10) !important;
                }
                </style>
                <span class=\"bc-finishbtn-marker\"></span>
                """, unsafe_allow_html=True)
            except Exception:
                pass

            if st.button(_finish_label, disabled=(not _all_done)):
                try:
                    _plano_active = str(st.session_state.get('plano_id_sel','Base'))
                    _ip_key = _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
                    clear_inprogress_session(_ip_key)
                except Exception:
                    pass
                st.balloons()
                time.sleep(1.0)
                st.rerun()

            st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
            st.markdown("---")
            _rst_flag = f"reset_treino_confirm::{perfil_sel}::{dia}"
            if not bool(st.session_state.get(_rst_flag, False)):
                if st.button("🧨 Reset treino", key=f"reset_treino_btn::{perfil_sel}::{dia}", width='stretch'):
                    st.session_state[_rst_flag] = True
                    st.rerun()
            else:
                st.warning("Isto vai reiniciar o progresso do treino atual (volta a 0/7).")
                cr1, cr2 = st.columns(2)
                if cr1.button("✅ Confirmar reset", key=f"reset_treino_yes::{perfil_sel}::{dia}", width='stretch'):
                    # parar descanso automático (se estiver a correr)
                    st.session_state["rest_auto_run"] = False
                    # limpar progresso do treino em memória
                    try:
                        _nex = len(cfg.get("exercicios", []))
                    except Exception:
                        _nex = 0
                    for _ix in range(int(_nex)):
                        for _k in [f"pt_done::{perfil_sel}::{dia}::{_ix}", f"pt_sets::{perfil_sel}::{dia}::{_ix}", f"rest_{_ix}"]:
                            if _k in st.session_state:
                                del st.session_state[_k]
                    # limpar inputs (peso/reps/rir) para não reaparecerem valores antigos
                    try:
                        for _k in list(st.session_state.keys()):
                            if re.match(r"^(peso|reps|rir)_\d+_\d+$", str(_k)):
                                del st.session_state[_k]
                        for _k in ["chk_aquecimento", "chk_mobilidade", "chk_cardio", "chk_tendoes", "chk_core", "chk_cooldown", "rest_info_pending", "rest_auto_run", "session_finished_flash"]:
                            if _k in st.session_state:
                                del st.session_state[_k]
                    except Exception:
                        pass
                    # voltar ao 1º exercício
                    try:
                        _set_pure_idx(0)
                    except Exception:
                        try:
                            st.session_state.pop(f"pure_idx::{pure_nav_key}", None)
                        except Exception:
                            pass
                    # apagar snapshot persistido (mobile restore)
                    try:
                        _plano_active = str(st.session_state.get('plano_id_sel','Base'))
                        _ip_key = _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
                        clear_inprogress_session(_ip_key)
                    except Exception:
                        pass
                    st.session_state[_rst_flag] = False
                    st.toast("Treino reiniciado.")
                    time.sleep(0.25)
                    st.rerun()
                if cr2.button("Cancelar", key=f"reset_treino_no::{perfil_sel}::{dia}", width='stretch'):
                    st.session_state[_rst_flag] = False
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

        dfp = _ensure_exercise_key_column(dfp)
        dias_filtrados = st.multiselect("Dia", dias_opts, default=[])
        blocos_filtrados = st.multiselect("Bloco", blocos_opts, default=[])
        ex_label_map = _exercise_label_map(dfp)
        ex_opts = sorted(ex_label_map.keys(), key=lambda k: ex_label_map.get(k, k))
        ex_filtro = st.multiselect("Exercício", ex_opts, default=[], format_func=lambda k: ex_label_map.get(k, k))

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
            dfp = dfp[dfp["Exercício_Key"].astype(str).isin([str(x) for x in ex_filtro])]

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
            dfw_all = _ensure_exercise_key_column(dfw_all)
            dfw = _ensure_exercise_key_column(dfw)
            _hist_label_map = _exercise_label_map(dfw_all)
            best_hist = dfw_all.groupby("Exercício_Key")["1RM Estimado"].max()
            best_week = dfw.groupby("Exercício_Key")["1RM Estimado"].max()
            prs = []
            for ex_key, val_week in best_week.items():
                val_hist = float(best_hist.get(ex_key, 0))
                if val_week > 0 and abs(val_week - val_hist) < 1e-9:
                    prs.append((_hist_label_map.get(str(ex_key), str(ex_key)), val_week))
            if prs:
                st.success("Novos PRs detetados nesta semana:")
                st.dataframe(pd.DataFrame(prs, columns=["Exercício","1RM Estimado (PR)"]), hide_index=True, width='stretch')
            else:
                st.info("Sem PRs nesta semana.")

            pass  # divider removed

            st.subheader("📈 Progressão de Força (1RM Estimado)")
            lista_exercicios = sorted(_hist_label_map.keys(), key=lambda k: _hist_label_map.get(k, k))
            filtro_ex = st.selectbox("Escolhe um Exercício:", lista_exercicios, format_func=lambda k: _hist_label_map.get(k, k))
            df_chart = dfw_all[dfw_all["Exercício_Key"].astype(str) == str(filtro_ex)].copy()
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
