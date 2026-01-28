import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai

# --- CONFIGURAÇÃO DA IA (COMPATIBILIDADE MÁXIMA) ---
API_KEY = "AIzaSyAO9CysPJuLdaM9Br-lVByTq-6dlgyJXdQ"
genai.configure(api_key=API_KEY)

# --- CONTROLE DE NAVEGAÇÃO (Evita voltar para o início) ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Dashboard"

def mudar_pagina(nome):
    st.session_state.pagina = nome

# --- BANCO DE DADOS (Criação Segura) ---
def init_db():
    # Usamos um novo nome de arquivo para forçar a criação correta das colunas
    conn = sqlite3.connect('nutri_vfinal.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     nome TEXT, objetivo TEXT, clinico TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- SIDEBAR ---
st.sidebar.title("🍎 NutriSync")
if st.sidebar.button("📊 Dashboard"): mudar_pagina("Dashboard")
if st.sidebar.button("📝 Novo Paciente"): mudar_pagina("Cadastro")
if st.sidebar.button("🤖 Gerar Dieta"): mudar_pagina("IA")

# --- TELAS ---
if st.session_state.pagina == "Dashboard":
    st.title("Painel")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    st.dataframe(df, use_container_width=True)

elif st.session_state.pagina == "Cadastro":
    st.title("Cadastro")
    with st.form("cad"):
        nome = st.text_input("Nome")
        obj = st.text_input("Objetivo")
        cli = st.text_area("Histórico Clínico")
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT INTO pacientes (nome, objetivo, clinico) VALUES (?,?,?)", (nome, obj, cli))
            conn.commit()
            st.success("Salvo!")

elif st.session_state.pagina == "IA":
    st.title("Assistente IA")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    if not df.empty:
        sel = st.selectbox("Paciente", df['nome'])
        p = df[df['nome'] == sel].iloc[0]
        if st.button("🪄 Gerar Dieta"):
            try:
                # Usamos gemini-pro para evitar o erro 404 da versão 0.8.6
                model = genai.GenerativeModel('gemini-pro')
                res = model.generate_content(f"Dieta para {sel}, objetivo {p['objetivo']}")
                st.write(res.text)
            except Exception as e:
                st.error(f"Erro: {e}")
