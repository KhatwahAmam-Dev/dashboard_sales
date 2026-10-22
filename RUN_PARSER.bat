@echo off
echo ========================================
echo  Parser SQL Dump - AM024/AM022
echo  Double klik untuk jalan
echo ========================================
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
  echo Python belum terinstall! Install dari python.org
  pause
  exit /b
)
pip install openpyxl --quiet
set /p file=Drag file .sql kesini atau ketik nama file: 
python parse_sql_dump_FINAL.py "%file%" --json --csv --excel
echo.
echo Selesai! Cek folder output_...
pause
