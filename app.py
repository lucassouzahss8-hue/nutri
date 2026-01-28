import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="NutriSync Pro", layout="wide", page_icon="🍎")

# --- CONEXÃO COM BANCO DE DADOS ---
conn = sqlite3.connect('nutri_data.db', check_same_thread=False)
c = conn.cursor()

# Criar tabelas básicas se não existirem
c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
             (id INTEGER PRIMARY KEY, nome TEXT, idade INTEGER, objetivo TEXT)''')
conn.commit()

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2e7d32; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("🍎 NutriSync v1.0")
menu = st.sidebar.radio("Navegação", [
    "Dashboard", 
    "Prontuário (Anamnese)", 
    "Antropometria", 
    "Plano Alimentar", 
    "Suplementação", 
    "Financeiro"
])

# --- LÓGICA DAS PÁGINAS ---

if menu == "Dashboard":
    st.title("📊 Painel Geral")
    col1, col2, col3 = st.columns(3)
    col1.metric("Pacientes Ativos", "12")
    col2.metric("Consultas Hoje", "4")
    col3.metric("Receita Mensal", "R$ 4.500", "+15%")
    
    st.subheader("Agenda do Dia")
    agenda = pd.DataFrame({
        "Horário": ["09:00", "10:30", "14:00"],
        "Paciente": ["João Silva", "Maria Oliveira", "Carlos Souza"],
        "Status": ["Confirmado", "Em espera", "Online"]
    })
    st.table(agenda)

elif menu == "Prontuário (Anamnese)":
    st.title("📝 Cadastro e Anamnese")
    with st.form("form_paciente"):
        nome = st.text_input("Nome Completo")
        data_nasc = st.date_input("Data de Nascimento")
        objetivo = st.selectbox("Objetivo Principal", ["Emagrecimento", "Hipertrofia", "Performance", "Saúde"])
        historico = st.text_area("Histórico Clínico (Doenças, Alergias, Medicamentos)")
        if st.form_submit_button("Salvar Prontuário"):
            c.execute("INSERT INTO pacientes (nome, idade, objetivo) VALUES (?,?,?)", (nome, 25, objetivo))
            conn.commit()
            st.success("Paciente cadastrado com sucesso!")

elif menu == "Antropometria":
    st.title("⚖️ Composição Corporal")
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Peso (kg)", value=70.0)
        altura = st.number_input("Altura (cm)", value=170)
    with col2:
        pescoço = st.number_input("Circunferência Pescoço (cm)", value=35.0)
        cintura = st.number_input("Circunferência Cintura (cm)", value=80.0)
    
    # Cálculo Simples de IMC
    imc = peso / ((altura/100)**2)
    st.metric("IMC Atual", f"{imc:.2f}")
    
    if imc < 18.5: st.warning("Abaixo do peso")
    elif imc < 25: st.success("Peso normal")
    else: st.error("Sobrepeso/Obesidade")

elif menu == "Plano Alimentar":
    st.title("🍽️ Prescrição Dietética")
    paciente_sel = st.selectbox("Selecionar Paciente", ["João Silva", "Maria Oliveira"])
    
    st.subheader("Distribuição de Macronutrientes")
    carb = st.slider("Carboidratos (%)", 0, 100, 40)
    prot = st.slider("Proteínas (%)", 0, 100, 30)
    fat = st.slider("Gorduras (%)", 0, 100, 30)
    
    if carb + prot + fat != 100:
        st.error("A soma dos macros deve ser 100%!")
    
    st.text_area("Refeição 1 - Café da Manhã", "Ex: 2 ovos mexidos + 1 fatia de pão integral")
    st.button("Gerar PDF do Plano")

elif menu == "Suplementação":
    st.title("💊 Prescrição de Suplementos")
    suplemento = st.text_input("Nome do Suplemento/Fórmula")
    dosagem = st.text_input("Dosagem (ex: 5g, 500mg)")
    horario = st.text_input("Posologia (ex: Pré-treino, Após almoço)")
    if st.button("Adicionar à Receita"):
        st.write(f"✅ Adicionado: {suplemento} - {dosagem} ({horario})")

elif menu == "Financeiro":
    st.title("💰 Gestão Financeira")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Entradas")
        st.date_input("Data do Recebimento")
        valor = st.number_input("Valor da Consulta (R$)", value=250.0)
        metodo = st.selectbox("Forma de Pagamento", ["Pix", "Cartão", "Dinheiro"])
        if st.button("Registrar Pagamento"):
            st.success("Lançamento efetuado!")
    with col2:
        st.subheader("Resumo Mensal")
        st.info("Total Recebido: R$ 4.500,00")
        st.error("Despesas Fixas: R$ 1.200,00")

# --- RODAPÉ ---
st.sidebar.markdown("---")
st.sidebar.caption("Desenvolvido para Nutricionistas v1.0")
