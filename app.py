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

# --- ESTILIZAÇÃO CSS (CORREÇÃO DE CONTRASTE E QUADROS) ---
st.markdown("""
    <style>
    /* Fundo da página */
    .main { background-color: #f0f2f6; }

    /* Quadros de Métrica (Azul Escuro) */
    div[data-testid="metric-container"] {
        background-color: #001E3C !important;
        border: 1px solid #003366;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
    }

    /* Texto das Métricas (Branco Puro para leitura) */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
    }

    /* Estilização da Mensagem "Sem Informações" */
    .empty-state {
        text-align: center;
        padding: 40px;
        background-color: #ffffff;
        border-radius: 20px;
        border: 2px dashed #bdc3c7;
        color: #7f8c8d;
        margin-top: 20px;
    }

    /* Botões */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #001E3C;
        color: white;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# Função para exibir estado vazio estilizado
def show_empty_state(mensagem="Não há informações no momento"):
    st.markdown(f"""
        <div class="empty-state">
            <h1 style="font-size: 50px;">📂</h1>
            <h3>{mensagem}</h3>
            <p>Os dados aparecerão aqui assim que forem registrados no sistema.</p>
        </div>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("🍎 NutriSync Pro")
menu = st.sidebar.radio("Navegação", [
    "Dashboard", "Prontuário", "Antropometria", "Plano Alimentar", "Financeiro"
])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Painel Geral")
    
    # Métricas
    qtd_p = pd.read_sql_query("SELECT COUNT(*) as total FROM pacientes", conn).iloc[0]['total']
    fin_p = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", qtd_p)
    col2.metric("Consultas Hoje", "0")
    col3.metric("Faturamento", f"R$ {fin_p:,.2f}")
    
    st.divider()
    
    st.subheader("📅 Agenda do Dia")
    agenda_df = pd.read_sql_query("SELECT horario, paciente, status FROM agenda", conn)
    
    if agenda_df.empty:
        show_empty_state("Sua agenda está livre hoje")
    else:
        st.table(agenda_df)

# --- 2. PRONTUÁRIO ---
elif menu == "Prontuário":
    st.title("📝 Prontuário")
    tab1, tab2 = st.tabs(["Cadastrar Novo", "Lista de Pacientes"])
    
    with tab1:
        with st.form("add_p"):
            nome = st.text_input("Nome")
            if st.form_submit_button("Salvar"):
                c.execute("INSERT INTO pacientes (nome) VALUES (?)", (nome,))
                conn.commit()
                st.success("Salvo!")
                st.rerun()
                
    with tab2:
        pacientes_df = pd.read_sql_query("SELECT nome FROM pacientes", conn)
        if pacientes_df.empty:
            show_empty_state("Nenhum paciente cadastrado")
        else:
            st.dataframe(pacientes_df, use_container_width=True)

# --- 3. ANTROPOMETRIA ---
elif menu == "Antropometria":
    st.title("⚖️ Avaliação")
    # Se não houver pacientes, mostra estado vazio
    p_check = pd.read_sql_query("SELECT nome FROM pacientes", conn)
    if p_check.empty:
        show_empty_state("Cadastre um paciente para iniciar a avaliação")
    else:
        st.selectbox("Selecione o Paciente", p_check['nome'])
        st.number_input("Peso (kg)")
        st.number_input("Altura (cm)")
        st.button("Calcular")

# --- 4. PLANO ALIMENTAR ---
elif menu == "Plano Alimentar":
    st.title("🍽️ Plano Alimentar")
    show_empty_state("Nenhum plano alimentar gerado recentemente")

# --- 5. FINANCEIRO ---
elif menu == "Financeiro":
    st.title("💰 Gestão Financeira")
    col1, col2 = st.columns([1, 2])
    with col1:
        val = st.number_input("Valor")
        if st.button("Lançar"):
            dt = datetime.now().strftime("%d/%m/%Y")
            c.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", (dt, val))
            conn.commit()
            st.rerun()
    with col2:
        fin_df = pd.read_sql_query("SELECT * FROM financeiro", conn)
        if fin_df.empty:
            show_empty_state("Sem histórico financeiro")
        else:
            st.dataframe(fin_df)
