import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="V-Shape Planner", page_icon="🦍", layout="centered")
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

# --- 3. BASE DE DADOS "BASE" (Semana 1-2) ---
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

# --- 4. LÓGICA DE PERIODIZAÇÃO (O Cérebro da App) ---
def gerar_treino_do_dia(dia, semana):
    treino_base = treinos_base.get(dia, [])
    treino_final = []

    for item in treino_base:
        novo_item = item.copy()
        
        # --- SEMANA 3: CHOQUE (Aumenta Carga e Volume) ---
        if semana == 3:
            # Compostos principais sobem para 5 séries e RPE 9 (quase falha)
            if item["tipo"] == "composto":
                novo_item["series"] += 1  # De 4x passa a 5x
                novo_item["rpe"] = 9      # RPE sobe
                if novo_item["reps"] == "5": # Se for força (5 reps) mantém
                    pass 
            else:
                novo_item["rpe"] = 9 # Acessórios também ficam mais pesados

        # --- SEMANA 4: DELOAD (Recuperação) ---
        elif semana == 4:
            # Reduz séries e intensidade drasticamente
            novo_item["series"] = max(2, item["series"] - 1) # Tira 1 série de tudo
            novo_item["rpe"] = 6 # RPE leve (Técnica)
            
            # Ajuste específico do doc: Supino/Agachamento vira 3x6 leve
            if item["reps"] == "5":
                novo_item["reps"] = "6"
        
        treino_final.append(novo_item)
    
    return treino_final

# --- 5. INTERFACE ---
st.sidebar.header("Planeamento")

# Seletor de Semana com explicação visual
semana = st.sidebar.radio(
    "Fase Atual:",
    [1, 2, 3, 4],
    format_func=lambda x: f"Semana {x}: {'Volume Moderado (RPE 8)' if x<=2 else 'INTENSIDADE MÁXIMA (RPE 9)' if x==3 else 'Deload / Recuperação (RPE 6)'}"
)

dia = st.sidebar.selectbox("Treino de Hoje", list(treinos_base.keys()) + ["Descanso"])

# Ajustes de Lesão
st.sidebar.markdown("---")
dor_joelho = st.sidebar.checkbox("⚠️ Dor no Joelho")
dor_costas = st.sidebar.checkbox("⚠️ Dor nas Costas")

def adaptar_nome(nome):
    if dor_joelho and ("Agachamento" in nome or "Afundo" in nome):
        return f"{nome} ➡️ LEG PRESS (Adaptado)"
    if dor_costas and "Curvada" in nome:
        return f"{nome} ➡️ APOIADO (Adaptado)"
    return nome

# CORPO PRINCIPAL
st.title("V-Shape Tracker 🦍")

if dia == "Descanso":
    st.info("Hoje é dia de descanso ativo. Caminhada 30min e Mobilidade.")
else:
    # Gera o treino com a lógica da semana aplicada
    treino_hoje = gerar_treino_do_dia(dia, semana)
    
    # Barra de progresso visual
    total = len(treino_hoje)
    prog = st.progress(0)

    for i, item in enumerate(treino_hoje):
        nome_display = adaptar_nome(item['ex'])
        series_reais = item['series']
        reps_reais = item['reps']
        rpe_real = item['rpe']
        
        # Busca histórico
        last_w, last_r = get_ultimo_registro(nome_display)
        
        with st.expander(f"{i+1}. {nome_display}", expanded=(i==0)):
            # Cabeçalho Informativo
            col_info1, col_info2 = st.columns(2)
            col_info1.markdown(f"**Meta:** {series_reais} Séries x {reps_reais} Reps")
            
            # Explicação dinâmica do RPE
            if rpe_real >= 9:
                rpe_desc = "🔴 MUITO PESADO (Sobra 1 rep)"
            elif rpe_real <= 6:
                rpe_desc = "🟢 LEVE (Técnica perfeita)"
            else:
                rpe_desc = "🟡 MODERADO (Sobram 2 reps)"
            
            col_info2.markdown(f"**RPE {rpe_real}:** {rpe_desc}")

            if last_w:
                st.caption(f"🔙 Anterior: {last_w}kg ({last_r} reps)")

            # Formulário
            with st.form(key=f"form_{i}"):
                c1, c2, c3 = st.columns([1,1,2])
                peso = c1.number_input("Peso (kg)", value=float(last_w) if last_w else 0.0, step=2.5)
                reps = c2.number_input("Reps", value=int(str(reps_reais).split('-')[0]), step=1)
                notas = c3.text_input("Notas")
                
                if st.form_submit_button("Gravar Série"):
                    salvar_set(nome_display, peso, reps, rpe_real, notas)
                    st.success("Registado!")
            
            # Timer com base no tipo de exercício
            tempo_descanso = 180 if item["tipo"] == "composto" and semana != 4 else 90
            if st.button(f"⏱️ Descanso ({tempo_descanso}s)", key=f"t_{i}"):
                with st.empty():
                    for s in range(tempo_descanso, 0, -1):
                        st.metric("Descansa...", f"{s}s")
                        time.sleep(1)
                    st.success("BORA!")
