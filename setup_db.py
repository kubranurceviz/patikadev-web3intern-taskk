import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Kullanıcılar tablosu (önceden oluşturulmuş)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    github_username TEXT NOT NULL,
    cv_text TEXT NOT NULL,
    approved_skills TEXT
)
''')

# Repositories tablosu
cursor.execute('''
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    repo_name TEXT,
    repo_url TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Commits tablosu
cursor.execute('''
CREATE TABLE IF NOT EXISTS commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER,
    commit_message TEXT,
    commit_url TEXT,
    commit_date TEXT,
    FOREIGN KEY (repo_id) REFERENCES repositories (id)
)
''')

conn.commit()
conn.close()
