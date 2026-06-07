from flask import Flask, render_template, request, session, redirect, send_file
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from gemini_helper import get_ai_insight
from report_generator import generate_study_report
from ai_report_helper import generate_weekly_report


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

    cursor.execute(
        """
        SELECT COUNT(*) AS total_problems
        FROM coding_entries
        WHERE user_id=%s
        """,
        (user_id,)
    )

    total_problems = cursor.fetchone()["total_problems"]

    cursor.execute(
        """
        SELECT COUNT(*) AS easy_count
        FROM coding_entries
        WHERE user_id=%s AND difficulty='Easy'
        """,
        (user_id,)
    )

    easy_count = cursor.fetchone()["easy_count"]

    cursor.execute(
        """
        SELECT COUNT(*) AS medium_count
        FROM coding_entries
        WHERE user_id=%s AND difficulty='Medium'
        """,
        (user_id,)
    )

    medium_count = cursor.fetchone()["medium_count"]

    cursor.execute(
        """
        SELECT COUNT(*) AS hard_count
        FROM coding_entries
        WHERE user_id=%s AND difficulty='Hard'
        """,
        (user_id,)
    )

    hard_count = cursor.fetchone()["hard_count"]

    cursor.execute("""
    SELECT difficulty, COUNT(*) AS count
    FROM coding_entries
    WHERE user_id=%s
    GROUP BY difficulty
    """, (user_id,))
    
    difficulty_data = cursor.fetchall()

    cursor.execute("""
    SELECT
        DAYNAME(entry_date) AS day_name,
        SUM(hours) AS total_hours
    FROM learning_entries
    WHERE user_id=%s
    GROUP BY entry_date
    ORDER BY entry_date
    """, (user_id,))

    weekly_study_data = cursor.fetchall()


    problem_progress = min(total_problems, 10)
    study_progress = min(total_hours, 25)
    streak_progress = min(streak, 7)

    cursor.execute(
        "SELECT * FROM leetcode_stats WHERE user_id=%s ORDER BY id DESC LIMIT 1",
        (user_id,)
    )

    leetcode_stats = cursor.fetchone()

    if not leetcode_stats:
        leetcode_stats = {
            "total_solved": 0,
            "easy_solved": 0,
            "medium_solved": 0,
            "hard_solved": 0
        }

    cursor.execute(
        "SELECT weekly_goal FROM study_goals WHERE user_id=%s ORDER BY id DESC LIMIT 1",
        (user_id,)
    )

    goal_data = cursor.fetchone()

    weekly_goal = goal_data["weekly_goal"] if goal_data else 0

    goal_percentage = 0

    if weekly_goal > 0:
        goal_percentage = round((total_hours / weekly_goal) * 100, 1)

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
        badges=badges,
        total_problems=total_problems,
        easy_count=easy_count,
        medium_count=medium_count,
        hard_count=hard_count,
        difficulty_data=difficulty_data,
        weekly_study_data=weekly_study_data,
        problem_progress=problem_progress,
        study_progress=study_progress,
        streak_progress=streak_progress,
        leetcode_stats=leetcode_stats
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

    cursor.execute(
        "SELECT COUNT(*) AS total_problems FROM coding_entries WHERE user_id=%s",
        (user_id,)
    )
    total_problems = cursor.fetchone()["total_problems"]

    cursor.execute(
            "SELECT * FROM leetcode_stats WHERE user_id=%s ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
    leetcode = cursor.fetchone()

    if leetcode:
        leetcode_total = leetcode["total_solved"]
        leetcode_easy = leetcode["easy_solved"]
        leetcode_medium = leetcode["medium_solved"]
        leetcode_hard = leetcode["hard_solved"]
    else:
        leetcode_total = 0
        leetcode_easy = 0
        leetcode_medium = 0
        leetcode_hard = 0

    cursor.close()
    conn.close()

    generate_study_report(
        filename,
        user_name,
        total_entries,
        total_hours,
        latest_topic,
        streak,
        ai_insight,
        total_problems,
        leetcode_total,
        leetcode_easy,
        leetcode_medium,
        leetcode_hard
    )

    return send_file(filename, as_attachment=True)


@app.route("/coding", methods=["GET", "POST"])
def coding():

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    if request.method == "POST":
        platform = request.form["platform"]
        problem_name = request.form["problem_name"]
        difficulty = request.form["difficulty"]
        topic = request.form["topic"]
        status = request.form["status"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO coding_entries(user_id, platform, problem_name, difficulty, topic, status)
            VALUES(%s, %s, %s, %s, %s, %s)
            """,
            (user_id, platform, problem_name, difficulty, topic, status)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/coding")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM coding_entries WHERE user_id=%s ORDER BY id DESC",
        (user_id,)
    )

    coding_entries = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("coding.html", coding_entries=coding_entries)

@app.route("/leetcode", methods=["GET", "POST"])
def leetcode():

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    if request.method == "POST":
        total_solved = request.form["total_solved"]
        easy_solved = request.form["easy_solved"]
        medium_solved = request.form["medium_solved"]
        hard_solved = request.form["hard_solved"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM leetcode_stats WHERE user_id=%s",
            (user_id,)
        )

        cursor.execute(
            """
            INSERT INTO leetcode_stats(user_id, total_solved, easy_solved, medium_solved, hard_solved)
            VALUES(%s, %s, %s, %s, %s)
            """,
            (user_id, total_solved, easy_solved, medium_solved, hard_solved)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/dashboard")

    return render_template("leetcode.html")


@app.route("/ai-weekly-report")
def ai_weekly_report():

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT SUM(hours) AS total_hours FROM learning_entries WHERE user_id=%s",
        (user_id,)
    )
    result = cursor.fetchone()
    total_hours = result["total_hours"] if result["total_hours"] else 0

    cursor.execute(
        "SELECT COUNT(*) AS total_problems FROM coding_entries WHERE user_id=%s",
        (user_id,)
    )
    total_problems = cursor.fetchone()["total_problems"]

    cursor.execute(
        "SELECT * FROM leetcode_stats WHERE user_id=%s ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    leetcode_stats = cursor.fetchone()

    leetcode_total = leetcode_stats["total_solved"] if leetcode_stats else 0

    cursor.close()
    conn.close()

    streak = 0

    report = generate_weekly_report(
        total_hours,
        total_problems,
        streak,
        leetcode_total
    )

    return render_template("ai_weekly_report.html", report=report)


@app.route("/goals", methods=["GET", "POST"])
def goals():

    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    if request.method == "POST":
        weekly_goal = request.form["weekly_goal"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM study_goals WHERE user_id=%s",
            (user_id,)
        )

        cursor.execute(
            "INSERT INTO study_goals(user_id, weekly_goal) VALUES(%s, %s)",
            (user_id, weekly_goal)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/dashboard")

    return render_template("goals.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



if __name__ == "__main__":
    app.run(debug=True)