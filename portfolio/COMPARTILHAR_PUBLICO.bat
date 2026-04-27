@echo off
REM ============================================================
REM JOSE VICTOR — PORTFOLIO PUBLICO (Cloudflare Tunnel)
REM ============================================================
title Portfolio Publico — Cloudflare Tunnel

cd /d "%~dp0"

echo.
echo  ============================================================
echo    JOSE VICTOR — Compartilhar Publicamente
echo  ============================================================
echo.
echo   Vai gerar uma URL publica tipo:
echo     https://random-words.trycloudflare.com
echo.
echo   QUALQUER PESSOA com o link consegue ver. Admin fica
echo   bloqueado pra acesso publico (so editavel localmente).
echo.
echo   Pressione Ctrl+C aqui ou na janela do tunel pra parar.
echo  ============================================================
echo.

REM checa python
where python >nul 2>nul
if %errorlevel% neq 0 (
  where py >nul 2>nul
  if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado.
    pause
    exit /b 1
  )
  set PY=py
) else (
  set PY=python
)

REM checa cloudflared no PATH
where cloudflared >nul 2>nul
if %errorlevel% neq 0 (
  REM verifica se ja baixou local
  if not exist "cloudflared.exe" (
    echo Baixando cloudflared.exe ^(uma unica vez^)...
    echo.
    powershell -Command "& {$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'}"
    if not exist "cloudflared.exe" (
      echo ERRO: download falhou. Tenta:
      echo   choco install cloudflared
      pause
      exit /b 1
    )
    echo OK baixado.
    echo.
  )
  set CFD=cloudflared.exe
) else (
  set CFD=cloudflared
)

REM inicia server em modo public ^(localhost-only admin^), em janela separada
start "Portfolio Server" %PY% server.py 8765 --lan --public

REM espera 2 segundos pro server subir
timeout /t 2 /nobreak >nul

REM abre tunnel
echo.
echo Abrindo tunel publico... aguarde a URL aparecer abaixo:
echo.
%CFD% tunnel --url http://localhost:8765
