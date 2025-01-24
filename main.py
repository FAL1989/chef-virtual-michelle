import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
from database_supabase import ReceitasDB as SupabaseDB
from database_interface import DatabaseInterface
import json
from datetime import datetime
import httpx
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

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

def render_recipe_preview(receita: Dict):
    """Renderiza um preview da receita com botão para ver completa"""
    try:
        # Verifica se a receita tem ID
        receita_id = receita.get('id')
        if not receita_id:
            st.warning("Receita sem ID encontrada")
            return
        
        # Cria uma coluna para o preview
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {receita['titulo']}")
            if receita.get('descricao'):
                st.markdown(receita['descricao'])
            
            # Mostra os ingredientes principais
            st.markdown("**Ingredientes principais:**")
            ingredientes = receita.get('ingredientes', [])
            for ing in ingredientes[:5]:  # Mostra só os 5 primeiros
                st.markdown(f"• {ing}")
            if len(ingredientes) > 5:
                st.markdown("_(e mais ingredientes...)_")
        
        with col2:
            # Botão para ver a receita completa
            if st.button("Ver receita completa", key=f"btn_{receita_id}"):
                # Instancia o banco de dados
                db = ReceitasDB()
                # Busca a receita completa
                receita_completa = db.buscar_receita_por_id(receita_id)
                
                if receita_completa:
                    st.markdown("---")
                    st.markdown(f"## {receita_completa['titulo']}")
                    
                    if receita_completa.get('descricao'):
                        st.markdown(receita_completa['descricao'])
                    
                    st.markdown("\n### Ingredientes")
                    for ing in receita_completa.get('ingredientes', []):
                        st.markdown(f"• {ing}")
                    
                    if receita_completa.get('modo_preparo'):
                        st.markdown("\n### Modo de Preparo")
                        for i, passo in enumerate(receita_completa['modo_preparo'], 1):
                            st.markdown(f"{i}. {passo}")
                    
                    if receita_completa.get('tempo_preparo'):
                        st.markdown(f"\n⏱️ **Tempo de preparo:** {receita_completa['tempo_preparo']}")
                    
                    if receita_completa.get('porcoes'):
                        st.markdown(f"🍽️ **Porções:** {receita_completa['porcoes']}")
                    
                    if receita_completa.get('dificuldade'):
                        st.markdown(f"📊 **Dificuldade:** {receita_completa['dificuldade']}")
                    
                    if receita_completa.get('dicas'):
                        st.markdown("\n### Dicas")
                        for dica in receita_completa['dicas']:
                            st.markdown(f"• {dica}")
                    
                    if receita_completa.get('harmonizacao'):
                        st.markdown(f"\n### Harmonização")
                        st.markdown(receita_completa['harmonizacao'])
                else:
                    st.error("Não foi possível carregar a receita completa")
    except Exception as e:
        st.error(f"Erro ao renderizar preview: {str(e)}")
        logger.error(f"Erro ao renderizar preview: {str(e)}")

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

def process_user_input(client: OpenAI, db: DatabaseInterface):
    """Processa a entrada do usuário e retorna uma resposta"""
    try:
        # Obtém a mensagem do usuário
        prompt = st.session_state.user_input
        
        # Limpa a entrada
        st.session_state.user_input = ""
        
        # Adiciona a mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Busca receitas relacionadas
        receitas = db.buscar_receitas_por_texto(prompt)
        
        if receitas:
            # Formata a resposta em linguagem natural
            resposta = "Encontrei algumas receitas que podem te ajudar!\n\n"
            
            for receita in receitas:
                resposta += f"**{receita['titulo']}**\n"
                if receita.get('descricao'):
                    resposta += f"{receita['descricao']}\n\n"
                
                # Mostra apenas os 5 primeiros ingredientes
                resposta += "**Ingredientes principais:**\n"
                ingredientes = receita.get('ingredientes', [])
                for ing in ingredientes[:5]:
                    resposta += f"• {ing}\n"
                if len(ingredientes) > 5:
                    resposta += "_(e mais ingredientes...)_\n"
                
                # Tempo de preparo e porções se disponível
                if receita.get('tempo_preparo'):
                    resposta += f"\n⏱️ **Tempo de preparo:** {receita['tempo_preparo']}"
                if receita.get('porcoes'):
                    resposta += f"\n🍽️ **Porções:** {receita['porcoes']}"
                if receita.get('dificuldade'):
                    resposta += f"\n📊 **Dificuldade:** {receita['dificuldade']}"
                
                resposta += "\n\n_Clique em 'Ver receita completa' para mais detalhes!_\n\n---\n\n"
            
            # Adiciona a resposta ao histórico
            st.session_state.messages.append({"role": "assistant", "content": resposta})
            
            # Mostra os previews das receitas encontradas
            for receita in receitas:
                render_recipe_preview(receita)
                st.divider()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Não encontrei receitas existentes com esses ingredientes. Vou criar uma nova receita para você!"})
            nova_receita = generate_new_recipe(client, prompt, db)
            if nova_receita:
                try:
                    # Tenta converter para dict se for string JSON
                    if isinstance(nova_receita, str):
                        receita_dict = json.loads(nova_receita)
                    else:
                        receita_dict = nova_receita
                    
                    # Salva no banco
                    if db.adicionar_receita(receita_dict):
                        st.success("Receita salva no banco de dados!")
                        
                        # Formata a resposta em linguagem natural
                        resposta = f"Criei uma receita especial de {receita_dict['titulo'].lower()} para você!\n\n"
                        if receita_dict.get('descricao'):
                            resposta += f"{receita_dict['descricao']}\n\n"
                        
                        resposta += "**Ingredientes necessários:**\n"
                        for ing in receita_dict.get('ingredientes', []):
                            resposta += f"• {ing}\n"
                        
                        resposta += "\n**Modo de preparo:**\n"
                        for i, step in enumerate(receita_dict.get('modo_preparo', []), 1):
                            resposta += f"{i}. {step}\n"
                        
                        if receita_dict.get('dicas'):
                            resposta += "\n**Dicas:**\n"
                            for dica in receita_dict['dicas']:
                                resposta += f"• {dica}\n"
                        
                        if receita_dict.get('harmonizacao'):
                            resposta += f"\n**Harmonização:** {receita_dict['harmonizacao']}"
                        
                        st.session_state.messages.append({"role": "assistant", "content": resposta})
                        
                        # Mostra o preview da nova receita
                        render_recipe_preview(receita_dict)
                    else:
                        st.error("Erro ao salvar a receita no banco de dados")
                except Exception as e:
                    st.error(f"Erro ao processar nova receita: {str(e)}")
                    logger.error(f"Erro ao processar nova receita: {str(e)}")
    except Exception as e:
        st.error(f"Erro ao processar entrada: {str(e)}")
        logger.error(f"Erro ao processar entrada: {str(e)}")

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
    
    # Processa a entrada do usuário
    process_user_input(client, db)
    
    # Área de busca (colapsada por padrão)
    with st.expander("🔍 Buscar no banco de receitas"):
        busca = st.text_input("Digite sua busca:", key="busca")
        
        if busca:
            # Usa o método direto de busca
            receitas = db.buscar_receitas(busca)  # Removido o _cached
            if receitas:
                st.write(f"Encontradas {len(receitas)} receitas!")
                for receita in receitas:
                    render_recipe_preview(receita)
            else:
                st.info("Nenhuma receita encontrada. Que tal me perguntar diretamente?")

    # DEBUG: Teste de busca
    if st.button("Testar Busca"):
        try:
            db = get_database()
            resultados = db.buscar_receitas("bolo")
            st.write("Resultados do teste:", len(resultados))
            for r in resultados:
                st.write("Título:", r.get('titulo'))
        except Exception as e:
            st.error(f"Erro no teste: {str(e)}")

if __name__ == "__main__":
    main()
