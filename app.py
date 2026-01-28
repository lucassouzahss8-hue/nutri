import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURAÇÃO DA IA ---
API_KEY = "AIzaSyCBcNud4YjHkv0wLWZneZ1wQ3eBoV7qoJg" 
genai.configure(api_key=API_KEY)

# --- INICIALIZAÇÃO DO ESTADO DE NAVEGAÇÃO ---
# Isso impede que o app volte para o início ao clicar em botões
if 'pagina' not in st.session_state:
    st.session_state.pagina = "📊 Dashboard"

# --- CONFIGURAÇÃO DO BANCO DE DADOS (VERSÃO LIMPA) ---
def init_db():
    conn = sqlite3.connect('nutri_v10_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, objetivo TEXT, clinico TEXT, data_cadastro TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- FUNÇÃO PARA NAVEGAR ---
def ir_para(nome_pagina):
    st.session_state.pagina = nome_pagina

# --- SIDEBAR PERSISTENTE ---
st.sidebar.title("🍎 NutriSync Pro")
st.sidebar.write(f"Página atual: **{st.session_state.pagina}**")

if st.sidebar.button("📊 Dashboard"):
    ir_para("📊 Dashboard")
if st.sidebar.button("📝 Novo Paciente"):
    ir_para("📝 Novo Paciente")
if st.sidebar.button("🤖 IA Prescritora"):
    ir_para("🤖 IA Prescritora")

# --- LÓGICA DE TELAS ---

# 1. DASHBOARD
if st.session_state.pagina == "📊 Dashboard":
    st.title("Painel de Pacientes")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    if not df.empty:
        st.dataframe(df[['nome', 'objetivo', 'data_cadastro']], use_container_width=True)
    else:
        st.info("Nenhum paciente cadastrado.")

# 2. CADASTRO
elif st.session_state.pagina == "📝 Novo Paciente":
    st.title("Cadastro de Prontuário")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        clin = st.text_area("Histórico Clínico")
        
        if st.form_submit_button("Salvar Paciente"):
            if nome:
                dt = datetime.now().strftime("%d/%m/%Y")
                conn.execute("INSERT INTO pacientes (nome, objetivo, clinico, data_cadastro) VALUES (?,?,?,?)",
                             (nome, obj, clin, dt))
                conn.commit()
                st.success("Paciente salvo com sucesso!")
            else:
                st.error("O nome é obrigatório.")

# 3. IA PRESCRITORA (COM PROTEÇÃO CONTRA RESET E ERRO 404)
elif st.session_state.pagina == "🤖 IA Prescritora":
    st.title("Assistente Nutricional Gemini")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    
    if df.empty:
        st.warning("Cadastre um paciente primeiro.")
    else:
        paciente_sel = st.selectbox("Escolha o Paciente", df['nome'])
        dados = df[df['nome'] == paciente_sel].iloc[0]
        
        # Botão que não reseta a página
        if st.button("🪄 Gerar Dieta"):
            with st.spinner("IA Processando..."):
                # Tenta o modelo Flash 1.5
                # Se falhar com 404 (como nas fotos), tenta o Gemini Pro
                modelos = ['gemini-1.5-flash', 'gemini-pro']
                sucesso = False
                
                for m in modelos:
                    try:
                        model = genai.GenerativeModel(m)
                        prompt = f"Gere uma dieta para {paciente_sel}, foco em {dados['objetivo']}, clínico: {dados['clinico']}."
                        response = model.generate_content(prompt)
                        st.markdown(f"### Plano Sugerido via {m}")
                        st.write(response.text)
                        sucesso = True
                        break
                    except Exception as e:
                        if "404" in str(e):
                            continue # Tenta o próximo modelo
                        else:
                            st.error(f"Erro: {e}")
                            break
                
                if not sucesso:
                    st.error("Não foi possível conectar à IA. Verifique sua chave API.")
