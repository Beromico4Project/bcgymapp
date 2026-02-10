import streamlit as st
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="V-Shape Planner", page_icon="💪", layout="centered")

# --- CABEÇALHO ---
st.title("🏋️‍♂️ Plano V-Shape Adaptativo")
st.markdown("Foco: Ombros/Dorsais largos, Cintura estreita. Periodização em Ondas.")

# --- BARRA LATERAL (INPUTS) ---
st.sidebar.header("⚙️ Configuração Diária")

# Seleção da Semana (Lógica de Ondas)
semana = st.sidebar.selectbox(
    "Semana do Ciclo",
    [1, 2, 3, 4],
    format_func=lambda x: f"Semana {x} - {'Volume Moderado' if x <= 2 else 'INTENSIDADE MÁXIMA' if x == 3 else 'Deload/Recuperação'}"
)

# Seleção do Dia
dia_semana = st.sidebar.selectbox(
    "Treino de Hoje",
    ["Segunda (Upper Força)", "Terça (Lower Força)", "Quarta (Descanso Ativo)", 
     "Quinta (Upper Hipertrofia)", "Sexta (Lower Hipertrofia)", "Sábado (Ombros/Braços)"]
)

# Inputs de Estado Físico (Adaptação a Lesões)
st.sidebar.markdown("---")
st.sidebar.subheader("🚑 Estado Físico")
dor_joelho = st.sidebar.checkbox("Sentindo desconforto no joelho?", value=False)
dor_costas = st.sidebar.checkbox("Desconforto na lombar/escoliose?", value=False)

# --- LÓGICA ADAPTATIVA ---

def get_intensidade(sem):
    if sem <= 2: return "RPE 7-8 (Moderado)"
    if sem == 3: return "RPE 9 (Quase Falha) - Aumentar Carga"
    return "RPE 6-7 (Leve/Técnica) - Carga 50-60%"

def get_descanso(sem):
    if sem == 4: return "Pausas curtas, foco em mobilidade"
    return "2-3 min compostos, 1-2 min acessórios"

# Funções de Substituição de Exercícios por Lesão
def adaptar_agachamento(exercicio_base):
    if dor_joelho:
        return "⚠️ Leg Press ou Agachamento Parcial (4x6) - Não travar joelhos [Adaptado]"
    return exercicio_base

def adaptar_coluna(exercicio_base):
    if dor_costas:
        return f"{exercicio_base} (Fazer com apoio ou unilateral para simetria)"
    return exercicio_base

# --- ESTRUTURA DOS TREINOS ---
treinos = {
    "Segunda (Upper Força)": [
        {"ex": "Supino Reto (Barra)", "series": "4x5", "rpe": "8-9"},
        {"ex": adaptar_coluna("Remada Curvada"), "series": "4x6", "rpe": "8"},
        {"ex": "Desenvolvimento Militar", "series": "3x6", "rpe": "8"},
        {"ex": "Puxada Frente", "series": "3x8", "rpe": "8"},
        {"ex": "Face Pull + Core", "series": "3x12", "obs": "Foco em postura"},
    ],
    "Terça (Lower Força)": [
        {"ex": adaptar_agachamento("Agachamento Livre 4x5"), "rpe": "8"},
        {"ex": "Stiff (Terra Romeno)", "series": "3x6", "rpe": "8"},
        {"ex": adaptar_agachamento("Afundo/Split Squat 3x8"), "rpe": "7"},
        {"ex": "Elevação de Gémeos", "series": "4x12", "rpe": "8"},
        {"ex": "Bird-Dog (Core)", "series": "3x8/lado", "obs": "Estabilidade espinhal"}
    ],
    "Quarta (Descanso Ativo)": [
        {"ex": "Caminhada ou Cardio Leve", "tempo": "20-30 min", "obs": "Manter circulação sem fadiga"},
        {"ex": "Mobilidade de Coluna (Cat-Camel)", "series": "3 rounds", "obs": "Soltar a rigidez"},
        {"ex": "Alongamento Cadeia Posterior", "series": "2x30s", "obs": "Glúteos e Isquios"}
    ],
    "Quinta (Upper Hipertrofia)": [
        {"ex": "Supino Inclinado Halteres", "series": "3x10", "rpe": "7-8"},
        {"ex": "Puxada Lateral Aberta", "series": "4x8-10", "rpe": "8"},
        {"ex": "Remada Baixa", "series": "3x8-10", "rpe": "8"},
        {"ex": "Desenvolvimento Arnold", "series": "3x10", "rpe": "8"},
        {"ex": "Elevação Lateral + Tríceps", "series": "3x12", "rpe": "Falha -1"}
    ],
    "Sexta (Lower Hipertrofia)": [
        {"ex": adaptar_agachamento("Hack Squat ou Leg Press"), "series": "4x10", "rpe": "7"},
        {"ex": "Hip Thrust (Ponte)", "series": "3x8-10", "rpe": "7"},
        {"ex": "Cadeira Extensora (Leve)", "series": "3x12", "obs": "Cuidado com joelho"},
        {"ex": "Mesa Flexora", "series": "3x12", "rpe": "8"},
        {"ex": "Abdominal Bicicleta", "series": "3x15", "rpe": "-"}
    ],
    "Sábado (Ombros/Braços)": [
        {"ex": "Press Militar", "series": "3x6", "rpe": "8"},
        {"ex": "Elevação Lateral Unilateral", "series": "3x12", "rpe": "Falha"},
        {"ex": "Pallof Press (Obrigatório)", "series": "3x12/lado", "obs": "Para Escoliose/Core"},
        {"ex": "Super-série: Bíceps/Tríceps", "series": "3x10", "rpe": "8"},
        {"ex": "Caminhada Leve", "tempo": "10 min", "obs": "Resfriamento"}
    ]
}

# --- RENDERIZAÇÃO NA TELA ---

st.header(f"📅 {dia_semana}")
st.subheader(f"Fase: {get_intensidade(semana)}")

# Mensagens de Alerta
if dor_joelho and "Lower" in dia_semana:
    st.error("🚨 Modo Joelho Ativado: Agachamentos livres removidos. Foco em estabilidade e Leg Press.")
    st.info("💡 Lembrete: Mantenha joelhos alinhados e fortaleça glúteos [Fonte: Dr. Itamar].")

if semana == 4:
    st.success("🟢 Semana de Deload: Reduza cargas em 40-50%. Foco total na técnica.")
elif semana == 3:
    st.warning("🔥 Semana de Choque: Tente aumentar 1kg ou 1 repetição em relação à semana passada.")

# Exibição do Treino
st.divider()

if dia_semana in treinos:
    lista_exercicios = treinos[dia_semana]
    
    for item in lista_exercicios:
        with st.container():
            # Formatação visual do exercício
            col1, col2 = st.columns([3, 1])
            
            nome = item.get("ex", "Exercício")
            series = item.get("series", "-")
            rpe = item.get("rpe", "-")
            obs = item.get("obs", "")
            tempo = item.get("tempo", "")
            
            # Ajuste de Deload (Semana 4)
            if semana == 4 and "series" in item:
                # Reduz séries visualmente
                series = f"{series} (Fazer -1 série)"
                rpe = "RPE 6 (Leve)"

            with col1:
                st.markdown(f"**{nome}**")
                if obs: st.caption(f"ℹ️ {obs}")
            
            with col2:
                if tempo:
                    st.markdown(f"⏱️ {tempo}")
                else:
                    st.markdown(f"🔢 {series}")
                    st.markdown(f"🔥 {rpe}")
            
            st.markdown("---")

# --- CHECKLIST FINAL ---
st.checkbox("Mobilidade Inicial Feita? (Foco Escoliose)")
st.checkbox("Cardio Final (Circulação)?")

if st.button("Concluir Treino"):
    st.balloons()
    st.success("Treino registrado! Bom descanso.")