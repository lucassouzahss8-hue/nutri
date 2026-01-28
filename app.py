import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="NutriSync Pro", layout="wide")

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
    /* Texto Branco nas métricas */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
    }
    /* Estilo do Card Vazio */
    .empty-card {
        text-align: center;
        padding: 40px;
        border: 2px dashed #444;
        border-radius: 15px;
        color: #888;
        background-color: #161b22;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÃO ÚNICA DE BANCO DE DADOS ---
# O segredo para as abas conversarem é usar a mesma conexão
def get_connection():
    return sqlite3.connect('nutri_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS pacientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, objetivo TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)')
    conn.commit()

init_db()

# --- 3. MENU LATERAL (SUBSTITUI AS ABAS SEPARADAS) ---
st.sidebar.title("🍎 NutriSync Pro")
aba = st.sidebar.radio("Navegar para:", ["📊 Dashboard", "📝 Anamnese", "⚖️ Antropometria", "💰 Financeiro"])

# --- 4. LÓGICA INTEGRADA ---

if aba == "📊 Dashboard":
    st.title("Painel Geral")
    conn = get_connection()
    
    # Busca dados salvos para as métricas
    pacientes_df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    fin_df = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn)
    faturamento = fin_df['total'].iloc[0] or 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", len(pacientes_df))
    col2.metric("Consultas Hoje", "0")
    col3.metric("Faturamento", f"R$ {faturamento:,.2f}")
    
    st.divider()
    st.subheader("📅 Pacientes Recentes")
    if pacientes_df.empty:
        st.markdown('<div class="empty-card"><h3>Não há informações no momento</h3><p>Vá em Anamnese para cadastrar.</p></div>', unsafe_allow_html=True)
    else:
        st.dataframe(pacientes_df[['nome', 'objetivo']], use_container_width=True)

elif aba == "📝 Anamnese":
    st.title("Cadastro de Pacientes")
    conn = get_connection()
    
    with st.form("cad_paciente", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        if st.form_submit_button("Salvar Paciente"):
            if nome:
                conn.execute("INSERT INTO pacientes (nome, objetivo) VALUES (?,?)", (nome, obj))
                conn.commit()
                st.success(f"Paciente {nome} salvo! Agora ele aparecerá em todas as abas.")
            else:
                st.error("Digite o nome do paciente.")

elif aba == "⚖️ Antropometria":
    st.title("Avaliação Física")
    conn = get_connection()
    # Aqui a aba "conversa" com a Anamnese buscando os nomes salvos
    pacientes = pd.read_sql_query("SELECT nome FROM pacientes", conn)['nome'].tolist()
    
    if not pacientes:
        st.markdown('<div class="empty-card"><h3>Não há informações no momento</h3><p>Cadastre um paciente primeiro.</p></div>', unsafe_allow_html=True)
    else:
        st.selectbox("Selecionar Paciente Salvo", pacientes)
        st.number_input("Peso (kg)")
        st.number_input("Altura (cm)")
        st.button("Salvar Avaliação")

elif aba == "💰 Financeiro":
    st.title("Financeiro")
    conn = get_connection()
    
    col1, col2 = st.columns(2)
    with col1:
        valor = st.number_input("Valor Recebido", min_value=0.0)
        if st.button("Registrar"):
            data_atual = datetime.now().strftime("%d/%m/%Y")
            conn.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", (data_atual, valor))
            conn.commit()
            st.success("Valor registrado!")
            st.rerun()
    
    with col2:
        historico = pd.read_sql_query("SELECT data, valor FROM financeiro", conn)
        if historico.empty:
            st.markdown('<div class="empty-card"><h3>Não há informações no momento</h3></div>', unsafe_allow_html=True)
        else:
            st.dataframe(historico, use_container_width=True)
