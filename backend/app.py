"""
VagaMatch - Backend API (FastAPI)
"""
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import uvicorn

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Garantir que o diretório backend esteja no path
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from config import DEFAULT_JOB_SEARCH_TERM, RESUME_ENCRYPTED
from security import salvar_curriculo, carregar_curriculo
from job_scraper import buscar_vagas_filtradas
from job_matcher import parse_curriculo, calcula_match, classificar_vaga, gerar_recomendacoes
from resume_parser import processar_curriculo_upload

# Inicializar FastAPI
app = FastAPI(
    title="VagaMatch API",
    description="Motor de busca inteligente de vagas compatíveis com seu currículo",
    version="1.0.0"
)

# CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "frontend")), name="static")


# ========== ROTAS PRINCIPAIS ==========

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redireciona para a interface principal"""
    api_path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    if api_path.exists():
        return HTMLResponse(content=api_path.read_text(encoding="utf-8"), media_type="text/html")
    return HTMLResponse(
        content="<h1>VagaMatch API</h1><p>Acesse <a href='/dashboard'>/dashboard</a></p>",
        media_type="text/html"
    )


@app.get("/api/status")
async def status():
    """Verifica se o backend está online"""
    return {"status": "online", "timestamp": datetime.now().isoformat()}


# ========== GESTÃO DE CURRÍCULO ==========

@app.get("/api/resume")
async def get_curriculo():
    """Recupera o currículo salvo"""
    curriculo = carregar_curriculo()
    if curriculo:
        return JSONResponse(content=curriculo)
    return JSONResponse(content={"error": "Nenhum currículo encontrado. Faça upload primeiro."})


@app.post("/api/resume/upload-file")
async def upload_curriculo_arquivo(
    file: UploadFile = File(...)
):
    """
    Recebe um arquivo de currículo (PDF, DOCX, DOC, TXT) e processa
    """
    try:
        # Ler o arquivo
        arquivo_bytes = await file.read()
        filename = file.filename or "curriculo.pdf"

        # Validar tamanho (máx 10MB)
        if len(arquivo_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Arquivo muito grande (máx 10MB)")

        # Validar extensão
        ext_permitidas = [".pdf", ".docx", ".doc", ".txt"]
        ext = Path(filename).suffix.lower()
        if ext not in ext_permitidas:
            raise HTTPException(
                status_code=400,
                detail=f"Formato não suportado. Use: {', '.join(ext_permitidas)}"
            )

        # Processar
        dados_processados = processar_curriculo_upload(filename, arquivo_bytes)

        # Parsear para extrair habilidades
        curriculo_parsed = parse_curriculo({
            "nome": dados_processados["nome"],
            "experiencia": dados_processados["texto_completo"],
            "educacao": "",
            "habilidades": dados_processados["texto_completo"]
        })

        # Adicionar metadados
        curriculo_parsed["arquivo_original"] = filename
        curriculo_parsed["tamanho_arquivo"] = dados_processados["tamanho_arquivo"]
        curriculo_parsed["formato"] = dados_processados["formato"]

        # Salvar
        if salvar_curriculo(curriculo_parsed):
            return JSONResponse(content={
                "success": True,
                "message": f"Currículo '{filename}' processado com sucesso!",
                "curriculo": curriculo_parsed,
                "habilidades_detectadas": len(curriculo_parsed.get("habilidades", []))
            })

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERRO] Falha no processamento: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar arquivo")


@app.delete("/api/resume")
async def delete_curriculo():
    """Remove o currículo salvo"""
    if RESUME_ENCRYPTED.exists():
        RESUME_ENCRYPTED.unlink()
    return {"success": True, "message": "Currículo removido"}


# ========== BUSCAR VAGAS POR PERFIL ==========

@app.post("/api/jobs/search")
async def buscar_vagas_por_perfil(
    termo_busca: str = Form(...),
    regiao: str = Form("Brasil"),
    modelos_trabalho: str = Form(""),
    fontes: str = Form(""),
    nivel_compativel: str = Form("true"),
    ordenacao: str = Form("relevancia"),
    recencia_dias: int = Form(0)
):
    """
    Busca vagas baseado no termo de busca,
    calcula compatibilidade com o currículo e retorna rankeado.

    Filtra opcionalmente por:
    - modelos_trabalho: "remoto,híbrido,presencial" (separado por vírgula)
    - recencia_dias: inteiro (0 = sem filtro, 15 = ultimos 15 dias)
    - ordenacao: "relevancia", "recentes", "distancia"
    - fontes: "linkedin,jobbol,vagas.com,catho" (separado por vírgula)
    - nivel_compativel: "true"/"false" - se true, prioriza vagas compatíveis
      com o nível de experiência detectado do currículo
    """
    # Carregar currículo
    curriculo = carregar_curriculo()
    if not curriculo:
        return JSONResponse(
            content={"error": "Nenhum currículo salvo. Faça upload primeiro."},
            status_code=400
        )

    # O campo continua editável, mas a busca padrão deve permanecer na área
    # de qualidade e testes de software.
    termo_busca = (termo_busca or "").strip() or DEFAULT_JOB_SEARCH_TERM

    # Extrair habilidades do currículo para logs
    habs = curriculo.get("habilidades", [])
    if isinstance(habs, set):
        habs = list(habs)

    # Parsear filtros
    modelos_list = [m.strip().lower() for m in modelos_trabalho.split(",") if m.strip()]
    fontes_list = [f.strip().lower() for f in fontes.split(",") if f.strip()]
    filter_nivel = nivel_compativel.lower() in ("true", "1", "yes", "sim")

    # Detectar nível do candidato
    nivel_candidato = curriculo.get("nivel_detectado", "desconhecido")
    if nivel_candidato == "desconhecido":
        from job_matcher import detectar_nivel_candidato
        nivel_candidato = detectar_nivel_candidato(curriculo)

    print(f"[INFO] Buscando '{termo_busca}' em '{regiao}'")
    print(f"[INFO] Filtros: modelos={modelos_list}, fontes={fontes_list}")
    print(f"[INFO] Habilidades do currículo ({len(habs)}): {sorted(habs)}")
    print(f"[INFO] Nível detectado do candidato: {nivel_candidato}")

    # Mapear fontes (nomes antigos para novos)
    mapa_fontes = {
        "linkedin": "jsearch",
        "jobbol": "jsearch",
        "vagas.com": "jooble",
        "vagas": "jooble",
        "catho": "jooble",
        "google": "google",
        "jooble": "jooble",
        "indeed": "indeed",
        "jsearch": "jsearch",
    }

    fontes_selecionadas = []
    if fontes_list:
        for f in fontes_list:
            mapeado = mapa_fontes.get(f)
            if mapeado and mapeado not in fontes_selecionadas:
                fontes_selecionadas.append(mapeado)

    # Buscar vagas em múltiplas APIs com filtros de modelo de trabalho
    # Usar cache para evitar chamadas repetidas às APIs (TTL: 30 minutos)
    from job_scraper import _cache_get, _cache_set, _gerar_cache_key
    cache_key = _gerar_cache_key(termo_busca, regiao, fontes_selecionadas)
    vagas = _cache_get(cache_key)
    cache_hit = vagas is not None
    if not cache_hit:
        recencia = int(recencia_dias) if recencia_dias else 0
        vagas = buscar_vagas_filtradas(
            palavras_chave=[termo_busca],
            tipos_vaga=[],  # Deixar vazio para não duplicar queries
            modelos_trabalho=modelos_list if modelos_list else [],
            regioes=[regiao] if regiao else [],
            max_results=50,
            fontes=fontes_selecionadas if fontes_selecionadas else None,
            recencia_dias=recencia
        )
        _cache_set(cache_key, vagas)
    else:
        print(f"[INFO] Cache hit: {len(vagas)} vagas recuperadas do cache")

    if not vagas:
        return JSONResponse(content={
            "vagas": [],
            "total": 0,
            "termo_busca": termo_busca,
            "mensagem": (
                "Nenhuma vaga foi encontrada. Verifique as chaves das APIs, "
                "a conexão com a internet ou tente outro termo/localização."
            ),
            "fontes_consultadas": fontes_selecionadas or ["google", "jooble", "indeed", "jsearch"]
        })

    # Calcular match para cada vaga
    from job_scraper import _parsear_data_posted
    vagas_com_match = []
    for vaga in vagas:
        match_result = calcula_match(curriculo, vaga)
        chance = calcular_chance_contratacao(curriculo, match_result, vaga)
        recomendacoes = gerar_recomendacoes(curriculo, match_result)

        # Calcular dias desde publicação
        posted_date = vaga.get("posted_date", "")
        dias_desde_postagem = None
        if posted_date:
            data_posted = _parsear_data_posted(posted_date)
            if data_posted:
                dias_desde_postagem = (datetime.now() - data_posted).days

        vaga_completa = {
            "title": vaga.get("title", ""),
            "company": vaga.get("company", ""),
            "location": vaga.get("location", ""),
            "description": vaga.get("description", ""),
            "link": vaga.get("link", ""),
            "apply_link": vaga.get("apply_link", ""),
            "posted_date": posted_date,
            "dias_desde_postagem": dias_desde_postagem,
            "source": vaga.get("source", ""),
            "tags": vaga.get("tags", []),
            "nivel_vaga": match_result.get("nivel_vaga", "não especificado"),
            "match": match_result,
            "chance_contratacao": chance,
            "classificacao": classificar_vaga(match_result),
            "recomendacoes": recomendacoes
        }
        vagas_com_match.append(vaga_completa)

    # ATENÇÃO: NÃO filtrar vagas por nível!
    # O usuário quer ver TODAS as vagas e decidir por si mesmo qual é melhor.
    # O score de compatibilidade ainda é calculado para informar o usuário.
    # A filtragem por nível foi desabilitada para não perder vagas relevantes.
    pass  # Nenhuma filtragem por nível - mostrar todas as vagas

    # Ordenar por chance de contratação primeiro, depois por recência (mais recentes primeiro)
    # Prioriza vagas com maior chance, mas empata vagas de mesma chance por data (mais recentes primeiro)
    vagas_com_match.sort(key=lambda x: (
        x.get("chance_contratacao", {}).get("score", 0),
        -(x.get("dias_desde_postagem", 999) or 999)  # Menos dias = mais recente = maior valor
    ), reverse=True)

    # Contar por classificação e recência
    alta = len([v for v in vagas_com_match if v["chance_contratacao"]["score"] >= 65])
    media = len([v for v in vagas_com_match if 50 <= v["chance_contratacao"]["score"] < 65])
    recentes_7dias = len([v for v in vagas_com_match if v.get("dias_desde_postagem") is not None and v["dias_desde_postagem"] <= 7])

    # Separar vagas por localização
    vagas_araraquara = []
    vagas_regiao = []
    for v in vagas_com_match:
        location = v.get("location", "").lower()
        cidade_norm = _normalizar_cidade(v.get("location", "")).get("cidade", "").lower()
        if "araraquara" in location or cidade_norm == "araraquara":
            vagas_araraquara.append(v)
        else:
            vagas_regiao.append(v)

    # Atualizar contadores
    alta_araraquara = len([v for v in vagas_araraquara if v.get("chance_contratacao", {}).get("score", 0) >= 65])

    return JSONResponse(content={
        "vagas": vagas_com_match,
        "vagas_araraquara": vagas_araraquara,
        "vagas_regiao": vagas_regiao,
        "total": len(vagas_com_match),
        "total_araraquara": len(vagas_araraquara),
        "termo_busca": termo_busca,
        "regiao": regiao,
        "cache_usado": cache_hit,
        "filtros_aplicados": {
            "modelos_trabalho": modelos_list,
            "fontes": fontes_list,
            "nivel_compativel": filter_nivel
        },
        "resumo": {
            "alta_chance": alta,
            "media_chance": media,
            "recentes_7dias": recentes_7dias,
            "curriculo_habilidades": habs[:15],
            "nivel_detectado": nivel_candidato
        },
        "mensagem": f"Encontradas {len(vagas_com_match)} vagas! {len(vagas_araraquara)} em Araraquara. {alta} com alta chance, {media} com média chance."
    })


# ========== ANÁLISE DE VAGA ESPECÍFICA ==========

@app.post("/api/jobs/analyze")
async def analisar_vaga(
    vaga_nome: str = Form(...),
    vaga_descricao: str = Form("")
):
    """
    Analisa uma vaga específica contra o currículo do usuário.
    Busca a vaga na web se não houver descrição, senão usa a descrição fornecida.
    """
    # Carregar currículo
    curriculo = carregar_curriculo()
    if not curriculo:
        return JSONResponse(
            content={"error": "Nenhum currículo salvo. Faça upload primeiro."},
            status_code=400
        )

    # Se não há descrição, buscar via SerpAPI
    if not vaga_descricao.strip():
        print(f"[INFO] Buscando vaga '{vaga_nome}' no Google Jobs...")
        vagas_encontradas = buscar_vagas_filtradas(
            palavras_chave=[vaga_nome],
            tipos_vaga=[],  # Não duplicar queries
            modelos_trabalho=[],
            regioes=[],
            max_results=1
        )

        if vagas_encontradas:
            vaga = vagas_encontradas[0]
            vaga_descricao = f"{vaga.get('title', '')} {vaga.get('description', '')} {vaga.get('company', '')}"
            vaga_encontrada = vaga
        else:
            # Fallback para análise só com nome
            vaga_descricao = vaga_nome
            vaga_encontrada = {"title": vaga_nome, "description": "", "company": "", "link": ""}
    else:
        vaga_encontrada = {
            "title": vaga_nome,
            "description": vaga_descricao,
            "company": "",
            "link": ""
        }

    # Montar vaga para análise
    vaga_para_analise = {
        "title": vaga_nome,
        "description": vaga_descricao,
        "company": vaga_encontrada.get("company", ""),
        "link": vaga_encontrada.get("link", ""),
        "tags": _extrair_tags_simples(vaga_descricao)
    }

    # Calcular match
    match_result = calcula_match(curriculo, vaga_para_analise)
    classificacao = classificar_vaga(match_result)
    recomendacoes = gerar_recomendacoes(curriculo, match_result)

    # Calcular chance de contratação
    chance = calcular_chance_contratacao(curriculo, match_result, vaga_para_analise)

    return JSONResponse(content={
        "vaga": {
            "nome": vaga_nome,
            "descricao": vaga_descricao[:500],
            "empresa": vaga_encontrada.get("company", ""),
            "link": vaga_encontrada.get("link", "")
        },
        "match": match_result,
        "classificacao": classificacao,
        "chance_contratacao": chance,
        "recomendacoes": recomendacoes
    })


def _extrair_tags_simples(texto: str) -> List[str]:
    """Extrai tags simples da descrição da vaga."""
    from job_scraper import _extrair_tags
    return _extrair_tags({"description": texto})


def _normalizar_cidade(localizacao: str) -> dict:
    """Tenta extrair cidade e estado de uma string de localização."""
    loc = localizacao.lower().strip()
    # Padrões comuns: "Cidade, SP", "Cidade - SP", "Cidade, Estado, Brasil"
    partes = loc.replace("-", ",").split(",")
    partes = [p.strip() for p in partes if p.strip()]

    cidade = partes[0] if partes else ""
    estado = ""

    if len(partes) >= 2:
        # Pode ser "São Paulo, SP" ou "São Paulo, São Paulo, Brasil"
        segundo = partes[1]
        if len(segundo) <= 3 or segundo in ("sp", "rj", "mg", "rs", "ba", "df", "pe", "pr", "sc", "ce", "am", "ms", "go", "es", "pb", "rn", "mt", "ma", "pa"):
            # É sigla de estado
            estados_map = {
                "sp": "São Paulo", "rj": "Rio de Janeiro", "mg": "Minas Gerais",
                "rs": "Rio Grande do Sul", "ba": "Bahia", "df": "Distrito Federal",
                "pe": "Pernambuco", "pr": "Paraná", "sc": "Santa Catarina",
                "ce": "Ceará", "am": "Amazonas", "ms": "Mato Grosso do Sul",
                "go": "Goiás", "es": "Espírito Santo", "pb": "Paraíba",
                "rn": "Rio Grande do Norte", "mt": "Mato Grosso", "ma": "Maranhão",
                "pa": "Pará",
            }
            estado = estados_map.get(segundo, segundo)
        else:
            estado = segundo

    return {"cidade": cidade.title() if cidade else "", "estado": estado.title() if estado else ""}


def calcular_chance_contratacao(curriculo: dict, match_result: dict, vaga: dict) -> dict:
    """
    Calcula a chance de contratação baseada em:
    - Match de habilidades (peso 60%)
    - Experiência (peso 25%)
    - Alinhamento de nível (peso 15%)
    """
    score_habilidades = match_result.get("score", 0)

    # Usar níveis já detectados no match_result, ou detectar aqui
    nivel_candidato = match_result.get("nivel_candidato") or curriculo.get("nivel_detectado")
    nivel_vaga = match_result.get("nivel_vaga")

    if not nivel_candidato:
        from job_matcher import detectar_nivel_candidato, detectar_nivel_vaga
        nivel_candidato = detectar_nivel_candidato(curriculo)
    if not nivel_vaga:
        from job_matcher import detectar_nivel_vaga
        nivel_vaga = detectar_nivel_vaga(vaga)

    # Pontuação de experiência baseada no nível do candidato
    # Um candidato junior tem menos experiência, sênior tem mais
    exp_scores_nivel = {
        "júnior": 65,      # ~2 anos de experiência
        "pleno": 80,       # ~4 anos de experiência
        "sênior": 95,      # ~7+ anos de experiência
        "desconhecido": 50
    }

    exp_score = exp_scores_nivel.get(nivel_candidato, 50)

    # Extrair anos de experiência mencionados no currículo (se houver)
    curriculo_texto = curriculo.get("texto_completo", "").lower()
    import re
    anos_match = re.findall(r"(\d+)\s*ano?s?\s*(?:de\s*)?experi[ée]ncia?", curriculo_texto)
    if anos_match:
        anos = max(int(a) for a in anos_match)
        if anos >= 5:
            exp_score = max(exp_score, 90)
        elif anos >= 3:
            exp_score = max(exp_score, 75)
        elif anos >= 1:
            exp_score = max(exp_score, 60)

    # Pontuação de alinhamento de nível (peso 15%)
    # Mesmo nível = 100, um nível abaixo = 50, dois níveis abaixo = 20
    nivel_hierarquia = {"júnior": 1, "pleno": 2, "sênior": 3}
    cand_level_num = nivel_hierarquia.get(nivel_candidato, 1)
    vaga_level_num = nivel_hierarquia.get(nivel_vaga, 2)  # padrão pleno

    if nivel_vaga == "não especificado":
        nivel_score = 70  # neutro quando não informado
    else:
        diff = vaga_level_num - cand_level_num

        if diff <= 0:
            # Candidato no mesmo nível ou acima
            nivel_score = 100 if diff == 0 else 85
        elif diff == 1:
            # Candidato um nível abaixo - ainda adequado
            nivel_score = 65
        elif diff == 2:
            # Candidato dois níveis abaixo - não ideal
            nivel_score = 30
        else:
            nivel_score = 15

    # Score final ponderado
    chance_final = int(score_habilidades * 0.60 + exp_score * 0.25 + nivel_score * 0.15)

    # Classificação
    if chance_final >= 80:
        label = "Muito Alta"
        cor = "success"
    elif chance_final >= 65:
        label = "Alta"
        cor = "success"
    elif chance_final >= 50:
        label = "Média"
        cor = "warning"
    elif chance_final >= 35:
        label = "Baixa"
        cor = "warning"
    else:
        label = "Muito Baixa"
        cor = "danger"

    return {
        "score": chance_final,
        "label": label,
        "cor": cor,
        "nivel_candidato": nivel_candidato,
        "nivel_vaga": nivel_vaga,
        "detalhes": {
            "habilidades": score_habilidades,
            "experiencia": exp_score,
            "nivel_match": nivel_score
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
