#!/usr/bin/env python3
"""
VagaMatch - Script de inicialização
Sobe o servidor FastAPI e abre a interface no navegador
"""
import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

# Adicionar backend ao path
BACKEND_PATH = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_PATH))


def abrir_navegador():
    """Abre o navegador após o servidor iniciar"""
    time.sleep(2)  # Aguarda servidor iniciar
    webbrowser.open("http://localhost:8000")


def main():
    print("=" * 50)
    print("    🧭 VagaMatch - Motor de Busca de Vagas")
    print("=" * 50)
    print()

    # Verificar se dependências estão instaladas
    try:
        import fastapi
        import uvicorn
        import requests
    except ImportError:
        print("[⚠️] Instalando dependências...")
        os.system("pip install -r backend/requirements.txt")
        print()

    # Verificar API keys
    from dotenv import load_dotenv
    load_dotenv()

    print("[📡] Fontes de vagas suportadas:")
    print("       • Google Jobs (via SerpAPI) - " + ("configurado ✅" if os.getenv("SERPAPI_KEY") else "não configurado"))
    print("       • Jooble - " + ("configurado ✅" if os.getenv("JOOBLE_API_KEY") else "não configurado"))
    print("       • Indeed (via RapidAPI) - " + ("configurado ✅" if os.getenv("RAPIDAPI_KEY") else "não configurado"))
    print("       • Glassdoor (via RapidAPI) - " + ("configurado ✅" if os.getenv("RAPIDAPI_KEY") else "não configurado"))
    print("       • JSearch (via RapidAPI) - " + ("configurado ✅" if os.getenv("RAPIDAPI_KEY") else "não configurado"))
    print()

    if os.getenv("SERPAPI_KEY") is None:
        print("[💡] DICA: Crie uma conta gratuita em https://serpapi.com")
        print("       Adicione a chave em um arquivo .env na raiz do projeto")
        print("       Exemplo: SERPAPI_KEY=sk_your_key_here")
        print()

    # Iniciar thread do navegador
    threading.Thread(target=abrir_navegador, daemon=True).start()

    # Iniciar servidor
    print("[🚀] Iniciando servidor em http://localhost:8000")
    print("[🔧] Pressione Ctrl+C para parar")
    print()

    import uvicorn
    from backend.app import app

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()