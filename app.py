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
        return pd.DataFrame(columns=["Data", "Exercício", "Peso", "Reps", "RPE", "Notas"])

# Cálculo de 1RM (Fórmula de Epley)
def calcular_1rm(peso, reps):
    try:
        pesos = [float(p) for p in str(peso).split(",")]
        repeticoes = [int(r) for r in str(reps).split(",")]

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


def salvar_sets_agrupados(exercicio, lista_sets):
    df_existente = get_data()

    pesos = ",".join([str(s["peso"]) for s in lista_sets])
    reps = ",".join([str(s["reps"]) for s in lista_sets])
    rpes = ",".join([str(s["rpe"]) for s in lista_sets])

    novo_dado = pd.DataFrame([{
        "Data": datetime.date.today().strftime("%d/%m/%Y"),
        "Exercício": exercicio,
        "Peso": pesos,
        "Reps": reps,
        "RPE": rpes,
        "Notas": ""
    }])

    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
    conn.update(data=df_final)

# --- 5. BASE DE DADOS TREINOS (configurada para coincidir com o plano) ---
mapa_musculos = {
    "Supino Reto": "Peito",
    "Supino Inclinado Halter": "Peito",
    "Dips": "Peito",
    "Desenvolvimento Militar": "Ombros",
    "Desenv. Arnold": "Ombros",
    "Elevação Lateral": "Ombros",
    "Puxada Alta": "Costas",
    "Remada Curvada": "Costas",
    "Remada Baixa": "Costas",
    "Levantamento Terra Romeno": "Posterior",
    "Agachamento Livre": "Quadríceps",
    "Hack Squat / Leg Press": "Quadríceps",
    "Hip Thrust": "Glúteos",
    "Mesa Flexora": "Posterior",
    "Gémeos": "Panturrilha",
    "Rosca Direta": "Bíceps",
    "Tríceps Testa": "Tríceps",
    "Tríceps Corda": "Tríceps"
}

treinos_base = {
    "Segunda (Push Força)": [
        {"ex": "Supino Reto", "series": 4, "reps": "4-6", "rpe": 8, "tipo": "composto"},
        {"ex": "Desenvolvimento Militar", "series": 3, "reps": "5-6", "rpe": 8, "tipo": "composto"},
        {"ex": "Dips", "series": 3, "reps": "6-8", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Tríceps Corda", "series": 2, "reps": "10-12", "rpe": 8, "tipo": "isolado"}
    ],

    "Terça (Pull Força)": [
        {"ex": "Agachamento Livre", "series": 4, "reps": "4-6", "rpe": 8, "tipo": "composto"},
        {"ex": "Levantamento Terra Romeno", "series": 3, "reps": "6-8", "rpe": 8, "tipo": "composto"},
        {"ex": "Remada Curvada", "series": 3, "reps": "6-8", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Ab Wheel / Prancha", "series": 3, "reps": "10-15", "rpe": 7, "tipo": "core"}
    ],

    "Quinta (Push Hipertrofia)": [
        {"ex": "Supino Inclinado Halter", "series": 3, "reps": "8-12", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Desenv. Arnold", "series": 3, "reps": "8-12", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Elevação Lateral", "series": 3, "reps": "12-15", "rpe": 9, "tipo": "isolado"},
        {"ex": "Tríceps Testa", "series": 2, "reps": "10-12", "rpe": 8, "tipo": "isolado"}
    ],

    "Sexta (Pull Hipertrofia)": [
        {"ex": "Puxada Alta", "series": 4, "reps": "8-12", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Remada Baixa", "series": 3, "reps": "10-12", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Face Pull", "series": 3, "reps": "12-15", "rpe": 9, "tipo": "isolado"},
        {"ex": "Rosca Direta", "series": 3, "reps": "10-12", "rpe": 8, "tipo": "isolado"}
    ],

    "Sábado (Legs Hipertrofia)": [
        {"ex": "Hack Squat / Leg Press", "series": 4, "reps": "8-12", "rpe": 8, "tipo": "composto"},
        {"ex": "Hip Thrust", "series": 3, "reps": "8-12", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Mesa Flexora", "series": 3, "reps": "10-15", "rpe": 8, "tipo": "isolado"},
        {"ex": "Gémeos", "series": 4, "reps": "12-15", "rpe": 8, "tipo": "isolado"}
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
                        salvar_sets_agrupados(nome_display, lista_sets)
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
            st.balloons()
            if os.path.exists("success.png"):
                st.image("success.png")
            else:
                st.success("LIMITES SUPERADOS!")
            time.sleep(3)
            st.experimental_rerun()

with tab_historico:
    st.header("Grimório de Batalha 📊")
    df = get_data()
    
    st.subheader("📊 Volume Semanal por Grupo Muscular")

    if not df.empty:
        df_volume = df.copy()
        df_volume["Peso"] = df_volume["Peso"].astype(str)
        df_volume["Series"] = df_volume["Peso"].apply(lambda x: len(x.split(",")))
    
        df_volume["Grupo"] = df_volume["Exercício"].map(mapa_musculos)
        volume_semana = df_volume.groupby("Grupo")["Series"].sum()
    
        st.bar_chart(volume_semana)

    
    if not df.empty:
        lista_exercicios = sorted(df["Exercício"].unique())
        filtro_ex = st.selectbox("Escolhe um Feitiço (Exercício):", lista_exercicios)
        if filtro_ex:
            df_chart = df[df["Exercício"] == filtro_ex].copy()
            df_chart["1RM Estimado"] = df_chart.apply(lambda x: calcular_1rm(x["Peso"], x["Reps"]), axis=1)
            st.subheader(f"Progressão de Força: {filtro_ex}")
            st.line_chart(df_chart, x="Data", y="1RM Estimado")
            st.markdown("### Histórico Completo")
            st.dataframe(df_chart.sort_index(ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Ainda sem registos.")

    st.subheader("⚠️ Análise de Fadiga")

    overtraining = volume_semana[volume_semana > 20]
    
    if not overtraining.empty:
        st.warning("Possível excesso de volume em:")
        st.write(overtraining)
    else:
        st.success("Volume equilibrado.")





