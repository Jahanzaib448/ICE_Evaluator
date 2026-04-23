# 🔐 Intelligent Credential Evaluator (ICE) Prototype

## 📋 Project Overview
A penetration testing automation prototype that demonstrates bypassing multiple security layers of a target web application.

**Task Duration:** 48 Hours  
**Tech Stack:** Python, Flask, Playwright

---

## 🏗️ Project Structure

    ICE-Project/
    │
    ├── target_server/ # Part 1: Vulnerable Web Application
    │ ├── app.py # Flask backend with intentional vulnerabilities
    │ ├── requirements.txt # Python dependencies
    │ └── templates/ # HTML frontend
    │ ├── login.html # Login page with anti-bot check
    │ ├── otp.html # OTP verification page
    │ └── dashboard.html # Success page
    │
    ├── ice_evaluator/ # Part 2: Automated Attack Script
    │ ├── ice_attacker.py # Main attack script (Playwright)
    │ ├── creds.txt # Test credentials file
    │ ├── requirements.txt # Python dependencies
    │ └── results.json # Automated output report
    │
    └── README.md # This file