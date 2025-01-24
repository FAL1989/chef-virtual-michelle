import pytest
import os
from database_supabase import ReceitasDB, DatabaseError
import streamlit as st

@pytest.fixture
def test_db():
    """Fixture que cria uma instância de teste do ReceitasDB"""
    db = ReceitasDB()
    yield db

@pytest.fixture(autouse=True)
def clean_db(test_db):
    """Fixture que limpa o banco antes de cada teste"""
    test_db.limpar_banco()
    yield

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
    receitas = test_db.buscar_receitas("BOLO DE CHOCOLATE")  # Busca em maiúsculo
    assert len(receitas) == 1
    assert receitas[0]["titulo"] == "BOLO DE CHOCOLATE"

def test_buscar_receitas(test_db):
    """Testa a busca de receitas"""
    # Adiciona algumas receitas para teste
    receitas_teste = [
        {
            "titulo": "Pão de Queijo Mineiro",
            "ingredientes": ["Polvilho", "Queijo", "Ovo"],
            "modo_preparo": ["Misture tudo", "Asse"]
        },
        {
            "titulo": "Brigadeiro de Chocolate",
            "ingredientes": ["Leite condensado", "Chocolate em pó"],
            "modo_preparo": ["Misture", "Cozinhe"]
        }
    ]
    
    for receita in receitas_teste:
        test_db.adicionar_receita(receita)
    
    # Testa busca por título parcial
    resultados = test_db.buscar_receitas("QUEIJO")  # Busca parcial em maiúsculo
    assert len(resultados) == 1
    assert resultados[0]["titulo"] == "PÃO DE QUEIJO MINEIRO"
    
    # Testa busca por título parcial
    resultados = test_db.buscar_receitas("BRIGADEIRO")  # Busca parcial em maiúsculo
    assert len(resultados) == 1
    assert resultados[0]["titulo"] == "BRIGADEIRO DE CHOCOLATE"

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
    
    # Testa exportação de receitas
    receitas = test_db.exportar_receitas()
    assert len(receitas) > 0
    assert any(r["titulo"] == "BOLO SIMPLES" for r in receitas)

def test_buscar_receita_por_id(test_db):
    """Testa a busca de receita por ID"""
    # Adiciona uma receita para teste
    receita = {
        "titulo": "Teste Busca ID",
        "ingredientes": ["Teste"],
        "modo_preparo": ["Teste"]
    }
    test_db.adicionar_receita(receita)
    
    # Busca a receita adicionada usando título exato
    receitas = test_db.buscar_receitas("Teste Busca ID")
    assert len(receitas) == 1
    
    # Testa busca por ID
    receita_id = receitas[0]["id"]
    receita_por_id = test_db.buscar_receita_por_id(receita_id)
    assert receita_por_id is not None
    assert receita_por_id["titulo"] == "TESTE BUSCA ID" 