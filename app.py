import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro", layout="wide", page_icon="🍎")

# --- CONEXÃO E CRIAÇÃO DO BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('nutri_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, idade INTEGER, objetivo TEXT, historico TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS agenda 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, horario TEXT, paciente TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS financeiro 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL, metodo TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- ESTILIZAÇÃO CSS (QUADROS AZUL ESCURO) ---
st.markdown("""
    <style>
    /* Fundo principal */
    .main { background-color: #f8f9fa; }

    /* Estilo dos Quadros de Métrica (Azul Escuro) */
    div[data-testid="metric-container"] {
        background-color: #002b5b; 
        border: 1px solid #001f3f;
        padding: 20px;
        border-radius: 12px;
        color: white;
    }

    /* Forçar texto das métricas para branco */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stMetricDeltaIcon"] {
        color: white !important;
    }

    /* Botões */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #2e7d32;
        color: white;
        font-weight: bold;
    }
    
    /* Ajuste da Barra Lateral */
    .css-1d391kg { background-color: #f1f3f5; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("🍎 NutriSync Pro")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação", [
    "Dashboard", 
    "Prontuário (Anamnese)", 
    "Antropometria", 
    "Plano Alimentar", 
    "Suplementação", 
    "Financeiro"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Painel de Controle")
    
    # Busca dados reais para os quadros
    qtd_pacientes = pd.read_sql_query("SELECT COUNT(*) as total FROM pacientes", conn).iloc[0]['total']
    receita_total = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    consultas_hoje = pd.read_sql_query("SELECT COUNT(*) as total FROM agenda", conn).iloc[0]['total']
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", qtd_pacientes)
    col2.metric("Consultas Agendadas", consultas_hoje)
    col3.metric("Receita Total", f"R$ {receita_total:,.2f}")
    
    st.divider()
    
    st.subheader("📅 Agenda do Dia")
    agenda_df = pd.read_sql_query("SELECT horario as 'Horário', paciente as 'Paciente', status as 'Status' FROM agenda", conn)
    
    if agenda_df.empty:
        st.info("Agenda vazia para hoje.")
    else:
        st.table(agenda_df)

    # Formulário para alimentar a agenda
    with st.expander("➕ Adicionar Novo Agendamento"):
        with st.form("add_agenda_form"):
            h = st.text_input("Horário (ex: 14:30)")
            p = st.text_input("Nome do Paciente")
            s = st.selectbox("Status", ["Confirmado", "Pendente", "Online"])
            if st.form_submit_button("Confirmar Agendamento"):
                c.execute("INSERT INTO agenda (horario, paciente, status) VALUES (?,?,?)", (h, p, s))
                conn.commit()
                st.success("Agendado com sucesso!")
                st.rerun()

# --- 2. PRONTUÁRIO ---
elif menu == "Prontuário (Anamnese)":
    st.title("📝 Prontuário Eletrônico")
    tab1, tab2 = st.tabs(["Novo Cadastro", "Lista de Pacientes"])
    
    with tab1:
        with st.form("anamnese"):
            nome = st.text_input("Nome Completo")
            idade = st.number_input("Idade", 0, 120, 25)
            obj = st.selectbox("Objetivo", ["Emagrecimento", "Ganho de Massa", "Saúde", "Performance"])
            hist = st.text_area("Histórico Clínico e Queixas")
            if st.form_submit_button("Salvar Registro"):
                c.execute("INSERT INTO pacientes (nome, idade, objetivo, historico) VALUES (?,?,?,?)", (nome, idade, obj, hist))
                conn.commit()
                st.success("Paciente cadastrado!")

    with tab2:
        df_p = pd.read_sql_query("SELECT nome as Nome, idade as Idade, objetivo as Objetivo FROM pacientes", conn)
        st.dataframe(df_p, use_container_width=True)

# --- 3. ANTROPOMETRIA ---
elif menu == "Antropometria":
    st.title("⚖️ Composição Corporal")
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Peso Atual (kg)", 30.0, 250.0, 70.0)
        altura = st.number_input("Altura (cm)", 100, 250, 170)
    
    imc = peso / ((altura/100)**2)
    
    with col2:
        st.metric("Seu IMC", f"{imc:.2f}")
        if imc < 18.5: st.warning("Abaixo do peso")
        elif imc < 25: st.success("Peso saudável")
        else: st.error("Sobrepeso")

# --- 4. PLANO ALIMENTAR ---
elif menu == "Plano Alimentar":
    st.title("🍽️ Prescrição de Plano Alimentar")
    pacientes = pd.read_sql_query("SELECT nome FROM pacientes", conn)['nome'].tolist()
    if pacientes:
        st.selectbox("Selecionar Paciente", pacientes)
        st.text_area("Refeição 1: Café da Manhã")
        st.text_area("Refeição 2: Almoço")
        st.text_area("Refeição 3: Jantar")
        st.button("Salvar Dieta")
    else:
        st.warning("Cadastre um paciente primeiro para elaborar a dieta.")

# --- 5. SUPLEMENTAÇÃO ---
elif menu == "Suplementação":
    st.title("💊 Prescrição de Suplementos")
    with st.form("suple"):
        item = st.text_input("Suplemento/Fórmula")
        dose = st.text_input("Posologia (ex: 1 cápsula após almoço)")
        if st.form_submit_button("Gerar Prescrição"):
            st.write(f"**Prescrito:** {item} - {dose}")

# --- 6. FINANCEIRO ---
elif menu == "Financeiro":
    st.title("💰 Gestão Financeira")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Nova Entrada")
        val = st.number_input("Valor da Consulta (R$)", 0.0)
        met = st.selectbox("Método", ["Pix", "Cartão", "Dinheiro"])
        if st.button("Registrar"):
            dt = datetime.now().strftime("%d/%m/%Y")
            c.execute("INSERT INTO financeiro (data, valor, metodo) VALUES (?,?,?)", (dt, val, met))
            conn.commit()
            st.success("Registrado!")
            st.rerun()

    with col2:
        st.subheader("Histórico de Recebimentos")
        df_f = pd.read_sql_query("SELECT data as Data, valor as Valor, metodo as Método FROM financeiro", conn)
        st.dataframe(df_f, use_container_width=True)

# --- RODAPÉ ---
st.sidebar.markdown("---")
st.sidebar.caption(f"Versão 1.0 - {datetime.now().year}")
