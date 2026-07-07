@echo off
cd /d "%~dp0"
set "PATH=%PATH%;C:\Users\user2\.local\bin"

echo Starting Postgres...
docker compose up -d >nul 2>&1

echo Opening browser in a few seconds...
start "" /min cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8010"

echo Starting Rowad SQL Data Assistant...
echo (Ollama must already be running with gemma4:e4b pulled.)
echo Close this window to stop the chatbot.
echo.
uv run uvicorn app.main:app --port 8010

pause
