# Chef Virtual - Receitas da Michelle 👩‍🍳

Um assistente virtual de culinária que ajuda você a encontrar e criar receitas deliciosas!

## Funcionalidades ✨

- 🔍 Busca de receitas existentes
- 🤖 Geração de novas receitas com IA
- 💬 Interface de chat interativa
- 📥 Exportação do histórico de conversas
- 📱 Interface responsiva e amigável

## Pré-requisitos 📋

- Python 3.8 ou superior
- pip (gerenciador de pacotes do Python)
- Chave de API do OpenAI

## Instalação 🚀

1. Clone o repositório ou baixe os arquivos

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv

# No Windows:
venv\Scripts\activate

# No Linux/Mac:
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

## Como Usar 🎯

1. Ative o ambiente virtual (se não estiver ativado):
```bash
# No Windows:
venv\Scripts\activate

# No Linux/Mac:
source venv/bin/activate
```

2. Execute o aplicativo:
```bash
streamlit run main.py
```

3. Abra seu navegador em `http://localhost:8501`

## Funcionalidades Detalhadas 📝

### Busca de Receitas
- Use a barra lateral para buscar receitas existentes
- Digite ingredientes ou nomes de pratos

### Chat Interativo
- Faça perguntas sobre receitas
- Peça sugestões baseadas em ingredientes
- Receba receitas personalizadas

### Exportação
- Exporte todo o histórico da conversa
- Formato Markdown para fácil leitura
- Inclui data e hora das interações

## Suporte 🆘

Em caso de dúvidas ou problemas:
1. Verifique se todas as dependências estão instaladas
2. Confirme se o arquivo `.env` está configurado corretamente
3. Verifique se o Python e o pip estão atualizados

## Licença 📄

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes. 