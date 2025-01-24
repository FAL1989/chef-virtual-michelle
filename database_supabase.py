from typing import Dict, List, Optional, Union
import json
import logging
from datetime import datetime
from supabase import create_client, Client
import streamlit as st
import os
from unidecode import unidecode

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Exceção customizada para erros do banco de dados"""
    pass

class ReceitasDB:
    def __init__(self):
        """Inicializa a conexão com o banco de dados"""
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            
            if not url or not key:
                st.error("⚠️ Erro: Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY não configuradas!")
                st.info("Por favor, configure as variáveis de ambiente no arquivo .env ou nas configurações do Streamlit Cloud.")
                st.stop()
            
            self.supabase = create_client(url, key)
            self._cache = {}
            
        except Exception as e:
            st.error("⚠️ Erro ao conectar com o banco de dados!")
            st.info("Verifique se as credenciais do Supabase estão corretas.")
            st.stop()
    
    def _normalizar_texto(self, texto: str) -> str:
        """Normaliza o texto removendo acentos e convertendo para minúsculo"""
        return unidecode(texto.lower().strip())
    
    def _processar_ingredientes(self, ingredientes_raw: str) -> List[str]:
        """Processa a string de ingredientes em uma lista"""
        if not ingredientes_raw:
            return []
        
        # Divide por quebras de linha e limpa
        ingredientes = [ing.strip() for ing in ingredientes_raw.split('\n') if ing.strip()]
        
        # Limita a 3 ingredientes + reticências para o preview
        if len(ingredientes) > 3:
            return ingredientes[:3] + ["..."]
        return ingredientes
    
    def _criar_resumo_receita(self, receita_db: Dict) -> Optional[Dict]:
        """Cria um resumo da receita para preview"""
        try:
            # Extrai dados básicos
            receita_id = str(receita_db.get('id', '')).strip()
            if not receita_id:
                return None
            
            # Processa ingredientes
            ingredientes_raw = receita_db.get('ingredientes', '')
            preview_ingredientes = self._processar_ingredientes(ingredientes_raw)
            
            # Monta o resumo
            return {
                'id': receita_id,
                'titulo': str(receita_db.get('titulo', '')).strip().upper(),
                'descricao': str(receita_db.get('descricao', '')).strip(),
                'preview_ingredientes': preview_ingredientes
            }
        except Exception:
            return None
    
    def buscar_receitas_cached(self, query: str) -> List[Dict]:
        """Busca receitas com cache"""
        query_norm = self._normalizar_texto(query)
        
        # Verifica cache
        if query_norm in self._cache:
            return self._cache[query_norm]
        
        # Faz a busca direta sem chamar o método cached novamente
        resultados = self.buscar_receitas(query)
        
        # Atualiza cache
        self._cache[query_norm] = resultados
        return resultados
    
    def buscar_receitas(self, query: str) -> List[Dict]:
        """Busca receitas no banco de dados"""
        query_norm = self._normalizar_texto(query)
        
        # Busca por título
        response = self.supabase.table('receitas').select('*').ilike('titulo', f'%{query_norm}%').execute()
        
        # Processa resultados
        receitas_validas = []
        for receita in response.data:
            resumo = self._criar_resumo_receita(receita)
            if resumo:
                receitas_validas.append(resumo)
        
        return receitas_validas
    
    def buscar_receita_por_id(self, receita_id: str) -> Optional[Dict]:
        """Busca uma receita específica por ID"""
        response = self.supabase.table('receitas').select('*').eq('id', receita_id).execute()
        
        if not response.data:
            return None
        
        receita_db = response.data[0]
        
        # Converte para o formato esperado
        return {
            'id': str(receita_db.get('id', '')).strip(),
            'titulo': str(receita_db.get('titulo', '')).strip().upper(),
            'descricao': str(receita_db.get('descricao', '')).strip(),
            'ingredientes': self._processar_ingredientes(receita_db.get('ingredientes', '')),
            'modo_preparo': receita_db.get('modo_preparo', []),
            'tempo_preparo': str(receita_db.get('tempo_preparo', '')).strip(),
            'porcoes': str(receita_db.get('porcoes', '')).strip(),
            'dificuldade': str(receita_db.get('dificuldade', '')).strip(),
            'utensilios': str(receita_db.get('utensilios', '')).strip(),
            'harmonizacao': str(receita_db.get('harmonizacao', '')).strip(),
            'informacoes_nutricionais': receita_db.get('informacoes_nutricionais', {}),
            'beneficios_funcionais': receita_db.get('beneficios_funcionais', []),
            'dicas': receita_db.get('dicas', [])
        }
    
    def salvar_receita(self, receita: Dict) -> bool:
        """Salva uma nova receita no banco de dados"""
        try:
            response = self.supabase.table('receitas').insert(receita).execute()
            return bool(response.data)
        except Exception:
            return False

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
                'id': str(receita_db.get('id', '')).strip(),  # Mantém o ID na conversão
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