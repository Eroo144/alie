from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import request
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'gizli-anahtar'  # Session için gerekli

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.String(500))
    profile_pic = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)

    posts = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(300), nullable=False)
    caption = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()
# Veritabanı bağlantısı
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    if 'username' in session:
        conn = get_db_connection()
        posts = conn.execute('''
            SELECT posts.*, users.username 
            FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY created_at DESC
        ''').fetchall()
        conn.close()
        return render_template('home.html', username=session['username'], posts=posts)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Kayıt başarılı! Giriş yapabilirsiniz.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Bu kullanıcı adı zaten var.')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Kullanıcı adı veya şifre hatalı.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# ✅ ADMIN PANEL ROUTE’U
@app.route('/admin')
def admin_panel():
    if 'username' not in session:
        flash('Önce giriş yapmalısınız.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()

    if not user or user['is_admin'] != 1:
        conn.close()
        flash('Bu sayfaya erişim izniniz yok.')
        return redirect(url_for('home'))

    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    return render_template('admin.html', users=users)

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' not in session:
        flash('Önce giriş yapmalısınız.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    current_user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    
    if not current_user or current_user['is_admin'] != 1:
        conn.close()
        flash('Bu işlemi yapmaya yetkiniz yok.')
        return redirect(url_for('home'))

    # Kendi hesabını silmesini engelleyelim
    if current_user['id'] == user_id:
        conn.close()
        flash('Kendi hesabınızı silemezsiniz!')
        return redirect(url_for('admin_panel'))

    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    flash('Kullanıcı silindi.')
    return redirect(url_for('admin_panel'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        flash('Önce giriş yapmalısınız.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()

    if request.method == 'POST':
        bio = request.form['bio']
        profile_pic = request.form['profile_pic']

        conn.execute('UPDATE users SET bio = ?, profile_pic = ? WHERE username = ?', (bio, profile_pic, session['username']))
        conn.commit()
        flash('Profil güncellendi!')

    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    conn.close()

    return render_template('profile.html', user=user)


@app.route('/user/<username>')
def view_user_profile(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if not user:
        flash("Kullanıcı bulunamadı.")
        return redirect(url_for('home'))

    return render_template('public_profile.html', user=user)

@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if 'username' not in session:
        flash('Önce giriş yapmalısınız.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()

    if request.method == 'POST':
        image_url = request.form['image_url']
        caption = request.form['caption']

        if image_url.strip() == "":
            flash("Fotoğraf URL'si boş olamaz!")
            return redirect(url_for('add_post'))

        conn.execute('INSERT INTO posts (user_id, image_url, caption) VALUES (?, ?, ?)',
                     (user['id'], image_url, caption))
        conn.commit()
        conn.close()
        flash("Post başarıyla paylaşıldı!")
        return redirect(url_for('home'))

    conn.close()
    return render_template('add_post.html')



with app.app_context():
    db.create_all()  # Veritabanı tablolarını oluşturur (sadece ilk sefer çalıştır)

if __name__ == '__main__':
    app.run(debug=True)