@echo off
chcp 65001 >nul 2>&1
title VagaMatch - Servidor

echo ========================================
echo    VagaMatch - Iniciando servidor...
echo ========================================
echo.

REM Verificar se python esta disponivel no PATH
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Instale Python 3.11+ em: https://www.python.org/downloads/
    pause
    exit /b 1
)

set "PYTHON_EXE=python"
echo [OK] Python encontrado: %PYTHON_EXE%
echo.

REM Ir para pasta backend
cd /d "%~dp0backend"

REM Instalar dependencias se necessario
echo Verificando dependencias...
"%PYTHON_EXE%" -c "import fastapi" 2>nul || (
    echo Instalando dependencias...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
)

REM Iniciar servidor
echo.
echo ========================================
echo    Servidor iniciado!
echo    Acesse: http://localhost:8001
echo ========================================
echo.

"%PYTHON_EXE%" app.py

pause
