@echo off
title Smart Classroom Monitoring System
echo ========================================================
echo Starting Smart Classroom Monitoring System...
echo ========================================================

if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe run.py
) else (
    python run.py
)

pause
