import streamlit as st
import google.generativeai as genai

# Configuração da API
API_KEY = "AIzaSyCBcNud4YjHkv0wLWZneZ1wQ3eBoV7qoJg"
genai.configure(api_key=API_KEY)

st.title("🍎 NutriSync - Conexão Estabilizada")

pergunta = st.text_input("Diga algo para a IA:", "Olá!")

if st.button("Executar"):
    # Tentativa 1: Gemini 1.5 Flash
    # Tentativa 2: Gemini 1.0 Pro (Caso a primeira falhe com erro 404)
    modelos_para_testar = ['gemini-1.5-flash', 'gemini-pro']
    
    sucesso = False
    for nome_modelo in modelos_para_testar:
        try:
            model = genai.GenerativeModel(nome_modelo)
            response = model.generate_content(pergunta)
            st.success(f"✅ Conectado com sucesso via: {nome_modelo}")
            st.write(response.text)
            sucesso = True
            break # Para se funcionar
        except Exception as e:
            if "404" in str(e):
                st.warning(f"Tentando alternativa... ({nome_modelo} não disponível)")
            else:
                st.error(f"Erro técnico: {e}")
                break
    
    if not sucesso:
        st.error("Não foi possível conectar a nenhum modelo da IA. Verifique sua chave API.")
