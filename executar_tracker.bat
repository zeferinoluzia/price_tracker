@echo off
cd /d "C:\Users\luzia\OneDrive\Área de Trabalho\price_tracker"

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

python -u main.py >> tracker.log 2>&1