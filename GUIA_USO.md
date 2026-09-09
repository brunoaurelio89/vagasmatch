# 📋 Guia de Uso - VagaMatch para Automação de Candidatura

Este guia explica como usar o VagaMatch para encontrar e se candidatar a vagas de forma rápida e eficiente.

---

## 🎯 Objetivo

Automatizar sua busca e candidatura a vagas de emprego:
- ✅ Encontrar vagas compatíveis com seu perfil
- ✅ Filtrar por nível (Júnior/Pleno/Sênior)
- ✅ Priorizar vagas onde você tem mais chances
- ✅ Candidatar-se rapidamente via link direto

---

## 🚀 Passo a Passo

### 1. Configuração Inicial

```bash
# Navegue até o projeto
cd C:\Users\Vitor Hugo Gianini\Desktop\VagaMatch

# Instale as dependências
pip install -r backend/requirements.txt

# Crie o arquivo .env (copie do exemplo)
copy .env.example .env
```

Edite o arquivo `.env` e adicione suas chaves de API (veja seção abaixo).

---

### 2. Configurar APIs (Importante!)

Quanto mais APIs você configurar, mais vagas encontrará.

| API | Onde obter | Gratuito? | Necessário? |
|-----|-----------|-----------|------------|
| **SerpAPI** (Google Jobs) | serpapi.com | 100/mês | ✅ Sim (base) |
| **Jooble** | jooble.org/api/about | Sim | ⭐ Recomendado |
| **RapidAPI** (Indeed, Glassdoor, JSearch) | rapidapi.com | 500/dia | ⭐ Recomendado |

**Exemplo de .env:**
```env
SERPAPI_KEY=sua_chave_serpapi
JOOBLE_API_KEY=sua_chave_jooble
RAPIDAPI_KEY=sua_chave_rapidapi
```

---

### 3. Iniciar o Servidor

```bash
python run.py
```

O navegador abrirá automaticamente em `http://localhost:8000`

---

### 4. Usar para Automação de Candidatura

#### Passo A: Upload do Currículo
1. Na primeira tela, faça upload do seu currículo (PDF, DOCX, TXT)
2. O sistema detectará automaticamente seu nível (Júnior/Pleno/Sênior)
3. Veja suas habilidades detectadas

#### Passo B: Configurar Busca
1. Digite o cargo desejado (ex: "Desenvolvedor Python")
2. Selecione sua região (ex: "São Paulo-SP")
3. Marque os modelos de trabalho (Remoto, Híbrido, Presencial)
4. **Marque as fontes de vagas** (LinkedIn, Jooble, Glassdoor, etc.)
5. ⭐ **Deixe marcado "Filtrar por nível compatível"** - isso garante que você verá apenas vagas adequadas ao seu nível

#### Passo C: Analisar e Candidatar
1. O sistema mostrará vagas classificadas por % de chance
2. Cada vaga tem:
   - **Score de match** (0-100%): quanto mais alto, melhor para você
   - **Badge de nível**: Júnior/Pleno/Sênior
   - **Botão "Candidatar"**: abre a vaga direto na fonte original
3. Clique em "Candidatar" nas vagas com 65%+ de chance
4. Repita para várias vagas em poucos minutos

---

## ⚡ Dicas para Automação Rápida

### Estratégia 1: Foco em Alta Chance
- Filtre apenas vagas com score ≥ 70%
- Candidata-se a 10-20 vagas/dia neste range
- Maior taxa de retorno

### Estratégia 2: Por Nível
- Júnior: foque em vagas Júnior + algumas Pleno
- Pleno: foque em vagas Pleno + algumas Sênior
- Sênior: foque em vagas Sênior + algumas Pleno

### Estratégia 3: Multi-fonte
- Marque TODAS as fontes disponíveis
- Mais vagas = mais oportunidades
- Use o filtro de nível para não se perder

---

## 🧪 Testando Sua Configuração

Antes de usar, verifique se tudo funciona:

```bash
cd backend
python -m pytest tests/ -v
```

Ou teste individualmente:

```bash
python tests/test_apis.py
```

Isso mostrará quais APIs estão conectadas e se o matching funciona.

---

## 🔧 Solução de Problemas

### Erro: "Nenhuma vaga encontrada"
- ✅ Verifique se pelo menos uma API key está configurada
- ✅ Tente uma região maior (ex: "Brasil" em vez de "Cidade Pequena-SP")
- ✅ Verifique se o termo de busca está correto

### Erro: "Servidor não inicia"
- ✅ Verifique se Python 3.10+ está instalado
- ✅ Execute `pip install -r backend/requirements.txt`
- ✅ Verifique se a porta 8000 não está em uso

### Erro: "Nível não detectado"
- ✅ Adicione anos de experiência no currículo (ex: "3 anos de experiência")
- ✅ Liste suas principais tecnologias
- ✅ O sistema inferirá o nível pelas habilidades

---

## 📊 Interpretação dos Resultados

| Score | Classificação | Ação Recomendada |
|-------|--------------|------------------|
| 80-100% | 🔥 Muito Alta | Candidatar IMEDIATAMENTE |
| 65-79% | 💡 Alta | Candidatar hoje |
| 50-64% | ⚠️ Média | Candidatar esta semana |
| <50% | ❌ Baixa | Estudar habilidades faltantes |

---

## 🎯 Exemplo de Uso Diário

```
09:00 - Upload currículo atualizado
09:05 - Buscar "Desenvolvedor Python" em "São Paulo-SP"
09:10 - Filtrar apenas vagas com 65%+ chance
09:15 - Candidatar em 15 vagas (clique rápido)
09:30 - Buscar "Analista de Dados" na mesma região
09:45 - Candidatar em mais 10 vagas
10:00 - Concluído! 25 candidaturas em 1 hora
```

---

## 🔐 Segurança

- ✅ Seu currículo é criptografado localmente (Fernet/AES-128)
- ✅ Nenhuma senha é armazenada
- ✅ Dados nunca saem do seu computador (exceto para busca de vagas)
- ✅ Você controla quais fontes usar

---

## 📞 Suporte

Problemas? Verifique:
1. Arquivo `.env` configurado corretamente
2. Dependências instaladas
3. Chaves de API válidas
4. Conexão com internet

---

**Versão:** 2.0
**Última atualização:** 2026-08-29
**Autor:** Vitor Hugo Gianini
