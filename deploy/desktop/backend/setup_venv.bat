@echo off
REM ============================================================
REM Ivan Helpdesk - Setup do Ambiente Virtual
REM Execute uma vez para configurar o venv e dependências
REM ============================================================

title Ivan Helpdesk - Setup
color 0A

set BACKEND_DIR=E:\projetos\ivan-helpdesk\deploy\desktop\backend
set VENV_DIR=%BACKEND_DIR%\.venv

echo.
echo  ╔═════════════════════════════════════════════════════════╗
echo  ║          IVAN HELPDESK - SETUP DO AMBIENTE               ║
echo  ╚═════════════════════════════════════════════════════════╝
echo.

cd /d "%BACKEND_DIR%"

REM Cria venv se não existir
if not exist "%VENV_DIR%" (
    echo [1/3] Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar venv. Verifique se Python está no PATH.
        pause
        exit /b 1
    )
    echo OK
) else (
    echo [1/3] Ambiente virtual já existe - pulando criação
)

REM Atualiza pip
echo [2/3] Atualizando pip...
%VENV_DIR%\Scripts\python.exe -m pip install --upgrade pip --quiet

REM Instala dependências
echo [3/3] Instalando dependências do requirements.txt...
%VENV_DIR%\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependências.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  SETUP CONCLUÍDO COM SUCESSO!
echo ============================================================
echo.
echo Para executar a demo, dê duplo clique em:
echo   "Ivan Helpdesk Demo.bat"  (na Área de Trabalho)
echo.
echo Ou execute manualmente:
echo   cd %BACKEND_DIR%
echo   .venv\Scripts\uvicorn.exe main:app --reload --port 8000
echo.
pause