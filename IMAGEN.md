# VagaMatch - Guia Visual

## 📸 Como funciona (Imagem mental)

```
┌─────────────────────────────────────────────────────────────┐
│                    TALENTOSYNC                            │
│           Motor de Busca Inteligente de Vagas            │
└─────────────────────────────────────────────────────────────┘

  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │   PASSO 1    │    │   PASSO 2    │    │   PASSO 3    │
  │   Currículo  │───▶│  Buscar Vagas│───▶│ Resultados   │
  │   Upload     │    │  Filtros     │    │  com Match   │
  └──────────────┘    └──────────────┘    └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      PASSO 1 - UPLOAD                       │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  Nome: Vitor Hugo                                           │
│  Habilidades: Python, SQL, API, Docker, AWS                │
│  Experiência: 5 anos em desenvolvimento web                │
│  Educação: Bacharelado em Sistemas de Informação          │
└─────────────────────────────────────────────────────────────┘
                ▼
┌─────────────────────────────────────────────────────────────┐
│              PASSO 2 - FILTROS PERSONALIZADOS               │
└─────────────────────────────────────────────────────────────┘
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────┐
│ Tipos de Vaga        │  │ Modelo de Trabalho   │  │ Região   │
│ ▢ Analista Sistemas  │  │ ☑ Remoto             │  │  São Paulo│
│ ▢ Analista Dados     │  │ ☑ Híbrido            │  │  Rio      │
│                      │  │ ☐ Presencial         │  │  Remoto   │
└──────────────────────┘  └──────────────────────┘  └──────────┘

┌─────────────────────────────────────────────────────────────┐
│                     PASSO 3 - RESULTADOS                    │
└─────────────────────────────────────────────────────────────┘

VAGA 1: Analista de Sistemas Sênior
┌─────────────────────────────────────────────────────────────┐
│ Empresa: Tech Solutions BR     📍 São Paulo (Remoto)        │
│                                                             │
│  🎯 MATCH: 85%  (🔥 Alta Chance)                          │
│                                                             │
│  ✅ Você tem:                                               │
│     • Python, SQL, API, Docker                             │
│     • AWS (certificado básico)                              │
│                                                             │
│  ⚠️ Precisa:                                                │
│     • Django/Flask (sistema de templates)                  │
│     • Kubernetes (produção)                                  │
│                                                             │
│  [📎 Candidatar]                                            │
└─────────────────────────────────────────────────────────────┘

VAGA 2: Analista de Dados Pleno
┌─────────────────────────────────────────────────────────────┐
│ Empresa: DataTech         📍 Rio de Janeiro (Híbrido)       │
│                                                             │
│  🎯 MATCH: 68%  (💡 Boa Chance)                            │
│                                                             │
│  ✅ Você tem:                                               │
│     • Python, SQL                                          │
│                                                             │
│  ⚠️ Precisa:                                                │
│     • Pandas, NumPy                                        │
│     • Power BI ou Tableau                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    RECOMENDAÇÕES                          │
└─────────────────────────────────────────────────────────────┘
└─ 📚 Estude: Django, Kubernetes, Pandas, NumPy
  └─ 💡 Curso gratuito: https://docs.djangoproject.com
  └─ 💡 Curso gratuito: https://kubernetes.io/docs
  └─ 💡 Curso gratuito: https://pandas.pydata.org/docs

┌─────────────────────────────────────────────────────────────┐
│                    SEGURANÇA DOS DADOS                      │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Seu currículo → [FERNET ENCRYPTION] → encrypted/resume.enc │
│ Sua credencial → [FERNET ENCRYPTION] → encrypted/creds.enc  │
│                                                             │
│  ✅ Criptografado localmente (AES-128)                      │
│  ✅ Nenhum dado enviado para servidores externos             │
│  ✅ Chave mestra local: data/secret.key                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       FLUXO COMPLETO                        │
└─────────────────────────────────────────────────────────────┘
                                                               │
  [Navegador] ◀────────────────────────────── [Python]        │
        ▲                                           ▲          │
        │ abre localhost:8000                       │          │
        │                                           │          │
        │    ┌─────────────────────────────────┐   │          │
        │    │  FASTAPI (backend)              │   │          │
        │    │  GET /api/jobs/search             │───┼──[SerpAPI]
        │    │  POST /api/resume/upload          │   │          │
        │    │  GET  /api/resume (criptografado) │   │          │
        │    └─────────────────────────────────┘   │          │
        │                      ▲                    │          │
        │                      │                    │          │
        └──────────────────────┴────────────────────└──────────┘

```