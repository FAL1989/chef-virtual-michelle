import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
from database_supabase import ReceitasDB
import json
from datetime import datetime
import httpx
from typing import List, Dict, Optional

# Configuração da página
st.set_page_config(
    page_title="Chef Virtual - Receitas da Michelle",
    page_icon="👩‍🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_openai_client() -> Optional[OpenAI]:
    """Inicializa o cliente OpenAI com configuração HTTP personalizada"""
    try:
        http_client = httpx.Client(
            base_url="https://api.openai.com/v1",
            follow_redirects=True,
            timeout=60.0
        )
        
        return OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"],
            http_client=http_client
        )
    except Exception as e:
        st.error(f"Erro ao inicializar OpenAI: {str(e)}")
        return None

def init_session_state():
    """Inicializa o estado da sessão"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_search" not in st.session_state:
        st.session_state.last_search = None

def format_recipe(recipe: Dict) -> str:
    """Formata uma receita para exibição"""
    texto = f"### {recipe['titulo']}\n\n"
    
    if recipe.get('descricao'):
        texto += f"{recipe['descricao']}\n\n"
    
    if recipe.get('beneficios_funcionais'):
        texto += "**BENEFÍCIOS FUNCIONAIS:**\n"
        for beneficio in recipe['beneficios_funcionais']:
            texto += f"- {beneficio}\n"
        texto += "\n"
    
    if recipe.get('categoria'):
        texto += f"**CATEGORIA:** {recipe['categoria']}\n\n"
    
    texto += "**INFORMAÇÕES GERAIS:**\n"
    if recipe.get('tempo_preparo'):
        texto += f"⏱️ Tempo de Preparo: {recipe['tempo_preparo']}\n"
    if recipe.get('porcoes'):
        texto += f"🍽️ Porções: {recipe['porcoes']}\n"
    if recipe.get('dificuldade'):
        texto += f"📊 Dificuldade: {recipe['dificuldade']}\n"
    texto += "\n"
    
    if recipe.get('informacoes_nutricionais'):
        texto += "**INFORMAÇÕES NUTRICIONAIS (por porção):**\n"
        info_nutri = recipe['informacoes_nutricionais']
        if info_nutri.get('calorias'):
            texto += f"🔸 Calorias: {info_nutri['calorias']}\n"
        if info_nutri.get('proteinas'):
            texto += f"🔸 Proteínas: {info_nutri['proteinas']}\n"
        if info_nutri.get('carboidratos'):
            texto += f"🔸 Carboidratos: {info_nutri['carboidratos']}\n"
        if info_nutri.get('gorduras'):
            texto += f"🔸 Gorduras: {info_nutri['gorduras']}\n"
        if info_nutri.get('fibras'):
            texto += f"🔸 Fibras: {info_nutri['fibras']}\n"
        texto += "\n"
    
    if recipe.get('utensilios'):
        texto += f"**UTENSÍLIOS NECESSÁRIOS:**\n{recipe['utensilios']}\n\n"
    
    texto += "**INGREDIENTES:**\n"
    ingredientes = recipe['ingredientes']
    if isinstance(ingredientes, list):
        for ingrediente in ingredientes:
            texto += f"- {ingrediente}\n"
    else:
        texto += ingredientes
    texto += "\n"
    
    texto += "**MODO DE PREPARO:**\n"
    modo_preparo = recipe['modo_preparo']
    if isinstance(modo_preparo, list):
        for i, passo in enumerate(modo_preparo, 1):
            texto += f"{i}. {passo}\n"
    else:
        texto += modo_preparo
    texto += "\n"
    
    if recipe.get('dicas'):
        texto += "**DICAS DA CHEF:**\n"
        dicas = recipe['dicas']
        if isinstance(dicas, list):
            for dica in dicas:
                texto += f"💡 {dica}\n"
        else:
            texto += f"💡 {dicas}\n"
        texto += "\n"
    
    if recipe.get('harmonizacao'):
        texto += f"**HARMONIZAÇÃO E CONSUMO:**\n{recipe['harmonizacao']}\n\n"
    
    texto += "---\n"
    return texto

def render_recipe_card(recipe: Dict) -> None:
    """Renderiza um card de receita"""
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(recipe['titulo'])
            if recipe.get('descricao'):
                st.write(recipe['descricao'])
            
            # Métricas principais
            metrics_cols = st.columns(3)
            with metrics_cols[0]:
                st.metric("⏱️ Tempo", recipe.get('tempo_preparo', 'N/A'))
            with metrics_cols[1]:
                st.metric("🍽️ Porções", recipe.get('porcoes', 'N/A'))
            with metrics_cols[2]:
                st.metric("📊 Dificuldade", recipe.get('dificuldade', 'N/A'))
        
        with col2:
            # Informações nutricionais em formato compacto
            if recipe.get('informacoes_nutricionais'):
                st.write("📊 Info. Nutricional")
                info = recipe['informacoes_nutricionais']
                if info.get('calorias'):
                    st.write(f"🔸 Cal: {info['calorias']}")
                if info.get('proteinas'):
                    st.write(f"🔸 Prot: {info['proteinas']}")
        
        # Expandir para ver mais detalhes
        with st.expander("Ver receita completa"):
            st.markdown(format_recipe(recipe))
    st.divider()

def render_sidebar(db: ReceitasDB):
    """Renderiza a barra lateral"""
    with st.sidebar:
        st.title("🔍 Busca")
        busca = st.text_input("Digite sua busca:", key="busca")
        
        if busca:
            receitas = ReceitasDB.buscar_receitas_cached(busca)  # Usando método estático
            if receitas:
                st.success(f"Encontradas {len(receitas)} receitas!")
            else:
                st.warning("Nenhuma receita encontrada.")
        else:
            receitas = ReceitasDB.exportar_receitas_cached()  # Usando método estático
            if receitas:
                st.success(f"Total de {len(receitas)} receitas!")
            else:
                st.warning("Nenhuma receita encontrada.")
        
        return receitas

def export_history():
    """Exporta o histórico da conversa para um arquivo"""
    if not st.session_state.messages:
        st.warning("Não há histórico para exportar!")
        return
    
    texto = "# Histórico de Receitas - Chef Virtual Michelle\n\n"
    texto += f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            texto += f"## 👤 Pergunta:\n{msg['content']}\n\n"
        else:
            texto += f"## 👩‍🍳 Resposta da Chef Michelle:\n{msg['content']}\n\n"
            texto += "---\n\n"
    
    st.download_button(
        label="📥 Exportar Histórico",
        data=texto,
        file_name=f"receitas_michelle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )

def render_message_history():
    """Renderiza o histórico de mensagens"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def process_user_input(client: OpenAI, db: ReceitasDB):
    """Processa a entrada do usuário"""
    if prompt := st.chat_input("Digite aqui sua pergunta ou ingredientes:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processando sua solicitação..."):
                receitas_encontradas = db.buscar_receitas(prompt)
                
                if receitas_encontradas:
                    resposta = "Encontrei estas receitas no nosso banco de dados:\n\n"
                    for receita in receitas_encontradas:
                        resposta += format_recipe(receita) + "\n---\n\n"
                else:
                    st.info("Não encontrei receitas existentes com esses ingredientes. Vou criar uma nova receita para você!")
                    resposta = generate_new_recipe(client, prompt, db)
                
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

def generate_new_recipe(client: OpenAI, prompt: str, db: ReceitasDB) -> str:
    """Gera uma nova receita usando a API da OpenAI"""
    try:
        messages = prepare_ai_context(prompt)
        response = call_openai_api(client, messages)
        
        # Tenta salvar a receita no banco de dados
        try:
            receita_dict = json.loads(response)
            if db.adicionar_receita(receita_dict):
                st.success("Receita salva no banco de dados!")
        except json.JSONDecodeError:
            st.warning("Não foi possível salvar a receita no banco de dados.")
        
        return response
    except Exception as e:
        return f"Desculpe, ocorreu um erro ao gerar a receita: {str(e)}"

def prepare_ai_context(prompt: str) -> List[Dict]:
    """Prepara o contexto para a chamada da IA"""
    context = """Você é a Chef Michelle Mística, uma renomada chef especializada em gastronomia funcional com formação em nutrição funcional e fitoterapia. Sua abordagem única combina:

    FILOSOFIA CULINÁRIA:
    - Criação de receitas que são simultaneamente nutritivas E deliciosas
    - Uso inteligente de ingredientes funcionais sem comprometer o sabor
    - Adaptação de receitas tradicionais para versões mais saudáveis
    - Equilíbrio entre prazer gastronômico e benefícios nutricionais

    ESPECIALIDADES:
    - Técnicas avançadas de gastronomia funcional
    - Conhecimento profundo de propriedades nutricionais dos alimentos
    - Combinações sinérgicas de ingredientes para potencializar benefícios
    - Adaptações para diferentes necessidades (sem ser restritiva)

    DIFERENCIAIS:
    - Receitas que agradam tanto amantes da comida saudável quanto céticos
    - Uso criativo de ingredientes funcionais em pratos tradicionais
    - Explicações sobre os benefícios nutricionais de cada ingrediente
    - Dicas de substituições e adaptações para diferentes preferências

    Ao criar uma receita, sempre inclua:
    1. Título criativo que destaque o aspecto funcional
    2. Lista de ingredientes com quantidades precisas
    3. Benefícios funcionais dos ingredientes principais
    4. Modo de preparo detalhado
    5. Tempo de preparo e rendimento
    6. Dicas de substituições e variações
    7. Informações nutricionais relevantes
    8. Sugestões de harmonização e consumo

    Formate a resposta em JSON com os campos:
    {
        "titulo": "Nome da receita",
        "descricao": "Breve descrição dos benefícios e características",
        "beneficios_funcionais": ["Lista de benefícios principais"],
        "ingredientes": ["Lista com quantidades"],
        "modo_preparo": ["Passos detalhados"],
        "tempo_preparo": "Tempo total",
        "porcoes": "Número de porções",
        "dificuldade": "Nível de dificuldade",
        "informacoes_nutricionais": {
            "calorias": "por porção",
            "proteinas": "em gramas",
            "carboidratos": "em gramas",
            "gorduras": "em gramas",
            "fibras": "em gramas"
        },
        "dicas": ["Dicas de preparo e substituições"],
        "harmonizacao": "Sugestões de consumo e acompanhamentos"
    }
    """
    
    return [
        {"role": "system", "content": context},
        {"role": "user", "content": prompt}
    ]

def call_openai_api(client: OpenAI, messages: List[Dict]) -> str:
    """Faz a chamada à API da OpenAI"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=messages,
            temperature=0.85,
            max_tokens=2000,
            top_p=0.95,
            frequency_penalty=0.3,
            presence_penalty=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Erro na chamada da API: {str(e)}")

def main():
    """Função principal do aplicativo"""
    # Carrega as variáveis de ambiente
    if os.path.exists(".env"):
        load_dotenv()
    
    # Inicializa o cliente OpenAI
    client = init_openai_client()
    if not client:
        st.stop()
    
    # Inicializa o banco de dados
    db = ReceitasDB()
    
    # Inicializa o estado da sessão
    init_session_state()
    
    # Renderiza o título
    st.title("Chef Virtual - Receitas da Michelle")
    st.write("Bem-vindo! Pergunte por uma receita ou informe os ingredientes que você tem disponível.")
    
    # Renderiza a barra lateral
    render_sidebar(db)
    
    # Renderiza o histórico de mensagens
    render_message_history()
    
    # Processa a entrada do usuário
    process_user_input(client, db)

if __name__ == "__main__":
    main()
