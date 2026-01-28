import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURAÇÃO DA IA ---
# Substitua pela sua chave real
API_KEY = "AIzaSyAO9CysPJuLdaM9Br-lVByTq-6dlgyJXdQ" 
genai.configure(api_key=API_KEY)

# Usando o modelo estável para evitar o erro 404
model = genai.GenerativeModel('gemini-1.5-flash') 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro", layout="wide", page_icon="🍎")

# --- BANCO DE DADOS COM AUTO-CORREÇÃO (Resolve o KeyError) ---
def get_connection():
    return sqlite3.connect('nutri_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, idade INTEGER, objetivo TEXT, 
                  clinico TEXT, exames TEXT, data_cadastro TEXT)''')
    
    # RESOLVE O KEYERROR: Verifica as colunas e as cria se faltarem no banco antigo
    cursor = conn.execute('SELECT * FROM pacientes')
    cols = [description[0] for description in cursor.description]
    
    if 'data_cadastro' not in cols:
        c.execute('ALTER TABLE pacientes ADD COLUMN data_cadastro TEXT')
    if 'clinico' not in cols:
        c.execute('ALTER TABLE pacientes ADD COLUMN clinico TEXT')
    if 'idade' not in cols:
        c.execute('ALTER TABLE pacientes ADD COLUMN idade INTEGER')
    
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)')
    conn.commit()

init_db()

# --- ESTILIZAÇÃO PARA VISIBILIDADE ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #001E3C !important;
        border-radius: 12px; padding: 20px;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("🍎 NutriSync Pro")
menu = st.sidebar.radio("Ir para:", ["📊 Dashboard", "📝 Prontuário", "🤖 Gerar Dieta IA"])
conn = get_connection()

# --- LOGICA DAS SEÇÕES ---
if menu == "📊 Dashboard":
    st.title("Pacientes Recentes")
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    
    if not df_p.empty:
        # Exibe apenas colunas que garantidamente existem agora
        st.dataframe(df_p[['nome', 'objetivo', 'data_cadastro']], use_container_width=True)
    else:
        st.info("Nenhum paciente cadastrado.")

elif menu == "📝 Prontuário":
    st.title("Cadastro de Paciente")
    with st.form("cad_form", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 0, 120)
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        clin = st.text_area("Histórico Clínico/Restrições")
        exames = st.text_area("Resultados de Exames")
        
        if st.form_submit_button("Salvar Paciente"):
            if nome:
                dt = datetime.now().strftime("%d/%m/%Y")
                conn.execute("INSERT INTO pacientes (nome, idade, objetivo, clinico, exames, data_cadastro) VALUES (?,?,?,?,?,?)",
                             (nome, idade, obj, clin, exames, dt))
                conn.commit()
                st.success(f"Paciente {nome} salvo com sucesso!")
            else:
                st.error("O nome é obrigatório.")

elif menu == "🤖 Gerar Dieta IA":
    st.title("Assistente de IA")
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    
    if df_p.empty:
        st.warning("Cadastre um paciente primeiro no prontuário.")
    else:
        sel = st.selectbox("Escolha o Paciente", df_p['nome'])
        p = df_p[df_p['nome'] == sel].iloc[0]
        
        if st.button("🪄 Gerar Dieta"):
            prompt = f"Como nutricionista, crie uma dieta para {p.get('nome')}, objetivo: {p.get('objetivo')}, clínico: {p.get('clinico')}."
            with st.spinner("O Gemini está analisando os dados..."):
                try:
                    response = model.generate_content(prompt)
                    st.markdown("### Plano Alimentar Sugerido")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Erro ao gerar dieta: {e}")
