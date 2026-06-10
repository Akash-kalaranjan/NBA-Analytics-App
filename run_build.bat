@echo off
REM Batch script to run the automated build
REM This is what Task Scheduler will call

cd /d "C:\Users\akash\OneDrive\Desktop\New folder\NBA-Analytics-App"
C:/Users/akash/AppData/Local/Programs/Python/Python311/python.exe run_build_scheduler.py

REM Exit with the same code as Python script
exit /b %ERRORLEVEL%
