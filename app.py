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
    # Tabela de Pacientes
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, idade INTEGER, objetivo TEXT, historico TEXT)''')
    # Tabela de Agenda
    c.execute('''CREATE TABLE IF NOT EXISTS agenda 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, horario TEXT, paciente TEXT, status TEXT)''')
    # Tabela Financeira
    c.execute('''CREATE TABLE IF NOT EXISTS financeiro 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL, metodo TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; background-color: #2e7d32; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("🍎 NutriSync Pro")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Ir para:", [
    "Dashboard", 
    "Prontuário (Anamnese)", 
    "Antropometria", 
    "Plano Alimentar", 
    "Suplementação", 
    "Financeiro"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Painel Geral")
    
    # Busca dados para os cards
    qtd_pacientes = pd.read_sql_query("SELECT COUNT(*) as total FROM pacientes", conn).iloc[0]['total']
    receita_total = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", qtd_pacientes)
    col2.metric("Consultas Hoje", "0") # Pode ser automatizado com filtro de data
    col3.metric("Receita Total", f"R$ {receita_total:,.2f}")
    
    st.divider()
    
    st.subheader("📅 Agenda do Dia")
    agenda_df = pd.read_sql_query("SELECT horario as 'Horário', paciente as 'Paciente', status as 'Status' FROM agenda", conn)
    
    if agenda_df.empty:
        st.info("Sua agenda para hoje está vazia.")
    else:
        st.table(agenda_df)

    # Formulário rápido para adicionar à agenda
    with st.expander("➕ Novo Agendamento"):
        with st.form("add_agenda"):
            h = st.text_input("Horário (ex: 14:00)")
            p = st.text_input("Nome do Paciente")
            s = st.selectbox("Status", ["Confirmado", "Pendente", "Online"])
            if st.form_submit_button("Agendar"):
                c.execute("INSERT INTO agenda (horario, paciente, status) VALUES (?,?,?)", (h, p, s))
                conn.commit()
                st.success("Agendado!")
                st.rerun()

# --- 2. PRONTUÁRIO ---
elif menu == "Prontuário (Anamnese)":
    st.title("📝 Cadastro e Anamnese")
    
    tab1, tab2 = st.tabs(["Novo Cadastro", "Ver Pacientes"])
    
    with tab1:
        with st.form("form_paciente"):
            nome = st.text_input("Nome Completo")
            idade = st.number_input("Idade", min_value=0, max_value=120)
            objetivo = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde", "Performance"])
            historico = st.text_area("Histórico Clínico")
            if st.form_submit_button("Salvar Paciente"):
                c.execute("INSERT INTO pacientes (nome, idade, objetivo, historico) VALUES (?,?,?,?)", (nome, idade, objetivo, historico))
                conn.commit()
                st.success("Paciente salvo!")

    with tab2:
        pacientes_df = pd.read_sql_query("SELECT nome, idade, objetivo FROM pacientes", conn)
        st.dataframe(pacientes_df, use_container_width=True)

# --- 3. ANTROPOMETRIA ---
elif menu == "Antropometria":
    st.title("⚖️ Avaliação Antropométrica")
    with st.container():
        col1, col2 = st.columns(2)
        peso = col1.number_input("Peso (kg)", value=70.0)
        altura = col2.number_input("Altura (cm)", value=170)
        
        imc = peso / ((altura/100)**2)
        st.subheader(f"IMC: {imc:.2f}")
        
        if imc < 18.5: st.warning("Abaixo do peso")
        elif imc < 25: st.success("Peso ideal")
        else: st.error("Sobrepeso")

# --- 4. PLANO ALIMENTAR ---
elif menu == "Plano Alimentar":
    st.title("🍽️ Prescrição de Dieta")
    paciente_lista = pd.read_sql_query("SELECT nome FROM pacientes", conn)
    sel_paciente = st.selectbox("Selecione o Paciente", paciente_lista)
    
    st.text_area("Café da Manhã")
    st.text_area("Almoço")
    st.text_area("Jantar")
    st.button("💾 Salvar Plano Alimentar")

# --- 5. SUPLEMENTAÇÃO ---
elif menu == "Suplementação":
    st.title("💊 Prescrição de Suplementos")
    with st.form("suple"):
        nome_s = st.text_input("Suplemento")
        dose = st.text_input("Dose (ex: 5g)")
        if st.form_submit_button("Adicionar"):
            st.write(f"Adicionado: {nome_s} - {dose}")

# --- 6. FINANCEIRO ---
elif menu == "Financeiro":
    st.title("💰 Gestão Financeira")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.form("financeiro_form"):
            valor = st.number_input("Valor Recebido (R$)", min_value=0.0)
            metodo = st.selectbox("Método", ["Pix", "Cartão", "Dinheiro"])
            data = datetime.now().strftime("%d/%m/%Y")
            if st.form_submit_button("Registrar Entrada"):
                c.execute("INSERT INTO financeiro (data, valor, metodo) VALUES (?,?,?)", (data, valor, metodo))
                conn.commit()
                st.success("Lançamento realizado!")
                st.rerun()

    with col2:
        df_fin = pd.read_sql_query("SELECT data, valor, metodo FROM financeiro", conn)
        st.dataframe(df_fin)

# Rodapé lateral
st.sidebar.markdown("---")
st.sidebar.info(f"Logado como: Nutricionista")
