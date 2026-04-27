@echo off
REM ============================================================
REM JOSE VICTOR - PORTFOLIO LAUNCHER
REM ============================================================
title Portfolio Jose Victor

cd /d "%~dp0"

echo.
echo  ============================================================
echo    JOSE VICTOR - Portfolio Local
echo  ============================================================
echo.
echo  Iniciando servidor em http://localhost:8765
echo  Admin em            http://localhost:8765/admin.html
echo  Senha padrao:       joseivictor2026
echo.
echo  Pressione Ctrl+C para parar
echo  ============================================================
echo.

REM tenta python no PATH
where python >nul 2>nul
if %errorlevel%==0 (
    start "" http://localhost:8765/
    python server.py 8765
    goto :end
)

REM fallback: py launcher
where py >nul 2>nul
if %errorlevel%==0 (
    start "" http://localhost:8765/
    py server.py 8765
    goto :end
)

echo ERRO: Python nao encontrado no PATH.
echo Instale Python 3 em https://python.org
pause
:end
