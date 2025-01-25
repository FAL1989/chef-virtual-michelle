import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
from database_supabase import ReceitasDB, SupabaseDB
from database_interface import DatabaseInterface
import json
from datetime import datetime
import httpx
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import logging

# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Para debug em desenvolvimento, usar logging.DEBUG em arquivos específicos
if os.getenv('ENVIRONMENT') == 'development':
    logger.setLevel(logging.DEBUG)

# Configuração da página
st.set_page_config(
    page_title="Chef Virtual - Receitas da Michelle",
    page_icon="👩‍🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

class DatabaseInterface(ABC):
    @abstractmethod
    def buscar_receitas(self, query: str) -> List[Dict]:
        pass
    
    @abstractmethod
    def adicionar_receita(self, receita: Dict) -> bool:
        pass

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
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""
    if "busca" not in st.session_state:
        st.session_state.busca = ""

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

def render_recipe_preview(receita: dict):
    """Renderiza uma prévia da receita"""
    
    if not receita.get('id'):
        st.warning("Receita sem ID")
        return
        
    # Instancia o banco de dados
    db = ReceitasDB()
        
    col1, col2 = st.columns([3,1])
    
    with col1:
        st.markdown(f"## {receita['titulo']}")
        if receita.get('descricao'):
            st.markdown(f"_{receita['descricao']}_")
            
        st.markdown("### 📝 Ingredientes")
        # Trata ingredientes como string ou lista
        ingredientes = receita['ingredientes']
        if isinstance(ingredientes, str):
            ingredientes = ingredientes.split('\n')
        elif isinstance(ingredientes, list):
            ingredientes = [ing.strip() for ing in ingredientes if ing.strip()]
            
        for i, ing in enumerate(ingredientes[:5]):
            st.markdown(f"• {ing}")
        if len(ingredientes) > 5:
            st.markdown(f"_...e mais {len(ingredientes)-5} ingredientes_")
            
        if receita.get('tempo_preparo'):
            st.markdown(f"⏱️ **Tempo de Preparo**: {receita['tempo_preparo']}")
        if receita.get('porcoes'):
            st.markdown(f"🍽️ **Porções**: {receita['porcoes']}")
        if receita.get('dificuldade'):
            st.markdown(f"📊 **Dificuldade**: {receita['dificuldade']}")
            
    with col2:
        if st.button("Ver receita completa", key=f"btn_{receita['id']}"):
            try:
                receita_completa = db.buscar_receita_por_id(receita['id'])
                if receita_completa:
                    st.markdown("---")
                    st.markdown(f"# {receita_completa['titulo']}")
                    
                    if receita_completa.get('descricao'):
                        st.markdown(f"_{receita_completa['descricao']}_\n")
                    
                    st.markdown("## 📝 Ingredientes")
                    # Trata ingredientes como string ou lista
                    ingredientes = receita_completa['ingredientes']
                    if isinstance(ingredientes, str):
                        ingredientes = ingredientes.split('\n')
                    elif isinstance(ingredientes, list):
                        ingredientes = [ing.strip() for ing in ingredientes if ing.strip()]
                        
                    for ing in ingredientes:
                        st.markdown(f"• {ing}")
                        
                    st.markdown("\n## 👩‍🍳 Modo de Preparo")
                    # Trata modo de preparo como string ou lista
                    modo_preparo = receita_completa['modo_preparo']
                    if isinstance(modo_preparo, str):
                        modo_preparo = modo_preparo.split('\n')
                    elif isinstance(modo_preparo, list):
                        modo_preparo = [passo.strip() for passo in modo_preparo if passo.strip()]
                        
                    for i, passo in enumerate(modo_preparo, 1):
                        st.markdown(f"{i}. {passo}")
                        
                    if receita_completa.get('tempo_preparo'):
                        st.markdown(f"\n⏱️ **Tempo de Preparo**: {receita_completa['tempo_preparo']}")
                    if receita_completa.get('porcoes'):
                        st.markdown(f"🍽️ **Porções**: {receita_completa['porcoes']}")
                    if receita_completa.get('dificuldade'):
                        st.markdown(f"📊 **Dificuldade**: {receita_completa['dificuldade']}")
                        
                    if receita_completa.get('dicas'):
                        st.markdown("\n## 💡 Dicas")
                        dicas = receita_completa['dicas']
                        if isinstance(dicas, str):
                            dicas = dicas.split('\n')
                        for dica in dicas:
                            st.markdown(f"• {dica}")
                            
                    if receita_completa.get('harmonizacao'):
                        st.markdown("\n## 🍷 Harmonização")
                        st.markdown(receita_completa['harmonizacao'])
                        
                    st.markdown("---")
                else:
                    st.error("Não foi possível carregar a receita completa")
            except Exception as e:
                st.error(f"Erro ao carregar receita: {str(e)}")
                logger.error(f"Erro ao carregar receita: {str(e)}")

def search_recipes():
    """Interface de busca de receitas"""
    query = st.text_input("Digite sua busca:")
    
    if query:
        # Cria uma nova instância do ReceitasDB
        db = ReceitasDB()
        receitas = db.buscar_receitas(query)
        if receitas:
            st.write(f"Encontradas {len(receitas)} receitas:")
            for receita in receitas:
                render_recipe_preview(receita)
                st.divider()
        else:
            st.info("Nenhuma receita encontrada. Que tal me perguntar diretamente? Posso criar uma receita especialmente para você!")

def render_recipe_card(recipe: Dict) -> None:
    """Renderiza uma receita completa em formato de card"""
    try:
        with st.container():
            st.header(recipe['titulo'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("⏰ Tempo")
                st.write(recipe.get('tempo_preparo', 'N/A'))
            with col2:
                st.write("🍽️ Porções")
                st.write(recipe.get('porcoes', 'N/A'))
            with col3:
                st.write("📊 Dificuldade")
                st.write(recipe.get('dificuldade', 'N/A'))

            if recipe.get('descricao'):
                st.write("📝 Descrição")
                st.write(recipe['descricao'])

            if recipe.get('ingredientes'):
                st.write("🥗 Ingredientes")
                for ing in recipe['ingredientes']:
                    st.write(f"• {ing}")

            if recipe.get('modo_preparo'):
                st.write("👩‍🍳 Modo de Preparo")
                for i, step in enumerate(recipe['modo_preparo'], 1):
                    st.write(f"{i}. {step}")

            if recipe.get('utensilios'):
                st.write("🔪 Utensílios")
                st.write(recipe['utensilios'])

            if recipe.get('harmonizacao'):
                st.write("🍷 Harmonização")
                st.write(recipe['harmonizacao'])

            info_nutri = recipe.get('informacoes_nutricionais', {})
            if any(info_nutri.values()):
                st.write("📊 Informações Nutricionais")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Calorias", info_nutri.get('calorias', 'N/A'))
                with col2:
                    st.metric("Proteínas", info_nutri.get('proteinas', 'N/A'))
                with col3:
                    st.metric("Carboidratos", info_nutri.get('carboidratos', 'N/A'))
                with col4:
                    st.metric("Gorduras", info_nutri.get('gorduras', 'N/A'))
                with col5:
                    st.metric("Fibras", info_nutri.get('fibras', 'N/A'))

            beneficios = recipe.get('beneficios_funcionais', [])
            if beneficios:
                st.write("🌿 Benefícios Funcionais")
                for b in beneficios:
                    st.write(f"• {b}")

            dicas = recipe.get('dicas', [])
            if dicas:
                st.write("💡 Dicas")
                for d in dicas:
                    st.write(f"• {d}")

    except Exception as e:
        st.error(f"Erro ao renderizar receita")

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

def extract_search_terms(prompt: str) -> str:
    """Extrai termos de busca de uma pergunta"""
    # Remove pontuação e converte para minúsculas
    prompt = prompt.lower()
    
    # Remove palavras comuns de perguntas
    common_phrases = [
        'tem alguma receita',
        'tem receita',
        'sabe fazer',
        'como fazer',
        'tem como fazer'
    ]
    
    for phrase in common_phrases:
        if prompt.startswith(phrase):
            prompt = prompt[len(phrase):].strip()
            break
    
    # Remove preposições comuns
    prepositions = [' de ', ' do ', ' da ', ' com ']
    for prep in prepositions:
        if prep in prompt:
            prompt = prompt.replace(prep, ' ')
    
    # Remove pontuação e espaços extras
    prompt = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in prompt)
    prompt = ' '.join(prompt.split())
    
    return prompt.strip()

def classify_message(text: str) -> str:
    """Classifica o tipo de mensagem do usuário"""
    text = text.lower().strip()
    
    # Saudações comuns
    greetings = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'ei']
    if any(text.startswith(g) for g in greetings) and len(text.split()) <= 3:
        return "greeting"
        
    # Perguntas sobre funcionalidades
    help_patterns = ['como', 'ajuda', 'pode me ajudar', 'o que você faz', 'quais são']
    if any(p in text for p in help_patterns):
        return "help"
        
    # Busca por receitas
    recipe_patterns = ['receita', 'como fazer', 'tem alguma', 'quero fazer', 'sabe fazer']
    if any(p in text for p in recipe_patterns):
        return "recipe_search"
        
    # Padrão: assume que é uma busca por receita
    return "recipe_search"

def gerar_receita(client: OpenAI, prompt: str) -> Optional[Dict]:
    """Gera uma nova receita usando a API da OpenAI"""
    try:
        # Prepara o contexto para a IA
        messages = prepare_ai_context(prompt)
        
        # Faz a chamada à API
        response = call_openai_api(client, messages)
        
        try:
            # Limpa a resposta da API
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]  # Remove ```json
            if response.endswith("```"):
                response = response[:-3]  # Remove ```
            response = response.strip()
            
            # Converte a resposta para dict
            receita_dict = json.loads(response)
            
            # Valida campos obrigatórios
            campos_obrigatorios = ['titulo', 'ingredientes', 'modo_preparo']
            campos_faltantes = [campo for campo in campos_obrigatorios if campo not in receita_dict]
            
            if campos_faltantes:
                logger.error(f"Receita gerada não contém os campos obrigatórios: {', '.join(campos_faltantes)}")
                logger.error(f"Resposta da API: {response}")
                return None
                
            # Valida tipos de dados
            if not isinstance(receita_dict['ingredientes'], list):
                logger.error("Campo 'ingredientes' não é uma lista")
                return None
                
            if not isinstance(receita_dict['modo_preparo'], list):
                logger.error("Campo 'modo_preparo' não é uma lista")
                return None
                
            # Valida conteúdo mínimo
            if not receita_dict['ingredientes']:
                logger.error("Lista de ingredientes está vazia")
                return None
                
            if not receita_dict['modo_preparo']:
                logger.error("Modo de preparo está vazio")
                return None
                
            return receita_dict
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar resposta da API: {str(e)}")
            logger.error(f"Resposta da API: {response}")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao gerar receita: {str(e)}")
        return None

def process_user_input(client, db):
    """Processa a entrada do usuário e retorna uma resposta"""
    try:
        # Obtém a mensagem do usuário
        prompt = st.session_state.user_input
        if not prompt:
            return
            
        # Limpa o input após processar
        st.session_state.user_input = ""
        
        # Adiciona a mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Classifica o tipo de mensagem
        msg_type = classify_message(prompt)
        
        if msg_type == "greeting":
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Olá! 👋 Sou a Chef Michelle, especialista em gastronomia funcional. Como posso ajudar você hoje? Posso sugerir receitas saudáveis e deliciosas, dar dicas de substituições de ingredientes ou criar novas receitas personalizadas para você! 🌟"
            })
            return
            
        if msg_type == "help":
            st.session_state.messages.append({
                "role": "assistant",
                "content": """Posso ajudar você de várias formas! 👩‍🍳

- Buscar receitas específicas
- Sugerir receitas com os ingredientes que você tem
- Criar novas receitas funcionais
- Dar dicas de substituições de ingredientes
- Explicar benefícios nutricionais
- Sugerir harmonizações

Basta me dizer o que você precisa! 🌟"""
            })
            return
        
        # Extrai termos de busca
        termos_busca = extract_search_terms(prompt)
        
        # Busca receitas relacionadas
        receitas = db.buscar_receitas_por_texto(termos_busca)
        
        if receitas:
            # Encontrou receitas - mostra os resultados
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Encontrei {len(receitas)} {'receita' if len(receitas) == 1 else 'receitas'} que podem te ajudar! 🎉"
            })
            
            # Renderiza cada receita encontrada
            for receita in receitas:
                render_recipe_preview(receita)
                
        else:
            # Não encontrou receitas - gera uma nova
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Não encontrei nenhuma receita com esses ingredientes, mas posso criar uma nova receita para você! 👩‍🍳 Aguarde um momento..."
            })
            
            # Faz a chamada à API
            response = call_openai_api(client, prepare_ai_context(prompt))
            
            # Adiciona a resposta ao histórico
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })
                
    except Exception as e:
        st.error(f"Erro ao processar mensagem: {str(e)}")
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        
    # Atualiza a interface
    render_message_history()

def generate_new_recipe(client: OpenAI, prompt: str, db: DatabaseInterface) -> str:
    """Gera uma nova receita usando a API da OpenAI"""
    try:
        messages = prepare_ai_context(prompt)
        response = call_openai_api(client, messages)
        
        try:
            # Converte a resposta para dict para salvar no banco
            receita_dict = json.loads(response)
            if db.adicionar_receita(receita_dict):
                st.success("Receita salva no banco de dados!")
            
            # Formata a resposta em linguagem natural
            resposta = "Criei uma receita especial para você!\n\n"
            resposta += f"O {receita_dict['titulo'].lower()} é uma ótima opção! "
            if receita_dict.get('descricao'):
                resposta += f"{receita_dict['descricao']}\n\n"
            
            if receita_dict.get('beneficios_funcionais'):
                resposta += "Esta receita traz os seguintes benefícios:\n"
                for b in receita_dict['beneficios_funcionais']:
                    resposta += f"• {b}\n"
                resposta += "\n"
            
            resposta += "Você vai precisar dos seguintes ingredientes:\n"
            for ing in receita_dict.get('ingredientes', []):
                resposta += f"• {ing}\n"
            
            resposta += "\nModo de preparo:\n"
            for i, step in enumerate(receita_dict.get('modo_preparo', []), 1):
                resposta += f"{i}. {step}\n"
            
            resposta += f"\n⏰ Tempo de preparo: {receita_dict.get('tempo_preparo', 'N/A')}"
            resposta += f"\n🍽️ Rende: {receita_dict.get('porcoes', 'N/A')}"
            resposta += f"\n📊 Dificuldade: {receita_dict.get('dificuldade', 'N/A')}\n"
            
            if receita_dict.get('dicas'):
                resposta += "\nDicas importantes:\n"
                for dica in receita_dict['dicas']:
                    resposta += f"• {dica}\n"
            
            if receita_dict.get('harmonizacao'):
                resposta += f"\nDica de harmonização: {receita_dict['harmonizacao']}"
            
            return resposta
            
        except json.JSONDecodeError:
            st.error("Não foi possível salvar a receita no banco de dados.")
            # Retorna a resposta em formato natural mesmo se falhar ao salvar
            return "Desculpe, tive um problema ao salvar a receita, mas aqui está ela em formato texto:\n\n" + response
            
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
    1. Um título criativo que destaque o aspecto funcional
    2. Uma breve descrição dos benefícios e características
    3. Lista de ingredientes com quantidades precisas
    4. Modo de preparo detalhado e passo a passo
    5. Tempo de preparo e rendimento
    6. Dicas de substituições e variações
    7. Informações nutricionais relevantes
    8. Sugestões de harmonização e consumo

    Formate a resposta de forma natural e amigável, como se estivesse conversando diretamente com a pessoa. Use emojis para tornar a comunicação mais acolhedora.

    Exemplo de formato:
    ✨ [Nome da Receita] ✨

    [Breve descrição dos benefícios e características]

    🌿 Benefícios Principais:
    • [Lista de benefícios]

    📝 Ingredientes:
    • [Lista com quantidades]

    👩‍🍳 Modo de Preparo:
    1. [Passos detalhados]

    ⏱️ Tempo de Preparo: [tempo]
    🍽️ Rendimento: [porções]
    📊 Dificuldade: [nível]

    📊 Informações Nutricionais (por porção):
    • Calorias: [valor]
    • Proteínas: [valor]
    • Carboidratos: [valor]
    • Gorduras: [valor]
    • Fibras: [valor]

    💡 Dicas:
    • [Lista de dicas e substituições]

    🍷 Harmonização:
    [Sugestões de consumo e acompanhamentos]
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
            max_tokens=2500,
            top_p=0.95,
            frequency_penalty=0.3,
            presence_penalty=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Erro detalhado na chamada da API: {str(e)}")
        raise Exception(f"Erro na chamada da API: {str(e)}")

def init_app(db: DatabaseInterface) -> None:
    st.session_state.db = db

def get_database() -> DatabaseInterface:
    db_type = st.secrets.get("DATABASE_TYPE", "supabase")
    if db_type == "sqlite":
        from database import SQLiteDB
        return SQLiteDB()
    return SupabaseDB()  # Usando o alias SupabaseDB

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
    db = get_database()
    
    # Inicializa o estado da sessão
    init_session_state()
    
    # Layout principal
    st.title("👩‍🍳 Chef Virtual - Receitas da Michelle")
    st.write("Olá! Sou a Chef Michelle, especialista em gastronomia funcional. Como posso ajudar você hoje?")
    st.write("Você pode:")
    st.write("- Pedir uma receita específica")
    st.write("- Informar os ingredientes que tem disponível")
    st.write("- Perguntar sobre substituições e dicas")
    
    # Renderiza o histórico de mensagens
    render_message_history()
    
    # Campo de entrada do usuário
    st.text_input("Digite sua mensagem:", key="user_input", on_change=lambda: process_user_input(client, db))
    
    # Área de busca (colapsada por padrão)
    with st.expander("🔍 Buscar no banco de receitas"):
        busca = st.text_input("Digite sua busca:", key="busca")
        
        if busca:
            # Usa o método direto de busca
            receitas = db.buscar_receitas(busca)
            if receitas:
                st.write(f"Encontradas {len(receitas)} receitas!")
                for receita in receitas:
                    render_recipe_preview(receita)
            else:
                st.info("Nenhuma receita encontrada. Que tal me perguntar diretamente?")
    
    # Botão para exportar histórico
    if st.session_state.messages:
        export_history()

if __name__ == "__main__":
    main()
