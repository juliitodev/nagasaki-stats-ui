@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist "..\src\docker-compose.yml" (
  cd /d "%~dp0..\src"
) else (
  cd /d "%~dp0.."
)

echo Deteniendo desde: %CD%
echo (Se conservan vistas, marcadores y notas en Redis.)
echo.

docker compose --profile tools down
if errorlevel 1 (
  echo.
  echo ERROR: fallo al detener los contenedores.
  pause
  exit /b 1
)

echo.
echo Listo.
pause
