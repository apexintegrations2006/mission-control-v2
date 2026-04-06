"""Restore script — reads a backup JSON file and restores all data into Postgres.

Usage: python3 restore.py backups/backup_2026-04-06_000000.json
"""
import os
import sys
import json
from dotenv import load_dotenv
import sqlalchemy

load_dotenv()

if len(sys.argv) < 2:
    print('Usage: python3 restore.py <backup_file.json>')
    sys.exit(1)

backup_file = sys.argv[1]
if not os.path.exists(backup_file):
    print(f'Error: File not found: {backup_file}')
    sys.exit(1)

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL not set')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

with open(backup_file) as f:
    data = json.load(f)

print(f'Backup from: {data.get("backed_up_at", "unknown")}')

# Order matters for foreign keys
TABLES = ['clients', 'contract_templates', 'contracts_sent']

engine = sqlalchemy.create_engine(DATABASE_URL)

with engine.connect() as conn:
    for table in TABLES:
        rows = data.get(table, [])
        if not rows:
            print(f'  {table}: no data in backup, skipping')
            continue

        existing = conn.execute(sqlalchemy.text(f'SELECT COUNT(*) FROM {table}')).fetchone()[0]
        if existing > 0:
            confirm = input(f'  {table}: {existing} rows exist in DB, {len(rows)} in backup. Overwrite? (yes/no): ')
            if confirm.lower() != 'yes':
                print(f'  {table}: skipped')
                continue
            conn.execute(sqlalchemy.text(f'DELETE FROM {table}'))
            conn.commit()
            print(f'  {table}: cleared {existing} existing rows')

        columns = list(rows[0].keys())
        for row in rows:
            placeholders = ', '.join([f':{c}' for c in columns])
            col_names = ', '.join(columns)
            conn.execute(sqlalchemy.text(f'INSERT INTO {table} ({col_names}) VALUES ({placeholders})'), row)

        conn.commit()
        print(f'  {table}: restored {len(rows)} rows')

print('\nRestore complete.')
