@echo off
REM ============================================================
REM JOSE VICTOR - REDEPLOY DO SITE PUBLICO (Vercel)
REM ============================================================
REM Toda vez que voce adicionar videos/experts/cursos no admin
REM local, rode este .bat pra atualizar a versao publica em
REM https://jose-victor-portfolio.vercel.app
REM ============================================================
title Atualizar Site Publico

cd /d "%~dp0"

echo.
echo  ============================================================
echo    Atualizando https://jose-victor-portfolio.vercel.app
echo  ============================================================
echo.

where vercel >nul 2>nul
if %errorlevel% neq 0 (
  echo ERRO: Vercel CLI nao encontrado.
  echo Instalando...
  npm install -g vercel
)

echo Subindo nova versao... ^(pode demorar 30-60 segundos^)
echo.

vercel deploy --prod --yes

echo.
echo  ============================================================
echo   Pronto! Site atualizado.
echo   URL: https://jose-victor-portfolio.vercel.app
echo  ============================================================
echo.
pause
