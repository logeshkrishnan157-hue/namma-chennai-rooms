from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import random
import requests

app = Flask(__name__)
app.secret_key = "namma_chennai_rooms_super_secret_key_2026"

# Telegram Bot Configurations
TELEGRAM_BOT_TOKEN = "8874820853:AAGbZYqZ2Td8olEW6Cw1DJvcx6OTJCD4HgE"
TELEGRAM_CHAT_ID = "6269474117"

# Cashfree Test Configurations
CASHFREE_APP_ID = "TEST11266601795c7fce6a401c75e9d810666211"
CASHFREE_SECRET_KEY = "cfsk_ma_test_ea1f7c93499c2604d0376ff7e0343d7_OceO1973"

# Google Sheets Setup
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_google_sheet():
    try:
        creds_dict = None
        if os.path.exists("apt.json.json"):
            with open("apt.json.json", "r") as f:
                creds_dict = json.load(f)
                
        if creds_dict:
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
            client = gspread.authorize(creds)
            sheet = client.open("Namma Chennai Rooms Sheet API").sheet1
            return sheet
    except Exception as e:
        print("Google Sheet Connection Error:", e)
    return None

# --- HTML TEMPLATE (COMBINED IN SINGLE FILE) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Namma Chennai Rooms</title>
    <script src="https://sdk.cashfree.com/js/v3/cashfree.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h2 { color: #333; text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #666; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { background: #ff4757; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #e84118; }
        #whatsapp-section { display: none; margin-top: 20px; padding: 15px; background: #e1fedb; border: 1px solid #2ecc71; border-radius: 5px; text-align: center; }
        .whatsapp-link { color: #27ae60; font-weight: bold; font-size: 18px; text-decoration: none; display: inline-block; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Namma Chennai Rooms</h2>
        <div id="booking-form">
            <div class="form-group">
                <label>Name</label>
                <input type="text" id="name" placeholder="Enter your name" required>
            </div>
            <div class="form-group">
                <label>Phone Number</label>
                <input type="text" id="phone" placeholder="Enter phone number" required>
            </div>
            <div class="form-group">
                <label>Room Type</label>
                <select id="room_type">
                    <option value="Standard AC Room - ₹50">Standard AC Room - ₹50</option>
                    <option value="Deluxe Suite - ₹50">Deluxe Suite - ₹50</option>
                </select>
            </div>
            <div class="form-group">
                <label>Date</label>
                <input type="date" id="date" required>
            </div>
            <button onclick="startPayment()">Pay & Book via UPI</button>
        </div>

        <div id="whatsapp-section">
            <h3 id="status-message" style="color: #27ae60; margin: 0 0 10px 0;"></h3>
            <p>Booking Confirmed! Contact Admin on WhatsApp:</p>
            <a class="whatsapp-link" href="https://wa.me/919999999999?text=Hi%2C%20I%20have%20completed%20my%20payment%20for%20room%20booking." target="_blank">Chat on WhatsApp 💬</a>
        </div>
    </div>

    <script>
        const cashfree = Cashfree({ mode: "sandbox" });

        async function startPayment() {
            const name = document.getElementById("name").value;
            const phone = document.getElementById("phone").value;
            const room_type = document.getElementById("room_type").value;
            const date = document.getElementById("date").value;

            if(!name || !phone || !date) {
                alert("Please fill all fields!");
                return;
            }

            try {
                // 1. Submit lead to Google Sheet first
                let formData = new FormData();
                formData.append('name', name);
                formData.append('phone', phone);
                formData.append('room_type', room_type);
                formData.append('date', date);

                await fetch('/submit_lead', { method: 'POST', body: formData });

                // 2. Create Cashfree Payment Order (UPI Only)
                const response = await fetch('/create-payment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ room_type: room_type, amount: 50.00 })
                });
                const data = await response.json();

                if (data.payment_session_id) {
                    let checkoutOptions = {
                        paymentSessionId: data.payment_session_id,
                        redirectTarget: "_modal",
                        allowedPaymentModes: ["upi"] // UPI Apps Only
                    };

                    cashfree.checkout(checkoutOptions).then(function(result) {
                        if (result.error) {
                            alert("Payment Failed or Cancelled: " + result.error.message);
                        }
                        if (result.paymentDetails) {
                            // 3. SUCCESS: Hide Form & Show WhatsApp Info Only Now
                            document.getElementById("booking-form").style.display = "none";
                            document.getElementById("whatsapp-section").style.display = "block";
                            document.getElementById("status-message").innerText = "Payment Successful!";
                        }
                    });
                } else {
                    alert("Error creating payment session");
                }
            } catch (err) {
                console.error(err);
                alert("An error occurred.");
            }
        }
    </script>
</body>
</html>
"""

# --- ADMIN LOGIN HTML TEMPLATE ---
ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Admin Login</title></head>
<body style="font-family:Arial; display:flex; justify-content:center; align-items:center; height:100vh; background:#222; color:white;">
    <div style="background:#333; padding:30px; border-radius:8px; width:300px; text-align:center;">
        <h2>Admin Login</h2>
        {% if error %}<p style="color:#ff4757;">{{ error }}</p>{% endif %}
        <form method="POST">
            <button type="submit" style="padding:10px; width:100%; background:#2ed573; color:white; border:none; border-radius:4px; font-size:16px; cursor:pointer;">Send OTP to Telegram</button>
        </form>
    </div>
</body>
</html>
"""

ADMIN_VERIFY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Verify OTP</title></head>
<body style="font-family:Arial; display:flex; justify-content:center; align-items:center; height:100vh; background:#222; color:white;">
    <div style="background:#333; padding:30px; border-radius:8px; width:300px; text-align:center;">
        <h2>Enter Telegram OTP</h2>
        {% if error %}<p style="color:#ff4757;">{{ error }}</p>{% endif %}
        <form method="POST">
            <input type="text" name="otp" placeholder="Enter 4-digit OTP" required style="padding:10px; width:90%; margin-bottom:15px; border-radius:4px; border:none; text-align:center; font-size:18px;"><br>
            <button type="submit" style="padding:10px; width:100%; background:#2ed573; color:white; border:none; border-radius:4px; font-size:16px; cursor:pointer;">Verify OTP</button>
        </form>
    </div>
</body>
</html>
"""

ADMIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Admin Dashboard</title></head>
<body style="font-family:Arial; padding:40px; background:#f4f7f6;">
    <div style="max-width:600px; margin:0 auto; background:white; padding:30px; border-radius:8px; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
        <h2>Welcome Admin! 🎉</h2>
        <p>Your Telegram OTP Authentication was successful. Leads are automatically synced to Google Sheets.</p>
        <a href="/admin/logout" style="color:red; text-decoration:none; font-weight:bold;">Logout 🚪</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# --- LEAD SUBMISSION ROUTE ---
@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    try:
        name = request.form.get('name')
        phone = request.form.get('phone')
        room_type = request.form.get('room_type')
        date = request.form.get('date', '')
        
        sheet = get_google_sheet()
        if sheet:
            sheet.append_row([name, phone, room_type, date])
            return jsonify({"status": "success", "message": "Lead saved successfully!"})
        else:
            return jsonify({"status": "error", "message": "Database connection failed."}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- CASHFREE PAYMENT ORDER CREATION ---
@app.route('/create-payment', methods=['POST'])
def create_payment():
    try:
        data = request.get_json() or request.form
        room_type = data.get('room_type', 'Standard Room')
        amount = float(data.get('amount', 50.00))
        
        url = "https://sandbox.cashfree.com/pg/orders"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-client-id": CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET_KEY,
            "x-api-version": "2022-09-01"
        }
        payload = {
            "order_amount": amount,
            "order_currency": "INR",
            "customer_details": {
                "customer_id": "user_chennai_01",
                "customer_phone": "9999999999",
                "customer_email": "user@nammachennairooms.com"
            },
            "order_meta": {
                "return_url": "https://namma-chennai-rooms.onrender.com/"
            },
            "order_note": f"Booking for {room_type} - Namma Chennai Rooms"
        }
        response = requests.post(url, json=payload, headers=headers)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- TELEGRAM OTP ADMIN LOGIN ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        otp = str(random.randint(1000, 9999))
        session['generated_otp'] = otp
        
        message = f"🔐 *Namma Chennai Rooms* Admin Login OTP: `{otp}`\nDo not share this with anyone!"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return redirect(url_for('admin_verify'))
            else:
                return render_template_string(ADMIN_LOGIN_TEMPLATE, error="Failed to send OTP. Check Telegram Bot Token & Chat ID.")
        except Exception as e:
            return render_template_string(ADMIN_LOGIN_TEMPLATE, error=f"Error: {str(e)}")
            
    return render_template_string(ADMIN_LOGIN_TEMPLATE)

@app.route('/admin/verify', methods=['GET', 'POST'])
def admin_verify():
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        if user_otp and user_otp == session.get('generated_otp'):
            session['admin_logged_in'] = True
            session.pop('generated_otp', None)
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template_string(ADMIN_VERIFY_TEMPLATE, error="Invalid OTP! Try again.")
    return render_template_string(ADMIN_VERIFY_TEMPLATE)

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
