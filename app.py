import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURAÇÃO DA IA ---
API_KEY = "AIzaSyAO9CysPJuLdaM9Br-lVByTq-6dlgyJXdQ" 
genai.configure(api_key=API_KEY)
# Chamada robusta para o modelo Gemini 1.5 Flash
model = genai.GenerativeModel('gemini-1.5-flash') 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro v4", layout="wide")

# --- BANCO DE DADOS COM REPARO DINÂMICO ---
def init_db():
    conn = sqlite3.connect('nutri_data.db', check_same_thread=False)
    c = conn.cursor()
    # Cria a tabela base se não existir
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)''')
    
    # LISTA DE REPARO: Adiciona cada coluna se ela estiver faltando (Resolve o KeyError das fotos)
    colunas_necessarias = [
        ('idade', 'INTEGER'),
        ('objetivo', 'TEXT'),
        ('clinico', 'TEXT'),
        ('exames', 'TEXT'),
        ('data_cadastro', 'TEXT')
    ]
    for col, tipo in colunas_necessarias:
        try:
            c.execute(f'ALTER TABLE pacientes ADD COLUMN {col} {tipo}')
        except sqlite3.OperationalError:
            pass # A coluna já existe, ignora o erro
    conn.commit()
    return conn

conn = init_db()

# --- NAVEGAÇÃO ---
st.sidebar.title("🍎 NutriSync")
menu = st.sidebar.radio("Menu", ["📊 Dashboard", "📝 Novo Paciente", "🤖 IA Prescritora"])

if menu == "📊 Dashboard":
    st.title("Pacientes Cadastrados")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    
    if not df.empty:
        # PROTEÇÃO CONTRA KEYERROR: Filtra apenas as colunas que REALMENTE existem no DataFrame
        cols_desejadas = ['nome', 'idade', 'objetivo', 'data_cadastro']
        cols_existentes = [c for c in cols_desejadas if c in df.columns]
        st.dataframe(df[cols_existentes], use_container_width=True)
    else:
        st.info("Nenhum paciente encontrado. Vá em 'Novo Paciente' para começar.")

elif menu == "📝 Novo Paciente":
    st.title("Cadastro de Paciente")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 0, 120)
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        clinico = st.text_area("Histórico Clínico")
        if st.form_submit_button("Salvar Registro"):
            if nome:
                dt = datetime.now().strftime("%d/%m/%Y")
                conn.execute("INSERT INTO pacientes (nome, idade, objetivo, clinico, data_cadastro) VALUES (?,?,?,?,?)",
                             (nome, idade, obj, clinico, dt))
                conn.commit()
                st.success(f"Paciente {nome} salvo com sucesso!")
            else:
                st.error("O campo Nome é obrigatório.")

elif menu == "🤖 IA Prescritora":
    st.title("Assistente Nutricional Gemini")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    
    if df.empty:
        st.warning("Cadastre um paciente primeiro.")
    else:
        paciente_nome = st.selectbox("Selecione o Paciente", df['nome'])
        p_data = df[df['nome'] == paciente_nome].iloc[0]
        
        if st.button("🪄 Gerar Dieta com IA"):
            # Uso de .get para evitar erro se a coluna sumir
            prompt = f"Gere uma dieta para {paciente_nome}, foco em {p_data.get('objetivo', 'Saúde')}, restrições: {p_data.get('clinico', 'Nenhuma')}."
            with st.spinner("IA processando..."):
                try:
                    response = model.generate_content(prompt)
                    st.markdown("### Plano Sugerido")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Erro na IA: {e}")
