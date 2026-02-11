import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import base64  # <--- 1. Import necessário para o fundo

# --- 2. CONFIGURAÇÃO DA PÁGINA (Tem de ser a primeira instrução ST) ---
st.set_page_config(page_title="Black Clover Workout", page_icon="♣️", layout="centered")

# --- 3. FUNÇÕES PARA O FUNDO DESFOCADO ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.80); /* 80% Escuro para leitura */
        backdrop-filter: blur(8px); /* Desfoque */
        z-index: -1;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

# --- 4. APLICAR O FUNDO ---
# Certifica-te que o ficheiro 'banner.png' está na pasta!
try:
    set_background('banner.png') 
except:
    pass # Se não encontrar a imagem, continua sem fundo

# --- 5. RESTO DO CSS (Botões, Títulos) ---
st.markdown("""
    <style>
    /* Títulos */
    h1, h2, h3 {
        color: #FF4B4B !important; 
        text-shadow: 2px 2px 4px #000000;
        font-family: 'Arial Black', sans-serif;
        text-transform: uppercase;
    }
    /* Expander */
    .streamlit-expanderHeader {
        background-color: rgba(38, 39, 48, 0.8); /* Transparente */
        border-radius: 10px;
        color: #ffffff;
        border: 1px solid #FF4B4B;
    }
    /* Botões */
    div.stButton > button:first-child {
        background-color: #8B0000; 
        color: white;
        border: 2px solid #FF0000;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 6. O RESTO DA TUA APP (Lógica e Dados) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. FUNÇÕES DE DADOS ---
def get_data():
    try:
        return conn.read(ttl="0")
    except:
        return pd.DataFrame(columns=["Data", "Exercício", "Peso", "Reps", "RPE", "Notas"])

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

# --- 3. BASE DE DADOS (Baseado no DOCX) ---
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
            if item["reps"] == "5":
                novo_item["reps"] = "6"
        treino_final.append(novo_item)
    return treino_final

# --- 5. INTERFACE ---
st.sidebar.title("♣️ Grimório")

semana = st.sidebar.radio(
    "Nível de Poder:",
    [1, 2, 3, 4],
    format_func=lambda x: f"Semana {x}: {'Base' if x<=2 else 'MODO DEMÓNIO (Limite)' if x==3 else 'Recuperação (Deload)'}"
)

dia = st.sidebar.selectbox("Treino de Hoje", list(treinos_base.keys()) + ["Descanso"])

st.sidebar.markdown("---")
dor_joelho = st.sidebar.checkbox("⚠️ Dor no Joelho")
dor_costas = st.sidebar.checkbox("⚠️ Dor nas Costas")

def adaptar_nome(nome):
    if dor_joelho and ("Agachamento" in nome or "Afundo" in nome):
        return f"{nome} ➡️ LEG PRESS"
    if dor_costas and "Curvada" in nome:
        return f"{nome} ➡️ APOIADO"
    return nome

# --- HEADER COM LOGO ---
col_logo1, col_logo2 = st.columns([1, 4])
with col_logo1:
    # Usa a imagem local (certifica-te que está no GitHub como logo.png)
    try:
        st.image("logo.png", width=90)
    except:
        st.write("♣️") # Fallback se a imagem falhar
with col_logo2:
    st.title("BLACK CLOVER PROJECT")
    st.caption("A MINHA MAGIA É NÃO DESISTIR! 🗡️🖤")

# --- CRIAÇÃO DAS ABAS (CORRIGIDO: Antes do uso) ---
tab_treino, tab_historico = st.tabs(["🔥 Treino do Dia", "📜 Histórico"])

# --- ABA 1: TREINO ---
with tab_treino:
    # Banner Principal
    try:
        st.image("banner.png", use_column_width=True)
    except:
        pass

    with st.expander("ℹ️ Guia de RPE (Nível de Esforço)"):
        st.markdown("""
        * 🔴 **RPE 10 (Falha):** 0 reps na reserva.
        * 🟠 **RPE 9 (Limite):** 1 rep na reserva.
        * 🟡 **RPE 8 (Pesado):** 2 reps na reserva.
        * 🟢 **RPE 6 (Deload):** 3-4 reps na reserva (Técnica).
        """)

    if dia == "Descanso":
        st.info("Hoje é dia de descanso ativo. Caminhada 30min e Mobilidade.")
    else:
        treino_hoje = gerar_treino_do_dia(dia, semana)
        
        for i, item in enumerate(treino_hoje):
            nome_display = adaptar_nome(item['ex'])
            series_reais = item['series']
            reps_reais = item['reps']
            rpe_real = item['rpe']
            
            last_w, last_r = get_ultimo_registro(nome_display)
            
            with st.expander(f"{i+1}. {nome_display}", expanded=(i==0)):
                col_info1, col_info2 = st.columns(2)
                
                if rpe_real >= 9: rpe_text = "🔴 MODO DEMONÍACO, VAI COM TUDO"
                elif rpe_real <= 6: rpe_text = "🟢 CONCENTRA-TE SÓ, FOCO NO ATAQUE"
                else: rpe_text = "🟡 UM ALVO FORMIDÁVEL, NÃO PRECISAS DAR TUDO"
                
                col_info1.markdown(f"**Meta:** {series_reais} Séries x {reps_reais} Reps")
                col_info2.markdown(f"**{rpe_text}**")

                if last_w:
                    st.caption(f"🔙 Anterior: {last_w}kg ({last_r} reps)")

                with st.form(key=f"form_{i}"):
                    c1, c2, c3 = st.columns([1,1,2])
                    peso = c1.number_input("Peso (kg)", value=float(last_w) if last_w else 0.0, step=2.5)
                    reps = c2.number_input("Reps", value=int(str(reps_reais).split('-')[0]), step=1)
                    notas = c3.text_input("Notas", placeholder="Obs...")
                    
                    if st.form_submit_button("Gravar"):
                        salvar_set(nome_display, peso, reps, rpe_real, notas)
                        st.success("Registado!")
                
                tempo = 180 if item["tipo"] == "composto" and semana != 4 else 90
                if st.button(f"⏱️ Descanso ({tempo}s)", key=f"t_{i}"):
                    with st.empty():
                        for s in range(tempo, 0, -1):
                            st.metric("Recupera...", f"{s}s")
                            time.sleep(1)
                        st.success("BORA!")

        st.divider()
        st.markdown("### 🏁 Checkout")
        c1, c2 = st.columns(2)
        with c1: st.checkbox("Cardio (5-10min)?")
        with c2: st.checkbox("Mobilidade?")

        if st.button("TERMINEI O TREINO (Superar Limites!)", type="primary"):
            st.balloons()
            try:
                st.image("success.png", caption="LIMITS SURPASSED!")
            except:
                st.success("LIMITS SURPASSED!")
            time.sleep(4)
            st.rerun()

# --- ABA 2: HISTÓRICO ---
with tab_historico:
    st.header("Grimório de Batalha 📖")
    df = get_data()
    if not df.empty:
        filtro = st.multiselect("Filtrar:", df["Exercício"].unique())
        df_show = df[df["Exercício"].isin(filtro)] if filtro else df
        st.dataframe(df_show.sort_index(ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Ainda sem registos.")


