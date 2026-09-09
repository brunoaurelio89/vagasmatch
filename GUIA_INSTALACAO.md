# VagaMatch - Guia de Instalação e Execução

## Pré-requisitos

- **Python 3.11 ou superior** (3.13 recomendado)
  - Download: https://www.python.org/downloads/
  - Durante a instalação, marque a opção **"Add Python to PATH"**

- **Sistema operacional:** Windows 10/11, macOS ou Linux

---

## Passo a passo

### 1. Extrair o projeto

Extraia o arquivo `MatchVagas-main.zip` em uma pasta de sua escolha.

### 2. Configurar API Keys (opcional mas recomendado)

Na raiz do projeto, crie um arquivo `.env` baseado no `.env.example`:

```env
SERPAPI_KEY=sua_chave_serpapi_aqui
JOOBLE_API_KEY=sua_chave_jooble_aqui
RAPIDAPI_KEY=sua_chave_rapidapi_aqui
```

> **Dica:** O app funciona mesmo sem API keys, mas buscará vagas em menos fontes.

### 3. Instalar dependências Python

Abra o terminal na pasta raiz do projeto e execute:

```bash
pip install -r backend/requirements.txt
```

#### Dependências instaladas:

| Pacote | Versão | Função |
|---|---|---|
| `fastapi` | >= 0.104.0 | Framework web do backend |
| `uvicorn` | >= 0.23.0 | Servidor ASGI |
| `python-multipart` | >= 0.0.6 | Upload de arquivos (currículo) |
| `requests` | >= 2.31.0 | Requisições HTTP para APIs de vagas |
| `cryptography` | >= 41.0.0 | Criptografia do currículo salvo |
| `python-dotenv` | >= 1.0.0 | Carregar variáveis do `.env` |
| `pypdf` | >= 4.0.0 | Ler currículos em PDF |
| `python-docx` | >= 0.8.11 | Ler currículos em DOCX |

### 4. Iniciar o servidor

**Opção A — Usando o arquivo batch (Windows):**

```
iniciar.bat
```

**Opção B — Linha de comando:**

```bash
# Windows
python backend/app.py

# macOS/Linux
python3 backend/app.py
```

### 5. Acessar a aplicação

Abra o navegador em: **http://localhost:8001**

---

## Estrutura do projeto

```
MatchVagas-main/
├── backend/
│   ├── app.py              # Servidor FastAPI
│   ├── config.py           # Configurações globais
│   ├── job_scraper.py      # Busca de vagas nas APIs
│   ├── job_matcher.py      # Motor de compatibilidade currículo × vaga
│   ├── resume_parser.py    # Extrai texto de PDF/DOCX
│   ├── security.py         # Criptografia do currículo
│   └── requirements.txt    # Dependências Python
├── frontend/
│   ├── index.html          # Interface web
│   ├── app.js              # Lógica do frontend
│   └── styles.css          # Estilos
├── data/                   # Dados locais (currículos criptografados)
├── iniciar.bat             # Script de inicialização (Windows)
├── .env.example            # Modelo de variáveis de ambiente
└── .env                    # Suas API keys (criar manualmente)
```

---

## Solução de problemas

| Problema | Solução |
|---|---|
| `python` não reconhecido | Reinstale o Python marcando "Add to PATH" |
| Erro ao importar módulos | Execute `pip install -r backend/requirements.txt` |
| Porta 8001 ocupada | Feche o processo que está usando a porta ou altere a porta em `backend/app.py` linha 555 |
| Frontend não carrega | Verifique se a pasta `frontend/` existe na raiz do projeto |
| Busca de vagas retorna vazio | Configure as API keys no arquivo `.env` |
