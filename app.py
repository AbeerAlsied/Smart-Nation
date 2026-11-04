import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import qrcode
import io
import uuid
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

    # Compatibility with older database versions
    identity_columns = [
        row[1] for row in cursor.execute(
            "PRAGMA table_info(identities)"
        ).fetchall()
    ]

    if "user_type" not in identity_columns:
        cursor.execute(
            "ALTER TABLE identities ADD COLUMN user_type TEXT"
        )

    report_columns = [
        row[1] for row in cursor.execute(
            "PRAGMA table_info(reports)"
        ).fetchall()
    ]

    if "latitude" not in report_columns:
        cursor.execute(
            "ALTER TABLE reports ADD COLUMN latitude REAL"
        )

    if "longitude" not in report_columns:
        cursor.execute(
            "ALTER TABLE reports ADD COLUMN longitude REAL"
        )

    conn.commit()
    conn.close()


initialize_database()


# =====================================
# CLASSIFICATION
# =====================================

def analyze_report(description):

    text = description.lower()

    categories = {
        "Electricity": [
            "electricity", "power", "light",
            "كهرباء", "إنارة", "انقطاع"
        ],

        "Water": [
            "water", "leak", "pipe",
            "مياه", "تسريب", "ماسورة"
        ],

        "Cleaning": [
            "garbage", "waste", "trash",
            "نفايات", "قمامة", "نظافة"
        ],

        "Roads": [
            "road", "pothole", "street",
            "asphalt", "شارع", "حفرة",
            "طريق", "أسفلت"
        ]
    }

    detected_category = "General"

    for category, keywords in categories.items():

        if any(word in text for word in keywords):
            detected_category = category
            break

    priority = "Normal"

    urgent_keywords = [
        "urgent", "emergency", "danger",
        "fire", "explosion", "عاجل",
        "طوارئ", "خطير", "حريق", "انفجار"
    ]

    if any(word in text for word in urgent_keywords):
        priority = "High"

    return detected_category, priority


# =====================================
# QR CODE
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

def load_reports():

    conn = get_db()

    df = pd.read_sql_query(
        "SELECT * FROM reports ORDER BY id DESC",
        conn
    )

    conn.close()

    return df


def load_identities():

    conn = get_db()

    df = pd.read_sql_query(
        "SELECT * FROM identities ORDER BY id DESC",
        conn
    )

    conn.close()

    return df


# =====================================
# DESIGN
# =====================================

st.markdown("""
<style>

.stApp {
    background-color: #F3F7FA;
}

h1, h2, h3 {
    color: #123456;
}

div[data-testid="stMetric"] {
    background-color: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #DCE5EC;
}

.stButton button {
    background-color: #123456;
    color: white;
    border-radius: 8px;
    border: none;
}

.stButton button:hover {
    background-color: #087E8B;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #E7EFF5;
}

</style>
""", unsafe_allow_html=True)


# =====================================
# HEADER
# =====================================

st.markdown(
    """
    <div style="text-align:center;">
        <h1>🌍 SMART NATION</h1>
        <p style="color:#64748b;font-size:18px;">
            Integrated Digital Transformation Platform
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# =====================================
# NAVIGATION
# =====================================

st.sidebar.title("🌍 Smart Nation Portal")

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard & Analytics",
        "Submit Report",
        "Manage Reports",
        "Digital Identities",
        "Verify Identity",
        "City Map",
        "AI Intelligence"
    ]
)


# =====================================
# 1. DASHBOARD
# =====================================

if menu == "Dashboard & Analytics":

    st.title("📊 Smart Nation Dashboard")

    st.write(
        "Monitor civic reports, infrastructure status, "
        "and digital identity records."
    )

    reports = load_reports()
    identities = load_identities()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Reports", len(reports))

    with col2:
        resolved = (
            len(reports[reports["status"] == "Resolved"])
            if not reports.empty else 0
        )
        st.metric("Resolved Issues", resolved)

    with col3:
        pending = (
            len(reports[reports["status"] != "Resolved"])
            if not reports.empty else 0
        )
        st.metric("Pending / Active", pending)

    with col4:
        st.metric("Digital Identities", len(identities))

    st.divider()

    if not reports.empty:

        col_a, col_b = st.columns(2)

        with col_a:

            st.subheader("Reports by Category")

            fig_cat = px.pie(
                reports,
                names="category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            st.plotly_chart(
                fig_cat,
                use_container_width=True
            )

        with col_b:

            st.subheader("Reports by Status")

            fig_status = px.bar(
                reports,
                x="status",
                color="priority",
                barmode="group"
            )

            st.plotly_chart(
                fig_status,
                use_container_width=True
            )

    else:

        st.info("No reports submitted yet.")


# =====================================
# 2. SUBMIT REPORT
# =====================================

elif menu == "Submit Report":

    st.title("📝 Submit Civic Report")

    st.write(
        "Report infrastructure issues, sanitation problems, "
        "or utility failures."
    )

    with st.form("report_form"):

        description = st.text_area(
            "Issue Description",
            placeholder="Describe the problem..."
        )

        location = st.text_input(
            "Location Name / Address",
            placeholder="Enter location..."
        )

        col1, col2 = st.columns(2)

        with col1:

            latitude = st.number_input(
                "Latitude",
                value=15.500000,
                format="%.6f"
            )

        with col2:

            longitude = st.number_input(
                "Longitude",
                value=32.500000,
                format="%.6f"
            )

        submitted = st.form_submit_button(
            "Submit Report"
        )

        if submitted:

            if not description.strip() or not location.strip():

                st.error(
                    "Please enter the description and location."
                )

            elif not (-90 <= latitude <= 90):

                st.error("Invalid latitude.")

            elif not (-180 <= longitude <= 180):

                st.error("Invalid longitude.")

            else:

                category, priority = analyze_report(
                    description
                )

                report_code = str(uuid.uuid4())

                conn = get_db()

                conn.execute("""
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
                    category,
                    description.strip(),
                    location.strip(),
                    latitude,
                    longitude,
                    priority,
                    "Pending",
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ))

                conn.commit()
                conn.close()

                st.success(
                    "Report submitted successfully!"
                )

                st.info(
                    f"Category: {category} | Priority: {priority}"
                )

                st.write("Report Code:", report_code)


# =====================================
# 3. MANAGE REPORTS
# =====================================

elif menu == "Manage Reports":

    st.title("📋 Manage Reports")

    admin_password = st.secrets.get(
        "ADMIN_PASSWORD", ""
    )

    if not admin_password:

        st.warning(
            "Admin password has not been configured."
        )

    else:

        password = st.text_input(
            "Admin Password",
            type="password"
        )

        if st.button("Login"):

            if hmac.compare_digest(
                password,
                admin_password
            ):

                st.session_state["admin_access"] = True

            else:

                st.error("Incorrect password.")

        if st.session_state.get("admin_access", False):

            st.success("Admin access granted.")

            reports = load_reports()

            if not reports.empty:

                st.dataframe(
                    reports,
                    use_container_width=True
                )

                selected_id = st.selectbox(
                    "Select Report ID",
                    reports["id"].tolist()
                )

                new_status = st.selectbox(
                    "Update Report Status",
                    [
                        "Pending",
                        "In Progress",
                        "Resolved"
                    ]
                )

                if st.button("Save Update"):

                    conn = get_db()

                    conn.execute("""
                        UPDATE reports
                        SET status = ?
                        WHERE id = ?
                    """, (
                        new_status,
                        selected_id
                    ))

                    conn.commit()
                    conn.close()

                    st.success("Report updated.")

                    st.rerun()

                csv_data = reports.to_csv(
                    index=False
                ).encode("utf-8-sig")

                st.download_button(
                    "Download Reports CSV",
                    data=csv_data,
                    file_name="smart_nation_reports.csv",
                    mime="text/csv"
                )

            else:

                st.info("No reports available.")

            if st.button("Logout"):

                st.session_state["admin_access"] = False
                st.rerun()


# =====================================
# 4. DIGITAL IDENTITIES
# =====================================

elif menu == "Digital Identities":

    st.title("🪪 Digital Identity")

    st.write(
        "Create a digital identity and generate a QR code."
    )

    with st.form("identity_form"):

        full_name = st.text_input("Full Name")

        email = st.text_input("Email Address")

        user_type = st.selectbox(
            "User Type",
            ["Citizen", "Student", "Employee"]
        )

        submitted = st.form_submit_button(
            "Create Identity"
        )

        if submitted:

            if not full_name.strip() or not email.strip():

                st.error("Please fill in all fields.")

            elif "@" not in email or "." not in email:

                st.error("Enter a valid email address.")

            else:

                identity_code = str(uuid.uuid4())

                conn = get_db()

                try:

                    conn.execute("""
                        INSERT INTO identities (
                            identity_code,
                            full_name,
                            email,
                            user_type,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        identity_code,
                        full_name.strip(),
                        email.strip(),
                        user_type,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    ))

                    conn.commit()

                    st.session_state["identity_code"] = identity_code

                    st.success(
                        "Digital identity created successfully!"
                    )

                except sqlite3.IntegrityError:

                    st.error("Could not create identity.")

                finally:

                    conn.close()

    if "identity_code" in st.session_state:

        code = st.session_state["identity_code"]

        st.write("Identity Code:", code)

        qr_image = generate_qr(code)

        st.image(
            qr_image,
            caption="Digital Identity QR Code"
        )

        st.download_button(
            "Download QR Code",
            data=qr_image,
            file_name="identity_qr.png",
            mime="image/png"
        )

    st.divider()

    st.subheader("Registered Identities")

    identities = load_identities()

    if not identities.empty:

        st.dataframe(
            identities.drop(columns=["identity_code"]),
            use_container_width=True
        )

    else:

        st.info("No identities registered.")


# =====================================
# 5. VERIFY IDENTITY
# =====================================

elif menu == "Verify Identity":

    st.title("🔍 Verify Digital Identity")

    code = st.text_input(
        "Enter Identity Code"
    )

    if st.button("Verify Identity"):

        if not code.strip():

            st.warning("Enter an identity code.")

        else:

            conn = get_db()

            result = pd.read_sql_query(
                """
                SELECT full_name, email, user_type, created_at
                FROM identities
                WHERE identity_code = ?
                """,
                conn,
                params=(code.strip(),)
            )

            conn.close()

            if not result.empty:

                st.success("Identity found in the database.")

                st.write(
                    "Name:",
                    result.iloc[0]["full_name"]
                )

                st.write(
                    "Email:",
                    result.iloc[0]["email"]
                )

                st.write(
                    "User Type:",
                    result.iloc[0]["user_type"]
                )

            else:

                st.error("Identity not found.")


# =====================================
# 6. CITY MAP
# =====================================

elif menu == "City Map":

    st.title("🗺️ City Reports Map")

    reports = load_reports()

    if not reports.empty:

        map_data = reports.dropna(
            subset=["latitude", "longitude"]
        )

        if not map_data.empty:

            st.map(
                map_data[["latitude", "longitude"]],
                zoom=5
            )

            st.subheader("Report Locations")

            st.dataframe(
                map_data[
                    [
                        "category",
                        "location",
                        "priority",
                        "status"
                    ]
                ],
                use_container_width=True
            )

        else:

            st.info("No geographic locations available.")

    else:

        st.info("No reports available for the map.")


# =====================================
# 7. AI INTELLIGENCE
# =====================================

elif menu == "AI Intelligence":

    st.title("🤖 Smart Report Intelligence")

    st.info(
        "This prototype uses keyword-based rules to classify "
        "reports and estimate their priority. It does not "
        "currently use a trained machine learning model."
    )

    description = st.text_area(
        "Enter a report description"
    )

    if st.button("Analyze Report"):

        if description.strip():

            category, priority = analyze_report(
                description
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Detected Category",
                category
            )

            col2.metric(
                "Priority",
                priority
            )

        else:

            st.warning("Please enter a description.")

    st.divider()

    reports = load_reports()

    st.subheader("Reports Analysis")

    if not reports.empty:

        st.bar_chart(
            reports["category"].value_counts()
        )

    else:

        st.info("No reports available for analysis.")


# =====================================
# FOOTER
# =====================================

st.divider()

st.markdown(
    """
    <div style="text-align:center;color:#64748b;">
        🌍 Smart Nation
        <br>
        Integrated Digital Transformation Platform
        <br>
        Project Prototype
    </div>
    """,
    unsafe_allow_html=True
    )
