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
import math
import statistics
import json
from zoneinfo import ZoneInfo

# =========================================================
# ♣ BLACK CLOVER WORKOUT — RIR Edition (8 semanas + perfis)
# =========================================================

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
# --- UI theme knobs (ajusta facilmente) ---
BANNER_BLUR_PX = 1.5
BANNER_BRIGHTNESS = 1.5
CLOVER_OPACITY = 0.06

st.set_page_config(page_title="Black Clover Training APP", page_icon="♣️", layout="centered", initial_sidebar_state="expanded")

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
                        const txt = ((el.innerText || '') + '').replace(/\s+/g, '').trim();
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

    # RIR alvo: preferir campo do item; senão calcula pelo bloco/semana
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
.bc-rest-track{width:100%; height:10px; border-radius:999px; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.08); overflow:hidden; margin-top:6px; touch-action: none; overscroll-behavior: contain; user-select: none;}
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
  font-size: clamp(1.72rem, 5.1vw, 2.35rem);
  line-height: 1.05;
  letter-spacing: .02em;
  background: transparent !important;
}

.bc-main-title::after{
  content:"♣";
  position:absolute;
  right:-18px;
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

def _make_inprogress_key(perfil: str, plano_id: str, dia: str, semana: int, date_iso: str) -> str:
    return f"{perfil}||{plano_id}||{dia}||{int(semana)}||{date_iso}"

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
                    if ts and (now - ts) > 72*3600:
                        del store[k]
        except Exception:
            pass
        store[key] = payload
        _save_inprogress_store(store)
    except Exception:
        pass

def clear_inprogress_session(key: str) -> None:
    try:
        store = _load_inprogress_store()
        if key in store:
            del store[key]
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
    }
    for ix in range(int(n_ex)):
        dk = f"pt_done::{perfil}::{dia}::{ix}"
        sk = f"pt_sets::{perfil}::{dia}::{ix}"
        try:
            payload["pt_done"][str(ix)] = int(st.session_state.get(dk, 0) or 0)
        except Exception:
            payload["pt_done"][str(ix)] = 0
        sets = st.session_state.get(sk, [])
        payload["pt_sets"][str(ix)] = sets if isinstance(sets, list) else []
    return payload

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
    # contexto
    prof.setdefault("checkins", [])      # list[{date,...}]
    # IA "a sério"
    prof.setdefault("models", {})        # {ex: {mu, sigma2, n, last_key, last_dt, last_obs_e1rm}}
    prof.setdefault("patterns", {})      # {pattern: {mu, sigma2, n}}
    prof.setdefault("bandit", {})        # {ex: {arm: {a,b}}}
    prof.setdefault("obs_hist", {})      # {ex: list[{dt,e1rm,w,reps,rir_eff}]}
    return prof

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

def yami_adjust_rir_target(rir_base: float, item: dict) -> float:
    try:
        base = float(rir_base)
    except Exception:
        base = 2.0

    read = st.session_state.get("yami_readiness", {}) or {}
    try:
        base += float(read.get("adj_rir", 0.0) or 0.0)
    except Exception:
        pass

    # Política de falha: compostos sem falha → mínimo RIR 1
    if str(item.get("tipo", "")).lower() == "composto":
        base = max(1.0, base)

    base = max(0.0, min(6.0, base))
    return float(round(base * 2) / 2.0)


def yami_prontidao_latente(perfil: str, ex: str) -> dict:
    """Estima prontidão sem check-in, a partir dos resíduos recentes do modelo (EWMA).
    Não é magia: é só detectar se hoje estás acima/abaixo do esperado.
    Retorna ajustes pequenos (percentuais) para não destabilizar o plano.
    """
    try:
        stt = _yami_state_load()
        prof = stt.get("profiles", {}).get(str(perfil or "—"), {})
        model = (prof.get("models", {}) or {}).get(str(ex), {}) or {}
        zew = float(model.get("resid_z_ewma", 0.0) or 0.0)
    except Exception:
        zew = 0.0

    # zew < 0 => desempenho abaixo do esperado (dia "pior"); zew > 0 => acima
    adj_pct, score_delta, label = 0.0, 0.0, "latente: normal"
    if zew <= -1.0:
        adj_pct, score_delta, label = -0.02, -0.20, "latente: baixa"
    elif zew <= -0.5:
        adj_pct, score_delta, label = -0.01, -0.10, "latente: média-baixa"
    elif zew >= 1.0:
        adj_pct, score_delta, label = +0.01, +0.10, "latente: alta"
    elif zew >= 0.5:
        adj_pct, score_delta, label = +0.005, +0.05, "latente: boa"

    return {"adj_load_pct": float(adj_pct), "score_delta": float(score_delta), "label": str(label), "z": float(zew)}



# =========================================================
# YAMI IA — nível acima (modeloo + incerteza + multi-braço)
# Implementa 5 upgrades:
#  1) Kalman/e1RM com incerteza por exercício
#  4) Change-point (dia mau vs tendência)
#  7) "Embeddings" simples por padrão de movimento
#  6) Multi-braço (escolhe estratégia de progressão)
#  9) Explicação humana (LLM-like, sem depender de API)
# =========================================================

def yami_exercise_pattern(ex: str) -> str:
    exl = str(ex or "").lower()
    # padrões grossos (suficiente para transferir comportamento)
    if any(k in exl for k in ["agach", "squat", "hack", "leg press", "front squat", "belt squat"]):
        return "squat"
    if any(k in exl for k in ["deadlift", "rdl", "stiff", "good morning", "hip hinge"]):
        return "hinge"
    if any(k in exl for k in ["hip thrust", "glute bridge"]):
        return "glute"
    if any(k in exl for k in ["overhead", "ohp", "military", "shoulder press"]):
        return "push_vertical"
    if any(k in exl for k in ["supino", "bench", "press", "inclinado", "floor press", "push-up"]):
        return "push_horizontal"
    if any(k in exl for k in ["pull up", "pull-up", "chin", "lat pulldown", "pulldown", "barra fixa"]):
        return "pull_vertical"
    if any(k in exl for k in ["remada", "row", "seal row", "chest supported"]):
        return "pull_horizontal"
    if any(k in exl for k in ["lunge", "bulgar", "split squat", "step up"]):
        return "single_leg"
    if any(k in exl for k in ["curl", "tríceps", "triceps", "bíceps", "biceps", "extensão", "extension", "fly", "lateral raise", "elevação lateral"]):
        return "isolation"
    if any(k in exl for k in ["core", "ab", "abs", "plank"]):
        return "core"
    return "other"


def yami_e1rm_obs(w: float, reps: float, rir_eff: float) -> float:
    """e1RM heurístico (Epley) usando reps até à falha ~ reps + RIR efetivo."""
    try:
        w = float(w); reps = float(reps); rir_eff = float(rir_eff)
    except Exception:
        return 0.0
    if w <= 0 or reps <= 0:
        return 0.0
    rtf = max(1.0, reps + max(0.0, rir_eff))
    rtf = min(15.0, rtf)  # cap para evitar e1RM ridículo em reps altas
    return float(w) * (1.0 + (rtf / 30.0))


def _yami_model_get(perfil: str, ex: str) -> dict:
    prof = _yami_profile_state(perfil)
    models = prof.setdefault("models", {})
    return models.setdefault(str(ex), {})


def _yami_pattern_get(perfil: str, pattern: str) -> dict:
    prof = _yami_profile_state(perfil)
    pats = prof.setdefault("patterns", {})
    return pats.setdefault(str(pattern), {})


def _yami_model_init_if_missing(perfil: str, ex: str, init_e1rm: float | None = None) -> None:
    """Inicializa (se faltar) o filtro com prior do padrão de movimento."""
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    prof.setdefault("models", {})
    prof.setdefault("patterns", {})
    prof.setdefault("bandit", {})
    prof.setdefault("obs_hist", {})
    prof.setdefault("families", {})
    prof.setdefault("bases", {})
    prof.setdefault("clf", {})
    prof.setdefault("ctx_bandit", {})
    prof.setdefault("prefs", {})
    prof.setdefault("pain_model", {})
    prof.setdefault("day_clusters", {})
    prof.setdefault("latent", {})
    prof.setdefault("tech", {})
    prof.setdefault("audit", {})
    prof.setdefault("rir_err", {})

    ex = str(ex)
    model = prof["models"].setdefault(ex, {})
    if "mu" in model and "sigma2" in model:
        _yami_state_save(stt)
        return

    pat = yami_exercise_pattern(ex)
    pstate = prof["patterns"].setdefault(pat, {})
    mu0 = float(pstate.get("mu", 0.0) or 0.0)
    s20 = float(pstate.get("sigma2", 120.0) or 120.0)
    n0 = int(pstate.get("n", 0) or 0)

    if mu0 <= 0.0 and init_e1rm and float(init_e1rm) > 0:
        mu0 = float(init_e1rm)
        s20 = 120.0
        n0 = 0

    # a priori base se ainda não há nada
    if mu0 <= 0.0:
        mu0 = float(init_e1rm or 0.0)
    if mu0 <= 0.0:
        mu0 = 0.0

    model.setdefault("mu", float(mu0))
    model.setdefault("sigma2", float(max(40.0, s20)))
    model.setdefault("n", int(n0))
    model.setdefault("pattern", str(pat))
    model.setdefault("last_key", "")
    model.setdefault("last_dt", "")
    model.setdefault("last_obs_e1rm", 0.0)
    model.setdefault("obs_mult", 1.0)

    # multi-braço arms default
    b = prof["bandit"].setdefault(ex, {})
    for arm in ("micro_load", "add_rep", "hold"):
        st_arm = b.setdefault(arm, {})
        st_arm.setdefault("a", 2)  # a priori leve pró-sucesso
        st_arm.setdefault("b", 2)

    _yami_state_save(stt)


def yami_kalman_update(perfil: str, ex: str, obs: float, obs_var: float, process_var: float = 6.0) -> dict:
    """Atualiza o filtro de Kalman 1D (mu/sigma2) para e1RM do exercício."""
    _yami_model_init_if_missing(perfil, ex, init_e1rm=obs)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    model = prof.setdefault("models", {}).setdefault(str(ex), {})

    try:
        mu = float(model.get("mu", 0.0) or 0.0)
        s2 = float(model.get("sigma2", 120.0) or 120.0)
    except Exception:
        mu, s2 = 0.0, 120.0

    try:
        obs = float(obs)
        R0 = float(max(4.0, obs_var))
        Q = float(max(1.0, process_var))
        # ruído adaptativo: se as observações têm sido incoerentes, o Yami confia menos nelas
        try:
            mult = float(model.get("obs_mult", 1.0) or 1.0)
        except Exception:
            mult = 1.0
        mult = max(0.5, min(3.0, float(mult)))
        R = float(R0 * (mult ** 2))
    except Exception:
        obs, R, Q = 0.0, 20.0, 6.0

    # predict
    s2 = s2 + Q

    if obs > 0.0 and s2 > 0.0:
        # update
        S = (s2 + R)
        K = s2 / S
        resid = (obs - mu)
        mu = mu + K * resid
        s2 = (1.0 - K) * s2
        # aprende "confiabilidade" do input (RIR/reps variam muito? então aumenta ruído)
        try:
            z_signed = float(resid) / math.sqrt(max(1e-9, float(S)))
        except Exception:
            z_signed = 0.0
        z_abs = abs(float(z_signed))
        z_clip = max(0.5, min(3.0, float(z_abs)))

        try:
            mult = float(model.get("obs_mult", 1.0) or 1.0)
        except Exception:
            mult = 1.0
        mult = max(0.5, min(3.0, float(mult)))
        mult = 0.9 * mult + 0.1 * z_clip
        mult = max(0.5, min(3.0, float(mult)))
        model["obs_mult"] = float(mult)

        # prontidão latente: EWMA do resíduo normalizado (sinal importa)
        try:
            zew = float(model.get("resid_z_ewma", 0.0) or 0.0)
        except Exception:
            zew = 0.0
        zew = 0.85 * float(zew) + 0.15 * max(-3.0, min(3.0, float(z_signed)))
        model["resid_z_ewma"] = float(zew)

    model["mu"] = float(mu)
    model["sigma2"] = float(max(12.0, s2))
    model["n"] = int(model.get("n", 0) or 0) + (1 if obs > 0 else 0)
    model["last_obs_e1rm"] = float(obs)

    # atualiza também a priori do padrão (transfer learning interno)
    pat = str(model.get("pattern") or yami_exercise_pattern(ex))
    model["pattern"] = pat
    pstate = prof.setdefault("patterns", {}).setdefault(pat, {})
    try:
        pmu = float(pstate.get("mu", 0.0) or 0.0)
        ps2 = float(pstate.get("sigma2", 140.0) or 140.0)
        pn = int(pstate.get("n", 0) or 0)
    except Exception:
        pmu, ps2, pn = 0.0, 140.0, 0

    # mistura lenta para não "contaminar" o padrão com 1 treino
    alpha = 0.12 if pn < 10 else 0.06
    if obs > 0.0:
        if pmu <= 0.0:
            pmu = obs
        else:
            pmu = (1 - alpha) * pmu + alpha * obs
        ps2 = max(20.0, (1 - alpha) * ps2 + alpha * float(model["sigma2"]))
        pn = pn + 1

    pstate["mu"] = float(pmu)
    pstate["sigma2"] = float(ps2)
    pstate["n"] = int(pn)

    _yami_state_save(stt)
    return {"mu": float(mu), "sigma2": float(s2), "pattern": pat, "n": int(model["n"])}


def yami_kalman_predict(perfil: str, ex: str) -> dict:
    _yami_model_init_if_missing(perfil, ex, init_e1rm=None)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    model = prof.setdefault("models", {}).setdefault(str(ex), {})
    try:
        mu = float(model.get("mu", 0.0) or 0.0)
        s2 = float(model.get("sigma2", 120.0) or 120.0)
        n = int(model.get("n", 0) or 0)
        pat = str(model.get("pattern") or yami_exercise_pattern(ex))
    except Exception:
        mu, s2, n, pat = 0.0, 120.0, 0, yami_exercise_pattern(ex)
    return {"mu": float(mu), "sigma": float(math.sqrt(max(1e-9, s2))), "sigma2": float(s2), "n": int(n), "pattern": pat, "obs_mult": float(model.get("obs_mult", 1.0) or 1.0)}


def _yami_bandit_pick(perfil: str, ex: str) -> str:
    """Escolhe estratégia via Thompson Sampling (bandit).
    Nota (Streamlit): determinístico por contexto para não variar a cada rerun.
    """
    _yami_model_init_if_missing(perfil, ex, init_e1rm=None)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    b = prof.setdefault("bandit", {}).setdefault(str(ex), {})

    # Seed estável: perfil + exercício + último registo ingerido
    try:
        model = prof.setdefault("models", {}).setdefault(str(ex), {})
        last_key = str(model.get("last_key", "") or "")
    except Exception:
        last_key = ""
    today = datetime.date.today().isoformat()
    seed_str = f"{perfil}|{ex}|{last_key}|{today}"
    seed = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)

    best_arm, best_sample = "micro_load", -1.0
    for arm in ("micro_load", "add_rep", "hold"):
        st_arm = b.setdefault(arm, {"a": 2, "b": 2})
        a = float(st_arm.get("a", 2) or 2)
        bb = float(st_arm.get("b", 2) or 2)
        samp = rng.betavariate(max(0.5, a), max(0.5, bb))
        if samp > best_sample:
            best_sample, best_arm = samp, armrm

    _yami_state_save(stt)
    return str(best_arm)




def _yami_bandit_update(perfil: str, ex: str, arm: str, reward: int) -> None:
    try:
        reward = 1 if int(reward) > 0 else 0
    except Exception:
        reward = 0
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    b = prof.setdefault("bandit", {}).setdefault(str(ex), {})
    st_arm = b.setdefault(str(arm), {"a": 2, "b": 2})
    try:
        if reward == 1:
            st_arm["a"] = int(st_arm.get("a", 2) or 2) + 1
        else:
            st_arm["b"] = int(st_arm.get("b", 2) or 2) + 1
    except Exception:
        pass
    _yami_state_save(stt)



# --- YAMI AI+ (probabilidade, contextual multi-braço, twin, auditor) ---

def yami_exercise_family(ex: str) -> str:
    """Família/padrão de movimento (granular o suficiente para transfer learning)."""
    exl = str(ex or "").lower()
    # squat-ish
    if any(k in exl for k in ["agach", "squat", "hack", "belt squat", "leg press", "front squat"]):
        return "squat"
    # hinge-ish
    if any(k in exl for k in ["deadlift", "rdl", "stiff", "good morning", "hip hinge", "romeno"]):
        return "hinge"
    # push horizontal
    if any(k in exl for k in ["supino", "bench", "chest press", "press peito", "push up", "push-up", "dips"]):
        return "push_h"
    # push vertical
    if any(k in exl for k in ["ohp", "overhead", "military", "arnold", "shoulder press", "press ombro"]):
        return "push_v"
    # pull vertical
    if any(k in exl for k in ["pull-up", "chin", "barra fixa", "lat pulldown", "puxada", "pulldown"]):
        return "pull_v"
    # pull horizontal
    if any(k in exl for k in ["remada", "row", "seal row", "chest supported", "cable row"]):
        return "pull_h"
    # carry / core
    if any(k in exl for k in ["carry", "farmers", "suitcase", "core", "ab", "prancha", "plank"]):
        return "core_carry"
    # isolation heuristics
    if any(k in exl for k in ["curl", "bíceps", "biceps", "tríceps", "triceps", "extensão", "extension", "elevação lateral", "lateral raise", "fly", "peck", "leg curl"]):
        return "isolation"
    return "other"


_CANON_STRIP = [
    "halteres","haltere","dumbbell","db",
    "máquina","maquina","machine",
    "smith","cabo","cable",
    "inclinado","inclinada","incline",
    "declinado","decline",
    "sentado","sentada","seated",
    "em pé","de pé","standing",
    "neutro","neutra","pegada","grip",
    "barra","bar","barbell",
    "tempo","pausa","pause",
]

def yami_exercise_base(ex: str) -> str:
    """Tenta obter um 'exercício base' para hierarquia (variações herdam do base)."""
    s = re.sub(r"\([^\)]*\)", " ", str(ex or ""), flags=re.UNICODE)
    s = re.sub(r"\[[^\]]*\]", " ", s, flags=re.UNICODE)
    s = re.sub(r"[^\w\sáàâãéêíóôõúç\-]", " ", s.lower(), flags=re.UNICODE)
    parts = [p for p in re.split(r"\s+", s) if p]
    parts = [p for p in parts if p not in _CANON_STRIP]
    # mantém 3-5 tokens para não virar sopa
    base = " ".join(parts[:5]).strip()
    return base if base else str(ex or "").strip()


def _yami_prof(perfil: str) -> dict:
    stt = _yami_state_load()
    return stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})


def _yami_ensure_ai_structures(perfil: str) -> None:
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    prof.setdefault("families", {})         # family a prioris
    prof.setdefault("bases", {})            # base exercise a prioris
    prof.setdefault("clf", {})              # success classifier
    prof.setdefault("ctx_bandit", {})       # contextual multi-braço
    prof.setdefault("prefs", {})            # user preference modelo
    prof.setdefault("pain_model", {})       # pain risco modelo
    prof.setdefault("day_clusters", {})     # agrupamento for day types
    prof.setdefault("latent", {})           # latent readiness estimate
    prof.setdefault("tech", {})             # technique anomaly stats
    prof.setdefault("audit", {})            # audit notes
    _yami_state_save(stt)


def _sigmoid(x: float) -> float:
    try:
        x = float(x)
    except Exception:
        return 0.5
    if x >= 35: return 1.0
    if x <= -35: return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def _dot(a, b) -> float:
    try:
        return float(sum(float(x) * float(y) for x, y in zip(a, b)))
    except Exception:
        return 0.0


def yami_pref_get(perfil: str) -> dict:
    _yami_ensure_ai_structures(perfil)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    p = prof.setdefault("prefs", {})
    # load_vs_rep: 1.0 = gosta de subir carga; 0.0 = gosta de reps
    p.setdefault("load_vs_rep", 0.55)
    p.setdefault("risk_aversion", 0.55)  # 0..1
    p.setdefault("n", 0)
    _yami_state_save(stt)
    return dict(p)


def yami_pref_update_from_arm(perfil: str, ex: str, arm_used: str) -> None:
    try:
        arm_used = str(arm_used)
    except Exception:
        arm_used = "hold"
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    p = prof.setdefault("prefs", {})
    lv = float(p.get("load_vs_rep", 0.55) or 0.55)
    n = int(p.get("n", 0) or 0)
    # micro_load puxa para carga, add_rep puxa para reps
    if arm_used == "micro_load":
        lv = 0.97 * lv + 0.03 * 1.0
    elif arm_used == "add_rep":
        lv = 0.97 * lv + 0.03 * 0.0
    else:
        lv = 0.995 * lv + 0.005 * 0.55
    p["load_vs_rep"] = float(max(0.0, min(1.0, lv)))
    p["n"] = int(n + 1)
    _yami_state_save(stt)


# ---- Hierarquia (7): família -> base -> variação ----

def yami_hier_prior_get(perfil: str, ex: str) -> dict:
    """Devolve priors (family/base/variant) para cold-start."""
    _yami_ensure_ai_structures(perfil)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    fam = yami_exercise_family(ex)
    base = yami_exercise_base(ex)
    fam_state = prof.setdefault("families", {}).setdefault(fam, {"mu": 0.0, "sigma2": 180.0, "n": 0})
    base_state = prof.setdefault("bases", {}).setdefault(base, {"mu": 0.0, "sigma2": 160.0, "n": 0, "family": fam})
    var_state = prof.setdefault("models", {}).setdefault(str(ex), {})
    # resolve mu0
    mu0 = float(var_state.get("mu", 0.0) or 0.0)
    s20 = float(var_state.get("sigma2", 0.0) or 0.0)
    if mu0 <= 0:
        mu0 = float(base_state.get("mu", 0.0) or 0.0)
        s20 = float(base_state.get("sigma2", 160.0) or 160.0)
    if mu0 <= 0:
        mu0 = float(fam_state.get("mu", 0.0) or 0.0)
        s20 = float(fam_state.get("sigma2", 180.0) or 180.0)
    return {"family": fam, "base": base, "mu0": float(mu0), "sigma2_0": float(max(40.0, s20))}


def yami_hier_kalman_update(perfil: str, ex: str, obs: float, obs_var: float, process_var: float = 6.0) -> dict:
    """Atualiza variação + empurra info para base e família (slow)."""
    _yami_ensure_ai_structures(perfil)
    # init variant from hierarchy if missing
    pr = yami_hier_prior_get(perfil, ex)
    if pr.get("mu0", 0.0) > 0:
        _yami_model_init_if_missing(perfil, ex, init_e1rm=float(pr["mu0"]))

    # IA: prontidão latente a partir do residual (não depende do check-in)
    try:
        _pred_before = yami_kalman_predict(perfil, ex)
        _mu_before = float(_pred_before.get('mu', 0.0) or 0.0)
        if _mu_before > 0 and float(obs_best) > 0:
            _resid_pct = (float(obs_best) - _mu_before) / _mu_before
            yami_latent_update_from_residual(perfil, float(_resid_pct))
    except Exception:
        pass

    upd = yami_hier_kalman_update(perfil, ex, obs, obs_var, process_var=process_var)

    # update base & family with slow EMA (não é o mesmo filtro para não sobre-ajustar)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    fam = str(pr.get("family"))
    base = str(pr.get("base"))
    fam_state = prof.setdefault("families", {}).setdefault(fam, {"mu": 0.0, "sigma2": 180.0, "n": 0})
    base_state = prof.setdefault("bases", {}).setdefault(base, {"mu": 0.0, "sigma2": 160.0, "n": 0, "family": fam})

    try:
        obs = float(obs)
    except Exception:
        obs = 0.0

    if obs > 0:
        # base
        bn = int(base_state.get("n", 0) or 0)
        balpha = 0.10 if bn < 8 else 0.05
        bmu = float(base_state.get("mu", 0.0) or 0.0)
        bs2 = float(base_state.get("sigma2", 160.0) or 160.0)
        base_state["mu"] = float(obs if bmu <= 0 else (1 - balpha) * bmu + balpha * obs)
        base_state["sigma2"] = float(max(30.0, (1 - balpha) * bs2 + balpha * float(upd.get("sigma2", bs2) or bs2)))
        base_state["n"] = int(bn + 1)

        # family
        fn = int(fam_state.get("n", 0) or 0)
        falpha = 0.08 if fn < 12 else 0.03
        fmu = float(fam_state.get("mu", 0.0) or 0.0)
        fs2 = float(fam_state.get("sigma2", 180.0) or 180.0)
        fam_state["mu"] = float(obs if fmu <= 0 else (1 - falpha) * fmu + falpha * obs)
        fam_state["sigma2"] = float(max(40.0, (1 - falpha) * fs2 + falpha * float(upd.get("sigma2", fs2) or fs2)))
        fam_state["n"] = int(fn + 1)

    _yami_state_save(stt)
    return upd


# ---- (1) Classificador de sucesso por set (online logistic) ----

def _yami_clf_get(perfil: str, key: str) -> dict:
    _yami_ensure_ai_structures(perfil)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    clf = prof.setdefault("clf", {}).setdefault(str(key), {})
    clf.setdefault("w", [0.0] * 10)
    clf.setdefault("lr", 0.08)
    clf.setdefault("l2", 0.0015)
    clf.setdefault("n", 0)
    _yami_state_save(stt)
    return clf


def _yami_clf_features(
    e1rm_mu: float,
    e1rm_sigma: float,
    weight: float,
    target_reps: float,
    rir_target: float,
    rest_s: float,
    set_idx: float,
    total_sets: float,
    readiness: float,
    daytype_id: float,
    risk_aversion: float
) -> list:
    # normalizações leves
    try:
        mu = max(1.0, float(e1rm_mu))
        w = max(0.0, float(weight))
        ratio = w / mu
    except Exception:
        ratio = 0.0
    try:
        tr = float(target_reps) / 12.0
    except Exception:
        tr = 0.0
    try:
        rr = float(rir_target) / 5.0
    except Exception:
        rr = 0.0
    try:
        rs = float(rest_s) / 240.0
    except Exception:
        rs = 0.0
    try:
        si = float(set_idx) / max(1.0, float(total_sets))
    except Exception:
        si = 0.0
    try:
        unc = float(e1rm_sigma) / max(20.0, float(e1rm_mu))
    except Exception:
        unc = 0.5
    try:
        rd = float(readiness)  # já é pequeno (-0.1..+0.1)
    except Exception:
        rd = 0.0
    try:
        dt = float(daytype_id)
    except Exception:
        dt = 0.0
    try:
        ra = float(risk_aversion)
    except Exception:
        ra = 0.55

    # 10 dims (+bias)
    return [
        1.0,
        ratio,
        tr,
        rr,
        rs,
        si,
        unc,
        rd,
        dt,
        ra,
    ]


def yami_clf_predict(perfil: str, ex: str, feats: list) -> dict:
    key_var = str(ex)
    key_base = "base::" + yami_exercise_base(ex)
    key_fam = "fam::" + yami_exercise_family(ex)

    st_var = _yami_clf_get(perfil, key_var)
    st_base = _yami_clf_get(perfil, key_base)
    st_fam = _yami_clf_get(perfil, key_fam)

    wv, wb, wf = list(st_var.get("w", [])), list(st_base.get("w", [])), list(st_fam.get("w", []))
    # mistura: se ainda não tem dados na variação, usa mais base/fam
    nv = int(st_var.get("n", 0) or 0)
    nb = int(st_base.get("n", 0) or 0)
    nf = int(st_fam.get("n", 0) or 0)

    av = min(0.65, 0.15 + 0.05 * nv)
    ab = min(0.55, 0.20 + 0.03 * nb)
    af = 1.0 - min(0.85, av + ab)
    af = max(0.10, af)

    # alinhar tamanho
    L = len(feats)
    def _pad(w):
        w = list(w or [])
        if len(w) < L:
            w += [0.0] * (L - len(w))
        return w[:L]

    w = [av * x + ab * y + af * z for x, y, z in zip(_pad(wv), _pad(wb), _pad(wf))]
    score = _dot(w, feats)
    p = _sigmoid(score)
    return {"p": float(p), "score": float(score), "n_var": int(nv)}


def yami_clf_update(perfil: str, ex: str, feats: list, y: int) -> None:
    y = 1 if int(y) > 0 else 0
    keys = [str(ex), "base::" + yami_exercise_base(ex), "fam::" + yami_exercise_family(ex)]
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    clf = prof.setdefault("clf", {})
    for k in keys:
        st = clf.setdefault(str(k), {"w": [0.0] * 10, "lr": 0.08, "l2": 0.0015, "n": 0})
        w = list(st.get("w", [0.0] * 10))
        # pad
        if len(w) < len(feats):
            w += [0.0] * (len(feats) - len(w))
        w = w[:len(feats)]
        lr = float(st.get("lr", 0.08) or 0.08)
        l2 = float(st.get("l2", 0.0015) or 0.0015)

        p = _sigmoid(_dot(w, feats))
        err = (float(y) - float(p))
        # SGD update
        for i in range(len(w)):
            grad = err * float(feats[i]) - l2 * float(w[i])
            w[i] = float(w[i]) + lr * grad
        st["w"] = w
        st["n"] = int(st.get("n", 0) or 0) + 1
    _yami_state_save(stt)


# ---- (4) Modeloo de erro de RIR (sem slider) ----

def yami_rir_error_predict(perfil: str, ex: str) -> dict:
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    st = prof.setdefault("rir_err", {}).setdefault(str(ex), {"mu": 0.0, "s2": 1.0, "n": 0})
    try:
        mu = float(st.get("mu", 0.0) or 0.0)
        s2 = float(st.get("s2", 1.0) or 1.0)
        n = int(st.get("n", 0) or 0)
    except Exception:
        mu, s2, n = 0.0, 1.0, 0
    return {"mu": float(mu), "sigma": float(math.sqrt(max(1e-9, s2))), "n": int(n)}


def yami_rir_error_update(perfil: str, ex: str, err: float) -> None:
    try:
        err = float(err)
    except Exception:
        return
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    st = prof.setdefault("rir_err", {}).setdefault(str(ex), {"mu": 0.0, "s2": 1.0, "n": 0})
    mu = float(st.get("mu", 0.0) or 0.0)
    s2 = float(st.get("s2", 1.0) or 1.0)
    n = int(st.get("n", 0) or 0)

    # Welford-ish update
    n2 = n + 1
    delta = err - mu
    mu2 = mu + delta / n2
    # update variance (approx)
    s2 = max(1e-6, (0.97 * s2 + 0.03 * (delta * (err - mu2) + 1e-6)))
    st["mu"], st["s2"], st["n"] = float(mu2), float(s2), int(n2)
    _yami_state_save(stt)


# ---- (3 & 5) prontidão latente + agrupamento de dias ----

def yami_latent_get(perfil: str) -> dict:
    _yami_ensure_ai_structures(perfil)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    lat = prof.setdefault("latent", {})
    lat.setdefault("mu", 0.0)     # -0.12..+0.12 (aprox)
    lat.setdefault("s2", 0.0025)  # variância
    lat.setdefault("n", 0)
    _yami_state_save(stt)
    return dict(lat)


def yami_latent_update_from_residual(perfil: str, resid_pct: float) -> dict:
    """Atualiza prontidão latente usando residual relativo (obs - pred)/pred."""
    _yami_ensure_ai_structures(perfil)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    lat = prof.setdefault("latent", {})
    mu = float(lat.get("mu", 0.0) or 0.0)
    s2 = float(lat.get("s2", 0.0025) or 0.0025)
    n = int(lat.get("n", 0) or 0)

    try:
        x = max(-0.20, min(0.20, float(resid_pct)))
    except Exception:
        x = 0.0
    # EWMA + variance
    alpha = 0.10 if n < 10 else 0.05
    mu2 = (1 - alpha) * mu + alpha * x
    s2 = max(1e-5, (1 - alpha) * s2 + alpha * ((x - mu2) ** 2 + 1e-6))
    lat["mu"], lat["s2"], lat["n"] = float(mu2), float(s2), int(n + 1)

    # update day agrupamentos (k=3, online)
    cl = prof.setdefault("day_clusters", {}).setdefault("k3", {"c": [-0.06, 0.0, 0.06], "n": [1, 1, 1]})
    c = list(cl.get("c", [-0.06, 0.0, 0.06]))
    nn = list(cl.get("n", [1, 1, 1]))
    # pick nearest center
    idx = min(range(3), key=lambda i: abs(float(c[i]) - float(x)))
    nn[idx] = int(nn[idx]) + 1
    lr = 1.0 / max(8.0, float(nn[idx]))  # decai
    c[idx] = float(c[idx]) + lr * (float(x) - float(c[idx]))
    cl["c"], cl["n"] = c, nn

    _yami_state_save(stt)
    return {"mu": float(mu2), "sigma": float(math.sqrt(max(1e-9, s2))), "cluster_centers": c}


def yami_daytype(perfil: str) -> dict:
    """Devolve tipo de dia (0 fraco, 1 normal, 2 forte) + score."""
    lat = yami_latent_get(perfil)
    mu = float(lat.get("mu", 0.0) or 0.0)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    cl = (prof.get("day_clusters", {}) or {}).get("k3", {"c": [-0.06, 0.0, 0.06], "n": [1, 1, 1]})
    c = list(cl.get("c", [-0.06, 0.0, 0.06]))
    idx = min(range(3), key=lambda i: abs(float(c[i]) - float(mu)))
    label = ["fraco", "normal", "forte"][idx] if 0 <= idx < 3 else "normal"
    return {"id": int(idx), "label": str(label), "score": float(mu), "centers": c}


# ---- (6) Anomaly/technique detector (sem vídeo) ----

def yami_tech_update(perfil: str, ex: str, sets_list: list, e1rm_mu: float) -> dict:
    """Atualiza estatísticas de 'quebra técnica' a partir do padrão interno do exercício."""
    _yami_ensure_ai_structures(perfil)
    # métrica simples: drop de reps e inconsistência de RIR
    reps = []
    rirs = []
    wts = []
    for s in list(sets_list or []):
        try:
            wts.append(float(s.get("peso", 0) or 0))
            reps.append(float(s.get("reps", 0) or 0))
            rirs.append(float(s.get("rir", 0) or 0))
        except Exception:
            pass
    flag = False
    score = 0.0
    try:
        if len(reps) >= 2:
            drop = (reps[0] - reps[-1]) / max(1.0, reps[0])
            rir_var = statistics.pvariance(rirs) if len(rirs) >= 3 else 0.0
            # heurística: drop grande + RIR instável
            score = 0.7 * max(0.0, drop) + 0.3 * min(1.0, rir_var / 2.0)
            flag = (drop >= 0.35 and (statistics.mean(rirs) <= 3.0)) or (score >= 0.55)
    except Exception:
        flag = False

    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    t = prof.setdefault("tech", {}).setdefault(str(ex), {"flag": False, "last": 0.0, "n": 0})
    t["flag"] = bool(flag)
    t["last"] = float(score)
    t["n"] = int(t.get("n", 0) or 0) + 1
    _yami_state_save(stt)
    return {"flag": bool(flag), "score": float(score)}


def yami_tech_flag(perfil: str, ex: str) -> dict:
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    t = (prof.get("tech", {}) or {}).get(str(ex), {"flag": False, "last": 0.0, "n": 0})
    return {"flag": bool(t.get("flag", False)), "score": float(t.get("last", 0.0) or 0.0), "n": int(t.get("n", 0) or 0)}


# ---- (8) Contextual multi-braço ----

def yami_context_key(perfil: str, bloco: str, pain_bucket: int = 0) -> str:
    dt = yami_daytype(perfil)
    dlab = str(dt.get("label", "normal"))
    phase = str(bloco or "Base")
    pb = int(pain_bucket)
    return f"{dlab}|{phase}|pain{pb}"


def yami_ctx_bandit_pick(perfil: str, ex: str, ctx: str) -> str:
    _yami_ensure_ai_structures(perfil)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    cb = prof.setdefault("ctx_bandit", {}).setdefault(str(ctx), {}).setdefault(str(ex), {})

    # Preferência do utilizador (só para ordenar braços quando empata)
    pref = yami_pref_get(perfil)
    lv = float(pref.get("load_vs_rep", 0.55) or 0.55)

    arms = ["micro_load", "add_rep", "hold", "cut_volume"]
    if lv < 0.45:
        arms = ["add_rep", "hold", "micro_load", "cut_volume"]
    elif lv > 0.65:
        arms = ["micro_load", "hold", "add_rep", "cut_volume"]

    # IMPORTANTÍSSIMO (Streamlit): isto tem de ser determinístico dentro do mesmo contexto.
    # Caso contrário, cada 'rerun' escolhe um braço diferente e o Yami parece aleatório.
    try:
        model = prof.setdefault("models", {}).setdefault(str(ex), {})
        last_key = str(model.get("last_key", "") or "")
    except Exception:
        last_key = ""

    today = datetime.date.today().isoformat()
    seed_str = f"{perfil}|{ex}|{ctx}|{last_key}|{today}"
    seed = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)

    best_arm, best_sample = "micro_load", -1.0
    for arm in arms:
        st_arm = cb.setdefault(arm, {"a": 2, "b": 2})
        a = float(st_arm.get("a", 2) or 2)
        bb = float(st_arm.get("b", 2) or 2)
        samp = rng.betavariate(max(0.5, a), max(0.5, bb))
        if samp > best_sample:
            best_sample, best_arm = samp, armrm

    _yami_state_save(stt)
    return str(best_arm)




def yami_ctx_bandit_update(perfil: str, ex: str, ctx: str, arm: str, reward: int) -> None:
    reward = 1 if int(reward) > 0 else 0
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    cb = prof.setdefault("ctx_bandit", {}).setdefault(str(ctx), {}).setdefault(str(ex), {})
    st_arm = cb.setdefault(str(arm), {"a": 2, "b": 2})
    if reward == 1:
        st_arm["a"] = int(st_arm.get("a", 2) or 2) + 1
    else:
        st_arm["b"] = int(st_arm.get("b", 2) or 2) + 1
    _yami_state_save(stt)


# ---- (10) Gémeo digital (simulador simples) ----

def yami_twin_predict_reps_to_fail(e1rm: float, weight: float) -> float:
    try:
        e1rm = float(e1rm); weight = float(weight)
    except Exception:
        return 0.0
    if e1rm <= 0 or weight <= 0:
        return 0.0
    ratio = max(1.0, e1rm / weight)
    reps_to_fail = 30.0 * (ratio - 1.0)
    return float(max(0.0, min(20.0, reps_to_fail)))


def yami_twin_predict(perfil: str, ex: str, weight: float, target_reps: float, rir_target: float, rest_s: float, set_idx: int, total_sets: int) -> dict:
    pred = yami_kalman_predict(perfil, ex)
    mu = float(pred.get("mu", 0.0) or 0.0)
    sig = float(pred.get("sigma", 999.0) or 999.0)
    # prontidão latente
    dt = yami_daytype(perfil)
    r_lat = float(dt.get("score", 0.0) or 0.0)
    # ajuste e1RM do dia (pequeno)
    e_today = mu * (1.0 + r_lat)
    reps_fail = yami_twin_predict_reps_to_fail(e_today, float(weight))
    rir_pred = float(reps_fail) - float(target_reps)
    # transforma em probabilidade "física" (quanto acima do alvo)
    margin = (rir_pred - float(rir_target))
    p_phys = _sigmoid(2.6 * margin)  # 0.5 quando margin=0
    return {"p_phys": float(p_phys), "rir_pred": float(rir_pred), "reps_to_fail": float(reps_fail), "mu": float(mu), "sigma": float(sig), "readiness": float(r_lat), "daytype": dt}


# ---- (2) Otimizador com restrições ----

def yami_pick_weight_optimized(
    perfil: str,
    ex: str,
    item: dict,
    base_weight: float,
    target_reps: int,
    rir_target: float,
    rest_s: float,
    set_idx: int,
    total_sets: int,
    bloco: str,
    pain_risk: float = 0.0,
    week_penalty: float = 0.0,
) -> dict:
    gran = float(_yami_granularidade_peso(ex, item))
    pred = yami_kalman_predict(perfil, ex)
    twin = yami_twin_predict(perfil, ex, base_weight, target_reps, rir_target, rest_s, set_idx, total_sets)
    pref = yami_pref_get(perfil)
    ra = float(pref.get("risk_aversion", 0.55) or 0.55)

    # passo de exploração: usa a granularidade do exercício (evita sugestões a 0.5 kg em compostos)
    try:
        step = float(gran)
    except Exception:
        step = 2.5
    step = max(0.5, step)

    # candidates around base
    base = max(0.0, float(base_weight))
    cands = [base + k * step for k in (-2, -1, 0, 1, 2)]
    cands = [max(0.0, c) for c in cands if c > 0]
    # de-dup and round to 0.5
    cands = sorted({float(_round_to_nearest(c, gran)) for c in cands})
    if not cands:
        cands = [float(_round_to_nearest(base, gran))]

    best = {"w": float(base), "p": 0.5, "score": -1e9, "why": "base"}
    for w in cands:
        twin_w = yami_twin_predict(perfil, ex, w, target_reps, rir_target, rest_s, set_idx, total_sets)
        feats = _yami_clf_features(
            e1rm_mu=float(pred.get("mu", 0.0) or 0.0),
            e1rm_sigma=float(pred.get("sigma", 999.0) or 999.0),
            weight=float(w),
            target_reps=float(target_reps),
            rir_target=float(rir_target),
            rest_s=float(rest_s),
            set_idx=float(set_idx),
            total_sets=float(total_sets),
            readiness=float(twin_w.get("readiness", 0.0) or 0.0),
            daytype_id=float(twin_w.get("daytype", {}).get("id", 1) if isinstance(twin_w.get("daytype"), dict) else 1),
            risk_aversion=float(ra),
        )
        clf = yami_clf_predict(perfil, ex, feats)
        p = 0.55 * float(twin_w.get("p_phys", 0.5) or 0.5) + 0.45 * float(clf.get("p", 0.5) or 0.5)

        # recompensa de estímulo (peso) + penalizações (falha, dor, semana)
        stim = float(w)
        fail_pen = (1.0 - p) * stim * (0.55 + 0.65 * ra)
        pain_pen = float(pain_risk) * stim * 0.65
        week_pen = float(week_penalty) * stim * 0.55

        s = p * stim - fail_pen - pain_pen - week_pen

        # se o user prefere reps, penaliza subir peso
        lv = float(pref.get("load_vs_rep", 0.55) or 0.55)
        if lv < 0.45 and w > base:
            s -= (0.10 + 0.20 * (0.45 - lv)) * stim
        if lv > 0.65 and w < base:
            s -= (0.08 + 0.15 * (lv - 0.65)) * stim

        if s > float(best["score"]):
            best = {"w": float(w), "p": float(p), "score": float(s), "why": f"opt({len(cands)})"}

    return best


# ---- (9) MPC-lite semanal + (14) auditor ----

def yami_week_stats(df_hist: pd.DataFrame, perfil: str) -> dict:
    out = {"week_load": 0.0, "fam_load": {}, "n_rows": 0}
    try:
        if df_hist is None or df_hist.empty:
            return out
        dfp = yami_df_limpo_para_yami(df_hist, perfil)
        if dfp.empty:
            return out
        # parse date
        dfp["__date"] = pd.to_datetime(dfp["Data"], errors="coerce", dayfirst=True)
        dfp = dfp.dropna(subset=["__date"])
        if dfp.empty:
            return out
        now = datetime.datetime.now(ZoneInfo("Europe/Lisbon"))
        iso_year, iso_week, _ = now.isocalendar()
        dfp["__iso_year"] = dfp["__date"].dt.isocalendar().year.astype(int)
        dfp["__iso_week"] = dfp["__date"].dt.isocalendar().week.astype(int)
        dfw = dfp[(dfp["__iso_year"] == iso_year) & (dfp["__iso_week"] == iso_week)]
        if dfw.empty:
            return out
        load_total = 0.0
        fam = {}
        for _, r in dfw.iterrows():
            ex = str(r.get("Exercício", ""))
            w = float(r.get("Peso", 0) or 0)
            reps = float(r.get("Reps", 0) or 0)
            # cada linha é 1 set no schema atual
            load = max(0.0, w * reps)
            load_total += load
            f = yami_exercise_family(ex)
            fam[f] = fam.get(f, 0.0) + load
        out = {"week_load": float(load_total), "fam_load": fam, "n_rows": int(len(dfw))}
        return out
    except Exception:
        return out


def yami_week_penalty(df_hist: pd.DataFrame, perfil: str, ex: str) -> float:
    """Penalização 0..1 quando a semana já está pesada naquela família."""
    try:
        st = yami_week_stats(df_hist, perfil)
        fam = yami_exercise_family(ex)
        fam_load = float((st.get("fam_load", {}) or {}).get(fam, 0.0) or 0.0)
        # limiares grosseiros (ajusta depois com dados)
        thresh = 12000.0 if fam in ("squat", "hinge") else 9000.0 if fam in ("push_h","pull_h","push_v","pull_v") else 7000.0
        pen = max(0.0, min(1.0, fam_load / max(1.0, thresh) - 0.65))
        return float(pen)
    except Exception:
        return 0.0


def yami_audit_plan(df_hist: pd.DataFrame, perfil: str) -> list:
    """Auditor rápido: procura desequilíbrios e padrões suspeitos."""
    warnings = []
    try:
        if df_hist is None or df_hist.empty:
            return warnings
        dfp = yami_df_limpo_para_yami(df_hist, perfil)
        if dfp.empty:
            return warnings
        dfp["__date"] = pd.to_datetime(dfp["Data"], errors="coerce", dayfirst=True)
        dfp = dfp.dropna(subset=["__date"])
        if dfp.empty:
            return warnings
        cutoff = datetime.datetime.now(ZoneInfo("Europe/Lisbon")) - datetime.timedelta(days=10)
        dfp = dfp[dfp["__date"] >= cutoff]
        if dfp.empty:
            return warnings
        fam_counts = {}
        for ex in dfp["Exercício"].astype(str).tolist():
            fam = yami_exercise_family(ex)
            fam_counts[fam] = fam_counts.get(fam, 0) + 1
        # excesso
        for fam, n in sorted(fam_counts.items(), key=lambda x: -x[1]):
            if n >= 18 and fam in ("squat","hinge"):
                warnings.append(f"⚠️ Muito {fam} nos últimos 10 dias ({n} sets). Considera aliviar volume ou alternar variações.")
            if n >= 16 and fam in ("push_h","push_v"):
                warnings.append(f"⚠️ Push muito alto nos últimos 10 dias ({n} sets). Onde está o pull para equilibrar ombro?")
        # falta
        if fam_counts.get("pull_h", 0) + fam_counts.get("pull_v", 0) <= 6:
            warnings.append("⚠️ Pouco pull nos últimos 10 dias. Isso costuma cobrar juros no ombro/postura.")
        if fam_counts.get("squat", 0) + fam_counts.get("hinge", 0) <= 6:
            warnings.append("ℹ️ Pouca perna/hinge recente. Se isso não é intencional, estás a fugir do problema.")
        return warnings[:4]
    except Exception:
        return warnings


# ---- (13) Pain-aware policy aprendida (modeloo simples) ----

def _pain_key(area: str) -> str:
    return f"pain::{str(area)}"


def yami_pain_predict(perfil: str, ex: str, feats: list, area: str) -> float:
    _yami_ensure_ai_structures(perfil)
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    pm = prof.setdefault("pain_model", {}).setdefault(_pain_key(area), {"w": [0.0]*len(feats), "lr": 0.06, "l2": 0.001, "n": 0})
    w = list(pm.get("w", [0.0]*len(feats)))
    if len(w) < len(feats):
        w += [0.0]*(len(feats)-len(w))
    w = w[:len(feats)]
    return float(_sigmoid(_dot(w, feats)))


def yami_pain_update(perfil: str, feats: list, area: str, y: int) -> None:
    y = 1 if int(y) > 0 else 0
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    pm = prof.setdefault("pain_model", {}).setdefault(_pain_key(area), {"w": [0.0]*len(feats), "lr": 0.06, "l2": 0.001, "n": 0})
    w = list(pm.get("w", [0.0]*len(feats)))
    if len(w) < len(feats):
        w += [0.0]*(len(feats)-len(w))
    w = w[:len(feats)]
    lr = float(pm.get("lr", 0.06) or 0.06)
    l2 = float(pm.get("l2", 0.001) or 0.001)

    p = _sigmoid(_dot(w, feats))
    err = float(y) - float(p)
    for i in range(len(w)):
        w[i] = float(w[i]) + lr * (err * float(feats[i]) - l2 * float(w[i]))
    pm["w"] = w
    pm["n"] = int(pm.get("n", 0) or 0) + 1
    _yami_state_save(stt)


def yami_pain_feat_simple(perfil: str, ex: str, item: dict, avg_w: float, avg_reps: float, avg_rir: float, week_pen: float) -> list:
    fam = yami_exercise_family(ex)
    is_comp = 1.0 if str(item.get("tipo","")).lower() == "composto" else 0.0
    # one-hot family into 6 buckets
    fams = ["squat","hinge","push_h","push_v","pull_h","pull_v"]
    one = [1.0 if fam==f else 0.0 for f in fams]
    return [1.0] + one + [is_comp, float(avg_w)/100.0, float(avg_reps)/12.0, float(avg_rir)/5.0, float(week_pen)]


# ---- (11) Aprender preferências por substituição manual ----

def yami_pref_update_override(perfil: str, ex: str, suggested: float, actual: float) -> None:
    try:
        suggested = float(suggested); actual = float(actual)
    except Exception:
        return
    if suggested <= 0 or actual <= 0:
        return
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    p = prof.setdefault("prefs", {})
    lv = float(p.get("load_vs_rep", 0.55) or 0.55)
    ra = float(p.get("risk_aversion", 0.55) or 0.55)
    n = int(p.get("n", 0) or 0)

    diff = (actual - suggested) / suggested
    # se o user baixa consistentemente, aumenta aversão ao risco; se sobe, diminui
    if diff <= -0.03:
        ra = 0.97 * ra + 0.03 * 0.85
        lv = 0.985 * lv + 0.015 * 0.35
    elif diff >= 0.03:
        ra = 0.97 * ra + 0.03 * 0.25
        lv = 0.985 * lv + 0.015 * 0.75

    p["risk_aversion"] = float(max(0.0, min(1.0, ra)))
    p["load_vs_rep"] = float(max(0.0, min(1.0, lv)))
    p["n"] = int(n + 1)
    _yami_state_save(stt)


# ---- Helper: update IA quando guardas um exercício ----

def yami_ai_update_from_saved_sets(
    perfil: str,
    ex: str,
    item: dict,
    sets_list: list,
    bloco: str,
    df_hist: pd.DataFrame | None,
    pain_flags: dict | None = None,
):
    """Atualiza: hier kalman, latent readiness, clustering, tech, classifier, pain model, prefs."""
    try:
        sets_list = list(sets_list or [])
    except Exception:
        sets_list = []
    if not sets_list:
        return

    # compute best obs e1RM
    obs_best = 0.0
    obs_var = 26.0
    for s in sets_list:
        try:
            w = float(s.get("peso", 0) or 0)
            r = float(s.get("reps", 0) or 0)
            rir = float(s.get("rir", 0) or 0)
        except Exception:
            continue
        if w <= 0 or r <= 0:
            continue
        e1 = yami_e1rm_obs(w, r, max(0.0, rir))
        if e1 > obs_best:
            obs_best = e1
            # obs var heuristic
            obs_var = 26.0
            if r >= 6: obs_var -= 6.0
            if r >= 10: obs_var -= 6.0
            if rir <= 1.0: obs_var -= 6.0
            obs_var = max(8.0, obs_var)

    # IA: ajusta ruído com base no teu padrão de erro de RIR (se és incoerente, eu confio menos)
    try:
        _re = yami_rir_error_predict(perfil, ex)
        _sig = float(_re.get('sigma', 0.0) or 0.0)
        if _sig > 0:
            obs_var = float(obs_var) * (1.0 + min(1.0, _sig / 2.5))
    except Exception:
        pass

    # a priori prediction for residual
    pred_before = yami_kalman_predict(perfil, ex)
    mu_before = float(pred_before.get("mu", 0.0) or 0.0)
    resid_pct = 0.0
    if mu_before > 0 and obs_best > 0:
        resid_pct = (float(obs_best) - float(mu_before)) / float(mu_before)

    # latent readiness update
    yami_latent_update_from_residual(perfil, resid_pct)

    # update kalman hierarchy
    read = st.session_state.get("yami_readiness", {}) or {}
    try:
        rlabel = str(read.get("label", "Normal") or "Normal")
    except Exception:
        rlabel = "Normal"
    Q = 6.0
    if "Baixa" in rlabel:
        Q = 10.0
    elif "Boa" in rlabel:
        Q = 5.0
    yami_hier_kalman_update(perfil, ex, obs_best, obs_var, process_var=Q)

    # technique update
    yami_tech_update(perfil, ex, sets_list, mu_before)

    # update RIR error modelo
    try:
        pred_after = yami_kalman_predict(perfil, ex)
        e1_mu = float(pred_after.get("mu", mu_before) or mu_before)
    except Exception:
        e1_mu = mu_before
    for s in sets_list:
        try:
            w = float(s.get("peso", 0) or 0)
            r = float(s.get("reps", 0) or 0)
            rir = float(s.get("rir", 0) or 0)
        except Exception:
            continue
        if w <= 0 or r <= 0:
            continue
        implied_fail = float(r) + float(max(0.0, rir))
        exp_fail = yami_twin_predict_reps_to_fail(e1_mu, w)
        err = implied_fail - exp_fail
        yami_rir_error_update(perfil, ex, err)

    # classifier update (label success vs alvo)
    rep_info = _parse_rep_scheme(str(item.get("reps", "")), int(item.get("series", 0) or 0)) if isinstance(item, dict) else {"kind": "", "low": 0, "high": 0, "expected": []}
    kind = str(rep_info.get("kind") or "")
    low = int(rep_info.get("low") or 0)
    high = int(rep_info.get("high") or 0)
    expected = list(rep_info.get("expected") or [])
    rir_target = float(rir_alvo_num(item.get("tipo", ""), str(bloco or "Base"), int(st.session_state.get("semana", 1) or 1)) or 2.0) if isinstance(item, dict) else 2.0

    pref = yami_pref_get(perfil)
    ra = float(pref.get("risk_aversion", 0.55) or 0.55)
    dt = yami_daytype(perfil)
    dtid = float(dt.get("id", 1) or 1)

    pred_now = yami_kalman_predict(perfil, ex)
    for idx, s in enumerate(sets_list):
        try:
            w = float(s.get("peso", 0) or 0)
            r = int(float(s.get("reps", 0) or 0))
            rir = float(s.get("rir", 0) or 0)
        except Exception:
            continue
        if w <= 0 or r <= 0:
            continue

        # alvo por série
        targ = 0
        if kind == "fixed_seq" and idx < len(expected):
            try:
                targ = int(float(expected[idx]) or 0)
            except Exception:
                targ = 0
        if targ <= 0 and low > 0 and high > 0:
            targ = int(round((low + high) / 2.0))
        if targ <= 0 and low > 0:
            targ = int(low)
        if targ <= 0:
            targ = max(1, r)

        # label sucesso: reps >= targ e RIR não abaixo do alvo por muito
        y = 1 if (r >= targ and float(rir) >= float(rir_target) - 0.75) else 0

        feats = _yami_clf_features(
            e1rm_mu=float(pred_now.get("mu", 0.0) or 0.0),
            e1rm_sigma=float(pred_now.get("sigma", 999.0) or 999.0),
            weight=float(w),
            target_reps=float(targ),
            rir_target=float(rir_target),
            rest_s=float(item.get("descanso_s", 120) if isinstance(item, dict) else 120),
            set_idx=float(idx),
            total_sets=float(max(1, len(sets_list))),
            readiness=float(dt.get("score", 0.0) or 0.0),
            daytype_id=float(dtid),
            risk_aversion=float(ra),
        )
        yami_clf_update(perfil, ex, feats, y)

    # pain modelo update (label = pain flags atuais)
    pain_flags = pain_flags or {}
    week_pen = yami_week_penalty(df_hist, perfil, ex) if df_hist is not None else 0.0
    try:
        avg_w = statistics.mean([float(s.get("peso", 0) or 0) for s in sets_list if float(s.get("peso", 0) or 0) > 0])
        avg_r = statistics.mean([float(s.get("reps", 0) or 0) for s in sets_list if float(s.get("reps", 0) or 0) > 0])
        avg_rir = statistics.mean([float(s.get("rir", 0) or 0) for s in sets_list if float(s.get("reps", 0) or 0) > 0])
    except Exception:
        avg_w, avg_r, avg_rir = 0.0, 0.0, 0.0

    feats_p = yami_pain_feat_simple(perfil, ex, item if isinstance(item, dict) else {}, avg_w, avg_r, avg_rir, float(week_pen))
    for area, flag in pain_flags.items():
        try:
            yami_pain_update(perfil, feats_p, str(area), 1 if flag else 0)
        except Exception:
            pass

    # preference update by substituição manual
    try:
        last_sugs = st.session_state.get("yami_last_sug", {}) or {}
        sug = float(last_sugs.get(str(ex), 0) or 0)
        if sug > 0 and avg_w > 0:
            yami_pref_update_override(perfil, ex, sug, avg_w)
    except Exception:
        pass


def yami_detect_changepoint(perfil: str, ex: str) -> dict:
    """Detecta queda persistente (tendência), não só um dia mau."""
    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    hist = list((prof.get("obs_hist", {}) or {}).get(str(ex), []) or [])
    hist = [h for h in hist if float(h.get("e1rm", 0) or 0) > 0]
    if len(hist) < 6:
        return {"flag": False, "delta_pct": 0.0}
    hist = sorted(hist, key=lambda x: str(x.get("dt", "")))[-6:]
    a = [float(x.get("e1rm", 0) or 0) for x in hist[:3]]
    b = [float(x.get("e1rm", 0) or 0) for x in hist[3:]]
    ma = sum(a)/len(a); mb = sum(b)/len(b)
    if ma <= 0:
        return {"flag": False, "delta_pct": 0.0}
    delta_pct = (mb - ma) / ma
    # queda >1.5% na média das últimas 3 vs 3 anteriores
    flag = delta_pct <= -0.015
    return {"flag": bool(flag), "delta_pct": float(delta_pct)}


def yami_sync_model_from_history(perfil: str, ex: str, latest: dict, prev: dict | None) -> dict:
    """Sincroniza o modelo persistente a partir do histórico da sheet, uma vez por sessão gravada."""
    # cria chave única (para não atualizar repetidamente em cada rerun)
    try:
        key = f"{latest.get('data','')}|{latest.get('pesos', [])}|{latest.get('reps', [])}|{latest.get('rirs', [])}"
    except Exception:
        key = str(latest.get('data', ''))

    _yami_model_init_if_missing(perfil, ex, init_e1rm=None)

    stt = _yami_state_load()
    prof = stt.setdefault("profiles", {}).setdefault(str(perfil or "—"), {})
    model = prof.setdefault("models", {}).setdefault(str(ex), {})
    if str(model.get("last_key", "")) == str(key):
        # já sincronizado
        pred = yami_kalman_predict(perfil, ex)
        return {"synced": False, "pred": pred, "key": str(key)}

    # calcula observação e1RM da sessão: usa o melhor e1RM dos sets
    pesos = [float(x) for x in list(latest.get("pesos", []) or []) if x is not None]
    reps = [float(x) for x in list(latest.get("reps", []) or []) if x is not None]
    rirs = [float(x) for x in list(latest.get("rirs", []) or []) if x is not None]

    obs_best = 0.0
    obs_w = 0.0
    obs_r = 0.0
    obs_rir_eff = 0.0

    for i in range(max(len(pesos), len(reps), len(rirs))):
        try:
            w = float(pesos[i]) if i < len(pesos) else 0.0
            r = float(reps[i]) if i < len(reps) else 0.0
            rr = float(rirs[i]) if i < len(rirs) else None
        except Exception:
            continue
        if w <= 0 or r <= 0 or rr is None:
            continue
        rir_eff = max(0.0, float(rr))
        e1 = yami_e1rm_obs(w, r, rir_eff)
        if e1 > obs_best:
            obs_best, obs_w, obs_r, obs_rir_eff = e1, w, r, rir_eff

    # variância de observação: mais reps e mais perto da falha = melhor leitura (menos ruído)
    obs_var = 30.0
    if obs_best > 0:
        obs_var = 26.0
        if obs_r >= 6: obs_var -= 6.0
        if obs_r >= 10: obs_var -= 6.0
        if obs_rir_eff <= 1.0: obs_var -= 6.0
        obs_var = max(8.0, obs_var)

    # process noise: prontidão altera instabilidade (dia mau = mais ruído)
    read = st.session_state.get("yami_readiness", {}) or {}
    try:
        rlabel = str(read.get("label", "Normal") or "Normal")
    except Exception:
        rlabel = "Normal"
    Q = 6.0
    if "Baixa" in rlabel:
        Q = 10.0
    elif "Boa" in rlabel:
        Q = 5.0

    upd = yami_kalman_update(perfil, ex, obs_best, obs_var, process_var=Q)
    pred = yami_kalman_predict(perfil, ex)

    # guardar obs_hist (para change-point e diagnósticos)
    oh = prof.setdefault("obs_hist", {}).setdefault(str(ex), [])
    try:
        oh.append({
            "dt": str(latest.get("dt", latest.get("data", "")) or ""),
            "e1rm": float(obs_best),
            "w": float(obs_w),
            "reps": float(obs_r),
            "rir_eff": float(obs_rir_eff),
        })
        oh = sorted(oh, key=lambda x: str(x.get("dt","")))[-30:]
        prof["obs_hist"][str(ex)] = oh
    except Exception:
        pass

    # Multi-braço recompensa (inferido): que estratégia tu usaste de facto?
    arm_used = "hold"
    try:
        w_prev = float(prev.get("peso_medio", 0) or 0) if prev else 0.0
        w_now = float(latest.get("peso_medio", 0) or 0)
        reps_prev = float(prev.get("reps_media", 0) or 0) if prev else 0.0
        reps_now = float(latest.get("reps_media", 0) or 0)
        if w_prev > 0 and abs(w_now - w_prev) <= max(0.5, w_prev * 0.01) and reps_now > reps_prev + 0.5:
            arm_used = "add_rep"
        elif w_prev > 0 and w_now > w_prev + max(0.5, w_prev * 0.01):
            arm_used = "micro_load"
        else:
            arm_used = "hold"
    except Exception:
        arm_used = "hold"

    # recompensa: e1RM subiu (>= +0.25%) ou segurou bem (>= -0.25%)
    reward = 0
    try:
        prev_hist = [x for x in oh[:-1] if float(x.get("e1rm", 0) or 0) > 0]
        if prev_hist:
            prev_e1 = float(prev_hist[-1].get("e1rm", 0) or 0)
            if prev_e1 > 0:
                chg = (float(obs_best) - prev_e1) / prev_e1
                if chg >= 0.0025:
                    reward = 1
                elif chg >= -0.0025:
                    reward = 1 if arm_used == "hold" else 0
    except Exception:
        reward = 0

    _yami_bandit_update(perfil, ex, arm_used, reward)

    # atualizar last_key para evitar duplicação
    model["last_key"] = str(key)
    model["last_dt"] = str(latest.get("dt", latest.get("data", "")) or "")
    _yami_state_save(stt)

    return {"synced": True, "pred": pred, "arm_used": arm_used, "reward": int(reward), "key": str(key), "upd": upd}


def yami_explain_ai(
    ex: str,
    arm: str,
    pred: dict,
    changep: dict,
    readiness_label: str,
    reason_bits: list[str],
) -> str:
    """Texto curto 'LLM-like' (sem API)."""
    pat = str(pred.get("pattern", "") or "")
    mu = float(pred.get("mu", 0) or 0)
    sig = float(pred.get("sigma", 0) or 0)
    n = int(pred.get("n", 0) or 0)
    cp = bool(changep.get("flag", False))
    dp = float(changep.get("delta_pct", 0.0) or 0.0) * 100.0

    arm_pt = {"micro_load": "subir micro-carga", "add_rep": "ganhar reps", "hold": "manter/gerir fadiga"}.get(str(arm), str(arm))
    bits = [b for b in (reason_bits or []) if b]
    extra = ""
    if bits:
        extra = " " + " ".join(bits[:2])

    variants = [
        f"Estratégia hoje: **{arm_pt}**. Modelo ({pat}) estima e1RM ~{mu:.0f}±{sig:.0f} (n={n}).{extra}",
        f"Vou por **{arm_pt}**. Estás em '{readiness_label}'. e1RM estimado {mu:.0f}±{sig:.0f}.{extra}",
        f"Decisão: **{arm_pt}** com base no teu padrão ({pat}) e consistência recente. Incerteza: ±{sig:.0f}.{extra}",
    ]
    if cp:
        variants.insert(0, f"Estou a ver uma **queda persistente** (~{dp:.1f}%). Hoje é dia de **segurança**: {arm_pt}.{extra}")
    # determinístico por contexto (para não mudar a cada clique)
    perfil_key = str(st.session_state.get('perfil_sel', '') or '')
    today = datetime.date.today().isoformat()
    seed_str = f"{perfil_key}|{ex}|{arm}|{pat}|{mu:.2f}|{sig:.2f}|{int(cp)}|{readiness_label}|{today}"
    seed = int(hashlib.sha256(seed_str.encode('utf-8')).hexdigest()[:16], 16)
    idx = seed % max(1, len(variants))
    return variants[int(idx)]


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


def _is_composto_exercicio(ex_name: str, item: dict | None = None) -> bool:
    """Heurística para classificar 'composto' quando o plano não traz 'tipo'."""
    try:
        tipo = str((item or {}).get("tipo", "")).strip().lower()
        if tipo:
            return tipo == "composto"
    except Exception:
        pass

    ex = str(ex_name or "").lower()

    # isoladores/acessórios típicos (evita falsos positivos)
    isol_keys = [
        "curl", "extens", "extensão", "extensao", "pushdown", "tríceps", "triceps",
        "elevação", "elevacao", "lateral", "fly", "crucif", "peck", "kickback",
        "panturrilha", "calf", "abductor", "adutor", "abdutor", "adutor",
        "shrug", "face pull", "pullover"
    ]
    if any(k in ex for k in isol_keys):
        return False

    comp_keys = [
        "supino", "bench", "press", "ohp", "overhead", "agach", "squat",
        "deadlift", "rdl", "levantamento terra", "remada", "row",
        "barra fixa", "pull-up", "chin-up", "dips", "leg press", "hack", "belt squat"
    ]
    return any(k in ex for k in comp_keys)


def _yami_granularidade_peso(ex: str, item: dict | None = None) -> float:
    """Passo mínimo (kg) para arredondar sugestões de carga, alinhado com o equipamento real."""
    try:
        tipo = str((item or {}).get("tipo", "")).strip().lower()
    except Exception:
        tipo = ""

    is_lower = _is_lower_exercise(ex)
    is_comp = (tipo == "composto") if tipo else _is_composto_exercicio(ex, item)

    if is_lower and is_comp:
        return 5.0
    if is_comp:
        return 2.5
    return 1.0

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



def _yami_is_composto(ex: str, item: dict) -> bool:
    """Heurística para classificar composto vs isolador quando o plano não traz 'tipo'.

    Regras:
    - se item['tipo'] contém 'comp' -> composto
    - se contém 'isol'/'acess' -> isolador
    - fallback por palavras-chave no nome do exercício
    """
    try:
        tipo = str(item.get("tipo", "") or "").strip().lower()
    except Exception:
        tipo = ""
    if "comp" in tipo:
        return True
    if "isol" in tipo or "acess" in tipo:
        return False

    exl = str(ex or "").lower()

    comp_kw = [
        "supino", "bench", "press", "agach", "squat", "terra", "deadlift", "rdl",
        "remada", "row", "barra fixa", "pull-up", "pull up", "chin", "dip",
        "lunge", "leg press", "hack", "hip thrust", "clean", "snatch",
        "overhead", "military", "puxada", "pull", "push"
    ]
    iso_kw = [
        "curl", "bíceps", "biceps", "tríceps", "triceps", "elevação", "elevacao",
        "extensão", "extensao", "fly", "crucif", "panturr", "géme", "geme",
        "abdu", "addu", "face pull", "pullover", "pushdown", "kickback",
        "peck deck", "leg extension", "leg curl", "machine fly"
    ]

    if any(k in exl for k in comp_kw):
        return True
    if any(k in exl for k in iso_kw):
        return False

    # fallback: se for lower-body, assume composto (tende a ser)
    try:
        if _is_lower_exercise(ex):
            return True
    except Exception:
        pass

    # último fallback: mais seguro assumir composto (evita micro-incrementos ridículos)
    return True


def _yami_peso_granularidade(ex: str, item: dict) -> float:
    """Granularidade realista de incrementos, para evitar sugestões tipo +0.5kg em barra."""
    try:
        is_lower = _is_lower_exercise(ex)
    except Exception:
        is_lower = False
    is_comp = _yami_is_composto(ex, item)

    if is_lower and is_comp:
        return 5.0
    if is_comp:
        return 2.5
    return 1.0


def _yami_inc_steps(ex: str, item: dict) -> tuple[float, float]:
    """Incrementos típicos (subir/descer) para ajustes intra-sessão.

    Nota: respeita a granularidade realista (ex.: barra -> 2.5kg, lower composto -> 5kg),
    para não sugerir coisas impraticáveis tipo +0.5kg.
    """
    gran = _yami_peso_granularidade(ex, item)
    return float(gran), float(gran)




def _yami_weight_profile_for_item(ex: str, item: dict, peso_base: float, df_last: pd.DataFrame | None = None) -> list[float]:
    gran = float(_yami_granularidade_peso(ex, item))

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
                    out = [float(_round_to_nearest(base * ratios[s], gran)) for s in range(series_n)]
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

            out = [float(_round_to_nearest(base_adj * m, gran)) for m in mults]
            return out

    # 3) Default: constante (o ajuste série-a-série vem da performance real)
    return [float(_round_to_nearest(base, gran)) for _ in range(series_n)]


def _yami_suggest_weight_for_series(
    perfil: str,
    ex: str,
    item: dict,
    peso_base: float,
    df_last: pd.DataFrame | None,
    df_hist: pd.DataFrame | None,
    pending_sets: list,
    series_index: int,
    rir_target_num: float,
    bloco: str = "",
    semana: int = 1,
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
        is_comp = _yami_is_composto(ex, item)
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

    # micro-steps (respeita a granularidade real)
    inc_micro = _yami_peso_granularidade(ex, item)


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

        # --- YAMI AI+: otimização probabilística por série ---
    try:
        rest_s = float(item.get('descanso_s', 120) or 120)
    except Exception:
        rest_s = 120.0
    try:
        total_sets = int(item.get('series', 0) or (len(profile) if profile else 1))
    except Exception:
        total_sets = 1
    try:
        week_pen = float(yami_week_penalty(df_hist, perfil, ex) or 0.0) if df_hist is not None else 0.0
    except Exception:
        week_pen = 0.0
    try:
        _tech = yami_tech_flag(perfil, ex)
        if _tech.get('flag', False) and sug > last_w:
            # se há sinal de quebra técnica, evita subir nesta série
            sug = float(last_w)
    except Exception:
        pass
    try:
        opt = yami_pick_weight_optimized(
            perfil=perfil,
            ex=ex,
            item=item,
            base_weight=float(sug),
            target_reps=int(target_reps),
            rir_target=float(rir_target_num),
            rest_s=float(rest_s),
            set_idx=int(s_idx),
            total_sets=int(max(1, total_sets)),
            bloco=str(bloco or ''),
            pain_risk=0.0,
            week_penalty=float(week_pen),
        )
        sug = float(opt.get('w', sug) or sug)
    except Exception:
        pass

    gran = _yami_peso_granularidade(ex, item)
    return float(_round_to_nearest(sug, gran))



def _prefill_sets_from_last(i, item, df_last, peso_sug, reps_low, rir_target_num, use_df_exact: bool = True):
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
            payload["reps"].append(int(reps_low))

        if use_df_exact and s < len(rirs) and pd.notna(rirs[s]):
            payload["rir"].append(float(rirs[s]))
        else:
            payload["rir"].append(float(rir_target_num))

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
    # a prioriidade: separador de listas é vírgula; decimal pode vir com ponto.
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

    # Esquemas especiais (agrupamentos / 4(5/4/3/2/1)) -> usar números apenas como referência leve
    out.update({'kind': 'special', 'low': min(nums), 'high': max(nums), 'expected': nums})
    return out


def _reps_bounds_from_item(item: dict) -> tuple[dict, int, int]:
    """Devolve (rep_info, reps_low, reps_high) a partir do texto de reps do item.

    Preferimos ter sempre low/high definidos (mesmo em esquemas fixos/seq),
    para evitar NameError e para suportar defaults coerentes na UI.
    """
    try:
        rep_text = str((item or {}).get("reps", "") or "")
    except Exception:
        rep_text = ""
    try:
        series_hint = int((item or {}).get("series", 0) or 0)
    except Exception:
        series_hint = 0

    rep_info = _parse_rep_scheme(rep_text, series_hint)
    kind = str(rep_info.get("kind") or "")

    reps_low, reps_high = 0, 0

    if kind == "fixed_seq":
        seq = []
        for x in (rep_info.get("expected") or []):
            try:
                v = int(float(x) or 0)
                if v > 0:
                    seq.append(v)
            except Exception:
                pass
        if seq:
            reps_low, reps_high = int(min(seq)), int(max(seq))
    else:
        try:
            reps_low = int(rep_info.get("low") or 0)
        except Exception:
            reps_low = 0
        try:
            reps_high = int(rep_info.get("high") or reps_low or 0)
        except Exception:
            reps_high = 0

    # fallback: tenta extrair pelo menos um número do texto; senão, default simples
    if reps_low <= 0 and reps_high <= 0:
        try:
            m = re.search(r"\d+", rep_text)
            if m:
                reps_low = reps_high = int(m.group(0))
        except Exception:
            pass
    if reps_low <= 0 and reps_high <= 0:
        reps_low, reps_high = 8, 12

    if reps_high <= 0:
        reps_high = reps_low

    return rep_info, int(reps_low), int(reps_high)


def _default_reps_for_set(rep_info: dict, set_index: int, reps_low: int, reps_high: int, prefer_max: bool = True) -> int:
    """Default de reps para uma série.

    - Em sequências fixas (15/12/10/8), devolve o valor da série.
    - Em ranges, usa por defeito o topo da faixa (prefer_max=True).
    """
    kind = str((rep_info or {}).get("kind") or "")
    try:
        s = int(set_index)
    except Exception:
        s = 0

    if kind == "fixed_seq":
        seq = (rep_info or {}).get("expected") or []
        try:
            if 0 <= s < len(seq):
                v = int(float(seq[s]) or 0)
                if v > 0:
                    return v
        except Exception:
            pass
        return int(max(1, reps_high if reps_high > 0 else reps_low if reps_low > 0 else 1))

    if prefer_max:
        return int(reps_high if reps_high > 0 else reps_low if reps_low > 0 else 1)
    return int(reps_low if reps_low > 0 else reps_high if reps_high > 0 else 1)




# =========================================================
# 🧠 YAMI — HIGIENE/INSPEÇÃO DE DADOS (para decisões estáveis)
# =========================================================

def _yami_df_signature(df: pd.DataFrame) -> str:
    """Assinatura leve do DF para cache em sessão (evita recomputar limpeza/diagnóstico)."""
    try:
        if df is None or df.empty:
            return "empty"
        n = int(len(df))
        tail = df.tail(1)
        if tail.empty:
            return f"n={n}"
        r = tail.iloc[0].to_dict()
        core = {
            "n": n,
            "Data": str(r.get("Data", "")),
            "Perfil": str(r.get("Perfil", "")),
            "Dia": str(r.get("Dia", "")),
            "Bloco": str(r.get("Bloco", "")),
            "Plano_ID": str(r.get("Plano_ID", "")),
            "Exercício": str(r.get("Exercício", "")),
            "Peso": str(r.get("Peso", "")),
            "Reps": str(r.get("Reps", "")),
            "RIR": str(r.get("RIR", "")),
        }
        return hashlib.sha256(json.dumps(core, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    except Exception:
        return "sig_err"

def _yami_cell_to_list(v) -> list:
    """Converte uma célula (número ou lista em string) numa lista de floats."""
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return []
        if isinstance(v, (int, float)):
            return [float(v)]
        s = str(v).strip()
        if not s:
            return []
        # aceita formatos: "70;72.5" | "70, 72.5" | "70/72.5" | "70 72.5"
        s = s.replace(",", ";").replace("/", ";").replace("|", ";")
        parts = [p.strip() for p in s.split(";") if p.strip() != ""]
        out = []
        for p in parts:
            p2 = p.replace("kg", "").replace("KG", "").strip()
            try:
                out.append(float(p2))
            except Exception:
                # tenta extrair número dentro de texto
                m = re.search(r"(-?\d+(?:\.\d+)?)", p2)
                if m:
                    try:
                        out.append(float(m.group(1)))
                    except Exception:
                        pass
        return out
    except Exception:
        return []

def yami_df_limpo_para_yami(df_hist: pd.DataFrame, perfil: str) -> pd.DataFrame:
    """Limpa (apenas para o Yami) e estabiliza ordenação:
    - parse de data (dayfirst)
    - converte Peso/Reps/RIR em numérico (quando possível)
    - remove linhas obviamente inválidas
    - dedup por assinatura (evita duplicados por rerun)
    - mantém uma ordem determinística (data + índice)
    """
    try:
        if df_hist is None or df_hist.empty:
            return pd.DataFrame(columns=SCHEMA_COLUMNS)
        if "Perfil" not in df_hist.columns:
            return df_hist.copy()

        sig = f"{perfil}|{_yami_df_signature(df_hist)}"
        cache_key = st.session_state.get("_yami_df_clean_key")
        cache_df = st.session_state.get("_yami_df_clean_df")
        if cache_key == sig and isinstance(cache_df, pd.DataFrame):
            return cache_df.copy()

        dfp = df_hist[df_hist["Perfil"].astype(str) == str(perfil)].copy()
        if dfp.empty:
            out = dfp
        else:
            dfp["__idx"] = list(range(len(dfp)))
            dfp["__dt"] = pd.to_datetime(dfp.get("Data"), dayfirst=True, errors="coerce")
            # mantém Data como texto original, mas remove datas inválidas
            dfp = dfp.dropna(subset=["__dt"])

            # tenta converter Peso/Reps/RIR se forem escalares; se forem listas em string, deixa como string
            for c in ["Peso", "Reps", "RIR"]:
                if c in dfp.columns:
                    # só converte quando parece escalar (não contém separadores típicos)
                    s = dfp[c].astype(str)
                    mask_list = s.str.contains(r"[;|/]", regex=True) | s.str.contains(r"\b\d+\s+\d+\b", regex=True)
                    conv = pd.to_numeric(dfp.loc[~mask_list, c], errors="coerce")
                    dfp.loc[~mask_list, c] = conv

            # remove sets impossíveis quando temos valores escalares
            if "Peso" in dfp.columns and "Reps" in dfp.columns:
                w = pd.to_numeric(dfp["Peso"], errors="coerce")
                r = pd.to_numeric(dfp["Reps"], errors="coerce")
                ok = (w.isna() | (w > 0)) & (r.isna() | (r > 0))
                dfp = dfp[ok]

            # dedup por assinatura das colunas principais (evita duplicados por rerun)
            sig_cols = [c for c in ["Data","Perfil","Dia","Bloco","Plano_ID","Exercício","Peso","Reps","RIR"] if c in dfp.columns]
            if sig_cols:
                dfp["__sig"] = dfp[sig_cols].astype(str).agg("|".join, axis=1)
                dfp = dfp.sort_values(["__dt", "__idx"], ascending=[True, True])
                dfp = dfp.drop_duplicates("__sig", keep="last")

            out = dfp.sort_values(["__dt", "__idx"], ascending=[True, True])

        try:
            st.session_state["_yami_df_clean_key"] = sig
            st.session_state["_yami_df_clean_df"] = out.copy()
        except Exception:
            pass
        return out.copy()
    except Exception:
        return df_hist.copy() if isinstance(df_hist, pd.DataFrame) else pd.DataFrame(columns=SCHEMA_COLUMNS)

def yami_inspecao_geral(df_hist: pd.DataFrame, perfil: str) -> dict:
    """Inspeção geral dos dados (não altera a sheet). Devolve contagens e problemas prováveis."""
    out = {
        "perfil": str(perfil),
        "linhas": 0,
        "datas_unicas": 0,
        "exercicios_unicos": 0,
        "datas_invalidas": 0,
        "faltas_peso": 0,
        "faltas_reps": 0,
        "faltas_rir": 0,
        "rir_fora": 0,
        "reps_fora": 0,
        "peso_fora": 0,
        "duplicados": 0,
        "problemas": [],
    }
    try:
        if df_hist is None or df_hist.empty:
            out["problemas"].append("Sem dados na sheet (ou falha de leitura).")
            return out
        if "Perfil" not in df_hist.columns:
            out["problemas"].append("Coluna 'Perfil' não existe. Schema inesperado.")
            return out

        dfp = df_hist[df_hist["Perfil"].astype(str) == str(perfil)].copy()
        out["linhas"] = int(len(dfp))
        if dfp.empty:
            out["problemas"].append("Sem linhas para este perfil.")
            return out

        dt = pd.to_datetime(dfp.get("Data"), dayfirst=True, errors="coerce")
        out["datas_invalidas"] = int(dt.isna().sum())
        dfp["__dt"] = dt
        out["datas_unicas"] = int(dfp["__dt"].dropna().dt.date.nunique())

        if "Exercício" in dfp.columns:
            out["exercicios_unicos"] = int(dfp["Exercício"].astype(str).nunique())

        # faltas
        if "Peso" in dfp.columns:
            out["faltas_peso"] = int(dfp["Peso"].isna().sum())
        if "Reps" in dfp.columns:
            out["faltas_reps"] = int(dfp["Reps"].isna().sum())
        if "RIR" in dfp.columns:
            out["faltas_rir"] = int(dfp["RIR"].isna().sum())

        # fora de gama (apenas quando são escalares)
        w = pd.to_numeric(dfp["Peso"], errors="coerce") if "Peso" in dfp.columns else pd.Series(dtype=float)
        r = pd.to_numeric(dfp["Reps"], errors="coerce") if "Reps" in dfp.columns else pd.Series(dtype=float)
        rir = pd.to_numeric(dfp["RIR"], errors="coerce") if "RIR" in dfp.columns else pd.Series(dtype=float)

        if not w.empty:
            out["peso_fora"] = int(((w > 400) | (w < 0)).sum())  # 400kg já é o suficiente para acusar outlier
        if not r.empty:
            out["reps_fora"] = int(((r > 50) | (r < 0)).sum())
        if not rir.empty:
            out["rir_fora"] = int(((rir > 10) | (rir < 0)).sum())

        # duplicados prováveis
        sig_cols = [c for c in ["Data","Perfil","Dia","Bloco","Plano_ID","Exercício","Peso","Reps","RIR"] if c in dfp.columns]
        if sig_cols:
            sigs = dfp[sig_cols].astype(str).agg("|".join, axis=1)
            out["duplicados"] = int(sigs.duplicated().sum())

        # problemas resumidos
        if out["datas_invalidas"] > 0:
            out["problemas"].append(f"{out['datas_invalidas']} linhas com 'Data' inválida (formato estranho).")
        if out["duplicados"] > 0:
            out["problemas"].append(f"{out['duplicados']} duplicados prováveis (pode acontecer em reruns).")
        if out["rir_fora"] > 0:
            out["problemas"].append(f"{out['rir_fora']} linhas com RIR fora de 0–10.")
        if out["reps_fora"] > 0:
            out["problemas"].append(f"{out['reps_fora']} linhas com reps fora do normal (0–50).")
        if out["peso_fora"] > 0:
            out["problemas"].append(f"{out['peso_fora']} linhas com peso fora do normal (<0 ou >400).")
        return out
    except Exception:
        out["problemas"].append("Falha ao analisar os dados (erro interno).")
        return out


def _historico_resumos_exercicio(df: pd.DataFrame, perfil: str, ex: str) -> list:
    """Resumo por sessão/dia para um exercício.
    Nota: a sheet tem 1 linha por set (schema atual), mas suportamos legado com listas na célula.
    Para o Yami, o que interessa é agrupar sets do mesmo dia (e plano) para evitar "histórico por set"
    que deixa as sugestões instáveis.
    """
    if df is None or getattr(df, 'empty', True):
        return []
    if 'Perfil' not in df.columns or 'Exercício' not in df.columns:
        return []

    # limpeza + ordenação determinística (só para o Yami)
    d0 = yami_df_limpo_para_yami(df, perfil)
    if d0 is None or getattr(d0, 'empty', True):
        return []

    d = d0[d0['Exercício'].astype(str) == str(ex)].copy()
    if d.empty:
        return []

    # chaves de sessão (a melhor proxy sem timestamp)
    group_cols = [c for c in ['Data', 'Plano_ID', 'Dia', 'Bloco'] if c in d.columns]
    if not group_cols:
        group_cols = ['Data']

    # garante __dt e __idx
    if "__dt" not in d.columns:
        d["__dt"] = pd.to_datetime(d.get('Data'), dayfirst=True, errors='coerce')
    if "__idx" not in d.columns:
        d["__idx"] = list(range(len(d)))

    out = []
    # agrupa por sessão e agrega sets
    for gkey, g in d.groupby(group_cols, dropna=False):
        try:
            g = g.sort_values("__idx", ascending=True)
        except Exception:
            pass

        pesos, reps, rirs = [], [], []
        for _, row in g.iterrows():
            pesos += _yami_cell_to_list(row.get('Peso'))
            reps += _yami_cell_to_list(row.get('Reps'))
            rirs += _yami_cell_to_list(row.get('RIR'))

        # normaliza: reps como int quando possível
        reps_num = [x for x in reps if x is not None and not (isinstance(x, float) and pd.isna(x))]
        rirs_num = [x for x in rirs if x is not None and not (isinstance(x, float) and pd.isna(x))]
        pesos_num = [x for x in pesos if x is not None and not (isinstance(x, float) and pd.isna(x))]

        n_sets = max(len(pesos_num), len(reps_num), len(rirs_num))
        if n_sets <= 0:
            continue

        dt = None
        try:
            dt = g["__dt"].max()
        except Exception:
            dt = None

        out.append({
            'data': str(g.iloc[0].get('Data', '—')),
            'dt': dt,
            'peso_medio': float(sum(pesos_num)/len(pesos_num)) if pesos_num else 0.0,
            'reps_media': float(sum(reps_num)/len(reps_num)) if reps_num else 0.0,
            'reps_min': int(min(reps_num)) if reps_num else 0,
            'reps_max': int(max(reps_num)) if reps_num else 0,
            'rirs_media': float(sum(rirs_num)/len(rirs_num)) if rirs_num else None,
            'n_sets': int(n_sets),
            'pesos': [float(x) for x in pesos_num],
            'reps': [int(round(float(x))) for x in reps_num],
            'rirs': [float(x) for x in rirs_num],
            'sess_key': str(gkey),
        })

    out = sorted(out, key=lambda x: (x.get('dt') is not None, x.get('dt')), reverse=True)
    return out




def yami_coach_sugestao(df_hist: pd.DataFrame, perfil: str, ex: str, item: dict, bloco: str, semana: int, plano_id: str) -> dict:
    """Coach de progressão ('Yami'): sugere carga e explica o porquê, com heurística mais robusta."""
    yami_mode = str(st.session_state.get('yami_mode', 'Brutal'))

    series_alvo = int(item.get('series', 0) or 0)
    rep_info = _parse_rep_scheme(item.get('reps', ''), series_alvo)
    rir_alvo_base = float(rir_alvo_num(item.get('tipo', ''), bloco, semana) or 2.0)
    rir_alvo_num_ = float(yami_adjust_rir_target(rir_alvo_base, item))
    read = st.session_state.get('yami_readiness', {}) or {}
    try:
        read_score_delta = float(read.get('score_delta', 0.0) or 0.0)
        read_adj_pct = float(read.get('adj_load_pct', 0.0) or 0.0)
        read_label = str(read.get('label', 'Normal') or 'Normal')
    except Exception:
        read_score_delta, read_adj_pct, read_label = 0.0, 0.0, 'Normal'

    # prontidão latente (automática) + sinais do corpo (dor) influenciam decisões
    pain_bucket = int(st.session_state.get("yami_pain_bucket", 0) or 0)
    pain_flags = st.session_state.get("yami_pain_flags", {}) or {}

    lat = yami_prontidao_latente(perfil, ex)
    lat_adj = float(lat.get("adj_load_pct", 0.0) or 0.0)
    lat_score = float(lat.get("score_delta", 0.0) or 0.0)
    lat_label = str(lat.get("label", "latente: normal") or "latente: normal")

    # dor: ajuste pequeno, mas real (não é para te “punir”; é para não agravar)
    pain_adj = 0.0
    pain_score = 0.0
    if pain_bucket == 1:
        pain_adj = -0.02
        pain_score = -0.20
    elif pain_bucket >= 2:
        pain_adj = -0.04
        pain_score = -0.35

    # combina (check-in + latente + dor)
    read_adj_pct = float(read_adj_pct) + float(lat_adj) + float(pain_adj)
    read_score_delta = float(read_score_delta) + float(lat_score) + float(pain_score)

    # etiqueta para aparecer no “porquê”
    _bits_lbl = []
    if lat_label and "normal" not in lat_label:
        _bits_lbl.append(lat_label)
    if pain_bucket > 0:
        _bits_lbl.append("sinais do corpo")
    if _bits_lbl:
        read_label = f"{read_label} · " + " · ".join(_bits_lbl)



    hist = _historico_resumos_exercicio(df_hist, perfil, ex)
    latest = hist[0] if hist else None
    prev = hist[1] if len(hist) > 1 else None
    prev2 = hist[2] if len(hist) > 2 else None

    # Cache por contexto (Streamlit rerun): garante que ao clicar no botão o Yami não muda
    # a sugestão nem a justificação sem haver dados novos.
    try:
        latest_key = ""
        if latest:
            latest_key = f"{latest.get('data','')}|{latest.get('pesos', [])}|{latest.get('reps', [])}|{latest.get('rirs', [])}"
        cache_blob = {
            "perfil": str(perfil),
            "ex": str(ex),
            "plano_id": str(plano_id),
            "bloco": str(bloco),
            "semana": int(semana),
            "yami_mode": str(yami_mode),
            "item_reps": str(item.get("reps", "")),
            "item_series": int(item.get("series", 0) or 0),
            "item_tipo": str(item.get("tipo", "")),
            "rir_alvo": float(rir_alvo_num_),
            "read_label": str(read_label),
            "read_adj_pct": float(read_adj_pct),
            "read_score_delta": float(read_score_delta),
            "latest_key": str(latest_key),
        }
        cache_key = hashlib.sha256(json.dumps(cache_blob, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        _cache = st.session_state.setdefault("_yami_coach_cache", {})
        if cache_key in _cache:
            return dict(_cache[cache_key])
    except Exception:
        cache_key = None
    # --- YAMI IA: sincroniza modeloo (Kalman) + escolhe estratégia (multi-braço) ---
    pred_ai = {"mu": 0.0, "sigma": 999.0, "n": 0, "pattern": yami_exercise_pattern(ex)}
    arm_ai = "micro_load"
    changep = {"flag": False, "delta_pct": 0.0}
    try:
        if latest:
            _ = yami_sync_model_from_history(perfil, ex, latest, prev)
        pred_ai = yami_kalman_predict(perfil, ex)
        ctx_key = yami_context_key(perfil, bloco, pain_bucket=pain_bucket)
        arm_ai = yami_ctx_bandit_pick(perfil, ex, ctx_key)
        changep = yami_detect_changepoint(perfil, ex)
    except Exception:
        pass

    is_lower = _is_lower_exercise(ex)
    is_comp = str(item.get('tipo', '')).lower() == 'composto'
    if is_lower and is_comp:
        inc_up = inc_down = 5.0
    elif is_comp:
        inc_up = inc_down = 2.5
    else:
        inc_up = inc_down = 1.0


    # granularidade de arredondamento (passo mínimo de carga) para este exercício
    gran = float(inc_up)

    def _fmt_inc(v: float) -> str:
        return str(int(v)) if float(v).is_integer() else str(v)

    if not latest or float(latest.get('peso_medio', 0) or 0) <= 0:
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

    p_atual = float(latest.get('peso_medio', 0) or 0)
    reps_list = list(latest.get('reps', []) or [])
    rirs_list = [float(x) for x in list(latest.get('rirs', []) or []) if x is not None]
    reps_media = float(latest.get('reps_media', 0) or 0)
    rir_media = None if latest.get('rirs_media') is None else float(latest.get('rirs_media'))

    rir_eff = None if rir_media is None else float(rir_media)
    if rir_eff is not None:
        rir_eff = max(0.0, min(10.0, float(rir_eff)))


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
        f"Último treino ({latest.get('data','—')}): {latest.get('n_sets',0)}/{series_alvo or latest.get('n_sets',0)} séries · média {p_atual:.1f} kg · {reps_media:.1f} reps"
        + (f" · RIR {rir_media:.1f}" if rir_media is not None else "")
    )
    # IA: estimativa com incerteza + estratégia escolhida
    try:
        _mu = float(pred_ai.get("mu", 0) or 0)
        _sig = float(pred_ai.get("sigma", 0) or 0)
        _n = int(pred_ai.get("n", 0) or 0)
        _pat = str(pred_ai.get("pattern", "") or "")
        _arm_pt = {"micro_load":"micro-carga","add_rep":"reps","hold":"segurar"}.get(str(arm_ai), str(arm_ai))
        if _mu > 0 and _sig > 0:
            reasons.append(f"IA: {_pat} · e1RM ~{_mu:.0f}±{_sig:.0f} (n={_n}) · estratégia: {_arm_pt}.")
    except Exception:
        pass
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
        same_load_streak.append(float(h.get('peso_medio', 0) or 0))
    stable_load = False
    if len(same_load_streak) >= 2:
        stable_load = (max(same_load_streak[:2]) - min(same_load_streak[:2])) <= max(0.5, p_atual * 0.01)

    if prev and float(prev.get('peso_medio', 0) or 0) > 0:
        p_prev = float(prev.get('peso_medio', 0) or 0)
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
        pesos_trio = [float(h.get('peso_medio', 0) or 0) for h in trio]
        same_load_3 = (max(pesos_trio) - min(pesos_trio)) <= max(0.5, p_atual * 0.01)
        if same_load_3:
            reps_trio = [float(h.get('reps_media', 0) or 0) for h in trio]
            # sem evolução real nas reps e RIR a cair -> sinal de carga alta/fadiga
            if max(reps_trio) - min(reps_trio) < 0.75:
                stall_flag = True
                if all((h.get('rirs_media') is not None and float(h.get('rirs_media')) <= max(0.5, rir_alvo_num_ - 0.5)) for h in trio if h.get('rirs_media') is not None):
                    overload_flag = True

    score = 0.0

    if deload_now:
        p_sug = max(0.0, _round_to_nearest(p_atual * 0.88, gran))
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

    # RIR vs alvo
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

    if stall_flag:
        score -= 0.5
        reasons.append('Estagnação recente (2–3 sessões) detectada na mesma carga.')
    if overload_flag:
        score -= 0.75
        reasons.append('Estagnação + RIR baixo recorrente: sinal de fadiga/carga alta.')

    # Prontidão do dia (check-in) — pode inclinar a decisão
    try:
        if abs(float(read_score_delta)) > 1e-9 or abs(float(read_adj_pct)) > 1e-9:
            score += float(read_score_delta)
            reasons.append(f"Prontidão hoje: {read_label} (ajuste {float(read_adj_pct)*100:+.0f}% carga).")
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
        inc_micro = max(gran, float(inc_up) / 2.0)
    except Exception:
        inc_micro = gran

    if score >= 2.25:
        acao = f"+{_fmt_inc(inc_up)}kg"
        p_sug = _round_to_nearest(p_atual + inc_up, gran)
        resumo = 'Boa execução. Vamos subir — sem pressa, mas sem medo.'
    elif score >= 0.6:
        acao = f"+{_fmt_inc(inc_micro)}kg"
        p_sug = _round_to_nearest(p_atual + inc_micro, gran)
        resumo = 'Margem pequena, mas real. Sobe micro e mantém a técnica limpa.'
    elif score <= -2.25:
        acao = f"Baixa {_fmt_inc(inc_down)}kg"
        p_sug = max(0.0, _round_to_nearest(p_atual - inc_down, gran))
        resumo = 'Isto está pesado para o alvo de hoje. Regride um passo e volta a construir.'
    elif score <= -0.6:
        # micro-regressão (mais frequente em isoladores; em compostos tende a "manter" antes de baixar)
        if is_comp and score > -1.0:
            acao = 'Mantém carga'
            p_sug = _round_to_nearest(p_atual, gran)
            resumo = 'Está a apertar. Mantém e garante reps limpas.'
        else:
            acao = f"Baixa {_fmt_inc(inc_micro)}kg"
            p_sug = max(0.0, _round_to_nearest(p_atual - inc_micro, gran))
            resumo = 'Baixa micro para bater reps/RIR com técnica.'
    else:
        acao = 'Mantém carga'
        p_sug = _round_to_nearest(p_atual, gran)
        resumo = 'Consolida. Ainda não há sinal limpo para mexer na carga.'

    # Ajuste por prontidão e deload recomendado
    try:
        if deload_force:
            acao = "DELOAD recomendado (-10%)"
            p_sug = max(0.0, _round_to_nearest(p_atual * 0.90, gran))
            resumo = 'Fadiga alta. Deload curto para voltares a subir com qualidade.'
        else:
            # prontidão: pode "puxar" ligeiramente a carga sugerida
            if abs(float(read_adj_pct)) > 1e-9:
                _pre = float(p_sug)
                _adj = float(_round_to_nearest(float(p_sug) * (1.0 + float(read_adj_pct)), gran))
                # em dias maus, não deixar subir só por score; em dias bons, permitir micro
                if float(read_adj_pct) < 0:
                    p_sug = min(float(p_sug), float(_adj))
                elif float(read_adj_pct) > 0:
                    p_sug = max(float(p_sug), float(_adj))

                _d2 = float(p_sug) - float(p_atual)
                if abs(_d2) < 0.25:
                    acao = "Mantém carga"
                    p_sug = float(_round_to_nearest(p_atual, gran))
                elif _d2 > 0:
                    acao = f"+{_fmt_inc(_d2)}kg"
                else:
                    acao = f"Baixa {_fmt_inc(abs(_d2))}kg"

                if abs(float(p_sug) - float(_pre)) >= 0.5:
                    resumo = resumo + f" (prontidão: {read_label})"
    except Exception:
        pass

    # --- YAMI IA: combinar heurística com modeloo probabilístico ---
    try:
        mu = float(pred_ai.get("mu", 0) or 0)
        sig = float(pred_ai.get("sigma", 999.0) or 999.0)

        # prontidão (check-in + latente + sinais do corpo) ajusta a estimativa do dia
        try:
            mu = float(mu) * (1.0 + float(read_adj_pct))
        except Exception:
            pass
        try:
            if int(pain_bucket) > 0:
                sig = float(sig) * (1.0 + 0.25 * float(pain_bucket))
        except Exception:
            pass
        n_ai = int(pred_ai.get("n", 0) or 0)
        pat = str(pred_ai.get("pattern", "") or "")
        cp_flag = bool(changep.get("flag", False))
        cp_drop = float(changep.get("delta_pct", 0.0) or 0.0)

        # define reps-alvo para o cálculo do peso (meio da faixa; se já bates topo, aponta topo)
        target_reps = 0
        if rep_kind == "fixed_seq":
            seq = list(rep_info.get("expected") or [])
            target_reps = int(seq[-1]) if seq else int(reps_media or 0)
        elif low > 0 and high > 0:
            target_reps = int(high)
        elif low > 0:
            target_reps = int(low)
        else:
            target_reps = max(1, int(round(reps_media or 1)))

        reps_to_fail_target = max(1.0, float(target_reps) + float(rir_alvo_num_))
        # peso que o modeloo "acha" que encaixa nesse alvo
        p_ai = 0.0
        if mu > 0:
            p_ai = float(mu) / (1.0 + (min(15.0, reps_to_fail_target) / 30.0))
            p_ai = float(_round_to_nearest(p_ai, gran))

        # probabilidade aproximada de bater o alvo (assumindo normal em e1RM)
        prob_hit = None
        if mu > 0 and sig > 1e-6 and p_ai > 0:
            req_e1 = float(p_ai) * (1.0 + (min(15.0, reps_to_fail_target) / 30.0))
            z = (req_e1 - mu) / sig
            # CDF normal via erf
            cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
            prob_hit = float(max(0.01, min(0.99, 1.0 - cdf)))

        # queda persistente -> força "hold" e puxa a carga para baixo
        if cp_flag:
            arm_ai = "hold"
            if cp_drop <= -0.03:
                # queda forte: descarrega 5%
                p_ai = max(0.0, float(_round_to_nearest(p_atual * 0.95, gran)))
            elif cp_drop <= -0.015:
                p_ai = max(0.0, float(_round_to_nearest(p_atual * 0.97, gran)))

        # mistura depende da incerteza
        # sig baixo + n bom -> confiar mais no modeloo; caso contrário, confiar mais na heurística
        blend = 0.55 if (n_ai >= 4 and sig <= 18.0) else 0.35
        if p_ai <= 0:
            blend = 0.0
        p_mix = float(_round_to_nearest(((1.0 - blend) * float(p_sug) + blend * float(p_ai)), gran))

        # aplica a estratégia escolhida
        if arm_ai == "add_rep":
            p_mix = float(_round_to_nearest(p_atual, gran))
            acao = "Mantém e soma reps"
            resumo = "Mantém carga e tenta +1 rep (sem trair o tempo)."
        elif arm_ai == "micro_load":
            if not (deload_now or deload_force):
                max_inc = float(inc_up)
                # se o sinal é bom mas o mix ficou tímido, sobe micro
                if hit_top_all and (rir_eff is None or float(rir_eff) >= float(rir_alvo_num_) - 0.25) and p_mix <= p_atual + 0.25:
                    micro = float(gran)
                    p_mix = float(_round_to_nearest(p_atual + min(max_inc, micro), gran))
                p_mix = min(p_atual + max_inc, p_mix)
            if p_mix > p_atual + 0.25:
                acao = f"+{_fmt_inc(p_mix - p_atual)}kg"
        else:
            # hold: por defeito não sobe; pode baixar se CP/fadiga
            p_mix = min(p_mix, float(_round_to_nearest(p_atual, gran))) if not (deload_now or deload_force) else p_mix
            if p_mix < p_atual - 0.25:
                acao = f"Baixa {_fmt_inc(p_atual - p_mix)}kg"
                resumo = "Gestão de fadiga: mantém qualidade e volta a construir."

        # aplicar prontidão (check-in + latente + sinais do corpo) também ao mix final da IA
        try:
            if abs(float(read_adj_pct)) > 1e-9:
                _pre_mix = float(p_mix)
                _adj_mix = float(_round_to_nearest(float(p_mix) * (1.0 + float(read_adj_pct)), gran))
                if float(read_adj_pct) < 0:
                    p_mix = min(float(p_mix), float(_adj_mix))
                elif float(read_adj_pct) > 0:
                    p_mix = max(float(p_mix), float(_adj_mix))

                if abs(float(p_mix) - float(_pre_mix)) >= (0.5 if gran <= 1.0 else gran - 1e-6):
                    _d_mix = float(p_mix) - float(_pre_mix)
                    reasons.append(f"IA: prontidão aplicada no peso sugerido ({_d_mix:+.1f} kg).")
        except Exception:
            pass

        p_sug = float(p_mix)

        # reforço de explicação (aparece na UI do chip)
        try:
            _bits = []
            if prob_hit is not None:
                _bits.append(f"Chance ~{int(round(prob_hit*100))}%")
            if cp_flag:
                _bits.append("queda persistente")
            resumo = yami_explain_ai(ex, arm_ai, pred_ai, changep, read_label, _bits) or resumo
        except Exception:
            pass

        if mu > 0 and sig > 0 and (prob_hit is not None):
            reasons.append(f"IA: alvo {target_reps} reps @RIR {rir_alvo_num_:.1f} · chance ~{int(round(prob_hit*100))}%.")

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

    # confiança (combina consistência da sessão + incerteza do modeloo)
    try:
        _sigma = float(pred_ai.get("sigma", 999.0) or 999.0)
        _n_ai = int(pred_ai.get("n", 0) or 0)
        _mult = float(pred_ai.get("obs_mult", 1.0) or 1.0)
    except Exception:
        _sigma, _n_ai, _mult = 999.0, 0, 1.0

    # base pela qualidade do registo
    if sessao_incompleta or sets_ratio < 0.75 or latest.get("n_sets", 0) < max(1, min(series_alvo, 2)):
        conf = "baixa"
    else:
        # modeloo ainda sem dados: baixa
        if _n_ai < 2 or _sigma >= 24.0:
            conf = "baixa"
        elif _n_ai >= 5 and _sigma <= 12.0 and _mult <= 1.35 and not bool(changep.get("flag", False)):
            conf = "alta"
        elif abs(score) >= 2 and (prev is not None) and _sigma <= 18.0 and _mult <= 1.7:
            conf = "alta"
        else:
            conf = "média"

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

    
    # --- YAMI AI+: penalização semanal (MPC-lite) + auditor + técnica + dor ---
    week_pen = 0.0
    try:
        week_pen = float(yami_week_penalty(df_hist, perfil, ex) or 0.0)
    except Exception:
        week_pen = 0.0

    # auditor de distribuição do plano
    try:
        for _w in (yami_audit_plan(df_hist, perfil) or []):
            if _w and _w not in reasons:
                reasons.append(_w)
    except Exception:
        pass

    # flag de técnica (sem vídeo)
    try:
        _tech = yami_tech_flag(perfil, ex)
        if _tech.get("flag", False):
            reasons.append(f"⚠️ Padrão de quebra técnica/fadiga no exercício (score {float(_tech.get('score',0) or 0):.2f}). Hoje joga mais limpo: mais descanso ou -1 micro-passo.")
            score -= 0.20
    except Exception:
        pass

    # risco de dor (modeloo aprendido) -> só entra se houver sinal/treino pesado
    pain_risk = 0.0
    try:
        _avg_w = float(p_atual)
        _avg_r = float(reps_media or 0)
        _avg_rir = float(rir_eff if rir_eff is not None else rir_alvo_num_)
        _pf = yami_pain_feat_simple(perfil, ex, item, _avg_w, _avg_r, _avg_rir, float(week_pen))
        _areas = ["joelho","ombro","cotovelo","lombar"]
        # se não há modeloo treinado, isto dá ~0.5 (neutro). Vamos baixar o impacto nesse caso.
        _prs = []
        for _a in _areas:
            _p = float(yami_pain_predict(perfil, ex, _pf, _a) or 0.0)
            _prs.append(_p)
        if _prs:
            pain_risk = max(_prs)
            if pain_risk >= 0.65:
                reasons.append("🩹 Risco alto de irritação hoje (estimativa). Sugiro variação mais amigável/ROM controlado e manter RIR mais alto.")
                score -= 0.30
            elif pain_risk >= 0.55:
                reasons.append("🩹 Risco moderado de irritação. Mantém técnica, evita grind e considera reduzir 1 micro-passo.")
                score -= 0.12
    except Exception:
        pain_risk = 0.0

    # guardar sugestão atual para aprender preferências (substituição manual)
    try:
        st.session_state.setdefault("yami_last_sug", {})[str(ex)] = float(p_sug)
    except Exception:
        pass
# peso de trabalho acompanha a variação sugerida (inclui prontidão)
    try:
        scale = float(p_sug) / float(p_atual) if float(p_atual) > 0 else 1.0
    except Exception:
        scale = 1.0
    # MPC-lite: se a semana já está pesada na família, desacelera um pouco
    try:
        if week_pen > 0 and (not deload_now) and (not deload_force):
            scale = float(scale) * max(0.90, 1.0 - 0.05 * float(week_pen))
    except Exception:
        pass

    if deload_now or deload_force or ('DELOAD' in str(acao)):
        scale = min(scale, 0.92)
    w_work_sug = float(_round_to_nearest(max(0.0, w_work_last * scale), gran))

    out = {
        'acao': acao,
        'peso_sugerido': float(p_sug),
        'delta': float(p_sug - p_atual),
        'confianca': conf,
        'resumo': resumo,
        'porque': str(porque),
        'razoes': reasons,
        'deload_reco': bool(deload_reco),
        'readiness': str(read_label),
        'rir_alvo': float(rir_alvo_num_),
'score': float(score),
        'peso_atual': float(p_atual),
        'peso_work_last': float(w_work_last),
        'peso_work_sugerido': float(w_work_sug),
    }

    try:
        if cache_key:
            st.session_state.setdefault("_yami_coach_cache", {})[cache_key] = dict(out)
    except Exception:
        pass
    return out


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


def guardar_sets_agrupados(perfil, dia, bloco, ex, lista_sets, req, justificativa="", item=None, semana=None, plano_id=None, df_hist=None, pain_flags=None):
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

        # --- YAMI AI+: aprende com o que acabaste de fazer (set-level) ---
        try:
            if item is None:
                item = {}
            yami_ai_update_from_saved_sets(
                perfil=str(perfil),
                ex=str(ex),
                item=dict(item) if isinstance(item, dict) else {},
                sets_list=list(lista_sets or []),
                bloco=str(bloco),
                df_hist=df_hist,
                pain_flags=pain_flags,
            )
        except Exception:
            pass

        # contextual multi-braço + preferência (o que tu fizeste vs o que era esperado)
        try:
            hist = _historico_resumos_exercicio(df_hist, str(perfil), str(ex)) if isinstance(df_hist, pd.DataFrame) else []
            prev = hist[0] if hist else None
            # arm usado (inferência simples)
            arm_used = "hold"
            try:
                w_prev = float(prev.get("peso_medio", 0) or 0) if prev else 0.0
            except Exception:
                w_prev = 0.0
            try:
                w_now = statistics.mean([float(s.get("peso", 0) or 0) for s in (lista_sets or []) if float(s.get("peso", 0) or 0) > 0])
            except Exception:
                w_now = 0.0
            try:
                reps_now = statistics.mean([float(s.get("reps", 0) or 0) for s in (lista_sets or []) if float(s.get("reps", 0) or 0) > 0])
                reps_prev = float(prev.get("reps_media", 0) or 0) if prev else 0.0
            except Exception:
                reps_now, reps_prev = 0.0, 0.0

            if w_prev > 0 and abs(w_now - w_prev) <= max(0.5, w_prev * 0.01) and reps_now > reps_prev + 0.5:
                arm_used = "add_rep"
            elif w_prev > 0 and w_now > w_prev + max(0.5, w_prev * 0.01):
                arm_used = "micro_load"
            else:
                arm_used = "hold"

            yami_pref_update_from_arm(str(perfil), str(ex), arm_used)

            # recompensa simples: sucesso médio (sem colapsar RIR) e sem muita dor
            reward = 0
            try:
                avg_rir = statistics.mean([float(s.get("rir", 0) or 0) for s in (lista_sets or []) if float(s.get("reps", 0) or 0) > 0])
            except Exception:
                avg_rir = 0.0
            pain_bucket = 1 if (pain_flags and any(bool(v) for v in pain_flags.values())) else 0
            if reps_now > 0 and avg_rir >= 0.5 and pain_bucket == 0:
                reward = 1

            ctx = yami_context_key(str(perfil), str(bloco), pain_bucket=int(pain_bucket))
            yami_ctx_bandit_update(str(perfil), str(ex), ctx, arm_used, reward)
        except Exception:
            pass

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

GUI_PPLA_ID = "GUI_PPLA_v1"
GUI_BLOCOS = {"PUSH", "PULL", "LEGS", "ARMS"}

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

def semana_label_por_plano(week: int, plano_id: str) -> str:
    if plano_id == GUI_PPLA_ID:
        return semana_label_gui(week)
    return semana_label(week)

def is_deload_for_plan(week: int, plano_id: str) -> bool:
    if plano_id == GUI_PPLA_ID:
        return is_gui_deload_week(week)
    return is_deload(week)

def rir_alvo(item_tipo, bloco, week):
    if bloco in GUI_BLOCOS:
        return "2–4" if is_gui_deload_week(week) else "2"
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
    if bloco in GUI_BLOCOS:
        return 75
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
            {"ex":"Remada unilateral com halteres", "series":3, "reps":"5-6", "tipo":"composto"},
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
            {"ex":"Deadlift", "series":4, "reps":"3-5", "tipo":"composto"},
            {"ex":"Bulgarian Split Squat (passo longo)", "series":3, "reps":"5-6", "tipo":"composto"},
            {"ex":"Hip Thrust (máquina)", "series":4, "reps":"5", "tipo":"composto"},
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
            {"ex":"Hip Thrust (barra)", "series":4, "reps":"8-10", "tipo":"composto"},
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
            {"ex":"Elevação lateral com halteres (myo-reps)", "series":3, "reps":"15-20", "tipo":"isolado"},
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

PLANOS = {"Base": treinos_base, "INEIX_ABC_v1": treinos_ineix, GUI_PPLA_ID: treinos_gui}

def gerar_treino_do_dia(dia, week, treinos_dict=None, plan_id="Base"):
    if plan_id == GUI_PPLA_ID:
        return gerar_treino_gui_dia(dia, week)
    treinos_dict = treinos_dict or treinos_base
    cfg = treinos_dict.get(dia, None)
    if not cfg:
        return {"bloco":"—","sessao":"","protocolos":{}, "exercicios":[]}
    bloco = cfg["bloco"]
    treino_final = []
    for item in cfg["exercicios"]:
        novo = dict(item)
        if ((plan_id == "Base" and is_deload(week) and bloco in ["Força","Hipertrofia"]) or (plan_id == GUI_PPLA_ID and is_gui_deload_week(week) and bloco in GUI_BLOCOS)):
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

# plano do perfil (preparado para ter planos diferentes no futuro)
plano_id_sel = get_plan_id_for_profile(perfil_sel, df_profiles) if df_profiles is not None else "Base"
if str(perfil_sel).strip().lower() == "ineix":
    plano_id_sel = "INEIX_ABC_v1"
elif str(perfil_sel).strip().lower() == "gui":
    plano_id_sel = GUI_PPLA_ID
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

# SEMANA — varia por plano (Base 8 semanas / Gui 12 semanas / Ineix sem ciclo)
plano_cycle = st.session_state.get("plano_id_sel","Base")
is_ineix = (plano_cycle == "INEIX_ABC_v1")
if not is_ineix:
    try:
        _wk_state = int(st.session_state.get("semana_sel", 1))
    except Exception:
        _wk_state = 1
    if plano_cycle == GUI_PPLA_ID:
        if _wk_state < 1 or _wk_state > 12:
            st.session_state["semana_sel"] = 1
            _wk_state = 1
        st.sidebar.markdown("<h3>Periodização</h3>", unsafe_allow_html=True)
        semana_sel = st.sidebar.radio(
            "Semana do ciclo:",
            list(range(1,13)),
            format_func=semana_label_gui,
            index=min(max(_wk_state-1,0),11),
            key="semana_sel",
            on_change=_reset_daily_state,
            label_visibility="collapsed",
        )
    else:
        if _wk_state < 1 or _wk_state > 8:
            st.session_state["semana_sel"] = 1
            _wk_state = 1
        st.sidebar.markdown("<h3>Periodização</h3>", unsafe_allow_html=True)
        semana_sel = st.sidebar.radio(
            "Semana do ciclo:",
            list(range(1,9)),
            format_func=semana_label,
            index=min(max(_wk_state-1,0),7),
            key="semana_sel",
            on_change=_reset_daily_state,
            label_visibility="collapsed",
        )
    semana = int(semana_sel)
    pass  # sidebar divider removido
else:
    # Plano Ineix (A/B/C) não usa periodização por semanas
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

_treino_options = list(treinos_dict.keys())
if ("dia_sel" not in st.session_state) or (st.session_state.get("dia_sel") not in _treino_options):
    _idx_today = _default_treino_index_for_today(_treino_options)
    try:
        st.session_state["dia_sel"] = _treino_options[_idx_today]
    except Exception:
        pass

st.sidebar.markdown("<h3>Treino</h3>", unsafe_allow_html=True)
dia = st.sidebar.selectbox("Treino", _treino_options, key="dia_sel", on_change=_reset_daily_state, label_visibility="collapsed")
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
    _ck["date"] = datetime.date.today().isoformat()
    yami_log_checkin(perfil_sel, _ck)
    st.sidebar.success("Check-in guardado.")

st.sidebar.markdown('</div>', unsafe_allow_html=True)


# --- YAMI: diagnóstico de dados (inspeção geral) ---
st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
st.sidebar.markdown("<h3>Diagnóstico (Yami)</h3>", unsafe_allow_html=True)

_df_diag = st.session_state.get("_df_cache_data")
if not isinstance(_df_diag, pd.DataFrame):
    try:
        _df_diag = get_data(force_refresh=False)
    except Exception:
        _df_diag = None

_diag_sig = f"{perfil_sel}|{_yami_df_signature(_df_diag) if isinstance(_df_diag, pd.DataFrame) else 'na'}"
_diag_cache = st.session_state.get("_yami_diag_cache")
if isinstance(_diag_cache, dict) and _diag_cache.get("sig") == _diag_sig:
    _diag = _diag_cache.get("data", {})
else:
    _diag = yami_inspecao_geral(_df_diag, perfil_sel) if isinstance(_df_diag, pd.DataFrame) else {"problemas":["Sem DF em memória."]}
    try:
        st.session_state["_yami_diag_cache"] = {"sig": _diag_sig, "data": dict(_diag)}
    except Exception:
        pass

try:
    st.sidebar.caption(
        f"Linhas: **{int(_diag.get('linhas',0) or 0)}** · "
        f"Datas: **{int(_diag.get('datas_unicas',0) or 0)}** · "
        f"Exercícios: **{int(_diag.get('exercicios_unicos',0) or 0)}**"
    )
except Exception:
    pass

_problemas = list(_diag.get("problemas", []) or [])
if _problemas:
    st.sidebar.warning(" • ".join(_problemas[:3]))

with st.sidebar.expander("Ver detalhes", expanded=False):
    st.write({
        "Datas inválidas": int(_diag.get("datas_invalidas",0) or 0),
        "Duplicados prováveis": int(_diag.get("duplicados",0) or 0),
        "RIR fora (0–10)": int(_diag.get("rir_fora",0) or 0),
        "Reps fora (0–50)": int(_diag.get("reps_fora",0) or 0),
        "Peso fora (<0 ou >400)": int(_diag.get("peso_fora",0) or 0),
        "Faltas Peso": int(_diag.get("faltas_peso",0) or 0),
        "Faltas Reps": int(_diag.get("faltas_reps",0) or 0),
        "Faltas RIR": int(_diag.get("faltas_rir",0) or 0),
    })
    if _problemas:
        st.caption("Notas:")
        for p in _problemas[:10]:
            st.write(f"- {p}")

st.sidebar.markdown('</div>', unsafe_allow_html=True)


# FLAGS
st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
st.sidebar.markdown("<h3>Sinais do corpo</h3>", unsafe_allow_html=True)

# Estes sinais têm efeito real: entram no contexto do Yami (estratégia) e reduzem ligeiramente a carga sugerida.
dor_joelho = st.sidebar.checkbox(
    "Dor no joelho (pontiaguda)",
    key="dor_joelho_flag",
    help="Se for dor pontiaguda/articular, o Yami fica mais conservador e a app sugere substituições (não é para ‘aguentar’).",
)
dor_cotovelo = st.sidebar.checkbox(
    "Dor no cotovelo",
    key="dor_cotovelo_flag",
    help="Se o cotovelo estiver a reclamar, o Yami fica mais conservador e sugere variações mais amigáveis (ex.: pushdown barra V).",
)
dor_ombro = st.sidebar.checkbox(
    "Dor no ombro",
    key="dor_ombro_flag",
    help="Se o ombro estiver sensível, o Yami reduz agressividade e sugere ajustes (pega neutra, inclinação menor, sem grind).",
)
dor_lombar = st.sidebar.checkbox(
    "Dor na lombar",
    key="dor_lombar_flag",
    help="Se a lombar estiver a dar sinal, o Yami puxa a carga para baixo e sugere amplitude/variações seguras.",
)

# bucket de dor (0/1/2) para condicionar decisões do Yami
_pain_n = int(bool(dor_joelho)) + int(bool(dor_cotovelo)) + int(bool(dor_ombro)) + int(bool(dor_lombar))
_pain_bucket = 0
if _pain_n >= 2 or bool(dor_lombar):
    _pain_bucket = 2
elif _pain_n == 1:
    _pain_bucket = 1

st.session_state["yami_pain_bucket"] = int(_pain_bucket)
st.session_state["yami_pain_flags"] = {
    "joelho": bool(dor_joelho),
    "cotovelo": bool(dor_cotovelo),
    "ombro": bool(dor_ombro),
    "lombar": bool(dor_lombar),
}

# feedback visual (para não parecer que isto é decorativo)
if _pain_bucket == 0:
    st.sidebar.caption("🟢 Sem sinais marcados (Yami normal).")
elif _pain_bucket == 1:
    st.sidebar.caption("🟠 Sinal marcado (Yami mais conservador).")
else:
    st.sidebar.caption("🔴 Vários sinais / lombar (Yami bem mais conservador).")

st.sidebar.markdown('</div>', unsafe_allow_html=True)

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
.bc-subtitle{ margin-top: 4px; font-size: 0.95rem; color: rgba(232,226,226,0.90); }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='bc-header-center'>
  <div class='bc-main-title'>Black Clover Training</div>
  <div class='bc-subtitle'>A minha magia é não desistir 🗡️🖤</div>
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
        st.session_state["yami_last_rest_s"] = secs

    if st.session_state.get("rest_auto_run", False):
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
            time.sleep(1)
            st.rerun()
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

    pure_nav_key = None
    pure_idx = 0
    if pure_workout_mode and bloco != "Fisio" and len(cfg.get("exercicios", [])) > 0:
        ex_names = [str(it.get("ex","")) for it in cfg["exercicios"]]
        pure_nav_key = f"pt_idx::{perfil_sel}::{st.session_state.get('plano_id_sel','Base')}::{dia}::{semana}"
        # AUTO-RESTORE: em mobile o browser pode suspender e a sessão do Streamlit recomeça (session_estado limpa).
        # Se houver snapshot recente para este perfil/dia/plano/semana, restaura progresso e séries pendentes.
        try:
            _plano_active = str(st.session_state.get('plano_id_sel','Base'))
            _ip_key = _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
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
        # --- Aquecimento/Mobilidade (mais destacado, antes do progresso) ---
        st.markdown(
            "<div class='bc-prep-head'>"
            "<div class='bc-prep-title'>Preparação</div>"
            "<div class='bc-prep-sub'>Marca antes de começar (qualidade do treino &gt; ego).</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        w1, w2 = st.columns(2, gap="large")
        with w1:
            st.markdown(
                "<div class='bc-prep-card'>"
                "<div class='t'>🔥 Aquecimento</div>"
                "<div class='s'>4–5 min leves + ramp-up do 1º exercício.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            aq = st.checkbox("Feito", key="chk_aquecimento")
            st.caption("✅ Marcado" if aq else " ")

        with w2:
            st.markdown(
                "<div class='bc-prep-card'>"
                "<div class='t'>🧘 Mobilidade</div>"
                "<div class='s'>Ativação: ombros, anca, escápulas (2–4 min).</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            mob = st.checkbox("Feito", key="chk_mobilidade")
            st.caption("✅ Marcado" if mob else " ")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        render_progress_compact(_done_ex, len(cfg["exercicios"]))

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
        elif bloco in GUI_BLOCOS:
            if is_gui_deload_week(semana):
                st.warning("DELOAD GUI: ~50–60% das séries, -10 a -15% carga, sem drop e sem mini-sets.")
            elif semana >= 7:
                st.info("Gui: repetição do mesociclo (semanas 7–11). Tenta +2,5 kg ou +1–2 reps mantendo RIR 2.")
            else:
                st.info("Gui: progressão semanal da sheet (Mesociclos 1→5). Mantém descanso 60–90s e RIR 2.")
        df_now = df_all.copy() if isinstance(df_all, pd.DataFrame) else get_data()
        df_hist = df_now  # histórico completo (usado pelo Yami AI)
        for i,item in enumerate(cfg["exercicios"]):
            if pure_workout_mode and pure_nav_key is not None and i != pure_idx:
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
                peso_sug = sugerir_carga(peso_medio, rir_medio, rir_target_num, passo_up, 0.05)

            rep_info, reps_low, reps_high = _reps_bounds_from_item(item)

            with st.expander(f"{i+1}. {ex}", expanded=(i==0 or (pure_workout_mode and pure_nav_key is not None and i == pure_idx))):
                if pure_workout_mode and pure_nav_key is not None and i == pure_idx:
                    st.markdown("<div id='exercise-current-anchor'></div>", unsafe_allow_html=True)
                series_txt = str(item.get('series',''))
                reps_txt = str(item.get('reps',''))
                meta_line = f"🎯 Meta: {series_txt}×{reps_txt}  •  RIR alvo: {rir_target_str}"
                sub_line = f"⏱️ Tempo {item['tempo']} · Descanso ~{item['descanso_s']}s"
                st.markdown(
                    f"""<div class='bc-meta-card'>
  <div class='bc-meta-top'>{html.escape(meta_line)}</div>
  <div class='bc-meta-sub'>{html.escape(sub_line)}</div>
</div>""",
                    unsafe_allow_html=True
                )


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
                                    f"Prontidão: {yami.get('readiness','Normal')} · RIR alvo: {float(yami.get('rir_alvo', rir_target_num) or rir_target_num):.1f} "
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
                            for _r in list(yami.get('razoes', []) or []):
                                st.markdown(f"- {_r}")

                _last_chip = _latest_set_summary_from_df_last(df_last)
                if _last_chip:
                    _tempo = str(item.get("tempo", "") or "").strip()
                    if _tempo:
                        st.markdown(
                            f"<div class='bc-last-chip'>"
                            f"<span class='bc-lastset'>⏮️ {html.escape(str(_last_chip))}</span>"
                            f"<span class='bc-tempo'>⏱️ Tempo {html.escape(_tempo)}</span>"
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
                        _prefill_sets_from_last(i, item, df_last, peso_sug, reps_low, rir_target_num, use_df_exact=True)
                        st.rerun()
                    if p2.button("🎯 Usar sugestão do Yami", key=f"pref_sug_{i}", width='stretch'):
                        _prefill_sets_from_last(i, item, df_last, peso_sug, reps_low, rir_target_num, use_df_exact=False)
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
                            default_peso = _yami_suggest_weight_for_series(perfil_sel, ex, item, float(peso_sug), df_last, df_hist, pending_sets, s, float(rir_target_num), bloco=str(bloco), semana=int(semana))
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
                                f"Reps • S{s+1}", min_value=0, value=int(_default_reps_for_set(rep_info, s, reps_low, reps_high, prefer_max=True)), step=1, key=f"reps_{i}_{s}"
                            )
                            rir = rcol2.number_input(
                                f"RIR • S{s+1}", min_value=0.0, max_value=6.0,
                                value=float(rir_target_num), step=0.5, key=f"rir_{i}_{s}"
                            )

                            is_last = (s == total_series - 1)
                            is_last_ex = (i == len(cfg["exercicios"]) - 1)
                            if not is_last:
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

                                if is_last:
                                    ok_gravou = guardar_sets_agrupados(perfil_sel, dia, bloco, ex, novos_sets, req, justificativa, item=item, semana=semana, plano_id=str(st.session_state.get('plano_id_sel','Base')), df_hist=df_hist, pain_flags={'joelho':dor_joelho,'cotovelo':dor_cotovelo,'ombro':dor_ombro,'lombar':dor_lombar})
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
                                            st.success("Exercício guardado. A seguir…")
                                        
                                        # snapshot: se acabou o último exercício, limpa; senão, guarda progresso atualizado
                                        try:
                                            _plano_active = str(st.session_state.get('plano_id_sel','Base'))
                                            _ip_key = _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
                                            if is_last_ex:
                                                clear_inprogress_session(_ip_key)
                                            else:
                                                _payload = _build_inprogress_payload(perfil_sel, dia, _plano_active, int(semana), pure_nav_key, len(cfg.get('exercicios', [])))
                                                save_inprogress_session(_ip_key, _payload)
                                        except Exception:
                                            pass

                                        time.sleep(0.35)
                                        st.rerun()
                                else:
                                    # descanso definido pelo Yami para a PRÓXIMA série
                                    try:
                                        _prev_reps = int(novos_sets[-2]['reps']) if len(novos_sets) >= 2 else None
                                    except Exception:
                                        _prev_reps = None
                                    # RIR obtido (sem calibração)
                                    _rir_eff = float(rir) if rir is not None else None

                                    _rest_yami = yami_definir_descanso_s(
                                        int(item.get('descanso_s', 75)),
                                        _rir_eff, float(rir_target_num),
                                        int(reps), reps_low, (lambda _ri: int(_ri.get('high') or 0) if str(_ri.get('kind') or '') in ('range','fixed','fixed_seq') else None)(_parse_rep_scheme(item.get('reps',''), int(item.get('series',0) or 0))),
                                        _prev_reps,
                                        is_composto=(str(item.get('tipo','')).lower()=='composto')
                                    )
                                    _queue_auto_rest(int(_rest_yami), ex)
                                    try:
                                        # comentário curto "ao vivo" (Yami)
                                        if (_rir_eff is not None) and float(_rir_eff) <= max(0.5, float(rir_target_num) - 1.0):
                                            st.toast(f"🧠 Yami: Descansa {_rest_yami}s. Isso foi pesado — limpa a próxima.")
                                        elif (_rir_eff is not None) and float(_rir_eff) >= float(rir_target_num) + 1.0:
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
                            ok_gravou = guardar_sets_agrupados(perfil_sel, dia, bloco, ex, pending_sets, req, justificativa, item=item, semana=semana, plano_id=str(st.session_state.get('plano_id_sel','Base')), df_hist=df_hist, pain_flags={'joelho':dor_joelho,'cotovelo':dor_cotovelo,'ombro':dor_ombro,'lombar':dor_lombar})
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
                                    st.success("Exercício guardado. A seguir…")
                                
                                # snapshot: se acabou o último exercício, limpa; senão, guarda progresso atualizado
                                try:
                                    _plano_active = str(st.session_state.get('plano_id_sel','Base'))
                                    _ip_key = _make_inprogress_key(perfil_sel, _plano_active, dia, int(semana), _inprogress_today_key_date())
                                    if is_last_ex2:
                                        clear_inprogress_session(_ip_key)
                                    else:
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
                            reps = rcol1.number_input(f"Reps • S{s+1}", min_value=0, value=int(_default_reps_for_set(rep_info, s, reps_low, reps_high, prefer_max=True)),
                                                      step=1, key=f"reps_{i}_{s}")
                            rir = rcol2.number_input(f"RIR • S{s+1}", min_value=0.0, max_value=6.0,
                                                     value=float(rir_target_num), step=0.5, key=f"rir_{i}_{s}")
                            lista_sets.append({"peso":peso,"reps":reps,"rir":rir})

                        if st.form_submit_button("💾 Gravar exercício", width='stretch'):
                            ok_gravou = guardar_sets_agrupados(perfil_sel, dia, bloco, ex, lista_sets, req, justificativa, item=item, semana=semana, plano_id=str(st.session_state.get('plano_id_sel','Base')), df_hist=df_hist, pain_flags={'joelho':dor_joelho,'cotovelo':dor_cotovelo,'ombro':dor_ombro,'lombar':dor_lombar})
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

        req = _get_req_state_from_session()

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

        req = _get_req_state_from_session()
        justificativa = ""
        xp_pre, ok_checklist = checklist_xp(req, justificativa="")

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


        _finish_label = "🏁 Terminar treino" if not _all_done else "🏁 Terminar treino (concluído)"
        
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

        if st.button(_finish_label):
            st.balloons()
            time.sleep(1.2)
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











