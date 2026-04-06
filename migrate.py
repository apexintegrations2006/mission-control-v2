"""Add missing columns to the clients table without dropping data."""
import os
import sqlalchemy

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:HzaTftnwdqssxpzbbHAgcDjMKMTAjhxd@junction.proxy.rlwy.net:57759/railway',
)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

COLUMNS_TO_ADD = [
    ('github_repo',           'VARCHAR(500)', "''"),
    ('cloudflare_url',        'VARCHAR(500)', "''"),
    ('live_url',              'VARCHAR(500)', "''"),
    ('google_business',       'VARCHAR(500)', "''"),
    ('google_search_console', 'VARCHAR(500)', "''"),
    ('google_analytics',      'VARCHAR(500)', "''"),
    ('login_credentials',     'TEXT',         "''"),
    ('start_date',            'VARCHAR(20)',   "''"),
    ('total_paid',            'FLOAT',        '0'),
    ('payment_history',       'TEXT',         "'[]'"),
]

engine = sqlalchemy.create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Get existing columns
    result = conn.execute(sqlalchemy.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'clients'"
    ))
    existing = {row[0] for row in result}
    print(f"Existing columns: {sorted(existing)}")

    added = []
    for col_name, col_type, default in COLUMNS_TO_ADD:
        if col_name not in existing:
            sql = f"ALTER TABLE clients ADD COLUMN {col_name} {col_type} DEFAULT {default}"
            conn.execute(sqlalchemy.text(sql))
            added.append(col_name)
            print(f"  + Added: {col_name} ({col_type})")
        else:
            print(f"  . Exists: {col_name}")

    conn.commit()

    # Set start_date on existing seed clients that don't have one
    conn.execute(sqlalchemy.text(
        "UPDATE clients SET start_date = '2025-11-01' WHERE business_name = 'Presidio Dental Care' AND (start_date IS NULL OR start_date = '')"
    ))
    conn.execute(sqlalchemy.text(
        "UPDATE clients SET start_date = '2026-01-15' WHERE business_name = 'Smile Tucson Family Dentistry' AND (start_date IS NULL OR start_date = '')"
    ))
    conn.execute(sqlalchemy.text(
        "UPDATE clients SET start_date = '2026-03-20' WHERE business_name = 'Desert Ridge Oral Surgery' AND (start_date IS NULL OR start_date = '')"
    ))
    conn.commit()
    print("  Updated seed client start dates")

    # Verify
    result = conn.execute(sqlalchemy.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'clients' ORDER BY ordinal_position"
    ))
    final = [row[0] for row in result]
    print(f"\nFinal columns ({len(final)}): {final}")
    print(f"\nMigration complete. Added {len(added)} columns.")
