# AMANDAMART AM024 - Dashboard Sales & SQL Parser

Link Live: https://khatwahamam-dev.github.io/dashboard_sales/

## 1 Link Untuk Semua

Repo ini berisi 1 link GitHub Pages yang gabungin:
- **Parser SQL Dump** (57 tables, 2.1jt rows, 194MB) - versi JS streaming, tanpa perlu Python
- **Dashboard V3 Ultimate** - Sales 22.295 trx + ms_item 11.548 (RH & Plano) + m_planogram 3.971

## Cara Pakai (Online - 1 Link)

Buka: https://khatwahamam-dev.github.io/dashboard_sales/

- Tab Parser: Drop file .sql 194MB -> auto parse -> export JSON/CSV/Excel
- Tab Dashboard: Lihat penjualan, RH & Plano, Cross Analysis (Slow+NO RETURN, Fast+Plano kosong)

## Cara Pakai (Offline - 1 Klik Double Klik)

1. Download repo ini sebagai ZIP (Code -> Download ZIP)
2. Extract ke D:\AM024\
3. Double klik RUN_ALL.bat
   - Pilih 1: Parse SQL Dump (butuh Python)
   - Pilih 2: Buka Dashboard
   - Pilih 3: Buka Converter

Atau langsung:
- Double klik RUN_PARSER.bat -> parse
- Double klik RUN_DASHBOARD.bat -> dashboard

## Cara Setup GitHub Pages

1. Fork/Clone repo ini
2. Settings -> Pages -> Source: Deploy from branch -> Branch: main -> Folder: /docs -> Save
3. Tunggu 2 menit, link jadi https://username.github.io/dashboard_sales/

## Build .EXE (Opsional)

```
pip install pyinstaller
pyinstaller --onefile --noconsole --name AM024_Parser python/parse_sql_dump_FINAL.py
```
Hasil di dist/AM024_Parser.exe

## Fitur RH & Plano

- ms_item.csv: kolom retur_h (RH) = R_H-90 DAYS, R_H-30, NO RETURN, TUKAR GULING
- planogram = No Rak, \N = belum punya rak
- Cross Analysis: Slow+NO RETURN harus clearance, Fast+Plano kosong harus segera set rak

