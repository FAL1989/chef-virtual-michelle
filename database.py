import sqlite3
from typing import Dict, List, Optional, Union
import json
import logging
from datetime import datetime

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Exceção customizada para erros do banco de dados"""
    pass

class ReceitasDB:
    def __init__(self, db_name: str = 'receitas.db'):
        """Inicializa a conexão com o banco de dados"""
        self.db_name = db_name
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.criar_tabelas()
            logger.info(f"Conexão estabelecida com {db_name}")
        except sqlite3.Error as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise DatabaseError(f"Erro ao conectar ao banco de dados: {e}")

    def __del__(self):
        """Fecha a conexão quando o objeto é destruído"""
        if hasattr(self, 'conn'):
            try:
                self.conn.close()
                logger.info("Conexão com o banco de dados fechada")
            except sqlite3.Error as e:
                logger.error(f"Erro ao fechar conexão: {e}")

    def criar_tabelas(self):
        """Cria as tabelas necessárias"""
        try:
            cursor = self.conn.cursor()

            # Tabela de categorias
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            # Tabela de receitas
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT,
                categoria_id INTEGER,
                utensilios TEXT,
                ingredientes TEXT,
                modo_preparo TEXT,
                tempo_preparo TEXT,
                porcoes INTEGER,
                dificuldade TEXT,
                harmonizacao TEXT,
                calorias TEXT,
                proteinas TEXT,
                carboidratos TEXT,
                gorduras TEXT,
                fibras TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id)
            )''')

            # Tabela de dicas
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS dicas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receita_id INTEGER,
                dica TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (receita_id) REFERENCES receitas (id)
            )''')

            # Tabela de benefícios funcionais
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS beneficios_funcionais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receita_id INTEGER,
                beneficio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (receita_id) REFERENCES receitas (id)
            )''')

            # Trigger para atualizar updated_at
            cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_receitas_timestamp 
            AFTER UPDATE ON receitas
            BEGIN
                UPDATE receitas SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
            ''')

            self.conn.commit()
            logger.info("Tabelas criadas/verificadas com sucesso")
        except sqlite3.Error as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            raise DatabaseError(f"Erro ao criar tabelas: {e}")

    def adicionar_categoria(self, nome: str) -> Optional[int]:
        """Adiciona uma nova categoria"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO categorias (nome) VALUES (?)', (nome,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Erro ao adicionar categoria: {e}")
            return None

    def adicionar_receita(self, receita: Dict) -> bool:
        """Adiciona uma receita ao banco de dados"""
        try:
            # Garante que todos os campos são strings
            titulo = str(receita['titulo'])
            descricao = str(receita.get('descricao', ''))
            utensilios = str(receita.get('utensilios', ''))
            
            # Converte listas para strings se necessário
            ingredientes = receita['ingredientes']
            if isinstance(ingredientes, list):
                ingredientes = '\n'.join(ingredientes)
            
            modo_preparo = receita['modo_preparo']
            if isinstance(modo_preparo, list):
                modo_preparo = '.\n'.join(modo_preparo) + '.'
            
            # Campos opcionais
            tempo_preparo = str(receita.get('tempo_preparo', ''))
            porcoes = int(receita.get('porcoes', 0))
            dificuldade = str(receita.get('dificuldade', ''))
            harmonizacao = str(receita.get('harmonizacao', ''))
            
            # Informações nutricionais
            info_nutri = receita.get('informacoes_nutricionais', {})
            calorias = str(info_nutri.get('calorias', ''))
            proteinas = str(info_nutri.get('proteinas', ''))
            carboidratos = str(info_nutri.get('carboidratos', ''))
            gorduras = str(info_nutri.get('gorduras', ''))
            fibras = str(info_nutri.get('fibras', ''))
            
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO receitas (
                titulo, descricao, utensilios, ingredientes, modo_preparo,
                tempo_preparo, porcoes, dificuldade, harmonizacao,
                calorias, proteinas, carboidratos, gorduras, fibras
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (titulo, descricao, utensilios, ingredientes, modo_preparo,
                 tempo_preparo, porcoes, dificuldade, harmonizacao,
                 calorias, proteinas, carboidratos, gorduras, fibras))
            
            receita_id = cursor.lastrowid
            
            # Adiciona dicas se existirem
            if 'dicas' in receita and receita['dicas']:
                dicas = receita['dicas']
                if isinstance(dicas, str):
                    dicas = [dicas]
                for dica in dicas:
                    cursor.execute(
                        'INSERT INTO dicas (receita_id, dica) VALUES (?, ?)',
                        (receita_id, str(dica))
                    )
            
            # Adiciona benefícios funcionais se existirem
            if 'beneficios_funcionais' in receita and receita['beneficios_funcionais']:
                beneficios = receita['beneficios_funcionais']
                if isinstance(beneficios, str):
                    beneficios = [beneficios]
                for beneficio in beneficios:
                    cursor.execute(
                        'INSERT INTO beneficios_funcionais (receita_id, beneficio) VALUES (?, ?)',
                        (receita_id, str(beneficio))
                    )
            
            self.conn.commit()
            logger.info(f"Receita '{titulo}' adicionada com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar receita: {e}")
            return False

    def buscar_receitas(self, termo: str = None) -> List[Dict]:
        """Busca receitas no banco de dados"""
        try:
            cursor = self.conn.cursor()
            
            if termo:
                # Normaliza o termo de busca
                termo = termo.lower()
                termo = f"%{termo}%"
                
                sql = '''
                SELECT r.*, 
                       GROUP_CONCAT(DISTINCT d.dica) as dicas,
                       GROUP_CONCAT(DISTINCT b.beneficio) as beneficios
                FROM receitas r
                LEFT JOIN dicas d ON r.id = d.receita_id
                LEFT JOIN beneficios_funcionais b ON r.id = b.receita_id
                WHERE LOWER(r.titulo) LIKE ?
                OR LOWER(r.descricao) LIKE ?
                OR LOWER(r.ingredientes) LIKE ?
                OR LOWER(r.modo_preparo) LIKE ?
                GROUP BY r.id
                ORDER BY r.created_at DESC
                LIMIT 10
                '''
                cursor.execute(sql, (termo, termo, termo, termo))
            else:
                sql = '''
                SELECT r.*, 
                       GROUP_CONCAT(DISTINCT d.dica) as dicas,
                       GROUP_CONCAT(DISTINCT b.beneficio) as beneficios
                FROM receitas r
                LEFT JOIN dicas d ON r.id = d.receita_id
                LEFT JOIN beneficios_funcionais b ON r.id = b.receita_id
                GROUP BY r.id
                ORDER BY r.created_at DESC
                LIMIT 10
                '''
                cursor.execute(sql)
            
            receitas = []
            for row in cursor.fetchall():
                receita = {
                    'id': row[0],
                    'titulo': row[1],
                    'descricao': row[2],
                    'categoria': row[3],
                    'utensilios': row[4],
                    'ingredientes': row[5],
                    'modo_preparo': row[6],
                    'tempo_preparo': row[7],
                    'porcoes': row[8],
                    'dificuldade': row[9],
                    'harmonizacao': row[10],
                    'informacoes_nutricionais': {
                        'calorias': row[11],
                        'proteinas': row[12],
                        'carboidratos': row[13],
                        'gorduras': row[14],
                        'fibras': row[15]
                    },
                    'created_at': row[16],
                    'updated_at': row[17],
                    'dicas': row[18].split(',') if row[18] else [],
                    'beneficios_funcionais': row[19].split(',') if row[19] else []
                }
                receitas.append(receita)
            
            logger.info(f"Busca por '{termo}' retornou {len(receitas)} receitas")
            return receitas
        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar receitas: {e}")
            return []

    def get_todas_receitas(self) -> str:
        """Retorna todas as receitas em formato de texto"""
        try:
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
        except Exception as e:
            logger.error(f"Erro ao obter todas as receitas: {e}")
            return ""

    def limpar_banco(self):
        """Limpa todas as tabelas do banco de dados"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM dicas')
            cursor.execute('DELETE FROM receitas')
            cursor.execute('DELETE FROM categorias')
            self.conn.commit()
            logger.info("Banco de dados limpo com sucesso")
        except sqlite3.Error as e:
            logger.error(f"Erro ao limpar banco de dados: {e}")
            raise DatabaseError(f"Erro ao limpar banco de dados: {e}")

    def exportar_receitas(self, formato: str = 'json') -> Union[str, Dict]:
        """Exporta todas as receitas em um formato específico"""
        try:
            receitas = self.buscar_receitas()
            
            if formato == 'json':
                return json.dumps(receitas, ensure_ascii=False, indent=2)
            elif formato == 'markdown':
                texto = "# Receitas da Chef Michelle\n\n"
                texto += f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                
                for receita in receitas:
                    texto += f"## {receita['titulo']}\n\n"
                    texto += "### Ingredientes\n\n"
                    texto += f"{receita['ingredientes']}\n\n"
                    texto += "### Modo de Preparo\n\n"
                    texto += f"{receita['modo_preparo']}\n\n"
                    if receita['dicas']:
                        texto += "### Dicas\n\n"
                        for dica in receita['dicas']:
                            texto += f"- {dica}\n"
                        texto += "\n"
                    texto += "---\n\n"
                return texto
            else:
                raise ValueError(f"Formato '{formato}' não suportado")
        except Exception as e:
            logger.error(f"Erro ao exportar receitas: {e}")
            return "" if formato == 'markdown' else "{}" 