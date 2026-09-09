"""
VagaMatch - Scraper de vagas via múltiplas APIs
Suporta: Google Jobs (SerpAPI), Jooble, Indeed (RapidAPI), Glassdoor (RapidAPI), JSearch (RapidAPI)
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
import json
import time
from functools import lru_cache

from config import (
    SERPAPI_KEY, JOOBLE_API_KEY, RAPIDAPI_KEY,
    INDERED_API_KEY, GLASSDOOR_API_KEY, JOB_CACHE_MINUTES
)


# ========== CACHE DE VAGAS ==========

# Cache simples em memória com TTL
_vagas_cache: Dict[str, Dict] = {}
_cache_ttl = JOB_CACHE_MINUTES * 60  # em segundos


def _cache_get(chave: str) -> Optional[List[Dict]]:
    """Obtém vagas do cache se ainda são válidas."""
    if chave in _vagas_cache:
        dado = _vagas_cache[chave]
        if time.time() - dado['_timestamp'] < _cache_ttl:
            return dado['vagas']
        else:
            del _vagas_cache[chave]
    return None


def _cache_set(chave: str, vagas: List[Dict]) -> None:
    """Salva vagas no cache."""
    _vagas_cache[chave] = {
        'vagas': vagas,
        '_timestamp': time.time()
    }


def _gerar_cache_key(query: str, location: str, fontes: List[str]) -> str:
    """Gera chave de cache baseada nos parâmetros de busca."""
    return f"{query}_{location}_{hash(tuple(sorted(fontes))) if fontes else 'all'}"


def _traduzir_termo_busca(query: str) -> str:
    """
    Traduz termos de busca do inglês para português para melhorar resultados no Brasil.
    Retorna o termo original se já estiver em português.
    """
    query_lower = query.lower().strip()

    # Mapeamento de termos em inglês para português
    # Ordem importa: termos compostos primeiro
    traducoes = {
        # Termos compostos (mais específicos primeiro)
        "full stack developer": "desenvolvedor fullstack",
        "backend developer": "desenvolvedor backend",
        "frontend developer": "desenvolvedor frontend",
        "data scientist": "cientista de dados",
        "data engineer": "engenheiro de dados",
        "software engineer": "engenheiro de software",
        "devops engineer": "engenheiro devops",
        "senior developer": "desenvolvedor sênior",
        "junior developer": "desenvolvedor júnior",
        "lead developer": "desenvolvedor líder",
        "full stack": "fullstack",
        "machine learning": "machine learning",

        # Termos simples
        "developer": "desenvolvedor",
        "engineer": "engenheiro",
        "analyst": "analista",
        "manager": "gerente",
        "senior": "sênior",
        "junior": "júnior",
        "lead": "líder",
        "architect": "arquiteto",
        "frontend": "frontend",
        "backend": "backend",
        "fullstack": "fullstack",
        "devops": "devops",
        "cloud": "nuvem",
    }

    # Verificar se o termo já está em português
    # Apenas palavras inequivocamente em português (não "frontend"/"backend" que são iguais)
    palavras_portugues = ["desenvolvedor", "analista", "programador", "engenheiro", "cientista", "pleno"]
    for palavra in palavras_portugues:
        if palavra in query_lower:
            return query  # Já está em português

    # Traduzir termos compostos primeiro (ordenar por tamanho decrescente)
    for termo_ingles in sorted(traducoes.keys(), key=len, reverse=True):
        if termo_ingles in query_lower:
            query_lower = query_lower.replace(termo_ingles, traducoes[termo_ingles])

    # Se a query foi alterada, retorna a versão traduzida
    if query_lower != query.lower().strip():
        # Capitalizar cada palavra
        return ' '.join(word.capitalize() for word in query_lower.split())

    return query


# ========== NORMALIZAÇÃO DE LOCALIZAÇÃO ==========

# Mapeamento completo de estados brasileiros
ESTADOS_BRASIL = {
    "ac": "Acre", "al": "Alagoas", "ap": "Amapá", "am": "Amazonas",
    "ba": "Bahia", "ce": "Ceará", "df": "Distrito Federal", "es": "Espírito Santo",
    "go": "Goiás", "ma": "Maranhão", "mt": "Mato Grosso", "ms": "Mato Grosso do Sul",
    "mg": "Minas Gerais", "pa": "Pará", "pb": "Paraíba", "pr": "Paraná",
    "pe": "Pernambuco", "pi": "Piauí", "rj": "Rio de Janeiro", "rn": "Rio Grande do Norte",
    "rs": "Rio Grande do Sul", "ro": "Rondônia", "rr": "Roraima", "sc": "Santa Catarina",
    "sp": "São Paulo", "se": "Sergipe", "to": "Tocantins"
}

# Cidades brasileiras principais para mapeamento direto
PRINCIPAIS_CIDADES = {
    # São Paulo
    "araraquara": "Araraquara, São Paulo, Brazil",
    "campinas": "Campinas, São Paulo, Brazil",
    "santos": "Santos, São Paulo, Brazil",
    "são josé dos campos": "São José dos Campos, São Paulo, Brazil",
    "ribeirão preto": "Ribeirão Preto, São Paulo, Brazil",
    "sorocaba": "Sorocaba, São Paulo, Brazil",
    "bauru": "Bauru, São Paulo, Brazil",
    "mogi mirim": "Mogi Mirim, São Paulo, Brazil",
    "limeira": "Limeira, São Paulo, Brazil",
    "piracicaba": "Piracicaba, São Paulo, Brazil",
    " São paulo": "São Paulo, São Paulo, Brazil",
    # Rio de Janeiro
    "rio de janeiro": "Rio de Janeiro, Rio de Janeiro, Brazil",
    "niterói": "Niterói, Rio de Janeiro, Brazil",
    "duque de caxias": "Duque de Caxias, Rio de Janeiro, Brazil",
    "nova iguaçu": "Nova Iguaçu, Rio de Janeiro, Brazil",
    # Minas Gerais
    "belo horizonte": "Belo Horizonte, Minas Gerais, Brazil",
    "uberlândia": "Uberlândia, Minas Gerais, Brazil",
    "contagem": "Contagem, Minas Gerais, Brazil",
    "juiz de fora": "Juiz de Fora, Minas Gerais, Brazil",
    "betim": "Betim, Minas Gerais, Brazil",
    # Bahia
    "salvador": "Salvador, Bahia, Brazil",
    "feira de santana": "Feira de Santana, Bahia, Brazil",
    "vitoria da conquista": "Vitória da Conquista, Bahia, Brazil",
    # Paraná
    "curitiba": "Curitiba, Paraná, Brazil",
    "londrina": "Londrina, Paraná, Brazil",
    "maringá": "Maringá, Paraná, Brazil",
    # Rio Grande do Sul
    "porto alegre": "Porto Alegre, Rio Grande do Sul, Brazil",
    "caxias do sul": "Caxias do Sul, Rio Grande do Sul, Brazil",
    "pelotas": "Pelotas, Rio Grande do Sul, Brazil",
    # Pernambuco
    "recife": "Recife, Pernambuco, Brazil",
    "jaboatão dos guararapes": "Jaboatão dos Guararapes, Pernambuco, Brazil",
    # Ceará
    "fortaleza": "Fortaleza, Ceará, Brazil",
    # Distrito Federal
    "brasília": "Brasília, Distrito Federal, Brazil",
    # Goiás
    "goiânia": "Goiânia, Goiás, Brazil",
    # Santa Catarina
    "florianópolis": "Florianópolis, Santa Catarina, Brazil",
    "joinville": "Joinville, Santa Catarina, Brazil",
    # Amazonas
    "manaus": "Manaus, Amazonas, Brazil",
}


def _normalizar_localizacao(location: str) -> Optional[str]:
    """
    Normaliza a localização informada para formato válido do SerpAPI.
    Suporta formatos: "Brasil", "São Paulo", "SP", "Araraquara-SP", "Remote", etc.
    Retorna None se não for possível mapear.
    """
    if not location:
        return None

    loc_raw = location.strip()
    loc_lower = loc_raw.lower()

    # Mapeamento de estados -> nome no SerpAPI
    estados = {
        "sp": "São Paulo",
        "rj": "Rio de Janeiro",
        "mg": "Minas Gerais",
        "rs": "Rio Grande do Sul",
        "ba": "Bahia",
        "df": "Distrito Federal",
        "pe": "Pernambuco",
        "pr": "Paraná",
        "sc": "Santa Catarina",
        "ce": "Ceará",
        "am": "Amazonas",
        "ms": "Mato Grosso do Sul",
        "go": "Goiás",
        "es": "Espírito Santo",
        "pb": "Paraíba",
        "rn": "Rio Grande do Norte",
        "mt": "Mato Grosso",
        "ma": "Maranhão",
        "pa": "Pará",
    }

    # Países
    if loc_lower in ("brasil", "br", "brazil"):
        return "Brazil"
    # Para o SerpAPI, "Remote" nao funciona como location.
    # Devolvemos "Brazil" e a busca sera feita com todo o territorio;
    # o filtro por modelo de trabalho sera aplicado depois.
    if loc_lower in ("remote", "remoto"):
        return "Brazil"

    # Formato "Cidade-Estado" (ex: "Araraquara-SP", "Sao Paulo-SP", "São Paulo-SP")
    if "-" in loc_raw:
        # Separar cidade e estado
        city_part, state_part = loc_raw.rsplit("-", 1)
        city = city_part.strip()
        state = state_part.strip().lower().replace(".", "")

        # Normalizar cidade (remover acentos e espaços) para busca no mapeamento
        city_norm = city.lower().replace("ã", "a").replace("é", "e").replace("í", "i").replace("õ", "o").replace("ú", "u").replace("ç", "c")
        city_norm = city_norm.replace(" ", "")

        # Verificar se a cidade está no mapeamento de cidades conhecidas
        for key, value in PRINCIPAIS_CIDADES.items():
            key_norm = key.lower().replace("ã", "a").replace("é", "e").replace("í", "i").replace("õ", "o").replace("ú", "u").replace("ç", "c")
            key_norm = key_norm.replace(" ", "")
            if key_norm == city_norm:
                return value

        # Se for sigla de estado, transformar para nome completo
        state_name = ESTADOS_BRASIL.get(state, state)

        # Capitalizar primeira letra da cidade
        if city:
            city = city[0].upper() + city[1:].lower()

        return f"{city}, {state_name}, Brazil"

    # Verificar se é uma cidade principal conhecida
    if loc_lower in PRINCIPAIS_CIDADES:
        return PRINCIPAIS_CIDADES[loc_lower]

    # Verificar se é apenas um estado
    if loc_lower in ESTADOS_BRASIL:
        return f"{ESTADOS_BRASIL[loc_lower]}, {ESTADOS_BRASIL[loc_lower]}, Brazil"

    # Cidades/estados conhecidos (fallback)
    cidades = {
        "sao paulo": "São Paulo, São Paulo, Brazil",
        "são paulo": "São Paulo, São Paulo, Brazil",
        "sp": "São Paulo, São Paulo, Brazil",
        "rio de janeiro": "Rio de Janeiro, Rio de Janeiro, Brazil",
        "rj": "Rio de Janeiro, Rio de Janeiro, Brazil",
        "belo horizonte": "Belo Horizonte, Minas Gerais, Brazil",
        "bh": "Belo Horizonte, Minas Gerais, Brazil",
        "porto alegre": "Porto Alegre, Rio Grande do Sul, Brazil",
        "salvador": "Salvador, Bahia, Brazil",
        "brasilia": "Brasília, Distrito Federal, Brazil",
        "recife": "Recife, Pernambuco, Brazil",
        "curitiba": "Curitiba, Paraná, Brazil",
        "florianopolis": "Florianópolis, Santa Catarina, Brazil",
        "fortaleza": "Fortaleza, Ceará, Brazil",
        "manaus": "Manaus, Amazonas, Brazil",
        "campo grande": "Campo Grande, Mato Grosso do Sul, Brazil",
    }

    return cidades.get(loc_lower)


def _normalizar_localizacao_jooble(location: str) -> str:
    """Normaliza localização para formato Jooble (cidade, país)."""
    if not location or location.lower() in ("brasil", "br", ""):
        return "Brazil"
    if location.lower() in ("remote", "remoto"):
        return "Remote"

    # Formato "Cidade-Estado"
    if "-" in location:
        city_part, state_part = location.rsplit("-", 1)
        return f"{city_part.strip()}, Brazil"

    return f"{location.strip()}, Brazil"


def _normalizar_localizacao_indeed(location: str) -> str:
    """Normaliza localização para formato Indeed (cidade, estado)."""
    if not location or location.lower() in ("brasil", "br", ""):
        return "Brazil"
    if location.lower() in ("remote", "remoto"):
        return "Remote"

    # Formato "Cidade-Estado"
    if "-" in location:
        city_part, state_part = location.rsplit("-", 1)
        return f"{city_part.strip()}, {state_part.strip()}"

    return location.strip()


def _normalizar_localizacao_glassdoor(location: str) -> str:
    """Normaliza localização para formato Glassdoor (cidade)."""
    if not location or location.lower() in ("brasil", "br", ""):
        return "Brazil"
    if location.lower() in ("remote", "remoto"):
        return "Remote"

    # Formato "Cidade-Estado"
    if "-" in location:
        city_part, state_part = location.rsplit("-", 1)
        return city_part.strip()

    return location.strip()


def _normalizar_localizacao_jsearch(location: str) -> str:
    """Normaliza localização para formato JSearch (cidade, país)."""
    if not location or location.lower() in ("brasil", "br", ""):
        return "Brazil"
    if location.lower() in ("remote", "remoto"):
        return "Remote"

    # Formato "Cidade-Estado"
    if "-" in location:
        city_part, state_part = location.rsplit("-", 1)
        return f"{city_part.strip()}, Brazil"

    return location.strip()


def _filtrar_apenas_cidade(vagas: List[Dict], localizacao_usuario: str) -> List[Dict]:
    """
    Filtra vagas APENAS pela cidade especificada (não pelo estado).
    Quando o usuario busca "Araraquara-SP", a busca no SerpAPI foi feita
    para o estado inteiro (mais permissivo). Aqui isolamos apenas vagas
    cuja localizacao realmente contenha a cidade informada.
    A comparacao e feita exclusivamente no campo 'location' da vaga.
    Se nao encontrar nenhuma vaga, retorna todas (fallback).
    """
    if "-" not in localizacao_usuario:
        return _filtrar_por_regiao(vagas, localizacao_usuario)

    city_part, state_part = localizacao_usuario.rsplit("-", 1)
    cidade = city_part.strip().lower()

    # Versao sem acentos da cidade de busca
    cidade_sem_acento = (
        cidade.replace("ã", "a").replace("é", "e").replace("í", "i")
        .replace("õ", "o").replace("ú", "u").replace("ç", "c")
        .replace("á", "a").replace("ê", "e").replace("ô", "o")
    )

    # Lista de cidades conhecidas do estado (para evitar falsos positivos
    # quando o usuario busca uma cidade pequena e o SerpAPI devolve SP/Campinas)
    cidades_grandes_estado = {
        "sp": ["são paulo", "sao paulo", "campinas", "santos", "são josé dos campos", "ribeirão preto", "sorocaba", "guarulhos", "osasco", "são bernardo do campo", "são carlos"],
        "rj": ["rio de janeiro", "niteroi", "niterói", "duque de caxias", "nova iguaçu"],
        "mg": ["belo horizonte", "uberlândia", "contagem", "juiz de fora", "betim"],
        "rs": ["porto alegre", "caxias do sul", "pelotas", "canoas"],
        "ba": ["salvador", "feira de santana"],
        "pr": ["curitiba", "londrina", "marínga", "maringá"],
        "sc": ["florianópolis", "florianopolis", "joinville", "blumenau"],
        "pe": ["recife", "jaboatão dos guararapes"],
        "ce": ["fortaleza", "caucaia"],
        "df": ["brasília", "brasilia"],
        "am": ["manaus"],
        "go": ["goiânia", "goiania", "aparecida de goiânia"],
    }

    state_sigla = state_part.strip().lower().replace(".", "")
    cidades_grandes = cidades_grandes_estado.get(state_sigla, [])

    vagas_filtradas = []
    for vaga in vagas:
        loc_vaga = vaga.get("location", "")
        if not loc_vaga:
            continue

        loc_vaga_lower = loc_vaga.lower()
        loc_vaga_sem_acento = (
            loc_vaga_lower.replace("ã", "a").replace("é", "e").replace("í", "i")
            .replace("õ", "o").replace("ú", "u").replace("ç", "c")
            .replace("á", "a").replace("ê", "e").replace("ô", "o")
        )

        # 1) Ignorar vagas com localizacao generica (nao especificam cidade)
        if loc_vaga_lower in ("qualquer lugar", "anywhere", "remote", "remoto",
                               "brasil", "brazil", "todo brasil", "toute brazil",
                               "toda amérique latine"):
            continue

        # 2) Verificar se a cidade do usuario esta NO INICIO da localizacao da vaga
        # (evita falso-positivo: "araraquara" nao deve casar em "São Paulo, SP")
        cidade_match = (
            loc_vaga_lower.startswith(cidade + ",") or
            loc_vaga_lower.startswith(cidade + " -") or
            loc_vaga_lower.startswith(cidade + " (") or
            loc_vaga_lower.startswith(cidade + " |") or
            (loc_vaga_lower.startswith(cidade) and (
                len(loc_vaga_lower) == len(cidade) or
                loc_vaga_lower[len(cidade):len(cidade)+1] in (",", " ", "|", ")")
            ))
        )
        if not cidade_match:
            # Tentar versão sem acento
            cidade_match = (
                loc_vaga_sem_acento.startswith(cidade_sem_acento + ",") or
                loc_vaga_sem_acento.startswith(cidade_sem_acento + " -") or
                loc_vaga_sem_acento.startswith(cidade_sem_acento + " (") or
                loc_vaga_sem_acento.startswith(cidade_sem_acento + " |") or
                (loc_vaga_sem_acento.startswith(cidade_sem_acento) and (
                    len(loc_vaga_sem_acento) == len(cidade_sem_acento) or
                    loc_vaga_sem_acento[len(cidade_sem_acento):len(cidade_sem_acento)+1] in (",", " ", "|", ")")
                ))
            )
        if not cidade_match:
            continue

        # 3) Filtro anti-falso-positivo: se a localizacao da vaga for outra
        # cidade grande do estado e nao contiver explicitamente a cidade do
        # usuario (ex: "Araraquara"), descartar.
        eh_outra_cidade_grande = False
        for outra_cidade in cidades_grandes:
            outra_cidade_norm = (
                outra_cidade.replace("ã", "a").replace("é", "e").replace("í", "i")
                .replace("õ", "o").replace("ú", "u").replace("ç", "c")
                .replace("á", "a").replace("ê", "e").replace("ô", "o")
            )
            if (outra_cidade in loc_vaga_lower or outra_cidade_norm in loc_vaga_sem_acento):
                if cidade not in loc_vaga_lower and cidade_sem_acento not in loc_vaga_sem_acento:
                    eh_outra_cidade_grande = True
                    break

        if not eh_outra_cidade_grande:
            vagas_filtradas.append(vaga)

    # Se nao encontrou nenhuma vaga, retornar todas (fallback para o estado)
    if not vagas_filtradas:
        return vagas

    return vagas_filtradas


def _filtrar_por_regiao(vagas: List[Dict], localizacao_usuario: str) -> List[Dict]:
    """
    Filtra vagas pela região especificada.
    Extrai cidade e estado do formato "Cidade-Estado" e compara com a localização da vaga.
    """
    # Extrair cidade e estado da entrada do usuário
    loc_lower = localizacao_usuario.lower()

    # Mapa de cidades para matching flexível
    estado_variacoes = {}
    estados = {
        "sp": "são paulo", "rj": "rio de janeiro", "mg": "minas gerais",
        "rs": "rio grande do sul", "ba": "bahia", "df": "distrito federal",
        "pe": "pernambuco", "pr": "paraná", "sc": "santa catarina",
        "ce": "ceará", "am": "amazonas", "ms": "mato grosso do sul",
        "go": "goiás", "es": "espírito santo", "pb": "paraíba",
        "rn": "rio grande do norte", "mt": "mato grosso", "ma": "maranhão",
        "pa": "pará",
    }

    # Determinar termos de busca para matching
    termos_busca = [loc_lower]

    # Se for formato "Cidade-Estado", adicionar variações
    if "-" in localizacao_usuario:
        city_part, state_part = localizacao_usuario.rsplit("-", 1)
        cidade = city_part.strip()
        state_sigla = state_part.strip().replace(".", "").lower()

        # Adicionar cidade e estado como termos de busca
        if cidade:
            termos_busca.append(cidade.lower())

        if state_sigla in estados:
            state_name = estados[state_sigla]
            termos_busca.append(state_name)

        # Variações da cidade (com/sem acento)
        cidade_acentuada = cidade.lower()
        cidade_sem_acento = cidade_acentuada.replace("ã", "a").replace("é", "e").replace("í", "i").replace("õ", "o").replace("ú", "u").replace("ç", "c").replace("á", "a").replace("ê", "e").replace("ô", "o")
        if cidade_acentuada != cidade_sem_acento:
            termos_busca.append(cidade_sem_acento)
    else:
        # Se for apenas sigla de estado (ex: "SP", "RJ", "MG")
        if loc_lower in estados:
            termos_busca.append(estados[loc_lower])

    # Normalizar termos: remover acentos para matching mais flexível
    termos_normalizados = []
    for t in termos_busca:
        # Remover acentos
        t_sem_acento = t.replace("ã", "a").replace("é", "e").replace("í", "i").replace("õ", "o").replace("ú", "u").replace("ç", "c").replace("á", "a").replace("ê", "e").replace("ô", "o").replace("ã", "a").replace("õ", "o")
        termos_normalizados.append(t.lower())
        if t != t_sem_acento:
            termos_normalizados.append(t_sem_acento)

    vagas_filtradas = []
    for vaga in vagas:
        loc_vaga = vaga.get("location", "").lower()
        # Remover acentos da localização da vaga também
        loc_vaga_sem_acento = loc_vaga.replace("ã", "a").replace("é", "e").replace("í", "i").replace("õ", "o").replace("ú", "u").replace("ç", "c").replace("á", "a").replace("ê", "e").replace("ô", "o")

        for termo in termos_normalizados:
            if termo in loc_vaga or termo in loc_vaga_sem_acento:
                vagas_filtradas.append(vaga)
                break

    return vagas_filtradas


# ========== GOOGLE JOBS (SerpAPI) ==========

def buscar_vagas_google_jobs(
    query: str,
    location: str = "Brasil",
    page: int = 1,
    min_date: str = None  # None = sem filtro de data (mais resultados)
) -> List[Dict]:
    """
    Busca vagas na Google Jobs via SerpAPI.

    Args:
        query: Termo de busca (ex: "analista de sistemas")
        location: Localização ou "Remote"/"Remoto"
        page: Número da página (para paginação)
        min_date: Período mínimo (last_week, last_month)

    Returns:
        Lista de vagas (dicionários)
    """
    # Traduzir termo de busca para português (melhor resultados no Brasil)
    query_original = query
    query = _traduzir_termo_busca(query)
    if query != query_original:
        print(f"[INFO] Termo traduzido: '{query_original}' -> '{query}'")

    # Normalizar localização para o formato do SerpAPI
    normalized_location = _normalizar_localizacao(location)
    if not normalized_location:
        print(f"[AVISO] Localização inválida: {location}")
        return []

    # Armazenar localização original para filtro posterior
    localizacao_original = location

    todas_vagas = []
    links_vistos = set()
    MAX_VAGAS = 40  # suficiente para um card bom sem explodir requests

    # Estratégia de localizações otimizada:
    # 1) Cidade específica (ex: "Araraquara, São Paulo, Brazil") — 2 págs
    # 2) Estado amplo (ex: "São Paulo, São Paulo, Brazil") — 1 pág
    # Evita "Brazil" pois devolve muito lixo e explode custo.
    locations_to_search = [normalized_location]

    if localizacao_original and "-" in localizacao_original:
        city_part, state_part = localizacao_original.rsplit("-", 1)
        state_sigla = state_part.strip().lower().replace(".", "")
        if state_sigla in ESTADOS_BRASIL:
            state_name = ESTADOS_BRASIL[state_sigla]
            state_location = f"{state_name}, {state_name}, Brazil"
            if state_location != normalized_location:
                locations_to_search.append(state_location)

    # Páginas por local: cidade=2, estado=1
    paginas_por_local = {normalized_location: 2}
    for loc in locations_to_search[1:]:
        paginas_por_local[loc] = 1

    for loc in locations_to_search:
        max_pag = paginas_por_local.get(loc, 2)
        for pagina in range(1, max_pag + 1):
            if len(todas_vagas) >= MAX_VAGAS:
                break

            url = "https://serpapi.com/search"
            params = {
                "engine": "google_jobs",
                "q": query,
                "location": loc,
                "hl": "pt-BR",
                "gl": "br",
                "api_key": SERPAPI_KEY,
                "page": pagina,
                "sort": "v"
            }

            try:
                response = requests.get(url, params=params, timeout=30)
                data = response.json()

                if data.get("error"):
                    print(f"[AVISO] SerpAPI ({loc}): {data['error']}")
                    break

                jobs = data.get("jobs_results", [])
                if not jobs:
                    break

                novos = 0
                for job in jobs:
                    link = job.get("source_link", job.get("share_link", ""))
                    if not link or link in links_vistos:
                        continue
                    links_vistos.add(link)

                    apply_link = ""
                    if job.get("apply_options"):
                        apply_link = job["apply_options"][0].get("link", "")
                    elif job.get("source_link"):
                        apply_link = job["source_link"]
                    elif job.get("share_link"):
                        apply_link = job["share_link"]

                    vaga = {
                        "title": job.get("title", ""),
                        "company": job.get("company_name", ""),
                        "location": job.get("location", ""),
                        "description": job.get("description", ""),
                        "link": link,
                        "posted_date": job.get("detected_extensions", {}).get("posted_at", ""),
                        "source": job.get("via", "Google Jobs"),
                        "apply_link": apply_link,
                        "tags": _extrair_tags(job)
                    }
                    todas_vagas.append(vaga)
                    novos += 1

                print(f"[INFO] Google Jobs ({loc}, pág {pagina}): {novos} vagas novas")

                if novos < 3:
                    break

            except requests.RequestException as e:
                print(f"[ERRO] Falha na requisição ({loc}): {e}")
                break
            except Exception as e:
                print(f"[ERRO] Erro inesperado ({loc}): {e}")
                break

    # Filtrar por região se não for "Brasil" ou "Remote"
    if localizacao_original and localizacao_original.lower() not in ("brasil", "br", "remote", "remoto"):
        if "-" in localizacao_original:
            vagas_filtradas = _filtrar_apenas_cidade(todas_vagas, localizacao_original)
            if len(vagas_filtradas) > 0:
                print(f"[INFO] Filtradas {len(vagas_filtradas)} vagas em '{localizacao_original}' de {len(todas_vagas)} total")
                return vagas_filtradas
            else:
                print(f"[INFO] Nenhuma vaga filtrada por cidade em '{localizacao_original}', mostrando {len(todas_vagas)} vagas totais")
        else:
            vagas_filtradas = _filtrar_por_regiao(todas_vagas, localizacao_original)
            print(f"[INFO] Filtradas {len(vagas_filtradas)} vagas em '{localizacao_original}' de {len(todas_vagas)} total")
            return vagas_filtradas

    return todas_vagas


# ========== JOOBLE API ==========

def buscar_vagas_jooble(
    query: str,
    location: str = "Brasil",
    page: int = 1,
    max_results: int = 20
) -> List[Dict]:
    """
    Busca vagas via Jooble API (https://jooble.org/api/about).
    API pública gratuita, requer apenas um api_key.
    """
    if not JOOBLE_API_KEY or JOOBLE_API_KEY == "YOUR_API_KEY_HERE":
        print("[AVISO] Jooble API key não configurada")
        return []

    url = f"https://jooble.org/api/{JOOBLE_API_KEY}"

    # Normalizar localização para formato Jooble
    location_jooble = _normalizar_localizacao_jooble(location)

    payload = {
        "keywords": query,
        "location": location_jooble,
        "page": page
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()

        if data.get("error"):
            print(f"[AVISO] Jooble: {data['error']}")
            return []

        vagas = []
        for job in data.get("jobs", []):
            vaga = {
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "description": job.get("snippet", ""),
                "link": job.get("link", ""),
                "posted_date": job.get("updated", ""),
                "source": "Jooble",
                "apply_link": job.get("link", ""),
                "tags": _extrair_tags({"description": job.get("snippet", "")})
            }
            vagas.append(vaga)
            if len(vagas) >= max_results:
                break

        return vagas

    except requests.RequestException as e:
        print(f"[ERRO] Falha na requisição Jooble: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERRO] Resposta JSON inválida Jooble: {e}")
        return []
    except Exception as e:
        print(f"[ERRO] Erro inesperado Jooble: {e}")
        return []


# ========== INDEED (via RapidAPI) ==========

def buscar_vagas_indeed(
    query: str,
    location: str = "Brasil",
    page: int = 0,
    max_results: int = 20
) -> List[Dict]:
    """
    Busca vagas via Indeed API (RapidAPI: indeed11.p.rapidapi.com).
    Requer RAPIDAPI_KEY configurado no .env
    """
    if not RAPIDAPI_KEY or RAPIDAPI_KEY == "YOUR_API_KEY_HERE":
        print("[AVISO] RapidAPI key não configurada (necessária para Indeed)")
        return []

    url = "https://indeed11.p.rapidapi.com/search"

    # Normalizar localização para formato Indeed
    location_indeed = _normalizar_localizacao_indeed(location)

    querystring = {
        "query": query,
        "location": location_indeed,
        "page_id": str(page),
        "locality": "pt_BR"
    }

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "indeed11.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        data = response.json()

        if data.get("error"):
            print(f"[AVISO] Indeed: {data['error']}")
            return []

        vagas = []
        for job in data.get("jobs", []):
            vaga = {
                "title": job.get("title", ""),
                "company": job.get("company_name", ""),
                "location": job.get("location", ""),
                "description": job.get("description", ""),
                "link": job.get("url", ""),
                "posted_date": job.get("posted_time", ""),
                "source": "Indeed",
                "apply_link": job.get("url", ""),
                "tags": _extrair_tags({"description": job.get("description", "")})
            }
            vagas.append(vaga)
            if len(vagas) >= max_results:
                break

        return vagas

    except requests.RequestException as e:
        print(f"[ERRO] Falha na requisição Indeed: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERRO] Resposta JSON inválida Indeed: {e}")
        return []
    except Exception as e:
        print(f"[ERRO] Erro inesperado Indeed: {e}")
        return []


# ========== GLASSDOOR (via RapidAPI) ==========

def buscar_vagas_glassdoor(
    query: str,
    location: str = "Brasil",
    page: int = 1,
    max_results: int = 20
) -> List[Dict]:
    """
    Busca vagas via Glassdoor API (RapidAPI: glassdoor-api.p.rapidapi.com).
    Requer RAPIDAPI_KEY configurado no .env
    """
    if not RAPIDAPI_KEY or RAPIDAPI_KEY == "YOUR_API_KEY_HERE":
        print("[AVISO] RapidAPI key não configurada (necessária para Glassdoor)")
        return []

    url = "https://glassdoor-api.p.rapidapi.com/jobs/search"

    # Normalizar localização para formato Glassdoor
    location_glassdoor = _normalizar_localizacao_glassdoor(location)

    querystring = {
        "job_title": query,
        "location": location_glassdoor,
        "page": str(page),
        "job_type": "all"
    }

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "glassdoor-api.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        data = response.json()

        if data.get("error"):
            print(f"[AVISO] Glassdoor: {data['error']}")
            return []

        vagas = []
        results = data.get("results", data.get("jobs", []))
        for job in results:
            vaga = {
                "title": job.get("jobTitle", job.get("title", "")),
                "company": job.get("employerName", job.get("company", "")),
                "location": job.get("location", job.get("jobLocation", "")),
                "description": job.get("jobDescription", job.get("description", "")),
                "link": job.get("jobUrl", job.get("url", "")),
                "posted_date": job.get("pubDate", job.get("posted", "")),
                "source": "Glassdoor",
                "apply_link": job.get("jobUrl", job.get("url", "")),
                "tags": _extrair_tags({"description": job.get("jobDescription", job.get("description", ""))})
            }
            vagas.append(vaga)
            if len(vagas) >= max_results:
                break

        return vagas

    except requests.RequestException as e:
        print(f"[ERRO] Falha na requisição Glassdoor: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERRO] Resposta JSON inválida Glassdoor: {e}")
        return []
    except Exception as e:
        print(f"[ERRO] Erro inesperado Glassdoor: {e}")
        return []


# ========== JSEARCH (via RapidAPI - Google Jobs alternativo) ==========

def buscar_vagas_jsearch(
    query: str,
    location: str = "Brasil",
    page: int = 1,
    max_results: int = 20
) -> List[Dict]:
    """
    Busca vagas via JSearch API (RapidAPI: jsearch.p.rapidapi.com).
    Alternativa ao Google Jobs, com mais vagas de diversas fontes.
    Requer RAPIDAPI_KEY configurado no .env
    """
    if not RAPIDAPI_KEY or RAPIDAPI_KEY == "YOUR_API_KEY_HERE":
        print("[AVISO] RapidAPI key não configurada (necessária para JSearch)")
        return []

    url = "https://jsearch.p.rapidapi.com/search"

    # Normalizar localização para formato JSearch
    location_jsearch = _normalizar_localizacao_jsearch(location)

    # Para JSearch, se for cidade específica, usar formato apropriado
    if "-" in location:
        city_part, state_part = location.rsplit("-", 1)
        cidade_jsearch = city_part.strip()
        querystring = {
            "query": f"{query} in {cidade_jsearch}",
            "page": str(page),
            "num_pages": "1",
            "country": "br",
            "language": "pt"
        }
    else:
        querystring = {
            "query": f"{query} in {location_jsearch}",
            "page": str(page),
            "num_pages": "1",
            "country": "br",
            "language": "pt"
        }

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        data = response.json()

        if data.get("status") != "OK" or data.get("error"):
            print(f"[AVISO] JSearch: {data.get('error', 'Erro desconhecido')}")
            return []

        vagas = []
        for job in data.get("data", []):
            vaga = {
                "title": job.get("job_title", ""),
                "company": job.get("employer_name", ""),
                "location": job.get("job_city", job.get("job_location", "")),
                "description": job.get("job_description", ""),
                "link": job.get("job_apply_link", job.get("job_url", "")),
                "posted_date": job.get("job_posted_at_datetime_utc", ""),
                "source": "JSearch",
                "apply_link": job.get("job_apply_link", job.get("job_url", "")),
                "tags": _extrair_tags({"description": job.get("job_description", "")})
            }
            vagas.append(vaga)
            if len(vagas) >= max_results:
                break

        return vagas

    except requests.RequestException as e:
        print(f"[ERRO] Falha na requisição JSearch: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"[ERRO] Resposta JSON inválida JSearch: {e}")
        return []
    except Exception as e:
        print(f"[ERRO] Erro inesperado JSearch: {e}")
        return []


# ========== NORMALIZAÇÃO DE LOCALIZAÇÃO POR API ==========

def _normalizar_localizacao_brasil(location: str) -> dict:
    """Normaliza a localização informada para extrair cidade, estado, sigla e formato SerpAPI."""
    normalized = _normalizar_localizacao(location)
    if not normalized:
        return {"cidade": "", "estado": "", "sigla": "", "formato_serpapi": ""}

    parts = [p.strip() for p in normalized.split(",")]
    cidade = parts[0] if parts else ""
    estado = parts[1] if len(parts) > 1 else ""
    sigla = ""

    estado_sigla = {
        "São Paulo": "SP",
        "Rio de Janeiro": "RJ",
        "Minas Gerais": "MG",
        "Rio Grande do Sul": "RS",
        "Bahia": "BA",
        "Distrito Federal": "DF",
        "Pernambuco": "PE",
        "Paraná": "PR",
        "Santa Catarina": "SC",
        "Ceará": "CE",
        "Amazonas": "AM",
        "Mato Grosso do Sul": "MS",
        "Goiás": "GO",
        "Espírito Santo": "ES",
        "Paraíba": "PB",
        "Rio Grande do Norte": "RN",
        "Mato Grosso": "MT",
        "Maranhão": "MA",
        "Pará": "PA",
    }

    if estado in estado_sigla:
        sigla = estado_sigla[estado]

    return {"cidade": cidade, "estado": estado, "sigla": sigla, "formato_serpapi": normalized}


# ========== BUSCA UNIFICADA ==========

def buscar_vagas_filtradas(
    palavras_chave: List[str],
    tipos_vaga: List[str],
    modelos_trabalho: List[str],
    regioes: List[str],
    max_results: int = 20,
    fontes: List[str] = None,
    recencia_dias: int = 0  # 0 = sem filtro de recência
) -> List[Dict]:
    """
    Busca vagas filtrando por critérios combinados através de múltiplas APIs.

    Args:
        fontes: Lista de fontes para buscar. Opções: "google", "jooble", "indeed",
                "glassdoor", "jsearch". Se None, usa todas disponíveis.
        recencia_dias: Número máximo de dias para buscar vagas recentes (padrão: 0).
                       0 ou None = sem filtro de recência.
    """
    # Verificar cache
    cache_key = _gerar_cache_key(
        " ".join(palavras_chave + tipos_vaga),
        regioes[0] if regioes else "Brasil",
        fontes
    )
    vagas_cacheadas = _cache_get(cache_key)
    if vagas_cacheadas is not None:
        return vagas_cacheadas

    todos_resultados = []
    vagas_unicas = {}  # Evita duplicatas

    # Fontes disponíveis
    fontes_disponiveis = {
        "google": buscar_vagas_google_jobs,
        "jooble": buscar_vagas_jooble,
        "indeed": buscar_vagas_indeed,
        "glassdoor": buscar_vagas_glassdoor,
        "jsearch": buscar_vagas_jsearch,
    }

    # Se não especificou fontes, usar todas
    if not fontes:
        fontes = list(fontes_disponiveis.keys())

    # Construir queries para cada combinação
    # Se tipos_vaga foi fornecido (não-vazio), usar APENAS tipos (já inclui palavras-chave refinadas)
    # Se tipos_vaga está vazio ou None, usar palavras_chave diretamente (sem duplicar)
    if tipos_vaga:
        tipos_para_busca = tipos_vaga
    else:
        tipos_para_busca = palavras_chave
    locais_busca = regioes if regioes else ["Brasil"]

    # Google Jobs só retorna 10 resultados por query (paginação não funciona via SerpAPI).
    # Para obter mais vagas, gerar queries alternativas relacionadas ao termo principal.
    def _gerar_queries_alternativas(query: str) -> List[str]:
        """Gera queries alternativas para maximizar resultados do Google Jobs.

        Google Jobs via SerpAPI não suporta paginação efetiva (retorna sempre 10
        resultados) e repete as mesmas vagas nas páginas. Para obter mais vagas,
        fazemos múltiplas buscas com termos relacionados.
        """
        q_lower = query.strip().lower()
        queries_extra = [query]  # sempre incluir o original

        # Se for um termo único (ex: "python"), gerar variações
        palavras = q_lower.split()
        if len(palavras) <= 2:
            if "python" in q_lower and "desenvolvedor" not in q_lower and "programador" not in q_lower:
                queries_extra.extend([
                    f"desenvolvedor {q_lower}",
                    f"programador {q_lower}",
                ])
            elif "desenvolvedor" in q_lower:
                queries_extra.append(q_lower.replace("desenvolvedor", "programador"))
            elif "engenheiro" in q_lower:
                queries_extra.append(q_lower.replace("engenheiro", "analista"))
            elif "analista" in q_lower:
                # Para "analista", adicionar variações para buscar mais resultados
                # em outras áreas (processos, qualidade, administrativo, etc.)
                queries_extra.extend([
                    f"analista de {q_lower}",  # redundante, mantém consistência
                    f"auxiliar {q_lower}",
                ])
            else:
                # Tenta adicionar prefixos comuns
                for prefixo in ["desenvolvedor", "programador", "analista"]:
                    queries_extra.append(f"{prefixo} {q_lower}")

        return queries_extra

    # Para evitar queries duplicadas (ex: "python python"):
    # - Se tipos_vaga foi passado explicitamente (lista não-vazia), cada tipo já é a query completa
    # - Se tipos_vaga está vazio, usar cada palavra_chave como query direta (não combinar)
    for tipo in tipos_para_busca:
        if tipos_vaga:
            # tipos_vaga foi passado explicitamente - usar cada tipo como query
            queries = [tipo]
        else:
            # tipos_vaga vazio - cada item de tipos_para_busca (que == palavras_chave) já é a query completa
            queries = [tipo]

        # Para Google, expandir queries alternativas para obter mais resultados
        # (SerpAPI não suporta paginação efetiva no motor google_jobs)
        if "google" in fontes:
            queries = _gerar_queries_alternativas(queries[0]) if len(queries) == 1 else queries
            # Remover duplicatas mantendo ordem
            queries = list(dict.fromkeys(queries))

        for query in queries:
            for local in locais_busca:
                for fonte in fontes:
                    func = fontes_disponiveis.get(fonte)
                    if not func:
                        continue

                    try:
                        if fonte == "google":
                            # Google Jobs - sem filtro de data para maximizar resultados
                            vagas = func(query, location=local, min_date=None, page=1)
                        elif fonte == "jsearch":
                            vagas = func(query, location=local, page=1, max_results=max_results)
                        elif fonte == "jooble":
                            vagas = func(query, location=local, page=1, max_results=max_results)
                        else:
                            vagas = func(query, location=local, page=1, max_results=max_results)

                        print(f"[INFO] {fonte.upper()}: {len(vagas)} vagas para '{query}' em '{local}'")

                        # Aplicar filtro de modelo de trabalho
                        for vaga in vagas:
                            desc = vaga.get("description", "").lower()
                            loc = vaga.get("location", "").lower()
                            title_lower = vaga.get("title", "").lower()

                            # Verificar modelo de trabalho (se houver filtro)
                            modelo_ok = True
                            modelos_filtrados = [m.strip().lower() for m in modelos_trabalho if m.strip()]
                            if modelos_filtrados:
                                modelo_ok = False
                                for modelo_lower in modelos_filtrados:
                                    termos = [modelo_lower]
                                    if modelo_lower in ["remoto", "home office", "remote", "telecommute"]:
                                        termos.extend(["remote", "100% home", "trabalho remoto", "home office", "remote-friendly", "100% remote"])
                                    elif modelo_lower in ["híbrido", "hibrido"]:
                                        termos.extend(["hybrid", "semi-presencial", "semi presencial", "hybrid-friendly"])
                                    elif modelo_lower in ["presencial"]:
                                        termos.extend(["on-site", "presencial", "in-office"])

                                    for termo in termos:
                                        if termo in loc or termo in desc or termo in title_lower:
                                            modelo_ok = True
                                            break
                                    if modelo_ok:
                                        break

                            # Aplicar filtro de cidade se for especificado uma cidade no formato "Cidade-Estado"
                            cidade_ok = True
                            if regioes and regioes[0] and "-" in regioes[0]:
                                loc_vaga = vaga.get("location", "").lower()
                                cidade_filtro = regioes[0].rsplit("-", 1)[0].strip().lower()
                                estado_filtro = regioes[0].rsplit("-", 1)[1].strip().lower()
                                loc_vaga_sem_acento = loc_vaga.replace("ã", "a").replace("é", "e").replace("í", "i").replace("õ", "o").replace("ú", "u").replace("ç", "c").replace("á", "a").replace("ê", "e").replace("ô", "o")
                                # ACEITAR se a cidade ou estado estiverem na localização
                                if (cidade_filtro not in loc_vaga and
                                    cidade_filtro not in loc_vaga_sem_acento and
                                    estado_filtro not in loc_vaga and
                                    estado_filtro not in loc_vaga_sem_acento):
                                    cidade_ok = False

                            if modelo_ok and cidade_ok:
                                link = vaga.get("link", "")
                                if link and link not in vagas_unicas:
                                    vagas_unicas[link] = vaga
                                    vagas_unicas[link]["score_relevance"] = _calcular_relevancia(
                                        palavras_chave, tipos_vaga, vaga
                                    )

                    except Exception as e:
                        print(f"[ERRO] Falha ao buscar em {fonte}: {e}")
                        continue

    # Ordenar por relevância e recência (mais recentes primeiro para empates)
    def get_sort_key(vaga):
        score = vaga.get("score_relevance", 0)
        data_posted = _parsear_data_posted(vaga.get("posted_date", ""))
        if data_posted:
            dias = (datetime.now() - data_posted).days
            return (score, -dias)  # Menos dias = mais recente
        return (score, 0)

    resultados = sorted(
        vagas_unicas.values(),
        key=get_sort_key,
        reverse=True
    )

    # Filtrar por recência se solicitado (apenas vagas dos últimos X dias)
    if recencia_dias and recencia_dias > 0:
        resultados_filtrados = []
        for vaga in resultados:
            data_posted = _parsear_data_posted(vaga.get("posted_date", ""))
            if data_posted:
                dias = (datetime.now() - data_posted).days
                # Só filtrar se a data estiver dentro do limite; manter vagas sem data
                if dias <= recencia_dias:
                    resultados_filtrados.append(vaga)
                else:
                    print(f"[INFO] Vaga '{vaga.get('title', '')[:40]}' descartada: {dias} dias > {recencia_dias} limite")
            else:
                # Manter vagas sem data parseável (não podemos determinar a idade)
                resultados_filtrados.append(vaga)
        resultados = resultados_filtrados

    # Salvar no cache
    _cache_set(cache_key, resultados[:max_results])

    return resultados[:max_results]


def _extrair_tags(job: dict) -> List[str]:
    """Extrai tags de modelo de trabalho e habilidades da descrição da vaga."""
    desc = (job.get("description") or "").lower()
    tags_set = set()

    # Habilidades técnicas
    tech_keywords = [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "php", "ruby", "swift", "kotlin",
        "react", "vue", "angular", "svelte",
        "django", "flask", "spring", "laravel", "node.js",
        "mysql", "postgresql", "mongodb", "oracle", "mssql", "redis",
        "aws", "azure", "gcp", "kubernetes", "docker", "terraform",
        "api", "rest", "graphql", "microservices",
        "machine learning", "data science", "ci/cd", "devops"
    ]
    for keyword in tech_keywords:
        if keyword in desc:
            tags_set.add(keyword)

    # Modelos de trabalho
    loc_lower = job.get("company_location", "").lower()
    desc_lower = desc
    title_lower = job.get("title", "").lower()

    # Remote-related tags
    if "remoto" in loc_lower or "remote" in desc_lower or "remote" in title_lower:
        tags_set.add("Remoto")
    if "remote-friendly" in desc_lower:
        tags_set.add("Remote Friendly")
    if "work from home" in desc_lower:
        tags_set.add("Work from home")
    if "home office" in desc_lower:
        tags_set.add("Home office")
    if "100% remote" in desc_lower:
        tags_set.add("100% Remote")
    if "telecommute" in desc_lower:
        tags_set.add("Telecommute")

    # Hybrid-related tags
    if "híbrido" in loc_lower or "hybrid" in desc_lower:
        tags_set.add("Híbrido")
    if "hybrid" in desc_lower:
        tags_set.add("Hybrid")
    if "semi-presencial" in desc_lower or "semi presencial" in desc_lower:
        tags_set.add("Hybrid")  # treat as hybrid
    if "on-site" in loc_lower or "presencial" in desc_lower:
        tags_set.add("On-site")

    return list(tags_set)


def _parsear_data_posted(data_str: str) -> Optional[datetime]:
    """
    Parseia data de diferentes formatos das APIs:
    - Google Jobs: "30 days ago", "1 month ago", "June 15, 2024", "2024-06-15"
    - Jooble: "2024-06-15T10:30:00Z", "2 hours ago"
    - Indeed: "3 days ago", "2024-06-15"
    - Glassdoor: "Jun 15, 2024", "2024-06-15T10:30:00.000Z"
    - JSearch: "2024-06-15T10:30:00.000Z" (ISO 8601 UTC)

    Returns:
        datetime object ou None se não conseguir parsear
    """
    if not data_str:
        return None

    data_str = data_str.strip()
    agora = datetime.now()

    # Formatos ISO 8601 (JSearch, Glassdoor, Jooble)
    formatos_iso = [
        "%Y-%m-%dT%H:%M:%S.%fZ",      # 2024-06-15T10:30:00.000Z
        "%Y-%m-%dT%H:%M:%SZ",         # 2024-06-15T10:30:00Z
        "%Y-%m-%dT%H:%M:%S.%f%z",     # 2024-06-15T10:30:00.000+0000
        "%Y-%m-%dT%H:%M:%S%z",        # 2024-06-15T10:30:00+0000
        "%Y-%m-%d",                   # 2024-06-15
    ]

    for fmt in formatos_iso:
        try:
            return datetime.strptime(data_str, fmt)
        except ValueError:
            continue

    # Formatos textuais relativos (Google Jobs, Indeed, Jooble)
    # "X days ago", "X hours ago", "X weeks ago", "X months ago"
    # "X minutes ago", "X seconds ago"
    import re
    match_relativo = re.match(r"(\d+)\s*(day|days|hour|hours|minute|minutes|second|seconds|week|weeks|month|months)\s*ago", data_str.lower())
    if match_relativo:
        valor = int(match_relativo.group(1))
        unidade = match_relativo.group(2)
        if unidade.startswith("day"):
            return agora - timedelta(days=valor)
        elif unidade.startswith("hour"):
            return agora - timedelta(hours=valor)
        elif unidade.startswith("minute"):
            return agora - timedelta(minutes=valor)
        elif unidade.startswith("second"):
            return agora - timedelta(seconds=valor)
        elif unidade.startswith("week"):
            return agora - timedelta(weeks=valor)
        elif unidade.startswith("month"):
            return agora - timedelta(days=valor * 30)

    # "today", "yesterday"
    if data_str.lower() in ("today", "hoje"):
        return agora
    if data_str.lower() in ("yesterday", "ontem"):
        return agora - timedelta(days=1)

    # Formatos de data completos (Google Jobs: "June 15, 2024")
    formatos_data = [
        "%B %d, %Y",       # June 15, 2024
        "%b %d, %Y",       # Jun 15, 2024
        "%d %B %Y",        # 15 June 2024
        "%d %b %Y",        # 15 Jun 2024
        "%d/%m/%Y",        # 15/06/2024
        "%m/%d/%Y",        # 06/15/2024
        "%Y-%m-%d",        # 2024-06-15
    ]

    for fmt in formatos_data:
        try:
            return datetime.strptime(data_str, fmt)
        except ValueError:
            continue

    # Se chegou aqui, não conseguiu parsear
    return None


def _calcular_relevancia(palavras_chave: List[str], tipos_vaga: List[str], vaga: dict) -> float:
    """Calcula relevância baseada em palavras-chave, tipo da vaga E recência."""
    score = 0
    texto_completo = f"{vaga.get('title', '')} {vaga.get('description', '')}".lower()

    for pk in palavras_chave:
        if pk.lower() in texto_completo:
            score += 10

    for tipo in tipos_vaga:
        if tipo.lower() in texto_completo:
            score += 5

    # Bonus se for recente - usando parser robusto
    data_posted = _parsear_data_posted(vaga.get("posted_date", ""))
    if data_posted:
        dias_diferenca = (datetime.now() - data_posted).days
        if dias_diferenca <= 1:
            score += 15      # Hoje/ontem - muito recente
        elif dias_diferenca <= 3:
            score += 10      # 2-3 dias - recente
        elif dias_diferenca <= 7:
            score += 5       # 4-7 dias - razoavelmente recente
        elif dias_diferenca <= 14:
            score += 2       # 8-14 dias - ainda aceitável
        # >14 dias = sem bônus

    return min(score, 100)


def validar_api_keys() -> Dict[str, bool]:
    """
    Valida quais APIs estão configuradas e retornam um dicionário com o status.

    Returns:
        Dicionário com o status de cada API (True se configurada, False caso contrário)
    """
    return {
        "google": bool(SERPAPI_KEY and SERPAPI_KEY != "YOUR_API_KEY_HERE"),
        "jooble": bool(JOOBLE_API_KEY and JOOBLE_API_KEY != "YOUR_API_KEY_HERE"),
        "indeed": bool(RAPIDAPI_KEY and RAPIDAPI_KEY != "YOUR_API_KEY_HERE"),
        "glassdoor": bool(RAPIDAPI_KEY and RAPIDAPI_KEY != "YOUR_API_KEY_HERE"),
        "jsearch": bool(RAPIDAPI_KEY and RAPIDAPI_KEY != "YOUR_API_KEY_HERE")
    }
