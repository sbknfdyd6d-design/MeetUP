import os
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from markupsafe import escape

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------- Models ----------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)


# ---------- Forms ----------

class RegistrationForm(FlaskForm):
    username = StringField('Benutzername',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('E-Mail',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Passwort',
                             validators=[DataRequired()])
    confirm_password = PasswordField('Passwort bestätigen',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrieren')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Dieser Benutzername ist bereits vergeben.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Diese E-Mail-Adresse ist bereits registriert.')


class LoginForm(FlaskForm):
    email = StringField('E-Mail',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Passwort',
                             validators=[DataRequired()])
    remember = BooleanField('Angemeldet bleiben')
    submit = SubmitField('Einloggen')


# ---------- Auth ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash(f'Konto für {form.username.data} erstellt! Du kannst dich jetzt einloggen.', 'success')
        return redirect(url_for('login'))
    return render_template("register.html", title='Registrieren', form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Erfolgreich eingeloggt!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login fehlgeschlagen. Bitte E-Mail und Passwort prüfen.', 'danger')
    return render_template("login.html", title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


# ---------- Pages ----------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/events")
@login_required
def events():
    all_events = Event.query.all()
    return render_template("events.html", events=all_events)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        new_event = Event(
            title=request.form["title"],
            date=request.form["date"],
            time=request.form["time"],
            description=request.form["description"]
        )
        db.session.add(new_event)
        db.session.commit()
        flash('Event wurde erstellt!', 'success')
        return redirect(url_for('events'))
    return render_template("create_event.html")


@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        text = request.form["text"]
        new_message = Message(username=current_user.username, text=text)
        db.session.add(new_message)
        db.session.commit()
        return redirect(url_for('chat'))
    messages = Message.query.all()
    return render_template("chat.html", messages=messages)


@app.route("/messages")
def messages():
    messages = Message.query.all()
    html = ""
    for message in messages:
        html += f"""
        <div class="event-card">
            <h3>{escape(message.username)}</h3>
            <p>{escape(message.text)}</p>
        </div>
        """
    return html


@app.route("/delete/<int:event_id>", methods=["POST"])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event wurde gelöscht.', 'success')
    return redirect(url_for('events'))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
