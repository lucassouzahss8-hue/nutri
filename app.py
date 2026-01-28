import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURAÇÃO DA IA ---
# Substitua pela sua chave real do Google AI Studio
API_KEY = "AIzaSyAO9CysPJuLdaM9Br-lVByTq-6dlgyJXdQ" 
genai.configure(api_key=API_KEY)
# Usando o Gemini 1.5 Flash para geração rápida
model = genai.GenerativeModel('gemini-1.5-flash') 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro", layout="wide", page_icon="🍎")

# --- BANCO DE DADOS (COM CORREÇÃO DE COLUNAS) ---
def get_connection():
    return sqlite3.connect('nutri_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Criando tabela com todas as colunas necessárias
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, idade INTEGER, objetivo TEXT, 
                  clinico TEXT, exames TEXT, data_cadastro TEXT)''')
    
    # RESOLVE O KEYERROR: Verifica se a coluna data_cadastro existe, senão cria
    try:
        c.execute("SELECT data_cadastro FROM pacientes LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE pacientes ADD COLUMN data_cadastro TEXT")
        
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)')
    conn.commit()

init_db()

# --- ESTILO PARA VISIBILIDADE ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #001E3C !important;
        border-radius: 12px; padding: 20px;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #FFFFFF !important; }
    .stTextArea textarea { height: 200px; }
    </style>
    """, unsafe_allow_html=True)

# --- MENU LATERAL (RESOLVE AS ABAS QUE NÃO SE CONVERSAM) ---
st.sidebar.title("🍎 NutriSync Pro")
menu = st.sidebar.radio("Navegação:", ["📊 Dashboard", "📝 Anamnese", "🤖 IA Prescritora", "💰 Financeiro"])
conn = get_connection()

# --- LÓGICA DAS SEÇÕES ---

if menu == "📊 Dashboard":
    st.title("Painel de Controle")
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    total_fin = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Pacientes Ativos", len(df_p))
    c2.metric("Motor IA", "Gemini 1.5 Flash")
    c3.metric("Faturamento", f"R$ {total_fin:,.2f}")
    
    st.divider()
    if not df_p.empty:
        # Exibindo apenas colunas que garantidamente existem
        st.dataframe(df_p[['nome', 'objetivo', 'data_cadastro']], use_container_width=True)
    else:
        st.info("Nenhum paciente cadastrado.")

elif menu == "📝 Anamnese":
    st.title("Prontuário do Paciente")
    with st.form("form_cad", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 0, 120)
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        clinico = st.text_area("Histórico Clínico (Alergias, Doenças)")
        exames = st.text_area("Exames Laboratoriais")
        if st.form_submit_button("Salvar Registro"):
            if nome:
                dt = datetime.now().strftime("%d/%m/%Y")
                conn.execute("INSERT INTO pacientes (nome, idade, objetivo, clinico, exames, data_cadastro) VALUES (?,?,?,?,?,?)",
                             (nome, idade, obj, clinico, exames, dt))
                conn.commit()
                st.success(f"Paciente {nome} salvo!")
            else: st.error("O nome é obrigatório.")

elif menu == "🤖 IA Prescritora":
    st.title("Assistente de Dieta (IA)")
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    if df_p.empty:
        st.warning("Cadastre um paciente primeiro.")
    else:
        paciente_sel = st.selectbox("Selecione o Paciente", df_p['nome'])
        dados = df_p[df_p['nome'] == paciente_sel].iloc[0]
        
        if st.button("🪄 Gerar Dieta com IA"):
            prompt = f"Crie uma dieta para {dados['nome']}, objetivo {dados['objetivo']}, histórico: {dados['clinico']}."
            with st.spinner("IA processando..."):
                try:
                    # Geração de texto pela IA
                    response = model.generate_content(prompt)
                    st.session_state['dieta'] = response.text
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
        
        if 'dieta' in st.session_state:
            plano = st.text_area("Plano Sugerido:", value=st.session_state['dieta'])
            st.download_button("Baixar Plano (TXT)", plano, file_name=f"dieta_{dados['nome']}.txt")

elif menu == "💰 Financeiro":
    st.title("Financeiro")
    valor = st.number_input("Valor da Consulta", 0.0)
    if st.button("Lançar"):
        dt = datetime.now().strftime("%d/%m/%Y")
        conn.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", (dt, valor))
        conn.commit()
        st.rerun()
