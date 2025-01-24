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
        st.write("DEBUG - Convertendo receita:", receita_db)
        
        if not isinstance(receita_db, dict):
            st.error(f"Receita inválida, tipo recebido: {type(receita_db)}")
            return None
            
        try:
            # Verifica se o título existe
            if 'titulo' not in receita_db:
                st.error("Receita sem título")
                return None
                
            # Converte informações nutricionais de JSONB para dict
            info_nutri = receita_db.get('informacoes_nutricionais', {})
            if isinstance(info_nutri, str):
                info_nutri = json.loads(info_nutri)
            
            # Converte benefícios funcionais de JSONB para list
            beneficios = receita_db.get('beneficios_funcionais', [])
            if isinstance(beneficios, str):
                beneficios = json.loads(beneficios)
            
            # Converte dicas de JSONB para list
            dicas = receita_db.get('dicas', [])
            if isinstance(dicas, str):
                dicas = json.loads(dicas)
            
            receita_convertida = {
                'titulo': str(receita_db.get('titulo', '')),
                'descricao': str(receita_db.get('descricao', '')),
                'utensilios': str(receita_db.get('utensilios', '')),
                'ingredientes': str(receita_db.get('ingredientes', '')).split('\n') if receita_db.get('ingredientes') else [],
                'modo_preparo': str(receita_db.get('modo_preparo', '')).split('\n') if receita_db.get('modo_preparo') else [],
                'tempo_preparo': str(receita_db.get('tempo_preparo', '')),
                'porcoes': str(receita_db.get('porcoes', '')),
                'dificuldade': str(receita_db.get('dificuldade', '')),
                'harmonizacao': str(receita_db.get('harmonizacao', '')),
                'informacoes_nutricionais': info_nutri,
                'beneficios_funcionais': beneficios,
                'dicas': dicas
            }
            
            st.write("DEBUG - Receita convertida:", receita_convertida)
            return receita_convertida
        except Exception as e:
            st.error(f"Erro ao converter receita: {str(e)}")
            return None

    def adicionar_receita(self, receita: Dict) -> bool:
        """Adiciona uma nova receita ao banco de dados"""
        try:
            # Garante que os campos numéricos sejam 0 quando vazios
            info_nutri = receita.get('informacoes_nutricionais', {})
            for campo in ['calorias', 'proteinas', 'carboidratos', 'gorduras', 'fibras']:
                valor = info_nutri.get(campo, '')
                info_nutri[campo] = 0 if valor == '' else float(valor)
            receita['informacoes_nutricionais'] = info_nutri

            # Garante que arrays sejam listas vazias quando nulos
            for campo in ['ingredientes', 'modo_preparo', 'beneficios_funcionais', 'dicas']:
                if not receita.get(campo):
                    receita[campo] = []

            # Garante que strings sejam vazias quando nulas
            for campo in ['titulo', 'descricao', 'categoria', 'tempo_preparo', 'porcoes', 'dificuldade', 'utensilios', 'harmonizacao']:
                if not receita.get(campo):
                    receita[campo] = ''

            data = self.supabase.table('receitas').insert(receita).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar receita: {e}")
            return False

    def buscar_receitas(self, query: str = None) -> List[Dict]:
        """Busca receitas no banco de dados"""
        try:
            if query:
                # Busca por título ou descrição
                data = self.supabase.table('receitas').select('*').or_(
                    f"titulo.ilike.%{query}%,descricao.ilike.%{query}%"
                ).execute()
            else:
                # Retorna todas as receitas
                data = self.supabase.table('receitas').select('*').execute()
            
            st.write("DEBUG - Dados brutos do Supabase:", data.data)
            
            if not data.data:
                st.warning("Nenhum dado retornado do Supabase")
                return []
            
            # Converte cada receita para o formato esperado
            receitas = []
            for receita in data.data:
                # Se a receita vier como string, tenta converter para dict
                if isinstance(receita, str):
                    try:
                        receita = json.loads(receita)
                    except json.JSONDecodeError:
                        st.error(f"Erro ao decodificar receita: {receita}")
                        continue
                
                receita_convertida = self._converter_formato_db(receita)
                if receita_convertida:
                    receitas.append(receita_convertida)
            
            st.write("DEBUG - Dados convertidos:", receitas)
            
            return receitas
        except Exception as e:
            st.error(f"Erro ao buscar receitas: {str(e)}")
            return []

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
            st.write("DEBUG - Dados brutos do Supabase:", data.data)
            
            # Converte cada receita para o formato esperado
            receitas = []
            for receita in data.data:
                # Se a receita vier como string, tenta converter para dict
                if isinstance(receita, str):
                    try:
                        receita = json.loads(receita)
                    except json.JSONDecodeError:
                        st.error(f"Erro ao decodificar receita: {receita}")
                        continue
                
                receita_convertida = self._converter_formato_db(receita)
                if receita_convertida:
                    receitas.append(receita_convertida)
            
            st.write("DEBUG - Dados convertidos:", receitas)
            return receitas
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