from flask import Flask, render_template, request, session, redirect, send_file
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from gemini_helper import get_ai_insight
from report_generator import generate_study_report

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

    cursor.execute(
        """
        SELECT topic
        FROM learning_entries
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    )

    latest = cursor.fetchone()

    latest_topic = latest["topic"] if latest else "No Entries"

    cursor.execute(
        """
        SELECT DISTINCT entry_date
        FROM learning_entries
        WHERE user_id=%s
        ORDER BY entry_date DESC
        """,
        (user_id,)
    )

    dates = cursor.fetchall()

    streak = 0
    today = date.today()

    for row in dates:

        entry_date = row["entry_date"]

        if (today - entry_date).days == streak:
            streak += 1
        else:
            break
    cursor.execute(
        """
        SELECT DAYNAME(entry_date) AS day_name, SUM(hours) AS total
        FROM learning_entries
        WHERE user_id=%s
        GROUP BY entry_date
        ORDER BY entry_date
        """,
        (user_id,)
    )

    weekly_data = cursor.fetchall()

    prompt = f"""
    You are an AI placement preparation mentor.
    
    Student data:
    Total study entries: {total_entries}
    Total study hours: {total_hours}
    Latest topic studied: {latest_topic}
    Current study streak: {streak} days
    
    Give a short study improvement suggestion in 2-3 lines.
    Keep it simple and motivating.
    """
    
    try:
        ai_insight = get_ai_insight(prompt)
    except:
        ai_insight = "AI insight is currently unavailable. Keep tracking your study progress regularly."    

    badges = []

    if total_entries >= 1:
        badges.append("🥉 First Entry")

    if total_hours >= 5:
        badges.append("🥈 5 Study Hours")

    if total_hours >= 20:
        badges.append("🥇 20 Study Hours")

    if streak >= 3:
        badges.append("🔥 Consistent Learner")

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_entries=total_entries,
        total_hours=total_hours,
        latest_topic=latest_topic,
        streak=streak,
        weekly_data=weekly_data,
        ai_insight=ai_insight,
        badges=badges
    )


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

@app.route("/delete-entry/<int:id>")
def delete_entry(id):

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM learning_entries WHERE id=%s AND user_id=%s",
        (id, user_id)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/learning")

@app.route("/edit-entry/<int:id>", methods=["GET", "POST"])
def edit_entry(id):

    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":

        topic = request.form["topic"]
        hours = request.form["hours"]
        category = request.form["category"]
        entry_date = request.form["entry_date"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE learning_entries
            SET topic=%s, hours=%s, category=%s, entry_date=%s
            WHERE id=%s
            """,
            (topic, hours, category, entry_date, id)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/learning")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM learning_entries WHERE id=%s",
        (id,)
    )

    entry = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("edit_entry.html", entry=entry)


@app.route("/download-report")
def download_report():

    if "user_id" not in session:
        return redirect("/")

    user_name = session["user_name"]
    filename = "trackify_report.pdf"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    user_id = session["user_id"]

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

    cursor.execute(
        "SELECT topic FROM learning_entries WHERE user_id=%s ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    latest = cursor.fetchone()
    latest_topic = latest["topic"] if latest else "No Entries"

    streak = 0
    ai_insight = "Keep tracking your preparation regularly and focus on weak topics."

    cursor.close()
    conn.close()

    generate_study_report(
        filename,
        user_name,
        total_entries,
        total_hours,
        latest_topic,
        streak,
        ai_insight
    )

    return send_file(filename, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



if __name__ == "__main__":
    app.run(debug=True)