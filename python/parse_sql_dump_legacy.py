
"""
SQL Dump Parser - AM024/AM022 - Convert COPY to JSON/CSV/Excel
Bisa handle file 194MB++ (streaming line-by-line, bukan regex raksasa)
Usage:
    python parse_sql_dump.py db_toko_AM022_20261010_220855.sql
    python parse_sql_dump.py db_toko_AM022_20261010_220855.sql --excel --json --csv
"""
import re
import json
import csv
import sys
import os
from collections import defaultdict

def parse_sql_dump(filepath, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    
    db = {}  # table -> {columns: [], rows: []}
    current_table = None
    current_cols = None
    current_rows = []
    total_rows = 0
    tables_found = []
    
    print(f"📂 Membuka file: {filepath} ({os.path.getsize(filepath)/1024/1024:.2f} MB)")
    
    # Regex untuk COPY
    copy_re = re.compile(r'COPY\s+(?:public\.)?"?([a-zA-Z0-9_]+)"?\s*(?:\(([^)]+)\))?\s+FROM\s+stdin;', re.I)
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        line_num = 0
        for line in f:
            line_num += 1
            stripped = line.strip()
            
            # Deteksi awal COPY
            if line.startswith('COPY'):
                # Simpan table sebelumnya jika ada
                if current_table and current_rows:
                    if current_table not in db:
                        db[current_table] = {'columns': current_cols, 'rows': []}
                    db[current_table]['rows'].extend(current_rows)
                    total_rows += len(current_rows)
                    print(f"✅ {current_table}: {len(current_rows)} rows (total {len(db[current_table]['rows'])})")
                    tables_found.append(current_table)
                
                m = copy_re.match(line)
                if m:
                    current_table = m.group(1)
                    cols_raw = m.group(2)
                    if cols_raw:
                        current_cols = [c.strip().strip('"') for c in cols_raw.split(',')]
                    else:
                        current_cols = None
                    current_rows = []
                    if line_num % 10000 == 0:
                        print(f"  ... line {line_num}: start {current_table}")
                else:
                    current_table = None
                    current_cols = None
                    current_rows = []
            
            # Deteksi akhir data: \.
            elif stripped == '\\.' or stripped == '\.':
                if current_table and current_rows:
                    if current_table not in db:
                        db[current_table] = {'columns': current_cols, 'rows': []}
                    db[current_table]['rows'].extend(current_rows)
                    total_rows += len(current_rows)
                    print(f"✅ {current_table}: {len(current_rows)} rows (closed by \\.) - total {len(db[current_table]['rows'])}")
                    tables_found.append(current_table)
                current_table = None
                current_cols = None
                current_rows = []
            
            # Data row (ada TAB)
            elif current_table and '\t' in line:
                parts = line.rstrip('\n\r').split('\t')
                # Jika kolom belum diketahui, buat col_0, col_1...
                if current_cols is None:
                    current_cols = [f'col_{i}' for i in range(len(parts))]
                
                # Handle jika jumlah parts beda (kadang ada \t di dalam data? tapi di POS biasanya aman)
                if len(parts) < len(current_cols):
                    # skip baris rusak
                    continue
                
                row = {}
                for idx, col in enumerate(current_cols):
                    if idx < len(parts):
                        val = parts[idx]
                        if val == '\\N' or val == '\N':
                            val = None
                        row[col] = val
                    else:
                        row[col] = None
                current_rows.append(row)
                
                # Flush tiap 50k rows biar memory nggak bengkak
                if len(current_rows) >= 50000:
                    if current_table not in db:
                        db[current_table] = {'columns': current_cols, 'rows': []}
                    db[current_table]['rows'].extend(current_rows)
                    total_rows += len(current_rows)
                    print(f"  ... {current_table}: flush {len(current_rows)} rows (total so far {len(db[current_table]['rows'])})")
                    current_rows = []
    
    # Simpan sisa
    if current_table and current_rows:
        if current_table not in db:
            db[current_table] = {'columns': current_cols, 'rows': []}
        db[current_table]['rows'].extend(current_rows)
        total_rows += len(current_rows)
    
    print(f"\n🎉 Selesai! Total Tables: {len(db)}, Total Rows: {total_rows}")
    for t in db:
        print(f"  - {t}: {len(db[t]['rows'])} rows, {len(db[t]['columns'] or [])} cols")
        if 'retur_h' in (db[t]['columns'] or []):
            print(f"    → Ada kolom RH (retur_h)")
        if 'planogram' in (db[t]['columns'] or []):
            print(f"    → Ada kolom Plano (planogram)")
    
    return db

def export_json(db, output_dir):
    for table, info in db.items():
        path = os.path.join(output_dir, f"{table}.json")
        with open(path, 'w', encoding='utf-8') as out:
            json.dump(info['rows'], out, ensure_ascii=False, indent=2)
        print(f"📄 JSON: {path} ({len(info['rows'])} rows)")

def export_csv(db, output_dir):
    for table, info in db.items():
        path = os.path.join(output_dir, f"{table}.csv")
        cols = info['columns'] or (list(info['rows'][0].keys()) if info['rows'] else [])
        with open(path, 'w', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=cols, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(info['rows'])
        print(f"📄 CSV: {path}")

def export_excel(db, output_dir):
    try:
        import openpyxl
    except ImportError:
        print("⚠️ openpyxl belum install, install dulu: pip install openpyxl")
        print("   Pakai xlsxwriter sebagai fallback...")
        try:
            import xlsxwriter
        except ImportError:
            print("❌ Tidak ada library Excel. Export JSON/CSV saja. Install: pip install openpyxl")
            return
    
    # Export per table 1 file Excel (biar tidak terlalu besar)
    for table, info in db.items():
        path = os.path.join(output_dir, f"{table}.xlsx")
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = table[:31]
            cols = info['columns'] or list(info['rows'][0].keys()) if info['rows'] else []
            ws.append(cols)
            for row in info['rows'][:100000]:  # limit 100k per file biar tidak berat
                ws.append([row.get(c) for c in cols])
            wb.save(path)
            print(f"📊 Excel: {path} ({min(len(info['rows']),100000)} rows)")
        except Exception as e:
            print(f"❌ Gagal export Excel {table}: {e}")

    # Export all-in-one multi-sheet
    all_path = os.path.join(output_dir, f"ALL_TABLES_{len(db)}tables.xlsx")
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        for table, info in db.items():
            ws = wb.create_sheet(title=table[:31])
            cols = info['columns'] or (list(info['rows'][0].keys()) if info['rows'] else [])
            ws.append(cols)
            for row in info['rows'][:50000]:  # limit 50k per sheet
                ws.append([row.get(c) for c in cols])
        wb.save(all_path)
        print(f"📊 All-in-one Excel: {all_path}")
    except Exception as e:
        print(f"❌ Gagal all-in-one Excel: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_sql_dump.py <file.sql> [--json --csv --excel]")
        print("Contoh: python parse_sql_dump.py db_toko_AM022_20261010_220855.sql --json --csv --excel")
        sys.exit(1)
    
    filepath = sys.argv[1]
    do_json = '--json' in sys.argv or len(sys.argv)==2
    do_csv = '--csv' in sys.argv or len(sys.argv)==2
    do_excel = '--excel' in sys.argv
    
    output_dir = f"output_{os.path.splitext(os.path.basename(filepath))[0]}"
    
    db = parse_sql_dump(filepath, output_dir)
    
    if do_json:
        export_json(db, output_dir)
    if do_csv:
        export_csv(db, output_dir)
    if do_excel:
        export_excel(db, output_dir)
    
    print(f"\n✅ Semua file ada di folder: {output_dir}/")
    print(f"   Khusus RH & Plano cek: ms_item.csv / ms_item.xlsx")
    print(f"   Kolom retur_h = RH, planogram = Plano/No Rak")
