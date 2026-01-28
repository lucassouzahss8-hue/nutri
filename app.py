import streamlit as st
import requests
import sqlite3
import pandas as pd

# CONFIGURAÇÃO
API_KEY = "AIzaSyCBcNud4YjHkv0wLWZneZ1wQ3eBoV7qoJg"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# BANCO DE DADOS (NOVO NOME PARA RESETAR TUDO)
conn = sqlite3.connect('nutri_v10.db', check_same_thread=False)
conn.execute('CREATE TABLE IF NOT EXISTS p (nome TEXT, objetivo TEXT)')

st.title("🍎 NutriSync Pro - Versão Final")

# CADASTRO SIMPLES
with st.form("cad"):
    n = st.text_input("Nome")
    o = st.text_input("Objetivo")
    if st.form_submit_button("Salvar"):
        conn.execute("INSERT INTO p VALUES (?,?)", (n, o))
        st.success("Salvo!")

# IA VIA HTTP (IGNORA ERROS DE BIBLIOTECA)
st.divider()
df = pd.read_sql_query("SELECT * FROM p", conn)
if not df.empty:
    paciente = st.selectbox("Selecionar", df['nome'])
    if st.button("Gerar Dieta"):
        payload = {"contents": [{"parts": [{"text": f"Gere uma dieta para {paciente}"}]}]}
        with st.spinner("IA respondendo via Nuvem..."):
            res = requests.post(URL, json=payload)
            if res.status_code == 200:
                texto = res.json()['candidates'][0]['content']['parts'][0]['text']
                st.markdown(texto)
            else:
                st.error(f"Erro na chave ou servidor: {res.status_code}")
