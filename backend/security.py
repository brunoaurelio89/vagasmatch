"""
VagaMatch - Módulo de segurança e criptografia
Responsável por criptografar/descodificar dados sensíveis (currículo, credenciais)
usando AES-256-GCM com HMAC para integridade
"""
import json
import os
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from config import RESUME_ENCRYPTED, DEFAULT_EXPIRATION_SECONDS

# Arquivo onde a chave mestra é armazenada
KEY_FILE = Path(__file__).resolve().parent.parent / "data" / "secret.key"

# TTL para expiração do currículo (em segundos) - padrão 24 horas
RESUME_TTL_SECONDS = DEFAULT_EXPIRATION_SECONDS

# Campos considerados sensíveis e removidos do resumo público
CAMPOS_SENSIVEIS = [
    "cpf", "telefone", "email", "endereco", "cep", "senha",
    "documentos", "banco", "agencia", "conta", "pix",
    "data_nascimento", "foto", "observacoes_privadas",
]

# Campos públicos seguros para compartilhamento
CAMPOS_PUBLICOS_SEGUROS = [
    "nome", "idade", "formacao", "habilidades", "experiencias",
    "cursos", "certificacoes", "idiomas", "modelo_preferido",
    "salario_esperado", "disponibilidade", "area_atuacao", "nivel_experiencia",
]

# Campos mínimos obrigatórios para validar um currículo
CAMPOS_MINIMOS_OBRIGATORIOS = ["nome", "habilidades"]


def carregar_ou_criar_chave() -> bytes:
    """Carrega a chave mestra do arquivo ou cria uma nova se não existir.

    Usa AES-256 (32 bytes). A chave é armazenada como bytes brutos.

    Retorna bytes brutos da chave (32 bytes para AES-256).
    """
    if KEY_FILE.exists():
        chave = KEY_FILE.read_bytes()
        # Validar tamanho da chave - se for Fernet (44 bytes), reutilizar
        # Se for 32 bytes, usar diretamente
        if len(chave) == 32:
            return chave
        elif len(chave) >= 32:
            # Chave existente com mais de 32 bytes (ex: Fernet), recortar
            return chave[:32]

    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Gerar chave AES-256 (32 bytes)
    chave = AESGCM.generate_key(bit_length=256)
    KEY_FILE.write_bytes(chave)
    return chave


def get_aesgcm() -> AESGCM:
    """Retorna uma instância de AESGCM autenticada com a chave mestra (AES-256-GCM)."""
    chave = carregar_ou_criar_chave()
    return AESGCM(chave)


def _encriptar_com_aes256(dados_json: str) -> bytes:
    """Criptografa dados usando AES-256-GCM.

    Returns bytes no formato: nonce (12 bytes) + ciphertext + tag
    """
    cipher = get_aesgcm()
    nonce = os.urandom(12)  # GCM nonce recomendado: 12 bytes
    dados_bytes = dados_json.encode("utf-8")
    # AESGCM.encrypt inclui automaticamente o tag de autenticação
    ciphertext = cipher.encrypt(nonce, dados_bytes, None)
    return nonce + ciphertext


def _decriptar_com_aes256(dados_criptografados: bytes) -> str:
    """Descriptografa dados usando AES-256-GCM.

    Espera formato: nonce (12 bytes) + ciphertext + tag
    """
    cipher = get_aesgcm()
    nonce = dados_criptografados[:12]
    ciphertext = dados_criptografados[12:]
    dados_bytes = cipher.decrypt(nonce, ciphertext, None)
    return dados_bytes.decode("utf-8")


def criptografar_dados(dados: dict, caminho_arquivo: Path) -> bool:
    """
    Criptografa um dicionário e salva em arquivo usando AES-256-GCM.
    Inclui timestamp de criação para controle de expiração (TTL)
    e hash de verificação de integridade.
    Retorna True em caso de sucesso.
    """
    try:
        # Adicionar metadados de timestamp e hash de verificação
        dados_com_meta = dados.copy()
        dados_com_meta["_timestamp_criacao"] = time.time()
        dados_com_meta["_hash_verificacao"] = _gerar_hash_verificacao(dados_com_meta)

        dados_json = json.dumps(dados_com_meta, ensure_ascii=False, indent=2)

        dados_criptografados = _encriptar_com_aes256(dados_json)

        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        caminho_arquivo.write_bytes(dados_criptografados)
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao criptografar dados: {e}")
        return False


def descriptografar_dados(caminho_arquivo: Path) -> dict | None:
    """
    Lê e descriptografa um arquivo usando AES-256-GCM.
    Verifica validade do TTL se o dado tiver timestamp.
    Verifica integridade via hash.
    Retorna o dicionário original ou None se não existir, expirado ou falhar.
    """
    if not caminho_arquivo.exists():
        return None

    try:
        dados_criptografados = caminho_arquivo.read_bytes()
        dados_json = _decriptar_com_aes256(dados_criptografados)
        dados = json.loads(dados_json)

        # Verificar expiração (TTL)
        timestamp_criacao = dados.get("_timestamp_criacao")
        if timestamp_criacao is not None:
            if time.time() - timestamp_criacao > RESUME_TTL_SECONDS:
                print("[AVISO] Dados expirados (TTL atingido). Removendo dados antigos.")
                try:
                    caminho_arquivo.unlink(missing_ok=True)
                except Exception:
                    pass
                return None

        # Verificar integridade via hash
        hash_armazenado = dados.pop("_hash_verificacao", None)
        if hash_armazenado is not None:
            if not _verificar_hash(dados, hash_armazenado):
                print("[ERRO] Integridade dos dados comprometida (hash inválido).")
                return None

        # Remover metadados internos antes de retornar
        dados.pop("_timestamp_criacao", None)

        return dados
    except Exception as e:
        print(f"[ERRO] Falha ao descriptografar dados: {e}")
        return None


def _gerar_hash_verificacao(dados: dict) -> str:
    """Gera um hash SHA-256 para verificação de integridade dos dados."""
    dados_serializados = json.dumps(dados, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(dados_serializados.encode("utf-8")).hexdigest()


def _verificar_hash(dados: dict, hash_esperado: str) -> bool:
    """Verifica se o hash dos dados corresponde ao esperado."""
    hash_calculado = _gerar_hash_verificacao(dados)
    return hash_calculado == hash_esperado


def salvar_curriculo(curriculo: dict) -> bool:
    """Salva o currículo parseado criptografado com AES-256-GCM e timestamp."""
    curriculo_com_metadata = {
        **curriculo,
        "_metadata": {
            "salvo_em": datetime.now().isoformat(),
            "versao": "2.0",
            "algoritmo": "AES-256-GCM",
        }
    }
    return criptografar_dados(curriculo_com_metadata, RESUME_ENCRYPTED)


def carregar_curriculo() -> dict | None:
    """Carrega o currículo criptografado.

    Verifica expiração (TTL) automaticamente.
    Se expirado, retorna None e remove o arquivo.
    """
    return descriptografar_dados(RESUME_ENCRYPTED)


def validar_curriculo(curriculo: dict) -> tuple[bool, list[str]]:
    """
    Verifica se o currículo tem campos mínimos obrigatórios (nome, habilidades).

    Retorna (valido, lista_de_erros).
    """
    erros = []

    if not curriculo or not isinstance(curriculo, dict):
        return False, ["Currículo vazio, nulo ou não é um dicionário válido"]

    # Verificar campos obrigatórios
    for campo in CAMPOS_MINIMOS_OBRIGATORIOS:
        if campo not in curriculo or curriculo.get(campo) is None:
            erros.append(f"Campo obrigatório '{campo}' não encontrado")
        elif not curriculo.get(campo):
            erros.append(f"Campo obrigatório '{campo}' está vazio")

    # Validar nome
    nome = curriculo.get("nome", "")
    if isinstance(nome, str) and len(nome.strip()) < 2:
        erros.append("Campo 'nome' deve ter pelo menos 2 caracteres")

    # Validar habilidades
    habilidades = curriculo.get("habilidades")
    if isinstance(habilidades, str):
        habilidades = [h.strip() for h in habilidades.split(",") if h.strip()]
    if not habilidades or len(habilidades) == 0:
        erros.append("Campo 'habilidades' deve conter pelo menos uma habilidade")
    elif not isinstance(habilidades, (list, tuple)):
        erros.append("Campo 'habilidades' deve ser uma lista")

    # Verificar se o currículo está expirado (TTL)
    metadata = curriculo.get("_metadata", {}) or curriculo.get("_metadata")
    salvo_em = metadata.get("salvo_em") if isinstance(metadata, dict) else None
    if salvo_em:
        try:
            data_salvamento = datetime.fromisoformat(salvo_em)
            diferenca = (datetime.now() - data_salvamento).total_seconds()
            if diferenca > RESUME_TTL_SECONDS:
                erros.append("Currículo expirado (TTL atingido)")
        except (ValueError, TypeError):
            pass  # Ignora erros de parsing de data

    return len(erros) == 0, erros


def get_resumo_curriculo(curriculo: dict) -> dict:
    """
    Retorna apenas campos públicos seguros do currículo (sem dados sensíveis).

    Remove informações pessoais e sensíveis como:
    - CPF, telefone, email, endereço
    - Dados bancários
    - Foto
    - Observações privadas

    Mantém apenas informações profissionais relevantes para busca.
    """
    if not curriculo or not isinstance(curriculo, dict):
        return {}

    resumo = {}

    # Copiar campos públicos seguros
    for campo in CAMPOS_PUBLICOS_SEGUROS:
        if campo in curriculo:
            valor = curriculo[campo]
            # Processar campos de lista
            if campo in ("habilidades", "formacao", "cursos", "certificacoes", "idiomas"):
                if isinstance(valor, set):
                    resumo[campo] = list(valor)
                elif isinstance(valor, str):
                    resumo[campo] = [item.strip() for item in valor.split(",") if item.strip()]
                elif isinstance(valor, list):
                    resumo[campo] = valor[:]
                else:
                    resumo[campo] = [str(valor)]
            else:
                resumo[campo] = valor

    # Adicionar contagens para estatísticas sem revelar dados sensíveis
    habilidades = curriculo.get("habilidades", [])
    if isinstance(habilidades, set):
        habilidades = list(habilidades)
    elif isinstance(habilidades, str):
        habilidades = [h.strip() for h in habilidades.split(",") if h.strip()]

    experiencias = curriculo.get("experiencias", [])
    if not isinstance(experiencias, list):
        experiencias = []

    resumo["_contagem_habilidades"] = len(habilidades)
    resumo["_contagem_experiencias"] = len(experiencias)
    resumo["_contagem_cursos"] = len(curriculo.get("cursos", []))
    resumo["_contagem_certificacoes"] = len(curriculo.get("certificacoes", []))
    resumo["_contagem_idiomas"] = len(curriculo.get("idiomas", []))
    resumo["_contagem_formacao"] = len(curriculo.get("formacao", []))

    return resumo


def get_statistic_resume(curriculo: dict) -> dict:
    """
    Retorna estatísticas do currículo sem revelar dados sensíveis.

    Fornece métricas agregadas e contagens para análise estatística
    sem expor informações pessoais ou identificáveis.
    """
    if not curriculo or not isinstance(curriculo, dict):
        return {
            "existe": False,
            "valido": False,
            "estatisticas": {},
        }

    habilidades = curriculo.get("habilidades", [])
    if isinstance(habilidades, set):
        habilidades = list(habilidades)
    elif isinstance(habilidades, str):
        habilidades = [h.strip() for h in habilidades.split(",") if h.strip()]

    experiencias = curriculo.get("experiencias", [])
    if not isinstance(experiencias, list):
        experiencias = []

    cursos = curriculo.get("cursos", [])
    certificacoes = curriculo.get("certificacoes", [])
    idiomas = curriculo.get("idiomas", [])
    formacao = curriculo.get("formacao", [])

    # Verificar validade
    valido, _ = validar_curriculo(curriculo)

    # Calcular tempo total de experiência
    anos_experiencia = _calcular_anos_experiencia(experiencias)

    # Determinar senioridade baseada em experiência
    senioridade = _determinar_senioridade(anos_experiencia, len(experiencias))

    # Determinar score de completude do currículo (0-100)
    score_completude = _calcular_score_completude(curriculo)

    # Contar habilidades por categoria
    tech_skills, soft_skills, idiomas_skills = _categorizar_habilidades(habilidades)

    return {
        "existe": True,
        "valido": valido,
        "estatisticas": {
            "total_habilidades": len(habilidades),
            "total_experiencias": len(experiencias),
            "total_cursos": len(cursos),
            "total_certificacoes": len(certificacoes),
            "total_idiomas": len(idiomas),
            "total_formacao": len(formacao),
            "anos_experiencia_estimados": anos_experiencia,
            "senioridade_estimada": senioridade,
            "tech_skills_count": len(tech_skills),
            "soft_skills_count": len(soft_skills),
            "idiomas_skills_count": len(idiomas_skills),
        },
        "score_completude": score_completude,
        "tem_habilidades": len(habilidades) > 0,
        "tem_experiencia": len(experiencias) > 0,
        "tem_formacao": len(formacao) > 0,
        "tem_cursos": len(cursos) > 0,
        "tem_certificacoes": len(certificacoes) > 0,
        "tem_idiomas": len(idiomas) > 0,
        "modelo_preferido": curriculo.get("modelo_preferido", "não especificado"),
        "area_atuacao": curriculo.get("area_atuacao", "não especificada"),
        "nivel_experiencia": curriculo.get("nivel_experiencia", "não especificado"),
        "disponibilidade": curriculo.get("disponibilidade", "não especificada"),
        "metadata": {
            "campos_total": len(curriculo),
            "campos_sensiveis_removidos": len([k for k in curriculo if k.lower() in CAMPOS_SENSIVEIS]),
            "algoritmo_criptografia": "AES-256-GCM",
        }
    }


def _categorizar_habilidades(habilidades: list) -> tuple[list, list, list]:
    """Categoriza habilidades em técnicas, comportamentais e idiomas."""
    tech_keywords = {
        "python", "java", "javascript", "typescript", "sql", "react", "angular",
        "vue", "node", "django", "flask", "fastapi", "aws", "docker", "kubernetes",
        "azure", "gcp", "git", "linux", "mongodb", "postgresql", "mysql",
        "redis", "graphql", "rest", "api", "microservicos", "ci/cd",
        "jenkins", "terraform", "ansible", "react native", "flutter",
        "swift", "kotlin", "c#", "c++", "ruby", "php", "perl",
        "html", "css", "sass", "tailwind", "bootstrap", "vue.js",
    }
    idioma_keywords = {
        "inglês", "espanhol", "francês", "mandarim", "alemão", "italiano",
        "português", "japonês", "coreano", "árabe", "russo", "holandês",
        "hebraico", "grego", "turco", "polonês",
    }

    tech_skills = []
    soft_skills = []
    idiomas_skills = []

    for hab in habilidades:
        hab_lower = hab.lower().strip()
        if hab_lower in idioma_keywords:
            idiomas_skills.append(hab)
        elif hab_lower in tech_keywords:
            tech_skills.append(hab)
        else:
            soft_skills.append(hab)

    return tech_skills, soft_skills, idiomas_skills


def _calcular_anos_experiencia(experiencias: list) -> float:
    """Calcula anos estimados de experiência total."""
    total_anos = 0.0

    for exp in experiencias:
        if isinstance(exp, dict):
            # Tentar extrair duração em meses
            duracao = exp.get("duracao") or exp.get("periodo") or exp.get("tempo")
            if isinstance(duracao, (int, float)):
                # Assumir meses
                total_anos += duracao / 12.0

            # Extrair de datas
            data_inicio = exp.get("data_inicio") or exp.get("inicio")
            data_fim = exp.get("data_fim") or exp.get("fim")

            if data_inicio and data_fim:
                anos = _extrair_diferenca_anos(data_inicio, data_fim)
                if anos is not None:
                    total_anos += anos

    return round(total_anos, 1)


def _extrair_diferenca_anos(data_inicio: Any, data_fim: Any) -> float | None:
    """Extrai a diferença em anos entre duas datas."""
    try:
        if isinstance(data_inicio, str):
            data_inicio = datetime.fromisoformat(data_inicio[:10])
        if isinstance(data_fim, str):
            data_fim = datetime.fromisoformat(data_fim[:10])

        if isinstance(data_inicio, datetime) and isinstance(data_fim, datetime):
            diff = (data_fim - data_inicio).days / 365.25
            return max(0, diff)
    except (ValueError, TypeError):
        pass

    return None


def _determinar_senioridade(anos_experiencia: float, total_experiencias: int) -> str:
    """Determina a senioridade baseada na experiência."""
    if anos_experiencia >= 10 or total_experiencias >= 4:
        return "sênior"
    elif anos_experiencia >= 5 or total_experiencias >= 3:
        return "pleno"
    elif anos_experiencia >= 2 or total_experiencias >= 2:
        return "júnior"
    else:
        return "estágio"


def _calcular_score_completude(curriculo: dict) -> int:
    """Calcula o score de completude do currículo (0-100)."""
    if not isinstance(curriculo, dict):
        return 0

    # Campos considerados para score com pesos
    campos_pesos = {
        "nome": 10,
        "habilidades": 20,
        "formacao": 10,
        "experiencias": 20,
        "cursos": 10,
        "certificacoes": 10,
        "idiomas": 5,
        "area_atuacao": 5,
        "nivel_experiencia": 5,
        "modelo_preferido": 3,
        "salario_esperado": 2,
    }

    score = 0
    for campo, peso in campos_pesos.items():
        valor = curriculo.get(campo)
        if valor is not None and valor != "" and valor != [] and valor != {}:
            score += peso

    return min(100, score)


def limpar_curriculo_expirado() -> bool:
    """
    Remove o currículo se estiver expirado (TTL atingido).
    Retorna True se o currículo foi removido ou False se ainda é válido.
    """
    curriculo = carregar_curriculo()
    if not curriculo:
        return False

    valido, _ = validar_curriculo(curriculo)
    if not valido:
        if RESUME_ENCRYPTED.exists():
            RESUME_ENCRYPTED.unlink()
            print("[INFO] Currículo expirado removido")
            return True

    return False


def limpar_dados_expirados() -> int:
    """
    Remove arquivos de dados expirados (TTL atingido).
    Verifica todos os arquivos de dados criptografados.
    Retorna o número de arquivos removidos.
    """
    arquivos_verificados = [
        RESUME_ENCRYPTED,
        RESUME_ENCRYPTED.parent / "credentials.enc",
    ]

    itens_removidos = 0
    for arquivo in arquivos_verificados:
        if not arquivo.exists():
            continue

        try:
            dados = descriptografar_dados(arquivo)
            # descriptografar_dados já verifica TTL e remove se expirado
            # Se retornou None e o arquivo ainda existe, pode ser expirado
            if dados is None and arquivo.exists():
                dados_cripto = arquivo.read_bytes()
                if len(dados_cripto) > 12:
                    try:
                        dados_json = _decriptar_com_aes256(dados_cripto)
                        dados_brutos = json.loads(dados_json)
                        timestamp = dados_brutos.get("_timestamp_criacao")
                        if timestamp and (time.time() - timestamp > RESUME_TTL_SECONDS):
                            arquivo.unlink(missing_ok=True)
                            itens_removidos += 1
                    except Exception:
                        pass
        except Exception:
            pass

    if itens_removidos > 0:
        print(f"[INFO] {itens_removidos} arquivo(s) de dados expirado(s) removido(s).")

    return itens_removidos


# Compatibilidade com código antigo que usava Fernet
class _FernetCompat:
    """Classe de compatibilidade para código antigo que usava Fernet.

    Agora usa AES-256-GCM internamente. Mantém compatibilidade
    com chamadas externas que ainda usam get_cipher().

    .. deprecated:: Use get_aesgcm() ou as funções de criptografia direta
    """
    @staticmethod
    def encrypt(dados_bytes: bytes) -> bytes:
        """Criptografa dados usando AES-256-GCM."""
        cipher = get_aesgcm()
        nonce = os.urandom(12)
        ciphertext = cipher.encrypt(nonce, dados_bytes, None)
        return nonce + ciphertext

    @staticmethod
    def decrypt(dados_criptografados: bytes) -> bytes:
        """Descriptografa dados usando AES-256-GCM."""
        cipher = get_aesgcm()
        nonce = dados_criptografados[:12]
        ciphertext = dados_criptografados[12:]
        return cipher.decrypt(nonce, ciphertext, None)


def get_cipher():
    """Retorna wrapper de compatibilidade para código antigo.

    .. deprecated:: Use get_aesgcm() ou criptografar_dados/descriptografar_dados
    """
    return _FernetCompat()
