"""Manual backup script — dumps all Postgres tables to JSON."""
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import sqlalchemy

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL not set')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

engine = sqlalchemy.create_engine(DATABASE_URL)

TABLES = ['clients', 'contract_templates', 'contracts_sent']

data = {'backed_up_at': datetime.utcnow().isoformat(), 'database_url': DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}

with engine.connect() as conn:
    for table in TABLES:
        result = conn.execute(sqlalchemy.text(f'SELECT * FROM {table}'))
        columns = list(result.keys())
        rows = []
        for row in result:
            r = {}
            for i, col in enumerate(columns):
                val = row[i]
                if isinstance(val, datetime):
                    val = val.isoformat()
                r[col] = val
            rows.append(r)
        data[table] = rows
        print(f'  {table}: {len(rows)} rows')

filename = 'backup_' + datetime.utcnow().strftime('%Y-%m-%d_%H%M%S') + '.json'
filepath = os.path.join(BACKUP_DIR, filename)
with open(filepath, 'w') as f:
    json.dump(data, f, indent=2, default=str)

print(f'\nBackup saved: {filepath}')
print(f'Total: {sum(len(data[t]) for t in TABLES)} records across {len(TABLES)} tables')
