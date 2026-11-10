import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import sqlite3
import pandas as pd
import plotly.express as px
import pydeck as pdk
import qrcode
import io
import uuid
import hashlib
import hmac
import secrets
import os
import re
import unicodedata
from datetime import datetime

# =====================================================
# 1. CONFIGURATION
# =====================================================
st.set_page_config(page_title="WNS | النيل الأبيض الذكية", page_icon="🌍", layout="wide")
DB_NAME = "smart_nation.db"
NOW = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# =====================================================
# 2. LANGUAGE
# =====================================================
if "language" not in st.session_state:
    st.session_state.language = "العربية"

# =====================================================
# 3. GOVERNMENT DEPARTMENTS & CITIES
# =====================================================
DEPARTMENTS = {
    "Electricity": {"ar": "هيئة الكهرباء", "en": "Electricity Authority", "icon": "⚡"},
    "Water": {"ar": "هيئة مياه ولاية النيل الأبيض", "en": "White Nile Water Authority", "icon": "💧"},
    "Cleaning": {"ar": "إدارة النظافة بالمحلية", "en": "Local Cleaning Department", "icon": "🗑️"},
    "Roads": {"ar": "إدارة الطرق والجسور", "en": "Roads and Bridges Department", "icon": "🛣️"},
    "Sewage": {"ar": "إدارة الصرف الصحي", "en": "Sewage Department", "icon": "🚰"},
    "Health": {"ar": "إدارة الصحة", "en": "Health Department", "icon": "🏥"},
    "Environment": {"ar": "إدارة البيئة", "en": "Environment Department", "icon": "🌳"},
    "Emergency": {"ar": "الدفاع المدني", "en": "Civil Defense", "icon": "🚒"},
    "Traffic": {"ar": "شرطة المرور", "en": "Traffic Police", "icon": "🚦"},
    "Education": {"ar": "إدارة التعليم", "en": "Education Department", "icon": "🏫"},
    "Other": {"ar": "غرفة المتابعة والشرطة العامة", "en": "General Follow-up & Police Office", "icon": "📋"}
}
CITIES = {
    "كوستي": (13.16290, 32.66347), "ربك": (13.18087, 32.73999),
    "الدويم": (14.00120, 32.31160), "القطينة": (14.86480, 32.36680),
    "تندلتي": (13.01667, 31.86667), "مرابة": (12.35000, 32.18333),
    "الجزيرة أبا": (13.31930, 32.61320), "الكوة": (13.74630, 32.49960),
    "ود الزاكي": (14.46190, 32.20650)
}
CATEGORY_KEYWORDS = {
    "Electricity": ["كهرباء", "كهربا", "النور", "تيار", "انارة", "عمود كهرباء", "سلك", "اسلاك", "لمبات", "ضلمه", "electricity", "power", "outage", "electric"],
    "Water": ["مياه", "موية", "مويا", "مويه", "حنفيه", "حنفية", "ماسوره", "انبوب", "تسريب", "تسرب مياه", "انقطاع المياه", "water", "leak", "pipe"],
    "Cleaning": ["نفايات", "قمامه", "زباله", "زبل", "وسخ", "اوساخ", "كوشه", "نظافه", "مخلفات", "روائح", "garbage", "waste", "trash"],
    "Roads": ["شارع", "شوارع", "حفره", "طريق", "اسفلت", "مكسر", "محفر", "مطب", "رصيف", "road", "pothole", "street"],
    "Sewage": ["صرف صحي", "مجاري", "طفح", "مجرى", "بالوعه", "انسداد المجاري", "sewage", "drainage"],
    "Health": ["مستشفى", "مركز صحي", "مرض", "وباء", "كوليرا", "اسهالات", "اسهال", "تسمم", "عياده", "صحه", "ادويه", "فيروس", "عدوى", "حمى", "علاج", "hospital", "health", "clinic", "cholera", "epidemic"],
    "Environment": ["تلوث", "بيئه", "حرق نفايات", "دخان المصانع", "تلوث الهواء", "pollution", "environment"],
    "Emergency": ["حريق", "نار", "دخان", "انفجار", "انهيار", "غرق", "فيضان", "حادث خطير", "emergency", "fire", "explosion"],
    "Traffic": ["مرور", "حادث مروري", "اشاره مرور", "ازدحام", "اختناق مروري", "اشارات", "traffic", "accident"],
    "Education": ["مدرسه", "مدارس", "تعليم", "فصل دراسي", "معلم", "مدرس", "school", "education"],
    "Other": ["جريمة", "جريمه", "سرقة", "سرقه", "اعتداء", "شجار", "احتيال", "نهب", "تهديد", "شرطة", "شرطه", "بلاغ جنائي", "أمن", "حرامي", "سطو", "crime", "theft", "police", "robbery"]
}
CRITICAL_TERMS = ["حريق", "نار", "انفجار", "صعق", "سلك عريان", "سلك مكشوف", "سلك واقع", "عمود واقع", "عمود ساقط", "انهيار", "غرق", "فيضان", "تسمم", "وباء", "كوليرا", "سرقة", "جريمة", "قتل", "سطو", "fire", "explosion", "emergency", "crime"]
URGENT_TERMS = ["انقطاع المياه", "انقطاع الكهرباء", "المويه قاطعه", "النور قاطع", "ماسوره مكسوره", "طفح المجاري", "تسرب كبير", "حادث", "اسهالات", "no water", "no electricity"]
IMPORTANT_TERMS = ["مدرسه", "مستشفى", "مركز صحي", "الحي بالكامل", "كل الحي", "شارع رئيسي", "عدد كبير", "hospital", "whole neighborhood"]

language = st.sidebar.selectbox("🌐 اللغة / Language", ["العربية", "English"],
    index=0 if st.session_state.language == "العربية" else 1)
st.session_state.language = language
AR = language == "العربية"

def label(ar, en):
    return ar if AR else en

PRIORITIES = {
    "Normal": "🟢 عادي" if AR else "🟢 Normal",
    "Important": "🟡 مهم" if AR else "🟡 Important",
    "Urgent": "🟠 عاجل" if AR else "🟠 Urgent",
    "Emergency": "🔴 طارئ" if AR else "🔴 Emergency"
}
STATUSES = {
    "Pending": "🟡 قيد الانتظار" if AR else "🟡 Pending",
    "In Progress": "🔵 جارٍ المعالجة" if AR else "🔵 In Progress",
    "Resolved": "🟢 تمت المعالجة" if AR else "🟢 Resolved"
}
def category_name(key):
    item = DEPARTMENTS.get(key, DEPARTMENTS["Other"])
    return item["ar"] if AR else item["en"]
def priority_name(key):
    return PRIORITIES.get(key, key)
def status_name(key):
    return STATUSES.get(key, key)

# =====================================================
# 4. RTL / LTR + DESIGN
# =====================================================
direction = "rtl" if AR else "ltr"
align = "right" if AR else "left"
st.markdown(f"""
<style>
.stApp {{background:#EAF4F8;}}
section[data-testid="stSidebar"] {{background:#12304A; direction:{direction};}}
section[data-testid="stSidebar"] * {{color:white !important; text-align:{align};}}
/* Keep Streamlit's main layout direction unchanged; apply RTL to text only. */
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {{
 text-align:{align};
}}
[data-testid="stMainBlockContainer"] h1,
[data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3,
[data-testid="stMainBlockContainer"] h4,
[data-testid="stMainBlockContainer"] p,
[data-testid="stMainBlockContainer"] label,
[data-testid="stMainBlockContainer"] li,
[data-testid="stMainBlockContainer"] td,
[data-testid="stMainBlockContainer"] th {{
 direction:{direction};
 text-align:{align};
}}
h1,h2,h3,h4,p,label {{direction:{direction}; text-align:{align}; color:#12304A;}}
input,textarea {{direction:{direction}; text-align:{align};}}
div[data-baseweb="select"] {{direction:{direction};}}
.stButton>button {{background:linear-gradient(90deg,#079B91,#087E8B);color:white;border:0;border-radius:10px;padding:10px 18px;font-weight:bold;}}
.stButton>button:hover {{background:#066B72;color:white;}}
.stDownloadButton>button {{background:#12304A;color:white;border-radius:10px;}}
div[data-testid="stMetric"] {{background:white;padding:18px;border-radius:14px;border-left:5px solid #079B91;box-shadow:0 3px 12px rgba(0,0,0,.05);}}
div[data-testid="stForm"] {{background:white;padding:20px;border-radius:14px;border:1px solid #DCEAF2;}}
div[data-testid="stExpander"] {{background:white;border-radius:12px;}}
.wns-header {{background:linear-gradient(110deg,#12304A,#087E8B);padding:25px;border-radius:16px;color:white;text-align:center;margin-bottom:20px;}}
.wns-header h1,.wns-header h3 {{color:white !important;text-align:center !important;}}
.wns-card {{background:white;border-radius:14px;padding:20px;margin:10px 0;border:1px solid #DCEAF2;}}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 4A. RESPONSIVE RTL / LTR REFINEMENT (visual only)
# =====================================================
st.markdown("""
<style>
[data-testid="stSidebar"] [data-testid="stSelectbox"] {
    width:100% !important;
    min-width:0 !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] * {
    white-space:nowrap !important;
}
[data-baseweb="select"] > div {
    min-height:42px;
}
[data-testid="stMainBlockContainer"] {
    padding-left:clamp(1rem, 4vw, 3rem);
    padding-right:clamp(1rem, 4vw, 3rem);
}
@media (max-width:768px) {
    [data-testid="stMainBlockContainer"] {
        padding-left:0.8rem !important;
        padding-right:0.8rem !important;
    }

    /* Stack Streamlit columns vertically on phones instead of splitting the screen */
    div[data-testid="stHorizontalBlock"] {
        display:flex !important;
        flex-direction:column !important;
        flex-wrap:nowrap !important;
        gap:0.7rem !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width:100% !important;
        min-width:100% !important;
        max-width:100% !important;
        flex:1 1 100% !important;
    }

    .wns-header {padding:16px !important;}
    .wns-card {padding:14px !important;}
    div[data-testid="stMetric"] {padding:12px !important;}
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 5. TEXT ANALYSIS
# =====================================================
def normalize_text(value):
    text = str(value or "").lower().strip()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[ً-ٰٟ]", "", text).replace("ـ", "")
    text = text.translate(str.maketrans({"أ":"ا","إ":"ا","آ":"ا","ى":"ي","ة":"ه"}))
    return re.sub(r"\s+", " ", text)

def analyze_report(description):
    text = normalize_text(description)
    scores, detected = {}, []
    for category, words in CATEGORY_KEYWORDS.items():
        matched = [w for w in words if normalize_text(w) in text]
        scores[category] = len(matched)
        detected.extend(matched)
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        best = "Other"
    critical = any(normalize_text(x) in text for x in CRITICAL_TERMS)
    urgent = any(normalize_text(x) in text for x in URGENT_TERMS)
    important = any(normalize_text(x) in text for x in IMPORTANT_TERMS)
    if critical:
        priority, risk = "Emergency", 95
    elif urgent:
        priority, risk = "Urgent", 75
    elif important:
        priority, risk = "Important", 50
    else:
        priority, risk = "Normal", 20
    return best, priority, risk, DEPARTMENTS[best]["ar"], detected[:10], critical

# =====================================================
# 6. DATABASE & SAFE MIGRATIONS
# =====================================================
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def add_column_if_missing(conn, table, column, definition):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def initialize_database():
    conn = get_connection()
    conn.execute("""CREATE TABLE IF NOT EXISTS identities (
        id INTEGER PRIMARY KEY AUTOINCREMENT, identity_code TEXT UNIQUE,
        full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, user_type TEXT,
        password_hash TEXT DEFAULT '', created_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, report_code TEXT UNIQUE,
        identity_code TEXT DEFAULT '', category TEXT, description TEXT,
        location TEXT, latitude REAL, longitude REAL, priority TEXT,
        status TEXT, created_at TEXT)""")
    for col, definition in {
        "department_id":"INTEGER", "department_name":"TEXT DEFAULT ''",
        "city":"TEXT DEFAULT ''", "neighborhood":"TEXT DEFAULT ''",
        "risk_score":"INTEGER DEFAULT 0", "is_critical":"INTEGER DEFAULT 0",
        "updated_at":"TEXT DEFAULT ''"
    }.items():
        add_column_if_missing(conn, "reports", col, definition)
    conn.execute("""CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, department_key TEXT UNIQUE,
        name_ar TEXT, name_en TEXT, is_active INTEGER DEFAULT 1)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS staff_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
        full_name TEXT, password_hash TEXT, role TEXT, department_id INTEGER,
        city TEXT DEFAULT '', is_active INTEGER DEFAULT 1)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS admin_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER,
        title TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL,
        is_read INTEGER DEFAULT 0, recipient_type TEXT DEFAULT 'admin',
        department_id INTEGER)""")
    add_column_if_missing(conn, "admin_notifications", "recipient_type", "TEXT DEFAULT 'admin'")
    add_column_if_missing(conn, "admin_notifications", "department_id", "INTEGER")
    conn.execute("""CREATE TABLE IF NOT EXISTS citizen_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, identity_code TEXT,
        report_id INTEGER, title TEXT, message TEXT, created_at TEXT,
        is_read INTEGER DEFAULT 0)""")
    for key, item in DEPARTMENTS.items():
        conn.execute("INSERT OR IGNORE INTO departments(department_key,name_ar,name_en) VALUES(?,?,?)",
                     (key, item["ar"], item["en"]))
    # Repair department assignment for ALL legacy reports, not only NULL values.
    # Older versions may have saved Arabic labels, lowercase names, or stale department IDs.
    category_aliases = {}
    for key, item in DEPARTMENTS.items():
        category_aliases[normalize_text(key)] = key
        category_aliases[normalize_text(item["ar"])] = key
        category_aliases[normalize_text(item["en"])] = key
    extra_aliases = {
        "كهرباء": "Electricity", "الكهرباء": "Electricity", "electric": "Electricity",
        "مياه": "Water", "المياه": "Water", "الموية": "Water", "water authority": "Water",
        "نظافة": "Cleaning", "النظافة": "Cleaning", "نفايات": "Cleaning", "waste": "Cleaning",
        "طرق": "Roads", "الطرق": "Roads", "الجسور": "Roads", "roads and bridges": "Roads",
        "مجاري": "Sewage", "الصرف الصحي": "Sewage", "sewerage": "Sewage",
        "الصحة": "Health", "صحة": "Health", "مستشفى": "Health",
        "البيئة": "Environment", "بيئة": "Environment",
        "الدفاع المدني": "Emergency", "طوارئ": "Emergency", "حريق": "Emergency",
        "المرور": "Traffic", "شرطة المرور": "Traffic",
        "التعليم": "Education", "مدرسة": "Education",
        "أخرى": "Other", "عام": "Other", "متابعة": "Other", "الشرطة": "Other"
    }
    category_aliases.update({normalize_text(alias): key for alias, key in extra_aliases.items()})
    rows = conn.execute("SELECT id,category,description,department_id,department_name FROM reports").fetchall()
    for rid, old_category, desc, old_dep_id, old_dep_name in rows:
        normalized_category = normalize_text(old_category)
        canonical_category = category_aliases.get(normalized_category)
        if not canonical_category:
            # Classify from the report text when the saved category is missing or legacy/unknown.
            canonical_category = analyze_report(desc or "")[0]
        if canonical_category not in DEPARTMENTS:
            canonical_category = "Other"
        dep = conn.execute("SELECT id,name_ar FROM departments WHERE department_key=?", (canonical_category,)).fetchone()
        if dep and (old_category != canonical_category or old_dep_id != dep[0] or old_dep_name != dep[1]):
            conn.execute("UPDATE reports SET category=?,department_id=?,department_name=? WHERE id=?",
                         (canonical_category, dep[0], dep[1], rid))
    # Bring old department notifications into line with the repaired report assignment.
    conn.execute("""UPDATE admin_notifications
        SET department_id=(SELECT r.department_id FROM reports r WHERE r.id=admin_notifications.report_id)
        WHERE recipient_type='department' AND report_id IS NOT NULL
          AND EXISTS (SELECT 1 FROM reports r WHERE r.id=admin_notifications.report_id)""")
    conn.commit()
    conn.close()

# Define password functions before app initialization.
def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200000)
    return salt + "$" + digest.hex()

def verify_password(password, stored):
    try:
        salt, expected = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200000).hex()
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

initialize_database()

# =====================================================
# 7. DATABASE HELPERS
# =====================================================
def get_department_id(category):
    conn = get_connection()
    row = conn.execute("SELECT id FROM departments WHERE department_key=?", (category,)).fetchone()
    conn.close()
    return row[0] if row else None

def load_reports():
    conn = get_connection()
    df = pd.read_sql_query("""SELECT * FROM reports ORDER BY
        CASE priority WHEN 'Emergency' THEN 1 WHEN 'Urgent' THEN 2
        WHEN 'Important' THEN 3 ELSE 4 END, id DESC""", conn)
    conn.close()
    return df

def load_identities():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id,identity_code,full_name,email,user_type,created_at FROM identities ORDER BY id DESC", conn)
    conn.close()
    return df

def create_notification(report_id, title, message, recipient_type="admin", department_id=None):
    conn = get_connection()
    conn.execute("""INSERT INTO admin_notifications
        (report_id,title,message,created_at,is_read,recipient_type,department_id)
        VALUES(?,?,?,?,0,?,?)""", (report_id,title,message,NOW(),recipient_type,department_id))
    conn.commit()
    conn.close()

def notify_citizen(identity_code, report_id, title, message):
    conn = get_connection()
    conn.execute("""INSERT INTO citizen_notifications
        (identity_code,report_id,title,message,created_at)
        VALUES(?,?,?,?,?)""", (identity_code,report_id,title,message,NOW()))
    conn.commit()
    conn.close()

def load_notifications(department_id=None):
    conn = get_connection()
    if department_id is None:
        query = """SELECT n.*,r.category,r.location,r.priority,r.status
                   FROM admin_notifications n LEFT JOIN reports r ON n.report_id=r.id
                   WHERE n.recipient_type='admin' ORDER BY n.id DESC"""
        df = pd.read_sql_query(query, conn)
    else:
        query = """SELECT n.*,r.category,r.location,r.priority,r.status
                   FROM admin_notifications n LEFT JOIN reports r ON n.report_id=r.id
                   WHERE n.recipient_type='department' AND n.department_id=? ORDER BY n.id DESC"""
        df = pd.read_sql_query(query, conn, params=(department_id,))
    conn.close()
    return df

# =====================================================
# 8. IDENTITY & STAFF AUTHENTICATION
# =====================================================
def current_identity():
    code = st.session_state.get("citizen_identity_code")
    if not code:
        return None
    conn = get_connection()
    row = conn.execute("""SELECT identity_code,full_name,email,user_type,created_at
                          FROM identities WHERE identity_code=?""", (code,)).fetchone()
    conn.close()
    return row

def logout_citizen():
    st.session_state.pop("citizen_identity_code", None)
    st.session_state.pop("citizen_identity_verified", None)
    st.rerun()

def mask_email(email):
    if not email or "@" not in email:
        return email
    user, domain = email.split("@", 1)
    masked = user[0] + ("*" * max(1, len(user)-2)) + (user[-1] if len(user)>1 else "")
    return f"{masked}@{domain}"

def seed_default_departments():
    conn = get_connection()
    depts = conn.execute("SELECT id,department_key,name_ar FROM departments").fetchall()
    created = 0
    for dep_id, key, name in depts:
        username = f"{key.lower()}_user"
        if not conn.execute("SELECT 1 FROM staff_users WHERE username=?", (username,)).fetchone():
            conn.execute("""INSERT INTO staff_users
                (username,full_name,password_hash,role,department_id,city,is_active)
                VALUES(?,?,?,'department',?,'',1)""",
                (username, f"مسؤول {name}", hash_password(f"{key.lower()}12345"), dep_id))
            created += 1
    conn.commit()
    conn.close()
    return created

def get_staff():
    user_id = st.session_state.get("staff_id")
    if user_id == -999 and st.session_state.get("root_admin"):
        return (-999, "admin", "مدير النظام", "admin", None, "")
    if not user_id:
        return None
    conn = get_connection()
    row = conn.execute("""SELECT id,username,full_name,role,department_id,city
                          FROM staff_users WHERE id=? AND is_active=1""", (user_id,)).fetchone()
    conn.close()
    return row

def staff_login(username, password):
    conn = get_connection()
    row = conn.execute("SELECT id,password_hash FROM staff_users WHERE username=? AND is_active=1",
                       (username,)).fetchone()
    conn.close()
    if row and verify_password(password, row[1]):
        st.session_state["staff_id"] = row[0]
        return True
    return False

def get_admin_password():
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return os.environ.get("ADMIN_PASSWORD", "admin123")

# =====================================================
# 9. QR & SMART ASSISTANT
# =====================================================
def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=8, border=3)
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#12304A", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def smart_assistant(question):
    text = normalize_text(question)
    if not text:
        return label("يرجى كتابة سؤالك لنتمكن من مساعدتك.", "Please type your question so we can assist you.")
    if any(x in text for x in ["كيف ارسل", "تقديم بلاغ", "طريقة البلاغ", "كيف اشتكي", "ارسل بلاغ", "اعمل بلاغ", "خطوات البلاغ"]):
        return label("لإرسال بلاغ جديد:\\n1. سجل دخولك أو أنشئ هوية رقمية.\\n2. افتح صفحة إرسال بلاغ.\\n3. اختر منطقتك واكتب وصف المشكلة.\\n4. سيوجه النظام البلاغ للجهة المختصة.",
                     "To submit a report: create or log in to your digital identity, open Submit Report, select your location, describe the issue, and submit.")
    if any(x in text for x in ["متابعة", "متابعه", "اين بلاغي", "حالة البلاغ", "تتبع", "بلاغاتي", "نتيجة البلاغ"]):
        return label("يمكنك متابعة بلاغاتك وإشعاراتها من صفحة خدماتي وبلاغاتي بعد تسجيل الدخول.",
                     "Track your reports and updates in My Services after logging in.")
    scores, matches = {}, {}
    for key, words in CATEGORY_KEYWORDS.items():
        found = [w for w in words if normalize_text(w) in text]
        if found:
            scores[key], matches[key] = len(found), found
    if scores:
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        first = ranked[0][0]
        first_info = DEPARTMENTS.get(first, DEPARTMENTS["Other"])
        first_name = first_info["ar"] if AR else first_info["en"]
        if len(ranked) > 1:
            second = ranked[1][0]
            second_info = DEPARTMENTS.get(second, DEPARTMENTS["Other"])
            second_name = second_info["ar"] if AR else second_info["en"]
            return label(f"سؤالك يتعلق بأكثر من موضوع: ({matches[first][0]}) يتبع لـ {first_name}، و({matches[second][0]}) يتبع لـ {second_name}. يُفضّل تقديم بلاغ منفصل لكل مشكلة.",
                         f"Your question covers more than one issue: {first_name} and {second_name}. Please submit separate reports.")
        return label(f"هذا الموضوع يقع تحت اختصاص {first_name} {first_info['icon']}. يمكنك تقديم بلاغ وسيوجهه النظام للجهة المختصة.",
                     f"This issue falls under {first_name}. Submit a report and WNS will route it to the responsible department.")
    return label("أنا مساعد النيل الأبيض الذكي 🌍. اسألني عن تقديم البلاغات أو متابعتها أو عن الكهرباء والمياه والطرق والنظافة والصحة والمرور والدفاع المدني.",
                 "I am the White Nile Smart Assistant. Ask about submitting or tracking reports and public services.")

# =====================================================
# 10. HEADER & NAVIGATION
# =====================================================
st.markdown("""<div class="wns-header">
<h1>🌍 النيل الأبيض الذكية</h1>
<h3>WHITE NILE SMART (WNS)</h3>
<p style="color:white">منصة التحول الرقمي والخدمات الحكومية الذكية</p>
</div>""", unsafe_allow_html=True)

pages = {
    "digital_identities": label("الهويات الرقمية", "Digital Identities"),
    "verify_identity": label("التحقق من الهوية", "Verify Identity"),
    "submit_report": label("إرسال بلاغ", "Submit Report"),
    "my_services": label("خدماتي وبلاغاتي", "My Services"),
    "dashboard": label("لوحة التحكم", "Dashboard"),
    "city_map": label("خريطة المدينة", "City Map"),
    "assistant": label("مساعد النيل الأبيض", "Smart Assistant"),
    "manage_reports": label("إدارة البلاغات والإشعارات", "Reports & Notifications")
}
if st.session_state.get("navigation_target") in pages:
    default_key = st.session_state.pop("navigation_target")
    default_index = list(pages).index(default_key)
else:
    default_index = 0
selected_page = st.sidebar.radio(label("القائمة الرئيسية", "Main Navigation"),
    list(pages), index=default_index, format_func=lambda key: pages[key])

# =====================================================
# 11. DASHBOARD
# =====================================================
if selected_page == "dashboard":
    st.header("📊 " + label("لوحة التحكم والتحليلات", "Dashboard"))
    reports, identities = load_reports(), load_identities()
    total = len(reports)
    pending = int((reports.status == "Pending").sum()) if total else 0
    resolved = int((reports.status == "Resolved").sum()) if total else 0
    urgent = int(reports.priority.isin(["Urgent", "Emergency"]).sum()) if total else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric(label("إجمالي البلاغات","Total Reports"), total)
    c2.metric(label("قيد الانتظار","Pending"), pending)
    c3.metric(label("تمت المعالجة","Resolved"), resolved)
    c4.metric(label("البلاغات العاجلة والطارئة","Urgent Reports"), urgent)
    if not reports.empty:
        left,right = st.columns(2)
        with left:
            st.subheader(label("البلاغات حسب النوع","Reports by Category"))
            chart = reports.category.value_counts().rename_axis("Category").reset_index(name="Count")
            chart["Category"] = chart.Category.apply(category_name)
            st.plotly_chart(px.pie(chart,names="Category",values="Count",hole=.45),use_container_width=True)
        with right:
            st.subheader(label("البلاغات حسب الحالة","Reports by Status"))
            chart = reports.status.value_counts().rename_axis("Status").reset_index(name="Count")
            chart["Status"] = chart.Status.apply(status_name)
            st.plotly_chart(px.bar(chart,x="Status",y="Count"),use_container_width=True)
        st.subheader(label("أحدث البلاغات","Recent Reports"))
        display = reports.head(10).copy()
        display["category"] = display.category.apply(category_name)
        display["priority"] = display.priority.apply(priority_name)
        display["status"] = display.status.apply(status_name)
        st.dataframe(display[["report_code","category","location","priority","status"]],use_container_width=True,hide_index=True)
    else:
        st.info(label("لا توجد بلاغات مسجلة.","No reports yet."))

# =====================================================
# 12. DIGITAL IDENTITIES
# =====================================================
elif selected_page == "digital_identities":
    st.header("🪪 " + label("إنشاء الهوية الرقمية","Digital Identity"))
    tab1,tab2 = st.tabs([label("إنشاء حساب","Create Account"),label("تسجيل الدخول","Login")])
    with tab1:
        with st.form("create_identity"):
            name = st.text_input(label("الاسم الكامل","Full Name"))
            email = st.text_input(label("البريد الإلكتروني","Email")).strip().lower()
            user_type = st.selectbox(label("نوع المستخدم","User Type"),["Citizen","Student","Employee","Other"])
            password = st.text_input(label("كلمة المرور","Password"),type="password")
            confirm = st.text_input(label("تأكيد كلمة المرور","Confirm Password"),type="password")
            submit = st.form_submit_button(label("إنشاء الهوية الرقمية","Create Identity"))
        if submit:
            if not name.strip() or not email or not password:
                st.error(label("يرجى تعبئة جميع الحقول.","Fill all fields."))
            elif len(password)<8:
                st.error(label("كلمة المرور يجب أن تكون 8 أحرف على الأقل.","Password must be at least 8 characters."))
            elif password != confirm:
                st.error(label("كلمتا المرور غير متطابقتين.","Passwords do not match."))
            else:
                conn = get_connection()
                try:
                    code = "WNS-" + str(uuid.uuid4())[:8].upper()
                    conn.execute("""INSERT INTO identities(identity_code,full_name,email,user_type,password_hash,created_at)
                        VALUES(?,?,?,?,?,?)""",(code,name.strip(),email,user_type,hash_password(password),NOW()))
                    conn.commit()
                    st.session_state["citizen_identity_code"] = code
                    st.session_state["citizen_identity_verified"] = True
                    st.success(label("تم إنشاء هويتك الرقمية بنجاح!","Identity created successfully!"))
                    st.code(code)
                    st.image(generate_qr(code).getvalue(),width=180)
                except sqlite3.IntegrityError:
                    st.error(label("هذا البريد مسجل بالفعل.","Email already exists."))
                finally:
                    conn.close()
    with tab2:
        with st.form("citizen_login"):
            email = st.text_input(label("البريد الإلكتروني","Email")).strip().lower()
            password = st.text_input(label("كلمة المرور","Password"),type="password")
            login = st.form_submit_button(label("تسجيل الدخول","Login"))
        if login:
            conn = get_connection()
            row = conn.execute("SELECT identity_code,password_hash FROM identities WHERE email=?",(email,)).fetchone()
            conn.close()
            if row and verify_password(password,row[1]):
                st.session_state["citizen_identity_code"] = row[0]
                st.session_state["citizen_identity_verified"] = True
                st.success(label("تم تسجيل الدخول بنجاح.","Login successful."))
                st.rerun()
            else:
                st.error(label("بيانات الدخول غير صحيحة.","Incorrect login details."))

# =====================================================
# 13. SUBMIT REPORT
# =====================================================
elif selected_page == "submit_report":
    st.header("📝 " + label("إرسال بلاغ جديد","Submit New Report"))
    identity = current_identity()
    if not identity:
        st.warning(label("يجب تسجيل الدخول أولاً.","Please log in first."))
        if st.button(label("الذهاب للهويات الرقمية","Go to Digital Identity")):
            st.session_state.navigation_target = "digital_identities"
            st.rerun()
    else:
        st.success(f"{label('مرحباً','Welcome')} {identity[1]}")
        st.info(label("سيتم ربط بلاغك بهويتك الرقمية وإرساله تلقائياً للجهة المختصة.",
                      "Your report will be linked to your identity and routed to the responsible department."))
        col_geo,col_status = st.columns([1,2])
        with col_geo:
            try:
                detected = streamlit_geolocation()
            except Exception:
                detected = None
        with col_status:
            if isinstance(detected,dict) and detected.get("latitude") is not None and detected.get("longitude") is not None:
                st.session_state.report_lat = float(detected["latitude"])
                st.session_state.report_lon = float(detected["longitude"])
                st.success(f"📍 {label('تم تحديد موقعك','Location detected')}: ({detected['latitude']:.4f}, {detected['longitude']:.4f})")
            else:
                st.caption(label("يمكنك تحديد موقعك تلقائياً أو اختيار المدينة وإدخال الإحداثيات.","You can detect your location or select a city and enter coordinates."))
        with st.form("new_report_form"):
            city = st.selectbox(label("المدينة / المحلية","City / Locality"),list(CITIES.keys()),index=list(CITIES).index("كوستي"))
            neighborhood = st.text_input(label("الحي أو الشارع","Neighborhood / Street"))
            landmark = st.text_input(label("أقرب معلم معروف (اختياري)","Nearest Landmark (optional)"))
            category = st.selectbox(label("نوع البلاغ","Report Category"),["Auto"]+list(DEPARTMENTS),
                format_func=lambda x: label("تصنيف تلقائي حسب وصف المشكلة","Automatic Classification") if x=="Auto" else category_name(x))
            description = st.text_area(label("وصف المشكلة بالتفصيل","Describe the Issue"),height=140)
            default_lat,default_lon = CITIES[city]
            latitude = st.number_input(label("خط العرض","Latitude"),value=float(st.session_state.get("report_lat",default_lat)),format="%.6f")
            longitude = st.number_input(label("خط الطول","Longitude"),value=float(st.session_state.get("report_lon",default_lon)),format="%.6f")
            submit = st.form_submit_button(label("🚀 إرسال البلاغ","Submit Report"))
        if submit:
            if not neighborhood.strip() or not description.strip():
                st.error(label("يرجى كتابة الحي ووصف البلاغ.","Enter neighborhood and report description."))
            else:
                predicted,priority,risk,_,keywords,critical = analyze_report(description)
                final_category = predicted if category=="Auto" else category
                department_id = get_department_id(final_category)
                dept = DEPARTMENTS[final_category]["ar" if AR else "en"]
                location = f"{city} - {neighborhood.strip()}"
                if landmark.strip():
                    location += f" - {label('بالقرب من','Near')} {landmark.strip()}"
                report_code = "REP-" + str(uuid.uuid4())[:8].upper()
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""INSERT INTO reports
                    (report_code,identity_code,category,description,location,latitude,longitude,
                     priority,status,created_at,department_id,department_name,city,neighborhood,
                     risk_score,is_critical,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (report_code,identity[0],final_category,description,location,latitude,longitude,
                     priority,"Pending",NOW(),department_id,dept,city,neighborhood.strip(),risk,int(critical),NOW()))
                report_id = cur.lastrowid
                conn.commit()
                conn.close()
                create_notification(report_id,"بلاغ جديد / New Report",
                    f"{label('بلاغ جديد من','New report from')} {identity[1]} | {label('الموقع','Location')}: {location} | {label('الأولوية','Priority')}: {priority_name(priority)}",
                    "department",department_id)
                create_notification(report_id,"بلاغ جديد يحتاج المتابعة",
                    f"{label('تم توجيه البلاغ','Report routed')} {report_code} {label('إلى','to')} {dept}","admin",None)
                notify_citizen(identity[0],report_id,"تم استلام بلاغك",
                    f"تم استلام البلاغ {report_code} وتوجيهه إلى {dept}.")
                st.success(label("تم إرسال البلاغ وتوجيهه للجهة المختصة بنجاح!","Report submitted and routed successfully!"))
                st.subheader(label("نتيجة التوجيه الذكي","Smart Routing Result"))
                st.write(f"**{label('رمز البلاغ','Report Code')}:** {report_code}")
                st.write(f"**{label('التصنيف','Category')}:** {category_name(final_category)}")
                st.write(f"**{label('الجهة المختصة','Department')}:** {dept}")
                st.write(f"**{label('الأولوية','Priority')}:** {priority_name(priority)}")
                st.write(f"**{label('درجة الخطورة التقديرية','Estimated Risk')}:** {risk}%")
                st.progress(risk/100)
                qr_data = generate_qr(report_code).getvalue()
                st.image(qr_data,width=180)
                st.download_button(label("تحميل رمز البلاغ QR","Download Report QR"),data=qr_data,file_name=f"{report_code}.png",mime="image/png")

# =====================================================
# 14. MY SERVICES
# =====================================================
elif selected_page == "my_services":
    st.header("👤 " + label("خدماتي وبلاغاتي","My Services"))
    identity = current_identity()
    if not identity:
        st.warning(label("يرجى تسجيل الدخول أولاً.","Please log in first."))
    else:
        st.success(f"{label('مرحباً','Welcome')} {identity[1]}")
        st.write(f"**{label('البريد الإلكتروني','Email')}:** {identity[2]}")
        st.write(f"**{label('رمز الهوية','Identity Code')}:** {identity[0]}")
        if st.button(label("تسجيل الخروج","Logout")):
            logout_citizen()
        conn = get_connection()
        reports = pd.read_sql_query("SELECT * FROM reports WHERE identity_code=? ORDER BY id DESC",conn,params=(identity[0],))
        notifications = pd.read_sql_query("SELECT * FROM citizen_notifications WHERE identity_code=? ORDER BY id DESC",conn,params=(identity[0],))
        conn.close()
        st.subheader(label("بلاغاتي","My Reports"))
        if reports.empty:
            st.info(label("لا توجد بلاغات حتى الآن.","No reports yet."))
        else:
            for _,row in reports.iterrows():
                with st.expander(f"{row['report_code']} | {category_name(row['category'])} | {status_name(row['status'])}"):
                    st.write(f"**{label('الوصف','Description')}:** {row['description']}")
                    st.write(f"**{label('الموقع','Location')}:** {row['location']}")
                    st.write(f"**{label('الجهة المختصة','Department')}:** {row['department_name']}")
                    st.write(f"**{label('الأولوية','Priority')}:** {priority_name(row['priority'])}")
                    st.write(f"**{label('الحالة','Status')}:** {status_name(row['status'])}")
                    st.write(f"**{label('التاريخ','Date')}:** {row['created_at']}")
        st.subheader("🔔 " + label("إشعاراتي","My Notifications"))
        if notifications.empty:
            st.info(label("لا توجد إشعارات.","No notifications."))
        else:
            for _,row in notifications.iterrows():
                st.info(f"**{row['title']}** — {row['message']}")
                st.caption(row["created_at"])

# =====================================================
# 15. VERIFY IDENTITY
# =====================================================
elif selected_page == "verify_identity":
    st.header("🔍 " + label("التحقق من الهوية الرقمية","Verify Identity"))
    code = st.text_input(label("رمز الهوية أو البريد الإلكتروني","Identity Code or Email"))
    if st.button(label("التحقق","Verify")):
        conn = get_connection()
        result = conn.execute("""SELECT identity_code,full_name,email,user_type,created_at
            FROM identities WHERE identity_code=? OR email=?""",(code.strip(),code.strip().lower())).fetchone()
        conn.close()
        if result:
            st.success(label("الهوية الرقمية صحيحة ومسجلة بالنظام.","Valid registered digital identity."))
            st.write(f"**{label('الاسم','Name')}:** {result[1]}")
            st.write(f"**Email:** {mask_email(result[2])}")
            st.write(f"**Identity Code:** {result[0]}")
            st.write(f"**{label('نوع المستفيد','User Type')}:** {result[3]}")
            st.write(f"**{label('تاريخ الإنشاء','Created At')}:** {result[4]}")
        else:
            st.error(label("الهوية غير موجودة.","Identity not found."))

# =====================================================
# 16. CITY MAP - SEPARATE TOOLTIP DATA FOR CITIES & REPORTS
# =====================================================
elif selected_page == "city_map":
    st.header("🗺️ " + label("خريطة بلاغات النيل الأبيض التفصيلية","White Nile Detailed Reports Map"))
    reports = load_reports()
    city_df = pd.DataFrame([{"name":city,"latitude":xy[0],"longitude":xy[1],"kind":"City"} for city,xy in CITIES.items()])
    layers = [pdk.Layer("ScatterplotLayer",data=city_df,get_position="[longitude, latitude]",
        get_radius=1200,get_fill_color=[7,155,145,180],pickable=True)]
    located = pd.DataFrame()
    if not reports.empty:
        located = reports.copy()
        located["latitude"] = pd.to_numeric(located["latitude"],errors="coerce")
        located["longitude"] = pd.to_numeric(located["longitude"],errors="coerce")
        located = located.dropna(subset=["latitude","longitude"])
        if not located.empty:
            located["category_display"] = located.category.apply(category_name)
            located["status_display"] = located.status.apply(status_name)
            located["priority_display"] = located.priority.apply(priority_name)
            layers.append(pdk.Layer("ScatterplotLayer",data=located,get_position="[longitude, latitude]",
                get_radius=350,get_fill_color=[232,180,74,220],pickable=True))
    deck = pdk.Deck(layers=layers,initial_view_state=pdk.ViewState(latitude=13.6,longitude=32.5,zoom=7),
        tooltip={"html":"<b>{name}</b><br/>{kind}","style":{"color":"white","backgroundColor":"#12304A"}})
    st.pydeck_chart(deck,use_container_width=True)
    st.caption(label("الخريطة تعرض المدن ومواقع البلاغات المسجلة ذات الإحداثيات.","Map displays cities and geolocated reports."))
    if not located.empty:
        st.subheader(label("📋 تفاصيل البلاغات المعروضة على الخريطة","Geolocated Reports Details"))
        for _,r in located.iterrows():
            with st.expander(f"📍 {r['report_code']} | {r['category_display']} | {r['status_display']}"):
                st.write(f"**{label('الوصف','Description')}:** {r['description']}")
                st.write(f"**{label('الموقع الجغرافي','Location')}:** {r['location']}")
                st.write(f"**{label('الإحداثيات','Coordinates')}:** {r['latitude']:.5f}, {r['longitude']:.5f}")
                st.write(f"**{label('الأولوية','Priority')}:** {r['priority_display']}")
                st.write(f"**{label('الجهة المختصة','Department')}:** {r['department_name']}")

# =====================================================
# 17. SMART ASSISTANT
# =====================================================
elif selected_page == "assistant":
    st.header("🤖 " + label("مساعد النيل الأبيض الذكي","White Nile Smart Assistant"))
    st.markdown("""<div class="wns-card"><h3>🌍 WNS Smart Assistant</h3>
    <p>مساعدك لمعرفة الخدمات الحكومية وطريقة تقديم البلاغات.</p></div>""",unsafe_allow_html=True)
    question = st.text_area(label("كيف يمكنني مساعدتك؟","How can I help you?"),
        placeholder=label("مثال: أين أبلغ عن انقطاع المياه أو انتشار الكوليرا؟","Example: Where can I report a water outage or disease outbreak?"))
    if st.button(label("إرسال السؤال","Send Question")):
        if question.strip():
            st.success(smart_assistant(question))

# =====================================================
# 18. REPORT MANAGEMENT & NOTIFICATIONS
# =====================================================
elif selected_page == "manage_reports":
    st.header("⚙️ " + label("الإدارة والجهات الحكومية","Administration & Departments"))
    staff = get_staff()
    if staff:
        staff_id,username,full_name,role,department_id,staff_city = staff
        # لا تعرض رسالة ترحيب للمدير العام أثناء فتح إدارة محددة.
        if not (role in ["admin", "governor"] and st.session_state.get("admin_department_view") is not None):
            st.success(f"{label('مرحباً','Welcome')} {full_name} | {role}")
        if st.button(label("تسجيل الخروج","Logout")):
            st.session_state.pop("staff_id",None)
            st.session_state.pop("root_admin",None)
            st.session_state.pop("admin_department_view",None)
            st.rerun()
        reports = load_reports()
        # المدير العام يستطيع فتح صفحة أي إدارة بضغطة، دون الدخول بحساب المسؤول أو تجاوز كلمة مروره.
        if role in ["admin", "governor"]:
            dept_conn = get_connection()
            departments_for_admin = pd.read_sql_query(
                "SELECT id, department_key, name_ar, name_en FROM departments ORDER BY id", dept_conn)
            dept_conn.close()
            current_department_view = st.session_state.get("admin_department_view")
            if current_department_view is None:
                st.subheader("🏢 " + label("الدخول السريع للإدارات", "Quick Access to Departments"))
                if not departments_for_admin.empty:
                    card_cols = st.columns(3)
                    for idx, dep_row in departments_for_admin.iterrows():
                        dep_name = dep_row["name_ar"] if AR else dep_row["name_en"]
                        dep_icon = DEPARTMENTS.get(dep_row["department_key"], {}).get("icon", "🏢")
                        with card_cols[idx % 3]:
                            if st.button(f"{dep_icon} {dep_name}", key=f"admin_open_department_{int(dep_row['id'])}", use_container_width=True):
                                st.session_state["admin_department_view"] = int(dep_row["id"])
                                st.rerun()
            else:
                selected_dep_row = departments_for_admin[departments_for_admin.id == current_department_view]
                if selected_dep_row.empty:
                    st.session_state.pop("admin_department_view", None)
                    st.rerun()
                dep_title = selected_dep_row.iloc[0]["name_ar"] if AR else selected_dep_row.iloc[0]["name_en"]
                st.header("🏢 " + dep_title)
                if st.button(label("⬅️ رجوع للإدارات", "⬅️ Back to Departments"), key="admin_show_all_departments"):
                    st.session_state.pop("admin_department_view", None)
                    st.rerun()
                reports = reports[reports.department_id == current_department_view]
        if role == "department":
            reports = reports[reports.department_id == department_id]
        elif role == "locality":
            if staff_city:
                reports = reports[reports.city == staff_city]
        elif role not in ["admin","governor"]:
            st.error(label("ليس لديك صلاحية.","Access denied."))
            st.stop()
        st.subheader("🔔 " + label("الإشعارات الذكية","Smart Notifications"))
        if role == "department":
            notifications = load_notifications(department_id)
        elif role in ["admin", "governor"] and st.session_state.get("admin_department_view") is not None:
            notifications = load_notifications(int(st.session_state["admin_department_view"]))
        else:
            notifications = load_notifications()
        if notifications.empty:
            st.info(label("لا توجد إشعارات.","No notifications."))
        else:
            unread = notifications[notifications.is_read == 0]
            read = notifications[notifications.is_read == 1]
            tab_unread,tab_read = st.tabs([f"{label('غير المقروءة','Unread')} ({len(unread)})",f"{label('المقروءة','Read')} ({len(read)})"])
            with tab_unread:
                if unread.empty:
                    st.info(label("جميع الإشعارات مقروءة.","All notifications read."))
                for _,n in unread.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**🔔 {n.title}**")
                        st.write(n.message)
                        if pd.notna(n.get("location")):
                            st.write(f"📍 {n.location}")
                        st.caption(n.created_at)
                        if st.button(label("تحديد كمقروء","Mark as Read"),key=f"read_{n.id}"):
                            conn=get_connection()
                            conn.execute("UPDATE admin_notifications SET is_read=1 WHERE id=?",(int(n.id),))
                            conn.commit()
                            conn.close()
                            st.rerun()
            with tab_read:
                if read.empty:
                    st.info(label("لا توجد إشعارات مقروءة.","No read notifications."))
                for _,n in read.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**✔️ {n.title}**")
                        st.write(n.message)
                        st.caption(n.created_at)
        st.divider()
        st.subheader("📋 " + label("البلاغات الموجهة إليك","Assigned Reports"))
        if reports.empty:
            st.info(label("لا توجد بلاغات.","No reports available."))
        else:
            for _,row in reports.iterrows():
                with st.expander(f"{row.report_code} | {category_name(row.category)} | {priority_name(row.priority)}"):
                    st.write(f"**{label('الوصف','Description')}:** {row.description}")
                    st.write(f"**{label('الموقع','Location')}:** {row.location}")
                    st.write(f"**{label('الجهة','Department')}:** {row.department_name}")
                    st.write(f"**{label('الأولوية','Priority')}:** {priority_name(row.priority)}")
                    st.write(f"**{label('الحالة','Status')}:** {status_name(row.status)}")
                    can_update = role in ["admin","governor","locality"] or (role=="department" and department_id==row.department_id)
                    if can_update:
                        states=["Pending","In Progress","Resolved"]
                        current = row.status if row.status in states else "Pending"
                        new_status=st.selectbox(label("تحديث حالة البلاغ","Update Status"),states,index=states.index(current),
                            format_func=status_name,key=f"status_{row.id}")
                        if st.button(label("حفظ التحديث","Save Update"),key=f"save_{row.id}"):
                            conn=get_connection()
                            conn.execute("UPDATE reports SET status=?,updated_at=? WHERE id=?",(new_status,NOW(),int(row.id)))
                            conn.commit()
                            conn.close()
                            notify_citizen(row.identity_code,int(row.id),"تحديث حالة البلاغ",
                                f"تم تحديث البلاغ {row.report_code} إلى {status_name(new_status)}")
                            create_notification(int(row.id),"تحديث حالة بلاغ",
                                f"تم تحديث حالة البلاغ {row.report_code} إلى {new_status}","admin",None)
                            st.success(label("تم تحديث البلاغ وإشعار المواطن.","Report updated and citizen notified."))
                            st.rerun()
        if role in ["admin","governor"] and st.session_state.get("admin_department_view") is None:
            st.divider()
            with st.expander("🏢 " + label("إدارة الجهات وحسابات المسؤولين","Departments & Staff Accounts Management"), expanded=False):
                tab_departments, tab_staff = st.tabs([label("🏛️ الجهات الحكومية","Government Departments"), label("👥 حسابات المسؤولين","Staff Accounts")])
                conn=get_connection()
                departments_df=pd.read_sql_query("SELECT * FROM departments ORDER BY id",conn)
                conn.close()
                with tab_departments:
                    st.subheader(label("الجهات الحكومية","Government Departments"))
                    st.dataframe(departments_df,use_container_width=True,hide_index=True)
                    with st.expander(label("⚡ إنشاء حسابات الجهات التلقائية","Generate Default Department Accounts")):
                        st.warning(label("الحسابات الافتراضية مخصصة للتجربة فقط. غيّر كلمات المرور قبل النشر الفعلي.",
                                         "Default accounts are for demonstration only. Change passwords before public deployment."))
                        if st.button(label("توليد الحسابات الافتراضية الآن","Generate Default Accounts Now"), key="generate_dept_accounts"):
                            count=seed_default_departments()
                            st.success(label(f"تم إنشاء {count} حسابات جديدة.","Created {count} new accounts."))
                            st.rerun()
                with tab_staff:
                    st.subheader(label("إنشاء وعرض حسابات المسؤولين","Create and View Staff Accounts"))
                    with st.expander(label("➕ إنشاء حساب مسؤول جهة","Create Department Account"), expanded=False):
                        with st.form("staff_creation"):
                            staff_name=st.text_input(label("اسم المسؤول","Staff Name"))
                            username_new=st.text_input(label("اسم المستخدم","Username"))
                            staff_password=st.text_input(label("كلمة المرور","Password"),type="password")
                            staff_role=st.selectbox(label("نوع الصلاحية","Role"),["department","locality"],
                                format_func=lambda x: "مسؤول جهة حكومية" if x=="department" and AR else ("مدير محلية" if x=="locality" and AR else x))
                            selected_department=st.selectbox(label("الجهة الحكومية","Department"),departments_df.id.tolist(),
                                format_func=lambda x: departments_df.loc[departments_df.id==x,"name_ar"].iloc[0] if AR else departments_df.loc[departments_df.id==x,"name_en"].iloc[0])
                            staff_city_new=st.selectbox(label("المحلية / المدينة","City"),[""]+list(CITIES))
                            create_user=st.form_submit_button(label("إنشاء الحساب","Create Account"))
                        if create_user:
                            if not staff_name.strip() or not username_new.strip() or len(staff_password)<8:
                                st.error(label("أدخل جميع البيانات، واجعل كلمة المرور 8 أحرف على الأقل.","Complete all fields and use at least 8 characters."))
                            else:
                                conn=get_connection()
                                try:
                                    conn.execute("""INSERT INTO staff_users(username,full_name,password_hash,role,department_id,city)
                                        VALUES(?,?,?,?,?,?)""",(username_new.strip(),staff_name.strip(),hash_password(staff_password),
                                        staff_role,selected_department,staff_city_new))
                                    conn.commit()
                                    st.success(label("تم إنشاء حساب المسؤول بنجاح.","Staff account created successfully."))
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error(label("اسم المستخدم مستخدم بالفعل.","Username already exists."))
                                finally:
                                    conn.close()
                    with st.expander(label("📋 عرض حسابات المسؤولين","View Staff Accounts"), expanded=True):
                        conn=get_connection()
                        staff_df=pd.read_sql_query("SELECT id,username,full_name,role,department_id,city,is_active FROM staff_users ORDER BY id DESC",conn)
                        conn.close()
                        st.dataframe(staff_df,use_container_width=True,hide_index=True)
                        active_staff=staff_df[staff_df.is_active==1]
                        if not active_staff.empty:
                            selected_staff=st.selectbox(label("اختر حساباً لتعطيله","Select Account to Disable"),active_staff.id.tolist(),key="disable_staff_select")
                            if st.button(label("تعطيل الحساب","Disable Account"),key="disable_staff_button"):
                                conn=get_connection()
                                conn.execute("UPDATE staff_users SET is_active=0 WHERE id=?",(int(selected_staff),))
                                conn.commit()
                                conn.close()
                                st.success(label("تم تعطيل الحساب.","Account disabled."))
                                st.rerun()
            st.divider()
            st.download_button(label("📥 تحميل جميع البلاغات CSV","Download Reports CSV"),
                data=reports.to_csv(index=False).encode("utf-8-sig"),
                file_name="WNS_Reports.csv",mime="text/csv")
    else:
        tab_admin,tab_dept=st.tabs([label("دخول الإدارة العامة","General Administration"),label("دخول الجهات الحكومية","Department Login")])
        with tab_admin:
            password=st.text_input(label("كلمة مرور مدير النظام","Administrator Password"),type="password")
            if st.button(label("دخول المدير","Admin Login")):
                expected=get_admin_password()
                if hmac.compare_digest(password,expected):
                    st.session_state.root_admin=True
                    st.session_state.staff_id=-999
                    st.rerun()
                else:
                    st.error(label("كلمة المرور غير صحيحة.","Incorrect password."))
            st.caption(label("للنشر، عيّن ADMIN_PASSWORD في Secrets أو متغيرات البيئة، ولا تعتمد كلمة المرور الافتراضية.",
                             "For deployment, set ADMIN_PASSWORD in Secrets or environment variables; do not use the fallback password."))
        with tab_dept:
            st.info(label("أنشئ حسابات الجهات أولاً من دخول الإدارة العامة، ثم استخدم بيانات الحساب الذي أنشأته.",
                          "Create department accounts from the administrator area first, then sign in with the credentials you created."))
            with st.expander(label("بيانات الحسابات الافتراضية التجريبية","Demo default account credentials")):
                st.warning(label("هذه الحسابات لا تعمل إلا بعد الضغط على توليد الحسابات الافتراضية. غيّر كلمات المرور قبل النشر.",
                                 "These accounts work only after generating defaults. Change passwords before deployment."))
                demo_lines = [
                    ("هيئة الكهرباء","electricity_user","electricity12345"),
                    ("هيئة المياه","water_user","water12345"),
                    ("إدارة النظافة","cleaning_user","cleaning12345"),
                    ("إدارة الطرق والجسور","roads_user","roads12345"),
                    ("إدارة الصرف الصحي","sewage_user","sewage12345"),
                    ("إدارة الصحة","health_user","health12345"),
                    ("إدارة البيئة","environment_user","environment12345"),
                    ("الدفاع المدني","emergency_user","emergency12345"),
                    ("شرطة المرور","traffic_user","traffic12345"),
                    ("إدارة التعليم","education_user","education12345"),
                    ("غرفة المتابعة","other_user","other12345")
                ]
                for dep,usr,pwd in demo_lines:
                    st.write(f"**{dep}:** `{usr}` / `{pwd}`")
            username_login=st.text_input(label("اسم المستخدم","Username"),key="dept_username_input")
            password_login=st.text_input(label("كلمة المرور","Password"),type="password",key="staff_password_login")
            if st.button(label("تسجيل الدخول","Login to Department")):
                if staff_login(username_login,password_login):
                    st.rerun()
                else:
                    st.error(label("اسم المستخدم أو كلمة المرور غير صحيحة.","Incorrect username or password."))

# =====================================================
# 19. FOOTER
# =====================================================
st.divider()
st.markdown("""<div style="text-align:center;padding:20px;color:#12304A;background:white;border-radius:12px;">
<h4>🌍 WHITE NILE SMART (WNS)</h4>
<p>النيل الأبيض الذكية | منصة التحول الرقمي المتكاملة</p>
<p style="color:#079B91;">Smart Government • AI • Digital Services • Smart Notifications</p>
</div>""",unsafe_allow_html=True)
