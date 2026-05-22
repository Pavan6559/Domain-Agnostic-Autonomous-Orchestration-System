@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
echo Activating virtual environment and running RAG.py...
.\.venv\Scripts\python.exe RAG.py
pause

