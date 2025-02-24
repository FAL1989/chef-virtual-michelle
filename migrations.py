import json
import sqlite3
from database_supabase import ReceitasDB
from typing import List, Dict

SQL_CREATE_TABLES = """
-- Habilitar extensões necessárias
create extension if not exists pg_trgm;
create extension if not exists pg_jsonschema;

-- Tabela de receitas
drop table if exists receitas cascade;

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

-- Índices para busca em texto
create index if not exists idx_receitas_titulo_gin on receitas using gin (titulo gin_trgm_ops);
create index if not exists idx_receitas_ingredientes_gin on receitas using gin (ingredientes gin_trgm_ops);
create index if not exists idx_receitas_descricao_gin on receitas using gin (descricao gin_trgm_ops);

-- Índices para campos JSONB
create index if not exists idx_receitas_info_nutri on receitas using gin (informacoes_nutricionais);
create index if not exists idx_receitas_beneficios on receitas using gin (beneficios_funcionais);
create index if not exists idx_receitas_dicas on receitas using gin (dicas);

-- Validação de schema para campos JSONB
alter table receitas 
add constraint check_info_nutri 
check (
    jsonb_typeof(informacoes_nutricionais) = 'object' 
    and informacoes_nutricionais ? 'calorias'
    and informacoes_nutricionais ? 'proteinas'
    and informacoes_nutricionais ? 'carboidratos'
    and informacoes_nutricionais ? 'gorduras'
    and informacoes_nutricionais ? 'fibras'
);

alter table receitas 
add constraint check_arrays
check (
    jsonb_typeof(beneficios_funcionais) = 'array'
    and jsonb_typeof(dicas) = 'array'
);
"""

def criar_tabelas(db: ReceitasDB):
    """Cria as tabelas no Supabase"""
    try:
        print("Recriando tabelas...")
        # Exclui todas as receitas existentes
        db.supabase.table('receitas').delete().gte('id', '00000000-0000-0000-0000-000000000000').execute()
        print("Tabelas limpas com sucesso!")
    except Exception as e:
        print(f"Erro ao limpar tabelas: {e}")
        raise

def converter_formato_receita(receita: Dict) -> Dict:
    """Converte o formato antigo para o novo formato"""
    ingredientes = []
    for ing in receita.get('ingredientes', []):
        if isinstance(ing, dict):
            ingredientes.append(f"{ing.get('quantidade', '')} de {ing.get('item', '')}")
        else:
            ingredientes.append(ing)
    
    modo_preparo = []
    for passo in receita.get('modo_preparo', []):
        if passo and not passo.isdigit():  # Remove números soltos
            modo_preparo.append(passo)
    
    return {
        'titulo': receita.get('titulo', ''),
        'descricao': receita.get('descricao', ''),
        'utensilios': receita.get('utensilios', ''),
        'ingredientes': '\n'.join(ingredientes),
        'modo_preparo': '\n'.join(modo_preparo),
        'tempo_preparo': receita.get('tempo_preparo', ''),
        'porcoes': str(receita.get('porcoes', '')),
        'dificuldade': receita.get('dificuldade', ''),
        'harmonizacao': receita.get('harmonizacao', ''),
        'informacoes_nutricionais': {
            'calorias': str(receita.get('calorias', '0')),
            'proteinas': str(receita.get('proteinas', '0')),
            'carboidratos': str(receita.get('carboidratos', '0')),
            'gorduras': str(receita.get('gorduras', '0')),
            'fibras': str(receita.get('fibras', '0'))
        },
        'beneficios_funcionais': receita.get('beneficios_funcionais', []),
        'dicas': receita.get('dicas', [])
    }

def carregar_dados_sqlite() -> List[Dict]:
    """Carrega os dados do banco SQLite"""
    try:
        # Carrega do arquivo JSON primeiro (backup)
        with open('receitas_clean.json', 'r', encoding='utf-8') as f:
            receitas = json.load(f)
            return [converter_formato_receita(r) for r in receitas]
    except Exception as e:
        print(f"Erro ao carregar JSON: {e}")
        return []

def migrar_dados():
    """Migra os dados do SQLite para o Supabase"""
    # Carrega os dados antigos
    receitas = carregar_dados_sqlite()
    if not receitas:
        print("Nenhum dado encontrado para migrar!")
        return
    
    # Inicializa a conexão com Supabase
    db = ReceitasDB()
    
    # Cria as tabelas se não existirem
    criar_tabelas(db)
    
    # Migra cada receita
    total = len(receitas)
    sucesso = 0
    
    for i, receita in enumerate(receitas, 1):
        print(f"Migrando receita {i}/{total}: {receita.get('titulo', 'Sem título')}")
        if db.adicionar_receita(receita):
            sucesso += 1
        
    print(f"\nMigração concluída!")
    print(f"Total de receitas: {total}")
    print(f"Migradas com sucesso: {sucesso}")
    print(f"Falhas: {total - sucesso}")

if __name__ == "__main__":
    migrar_dados() 