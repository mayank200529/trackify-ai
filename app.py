from flask import Flask, render_template, request, session, redirect
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "trackify_secret"

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect("/dashboard")
        else:
            return "Invalid email or password"

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                (name, email, hashed_password)
            )

            conn.commit()

            cursor.close()
            conn.close()
            return "User Registered Successfully!"
        except:

            cursor.close()
            conn.close()
            return "Email already exists!"

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT COUNT(*) AS total_entries FROM learning_entries WHERE user_id=%s",
        (user_id,)
    )
    total_entries = cursor.fetchone()["total_entries"]

    cursor.execute(
        "SELECT SUM(hours) AS total_hours FROM learning_entries WHERE user_id=%s",
        (user_id,)
    )

    result = cursor.fetchone()
    total_hours = result["total_hours"] if result["total_hours"] else 0

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_entries=total_entries,
        total_hours=total_hours
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/learning", methods=["GET", "POST"])
def learning():

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    if request.method == "POST":
        topic = request.form["topic"]
        hours = request.form["hours"]
        category = request.form["category"]
        entry_date = request.form["entry_date"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO learning_entries(user_id, topic, hours, category, entry_date) VALUES(%s,%s,%s,%s,%s)",
            (user_id, topic, hours, category, entry_date)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/learning")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM learning_entries WHERE user_id=%s ORDER BY entry_date DESC",
        (user_id,)
    )

    entries = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("learning.html", entries=entries)

if __name__ == "__main__":
    app.run(debug=True)