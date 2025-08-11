import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

username = "eroo1443587"  # BURAYA admin yapmak istediğin kullanıcı adını yaz

cursor.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
conn.commit()

if cursor.rowcount == 0:
    print(f"Kullanıcı bulunamadı: {username}")
else:
    print(f"{username} artık admin!")

conn.close()
