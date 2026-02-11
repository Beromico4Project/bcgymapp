import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Black Clover Workout", page_icon="♣️", layout="centered")
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

# --- 4. LÓGICA DE PERIODIZAÇÃO ---
def gerar_treino_do_dia(dia, semana):
    treino_base = treinos_base.get(dia, [])
    treino_final = []

    for item in treino_base:
        novo_item = item.copy()
        
        # --- SEMANA 3: CHOQUE ---
        if semana == 3:
            if item["tipo"] == "composto":
                novo_item["series"] += 1 
                novo_item["rpe"] = 9
                if novo_item["reps"] == "5": pass 
            else:
                novo_item["rpe"] = 9

        # --- SEMANA 4: DELOAD ---
        elif semana == 4:
            novo_item["series"] = max(2, item["series"] - 1)
            novo_item["rpe"] = 6
            if item["reps"] == "5":
                novo_item["reps"] = "6"
        
        treino_final.append(novo_item)
    
    return treino_final

# --- 5. INTERFACE ---
st.sidebar.title("♣️ Black Clover")
st.sidebar.header("Planeamento")

semana = st.sidebar.radio(
    "Fase Atual:",
    [1, 2, 3, 4],
    format_func=lambda x: f"Semana {x}: {'Volume Moderado (RPE 8)' if x<=2 else 'INTENSIDADE MÁXIMA (RPE 9)' if x==3 else 'Deload (RPE 6)'}"
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

# --- CORPO PRINCIPAL COM ABAS ---
st.title("Black Clover Workout ⚔️")

# CRIAÇÃO DAS ABAS AQUI
tab_treino, tab_historico = st.tabs(["🔥 Treino do Dia", "📜 Histórico"])


# --- ABA 1: TREINO ---
with tab_treino:
    # 1. GUIA RPE (NOVO)
    with st.expander("ℹ️ Guia de RPE (Como escolher a carga?)"):
        st.markdown("""
        **RPE = Rate of Perceived Exertion (Esforço Percebido)**
        
        * 🔴 **RPE 10 (Falha Total):** Não consegues fazer mais nenhuma repetição.
        * 🟠 **RPE 9 (Muito Pesado):** Conseguias fazer **apenas mais 1** repetição. (Foco da Semana 3)[cite: 66].
        * 🟡 **RPE 8 (Pesado):** Conseguias fazer **mais 2** repetições. (Foco das Semanas 1-2) [cite: 15, 26].
        * 🟢 **RPE 6-7 (Leve/Técnica):** Conseguias fazer **mais 3 ou 4** repetições. Velocidade rápida. (Foco da Semana 4/Deload) [cite: 89].
        """)

    if dia == "Descanso":
        st.info("Hoje é dia de descanso ativo. Caminhada 30min e Mobilidade.")
    else:
        treino_hoje = gerar_treino_do_dia(dia, semana)
        
        total = len(treino_hoje)
        prog = st.progress(0)

        for i, item in enumerate(treino_hoje):
            nome_display = adaptar_nome(item['ex'])
            series_reais = item['series']
            reps_reais = item['reps']
            rpe_real = item['rpe']
            
            last_w, last_r = get_ultimo_registro(nome_display)
            
            with st.expander(f"{i+1}. {nome_display}", expanded=(i==0)):
                col_info1, col_info2 = st.columns(2)
                
                # 2. DESCRIÇÃO DINÂMICA MELHORADA
                if rpe_real >= 9:
                    rpe_text = "🔴 MUITO PESADO (Sobra 1 rep)"
                elif rpe_real <= 7:
                    rpe_text = "🟢 LEVE (Sobram 3-4 reps)"
                else:
                    rpe_text = "🟡 PESADO (Sobram 2 reps)"
                
                col_info1.markdown(f"**Meta:** {series_reais} Séries x {reps_reais} Reps")
                col_info2.markdown(f"**{rpe_text}**") # RPE mais visível

                if last_w:
                    st.caption(f"🔙 Anterior: {last_w}kg ({last_r} reps)")

                with st.form(key=f"form_{i}"):
                    c1, c2, c3 = st.columns([1,1,2])
                    peso = c1.number_input("Peso (kg)", value=float(last_w) if last_w else 0.0, step=2.5)
                    reps = c2.number_input("Reps", value=int(str(reps_reais).split('-')[0]), step=1)
                    notas = c3.text_input("Notas", placeholder="Dificuldade?")
                    
                    if st.form_submit_button("Gravar Série"):
                        salvar_set(nome_display, peso, reps, rpe_real, notas)
                        st.success("Registado!")
                
                tempo_descanso = 180 if item["tipo"] == "composto" and semana != 4 else 90
                if st.button(f"⏱️ Descanso ({tempo_descanso}s)", key=f"t_{i}"):
                    with st.empty():
                        for s in range(tempo_descanso, 0, -1):
                            st.metric("Descansa...", f"{s}s")
                            time.sleep(1)
                        st.success("BORA!")

        st.divider()
        st.markdown("### 🏁 Checkout")
        
        c_end1, c_end2 = st.columns(2)
        with c_end1: st.checkbox("Cardio Leve (5-10min)?")
        with c_end2: st.checkbox("Mobilidade Final?")

        if st.button("TERMINAR TREINO (Superar Limites!)", type="primary"):
            st.balloons()
            st.success("TREINO CONCLUÍDO! O teu grimório está mais forte. 💪♣️")
            time.sleep(3)
            st.rerun()

# --- ABA 2: HISTÓRICO ---
with tab_historico:
    st.header("Grimório de Treinos 📖")
    df = get_data()
    
    if not df.empty:
        # Filtros
        lista_exercicios = df["Exercício"].unique()
        filtro_ex = st.multiselect("Filtrar por exercício:", lista_exercicios)
        
        if filtro_ex:
            df_filtrado = df[df["Exercício"].isin(filtro_ex)]
        else:
            df_filtrado = df
            
        st.dataframe(
            df_filtrado.sort_index(ascending=False), 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Ainda não tens registos no teu grimório. Começa a treinar!")


