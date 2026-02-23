
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import base64
import os

# =========================================================
# ♣ BLACK CLOVER WORKOUT — RIR Edition (8 semanas + perfis)
# =========================================================

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Black Clover Workout", page_icon="♣️", layout="centered")

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

# --- 3. CSS DA INTERFACE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=MedievalSharp&display=swap');
    html, body, [class*="css"] {
        font-family: 'MedievalSharp', cursive;
        color: #E0E0E0;
    }
    h1, h2, h3 {
        color: #FF4B4B !important;
        font-family: 'Cinzel', serif !important;
        text-shadow: 2px 2px 4px #000;
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
        color: #FFD700 !important;
        border: 1px solid #FF4B4B !important;
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.3);
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
        background: linear-gradient(180deg, #8B0000 0%, #3a0000 100%);
        color: #FFD700;
        border: 1px solid #FF4B4B;
        font-family: 'Cinzel', serif;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(255, 0, 0, 0.4);
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
  border-right: 1px solid rgba(255,75,75,0.35) !important;
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
  color: rgba(255, 215, 0, 0.85);
  text-shadow: 0 0 12px rgba(255, 215, 0, 0.18);
}
.sidebar-seal-title{
  font-family: 'Cinzel', serif;
  font-weight: 900;
  letter-spacing: .12em;
  color: #FFD700;
  text-shadow: 0 0 14px rgba(255, 215, 0, 0.18);
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
  border-left: 3px solid rgba(255, 75, 75, 0.75);
  padding: 12px 12px;
  border-radius: 16px;
  box-shadow: 0 10px 22px rgba(0,0,0,0.35);
  margin: 0 10px 12px 10px;
}
.sidebar-card h3{
  font-family: 'Cinzel', serif;
  color: #FFD700 !important;
  letter-spacing: .08em;
  margin: 0 0 6px 0;
  text-shadow: 0 0 10px rgba(255,215,0,0.16);
}

/* Divisor “runa” */
.rune-divider{
  margin: 10px 0 8px 0;
  height: 1px;
  border: none;
  background: linear-gradient(90deg, transparent, rgba(255,75,75,0.7), transparent);
  position: relative;
}
.rune-divider::after{
  content: "✦";
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  top: -10px;
  font-size: 12px;
  color: rgba(255,215,0,0.80);
  text-shadow: 0 0 10px rgba(255,215,0,0.20);
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
  background: rgba(255,75,75,0.35);
  border-radius: 999px;
}
section[data-testid="stSidebar"] ::-webkit-scrollbar-track {
  background: rgba(0,0,0,0.15);
}
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

def get_profiles_df():
    """Perfis ficam na worksheet 'Perfis'. Se não existir / sem permissão, faz fallback."""
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
        return dfp, True, ""
    except Exception as e:
        # fallback offline
        dfp_off = _load_offline_profiles()
        if dfp_off is not None and not dfp_off.empty:
            return dfp_off, False, f"{e}"
        return pd.DataFrame(columns=PROFILES_COLUMNS), False, f"{e}"

def save_profiles_df(dfp: pd.DataFrame):
    try:
        _conn_update_worksheet(dfp[PROFILES_COLUMNS], PROFILES_WORKSHEET)
        _save_offline_profiles(dfp[PROFILES_COLUMNS])
        return True, ""
    except Exception as e:
        _save_offline_profiles(dfp[PROFILES_COLUMNS])
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


def _to_bool(x):
    s = str(x).strip().lower()
    return s in ["true","1","yes","y","sim"]

def get_data():
    """Lê a sheet e garante schema (migração RPE->RIR e Alongamento->Mobilidade).
    Se a Google Sheet falhar, usa um backup local (offline_backup.csv).
    """
    df = safe_read_sheet()

    if df is None or df.empty:
        df = pd.DataFrame(columns=SCHEMA_COLUMNS)

    if "RPE" in df.columns and "RIR" not in df.columns:
        df = df.rename(columns={"RPE":"RIR"})
    if "Alongamento" in df.columns and "Mobilidade" not in df.columns:
        df = df.rename(columns={"Alongamento":"Mobilidade"})

    for c in SCHEMA_COLUMNS:
        if c not in df.columns:
            df[c] = None

    return df[SCHEMA_COLUMNS]

def normalize_for_save(df):
    for c in SCHEMA_COLUMNS:
        if c not in df.columns:
            df[c] = None
    return df[SCHEMA_COLUMNS]

def _parse_list_floats(v):
    s = str(v).strip()
    if s == "" or s.lower() in ["nan","none"]:
        return []
    out = []
    for x in s.split(","):
        x = str(x).strip()
        if x == "":
            continue
        try:
            out.append(float(x))
        except Exception:
            try:
                out.append(float(x.replace("kg","").strip()))
            except Exception:
                pass
    return out

def _parse_list_ints(v):
    s = str(v).strip()
    if s == "" or s.lower() in ["nan","none"]:
        return []
    out = []
    for x in s.split(","):
        x = str(x).strip()
        if x == "":
            continue
        try:
            out.append(int(float(x)))
        except Exception:
            pass
    return out

def series_count_row(row):
    return len(_parse_list_floats(row.get("Peso","")))

def tonnage_row(row):
    pesos = _parse_list_floats(row.get("Peso",""))
    reps = _parse_list_ints(row.get("Reps",""))
    return float(sum(p*r for p,r in zip(pesos,reps)))

def avg_rir_row(row):
    rirs = _parse_list_floats(row.get("RIR",""))
    return float(sum(rirs)/len(rirs)) if rirs else 0.0

def calcular_1rm(peso, reps):
    pesos = _parse_list_floats(peso)
    repeticoes = _parse_list_ints(reps)
    vals = []
    for p,r in zip(pesos,repeticoes):
        if r <= 0:
            continue
        if r == 1:
            vals.append(p)
        else:
            vals.append(p * (1 + (r/30)))
    return round(max(vals), 1) if vals else 0.0

def best_1rm_row(row):
    return float(calcular_1rm(row.get("Peso",""), row.get("Reps","")))

def add_calendar_week(df_in):
    df = df_in.copy()
    df["Data_dt"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Data_dt"])
    iso = df["Data_dt"].dt.isocalendar()
    df["ISO_Ano"] = iso["year"].astype(int)
    df["ISO_Semana"] = iso["week"].astype(int)
    df["Semana_ID"] = df.apply(lambda x: f"{int(x['ISO_Ano'])}-W{int(x['ISO_Semana']):02d}", axis=1)
    return df

def checklist_xp(req, justificativa=""):
    """req tem chaves: aquecimento,mobilidade,cardio,tendoes,core,cooldown e *_req"""
    base_points = {"aquecimento":20,"mobilidade":20,"cardio":20,"tendoes":15,"core":15,"cooldown":10}
    xp = 0
    ok_all_required = True
    any_missing_required = False
    for k,pts in base_points.items():
        done = bool(req.get(k, False))
        required = bool(req.get(f"{k}_req", False))
        if done:
            xp += pts
        if required and not done:
            ok_all_required = False
            any_missing_required = True
    justificativa_ok = len(str(justificativa).strip()) >= 8
    if ok_all_required:
        xp += 20
    elif any_missing_required and justificativa_ok:
        xp += 10
    return xp, ok_all_required

def get_last_streak(df, perfil):
    if df.empty:
        return 0
    dfp = df[df["Perfil"].astype(str) == str(perfil)].copy()
    if dfp.empty:
        return 0
    dfp = dfp[dfp["Checklist_OK"].apply(_to_bool)]
    if dfp.empty:
        return 0
    datas = pd.to_datetime(dfp["Data"], dayfirst=True, errors="coerce").dt.date.dropna().unique().tolist()
    if not datas:
        return 0
    datas = sorted(set(datas))
    streak = 1
    for i in range(len(datas)-1, 0, -1):
        if (datas[i] - datas[i-1]).days == 1:
            streak += 1
        else:
            break
    return streak

def calcular_rank(xp_total, streak_max, checklist_rate):
    if xp_total >= 2500 and streak_max >= 21 and checklist_rate >= 0.80:
        return "💎 PLATINA", "Elite"
    if xp_total >= 1500 and streak_max >= 14 and checklist_rate >= 0.70:
        return "🥇 OURO", "Consistente"
    if xp_total >= 700 and streak_max >= 7 and checklist_rate >= 0.60:
        return "🥈 PRATA", "Em evolução"
    return "🥉 BRONZE", "A construir base"

def get_historico_detalhado(df, perfil, exercicio):
    """FIX histórico: devolve o último registo em dataframe, + médias."""
    if df.empty:
        return None, 0.0, 0.0, None
    dfp = df[(df["Perfil"].astype(str)==str(perfil)) & (df["Exercício"].astype(str)==str(exercicio))].copy()
    if dfp.empty:
        return None, 0.0, 0.0, None
    dfp["Data_dt"] = pd.to_datetime(dfp["Data"], dayfirst=True, errors="coerce")
    dfp = dfp.dropna(subset=["Data_dt"]).sort_values("Data_dt")
    if dfp.empty:
        return None, 0.0, 0.0, None
    ultimo = dfp.iloc[-1]
    pesos = _parse_list_floats(ultimo["Peso"])
    reps = _parse_list_ints(ultimo["Reps"])
    rirs = _parse_list_floats(ultimo["RIR"])
    rows = []
    n = max(len(pesos), len(reps), len(rirs))
    for i in range(n):
        rows.append({
            "Set": i+1,
            "Peso (kg)": pesos[i] if i < len(pesos) else None,
            "Reps": reps[i] if i < len(reps) else None,
            "RIR": rirs[i] if i < len(rirs) else None,
        })
    df_last = pd.DataFrame(rows)
    peso_medio = float(sum(pesos)/len(pesos)) if pesos else 0.0
    rir_medio = float(sum(rirs)/len(rirs)) if rirs else 0.0
    return df_last, peso_medio, rir_medio, ultimo["Data"]

def sugerir_carga(peso_medio, rir_medio, rir_alvo, passo_up, passo_down):
    if peso_medio <= 0:
        return 0.0
    if rir_medio >= (rir_alvo + 1.0):
        return round(peso_medio * (1 + passo_up), 1)
    if rir_medio > (rir_alvo + 0.25):
        return round(peso_medio * (1 + passo_up/2), 1)
    if rir_medio <= max(0.0, rir_alvo - 1.0):
        return round(peso_medio * (1 - passo_down), 1)
    return round(peso_medio, 1)

def salvar_sets_agrupados(perfil, dia, bloco, exercicio, lista_sets, req, justificativa=""):
    df_existente = get_data()
    pesos = ",".join([str(s["peso"]) for s in lista_sets])
    reps = ",".join([str(s["reps"]) for s in lista_sets])
    rirs = ",".join([str(s["rir"]) for s in lista_sets])

    xp, ok = checklist_xp(req, justificativa)
    streak_atual = get_last_streak(df_existente, perfil)
    hoje = datetime.date.today().strftime("%d/%m/%Y")

    ja_ha_ok_hoje = False
    if not df_existente.empty:
        mask = (
            (df_existente["Perfil"].astype(str) == str(perfil)) &
            (df_existente["Data"].astype(str) == hoje) &
            (df_existente["Checklist_OK"].apply(_to_bool))
        )
        ja_ha_ok_hoje = bool(mask.any())

    if ok and not ja_ha_ok_hoje:
        streak_guardar = streak_atual + 1
    else:
        streak_guardar = streak_atual

    novo_dado = pd.DataFrame([{
        "Data": hoje,
        "Perfil": str(perfil),
        "Dia": str(dia),
        "Bloco": str(bloco),
        "Plano_ID": str(st.session_state.get("plano_id_sel","Base")),
        "Exercício": str(exercicio),
        "Peso": pesos,
        "Reps": reps,
        "RIR": rirs,
        "Notas": str(justificativa).strip(),
        "Aquecimento": bool(req.get("aquecimento", False)),
        "Mobilidade": bool(req.get("mobilidade", False)),
        "Cardio": bool(req.get("cardio", False)),
        "Tendões": bool(req.get("tendoes", False)),
        "Core": bool(req.get("core", False)),
        "Cooldown": bool(req.get("cooldown", False)),
        "XP": int(xp),
        "Streak": int(streak_guardar),
        "Checklist_OK": bool(ok),
    }])

    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
    ok_save, err = safe_update_sheet(df_final)
    if not ok_save:
        sa = _service_account_email()
        msg = "❌ Não consegui gravar na Google Sheet. Vou guardar localmente (offline_backup.csv) para não perder o treino."
        if sa:
            msg += f"\n\n✅ Confere se a Sheet está partilhada com o service account: {sa}"
        st.error(msg)
        st.code(err)
        return False
    return True

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
            {"ex":"Abdutora", "series":3, "reps":"15-25", "tipo":"isolado"},
            {"ex":"Hip thrust máquina / Glute bridge", "series":3, "reps":"8-12", "tipo":"composto"},
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
            {"ex":"Abdutora", "series":2, "reps":"20-30", "tipo":"isolado"},
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
    prefixes = ("chk_", "peso_", "reps_", "rir_", "rest_", "ineix_")
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
    "Seleciona o perfil:",
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
st.sidebar.caption(f"📘 Plano: **{plano_id_sel}**")
if plano_id_sel == "INEIX_ABC_v1" and df_profiles is not None and not df_profiles.empty:
    with st.sidebar.expander("⚙️ Plano (Ineix)"):
        st.caption("Este perfil usa o plano A/B/C (RIR 2 fixo).")
        if st.button("💾 Guardar Plano_ID no perfil (Sheet)"):
            try:
                dfp_u = df_profiles.copy()
                dfp_u["Perfil"] = dfp_u["Perfil"].astype(str).str.strip()
                mask = dfp_u["Perfil"].astype(str) == str(perfil_sel).strip()
                if mask.any():
                    dfp_u.loc[mask, "Plano_ID"] = "INEIX_ABC_v1"
                    okp, errp = save_profiles_df(dfp_u)
                    if okp:
                        st.success("Plano guardado no perfil!")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error("Não consegui gravar na aba Perfis.")
                        st.code(errp)
                else:
                    st.warning("Perfil não encontrado na aba Perfis.")
            except Exception as _e:
                st.error("Falha ao tentar gravar Plano_ID.")
                st.code(str(_e))

with st.sidebar.expander("➕ Criar novo perfil"):
    novo_perfil = st.text_input("Nome do perfil", "")
    if st.button("Criar Perfil"):
        np = str(novo_perfil).strip()
        if not np:
            st.warning("Escreve um nome.")
        elif np in perfis:
            st.warning("Esse perfil já existe.")
        else:
            # só grava em 'Perfis' (sem linha Setup no histórico)
            dfp_new = df_profiles.copy() if df_profiles is not None else pd.DataFrame(columns=PROFILES_COLUMNS)
            if dfp_new is None or dfp_new.empty:
                dfp_new = pd.DataFrame(columns=PROFILES_COLUMNS)

            hoje_iso = datetime.date.today().strftime("%Y-%m-%d")
            novo = pd.DataFrame([{
                "Perfil": np,
                "Criado_em": hoje_iso,
                "Plano_ID": "Base",
                "Ativo": "true",
            }])

            dfp_new = pd.concat([dfp_new, novo], ignore_index=True)
            for c in PROFILES_COLUMNS:
                if c not in dfp_new.columns:
                    dfp_new[c] = None
            dfp_new = dfp_new[PROFILES_COLUMNS].copy()

            ok_p, err_p = save_profiles_df(dfp_new)
            if ok_p:
                st.success("Perfil criado (na aba Perfis)!")
                time.sleep(0.6)
                st.rerun()
            else:
                sa = _service_account_email()
                st.error("Não consegui gravar o perfil na Google Sheet (aba 'Perfis').")
                if sa:
                    st.caption(f"Partilha a Sheet com: {sa} (Editor) e cria uma aba chamada **Perfis**.")
                st.code(err_p)


# --- Google Sheets: estado + backup ---
st.sidebar.subheader("📄 Google Sheets")
_ok_conn, _err_conn = True, ""
try:
    _ = conn.read(ttl="0")
except Exception as _e:
    _ok_conn, _err_conn = False, str(_e)

if _ok_conn:
    st.sidebar.success("Conectado ✅")
else:
    st.sidebar.error("Sem acesso ❌")
    sa = _service_account_email()
    if sa:
        st.sidebar.caption(f"Partilha a Sheet com: {sa}")
    if _err_conn:
        st.sidebar.code(_err_conn)

bk_df = _load_offline_backup()
if bk_df is not None and not bk_df.empty:
    st.sidebar.download_button(
        "⬇️ Download backup (CSV)",
        data=bk_df.to_csv(index=False).encode("utf-8"),
        file_name="offline_backup.csv",
        mime="text/csv",
        use_container_width=True
    )
st.sidebar.markdown('<hr class="rune-divider">', unsafe_allow_html=True)

# SEMANA (8)
st.sidebar.markdown("<h3>🧭 Periodização (8 semanas)</h3>", unsafe_allow_html=True)
is_ineix = (st.session_state.get("plano_id_sel","Base") == "INEIX_ABC_v1")
semana_sel = st.sidebar.radio(
    "Semana do ciclo:",
    list(range(1,9)),
    format_func=semana_label,
    index=0,
    key="semana_sel",
    on_change=_reset_daily_state,
    disabled=is_ineix
)
semana = 1 if is_ineix else semana_sel
if is_ineix:
    st.sidebar.caption("ℹ️ Para o plano Ineix (A/B/C), a periodização 8 semanas não se aplica (RIR 2 fixo).")

st.sidebar.markdown('<hr class="rune-divider">', unsafe_allow_html=True)

# DIA
# Plano ativo (preparado para suportar planos diferentes por perfil)
plan_id_active = st.session_state.get("plano_id_sel", "Base")
plan_obj = PLANOS.get(plan_id_active, treinos_base)

# Se for o plano Ineix, escolhe "Ginásio" vs "Casa" e usa o sub-plano certo
if plan_id_active == "INEIX_ABC_v1" and isinstance(plan_obj, dict):
    ineix_local = st.sidebar.radio("Local:", ["Ginásio","Casa"], key="ineix_local", horizontal=True, on_change=_reset_daily_state)
    treinos_dict = plan_obj.get(ineix_local, plan_obj.get("Ginásio", treinos_ineix_gym))
else:
    treinos_dict = plan_obj

dia = st.sidebar.selectbox("Treino de Hoje", list(treinos_dict.keys()), index=0, key="dia_sel", on_change=_reset_daily_state)
st.sidebar.caption(f"⏱️ Sessão-alvo: **{treinos_dict[dia]['sessao']}**")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# FLAGS
st.sidebar.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
st.sidebar.markdown("<h3>⚠️ Estado do Corpo</h3>", unsafe_allow_html=True)
dor_joelho = st.sidebar.checkbox("Dor no Joelho (pontiaguda?)")
dor_cotovelo = st.sidebar.checkbox("Dor no Cotovelo")
dor_ombro = st.sidebar.checkbox("Dor no Ombro")
dor_lombar = st.sidebar.checkbox("Dor na Lombar")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

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
st.title("♣️BLACK CLOVER Workout♣️")
st.caption("A MINHA MAGIA É NÃO DESISTIR! 🗡️🖤")

# --- 8. CORPO PRINCIPAL ---
tab_treino, tab_historico, tab_ranking = st.tabs(["🔥 Treino do Dia", "📊 Histórico", "🏅 Ranking"])

with tab_treino:
    with st.expander("📜 Regras do Plano (RIR, tempo, deload)"):
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

    cfg = gerar_treino_do_dia(dia, semana, treinos_dict=treinos_dict)
    bloco = cfg["bloco"]
    prot = cfg["protocolos"]

    st.markdown("## 🛡️ Checklist do Dia")

    req = {
        "aquecimento_req": True,
        "mobilidade_req": True,
        "cardio_req": bool(prot.get("cardio", False)),
        "tendoes_req": bool(prot.get("tendoes", False)),
        "core_req": bool(prot.get("core", False)),
        "cooldown_req": bool(prot.get("cooldown", True)),
    }

    c1,c2,c3 = st.columns(3)
    req["aquecimento"] = c1.checkbox("🔥 Aquecimento", value=False, key="chk_aquecimento")
    req["mobilidade"] = c2.checkbox("🧘 Mobilidade", value=False, key="chk_mobilidade")
    req["cardio"] = c3.checkbox("🏃 Cardio Zona 2", value=False, key="chk_cardio", disabled=(not req["cardio_req"]))

    c4,c5,c6 = st.columns(3)
    req["tendoes"] = c4.checkbox("🦾 Tendões", value=False, key="chk_tendoes", disabled=(not req["tendoes_req"]))
    req["core"] = c5.checkbox("🧱 Core escoliose", value=False, key="chk_core", disabled=(not req["core_req"]))
    req["cooldown"] = c6.checkbox("😮‍💨 Cool-down", value=False, key="chk_cooldown")

    justificativa = ""
    xp_pre, ok_checklist = checklist_xp(req, justificativa="")
    if not ok_checklist:
        st.info("Faltou algum item obrigatório? Escreve uma justificativa (ganhas XP extra).")
        justificativa = st.text_input("Justificativa:", "")
    xp_pre, ok_checklist = checklist_xp(req, justificativa=justificativa)

    df_now = get_data()
    streak_atual = get_last_streak(df_now, perfil_sel)

    m1,m2,m3 = st.columns(3)
    m1.metric("XP previsto hoje", f"{xp_pre}")
    m2.metric("Checklist", "✅ Completo" if ok_checklist else "⚠️ Incompleto")
    m3.metric("Streak atual", f"{streak_atual}")

    # rank por perfil
    dfp_rank = df_now[df_now["Perfil"].astype(str) == str(perfil_sel)].copy()
    dfp_rank = dfp_rank[dfp_rank["Bloco"].astype(str).str.lower() != "setup"]
    if not dfp_rank.empty:
        xp_total = int(pd.to_numeric(dfp_rank["XP"], errors="coerce").fillna(0).sum())
        streak_max = int(pd.to_numeric(dfp_rank["Streak"], errors="coerce").fillna(0).max()) if "Streak" in dfp_rank.columns else 0
        checklist_rate = float(dfp_rank["Checklist_OK"].apply(_to_bool).mean())
        rank, subtitulo = calcular_rank(xp_total, streak_max, checklist_rate)
        r1,r2,r3,r4 = st.columns(4)
        r1.metric("🏅 Rank", rank)
        r2.metric("✨ XP Total", xp_total)
        r3.metric("🔥 Streak Máx", streak_max)
        r4.metric("✅ Checklist", f"{checklist_rate*100:.0f}%")
        st.caption(f"Estado: **{subtitulo}**")

    st.divider()

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
        st.subheader(f"📘 Treino: **{dia}**")
        st.caption(f"Bloco: **{bloco}** | Semana: **{semana_label(semana)}**")

        if bloco in ["Força","Hipertrofia"]:
            if semana in [2,6]:
                st.info("Progressão: +1 rep por série OU +2,5–5% carga mantendo o RIR alvo.")
            if semana in [4,8]:
                st.warning("DELOAD: menos séries e mais leve. Técnica e tendões em 1º lugar.")
            if semana == 7 and bloco == "Hipertrofia":
                st.info("Semana 7: TOP SET (RIR 1) + back-off controlado nos compostos.")
        for i,item in enumerate(cfg["exercicios"]):
            ex = item["ex"]
            rir_target_str = item["rir_alvo"]
            rir_target_num = rir_alvo_num(item["tipo"], bloco, semana)

            df_last, peso_medio, rir_medio, data_ultima = get_historico_detalhado(df_now, perfil_sel, ex)

            passo_up = 0.05 if ("Deadlift" in ex or "Leg Press" in ex or "Hip Thrust" in ex) else 0.025
            peso_sug = sugerir_carga(peso_medio, rir_medio, rir_target_num, passo_up, 0.05)

            reps_low = int(str(item["reps"]).split("-")[0]) if "-" in str(item["reps"]) else int(float(item["reps"]))

            with st.expander(f"{i+1}. {ex}", expanded=(i==0)):
                a,b,c = st.columns(3)
                a.markdown(f"**Meta:** {item['series']}×{item['reps']}")
                b.markdown(f"**RIR alvo:** {rir_target_str}")
                c.markdown(f"**Tempo:** {item['tempo']} | **Descanso:** ~{item['descanso_s']}s")

                art = sugestao_articular(ex)
                if art:
                    st.warning(art)
                if item.get("nota_semana"):
                    st.info(item["nota_semana"])

                if df_last is not None:
                    st.markdown(f"📜 **Último registo ({data_ultima})**")
                    st.dataframe(df_last, hide_index=True, use_container_width=True)
                    st.caption(f"Último: peso médio ~ {peso_medio:.1f} kg | RIR médio ~ {rir_medio:.1f}")
                else:
                    st.caption("Sem registos anteriores para este exercício (neste perfil).")

                if peso_sug > 0:
                    with st.popover("🔥 Sugestão de carga (heurística)"):
                        st.markdown(f"**Carga sugerida (média):** {peso_sug} kg")
                        st.caption("Se o RIR sair do alvo, ajusta na hora. Técnica > ego.")

                lista_sets = []
                with st.form(key=f"form_{i}"):
                    for s in range(item["series"]):
                        st.markdown(f"### Série {s+1}")
                        cc1,cc2,cc3 = st.columns(3)
                        peso = cc1.number_input(f"Kg S{s+1}", min_value=0.0,
                                                value=float(peso_sug) if peso_sug>0 else 0.0,
                                                step=2.5, key=f"peso_{i}_{s}")
                        reps = cc2.number_input(f"Reps S{s+1}", min_value=0, value=int(reps_low),
                                                step=1, key=f"reps_{i}_{s}")
                        rir = cc3.number_input(f"RIR S{s+1}", min_value=0.0, max_value=6.0,
                                               value=float(rir_target_num), step=0.5, key=f"rir_{i}_{s}")
                        lista_sets.append({"peso":peso,"reps":reps,"rir":rir})

                    if st.form_submit_button("Gravar Exercício"):
                        ok_gravou = salvar_sets_agrupados(perfil_sel, dia, bloco, ex, lista_sets, req, justificativa)
                        if ok_gravou:
                            st.success("Exercício gravado!")
                            time.sleep(0.4)
                            st.rerun()

                rest_s = st.slider("⏱️ Descanso (segundos)", min_value=30, max_value=300,
                                   value=int(item["descanso_s"]), step=15, key=f"rest_{i}")
                if st.button(f"▶️ Iniciar descanso ({rest_s}s)", key=f"t_{i}"):
                    ph = st.empty()
                    for sec in range(rest_s, 0, -1):
                        ph.metric("Recupera...", f"{sec}s")
                        time.sleep(1)
                    ph.success("BORA! 🔥")

        st.divider()

        if prot.get("tendoes", False):
            with st.expander("🦾 TENDÕES (8–12 min) — protocolo"):
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
            with st.expander("🧱 CORE ESCOLIOSE (6–10 min) — protocolo"):
                st.markdown("""
- McGill curl-up 2×8–10 (pausa 2s)
- Side plank 2×25–40s (+1 série lado fraco)
- Bird dog 2×6–8/lado (pausa 2s)
- Suitcase carry 2×20–30m/lado (se houver espaço)
""")

        if st.button("TERMINAR TREINO (Superar Limites!)", type="primary"):
            st.balloons()
            time.sleep(1.2)
            st.rerun()

with tab_historico:
    st.header("Grimório de Batalha 📊")

    df = get_data()
    dfp = df[df["Perfil"].astype(str) == str(perfil_sel)].copy()

    # ignora linhas de setup de perfis
    dfp = dfp[dfp["Bloco"].astype(str).str.lower() != "setup"]

    if dfp.empty:
        st.info("Ainda sem registos neste perfil.")
    else:
        # Filtros (Dia / Bloco / Datas)
        f1,f2,f3 = st.columns(3)
        dias_opts = sorted(dfp["Dia"].dropna().astype(str).unique().tolist())
        blocos_opts = sorted(dfp["Bloco"].dropna().astype(str).unique().tolist())

        dias_filtrados = f1.multiselect("Filtrar por Dia", dias_opts, default=[])
        blocos_filtrados = f2.multiselect("Filtrar por Bloco", blocos_opts, default=[])

        datas_dt = pd.to_datetime(dfp["Data"], dayfirst=True, errors="coerce").dropna()
        if not datas_dt.empty:
            dmin = datas_dt.min().date()
            dmax = datas_dt.max().date()
            intervalo = f3.date_input("Filtrar por datas", value=(dmin, dmax))
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

        st.divider()

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

            st.divider()

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

            st.divider()

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
                st.dataframe(pd.DataFrame(prs, columns=["Exercício","1RM Estimado (PR)"]), hide_index=True, use_container_width=True)
            else:
                st.info("Sem PRs nesta semana.")

            st.divider()

            st.subheader("📈 Progressão de Força (1RM Estimado)")
            lista_exercicios = sorted(dfw_all["Exercício"].dropna().astype(str).unique())
            filtro_ex = st.selectbox("Escolhe um Exercício:", lista_exercicios)
            df_chart = dfw_all[dfw_all["Exercício"].astype(str) == str(filtro_ex)].copy()
            df_chart["1RM Estimado"] = df_chart.apply(best_1rm_row, axis=1)
            df_chart = df_chart.sort_values("Data_dt")

            st.line_chart(df_chart, x="Data_dt", y="1RM Estimado")

            st.markdown("### Histórico (filtrado)")
            st.dataframe(
                df_chart.sort_values("Data_dt", ascending=False)[
                    ["Data","Dia","Bloco","Exercício","Peso","Reps","RIR","XP","Checklist_OK","Notas"]
                ],
                use_container_width=True, hide_index=True
            )


with tab_ranking:
    st.header("Top Ranking dos Perfis 🏅")

    df_rank_all = get_data().copy()
    # ignora linhas de setup/ruído
    df_rank_all = df_rank_all[df_rank_all["Bloco"].astype(str).str.lower() != "setup"]
    df_rank_all = df_rank_all[df_rank_all["Dia"].astype(str).str.lower() != "setup"]
    df_rank_all = df_rank_all[df_rank_all["Exercício"].astype(str).str.lower() != "setup"]

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

        # pódio
        top3 = rank_df.head(3)
        if not top3.empty:
            p1,p2,p3 = st.columns(3)
            if len(top3) >= 1:
                p1.metric("🥇 #1", top3.iloc[0]["Perfil"], f"{top3.iloc[0]['Tier']} • {top3.iloc[0]['XP Total']} XP")
            if len(top3) >= 2:
                p2.metric("🥈 #2", top3.iloc[1]["Perfil"], f"{top3.iloc[1]['Tier']} • {top3.iloc[1]['XP Total']} XP")
            if len(top3) >= 3:
                p3.metric("🥉 #3", top3.iloc[2]["Perfil"], f"{top3.iloc[2]['Tier']} • {top3.iloc[2]['XP Total']} XP")

        st.dataframe(
            rank_df[["Posição","Perfil","Tier","Score","XP Total","Streak Máx","Checklist %","Sessões"]],
            use_container_width=True,
            hide_index=True
        )

        st.caption("Score = XP + (Streak×50) + (Checklist×500) + (Sessões×10). Isto é só para ranking — não muda o teu treino.")
