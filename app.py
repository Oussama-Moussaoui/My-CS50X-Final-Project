import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///notes.db")


@app.route("/")
@login_required
def index():

    # Get user notes
    index = db.execute("SELECT * FROM notes WHERE user_id = :user_id", user_id=session["user_id"])

    # Reverse list to get recent notes first
    index.reverse()

    return render_template("index.html", index=index)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Get user's new note
        note = request.form.get("note")

        # Ensure note was submitted
        if note == "":
            return apology("You wrote nothing!")

        db.execute("INSERT INTO 'notes' ('user_id', 'note') VALUES (:user_id, :note)", user_id=session["user_id"], note=note)

        # Redirect user to index
        flash("Added!")
        return redirect('/')

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure username was submitted
        if not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure confirmation was submitted
        if not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        # Ensure password confirmation is correct
        if not request.form.get("confirmation") == request.form.get("password"):
            return apology("paswords don't match")

        # Ensure username does not already exist
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        if len(rows) != 0:
            return apology("Username already exists, please change it.")

        # Register new user
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :password_hash)",
                   username=request.form.get("username"), password_hash=generate_password_hash(request.form.get("password")))

        # Log user in
        user_id = db.execute("SELECT id FROM users WHERE username = :username", username=request.form.get("username"))
        session["user_id"] = user_id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

#This route is for deleting note
@app.route('/delete/<note>/<datetime>', methods = ['GET', 'POST'])
def delete(note, datetime):
    # Delete note
    db.execute("DELETE FROM notes WHERE user_id == :user_id AND note == :note AND datetime == :datetime",
               user_id=session["user_id"], note=note, datetime=datetime)

    # Redirect url for index
    flash("Note Deleted Successfully")
    return redirect("/")

# This rout is for editing note
@app.route('/edit/<note>/<datetime>', methods = ['GET', 'POST'])
def update(note, datetime):

    if request.method == 'POST':

        # Get updated note
        new_note = request.form.get("new_note")

        # Update note
        db.execute("UPDATE notes SET note = :new_note WHERE user_id = :user_id AND note = :note AND datetime = :datetime",
                   new_note=new_note, user_id=session["user_id"], note=note, datetime=datetime)

        # Redirect user to index
        flash("Note Updated Successfully")
        return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)