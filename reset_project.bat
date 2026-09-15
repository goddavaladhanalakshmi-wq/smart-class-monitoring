@echo off
title Smart Classroom - Safe Project Reset
echo ========================================================
echo   SMART CLASS MONITORING - SAFE PROJECT RESET
echo ========================================================
echo.
echo This will create a backup, clear old test attendance,
echo remove old student profiles, and prepare the project
echo for a fresh live demonstration.
echo.
python reset_project.py
echo.
pause
