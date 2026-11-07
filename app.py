import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import sqlite3
import pandas as pd
import plotly.express as px
import pydeck as pdk
import QR code 
import io
import uuid
import hmac
import os
import hashlib
import secrets
import re
import unicodedata
import time
from datetime import datetime

# =====================================================
# CONFIGURATION & THEME (Blue & Turquoise)
# =====================================================
st.set_page_config(page_title="WNS", page_icon="🌍", layout="wide")
DB_NAME = "smart_nation.db"

st.markdown("""
<style>
.main {background-color:#f4f8fb;}
.block-container {padding-top:2rem;}
h1,h2,h3 {color:#123b5d;}
.stButton>button {
    background-color:#087e8b; color:white; border-radius:8px;
    border:none; padding:0.5rem 1rem; font-weight:bold;
}
.stButton>button:hover {background-color:#065a63; color:white;}
div[data-testid="stMetric"] {
    background-color:white; padding:18px; border-radius:12px;
    box-shadow:0 2px 8px rgba(8,126,139,0.1); border-left: 5px solid #087e8b;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# TRANSLATIONS
# =====================================================
translations = {
    "English": {
        "app_title":"WNS","subtitle":"Integrated Digital Transformation Platform",
        "navigation":"Navigation","dashboard":"Dashboard & Analytics","submit_report":"Submit Report",
        "manage_reports":"Manage Reports & Notifications","digital_identities":"Digital Identities",
        "verify_identity":"Verify Identity","my_services":"My Services","city_map":"City Map",
        "ai_intelligence":"AI Intelligence","overview":"Platform Overview","total_reports":"Total Reports",
        "pending_reports":"Pending Reports","resolved_reports":"Resolved Reports",
        "registered_identities":"Registered Identities","reports_by_category":"Reports by Category",
        "reports_by_status":"Reports by Status","recent_reports":"Recent Reports",
        "no_reports":"No reports have been submitted yet.","report_title":"Submit a Smart City Report",
        "full_name":"Full Name","email":"Email Address","user_type":"User Type","citizen":"Citizen",
        "student":"Student","employee":"Employee","other":"Other","category":"Category",
        "description":"Description","location":"Location","auto_detect":"Automatic detection",
        "latitude":"Latitude","longitude":"Longitude","priority":"Priority","normal":"Normal",
        "urgent":"Urgent","submit":"Submit Report","report_success":"Your report has been submitted successfully!",
        "report_error":"Please fill in all required fields.","manage_title":"Manage City Reports & Notifications",
        "admin_login":"Administrator Login","password":"Password","login":"Login",
        "wrong_password":"Incorrect email or password.",
        "password_not_set":"Admin password is not configured. Add ADMIN_PASSWORD in Streamlit Secrets.",
        "admin_access":"Administrator access granted.","report_code":"Report Code","status":"Status",
        "Pending":"Pending","In Progress":"In Progress","Resolved":"Resolved","update":"Update Status",
        "updated":"Report status updated.","logout":"Logout","download":"Download Reports CSV",
        "identity_title":"Create Digital Identity","create_identity":"Create Account & Identity",
        "identity_success":"Your account and digital identity were created successfully!",
        "identity_code":"Identity Code","created_at":"Created At","identity_list":"Registered Identities",
        "no_identities":"No digital identities registered yet.","verify_title":"Verify Digital Identity",
        "enter_code":"Enter Identity Code","verify":"Verify Identity",
        "valid_identity":"Valid digital identity found.","invalid_identity":"Identity not found. Please check the code.",
        "map_title":"Smart City Reports Map","map_empty":"No reports with location coordinates are available.",
        "ai_title":"AI Report Intelligence",
        "ai_description":"Enter a report description to analyze its category, risk level, and assigned department.",
        "analyze":"Analyze Report","analysis_result":"Analysis Result","electricity":"Electricity",
        "water":"Water","cleaning":"Cleaning","roads":"Roads","other_category":"Other",
        "classification_note":"This engine uses natural language rules and dictionary-based heuristics for real-time analysis.",
        "footer":"WNS | النيل الأبيض الذكية | Integrated Digital Transformation Platform",
        "report_details":"Report Details","enter_description":"Please enter a description.",
        "category_result":"Predicted Category","priority_result":"Predicted Priority",
        "identity_details":"Identity Details","identity_exists":"An identity with this email already exists.",
        "select_status":"Select Status","create_password":"Create Password","confirm_password":"Confirm Password",
        "password_mismatch":"Passwords do not match.","password_length":"Password must contain at least 8 characters.",
        "account_created":"Account created. You are now logged in.","my_reports":"My Reports",
        "login_required":"Please log in to view your services.","no_my_reports":"You have not submitted any reports yet.",
        "welcome":"Welcome","login_to_account":"Log in with Identity or Email",
        "report_owner_note":"Your report will be linked to your digital identity.",
        "report_saved":"Your report was saved and linked to your account.",
        "identity_created_at":"Identity Created","account":"Account",
        "identity_registration_note":"Step 1: Create your account. Step 2: Verify your digital identity. Step 3: Submit reports.",
        "verify_before_report":"Please verify your digital identity before submitting a report.",
        "verify_my_identity":"Verify my identity",
        "identity_verified":"Your digital identity has been verified. You can now submit reports.",
        "identity_not_logged":"Log in with your account first, then verify your identity.",
        "dialect_note":"The analyzer recognizes common Arabic expressions and some Sudanese colloquial words. Describe the issue clearly.",
        "logout_account":"Log out of account","status_tracking":"Report Status Tracking",
        "risk_score":"Risk Score","department":"Target Department","est_time":"Est. Response Time",
        "detected_keywords":"Detected Keywords","safety_hazard":"Safety Hazard Detected"
    },
    "العربية": {
        "app_title":"النيل الأبيض الذكية (WNS)","subtitle":"منصة التحول الرقمي المتكاملة",
        "navigation":"القائمة الرئيسية","dashboard":"لوحة التحكم والتحليلات","submit_report":"إرسال بلاغ",
        "manage_reports":"إدارة البلاغات والإشعارات","digital_identities":"الهويات الرقمية",
        "verify_identity":"التحقق من الهوية","my_services":"خدماتي وبلاغاتي","city_map":"خريطة المدينة",
        "ai_intelligence":"الذكاء الاصطناعي","overview":"نظرة عامة على المنصة",
        "total_reports":"إجمالي البلاغات","pending_reports":"البلاغات المعلقة",
        "resolved_reports":"البلاغات المحلولة","registered_identities":"الهويات المسجلة",
        "reports_by_category":"البلاغات حسب التصنيف","reports_by_status":"البلاغات حسب الحالة",
        "recent_reports":"أحدث البلاغات","no_reports":"لا توجد بلاغات حتى الآن.",
        "report_title":"إرسال بلاغ للمدينة الذكية","full_name":"الاسم الكامل","email":"البريد الإلكتروني",
        "user_type":"نوع المستخدم","citizen":"مواطن","student":"طالب","employee":"موظف","other":"أخرى",
        "category":"التصنيف","description":"وصف البلاغ","location":"الموقع","auto_detect":"التصنيف التلقائي",
        "latitude":"خط العرض","longitude":"خط الطول","priority":"الأولوية","normal":"عادي","urgent":"عاجل",
        "submit":"إرسال البلاغ","report_success":"تم إرسال البلاغ بنجاح!",
        "report_error":"يرجى تعبئة جميع الحقول المطلوبة.","manage_title":"إدارة البلاغات ومتابعة الإشعارات",
        "admin_login":"دخول المسؤول","password":"كلمة المرور","login":"تسجيل الدخول",
        "wrong_password":"البريد الإلكتروني أو رمز الهوية غير صحيح.",
        "password_not_set":"لم يتم إعداد كلمة مرور المسؤول. أضف ADMIN_PASSWORD في إعدادات Secrets.",
        "admin_access":"تم السماح بدخول المسؤول.","report_code":"رمز البلاغ","status":"الحالة",
        "Pending":"قيد الانتظار","In Progress":"جاري المعالجة","Resolved":"تمت المعالجة","update":"تحديث الحالة",
        "updated":"تم تحديث حالة البلاغ بنجاح.","logout":"تسجيل الخروج",
        "download":"تحميل البلاغات CSV","identity_title":"إنشاء هوية رقمية وسريعة",
        "create_identity":"إنشاء الهوية وتسجيل الدخول المباشر","identity_success":"تم إنشاء هويتك الرقمية بنجاح!",
        "identity_code":"رمز الهوية الرقمية","created_at":"تاريخ الإنشاء","identity_list":"الهويات المسجلة",
        "no_identities":"لا توجد هويات رقمية مسجلة حتى الآن.","verify_title":"التحقق من الهوية الرقمية",
        "enter_code":"أدخل رمز الهوية أو البريد","verify":"تحقق من الهوية",
        "valid_identity":"تم العثور على هوية رقمية صحيحة.",
        "invalid_identity":"لم يتم العثور على الهوية. يرجى التأكد من الرمز.",
        "map_title":"خريطة بلاغات المدينة الذكية",
        "map_empty":"لا توجد بلاغات تحتوي على إحداثيات للموقع.",
        "ai_title":"تحليل البلاغات بالذكاء الاصطناعي الذكي",
        "ai_description":"أدخل وصف البلاغ لتحليله تلقائياً، تقييم مستوى الخطورة، واقتراح جهة الاختصاص.",
        "analyze":"تحليل البلاغ الآن","analysis_result":"نتيجة التحليل الذكي","electricity":"الكهرباء",
        "water":"المياه","cleaning":"النظافة","roads":"الطرق","other_category":"أخرى",
        "classification_note":"يعتمد محرك التحليل على المعالجة اللغوية للنصوص والقواعد الاستكشافية المتقدمة لتقديم اقتراحات فورية.",
        "footer":"النيل الأبيض الذكية (WNS) | منصة التحول الرقمي المتكاملة","report_details":"تفاصيل البلاغات المسجلة",
        "enter_description":"يرجى إدخال وصف البلاغ.","category_result":"التصنيف المتوقع",
        "priority_result":"الأولوية المتوقعة","identity_details":"تفاصيل الهوية",
        "identity_exists":"توجد هوية مسجلة بهذا البريد الإلكتروني بالفعل.","select_status":"اختر الحالة الجديدة",
        "create_password":"إنشاء كلمة مرور للحساب","confirm_password":"تأكيد كلمة المرور",
        "password_mismatch":"كلمتا المرور غير متطابقتين.",
        "password_length":"يجب أن تتكون كلمة المرور من 8 أحرف على الأقل.",
        "account_created":"تم تسجيل دخولك بنجاح.","my_reports":"بلاغاتي الشخصية",
        "login_required":"يرجى تسجيل الدخول أو إدخال هويتك الرقمية لمتابعة خدماتك.","no_my_reports":"لم تقم بإرسال أي بلاغ حتى الآن.",
        "welcome":"مرحباً بك","login_to_account":"تسجيل الدخول السريع باستخدام الهوية أو البريد",
        "report_owner_note":"سيتم ربط البلاغ بهويتك الرقمية مباشرة لتسهيل متابعته.",
        "report_saved":"تم حفظ البلاغ وربطه بحسابك وإرسال إشعار فوري للمسؤول.",
        "identity_created_at":"تاريخ الإنشاء","account":"الحساب الشخصي",
        "identity_registration_note":"أنشئ هويتك الرقمية مرة واحدة واستخدمها للدخول السريع وإرسال ومتابعة البلاغات بكل سهولة.",
        "verify_before_report":"يرجى التحقق من هويتك الرقمية أولاً قبل إرسال البلاغ.",
        "verify_my_identity":"تفعيل هويتي الآن",
        "identity_verified":"تم التحقق من هويتك الرقمية بنجاح. يمكنك الآن إرسال البلاغات.",
        "identity_not_logged":"سجّل الدخول بهويتك الرقمية أولاً.",
        "dialect_note":"النظام يتعرّف على تعبيرات عربية دارجة وبعض الكلمات باللهجة السودانية (مثل: كوشة، ماسورة، نور قاطع، إلخ).",
        "logout_account":"تسجيل الخروج من الحساب","status_tracking":"حالة البلاغ",
        "risk_score":"نسبة الخطورة المتوقعة","department":"الجهة التنفيذية المقترحة","est_time":"الوقت المتوقع للاستجابة",
        "detected_keywords":"الكلمات المفتاحية المكتشفة","safety_hazard":"تنبيه: تم اكتشاف مؤشر خطر على السلامة العامة!"
    }
}

if "language" not in st.session_state:
    st.session_state.language = "English"

st.session_state.language = st.sidebar.selectbox(
    "🌐 Language / اللغة", ["English", "العربية"],
    index=0 if st.session_state.language == "English" else 1
)

def t(key):
    return translations[st.session_state.language].get(key, key)

# =====================================================
# DATABASE INITIALIZATION
# =====================================================
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def initialize_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
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
    cur.execute("""
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_read INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

initialize_database()

def load_reports():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM reports ORDER BY id DESC", conn)
    conn.close()
    return df

def load_identities():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM identities ORDER BY id DESC", conn)
    conn.close()
    return df

def load_admin_notifications(unread_only=False):
    conn = get_connection()
    query = "SELECT n.*, r.category, r.description as report_desc, r.location as report_loc, r.priority, r.status FROM admin_notifications n LEFT JOIN reports r ON n.report_id = r.id"
    if unread_only:
        query += " WHERE n.is_read = 0"
    query += " ORDER BY n.id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def mark_notifications_read():
    conn = get_connection()
    conn.execute("UPDATE admin_notifications SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()

# =====================================================
# SECURITY & PASSWORDS
# =====================================================
def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000)
    return salt + "$" + digest.hex()

def verify_password(password, stored_hash):
    try:
        salt, expected = stored_hash.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, AttributeError):
        return False

# =====================================================
# WHITE NILE LOCATIONS
# =====================================================
WHITE_NILE_CITIES = {
    "كوستي": (13.16290, 32.66347),
    "ربك": (13.18087, 32.73999),
    "الدويم": (14.00120, 32.31160),
    "القطينة": (14.86480, 32.36680),
    "تندلتي": (13.01667, 31.86667),
    "مرابة": (12.35000, 32.18333),
    "الجزيرة أبا": (13.31930, 32.61320),
    "الكوة": (13.74630, 32.49960),
    "ود الزاكي": (14.46190, 32.20650),
}

# =====================================================
# AI & TEXT ANALYSIS ENGINE
# =====================================================
def normalize_text(value):
    text = str(value or "").lower().strip()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u064b-\u065f\u0670]", "", text)
    text = text.replace("ـ", "")
    text = text.translate(str.maketrans({"أ":"ا", "إ":"ا", "آ":"ا", "ى":"ي", "ة":"ه"}))
    return re.sub(r"\s+", " ", text)

def analyze_report(description):
    text = normalize_text(description)
    category_terms = {
        "Electricity": ["كهرباء","كهربا","النور","تيار","اناره","عمود كهرباء","سلك","اسلاك","لمبات","ضلمه","power","electric","light","electricity","outage"],
        "Water": ["مياه","موية","مويا","مويه","حنفيه","حنفية","ماسوره","انبوب","تسريب","المجاري","صرف صحي","water","leak","pipe","drinking water","sewage"],
        "Cleaning": ["نفايات","قمامه","زباله","زبل","وسخ","اوساخ","كوشه","نظافه","مخلفات","ريحة","روائح","garbage","waste","trash","cleaning","rubbish"],
        "Roads": ["شارع","شوارع","حفره","طريق","اسفلت","مكسر","محفر","مطب","مطبات","رصيف","اشاره مرور","road","pothole","street","asphalt","traffic light"]
    }
    found_keywords = []
    scores = {}
    for cat, terms in category_terms.items():
        score = sum(1 for term in terms if normalize_text(term) in text)
        scores[cat] = score
        if score > 0:
            found_keywords.extend(terms[:1])

    best_category = max(scores, key=scores.get)
    category = best_category if scores[best_category] else "Other"

    critical_terms = ["حريق","نار","دخان","انفجار","صعق","سلك عريان","سلك مكشوف","سلك واقع","عمود واقع","عمود ساقط","خطر شديد","حادث خطير","انهيار","غرق","فيضان","تسمم","emergency","fire","electrocution"]
    service_failure_terms = ["الموية قاطعه","المويه قاطعه","مافي موية","انقطاع المياه","الكهربا قاطعه","النور قاطع","انقطاع الكهرباء","ماسوره مكسوره","طفح المجاري","no water","no electricity"]
    impact_terms = ["الحي بالكامل","كل الحي","عدد كبير","مدرسه","مستشفى","مركز صحي","شارع رئيسي","whole neighborhood","hospital"]

    is_critical = any(normalize_text(term) in text for term in critical_terms)
    service_score = sum(1 for term in service_failure_terms if normalize_text(term) in text)
    impact_score = sum(1 for term in impact_terms if normalize_text(term) in text)

    priority = "Urgent" if (is_critical or service_score >= 1 or impact_score >= 2) else "Normal"
    risk_score = min(100, (50 if is_critical else 20) + (service_score * 25) + (impact_score * 25))

    departments = {
        "Electricity": "الهيئة القومية للكهرباء - ولاية النيل الأبيض",
        "Water": "هيئة مياه ولاية النيل الأبيض / الصرف الصحي",
        "Cleaning": "إدارة النظافة وإعادة تدوير النفايات بالمحلية",
        "Roads": "إدارة الطرق والجسور والبنية التحتية",
        "Other": "غرفة المتابعة والخدمات العامة"
    }
    dept = departments.get(category, departments["Other"])
    est_time = "2 - 6 ساعات" if priority == "Urgent" else "24 - 48 ساعة"
    return category, priority, risk_score, dept, est_time, found_keywords, is_critical

def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=8, border=3)
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def translate_category(category):
    mapping = {"Electricity":"electricity","Water":"water","Cleaning":"cleaning","Roads":"roads","Other":"other_category"}
    return t(mapping.get(category, "other_category"))

def translate_status(status):
    # إرجاع الحالة المترجمة الصحيحة (قيد الانتظار، جاري المعالجة، تمت المعالجة)
    return t(status)

def translate_priority(priority):
    return t({"Normal":"normal","Urgent":"urgent"}.get(priority, "normal"))

# =====================================================
# NAVIGATION HEADER & SIDEBAR
# =====================================================
st.title("🌍 " + t("app_title"))
st.caption(t("subtitle"))
st.divider()

pages = [
    "digital_identities", "verify_identity", "submit_report", "my_services",
    "dashboard", "city_map", "ai_intelligence", "manage_reports"
]
page_labels = [t(page) for page in pages]

if "navigation_target" in st.session_state:
    target_page = st.session_state.pop("navigation_target")
    if target_page in pages:
        st.session_state["navigation_radio"] = t(target_page)

if st.session_state.get("navigation_radio") not in page_labels:
    st.session_state["navigation_radio"] = page_labels[0]

selected_label = st.sidebar.radio(t("navigation"), page_labels, key="navigation_radio")
selected_page = pages[page_labels.index(selected_label)]

def current_identity():
    identity_code = st.session_state.get("citizen_identity_code")
    if not identity_code:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT identity_code, full_name, email, user_type, created_at FROM identities WHERE identity_code = ? OR email = ?", (identity_code, identity_code))
    row = cur.fetchone()
    conn.close()
    return row

# =====================================================
# DASHBOARD PAGE
# =====================================================
if selected_page == "dashboard":
    st.header("📊 " + t("overview"))
    reports = load_reports()
    identities = load_identities()
    pending_count = len(reports[reports["status"] == "Pending"]) if not reports.empty else 0
    resolved_count = len(reports[reports["status"] == "Resolved"]) if not reports.empty else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("total_reports"), len(reports))
    c2.metric(t("pending_reports"), pending_count)
    c3.metric(t("resolved_reports"), resolved_count)
    c4.metric(t("registered_identities"), len(identities))
    st.divider()
    if not reports.empty:
        left, right = st.columns(2)
        with left:
            st.subheader(t("reports_by_category"))
            chart = reports["category"].value_counts().reset_index()
            chart.columns = ["Category","Count"]
            chart["Category"] = chart["Category"].apply(translate_category)
            st.plotly_chart(px.pie(chart, names="Category", values="Count", hole=0.4, color_discrete_sequence=px.colors.sequential.Teal), use_container_width=True)
        with right:
            st.subheader(t("reports_by_status"))
            chart = reports["status"].value_counts().reset_index()
            chart.columns = ["Status","Count"]
            chart["Status"] = chart["Status"].apply(translate_status)
            st.plotly_chart(px.bar(chart, x="Status", y="Count", color="Status", color_discrete_sequence=['#087e8b', '#123b5d', '#20a4f3']), use_container_width=True)
        st.subheader(t("recent_reports"))
        recent = reports.head(5).copy()
        for col, func in [("category", translate_category), ("status", translate_status), ("priority", translate_priority)]:
            recent[col] = recent[col].apply(func)
        st.dataframe(recent[["report_code","category","location","priority","status","created_at"]], use_container_width=True, hide_index=True)
    else:
        st.info(t("no_reports"))

# =====================================================
# DIGITAL IDENTITY PAGE (Simplified Login & Creation)
# =====================================================
elif selected_page == "digital_identities":
    st.header("🪪 " + t("identity_title"))
    st.info(t("identity_registration_note"))
    
    tab1, tab2 = st.tabs(["إنشاء هوية سريعة / Create ID", "تسجيل الدخول السريع / Quick Login"])
    
    with tab1:
        with st.form("identity_form"):
            full_name = st.text_input(t("full_name"))
            email = st.text_input(t("email")).strip().lower()
            user_types = ["Citizen","Student","Employee","Other"]
            user_type = st.selectbox(t("user_type"), user_types, format_func=lambda value:t(value.lower()))
            password = st.text_input(t("create_password"), type="password")
            confirm_password = st.text_input(t("confirm_password"), type="password")
            submitted = st.form_submit_button(t("create_identity"))

        if submitted:
            if not full_name.strip() or not email or not password:
                st.error(t("report_error"))
            elif len(password) < 8:
                st.error(t("password_length"))
            elif password != confirm_password:
                st.error(t("password_mismatch"))
            else:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT id FROM identities WHERE email = ?", (email,))
                existing = cur.fetchone()
                if existing:
                    st.warning(t("identity_exists"))
                    conn.close()
                else:
                    identity_code = "WNS-" + str(uuid.uuid4())[:8].upper()
                    cur.execute("""
                        INSERT INTO identities (identity_code,full_name,email,user_type,password_hash,created_at)
                        VALUES (?,?,?,?,?,?)
                    """, (identity_code, full_name.strip(), email, user_type, hash_password(password), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    conn.close()
                    st.session_state["citizen_identity_code"] = identity_code
                    st.session_state["citizen_identity_verified"] = True
                    st.success(t("identity_success"))
                    st.success(t("account_created"))

    with tab2:
        with st.form("quick_login_form"):
            login_id = st.text_input("أدخل البريد أو رمز الهوية (مثل WNS-XXXXX)").strip()
            login_pass = st.text_input(t("password"), type="password")
            login_btn = st.form_submit_button(t("login"))
        if login_btn:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT identity_code, password_hash FROM identities WHERE email = ? OR identity_code = ?", (login_id.lower(), login_id))
            acc = cur.fetchone()
            conn.close()
            if acc and verify_password(login_pass, acc[1]):
                st.session_state["citizen_identity_code"] = acc[0]
                st.session_state["citizen_identity_verified"] = True
                st.success(t("account_created"))
                st.rerun()
            else:
                st.error(t("wrong_password"))

# =====================================================
# MY SERVICES & REPORTS PAGE
# =====================================================
elif selected_page == "my_services":
    st.header("👤 " + t("my_services"))
    identity = current_identity()
    if identity:
        st.success(f"{t('welcome')}, {identity[1]}")
        st.write(f"**{t('email')}:** {identity[2]}")
        st.write(f"**{t('identity_code')}:** `{identity[0]}`")
        if st.button(t("logout_account")):
            st.session_state.pop("citizen_identity_code", None)
            st.session_state.pop("citizen_identity_verified", None)
            st.rerun()
        st.divider()
        st.subheader("📋 " + t("my_reports"))
        conn = get_connection()
        my_reports = pd.read_sql_query(
            "SELECT report_code,category,description,location,priority,status,created_at FROM reports WHERE identity_code = ? ORDER BY id DESC",
            conn, params=(identity[0],)
        )
        conn.close()
        if my_reports.empty:
            st.info(t("no_my_reports"))
        else:
            for _, report in my_reports.iterrows():
                with st.expander(f"{translate_category(report['category'])} — {report['report_code'][:8]} ({translate_status(report['status'])})"):
                    st.write(f"**{t('description')}:** {report['description']}")
                    st.write(f"**{t('location')}:** {report['location']}")
                    st.write(f"**{t('priority')}:** {translate_priority(report['priority'])}")
                    st.write(f"**{t('status_tracking')}:** `{translate_status(report['status'])}`")
                    st.write(f"**{t('created_at')}:** {report['created_at']}")
    else:
        st.warning(t("login_required"))

# =====================================================
# SUBMIT REPORT PAGE
# =====================================================
elif selected_page == "submit_report":
    st.header("📝 " + t("report_title"))
    identity = current_identity()
    if not identity:
        st.warning(t("login_required"))
    else:
        st.success(f"{t('welcome')}, {identity[1]}")
        st.caption(t("report_owner_note"))
        
        try:
            detected_location = streamlit_geolocation()
        except Exception:
            detected_location = None

        if isinstance(detected_location, dict) and detected_location.get("latitude"):
            st.session_state["report_latitude"] = float(detected_location["latitude"])
            st.session_state["report_longitude"] = float(detected_location["longitude"])
            st.success("تم تحديد موقعك الجغرافي بنجاح.")

        default_city = "كوستي"
        default_lat, default_lon = WHITE_NILE_CITIES[default_city]
        default_lat = float(st.session_state.get("report_latitude", default_lat))
        default_lon = float(st.session_state.get("report_longitude", default_lon))

        with st.form("report_form"):
            city_options = list(WHITE_NILE_CITIES.keys())
            selected_city = st.selectbox("المدينة / المحلية داخل ولاية النيل الأبيض", city_options, index=city_options.index(default_city))
            neighborhood = st.text_input("الحي أو الشارع / Neighborhood")
            location = f"{selected_city} - {neighborhood}".strip(" -")
            category_options = ["Auto","Electricity","Water","Cleaning","Roads","Other"]
            category = st.selectbox(t("category"), category_options, format_func=lambda value:t("auto_detect") if value == "Auto" else translate_category(value))
            description = st.text_area(t("description"))
            c1, c2 = st.columns(2)
            with c1:
                latitude = st.number_input(t("latitude"), value=default_lat, format="%.6f")
            with c2:
                longitude = st.number_input(t("longitude"), value=default_lon, format="%.6f")
            submitted = st.form_submit_button(t("submit"))

        if submitted:
            if location.strip() and description.strip():
                predicted_category, priority, risk_score, dept, est_time, keywords, is_critical = analyze_report(description)
                final_category = predicted_category if category in ("Auto","Other") else category
                report_code = "REP-" + str(uuid.uuid4())[:8].upper()
                conn = get_connection()
                cur = conn.cursor()
                created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute("""
                    INSERT INTO reports (report_code,identity_code,category,description,location,latitude,longitude,priority,status,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (report_code, identity[0], final_category, description, location, latitude, longitude, priority, "Pending", created_time))
                new_report_id = cur.lastrowid
                
                cur.execute("""
                    INSERT INTO admin_notifications (report_id,title,message,created_at,is_read)
                    VALUES (?,?,?,?,0)
                """, (new_report_id, "بلاغ جديد / New Report", f"بلاغ مقدم من {identity[1]} في {location}", created_time))
                conn.commit()
                conn.close()
                st.success(t("report_saved"))
                st.code(report_code)
            else:
                st.error(t("report_error"))

# =====================================================
# ADMIN REPORT MANAGEMENT & NOTIFICATIONS (Merged View)
# =====================================================
elif selected_page == "manage_reports":
    st.header("⚙️ " + t("manage_title"))
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.subheader(t("admin_login"))
        try:
            admin_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
        except Exception:
            admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
            
        entered_password = st.text_input(t("password"), type="password")
        if st.button(t("login"), key="admin_login_btn"):
            if entered_password == admin_password or hmac.compare_digest(entered_password, admin_password):
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error(t("wrong_password"))
    else:
        if st.button(t("logout"), key="admin_logout_btn"):
            st.session_state.admin_logged_in = False
            st.rerun()

        # Integrated Notifications & Reports Section
        unread_notifications = load_admin_notifications(unread_only=True)
        all_notifications = load_admin_notifications()
        unread_count = len(unread_notifications)

        st.subheader(f"🔔 إشعارات المسؤول والطلبات ({unread_count} جديدة)")
        if unread_count > 0:
            for _, notif in unread_notifications.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{notif['title']}** — 🕒 {notif['created_at']}")
                    st.write(notif["message"])
                    if pd.notna(notif.get("report_desc")):
                        st.info(f"**التفاصيل:** {notif['report_desc']} | **الموقع:** {notif['report_loc']}")
            if st.button("تحديد كل الإشعارات كمقروءة"):
                mark_notifications_read()
                st.rerun()
        else:
            st.success("لا توجد إشعارات جديدة بانتظار المراجعة.")

        st.divider()
        st.subheader("📋 " + t("report_details"))
        reports = load_reports()
        if reports.empty:
            st.info(t("no_reports"))
        else:
            statuses = ["Pending", "In Progress", "Resolved"]
            status_labels = {"Pending": "قيد الانتظار", "In Progress": "جاري المعالجة", "Resolved": "تمت المعالجة"}
            
            for _, row in reports.iterrows():
                current_stat = row["status"] if row["status"] in statuses else "Pending"
                with st.expander(f"{row['report_code']} — {translate_category(row['category'])} [{status_labels.get(current_stat, current_stat)}]"):
                    st.write(f"**{t('description')}:** {row['description']}")
                    st.write(f"**{t('location')}:** {row['location']}")
                    st.write(f"**{t('priority')}:** {translate_priority(row['priority'])}")
                    st.write(f"**{t('identity_code')}:** `{row.get('identity_code','')}`")
                    
                    new_status = st.selectbox(
                        t("select_status"), statuses,
                        index=statuses.index(current_stat),
                        format_func=lambda s: status_labels.get(s, s),
                        key=f"status_sel_{row['id']}"
                    )
                    if st.button(t("update"), key=f"upd_btn_{row['id']}"):
                        conn = get_connection()
                        conn.execute("UPDATE reports SET status = ? WHERE id = ?", (new_status, row["id"]))
                        conn.commit()
                        conn.close()
                        st.success(t("updated"))
                        st.rerun()
            
            st.download_button(t("download"), data=reports.to_csv(index=False).encode("utf-8-sig"), file_name="wns_reports.csv", mime="text/csv")

# =====================================================
# VERIFY IDENTITY PAGE
# =====================================================
elif selected_page == "verify_identity":
    st.header("🔍 " + t("verify_title"))
    code_input = st.text_input(t("enter_code"))
    if st.button(t("verify")):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT identity_code, full_name, email, user_type, created_at FROM identities WHERE identity_code = ? OR email = ?", (code_input.strip(), code_input.strip().lower()))
        res = cur.fetchone()
        conn.close()
        if res:
            st.success(t("valid_identity"))
            st.write(f"**{t('full_name')}:** {res[1]}")
            st.write(f"**{t('email')}:** {res[2]}")
            st.write(f"**{t('identity_code')}:** `{res[0]}`")
            st.write(f"**{t('created_at')}:** {res[4]}")
        else:
            st.error(t("invalid_identity"))

# =====================================================
# CITY MAP PAGE
# =====================================================
elif selected_page == "city_map":
    st.header("🗺️ " + t("map_title"))
    city_df = pd.DataFrame([{"name":c, "latitude":coord[0], "longitude":coord[1], "kind":"مدينة"} for c, coord in WHITE_NILE_CITIES.items()])
    reports = load_reports()
    layers = [pdk.Layer("ScatterplotLayer", data=city_df, get_position="[longitude, latitude]", get_radius=1500, get_fill_color=[8, 126, 139, 180], pickable=True)]
    deck = pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=13.16, longitude=32.66, zoom=8), map_style="light")
    st.pydeck_chart(deck, use_container_width=True)

# =====================================================
# AI INTELLIGENCE PAGE
# =====================================================
elif selected_page == "ai_intelligence":
    st.header("🤖 " + t("ai_title"))
    st.write(t("ai_description"))
    description = st.text_area(t("description"), height=150, placeholder="مثال: في سلك كهرباء عريان واقع في الشارع الرئيسي...")
    if st.button(t("analyze"), type="primary"):
        if description.strip():
            cat, pri, risk, dept, est_time, kw, is_crit = analyze_report(description)
            if is_crit:
                st.error("⚠️ " + t("safety_hazard"))
            c1, c2, c3 = st.columns(3)
            c1.metric(t("category_result"), translate_category(cat))
            c2.metric(t("priority_result"), translate_priority(pri))
            c3.metric(t("risk_score"), f"{risk}%")
            st.progress(risk / 100)
            st.info(f"🏢 **{t('department')}:** {dept}")
            st.warning(f"⏱️ **{t('est_time')}:** {est_time}")
        else:
            st.warning(t("enter_description"))

# =====================================================
# FOOTER
# =====================================================
st.divider()
st.markdown(f'<div style="text-align:center;color:#087e8b;padding:15px;">🌍 {t("footer")}</div>', unsafe_allow_html=True)
