from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import time
from detect import detect_objects

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ------------------ DATABASE CONFIG ------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "users.db")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ FILE CONFIG ------------------
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'static/outputs')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ------------------ DATABASE MODEL ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# ------------------ HELPERS ------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ ROUTES ------------------

# 🔐 LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password", "danger")

    return render_template('login.html')


# 📝 REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "warning")
            return redirect(url_for('register'))

        try:
            hashed_password = generate_password_hash(password)

            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash("Account created successfully! Please login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            return f"Error: {e}"

    return render_template('register.html')


# 🏠 HOME (UPLOAD + DETECTION)
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('image')

        if not file or file.filename == "":
            flash("Please select an image!", "warning")
            return redirect(url_for('home'))

        if not allowed_file(file.filename):
            flash("Only PNG, JPG, JPEG allowed!", "danger")
            return redirect(url_for('home'))

        # 🔥 Secure + unique filename
        filename = secure_filename(file.filename)
        filename = str(int(time.time())) + "_" + filename

        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        output_path = os.path.join(OUTPUT_FOLDER, filename)

        # 🔍 Detection
        output_image, stats, objects, summary = detect_objects(filepath, output_path)

        # ✅ Relative path for browser
        relative_path = "outputs/" + filename

        return render_template(
            'result.html',
            image=relative_path,
            stats=stats,
            objects=objects,
            summary=summary,
            user=session['user']
        )

    return render_template('index.html', user=session['user'])


# 🚪 LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))


# 🧪 DEBUG ROUTE
@app.route('/check_users')
def check_users():
    users = User.query.all()
    return str([u.username for u in users])


# ------------------ RUN ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)