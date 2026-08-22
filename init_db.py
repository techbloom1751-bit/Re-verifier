import sqlite3
import os

os.makedirs('database', exist_ok=True)
conn = sqlite3.connect('database/government.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS official_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference_number TEXT UNIQUE,
        department TEXT,
        issue_date TEXT,
        document_hash TEXT
    )
''')
cursor.execute('''
    INSERT OR IGNORE INTO official_documents 
    (reference_number, department, issue_date, document_hash)
    VALUES ('UP/EDU/2026/10293', 'Higher Education', '18 August 2026', '8f31c9a7')
''')
conn.commit()
conn.close()
print("✅ Database created!")