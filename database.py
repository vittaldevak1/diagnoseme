import sqlite3

def init_db():
    conn = sqlite3.connect("diagnoseme.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age TEXT,
            gender TEXT,
            allergies TEXT,
            conditions TEXT,
            medications TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            summary TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_user(name, age, gender, allergies, conditions, medications):
    conn = sqlite3.connect("diagnoseme.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (name, age, gender, allergies, conditions, medications)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, age, gender, allergies, conditions, medications))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def get_user(name):
    conn = sqlite3.connect("diagnoseme.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE name = ?', (name,))
    user = cursor.fetchone()
    conn.close()
    return user

def save_history(user_id, summary):
    conn = sqlite3.connect("diagnoseme.db")
    cursor = conn.cursor()
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute('''
        INSERT INTO history (user_id, date, summary)
        VALUES (?, ?, ?)
    ''', (user_id, date, summary))
    conn.commit()
    conn.close()

def get_history(user_id):
    conn = sqlite3.connect("diagnoseme.db")
    cursor = conn.cursor()
    cursor.execute('SELECT date, summary FROM history WHERE user_id = ?', (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history

init_db()
print("Database ready!")
