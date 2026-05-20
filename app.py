import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/events")
def events():
    all_events = Event.query.all()
    return render_template("events.html", events=all_events)

@app.route("/create", methods=["GET", "POST"])
def create_event():

    if request.method == "POST":

        title = request.form["title"]
        date = request.form["date"]
        time = request.form["time"]
        description = request.form["description"]

        new_event = Event(
            title=title,
            date=date,
            time=time,
            description=description
        )

        db.session.add(new_event)
        db.session.commit()

        return redirect("/events")

    return render_template("create_event.html")

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
