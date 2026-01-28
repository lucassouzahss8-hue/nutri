import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro v2.0", layout="wide", page_icon="🍎")

# --- 2. BANCO DE DADOS INTEGRADO ---
def get_connection():
    return sqlite3.connect('nutri_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabela de Prontuário Clínico Completo
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, idade INTEGER, objetivo TEXT, 
                  historico_clinico TEXT, exames_lab TEXT, 
                  data_cadastro TEXT)''')
    # Tabela de Avaliações e Prescrições
    c.execute('''CREATE TABLE IF NOT EXISTS prescricoes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  paciente_id INTEGER, peso REAL, altura REAL, 
                  kcal_total REAL, prot_g REAL, carb_g REAL, gord_g REAL,
                  plano_alimentar TEXT, data_prescricao TEXT)''')
    # Tabela Financeira
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)')
    conn.commit()

init_db()

# --- 3. ESTILIZAÇÃO CSS (Fundo Escuro e Quadros Azul Escuro) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #001E3C !important;
        border: 1px solid #003366;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { 
        color: #FFFFFF !important; 
    }
    .stTextArea textarea { height: 150px; }
    .status-card {
        padding: 20px;
        background-color: #161b22;
        border-radius: 10px;
        border: 1px solid #30363d;
        text-align: center;
        color: #8b949e;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. NAVEGAÇÃO LATERAL ---
st.sidebar.title("🍎 NutriSync Pro")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação", [
    "📊 Dashboard", 
    "📝 Prontuário & Exames", 
    "🍽️ Prescrição & Cálculo", 
    "💰 Financeiro"
])

conn = get_connection()

# --- 5. LÓGICA DAS ABAS ---

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("Painel de Controle")
    
    df_p = pd.read_sql_query("SELECT * FROM pacientes", conn)
    total_fin = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", len(df_p))
    col2.metric("Consultas Hoje", "0")
    col3.metric("Faturamento Mensal", f"R$ {total_fin:,.2f}")
    
    st.divider()
    st.subheader("📋 Pacientes Recentes")
    if df_p.empty:
        st.markdown('<div class="status-card"><h3>Não há informações no momento</h3><p>Cadastre pacientes na aba Prontuário.</p></div>', unsafe_allow_html=True)
    else:
        st.dataframe(df_p[['nome', 'idade', 'objetivo', 'data_cadastro']], use_container_width=True)

# --- PRONTUÁRIO & EXAMES ---
elif menu == "📝 Prontuário & Exames":
    st.title("Prontuário Eletrônico")
    
    with st.form("form_clinico", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        nome = c1.text_input("Nome Completo")
        idade = c2.number_input("Idade", 0, 120)
        obj = c3.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Saúde", "Performance"])
        
        st.subheader("Dados Clínicos")
        clinico = st.text_area("Anamnese (Histórico, Doenças, Medicamentos, Alergias)")
        
        st.subheader("Exames Laboratoriais")
        exames = st.text_area("Resultados (Colesterol, Glicemia, Vitaminas, etc.)")
        
        if st.form_submit_button("💾 Salvar Prontuário Completo"):
            if nome:
                data_atual = datetime.now().strftime("%d/%m/%Y")
                conn.execute('''INSERT INTO pacientes (nome, idade, objetivo, historico_clinico, exames_lab, data_cadastro) 
                                VALUES (?,?,?,?,?,?)''', (nome, idade, obj, clinico, exames, data_atual))
                conn.commit()
                st.success(f"Registro de {nome} criado com sucesso!")
            else:
                st.error("Por favor, insira o nome do paciente.")

# --- PRESCRIÇÃO & CÁLCULO ---
elif menu == "🍽️ Prescrição & Cálculo":
    st.title("Cálculo Dietético e Plano Alimentar")
    
    df_p = pd.read_sql_query("SELECT id, nome FROM pacientes", conn)
    
    if df_p.empty:
        st.markdown('<div class="status-card"><h3>Não há pacientes cadastrados</h3><p>Vá até a aba Prontuário primeiro.</p></div>', unsafe_allow_html=True)
    else:
        paciente_sel = st.selectbox("Selecione o Paciente", df_p['nome'])
        p_id = df_p[df_p['nome'] == paciente_sel]['id'].values[0]
        
        st.divider()
        col1, col2, col3 = st.columns(3)
        peso = col1.number_input("Peso Atual (kg)", min_value=1.0)
        altura = col2.number_input("Altura (cm)", min_value=1)
        nivel_ativ = col3.selectbox("Fator Atividade", [1.2, 1.375, 1.55, 1.725, 1.9], help="1.2 (Sedentário) a 1.9 (Atleta)")

        if peso > 0 and altura > 0:
            # Cálculo de TMB (Mifflin-St Jeor) e GET
            tmb = (10 * peso) + (6.25 * altura) - (5 * 30) + 5
            get = tmb * nivel_ativ
            imc = peso / ((altura/100)**2)
            
            st.info(f"**IMC:** {imc:.2f} | **Gasto Energético Total (GET):** {get:.0f} kcal")
            
            st.subheader("⚖️ Divisão de Macronutrientes")
            m1, m2 = st.columns(2)
            p_g_kg = m1.slider("Proteína (g/kg)", 0.8, 3.0, 2.0)
            g_g_kg = m2.slider("Gordura (g/kg)", 0.5, 1.5, 1.0)
            
            # Cálculo dos gramas
            prot_total = peso * p_g_kg
            gord_total = peso * g_g_kg
            carb_total = (get - (prot_total * 4) - (gord_total * 9)) / 4
            
            st.success(f"Alvos: P: {prot_total:.0f}g | C: {carb_total:.0f}g | G: {gord_total:.0f}g")
            
            st.subheader("📝 Plano Alimentar")
            plano_texto = st.text_area("Prescrição (Refeições e Horários)")
            
            if st.button("💾 Salvar Prescrição"):
                data_p = datetime.now().strftime("%d/%m/%Y")
                conn.execute('''INSERT INTO prescricoes (paciente_id, peso, altura, kcal_total, prot_g, carb_g, gord_g, plano_alimentar, data_prescricao) 
                                VALUES (?,?,?,?,?,?,?,?,?)''', (p_id, peso, altura, get, prot_total, carb_total, gord_total, plano_texto, data_p))
                conn.commit()
                st.success("Plano Alimentar e cálculos salvos!")

# --- FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("Gestão Financeira")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Lançar Receita")
        valor = st.number_input("Valor da Consulta (R$)", min_value=0.0)
        if st.button("Registrar"):
            data_fin = datetime.now().strftime("%d/%m/%Y")
            conn.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", (data_fin, valor))
            conn.commit()
            st.rerun()
            
    with col2:
        st.subheader("Histórico")
        df_fin = pd.read_sql_query("SELECT data as Data, valor as 'Valor (R$)' FROM financeiro", conn)
        if df_fin.empty:
            st.markdown('<div class="status-card"><h3>Sem registros</h3></div>', unsafe_allow_html=True)
        else:
            st.dataframe(df_fin, use_container_width=True)

# --- RODAPÉ ---
st.sidebar.markdown("---")
st.sidebar.caption(f"Logado como: Nutricionista | {datetime.now().year}")
