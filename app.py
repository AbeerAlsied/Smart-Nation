import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import qrcode
import io
import uuid
import hmac
from datetime import datetime


# =========================================
# PAGE CONFIG
# =========================================

st.set_page_config(
    page_title="Smart Nation",
    page_icon="🌍",
    layout="wide"
)

DB_NAME = "smart_nation.db"


# =========================================
# TRANSLATIONS
# =========================================

translations = {

    "English": {

        "portal": "🌍 Smart Nation Portal",
        "language": "🌐 Language",
        "dashboard": "Dashboard & Analytics",
        "submit": "Submit Report",
        "manage": "Manage Reports",
        "identities": "Digital Identities",
        "verify": "Verify Identity",
        "map": "City Map",
        "ai": "AI Intelligence",

        "subtitle": "Integrated Digital Transformation Platform",
        "dashboard_title": "📊 Smart Nation Dashboard",
        "dashboard_desc": "Monitor civic reports, infrastructure status, and digital identity records.",

        "total_reports": "Total Reports",
        "resolved": "Resolved Issues",
        "pending": "Pending / Active",
        "total_identities": "Digital Identities",

        "category_chart": "Reports by Category",
        "status_chart": "Reports by Status",
        "no_reports": "No reports submitted yet.",

        "submit_title": "📝 Submit Civic Report",
        "submit_desc": "Report infrastructure issues, sanitation problems, or utility failures.",
        "description": "Issue Description",
        "description_placeholder": "Describe the problem in detail...",
        "location": "Location Name / Address",
        "location_placeholder": "Enter location...",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "submit_button": "Submit Report",
        "fill_fields": "Please enter the description and location.",
        "invalid_lat": "Invalid latitude.",
        "invalid_lon": "Invalid longitude.",
        "report_success": "Report submitted successfully!",
        "category": "Category",
        "priority": "Priority",
        "report_code": "Report Code",

        "manage_title": "📋 Manage Reports",
        "admin_not_configured": "Admin password has not been configured.",
        "admin_password": "Admin Password",
        "login": "Login",
        "incorrect_password": "Incorrect password.",
        "admin_granted": "Admin access granted.",
        "select_report": "Select Report ID",
        "update_status": "Update Report Status",
        "save_update": "Save Update",
        "report_updated": "Report updated successfully.",
        "download_csv": "Download Reports CSV",
        "no_reports_available": "No reports available.",
        "logout": "Logout",

        "identities_title": "🪪 Digital Identity",
        "identity_desc": "Create a digital identity and generate a QR code.",
        "full_name": "Full Name",
        "email": "Email Address",
        "user_type": "User Type",
        "citizen": "Citizen",
        "student": "Student",
        "employee": "Employee",
        "create_identity": "Create Identity",
        "fill_identity": "Please fill in all fields.",
        "invalid_email": "Enter a valid email address.",
        "duplicate_email": "This email already has a registered identity.",
        "identity_success": "Digital identity created successfully!",
        "identity_code": "Identity Code",
        "download_qr": "Download QR Code",
        "qr_caption": "Digital Identity QR Code",
        "registered_identities": "Registered Identities",
        "no_identities": "No identities registered.",

        "verify_title": "🔍 Verify Digital Identity",
        "enter_code": "Enter Identity Code",
        "verify_button": "Verify Identity",
        "enter_identity_code": "Please enter an identity code.",
        "identity_found": "Identity found in the database.",
        "identity_not_found": "Identity not found.",
        "name": "Name",

        "map_title": "🗺️ City Reports Map",
        "report_locations": "Report Locations",
        "no_locations": "No geographic locations available.",
        "no_map_reports": "No reports available for the map.",

        "ai_title": "🤖 Smart Report Intelligence",
        "ai_notice": "This prototype uses keyword-based rules to classify reports and estimate their priority. It does not currently use a trained machine learning model.",
        "analyze_description": "Enter a report description",
        "analyze_button": "Analyze Report",
        "detected_category": "Detected Category",
        "analysis": "Reports Analysis",
        "enter_description": "Please enter a description.",

        "footer": "Integrated Digital Transformation Platform",
        "prototype": "Project Prototype",

        "Electricity": "Electricity",
        "Water": "Water",
        "Cleaning": "Cleaning",
        "Roads": "Roads",
        "General": "General",

        "Pending": "Pending",
        "In Progress": "In Progress",
        "Resolved": "Resolved",

        "High": "High",
        "Normal": "Normal",

        "email_column": "Email",
        "created_at": "Created At",
        "status": "Status",
        "report_id": "Report ID",
        "user_type_column": "User Type"
    },

    "العربية": {

        "portal": "🌍 بوابة الأمة الذكية",
        "language": "🌐 اللغة",
        "dashboard": "لوحة التحكم والإحصائيات",
        "submit": "تقديم بلاغ",
        "manage": "إدارة البلاغات",
        "identities": "الهويات الرقمية",
        "verify": "التحقق من الهوية",
        "map": "خريطة المدينة",
        "ai": "الذكاء الاصطناعي",

        "subtitle": "منصة التحول الرقمي المتكامل",
        "dashboard_title": "📊 لوحة تحكم الأمة الذكية",
        "dashboard_desc": "متابعة بلاغات المواطنين وحالة البنية التحتية وسجلات الهوية الرقمية.",

        "total_reports": "إجمالي البلاغات",
        "resolved": "البلاغات المحلولة",
        "pending": "البلاغات النشطة",
        "total_identities": "الهويات الرقمية",

        "category_chart": "البلاغات حسب التصنيف",
        "status_chart": "البلاغات حسب الحالة",
        "no_reports": "لا توجد بلاغات حتى الآن.",

        "submit_title": "📝 تقديم بلاغ مدني",
        "submit_desc": "يمكنك الإبلاغ عن مشكلات البنية التحتية أو النظافة أو الخدمات العامة.",
        "description": "وصف المشكلة",
        "description_placeholder": "اكتب وصفاً تفصيلياً للمشكلة...",
        "location": "اسم الموقع أو العنوان",
        "location_placeholder": "أدخل موقع المشكلة...",
        "latitude": "خط العرض",
        "longitude": "خط الطول",
        "submit_button": "إرسال البلاغ",
        "fill_fields": "يرجى إدخال وصف المشكلة والموقع.",
        "invalid_lat": "خط العرض غير صحيح.",
        "invalid_lon": "خط الطول غير صحيح.",
        "report_success": "تم إرسال البلاغ بنجاح!",
        "category": "التصنيف",
        "priority": "الأولوية",
        "report_code": "رمز البلاغ",

        "manage_title": "📋 إدارة البلاغات",
        "admin_not_configured": "لم يتم إعداد كلمة مرور المسؤول.",
        "admin_password": "كلمة مرور المسؤول",
        "login": "تسجيل الدخول",
        "incorrect_password": "كلمة المرور غير صحيحة.",
        "admin_granted": "تم منح صلاحية المسؤول.",
        "select_report": "اختر رقم البلاغ",
        "update_status": "تحديث حالة البلاغ",
        "save_update": "حفظ التحديث",
        "report_updated": "تم تحديث البلاغ بنجاح.",
        "download_csv": "تحميل البلاغات بصيغة CSV",
        "no_reports_available": "لا توجد بلاغات متاحة.",
        "logout": "تسجيل الخروج",

        "identities_title": "🪪 الهوية الرقمية",
        "identity_desc": "أنشئ هوية رقمية واحصل على رمز QR خاص بها.",
        "full_name": "الاسم الكامل",
        "email": "البريد الإلكتروني",
        "user_type": "نوع المستخدم",
        "citizen": "مواطن",
        "student": "طالب",
        "employee": "موظف",
        "create_identity": "إنشاء الهوية",
        "fill_identity": "يرجى ملء جميع الحقول.",
        "invalid_email": "يرجى إدخال بريد إلكتروني صحيح.",
        "duplicate_email": "هذا البريد الإلكتروني مسجل بالفعل.",
        "identity_success": "تم إنشاء الهوية الرقمية بنجاح!",
        "identity_code": "رمز الهوية",
        "download_qr": "تحميل رمز QR",
        "qr_caption": "رمز QR للهوية الرقمية",
        "registered_identities": "اله        f"Category: {category} | Priority: {priority}"
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
