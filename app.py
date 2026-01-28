import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro", layout="wide", page_icon="🍎")

# --- 2. BANCO DE DADOS CENTRALIZADO ---
def get_connection():
    # Centralizar a conexão garante que os dados salvos em uma aba apareçam na outra
    return sqlite3.connect('nutri_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabela de Pacientes: Inclui 'data_cadastro' para evitar o KeyError
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, idade INTEGER, objetivo TEXT, 
                  historico_clinico TEXT, exames_lab TEXT, 
                  data_cadastro TEXT)''')
    # Tabela de Prescrições e Cálculos
    c.execute('''CREATE TABLE IF NOT EXISTS prescricoes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  paciente_id INTEGER, peso REAL, altura REAL, 
                  kcal_total REAL, plano_alimentar TEXT, data_prescricao TEXT)''')
    # Tabela Financeira
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)')
    conn.commit()

init_db()

# --- 3. ESTILIZAÇÃO CSS (QUADROS AZUIS E TEXTO BRANCO) ---
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
    /* Forçar texto branco para resolver invisibilidade */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
    }
    .empty-card {
        text-align: center; padding: 40px; border: 2px dashed #444;
        border-radius: 15px; color: #888; background-color: #161b22;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. NAVEGAÇÃO LATERAL (Substitui a pasta pages) ---
st.sidebar.title("🍎 NutriSync Pro")
aba = st.sidebar.radio("Navegar para:", [
    "📊 Dashboard", 
    "📝 Prontuário & Exames", 
    "🍽️ Dieta & Cálculos", 
    "💰 Financeiro"
])

conn = get_connection()

# --- 5. LÓGICA DAS ABAS ---

if aba == "📊 Dashboard":
    st.title("Painel Geral")
    
    # Busca dados reais para as métricas
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    total_fin = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", len(df_p))
    col2.metric("Consultas Hoje", "0")
    col3.metric("Faturamento", f"R$ {total_fin:,.2f}")
    
    st.divider()
    st.subheader("📋 Pacientes Recentes")
    if df_p.empty:
        st.markdown('<div class="empty-card"><h3>Não há informações no momento</h3><p>Cadastre pacientes na aba Prontuário.</p></div>', unsafe_allow_html=True)
    else:
        # Exibe apenas as colunas existentes para evitar erro
        st.dataframe(df_p[['nome', 'objetivo', 'data_cadastro']], use_container_width=True)

elif aba == "📝 Prontuário & Exames":
    st.title("Prontuário e Dados Clínicos")
    with st.form("cad_paciente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome Completo")
        idade = col2.number_input("Idade", 0, 120)
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        
        st.subheader("Anamnese e Laboratório")
        clinico = st.text_area("Histórico Clínico e Queixas")
        exames = st.text_area("Exames (Colesterol, Glicemia, etc.)")
        
        if st.form_submit_button("Salvar Registro"):
            if nome:
                dt = datetime.now().strftime("%d/%m/%Y")
                conn.execute('''INSERT INTO pacientes (nome, idade, objetivo, historico_clinico, exames_lab, data_cadastro) 
                                VALUES (?,?,?,?,?,?)''', (nome, idade, obj, clinico, exames, dt))
                conn.commit()
                st.success(f"Paciente {nome} cadastrado com sucesso!")
                st.rerun()

elif aba == "🍽️ Dieta & Cálculos":
    st.title("Prescrição Dietética")
    df_p = pd.read_sql_query("SELECT id, nome FROM pacientes", conn)
    
    if df_p.empty:
        st.warning("Cadastre um paciente primeiro na aba de Prontuário.")
    else:
        paciente_nome = st.selectbox("Selecione o Paciente", df_p['nome'])
        p_id = df_p[df_p['nome'] == paciente_nome]['id'].values[0]
        
        c1, c2 = st.columns(2)
        peso = c1.number_input("Peso (kg)", 0.0)
        altura = c2.number_input("Altura (cm)", 0)
        
        if peso > 0 and altura > 0:
            imc = peso / ((altura/100)**2)
            st.info(f"**IMC:** {imc:.2f}")
            
        plano = st.text_area("Plano Alimentar Detalhado")
        if st.button("Salvar Plano"):
            dt_p = datetime.now().strftime("%d/%m/%Y")
            conn.execute('''INSERT INTO prescricoes (paciente_id, peso, altura, plano_alimentar, data_prescricao) 
                            VALUES (?,?,?,?,?)''', (p_id, peso, altura, plano, dt_p))
            conn.commit()
            st.success("Plano Alimentar salvo e vinculado ao paciente!")

elif aba == "💰 Financeiro":
    st.title("Gestão Financeira")
    valor = st.number_input("Valor da Consulta (R$)", min_value=0.0)
    if st.button("Registrar Receita"):
        dt_f = datetime.now().strftime("%d/%m/%Y")
        conn.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", (dt_f, valor))
        conn.commit()
        st.rerun()
