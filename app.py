import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="V-Shape Project", page_icon="🦍", layout="centered")

# --- 2. CONEXÃO GOOGLE SHEETS & DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # ttl=0 obriga a ler os dados frescos da nuvem
        return conn.read(ttl="0")
    except:
        return pd.DataFrame(columns=["Data", "Exercício", "Peso", "Reps", "RPE", "Notas"])

def get_ultimo_registro(exercicio):
    """Procura o peso e reps do último treino deste exercício específico"""
    df = get_data()
    if df.empty:
        return None, None
    
    # Filtra pelo exercício e pega o último registo
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

# --- 3. LÓGICA DO PLANO (Baseado no DOCX) ---
# Base de dados fiel ao documento "Plano Semanal de Musculação"
treinos_db = {
    "Segunda (Upper Força)": [
        {"ex": "Supino Reto (Barra)", "series": "4", "reps": "5", "rpe": "8-9"},
        {"ex": "Remada Curvada", "series": "4", "reps": "6", "rpe": "8"},
        {"ex": "Desenvolvimento Militar", "series": "3", "reps": "6", "rpe": "8"},
        {"ex": "Puxada Frente", "series": "3", "reps": "8", "rpe": "8"},
        {"ex": "Face Pull", "series": "3", "reps": "12", "rpe": "8 (Deltoide Post)"},
        {"ex": "Rosca Direta", "series": "2", "reps": "10-12", "rpe": "8"},
        {"ex": "Tríceps Testa", "series": "2", "reps": "10-12", "rpe": "8"}
    ],
    "Terça (Lower Força)": [
        {"ex": "Agachamento Livre", "series": "4", "reps": "5", "rpe": "8"},
        {"ex": "Stiff (Terra Romeno)", "series": "3", "reps": "6", "rpe": "8"},
        {"ex": "Afundo (Split Squat)", "series": "3", "reps": "8", "rpe": "7 (Cada perna)"},
        {"ex": "Leg Press", "series": "3", "reps": "8", "rpe": "8"},
        {"ex": "Elevação de Gémeos", "series": "4", "reps": "12", "rpe": "8"},
        {"ex": "Bird-Dog (Core)", "series": "3", "reps": "8", "rpe": "Controle"}
    ],
    "Quinta (Upper Hipertrofia)": [
        {"ex": "Supino Inclinado Halteres", "series": "3", "reps": "10", "rpe": "7-8"},
        {"ex": "Puxada Lateral Aberta", "series": "4", "reps": "8-10", "rpe": "8"},
        {"ex": "Remada Baixa Sentada", "series": "3", "reps": "8-10", "rpe": "8"},
        {"ex": "Desenvolvimento Arnold", "series": "3", "reps": "10", "rpe": "8"},
        {"ex": "Elevação Lateral", "series": "3", "reps": "12", "rpe": "Falha"},
        {"ex": "Rosca Martelo", "series": "2", "reps": "12", "rpe": "Falha-1"},
        {"ex": "Paralela Assistida", "series": "2", "reps": "12", "rpe": "Falha-1"}
    ],
    "Sexta (Lower Hipertrofia)": [
        {"ex": "Hack Squat ou Leg Press", "series": "4", "reps": "10", "rpe": "7"},
        {"ex": "Hip Thrust (Ponte)", "series": "3", "reps": "10", "rpe": "7"},
        {"ex": "Stiff", "series": "3", "reps": "10", "rpe": "8"},
        {"ex": "Cadeira Extensora", "series": "3", "reps": "12", "rpe": "Leve (Joelho)"},
        {"ex": "Mesa Flexora", "series": "3", "reps": "12", "rpe": "8"},
        {"ex": "Abs Bicicleta", "series": "3", "reps": "15", "rpe": "-"}
    ],
    "Sábado (Ombros/Braços/Costas)": [
        {"ex": "Press Militar", "series": "3", "reps": "6", "rpe": "8"},
        {"ex": "Elevação Lateral Unilateral", "series": "3", "reps": "12", "rpe": "Falha"},
        {"ex": "Remada Curvada Supinada", "series": "3", "reps": "8", "rpe": "8"},
        {"ex": "Remada Alta", "series": "3", "reps": "10", "rpe": "8"},
        {"ex": "Pallof Press (Escoliose)", "series": "3", "reps": "12", "rpe": "Core"},
        {"ex": "Super-série: Bíceps/Tríceps", "series": "3", "reps": "10", "rpe": "8"}
    ]
}

def timer_descanso(segundos):
    with st.empty():
        for i in range(segundos, 0, -1):
            st.metric("Descanso", f"{i}s")
            time.sleep(1)
        st.success("Bora! Próxima série! 🔥")

# --- 4. INTERFACE ---
st.sidebar.header("Configuração")
semana = st.sidebar.selectbox("Semana Atual", [1, 2, 3, 4], format_func=lambda x: f"Semana {x} ({'Deload' if x==4 else 'Choque' if x==3 else 'Base'})")
dia_semana = st.sidebar.selectbox("Treino de Hoje", list(treinos_db.keys()) + ["Quarta (Descanso Ativo)"])

# Ajustes de Lesão
st.sidebar.markdown("---")
dor_joelho = st.sidebar.checkbox("Dor no Joelho?", value=False)
dor_costas = st.sidebar.checkbox("Desconforto Costas?", value=False)

def adaptar_exercicio(nome):
    if dor_joelho and ("Agachamento" in nome or "Afundo" in nome):
        return f"⚠️ {nome} (USAR LEG PRESS)"
    if dor_costas and "Curvada" in nome:
        return f"{nome} (Com apoio de peito)"
    return nome

# CORPO PRINCIPAL
st.title("🏋️‍♂️ V-Shape Log")

tab_treino, tab_hist = st.tabs(["Treino Hoje", "Histórico Completo"])

with tab_treino:
    st.subheader(f"{dia_semana}")
    
    if dia_semana == "Quarta (Descanso Ativo)":
        st.info("Hoje: Caminhada 20-30 min + Mobilidade (Cat-Camel). Foco na recuperação!")
    else:
        exercicios = treinos_db.get(dia_semana, [])
        
        # Barra de Progresso
        progresso = st.progress(0)
        
        for i, item in enumerate(exercicios):
            nome_real = adaptar_exercicio(item['ex'])
            
            # Busca última carga usada
            last_weight, last_reps = get_ultimo_registro(nome_real)
            
            with st.expander(f"{i+1}. {nome_real}", expanded=(i==0)):
                # Cabeçalho com Meta
                st.markdown(f"**Meta:** {item['series']} Séries x {item['reps']} Reps @ RPE {item['rpe']}")
                
                # Mostrar histórico se existir
                if last_weight:
                    st.info(f"🔙 **Último Treino:** {last_weight}kg x {last_reps} reps")
                else:
                    st.caption("Primeira vez neste exercício.")
                
                # Formulário de Registo
                with st.form(key=f"form_{dia_semana}_{i}"):
                    c1, c2, c3 = st.columns([1, 1, 2])
                    peso = c1.number_input("Carga (kg)", min_value=0.0, step=1.0, value=float(last_weight) if last_weight else 0.0)
                    reps_feitas = c2.number_input("Reps", min_value=0, step=1, value=int(item['reps'].split('-')[0]) if '-' in item['reps'] else int(item['reps']))
                    nota = c3.text_input("Notas (Dificuldade/Dor)")
                    
                    if st.form_submit_button("💾 Salvar Série"):
                        salvar_set(nome_real, peso, reps_feitas, item['rpe'], nota)
                        st.toast(f"Salvo: {nome_real} - {peso}kg")
                
                # Timer
                tempo = 120 if "Força" in dia_semana else 90
                if st.button(f"⏱️ Descanso ({tempo}s)", key=f"timer_{i}"):
                    timer_descanso(tempo)

        st.success("Não te esqueças: Cardio final leve (5-10min) para circulação!")

with tab_hist:
    st.subheader("Diário de Evolução")
    df = get_data()
    if not df.empty:
        ex_filter = st.selectbox("Filtrar por Exercício", ["Todos"] + list(df["Exercício"].unique()))
        
        if ex_filter != "Todos":
            df = df[df["Exercício"] == ex_filter]
        
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("Ainda sem dados. Bom treino!")
