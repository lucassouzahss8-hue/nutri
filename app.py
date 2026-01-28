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
    c.execute('CREATE TABLE IF NOT EXISTS pacientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, objetivo TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS agenda (id INTEGER PRIMARY KEY AUTOINCREMENT, horario TEXT, paciente TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)')
    conn.commit()
    return conn

conn = init_db()

# --- ESTILIZAÇÃO CSS (CORREÇÃO DE CORES E QUADROS) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* Quadros de Métrica em Azul Escuro */
    div[data-testid="metric-container"] {
        background-color: #001E3C !important;
        border: 1px solid #003366;
        padding: 20px;
        border-radius: 12px;
    }

    /* FORÇAR TEXTO BRANCO PARA FICAR VISÍVEL */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
    }

    /* Card de Estado Vazio */
    .empty-card {
        text-align: center;
        padding: 50px;
        border: 2px dashed #444;
        border-radius: 15px;
        color: #888;
        background-color: #161b22;
    }
    </style>
    """, unsafe_allow_html=True)

# --- MENU LATERAL (Isso substitui as abas que estavam vazias) ---
st.sidebar.title("🍎 NutriSync Pro")
aba = st.sidebar.radio("Selecione uma seção:", [
    "📊 Dashboard", "📝 Anamnese", "⚖️ Antropometria", "🍽️ Plano Alimentar", "💰 Financeiro"
])

# --- LÓGICA DAS SEÇÕES ---

if aba == "📊 Dashboard":
    st.title("Painel Geral")
    
    # Busca dados reais
    qtd_p = pd.read_sql_query("SELECT COUNT(*) as total FROM pacientes", conn).iloc[0]['total']
    faturamento = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", qtd_p)
    col2.metric("Consultas Hoje", "0")
    col3.metric("Faturamento", f"R$ {faturamento:,.2f}")
    
    st.divider()
    
    st.subheader("📅 Agenda do Dia")
    st.markdown('<div class="empty-card"><h3>Não há informações no momento</h3><p>Vá em Anamnese para cadastrar seu primeiro paciente.</p></div>', unsafe_allow_html=True)

elif aba == "📝 Anamnese":
    st.title("Cadastro de Pacientes")
    with st.form("cad"):
        nome = st.text_input("Nome do Paciente")
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT INTO pacientes (nome, objetivo) VALUES (?,?)", (nome, obj))
            conn.commit()
            st.success("Paciente cadastrado!")
            st.rerun()

elif aba == "⚖️ Antropometria":
    st.title("Avaliação Física")
    st.markdown('<div class="empty-card"><h3>Não há informações no momento</h3><p>Selecione um paciente cadastrado para iniciar.</p></div>', unsafe_allow_html=True)

elif aba == "🍽️ Plano Alimentar":
    st.title("Plano Alimentar")
    st.markdown('<div class="empty-card"><h3>Não há informações no momento</h3><p>Crie uma dieta personalizada para seu paciente aqui.</p></div>', unsafe_allow_html=True)

elif aba == "💰 Financeiro":
    st.title("Financeiro")
    st.markdown('<div class="empty-card"><h3>Não há informações no momento</h3><p>Registre pagamentos e consultas aqui.</p></div>', unsafe_allow_html=True)
