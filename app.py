import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURAÇÃO DA IA ---
# Insira sua chave real obtida no Google AI Studio
API_KEY = "SUA_CHAVE_AQUI" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro", layout="wide", page_icon="🍎")

# --- BANCO DE DADOS COM CORREÇÃO AUTOMÁTICA (Resolve o KeyError) ---
def get_connection():
    return sqlite3.connect('nutri_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Cria a tabela base se não existir
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, idade INTEGER, objetivo TEXT, 
                  clinico TEXT, exames TEXT, data_cadastro TEXT)''')
    
    # RESOLVE O KEYERROR: Verifica as colunas existentes e adiciona as que faltam
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

# --- ESTILIZAÇÃO E NAVEGAÇÃO ---
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

st.sidebar.title("🍎 NutriSync Pro")
menu = st.sidebar.radio("Navegação:", ["📊 Dashboard", "📝 Prontuário", "🤖 Prescrição IA", "💰 Financeiro"])
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
        # Exibe apenas as colunas que agora garantidamente existem no DataFrame
        cols_to_show = [c for c in ['nome', 'idade', 'objetivo', 'data_cadastro'] if c in df_p.columns]
        st.dataframe(df_p[cols_to_show], use_container_width=True)
    else:
        st.info("Nenhum paciente cadastrado.")

elif menu == "📝 Prontuário":
    st.title("Anamnese e Exames")
    with st.form("form_paciente", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 0, 120)
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        clinico = st.text_area("Histórico Clínico (Alergias, Medicamentos, Patologias)")
        exames = st.text_area("Resultados de Exames")
        if st.form_submit_button("Salvar Registro"):
            if nome:
                dt = datetime.now().strftime("%d/%m/%Y")
                conn.execute("INSERT INTO pacientes (nome, idade, objetivo, clinico, exames, data_cadastro) VALUES (?,?,?,?,?,?)",
                             (nome, idade, obj, clinico, exames, dt))
                conn.commit()
                st.success("Paciente cadastrado com sucesso!")
            else: st.error("O nome é obrigatório.")

elif menu == "🤖 Prescrição IA":
    st.title("Assistente de IA")
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    if df_p.empty:
        st.warning("Cadastre um paciente primeiro.")
    else:
        sel = st.selectbox("Selecione o Paciente", df_p['nome'])
        p = df_p[df_p['nome'] == sel].iloc[0]
        
        # Uso seguro de chaves para evitar KeyError durante a geração do prompt
        p_nome = p.get('nome', 'Paciente')
        p_obj = p.get('objetivo', 'Saúde')
        p_clin = p.get('clinico', 'Nenhuma restrição informada')

        if st.button("🪄 Gerar Dieta"):
            prompt = f"Crie uma dieta personalizada para {p_nome}, com foco em {p_obj}. Considere o seguinte histórico clínico: {p_clin}."
            with st.spinner("IA processando..."):
                try:
                    response = model.generate_content(prompt)
                    st.markdown("### Sugestão de Plano Alimentar")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Erro ao gerar dieta: {e}")

elif menu == "💰 Financeiro":
    st.title("Financeiro")
    valor = st.number_input("Valor da Consulta", 0.0)
    if st.button("Lançar"):
        dt = datetime.now().strftime("%d/%m/%Y")
        conn.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", (dt, valor))
        conn.commit()
        st.rerun()
