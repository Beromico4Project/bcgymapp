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
    
    # CSS para o Fundo Desfocado
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
        /* Cinza Escuro com 85% de opacidade */
        filter: blur(12px) brightness(0.5); 
        z-index: -1;
    }}
    /* Camada extra de Cinza Escuro Transparente */
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

# Aplica o fundo
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
        # ttl="0" garante dados frescos para o auto-preenchimento funcionar bem
        return conn.read(ttl="0")
    except:
        return pd.DataFrame(columns=["Data", "Exercício", "Peso", "Reps", "RPE", "Notas"])

# --- FUNÇÃO 1: TABELA VISUAL DA SEMANA PASSADA ---
def get_treino_anterior_tabela(exercicio):
    df = get_data()
    if df.empty: return None
    
    df_ex = df[df["Exercício"] == exercicio]
    if df_ex.empty: return None
    
    # Ignora os dados de hoje para mostrar apenas o "passado"
    data_hoje = datetime.date.today().strftime("%d/%m/%Y")
    df_passado = df_ex[df_ex["Data"] != data_hoje]
    
    if df_passado.empty: return None
    
    # Pega a última data disponível
    ultima_data = df_passado.iloc[-1]["Data"]
    
    # Filtra e retorna
    cols_uteis = ["Peso", "Reps", "RPE", "Notas"]
    return df_passado[df_passado["Data"] == ultima_data][cols_uteis]

# --- FUNÇÃO 2: SUGESTÃO SMART (MACROFACTOR STYLE) ---
def get_sugestao_smart(exercicio, reps_alvo_str):
    """
    Retorna o último peso/reps registado ABSOLUTO.
    Se gravaste o Set 1 hoje, retorna esses valores para o Set 2.
    Se não, retorna do último treino.
    """
    df = get_data()
    
    # Valor padrão das reps alvo (ex: de "8-10" pega 8)
    reps_padrao = int(str(reps_alvo_str).split('-')[0])
    
    if df.empty: return 0.0, reps_padrao
    
    df_ex = df[df["Exercício"] == exercicio]
    if df_ex.empty: return 0.0, reps_padrao
    
    # Pega o registo mais recente de todos (incluindo hoje)
    ultimo_registo = df_ex.iloc[-1]
    
    return float(ultimo_registo["Peso"]), int(ultimo_registo["Reps"])

def salvar_set(exercicio, peso, reps, rpe, notas):
    df_existente = get_data()
    novo_dado = pd.DataFrame([{
        "Data": datetime.date.today().strftime("%d/%m/%Y"),
        "Exercício": exercicio,
        "Peso": peso,
        "Reps": reps,
        "RPE": rpe,
        "Notas": notas
    }])
    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
    conn.update(data=df_final)

# --- 5. BASE DE DADOS TREINOS ---
treinos_base = {
    "Segunda (Upper Força)": [
        {"ex": "Supino Reto", "series": 4, "reps": "5", "rpe": 8, "tipo": "composto"},
        {"ex": "Remada Curvada", "series": 4, "reps": "6", "rpe": 8, "tipo": "composto"},
        {"ex": "Desenvolvimento Militar", "series": 3, "reps": "6", "rpe": 8, "tipo": "composto"},
        {"ex": "Puxada Frente", "series": 3, "reps": "8", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Face Pull", "series": 3, "reps": "12", "rpe": 8, "tipo": "isolado"}
    ],
    "Terça (Lower Força)": [
        {"ex": "Agachamento Livre", "series": 4, "reps": "5", "rpe": 8, "tipo": "composto"},
        {"ex": "Stiff", "series": 3, "reps": "6", "rpe": 8, "tipo": "composto"},
        {"ex": "Afundo", "series": 3, "reps": "8", "rpe": 7, "tipo": "acessorio"},
        {"ex": "Leg Press", "series": 3, "reps": "8", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Gémeos", "series": 4, "reps": "12", "rpe": 8, "tipo": "isolado"}
    ],
    "Quinta (Upper Hipertrofia)": [
        {"ex": "Supino Inclinado Halter", "series": 3, "reps": "10", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Puxada Lateral", "series": 4, "reps": "8-10", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Remada Baixa", "series": 3, "reps": "10", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Desenv. Arnold", "series": 3, "reps": "10", "rpe": 8, "tipo": "acessorio"},
        {"ex": "Elevação Lateral", "series": 3, "reps": "12", "rpe": 9, "tipo": "isolado"}
    ],
    "Sexta (Lower Hipertrofia)": [
        {"ex": "Hack Squat/Leg Press", "series": 4, "reps": "10", "rpe": 7, "tipo": "composto"},
        {"ex": "Hip Thrust", "series": 3, "reps": "10", "rpe": 7, "tipo": "acessorio"},
        {"ex": "Cadeira Extensora", "series": 3, "reps": "12", "rpe": 8, "tipo": "isolado"},
        {"ex": "Mesa Flexora", "series": 3, "reps": "12", "rpe": 8, "tipo": "isolado"}
    ],
    "Sábado (Ombros/Braços)": [
        {"ex": "Press Militar", "series": 3, "reps": "6", "rpe": 8, "tipo": "composto"},
        {"ex": "Elevação Lateral Unilateral", "series": 3, "reps": "12", "rpe": 10, "tipo": "isolado"},
        {"ex": "Remada Curvada Supinada", "series": 3, "reps": "8", "rpe": 8, "tipo": "composto"},
        {"ex": "Pallof Press", "series": 3, "reps": "12", "rpe": 7, "tipo": "core"}
    ]
}

def gerar_treino_do_dia(dia, semana):
    treino_base = treinos_base.get(dia, [])
    treino_final = []
    for item in treino_base:
        novo_item = item.copy()
        if semana == 3: # Choque
            if item["tipo"] == "composto":
                novo_item["series"] += 1 
                novo_item["rpe"] = 9
                if novo_item["reps"] == "5": pass 
            else:
                novo_item["rpe"] = 9
        elif semana == 4: # Deload
            novo_item["series"] = max(2, item["series"] - 1)
            novo_item["rpe"] = 6
            if item["reps"] == "5": novo_item["reps"] = "6"
        treino_final.append(novo_item)
    return treino_final

# --- 6. INTERFACE SIDEBAR ---
st.sidebar.title("♣️ Grimório")
semana = st.sidebar.radio("Nível de Poder:", [1, 2, 3, 4], format_func=lambda x: f"Semana {x}: {'Base' if x<=2 else 'MODO DEMÓNIO (Limite)' if x==3 else 'Deload'}")
dia = st.sidebar.selectbox("Treino de Hoje", list(treinos_base.keys()) + ["Descanso"])
st.sidebar.markdown("---")
dor_joelho = st.sidebar.checkbox("⚠️ Dor no Joelho")
dor_costas = st.sidebar.checkbox("⚠️ Dor nas Costas")

def adaptar_nome(nome):
    if dor_joelho and ("Agachamento" in nome or "Afundo" in nome): return f"{nome} ➡️ LEG PRESS"
    if dor_costas and "Curvada" in nome: return f"{nome} ➡️ APOIADO"
    return nome

# --- 7. CABEÇALHO (SEM LOGO) ---
st.title("♣️BLACK CLOVER PROJECT♣️")
st.caption("A MINHA MAGIA É NÃO DESISTIR! 🗡️🖤")

# --- 8. CORPO PRINCIPAL ---
tab_treino, tab_historico = st.tabs(["🔥 Treino do Dia", "📜 Histórico"])

with tab_treino:
    with st.expander("ℹ️ Guia de RPE (Como escolher a carga?)"):
        st.markdown("""
        **RPE = Rate of Perceived Exertion (Esforço Percebido)**
        
        * 🔴 **RPE 10 (Falha Total):** Não consegues fazer mais nenhuma repetição.
        * 🟠 **RPE 9 (Muito Pesado):** Conseguias fazer **apenas mais 1** repetição. (Foco da Semana 3).
        * 🟡 **RPE 8 (Pesado):** Conseguias fazer **mais 2** repetições. (Foco das Semanas 1-2).
        * 🟢 **RPE 6-7 (Leve/Técnica):** Conseguias fazer **mais 3 ou 4** repetições. Velocidade rápida. (Foco da Semana 4/Deload).
        """)

    if dia == "Descanso":
        st.info("Hoje é dia de descanso ativo. Caminhada 30min e Mobilidade.")
    else:
        treino_hoje = gerar_treino_do_dia(dia, semana)
        
        for i, item in enumerate(treino_hoje):
            nome_display = adaptar_nome(item['ex'])
            
            # 1. Tabela Visual (Semana Passada)
            df_tabela = get_treino_anterior_tabela(nome_display)
            
            # 2. Sugestão Smart (MacroFactor) para Input
            sug_peso, sug_reps = get_sugestao_smart(nome_display, item['reps'])
            
            with st.expander(f"{i+1}. {nome_display}", expanded=(i==0)):
                c1, c2 = st.columns(2)
                rpe_txt = "🔴 MODO DEMONÍACO (FALHA)" if item['rpe'] >= 9 else "🟢 CONCENTRA-TE SÓ (Sobram 3-4 reps)" if item['rpe'] <= 6 else "🟡 ALVO FORMIDÁVEL (Sobram 2 reps)"
                c1.markdown(f"**Meta:** {item['series']}x{item['reps']}")
                c2.markdown(f"**{rpe_txt}**")
                
                # --- TABELA DE SÉRIES ANTERIORES ---
                if df_tabela is not None:
                    st.markdown("📜 **Séries Anteriores:**")
                    st.dataframe(df_tabela, hide_index=True, use_container_width=True)
                else:
                    st.caption("Sem registos anteriores.")

                with st.form(key=f"form_{i}"):
                    cc1, cc2, cc3 = st.columns([1,1,2])
                    
                    # --- AUTO-PREENCHIMENTO INTELIGENTE ---
                    # Value = Sugestão baseada no último set feito
                    peso = cc1.number_input("Kg", value=sug_peso, step=2.5)
                    reps = cc2.number_input("Reps", value=sug_reps, step=1)
                    notas = cc3.text_input("Obs")
                    
                    if st.form_submit_button("Gravar"):
                        salvar_set(nome_display, peso, reps, item['rpe'], notas)
                        st.success("Salvo!")
                        time.sleep(1) # Pequena pausa
                        st.rerun()    # Reinicia a app para o próximo set ter os dados atualizados!
                
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
                st.success("LIMITS SURPASSED!")
            time.sleep(3)
            st.rerun()

with tab_historico:
    st.header("Grimório 📖")
    df = get_data()
    if not df.empty:
        filtro = st.multiselect("Filtrar:", df["Exercício"].unique())
        df_show = df[df["Exercício"].isin(filtro)] if filtro else df
        st.dataframe(df_show.sort_index(ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Ainda sem registos.")
