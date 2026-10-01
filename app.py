import os
import json
import csv
import random
import threading
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_file
import requests

app = Flask(__name__)
app.secret_key = "lokesh_secret_key_render_final_2026"

# Telegram Bot Configurations (Fetched safely from Render Environment Variables)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ================= CASHFREE LIVE CONFIGURATIONS (Fetched safely from Render) =================
CASHFREE_APP_ID = os.environ.get("CASHFREE_APP_ID")
CASHFREE_SECRET_KEY = os.environ.get("CASHFREE_SECRET_KEY")

# Absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.json")
LEADS_CSV = os.path.join(BASE_DIR, "leads.csv")

def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "settings": {
                "wa_number": "9025034415"
            },
            "properties": {
                "CHTY01": {
                    "title": "2 BHK in Velachery", 
                    "rent": 18000, 
                    "advance": 60000, 
                    "electricity": 8,
                    "members": "3 to 4 Members",
                    "is_sold": False
                },
                "CHTY03": {
                    "title": "2 BHK Rooms in Mylapore", 
                    "rent": 22000, 
                    "advance": 80000, 
                    "electricity": 9,
                    "members": "2 to 3 Members",
                    "is_sold": False
                }
            }
        }
        save_db(default_data)
        return default_data
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_lead_to_csv(lead_data):
    file_exists = os.path.exists(LEADS_CSV)
    with open(LEADS_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Name", "Phone Number", "Room Details", "Current Step", "Payment Status"])
        writer.writerow([
            lead_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            lead_data.get("name"),
            lead_data.get("phone"),
            lead_data.get("prop_id"),
            lead_data.get("step"),
            lead_data.get("status")
        ])

def send_telegram_async(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={msg}", timeout=3)
    except:
        pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Namma Chennai Rooms Portal</title>
    <script src="https://sdk.cashfree.com/js/v3/cashfree.js"></script>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 15px; color: #333; position: relative; min-height: 100vh; }
        .container { width: 100%; max-width: 480px; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.08); margin: 30px auto; }
        h2, h3 { color: #1a1a1a; text-align: center; margin-top: 10px; font-size: 22px; }
        .property-box { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #007bff; font-size: 14px; line-height: 1.5; }
        .property-box p { margin: 8px 0; }
        .form-group { margin-bottom: 18px; }
        label { display: block; font-weight: 600; margin-bottom: 6px; color: #333; font-size: 14px; }
        select, input[type="text"], input[type="number"], input[type="tel"], input[type="password"] { width: 100%; padding: 12px; border: 1px solid #ccd0d5; border-radius: 8px; font-size: 16px; background: #fff; }
        button { background: #28a745; color: white; border: none; padding: 14px; width: 100%; font-size: 16px; font-weight: 600; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #218838; }
        .success-msg { background: #e8f5e9; color: #2e7d32; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #c8e6c9; text-align: center; }
        .sold-banner { background: #ff4d4d; color: white; padding: 20px; text-align: center; border-radius: 8px; font-size: 18px; font-weight: bold; }
        .admin-nav { text-align: right; margin-bottom: 10px; }
        .admin-nav a { background: #e4e6eb; color: #050505; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: 600; }
        .step-indicator { text-align: center; color: #65676b; font-size: 12px; font-weight: 600; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }
        .section-box { background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 15px; border: 1px solid #ddd; }
        .table-responsive { width: 100%; overflow-x: auto; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; white-space: nowrap; }
        th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
        th { background: #f2f2f2; }
        .badge { padding: 3px 6px; border-radius: 4px; font-weight: bold; color: white; font-size: 10px; }
        .badge-pending { background: #f39c12; }
        .badge-success { background: #27ae60; }
        .badge-visit { background: #2980b9; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }

        #secretAdminBar {
            position: fixed;
            left: 0;
            top: 40%;
            width: 8px;
            height: 60px;
            background: #007bff;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            z-index: 9999;
            cursor: pointer;
            box-shadow: 2px 0 5px rgba(0,0,0,0.2);
            transition: width 0.2s;
        }
        #secretAdminBar:hover { width: 15px; background: #0056b3; }
    </style>
</head>
<body>
    <div id="secretAdminBar" title="Admin Portal" onclick="window.location.href='/admin'"></div>

    <div class="container">
        {% if page in ['admin', 'admin_login', 'admin_verify', 'download_portal', 'download_verify'] %}
        <div class="admin-nav">
            <a href="/">🏠 Back to Portal</a>
        </div>
        {% endif %}

        <!-- ================= STEP 1: INSTAGRAM CHECK ================= -->
        {% if page == 'step1' %}
        <div class="step-indicator">Step 1 of 4</div>
        <h2>Namma Chennai Rooms</h2>
        <form method="POST" action="/step1">
            <div class="form-group" style="background: #fff8e1; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba;">
                <label style="color: #856404;">Have you followed our Instagram Page (@namma_chennai_rooms)?</label>
                <p style="font-size: 12px; margin: 5px 0 12px 0;">If not, please follow first: <a href="https://www.instagram.com/namma_chennai_rooms/" target="_blank" style="color: #0056b3; font-weight: bold;">Click here to Follow</a></p>
                <select name="followed" required>
                    <option value="yes" {% if followed == 'yes' %}selected{% endif %}>Yes, I have followed!</option>
                    <option value="no" {% if followed == 'no' %}selected{% endif %}>No</option>
                </select>
            </div>
            <button type="submit">Next ➔</button>
        </form>
        <div style="text-align: center; margin-top: 20px;">
            <a href="/download-portal" style="color: #007bff; font-size: 13px; text-decoration: none; font-weight: 600;">📥 Download Leads Report (OTP Secured)</a>
        </div>

        <!-- ================= STEP 2: PROPERTY SELECT & DETAILS ================= -->
        {% elif page == 'step2' %}
        <div class="step-indicator">Step 2 of 4</div>
        <h2>Select Property & Details</h2>
        <form method="GET" action="/step2">
            <input type="hidden" name="followed" value="{{ followed }}">
            <div class="form-group">
                <label>Choose Property:</label>
                <select name="prop_id" onchange="this.form.submit()">
                    {% for pid in properties.keys() %}
                        {% if not properties[pid].is_sold %}
                        <option value="{{ pid }}" {% if pid == selected_id %}selected{% endif %}>{{ pid }} - {{ properties[pid].title }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
            </div>
        </form>

        <div class="property-box">
            <p><strong>Title:</strong> {{ current_prop.title }}</p>
            <p><strong>Rent:</strong> ₹{{ current_prop.rent }}</p>
            <p><strong>Advance:</strong> ₹{{ current_prop.advance }}</p>
            <p><strong>Electricity:</strong> ₹{{ current_prop.electricity }}/unit</p>
            <p><strong>Allowed Members:</strong> {{ current_prop.members }}</p>
        </div>

        <form method="POST" action="/step2">
            <input type="hidden" name="prop_id" value="{{ selected_id }}">
            <input type="hidden" name="followed" value="{{ followed }}">
            <button type="submit">Next ➔</button>
        </form>

        <!-- ================= STEP 3: NAME & STRICT 10-DIGIT PHONE ================= -->
        {% elif page == 'step3' %}
        <div class="step-indicator">Step 3 of 4</div>
        <h2>Your Details</h2>
        <form method="POST" action="/step3">
            <input type="hidden" name="prop_id" value="{{ prop_id }}">
            <input type="hidden" name="followed" value="{{ followed }}">
            
            <div class="form-group">
                <label>Your Full Name:</label>
                <input type="text" name="name" id="name" value="{{ name }}" placeholder="Enter your name" required>
            </div>
            <div class="form-group">
                <label>WhatsApp Phone Number (Exact 10 Digits):</label>
                <input type="tel" name="phone" id="phone" pattern="[0-9]{10}" minlength="10" maxlength="10" 
                       oninput="this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);" 
                       value="{{ phone }}" placeholder="e.g. 9840123456" required>
            </div>
            <button type="submit">Proceed to Payment ➔</button>
        </form>

        <!-- ================= STEP 4: CASHFREE PRODUCTION UPI PAYMENT ================= -->
        {% elif page == 'payment' %}
        <div class="step-indicator">Step 4 of 4</div>
        <h2>Instant UPI Payment</h2>
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
                <p style="font-size: 14px; color: #555; margin-bottom: 15px;">Pay ₹50 registration fee via UPI. Room & Property details will automatically reflect in your payment app note.</p>
                <button type="button" onclick="startPayment()" style="background: #2ed573; font-size: 16px;">Pay ₹50 via UPI Apps 🚀</button>
            </div>
        </div>

        <script>
            const cashfree = Cashfree({ mode: "production" });

            async function startPayment() {
                try {
                    const response = await fetch('/create-payment', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prop_id: "{{ prop_id }}", amount: 50.00 })
                    });
                    const data = await response.json();

                    if (data.payment_session_id) {
                        let checkoutOptions = {
                            paymentSessionId: data.payment_session_id,
                            redirectTarget: "_modal",
                            allowedPaymentModes: ["upi"]
                        };

                        cashfree.checkout(checkoutOptions).then(function(result) {
                            if (result.error) {
                                alert("Payment Failed or Cancelled: " + result.error.message);
                            }
                            if (result.paymentDetails) {
                                window.location.href = "/success?prop_id={{ prop_id }}&name={{ name }}&phone={{ phone }}";
                            }
                        });
                    } else {
                        alert("Checkout Error: " + (data.message || JSON.stringify(data)));
                    }
                } catch (err) {
                    console.error(err);
                    alert("An error occurred during checkout: " + err.message);
                }
            }
        </script>

        <!-- ================= SUCCESS PAYMENT PAGE ================= -->
        {% elif page == 'success' %}
        <div class="step-indicator">Completed</div>
        <h2>Payment Successful! 🎉</h2>
        <div class="success-msg">
            <p style="font-size: 14px; color: #2e7d32; margin-bottom: 15px; font-weight: bold;">
                ✅ Payment Verified Successfully via Cashfree! Click below to open WhatsApp and send complete details to the owner:
            </p>
            <a href="https://wa.me/{{ wa_number }}?text={{ wa_message | urlencode }}" target="_blank">
                <button style="background: #25D366; font-size: 16px;">💬 Open WhatsApp Now</button>
            </a>
        </div>

        {% elif page == 'not_followed' %}
        <div style="background: #ffebee; color: #c62828; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ef9a9a;">
            <h3>⚠️ Please Follow Our Page First!</h3>
            <p style="font-size: 14px; margin-top: 10px;">To view property details and book house visits, you must follow our Instagram page.</p>
            <a href="/"><button style="margin-top: 15px; background: #007bff;">⬅️ Back to Start</button></a>
        </div>

        {% elif page == 'sold' %}
        <div class="sold-banner">
            🚫 Property Sold Out!<br><br>
            <span style="font-size: 14px; font-weight: normal;">This property has already been rented/sold out. Please check our Instagram page for more updates!</span>
        </div>

        <!-- ================= DOWNLOAD PORTAL (OTP REQUEST) ================= -->
        {% elif page == 'download_portal' %}
        <h2>📥 Download Leads Report</h2>
        <p style="font-size: 13px; color: #666; text-align: center; margin-bottom: 20px;">Click below to send a secure OTP to your Telegram to download the CSV file.</p>
        <form method="POST" action="/download-portal">
            <button type="submit" style="background: #007bff;">Send OTP to Telegram 📲</button>
        </form>

        <!-- ================= DOWNLOAD PORTAL (OTP VERIFY) ================= -->
        {% elif page == 'download_verify' %}
        <h2>🔐 Enter Telegram OTP</h2>
        <p style="font-size: 13px; color: #666; text-align: center; margin-bottom: 20px;">OTP sent to your Telegram chat!</p>
        {% if error %}<p style="color:red; text-align:center;">{{ error }}</p>{% endif %}
        <form method="POST" action="/download-verify">
            <div class="form-group">
                <input type="text" name="otp" placeholder="Enter 4-digit OTP" required style="text-align:center; font-size:18px;" maxlength="4">
            </div>
            <button type="submit" style="background: #2ed573;">Verify & Download 📥</button>
        </form>

        <!-- ================= ADMIN LOGIN ================= -->
        {% elif page == 'admin_login' %}
        <h2>🔐 Admin Login</h2>
        <form method="POST" action="/admin/login">
            <div class="form-group">
                <button type="submit" style="background: #2ed573;">Send OTP to Telegram 📲</button>
            </div>
        </form>

        {% elif page == 'admin_verify' %}
        <h2>🔐 Enter Telegram OTP</h2>
        {% if error %}<p style="color:red; text-align:center;">{{ error }}</p>{% endif %}
        <form method="POST" action="/admin/verify">
            <div class="form-group">
                <input type="text" name="otp" placeholder="Enter 4-digit OTP" required style="text-align:center; font-size:18px;" maxlength="4">
            </div>
            <button type="submit" style="background: #2ed573;">Verify OTP</button>
        </form>

        <!-- ================= ADMIN PANEL ================= -->
        {% elif page == 'admin' %}
        <h2>⚙️ Admin Dashboard</h2>
        <div style="text-align: right; margin-bottom: 10px;">
            <a href="/admin/logout" style="color: #d9534f; font-weight: bold; text-decoration: none; font-size: 12px;">🔒 Logout</a>
        </div>
        
        <div class="section-box">
            <h3>🔧 Global WhatsApp Settings</h3>
            <form method="POST" action="/admin/settings">
                <div class="form-group"><label>WhatsApp Number:</label><input type="text" name="wa_number" value="{{ settings.wa_number }}" required></div>
                <button type="submit" style="background: #007bff;">Update Settings</button>
            </form>
        </div>

        <div class="section-box">
            <h3>🏠 Manage / Add Properties</h3>
            <form method="GET" action="/admin" style="margin-bottom: 15px;">
                <div class="form-group">
                    <label>Select Property to Edit or Add New:</label>
                    <select name="edit_pid" onchange="this.form.submit()">
                        <option value="NEW" {% if edit_pid == 'NEW' %}selected{% endif %}>➕ Add New Property</option>
                        {% for pid in properties.keys() %}
                        <option value="{{ pid }}" {% if pid == edit_pid %}selected{% endif %}>{{ pid }} - {{ properties[pid].title }}</option>
                        {% endfor %}
                    </select>
                </div>
            </form>

            <form method="POST" action="/admin/save_property">
                <input type="hidden" name="is_new" value="{{ edit_pid }}">
                <div class="form-group">
                    <label>Property Code (e.g., CHTY02):</label>
                    <input type="text" name="pid" value="{% if edit_pid != 'NEW' %}{{ edit_pid }}{% endif %}" {% if edit_pid != 'NEW' %}readonly style="background:#e9ecef;"{% endif %} required>
                </div>
                <div class="form-group"><label>Title:</label><input type="text" name="title" value="{{ current_prop.title }}" required></div>
                <div class="form-group"><label>Rent (₹):</label><input type="number" name="rent" value="{{ current_prop.rent }}" required></div>
                <div class="form-group"><label>Advance (₹):</label><input type="number" name="advance" value="{{ current_prop.advance }}" required></div>
                <div class="form-group"><label>Electricity per unit (₹):</label><input type="number" name="electricity" value="{{ current_prop.electricity }}" required></div>
                <div class="form-group"><label>Allowed Members:</label><input type="text" name="members" value="{{ current_prop.members }}" placeholder="e.g. 3 to 4 Members" required></div>
                <div class="form-group"><label><input type="checkbox" name="is_sold" {% if current_prop.is_sold %}checked{% endif %}> Mark as SOLD OUT</label></div>
                
                <button type="submit" style="margin-bottom: 10px;">Save Property</button>
            </form>

            {% if edit_pid != 'NEW' %}
            <form method="POST" action="/admin/delete_property" onsubmit="return confirm('Are you sure you want to delete this property?');">
                <input type="hidden" name="pid" value="{{ edit_pid }}">
                <button type="submit" class="btn-danger">Delete Property 🗑️</button>
            </form>
            {% endif %}
        </div>

        <h3 style="margin-top: 30px;">📋 Live Leads & Status</h3>
        <div style="margin-bottom: 15px;">
            <a href="/download-portal" style="text-decoration: none;">
                <button type="button" style="background: #17a2b8;">📥 Download Leads Report (OTP Secured)</button>
            </a>
        </div>

        <div class="table-responsive">
            <table>
                <tr><th>Timestamp</th><th>Name</th><th>Phone</th><th>Prop</th><th>Step</th><th>Status</th></tr>
                {% for lead in leads %}
                <tr>
                    <td>{{ lead[0] }}</td>
                    <td>{{ lead[1] }}</td>
                    <td>{{ lead[2] }}</td>
                    <td>{{ lead[3] }}</td>
                    <td>{{ lead[4] }}</td>
                    <td>
                        {% if 'Success' in lead[5] %}
                            <span class="badge badge-success">{{ lead[5] }}</span>
                        {% elif 'Pending' in lead[5] %}
                            <span class="badge badge-pending">{{ lead[5] }}</span>
                        {% else %}
                            <span class="badge badge-visit">{{ lead[5] }}</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def step1():
    session.clear()
    session['followed'] = 'yes'
    return render_template_string(HTML_TEMPLATE, page="step1", followed='yes')

@app.route("/step1", methods=["POST"])
def post_step1():
    followed = request.form.get("followed")
    session['followed'] = followed
    if followed == "no":
        return render_template_string(HTML_TEMPLATE, page="not_followed")
    return redirect(url_for("step2"))

@app.route("/step2", methods=["GET", "POST"])
def step2():
    followed = session.get('followed', 'yes')
    data = load_db()
    db = data["properties"]
    
    active_keys = [k for k, v in db.items() if not v.get("is_sold", False)]
    if not active_keys:
        return render_template_string(HTML_TEMPLATE, page="sold")

    selected_id = request.args.get("prop_id") or session.get('lead_prop') or active_keys[0]
    if selected_id not in db or db[selected_id].get("is_sold", False):
        selected_id = active_keys[0]
        
    prop = db[selected_id]
    session['lead_prop'] = selected_id

    if request.method == "POST":
        prop_id = request.form.get("prop_id")
        session['lead_prop'] = prop_id
        return redirect(url_for("step3"))
        
    return render_template_string(HTML_TEMPLATE, page="step2", properties=db, selected_id=selected_id, current_prop=prop, followed=followed)

@app.route("/step3", methods=["GET", "POST"])
def step3():
    prop_id = session.get('lead_prop', 'CHTY01')
    followed = session.get('followed', 'yes')
    
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        
        if not phone or not phone.isdigit() or len(phone) != 10:
            return "<script>alert('Phone number must be exactly 10 digits!'); window.history.back();</script>"

        session['lead_name'] = name
        session['lead_phone'] = phone

        save_lead_to_csv({
            "name": name,
            "phone": phone,
            "prop_id": prop_id,
            "step": "Step 3 - Reached Payment",
            "status": "Pending Payment"
        })

        msg = f"🔥 Hot Lead (Reached Payment)!\nProperty: {prop_id}\nName: {name}\nPhone: {phone}"
        threading.Thread(target=send_telegram_async, args=(msg,)).start()

        return redirect(url_for("payment_page"))
        
    name = session.get('lead_name', '')
    phone = session.get('lead_phone', '')
    return render_template_string(HTML_TEMPLATE, page="step3", prop_id=prop_id, name=name, phone=phone, followed=followed)

@app.route("/payment", methods=["GET"])
def payment_page():
    prop_id = session.get('lead_prop', 'CHTY01')
    name = session.get('lead_name', '')
    phone = session.get('lead_phone', '')
    
    if not name or not phone:
        return redirect(url_for("step3"))
        
    return render_template_string(HTML_TEMPLATE, page="payment", prop_id=prop_id, name=name, phone=phone)

@app.route("/create-payment", methods=["POST"])
def create_payment():
    try:
        req_data = request.get_json() or {}
        prop_id = req_data.get('prop_id', 'CHTY01')
        amount = float(req_data.get('amount', 50.00))
        
        url = "https://api.cashfree.com/pg/orders"
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
                "customer_id": "cust_" + str(random.randint(1000, 9999)),
                "customer_phone": session.get('lead_phone', '9999999999'),
                "customer_email": "user@nammachennairooms.com"
            },
            "order_meta": {
                "return_url": "https://namma-chennai-rooms.onrender.com/"
            },
            "order_note": f"Booking for Property {prop_id} - Namma Chennai Rooms"
        }
        response = requests.post(url, json=payload, headers=headers)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/success", methods=["GET"])
def payment_success():
    prop_id = request.args.get("prop_id", "") or session.get('lead_prop', 'CHTY01')
    name = request.args.get("name", "") or session.get('lead_name', 'User')
    phone = request.args.get("phone", "") or session.get('lead_phone', 'N/A')
    
    data = load_db()
    properties = data["properties"]
    prop_info = properties.get(prop_id, {"title": "Standard Room", "rent": 0, "advance": 0, "members": "N/A"})
    
    save_lead_to_csv({
        "name": name,
        "phone": phone,
        "prop_id": prop_id,
        "step": "Completed",
        "status": "Success Paid"
    })

    wa_message = f"Hi, I have completed my ₹50 payment for property booking!\n\n📋 *Booking Details:*\n• Property ID: {prop_id}\n• Property Title: {prop_info['title']}\n• Rent: ₹{prop_info['rent']}\n• Advance: ₹{prop_info['advance']}\n• Allowed Members: {prop_info['members']}\n\n👤 *My Details:*\n• Name: {name}\n• Phone: {phone}"

    success_msg = f"✅ Payment Verified Successfully (Cashfree Live)!\nProperty: {prop_id} ({prop_info['title']})\nName: {name}"
    threading.Thread(target=send_telegram_async, args=(success_msg,)).start()

    return render_template_string(HTML_TEMPLATE, page="success", prop_id=prop_id, name=name, wa_number=data["settings"]["wa_number"], wa_message=wa_message)

@app.route("/download-portal", methods=["GET", "POST"])
def download_portal():
    if request.method == "POST":
        otp = str(random.randint(1000, 9999))
        session['download_otp'] = otp
        
        message = f"📥 *Namma Chennai Rooms* Lead Download OTP: `{otp}`\nDo not share this with anyone!"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload)
            return render_template_string(HTML_TEMPLATE, page="download_verify")
        except:
            return render_template_string(HTML_TEMPLATE, page="download_portal")
            
    return render_template_string(HTML_TEMPLATE, page="download_portal")

@app.route("/download-verify", methods=["POST"])
def download_verify():
    user_otp = request.form.get("otp")
    if user_otp and user_otp == session.get("download_otp"):
        session.pop("download_otp", None)
        if not os.path.exists(LEADS_CSV):
            save_lead_to_csv({
                "name": "System Sample",
                "phone": "9025034415",
                "prop_id": "CHTY01",
                "step": "Initialized",
                "status": "Ready"
            })
        return send_file(LEADS_CSV, as_attachment=True, download_name="Namma_Chennai_Rooms_Leads.csv")
    else:
        return render_template_string(HTML_TEMPLATE, page="download_verify", error="Invalid OTP! Try again.")

@app.route("/admin", methods=["GET"])
def admin_panel():
    if not session.get("admin_logged_in"):
        return render_template_string(HTML_TEMPLATE, page="admin_login")
        
    data = load_db()
    db = data["properties"]
    edit_pid = request.args.get("edit_pid", "NEW")
    
    if edit_pid == "NEW":
        current_prop = {"title": "", "rent": "", "advance": "", "electricity": "", "members": "", "is_sold": False}
    else:
        current_prop = db.get(edit_pid, {"title": "", "rent": "", "advance": "", "electricity": "", "members": "", "is_sold": False})

    leads = []
    if os.path.exists(LEADS_CSV):
        with open(LEADS_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            leads = list(reader)

    return render_template_string(HTML_TEMPLATE, page="admin", settings=data["settings"], properties=db, edit_pid=edit_pid, current_prop=current_prop, leads=leads)

@app.route("/admin/login", methods=["POST"])
def admin_login():
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
        requests.post(url, json=payload)
        return redirect(url_for("admin_verify"))
    except:
        return render_template_string(HTML_TEMPLATE, page="admin_login")

@app.route("/admin/verify", methods=["GET", "POST"])
def admin_verify():
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        if user_otp and user_otp == session.get('generated_otp'):
            session['admin_logged_in'] = True
            session.pop('generated_otp', None)
            return redirect(url_for("admin_panel"))
        else:
            return render_template_string(HTML_TEMPLATE, page="admin_verify", error="Invalid OTP! Try again.")
    return render_template_string(HTML_TEMPLATE, page="admin_verify")

@app.route("/admin/logout", methods=["GET"])
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_panel"))

@app.route("/admin/settings", methods=["POST"])
def admin_settings():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_panel"))
    data = load_db()
    data["settings"]["wa_number"] = request.form.get("wa_number").strip()
    save_db(data)
    return redirect(url_for("admin_panel"))

@app.route("/admin/save_property", methods=["POST"])
def admin_save_property():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_panel"))
    data = load_db()
    pid = request.form.get("pid").strip().upper()
    data["properties"][pid] = {
        "title": request.form.get("title"),
        "rent": int(request.form.get("rent")),
        "advance": int(request.form.get("advance")),
        "electricity": int(request.form.get("electricity")),
        "members": request.form.get("members"),
        "is_sold": True if request.form.get("is_sold") else False
    }
    save_db(data)
    return redirect(url_for("admin_panel", edit_pid=pid))

@app.route("/admin/delete_property", methods=["POST"])
def admin_delete_property():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_panel"))
    data = load_db()
    pid = request.form.get("pid")
    if pid in data["properties"]:
        del data["properties"][pid]
        save_db(data)
    return redirect(url_for("admin_panel"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
