import os
import json
import csv
import threading
from flask import Flask, render_template_string, request, redirect, url_for, session
import requests
from PIL import Image
import pytesseract

app = Flask(__name__)
app.secret_key = "lokesh_secret_key_render_final"

TELEGRAM_BOT_TOKEN = "8874820853:AAGbZYqZ2Td8olEW6Cw1DJvcx6OTJCD4HgE"
TELEGRAM_CHAT_ID = "6269474117"

DB_FILE = "database.json"
LEADS_CSV = "leads.csv"
ADMIN_PIN = "1234"

def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "settings": {
                "upi_id": "logeshkrishnan157-1@okicici",
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
            writer.writerow(["Name", "Phone", "Property ID", "Status"])
        writer.writerow([lead_data["name"], lead_data["phone"], lead_data["prop_id"], lead_data["status"]])

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
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 15px; color: #333; position: relative; min-height: 100vh; }
        .container { width: 100%; max-width: 480px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.08); margin: 20px auto; }
        h2, h3 { color: #1a1a1a; text-align: center; margin-top: 10px; font-size: 22px; }
        .property-box { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #007bff; font-size: 14px; line-height: 1.5; }
        .property-box p { margin: 8px 0; }
        .form-group { margin-bottom: 18px; }
        label { display: block; font-weight: 600; margin-bottom: 6px; color: #333; font-size: 14px; }
        select, input[type="text"], input[type="number"], input[type="tel"], input[type="password"], input[type="file"] { width: 100%; padding: 12px; border: 1px solid #ccd0d5; border-radius: 8px; font-size: 16px; background: #fff; }
        button { background: #28a745; color: white; border: none; padding: 14px; width: 100%; font-size: 16px; font-weight: 600; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #218838; }
        .download-btn { background: #007bff; display: inline-block; text-align: center; color: white; text-decoration: none; padding: 10px 15px; border-radius: 6px; font-size: 14px; font-weight: bold; margin-top: 10px; }
        .download-btn:hover { background: #0056b3; }
        .error-msg { background: #ffebee; color: #c62828; padding: 12px; border-radius: 8px; margin-top: 15px; font-size: 13px; border: 1px solid #ef9a9a; text-align: center; font-weight: bold; }
        .success-msg { background: #e8f5e9; color: #2e7d32; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #c8e6c9; text-align: center; }
        .sold-banner { background: #ff4d4d; color: white; padding: 20px; text-align: center; border-radius: 8px; font-size: 18px; font-weight: bold; }
        .admin-nav { text-align: right; margin-bottom: 15px; }
        .admin-nav a { background: #e4e6eb; color: #050505; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: 600; }
        .step-indicator { text-align: center; color: #65676b; font-size: 12px; font-weight: 600; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }
        .table-responsive { width: 100%; overflow-x: auto; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; white-space: nowrap; }
        th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
        th { background: #f2f2f2; }
        .section-box { background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 15px; border: 1px solid #ddd; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .qr-img { width: 170px; max-width: 100%; height: auto; border-radius: 8px; border: 2px solid #ddd; padding: 5px; background: #fff; }

        /* LEFT SIDE ORAMA KUTTY ADMIN BAR */
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
        #secretAdminBar:hover {
            width: 15px;
            background: #0056b3;
        }
    </style>
</head>
<body>
    <!-- LEFT SIDE ORAMA KUTTY ADMIN BAR -->
    <div id="secretAdminBar" title="Admin" onclick="window.location.href='/admin'"></div>

    <div class="container">
        <div class="admin-nav">
            {% if page == 'admin' or page == 'admin_login' %}
            <a href="/">🏠 Back to Portal</a>
            {% endif %}
        </div>

        <!-- ================= STEP 1: INSTAGRAM CHECK ================= -->
        {% if page == 'step1' %}
        <div class="step-indicator">Step 1 of 4</div>
        <h2>Namma Chennai Rooms</h2>
        <form method="POST" action="/step1">
            <div class="form-group" style="background: #fff8e1; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba;">
                <label style="color: #856404;">Have you followed our Instagram Page (@namma_chennai_rooms)?</label>
                <p style="font-size: 12px; margin: 5px 0 12px 0;">If not, please follow first: <a href="https://www.instagram.com/namma_chennai_rooms/" target="_blank" style="color: #0056b3; font-weight: bold;">Click here to Follow</a></p>
                <select name="followed" required>
                    <option value="yes">Yes, I have followed!</option>
                    <option value="no">No</option>
                </select>
            </div>
            <button type="submit">Next ➔</button>
        </form>

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
                <input type="text" name="name" placeholder="Enter your name" required>
            </div>
            <div class="form-group">
                <label>WhatsApp Phone Number (Exact 10 Digits):</label>
                <input type="tel" name="phone" pattern="[0-9]{10}" minlength="10" maxlength="10" 
                       oninput="this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);" 
                       placeholder="e.g. 9840123456" title="Enter exactly 10 digits number" required>
            </div>
            <button type="submit">Proceed to Payment ➔</button>
        </form>

        <!-- ================= STEP 4: PAYMENT & SCREENSHOT VERIFICATION ================= -->
        {% elif page == 'payment' %}
        <div class="step-indicator">Step 4 of 4</div>
        <h2>Scan & Verify ₹50 Payment</h2>
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="margin: 15px 0;">
                <img src="{{ url_for('static', filename='qr.jpg') }}" alt="Google Pay QR" class="qr-img"><br>
                <a href="{{ url_for('static', filename='qr.jpg') }}" download="NammaChennai_QR.jpg" class="download-btn">📥 Download QR Code</a>
                <p style="font-size: 13px; color: #555; margin-top: 8px;"><b>UPI ID to Pay:</b> <code>{{ upi_id }}</code></p>
            </div>

            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #ddd; text-align: left;">
                <form method="POST" action="/verify_payment" enctype="multipart/form-data">
                    <input type="hidden" name="prop_id" value="{{ prop_id }}">
                    <input type="hidden" name="name" value="{{ name }}">
                    <input type="hidden" name="phone" value="{{ phone }}">
                    
                    <label style="color: #333; font-size: 13px;">Upload Payment Screenshot:</label>
                    <input type="file" name="screenshot" accept="image/*" required style="margin-bottom: 12px;">
                    
                    <button type="submit" style="background: #4e54c8; font-size: 15px;">🔍 Verify Screenshot & Unlock WhatsApp</button>
                </form>
            </div>

            {% if error %}
            <div class="error-msg">
                ❌ {{ error }}
            </div>
            {% endif %}
        </div>

        <!-- ================= SUCCESS PAYMENT PAGE ================= -->
        {% elif page == 'success' %}
        <div class="step-indicator">Completed</div>
        <h2>Payment Verified Successfully! 🎉</h2>
        <div class="success-msg">
            <p style="font-size: 14px; color: #2e7d32; margin-bottom: 15px; font-weight: bold;">
                ✅ Your payment screenshot is verified! Click below to open WhatsApp and send details to the owner:
            </p>
            <a href="https://wa.me/{{ wa_number }}?text=Hi,%20I%20successfully%20paid%20Rs.50%20registration%20fee%20for%20property%20{{ prop_id }}.%20My%20Name:%20{{ name }}%20(Payment%20verified)" target="_blank">
                <button style="background: #25D366; font-size: 16px;">💬 Open WhatsApp Now</button>
            </a>
        </div>

        {% elif page == 'not_followed' %}
        <div class="error">
            <h3>⚠️ Please Follow Our Page First!</h3>
            <p style="color:#333; font-size: 14px; margin-top: 15px;">To view property details and book house visits, you must follow our Instagram page. Please go back, follow the page, and try again!</p>
            <a href="/"><button style="margin-top: 20px; background: #007bff;">⬅️ Back to Start</button></a>
        </div>

        {% elif page == 'sold' %}
        <div class="sold-banner">
            🚫 Property Sold Out!<br><br>
            <span style="font-size: 14px; font-weight: normal;">This property has already been rented/sold out. Please check our Instagram page for more updates!</span>
        </div>

        <!-- ================= ADMIN LOGIN ================= -->
        {% elif page == 'admin_login' %}
        <h2>🔐 Admin Login</h2>
        <form method="POST" action="/admin/login">
            <div class="form-group">
                <label>Enter Admin PIN / Password:</label>
                <input type="password" name="pin" placeholder="Enter 4-digit PIN" required>
            </div>
            <button type="submit" style="background: #007bff;">Login to Dashboard</button>
        </form>

        <!-- ================= ADMIN PANEL ================= -->
        {% elif page == 'admin' %}
        <h2>⚙️ Admin Dashboard</h2>
        <div style="text-align: right; margin-bottom: 10px;">
            <a href="/admin/logout" style="color: #d9534f; font-weight: bold; text-decoration: none; font-size: 12px;">🔒 Logout</a>
        </div>
        
        <div class="section-box">
            <h3>🔧 Global Payment & WhatsApp Settings</h3>
            <form method="POST" action="/admin/settings">
                <div class="form-group"><label>UPI ID:</label><input type="text" name="upi_id" value="{{ settings.upi_id }}" required></div>
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

        <h3 style="margin-top: 30px;">📋 Captured Leads (Live from leads.csv)</h3>
        <div class="table-responsive">
            <table>
                <tr><th>Name</th><th>Phone</th><th>Prop</th><th>Status</th></tr>
                {% for lead in leads %}
                <tr><td>{{ lead[0] }}</td><td>{{ lead[1] }}</td><td>{{ lead[2] }}</td><td>{{ lead[3] }}</td></tr>
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
    return render_template_string(HTML_TEMPLATE, page="step1")

@app.route("/step1", methods=["POST"])
def post_step1():
    followed = request.form.get("followed")
    if followed == "no":
        save_lead_to_csv({"name": "Unknown", "phone": "Unknown", "prop_id": "N/A", "status": "Not Followed Insta"})
        return render_template_string(HTML_TEMPLATE, page="not_followed")
    return redirect(url_for("step2", followed=followed))

@app.route("/step2", methods=["GET", "POST"])
def step2():
    followed = request.args.get("followed") or request.form.get("followed")
    data = load_db()
    db = data["properties"]
    
    active_keys = [k for k, v in db.items() if not v.get("is_sold", False)]
    if not active_keys:
        return render_template_string(HTML_TEMPLATE, page="sold")

    selected_id = request.args.get("prop_id", active_keys[0])
    prop = db.get(selected_id, db[active_keys[0]])
    
    if prop.get("is_sold", False):
        selected_id = active_keys[0]
        prop = db[selected_id]

    if request.method == "POST":
        prop_id = request.form.get("prop_id")
        return render_template_string(HTML_TEMPLATE, page="step3", prop_id=prop_id, followed=followed)
        
    return render_template_string(HTML_TEMPLATE, page="step2", properties=db, selected_id=selected_id, current_prop=prop, followed=followed)

@app.route("/step3", methods=["POST"])
def post_step3():
    prop_id = request.form.get("prop_id")
    name = request.form.get("name")
    phone = request.form.get("phone")
    
    if not phone or not phone.isdigit() or len(phone) != 10:
        return "<script>alert('Phone number must be exactly 10 digits!'); window.history.back();</script>"

    data = load_db()
    settings = data["settings"]
    
    save_lead_to_csv({"name": name, "phone": phone, "prop_id": prop_id, "status": "Reached Payment"})
    msg = f"🔥 Hot Lead (Reached Payment)!\nProperty: {prop_id}\nName: {name}\nPhone: {phone}"
    threading.Thread(target=send_telegram_async, args=(msg,)).start()

    return render_template_string(HTML_TEMPLATE, page="payment", prop_id=prop_id, name=name, phone=phone, upi_id=settings['upi_id'])

@app.route("/verify_payment", methods=["POST"])
def verify_payment():
    prop_id = request.form.get("prop_id")
    name = request.form.get("name")
    phone = request.form.get("phone")
    
    file = request.files.get("screenshot")
    if not file or file.filename == "":
        data = load_db()
        return render_template_string(HTML_TEMPLATE, page="payment", prop_id=prop_id, name=name, phone=phone, upi_id=data["settings"]["upi_id"], error="Please upload a payment screenshot!")

    data = load_db()
    target_upi = data["settings"]["upi_id"].strip().lower() # e.g. logeshkrishnan157-1@okicici
    # Extract the unique ending signature part like "57-1@okicici" or just "@okicici" to match GPay masked text
    upi_parts = target_upi.split('@')
    domain = upi_parts[1] if len(upi_parts) > 1 else "okicici"
    prefix_suffix = upi_parts[0][-4:] # takes last 4 chars like "57-1"

    # Save temp file to run OCR scan
    temp_path = "temp_screenshot.jpg"
    file.save(temp_path)

    try:
        # OCR Image processing
        img = Image.open(temp_path)
        extracted_text = pytesseract.image_to_string(img).lower()
        os.remove(temp_path)

        # Flexible verification supporting GPay masked format (e.g. "....57-1@okicici")
        has_domain = domain in extracted_text
        has_prefix = prefix_suffix in extracted_text
        has_amount = "50" in extracted_text

        if (has_domain and has_prefix) or has_amount or target_upi in extracted_text:
            save_lead_to_csv({"name": name, "phone": phone, "prop_id": prop_id, "status": "Payment Verified & Unlocked"})
            success_msg = f"✅ Payment Verified Successfully!\nProperty: {prop_id}\nName: {name}\nPhone: {phone}"
            threading.Thread(target=send_telegram_async, args=(success_msg,)).start()
            return render_template_string(HTML_TEMPLATE, page="success", prop_id=prop_id, name=name, wa_number=data["settings"]["wa_number"])
        else:
            return render_template_string(HTML_TEMPLATE, page="payment", prop_id=prop_id, name=name, phone=phone, upi_id=data["settings"]["upi_id"], error="Invalid Screenshot! Your transaction details were not clearly matched. Please upload a clear GPay/PhonePe screenshot showing ₹50 payment.")
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return render_template_string(HTML_TEMPLATE, page="payment", prop_id=prop_id, name=name, phone=phone, upi_id=data["settings"]["upi_id"], error="Error processing image. Please try uploading a clear screenshot.")

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
    pin = request.form.get("pin")
    if pin == ADMIN_PIN:
        session["admin_logged_in"] = True
        return redirect(url_for("admin_panel"))
    else:
        return "<script>alert('Incorrect PIN!'); window.location='/admin';</script>"

@app.route("/admin/logout", methods=["GET"])
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_panel"))

@app.route("/admin/settings", methods=["POST"])
def admin_settings():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_panel"))
    data = load_db()
    data["settings"]["upi_id"] = request.form.get("upi_id").strip()
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
