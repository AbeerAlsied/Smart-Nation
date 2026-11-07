import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import sqlite3
import pandas as pd
import plotly.express as px
import pydeck as pdk
import qrcode
import io
import uuid
import hmac
import os
import hashlib
import secrets
import re
import unicodedata
from datetime import datetime

# =====================================================
# CONFIGURATION
# =====================================================
st.set_page_config(page_title="Smart Nation", page_icon="🌍", layout="wide")
DB_NAME = "smart_nation.db"

# =====================================================
# TRANSLATIONS
# =====================================================
translations = {
    "English": {
        "app_title":"Smart Nation","subtitle":"Integrated Digital Transformation Platform",
        "navigation":"Navigation","dashboard":"Dashboard & Analytics","submit_report":"Submit Report",
        "manage_reports":"Manage Reports","digital_identities":"Digital Identities",
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
        "report_error":"Please fill in all required fields.","manage_title":"Manage City Reports",
        "admin_login":"Administrator Login","password":"Password","login":"Login",
        "wrong_password":"Incorrect email or password.",
        "password_not_set":"Admin password is not configured. Add ADMIN_PASSWORD in Streamlit Secrets.",
        "admin_access":"Administrator access granted.","report_code":"Report Code","status":"Status",
        "pending":"Pending","in_progress":"In Progress","resolved":"Resolved","update":"Update Status",
        "updated":"Report status updated.","logout":"Logout","download":"Download Reports CSV",
        "identity_title":"Create Digital Identity","create_identity":"Create Account & Identity",
        "identity_success":"Your account and digital identity were created successfully!",
        "identity_code":"Identity Code","created_at":"Created At","identity_list":"Registered Identities",
        "no_identities":"No digital identities registered yet.","verify_title":"Verify Digital Identity",
        "enter_code":"Enter Identity Code","verify":"Verify Identity",
        "valid_identity":"Valid digital identity found.","invalid_identity":"Identity not found. Please check the code.",
        "map_title":"Smart City Reports Map","map_empty":"No reports with location coordinates are available.",
        "ai_title":"AI Report Intelligence",
        "ai_description":"Enter a report description to analyze its category and priority.",
        "analyze":"Analyze Report","analysis_result":"Analysis Result","electricity":"Electricity",
        "water":"Water","cleaning":"Cleaning","roads":"Roads","other_category":"Other",
        "classification_note":"This prototype uses keyword-based rules. It is not a trained machine-learning model.",
        "footer":"Smart Nation | Integrated Digital Transformation Platform",
        "report_details":"Report Details","enter_description":"Please enter a description.",
        "category_result":"Predicted Category","priority_result":"Predicted Priority",
        "identity_details":"Identity Details","identity_exists":"An identity with this email already exists.",
        "select_status":"Select Status","create_password":"Create Password","confirm_password":"Confirm Password",
        "password_mismatch":"Passwords do not match.","password_length":"Password must contain at least 8 characters.",
        "account_created":"Account created. You are now logged in.","my_reports":"My Reports",
        "login_required":"Please log in to view your services.","no_my_reports":"You have not submitted any reports yet.",
        "welcome":"Welcome","login_to_account":"Log in to your account",
        "email_exists_no_password":"This email already has an identity. Use the login section or contact the administrator to set up access.",
        "report_owner_note":"Your report will be linked to your digital identity.",
        "report_saved":"Your report was saved and linked to your account.",
        "identity_created_at":"Identity Created","account":"Account",
        "identity_registration_note":"Step 1: Create your account. Step 2: Verify your digital identity. Step 3: Submit reports.",
        "verify_before_report":"Please verify your digital identity before submitting a report.",
        "verify_my_identity":"Verify my identity",
        "identity_verified":"Your digital identity has been verified. You can now submit reports.",
        "identity_not_logged":"Log in with your account first, then verify your identity.",
        "dialect_note":"The analyzer recognizes common Arabic expressions and some Sudanese colloquial words. Describe the issue clearly; the result is a suggestion.",
        "logout_account":"Log out of account","status_tracking":"Report Status Tracking"
    },
    "العربية": {
        "app_title":"الأمة الذكية","subtitle":"منصة التحول الرقمي المتكاملة",
        "navigation":"القائمة الرئيسية","dashboard":"لوحة التحكم والتحليلات","submit_report":"إرسال بلاغ",
        "manage_reports":"إدارة البلاغات","digital_identities":"الهويات الرقمية",
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
        "report_error":"يرجى تعبئة جميع الحقول المطلوبة.","manage_title":"إدارة بلاغات المدينة",
        "admin_login":"دخول المسؤول","password":"كلمة المرور","login":"تسجيل الدخول",
        "wrong_password":"البريد الإلكتروني أو كلمة المرور غير صحيحة.",
        "password_not_set":"لم يتم إعداد كلمة مرور المسؤول. أضف ADMIN_PASSWORD في إعدادات Secrets.",
        "admin_access":"تم السماح بدخول المسؤول.","report_code":"رمز البلاغ","status":"الحالة",
        "pending":"قيد الانتظار","in_progress":"قيد المعالجة","resolved":"تم الحل",
        "update":"تحديث الحالة","updated":"تم تحديث حالة البلاغ.","logout":"تسجيل الخروج",
        "download":"تحميل البلاغات CSV","identity_title":"إنشاء هوية رقمية",
        "create_identity":"إنشاء الحساب والهوية","identity_success":"تم إنشاء الحساب والهوية الرقمية بنجاح!",
        "identity_code":"رمز الهوية","created_at":"تاريخ الإنشاء","identity_list":"الهويات المسجلة",
        "no_identities":"لا توجد هويات رقمية مسجلة حتى الآن.","verify_title":"التحقق من الهوية الرقمية",
        "enter_code":"أدخل رمز الهوية","verify":"تحقق من الهوية",
        "valid_identity":"تم العثور على هوية رقمية صحيحة.",
        "invalid_identity":"لم يتم العثور على الهوية. يرجى التأكد من الرمز.",
        "map_title":"خريطة بلاغات المدينة الذكية",
        "map_empty":"لا توجد بلاغات تحتوي على إحداثيات للموقع.",
        "ai_title":"تحليل البلاغات بالذكاء الاصطناعي",
        "ai_description":"أدخل وصف البلاغ لتحليل التصنيف والأولوية.","analyze":"تحليل البلاغ",
        "analysis_result":"نتيجة التحليل","electricity":"الكهرباء","water":"المياه",
        "cleaning":"النظافة","roads":"الطرق","other_category":"أخرى",
        "classification_note":"هذا النموذج الأولي يعتمد على الكلمات المفتاحية والقواعد، وليس نموذج تعلم آلي مدرباً.",
        "footer":"الأمة الذكية | منصة التحول الرقمي المتكاملة","report_details":"تفاصيل البلاغ",
        "enter_description":"يرجى إدخال وصف البلاغ.","category_result":"التصنيف المتوقع",
        "priority_result":"الأولوية المتوقعة","identity_details":"تفاصيل الهوية",
        "identity_exists":"توجد هوية مسجلة بهذا البريد الإلكتروني بالفعل.","select_status":"اختر الحالة",
        "create_password":"إنشاء كلمة مرور","confirm_password":"تأكيد كلمة المرور",
        "password_mismatch":"كلمتا المرور غير متطابقتين.",
        "password_length":"يجب أن تتكون كلمة المرور من 8 أحرف على الأقل.",
        "account_created":"تم إنشاء الحساب وتسجيل دخولك.","my_reports":"بلاغاتي",
        "login_required":"يرجى تسجيل الدخول لمتابعة خدماتك.","no_my_reports":"لم تقم بإرسال أي بلاغ حتى الآن.",
        "welcome":"مرحباً","login_to_account":"تسجيل الدخول إلى حسابك",
        "email_exists_no_password":"هذا البريد لديه هوية مسجلة مسبقاً. استخدم تسجيل الدخول أو تواصل مع المسؤول لإعداد الدخول.",
        "report_owner_note":"سيتم ربط البلاغ بهويتك الرقمية.","report_saved":"تم حفظ البلاغ وربطه بحسابك.",
        "identity_created_at":"تاريخ إنشاء الهوية","account":"الحساب",
        "identity_registration_note":"الخطوة 1: أنشئ حسابك. الخطوة 2: تحقّق من هويتك الرقمية. الخطوة 3: أرسل البلاغات.",
        "verify_before_report":"يرجى التحقق من هويتك الرقمية أولاً قبل إرسال البلاغ.",
        "verify_my_identity":"التحقق من هويتي",
        "identity_verified":"تم التحقق من هويتك الرقمية. يمكنك الآن إرسال البلاغات.",
        "identity_not_logged":"سجّل الدخول إلى حسابك أولاً، ثم تحقّق من هويتك.",
        "dialect_note":"النظام يتعرّف على تعبيرات عربية دارجة وبعض الكلمات باللهجة السودانية. اشرح المشكلة بوضوح، والنتيجة تظل اقتراحاً قابلاً للمراجعة.",
        "logout_account":"تسجيل الخروج من الحساب","status_tracking":"متابعة حالة البلاغ"
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
# DATABASE
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
    identity_columns = [r[1] for r in cur.execute("PRAGMA table_info(identities)").fetchall()]
    if "password_hash" not in identity_columns:
        cur.execute("ALTER TABLE identities ADD COLUMN password_hash TEXT DEFAULT ''")
    report_columns = [r[1] for r in cur.execute("PRAGMA table_info(reports)").fetchall()]
    if "identity_code" not in report_columns:
        cur.execute("ALTER TABLE reports ADD COLUMN identity_code TEXT DEFAULT ''")
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
    query = "SELECT * FROM admin_notifications"
    if unread_only:
        query += " WHERE is_read = 0"
    query += " ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def mark_notifications_read():
    conn = get_connection()
    conn.execute("UPDATE admin_notifications SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()

# =====================================================
# PASSWORDS
# =====================================================
def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000
    )
    return salt + "$" + digest.hex()

def verify_password(password, stored_hash):
    try:
        salt, expected = stored_hash.split("$", 1)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000
        ).hex()
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
# TEXT ANALYSIS AND QR
# =====================================================
def normalize_text(value):
    text = str(value or "").lower().strip()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u064b-\u065f\u0670]", "", text)
    text = text.replace("ـ", "")
    text = text.translate(str.maketrans({
        "أ":"ا", "إ":"ا", "آ":"ا", "ى":"ي", "ة":"ه"
    }))
    return re.sub(r"\s+", " ", text)

def analyze_report(description):
    text = normalize_text(description)
    category_terms = {
        "Electricity": ["كهرباء","كهربا","النور","تيار","اناره","عمود كهرباء","سلك",
                        "اسلاك","لمبات","ضلمه","power","electric","light","electricity","outage"],
        "Water": ["مياه","موية","مويا","مويه","حنفيه","حنفية","ماسوره","انبوب",
                  "تسريب","المجاري","صرف صحي","water","leak","pipe","drinking water","sewage"],
        "Cleaning": ["نفايات","قمامه","زباله","زبل","وسخ","اوساخ","كوشه","نظافه",
                     "مخلفات","ريحة","روائح","garbage","waste","trash","cleaning","rubbish"],
        "Roads": ["شارع","شوارع","حفره","طريق","اسفلت","مكسر","محفر","مطب",
                  "مطبات","رصيف","اشاره مرور","road","pothole","street","asphalt","traffic light"]
    }
    scores = {
        category: sum(1 for term in terms if normalize_text(term) in text)
        for category, terms in category_terms.items()
    }
    best_category = max(scores, key=scores.get)
    category = best_category if scores[best_category] else "Other"

    critical_terms = [
        "حريق","نار","دخان","انفجار","صعق","سلك عريان","سلك مكشوف",
        "سلك كهرباء عريان","سلك كهربا عريان","سلك كهرباء مكشوف","سلك كهربا مكشوف",
        "سلك واقع","عمود واقع","عمود ساقط","اسلاك ساقطه","خطر شديد",
        "خطر على الناس","حادث خطير","انهيار","غرق","فيضان","مياه ملوثه",
        "موية ملوثه","تسمم","urgent","emergency","fire","smoke","explosion",
        "electrocution","live wire","fallen pole","collapse","flood",
        "contaminated water","life threatening"
    ]
    service_failure_terms = [
        "الموية قاطعه","المويه قاطعه","موية قاطعه","مافي موية","مافي مياه",
        "انقطاع المياه","انقطاع المويه","انقطاع الموية","الكهربا قاطعه",
        "الكهرباء قاطعه","النور قاطع","مافي كهربا","مافي كهرباء",
        "انقطاع الكهرباء","انقطاع التيار","ماسوره مكسوره","ماسورة مكسورة",
        "تسريب كبير","طفح المجاري","المجاري طافحه","الشارع غرقان",
        "حفره كبيره","الشارع مكسر","طريق مقفول","garbage not collected",
        "no water","no electricity","power outage","water outage",
        "sewage overflow","broken pipe","large pothole","road blocked"
    ]
    impact_terms = [
        "الحي بالكامل","كل الحي","المنطقه بالكامل","كل المنطقة","كل المنطقه",
        "بيوت كتيره","منازل كثيره","عدد كبير","الناس كلها","مدرسه","مستشفى",
        "مركز صحي","شارع رئيسي","يعطل حركة المرور","يسبب حوادث",
        "يعرض الناس للخطر","من امبارح","من يومين","من اسبوع","لفتره طويله",
        "whole neighborhood","entire area","many houses","hospital","school",
        "main road","causing accidents","long time","several days"
    ]
    critical = any(normalize_text(term) in text for term in critical_terms)
    service_score = sum(1 for term in service_failure_terms if normalize_text(term) in text)
    impact_score = sum(1 for term in impact_terms if normalize_text(term) in text)
    priority = "Urgent" if (critical or service_score >= 1 or impact_score >= 2) else "Normal"
    return category, priority

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
    mapping = {
        "Electricity":"electricity","Water":"water","Cleaning":"cleaning",
        "Roads":"roads","Other":"other_category"
    }
    return t(mapping.get(category, "other_category"))

def translate_status(status):
    return t({
        "Pending":"pending","In Progress":"in_progress","Resolved":"resolved"
    }.get(status, "pending"))

def translate_priority(priority):
    return t({"Normal":"normal","Urgent":"urgent"}.get(priority, "normal"))

# =====================================================
# STYLE
# =====================================================
st.markdown("""
<style>
.main {background-color:#f7f9fc;}
.block-container {padding-top:2rem;}
h1,h2,h3 {color:#123b5d;}
.stButton>button {
    background-color:#087e8b;color:white;border-radius:8px;
    border:none;padding:0.5rem 1rem;font-weight:bold;
}
.stButton>button:hover {background-color:#075d68;color:white;}
div[data-testid="stMetric"] {
    background-color:white;padding:18px;border-radius:12px;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);
}
</style>
""", unsafe_allow_html=True)

st.title("🌍 " + t("app_title"))
st.caption(t("subtitle"))
st.divider()

# =====================================================
# NAVIGATION - FIXED
# =====================================================
pages = [
    "digital_identities", "verify_identity", "submit_report", "my_services",
    "dashboard", "city_map", "ai_intelligence", "manage_reports"
]
page_labels = [t(page) for page in pages]

# A page key is stored, not a translated label. This also works after language changes.
if "navigation_target" in st.session_state:
    target_page = st.session_state.pop("navigation_target")
    if target_page in pages:
        st.session_state["navigation_radio"] = t(target_page)

if st.session_state.get("navigation_radio") not in page_labels:
    st.session_state["navigation_radio"] = page_labels[0]

selected_label = st.sidebar.radio(
    t("navigation"), page_labels, key="navigation_radio"
)
selected_page = pages[page_labels.index(selected_label)]

# =====================================================
# SESSION ACCOUNT HELPERS
# =====================================================
def current_identity():
    identity_code = st.session_state.get("citizen_identity_code")
    if not identity_code:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT identity_code, full_name, email, user_type, created_at
        FROM identities WHERE identity_code = ?
    """, (identity_code,))
    row = cur.fetchone()
    conn.close()
    return row

# =====================================================
# DASHBOARD
# =====================================================
if selected_page == "dashboard":
    st.header("📊 " + t("overview"))
    reports = load_reports()
    identities = load_identities()
    pending_count = len(reports[reports["status"] == "Pending"]) if not reports.empty else 0
    resolved_count = len(reports[reports["status"] == "Resolved"]) if not reports.empty else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric(t("total_reports"), len(reports))
    c2.metric(t("pending_reports"), pending_count)
    c3.metric(t("resolved_reports"), resolved_count)
    c4.metric(t("registered_identities"), len(identities))
    st.divider()
    if not reports.empty:
        left,right = st.columns(2)
        with left:
            st.subheader(t("reports_by_category"))
            chart = reports["category"].value_counts().reset_index()
            chart.columns = ["Category","Count"]
            chart["Category"] = chart["Category"].apply(translate_category)
            st.plotly_chart(px.pie(chart,names="Category",values="Count",hole=0.4),use_container_width=True)
        with right:
            st.subheader(t("reports_by_status"))
            chart = reports["status"].value_counts().reset_index()
            chart.columns = ["Status","Count"]
            chart["Status"] = chart["Status"].apply(translate_status)
            st.plotly_chart(px.bar(chart,x="Status",y="Count",color="Status"),use_container_width=True)
        st.subheader(t("recent_reports"))
        recent = reports.head(5).copy()
        for column,function in [
            ("category",translate_category),("status",translate_status),("priority",translate_priority)
        ]:
            recent[column] = recent[column].apply(function)
        st.dataframe(
            recent[["report_code","category","location","priority","status","created_at"]],
            use_container_width=True,hide_index=True
        )
    else:
        st.info(t("no_reports"))

# =====================================================
# CREATE DIGITAL IDENTITY
# =====================================================
elif selected_page == "digital_identities":
    st.header("🪪 " + t("identity_title"))
    st.info(t("identity_registration_note"))
    with st.form("identity_form"):
        full_name = st.text_input(t("full_name"))
        email = st.text_input(t("email")).strip().lower()
        user_types = ["Citizen","Student","Employee","Other"]
        user_type = st.selectbox(
            t("user_type"),user_types,
            format_func=lambda value:t(value.lower())
        )
        password = st.text_input(t("create_password"),type="password")
        confirm_password = st.text_input(t("confirm_password"),type="password")
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
            cur.execute("SELECT id FROM identities WHERE email = ?",(email,))
            existing = cur.fetchone()
            if existing:
                st.warning(t("identity_exists"))
                conn.close()
            else:
                identity_code = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO identities
                    (identity_code,full_name,email,user_type,password_hash,created_at)
                    VALUES (?,?,?,?,?,?)
                """,(
                    identity_code,full_name.strip(),email,user_type,hash_password(password),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                conn.commit()
                conn.close()
                st.session_state["citizen_identity_code"] = identity_code
                st.session_state["citizen_identity_verified"] = False
                st.session_state["new_identity_code"] = identity_code
                st.success(t("identity_success"))
                st.success(t("account_created"))

    if st.session_state.get("new_identity_code"):
        code = st.session_state["new_identity_code"]
        st.write("**" + t("identity_code") + ":**")
        st.code(code)
        qr_buffer = generate_qr(code)
        st.image(qr_buffer,caption=t("identity_code"),width=190)
        st.download_button(
            "Download QR Code",data=qr_buffer.getvalue(),
            file_name="digital_identity_qr.png",mime="image/png"
        )

    st.divider()
    st.subheader(t("identity_list"))
    identities = load_identities()
    if identities.empty:
        st.info(t("no_identities"))
    else:
        public_data = identities[["full_name","email","user_type","created_at"]].copy()
        public_data["user_type"] = public_data["user_type"].apply(
            lambda value:t(value.lower()) if value else ""
        )
        public_data.columns = [t("full_name"),t("email"),t("user_type"),t("created_at")]
        st.dataframe(public_data,use_container_width=True,hide_index=True)

# =====================================================
# MY SERVICES / LOGIN / MY REPORTS
# =====================================================
elif selected_page == "my_services":
    st.header("👤 " + t("my_services"))
    identity = current_identity()
    if identity:
        st.success(f"{t('welcome')}, {identity[1]}")
        st.write(f"**{t('email')}:** {identity[2]}")
        st.write(f"**{t('identity_code')}:**")
        st.code(identity[0])
        if st.button(t("logout_account")):
            st.session_state.pop("citizen_identity_code",None)
            st.session_state.pop("citizen_identity_verified",None)
            st.rerun()
        st.divider()
        st.subheader("📋 " + t("my_reports"))
        conn = get_connection()
        my_reports = pd.read_sql_query(
            """SELECT report_code,category,description,location,priority,status,created_at
               FROM reports WHERE identity_code = ? ORDER BY id DESC""",
            conn,params=(identity[0],)
        )
        conn.close()
        if my_reports.empty:
            st.info(t("no_my_reports"))
        else:
            for _,report in my_reports.iterrows():
                with st.expander(
                    f"{translate_category(report['category'])} — {report['report_code'][:8]}"
                ):
                    st.write(f"**{t('description')}:** {report['description']}")
                    st.write(f"**{t('location')}:** {report['location']}")
                    st.write(f"**{t('priority')}:** {translate_priority(report['priority'])}")
                    st.write(f"**{t('status_tracking')}:** {translate_status(report['status'])}")
                    st.write(f"**{t('created_at')}:** {report['created_at']}")
                    st.write(f"**{t('report_code')}:** `{report['report_code']}`")
    else:
        st.info(t("login_required"))
        st.subheader(t("login_to_account"))
        with st.form("citizen_login_form"):
            login_email = st.text_input(t("email")).strip().lower()
            login_password = st.text_input(t("password"),type="password")
            login_clicked = st.form_submit_button(t("login"))
        if login_clicked:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT identity_code,password_hash FROM identities WHERE email = ?",
                (login_email,)
            )
            account = cur.fetchone()
            conn.close()
            if account and account[1] and verify_password(login_password,account[1]):
                st.session_state["citizen_identity_code"] = account[0]
                st.session_state["citizen_identity_verified"] = False
                st.success(t("account_created"))
                st.rerun()
            else:
                st.error(t("wrong_password"))
        st.caption(t("identity_registration_note"))

# =====================================================
# SUBMIT REPORT
# =====================================================
elif selected_page == "submit_report":
    st.header("📝 " + t("report_title"))
    identity = current_identity()
    if not identity:
        st.warning(t("login_required"))
        st.info("Open " + t("my_services") + " and log in, or create a digital identity first.")
    elif not st.session_state.get("citizen_identity_verified",False):
        st.warning(t("verify_before_report"))
        st.info("1. " + t("digital_identities") + "  →  2. " + t("verify_identity") + "  →  3. " + t("submit_report"))
    else:
        st.success(f"{t('welcome')}, {identity[1]}")
        st.caption(t("report_owner_note"))
        st.subheader("📍 " + (
            "حدد موقعك الحالي" if st.session_state.language == "العربية"
            else "Detect my current location"
        ))
        st.caption(
            "اضغط على زر تحديد الموقع واسمح للمتصفح بالوصول إلى موقعك. يمكنك تعديل الإحداثيات يدوياً إذا لزم الأمر."
            if st.session_state.language == "العربية" else
            "Press the location button and allow your browser to access your location. You can still edit the coordinates manually."
        )
        try:
            detected_location = streamlit_geolocation()
        except Exception:
            detected_location = None
            st.warning(
                "تعذر تشغيل خدمة تحديد الموقع. يمكنك إدخال الإحداثيات يدوياً."
                if st.session_state.language == "العربية" else
                "The location service could not be loaded. You can enter coordinates manually."
            )

        if (
            isinstance(detected_location,dict)
            and detected_location.get("latitude") is not None
            and detected_location.get("longitude") is not None
        ):
            st.session_state["report_latitude"] = float(detected_location["latitude"])
            st.session_state["report_longitude"] = float(detected_location["longitude"])
            st.session_state["report_location_detected"] = True
            st.success(
                "تم تحديد موقعك بنجاح." if st.session_state.language == "العربية"
                else "Your location was detected successfully."
            )
            accuracy = detected_location.get("accuracy")
            if accuracy is not None:
                st.caption(
                    ("دقة الموقع التقريبية: " if st.session_state.language == "العربية"
                     else "Approximate location accuracy: ") + f"{accuracy:.0f} m"
                )

        default_city = "كوستي"
        default_lat,default_lon = WHITE_NILE_CITIES[default_city]
        default_lat = float(st.session_state.get("report_latitude",default_lat))
        default_lon = float(st.session_state.get("report_longitude",default_lon))

        with st.form("report_form"):
            city_options = list(WHITE_NILE_CITIES.keys())
            selected_city = st.selectbox(
                "المدينة / المحلية داخل ولاية النيل الأبيض",
                city_options,index=city_options.index(default_city)
            )
            neighborhood = st.text_input("الحي أو الشارع / Neighborhood")
            location = f"{selected_city} - {neighborhood}".strip(" -")
            category_options = ["Auto","Electricity","Water","Cleaning","Roads","Other"]
            category = st.selectbox(
                t("category"),category_options,
                format_func=lambda value:t("auto_detect") if value == "Auto" else translate_category(value)
            )
            description = st.text_area(t("description"))
            c1,c2 = st.columns(2)
            city_lat,city_lon = WHITE_NILE_CITIES[selected_city]
            fallback_lat = default_lat if st.session_state.get("report_location_detected") else city_lat
            fallback_lon = default_lon if st.session_state.get("report_location_detected") else city_lon
            with c1:
                latitude = st.number_input(t("latitude"),value=float(fallback_lat),format="%.6f")
            with c2:
                longitude = st.number_input(t("longitude"),value=float(fallback_lon),format="%.6f")
            submitted = st.form_submit_button(t("submit"))

        if submitted:
            if location.strip() and description.strip():
                predicted_category,priority = analyze_report(description)
                final_category = predicted_category if category in ("Auto","Other") else category
                report_code = str(uuid.uuid4())
                conn = get_connection()
                cur = conn.cursor()
                created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute("""
                    INSERT INTO reports
                    (report_code,identity_code,category,description,location,latitude,longitude,
                     priority,status,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """,(
                    report_code,identity[0],final_category,description,location,
                    latitude,longitude,priority,"Pending",created_time
                ))
                new_report_id = cur.lastrowid
                notification_title = (
                    "بلاغ جديد" if st.session_state.language == "العربية" else "New report"
                )
                notification_message = (
                    f"بلاغ جديد من {identity[1]} في {location}"
                    if st.session_state.language == "العربية"
                    else f"New report submitted by {identity[1]} at {location}"
                )
                cur.execute("""
                    INSERT INTO admin_notifications
                    (report_id,title,message,created_at,is_read)
                    VALUES (?,?,?,?,0)
                """,(
                    new_report_id,notification_title,notification_message,created_time
                ))
                conn.commit()
                conn.close()
                st.success(t("report_saved"))
                st.write(f"**{t('report_code')}:**")
                st.code(report_code)
                st.write(f"**{t('category')}:** {translate_category(final_category)}")
                st.write(f"**{t('priority')}:** {translate_priority(priority)}")
                st.info("Open " + t("my_services") + " to track this report.")
            else:
                st.error(t("report_error"))

# =====================================================
# ADMIN REPORT MANAGEMENT
# =====================================================
elif selected_page == "manage_reports":
    st.header("⚙️ " + t("manage_title"))
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.subheader(t("admin_login"))
        try:
            admin_password = st.secrets.get("ADMIN_PASSWORD","")
        except Exception:
            admin_password = os.environ.get("ADMIN_PASSWORD","")
        if not admin_password:
            st.warning(t("password_not_set"))
        entered_password = st.text_input(t("password"),type="password")
        if st.button(t("login"),key="admin_login_button"):
            if admin_password and hmac.compare_digest(entered_password,admin_password):
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error(t("wrong_password"))
    else:
        unread_notifications = load_admin_notifications(unread_only=True)
        all_notifications = load_admin_notifications()
        st.subheader(
            "🔔 إشعارات المسؤول" if st.session_state.language == "العربية"
            else "🔔 Admin Notifications"
        )
        if not unread_notifications.empty:
            st.error(
                f"لديك {len(unread_notifications)} إشعار جديد ببلاغات مقدمة."
                if st.session_state.language == "العربية"
                else f"You have {len(unread_notifications)} new report notification(s)."
            )
            for _,notification in unread_notifications.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{notification['title']}**")
                    st.write(notification["message"])
                    st.caption(notification["created_at"])
            if st.button(
                "تحديد كل الإشعارات كمقروءة"
                if st.session_state.language == "العربية" else "Mark all as read",
                key="mark_notifications_read"
            ):
                mark_notifications_read()
                st.rerun()
        else:
            st.success(
                "لا توجد إشعارات جديدة." if st.session_state.language == "العربية"
                else "There are no new notifications."
            )

        with st.expander(
            "سجل الإشعارات" if st.session_state.language == "العربية"
            else "Notification history"
        ):
            if all_notifications.empty:
                st.info(
                    "لا توجد إشعارات بعد." if st.session_state.language == "العربية"
                    else "No notifications yet."
                )
            else:
                for _,notification in all_notifications.iterrows():
                    status_label = "مقروء" if notification["is_read"] else "جديد"
                    st.write(
                        f"🔔 **{notification['title']}** — {notification['message']}"
                    )
                    st.caption(f"{notification['created_at']} · {status_label}")

        if st.button(t("logout"),key="admin_logout_button"):
            st.session_state.admin_logged_in = False
            st.rerun()

        reports = load_reports()
        if reports.empty:
            st.info(t("no_reports"))
        else:
            st.subheader(t("report_details"))
            for _,row in reports.iterrows():
                with st.expander(
                    f"{row['report_code'][:8]} — {translate_category(row['category'])}"
                ):
                    st.write(f"**{t('description')}:** {row['description']}")
                    st.write(f"**{t('location')}:** {row['location']}")
                    st.write(f"**{t('priority')}:** {translate_priority(row['priority'])}")
                    st.write(f"**{t('status')}:** {translate_status(row['status'])}")
                    st.write(f"**{t('identity_code')}:** {row.get('identity_code','')}")
                    statuses = ["Pending","In Progress","Resolved"]
                    current_status = row["status"] if row["status"] in statuses else "Pending"
                    new_status = st.selectbox(
                        t("select_status"),statuses,index=statuses.index(current_status),
                        format_func=translate_status,key=f"report_status_{row['id']}"
                    )
                    if st.button(t("update"),key=f"save_status_{row['id']}"):
                        conn = get_connection()
                        conn.execute(
                            "UPDATE reports SET status = ? WHERE id = ?",
                            (new_status,row["id"])
                        )
                        conn.commit()
                        conn.close()
                        st.success(t("updated"))
                        st.rerun()
            st.download_button(
                t("download"),data=reports.to_csv(index=False).encode("utf-8-sig"),
                file_name="smart_nation_reports.csv",mime="text/csv"
            )

# =====================================================
# VERIFY IDENTITY
# =====================================================
elif selected_page == "verify_identity":
    st.header("🔍 " + t("verify_title"))
    signed_identity = current_identity()
    if signed_identity:
        st.subheader(t("account") + ": " + signed_identity[1])
        if st.session_state.get("citizen_identity_verified",False):
            st.success(t("identity_verified"))
        elif st.button(t("verify_my_identity")):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT identity_code FROM identities WHERE identity_code = ?",
                (signed_identity[0],)
            )
            valid = cur.fetchone()
            conn.close()
            if valid:
                st.session_state["citizen_identity_verified"] = True
                st.success(t("identity_verified"))
                st.rerun()
            else:
                st.error(t("invalid_identity"))
    else:
        st.info(t("identity_not_logged"))

    st.divider()
    st.subheader(t("verify_title"))
    identity_code = st.text_input(t("enter_code"))
    if st.button(t("verify"),key="verify_identity_code"):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT identity_code,full_name,email,user_type,created_at
            FROM identities WHERE identity_code = ?
        """,(identity_code.strip(),))
        result = cur.fetchone()
        conn.close()
        if result:
            st.success(t("valid_identity"))
            st.subheader(t("identity_details"))
            st.write(f"**{t('full_name')}:** {result[1]}")
            st.write(f"**{t('email')}:** {result[2]}")
            st.write(f"**{t('user_type')}:** {t(result[3].lower()) if result[3] else ''}")
            st.write(f"**{t('created_at')}:** {result[4]}")
            if signed_identity and result[0] == signed_identity[0]:
                st.session_state["citizen_identity_verified"] = True
                st.success(t("identity_verified"))
        else:
            st.error(t("invalid_identity"))

# =====================================================
# CITY MAP
# =====================================================
elif selected_page == "city_map":
    st.header("🗺️ " + t("map_title"))
    st.caption("الخريطة مخصصة لولاية النيل الأبيض – السودان | White Nile State, Sudan")
    city_df = pd.DataFrame([
        {"name":city,"latitude":coords[0],"longitude":coords[1],"kind":"مدينة"}
        for city,coords in WHITE_NILE_CITIES.items()
    ])
    reports = load_reports()
    if not reports.empty:
        report_points = reports.dropna(subset=["latitude","longitude"]).copy()
        report_points["latitude"] = pd.to_numeric(report_points["latitude"],errors="coerce")
        report_points["longitude"] = pd.to_numeric(report_points["longitude"],errors="coerce")
        report_points = report_points.dropna(subset=["latitude","longitude"])
        if not report_points.empty:
            report_points["name"] = report_points["location"].fillna("بلاغ")
            report_points["kind"] = "بلاغ"
    else:
        report_points = pd.DataFrame()

    st.subheader("مدن ومحليات ولاية النيل الأبيض")
    st.dataframe(
        city_df[["name","latitude","longitude"]].rename(
            columns={"name":"المدينة / المحلية","latitude":"خط العرض","longitude":"خط الطول"}
        ),
        use_container_width=True,hide_index=True
    )
    layers = [
        pdk.Layer(
            "ScatterplotLayer",data=city_df,
            get_position="[longitude, latitude]",get_radius=1800,
            get_fill_color=[20,120,180,180],pickable=True
        )
    ]
    if not report_points.empty:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",data=report_points,
                get_position="[longitude, latitude]",get_radius=900,
                get_fill_color=[220,50,50,220],pickable=True
            )
        )
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=13.45,longitude=32.35,zoom=7,pitch=0
        ),
        map_style="light",
        tooltip={"text":"{name}\\n{kind}"}
    )
    st.pydeck_chart(deck,use_container_width=True)
    if report_points.empty:
        st.info(
            "الخريطة تعرض مواقع المدن والمحليات. ستظهر البلاغات بعلامات حمراء بعد تسجيلها بإحداثيات."
        )
    else:
        st.subheader("البلاغات المسجلة في الولاية")
        for _,row in report_points.iterrows():
            st.write(
                f"📍 **{row['name']}** — "
                f"{translate_category(row.get('category','Other'))} — "
                f"{translate_status(row.get('status','Pending'))}"
            )

# =====================================================
# AI INTELLIGENCE (RULE-BASED)
# =====================================================
elif selected_page == "ai_intelligence":
    st.header("🤖 " + t("ai_title"))
    st.write(t("ai_description"))
    st.caption(t("dialect_note"))
    description = st.text_area(t("description"),height=150)
    if st.button(t("analyze")):
        if description.strip():
            category,priority = analyze_report(description)
            c1,c2 = st.columns(2)
            c1.metric(t("category_result"),translate_category(category))
            c2.metric(t("priority_result"),translate_priority(priority))
        else:
            st.warning(t("enter_description"))
    st.divider()
    st.caption("ℹ️ " + t("classification_note"))

# =====================================================
# CITIZEN JOURNEY NAVIGATION BUTTONS - FIXED
# =====================================================
citizen_steps = [
    "digital_identities","verify_identity","submit_report","my_services"
]
if selected_page in citizen_steps:
    current_step_index = citizen_steps.index(selected_page)
    st.divider()
    previous_col,progress_col,next_col = st.columns([1,2,1])

    with previous_col:
        if current_step_index > 0:
            previous_page = citizen_steps[current_step_index - 1]
            if st.button(
                "← " + t(previous_page),
                key=f"step_previous_{selected_page}",
                use_container_width=True
            ):
                st.session_state["navigation_target"] = previous_page
                st.rerun()

    with progress_col:
        step_text = (
            f"الخطوة {current_step_index + 1} من {len(citizen_steps)}"
            if st.session_state.language == "العربية"
            else f"Step {current_step_index + 1} of {len(citizen_steps)}"
        )
        st.markdown(
            f"""<div style="text-align:center;padding-top:8px;color:#64748b;font-weight:bold;">
            {step_text}</div>""",
            unsafe_allow_html=True
        )

    with next_col:
        if current_step_index < len(citizen_steps) - 1:
            next_page = citizen_steps[current_step_index + 1]
            if st.button(
                t(next_page) + " →",
                key=f"step_next_{selected_page}",
                type="primary",
                use_container_width=True
            ):
                st.session_state["navigation_target"] = next_page
                st.rerun()

# =====================================================
# FOOTER
# =====================================================
st.divider()
st.markdown(
    f"""<div style="text-align:center;color:gray;padding:15px;">
    🌍 {t("footer")}<br><small>Smart Nation Prototype</small></div>""",
    unsafe_allow_html=True
)
