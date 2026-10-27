
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "data" / "retentioniq.db"

connection = sqlite3.connect(db_path)

query = """
SELECT name
FROM sqlite_master
WHERE type = 'table'
ORDER BY name;
"""

tables = connection.execute(query).fetchall()

print("Tables in RetentionIQ database:")

for table in tables:
    print(table[0])

print(f"\nTotal tables: {len(tables)}")

connection.close()
