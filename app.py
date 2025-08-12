from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'gizli-anahtar'  # Session için gerekli

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# MODELLER
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Veritabanı tablolarını oluştur
with app.app_context():
    db.create_all()

# ROUTE'LAR
@app.route('/')
def home():
    if 'username' in session:
        posts = Post.query.join(User).order_by(Post.created_at.desc()).all()
        return render_template('home.html', username=session['username'], posts=posts)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten var.')
        else:
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Kayıt başarılı! Giriş yapabilirsiniz.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            return redirect(url_for('home'))
        else:
            flash('Kullanıcı adı veya şifre hatalı.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin_panel():
    if 'username' not in session:
        flash('Önce giriş yapmalısınız.')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if not user or not user.is_admin:
        flash('Bu sayfaya erişim izniniz yok.')
        return redirect(url_for('home'))

    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' not in session:
        flash('Önce giriş yapmalısınız.')
        return redirect(url_for('login'))

    current_user = User.query.filter_by(username=session['username']).first()

    if not current_user or not current_user.is_admin:
        flash('Bu işlemi yapmaya yetkiniz yok.')
        return redirect(url_for('home'))

    if current_user.id == user_id:
        flash('Kendi hesabınızı silemezsiniz!')
        return redirect(url_for('admin_panel'))

    user_to_delete = User.query.get(user_id)
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Kullanıcı silindi.')
    else:
        flash('Kullanıcı bulunamadı.')

    return redirect(url_for('admin_panel'))

@app.route('/make_admin/<username>')
def make_admin(username):
    if 'username' not in session:
        flash('Önce giriş yapmalısınız.')
        return redirect(url_for('login'))

    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user or not current_user.is_admin:
        flash('Bu işlemi yapmaya yetkiniz yok.')
        return redirect(url_for('home'))

    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Kullanıcı bulunamadı.')
        return redirect(url_for('admin_panel'))

    user.is_admin = True
    db.session.commit()
    flash(f'{username} admin yapıldı.')
    return redirect(url_for('admin_panel'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        flash('Önce giriş yapmalısınız.')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        bio = request.form['bio']
        profile_pic = request.form['profile_pic']

        user.bio = bio
        user.profile_pic = profile_pic
        db.session.commit()
        flash('Profil güncellendi!')

    return render_template('profile.html', user=user)

@app.route('/user/<username>')
def view_user_profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("Kullanıcı bulunamadı.")
        return redirect(url_for('home'))

    return render_template('public_profile.html', user=user)

@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if 'username' not in session:
        flash('Önce giriş yapmalısınız.')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        image_url = request.form['image_url']
        caption = request.form['caption']

        if image_url.strip() == "":
            flash("Fotoğraf URL'si boş olamaz!")
            return redirect(url_for('add_post'))

        new_post = Post(user_id=user.id, image_url=image_url, caption=caption)
        db.session.add(new_post)
        db.session.commit()
        flash("Post başarıyla paylaşıldı!")
        return redirect(url_for('home'))

    return render_template('add_post.html')


if __name__ == '__main__':
    app.run(debug=True)
