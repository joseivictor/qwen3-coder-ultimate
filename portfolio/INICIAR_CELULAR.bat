@echo off
REM ============================================================
REM JOSE VICTOR — PORTFOLIO LAN (CELULAR mesma WiFi)
REM ============================================================
title Portfolio LAN — celular

cd /d "%~dp0"

echo.
echo  ============================================================
echo    JOSE VICTOR — Portfolio LAN
echo  ============================================================
echo.
echo   Servidor abrira na rede local (mesma WiFi do celular).
echo   ATENCAO: na 1a vez o Windows pode pedir pra liberar a porta.
echo            Click em "Permitir acesso" pra rede privada.
echo.
echo   Pressione Ctrl+C nesta janela pra parar.
echo  ============================================================
echo.

REM detecta python
where python >nul 2>nul
if %errorlevel% neq 0 (
  where py >nul 2>nul
  if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado. Instale em https://python.org
    pause
    exit /b 1
  )
  set PY=py
) else (
  set PY=python
)

REM mostra IP + QR primeiro (numa janela secundaria)
start "QR Code" %PY% show_qr.py

REM abre browser local
start "" http://localhost:8765/

REM inicia server escutando rede
%PY% server.py 8765 --lan
