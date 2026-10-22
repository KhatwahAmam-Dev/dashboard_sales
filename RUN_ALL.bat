@echo off
echo ========================================
echo  AMANDAMART AM024 - ALL IN ONE LAUNCHER
echo ========================================
echo  1. Parse SQL Dump (Python)
echo  2. Buka Dashboard V3 Ultimate (Browser)
echo  3. Buka Converter V3 Streaming (Browser)
echo  4. Keluar
echo ========================================
set /p pilih=Pilih (1-4): 
if "%pilih%"=="1" goto parse
if "%pilih%"=="2" goto dash
if "%pilih%"=="3" goto conv
if "%pilih%"=="4" exit /b

:parse
set /p file=Drag file .sql kesini: 
python parse_sql_dump_FINAL.py "%file%" --json --csv --excel
pause
goto all

:dash
start "" "dashboard-am024-v3-ultimate.html"
goto all

:conv
start "" "sql-converter-v3-streaming.html"
goto all

:all
"%~f0"
