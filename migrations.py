import json
import sqlite3
from database_supabase import ReceitasDB
from typing import List, Dict

SQL_CREATE_TABLES = """
-- Tabela de receitas
create table if not exists receitas (
    id uuid default uuid_generate_v4() primary key,
    titulo text not null,
    descricao text,
    beneficios_funcionais jsonb,
    categoria text,
    ingredientes jsonb not null,
    modo_preparo jsonb not null,
    tempo_preparo text,
    porcoes text,
    dificuldade text,
    informacoes_nutricionais jsonb,
    utensilios text,
    dicas jsonb,
    harmonizacao text,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Criar índices para melhorar a performance das buscas
create index if not exists idx_receitas_titulo on receitas using gin (to_tsvector('portuguese', titulo));
create index if not exists idx_receitas_descricao on receitas using gin (to_tsvector('portuguese', descricao));
create index if not exists idx_receitas_categoria on receitas (categoria);
"""

def criar_tabelas(db: ReceitasDB):
    """Cria as tabelas no Supabase"""
    try:
        db.supabase.table('receitas').select('id').limit(1).execute()
        print("Tabelas já existem!")
    except Exception as e:
        print("Criando tabelas...")
        db.supabase.sql(SQL_CREATE_TABLES).execute()
        print("Tabelas criadas com sucesso!")

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
        'descricao': '',  # Campo não existia no formato antigo
        'beneficios_funcionais': [],  # Campo não existia no formato antigo
        'categoria': '',  # Campo não existia no formato antigo
        'ingredientes': ingredientes,
        'modo_preparo': modo_preparo,
        'tempo_preparo': '',  # Campo não existia no formato antigo
        'porcoes': '',  # Campo não existia no formato antigo
        'dificuldade': '',  # Campo não existia no formato antigo
        'informacoes_nutricionais': {
            'calorias': '',
            'proteinas': '',
            'carboidratos': '',
            'gorduras': '',
            'fibras': ''
        },
        'utensilios': '',  # Campo não existia no formato antigo
        'dicas': [],  # Campo não existia no formato antigo
        'harmonizacao': ''  # Campo não existia no formato antigo
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