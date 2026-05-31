@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist "..\src\docker-compose.yml" (
  cd /d "%~dp0..\src"
) else (
  cd /d "%~dp0.."
)

echo AVISO: se borraran vistas, marcadores, notas y demas datos guardados.
echo.

docker compose --profile tools down -v --rmi local
if errorlevel 1 (
  echo.
  echo ERROR: fallo al limpiar.
  pause
  exit /b 1
)

echo.
echo Listo.
pause
