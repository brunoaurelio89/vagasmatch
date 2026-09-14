"""
VagaMatch - Module: Job Matcher
Matching inteligente entre currículo e vagas usando NLP simples
"""
import re
from typing import List, Dict, Set
from config import COMPATIBILITY_HIGH, COMPATIBILITY_MEDIUM

# Habilidades técnicas comuns para expandir matches
SKILL_EXTENSIONS = {
    "python": ["django", "flask", "fastapi", "numpy", "pandas"],
    "java": ["spring", "hibernate", "maven", "gradle"],
    "javascript": ["react", "vue", "angular", "nodejs", "express"],
    "sql": ["mysql", "postgresql", "mssql", "oracle", "sqlite"],
    "data": ["pandas", "numpy", "matplotlib", "sklearn", "tensorflow"],
    "frontend": ["html", "css", "javascript", "react", "vue", "bootstrap"],
    "backend": ["django", "flask", "spring", "laravel", "node"],
    "cloud": ["aws", "azure", "gcp", "docker", "kubernetes"],
    # Add new extensions if needed
}

# Mapeamento de níveis de vaga para termos de busca
NIVEIS_VAGA = {
    "júnior": ["júnior", "junior", "estágio", "estagio", "trainee", "jr"],
    "pleno": ["pleno"],
    "sênior": ["sênior", "senior", "especialista", "lead", "principal", "staff", "arquiteto", "architect"]
}

def extrair_habilidades(texto: str) -> Set[str]:
    """
    Extrai habilidades técnicas de um texto.
    Usa heurísticas baseadas em regex com limites de palavra para evitar falsos positivos.
    """
    texto_lower = texto.lower()
    habilidades = set()

    # Lista completa de habilidades (incluindo novas e em português)
    skill_list = [
        # palavras-chave técnicas (original + novas)
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "php", "ruby", "swift", "kotlin", "sql", "nosql", "mongodb", "redis",
        "react", "vue", "angular", "svelte", "next.js", "nuxt.js",
        "django", "flask", "fastapi", "spring", "laravel", "node.js", "express",
        "html", "css", "bootstrap", "tailwind", "sass", "less",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "git", "github", "gitlab", "ci/cd", "jenkins", "gitlab-ci",
        "api", "rest", "graphql", "microservices", "api rest",
        "machine learning", "ml", "deep learning", "nlp",
        "data science", "data analysis", "pandas", "numpy", "matplotlib",
        "excel", "power bi", "tableau", "looker",
        # Qualidade de software e testes
        "qa", "quality assurance", "qualidade de software",
        "software testing", "software test", "testes de software",
        "testes manuais", "testes automatizados", "automação de testes",
        "test automation", "manual testing", "automated testing",
        "selenium", "cypress", "playwright", "postman", "jmeter",
        "junit", "pytest", "testng", "cucumber", "gherkin", "bdd", "tdd",
        "testes de api", "testes de integração", "testes de regressão",
        "testes funcionais", "testes de performance", "testes de aceitação",
        # novas habilidades técnicas
        "react native", "flutter", "ionic", "android", "ios", "swift", "kotlin",
        "php", "laravel", "symfony", "ruby", "rails", "perl", "powershell",
        "bash", "shell", "linux", "windows", "macos", "vmware", "hyper-v",
        "vagrant", "packer", "consul", "vault", "nomad", "envoy", "grafana",
        "prometheus", "elk", "kibana", "logstash", "beats",
        # habilidades de negócio
        "agile", "scrum", "kanban", "jira", "confluence", "figma", "adobe",
        "photoshop", "illustrator", "indesign",
        # termos em português
        "trabalho remoto", "home office", "hibrido", "presencial",
    ]

    # Cria padrões de regex com limites de palavra
    skill_patterns = []
    for skill in skill_list:
        # Escapa caracteres especiais e substitui espaços por \s+ para termos multi-word
        escaped = re.escape(skill)
        pattern = r'\b' + escaped.replace(' ', r'\s+') + r'\b'
        skill_patterns.append((skill, pattern))

    # Busca cada padrão no texto
    for skill, pattern in skill_patterns:
        if re.search(pattern, texto_lower):
            habilidades.add(skill)

    # Adiciona extensões de habilidades técnicas (se houver)
    for skill in list(habilidades):  # copia para evitar modificação durante iteração
        if skill in SKILL_EXTENSIONS:
            for ext in SKILL_EXTENSIONS[skill]:
                ext_pattern = r'\b' + re.escape(ext).replace(' ', r'\s+') + r'\b'
                if re.search(ext_pattern, texto_lower):
                    habilidades.add(ext)

    return habilidades


def limpar_texto(texto: str) -> str:
    """Remove tags HTML, caracteres especiais e normaliza texto."""
    if not texto:
        return ""

    # Remover tags HTML
    texto = re.sub(r"<[^>]+>", " ", texto)
    # Normalizar whitespace
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def detectar_nivel_candidato(curriculo: dict) -> str:
    """
    Detecta o nível de experiência do candidato baseado no currículo.
    Analisa anos de experiência, formação acadêmica e palavras-chave.

    Returns:
        "júnior", "pleno", "sênior" ou "desconhecido"
    """
    texto = curriculo.get("texto_completo", "").lower()

    # Detectar formação acadêmica
    if re.search(r'\bmestrado\b', texto):
        return "sênior"
    if re.search(r'\bdoutorado\b', texto):
        return "sênior"
    if re.search(r'\bgraduação\b', texto):
        return "pleno"

    # Detectar nível júnior a partir de palavras-chave
    if re.search(r'\bestágio\b', texto) or re.search(r'\bjúnior\b', texto) or re.search(r'\bjunior\b', texto) or re.search(r'\btrainee\b', texto):
        return "júnior"

    # Extrair anos de experiência mencionados
    anos = []
    matches = re.findall(r"(\d+)\s*ano?s?\s*(?:de\s*)?experi[ée]ncia?", texto)
    anos.extend([int(a) for a in matches])

    matches2 = re.findall(r"(\d+)\s*\+?\s*ano?s?", texto)
    anos.extend([int(a) for a in matches2])

    max_anos = max(anos) if anos else 0

    # Determinar nível baseado nos anos (se não foi detectado por formação)
    if max_anos >= 8:
        return "sênior"
    elif max_anos >= 3:
        return "pleno"
    elif max_anos >= 1:
        return "júnior"
    else:
        return "desconhecido"


def detectar_nivel_vaga(vaga: dict) -> str:
    """
    Detecta o nível da vaga baseado no título e descrição.
    """
    texto = f"{vaga.get('title', '')} {vaga.get('description', '')}".lower()

    # Verificar senior (incluindo termos combinados)
    senior_terms = ["sênior", "senior", "especialista", "lead", "principal", "staff", "arquiteto", "architect",
                    "pleno-sênior", "pleno/sênior", "senior/pleno"]
    for termo in senior_terms:
        if re.search(rf'\b{re.escape(termo)}\b', texto):
            return "sênior"

    # Verificar júnior
    junior_terms = ["júnior", "junior", "estágio", "estagio", "trainee", "jr"]
    for termo in junior_terms:
        if re.search(rf'\b{re.escape(termo)}\b', texto):
            return "júnior"

    # Verificar pleno
    if re.search(r'\bpleno\b', texto) or re.search(r'\bplena\b', texto):
        return "pleno"

    return "não especificado"


def calcular_bonus_nivel(nivel_candidato: str, nivel_vaga: str) -> int:
    """
    Calcula bônus/penalidade baseado na compatibilidade entre
    nível do candidato e nível da vaga.
    """
    if nivel_vaga == "não especificado" or nivel_candidato == "desconhecido":
        return 0

    nivel_hierarquia = {"júnior": 1, "pleno": 2, "sênior": 3}
    cand_level = nivel_hierarquia.get(nivel_candidato, 0)
    vaga_level = nivel_hierarquia.get(nivel_vaga, 0)

    if not cand_level or not vaga_level:
        return 0

    diff = cand_level - vaga_level

    if diff == 0:
        # Mesmo nível - candidato ideal
        return 10
    elif diff == 1:
        # Candidato um nível acima - ainda adequado
        return 5
    elif diff >= 2:
        # Candidato muito acima - pode ser overqualified, não priorizar
        return 0
    else:
        # Candidato abaixo - penalizar menos fortemente
        return -10


def parse_curriculo(dados: dict) -> dict:
    """
    Parseia o currículo e extrai informações estruturadas.
    Espera formato com campos como 'nome', 'experiencia', 'educacao', 'habilidades'.
    """
    if not dados:
        return {}

    # Concatenar todos os valores relevantes em um texto
    texto_completo = " ".join([
        str(v) for k, v in dados.items()
        if v and isinstance(v, (str, int, float)) and k.lower() not in ["nome", "educacao", "experiencia", "idiomas"]
    ])

    habilidades_set = extrair_habilidades(texto_completo)

    # Detectar nível do candidato
    nivel_candidato = detectar_nivel_candidato({
        "texto_completo": texto_completo,
        "habilidades": habilidades_set
    })

    return {
        "nome": dados.get("nome", "Candidato"),
        "formacao": dados.get("educacao") or dados.get("formacao", ""),
        "experiencias": dados.get("experiencia") or dados.get("experiencias", ""),
        "idiomas": dados.get("idiomas") or dados.get("languages", ""),
        "habilidades": sorted(list(habilidades_set)),
        "texto_completo": texto_completo,
        "palavras_chave": sorted(list(habilidades_set)),
        "nivel_detectado": nivel_candidato
    }


def calcula_match(curriculo: dict, vaga: dict) -> dict:
    """
    Calcula o match entre currículo e vaga.
    Considera habilidades técnicas, alinhamento de nível, relevância do título e bônus por habilidades diferenciais.
    Retorna score de 0-100 e detalhes de matches/missing.
    """
    if not curriculo or not vaga:
        return {"score": 0, "matches": [], "missing": []}

    vaga_texto = limpar_texto(
        f"{vaga.get('title', '')} {vaga.get('description', '')} {' '.join(vaga.get('tags', []))}"
    )
    vaga_habilidades_set = extrair_habilidades(vaga_texto)
    vaga_habilidades_set.update(vaga.get("tags", []))
    vaga_habilidades = vaga_habilidades_set

    cur_habilidades_raw = curriculo.get("habilidades", [])
    cur_habilidades = set(cur_habilidades_raw) if not isinstance(cur_habilidades_raw, set) else cur_habilidades_raw

    # Interseção de habilidades
    matches = list(cur_habilidades.intersection(vaga_habilidades))
    missing = [h for h in vaga_habilidades if h not in cur_habilidades]

    # Score baseado em porcentagem de skills cobertas
    if vaga_habilidades:
        skill_coverage = len(matches) / len(vaga_habilidades) * 100
    else:
        skill_coverage = 0

    # Detectar níveis
    nivel_candidato = curriculo.get("nivel_detectado") or detectar_nivel_candidato(curriculo)
    nivel_vaga = detectar_nivel_vaga(vaga)

    # Bônus/penalidade baseado em alinhamento de nível
    bonus_nivel = calcular_bonus_nivel(nivel_candidato, nivel_vaga)
    skill_coverage += bonus_nivel

    # Penalidade por muitos missing (reduzida)
    if len(missing) > 5:
        skill_coverage -= (len(missing) - 5) * 1  # menor penalidade

    # Relevância do título da vaga (analista vs desenvolvedor, etc)
    titulo_palavras = set(re.findall(r'\b\w+\b', vaga.get('title', '').lower()))
    habilidades_candidato = cur_habilidades
    overlap_titulo = len(titulo_palavras.intersection(habilidades_candidato))
    if overlap_titulo:
        skill_coverage += min(5, overlap_titulo * 2)  # bônus por correspondência de título

    # Bônus por habilidades "desejadas" ou "diferenciais" mencionadas na descrição
    diferencial_bonus = 0
    desc_lower = vaga.get('description', '').lower()
    diferencial_keywords = ["desejado", "diferencial", "plus", "extra", "nice", "advantage"]
    for kw in diferencial_keywords:
        if kw in desc_lower:
            for skill in habilidades_candidato:
                if re.search(rf'\b{re.escape(skill)}\b', desc_lower):
                    diferencial_bonus += 2
                    break  # conta apenas uma vez por palavra-chave

    skill_coverage += diferencial_bonus

    score = max(0, min(100, int(skill_coverage)))

    # Classificação
    if score >= COMPATIBILITY_HIGH:
        classificacao = "Alta"
        candidatura = "🔥 Forte candidato"
    elif score >= COMPATIBILITY_MEDIUM:
        classificacao = "Média"
        candidatura = "💡 Candidatura viável"
    else:
        classificacao = "Baixa"
        candidatura = "⚠️ Precisa de preparação"

    return {
        "score": score,
        "classificacao": classificacao,
        "candidatura": candidatura,
        "matches": sorted(matches, key=lambda x: x.lower()),
        "missing": sorted(missing[:10], key=lambda x: x.lower()),
        "skills_vaga": sorted(list(vaga_habilidades), key=lambda x: x.lower()),
        "nivel_candidato": nivel_candidato,
        "nivel_vaga": nivel_vaga
    }


def classificar_vaga(match_result: dict) -> str:
    """Classifica a chance de aprovação baseada no score."""
    score = match_result.get("score", 0)

    if score >= 80:
        return "Muito Alta"
    elif score >= 65:
        return "Alta"
    elif score >= 50:
        return "Média-Alta"
    elif score >= 35:
        return "Média"
    else:
        return "Baixa"


def gerar_recomendacoes(curriculo: dict, match_result: dict) -> List[str]:
    """Gera recomendações de aperfeiçoamento."""
    recomendacoes = []

    missing = match_result.get("missing", [])[:5]

    if missing:
        recomendacoes.append(f"Estude: {', '.join(missing[:3])}")

    score = match_result.get("score", 0)

    nivel_candidato = match_result.get("nivel_candidato") or curriculo.get("nivel_detectado", "desconhecido")
    nivel_vaga = match_result.get("nivel_vaga", "não especificado")

    if nivel_vaga != "não especificado" and nivel_candidato != "desconhecido":
        nivel_hierarquia = {"júnior": 1, "pleno": 2, "sênior": 3}
        cand_num = nivel_hierarquia.get(nivel_candidato, 0)
        vaga_num = nivel_hierarquia.get(nivel_vaga, 0)

        if vaga_num > cand_num + 1:
            recomendacoes.append(
                f"Esta vaga é para nível {nivel_vaga.upper()}. Você está no nível {nivel_candidato.upper()}. "
                "Busque vagas de nível semelhante ou inferior."
            )

    if score < 50:
        recomendacoes.append("Recomendado: buscar vagas mais alinhadas ao seu perfil atual")
    elif score < 70:
        recomendacoes.append("Recomendado: atualizar currículo com mais projetos relevantes")

    return recomendacoes


def expandir_habilidades(habilidades: Set[str]) -> Set[str]:
    """
    Dada uma lista de habilidades, retorna um conjunto expandido com habilidades relacionadas.
    Por exemplo, se o candidato tem "python", adiciona automaticamente "django", "flask", "fastapi".
    """
    expanded = set(habilidades)
    for skill in list(habilidades):
        if skill in SKILL_EXTENSIONS:
            for ext in SKILL_EXTENSIONS[skill]:
                expanded.add(ext)
    return expanded


def calcular_compatibilidade_emprego(curriculo: dict, vaga: dict) -> dict:
    """
    Calcula compatibilidade entre candidato e vaga considerando:
    - Skills técnicas
    - Alinhamento de nível
    - Tipo de empresa
    - Tamanho da empresa
    - Localização
    """
    base = calcula_match(curriculo, vaga)
    score = base["score"]

    # Empresa: tipo, tamanho, localização
    empresa_tipo = vaga.get("tipo_empresa", "").lower()
    empresa_tamanho = vaga.get("tamanho_empresa", "").lower()
    empresa_loc = vaga.get("localizacao", "").lower()
    candidato_loc = curriculo.get("localizacao", "").lower()

    # Bônus de localização
    loc_bonus = 0
    if candidato_loc and empresa_loc and candidato_loc == empresa_loc:
        loc_bonus = 10

    # Bônus de tipo de empresa (ex.: cloud, tecnologia)
    tipo_bonus = 0
    if "cloud" in empresa_tipo or "tecnologia" in empresa_tipo or "software" in empresa_tipo:
        # Verifica se o candidato tem habilidades cloud
        if any(h in ("aws", "azure", "gcp", "docker", "kubernetes") for h in curriculo.get("habilidades", [])):
            tipo_bonus = 5

    # Bônus de tamanho da empresa
    size_bonus = 0
    if empresa_tamanho in ("grande", "large"):
        if base["nivel_candidato"] in ("pleno", "sênior"):
            size_bonus = 5

    final_score = min(100, score + loc_bonus + tipo_bonus + size_bonus)

    return {
        "score": final_score,
        "classificacao": base["classificacao"],
        "candidatura": base["candidatura"],
        "detalhes": {
            "loc_bonus": loc_bonus,
            "tipo_bonus": tipo_bonus,
            "size_bonus": size_bonus,
            "nivel_candidato": base["nivel_candidato"],
            "nivel_vaga": base["nivel_vaga"]
        }
    }