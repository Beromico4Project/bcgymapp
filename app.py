import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import base64
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Black Clover Workout", page_icon="♣️", layout="centered")

# --- 2. FUNÇÕES VISUAIS (Fundo e CSS) ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
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

# --- 4. CONEXÃO E DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        return conn.read(ttl="0")  # ttl=0 for fresh read
    except:
        return pd.DataFrame(columns=[
            "Data","Exercício","Peso","Reps","RPE","Notas",
            "Aquecimento","Alongamento","Cardio","XP","Streak","Checklist_OK"])


def checklist_xp(aquecimento: bool, alongamento: bool, cardio: bool, justificativa: str = ""):
    xp = 0
    xp += 20 if aquecimento else 0
    xp += 20 if alongamento else 0
    xp += 20 if cardio else 0

    ok = aquecimento and alongamento and cardio

    justificativa_ok = len(str(justificativa).strip()) >= 8

    # bónus (disciplina)
    if ok:
        xp += 20
    elif justificativa_ok:
        xp += 10  # “coach credit”: não fez tudo, mas explicou

    return xp, ok

def get_last_streak(df: pd.DataFrame):
    # streak = dias consecutivos com checklist OK
    if df.empty or "Checklist_OK" not in df.columns or "Data" not in df.columns:
        return 0

    df2 = df.copy()
    df2 = df2[df2["Checklist_OK"].astype(str).str.lower().isin(["true", "1", "yes"])]
    if df2.empty:
        return 0

    # datas únicas (dd/mm/yyyy)
    datas = sorted({str(x) for x in df2["Data"].dropna().tolist()})
    datas_dt = []
    for s in datas:
        try:
            datas_dt.append(datetime.datetime.strptime(s, "%d/%m/%Y").date())
        except:
            pass
    if not datas_dt:
        return 0

    datas_dt = sorted(set(datas_dt))
    streak = 1
    # conta consecutivos a partir do último dia registado
    for i in range(len(datas_dt) - 1, 0, -1):
        if (datas_dt[i] - datas_dt[i - 1]).days == 1:
            streak += 1
        else:
            break
    return streak

def calcular_rank(xp_total: int, streak_max: int, checklist_rate: float):
    """
    checklist_rate: 0.0 a 1.0
    """
    # thresholds simples e motivadores
    if xp_total >= 2500 and streak_max >= 21 and checklist_rate >= 0.80:
        return "💎 PLATINA", "Elite"
    if xp_total >= 1500 and streak_max >= 14 and checklist_rate >= 0.70:
        return "🥇 OURO", "Consistente"
    if xp_total >= 700 and streak_max >= 7 and checklist_rate >= 0.60:
        return "🥈 PRATA", "Em evolução"
    return "🥉 BRONZE", "A construir base"


# Cálculo de 1RM (Fórmula de Epley)
def calcular_1rm(peso, reps):
    try:
        pesos = [float(p) for p in str(peso).split(",") if str(p).strip() not in ["", "nan", "None"]]
        repeticoes = [int(float(r)) for r in str(reps).split(",") if str(r).strip() not in ["", "nan", "None"]]

        lista_1rm = []

        for p, r in zip(pesos, repeticoes):
            if r <= 0:
                continue
            if r == 1:
                lista_1rm.append(p)
            else:
                lista_1rm.append(p * (1 + (r / 30)))

        if lista_1rm:
            return round(max(lista_1rm), 1)  # pega o melhor 1RM
        else:
            return 0

    except:
        return 0
        
def _parse_list_floats(v):
    """Aceita '10,20,30' ou 10 -> [10.0,20.0,30.0]"""
    s = str(v).strip()
    if s == "" or s.lower() == "nan":
        return []
    return [float(x) for x in s.split(",") if str(x).strip() != ""]

def _parse_list_ints(v):
    s = str(v).strip()
    if s == "" or s.lower() == "nan":
        return []
    return [int(float(x)) for x in s.split(",") if str(x).strip() != ""]

def series_count_row(row):
    return len(_parse_list_floats(row.get("Peso", "")))

def tonnage_row(row):
    pesos = _parse_list_floats(row.get("Peso", ""))
    reps = _parse_list_ints(row.get("Reps", ""))
    return float(sum(p * r for p, r in zip(pesos, reps)))

def avg_rpe_row(row):
    rpes = _parse_list_floats(row.get("RPE", ""))
    return float(sum(rpes) / len(rpes)) if rpes else 0.0

def parse_data_ddmmyyyy(s):
    # "16/02/2026" -> datetime.date
    return datetime.datetime.strptime(str(s), "%d/%m/%Y").date()

def add_calendar_week(df_in):
    df = df_in.copy()
    df["Data_dt"] = df["Data"].apply(parse_data_ddmmyyyy)
    iso = df["Data_dt"].apply(lambda d: d.isocalendar())  # (year, week, weekday)
    df["ISO_Ano"] = iso.apply(lambda t: t[0])
    df["ISO_Semana"] = iso.apply(lambda t: t[1])
    df["Semana_ID"] = df.apply(lambda x: f"{int(x['ISO_Ano'])}-W{int(x['ISO_Semana']):02d}", axis=1)
    return df

def best_1rm_row(row):
    # usa a tua calcular_1rm atual (que já suporta vírgulas)
    return float(calcular_1rm(row.get("Peso", ""), row.get("Reps", "")))

# Histórico detalhado + auto-fill
def get_historico_detalhado(exercicio, reps_alvo_str):
    df = get_data()

    if df.empty:
        return None, 0.0, int(str(reps_alvo_str).split('-')[0])

    df_ex = df[df["Exercício"] == exercicio]
    if df_ex.empty:
        return None, 0.0, int(str(reps_alvo_str).split('-')[0])

    ultimo = df_ex.iloc[-1]

    try:
        pesos = [float(p) for p in str(ultimo["Peso"]).split(",")]
        rpes = [float(r) for r in str(ultimo["RPE"]).split(",")]
        peso_medio = sum(pesos) / len(pesos)
        rpe_medio = sum(rpes) / len(rpes)
    except:
        return None, 0.0, int(str(reps_alvo_str).split('-')[0])

    # Progressão simples
    if rpe_medio <= 7:
        peso_sugerido = round(peso_medio * 1.05, 1)   # sobe 5%
    elif rpe_medio <= 8:
        peso_sugerido = round(peso_medio * 1.025, 1)  # sobe 2.5%
    elif rpe_medio >= 9:
        peso_sugerido = round(peso_medio * 0.97, 1)   # reduz 3%
    else:
        peso_sugerido = peso_medio
        
    return None, peso_sugerido, int(str(reps_alvo_str).split('-')[0])


def salvar_sets_agrupados(exercicio, lista_sets, aquecimento, alongamento, cardio, justificativa=""):
    df_existente = get_data()

    pesos = ",".join([str(s["peso"]) for s in lista_sets])
    reps = ",".join([str(s["reps"]) for s in lista_sets])
    rpes = ",".join([str(s["rpe"]) for s in lista_sets])

    xp, ok = checklist_xp(aquecimento, alongamento, cardio, justificativa)

    streak_atual = get_last_streak(df_existente)

    hoje = datetime.date.today().strftime("%d/%m/%Y")
    ja_ha_ok_hoje = False
    if not df_existente.empty and "Data" in df_existente.columns and "Checklist_OK" in df_existente.columns:
        ja_ha_ok_hoje = ((df_existente["Data"].astype(str) == hoje) &
                         (df_existente["Checklist_OK"].astype(str).str.lower().isin(["true","1","yes"]))).any()

    if ok and not ja_ha_ok_hoje:
        streak_guardar = streak_atual + 1
    else:
        streak_guardar = streak_atual


    novo_dado = pd.DataFrame([{
        "Data": datetime.date.today().strftime("%d/%m/%Y"),
        "Exercício": exercicio,
        "Peso": pesos,
        "Reps": reps,
        "RPE": rpes,
        "Notas": str(justificativa).strip(),
        "Aquecimento": aquecimento,
        "Alongamento": alongamento,
        "Cardio": cardio,
        "XP": xp,
        "Streak": streak_guardar,
        "Checklist_OK": ok
    }])

    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
    conn.update(data=df_final)

# --- 5. BASE DE DADOS TREINOS (configurada para coincidir com o plano) ---
mapa_musculos = {
    "Supino Reto": "Peito",
    "Supino Inclinado Halter": "Peito",
    "Remada Curvada": "Costas",
    "Puxada Frente": "Costas",
    "Puxada Lateral": "Costas",
    "Remada Baixa": "Costas",
    "Desenvolvimento Militar": "Ombros",
    "Press Militar": "Ombros",
    "Elevação Lateral": "Ombros",
    "Face Pull": "Ombros",
    "Agachamento Livre": "Quadríceps",
    "Hack Squat / Leg Press": "Quadríceps",
    "Leg Press": "Quadríceps",
    "Hip Thrust": "Glúteos",
    "Mesa Flexora": "Posterior",
    "Levantamento Terra Romeno": "Posterior",
    "Gémeos": "Panturrilha",
    "Rosca Direta": "Bíceps",
    "Tríceps Testa": "Tríceps",
    "Tríceps Corda": "Tríceps",
    "Pallof Press": "Core",
}

treinos_base = {

    "Segunda (Upper Força)": [
        {"ex": "Supino Reto", "series": 4, "reps": "4-6", "rpe": 8, "tipo": "composto"},
        {"ex": "Remada Curvada", "series": 4, "reps": "5-6", "rpe": 8, "tipo": "composto"},
        {"ex": "Desenvolvimento Militar", "series": 3, "reps": "6", "rpe": 8, "tipo": "composto"},
        {"ex": "Rosca Direta", "series": 2, "reps": "8-10", "rpe": 8, "tipo": "isolado"},
        {"ex": "Tríceps Testa", "series": 2, "reps": "8-10", "rpe": 8, "tipo": "isolado"},
    ],

    "Terça (Lower Força)": [
        {"ex": "Agachamento Livre", "series": 4, "reps": "4-6", "rpe": 8, "tipo": "composto"},
        {"ex": "Levantamento Terra Romeno", "series": 3, "reps": "6-8", "rpe": 8, "tipo": "composto"},
        {"ex": "Leg Press", "series": 3, "reps": "8", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Gémeos", "series": 4, "reps": "12-15", "rpe": 8, "tipo": "isolado"},
    ],

    "Quinta (Upper Hipertrofia)": [
        {"ex": "Supino Inclinado Halter", "series": 3, "reps": "8-12", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Puxada Frente", "series": 4, "reps": "8-12", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Remada Baixa", "series": 3, "reps": "10-12", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Elevação Lateral", "series": 3, "reps": "12-15", "rpe": 9, "tipo": "isolado"},
        {"ex": "Tríceps Corda", "series": 2, "reps": "12-15", "rpe": 8, "tipo": "isolado"},
    ],

    "Sexta (Lower Hipertrofia)": [
        {"ex": "Hack Squat / Leg Press", "series": 4, "reps": "8-12", "rpe": 8, "tipo": "composto"},
        {"ex": "Hip Thrust", "series": 3, "reps": "8-12", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Mesa Flexora", "series": 3, "reps": "10-15", "rpe": 8, "tipo": "isolado"},
        {"ex": "Gémeos", "series": 4, "reps": "12-15", "rpe": 8, "tipo": "isolado"},
    ],

    "Sábado (Upper Volume Extra)": [
        {"ex": "Press Militar", "series": 3, "reps": "6-8", "rpe": 8, "tipo": "composto"},
        {"ex": "Puxada Lateral", "series": 3, "reps": "8-12", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Face Pull", "series": 3, "reps": "12-15", "rpe": 9, "tipo": "isolado"},
        {"ex": "Rosca Direta", "series": 3, "reps": "10-12", "rpe": 8, "tipo": "isolado"},
    ]
}

def gerar_treino_do_dia(dia, semana):
    treino_base = treinos_base.get(dia, [])
    treino_final = []
    for item in treino_base:
        novo_item = item.copy()
        # Ajustes para semana 3 (intensificação)
        if semana == 3:
            if item["tipo"] == "composto":
                novo_item["series"] += 1
                novo_item["rpe"] = 9
            else:
                novo_item["rpe"] = 9
        # Ajustes para semana 4 (deload)
        elif semana == 4:
            novo_item["series"] = max(2, int(item["series"] * 0.6))
            novo_item["rpe"] = 6
        treino_final.append(novo_item)
    return treino_final

# --- 6. INTERFACE SIDEBAR ---
st.sidebar.title("♣️Grimório♣️")
semana = st.sidebar.radio(
    "Nível de Poder:",
    [1, 2, 3, 4],
    format_func=lambda x: f"Semana {x}: {'Base' if x<=2 else 'MODO DEMÓNIO (Limite)' if x==3 else 'Deload'}"
)
dia = st.sidebar.selectbox("Treino de Hoje", list(treinos_base.keys()) + ["Descanso"])
st.sidebar.markdown("---")
dor_joelho = st.sidebar.checkbox("⚠️ Dor no Joelho")
dor_costas = st.sidebar.checkbox("⚠️ Dor nas Costas")

def adaptar_nome(nome):
    if dor_joelho and "Agachamento" in nome:
        return f"{nome} ➡️ LEG PRESS"
    if dor_costas and "Remada Curvada" in nome:
        return f"{nome} ➡️ APOIADO"
    return nome

# --- 7. CABEÇALHO ---
st.title("♣️BLACK CLOVER Workout♣️")
st.caption("A MINHA MAGIA É NÃO DESISTIR! 🗡️🖤")

# --- 8. CORPO PRINCIPAL ---
tab_treino, tab_historico = st.tabs(["🔥 Treino do Dia", "📊 Histórico"])
with tab_treino:
    with st.expander("ℹ️ Guia de RPE (Como escolher a carga?)"):
        st.markdown("""
        **RPE = Rate of Perceived Exertion (Esforço Percebido)**
        
        * 🔴 **RPE 10 (Falha Total):** Não consegues fazer mais nenhuma repetição.
        * 🟠 **RPE 9 (Muito Pesado):** Conseguias fazer **apenas mais 1** repetição.
        * 🟡 **RPE 8 (Pesado):** Conseguias fazer **mais 2** repetições. 
        * 🟢 **RPE 6-7 (Leve/Técnica):** Conseguias fazer **mais 3-4** repetições.
        """)

    st.markdown("## 🛡️ Disciplina do Atleta")

    col1, col2, col3 = st.columns(3)
    aquecimento = col1.checkbox("🔥 Aquecimento 5–10 min", value=True)
    alongamento = col2.checkbox("🧘 Mobilidade/Alongamento dinâmico", value=True)
    cardio = col3.checkbox("🏃 Cardio 10–15 min", value=False)
    
    justificativa = ""
    if not (aquecimento and alongamento and cardio):
        st.info("Coach: se não fizeres tudo, escreve uma justificativa (ganhas algum XP extra).")
        justificativa = st.text_input("Justificativa (opcional):", "")
    
    xp_pre, ok_checklist = checklist_xp(aquecimento, alongamento, cardio, justificativa)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("XP previsto hoje", f"{xp_pre}")
    c2.metric("Checklist", "✅ Completo" if ok_checklist else "⚠️ Incompleto")
    c3.metric("Streak atual", f"{get_last_streak(get_data())}")
    
    if not ok_checklist:
        st.warning("Checklist incompleto: sem stress — mas tenta melhorar para reduzir risco e subir performance.")

    df_rank = get_data()

    if df_rank.empty or "XP" not in df_rank.columns:
        st.info("Rank: começa a registar treinos para desbloquear níveis.")
    else:
        xp_total = int(pd.to_numeric(df_rank["XP"], errors="coerce").fillna(0).sum())
    
        if "Streak" in df_rank.columns:
            streak_max = int(pd.to_numeric(df_rank["Streak"], errors="coerce").fillna(0).max())
        else:
            streak_max = 0
    
        if "Checklist_OK" in df_rank.columns:
            checklist_rate = float(df_rank["Checklist_OK"].astype(str).str.lower().isin(["true","1","yes"]).mean())
        else:
            checklist_rate = 0.0
    
        rank, subtitulo = calcular_rank(xp_total, streak_max, checklist_rate)
    
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🏅 Rank", rank)
        c2.metric("✨ XP Total", xp_total)
        c3.metric("🔥 Streak Máx", streak_max)
        c4.metric("✅ Checklist", f"{checklist_rate*100:.0f}%")
        st.caption(f"Estado: **{subtitulo}**")

    if dia == "Descanso":
        st.info("Hoje é dia de descanso ativo. Caminhada 30min e mobilidade.")
    else:
        treino_hoje = gerar_treino_do_dia(dia, semana)
        for i, item in enumerate(treino_hoje):
            nome_display = adaptar_nome(item['ex'])
            df_passado, sug_peso, sug_reps = get_historico_detalhado(nome_display, item['reps'])
            with st.expander(f"{i+1}. {nome_display}", expanded=(i==0)):
                c1, c2 = st.columns(2)
                rpe_txt = (
                    "🔴 **MODO DEMONÍACO (FALHA)**" if item['rpe'] >= 9 
                    else "🟡 **ALVO FORMIDÁVEL (Sobram 2 reps)**" if item['rpe'] == 8 
                    else "🟢 **CONCENTRATE-TE (Sobram 3-4 reps)**"
                )
                c1.markdown(f"**Meta:** {item['series']}×{item['reps']}")
                c2.markdown(f"**{rpe_txt}**")
                if df_passado is not None:
                    st.markdown("📜 **Séries Anteriores (Último Treino):**")
                    st.dataframe(df_passado, hide_index=True, use_container_width=True)
                else:
                    st.caption("Sem registos anteriores.")
                if sug_peso > 0:
                    with st.popover("🔥 Cálculo de Peso"):
                        st.markdown(f"**Carga Alvo Sugerida:** {sug_peso} kg")
                        st.write(f"Set 1: {int(sug_peso*0.5)} kg × 8-10 reps (50%)")
                        st.write(f"Set 2: {int(sug_peso*0.7)} kg × 4-5 reps (70%)")
                        st.write(f"Set 3: {int(sug_peso*0.9)} kg × 1-2 reps (90%)")
                lista_sets = []

                with st.form(key=f"form_{i}"):
                    for s in range(item["series"]):
                        st.markdown(f"### Série {s+1}")
                        c1, c2 = st.columns(2)
                        peso = c1.number_input(f"Kg S{s+1}", value=sug_peso, step=2.5, key=f"peso_{i}_{s}")
                        reps = c2.number_input(f"Reps S{s+1}", value=sug_reps, step=1, key=f"reps_{i}_{s}")
                        lista_sets.append({"peso": peso, "reps": reps, "rpe": item["rpe"]})
                
                    if st.form_submit_button("Gravar Exercício"):
                        salvar_sets_agrupados(nome_display, lista_sets, aquecimento, alongamento, cardio, justificativa)
                        st.success("Exercício completo salvo!")
                        time.sleep(0.5)
                        st.rerun()

                tempo = 180 if item["tipo"] == "composto" and semana != 4 else 90
                if st.button(f"⏱️ Descanso ({tempo}s)", key=f"t_{i}"):
                    with st.empty():
                        for s in range(tempo, 0, -1):
                            st.metric("Recupera...", f"{s}s")
                            time.sleep(1)
                        st.success("BORA!")
        st.divider()

        if st.button("TERMINAR TREINO (Superar Limites!)", type="primary"):
            if not ok_checklist:
                st.info("Coach note: tenta bater o checklist completo no próximo treino 😉")
            st.balloons()
            time.sleep(2)
            st.rerun()

with tab_historico:
    st.header("Grimório de Batalha 📊")
    df = get_data()

    st.subheader("🏆 Ranking & Metas")

    if df.empty or "XP" not in df.columns:
        st.info("Ainda sem dados suficientes para ranking.")
    else:
        xp_total = int(pd.to_numeric(df["XP"], errors="coerce").fillna(0).sum())
    
        streak_max = int(pd.to_numeric(df["Streak"], errors="coerce").fillna(0).max()) if "Streak" in df.columns else 0
        checklist_rate = float(df["Checklist_OK"].astype(str).str.lower().isin(["true","1","yes"]).mean()) if "Checklist_OK" in df.columns else 0.0
    
        rank, subtitulo = calcular_rank(xp_total, streak_max, checklist_rate)
    
        c1, c2, c3 = st.columns(3)
        c1.metric("🏅 Rank Atual", rank)
        c2.metric("✨ XP Total", xp_total)
        c3.metric("✅ Checklist", f"{checklist_rate*100:.0f}%")
    
        st.caption(f"Status: **{subtitulo}** | 🔥 Streak Máx: **{streak_max}** dias")
    
        # Metas para subir
        st.markdown("### 🎯 Metas para subir de nível")
        metas = []
        if rank.startswith("🥉"):
            metas = [
                "Chegar a **700 XP**",
                "Fazer **streak máximo 7 dias**",
                "Manter checklist completo em **≥ 60%** dos registos",
            ]
        elif rank.startswith("🥈"):
            metas = [
                "Chegar a **1500 XP**",
                "Fazer **streak máximo 14 dias**",
                "Manter checklist completo em **≥ 70%** dos registos",
            ]
        elif rank.startswith("🥇"):
            metas = [
                "Chegar a **2500 XP**",
                "Fazer **streak máximo 21 dias**",
                "Manter checklist completo em **≥ 80%** dos registos",
            ]
        else:
            metas = ["Manter consistência. Agora é refinar performance e prevenir lesão. 💎"]
    
        for m in metas:
            st.write("• " + m)

    st.subheader("🧠 Disciplina")

    if not df.empty:
        if "Checklist_OK" in df.columns:
            ok_rate = (df["Checklist_OK"].astype(str).str.lower().isin(["true", "1", "yes"])).mean()
            st.metric("Checklist completo (taxa)", f"{ok_rate*100:.0f}%")
    
        if "XP" in df.columns:
            xp_total = pd.to_numeric(df["XP"], errors="coerce").fillna(0).sum()
            st.metric("XP total", f"{int(xp_total)}")
    
        if "Notas" in df.columns:
            st.caption("Justificativas recentes:")
            st.dataframe(df[["Data", "Exercício", "Notas"]].tail(10), hide_index=True, use_container_width=True)
    
        if "Streak" in df.columns:
            st.metric("Streak (último)", f"{int(pd.to_numeric(df['Streak'], errors='coerce').fillna(0).max())}")

    if df.empty:
        st.info("Ainda sem registos.")
    else:
        # ---- Preparação ----
        dfp = add_calendar_week(df)

        # filtro por semana (calendário)
        semanas = sorted(dfp["Semana_ID"].unique())
        semana_sel = st.selectbox("Seleciona a semana (ISO):", semanas, index=len(semanas)-1)

        dfw = dfp[dfp["Semana_ID"] == semana_sel].copy()
        dfw["Grupo"] = dfw["Exercício"].map(mapa_musculos).fillna("Outro")
        dfw["Séries"] = dfw.apply(series_count_row, axis=1)
        dfw["Tonnage"] = dfw.apply(tonnage_row, axis=1)
        dfw["RPE_médio"] = dfw.apply(avg_rpe_row, axis=1)
        dfw["1RM Estimado"] = dfw.apply(best_1rm_row, axis=1)

        # ---- KPIs topo ----
        total_series = int(dfw["Séries"].sum())
        total_tonnage = float(dfw["Tonnage"].sum())
        rpe_medio_semana = float(dfw["RPE_médio"].mean()) if len(dfw) else 0.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Séries na Semana", f"{total_series}")
        c2.metric("Tonnage na Semana", f"{total_tonnage:.0f} kg")
        c3.metric("RPE Médio (linhas)", f"{rpe_medio_semana:.1f}")

        st.divider()

        # ---- Volume por grupo ----
        st.subheader("📊 Séries por Grupo Muscular (semana)")
        vol_grupo = dfw.groupby("Grupo")["Séries"].sum().sort_values(ascending=False)
        st.bar_chart(vol_grupo)

        # ---- Tonnage por grupo ----
        st.subheader("🏋️ Tonnage por Grupo Muscular (semana)")
        ton_grupo = dfw.groupby("Grupo")["Tonnage"].sum().sort_values(ascending=False)
        st.bar_chart(ton_grupo)

        st.divider()

        # ---- Fadiga + Deload recomendação ----
        st.subheader("⚠️ Índice de Fadiga + Deload")
        # índice simples: tonnage normalizada + séries * rpe
        # (não é “científico perfeito”, mas é MUITO útil para decisão)
        fadiga = (dfw["Séries"] * dfw["RPE_médio"]).sum()
        st.metric("Fadiga (Σ Séries × RPE)", f"{fadiga:.1f}")

        over_vol = vol_grupo[vol_grupo > 20]
        over_int = rpe_medio_semana >= 8.7
        red_flag = (not over_vol.empty) or over_int or (fadiga >= 140)

        if not over_vol.empty:
            st.warning("Volume alto (>20 séries) em:")
            st.write(over_vol)

        if red_flag:
            st.error("Recomendação: **DELOAD** na próxima semana (reduz ~40% volume e RPE ~6).")
        else:
            st.success("Sem sinais fortes de deload. Mantém progressão.")

        st.divider()

        # ---- PR Detector ----
        st.subheader("🏆 PRs (Recordes) por Exercício")
        # calcula melhor 1RM histórico por exercício
        df_all = dfp.copy()
        df_all["1RM Estimado"] = df_all.apply(best_1rm_row, axis=1)

        best_hist = df_all.groupby("Exercício")["1RM Estimado"].max()
        best_week = dfw.groupby("Exercício")["1RM Estimado"].max()

        prs = []
        for ex, val_week in best_week.items():
            val_hist = float(best_hist.get(ex, 0))
            # PR se o melhor da semana == melhor histórico e >0
            if val_week > 0 and abs(val_week - val_hist) < 1e-9:
                prs.append((ex, val_week))

        if prs:
            st.success("Novos PRs detetados nesta semana:")
            st.dataframe(pd.DataFrame(prs, columns=["Exercício", "1RM Estimado (PR)"]), hide_index=True, use_container_width=True)
        else:
            st.info("Sem PRs nesta semana.")

        st.divider()

        # ---- Progressão por exercício (gráfico) ----
        st.subheader("📈 Progressão de Força (1RM Estimado)")
        lista_exercicios = sorted(dfp["Exercício"].unique())
        filtro_ex = st.selectbox("Escolhe um Exercício:", lista_exercicios)

        df_chart = dfp[dfp["Exercício"] == filtro_ex].copy()
        df_chart["1RM Estimado"] = df_chart.apply(best_1rm_row, axis=1)
        df_chart = df_chart.sort_values("Data_dt")

        st.line_chart(df_chart, x="Data_dt", y="1RM Estimado")

        st.markdown("### Histórico Completo (filtrado)")
        st.dataframe(df_chart.sort_values("Data_dt", ascending=False), use_container_width=True, hide_index=True)






