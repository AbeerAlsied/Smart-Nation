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
from datetime import datetime, timedelta

# =====================================================
# 1. CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="WNS | النيل الأبيض الذكية",
    page_icon="🌍",
    layout="wide"
)

DB_NAME = "smart_nation.db"

# =====================================================
# 2. DESIGN & THEME
# =====================================================

st.markdown("""
<style>

.stApp {
    background: #EAF4F8;
}

section[data-testid="stSidebar"] {
    background: #12304A;
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

h1, h2, h3, h4 {
    color: #12304A !important;
}

.stButton > button {
    background: linear-gradient(90deg,#079B91,#087E8B);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: bold;
}

.stButton > button:hover {
    background: #066B72;
    color: white;
}

.stDownloadButton > button {
    background: #12304A;
    color: white;
    border-radius: 10px;
}

div[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 14px;
    border-left: 5px solid #079B91;
    box-shadow: 0 3px 12px rgba(0,0,0,.05);
}

div[data-testid="stForm"] {
    background: white;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #DCEAF2;
}

div[data-testid="stExpander"] {
    background: white;
    border-radius: 12px;
}

.stProgress > div > div {
    background: #079B91;
}

div[data-testid="stAlert"] {
    border-radius: 12px;
}

.wns-header {
    background: linear-gradient(110deg,#12304A,#087E8B);
    padding: 25px;
    border-radius: 16px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
}

.wns-header h1 {
    color: white !important;
}

.wns-card {
    background: white;
    border-radius: 14px;
    padding: 20px;
    margin: 10px 0;
    border: 1px solid #DCEAF2;
}

.small-note {
    color: #607D8B;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# 3. TRANSLATIONS
# =====================================================

if "language" not in st.session_state:
    st.session_state.language = "العربية"

language = st.sidebar.selectbox(
    "🌐 اللغة / Language",
    ["العربية", "English"],
    index=0 if st.session_state.language == "العربية" else 1
)

st.session_state.language = language

AR = language == "العربية"

def label(ar, en):
    return ar if AR else en

# =====================================================
# 4. CATEGORIES & GOVERNMENT DEPARTMENTS
# =====================================================

DEPARTMENTS = {
    "Electricity": {
        "ar": "هيئة الكهرباء",
        "en": "Electricity Authority",
        "icon": "⚡"
    },
    "Water": {
        "ar": "هيئة مياه ولاية النيل الأبيض",
        "en": "White Nile Water Authority",
        "icon": "💧"
    },
    "Cleaning": {
        "ar": "إدارة النظافة بالمحلية",
        "en": "Local Cleaning Department",
        "icon": "🗑️"
    },
    "Roads": {
        "ar": "إدارة الطرق والجسور",
        "en": "Roads and Bridges Department",
        "icon": "🛣️"
    },
    "Sewage": {
        "ar": "إدارة الصرف الصحي",
        "en": "Sewage Department",
        "icon": "🚰"
    },
    "Health": {
        "ar": "إدارة الصحة",
        "en": "Health Department",
        "icon": "🏥"
    },
    "Environment": {
        "ar": "إدارة البيئة",
        "en": "Environment Department",
        "icon": "🌳"
    },
    "Emergency": {
        "ar": "الدفاع المدني",
        "en": "Civil Defense",
        "icon": "🚒"
    },
    "Traffic": {
        "ar": "شرطة المرور",
        "en": "Traffic Police",
        "icon": "🚦"
    },
    "Education": {
        "ar": "إدارة التعليم",
        "en": "Education Department",
        "icon": "🏫"
    },
    "Other": {
        "ar": "غرفة المتابعة العامة",
        "en": "General Follow-up Office",
        "icon": "📋"
    }
}

CITIES = {
    "كوستي": (13.16290, 32.66347),
    "ربك": (13.18087, 32.73999),
    "الدويم": (14.00120, 32.31160),
    "القطينة": (14.86480, 32.36680),
    "تندلتي": (13.01667, 31.86667),
    "مرابة": (12.35000, 32.18333),
    "الجزيرة أبا": (13.31930, 32.61320),
    "الكوة": (13.74630, 32.49960),
    "ود الزاكي": (14.46190, 32.20650)
}

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

# =====================================================
# 5. DATABASE
# =====================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def add_column_if_missing(conn, table, column, definition):
    existing = [
        row[1] for row in conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    ]

    if column not in existing:
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def initialize_database():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS identities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identity_code TEXT UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            user_type TEXT,
            password_hash TEXT DEFAULT '',
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_code TEXT UNIQUE,
            identity_code TEXT DEFAULT '',
            category TEXT,
            description TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            priority TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    # Upgrade old reports table safely
    new_columns = {
        "department_id": "INTEGER",
        "department_name": "TEXT DEFAULT ''",
        "city": "TEXT DEFAULT ''",
        "neighborhood": "TEXT DEFAULT ''",
        "risk_score": "INTEGER DEFAULT 0",
        "is_critical": "INTEGER DEFAULT 0",
        "updated_at": "TEXT DEFAULT ''"
    }

    for col, definition in new_columns.items():
        add_column_if_missing(conn, "reports", col, definition)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_key TEXT UNIQUE,
            name_ar TEXT,
            name_en TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS staff_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            full_name TEXT,
            password_hash TEXT,
            role TEXT,
            department_id INTEGER,
            city TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            recipient_type TEXT DEFAULT 'admin',
            department_id INTEGER
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS citizen_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identity_code TEXT,
            report_id INTEGER,
            title TEXT,
            message TEXT,
            created_at TEXT,
            is_read INTEGER DEFAULT 0
        )
    """)

    # Seed departments
    for key, item in DEPARTMENTS.items():
        conn.execute("""
            INSERT OR IGNORE INTO departments
            (department_key,name_ar,name_en)
            VALUES (?,?,?)
        """, (key, item["ar"], item["en"]))

    # Backward compatibility for old notifications
    add_column_if_missing(
        conn, "admin_notifications", "recipient_type",
        "TEXT DEFAULT 'admin'"
    )
    add_column_if_missing(
        conn, "admin_notifications", "department_id", "INTEGER"
    )

    conn.commit()
    conn.close()


initialize_database()


# =====================================================
# 6. PASSWORD SECURITY
# =====================================================

def hash_password(password):

    salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        200000
    )

    return salt + "$" + digest.hex()


def verify_password(password, stored):

    try:
        salt, expected = stored.split("$", 1)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            200000
        ).hex()

        return hmac.compare_digest(actual, expected)

    except Exception:
        return False


# =====================================================
# 7. TEXT NORMALIZATION & AI ENGINE
# =====================================================

def normalize_text(value):

    text = str(value or "").lower().strip()

    text = unicodedata.normalize("NFKC", text)

    text = re.sub(r"[ً-ٰٟ]", "", text)

    text = text.replace("ـ", "")

    text = text.translate(
        str.maketrans({
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ى": "ي",
            "ة": "ه"
        })
    )

    return re.sub(r"\s+", " ", text)


CATEGORY_KEYWORDS = {

    "Electricity": [
        "كهرباء", "كهربا", "النور", "تيار",
        "انارة", "عمود كهرباء", "سلك", "اسلاك",
        "لمبات", "ضلمه", "electricity", "power",
        "outage", "electric"
    ],

    "Water": [
        "مياه", "موية", "مويا", "مويه",
        "حنفيه", "حنفية", "ماسوره", "انبوب",
        "تسريب", "تسرب مياه", "انقطاع المياه",
        "water", "leak", "pipe"
    ],

    "Cleaning": [
        "نفايات", "قمامه", "زباله", "زبل",
        "وسخ", "اوساخ", "كوشه", "نظافه",
        "مخلفات", "روائح", "garbage",
        "waste", "trash"
    ],

    "Roads": [
        "شارع", "شوارع", "حفره", "طريق",
        "اسفلت", "مكسر", "محفر", "مطب",
        "رصيف", "road", "pothole", "street"
    ],

    "Sewage": [
        "صرف صحي", "مجاري", "طفح",
        "مجرى", "بالوعه", "انسداد المجاري",
        "sewage", "drainage"
    ],

    "Health": [
        "مستشفى", "مركز صحي", "مرض",
        "عياده", "صحه", "ادويه",
        "hospital", "health", "clinic"
    ],

    "Environment": [
        "تلوث", "بيئه", "حرق نفايات",
        "دخان المصانع", "تلوث الهواء",
        "pollution", "environment"
    ],

    "Emergency": [
        "حريق", "نار", "دخان", "انفجار",
        "انهيار", "غرق", "فيضان",
        "حادث خطير", "emergency", "fire",
        "explosion"
    ],

    "Traffic": [
        "مرور", "حادث مروري", "اشاره مرور",
        "ازدحام", "اختناق مروري", "اشارات",
        "traffic", "accident"
    ],

    "Education": [
        "مدرسه", "مدارس", "تعليم",
        "فصل دراسي", "معلم", "مدرس",
        "school", "education"
    ]
}


CRITICAL_TERMS = [
    "حريق", "نار", "انفجار", "صعق",
    "سلك عريان", "سلك مكشوف", "سلك واقع",
    "عمود واقع", "عمود ساقط", "انهيار",
    "غرق", "فيضان", "تسمم",
    "fire", "explosion", "emergency"
]

URGENT_TERMS = [
    "انقطاع المياه", "انقطاع الكهرباء",
    "المويه قاطعه", "النور قاطع",
    "ماسوره مكسوره", "طفح المجاري",
    "تسرب كبير", "حادث",
    "no water", "no electricity"
]

IMPORTANT_TERMS = [
    "مدرسه", "مستشفى", "مركز صحي",
    "الحي بالكامل", "كل الحي",
    "شارع رئيسي", "عدد كبير",
    "hospital", "whole neighborhood"
]


def analyze_report(description):

    text = normalize_text(description)

    scores = {}

    detected = []

    for category, words in CATEGORY_KEYWORDS.items():

        matched = [
            word for word in words
            if normalize_text(word) in text
        ]

        scores[category] = len(matched)

        detected.extend(matched)

    best_category = max(
        scores,
        key=scores.get
    )

    if scores[best_category] == 0:
        best_category = "Other"

    critical = any(
        normalize_text(x) in text
        for x in CRITICAL_TERMS
    )

    urgent = any(
        normalize_text(x) in text
        for x in URGENT_TERMS
    )

    important = any(
        normalize_text(x) in text
        for x in IMPORTANT_TERMS
    )

    if critical:
        priority = "Emergency"
        risk = 95

    elif urgent:
        priority = "Urgent"
        risk = 75

    elif important:
        priority = "Important"
        risk = 50

    else:
        priority = "Normal"
        risk = 20

    return (
        best_category,
        priority,
        risk,
        DEPARTMENTS[best_category]["ar"],
        detected[:10],
        critical
    )


# =====================================================
# 8. DATABASE HELPERS
# =====================================================

def get_department_id(category):

    conn = get_connection()

    row = conn.execute("""
        SELECT id FROM departments
        WHERE department_key = ?
    """, (category,)).fetchone()

    conn.close()

    return row[0] if row else None


def load_reports():

    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT * FROM reports
        ORDER BY
        CASE priority
            WHEN 'Emergency' THEN 1
            WHEN 'Urgent' THEN 2
            WHEN 'Important' THEN 3
            ELSE 4
        END,
        id DESC
    """, conn)

    conn.close()

    return df


def load_identities():

    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT id,identity_code,full_name,email,user_type,created_at
        FROM identities ORDER BY id DESC
    """, conn)

    conn.close()

    return df


def create_notification(
    report_id,
    title,
    message,
    recipient_type="admin",
    department_id=None
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO admin_notifications
        (report_id,title,message,created_at,is_read,
         recipient_type,department_id)
        VALUES (?,?,?,?,0,?,?)
    """, (
        report_id,
        title,
        message,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        recipient_type,
        department_id
    ))

    conn.commit()
    conn.close()


def notify_citizen(identity_code, report_id, title, message):

    conn = get_connection()

    conn.execute("""
        INSERT INTO citizen_notifications
        (identity_code,report_id,title,message,created_at)
        VALUES (?,?,?,?,?)
    """, (
        identity_code,
        report_id,
        title,
        message,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def load_notifications(department_id=None):

    conn = get_connection()

    if department_id is None:

        df = pd.read_sql_query("""
            SELECT n.*,r.category,r.location,r.priority,r.status
            FROM admin_notifications n
            LEFT JOIN reports r ON n.report_id=r.id
            WHERE n.recipient_type='admin'
            ORDER BY n.id DESC
        """, conn)

    else:

        df = pd.read_sql_query("""
            SELECT n.*,r.category,r.location,r.priority,r.status
            FROM admin_notifications n
            LEFT JOIN reports r ON n.report_id=r.id
            WHERE n.department_id=?
            ORDER BY n.id DESC
        """, conn, params=(department_id,))

    conn.close()

    return df


# =====================================================
# 9. IDENTITY MANAGEMENT & PRIVACY
# =====================================================

def current_identity():

    code = st.session_state.get("citizen_identity_code")

    if not code:
        return None

    conn = get_connection()

    row = conn.execute("""
        SELECT identity_code,full_name,email,user_type,created_at
        FROM identities
        WHERE identity_code=?
    """, (code,)).fetchone()

    conn.close()

    return row


def logout_citizen():

    st.session_state.pop("citizen_identity_code", None)
    st.session_state.pop("citizen_identity_verified", None)

    st.rerun()


def mask_email(email):

    if not email or "@" not in email:
        return email

    parts = email.split("@")
    user, domain = parts[0], parts[1]

    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + "*" * (len(user) - 2) + user[-1]

    return f"{masked_user}@{domain}"


# =====================================================
# 10. STAFF LOGIN & PERMISSIONS
# =====================================================


def seed_default_departments():
    conn = get_connection()
    depts = conn.execute("SELECT id, department_key, name_ar FROM departments").fetchall()
    
    created_count = 0
    for dept_id, key, name in depts:
        username = f"{key.lower()}_user"
        exists = conn.execute("SELECT id FROM staff_users WHERE username=?", (username,)).fetchone()
        if not exists:
            default_pass = hash_password(f"{key.lower()}12345")
            conn.execute("""
                INSERT INTO staff_users (username, full_name, password_hash, role, department_id, city, is_active)
                VALUES (?, ?, ?, 'department', ?, '', 1)
            """, (username, f"مسؤول {name}", default_pass, dept_id))
            created_count += 1
            
    conn.commit()
    conn.close()
    return created_count


def get_staff():

    user_id = st.session_state.get("staff_id")

    # Virtual root administrator
    if user_id == -999 and st.session_state.get("root_admin"):
        return (
            -999,
            "admin",
            "مدير النظام",
            "admin",
            None,
            ""
        )

    if not user_id:
        return None

    conn = get_connection()

    row = conn.execute("""
        SELECT id,username,full_name,role,department_id,city
        FROM staff_users
        WHERE id=? AND is_active=1
    """, (user_id,)).fetchone()

    conn.close()

    return row


def staff_login(username, password):

    conn = get_connection()

    row = conn.execute("""
        SELECT id, password_hash
        FROM staff_users
        WHERE username=? AND is_active=1
    """, (username,)).fetchone()

    conn.close()

    if row:
        user_id, stored_hash = row

        # دعم التشفير الآمن والنص العادي للطوارئ
        if verify_password(password, stored_hash) or stored_hash == password:

            st.session_state["staff_id"] = user_id

            return True

    return False


def get_admin_password():

    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return os.environ.get("ADMIN_PASSWORD", "admin123")


# =====================================================
# 11. QR GENERATOR
# =====================================================

def generate_qr(data):

    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=3
    )

    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="#12304A",
        back_color="white"
    )

    buffer = io.BytesIO()

    image.save(buffer, format="PNG")

    buffer.seek(0)

    return buffer


# =====================================================
# 12. CATEGORY TRANSLATION
# =====================================================

def category_name(category):

    item = DEPARTMENTS.get(category, DEPARTMENTS["Other"])

    return item["ar"] if AR else item["en"]


def priority_name(priority):

    return PRIORITIES.get(priority, priority)


def status_name(status):

    return STATUSES.get(status, status)


# =====================================================
# 13. SMART ASSISTANT
# =====================================================

def smart_assistant(question):

    text = normalize_text(question)

    if any(x in text for x in ["كيف ارسل", "تقديم بلاغ", "ارسل بلاغ", "submit report"]):

        return label(
            "يمكنك إنشاء حساب رقمي أولاً، ثم الدخول إلى صفحة إرسال بلاغ واختيار المدينة ووصف المشكلة وإرسالها.",
            "Create an account first, then open Submit Report, select your city, describe the issue and submit it."
        )

    if any(x in text for x in ["مياه", "موية", "ماسوره", "water"]):

        return label(
            "بلاغات المياه يتم توجيهها تلقائياً إلى هيئة مياه ولاية النيل الأبيض.",
            "Water reports are routed to the White Nile Water Authority."
        )

    if any(x in text for x in ["كهرباء", "النور", "electricity"]):

        return label(
            "بلاغات الكهرباء يتم توجيهها إلى هيئة الكهرباء.",
            "Electricity reports are routed to the Electricity Authority."
        )

    if any(x in text for x in ["نظافه", "نفايات", "كوشه", "garbage"]):

        return label(
            "بلاغات النظافة يتم توجيهها إلى إدارة النظافة بالمحلية.",
            "Cleaning reports are routed to the local cleaning department."
        )

    if any(x in text for x in ["بلاغي", "متابعه", "حاله البلاغ", "track"]):

        return label(
            "يمكنك متابعة حالة بلاغاتك من صفحة خدماتي وبلاغاتي بعد تسجيل الدخول.",
            "Track your reports through My Services after logging in."
        )

    if any(x in text for x in ["جهات", "مسؤول", "department"]):

        return label(
            "تقوم المنصة بربط كل نوع بلاغ بالجهة الحكومية المختصة به تلقائياً.",
            "The platform automatically routes each report to its responsible department."
        )

    return label(
        "مرحباً بك في مساعد النيل الأبيض الذكي. يمكنني مساعدتك في معرفة الخدمات وطريقة تقديم البلاغات والجهات المختصة.",
        "Welcome to White Nile Smart Assistant. I can help you understand services, submit reports and identify responsible departments."
    )


# =====================================================
# 14. HEADER
# =====================================================

st.markdown("""
<div class="wns-header">
    <h1>🌍 النيل الأبيض الذكية</h1>
    <h3 style="color:white !important;">
        WHITE NILE SMART (WNS)
    </h3>
    <p>منصة التحول الرقمي والخدمات الحكومية الذكية</p>
</div>
""", unsafe_allow_html=True)


# =====================================================
# 15. NAVIGATION & PAGE REDIRECTION FIX
# =====================================================

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

# Handle pending redirection target seamlessly across re-renders
if "navigation_target" in st.session_state and st.session_state["navigation_target"] in pages:
    default_key = st.session_state.pop("navigation_target")
    default_index = list(pages.keys()).index(default_key)
else:
    default_index = 0

selected_page = st.sidebar.radio(
    label("القائمة الرئيسية", "Main Navigation"),
    list(pages.keys()),
    index=default_index,
    format_func=lambda x: pages[x]
)

# =====================================================
# 16. DASHBOARD
# =====================================================

if selected_page == "dashboard":

    st.header("📊 " + label("لوحة التحكم والتحليلات", "Dashboard"))

    reports = load_reports()
    identities = load_identities()

    total = len(reports)

    pending = len(reports[reports.status == "Pending"]) if total else 0

    resolved = len(reports[reports.status == "Resolved"]) if total else 0

    urgent = len(
        reports[reports.priority.isin(["Urgent", "Emergency"])]
    ) if total else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(label("إجمالي البلاغات", "Total Reports"), total)

    c2.metric(label("قيد الانتظار", "Pending"), pending)

    c3.metric(label("تمت المعالجة", "Resolved"), resolved)

    c4.metric(label("البلاغات العاجلة والطارئة", "Urgent Reports"), urgent)

    st.divider()

    if not reports.empty:

        left, right = st.columns(2)

        with left:

            st.subheader(label("البلاغات حسب النوع", "Reports by Category"))

            chart = reports["category"].value_counts().reset_index()

            chart.columns = ["Category", "Count"]

            chart["Category"] = chart["Category"].apply(category_name)

            st.plotly_chart(
                px.pie(
                    chart,
                    names="Category",
                    values="Count",
                    hole=.45
                ),
                use_container_width=True
            )

        with right:

            st.subheader(label("البلاغات حسب الحالة", "Reports by Status"))

            chart = reports["status"].value_counts().reset_index()

            chart.columns = ["Status", "Count"]

            chart["Status"] = chart["Status"].apply(status_name)

            st.plotly_chart(
                px.bar(chart, x="Status", y="Count"),
                use_container_width=True
            )

        st.subheader(label("أحدث البلاغات", "Recent Reports"))

        display = reports.head(10).copy()

        display["category"] = display["category"].apply(category_name)

        display["priority"] = display["priority"].apply(priority_name)

        display["status"] = display["status"].apply(status_name)

        st.dataframe(
            display[
                ["report_code", "category", "location", "priority", "status"]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(label("لا توجد بلاغات مسجلة.", "No reports yet."))

# =====================================================
# 17. DIGITAL IDENTITIES
# =====================================================

elif selected_page == "digital_identities":

    st.header("🪪 " + label("إنشاء الهوية الرقمية", "Digital Identity"))

    tab1, tab2 = st.tabs([
        label("إنشاء حساب", "Create Account"),
        label("تسجيل الدخول", "Login")
    ])

    with tab1:

        with st.form("create_identity"):

            name = st.text_input(label("الاسم الكامل", "Full Name"))

            email = st.text_input(label("البريد الإلكتروني", "Email")).strip().lower()

            user_type = st.selectbox(
                label("نوع المستخدم", "User Type"),
                ["Citizen", "Student", "Employee", "Other"]
            )

            password = st.text_input(
                label("كلمة المرور", "Password"),
                type="password"
            )

            confirm = st.text_input(
                label("تأكيد كلمة المرور", "Confirm Password"),
                type="password"
            )

            submit = st.form_submit_button(
                label("إنشاء الهوية الرقمية", "Create Identity")
            )

        if submit:

            if not name.strip() or not email or not password:

                st.error(label("يرجى تعبئة جميع الحقول.", "Fill all fields."))

            elif len(password) < 8:

                st.error(label("كلمة المرور يجب أن تكون 8 أحرف على الأقل.", "Password must be at least 8 characters."))

            elif password != confirm:

                st.error(label("كلمتا المرور غير متطابقتين.", "Passwords do not match."))

            else:

                conn = get_connection()

                try:

                    identity_code = "WNS-" + str(uuid.uuid4())[:8].upper()

                    conn.execute("""
                        INSERT INTO identities
                        (identity_code,full_name,email,user_type,password_hash,created_at)
                        VALUES (?,?,?,?,?,?)
                    """, (
                        identity_code,
                        name.strip(),
                        email,
                        user_type,
                        hash_password(password),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))

                    conn.commit()

                    st.session_state["citizen_identity_code"] = identity_code

                    st.session_state["citizen_identity_verified"] = True

                    st.success(label("تم إنشاء هويتك الرقمية بنجاح!", "Identity created successfully!"))

                    st.code(identity_code)

                    st.image(generate_qr(identity_code).getvalue(), width=180)

                except sqlite3.IntegrityError:

                    st.error(label("هذا البريد مسجل بالفعل.", "Email already exists."))

                finally:

                    conn.close()

    with tab2:

        with st.form("citizen_login"):

            email = st.text_input(label("البريد الإلكتروني", "Email")).strip().lower()

            password = st.text_input(
                label("كلمة المرور", "Password"),
                type="password"
            )

            login = st.form_submit_button(
                label("تسجيل الدخول", "Login")
            )

        if login:

            conn = get_connection()

            row = conn.execute("""
                SELECT identity_code,password_hash
                FROM identities WHERE email=?
            """, (email,)).fetchone()

            conn.close()

            if row and verify_password(password, row[1]):

                st.session_state["citizen_identity_code"] = row[0]

                st.session_state["citizen_identity_verified"] = True

                st.success(label("تم تسجيل الدخول بنجاح.", "Login successful."))

                st.rerun()

            else:

                st.error(label("بيانات الدخول غير صحيحة.", "Incorrect login details."))


# =====================================================
# 18. SUBMIT REPORT
# =====================================================

elif selected_page == "submit_report":

    st.header("📝 " + label("إرسال بلاغ جديد", "Submit New Report"))

    identity = current_identity()

    if not identity:

        st.warning(label("يجب تسجيل الدخول أولاً.", "Please log in first."))

        if st.button(label("الذهاب للهويات الرقمية", "Go to Digital Identity")):

            st.session_state["navigation_target"] = "digital_identities"

            st.rerun()

    else:

        st.success(f"{label('مرحباً', 'Welcome')} {identity[1]}")

        st.info(label(
            "سيتم ربط بلاغك بهويتك الرقمية وإرساله تلقائياً للجهة المختصة.",
            "Your report will be linked to your identity and routed to the responsible department."
        ))

        # Geolocation button & detection with clear status UI
        col_geo, col_status = st.columns([1, 2])
        with col_geo:
            try:
                detected = streamlit_geolocation()
            except Exception:
                detected = None

        with col_status:
            if isinstance(detected, dict) and detected.get("latitude") is not None:
                st.session_state["report_lat"] = float(detected["latitude"])
                st.session_state["report_lon"] = float(detected["longitude"])
                st.success(f"📍 {label('تم تحديد موقعك الجغرافي تلقائياً', 'Location detected automatically')}: ({detected['latitude']:.4f}, {detected['longitude']:.4f})")
            else:
                st.caption(label("💡 اضغط على الزر أعلاه لتحديد موقعك الجغرافي بدقة، أو اختر المدينة أدناه.", "Click the button above to auto-detect location, or select a city below."))

        default_city = "كوستي"

        with st.form("new_report_form"):

            city = st.selectbox(
                label("المدينة / المحلية", "City / Locality"),
                list(CITIES.keys())
            )

            neighborhood = st.text_input(
                label("الحي أو الشارع", "Neighborhood / Street")
            )

            landmark = st.text_input(
                label("أقرب معلم معروف (اختياري)", "Nearest Landmark (optional)")
            )

            category_options = ["Auto"] + list(DEPARTMENTS.keys())

            category = st.selectbox(
                label("نوع البلاغ", "Report Category"),
                category_options,
                format_func=lambda x: (
                    label("تصنيف تلقائي حسب وصف المشكلة", "Automatic Classification")
                    if x == "Auto" else category_name(x)
                )
            )

            description = st.text_area(
                label("وصف المشكلة بالتفصيل", "Describe the Issue"),
                height=140
            )

            default_lat, default_lon = CITIES[city]

            latitude = st.number_input(
                label("خط العرض", "Latitude"),
                value=float(st.session_state.get("report_lat", default_lat)),
                format="%.6f"
            )

            longitude = st.number_input(
                label("خط الطول", "Longitude"),
                value=float(st.session_state.get("report_lon", default_lon)),
                format="%.6f"
            )

            submit = st.form_submit_button(
                label("🚀 إرسال البلاغ", "Submit Report")
            )

        if submit:

            if not neighborhood.strip() or not description.strip():

                st.error(label("يرجى كتابة الحي ووصف البلاغ.", "Enter neighborhood and report description."))

            else:

                predicted, priority, risk, dept, keywords, critical = analyze_report(description)

                final_category = predicted if category == "Auto" else category

                # Respect manually selected category
                if category != "Auto":
                    dept = DEPARTMENTS[final_category]["ar"]

                department_id = get_department_id(final_category)

                location = f"{city} - {neighborhood}"

                if landmark.strip():
                    location += f" - بالقرب من {landmark.strip()}"

                report_code = "REP-" + str(uuid.uuid4())[:8].upper()

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn = get_connection()

                cur = conn.cursor()

                cur.execute("""
                    INSERT INTO reports
                    (report_code,identity_code,category,description,
                     location,latitude,longitude,priority,status,
                     created_at,department_id,department_name,
                     city,neighborhood,risk_score,is_critical,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    report_code,
                    identity[0],
                    final_category,
                    description,
                    location,
                    latitude,
                    longitude,
                    priority,
                    "Pending",
                    now,
                    department_id,
                    dept,
                    city,
                    neighborhood,
                    risk,
                    int(critical),
                    now
                ))

                report_id = cur.lastrowid

                conn.commit()

                conn.close()

                # Smart notification to department
                create_notification(
                    report_id,
                    "بلاغ جديد / New Report",
                    f"بلاغ جديد من {identity[1]} | الموقع: {location} | الأولوية: {priority_name(priority)}",
                    "department",
                    department_id
                )

                # Notify general administration
                create_notification(
                    report_id,
                    "بلاغ جديد يحتاج المتابعة",
                    f"تم توجيه البلاغ {report_code} إلى {dept}",
                    "admin",
                    None
                )

                notify_citizen(
                    identity[0],
                    report_id,
                    "تم استلام بلاغك",
                    f"تم استلام البلاغ {report_code} وتوجيهه إلى {dept}."
                )

                st.success(label("تم إرسال البلاغ وتوجيهه للجهة المختصة بنجاح!", "Report submitted and routed successfully!"))

                st.subheader(label("نتيجة التوجيه الذكي", "Smart Routing Result"))

                st.write(f"**{label('رمز البلاغ','Report Code')}:** {report_code}")

                st.write(f"**{label('التصنيف','Category')}:** {category_name(final_category)}")

                st.write(f"**{label('الجهة المختصة','Department')}:** {dept}")

                st.write(f"**{label('الأولوية','Priority')}:** {priority_name(priority)}")

                st.write(f"**{label('درجة الخطورة التقديرية','Estimated Risk')}:** {risk}%")

                st.progress(risk / 100)

                st.image(generate_qr(report_code).getvalue(), width=180)

                st.download_button(
                    label("تحميل رمز البلاغ QR", "Download Report QR"),
                    data=generate_qr(report_code).getvalue(),
                    file_name=f"{report_code}.png",
                    mime="image/png"
                )


# =====================================================
# 19. MY SERVICES
# =====================================================

elif selected_page == "my_services":

    st.header("👤 " + label("خدماتي وبلاغاتي", "My Services"))

    identity = current_identity()

    if not identity:

        st.warning(label("يرجى تسجيل الدخول أولاً.", "Please log in first."))

    else:

        st.success(f"{label('مرحباً', 'Welcome')} {identity[1]}")

        st.write(f"**{label('البريد الإلكتروني','Email')}:** {identity[2]}")

        st.write(f"**{label('رمز الهوية','Identity Code')}:** {identity[0]}")

        if st.button(label("تسجيل الخروج", "Logout")):
            logout_citizen()

        st.divider()

        conn = get_connection()

        reports = pd.read_sql_query("""
            SELECT * FROM reports
            WHERE identity_code=?
            ORDER BY id DESC
        """, conn, params=(identity[0],))

        notifications = pd.read_sql_query("""
            SELECT * FROM citizen_notifications
            WHERE identity_code=?
            ORDER BY id DESC
        """, conn, params=(identity[0],))

        conn.close()

        st.subheader(label("بلاغاتي", "My Reports"))

        if reports.empty:

            st.info(label("لا توجد بلاغات حتى الآن.", "No reports yet."))

        else:

            for _, row in reports.iterrows():

                with st.expander(
                    f"{row['report_code']} | {category_name(row['category'])} | {status_name(row['status'])}"
                ):

                    st.write(f"**{label('الوصف','Description')}:** {row['description']}")

                    st.write(f"**{label('الموقع','Location')}:** {row['location']}")

                    st.write(f"**{label('الجهة المختصة','Department')}:** {row['department_name']}")

                    st.write(f"**{label('الأولوية','Priority')}:** {priority_name(row['priority'])}")

                    st.write(f"**{label('الحالة','Status')}:** {status_name(row['status'])}")

                    st.write(f"**{label('التاريخ','Date')}:** {row['created_at']}")

        st.divider()

        st.subheader(label("🔔 إشعاراتي", "🔔 My Notifications"))

        if notifications.empty:

            st.info(label("لا توجد إشعارات.", "No notifications."))

        else:

            for _, row in notifications.iterrows():

                st.info(f"**{row['title']}** — {row['message']}")

                st.caption(row["created_at"])


# =====================================================
# 20. VERIFY IDENTITY & PRIVACY PROTECTION
# =====================================================

elif selected_page == "verify_identity":

    st.header("🔍 " + label("التحقق من الهوية الرقمية", "Verify Identity"))

    code = st.text_input(label("رمز الهوية أو البريد الإلكتروني", "Identity Code or Email"))

    if st.button(label("التحقق", "Verify")):

        conn = get_connection()

        result = conn.execute("""
            SELECT identity_code,full_name,email,user_type,created_at
            FROM identities
            WHERE identity_code=? OR email=?
        """, (code.strip(), code.strip().lower())).fetchone()

        conn.close()

        if result:

            st.success(label("الهوية الرقمية صحيحة ومسجلة بالنظام.", "Valid registered digital identity."))

            st.write(f"**{label('الاسم','Name')}:** {result[1]}")

            # Masked email to protect citizen privacy
            st.write(f"**Email:** {mask_email(result[2])}")

            st.write(f"**Identity Code:** {result[0]}")

            st.write(f"**{label('نوع المستفيد','User Type')}:** {result[3]}")

            st.write(f"**{label('تاريخ الإنشاء','Created At')}:** {result[4]}")

        else:

            st.error(label("الهوية غير موجودة.", "Identity not found."))


# =====================================================
# 21. CITY MAP WITH REPORT DETAILS
# =====================================================

elif selected_page == "city_map":

    st.header("🗺️ " + label("خريطة بلاغات النيل الأبيض التفصيلية", "White Nile Detailed Reports Map"))

    reports = load_reports()

    city_df = pd.DataFrame([
        {
            "name": city,
            "latitude": coord[0],
            "longitude": coord[1],
            "kind": "City"
        }
        for city, coord in CITIES.items()
    ])

    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=city_df,
            get_position="[longitude, latitude]",
            get_radius=1200,
            get_fill_color=[7, 155, 145, 180],
            pickable=True
        )
    ]

    located = pd.DataFrame()

    if not reports.empty:

        located = reports.dropna(
            subset=["latitude", "longitude"]
        ).copy()

        if not located.empty:

            located["latitude"] = pd.to_numeric(
                located["latitude"], errors="coerce"
            )

            located["longitude"] = pd.to_numeric(
                located["longitude"], errors="coerce"
            )

            located = located.dropna(
                subset=["latitude", "longitude"]
            )

            if not located.empty:

                located["category_ar"] = located["category"].apply(category_name)
                located["status_ar"] = located["status"].apply(status_name)
                located["priority_ar"] = located["priority"].apply(priority_name)

                layers.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=located,
                        get_position="[longitude, latitude]",
                        get_radius=350,
                        get_fill_color=[232, 180, 74, 220],
                        pickable=True
                    )
                )

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=13.16,
            longitude=32.66,
            zoom=7
        ),
        tooltip={
            "html": "<b>{report_code}</b><br/><b>التصنيف:</b> {category_ar}<br/><b>الحالة:</b> {status_ar}<br/><b>الموقع:</b> {location}",
            "style": {"color": "white", "backgroundColor": "#12304A"}
        }
    )

    st.pydeck_chart(deck, use_container_width=True)

    st.caption(label(
        "الخريطة تعرض المدن ومواقع البلاغات المسجلة ذات الإحداثيات.",
        "Map displays cities and geolocated reports."
    ))

    # Detailed list of geolocated reports below map
    if not located.empty:

        st.subheader(label("📋 تفاصيل البلاغات المعروضة على الخريطة", "Geolocated Reports Details"))

        for _, r in located.iterrows():

            with st.expander(f"📍 {r['report_code']} | {r['category_ar']} | {r['status_ar']}"):

                st.write(f"**{label('الوصف','Description')}:** {r['description']}")
                st.write(f"**{label('الموقع الجغرافي','Location')}:** {r['location']}")
                st.write(f"**{label('الإحداثيات','Coordinates')}:** {r['latitude']:.5f}, {r['longitude']:.5f}")
                st.write(f"**{label('الأولوية','Priority')}:** {r['priority_ar']}")
                st.write(f"**{label('الجهة المختصة','Department')}:** {r['department_name']}")


# =====================================================
# 23. SMART ASSISTANT
# =====================================================

elif selected_page == "assistant":

    st.header("🤖 " + label("مساعد النيل الأبيض الذكي", "White Nile Smart Assistant"))

    st.markdown("""
    <div class="wns-card">
        <h3>🌍 WNS Smart Assistant</h3>
        <p>مساعدك الذكي لمعرفة الخدمات الحكومية وطريقة تقديم البلاغات.</p>
    </div>
    """, unsafe_allow_html=True)

    question = st.text_area(
        label("كيف يمكنني مساعدتك؟", "How can I help you?"),
        placeholder=label(
            "مثال: أين أبلغ عن انقطاع المياه؟",
            "Example: Where can I report a water outage?"
        )
    )

    if st.button(label("إرسال السؤال", "Send Question")):

        if question.strip():

            answer = smart_assistant(question)

            st.success(answer)


# =====================================================
# 24. REPORT MANAGEMENT & SMART NOTIFICATIONS
# =====================================================

elif selected_page == "manage_reports":

    st.header("⚙️ " + label("الإدارة والجهات الحكومية", "Administration & Departments"))

    staff = get_staff()

    if staff:

        staff_id, username, full_name, role, department_id, staff_city = staff

        st.success(
            f"{label('مرحباً','Welcome')} {full_name} | {role}"
        )

        if st.button(label("تسجيل الخروج", "Logout")):

            st.session_state.pop("staff_id", None)
            st.session_state.pop("root_admin", None)

            st.rerun()

        # -------------------------------------------------
        # FILTER REPORTS BY ROLE
        # -------------------------------------------------

        reports = load_reports()

        if role == "department":

            reports = reports[
                reports["department_id"] == department_id
            ]

        elif role == "locality":

            if staff_city:
                reports = reports[
                    reports["city"] == staff_city
                ]

        elif role not in ["admin", "governor"]:

            st.error(label("ليس لديك صلاحية.", "Access denied."))

            st.stop()

        # -------------------------------------------------
        # DEPARTMENT NOTIFICATIONS WITH ENHANCED FILTER & CLEARING
        # -------------------------------------------------

        st.subheader("🔔 " + label("الإشعارات الذكية", "Smart Notifications"))

        if role == "department":

            notifications = load_notifications(department_id)

        else:

            notifications = load_notifications()

        if notifications.empty:

            st.info(label("لا توجد إشعارات.", "No notifications."))

        else:

            unread = notifications[notifications["is_read"] == 0]
            read_notifs = notifications[notifications["is_read"] == 1]

            n_tab1, n_tab2 = st.tabs([
                f"{label('غير المقروءة', 'Unread')} ({len(unread)})",
                f"{label('المقروءة', 'Read')} ({len(read_notifs)})"
            ])

            with n_tab1:
                if unread.empty:
                    st.info(label("جميع الإشعارات مقروءة.", "All notifications read."))
                else:
                    for _, notif in unread.iterrows():

                        with st.container(border=True):

                            st.markdown(f"**🔔 {notif['title']}**")
                            st.write(notif["message"])

                            if pd.notna(notif.get("location")):
                                st.write(f"📍 {notif['location']}")

                            st.caption(f"⏱️ {notif['created_at']}")

                            if st.button(
                                label("تحديد كمقروء", "Mark as Read"),
                                key=f"read_{notif['id']}"
                            ):

                                conn = get_connection()

                                conn.execute("""
                                    UPDATE admin_notifications
                                    SET is_read=1 WHERE id=?
                                """, (int(notif["id"]),))

                                conn.commit()

                                conn.close()

                                st.rerun()

            with n_tab2:
                if read_notifs.empty:
                    st.info(label("لا توجد إشعارات مقروءة.", "No read notifications."))
                else:
                    for _, notif in read_notifs.iterrows():
                        with st.container(border=True):
                            st.markdown(f"**✔️ {notif['title']}**")
                            st.write(notif["message"])
                            st.caption(f"⏱️ {notif['created_at']}")

        st.divider()

        # -------------------------------------------------
        # REPORTS
        # -------------------------------------------------

        st.subheader("📋 " + label("البلاغات الموجهة إليك", "Assigned Reports"))

        if reports.empty:

            st.info(label("لا توجد بلاغات.", "No reports available."))

        else:

            for _, row in reports.iterrows():

                with st.expander(
                    f"{row['report_code']} | {category_name(row['category'])} | {priority_name(row['priority'])}"
                ):

                    st.write(f"**{label('الوصف','Description')}:** {row['description']}")

                    st.write(f"**{label('الموقع','Location')}:** {row['location']}")

                    st.write(f"**{label('الجهة','Department')}:** {row['department_name']}")

                    st.write(f"**{label('الأولوية','Priority')}:** {priority_name(row['priority'])}")

                    st.write(f"**{label('الحالة','Status')}:** {status_name(row['status'])}")

                    # Only administrators and the assigned department
                    # are allowed to update the report
                    can_update = (
                        role in ["admin", "governor", "locality"]
                        or (
                            role == "department"
                            and department_id == row["department_id"]
                        )
                    )

                    if can_update:

                        current_status = row["status"]

                        new_status = st.selectbox(
                            label("تحديث حالة البلاغ", "Update Status"),
                            ["Pending", "In Progress", "Resolved"],
                            index=["Pending", "In Progress", "Resolved"].index(
                                current_status
                            ) if current_status in ["Pending", "In Progress", "Resolved"] else 0,
                            format_func=status_name,
                            key=f"status_{row['id']}"
                        )

                        if st.button(
                            label("حفظ التحديث", "Save Update"),
                            key=f"save_{row['id']}"
                        ):

                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            conn = get_connection()

                            conn.execute("""
                                UPDATE reports
                                SET status=?,updated_at=?
                                WHERE id=?
                            """, (
                                new_status,
                                now,
                                int(row["id"])
                            ))

                            conn.commit()

                            conn.close()

                            notify_citizen(
                                row["identity_code"],
                                int(row["id"]),
                                "تحديث حالة البلاغ",
                                f"تم تحديث البلاغ {row['report_code']} إلى {status_name(new_status)}"
                            )

                            create_notification(
                                int(row["id"]),
                                "تحديث حالة بلاغ",
                                f"تم تحديث حالة البلاغ {row['report_code']} إلى {new_status}",
                                "admin",
                                None
                            )

                            st.success(label("تم تحديث البلاغ وإشعار المواطن.", "Report updated and citizen notified."))

                            st.rerun()

        # -------------------------------------------------
        # ADMINISTRATION SECTION
        # -------------------------------------------------

        if role in ["admin", "governor"]:

            st.divider()

            st.subheader("🏢 " + label("إدارة الجهات والمستخدمين", "Departments & Staff Management"))

            conn = get_connection()

            departments_df = pd.read_sql_query(
                "SELECT * FROM departments ORDER BY id",
                conn
            )

            conn.close()

            st.dataframe(
                departments_df,
                use_container_width=True,
                hide_index=True
            )

            # Quick seeding of department accounts
            with st.expander(label("⚡ إنشاء حسابات الجهات التلقائية", "Generate Default Department Accounts")):
                st.info(label("توليد حسابات افتراضية لجميع الجهات الحكومية المسجلة", "Generate default accounts for all departments"))
                if st.button(label("توليد الحسابات الافتراضية الآن", "Generate Default Accounts Now")):
                    count = seed_default_departments()
                    if count > 0:
                        st.success(label(f"تم إنشاء {count} حسابات افتراضية للجهات بنجاح!", f"Successfully created {count} default department accounts!"))
                    else:
                        st.info(label("جميع حسابات الجهات الافتراضية موجودة بالفعل.", "All default department accounts already exist."))
                    st.rerun()

            with st.expander(label("➕ إنشاء حساب جهة حكومية", "Create Department Account")):

                with st.form("staff_creation"):

                    staff_name = st.text_input(
                        label("اسم المسؤول", "Staff Name")
                    )

                    username = st.text_input(
                        label("اسم المستخدم", "Username")
                    )

                    staff_password = st.text_input(
                        label("كلمة المرور", "Password"),
                        type="password"
                    )

                    staff_role = st.selectbox(
                        label("نوع الصلاحية", "Role"),
                        ["department", "locality"],
                        format_func=lambda x: {
                            "department": "مسؤول جهة حكومية",
                            "locality": "مدير محلية"
                        }.get(x, x)
                    )

                    selected_department = st.selectbox(
                        label("الجهة الحكومية", "Department"),
                        departments_df["id"].tolist(),
                        format_func=lambda x: departments_df.loc[
                            departments_df["id"] == x,
                            "name_ar"
                        ].iloc[0]
                    )

                    staff_city = st.selectbox(
                        label("المحلية / المدينة", "City"),
                        [""] + list(CITIES.keys())
                    )

                    create_user = st.form_submit_button(
                        label("إنشاء الحساب", "Create Account")
                    )

                if create_user:

                    if not staff_name.strip() or not username.strip() or len(staff_password) < 8:

                        st.error(label(
                            "أدخل جميع البيانات، واجعل كلمة المرور 8 أحرف على الأقل.",
                            "Complete all fields and use at least 8 characters."
                        ))

                    else:

                        conn = get_connection()

                        try:

                            conn.execute("""
                                INSERT INTO staff_users
                                (username,full_name,password_hash,role,department_id,city)
                                VALUES (?,?,?,?,?,?)
                            """, (
                                username.strip(),
                                staff_name.strip(),
                                hash_password(staff_password),
                                staff_role,
                                selected_department,
                                staff_city
                            ))

                            conn.commit()

                            st.success(label(
                                "تم إنشاء حساب المسؤول بنجاح.",
                                "Staff account created successfully."
                            ))

                            st.rerun()

                        except sqlite3.IntegrityError:

                            st.error(label(
                                "اسم المستخدم مستخدم بالفعل.",
                                "Username already exists."
                            ))

                        finally:

                            conn.close()

            with st.expander(label("👥 عرض حسابات المسؤولين", "View Staff Accounts")):

                conn = get_connection()

                staff_df = pd.read_sql_query("""
                    SELECT id,username,full_name,role,department_id,city,is_active
                    FROM staff_users ORDER BY id DESC
                """, conn)

                conn.close()

                st.dataframe(
                    staff_df,
                    use_container_width=True,
                    hide_index=True
                )

                if not staff_df.empty:

                    selected_staff = st.selectbox(
                        label("اختر حساباً لتعطيله", "Select Account to Disable"),
                        staff_df["id"].tolist()
                    )

                    if st.button(label("تعطيل الحساب", "Disable Account")):

                        conn = get_connection()

                        conn.execute("""
                            UPDATE staff_users
                            SET is_active=0
                            WHERE id=?
                        """, (selected_staff,))

                        conn.commit()

                        conn.close()

                        st.success(label("تم تعطيل الحساب.", "Account disabled."))

                        st.rerun()

            # Report export
            st.divider()

            st.download_button(
                label("📥 تحميل جميع البلاغات CSV", "Download Reports CSV"),
                data=reports.to_csv(index=False).encode("utf-8-sig"),
                file_name="WNS_Reports.csv",
                mime="text/csv"
            )

    else:

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        tab1, tab2 = st.tabs([
            label("دخول الإدارة العامة", "General Administration"),
            label("دخول الجهات الحكومية", "Department Login")
        ])

        with tab1:

            password = st.text_input(
                label("كلمة مرور مدير النظام", "Administrator Password"),
                type="password"
            )

            if st.button(label("دخول المدير", "Admin Login")):

                expected = get_admin_password()

                if hmac.compare_digest(password, expected):

                    st.session_state["root_admin"] = True

                    # Create a virtual admin identity
                    st.session_state["staff_id"] = -999

                    st.rerun()

                else:

                    st.error(label("كلمة المرور غير صحيحة.", "Incorrect password."))

        with tab2:

            st.info(label("💡 أسماء المستخدمين وكلمات المرور الافتراضية للجهات (من 11 إلى 1):", "Default accounts (11 to 1):"))
            st.markdown("""
            1. **هيئة الكهرباء:** `electricity_user` / `electricity12345`
            2. **هيئة المياه:** `water_user` / `water12345`
            3. **إدارة النظافة:** `cleaning_user` / `cleaning12345`
            4. **إدارة الطرق والجسور:** `roads_user` / `roads12345`
            5. **إدارة الصرف الصحي:** `sewage_user` / `sewage12345`
            6. **إدارة الصحة:** `health_user` / `health12345`
            7. **إدارة البيئة:** `environment_user` / `environment12345`
            8. **الدفاع المدني:** `emergency_user` / `emergency12345`
            9. **شرطة المرور:** `traffic_user` / `traffic12345`
            10. **إدارة التعليم:** `education_user` / `education12345`
            11. **غرفة المتابعة العامة:** `other_user` / `other12345`
            """)

            username = st.text_input(
                label("اسم المستخدم", "Username"),
                key="dept_username_input"
            )

            password = st.text_input(
                label("كلمة المرور", "Password"),
                type="password",
                key="staff_password_login"
            )

            if st.button(label("تسجيل الدخول", "Login to Department")):

                if staff_login(username, password):

                    st.rerun()

                else:

                    st.error(label(
                        "اسم المستخدم أو كلمة المرور غير صحيحة.",
                        "Incorrect username or password."
                    ))


# =====================================================
# 25. FOOTER
# =====================================================

st.divider()

st.markdown("""
<div style="
text-align:center;
padding:20px;
color:#12304A;
background:white;
border-radius:12px;
">

<h4>🌍 WHITE NILE SMART (WNS)</h4>

<p>النيل الأبيض الذكية | منصة التحول الرقمي المتكاملة</p>

<p style="color:#079B91;">
Smart Government • AI • Digital Services • Smart Notifications
</p>

</div>
""", unsafe_allow_html=True)
