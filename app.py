import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

st.set_page_config(page_title="V-Shape Tracker", page_icon="📈")

# Ligação ao Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler dados
def get_data():
    return conn.read(ttl="0") # ttl=0 para atualizar sempre

st.title("🚀 V-Shape Training Log")

tab1, tab2 = st.tabs(["📝 Registar Treino", "📊 Histórico"])

with tab1:
    with st.form("treino_form"):
        # Lista baseada no teu documento (Upper/Lower/V-Shape)
        exercicios = [
            "Supino Reto (Barra)", "Remada Curvada", "Desenvolvimento Militar",
            "Puxada Frente", "Agachamento Livre", "Stiff (Terra Romeno)",
            "Afundo/Split Squat", "Elevação de Gémeos", "Supino Inclinado Halteres",
            "Puxada Lateral Aberta", "Remada Baixa", "Desenvolvimento Arnold",
            "Elevação Lateral", "Hack Squat / Leg Press", "Hip Thrust",
            "Cadeira Extensora", "Mesa Flexora", "Press Militar", "Pallof Press"
        ]
        
        ex = st.selectbox("Exercício", exercicios)
        col1, col2 = st.columns(2)
        peso = col1.number_input("Peso (kg)", min_value=0.0, step=0.5)
        rpe = col2.select_slider("RPE (Esforço)", options=list(range(1, 11)), value=8)
        notas = st.text_area("Notas (ex: senti a escoliose, joelho OK)")
        
        submit = st.form_submit_button("Gravar no Google Sheets")

        if submit:
            # Obter dados atuais
            df_existente = get_data()
            
            # Novo registo
            novo_dado = pd.DataFrame([{
                "Data": datetime.date.today().strftime("%d/%m/%Y"),
                "Exercício": ex,
                "Peso": peso,
                "RPE": rpe,
                "Notas": notas
            }])
            
            # Concatenar e atualizar
            df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
            conn.update(data=df_final)
            st.success("Dados gravados na nuvem! ✅")

with tab2:
    st.subheader("O teu progresso")
    dados = get_data()
    if not dados.empty:
        # Filtro simples
        search = st.text_input("Filtrar exercício:")
        if search:
            dados = dados[dados["Exercício"].str.contains(search, case=False)]
        
        st.dataframe(dados.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("Ainda não há dados na folha de cálculo.")
