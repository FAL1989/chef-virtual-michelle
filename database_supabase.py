from typing import Dict, List, Optional, Union
import json
import logging
from datetime import datetime
from supabase import create_client, Client
import streamlit as st
import os
from tenacity import retry, stop_after_attempt, wait_exponential
from database_interface import DatabaseInterface

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """Normaliza um texto para busca"""
    if not text:
        return ""
    return text.strip().lower()

def clean_search_query(query: str) -> str:
    """Limpa a query de busca, removendo palavras comuns e mantendo apenas termos relevantes"""
    # Palavras para remover
    stop_words = {
        'o', 'que', 'os', 'as', 'um', 'uns', 'uma', 'umas', 'com', 'para',
        'por', 'em', 'no', 'na', 'nos', 'nas', 'do', 'da', 'dos', 'das',
        'posso', 'pode', 'fazer', 'como', 'onde', 'quando', 'qual', 'quais',
        'aonde', 'porque', 'por que', 'usar', 'uso', 'de', 'e', 'ou', 'mas',
        'porem', 'entao', 'assim', 'pois'
    }
    
    # Remove pontuação
    query = ''.join(c for c in query if c.isalnum() or c.isspace())
    
    # Normaliza e divide em palavras
    words = normalize_text(query).split()
    
    # Remove stop words
    cleaned_words = [word for word in words if word not in stop_words]
    
    # Se ficou vazio após limpeza, retorna a query original normalizada
    if not cleaned_words:
        return normalize_text(query)
    
    return ' '.join(cleaned_words)

def format_recipe_output(recipe: Dict) -> str:
    """Formata a receita para exibição amigável"""
    output = []
    
    # Título e descrição
    output.append(f"# {recipe['titulo']}")
    if recipe.get('descricao'):
        output.append(f"\n{recipe['descricao']}\n")
    
    # Informações básicas
    if recipe.get('tempo_preparo'):
        output.append(f"⏰ Tempo de Preparo: {recipe['tempo_preparo']}")
    if recipe.get('porcoes'):
        output.append(f"🍽️ Porções: {recipe['porcoes']}")
    if recipe.get('dificuldade'):
        output.append(f"📊 Dificuldade: {recipe['dificuldade']}\n")
    
    # Ingredientes
    if recipe.get('ingredientes'):
        output.append("## Ingredientes:")
        for ing in recipe['ingredientes']:
            output.append(f"• {ing}")
        output.append("")
    
    # Modo de preparo
    if recipe.get('modo_preparo'):
        output.append("## Modo de Preparo:")
        for i, step in enumerate(recipe['modo_preparo'], 1):
            output.append(f"{i}. {step}")
        output.append("")
    
    # Informações nutricionais
    info_nutri = recipe.get('informacoes_nutricionais', {})
    if any(info_nutri.values()):
        output.append("## Informações Nutricionais:")
        for key, value in info_nutri.items():
            if value:
                output.append(f"• {key.title()}: {value}")
        output.append("")
    
    # Benefícios funcionais
    if recipe.get('beneficios_funcionais'):
        output.append("## Benefícios Funcionais:")
        for b in recipe['beneficios_funcionais']:
            output.append(f"• {b}")
        output.append("")
    
    # Dicas
    if recipe.get('dicas'):
        output.append("## Dicas:")
        for d in recipe['dicas']:
            output.append(f"• {d}")
        output.append("")
    
    # Harmonização
    if recipe.get('harmonizacao'):
        output.append(f"## Harmonização:\n{recipe['harmonizacao']}")
    
    return "\n".join(output)

class DatabaseError(Exception):
    """Exceção customizada para erros do banco de dados"""
    pass

class ReceitasDB(DatabaseInterface):
    def __init__(self):
        """Inicializa a conexão com o Supabase"""
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
            self.supabase: Client = create_client(url, key)
            logger.info("Conexão estabelecida com Supabase")
            self.criar_tabelas()
        except Exception as e:
            logger.error(f"Erro ao conectar com Supabase: {e}")
            raise

    def criar_tabelas(self):
        """
        Verifica se as tabelas existem.
        No Supabase, as tabelas devem ser criadas manualmente ou via migrations.
        Este método serve apenas para documentação da estrutura.
        """
        """
        Estrutura das tabelas no Supabase:

        -- Tabela de receitas
        create table receitas (
            id uuid default uuid_generate_v4() primary key,
            titulo text not null,
            descricao text,
            utensilios text,
            ingredientes text,
            modo_preparo text,
            tempo_preparo text,
            porcoes text,
            dificuldade text,
            harmonizacao text,
            informacoes_nutricionais jsonb default '{}'::jsonb,
            beneficios_funcionais jsonb default '[]'::jsonb,
            dicas jsonb default '[]'::jsonb,
            created_at timestamp with time zone default timezone('utc'::text, now())
        );

        -- Tabela de dicas
        create table dicas (
            id bigint generated by default as identity primary key,
            receita_id bigint references receitas(id),
            dica text not null,
            created_at timestamp with time zone default timezone('utc'::text, now()) not null
        );

        -- Tabela de benefícios funcionais
        create table beneficios_funcionais (
            id bigint generated by default as identity primary key,
            receita_id bigint references receitas(id),
            beneficio text not null,
            created_at timestamp with time zone default timezone('utc'::text, now()) not null
        );

        -- Trigger para atualizar updated_at
        create or replace function update_updated_at_column()
        returns trigger as $$
        begin
            new.updated_at = now();
            return new;
        end;
        $$ language plpgsql;

        create trigger update_receitas_updated_at
            before update on receitas
            for each row
            execute function update_updated_at_column();

        -- Índices para busca em texto
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        
        -- Índices GIN para campos de texto
        CREATE INDEX IF NOT EXISTS idx_receitas_titulo_gin ON receitas USING gin (titulo gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS idx_receitas_ingredientes_gin ON receitas USING gin (ingredientes gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS idx_receitas_descricao_gin ON receitas USING gin (descricao gin_trgm_ops);
        
        -- Índices GIN para campos JSONB
        CREATE INDEX IF NOT EXISTS idx_receitas_info_nutri ON receitas USING gin (informacoes_nutricionais);
        CREATE INDEX IF NOT EXISTS idx_receitas_beneficios ON receitas USING gin (beneficios_funcionais);
        CREATE INDEX IF NOT EXISTS idx_receitas_dicas ON receitas USING gin (dicas);
        """
        pass

    def _converter_formato_db(self, receita_db: Dict) -> Optional[Dict]:
        """Converte o formato do banco para o formato da aplicação"""
        return ReceitaAdapter.to_chat_format(receita_db)

    def adicionar_receita(self, receita: Dict) -> bool:
        """Adiciona uma nova receita ao banco de dados"""
        try:
            # Converte para o formato do banco
            receita_db = ReceitaAdapter.to_db_format(receita)
            if not receita_db:
                return False
            
            # Insere no banco
            data = self.supabase.table('receitas').insert(receita_db).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar receita: {e}")
            return False

    def verificar_estrutura(self):
        """Verifica a estrutura atual dos dados no Supabase"""
        try:
            # Busca uma receita qualquer
            data = self.supabase.table('receitas').select('*').limit(1).execute()
            
            if data and data.data:
                receita = data.data[0]
                st.write("DEBUG - Estrutura da receita:")
                st.write("Tipo de dados por campo:")
                for campo, valor in receita.items():
                    st.write(f"{campo}: {type(valor)}")
                st.write("\nValores:")
                st.write(receita)
            else:
                st.warning("Nenhuma receita encontrada")
                
        except Exception as e:
            st.error(f"Erro ao verificar estrutura: {str(e)}")
            
    def limpar_banco(self) -> bool:
        """Limpa todas as receitas do banco de dados"""
        try:
            # Deleta todas as receitas usando um filtro que sempre é verdadeiro
            self.supabase.table('receitas').delete().gte('created_at', '2000-01-01').execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar banco: {e}")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def buscar_receitas(self, query: str = "") -> list:
        """Busca receitas no banco de dados"""
        try:
            if not query:
                data = self.supabase.table("receitas").select("*").execute()
            else:
                # Busca usando match parcial no título (case insensitive)
                data = (self.supabase.table("receitas")
                       .select("*")
                       .ilike("titulo", f"%{query.strip().upper()}%")  # Busca parcial em maiúsculo
                       .execute())

            # Converte para o formato do chat e filtra valores None
            receitas = [ReceitaAdapter.to_chat_format(r) for r in data.data if r]
            receitas = [r for r in receitas if r]  # Remove None values
            
            logger.info(f"Encontradas {len(receitas)} receitas")
            return receitas

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []

    def buscar_receitas_por_texto(self, query: str) -> List[Dict]:
        """Busca receitas por texto livre (usado no chat)"""
        try:
            if not query:
                return []
            
            # Limpa e normaliza a query
            query = clean_search_query(query)
            logger.info(f"Buscando receitas com query: {query}")
            
            # Busca usando a sintaxe correta do Supabase
            data = (self.supabase.table('receitas')
                   .select('*')
                   .ilike('titulo', f'%{query}%')
                   .execute())
            
            # Se não encontrou por título, tenta por ingredientes
            if not data.data:
                data = (self.supabase.table('receitas')
                       .select('*')
                       .ilike('ingredientes', f'%{query}%')
                       .execute())
            
            # Converte para o formato do chat
            receitas = [ReceitaAdapter.to_chat_format(r) for r in data.data if r]
            receitas = [r for r in receitas if r]  # Remove None values
            
            logger.info(f"Encontradas {len(receitas)} receitas")
            return receitas
            
        except Exception as e:
            logger.error(f"Erro na busca: {str(e)}")
            st.error(f"Erro ao buscar receitas: {str(e)}")
            return []

    def _criar_resumo_receita(self, receita: Dict) -> Optional[Dict]:
        """Cria um resumo da receita com apenas as informações essenciais"""
        try:
            st.write("DEBUG - Criando resumo para receita:", receita)
            
            # Extrai e valida o ID
            receita_id = receita.get('id')
            st.write("DEBUG - ID original:", receita_id, "Tipo:", type(receita_id))
            
            # Validação do ID
            if not receita_id:  # Verifica se é None ou vazio
                st.warning("Receita sem ID encontrada")
                return None
            
            # Mantém o ID no formato original
            receita_id = str(receita_id).strip()
            st.write("DEBUG - ID validado:", receita_id)

            # Validação do título
            titulo = str(receita.get('titulo', '')).strip().upper()
            if not titulo:
                st.warning(f"Receita {receita_id} sem título encontrada")
                return None

            # Extrai os ingredientes para preview
            ingredientes_raw = receita.get('ingredientes', '')
            st.write(f"DEBUG - Ingredientes raw da receita {receita_id}:", ingredientes_raw)
            
            if isinstance(ingredientes_raw, str):
                ingredientes = [ing.strip() for ing in ingredientes_raw.split('\n') if ing.strip()][:3]
                if len(ingredientes_raw.split('\n')) > 3:
                    ingredientes.append('...')
            else:
                ingredientes = []
            
            st.write(f"DEBUG - Ingredientes processados da receita {receita_id}:", ingredientes)

            resumo = {
                'id': receita_id,
                'titulo': titulo,
                'descricao': str(receita.get('descricao', '')).strip(),
                'preview_ingredientes': ingredientes
            }
            
            st.write(f"DEBUG - Resumo final da receita {receita_id}:", resumo)
            return resumo
            
        except Exception as e:
            st.error(f"Erro ao criar resumo da receita: {str(e)}")
            st.write("DEBUG - Stack trace completo:", str(e))
            return None

    def buscar_receita_por_id(self, receita_id: str) -> Optional[Dict]:
        """Busca uma receita específica pelo ID (UUID)"""
        try:
            st.write("DEBUG - Iniciando busca por ID:", receita_id)
            
            # Faz a busca no Supabase usando o ID como string
            data = self.supabase.table('receitas').select('*').eq('id', receita_id).execute()
            
            st.write("DEBUG - Resposta do Supabase:", data.data)
            
            if not data.data:
                st.warning(f"Receita não encontrada: {receita_id}")
                return None
            
            # Converte para o formato do chat
            receita = self._converter_formato_db(data.data[0])
            
            # Debug para verificar a conversão
            st.write("DEBUG - Dados convertidos:", receita)
            
            return receita
                
        except Exception as e:
            st.error(f"Erro ao buscar receita: {str(e)}")
            st.write("DEBUG - Stack trace completo:", str(e))
            return None

    @staticmethod
    @st.cache_data(ttl=3600)
    def buscar_receitas_cached(query: str) -> List[Dict]:
        """Versão cacheada da busca de receitas"""
        try:
            db = ReceitasDB()
            return db.buscar_receitas(query)
        except Exception as e:
            logger.error(f"Erro na busca cacheada: {str(e)}")
            return []

    def exportar_receitas(self) -> List[Dict]:
        """Exporta todas as receitas do banco de dados"""
        try:
            data = self.supabase.table('receitas').select('*').execute()
            return [ReceitaAdapter.to_chat_format(receita) for receita in data.data]
        except Exception as e:
            logger.error(f"Erro ao exportar receitas: {e}")
            return []

    @staticmethod
    @st.cache_data(ttl=3600)
    def exportar_receitas_cached() -> List[Dict]:
        """Exporta todas as receitas do banco de dados com cache"""
        try:
            # Cria uma nova instância para cada exportação
            db = ReceitasDB()
            return db.exportar_receitas()
        except Exception as e:
            logger.error(f"Erro ao exportar receitas: {e}")
            return []

class ReceitaAdapter:
    """Adaptador para converter entre o formato rico do chat e o formato simples do banco"""
    
    @staticmethod
    def to_db_format(receita_chat: Dict) -> Dict:
        """Converte do formato rico do chat para o formato do banco"""
        try:
            # Converte arrays para strings com quebras de linha
            ingredientes = '\n'.join(receita_chat.get('ingredientes', [])) if isinstance(receita_chat.get('ingredientes'), list) else str(receita_chat.get('ingredientes', ''))
            modo_preparo = '\n'.join(receita_chat.get('modo_preparo', [])) if isinstance(receita_chat.get('modo_preparo'), list) else str(receita_chat.get('modo_preparo', ''))
            
            # Garante que informações nutricionais tenham a estrutura correta
            info_nutri = receita_chat.get('informacoes_nutricionais', {})
            if not isinstance(info_nutri, dict):
                info_nutri = {
                    'calorias': 0.0,
                    'proteinas': 0.0,
                    'carboidratos': 0.0,
                    'gorduras': 0.0,
                    'fibras': 0.0
                }
            
            # Garante que arrays sejam sempre listas
            beneficios = receita_chat.get('beneficios_funcionais', [])
            if not isinstance(beneficios, list):
                beneficios = []
                
            dicas = receita_chat.get('dicas', [])
            if not isinstance(dicas, list):
                dicas = []
            
            return {
                'titulo': str(receita_chat.get('titulo', '')).strip().upper(),
                'descricao': str(receita_chat.get('descricao', '')).strip(),
                'ingredientes': ingredientes.strip(),
                'modo_preparo': modo_preparo.strip(),
                'tempo_preparo': str(receita_chat.get('tempo_preparo', '')).strip(),
                'porcoes': str(receita_chat.get('porcoes', '')).strip(),
                'dificuldade': str(receita_chat.get('dificuldade', '')).strip(),
                'utensilios': str(receita_chat.get('utensilios', '')).strip(),
                'harmonizacao': str(receita_chat.get('harmonizacao', '')).strip(),
                'informacoes_nutricionais': info_nutri,
                'beneficios_funcionais': beneficios,
                'dicas': dicas
            }
        except Exception as e:
            st.error(f"Erro ao converter para formato DB: {str(e)}")
            return {}

    @staticmethod
    def to_chat_format(receita_db: Dict) -> Dict:
        """Converte do formato do banco para o formato rico do chat"""
        try:
            # Garante que o ID seja mantido
            receita_id = str(receita_db.get('id', '')).strip()
            if not receita_id:
                logger.warning("Receita sem ID encontrada")
                return None

            # Limpa e normaliza ingredientes
            ingredientes_raw = receita_db.get('ingredientes', '')
            if isinstance(ingredientes_raw, str):
                # Remove duplicatas e linhas vazias
                ingredientes = [ing.strip() for ing in ingredientes_raw.split('\n') if ing.strip()]
                # Remove duplicatas mantendo a ordem
                ingredientes = list(dict.fromkeys(ingredientes))
            else:
                ingredientes = []
            
            # Limpa e normaliza modo de preparo
            preparo_raw = receita_db.get('modo_preparo', '')
            if isinstance(preparo_raw, str):
                # Remove duplicatas e linhas vazias
                preparo = [step.strip() for step in preparo_raw.split('\n') if step.strip()]
                # Remove duplicatas mantendo a ordem
                preparo = list(dict.fromkeys(preparo))
            else:
                preparo = []

            return {
                'id': receita_id,  # Mantém o ID na conversão
                'titulo': str(receita_db.get('titulo', '')).strip().upper(),
                'descricao': str(receita_db.get('descricao', '')).strip(),
                'ingredientes': ingredientes,
                'modo_preparo': preparo,
                'tempo_preparo': str(receita_db.get('tempo_preparo', '')).strip(),
                'porcoes': str(receita_db.get('porcoes', '')).strip(),
                'dificuldade': str(receita_db.get('dificuldade', '')).strip(),
                'informacoes_nutricionais': receita_db.get('informacoes_nutricionais', {}),
                'dicas': receita_db.get('dicas', []),
                'harmonizacao': str(receita_db.get('harmonizacao', '')).strip()
            }
        except Exception as e:
            logger.error(f"Erro ao converter para formato chat: {str(e)}")
            return None

# Opcional: criar um alias para manter consistência
SupabaseDB = ReceitasDB 