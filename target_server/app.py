from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = "super_secret_key_change_me"

# ---------- Database Setup (Vulnerable SQLite) ----------
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin', 'admin123')")
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('john', 'password')")
    conn.commit()
    conn.close()

init_db()

# ---------- Helper Functions ----------
def generate_captcha():
    num1 = random.randint(10, 30)
    num2 = random.randint(1, 15)
    session['captcha_answer'] = num1 + num2
    return f"{num1} + {num2}"

# ---------- Routes ----------
@app.route('/')
def index():
    # 1. Anti-Bot Check (Navigator.webdriver check happens on client side via JS)
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # 2. Geo-Fencing Check
    x_forwarded = request.headers.get('X-Forwarded-For')
    if x_forwarded != '1.1.1.1':
        return "Access Denied: Invalid Geo Location", 403

    if request.method == 'GET':
        captcha_question = generate_captcha()
        return render_template('login.html', captcha=captcha_question)
    
    elif request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # 3. Captcha Validation
        user_answer = data.get('captcha')
        if not user_answer or int(user_answer) != session.get('captcha_answer'):
            return jsonify({"error": "Invalid Captcha"}), 400

        # 4. SQL Injection Vulnerable Login (Union/OR bypass possible)
        username = data.get('username')
        password = data.get('password')
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # !!! VULNERABLE QUERY - DO NOT USE IN PRODUCTION !!!
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        print(f"[!] Executing SQL: {query}")
        
        try:
            c.execute(query)
            user = c.fetchone()
        except Exception as e:
            user = None
            print(f"SQL Error: {e}")
        conn.close()

        if user:
            session['logged_in'] = True
            session['username'] = username
            return jsonify({"redirect": "/otp"}), 200
        else:
            return jsonify({"error": "Invalid Credentials"}), 401

@app.route('/otp', methods=['GET', 'POST'])
def otp():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('otp.html')
    
    elif request.method == 'POST':
        data = request.get_json()
        otp_code = data.get('otp')
        debug_flag = data.get('debug') # 5. Response Manipulation Vulnerability
        
        # Vulnerability 1: Blank OTP Bypass
        if otp_code == "" or otp_code is None:
            session['auth_success'] = True
            return jsonify({"redirect": "/dashboard"}), 200
        
        # Vulnerability 2: Debug Flag Bypass
        if debug_flag == "bypass_otp_please":
            session['auth_success'] = True
            return jsonify({"redirect": "/dashboard"}), 200
            
        # Normal OTP Logic (Hardcoded 123456 for demo)
        if otp_code == "123456":
            session['auth_success'] = True
            return jsonify({"redirect": "/dashboard"}), 200
        else:
            return jsonify({"error": "Invalid OTP"}), 400

@app.route('/dashboard')
def dashboard():
    if session.get('auth_success'):
        return render_template('dashboard.html', username=session.get('username'))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)