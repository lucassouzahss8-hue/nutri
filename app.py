import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURAÇÃO DA API (COLE SUA CHAVE AQUI) ---
API_KEY = "AIzaSyAO9CysPJuLdaM9Br-lVByTq-6dlgyJXdQ"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Versão otimizada para Web

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro + IA Real", layout="wide", page_icon="🍎")

# --- BANCO DE DADOS ---
def get_connection():
    return sqlite3.connect('nutri_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, idade INTEGER, objetivo TEXT, 
                  clinico TEXT, exames TEXT, data_cadastro TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)')
    conn.commit()

init_db()

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #001E3C !important;
        border-radius: 12px; padding: 20px;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #FFFFFF !important; }
    .stTextArea textarea { height: 250px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO IA REAL ---
def gerar_dieta_real(dados):
    prompt = f"""
    Atue como um nutricionista experiente. Elabore um plano alimentar para:
    Paciente: {dados['nome']}
    Idade: {dados['idade']} anos
    Objetivo: {dados['objetivo']}
    Histórico Clínico/Restrições: {dados['clinico']}
    Resultados de Exames: {dados['exames']}
    
    Estruture em: Café, Lanche da Manhã, Almoço, Lanche da Tarde e Jantar.
    Seja técnico e use alimentos acessíveis.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao conectar com a IA: {e}"

# --- NAVEGAÇÃO ---
st.sidebar.title("🍎 NutriSync Pro")
aba = st.sidebar.radio("Navegar:", ["📊 Dashboard", "📝 Prontuário", "🤖 Prescrição IA", "💰 Financeiro"])
conn = get_connection()

if aba == "📊 Dashboard":
    st.title("Painel de Controle")
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    total_fin = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", len(df_p))
    col2.metric("Motor IA", "Gemini 3 Flash") # Identificação do modelo
    col3.metric("Faturamento", f"R$ {total_fin:,.2f}")
    
    st.divider()
    if not df_p.empty:
        st.dataframe(df_p[['nome', 'objetivo', 'data_cadastro']], use_container_width=True)

elif aba == "📝 Prontuário":
    st.title("Prontuário Eletrônico")
    with st.form("cad"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome")
        idade = c2.number_input("Idade", 0, 120)
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        clinico = st.text_area("Histórico Clínico")
        exames = st.text_area("Exames")
        if st.form_submit_button("Salvar"):
            dt = datetime.now().strftime("%d/%m/%Y")
            conn.execute("INSERT INTO pacientes (nome, idade, objetivo, clinico, exames, data_cadastro) VALUES (?,?,?,?,?,?)",
                         (nome, idade, obj, clinico, exames, dt))
            conn.commit()
            st.success("Salvo!")

elif aba == "🤖 Prescrição IA":
    st.title("Assistente Nutricional Inteligente")
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    
    if df_p.empty:
        st.warning("Cadastre um paciente primeiro.")
    else:
        paciente_sel = st.selectbox("Selecione o Paciente", df_p['nome'])
        dados = df_p[df_p['nome'] == paciente_sel].iloc[0]
        
        if st.button("🪄 Gerar Dieta Personalizada com IA"):
            with st.spinner('O Gemini está analisando os dados clínicos...'):
                st.session_state['dieta_gerada'] = gerar_dieta_real(dados)
        
        if 'dieta_gerada' in st.session_state:
            plano = st.text_area("Plano Alimentar Gerado:", value=st.session_state['dieta_gerada'])
            st.download_button("📥 Baixar Plano", plano, file_name=f"dieta_{dados['nome']}.txt")

elif aba == "💰 Financeiro":
    st.title("Financeiro")
    valor = st.number_input("Valor (R$)", 0.0)
    if st.button("Lançar"):
        dt = datetime.now().strftime("%d/%m/%Y")
        conn.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", (dt, valor))
        conn.commit()
        st.rerun()
