import sqlite3
from typing import Dict, List

class ReceitasDB:
    def __init__(self, db_name: str = 'receitas.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.criar_tabelas()

    def __del__(self):
        """Fecha a conexão quando o objeto é destruído"""
        if hasattr(self, 'conn'):
            self.conn.close()

    def criar_tabelas(self):
        """Cria as tabelas necessárias"""
        cursor = self.conn.cursor()

        # Tabela de categorias
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )''')

        # Tabela de receitas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            categoria_id INTEGER,
            utensilios TEXT,
            ingredientes TEXT,
            modo_preparo TEXT,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        )''')

        # Tabela de dicas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receita_id INTEGER,
            dica TEXT,
            FOREIGN KEY (receita_id) REFERENCES receitas (id)
        )''')

        self.conn.commit()

    def limpar_banco(self):
        """Limpa todas as tabelas do banco de dados"""
        cursor = self.conn.cursor()
        
        cursor.execute('DELETE FROM dicas')
        cursor.execute('DELETE FROM receitas')
        cursor.execute('DELETE FROM categorias')
        self.conn.commit()

    def adicionar_receita(self, receita: Dict):
        """Adiciona uma receita ao banco de dados"""
        sql = '''
        INSERT INTO receitas (titulo, utensilios, ingredientes, modo_preparo)
        VALUES (?, ?, ?, ?)
        '''
        try:
            # Garante que todos os campos são strings
            titulo = str(receita['titulo'])
            utensilios = str(receita.get('utensilios', ''))
            
            # Converte listas para strings se necessário
            ingredientes = receita['ingredientes']
            if isinstance(ingredientes, list):
                ingredientes = '\n'.join(ingredientes)
            
            modo_preparo = receita['modo_preparo']
            if isinstance(modo_preparo, list):
                modo_preparo = '.\n'.join(modo_preparo) + '.'
            
            cursor = self.conn.cursor()
            cursor.execute(sql, (titulo, utensilios, ingredientes, modo_preparo))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao adicionar receita: {e}")
            return False

    def buscar_receitas(self, termo: str = None) -> List[Dict]:
        """Busca receitas no banco de dados"""
        cursor = self.conn.cursor()

        query = '''
        SELECT r.*, c.nome as categoria, GROUP_CONCAT(d.dica, '|') as dicas
        FROM receitas r
        LEFT JOIN categorias c ON r.categoria_id = c.id
        LEFT JOIN dicas d ON r.id = d.receita_id
        '''

        params = []
        if termo:
            palavras = termo.lower().replace('?', '').split()
            condicoes = []
            for palavra in palavras:
                condicao = '''
                (LOWER(r.titulo) LIKE ? 
                OR LOWER(r.ingredientes) LIKE ? 
                OR LOWER(r.modo_preparo) LIKE ?)
                '''
                condicoes.append(condicao)
                termo_busca = f'%{palavra}%'
                params.extend([termo_busca, termo_busca, termo_busca])
            
            if condicoes:
                query += ' WHERE ' + ' AND '.join(condicoes)

        query += ' GROUP BY r.id'
        
        cursor.execute(query, params)
        
        colunas = [desc[0] for desc in cursor.description]
        receitas = []
        
        for row in cursor.fetchall():
            receita = dict(zip(colunas, row))
            if receita['dicas']:
                receita['dicas'] = receita['dicas'].split('|')
            else:
                receita['dicas'] = []
            receitas.append(receita)

        return receitas

    def get_todas_receitas(self) -> str:
        """Retorna todas as receitas em formato de texto"""
        receitas = self.buscar_receitas()
        texto = ""
        for receita in receitas:
            texto += f"\nRECEITA: {receita['titulo']}\n"
            texto += f"INGREDIENTES:\n{receita['ingredientes']}\n"
            texto += f"MODO DE PREPARO:\n{receita['modo_preparo']}\n"
            if receita['dicas']:
                texto += "DICAS:\n" + "\n".join(receita['dicas']) + "\n"
            texto += "-" * 50 + "\n"
        return texto 