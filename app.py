import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time

# --- 1. CONFIGURAÇÃO INICIAL (Obrigatório ser a primeira linha) ---
st.set_page_config(page_title="Black Clover App", page_icon="♣️", layout="centered")

# --- 2. CONEXÃO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # ttl=0 garante que não usa cache antigo
    try:
        return conn.read(ttl="0")
    except:
        return pd.DataFrame(columns=["Data", "Exercício", "Peso", "Reps", "RPE", "Notas"])

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
    # Concatena e envia
    df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
    conn.update(data=df_final)

# --- 3. FUNÇÃO DE TIMER VISUAL ---
def timer_descanso(segundos):
    placeholder = st.empty()
    progresso = st.progress(0)
    for i in range(segundos, -1, -1):
        # Muda a cor ou texto conforme acaba
        status = "🟢 Descansa..." if i > 10 else "🔴 Prepara-te!"
        placeholder.metric(label=status, value=f"{i}s")
        progresso.progress((segundos - i) / segundos)
        time.sleep(1)
    placeholder.success("GO! 🔥 Próxima série!")
    time.sleep(2)
    placeholder.empty()
    progresso.empty()

# --- 4. DADOS DO TREINO (Lógica Adaptativa) ---
st.sidebar.title("♣️ Black Clover")
st.sidebar.markdown("---")

semana = st.sidebar.selectbox(
    "Semana do Ciclo", [1, 2, 3, 4],
    format_func=lambda x: f"Semana {x} - {'Volume' if x <= 2 else 'INTENSIDADE' if x == 3 else 'Deload'}"
)

dia_semana = st.sidebar.selectbox(
    "Treino de Hoje",
    ["Segunda (Upper Força)", "Terça (Lower Força)", "Quarta (Descanso)", 
     "Quinta (Upper Hipertrofia)", "Sexta (Lower Hipertrofia)", "Sábado (Ombros/Braços)"]
)

# Definição automática do tempo de descanso baseada no tipo de treino
tempo_descanso_base = 60 # padrão
if "Força" in dia_semana:
    tempo_descanso_base = 120 # 2 min para força
elif "Hipertrofia" in dia_semana:
    tempo_descanso_base = 90
elif semana == 4:
    tempo_descanso_base = 45 # Deload rápido

st.sidebar.markdown("---")
st.sidebar.caption("🚑 Adaptações")
dor_joelho = st.sidebar.checkbox("Dor Joelho", value=False)
dor_costas = st.sidebar.checkbox("Dor Costas", value=False)

# Funções de Adaptação
def adaptar_nome(nome):
    if dor_joelho and ("Agachamento" in nome or "Afundo" in nome):
        return f"⚠️ {nome} (SUBSTITUIR POR LEG PRESS)"
    if dor_costas and "Curvada" in nome:
        return f"{nome} (Apoiado no banco)"
    return nome

# Base de Dados dos Exercícios
treinos_db = {
    "Segunda (Upper Força)": [
        {"ex": "Supino Reto", "series": "4", "reps": "5", "rpe": "8-9"},
        {"ex": "Remada Curvada", "series": "4", "reps": "6", "rpe": "8"},
        {"ex": "Desenvolvimento Militar", "series": "3", "reps": "6", "rpe": "8"},
        {"ex": "Puxada Frente", "series": "3", "reps": "8", "rpe": "8"},
        {"ex": "Face Pull", "series": "3", "reps": "12", "rpe": "8"}
    ],
    "Terça (Lower Força)": [
        {"ex": "Agachamento Livre", "series": "4", "reps": "5", "rpe": "8"},
        {"ex": "Stiff", "series": "3", "reps": "6", "rpe": "8"},
        {"ex": "Afundo", "series": "3", "reps": "8", "rpe": "7"},
        {"ex": "Gémeos Sentado", "series": "4", "reps": "12", "rpe": "8"},
        {"ex": "Bird-Dog (Core)", "series": "3", "reps": "8", "rpe": "-"}
    ],
     "Quinta (Upper Hipertrofia)": [
        {"ex": "Supino Inclinado Halter", "series": "3", "reps": "10", "rpe": "7-8"},
        {"ex": "Puxada Lateral", "series": "4", "reps": "10", "rpe": "8"},
        {"ex": "Remada Baixa", "series": "3", "reps": "10", "rpe": "8"},
        {"ex": "Desenvolvimento Arnold", "series": "3", "reps": "10", "rpe": "8"},
        {"ex": "Elevação Lateral", "series": "3", "reps": "12", "rpe": "Falha"}
    ],
    "Sexta (Lower Hipertrofia)": [
        {"ex": "Hack Squat/Leg Press", "series": "4", "reps": "10", "rpe": "7"},
        {"ex": "Hip Thrust", "series": "3", "reps": "10", "rpe": "7"},
        {"ex": "Cadeira Extensora", "series": "3", "reps": "12", "rpe": "8"},
        {"ex": "Mesa Flexora", "series": "3", "reps": "12", "rpe": "8"},
        {"ex": "Abs Bicicleta", "series": "3", "reps": "15", "rpe": "-"}
    ],
    "Sábado (Ombros/Braços)": [
        {"ex": "Press Militar", "series": "3", "reps": "6", "rpe": "8"},
        {"ex": "Elevação Lateral Unilateral", "series": "3", "reps": "12", "rpe": "Falha"},
        {"ex": "Pallof Press", "series": "3", "reps": "12", "rpe": "Core"},
        {"ex": "Bíceps/Tríceps (Super-série)", "series": "3", "reps": "10", "rpe": "8"}
    ]
}

# --- 5. INTERFACE PRINCIPAL ---

tab_treino, tab_hist = st.tabs(["🔥 Treino do Dia", "📊 Histórico Geral"])

with tab_treino:
    st.subheader(f"{dia_semana}")
    
    if dia_semana == "Quarta (Descanso)":
        st.info("Hoje é dia de descanso ativo! Faz 30 min de caminhada e alongamentos.")
    else:
        exercicios_hoje = treinos_db.get(dia_semana, [])
        
        # BARRA DE PROGRESSO DO TREINO
        total_ex = len(exercicios_hoje)
        completed = st.session_state.get(f"progress_{dia_semana}", 0)
        st.progress(completed / total_ex if total_ex > 0 else 0)

        # LOOP PELOS EXERCÍCIOS
        for i, item in enumerate(exercicios_hoje):
            nome_real = adaptar_nome(item['ex'])
            target_series = item['series']
            target_reps = item['reps']
            target_rpe = item['rpe']
            
            # Ajuste de Deload
            if semana == 4: 
                target_rpe = "Leve"
            
            # --- CARTÃO DO EXERCÍCIO ---
            with st.expander(f"{i+1}. {nome_real} | {target_series}x{target_reps}", expanded=(i==0)):
                
                # Coluna 1: Metas e Timer | Coluna 2: Inputs de Registo
                c1, c2 = st.columns([1, 1.5])
                
                with c1:
                    st.markdown(f"**Meta:** {target_reps} reps")
                    st.markdown(f"**RPE:** {target_rpe}")
                    st.markdown("---")
                    
                    # TIMER AUTOMÁTICO
                    # Se for composto (Agachamento/Supino) dá mais tempo, se for isolado dá menos
                    tempo_local = tempo_descanso_base
                    if "Bíceps" in nome_real or "Lateral" in nome_real: tempo_local -= 30
                    
                    if st.button(f"⏱️ Descanso ({tempo_local}s)", key=f"btn_time_{i}"):
                        timer_descanso(tempo_local)

                with c2:
                    st.markdown("##### 📝 Registar Série")
                    with st.form(key=f"form_{dia_semana}_{i}"):
                        col_w, col_r = st.columns(2)
                        peso_input = col_w.number_input("Carga (kg)", step=2.5, min_value=0.0)
                        reps_input = col_r.number_input("Reps Feitas", step=1, value=int(target_reps) if target_reps.isdigit() else 8)
                        
                        rpe_input = st.slider("RPE Sentido", 1, 10, 8)
                        nota_input = st.text_input("Nota rápida", placeholder="Ex: Joelho estalou")
                        
                        submit = st.form_submit_button("✅ Salvar Série")
                        
                        if submit:
                            salvar_set(nome_real, peso_input, reps_input, rpe_input, nota_input)
                            st.success(f"Registado: {peso_input}kg")

with tab_hist:
    st.header("O teu Diário")
    df = get_data()
    
    if not df.empty:
        # Filtro rápido
        filtro_ex = st.multiselect("Filtrar por Exercício", df["Exercício"].unique())
        if filtro_ex:
            df = df[df["Exercício"].isin(filtro_ex)]
        
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
        
        # Botão de Download para Excel
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Histórico (CSV)", data=csv, file_name="meu_treino_log.csv")
    else:
        st.info("Ainda não tens registos. Começa a treinar! 💪")
