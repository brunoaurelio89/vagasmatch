# 🧭 VagaMatch

**Sistema inteligente de busca e automação de candidatura de vagas de emprego**

O VagaMatch analisa seu currículo, detecta seu nível de experiência (Júnior/Pleno/Sênior), busca vagas em múltiplas fontes e prioriza as que você tem mais chances de ser contratado.

---

## ✨ Funcionalidades

| Recurso | Descrição |
|---------|-----------|
| **Análise de currículo** | Extrai habilidades e experiência automaticamente de PDF, DOCX ou TXT |
| **Detecção de nível** | Identifica se você é Júnior, Pleno ou Sênior baseado no currículo |
| **Busca multi-fonte** | Google Jobs, Jooble, Indeed, LinkedIn, Glassdoor e JSearch em uma busca só, direcionada a QA, qualidade e testes de software |
| **Match por nível** | Prioriza vagas compatíveis com seu nível de experiência |
| **Score de aderência** | Calcula % de compatibilidade (habilidades + nível + experiência) |
| **Recomendações** | Sugere habilidades para melhorar seu perfil |
| **Interface moderna** | Design responsivo com dark mode automático |
| **Dados seguros** | Currículo criptografado localmente (AES-128) |

---

## 🚀 Instalação Rápida

### Pré-requisitos
- Python 3.10+
- Navegador web atualizado
- Chaves de API (ver abaixo)

### Passos

```bash
# 1. Clone ou extraia o projeto
cd C:\Users\Vitor Hugo Gianini\Desktop\VagaMatch

# 2. Instale as dependências
pip install -r backend/requirements.txt

# 3. Configure as APIs
copy .env.example .env
# Edite .env e adicione suas chaves

# 4. Inicie o servidor
python run.py
```

Acesse: **http://localhost:8000**

---

## 🔑 Configuração de APIs

| API | Onde obter | Limite grátis | Obrigatório? |
|-----|-----------|--------------|--------------|
| **SerpAPI** (Google Jobs) | [serpapi.com](https://serpapi.com) | 100/mês | ✅ Sim |
| **Jooble** | [jooble.org/api](https://jooble.org/api/about) | Ilimitado* | ⭐ Recomendado |
| **RapidAPI** (Indeed, LinkedIn, Glassdoor, JSearch) | [rapidapi.com](https://rapidapi.com) | 500/dia | ⭐ Recomendado |

*Jooble tem limite de requisições por minuto, mas é gratuito.

**Exemplo de `.env`:**
```env
SERPAPI_KEY=sua_chave_serpapi
JOOBLE_API_KEY=sua_chave_jooble
RAPIDAPI_KEY=sua_chave_rapidapi
```

A busca do LinkedIn usa a janela `24h` por padrão, pagina em lotes de 20 e
registra as consultas em `logs/linkedin_search.log`. A janela pode ser alterada
na variável `LINKEDIN_TIME_FRAME` em `backend/config.py`.

---

## 📖 Como Usar

1. **Upload do currículo** → Sistema detecta seu nível automaticamente
2. **Configurar busca** → A busca começa em qualidade de software, QA e testes; refine por cargo, região, modelo de trabalho e fontes
3. **Ver resultados** → Vagas classificadas por % de chance
4. **Candidatar** → Clique no botão para abrir a vaga na fonte original

**Para automação rápida:** Deixe marcado "Filtrar por nível compatível" e foque em vagas com 65%+ de chance.

📋 **Guia completo:** [GUIA_USO.md](GUIA_USO.md)

---

## 🧪 Testes

Teste suas configurações de API e o sistema de matching:

```bash
cd backend
python tests/test_apis.py
```

Saída esperada:
```
🔍 TALENTOSYNC - SUITE DE TESTES
============================================================
TESTE: Google Jobs (SerpAPI)
✅ OK: 15 vagas encontradas

TESTE: Jooble API
✅ OK: 10 vagas encontradas

TESTE: Matching por Nível
✅ Match Júnior→Júnior: 85%
✅ Match Júnior→Sênior: 45%
✅ OK: Candidato júnior pontuou melhor na vaga júnior
```

---

## 📊 Como o Match Funciona

```
Score Final = (Habilidades × 0.60) + (Experiência × 0.25) + (Nível × 0.15)
```

**Componentes:**
- **Habilidades (60%):** % de tecnologias da vaga que você domina
- **Experiência (25%):** Anos de carreira (inferidos do currículo)
- **Nível (15%):** Alinhamento entre seu nível e o da vaga
  - Mesmo nível: +10 bônus
  - 1 nível acima: +5 bônus
  - Abaixo do nível: -20 penalidade

**Classificação:**
| Score | Classificação | Ação |
|-------|--------------|------|
| 80-100% | 🔥 Muito Alta | Candidatar agora |
| 65-79% | 💡 Alta | Candidatar hoje |
| 50-64% | ⚠️ Média | Esta semana |
| <50% | ❌ Baixa | Estudar primeiro |

---

## 📂 Estrutura do Projeto

```
VagaMatch/
├── backend/
│   ├── app.py              # API FastAPI
│   ├── config.py           # Configurações e chaves de API
│   ├── security.py         # Criptografia (Fernet/AES-128)
│   ├── job_scraper.py      # Busca multi-fonte
│   ├── job_matcher.py      # Matching com detecção de nível
│   ├── resume_parser.py    # Parser de currículos
│   ├── requirements.txt    # Dependências Python
│   └── tests/
│       ├── __init__.py
│       └── test_apis.py    # Testes de integração
├── frontend/
│   ├── index.html          # Interface principal
│   ├── style.css           # Estilos
│   └── app.js              # Lógica do frontend
├── data/
│   └── encrypted/          # Currículo criptografado
├── .env.example            # Exemplo de configuração
├── GUIA_USO.md             # Guia de uso detalhado
├── run.py                  # Inicializador
└── README.md
```

---

## 🔐 Segurança

- ✅ Currículo criptografado localmente (nunca enviado para servidores externos)
- ✅ Sem armazenamento de senhas ou login em plataformas
- ✅ Cache de vagas por 30 minutos (otimização)
- ✅ Código open-source e auditável

---

## 🛠️ Tecnologias

- **Backend:** Python 3.10+, FastAPI, Uvicorn
- **Frontend:** HTML5, CSS3, JavaScript vanilla
- **APIs:** SerpAPI, Jooble, RapidAPI (Indeed, Glassdoor, JSearch)
- **Segurança:** Cryptography (Fernet)

---

## 📝 Roadmap

- [ ] Auto-candidatura (preenchimento automático de formulários)
- [ ] Alertas de novas vagas por email
- [ ] Histórico de candidaturas
- [ ] Machine Learning para melhor matching

---

## 🤝 Contribuição

Sinta-se à vontade para abrir issues ou pull requests com melhorias!

---

## 📜 Licença

MIT — Uso livre para fins pessoais e comerciais.

---

**Feito com ❤️ por Vitor Hugo Gianini**
