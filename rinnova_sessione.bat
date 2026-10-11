@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ============================================================
echo   RINNOVO SESSIONE SPID PER CUP MONITOR
echo ============================================================
echo.
echo 1. Si aprirà il browser: effettua il login SPID sul portale.
echo 2. Una volta completato il login, torna qui e premi INVIO.
echo.
python src/main.py --login
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Errore durante il login SPID.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ============================================================
echo   COPIA AUTOMATICA NEGLI APPUNTI
echo ============================================================
powershell -Command "Get-Content -Raw 'session/state.json' | Set-Clipboard"
echo ✅ Nuova sessione COPIATA NEGLI APPUNTI con successo!
echo.
echo Apertura pagina dei Secrets di GitHub in corso...
start https://github.com/edik17/CUP-Monitor/settings/secrets/actions/new
echo.
echo ============================================================
echo   ISTRUZIONI RAPIDE (2 PASSAGGI):
echo ============================================================
echo 1. Nella pagina aperta su GitHub, nel campo Name scrivi:
echo    CUP_SESSION_STATE
echo 2. Nel box Secret premi CTRL+V (Incolla) e clicca 'Add secret'.
echo ============================================================
echo.
echo Fatto! Ora puoi chiudere questa finestra e spegnere il PC.
pause
