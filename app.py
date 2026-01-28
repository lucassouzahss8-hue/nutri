import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro", layout="wide", page_icon="🍎")

# --- 2. BANCO DE DADOS (PERSISTÊNCIA) ---
def init_db():
    conn = sqlite3.connect('nutri_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, objetivo TEXT, historico TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS agenda 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, horario TEXT, paciente TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS financeiro 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, valor REAL)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- 3. ESTILIZAÇÃO CSS PERSONALIZADA ---
st.markdown("""
    <style>
    /* Fundo e Fonte */
    .main { background-color: #f4f7f6; }
    
    /* Quadros de Métrica (Azul Escuro) */
    div[data-testid="metric-container"] {
        background-color: #001E3C !important;
        border: 1px solid #003366;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Texto das Métricas (Branco) */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    /* Card de Estado Vazio */
    .empty-state-card {
        text-align: center;
        padding: 60px;
        background-color: #ffffff;
        border-radius: 20px;
        border: 2px dashed #bdc3c7;
        color: #7f8c8d;
        margin-bottom: 25px;
    }

    /* Botões */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #001E3C;
        color: white;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #003366;
        border-color: #003366;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNÇÕES AUXILIARES ---
def empty_state(titulo="Não há informações no momento", subtitulo="Os registros aparecerão aqui assim que você cadastrá-los."):
    st.markdown(f"""
        <div class="empty-state-card">
            <h1 style="font-size: 50px; margin-bottom: 10px;">📂</h1>
            <h3 style="color: #2c3e50;">{titulo}</h3>
            <p>{subtitulo}</p>
        </div>
    """, unsafe_allow_html=True)

# --- 5. MENU LATERAL ---
st.sidebar.title("🍎 NutriSync Pro")
st.sidebar.markdown("Sistema Integrado de Nutrição")
menu = st.sidebar.radio("Navegação Principal", [
    "📊 Dashboard", 
    "📝 Prontuário", 
    "⚖️ Antropometria", 
    "🍽️ Plano Alimentar", 
    "💰 Financeiro"
])

# --- 6. LÓGICA DAS ABAS ---

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("Painel de Controle")
    
    # KPIs
    qtd_p = pd.read_sql_query("SELECT COUNT(*) as total FROM pacientes", conn).iloc[0]['total']
    faturamento = pd.read_sql_query("SELECT SUM(valor) as total FROM financeiro", conn).iloc[0]['total'] or 0.0
    consultas = pd.read_sql_query("SELECT COUNT(*) as total FROM agenda", conn).iloc[0]['total']

    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", qtd_p)
    col2.metric("Consultas Marcadas", consultas)
    col3.metric("Faturamento Total", f"R$ {faturamento:,.2f}")

    st.divider()
    
    st.subheader("📅 Agenda Próxima")
    agenda_df = pd.read_sql_query("SELECT horario as 'Hora', paciente as 'Paciente', status as 'Status' FROM agenda", conn)
    
    if agenda_df.empty:
        empty_state("Agenda livre", "Nenhuma consulta agendada até o momento.")
    else:
        st.dataframe(agenda_df, use_container_width=True)

    with st.expander("➕ Adicionar Novo Compromisso"):
        with st.form("quick_agenda"):
            h = st.text_input("Horário (ex: 14:00)")
            p = st.text_input("Nome do Paciente")
            if st.form_submit_button("Agendar"):
                c.execute("INSERT INTO agenda (horario, paciente, status) VALUES (?,?,?)", (h, p, "Confirmado"))
                conn.commit()
                st.rerun()

# --- PRONTUÁRIO ---
elif menu == "📝 Prontuário":
    st.title("Prontuário e Cadastro")
    t1, t2 = st.tabs(["🆕 Novo Paciente", "📂 Base de Pacientes"])
    
    with t1:
        with st.form("cad_paciente"):
            nome = st.text_input("Nome Completo")
            obj = st.selectbox("Objetivo Principal", ["Emagrecimento", "Hipertrofia", "Saúde/Bem-estar"])
            hist = st.text_area("Anamnese / Observações")
            if st.form_submit_button("Finalizar Cadastro"):
                c.execute("INSERT INTO pacientes (nome, objetivo, historico) VALUES (?,?,?)", (nome, obj, hist))
                conn.commit()
                st.success(f"Paciente {nome} salvo com sucesso!")

    with t2:
        df_pacientes = pd.read_sql_query("SELECT nome as Nome, objetivo as Objetivo FROM pacientes", conn)
        if df_pacientes.empty:
            empty_state("Nenhum paciente cadastrado")
        else:
            st.dataframe(df_pacientes, use_container_width=True)

# --- ANTROPOMETRIA ---
elif menu == "⚖️ Antropometria":
    st.title("Avaliação Física")
    lista_p = pd.read_sql_query("SELECT nome FROM pacientes", conn)['nome'].tolist()
    
    if not lista_p:
        empty_state("Acesso Restrito", "Cadastre pelo menos um paciente no Prontuário para realizar avaliações.")
    else:
        with st.container():
            st.selectbox("Selecionar Paciente para Avaliação", lista_p)
            col1, col2 = st.columns(2)
            peso = col1.number_input("Peso Atual (kg)", min_value=1.0)
            altura = col2.number_input("Altura (cm)", min_value=1)
            if st.button("Calcular IMC"):
                imc = peso / ((altura/100)**2)
                st.info(f"O IMC calculado é: {imc:.2f}")

# --- PLANO ALIMENTAR ---
elif menu == "🍽️ Plano Alimentar":
    st.title("Prescrição Dietética")
    empty_state("Plano Alimentar", "Seção em desenvolvimento. Em breve você poderá montar cardápios personalizados aqui.")

# --- FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("Gestão Financeira")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Registrar Recebimento")
        with st.form("fin"):
            v = st.number_input("Valor da Consulta (R$)", min_value=0.0)
            if st.form_submit_button("Salvar Entrada"):
                c.execute("INSERT INTO financeiro (data, valor) VALUES (?,?)", 
                          (datetime.now().strftime("%d/%m/%Y"), v))
                conn.commit()
                st.rerun()
                
    with c2:
        st.subheader("Histórico")
        df_fin = pd.read_sql_query("SELECT data as Data, valor as Valor FROM financeiro", conn)
        if df_fin.empty:
            empty_state("Sem lançamentos")
        else:
            st.dataframe(df_fin, use_container_width=True)

# --- RODAPÉ ---
st.sidebar.markdown("---")
st.sidebar.caption(f"NutriSync Pro © 2026 | Logado como Nutricionista")
