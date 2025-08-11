# update_db.py
import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Users tablosu için ek sütunlar
try:
    cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    print("bio sütunu eklendi.")
except sqlite3.OperationalError:
    print("bio sütunu zaten mevcut.")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
    print("profile_pic sütunu eklendi.")
except sqlite3.OperationalError:
    print("profile_pic sütunu zaten mevcut.")

# Posts tablosu
cursor.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    caption TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")
print("posts tablosu kontrol edildi/oluşturuldu.")

conn.commit()
conn.close()
