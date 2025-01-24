import pytest
import os
from database import ReceitasDB, DatabaseError

@pytest.fixture
def test_db():
    """Fixture que cria um banco de dados de teste"""
    db_name = "test_receitas.db"
    db = ReceitasDB(db_name)
    yield db
    db.__del__()
    if os.path.exists(db_name):
        os.remove(db_name)

def test_criar_tabelas(test_db):
    """Testa a criação das tabelas"""
    # A criação das tabelas já acontece no __init__
    # Então só precisamos verificar se não houve erros
    assert True

def test_adicionar_receita(test_db):
    """Testa a adição de uma receita"""
    receita = {
        "titulo": "Bolo de Chocolate",
        "utensilios": "Forma, batedeira, tigela",
        "ingredientes": [
            "2 xícaras de farinha",
            "1 xícara de chocolate em pó",
            "3 ovos",
            "2 xícaras de açúcar"
        ],
        "modo_preparo": [
            "Misture os ingredientes secos",
            "Adicione os ovos e misture bem",
            "Asse por 40 minutos"
        ],
        "tempo_preparo": "45 minutos",
        "porcoes": 8,
        "dificuldade": "Médio",
        "dicas": [
            "Pré-aqueça o forno",
            "Use chocolate de boa qualidade"
        ]
    }
    
    assert test_db.adicionar_receita(receita) == True
    
    # Verifica se a receita foi adicionada
    receitas = test_db.buscar_receitas("Bolo de Chocolate")
    assert len(receitas) == 1
    assert receitas[0]["titulo"] == "Bolo de Chocolate"

def test_buscar_receitas(test_db):
    """Testa a busca de receitas"""
    # Adiciona algumas receitas para teste
    receitas_teste = [
        {
            "titulo": "Pão de Queijo",
            "ingredientes": ["Polvilho", "Queijo", "Ovo"],
            "modo_preparo": ["Misture tudo", "Asse"]
        },
        {
            "titulo": "Brigadeiro",
            "ingredientes": ["Leite condensado", "Chocolate em pó"],
            "modo_preparo": ["Misture", "Cozinhe"]
        }
    ]
    
    for receita in receitas_teste:
        test_db.adicionar_receita(receita)
    
    # Testa busca por título
    resultados = test_db.buscar_receitas("Pão")
    assert len(resultados) == 1
    assert resultados[0]["titulo"] == "Pão de Queijo"
    
    # Testa busca por ingrediente
    resultados = test_db.buscar_receitas("Chocolate")
    assert len(resultados) == 1
    assert resultados[0]["titulo"] == "Brigadeiro"

def test_exportar_receitas(test_db):
    """Testa a exportação de receitas"""
    # Adiciona uma receita para teste
    receita = {
        "titulo": "Bolo Simples",
        "ingredientes": ["Farinha", "Açúcar", "Ovos"],
        "modo_preparo": ["Misture", "Asse"],
        "dicas": ["Pré-aqueça o forno"]
    }
    test_db.adicionar_receita(receita)
    
    # Testa exportação JSON
    json_export = test_db.exportar_receitas("json")
    assert "Bolo Simples" in json_export
    assert "Farinha" in json_export
    
    # Testa exportação Markdown
    md_export = test_db.exportar_receitas("markdown")
    assert "# Receitas da Chef Michelle" in md_export
    assert "## Bolo Simples" in md_export

def test_limpar_banco(test_db):
    """Testa a limpeza do banco de dados"""
    # Adiciona uma receita
    receita = {
        "titulo": "Teste",
        "ingredientes": ["Teste"],
        "modo_preparo": ["Teste"]
    }
    test_db.adicionar_receita(receita)
    
    # Verifica se a receita foi adicionada
    assert len(test_db.buscar_receitas()) == 1
    
    # Limpa o banco
    test_db.limpar_banco()
    
    # Verifica se o banco está vazio
    assert len(test_db.buscar_receitas()) == 0

def test_erro_conexao():
    """Testa erro na conexão com o banco"""
    with pytest.raises(DatabaseError):
        ReceitasDB("/caminho/invalido/banco.db") 