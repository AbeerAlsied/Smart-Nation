import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import qrcode
import io
import uuid
import hashlib
import hmac
from datetime import datetime

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="Smart Nation",
    page_icon="🌍",
    layout="wide"
)

DB_NAME = "smart_nation.db"


# =====================================
# DATABASE
# =====================================

def get_db():
    return sqlite3.connect(DB_NAME)


def initialize_database():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS identities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identity_code TEXT UNIQUE,
        full_name TEXT,
        email TEXT,
        department TEXT,
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

    # Support databases created by older versions
    columns = [
        row[1] for row in cursor.execute(
            "PRAGMA table_info(reports)"
        ).fetchall()
    ]

    if "latitude" not in columns:
        cursor.execute(
            "ALTER TABLE reports ADD COLUMN latitude REAL"
        )

    if "longitude" not in columns:
        cursor.execute(
            "ALTER TABLE reports ADD COLUMN longitude REAL"
        )

    conn.commit()
    conn.close()


initialize_database()


# =====================================
# AI CLASSIFICATION
# =====================================

def analyze_report(description):

    text = description.lower()

    categories = {
        "Electricity": [
            "electricity", "power", "light",
            "كهرباء", "إنارة"
        ],

        "Water": [
            "water", "leak", "pipe",
            "مياه", "تسريب", "ماسورة"
        ],

        "Cleaning": [
            "garbage", "waste", "trash",
            "نفايات", "نظافة", "قمامة"
        ],

        "Roads": [
            "road", "street", "pothole",
            "طريق", "شارع", "حفرة"
        ]
    }

    for category, keywords in categories.items():

        if any(word in text for word in keywords):

            return category, "High"

    return "Other", "Normal"


# =====================================
# QR GENERATOR
# =====================================

def generate_qr(data):

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    output = io.BytesIO()

    image.save(output, format="PNG")

    return output.getvalue()


# =====================================
# LOAD DATA
# =====================================

def load_identities():

    conn = get_db()

    data = pd.read_sql_query(
        "SELECT * FROM identities ORDER BY id DESC",
        conn
    )

    conn.close()

    return data


def load_reports():

    conn = get_db()

    data = pd.read_sql_query(
        "SELECT * FROM reports ORDER BY id DESC",
        conn
    )

    conn.close()

    return data


# =====================================
# DESIGN
# =====================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

.main-title {
    font-size: 40px;
    font-weight: bold;
    color: #123456;
    text-align: center;
}

.subtitle {
    color: #64748b;
    text-align: center;
    font-size: 17px;
}

div[data-testid="stMetric"] {
    background-color: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}

.stButton button {
    background-color: #123456;
    color: white;
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)


# =====================================
# HEADER
# =====================================

st.markdown(
    '<div class="main-title">🌍 SMART NATION</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Integrated Digital Transformation Platform</div>',
    unsafe_allow_html=True
)

st.write("")


# =====================================
# LANGUAGE
# =====================================

language = st.sidebar.selectbox(
    "Language / اللغة",
    ["English", "العربية"]
)

arabic = language == "العربية"


# =====================================
# NAVIGATION
# =====================================

if arabic:

    menu = [
        "🏠 الرئيسية",
        "🪪 الهوية الرقمية",
        "🔍 التحقق من الهوية",
        "🏙️ المدينة الذكية",
        "🗺️ خريطة المدينة",
        "🤖 الذكاء الاصطناعي",
        "📊 لوحة الإدارة"
    ]

else:

    menu = [
        "🏠 Home",
        "🪪 Digital Identity",
        "🔍 Verify Identity",
        "🏙️ Smart City",
        "🗺️ City Map",
        "🤖 AI Intelligence",
        "📊 Admin Dashboard"
    ]


page = st.sidebar.radio(
    "Navigation",
    menu
)


# =====================================
# GET DATA
# =====================================

identities = load_identities()
reports = load_reports()


# =====================================
# HOME
# =====================================

if page in ["🏠 Home", "🏠 الرئيسية"]:

    st.subheader(
        "منصة المجتمع الرقمي الذكي"
        if arabic else
        "Welcome to Smart Nation"
    )

    st.write(
        "منصة موحدة للهوية الرقمية والخدمات الذكية."
        if arabic else
        "One platform for digital identity and smart city services."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "الهويات الرقمية" if arabic else "Digital Identities",
        len(identities)
    )

    col2.metric(
        "البلاغات" if arabic else "Reports",
        len(reports)
    )

    completed = (
        len(reports[reports["status"] == "Completed"])
        if not reports.empty else 0
    )

    col3.metric(
        "بلاغات مكتملة" if arabic else "Completed Reports",
        completed
    )

    pending = (
        len(reports[reports["status"] == "Pending"])
        if not reports.empty else 0
    )

    col4.metric(
        "بلاغات معلقة" if arabic else "Pending Reports",
        pending
    )

    st.divider()

    st.subheader(
        "عن المشروع" if arabic else "About Smart Nation"
    )

    st.info(
        "يهدف المشروع إلى رقمنة الخدمات وتحسين إدارة المدينة "
        "باستخدام الهوية الرقمية والذكاء الاصطناعي."
        if arabic else
        "Smart Nation transforms traditional services into "
        "digital services using digital identity and AI."
    )

    if not reports.empty:

        st.subheader(
            "إحصائيات البلاغات"
            if arabic else
            "Reports Statistics"
        )

        chart = px.pie(
            reports,
            names="category",
            title="توزيع البلاغات"
            if arabic else
            "Reports Distribution",
            hole=0.45
        )

        st.plotly_chart(
            chart,
            use_container_width=True
        )


# =====================================
# DIGITAL IDENTITY
# =====================================

elif page in [
    "🪪 Digital Identity",
    "🪪 الهوية الرقمية"
]:

    st.header(
        "إنشاء هوية رقمية"
        if arabic else
        "Create Digital Identity"
    )

    with st.form("identity_form"):

        name = st.text_input(
            "الاسم الكامل" if arabic else "Full Name"
        )

        email = st.text_input("Email")

        department = st.selectbox(
            "نوع المستخدم" if arabic else "User Type",
            ["Citizen", "Student", "Employee"]
        )

        submitted = st.form_submit_button(
            "إنشاء الهوية" if arabic else "Create Identity"
        )

        if submitted:

            if not name.strip() or not email.strip():

                st.error("يرجى إدخال جميع البيانات.")

            else:

                identity_code = str(uuid.uuid4())

                conn = get_db()

                try:

                    conn.execute("""
                    INSERT INTO identities
                    (identity_code, full_name, email,
                     department, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        identity_code,
                        name.strip(),
                        email.strip(),
                        department,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    ))

                    conn.commit()

                    st.session_state["new_identity"] = identity_code

                    st.success(
                        "تم إنشاء الهوية الرقمية بنجاح!"
                    )

                except sqlite3.IntegrityError:

                    st.error("تعذر إنشاء الهوية.")

                finally:

                    conn.close()

    if "new_identity" in st.session_state:

        code = st.session_state["new_identity"]

        st.write("Identity Code:", code)

        qr_image = generate_qr(code)

        st.image(qr_image)

        st.download_button(
            "تحميل QR Code",
            data=qr_image,
            file_name="digital_identity.png",
            mime="image/png"
        )


# =====================================
# VERIFY IDENTITY
# =====================================

elif page in [
    "🔍 Verify Identity",
    "🔍 التحقق من الهوية"
]:

    st.header(
        "التحقق من الهوية الرقمية"
        if arabic else
        "Verify Digital Identity"
    )

    code = st.text_input(
        "أدخل رمز الهوية" if arabic else "Enter Identity Code"
    )

    if st.button("تحقق الآن" if arabic else "Verify Now"):

        conn = get_db()

        result = pd.read_sql_query(
            "SELECT * FROM identities WHERE identity_code = ?",
            conn,
            params=(code.strip(),)
        )

        conn.close()

        if not result.empty:

            st.success(
                "الهوية موجودة في النظام."
                if arabic else
                "Identity verified in database."
            )

            st.write("Name:", result.iloc[0]["full_name"])
            st.write("Email:", result.iloc[0]["email"])
            st.write("Type:", result.iloc[0]["department"])

        else:

            st.error(
                "الهوية غير موجودة."
                if arabic else
                "Identity not found."
            )


# =====================================
# SMART CITY
# =====================================

elif page in [
    "🏙️ Smart City",
    "🏙️ المدينة الذكية"
]:

    st.header(
    
