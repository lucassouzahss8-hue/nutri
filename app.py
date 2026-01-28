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

# --- BANCO DE DADOS DINÂMICO ---
def init_db():
    # Usando um novo nome de arquivo para garantir um banco limpo
    conn = sqlite3.connect('nutri_v5_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome TEXT, 
                  objetivo TEXT, 
                  clinico TEXT, 
                  data_cadastro TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- INTERFACE ---
st.set_page_config(page_title="NutriSync Pro", layout="wide")

st.sidebar.title("🍎 NutriSync")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastrar Paciente", "IA Prescritora"])

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Pacientes Cadastrados")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    
    if not df.empty:
        # Seleção segura de colunas para evitar KeyError
        colunas_exibir = [c for c in ['nome', 'objetivo', 'data_cadastro'] if c in df.columns]
        st.dataframe(df[colunas_exibir], use_container_width=True)
    else:
        st.info("Nenhum paciente encontrado. Vá em 'Cadastrar Paciente'.")

# --- CADASTRO ---
elif menu == "Cadastrar Paciente":
    st.title("📝 Novo Prontuário")
    with st.form("form_cad", clear_on_submit=True):
        nome = st.text_input("Nome do Paciente")
        obj = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Performance", "Saúde"])
        clin = st.text_area("Histórico Clínico e Restrições")
        
        if st.form_submit_button("Salvar no Banco"):
            if nome:
                data_atual = datetime.now().strftime("%d/%m/%Y")
                conn.execute("INSERT INTO pacientes (nome, objetivo, clinico, data_cadastro) VALUES (?,?,?,?)",
                             (nome, obj, clin, data_atual))
                conn.commit()
                st.success(f"Paciente {nome} cadastrado com sucesso!")
            else:
                st.error("Por favor, insira o nome.")

# --- IA PRESCRITORA ---
elif menu == "IA Prescritora":
    st.title("🤖 Assistente de Prescrição")
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    
    if df.empty:
        st.warning("Cadastre um paciente primeiro.")
    else:
        paciente_sel = st.selectbox("Selecione o Paciente", df['nome'])
        dados = df[df['nome'] == paciente_sel].iloc[0]
        
        if st.button("✨ Gerar Dieta com Gemini"):
            with st.spinner("IA analisando dados..."):
                # Prompt estruturado para o Gemini 1.5 Flash
                prompt = f"""Como nutricionista profissional, elabore um plano alimentar para:
                Paciente: {dados['nome']}
                Objetivo: {dados['objetivo']}
                Restrições: {dados.get('clinico', 'Nenhuma')}
                
                Estruture por refeições e seja específico."""
                
                try:
                    response = model.generate_content(prompt)
                    st.markdown("### Sugestão de Plano Alimentar")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Erro na conexão com a IA: {e}")
                    st.info("Verifique se sua API KEY está correta.")
