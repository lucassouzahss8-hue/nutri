import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro", layout="wide", page_icon="🍎")

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('nutri_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, objetivo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS agenda 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, horario TEXT, paciente TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS financeiro 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- ESTILIZAÇÃO CSS (CORREÇÃO DE CORES) ---
st.markdown("""
    <style>
    /* Fundo Escuro para combinar com seu print */
    .main { background-color: #0e1117; }
    
    /* Quadros de Métrica em Azul Escuro */
    div[data-testid="metric-container"] {
        background-color: #001E3C !important;
        border: 1px solid #003366;
        padding: 20px;
        border-radius: 12px;
    }

    /* FORÇAR TEXTO BRANCO (Resolve o erro da sua imagem) */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
    }

    /* Estilo do Card Vazio */
    .empty-state {
        text-align: center;
        padding: 40px;
        border: 2px dashed #444;
        border-radius: 15px;
        color: #888;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO LATERAL (Substitui a pasta pages) ---
st.sidebar.title("🍎 NutriSync Pro")
aba = st.sidebar.radio("Navegar para:", [
    "📊 Dashboard", 
    "📝 Anamnese", 
    "⚖️ Antropometria", 
    "🍽️ Plano Alimentar", 
    "💰 Financeiro"
])

# --- LÓGICA DAS ABAS ---

if aba == "📊 Dashboard":
    st.title("Painel Geral")
    
    # Dados para as métricas
    qtd_p = pd.read_sql_query("SELECT COUNT(*) as total FROM pacientes", conn).iloc[0]['total']
    faturamento = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", qtd_p)
    col2.metric("Consultas Hoje", "0")
    col3.metric("Receita Total", f"R$ {faturamento:,.2f}")
    
    st.divider()
    
    st.subheader("📅 Agenda de Hoje")
    agenda_df = pd.read_sql_query("SELECT horario, paciente FROM agenda", conn)
    
    if agenda_df.empty:
        st.markdown('<div class="empty-state"><h3>Não há informações no momento</h3><p>Adicione um paciente ou agendamento para começar.</p></div>', unsafe_allow_html=True)
    else:
        st.table(agenda_df)

elif aba == "📝 Anamnese":
    st.title("Cadastro e Prontuário")
    with st.form("cadastro"):
        nome = st.text_input("Nome do Paciente")
        objetivo = st.selectbox("Objetivo", ["Emagrecimento", "Ganho de Massa", "Saúde"])
        if st.form_submit_button("Salvar Paciente"):
            c.execute("INSERT INTO pacientes (nome, objetivo) VALUES (?,?)", (nome, objetivo))
            conn.commit()
            st.success("Paciente cadastrado!")
            st.rerun()

    st.subheader("Pacientes Cadastrados")
    p_df = pd.read_sql_query("SELECT nome, objetivo FROM pacientes", conn)
    if p_df.empty:
        st.info("Nenhum paciente cadastrado.")
    else:
        st.dataframe(p_df, use_container_width=True)

elif aba == "⚖️ Antropometria":
    st.title("Avaliação Física")
    # Busca pacientes para o seletor
    pacientes = pd.read_sql_query("SELECT nome FROM pacientes", conn)['nome'].tolist()
    
    if not pacientes:
        st.warning("Cadastre um paciente na aba Anamnese primeiro.")
    else:
        st.selectbox("Selecionar Paciente", pacientes)
        col1, col2 = st.columns(2)
        col1.number_input("Peso (kg)")
        col2.number_input("Altura (cm)")
        st.button("Salvar Avaliação")

elif aba == "🍽️ Plano Alimentar":
    st.title("Prescrição de Dieta")
    st.markdown('<div class="empty-state"><h3>Não há planos criados</h3><p>Selecione um paciente para iniciar o cardápio.</p></div>', unsafe_allow_html=True)

elif aba == "💰 Financeiro":
    st.title("Gestão de Receitas")
    col1, col2 = st.columns(2)
    with col1:
        valor = st.number_input("Valor da Consulta", min_value=0.0)
        if st.button("Registrar Recebimento"):
            data = datetime.now().strftime("%d/%m/%Y")
            c.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", (data, valor))
            conn.commit()
            st.rerun()
    with col2:
        fin_df = pd.read_sql_query("SELECT data, valor FROM financeiro", conn)
        if fin_df.empty:
            st.info("Sem histórico financeiro.")
        else:
            st.dataframe(fin_df)
