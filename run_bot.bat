@echo off
rem ==============================================================================
rem Script: run_bot.bat
rem Progetto: CUP Marche Monitor Bot
rem Descrizione: Script batch per l'esecuzione del bot di monitoraggio delle
rem              disponibilita' CUP Marche.
rem              Imposta la cartella di lavoro, assicura la presenza della cartella
rem              logs ed esegue python src\main.py reindirizzando output ed errori
rem              in coda al file logs\scheduler.log.
rem ==============================================================================

cd /d "%~dp0"

if not exist logs mkdir logs

echo [%DATE% %TIME%] Inizio esecuzione del monitor... >> logs\scheduler.log
python src\main.py >> logs\scheduler.log 2>&1
echo [%DATE% %TIME%] Esecuzione terminata con codice: %ERRORLEVEL% >> logs\scheduler.log
echo ============================================================ >> logs\scheduler.log
