from flask import Flask, request, redirect, session
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "morph_scada_secret"

DB = "temperature.db"

USERS = {
    "admin": "1234",
    "operator": "1111"
}

# ---------- СТАТУС ----------
def get_status(temp):
    if temp is None:
        return ""
    if 16 <= temp <= 26:
        return "🟢 НОРМА"
    elif 27 <= temp <= 31:
        return "🟡 ВЫСОКАЯ"
    elif 32 <= temp <= 40:
        return "🔴 АВАРИЙНАЯ"
    else:
        return "⚪ НЕТ ДАННЫХ"

# ---------- DB ----------
def get_db():
    return sqlite3.connect(DB)

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect("/")

        return "<h2 style='color:red;text-align:center;'>НЕВЕРНЫЙ ЛОГИН</h2>"

    return """
    <html>
    <body style="background:#0b0f1a;color:white;text-align:center;padding-top:100px;">
        <h2>SCADA LOGIN</h2>
        <form method="POST">
            <input name="username" placeholder="login"><br><br>
            <input name="password" type="password" placeholder="password"><br><br>
            <button>Войти</button>
        </form>
    </body>
    </html>
    """

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------- MAIN ----------
@app.route("/")
def index():

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS temperatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            tsh1 REAL,
            tsh2 REAL,
            tsh6 REAL,
            tsh7 REAL
        )
    """)

    cursor.execute("""
        SELECT * FROM temperatures
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cursor.fetchall()
    conn.close()

    # ⚠️ ВАЖНО: JSON FIX (график теперь работает)
    labels = json.dumps([r[1] for r in rows][::-1])
    tsh1 = json.dumps([r[2] for r in rows][::-1])
    tsh2 = json.dumps([r[3] for r in rows][::-1])
    tsh6 = json.dumps([r[4] for r in rows][::-1])
    tsh7 = json.dumps([r[5] for r in rows][::-1])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>RAILCAST SCADA</title>

        <meta http-equiv="refresh" content="600">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <style>
            body {{
                margin:0;
                font-family:Arial;
                background:#0b0f1a;
                color:white;
            }}

            .topbar {{
                display:flex;
                justify-content:space-between;
                padding:12px 20px;
                background:#111827;
                border-bottom:2px solid #00e5ff;
            }}

            .user {{
                color:#00ffcc;
            }}

            .logout {{
                color:red;
                text-decoration:none;
            }}

            .container {{
                padding:15px;
            }}

            .chart-box {{
                background:#111827;
                border-radius:12px;
                height:300px;
                padding:10px;
            }}

            canvas {{
                width:100% !important;
                height:100% !important;
            }}

            table {{
                width:100%;
                margin-top:15px;
                border-collapse:collapse;
                background:#111827;
            }}

            th, td {{
                border:1px solid #2d3748;
                padding:6px;
                text-align:center;
            }}

            th {{
                background:#0f172a;
                color:#00e5ff;
            }}
        </style>
    </head>

    <body>

        <div class="topbar">
            <h3>📊Мониторинг температуры</h3>
            <div>
                👤 <span class="user">{session['user']}</span>
                <a class="logout" href="/logout">ВЫЙТИ</a>
            </div>
        </div>

        <div class="container">

            <div class="chart-box">
                <canvas id="chart"></canvas>
            </div>

            <table>
                <tr>
                    <th>ID</th>
                    <th>Дата</th>

                    <th>ТШ1</th><th>Статус</th>
                    <th>ТШ2</th><th>Статус</th>
                    <th>ТШ6</th><th>Статус</th>
                    <th>ТШ7</th><th>Статус</th>
                </tr>
    """

    for r in rows:
        html += f"""
        <tr>
            <td>{r[0]}</td>
            <td>{r[1]}</td>

            <td>{r[2]}</td><td>{get_status(r[2])}</td>
            <td>{r[3]}</td><td>{get_status(r[3])}</td>
            <td>{r[4]}</td><td>{get_status(r[4])}</td>
            <td>{r[5]}</td><td>{get_status(r[5])}</td>
        </tr>
        """

    html += f"""
            </table>
        </div>

        <script>
            const ctx = document.getElementById('chart');

            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {labels},
                    datasets: [
                        {{
                            label: 'ТШ1',
                            data: {tsh1},
                            borderColor: '#00e5ff',
                            tension: 0.3
                        }},
                        {{
                            label: 'ТШ2',
                            data: {tsh2},
                            borderColor: '#ff9800',
                            tension: 0.3
                        }},
                        {{
                            label: 'ТШ6',
                            data: {tsh6},
                            borderColor: '#00ff66',
                            tension: 0.3
                        }},
                        {{
                            label: 'ТШ7',
                            data: {tsh7},
                            borderColor: '#ff00ff',
                            tension: 0.3
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            labels: {{ color: 'white' }}
                        }}
                    }},
                    scales: {{
                        x: {{ ticks: {{ color: 'white' }} }},
                        y: {{ ticks: {{ color: 'white' }} }}
                    }}
                }}
            }});
        </script>

    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)