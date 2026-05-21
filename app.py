import os
from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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


# ---------- Auth ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            error = "Bitte alle Felder ausfüllen."
        elif User.query.filter_by(username=username).first():
            error = "Benutzername bereits vergeben."
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session["username"] = username
            return redirect(url_for("index"))
    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["username"] = username
            return redirect(url_for("index"))
        error = "Falscher Benutzername oder Passwort."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))


# ---------- Pages ----------

@app.route("/")
def index():
    return render_template("index.html", username=session.get("username"))


@app.route("/events")
def events():
    all_events = Event.query.all()
    return render_template("events.html", events=all_events)


@app.route("/create", methods=["GET", "POST"])
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
        return redirect("/events")
    return render_template("create_event.html")


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        text = request.form["text"]
        new_message = Message(username=session["username"], text=text)
        db.session.add(new_message)
        db.session.commit()
        return redirect("/chat")

    messages = Message.query.all()
    return render_template("chat.html", messages=messages, username=session["username"])


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
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect("/events")


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
