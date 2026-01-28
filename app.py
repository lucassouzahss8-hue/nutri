import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURAÇÃO DA IA ---
API_KEY = "AIzaSyAO9CysPJuLdaM9Br-lVByTq-6dlgyJXdQ" 
genai.configure(api_key=API_KEY)
# Chamada estável para o modelo Gemini 1.5 Flash
model = genai.GenerativeModel('gemini-1.5-flash') 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro", layout="wide")

# --- BANCO DE DADOS (COM REPARO AUTOMÁTICO) ---
def init_db():
    conn = sqlite3.connect('nutri_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)''')
    
    # Adiciona cada coluna individualmente se não existir (Evita o KeyError)
    colunas = [
        ('idade', 'INTEGER'),
        ('objetivo', 'TEXT'),
        ('clinico', 'TEXT'),
        ('exames', 'TEXT'),
        ('data_cadastro', 'TEXT')
    ]
    for col, tipo in colunas:
        try:
            c.execute(f'ALTER TABLE pacientes ADD COLUMN {col} {tipo}')
        except:
            pass # Se a coluna já existir, ele apenas pula
    conn.commit()
    return conn

conn = init_db()

# --- INTERFACE ---
st.sidebar.title("🍎 NutriSync")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastrar", "IA Prescritora"])

if menu == "Dashboard":
    st.title("Pacientes")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    
    if not df.empty:
        # Resolve o KeyError: Filtramos apenas as colunas que REALMENTE existem no banco agora
        colunas_disponiveis = [c for c in ['nome', 'idade', 'objetivo', 'data_cadastro'] if c in df.columns]
        st.dataframe(df[colunas_disponiveis], use_container_width=True)
    else:
        st.info("Nenhum dado encontrado.")

elif menu == "Cadastrar":
    st.title("Novo Registro")
    with st.form("cad"):
        nome = st.text_input("Nome")
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia"])
        clin = st.text_area("Histórico")
        if st.form_submit_button("Salvar"):
            dt = datetime.now().strftime("%d/%m/%Y")
            conn.execute("INSERT INTO pacientes (nome, objetivo, clinico, data_cadastro) VALUES (?,?,?,?)", 
                         (nome, obj, clin, dt))
            conn.commit()
            st.success("Salvo! Clique em Dashboard para ver.")

elif menu == "IA Prescritora":
    st.title("Assistente Gemini")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    if not df.empty:
        paciente = st.selectbox("Paciente", df['nome'])
        if st.button("Gerar Dieta"):
            p_dados = df[df['nome'] == paciente].iloc[0]
            # Prompt para o modelo generativo
            prompt = f"Gere uma dieta para {paciente} com foco em {p_dados.get('objetivo', 'Saúde')}."
            try:
                response = model.generate_content(prompt)
                st.write(response.text)
            except Exception as e:
                st.error(f"Erro na IA: {e}")
