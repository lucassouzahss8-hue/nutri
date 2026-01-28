import streamlit as st
import google.generativeai as genai

# 1. Configuração da IA (COLE SUA CHAVE AQUI)
API_KEY = "AIzaSyCBcNud4YjHkv0wLWZneZ1wQ3eBoV7qoJg"
genai.configure(api_key=API_KEY)

st.title("🧪 Teste de Conexão IA")

# 2. Diagnóstico de Versão
st.write(f"Versão da biblioteca: {genai.__version__}")

# 3. Campo de Teste
pergunta = st.text_input("Diga 'Olá' para a IA:", "Olá, você está funcionando?")

if st.button("Executar Teste"):
    try:
        # Chamada direta ao modelo estável
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(pergunta)
        
        st.success("✅ A IA RESPONDEU!")
        st.write(response.text)
        
    except Exception as e:
        st.error("❌ O erro persiste.")
        st.code(str(e))
        st.info("Se o erro for 404, sua biblioteca está desatualizada no servidor.")
