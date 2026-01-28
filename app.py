import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURAÇÃO DA IA ---
# Certifique-se de colocar sua chave aqui
API_KEY = "AIzaSyAO9CysPJuLdaM9Br-lVByTq-6dlgyJXdQ" 
genai.configure(api_key=API_KEY)
# Utilizando o modelo Gemini 1.5 Flash para máxima eficiência
model = genai.GenerativeModel('gemini-1.5-flash') 

# --- FUNÇÃO DE BANCO DE DATA (REBOOT AUTOMÁTICO) ---
def conectar_banco():
    conn = sqlite3.connect('nutri_sync_v2.db', check_same_thread=False)
    c = conn.cursor()
    # Criamos uma tabela nova com nome diferente para evitar conflitos antigos
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes_v2 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, 
                  objetivo TEXT, 
                  clinico TEXT, 
                  data_cadastro TEXT)''')
    conn.commit()
    return conn

conn = conectar_banco()

# --- INTERFACE ---
st.set_page_config(page_title="NutriSync Pro", layout="wide")

# CSS para forçar a cor branca nos textos e resolver o erro de visão
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: white !important; }
    .stDataFrame { background-color: #1e1e1e; }
    </style>
    """, unsafe_allow_html=True)

aba = st.sidebar.radio("Navegação", ["Início", "Novo Paciente", "IA Nutri"])

if aba == "Início":
    st.title("📊 Painel de Pacientes")
    # Lógica de leitura segura
    try:
        df = pd.read_sql_query("SELECT * FROM pacientes_v2", conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum paciente cadastrado ainda.")
    except Exception as e:
        st.error(f"Erro ao ler dados: {e}")

elif aba == "Novo Paciente":
    st.title("📝 Cadastro")
    with st.form("meu_form"):
        nome = st.text_input("Nome")
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Ganho de Massa"])
        hist = st.text_area("Histórico Clínico")
        if st.form_submit_button("Salvar"):
            data_hoje = datetime.now().strftime("%d/%m/%Y")
            conn.execute("INSERT INTO pacientes_v2 (nome, objetivo, clinico, data_cadastro) VALUES (?,?,?,?)",
                         (nome, obj, hist, data_hoje))
            conn.commit()
            st.success("Paciente cadastrado!")

elif aba == "IA Nutri":
    st.title("🤖 Prescrição Inteligente")
    try:
        df = pd.read_sql_query("SELECT * FROM pacientes_v2", conn)
        if df.empty:
            st.warning("Cadastre alguém primeiro.")
        else:
            p_escolhido = st.selectbox("Selecione o Paciente", df['nome'])
            dados_p = df[df['nome'] == p_escolhido].iloc[0]
            
            if st.button("🪄 Gerar Dieta com Gemini"):
                with st.spinner("Analisando perfil..."):
                    # Prompt para geração de conteúdo
                    prompt = f"Gere uma dieta para {p_escolhido}, objetivo: {dados_p['objetivo']}, clínico: {dados_p['clinico']}."
                    res = model.generate_content(prompt)
                    st.markdown(res.text)
    except Exception as e:
        st.error(f"Erro na IA: {e}")
