import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
from database import ReceitasDB
import json
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Chef Virtual - Receitas da Michelle",
    page_icon="👩‍🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carrega as variáveis de ambiente (local ou cloud)
if os.path.exists(".env"):
    load_dotenv()

# Inicializa o cliente OpenAI
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"))
db = ReceitasDB()

# Inicializa o histórico de mensagens no session_state se não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

def exportar_historico():
    """Exporta o histórico da conversa para um arquivo"""
    if not st.session_state.messages:
        st.warning("Não há histórico para exportar!")
        return
    
    # Formata o histórico para um texto legível
    texto = "# Histórico de Receitas - Chef Virtual Michelle\n\n"
    texto += f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            texto += f"## 👤 Pergunta:\n{msg['content']}\n\n"
        else:
            texto += f"## 👩‍🍳 Resposta da Chef Michelle:\n{msg['content']}\n\n"
            texto += "---\n\n"
    
    # Cria o arquivo para download
    st.download_button(
        label="📥 Exportar Histórico",
        data=texto,
        file_name=f"receitas_michelle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )

def buscar_receitas_existentes(pergunta: str) -> list:
    """Busca receitas no banco de dados"""
    # Normaliza a pergunta
    termos_busca = pergunta.lower()
    
    # Remove palavras comuns que podem atrapalhar a busca
    palavras_para_remover = ['receita', 'de', 'do', 'da', 'dos', 'das', 'com', 'e', 
                           'preciso', 'quero', 'como', 'fazer', 'tem', 'olá', 'oi']
    
    for palavra in palavras_para_remover:
        termos_busca = termos_busca.replace(f' {palavra} ', ' ')
    
    # Limpa espaços extras
    termos_busca = ' '.join(termos_busca.split())
    
    print(f"Buscando por: {termos_busca}")  # Debug
    return db.buscar_receitas(termos_busca)

def gerar_nova_receita(pergunta: str) -> str:
    """Gera uma nova receita usando a IA"""
    try:
        # Obtém o contexto das receitas existentes
        contexto = db.get_todas_receitas()
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": f"""Você é a Michelle Mística uma chef profissional especializada em criar receitas detalhadas e práticas.
                    Use as receitas a seguir como referência para entender o estilo e preferências da Chef Michelle:
                    
                    {contexto}
                    
                    Crie uma NOVA receita seguindo o mesmo estilo, mas não repita exatamente as receitas existentes.
                    Use o seguinte formato:

                    INGREDIENTES:
                    - (lista com quantidades precisas)

                    MODO DE PREPARO:
                    1. (passos numerados e detalhados)

                    TEMPO DE PREPARO: (tempo total)
                    PORÇÕES: (quantidade)
                    DIFICULDADE: (fácil/médio/difícil)

                    DICAS DO CHEF: (2-3 dicas importantes)"""
                },
                {
                    "role": "user",
                    "content": pergunta
                }
            ],
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9,
            frequency_penalty=0.2,
            presence_penalty=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao gerar a receita: {e}"

def formatar_receita(receita: dict) -> str:
    """Formata uma receita do banco de dados para exibição"""
    texto = f"RECEITA: {receita['titulo']}\n\n"
    
    if receita.get('categoria'):
        texto += f"CATEGORIA: {receita['categoria']}\n\n"
    
    texto += "UTENSÍLIOS:\n"
    texto += f"{receita['utensilios']}\n\n"
    
    texto += "INGREDIENTES:\n"
    texto += f"{receita['ingredientes']}\n\n"
    
    texto += "MODO DE PREPARO:\n"
    texto += f"{receita['modo_preparo']}\n"
    
    return texto

def main():
    st.title("Chef Virtual - Receitas da Michelle")
    st.write("Bem-vindo! Pergunte por uma receita ou informe os ingredientes que você tem disponível.")

    # Barra lateral para filtros e exportação
    with st.sidebar:
        st.header("Filtros")
        busca = st.text_input("Buscar receitas existentes:")
        if busca:
            receitas = db.buscar_receitas(busca)
            if receitas:
                st.success(f"Encontradas {len(receitas)} receitas!")
                for receita in receitas:
                    with st.expander(receita['titulo']):
                        st.write("**CATEGORIA:**", receita['categoria'])
                        st.write("**UTENSÍLIOS:**")
                        st.write(receita['utensilios'])
                        st.write("**INGREDIENTES:**")
                        st.write(receita['ingredientes'])
                        st.write("**MODO DE PREPARO:**")
                        st.write(receita['modo_preparo'])
        
        st.markdown("---")
        st.header("Exportar Conversa")
        exportar_historico()

    # Exibe o histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Área principal
    if prompt := st.chat_input("Digite aqui sua pergunta ou ingredientes:"):
        # Adiciona a mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Primeiro, tenta encontrar receitas existentes
        receitas_encontradas = buscar_receitas_existentes(prompt)
        
        with st.chat_message("assistant"):
            if receitas_encontradas:
                resposta = "Encontrei estas receitas no nosso banco de dados:\n\n"
                for receita in receitas_encontradas:
                    resposta += formatar_receita(receita) + "\n---\n\n"
            else:
                st.info("Não encontrei receitas existentes com esses ingredientes. Vou criar uma nova receita para você!")
                resposta = gerar_nova_receita(prompt)
            
            st.markdown(resposta)
            # Adiciona a resposta do assistente ao histórico
            st.session_state.messages.append({"role": "assistant", "content": resposta})

if __name__ == "__main__":
    main()
