# Chef Michelle Mística - Assistente Virtual de Gastronomia Funcional 👩‍🍳

Uma assistente virtual especializada em gastronomia funcional, que combina conhecimentos de nutrição funcional e fitoterapia para criar receitas deliciosas e nutritivas.

## 🌟 Características

### Expertise em Gastronomia Funcional
- Receitas que equilibram sabor e benefícios nutricionais
- Uso inteligente de ingredientes funcionais
- Adaptações saudáveis de receitas tradicionais
- Explicações detalhadas sobre benefícios nutricionais

### Funcionalidades do Sistema
- 🔍 Busca inteligente de receitas
- 🤖 Geração de novas receitas com IA
- 💬 Interface interativa de chat
- 📊 Informações nutricionais detalhadas
- 💡 Dicas e substituições personalizadas
- 📥 Exportação do histórico de conversas

## 🛠️ Tecnologias Utilizadas

- Python 3.11
- Streamlit
- OpenAI API
- SQLite
- HTTPX
- Python-dotenv

## 📋 Pré-requisitos

- Python 3.11 ou superior
- Pip (gerenciador de pacotes Python)
- Chave de API da OpenAI

## 🚀 Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/chef-michelle-mistica.git
cd chef-michelle-mistica
```

2. Crie e ative um ambiente virtual:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
- Crie um arquivo `.env` na raiz do projeto
- Adicione sua chave da API OpenAI:
```
OPENAI_API_KEY=sua_chave_aqui
```

5. Execute o aplicativo:
```bash
streamlit run main.py
```

## 🌐 Deploy no Streamlit Cloud

1. Faça login no [Streamlit Cloud](https://streamlit.io/cloud)
2. Conecte com seu repositório GitHub
3. Configure as seguintes variáveis de ambiente no Streamlit Cloud:
   - `OPENAI_API_KEY`: Sua chave da API OpenAI

## 🧪 Testes

Execute os testes unitários:
```bash
pytest test_database.py
```

## 🔍 Estrutura do Projeto

```
chef-michelle-mistica/
├── main.py              # Aplicativo principal
├── database.py          # Gerenciamento do banco de dados
├── requirements.txt     # Dependências do projeto
├── .env                 # Variáveis de ambiente (local)
├── .streamlit/         # Configurações do Streamlit
├── test_database.py    # Testes unitários
└── README.md           # Documentação
```

## 📝 Funcionalidades Detalhadas

### Busca de Receitas
- Pesquisa por ingredientes ou nome da receita
- Filtragem por categorias
- Resultados com informações nutricionais

### Geração de Receitas
- Criação de novas receitas baseadas em ingredientes
- Adaptações funcionais automáticas
- Cálculo de informações nutricionais

### Exportação
- Histórico de conversas em Markdown
- Receitas em formato estruturado
- Informações nutricionais detalhadas

## 👥 Contribuição

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🤝 Suporte

Em caso de dúvidas ou problemas:
1. Consulte a documentação
2. Verifique as issues existentes
3. Abra uma nova issue com detalhes do problema

---
Desenvolvido com ❤️ pela equipe Chef Michelle Mística 