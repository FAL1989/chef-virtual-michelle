import os
import re
from typing import Dict, List
from database_supabase import ReceitasDB

def parse_markdown_recipe(content: str) -> Dict:
    """Converte o conteúdo Markdown em um dicionário de receita"""
    lines = content.split('\n')
    recipe = {
        'titulo': '',
        'descricao': '',
        'ingredientes': [],
        'modo_preparo': [],
        'tempo_preparo': '',
        'porcoes': '',
        'dificuldade': 'Médio',
        'informacoes_nutricionais': {
            'calorias': '0',
            'proteinas': '0',
            'carboidratos': '0',
            'gorduras': '0',
            'fibras': '0'
        },
        'dicas': [],
        'harmonizacao': ''
    }
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Título (primeira linha com #)
        if line.startswith('# '):
            recipe['titulo'] = line[2:].strip()
            continue
            
        # Seções
        if line.startswith('## '):
            section = line[3:].strip().lower()
            if 'ingredientes' in section:
                current_section = 'ingredientes'
            elif 'preparo' in section or 'instruções' in section:
                current_section = 'modo_preparo'
            elif 'dicas' in section:
                current_section = 'dicas'
            elif 'harmonização' in section:
                current_section = 'harmonizacao'
            continue
            
        # Conteúdo das seções
        if current_section:
            if line.startswith('- ') or line.startswith('* '):
                item = line[2:].strip()
                if current_section in ['ingredientes', 'modo_preparo', 'dicas']:
                    recipe[current_section].append(item)
            elif line.startswith('1. ') or re.match(r'^\d+\. ', line):
                item = re.sub(r'^\d+\. ', '', line).strip()
                if current_section == 'modo_preparo':
                    recipe['modo_preparo'].append(item)
            else:
                if current_section == 'harmonizacao':
                    recipe['harmonizacao'] = line
    
    # Converte listas para strings com quebras de linha
    recipe['ingredientes'] = '\n'.join(recipe['ingredientes'])
    recipe['modo_preparo'] = '\n'.join(recipe['modo_preparo'])
    
    return recipe

def import_recipes():
    """Importa todas as receitas da pasta docs/receitas"""
    db = ReceitasDB()
    recipes_dir = 'docs/receitas'
    
    # Lista todos os arquivos .md
    md_files = [f for f in os.listdir(recipes_dir) if f.endswith('.md')]
    
    print(f"Encontrados {len(md_files)} arquivos Markdown")
    
    for md_file in md_files:
        print(f"\nProcessando {md_file}...")
        
        # Lê o arquivo
        with open(os.path.join(recipes_dir, md_file), 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Converte para o formato de receita
        recipe = parse_markdown_recipe(content)
        
        if not recipe['titulo']:
            print(f"AVISO: Receita sem título em {md_file}")
            continue
        
        # Adiciona ao banco
        if db.adicionar_receita(recipe):
            print(f"✓ Receita '{recipe['titulo']}' adicionada com sucesso")
        else:
            print(f"✗ Erro ao adicionar receita '{recipe['titulo']}'")

if __name__ == '__main__':
    import_recipes() 