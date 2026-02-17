import bcrypt
from flask import Flask, render_template, request, redirect, session, jsonify

import sqlite3
import pickle


app = Flask(__name__)
app.secret_key = "super_secret_key"

spam_numbers = [
    "9999999999",
    "8888888888",
    "7777777777"
]

def check_number(number):

    # Remove spaces
    number = number.strip()

    # Known spam numbers
    spam_numbers = ["9999999999", "8888888888", "7777777777"]

    # International numbers
    if number.startswith("+"):
        return "🌍 International Number Detected"

    # Company / Service Numbers (starts with 1)
    elif number.startswith("1") and len(number) >= 8:
        return "🏢 Company / Service Number"

    # Known spam numbers
    elif number in spam_numbers:
        return "🚨 Spam Number"

    # Invalid length
    elif not number.isdigit():
        return "❌ Invalid Number"

    elif len(number) != 10:
        return "⚠️ Suspicious Number Length"

    # Repeated digits
    elif number.count(number[0]) == len(number):
        return "⚠️ Suspicious Pattern Number"

    else:
        return "✅ Safe Number"


# Load model
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

@app.route("/predict_api", methods=["POST"])
def predict_api():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    message = data["message"]

    transformed = vectorizer.transform([message])
    prediction = model.predict(transformed)[0]
    prob = model.predict_proba(transformed)
    confidence = round(max(prob[0]) * 100, 2)

    if prediction == 1:
        result = f"Spam ({confidence}%)"
    else:
        result = f"Safe ({confidence}%)"

    return jsonify({"result": result})


spam_numbers = ["9999999999", "8888888888"]


@app.route("/")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register_user():

    username = request.form["username"]
    password = request.form["password"]

    # 🔐 HASH THE PASSWORD
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users(username,password) VALUES(?,?)",
        (username, hashed_password)
    )

    conn.commit()
    conn.close()

    return redirect("/")




@app.route("/login_user", methods=["POST"])
def login_user():

    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = cur.fetchone()
    conn.close()

    if user:
        stored_password = user[2]

        if bcrypt.checkpw(
            password.encode("utf-8"),
            stored_password
        ):
            session["user"] = username
            return redirect("/dashboard")

    return "Invalid Login"





@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT result FROM history WHERE username=? ORDER BY id DESC LIMIT 1",
        (session["user"],)
    )
    last = cur.fetchone()

    result = last[0] if last else None

    cur.execute(
        "SELECT COUNT(*) FROM history WHERE username=?",
        (session["user"],)
    )
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM history WHERE username=? AND result LIKE '%Spam%'",
        (session["user"],)
    )
    spam = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM history WHERE username=? AND result LIKE '%Safe%'",
        (session["user"],)
    )
    safe = cur.fetchone()[0]
    cur.execute(
    "SELECT message, result FROM history WHERE username=? ORDER BY id DESC",
    (session["user"],)
)
    history_data = cur.fetchall()

    
    conn.close()

    return render_template(
    "dashboard.html",
    user=session["user"],
    total=total,
    spam=spam,
    safe=safe,
    result=result,
    history_data=history_data
)




@app.route("/predict_message", methods=["POST"])
def predict_message():

    if "user" not in session:
        return redirect("/")

    message = request.form.get("message", "").strip()

    if not message:
        result = "⚠️ Please enter a message"
    else:
        data = vectorizer.transform([message])
        prediction = model.predict(data)
        prob = model.predict_proba(data)
        confidence = round(max(prob[0]) * 100, 2)

        if prediction[0] == 1:
            result = f"🚨 Spam Message ({confidence}% confidence)"
        else:
            result = f"✅ Safe Message ({confidence}% confidence)"

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO history(username, message, result) VALUES (?, ?, ?)",
            (session["user"], message, result)
        )

        conn.commit()
        conn.close()

    return redirect("/dashboard")



@app.route("/check_number", methods=["POST"])
def check_number_route():

    if "user" not in session:
        return redirect("/")

    number = request.form.get("number", "").strip()

    if not number:
        result = "⚠️ Please enter a number"
    else:
        result = check_number(number)

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO history(username, message, result) VALUES (?, ?, ?)",
            (session["user"], number, result)
        )

        conn.commit()
        conn.close()

    return redirect("/dashboard")
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/clear_history", methods=["POST"])
def clear_history():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM history WHERE username=?",
        (session["user"],)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")




if __name__ == "__main__":
    app.run()

