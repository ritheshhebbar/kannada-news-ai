import sqlite3
import os
import json

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kannada_news_local.db"))
if not os.path.exists(db_path):
    # Try current directory
    db_path = "kannada_news_local.db"

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def print_separator(title=""):
    print("\n" + "=" * 30 + f" {title} " + "=" * 30)

print_separator("DATABASE OVERVIEW")
print(f"Database File: {db_path}")

# 1. Table Counts
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row["name"] for row in cursor.fetchall() if not row["name"].startswith("sqlite_")]
print("\nTables and Total Records:")
for t in tables:
    cursor.execute(f"SELECT COUNT(*) as count FROM {t};")
    cnt = cursor.fetchone()["count"]
    print(f"  • {t:<22} : {cnt} rows")

# 2. Sources Configured
print_separator("ACTIVE NEWS SOURCES")
cursor.execute("SELECT id, name, base_url, active FROM sources;")
for s in cursor.fetchall():
    status = "Active" if s["active"] else "Inactive"
    print(f"  [{s['id']}] {s['name']:<24} ({status}) - {s['base_url']}")

# 3. Recent Articles with Translations & Summaries
print_separator("RECENT ARTICLES (LATEST 5)")
query = """
SELECT 
    a.id, 
    s.name as source_name, 
    a.title_kn, 
    t.title_en, 
    a.status,
    sm.summary_en,
    sm.key_points
FROM articles a
LEFT JOIN sources s ON a.source_id = s.id
LEFT JOIN translations t ON a.id = t.article_id AND t.is_active = 1
LEFT JOIN summaries sm ON a.id = sm.article_id
ORDER BY a.id DESC
LIMIT 5;
"""
cursor.execute(query)
articles = cursor.fetchall()

for idx, a in enumerate(articles, 1):
    print(f"\n--- Article #{a['id']} [{a['source_name'] or 'Direct Input'}] (Status: {a['status']}) ---")
    print(f"Kannada Title : {a['title_kn']}")
    print(f"English Title : {a['title_en'] or '(Not yet translated)'}")
    if a['summary_en']:
        print(f"AI Summary    : {a['summary_en']}")
    if a['key_points']:
        try:
            kp = json.loads(a['key_points'])
            print("Key Points    :")
            for p in kp:
                print(f"   • {p.get('text', '')} (Evidence: {p.get('evidence', [])})")
        except:
            pass

print("\n" + "=" * 75)
print("Tip: Run 'python scripts/view_db.py' anytime to inspect your SQLite database.")
conn.close()
