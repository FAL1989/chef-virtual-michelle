from typing import Dict, List, Optional, Union
import json
import logging
from datetime import datetime
from supabase import create_client, Client
import streamlit as st
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Exceção customizada para erros do banco de dados"""
    pass

class ReceitasDB:
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
            id bigint generated by default as identity primary key,
            titulo text not null,
            descricao text,
            utensilios text,
            ingredientes text,
            modo_preparo text,
            tempo_preparo text,
            porcoes integer,
            dificuldade text,
            harmonizacao text,
            calorias text,
            proteinas text,
            carboidratos text,
            gorduras text,
            fibras text,
            created_at timestamp with time zone default timezone('utc'::text, now()) not null,
            updated_at timestamp with time zone default timezone('utc'::text, now()) not null
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

    def buscar_receitas(self, query: str = None) -> List[Dict]:
        """Busca receitas no banco de dados por título ou ingredientes"""
        try:
            if not query:
                data = self.supabase.table('receitas').select('*').execute()
                st.write("DEBUG - Dados retornados (sem query):", data.data)
                # Filtra apenas os resumos válidos (não None)
                return [resumo for resumo in (self._criar_resumo_receita(receita) for receita in data.data) if resumo is not None]

            # Limpa e normaliza a query
            query = query.strip().lower()
            st.write("DEBUG - Query normalizada:", query)
            
            # Busca usando filter com ilike no título
            data = self.supabase.table('receitas').select('*').filter('titulo', 'ilike', f'%{query}%').execute()
            st.write("DEBUG - Dados retornados (busca por título):", data.data)
            
            # Se não encontrou no título, tenta nos ingredientes
            if not data.data:
                data = self.supabase.table('receitas').select('*').filter('ingredientes', 'ilike', f'%{query}%').execute()
                st.write("DEBUG - Dados retornados (busca por ingredientes):", data.data)
            
            if not data.data:
                st.info("Nenhuma receita encontrada.")
                return []
            
            # Cria resumo das receitas encontradas e filtra os inválidos
            receitas = []
            for receita in data.data:
                resumo = self._criar_resumo_receita(receita)
                if resumo is not None:  # Só adiciona se o resumo for válido
                    receitas.append(resumo)
            
            st.write("DEBUG - Resumos válidos criados:", receitas)
            return receitas
                
        except Exception as e:
            st.error(f"Erro ao buscar receitas: {str(e)}")
            return []

    def _criar_resumo_receita(self, receita: Dict) -> Dict:
        """Cria um resumo da receita com apenas as informações essenciais"""
        try:
            # Debug do objeto receita completo
            st.write("DEBUG - Receita completa recebida:", receita)
            
            # Extrai e valida o ID
            receita_id = receita.get('id')
            st.write("DEBUG - ID original:", receita_id, "Tipo:", type(receita_id))
            
            # Validação mais rigorosa do ID
            if receita_id is None:
                st.warning("Receita sem ID encontrada")
                return None  # Não cria resumo para receitas sem ID
            
            try:
                # Tenta converter para inteiro para validar
                receita_id = int(receita_id)
                st.write("DEBUG - ID validado:", receita_id)
            except (ValueError, TypeError):
                st.error(f"ID inválido encontrado: {receita_id}")
                return None  # Não cria resumo para receitas com ID inválido

            # Validação do título
            titulo = str(receita.get('titulo', '')).strip().upper()
            if not titulo:
                st.warning("Receita sem título encontrada")
                return None

            # Extrai os ingredientes para preview
            ingredientes_raw = receita.get('ingredientes', '')
            st.write("DEBUG - Ingredientes raw:", ingredientes_raw)
            
            if isinstance(ingredientes_raw, str):
                ingredientes = [ing.strip() for ing in ingredientes_raw.split('\n') if ing.strip()][:3]
                if len(ingredientes_raw.split('\n')) > 3:
                    ingredientes.append('...')
            else:
                ingredientes = []
            
            st.write("DEBUG - Ingredientes processados:", ingredientes)

            resumo = {
                'id': receita_id,  # Mantém como inteiro
                'titulo': titulo,
                'descricao': str(receita.get('descricao', '')).strip(),
                'preview_ingredientes': ingredientes
            }
            
            st.write("DEBUG - Resumo final:", resumo)
            return resumo
            
        except Exception as e:
            st.error(f"Erro ao criar resumo da receita: {str(e)}")
            return None  # Retorna None em vez de um objeto de erro

    def buscar_receita_por_id(self, receita_id: Union[str, int]) -> Optional[Dict]:
        """Busca uma receita específica pelo ID"""
        try:
            st.write("DEBUG - Iniciando busca por ID:", receita_id, "Tipo:", type(receita_id))
            
            # Garante que o ID seja um inteiro
            if isinstance(receita_id, str):
                receita_id = int(receita_id)
            
            st.write("DEBUG - ID convertido:", receita_id, "Tipo:", type(receita_id))
            
            # Faz a busca no Supabase
            data = self.supabase.table('receitas').select('*').eq('id', receita_id).execute()
            
            st.write("DEBUG - Resposta do Supabase:", data)
            
            if not data.data:
                st.warning(f"Receita não encontrada: {receita_id}")
                return None
            
            # Debug para verificar os dados retornados
            st.write("DEBUG - Dados brutos:", data.data[0])
            
            # Converte para o formato do chat
            receita = ReceitaAdapter.to_chat_format(data.data[0])
            
            # Debug para verificar a conversão
            st.write("DEBUG - Dados convertidos:", receita)
            
            return receita
                
        except ValueError as e:
            st.error(f"ID inválido: {receita_id} - Erro: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Erro ao buscar receita: {str(e)}")
            st.write("DEBUG - Stack trace completo:", str(e))
            return None

    @staticmethod
    @st.cache_data(ttl=3600)
    def buscar_receitas_cached(query: str = None) -> List[Dict]:
        """Busca receitas no banco de dados com cache"""
        try:
            # Cria uma nova instância para cada busca
            db = ReceitasDB()
            return db.buscar_receitas(query)
        except Exception as e:
            logger.error(f"Erro ao buscar receitas: {e}")
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
            
            # Garante que campos JSONB sejam dicts/lists
            info_nutri = receita_db.get('informacoes_nutricionais', {})
            if isinstance(info_nutri, str):
                try:
                    info_nutri = json.loads(info_nutri)
                except:
                    info_nutri = {
                        'calorias': 0.0,
                        'proteinas': 0.0,
                        'carboidratos': 0.0,
                        'gorduras': 0.0,
                        'fibras': 0.0
                    }
                    
            beneficios = receita_db.get('beneficios_funcionais', [])
            if isinstance(beneficios, str):
                try:
                    beneficios = json.loads(beneficios)
                except:
                    beneficios = []
                    
            dicas = receita_db.get('dicas', [])
            if isinstance(dicas, str):
                try:
                    dicas = json.loads(dicas)
                except:
                    dicas = []
            
            return {
                'titulo': str(receita_db.get('titulo', '')).strip().upper(),
                'descricao': str(receita_db.get('descricao', '')).strip(),
                'ingredientes': ingredientes,
                'modo_preparo': preparo,
                'tempo_preparo': str(receita_db.get('tempo_preparo', '')).strip(),
                'porcoes': str(receita_db.get('porcoes', '')).strip(),
                'dificuldade': str(receita_db.get('dificuldade', '')).strip(),
                'utensilios': str(receita_db.get('utensilios', '')).strip(),
                'harmonizacao': str(receita_db.get('harmonizacao', '')).strip(),
                'informacoes_nutricionais': info_nutri,
                'beneficios_funcionais': beneficios,
                'dicas': dicas
            }
        except Exception as e:
            st.error(f"Erro ao converter para formato chat: {str(e)}")
            return {} 