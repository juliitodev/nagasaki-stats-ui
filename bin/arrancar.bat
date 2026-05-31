@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist "..\src\docker-compose.yml" (
  cd /d "%~dp0..\src"
) else (
  cd /d "%~dp0.."
)

echo Arrancando desde: %CD%
echo Web: http://localhost:3080  (profesor / profesor123)
echo.

docker compose up --build %*
if errorlevel 1 (
  echo.
  echo ERROR: no se pudo arrancar. Comprueba que Docker Desktop este en marcha.
  pause
  exit /b 1
)
