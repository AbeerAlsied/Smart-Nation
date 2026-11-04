import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import qrcode
import io
import uuid
import hmac
import os
from datetime import datetime

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Smart Nation",
    page_icon="🌍",
    layout="wide"
)

DB_NAME = "smart_nation.db"


# =====================================================
# TRANSLATIONS
# =====================================================

translations = {
    "English": {
        "app_title": "Smart Nation",
        "subtitle": "Integrated Digital Transformation Platform",
        "language": "Language",
        "navigation": "Navigation",
        "dashboard": "Dashboard & Analytics",
        "submit_report": "Submit Report",
        "manage_reports": "Manage Reports",
        "digital_identities": "Digital Identities",
        "verify_identity": "Verify Identity",
        "city_map": "City Map",
        "ai_intelligence": "AI Intelligence",
        "overview": "Platform Overview",
        "total_reports": "Total Reports",
        "pending_reports": "Pending Reports",
        "resolved_reports": "Resolved Reports",
        "registered_identities": "Registered Identities",
        "reports_by_category": "Reports by Category",
        "reports_by_status": "Reports by Status",
        "recent_reports": "Recent Reports",
        "no_reports": "No reports have been submitted yet.",
        "report_title": "Submit a Smart City Report",
        "full_name": "Full Name",
        "email": "Email Address",
        "user_type": "User Type",
        "citizen": "Citizen",
        "student": "Student",
        "employee": "Employee",
        "other": "Other",
        "category": "Category",
        "description": "Description",
        "location": "Location",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "priority": "Priority",
        "normal": "Normal",
        "urgent": "Urgent",
        "submit": "Submit Report",
        "report_success": "Your report has been submitted successfully!",
        "report_error": "Please fill in all required fields.",
        "manage_title": "Manage City Reports",
        "admin_login": "Administrator Login",
        "password": "Admin Password",
        "login": "Login",
        "wrong_password": "Incorrect password.",
        "password_not_set": "Admin password is not configured. Add ADMIN_PASSWORD in Streamlit Secrets.",
        "admin_access": "Administrator access granted.",
        "report_code": "Report Code",
        "status": "Status",
        "pending": "Pending",
        "in_progress": "In Progress",
        "resolved": "Resolved",
        "update": "Update Status",
        "updated": "Report status updated.",
        "logout": "Logout",
        "download": "Download Reports CSV",
        "identity_title": "Create Digital Identity",
        "create_identity": "Create Identity",
        "identity_success": "Digital identity created successfully!",
        "identity_code": "Identity Code",
        "created_at": "Created At",
        "identity_list": "Registered Identities",
        "no_identities": "No digital identities registered yet.",
        "verify_title": "Verify Digital Identity",
        "enter_code": "Enter Identity Code",
        "verify": "Verify Identity",
        "valid_identity": "Valid digital identity found.",
        "invalid_identity": "Identity not found. Please check the code.",
        "map_title": "Smart City Reports Map",
        "map_empty": "No reports with location coordinates are available.",
        "ai_title": "AI Report Intelligence",
        "ai_description": "Enter a report description to analyze its category and priority.",
        "analyze": "Analyze Report",
        "analysis_result": "Analysis Result",
        "electricity": "Electricity",
        "water": "Water",
        "cleaning": "Cleaning",
        "roads": "Roads",
        "other_category": "Other",
        "classification_note": "This prototype uses keyword-based rules. It is not a trained machine-learning model.",
        "footer": "Smart Nation | Integrated Digital Transformation Platform",
        "report_details": "Report Details",
        "no_data": "No data available.",
        "enter_description": "Please enter a description.",
        "category_result": "Predicted Category",
        "priority_result": "Predicted Priority",
        "identity_details": "Identity Details",
        "not_logged_in": "Please log in to access this section.",
        "identity_exists": "An identity with this email already exists.",
        "select_status": "Select Status",
        "all": "All",
        "filter": "Filter Reports",
        "search": "Search"
    },

    "العربية": {
        "app_title": "الأمة الذكية",
        "subtitle": "منصة التحول الرقمي المتكاملة",
        "language": "اللغة",
        "navigation": "القائمة الرئيسية",
        "dashboard": "لوحة التحكم والتحليلات",
        "submit_report": "إرسال بلاغ",
        "manage_reports": "إدارة البلاغات",
        "digital_identities": "الهويات الرقمية",
        "verify_identity": "التحقق من الهوية",
        "city_map": "خريطة المدينة",
        "ai_intelligence": "الذكاء الاصطناعي",
        "overview": "نظرة عامة على المنصة",
        "total_reports": "إجمالي البلاغات",
        "pending_reports": "البلاغات المعلقة",
        "resolved_reports": "البلاغات المحلولة",
        "registered_identities": "الهويات المسجلة",
        "reports_by_category": "البلاغات حسب التصنيف",
        "reports_by_status": "البلاغات حسب الحالة",
        "recent_reports": "أحدث البلاغات",
        "no_reports": "لا توجد بلاغات حتى الآن.",
        "report_title": "إرسال بلاغ للمدينة الذكية",
        "full_name": "الاسم الكامل",
        "email": "البريد الإلكتروني",
        "user_type": "نوع المستخدم",
        "citizen": "مواطن",
        "student": "طالب",
        "employee": "موظف",
        "other": "أخرى",
        "category": "التصنيف",
        "description": "وصف البلاغ",
        "location": "الموقع",
        "latitude": "خط العرض",
        "longitude": "خط الطول",
        "priority": "الأولوية",
        "normal": "عادي",
        "urgent": "عاجل",
        "submit": "إرسال البلاغ",
        "report_success": "تم إرسال البلاغ بنجاح!",
        "report_error": "يرجى تعبئة جميع الحقول المطلوبة.",
        "manage_title": "إدارة بلاغات المدينة",
        "admin_login": "دخول المسؤول",
        "password": "كلمة مرور المسؤول",
        "login": "تسجيل الدخول",
        "wrong_password": "كلمة المرور غير صحيحة.",
        "password_not_set": "لم يتم إعداد كلمة مرور المسؤول. أضف ADMIN_PASSWORD في إعدادات Secrets.",
        "admin_access": "تم السماح بدخول المسؤول.",
        "report_code": "رمز البلاغ",
        "status": "الحالة",
        "pending": "قيد الانتظار",
        "in_progress": "قيد المعالجة",
        "resolved": "تم الحل",
        "update": "تحديث الحالة",
        "updated": "تم تحديث حالة البلاغ.",
        "logout": "تسجيل الخروج",
        "download": "تحميل البلاغات CSV",
        "identity_title": "إنشاء هوية رقمية",
        "create_identity": "إنشاء الهوية",
        "identity_success": "تم إنشاء الهوية الرقمية بنجاح!",
        "identity_code": "رمز الهوية",
        "created_at": "تاريخ الإنشاء",
        "identity_list": "الهويات المسجلة",
        "no_identities": "لا توجد هويات رقمية مسجلة حتى الآن.",
        "verify_title": "التحقق من الهوية الرقمية",
        "enter_code": "أدخل رمز الهوية",
        "verify": "تحقق من الهوية",
        "valid_identity": "تم العثور على هوية رقمية صحيحة.",
        "invalid_identity": "لم يتم العثور على الهوية. يرجى التأكد من الرمز.",
        "map_title": "خريطة بلاغات المدينة الذكية",
        "map_empty": "لا توجد بلاغات تحتوي على إحداثيات للموقع.",
        "ai_title": "تحليل البلاغات بالذكاء الاصطناعي",
        "ai_description": "أدخل وصف البلاغ لتحليل التصنيف والأولوية.",
        "analyze": "تحليل البلاغ",
        "analysis_result": "نتيجة التحليل",
        "electricity": "الكهرباء",
        "water": "المياه",
        "cleaning": "النظافة",
        "roads": "الطرق",
        "other_category": "أخرى",
        "classification_note": "هذا النموذج الأولي يعتمد على الكلمات المفتاحية والقواعد، وليس نموذج تعلم آلي مدرباً.",
        "footer": "الأمة الذكية | منصة التحول الرقمي المتكاملة",
        "report_details": "تفاصيل البلاغ",
        "no_data": "لا توجد بيانات.",
        "enter_description": "يرجى إدخال وصف البلاغ.",
        "category_result": "التصنيف المتوقع",
        "priority_result": "الأولوية المتوقعة",
        "identity_details": "تفاصيل الهوية",
        "not_logged_in": "يرجى تسجيل الدخول للوصول إلى هذا القسم.",
        "identity_exists": "توجد هوية مسجلة بهذا البريد الإلكتروني بالفعل.",
        "select_status": "اختر الحالة",
        "all": "الكل",
        "filter": "تصفية البلاغات",
        "search": "بحث"
    }
}


# =====================================================
# LANGUAGE SETTINGS
# =====================================================

if "language" not in st.session_state:
    st.session_state.language = "English"

language = st.sidebar.selectbox(
    "🌐 Language / اللغة",
    ["English", "العربية"],
    index=0 if st.session_state.language == "English" else 1
)

st.session_state.language = language


def t(key):
    return translations[st.session_state.language].get(key, key)


# =====================================================
# DATABASE
# =====================================================

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS identities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identity_code TEXT UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            user_type TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_code TEXT UNIQUE,
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

    conn.commit()
    conn.close()


initialize_database()


# =====================================================
# DATA FUNCTIONS
# =====================================================

def load_reports():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM reports ORDER BY id DESC",
        conn
    )
    conn.close()
    return df


def load_identities():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM identities ORDER BY id DESC",
        conn
    )
    conn.close()
    return df


# =====================================================
# AI CLASSIFICATION
# =====================================================

def analyze_report(description):

    text = description.lower()

    categories = {
        "Electricity": [
            "electricity", "power", "light", "electric",
            "كهرباء", "إنارة", "انقطاع", "تيار"
        ],

        "Water": [
            "water", "leak", "pipe", "drinking water",
            "مياه", "ماء", "تسريب", "ماسورة", "أنبوب"
        ],

        "Cleaning": [
            "garbage", "waste", "trash", "cleaning",
            "نفايات", "قمامة", "نظافة", "مخلفات"
        ],

        "Roads": [
            "road", "pothole", "street", "asphalt",
            "شارع", "حفرة", "طريق", "أسفلت"
        ]
    }

    category = "Other"

    for name, keywords in categories.items():
        if any(word in text for word in keywords):
            category = name
            break

    urgent_words = [
        "urgent", "emergency", "danger", "fire",
        "explosion", "accident", "serious",
        "عاجل", "طوارئ", "خطير", "حريق",
        "انفجار", "حادث", "خطر"
    ]

    priority = (
        "Urgent"
        if any(word in text for word in urgent_words)
        else "Normal"
    )

    return category, priority


# =====================================================
# QR CODE
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
        fill_color="black",
        back_color="white"
    )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


# =====================================================
# TRANSLATION HELPERS
# =====================================================

def translate_category(category):

    mapping = {
        "Electricity": "electricity",
        "Water": "water",
        "Cleaning": "cleaning",
        "Roads": "roads",
        "Other": "other_category"
    }

    return t(mapping.get(category, "other_category"))


def translate_status(status):

    mapping = {
        "Pending": "pending",
        "In Progress": "in_progress",
        "Resolved": "resolved"
    }

    return t(mapping.get(status, "pending"))


def translate_priority(priority):

    mapping = {
        "Normal": "normal",
        "Urgent": "urgent"
    }

    return t(mapping.get(priority, "normal"))


# =====================================================
# CUSTOM DESIGN
# =====================================================

st.markdown("""
<style>

.main {
    background-color: #f7f9fc;
}

.block-container {
    padding-top: 2rem;
}

h1, h2, h3 {
    color: #123b5d;
}

.stButton > button {
    background-color: #087e8b;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: bold;
}

.stButton > button:hover {
    background-color: #075d68;
    color: white;
}

div[data-testid="stMetric"] {
    background-color: white;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# HEADER
# =====================================================

st.title("🌍 " + t("app_title"))
st.caption(t("subtitle"))

st.divider()


# =====================================================
# NAVIGATION
# =====================================================

pages = [
    "dashboard",
    "submit_report",
    "manage_reports",
    "digital_identities",
    "verify_identity",
    "city_map",
    "ai_intelligence"
]

page_labels = [t(page) for page in pages]

selected_label = st.sidebar.radio(
    t("navigation"),
    page_labels
)

selected_page = pages[page_labels.index(selected_label)]


# =====================================================
# DASHBOARD
# =====================================================

if selected_page == "dashboard":

    st.header("📊 " + t("overview"))

    reports = load_reports()
    identities = load_identities()

    total_reports = len(reports)

    pending_count = (
        len(reports[reports["status"] == "Pending"])
        if not reports.empty else 0
    )

    resolved_count = (
        len(reports[reports["status"] == "Resolved"])
        if not reports.empty else 0
    )

    total_identities = len(identities)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(t("total_reports"), total_reports)
    col2.metric(t("pending_reports"), pending_count)
    col3.metric(t("resolved_reports"), resolved_count)
    col4.metric(t("registered_identities"), total_identities)

    st.divider()

    if not reports.empty:

        left, right = st.columns(2)

        with left:

            st.subheader(t("reports_by_category"))

            category_chart = reports["category"].value_counts().reset_index()
            category_chart.columns = ["Category", "Count"]

            category_chart["Category"] = category_chart["Category"].apply(
                translate_category
            )

            fig = px.pie(
                category_chart,
                names="Category",
                values="Count",
                hole=0.4
            )

            st.plotly_chart(fig, use_container_width=True)

        with right:

            st.subheader(t("reports_by_status"))

            status_chart = reports["status"].value_counts().reset_index()
            status_chart.columns = ["Status", "Count"]

            status_chart["Status"] = status_chart["Status"].apply(
                translate_status
            )

            fig = px.bar(
                status_chart,
                x="Status",
                y="Count",
                color="Status"
            )

            st.plotly_chart(fig, use_container_width=True)

        st.subheader(t("recent_reports"))

        display_reports = reports.head(5).copy()

        display_reports["category"] = display_reports["category"].apply(
            translate_category
        )

        display_reports["status"] = display_reports["status"].apply(
            translate_status
        )

        display_reports["priority"] = display_reports["priority"].apply(
            translate_priority
        )

        st.dataframe(
            display_reports[
                [
                    "report_code",
                    "category",
                    "location",
                    "priority",
                    "status",
                    "created_at"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(t("no_reports"))


# =====================================================
# SUBMIT REPORT
# =====================================================

elif selected_page == "submit_report":

    st.header("📝 " + t("report_title"))

    with st.form("report_form"):

        full_name = st.text_input(t("full_name"))

        email = st.text_input(t("email"))

        location = st.text_input(t("location"))

        category_options = [
            "Electricity",
            "Water",
            "Cleaning",
            "Roads",
            "Other"
        ]

        category = st.selectbox(
            t("category"),
            category_options,
            format_func=translate_category
        )

        description = st.text_area(t("description"))

        col1, col2 = st.columns(2)

        with col1:
            latitude = st.number_input(
                t("latitude"),
                value=15.5000,
                format="%.6f"
            )

        with col2:
            longitude = st.number_input(
                t("longitude"),
                value=32.5000,
                format="%.6f"
            )

        submitted = st.form_submit_button(t("submit"))

        if submitted:

            if (
                full_name.strip()
                and email.strip()
                and location.strip()
                and description.strip()
            ):

                predicted_category, priority = analyze_report(description)

                if category == "Other":
                    final_category = predicted_category
                else:
                    final_category = category

                report_code = str(uuid.uuid4())

                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO reports (
                        report_code,
                        category,
                        description,
                        location,
                        latitude,
                        longitude,
                        priority,
                        status,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report_code,
                    final_category,
                    description,
                    location,
                    latitude,
                    longitude,
                    priority,
                    "Pending",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                conn.commit()
                conn.close()

                st.success(t("report_success"))

                st.write("**" + t("report_code") + ":**")
                st.code(report_code)

                st.write(
                    f"**{t('category')}:
