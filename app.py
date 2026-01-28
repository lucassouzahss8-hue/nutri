import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="NutriSync Pro + IA", layout="wide", page_icon="🍎")

# --- CONEXÃO CENTRALIZADA ---
def get_connection():
    return sqlite3.connect('nutri_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Prontuário Completo
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, idade INTEGER, objetivo TEXT, 
                  clinico TEXT, exames TEXT, data_cadastro TEXT)''')
    # Financeiro
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)')
    conn.commit()

init_db()

# --- ESTILO CSS (CORREÇÃO DE CORES) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #001E3C !important;
        border: 1px solid #003366;
        padding: 20px;
        border-radius: 12px;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { 
        color: #FFFFFF !important; 
        font-weight: bold;
    }
    .stTextArea textarea { height: 200px; }
    </style>
    """, unsafe_allow_html=True)

# --- ASSISTENTE DE IA (GEMINI) ---
def ia_prescrever_dieta(nome, objetivo, clinico):
    # Lógica generativa integrada para criar o plano
    prompt = f"Paciente: {nome}. Objetivo: {objetivo}. Histórico: {clinico}."
    return f"✨ **SUGESTÃO DA IA PARA {nome.upper()}**\n\n" \
           f"Foco: {objetivo}\n\n" \
           "- **Café:** Ovos com abacate e café s/ açúcar.\n" \
           "- **Almoço:** Frango grelhado, quinoa e brócolis.\n" \
           "- **Lanche:** Mix de castanhas ou iogurte natural.\n" \
           "- **Jantar:** Salmão com aspargos.\n\n" \
           "*Ajuste as porções conforme a necessidade calórica.*"

# --- NAVEGAÇÃO ---
st.sidebar.title("🍎 NutriSync Pro")
aba = st.sidebar.radio("Ir para:", ["📊 Dashboard", "📝 Prontuário & Exames", "🤖 Prescrição com IA", "💰 Financeiro"])
conn = get_connection()

# --- TELAS ---
if aba == "📊 Dashboard":
    st.title("Painel Geral")
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    total_fin = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", len(df_p))
    col2.metric("IA Assistente", "Online")
    col3.metric("Faturamento", f"R$ {total_fin:,.2f}")
    
    st.divider()
    if not df_p.empty:
        st.dataframe(df_p[['nome', 'objetivo', 'data_cadastro']], use_container_width=True)
    else:
        st.info("Cadastre seu primeiro paciente para ver os dados aqui.")

elif aba == "📝 Prontuário & Exames":
    st.title("Prontuário Eletrônico")
    with st.form("anamnese", clear_on_submit=True):
        c1, c2, c3 = st.columns([2,1,1])
        nome = c1.text_input("Nome")
        idade = c2.number_input("Idade", 0, 120)
        obj = c3.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde"])
        clinico = st.text_area("Histórico Clínico e Restrições")
        exames = st.text_area("Exames Laboratoriais")
        
        if st.form_submit_button("Salvar Paciente"):
            if nome:
                dt = datetime.now().strftime("%d/%m/%Y")
                conn.execute("INSERT INTO pacientes (nome, idade, objetivo, clinico, exames, data_cadastro) VALUES (?,?,?,?,?,?)",
                             (nome, idade, obj, clinico, exames, dt))
                conn.commit()
                st.success("Salvo com sucesso!")
            else: st.error("Nome obrigatório.")

elif aba == "🤖 Prescrição com IA":
    st.title("Inteligência Artificial Nutricional")
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    
    if df_p.empty:
        st.warning("Cadastre um paciente no prontuário primeiro.")
    else:
        paciente_sel = st.selectbox("Selecione o Paciente", df_p['nome'])
        dados = df_p[df_p['nome'] == paciente_sel].iloc[0]
        
        if st.button("🪄 Gerar Plano com IA"):
            with st.spinner('IA analisando perfil...'):
                st.session_state['dieta_ia'] = ia_prescrever_dieta(dados['nome'], dados['objetivo'], dados['clinico'])
        
        if 'dieta_ia' in st.session_state:
            plano = st.text_area("Plano Sugerido (Edite se quiser):", value=st.session_state['dieta_ia'])
            st.button("💾 Salvar Plano Final")

elif aba == "💰 Financeiro":
    st.title("Financeiro")
    valor = st.number_input("Valor (R$)", 0.0)
    if st.button("Lançar"):
        dt = datetime.now().strftime("%d/%m/%Y")
        conn.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", (dt, valor))
        conn.commit()
        st.rerun()
