from flask import Flask, render_template, request
from db import get_db_connection
from werkzeug.security import generate_password_hash

app = Flask(__name__)

@app.route("/")
def home():
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

        cursor.execute(
            "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
            (name, email, hashed_password)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return "User Registered Successfully!"

    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)