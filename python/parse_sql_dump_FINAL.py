
import re
import json
import csv
import sys
import os

BACKSLASH_N = chr(92) + "N"
BACKSLASH_DOT = chr(92) + "."
NULL_MARKERS = [chr(92)+ "N", chr(92)+chr(92)+"N", "\\N"]

def parse_sql_dump(filepath, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    db = {}
    current_table = None
    current_cols = None
    current_rows = []
    total_rows = 0
    print(f"Membuka file: {filepath} ({os.path.getsize(filepath)/1024/1024:.2f} MB)")
    copy_re = re.compile(r'COPY\s+(?:public\.)?"?([a-zA-Z0-9_]+)"?\s*(?:\(([^)]+)\))?\s+FROM\s+stdin;', re.I)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            stripped = line.strip()
            if line.startswith('COPY'):
                if current_table and current_rows:
                    if current_table not in db:
                        db[current_table] = {'columns': current_cols, 'rows': []}
                    db[current_table]['rows'].extend(current_rows)
                    total_rows += len(current_rows)
                    print(f"OK {current_table}: {len(current_rows)} rows -> total {len(db[current_table]['rows'])}")
                m = copy_re.match(line)
                if m:
                    current_table = m.group(1)
                    cols_raw = m.group(2)
                    if cols_raw:
                        current_cols = [c.strip().strip('"') for c in cols_raw.split(',')]
                    else:
                        current_cols = None
                    current_rows = []
                else:
                    current_table = None
                    current_cols = None
                    current_rows = []
            elif stripped == BACKSLASH_DOT or stripped == chr(92)+chr(92)+".":
                if current_table and current_rows:
                    if current_table not in db:
                        db[current_table] = {'columns': current_cols, 'rows': []}
                    db[current_table]['rows'].extend(current_rows)
                    total_rows += len(current_rows)
                    print(f"OK {current_table}: {len(current_rows)} rows closed")
                current_table = None
                current_cols = None
                current_rows = []
            elif current_table and chr(9) in line:
                parts = line.rstrip('\n\r').split(chr(9))
                if current_cols is None:
                    current_cols = [f'col_{i}' for i in range(len(parts))]
                if len(parts) < 2:
                    continue
                row = {}
                for idx, col in enumerate(current_cols):
                    if idx < len(parts):
                        val = parts[idx]
                        if val == BACKSLASH_N or val == chr(92)+chr(92)+"N":
                            val = None
                        row[col] = val
                    else:
                        row[col] = None
                current_rows.append(row)
                if len(current_rows) >= 50000:
                    if current_table not in db:
                        db[current_table] = {'columns': current_cols, 'rows': []}
                    db[current_table]['rows'].extend(current_rows)
                    total_rows += len(current_rows)
                    print(f"  ... {current_table}: flush {len(current_rows)}")
                    current_rows = []
    if current_table and current_rows:
        if current_table not in db:
            db[current_table] = {'columns': current_cols, 'rows': []}
        db[current_table]['rows'].extend(current_rows)
        total_rows += len(current_rows)
    print(f"\nSelesai! Tables: {len(db)}, Rows: {total_rows}")
    for t in db:
        print(f"  - {t}: {len(db[t]['rows'])} rows")
    return db

def export_json(db, output_dir):
    for table, info in db.items():
        path = os.path.join(output_dir, f"{table}.json")
        with open(path, 'w', encoding='utf-8') as out:
            json.dump(info['rows'], out, ensure_ascii=False, indent=2)
        print(f"JSON: {path}")

def export_csv(db, output_dir):
    for table, info in db.items():
        path = os.path.join(output_dir, f"{table}.csv")
        cols = info['columns'] or (list(info['rows'][0].keys()) if info['rows'] else [])
        with open(path, 'w', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=cols, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(info['rows'])
        print(f"CSV: {path}")

def export_excel(db, output_dir):
    try:
        import openpyxl
    except ImportError:
        print("openpyxl belum install, pip install openpyxl")
        return
    for table, info in db.items():
        path = os.path.join(output_dir, f"{table}.xlsx")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = table[:31]
        cols = info['columns'] or (list(info['rows'][0].keys()) if info['rows'] else [])
        ws.append(cols)
        for row in info['rows'][:100000]:
            ws.append([row.get(c) for c in cols])
        wb.save(path)
        print(f"Excel: {path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_sql_dump.py <file.sql> [--json --csv --excel]")
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
    print(f"\nSemua file ada di folder: {output_dir}/")
