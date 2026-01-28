import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro", layout="wide", page_icon="🍎")

# --- 2. BANCO DE DADOS INTEGRADO ---
def get_connection():
    return sqlite3.connect('nutri_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Criamos a tabela com TODAS as colunas para evitar o KeyError das suas imagens
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, idade INTEGER, objetivo TEXT, 
                  historico_clinico TEXT, exames_lab TEXT, 
                  data_cadastro TEXT)''')
    
    # Verificação de segurança: Se a coluna data_cadastro não existir (banco antigo), nós adicionamos
    try:
        c.execute('SELECT data_cadastro FROM pacientes LIMIT 1')
    except:
        c.execute('ALTER TABLE pacientes ADD COLUMN data_cadastro TEXT')
        
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)')
    conn.commit()

init_db()

# --- 3. ESTILIZAÇÃO CSS (CORRIGE O BRANCO NO BRANCO) ---
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

    /* FORÇAR TEXTO BRANCO (Resolve o problema da sua 1ª imagem) */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    .status-card {
        text-align: center; padding: 40px; border: 2px dashed #444;
        border-radius: 15px; color: #888; background-color: #161b22;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. NAVEGAÇÃO LATERAL INTEGRADA ---
st.sidebar.title("🍎 NutriSync Pro")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "📝 Prontuário & Exames", "⚖️ Dieta & Cálculos", "💰 Financeiro"])

conn = get_connection()

# --- 5. LÓGICA DAS SEÇÕES ---

if aba == "📊 Dashboard":
    st.title("Painel Geral")
    
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    total_fin = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    
    col1, col2, col3 = st.columns(3)
    # Agora os números aparecerão em branco no fundo azul!
    col1.metric("Pacientes Ativos", len(df_p))
    col2.metric("Consultas Hoje", "0")
    col3.metric("Faturamento", f"R$ {total_fin:,.2f}")
    
    st.divider()
    st.subheader("📋 Pacientes Recentes")
    
    if df_p.empty:
        st.markdown('<div class="status-card"><h3>Sem pacientes cadastrados</h3></div>', unsafe_allow_html=True)
    else:
        # Resolve o KeyError garantindo que as colunas existem
        st.dataframe(df_p[['nome', 'objetivo', 'data_cadastro']], use_container_width=True)

elif aba == "📝 Prontuário & Exames":
    st.title("Prontuário e Dados Clínicos")
    with st.form("novo_paciente", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 0, 120)
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        clinico = st.text_area("Histórico Clínico")
        exames = st.text_area("Exames Laboratoriais")
        
        if st.form_submit_button("Salvar Registro"):
            if nome:
                dt = datetime.now().strftime("%d/%m/%Y")
                conn.execute('''INSERT INTO pacientes (nome, idade, objetivo, historico_clinico, exames_lab, data_cadastro) 
                                VALUES (?,?,?,?,?,?)''', (nome, idade, obj, clinico, exames, dt))
                conn.commit()
                st.success("Paciente salvo! Agora ele aparecerá no Dashboard e na Dieta.")
                st.rerun()

elif aba == "⚖️ Dieta & Cálculos":
    st.title("Cálculos e Prescrição")
    df_p = pd.read_sql_query("SELECT id, nome FROM pacientes", conn)
    
    if df_p.empty:
        st.warning("Cadastre um paciente primeiro para realizar cálculos.")
    else:
        paciente = st.selectbox("Selecione o Paciente", df_p['nome'])
        st.number_input("Peso (kg)")
        st.number_input("Altura (cm)")
        st.text_area("Prescrição Dietética")
        st.button("Salvar Dieta")

elif aba == "💰 Financeiro":
    st.title("Gestão Financeira")
    valor = st.number_input("Valor da Consulta", min_value=0.0)
    if st.button("Registrar"):
        dt = datetime.now().strftime("%d/%m/%Y")
        conn.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", (dt, valor))
        conn.commit()
        st.rerun()
