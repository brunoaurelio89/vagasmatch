/* VagaMatch - Frontend interativo moderno */
class VagaMatchApp {
    constructor() {
        this.curriculo = null;
        this.vagas = [];
        this.vagasOriginais = [];
        this.apisStatus = {};
        this.init();
    }

    init() {
        console.log("VagaMatch inicializado");

        // Event listeners
        const searchForm = document.getElementById("searchForm");

        if (searchForm) {
            searchForm.addEventListener("submit", (e) => this.handleSearchSubmit(e));
        }

        // Filtros compactos (tags)
        this.setupFilterTags();

        // Upload de arquivo
        this.setupFileUpload();

        // Verificar status da API
        this.checkApiStatus();

        // Carregar curriculo e filtros salvos
        this.loadSavedData();

        // Evento logout
        const logoutBtn = document.getElementById("logoutBtn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => this.handleLogout());
        }

        // Ordenação
        this.setupOrdenacao();
    }

    setupFilterTags() {
        // Configura os botões de filtro compactos (filter-tag)
        const filterTags = document.querySelectorAll(".filter-tag");
        filterTags.forEach(tag => {
            tag.addEventListener("click", (e) => {
                e.preventDefault();
                tag.classList.toggle("active");
                this.salvarFiltros();
            });
        });
    }

    setupOrdenacao() {
        // Dropdown customizado
        const trigger = document.getElementById("ordenacaoTrigger");
        const menu = document.getElementById("ordenacaoMenu");
        const valorSpan = document.getElementById("ordenacaoValor");
        const options = document.querySelectorAll(".ordenacao-option");

        if (trigger && menu) {
            trigger.addEventListener("click", (e) => {
                e.stopPropagation();
                const isExpanded = trigger.getAttribute("aria-expanded") === "true";
                trigger.setAttribute("aria-expanded", !isExpanded);
                menu.classList.toggle("open");
            });

            // Selecionar opção
            options.forEach(opt => {
                opt.addEventListener("click", () => {
                    options.forEach(o => {
                        o.classList.remove("active");
                        o.setAttribute("aria-selected", "false");
                    });
                    opt.classList.add("active");
                    opt.setAttribute("aria-selected", "true");
                    valorSpan.textContent = opt.textContent;
                    trigger.setAttribute("aria-expanded", "false");
                    menu.classList.remove("open");

                    // Ordenar
                    this.ordenarVagas(opt.dataset.value);
                });
            });

            // Fechar ao clicar fora
            document.addEventListener("click", () => {
                menu.classList.remove("open");
                trigger.setAttribute("aria-expanded", "false");
            });
        }
    }

    ordenarVagas(tipoOrdenacao) {
        let vagasOrdenadas = [...this.vagasOriginais];

        switch (tipoOrdenacao) {
            case "relevancia":
                vagasOrdenadas.sort((a, b) => {
                    const scoreA = a.chance_contratacao?.score || a.match?.score || 0;
                    const scoreB = b.chance_contratacao?.score || b.match?.score || 0;
                    return scoreB - scoreA;
                });
                break;
            case "recentes":
                vagasOrdenadas.sort((a, b) => {
                    const diasA = a.dias_desde_postagem ?? 999;
                    const diasB = b.dias_desde_postagem ?? 999;
                    return diasA - diasB;
                });
                break;
            case "distancia":
                vagasOrdenadas.sort((a, b) => {
                    const distA = a.distancia ?? 99999;
                    const distB = b.distancia ?? 99999;
                    return distA - distB;
                });
                break;
        }

        this.vagas = vagasOrdenadas;
        this.renderizarVagas();
    }

    setupFileUpload() {
        const dropzone = document.getElementById("dropzone");
        const fileInput = document.getElementById("fileInput");
        const btnSelecionar = document.getElementById("btnSelecionar");

        if (!dropzone || !fileInput) return;

        // Clicar para selecionar
        btnSelecionar?.addEventListener("click", () => fileInput.click());
        dropzone.addEventListener("click", (e) => {
            if (e.target !== btnSelecionar) fileInput.click();
        });

        // Drag and drop
        dropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        });

        dropzone.addEventListener("dragleave", () => {
            dropzone.classList.remove("dragover");
        });

        dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });

        // Input change
        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
    }

    async handleFileUpload(file) {
        // Validar tipo
        const ext = file.name.split('.').pop().toLowerCase();
        const permitidas = ['pdf', 'docx', 'doc', 'txt'];
        if (!permitidas.includes(ext)) {
            this.showToast(`Formato .${ext} não suportado. Use PDF, DOCX, DOC ou TXT.`, "error");
            return;
        }

        // Validar tamanho (10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.showToast("Arquivo muito grande (máx 10MB)", "error");
            return;
        }

        // Mostrar loading
        const dropzone = document.getElementById("dropzone");
        if (dropzone) {
            dropzone.style.opacity = "0.5";
            dropzone.style.pointerEvents = "none";
        }

        const btnSelecionar = document.getElementById("btnSelecionar");
        if (btnSelecionar) {
            btnSelecionar.disabled = true;
            btnSelecionar.textContent = "Processando...";
        }

        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch("/api/resume/upload-file", {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.curriculo = result.curriculo;
                this.updateUserInfo(result.curriculo.nome);
                this.showToast(result.message || "Currículo processado!", "success");
                this.showResumePreview(result.curriculo);
                this.salvarCurriculo();

                // Avançar para análise
                setTimeout(() => {
                    const step2 = document.querySelector('#step2');
                    if (step2) {
                        step2.scrollIntoView({ behavior: "smooth", block: "center" });
                    }
                }, 800);
            } else {
                this.showToast(result.error || "Erro ao processar arquivo", "error");
            }
        } catch (error) {
            console.error("Erro no upload:", error);

            // Fallback para modo local (ler via FileReader)
            try {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const content = e.target.result;
                    const dadosLocais = {
                        nome: file.name.split('.')[0].replace(/[_-]/g, ' '),
                        experiencia: content,
                        educacao: "",
                        habilidades: content
                    };
                    const parse = this.parseResumeLocally(dadosLocais);
                    this.curriculo = parse;
                    this.updateUserInfo(parse.nome);
                    this.showResumePreview(parse);
                    this.salvarCurriculo();
                    this.showToast("Currículo carregado localmente (sem análise de PDF)", "warning");
                };
                reader.readAsText(file);
            } catch (e2) {
                this.showToast("Erro ao processar arquivo.", "error");
            }
        } finally {
            const dropzone2 = document.getElementById("dropzone");
            if (dropzone2) {
                dropzone2.style.opacity = "1";
                dropzone2.style.pointerEvents = "auto";
            }
            const btnSelecionar2 = document.getElementById("btnSelecionar");
            if (btnSelecionar2) {
                btnSelecionar2.disabled = false;
                btnSelecionar2.textContent = "Selecionar arquivo";
            }
        }
    }

    /* ========== STATUS API ========== */
    async checkApiStatus() {
        const apis = [
            { url: "/api/status", name: "Backend" },
            { url: "/api/health", name: "Health" }
        ];

        for (const api of apis) {
            try {
                const response = await fetch(api.url, { signal: AbortSignal.timeout(5000) });
                if (response.ok) {
                    const data = await response.json().catch(() => ({}));
                    this.apisStatus[api.name] = { online: true, data };
                } else if (response.status === 401) {
                    this.apisStatus[api.name] = { online: false, erro: "API key inválida ou não configurada" };
                    this.mostrarErroApiKey();
                } else {
                    this.apisStatus[api.name] = { online: false, status: response.status };
                }
            } catch (e) {
                this.apisStatus[api.name] = { online: false, erro: e.message };
            }
        }

        const todasOnline = Object.values(this.apisStatus).every(s => s.online);
        if (todasOnline) {
            this.showToast("Sistema conectado", "success");
        } else {
            const offline = Object.entries(this.apisStatus)
                .filter(([_, s]) => !s.online)
                .map(([name]) => name);
            console.warn(`APIs offline: ${offline.join(", ")}`);
            this.showToast("Modo offline ativado - usando dados locais", "warning");
        }
    }

    mostrarErroApiKey() {
        console.error("========================================");
        console.error("ERRO: API key não configurada!");
        console.error("Por favor, configure as variáveis de ambiente:");
        console.error("  - GOOGLE_JOBS_API_KEY");
        console.error("  - LINKEDIN_COOKIES");
        console.error("  - ou outra API key necessária");
        console.error("========================================");
        this.showToast("API key não configurada. Verifique o console para mais detalhes.", "error");
    }

    /* ========== CURRÍCULO ========== */
    updateUserInfo(nome) {
        const userInfo = document.getElementById("userInfo");
        const userName = document.getElementById("userName");
        if (userInfo && userName) {
            userName.textContent = nome.split(" ")[0];
            userInfo.style.display = "flex";
        }
    }

    showResumePreview(curriculo) {
        // Usar getElementById com fallback seguro
        let preview = document.getElementById("resumePreview");

        if (!preview) {
            preview = document.createElement("div");
            preview.id = "resumePreview";
            preview.className = "resume-preview active";

            // Buscar elemento de referência para inserção
            const form = document.getElementById("resumeForm");
            const dropzone = document.getElementById("dropzone");
            const step1 = document.getElementById("step1");

            if (form) {
                form.parentNode.insertBefore(preview, form.nextSibling);
            } else if (dropzone) {
                dropzone.parentNode.insertBefore(preview, dropzone.nextSibling);
            } else if (step1) {
                step1.appendChild(preview);
            }
        }

        const habilidades = curriculo.habilidades
            ? (typeof curriculo.habilidades === "object"
                ? Array.from(curriculo.habilidades)
                : curriculo.habilidades.split(/[\s,;]+/).filter(Boolean))
            : [];
        const habilidadesHtml = habilidades.map(s => `<span class="tag">${s}</span>`).join("");

        preview.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="color: #22c55e; font-weight: 600;">✓ Pronto</span>
            </div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 10px;">
                <strong>Habilidades (${habilidades.length} detectadas):</strong>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                ${habilidadesHtml}
            </div>
        `;
        preview.style.display = "block";
    }

    parseResumeLocally(dados) {
        const texto = `${dados.nome} ${dados.experiencia} ${dados.educacao} ${dados.habilidades}`.toLowerCase();
        const habilidades = new Set();

        // Lista expandida de tecnologias com word boundaries
        const techs = [
            // Linguagens
            "python", "java(?!script)", "javascript", "typescript", "c\\+\\+", "c#", "c\\+\\+",
            "go\\b", "golang", "rust(?!er)", "php(?!p)?", "ruby", "swift", "kotlin", "scala",
            "r\\b", "matlab", "perl", "lua", "shell", "bash", "powershell",
            // Bancos
            "sql(?!ite)", "mysql", "postgresql", "postgres", "mongodb", "mongo", "redis",
            "elasticsearch", "cassandra", "oracle", "sqlite", "dynamodb", "mariadb",
            // Frameworks Front
            "react", "vue(\\.js)?", "angular", "svelte", "next(\\.js)?", "nuxt(\\.js)?",
            "gatsby", "remix", "backbone", "ember", "jquery",
            // Frameworks Back
            "django", "flask", "fastapi", "spring", "laravel", "node(\\.js)?", "express(\\.js)?",
            "rails", "ruby on rails", "asp\\.net", "nest(\\.js)?", "fiber",
            // Frontend
            "html5?", "css3?", "css", "bootstrap", "tailwind", "sass", "scss", "less",
            "webpack", "vite", "npm", "yarn", "pnpm", "responsive design",
            "graphql", "apollo", "rest api", "restful",
            // DevOps/Cloud
            "aws", "amazon web services", "azure", "gcp", "google cloud",
            "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
            "gitlab-ci", "github actions", "circleci", "travis", "ci/cd",
            // Versionamento
            "git", "github", "gitlab", "bitbucket", "svn",
            // Data/ML
            "machine learning", "deep learning", "nlp", "natural language processing",
            "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
            "scipy", "matplotlib", "seaborn", "tableau", "power ?bi",
            "data science", "data analysis", "big data", "spark", "hadoop",
            "etl", "data warehouse", "airflow", "dbt",
            // Agile
            "scrum", "kanban", "agile", "jira", "confluence", "asana",
            // Outros
            "api", "microservices", "microserviços", "oauth", "jwt", "ssl",
            "linux", "unix", "windows server", "nginx", "apache",
            "excel", "google sheets", "tableau", "looker", "datadog",
            "rabbitmq", "kafka", "websocket", "tcp/ip", "dns"
        ];

        for (const tech of techs) {
            const regex = new RegExp(`\\b${tech}\\b`, 'i');
            if (regex.test(texto)) {
                // Normalizar nome
                const match = texto.match(regex);
                if (match) {
                    habilidades.add(match[0]);
                }
            }
        }

        return {
            nome: dados.nome,
            habilidades: habilidades,
            palavras_chave: Array.from(habilidades),
            experiencia_bruta: dados.experiencia,
            educacao_bruta: dados.educacao
        };
    }

    /* ========== PERSISTÊNCIA ========== */
    salvarCurriculo() {
        if (this.curriculo) {
            try {
                localStorage.setItem("talentosync_resume", JSON.stringify(this.curriculo));
            } catch (e) {
                console.warn("Erro ao salvar currículo no localStorage:", e);
            }
        }
    }

    salvarFiltros() {
        const filtros = {
            modelos: Array.from(document.querySelectorAll('.filter-tag.active[data-name="modelo"]'))
                .map(tag => tag.dataset.value),
            fontes: Array.from(document.querySelectorAll('.filter-tag.active[data-name="fonte"]'))
                .map(tag => tag.dataset.value)
        };
        try {
            localStorage.setItem("talentosync_filtros", JSON.stringify(filtros));
        } catch (e) {
            console.warn("Erro ao salvar filtros:", e);
        }
    }

    carregarFiltrosSalvos() {
        try {
            const filtros = JSON.parse(localStorage.getItem("talentosync_filtros") || "{}");
            if (filtros.modelos) {
                filtros.modelos.forEach(valor => {
                    const tag = document.querySelector(`.filter-tag[data-name="modelo"][data-value="${valor}"]`);
                    if (tag) tag.classList.add("active");
                });
            }
            if (filtros.fontes) {
                filtros.fontes.forEach(valor => {
                    const tag = document.querySelector(`.filter-tag[data-name="fonte"][data-value="${valor}"]`);
                    if (tag) tag.classList.add("active");
                });
            }
        } catch (e) {
            console.warn("Erro ao carregar filtros salvos:", e);
        }
    }

    async loadSavedData() {
        // Carregar currículo
        const saved = localStorage.getItem("talentosync_resume");
        if (saved) {
            try {
                this.curriculo = JSON.parse(saved);
                this.updateUserInfo(this.curriculo.nome);
                this.showResumePreview(this.curriculo);
            } catch (e) {
                console.warn("Erro ao carregar currículo salvo:", e);
            }
        }

        // Carregar filtros
        this.carregarFiltrosSalvos();
    }

    handleLogout() {
        localStorage.removeItem("talentosync_resume");
        localStorage.removeItem("talentosync_filtros");
        const userInfo = document.getElementById("userInfo");
        if (userInfo) userInfo.style.display = "none";

        // Limpar preview
        const preview = document.getElementById("resumePreview");
        if (preview) preview.style.display = "none";

        // Resetar filtros
        document.querySelectorAll(".filter-tag").forEach(tag => tag.classList.remove("active"));

        this.showToast("Sessão encerrada", "info");
    }

    /* ========== COLETAR FILTROS ========== */
    coletarFiltros() {
        const regiaoInput = document.getElementById("regiao");
        const regiao = regiaoInput?.value?.trim() || "Brasil";

        const modelos = Array.from(document.querySelectorAll('.filter-tag.active[data-name="modelo"]'))
            .map(tag => tag.dataset.value);

        const fontes = Array.from(document.querySelectorAll('.filter-tag.active[data-name="fonte"]'))
            .map(tag => tag.dataset.value);

        const nivelCheck = document.querySelector('input[name="nivel_compativel"]');
        const nivelCompativel = nivelCheck?.checked ? "true" : "false";

        const recenciaCheck = document.getElementById("ultimos15dias");
        const recenciaDias = recenciaCheck?.checked ? 15 : 0;

        const ordenacaoVal = document.querySelector(".ordenacao-option.active")?.dataset?.value || "relevancia";

        return {
            termo_busca: document.getElementById("termo_busca")?.value?.trim() || "",
            regiao: regiao,
            modelos_trabalho: modelos,
            modelos_string: modelos.join(","),
            fontes: fontes,
            fontes_string: fontes.join(","),
            nivel_compativel: nivelCompativel,
            ordenacao: ordenacaoVal,
            recencia_dias: recenciaDias
        };
    }

    /* ========== BUSCA DE VAGAS ========== */
    async handleSearchSubmit(e) {
        e.preventDefault();
        const form = e.target;

        // Coletar filtros
        const filtros = this.coletarFiltros();

        // Validar termo de busca
        if (!filtros.termo_busca) {
            this.showToast("Por favor, informe o termo de busca", "error");
            const termoInput = document.getElementById("termo_busca");
            termoInput?.focus();
            return;
        }

        // Construir payload
        const payload = {
            termo_busca: filtros.termo_busca,
            regiao: filtros.regiao || "Brasil",
            modelos_trabalho: filtros.modelos_string,
            fontes: filtros.fontes_string,
            nivel_compativel: filtros.nivel_compativel,
            ordenacao: filtros.ordenacao || "relevancia",
            recencia_dias: filtros.recencia_dias || 0
        };

        // Mostrar skeleton loading
        this.mostrarSkeletonLoading();

        const btn = form.querySelector("button[type=submit]");
        const btnText = document.getElementById("searchText");
        const btnLoading = document.getElementById("searchLoading");

        btn.disabled = true;
        btnText.style.display = "none";
        btnLoading.style.display = "inline-flex";

        try {
            const response = await fetch("/api/jobs/search", {
                method: "POST",
                body: new URLSearchParams(payload)
            });

            if (response.status === 401) {
                this.mostrarErroApiKey();
                throw new Error("API key inválida ou não configurada");
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.exibirResultados(data);

        } catch (error) {
            console.error("Erro na busca:", error);
            this.esconderSkeletonLoading();
            this.showToast(error.message || "Erro ao buscar vagas", "error");
        } finally {
            btn.disabled = false;
            btnText.style.display = "inline";
            btnLoading.style.display = "none";
        }
    }

    /* ========== SKELETON LOADING ========== */
    mostrarSkeletonLoading() {
        const container = document.getElementById("jobsContainer");
        const step3 = document.getElementById("step3");

        step3.style.display = "block";
        step3.scrollIntoView({ behavior: "smooth", block: "center" });

        const skeletons = Array(3).fill(0).map(() => `
            <div class="job-card skeleton">
                <div class="card-header">
                    <div class="skeleton-line" style="width: 60px; height: 24px;"></div>
                    <div class="skeleton-line" style="width: 80px; height: 40px; border-radius: 8px;"></div>
                </div>
                <div class="card-body">
                    <div class="skeleton-line" style="width: 70%; height: 20px; margin-bottom: 8px;"></div>
                    <div class="skeleton-line" style="width: 40%; height: 16px; margin-bottom: 16px;"></div>
                    <div class="skeleton-line" style="width: 100%; height: 40px; margin-bottom: 12px;"></div>
                    <div style="display: flex; gap: 12px;">
                        <div class="skeleton-line" style="width: 30%; height: 60px;"></div>
                        <div class="skeleton-line" style="width: 30%; height: 60px;"></div>
                    </div>
                </div>
            </div>
        `).join("");

        container.innerHTML = skeletons;
    }

    esconderSkeletonLoading() {
        const skeletons = document.querySelectorAll(".job-card.skeleton");
        skeletons.forEach(s => s.remove());
    }

    /* ========== EXIBIR RESULTADOS ========== */
    exibirResultados(data) {
        const container = document.getElementById("jobsContainer");
        const summary = document.getElementById("resultsSummary");
        const step3 = document.getElementById("step3");

        step3.style.display = "block";
        step3.scrollIntoView({ behavior: "smooth", block: "center" });

        this.vagasOriginais = data.vagas || [];
        this.vagas = [...this.vagasOriginais];
        this.vagasAraraquara = this.filtrarPorLocalidade(this.vagasOriginais, "araraquara");
        this.vagasRegiao = this.filtrarPorLocalidade(this.vagasOriginais, "sp");
        this.vagasDestaque = this.vagasOriginais.filter(v => (v.chance_contratacao?.score || v.match?.score || 0) > 80);
        this.vagasRecentes = this.vagasOriginais.filter(v => (v.dias_desde_postagem ?? 999) <= 7);

        if (this.vagas.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <h3>Nenhuma vaga encontrada</h3>
                    <p style="color: var(--text-secondary);">Tente outro termo de busca ou região.</p>
                </div>
            `;
            summary.innerHTML = `<span class="badge badge-warning">0 vagas</span>`;
            return;
        }

        // Resumo
        const resumo = data.resumo || {};
        const nivelLabel = resumo.nivel_detectado ?
            (resumo.nivel_detectado.charAt(0).toUpperCase() + resumo.nivel_detectado.slice(1)) : "N/A";
        const nivelBadge = resumo.nivel_detectado ?
            `<span class="badge badge-info">👤 Nível: ${nivelLabel}</span>` : "";

        summary.innerHTML = `
            <div class="results-actions">
                <div class="results-filters">
                    <button class="filter-btn active" data-filter="all">
                        <span class="filter-dot all"></span> Todas (${this.vagas.length})
                    </button>
                    <button class="filter-btn" data-filter="araraquara">
                        <span class="filter-dot araraquara"></span> Araraquara (${this.vagasAraraquara.length})
                    </button>
                    <button class="filter-btn" data-filter="regiao">
                        <span class="filter-dot regiao"></span> Região SP (${this.vagasRegiao.length})
                    </button>
                    <button class="filter-btn" data-filter="destaque">
                        <span class="filter-dot destaque"></span> Destaque (${this.vagasDestaque.length})
                    </button>
                    <button class="filter-btn" data-filter="recentes">
                        <span class="filter-dot recentes"></span> Mais recentes (${this.vagasRecentes.length})
                    </button>
                    <button class="filter-btn" data-filter="high">
                        <span class="filter-dot high"></span> Alta chance (${resumo.alta_chance || 0})
                    </button>
                    <button class="filter-btn" data-filter="medium">
                        <span class="filter-dot medium"></span> Média chance (${resumo.media_chance || 0})
                    </button>
                </div>
                ${nivelBadge}
            </div>
        `;

        this.renderizarVagas();

        this._setupResultFilters();

        const araraquaraCount = this.vagasAraraquara.length;
        this.showToast(
            `Encontradas ${this.vagas.length} vagas! ${araraquaraCount > 0 ? `${araraquaraCount} em Araraquara 🎯` : ""}`,
            "success"
        );
    }

    renderizarVagas() {
        const container = document.getElementById("jobsContainer");
        container.innerHTML = this.vagas.map((vaga, i) => this.criarCardVaga(vaga, i)).join("");
    }

    /* ========== FILTRAR POR LOCALIDADE ========== */
    filtrarPorLocalidade(vagas, local) {
        const localLower = local.toLowerCase();
        const variations = this.getLocationVariations(localLower);

        return vagas.filter(vaga => {
            const location = (vaga.location || "").toLowerCase();
            return variations.some(v => location.includes(v));
        });
    }

    getLocationVariations(local) {
        const variations = [local];

        // Variações comuns
        const variationMap = {
            "araraquara": ["araraquara", "arara", "ARA"],
            "sp": ["sp", "são paulo", "sao paulo", "estado de sp", "são paulo, sp", "sao paulo, sp"],
            "são paulo": ["são paulo", "sao paulo", "sp"],
            "campinas": ["campinas", "campinas, sp"],
            "rio": ["rio de janeiro", "rj", "rio", "rio, rj"],
            "bh": ["belo horizonte", "mg"],
            "curitiba": ["curitiba", "pr"],
            "brasilia": ["brasília", "brasilia", "df"]
        };

        const lower = local.toLowerCase();
        if (variationMap[lower]) {
            variations.push(...variationMap[lower]);
        }

        return [...new Set(variations)];
    }

    _setupResultFilters() {
        const btns = document.querySelectorAll(".filter-btn[data-filter]");
        btns.forEach(btn => {
            btn.addEventListener("click", () => {
                // Remove active de todos
                btns.forEach(b => b.classList.remove("active"));
                // Ativa clicado
                btn.classList.add("active");

                const f = btn.dataset.filter;
                this.aplicarFiltroResultado(f);
            });
        });
    }

    aplicarFiltroResultado(filtro) {
        let vagasFiltradas = [...this.vagasOriginais];

        switch (filtro) {
            case "all":
                vagasFiltradas = [...this.vagasOriginais];
                break;
            case "araraquara":
                vagasFiltradas = this.vagasAraraquara;
                break;
            case "regiao":
                vagasFiltradas = this.vagasRegiao;
                break;
            case "destaque":
                vagasFiltradas = this.vagasDestaque;
                break;
            case "recentes":
                vagasFiltradas = this.vagasRecentes;
                break;
            case "high":
                vagasFiltradas = this.vagasOriginais.filter(v => v.chance_contratacao?.cor === "success");
                break;
            case "medium":
                vagasFiltradas = this.vagasOriginais.filter(v => v.chance_contratacao?.cor === "warning");
                break;
        }

        this.vagas = vagasFiltradas;
        this.renderizarVagas();

        // Aplicar ordenação atual
        const ordenacaoVal = document.querySelector(".ordenacao-option.active")?.dataset?.value || "relevancia";
        if (ordenacaoVal !== "relevancia") {
            this.ordenarVagas(ordenacaoVal);
        }
    }

    criarCardVaga(vaga, index) {
        const match = vaga.match || { score: 0, matches: [], missing: [] };
        const chance = vaga.chance_contratacao || { score: 0, label: "N/A", cor: "warning" };
        const chanceScore = chance.score || 0;
        const progressWidth = Math.min(chanceScore, 100);

        const matches = match.matches || [];
        const missing = match.missing || [];
        const total = matches.length + missing.length;
        const matchPct = total > 0 ? Math.round((matches.length / total) * 100) : 0;

        // Skills que você tem
        const hasSkillsHtml = matches.slice(0, 10).map(m => `
            <div class="skill-compare-item has-skill">
                <span class="skill-icon">✓</span>
                <span class="skill-name">${m}</span>
            </div>
        `).join("");

        // Skills pedidas pela vaga que você NÃO tem
        const needSkillsHtml = missing.slice(0, 8).map(m => `
            <div class="skill-compare-item need-skill">
                <span class="skill-icon">+</span>
                <span class="skill-name">${m}</span>
            </div>
        `).join("");

        const posted = vaga.posted_date || "Recente";
        const source = vaga.source || "Google Jobs";
        const rank = index + 1;
        const dias = vaga.dias_desde_postagem;
        const recente = dias !== null && dias <= 7 ? "novo" : "";
        const destaque = chanceScore > 80 ? "destaque" : "";

        // Badge de modelo de trabalho
        const modelo = (vaga.modelo_trabalho || vaga.job_type || "").toLowerCase();
        let modeloBadge = "";
        if (modelo.includes("remote") || modelo.includes("remoto")) {
            modeloBadge = '<span class="badge-modelo remoto">🏠 Remoto</span>';
        } else if (modelo.includes("hybrid") || modelo.includes("híbrido") || modelo.includes("hibrido")) {
            modeloBadge = '<span class="badge-modelo hibrido">🔄 Híbrido</span>';
        } else if (modelo.includes("presencial") || modelo.includes("on-site") || modelo.includes("onsite")) {
            modeloBadge = '<span class="badge-modelo presencial">🏢 Presencial</span>';
        }

        // Ícone da fonte melhorado
        let sourceIcon = "🌐";
        let sourceClass = "source-default";
        if (source.toLowerCase().includes("linkedin")) {
            sourceIcon = "💼";
            sourceClass = "source-linkedin";
        } else if (source.toLowerCase().includes("google")) {
            sourceIcon = "🔍";
            sourceClass = "source-google";
        } else if (source.toLowerCase().includes("catho")) {
            sourceIcon = "📋";
            sourceClass = "source-catho";
        } else if (source.toLowerCase().includes("vagas")) {
            sourceIcon = "🎯";
            sourceClass = "source-vagas";
        } else if (source.toLowerCase().includes("indeed")) {
            sourceIcon = "✅";
            sourceClass = "source-indeed";
        } else if (source.toLowerCase().includes("jooble")) {
            sourceIcon = "🔎";
            sourceClass = "source-jooble";
        }
        const fonteBadge = `<span class="badge-fonte ${sourceClass}" title="Fonte: ${source}">${sourceIcon} ${source}</span>`;

        // Badge de nível da vaga
        let nivelBadge = "";
        if (vaga.nivel_vaga && vaga.nivel_vaga !== "não especificado") {
            const nivelLabel = vaga.nivel_vaga.charAt(0).toUpperCase() + vaga.nivel_vaga.slice(1);
            const nivelClass = vaga.nivel_vaga === "júnior" || vaga.nivel_vaga === "junior" ? "junior" :
                              vaga.nivel_vaga === "pleno" ? "pleno" : "senior";
            nivelBadge = `<span class="nivel-badge ${nivelClass}">${nivelLabel}</span>`;
        }

        const recBadge = recente ? `<span class="badge-novo">⚡ Nova</span>` : "";

        // Detecção de localização melhorada
        const vagaLocation = (vaga.location || "").toLowerCase();
        const isAraraquara = this.ehLocalidade(vagaLocation, "araraquara");
        const isRegiao = !isAraraquara && (this.ehLocalidade(vagaLocation, "sp") || this.ehLocalidade(vagaLocation, "são paulo"));
        const locationClass = isAraraquara ? "araraquara" : isRegiao ? "regiao" : "";

        // Tooltip com descrição resumida
        const descricaoResumida = vaga.description
            ? vaga.description.substring(0, 200).replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()
            : "";
        const tooltipAttr = descricaoResumida ? `title="${descricaoResumida}..." data-tooltip="true"` : "";

        return `
            <div class="job-card ${chance.cor} ${recente} ${locationClass} ${destaque}" ${tooltipAttr}>
                <div class="card-header">
                    <div class="card-rank-info">
                        <div class="card-rank">#${rank}</div>
                        ${recBadge}
                        ${destaque ? '<span class="badge-destaque">⭐ Destaque</span>' : ''}
                    </div>
                    <div class="chance-badge ${chance.cor}">
                        <div class="chance-score">${chanceScore}%</div>
                        <div class="chance-label">${chance.label}</div>
                    </div>
                </div>

                <div class="card-body">
                    <h3 class="job-title" ${tooltipAttr}>${vaga.title || "Título não informado"}</h3>
                    <p class="job-company">${vaga.company || "Empresa não informada"}</p>

                    <div class="job-meta">
                        ${fonteBadge}
                        <span class="meta-item">📍 ${vaga.location || "Não informado"}</span>
                        <span class="meta-item">📅 ${posted}</span>
                    </div>

                    <div class="job-badges">
                        ${modeloBadge}
                        ${nivelBadge ? `<div class="nivel-container">${nivelBadge}</div>` : ""}
                    </div>

                    <div class="match-overview">
                        <div class="match-overview-bar">
                            <div class="match-overview-fill" style="width: ${matchPct}%"></div>
                        </div>
                        <div class="match-overview-stats">
                            <div class="stat-item stat-has">
                                <span class="stat-icon">✓</span>
                                <span class="stat-value">${matches.length}</span>
                                <span class="stat-label">Você tem</span>
                            </div>
                            <div class="stat-divider">de ${total} requisitos</div>
                            <div class="stat-item stat-need">
                                <span class="stat-icon">+</span>
                                <span class="stat-value">${missing.length}</span>
                                <span class="stat-label">Faltam</span>
                            </div>
                        </div>
                    </div>

                    <div class="compare-section">
                        <div class="compare-header">
                            <h4>📋 O que a vaga pede vs o que você tem</h4>
                        </div>

                        <div class="compare-grid">
                            <div class="compare-col compare-has">
                                <div class="compare-col-header">
                                    <span class="compare-icon">✓</span>
                                    <span>Você já tem</span>
                                    <span class="compare-count">${matches.length}</span>
                                </div>
                                <div class="compare-list">
                                    ${hasSkillsHtml || '<div class="compare-empty">Nenhuma match</div>'}
                                </div>
                            </div>

                            <div class="compare-col compare-need">
                                <div class="compare-col-header">
                                    <span class="compare-icon">+</span>
                                    <span>Você precisa</span>
                                    <span class="compare-count">${missing.length}</span>
                                </div>
                                <div class="compare-list">
                                    ${needSkillsHtml || '<div class="compare-empty">Nada! Você tem tudo</div>'}
                                </div>
                            </div>
                        </div>
                    </div>

                    ${vaga.description ? `
                    <details class="job-description-toggle">
                        <summary>Ver descrição da vaga</summary>
                        <p class="job-description">${vaga.description.substring(0, 500)}...</p>
                    </details>` : ""}
                </div>

                <div class="card-footer">
                    <a href="${vaga.apply_link || vaga.link}" target="_blank" class="btn btn-primary btn-block">
                        📎 Candidatar-se
                    </a>
                </div>
            </div>
        `;
    }

    ehLocalidade(locationText, locality) {
        const variations = this.getLocationVariations(locality);
        return variations.some(v => locationText.includes(v));
    }

    /* ========== TOAST ========== */
    showToast(message, type = "info") {
        let toast = document.getElementById("toast");

        if (!toast) {
            toast = document.createElement("div");
            toast.id = "toast";
            toast.className = "toast";
            document.body.appendChild(toast);
        }

        toast.textContent = message;
        toast.className = `toast show ${type}`;

        setTimeout(() => {
            toast.className = "toast";
        }, 5000);
    }
}

// Iniciar aplicação quando DOM estiver pronto
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => new VagaMatchApp());
} else {
    new VagaMatchApp();
}
