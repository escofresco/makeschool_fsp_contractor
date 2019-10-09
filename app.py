from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)
app.config["ENV"] = "development"
client = MongoClient()

users_collection = client.users


@app.route("/")
def home():
    return render_template("home.html", title="home")

@app.route("/login")
def login():
    return render_template("login.html", title="login")

@app.route("/signup")
def signup():
    return render_template("signup.html", title="signup")

if __name__ == "__main__":
    app.run(debug=True)
