"""
VagaMatch - Configurações e variáveis globais
"""
import os
from pathlib import Path

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Pastas
DATA_DIR = BASE_DIR / "data"
ENCRYPTED_DIR = DATA_DIR / "encrypted"

# Criar pastas se não existirem
ENCRYPTED_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Arquivos de dados
RESUME_ENCRYPTED = ENCRYPTED_DIR / "resume.enc"
CREDENTIALS_ENCRYPTED = ENCRYPTED_DIR / "credentials.enc"

# API Keys (deve ser configurado no .env)
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "YOUR_API_KEY_HERE")
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY", "YOUR_API_KEY_HERE")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "YOUR_API_KEY_HERE")
# Janela usada pela busca do LinkedIn. Opções da API: 1h, 24h, 7d e 6m.
LINKEDIN_TIME_FRAME = "24h"
INDERED_API_KEY = os.getenv("INDERED_API_KEY", "YOUR_API_KEY_HERE")
GLASSDOOR_API_KEY = os.getenv("GLASSDOOR_API_KEY", "YOUR_API_KEY_HERE")
JSEARCH_ENDPOINTS = [
    endpoint.strip()
    for endpoint in os.getenv("JSEARCH_ENDPOINTS", "/search-v2,/search").split(",")
    if endpoint.strip()
]
INDEED_API_HOSTS = [
    host.strip()
    for host in os.getenv(
        "INDEED_API_HOSTS",
        "indeed11.p.rapidapi.com,indeed12.p.rapidapi.com"
    ).split(",")
    if host.strip()
]

# Termo inicial da busca: mantém a experiência orientada à área de QA sem
# impedir que o usuário refine a consulta por cargo ou tecnologia.
DEFAULT_JOB_SEARCH_TERM = "Qualidade de Software QA Testes"

# =============================================================================
# Mapeamento completo de cidades brasileiras - Capitais e Principais Cidades
# =============================================================================
CIDADES_BRASILEIRAS = {
    # Região Norte
    "Acre": {"capital": "Rio Branco", "cidades": ["Rio Branco", "Cruzeiro do Sul", "Sena Madureira", "Tarauacá", "Feijó", "Mâncio Lima", "Brasiléia", "Xapuri"]},
    "Alagoas": {"capital": "Maceió", "cidades": ["Maceió", "Arapiraca", "Palmeira dos Índios", "Penedo", "Porto Real do Colégio", "União dos Palmares", "Campo Alegre", "Maragogi"]},
    "Amazonas": {"capital": "Manaus", "cidades": ["Manaus", "Parintins", "Manacapuru", "Itacoatiara", "Coari", "Tefé", "Lábrea", "São Gabriel da Cachoeira", "Tabatinga", "Letícia"]},
    "Amapá": {"capital": "Macapá", "cidades": ["Macapá", "Santana", "Oiapoque", "Laranjal do Jari", "Mazagão", "Pedra Branca do Amapari", "Serra do Navio"]},
    "Pará": {"capital": "Belém", "cidades": ["Belém", "Santarém", "Ananindeua", "Marabá", "Parauapebas", "Altamira", "Castanhal", "Abaetetuba", "Tucuruí", "Bragança", "Cametá", "Paragominas", "Patos de Minas"]},
    "Rondônia": {"capital": "Porto Velho", "cidades": ["Porto Velho", "Ji-Paraná", "Ariquemes", "Cacoal", "Guajará-Mirim", "Ouro Preto do Oeste", "Rolim de Moura", "Vilhena"]},
    "Roraima": {"capital": "Boa Vista", "cidades": ["Boa Vista", "Pacaraima", "Uiramutã", "Normandia", "Caracaraí"]},
    "Tocantins": {"capital": "Palmas", "cidades": ["Palmas", "Araguaína", "Gurupi", "Porto Nacional", "Paraíso do Tocantins", "Miracema do Tocantins", "Guaraí", "Colinas do Tocantins"]},

    # Região Nordeste
    "Alagoas": {"capital": "Maceió", "cidades": ["Maceió", "Arapiraca", "Palmeira dos Índios", "Penedo", "Porto Real do Colégio", "União dos Palmares", "Campo Alegre", "Maragogi"]},
    "Bahia": {"capital": "Salvador", "cidades": ["Salvador", "Feira de Santana", "Vitória da Conquista", "Itabuna", "Juazeiro", "Ilhéus", "Paulo Afonso", "Teixeira de Freitas", "Lauro de Freitas", "Simões Filho", "Camaçari", "Eunápolis", "Valença", "Jacobina", "Guanambi"]},
    "Ceará": {"capital": "Fortaleza", "cidades": ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanaú", "Sobral", "Crato", "Aracati", "Iguatu", "Quixadá", "Limoeiro do Norte", "Tianguá", "Canindé", "Lavras da Mangabeira", "Parambu"]},
    "Maranhão": {"capital": "São Luís", "cidades": ["São Luís", "São José de Ribamar", "Timon", "Caxias", "Açailândia", "Codó", "Balsas", "Imperatriz", "Pedreiras", "Presidente Médici", "Vitorino Freire"]},
    "Paraíba": {"capital": "João Pessoa", "cidades": ["João Pessoa", "Campina Grande", "Santa Rita", "Patos", "Sousa", "Conceição", "Guarabira", "Bayeux", "Cabedelo", "Pedras de Fogo", "Pombal"]},
    "Pernambuco": {"capital": "Recife", "cidades": ["Recife", "Jaboatão dos Guararapes", "Olinda", "Caruaru", "Petrolina", "Vitória de Santo Antão", "Garanhuns", "Escada", "Paulista", "Camaragibe", "Belo Jardim", "Araripina", "Serra Talhada", "Santa Cruz da Baixa Verde"]},
    "Piauí": {"capital": "Teresina", "cidades": ["Teresina", "Parnaíba", "Floriano", "Picos", "Campo Maior", "Oeiras", "São Raimundo Nonato", "Corrente", "Barra do Corda", "Altos", "Luís Correia", "José de Freitas"]},
    "Rio Grande do Norte": {"capital": "Natal", "cidades": ["Natal", "Mossoró", "Parnamirim", "Macaíba", "São Gonçalo do Amarante", "Ceará-Mirim", "Caicó", "Currais Novos", "Santa Cruz", "Assu", "Alecrim", "Vera Cruz"]},
    "Rio Grande do Sul": {"capital": "Porto Alegre", "cidades": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Novo Hamburgo", "Santa Maria", "Gravataí", "Viamão", "Cachoeirinha", "Uruguaiana", "Santa Cruz do Sul", "Erechim", "Passo Fundo", "Santana do Livramento", "Bage", "Santo Ângelo", "Torres"]},

    # Região Centro-Oeste
    "Goiás": {"capital": "Goiânia", "cidades": ["Goiânia", "Aparecida de Goiânia", "Anápolis", "Rio Verde", "Luziânia", "Águas Lindas de Goiás", "Valparaíso de Goiás", "Caldas Novas", "Itumbiara", "Jataí", "Pirenópolis", "Trindade"]},
    "Mato Grosso": {"capital": "Cuiabá", "cidades": ["Cuiabá", "Várzea Grande", "Rondonópolis", "Sinop", "Tangará da Serra", "Cáceres", "Alta Floresta", "Primavera do Leste", "Barra do Garças", "Lucas do Rio Verde", "Juína", "Nobres"]},
    "Mato Grosso do Sul": {"capital": "Campo Grande", "cidades": ["Campo Grande", "Dourados", "Três Lagoas", "Corumbá", "Ponta Porã", "Naviraí", "Sidrolândia", "Aquidauana", "Maracaju", "Sonora", "Costa Rica"]},
    "Distrito Federal": {"capital": "Brasília", "cidades": ["Brasília", "Águas Claras", "Taguatinga", "Ceilândia", "Gama", "Samambaia", "Planaltina", "Guará", "Recanto das Emas", "Lago Sul", "Lago Norte"]},

    # Região Sudeste
    "Espírito Santo": {"capital": "Vitória", "cidades": ["Vitória", "Vila Velha", "Serra", "Cariacica", "Linhares", "Colatina", "Aracruz", "Guarapari", "Mariana", "Domingos Martins", "Sooretama", "Anchieta"]},
    "Minas Gerais": {"capital": "Belo Horizonte", "cidades": ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim", "Montes Claros", "Ribeirão Preto", "Uberaba", "Governador Valadares", "Ipatinga", "Poços de Caldas", "Guanabacaba", "Ouro Preto", "Diamantina", "Curitiba", "Pouso Alegre", "Varginha", "Teófilo Otoni", "Pará de Minas", "Divinópolis"]},
    "Rio de Janeiro": {"capital": "Rio de Janeiro", "cidades": ["Rio de Janeiro", "São Gonçalo", "Duque de Caxias", "Nova Iguaçu", "Niterói", "Campos dos Goytacazes", "São João de Meriti", "Belford Roxo", "Petrópolis", "Volta Redonda", "Macaé", "Cabo Frio", "Niterói", "Angra dos Reis", "Itaguaí", "Queimados", "Nilópolis", "Mesquita", "Magé", "Seropédica"]},
    "São Paulo": {"capital": "São Paulo", "cidades": ["São Paulo", "Guarulhos", "Campinas", "São Bernardo do Campo", "São José dos Campos", "Santos", "Ribeirão Preto", "Sorocaba", "Mauriti", "São José do Rio Preto", "Mogi das Cruzes", "Lorena", "Carapicuíba", "Osasco", "Santo André", "Praia Grande", "Taubaté", "Bauru", "Jundiaí", "Piracicaba", "Presidente Prudente", "Marília", "Franca", "Araraquara", "São Carlos", "Ribeirão Preto", "Jacareí", "Itu", "Salto", "Mauá", "Diadema", "Taboão da Serra"]},

    # Região Sul
    "Paraná": {"capital": "Curitiba", "cidades": ["Curitiba", "Londrina", "Maringá", "Ponta Grossa", "Cascavel", "Foz do Iguaçu", "Palmas", "São José dos Pinhais", "Colombo", "Toledo", "Mauá", "Apucarana", "Lapa", "Umuarama", "Pato Branco", "Arapongas", "Faxinal"]},
    "Rio Grande do Sul": {"capital": "Porto Alegre", "cidades": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Novo Hamburgo", "Santa Maria", "Gravataí", "Viamão", "Cachoeirinha", "Uruguaiana", "Santa Cruz do Sul", "Erechim", "Passo Fundo", "Santana do Livramento", "Bage", "Santo Ângelo", "Torres", "Camaquã", "Sapucaia do Sul", "Viamão"]},
    "Santa Catarina": {"capital": "Florianópolis", "cidades": ["Florianópolis", "Joinville", "Blumenau", "São José", "Itajaí", "Chapecó", "Criciúma", "Tubarão", "Lages", "Palhoça", "São Francisco do Sul", "Rio do Sul", "Brusque", "Camboriú", "Curitibanos", "Araranguá", "Canoinhas", "Xanxerê", "Concórdia", "São Miguel do Oeste"]},
}

# Lista flat de todas as capitais para busca rápida
CAPITAIS_ESTADOS = {
    "Rio Branco": "Acre",
    "Maceió": "Alagoas",
    "Manaus": "Amazonas",
    "Macapá": "Amapá",
    "Belém": "Pará",
    "Porto Velho": "Rondônia",
    "Boa Vista": "Roraima",
    "Palmas": "Tocantins",
    "Salvador": "Bahia",
    "Feira de Santana": "Bahia",
    "Fortaleza": "Ceará",
    "São Luís": "Maranhão",
    "João Pessoa": "Paraíba",
    "Recife": "Pernambuco",
    "Teresina": "Piauí",
    "Natal": "Rio Grande do Norte",
    "João Pessoa": "Paraíba",
    "Porto Alegre": "Rio Grande do Sul",
    "Goiânia": "Goiás",
    "Cuiabá": "Mato Grosso",
    "Campo Grande": "Mato Grosso do Sul",
    "Brasília": "Distrito Federal",
    "Vitória": "Espírito Santo",
    "Belo Horizonte": "Minas Gerais",
    "Rio de Janeiro": "Rio de Janeiro",
    "São Paulo": "São Paulo",
    "Curitiba": "Paraná",
    "Florianópolis": "Santa Catarina",
}

# Lista de todas as capitais
TODAS_CAPITAIS = list(CAPITAIS_ESTADOS.keys())

# =============================================================================
# Modelos de Trabalho Suportados e seus Sinônimos
# =============================================================================
MODELOS_TRABALHO = {
    "remoto": {
        "sinonimos": ["remote", "home office", "work from home", "100% remote", "telecommute", "homeoffice", "home-office", "full remote", "distância", "online", "remotely", "wfh", "work from anywhere"],
        "descricao": "Trabalho integralmente remoto, sem necessidade de presença física"
    },
    "híbrido": {
        "sinonimos": ["hybrid", "semi-presencial", "semi presencial", "mixto", "mixto", "hybrido", "híbrido", "partially remote", "partially on-site", "flexível", "flexible", "blended"],
        "descricao": "Modelo misto, combinando trabalho remoto e presencial"
    },
    "presencial": {
        "sinonimos": ["on-site", "in-person", "presencial", "presencial", "presencial", "local", "presencial", "presencial", "no remote", "full-time on-site", "no hybrid", "exclusivo presencial", "presencial"],
        "descricao": "Trabalho exclusivamente presencial no local da empresa"
    },
}

# Lista flat de todos os sinônimos mapeados para o modelo principal
MAPA_MODELOS = {}
for modelo, info in MODELOS_TRABALHO.items():
    MAPA_MODELOS[modelo] = modelo
    for sinonimo in info["sinonimos"]:
        MAPA_MODELOS[sinonimo.lower()] = modelo

# =============================================================================
# Fontes de Vagas Suportadas com Nomes Corretos para a API
# =============================================================================
FONTES_VAGAS = {
    "serpapi": {
        "nome_api": "SERP API",
        "nome_friendly": "Google Jobs (SERP)",
        "descricao": "Busca de vagas via Google Search Results",
        "requer_api_key": True,
    },
    "jooble": {
        "nome_api": "Jooble API",
        "nome_friendly": "Jooble",
        "descricao": "Plataforma de busca de vagas agregada",
        "requer_api_key": True,
    },
    "rapidapi": {
        "nome_api": "RapidAPI",
        "nome_friendly": "RapidAPI Hub",
        "descricao": "Hub de APIs com múltiplas fontes de vagas",
        "requer_api_key": True,
    },
    "indeed": {
        "nome_api": "Indeed",
        "nome_friendly": "Indeed",
        "descricao": "Maior portal de vagas do mundo",
        "requer_api_key": True,
    },
    "glassdoor": {
        "nome_api": "Glassdoor",
        "nome_friendly": "Glassdoor",
        "descricao": "Portal de vagas e avaliações de empresas",
        "requer_api_key": True,
    },
    "linkedin": {
        "nome_api": "LinkedIn Jobs",
        "nome_friendly": "LinkedIn",
        "descricao": "Rede profissional e portal de vagas",
        "requer_api_key": True,
    },
    "indeed": {
        "nome_api": "Indeed",
        "nome_friendly": "Indeed",
        "descricao": "Portal de vagas",
        "requer_api_key": True,
    },
    "adzuna": {
        "nome_api": "Adzuna",
        "nome_friendly": "Adzuna",
        "descricao": "Agregador de vagas de emprego",
        "requer_api_key": True,
    },
    "ziprecruiter": {
        "nome_api": "ZipRecruiter",
        "nome_friendly": "ZipRecruiter",
        "descricao": "Plataforma de recrutamento",
        "requer_api_key": True,
    },
    "trabalhabrasil": {
        "nome_api": "TrabalhaBrasil",
        "nome_friendly": "Trabalha Brasil",
        "descricao": "Portal de vagas brasileiro",
        "requer_api_key": False,
    },
    "catari": {
        "nome_api": "Catho",
        "nome_friendly": "Catho",
        "descricao": "Portal de vagas especializado",
        "requer_api_key": True,
    },
}

# Lista de todas as fontes ativas
FONTES_ATIVAS = list(FONTES_VAGAS.keys())

# =============================================================================
# Configurações de Timeouts para Requisições HTTP
# =============================================================================
TIMEOUTS_HTTP = {
    "conexao": 10,       # Timeout de conexão em segundos
    "leitura": 30,       # Timeout de leitura/resposta em segundos
    "escrita": 15,       # Timeout de envio de dados em segundos
    "geral": 30,         # Timeout geral padrão em segundos
    "curto": 10,         # Timeout para operações rápidas
    "longo": 60,         # Timeout para operações demoradas
}

# =============================================================================
# Limites de Resultados por Página para Cada API
# =============================================================================
LIMITES_POR_PAGINA = {
    "serpapi": {
        "default": 10,
        "max": 100,
        "descricao": "Resultados por página do Google Jobs",
    },
    "jooble": {
        "default": 20,
        "max": 50,
        "descricao": "Resultados por página do Jooble",
    },
    "rapidapi": {
        "default": 20,
        "max": 50,
        "descricao": "Resultados por página do RapidAPI",
    },
    "indeed": {
        "default": 15,
        "max": 50,
        "descricao": "Resultados por página do Indeed",
    },
    "glassdoor": {
        "default": 15,
        "max": 50,
        "descricao": "Resultados por página do Glassdoor",
    },
    "linkedin": {
        "default": 10,
        "max": 50,
        "descricao": "Resultados por página do LinkedIn",
    },
    "adzuna": {
        "default": 20,
        "max": 50,
        "descricao": "Resultados por página do Adzuna",
    },
    "ziprecruiter": {
        "default": 20,
        "max": 50,
        "descricao": "Resultados por página do ZipRecruiter",
    },
    "trabalhabrasil": {
        "default": 20,
        "max": 50,
        "descricao": "Resultados por página do TrabalhaBrasil",
    },
    "catari": {
        "default": 15,
        "max": 50,
        "descricao": "Resultados por página da Catho",
    },
}

# Configurações padrão de paginação
PAGINACAO_PADRAO = {
    "pagina": 1,
    "itens_por_pagina": 20,
    "max_itens_por_pagina": 50,
}

# =============================================================================
# Status das APIs Configuradas
# =============================================================================
API_STATUS = {
    "serpapi": {
        "ativo": False,
        "api_key_configurada": bool(os.getenv("SERPAPI_KEY", "") != "YOUR_API_KEY_HERE" and os.getenv("SERPAPI_KEY", "")),
        "nome": "SERP API",
        "versao": "v1",
        "ultima_verificacao": None,
        "ultimo_status": None,
        "notas": "Configurar SERPAPI_KEY no .env",
    },
    "jooble": {
        "ativo": False,
        "api_key_configurada": bool(os.getenv("JOOBLE_API_KEY", "") != "YOUR_API_KEY_HERE" and os.getenv("JOOBLE_API_KEY", "")),
        "nome": "Jooble API",
        "versao": "v1",
        "ultima_verificacao": None,
        "ultimo_status": None,
        "notas": "Configurar JOOBLE_API_KEY no .env",
    },
    "rapidapi": {
        "ativo": False,
        "api_key_configurada": bool(os.getenv("RAPIDAPI_KEY", "") != "YOUR_API_KEY_HERE" and os.getenv("RAPIDAPI_KEY", "")),
        "nome": "RapidAPI Hub",
        "versao": "v1",
        "ultima_verificacao": None,
        "ultimo_status": None,
        "notas": "Configurar RAPIDAPI_KEY no .env",
    },
    "indeed": {
        "ativo": False,
        "api_key_configurada": bool(os.getenv("RAPIDAPI_KEY", "") != "YOUR_API_KEY_HERE" and os.getenv("RAPIDAPI_KEY", "")),
        "nome": "Indeed",
        "versao": "v2",
        "ultima_verificacao": None,
        "ultimo_status": None,
        "notas": "Usa RAPIDAPI_KEY e fallback Indeed11, Indeed12 e JSearch",
    },
    "glassdoor": {
        "ativo": False,
        "api_key_configurada": bool(os.getenv("GLASSDOOR_API_KEY", "") != "YOUR_API_KEY_HERE" and os.getenv("GLASSDOOR_API_KEY", "")),
        "nome": "Glassdoor",
        "versao": "v1",
        "ultima_verificacao": None,
        "ultimo_status": None,
        "notas": "Configurar GLASSDOOR_API_KEY no .env",
    },
}

# Status resumido das APIs
def get_api_status_resumido() -> dict:
    """Retorna um resumo do status de todas as APIs."""
    resumo = {}
    for api, status in API_STATUS.items():
        resumo[api] = {
            "ativo": status["ativo"],
            "api_key_configurada": status["api_key_configurada"],
            "nome": status["nome"],
        }
    return resumo

# Configurações de busca
DEFAULT_LOCATIONS = ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Porto Alegre", "Salvador", "Brasília", "Recife", "Curitiba", "Florianópolis", "Fortaleza", "Manaus", "Campo Grande"]
DEFAULT_MODELS = ["remoto", "híbrido", "presencial"]

# Score thresholds
COMPATIBILITY_HIGH = 80  # % - altas chances
COMPATIBILITY_MEDIUM = 60  # % - boas chances
COMPATIBILITY_LOW = 40  # % - chance baixa

# Cache de vagas (em memória por X minutos)
JOB_CACHE_MINUTES = 30

# =============================================================================
# Configurações Adicionais do Sistema
# =============================================================================
# Cache de candidatas em memória (TTL em segundos)
CANDIDATO_CACHE_TTL_SECONDS = 3600  # 1 hora

# Limite máximo de candidatos por busca
MAX_CANDIDATOS_POR_BUSCA = 100

# Timeout de expiração de dados em segundos (24 horas)
DEFAULT_EXPIRATION_SECONDS = 86400

# Idiomas suportados
IDIOMAS_SUPORTADOS = ["pt-BR", "en-US", "es-ES", "en"]

# Formato de data padrão
DATA_FORMATO = "%d/%m/%Y"
