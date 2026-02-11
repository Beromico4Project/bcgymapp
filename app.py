import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import base64
import os  # <--- FALTAVA ISTO PARA AS IMAGENS FUNCIONAREM

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Black Clover Workout", page_icon="♣️", layout="centered")

# --- 2. FUNÇÃO DE FUNDO (ROBUSTA) ---
def get_base64(bin_file):
    # Verifica se o ficheiro existe para não dar erro
    if not os.path.exists(bin_file):
        return None
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    
    # CSS BASE: Fontes Medievais
    style_base = """
    /* Importar Fontes */
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=MedievalSharp&display=swap');

    /* FORÇAR A FONTE EM TUDO */
    html, body, [class*="css"], div, label, p, .stMarkdown {
        font-family: 'MedievalSharp', cursive !important;
        color: #E0E0E0 !important;
    }
    
    /* TÍTULOS (H1-H3) */
    h1, h2, h3 {
        font-family: 'Cinzel', serif !important;
        color: #FF4B4B !important;
        text-shadow: 2px 2px 0px #000;
        text-transform: uppercase;
        font-weight: 900 !important;
    }

    /* ABAS (TABS) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(0, 0, 0, 0.6);
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #444;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: rgba(60, 60, 60, 0.8);
        border: 1px solid #555;
        border-radius: 5px;
        color: #ddd;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(139, 0, 0, 0.9) !important;
        color: #FFD700 !important;
        border: 2px solid #FF0000 !important;
    }

    /* BOTÕES */
    div.stButton > button:first-child {
        background: linear-gradient(180deg, #8B0000 0%, #400000 100%) !important;
        color: #FFD700 !important;
        border: 1px solid #FF4B4B !important;
        font-family: 'Cinzel', serif !important;
        font-size: 18px !important;
    }
    
    /* INPUTS */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: rgba(0, 0, 0, 0.6) !important;
        color: white !important;
        border: 1px solid #666 !important;
    }

    /* Remover barra superior branca */
    header { background: transparent !important; }
    """

    # Se a imagem existir, adiciona o CSS do fundo
    if bin_str:
        style_bg = f"""
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
            filter: blur(10px) brightness(0.4);
            z-index: -1;
        }}
        """
    else:
        # Fallback se não houver imagem
        style_bg = ".stApp { background-color: #121212; }"

    st.markdown(f"<style>{style_base} {style_bg}</style>", unsafe_allow_html=True)

# Aplica o visual
set_background('banner.png')

# --- 3. DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try: return conn.read(ttl="0")
    except: return pd.DataFrame(columns=["Data", "Exercício", "Peso", "Reps", "RPE", "Notas"])

def get_ultimo_registro(exercicio):
    df = get_data()
    if df.empty: return None, None
    registo = df[df["Exercício"] == exercicio]
    if not registo.empty:
        ultimo = registo.iloc[-1]
        return ultimo["Peso"], ultimo["Reps"]
    return None, None

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

# --- 4. PLANO DE TREINO ---
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
        if semana == 3: 
            if item["tipo"] == "composto":
                novo_item["series"] += 1 
                novo_item["rpe"] = 9
                if novo_item["reps"] == "5": pass 
            else:
                novo_item["rpe"] = 9
        elif semana == 4:
            novo_item["series"] = max(2, item["series"] - 1)
            novo_item["rpe"] = 6
            if item["reps"] == "5": novo_item["reps"] = "6"
        treino_final.append(novo_item)
    return treino_final

# --- 5. INTERFACE ---
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

# --- CORREÇÃO DAS COLUNAS AQUI ---
col_esq, col_dir = st.columns([1, 4]) # <--- Isto corrige o erro "with col_logo1"
with col_esq:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=90)
    else:
        st.write("♣️")
with col_dir:
    st.title("BLACK CLOVER PROJECT")
    st.caption("A MINHA MAGIA É NÃO DESISTIR! 🗡️🖤")

tab_treino, tab_historico = st.tabs(["🔥 Treino do Dia", "📜 Histórico"])

with tab_treino:
    with st.expander("ℹ️ Guia de RPE"):
        st.markdown("* 🔴 **RPE 10:** Falha.\n* 🟠 **RPE 9:** 1 na reserva.\n* 🟡 **RPE 8:** 2 na reserva.\n* 🟢 **RPE 6:** Deload.")

    if dia == "Descanso":
        st.info("Hoje é dia de descanso ativo. Caminhada 30min e Mobilidade.")
    else:
        treino_hoje = gerar_treino_do_dia(dia, semana)
        
        for i, item in enumerate(treino_hoje):
            nome_display = adaptar_nome(item['ex'])
            last_w, last_r = get_ultimo_registro(nome_display)
            
            with st.expander(f"{i+1}. {nome_display}", expanded=(i==0)):
                c1, c2 = st.columns(2)
                rpe_txt = "🔴 MUITO PESADO" if item['rpe'] >= 9 else "🟢 LEVE" if item['rpe'] <= 6 else "🟡 PESADO"
                c1.markdown(f"**Meta:** {item['series']}x{item['reps']}")
                c2.markdown(f"**{rpe_txt}**")
                
                if last_w: st.caption(f"🔙 Anterior: {last_w}kg")

                with st.form(key=f"form_{i}"):
                    cc1, cc2, cc3 = st.columns([1,1,2])
                    peso = cc1.number_input("Kg", value=float(last_w) if last_w else 0.0, step=2.5)
                    reps = cc2.number_input("Reps", value=int(str(item['reps']).split('-')[0]), step=1)
                    notas = cc3.text_input("Obs")
                    if st.form_submit_button("Gravar"):
                        salvar_set(nome_display, peso, reps, item['rpe'], notas)
                        st.success("Salvo!")
                
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
