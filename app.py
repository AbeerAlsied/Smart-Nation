import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import sqlite3, pandas as pd, plotly.express as px, pydeck as pdk
import qrcode, io, uuid, hashlib, hmac, secrets, os, re, unicodedata
from datetime import datetime

# =========================================================
# WNS - White Nile Smart
# =========================================================
st.set_page_config(page_title="WNS | النيل الأبيض الذكية", page_icon="🌍", layout="wide")
DB_NAME = "smart_nation.db"

# ------------------------- Theme -------------------------
st.markdown("""
<style>
.stApp{background:#EAF4F8}
section[data-testid="stSidebar"]{background:#12304A}
section[data-testid="stSidebar"] *{color:white}
h1,h2,h3,h4{color:#12304A}
.stButton>button{background:linear-gradient(90deg,#079B91,#087E8B);color:white;border:0;border-radius:10px;padding:10px 18px;font-weight:bold}
.stButton>button:hover{background:#066B72;color:white}
.stDownloadButton>button{background:#12304A;color:white;border-radius:10px}
div[data-testid="stMetric"]{background:white;padding:16px;border-radius:14px;border-left:5px solid #079B91;box-shadow:0 3px 12px #0000000d}
div[data-testid="stForm"],div[data-testid="stExpander"]{background:white;border-radius:14px}
div[data-testid="stForm"]{padding:18px;border:1px solid #DCEAF2}
.stProgress>div>div{background:#079B91}
.wns-header{background:linear-gradient(110deg,#12304A,#087E8B);padding:24px;border-radius:16px;color:white;text-align:center;margin-bottom:20px}
.wns-header h1,.wns-header h3{color:white!important}
.wns-card{background:white;border-radius:14px;padding:20px;margin:10px 0;border:1px solid #DCEAF2}
</style>
""", unsafe_allow_html=True)

if "language" not in st.session_state:
    st.session_state.language = "العربية"
language = st.sidebar.selectbox("🌐 اللغة / Language", ["العربية", "English"],
    index=0 if st.session_state.language == "العربية" else 1)
st.session_state.language = language
AR = language == "العربية"

def label(ar, en):
    return ar if AR else en

# Direction styling: direction is applied to content without relying on
# CSS left/right positioning, which Streamlit controls internally.
if AR:
    st.markdown("""
    <style>
    .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],
    [data-testid="stMainBlockContainer"],section[data-testid="stSidebar"]{
      direction:rtl!important;text-align:right!important}
    section[data-testid="stSidebar"] *{text-align:right!important}
    .stMarkdown,h1,h2,h3,h4,h5,p,label,textarea,input,
    div[data-baseweb="select"],div[data-testid="stForm"],
    div[data-testid="stExpander"],div[data-testid="stAlert"],
    div[data-testid="stMetric"],div[data-testid="stRadio"],
    div[data-testid="stCheckbox"],div[data-testid="stTabs"]{
      direction:rtl!important;text-align:right!important}
    textarea,input{direction:rtl!important}
    </style>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],
    [data-testid="stMainBlockContainer"],section[data-testid="stSidebar"]{
      direction:ltr!important;text-align:left!important}
    section[data-testid="stSidebar"] *{text-align:left!important}
    textarea,input{direction:ltr!important;text-align:left!important}
    </style>""", unsafe_allow_html=True)

# ---------------- Categories / departments ----------------
DEPARTMENTS = {
 "Electricity":{"ar":"هيئة الكهرباء","en":"Electricity Authority","icon":"⚡"},
 "Water":{"ar":"هيئة مياه ولاية النيل الأبيض","en":"White Nile Water Authority","icon":"💧"},
 "Cleaning":{"ar":"إدارة النظافة بالمحلية","en":"Local Cleaning Department","icon":"🗑️"},
 "Roads":{"ar":"إدارة الطرق والجسور","en":"Roads and Bridges Department","icon":"🛣️"},
 "Sewage":{"ar":"إدارة الصرف الصحي","en":"Sewage Department","icon":"🚰"},
 "Health":{"ar":"إدارة الصحة","en":"Health Department","icon":"🏥"},
 "Environment":{"ar":"إدارة البيئة","en":"Environment Department","icon":"🌳"},
 "Emergency":{"ar":"الدفاع المدني","en":"Civil Defense","icon":"🚒"},
 "Traffic":{"ar":"شرطة المرور","en":"Traffic Police","icon":"🚦"},
 "Education":{"ar":"إدارة التعليم","en":"Education Department","icon":"🏫"},
 "Other":{"ar":"غرفة المتابعة والشرطة العامة","en":"General Follow-up & Police Office","icon":"📋"}
}
CITIES = {
 "كوستي":(13.16290,32.66347),"ربك":(13.18087,32.73999),
 "الدويم":(14.00120,32.31160),"القطينة":(14.86480,32.36680),
 "تندلتي":(13.01667,31.86667),"مرابة":(12.35000,32.18333),
 "الجزيرة أبا":(13.31930,32.61320),"الكوة":(13.74630,32.49960),
 "ود الزاكي":(14.46190,32.20650)
}
PRIORITIES = {"Normal":"🟢 عادي" if AR else "🟢 Normal",
 "Important":"🟡 مهم" if AR else "🟡 Important",
 "Urgent":"🟠 عاجل" if AR else "🟠 Urgent",
 "Emergency":"🔴 طارئ" if AR else "🔴 Emergency"}
STATUSES = {"Pending":"🟡 قيد الانتظار" if AR else "🟡 Pending",
 "In Progress":"🔵 جارٍ المعالجة" if AR else "🔵 In Progress",
 "Resolved":"🟢 تمت المعالجة" if AR else "🟢 Resolved"}

CATEGORY_KEYWORDS = {
 "Electricity":["كهرباء","كهربا","النور","تيار","انارة","عمود كهرباء","سلك","اسلاك","لمبات","ضلمه","electricity","power","outage","electric"],
 "Water":["مياه","موية","مويا","مويه","حنفيه","حنفية","ماسوره","انبوب","تسريب","تسرب مياه","انقطاع المياه","water","leak","pipe"],
 "Cleaning":["نفايات","قمامه","زباله","زبل","وسخ","اوساخ","كوشه","نظافه","مخلفات","روائح","garbage","waste","trash"],
 "Roads":["شارع","شوارع","حفره","طريق","اسفلت","مكسر","محفر","مطب","رصيف","road","pothole","street"],
 "Sewage":["صرف صحي","مجاري","طفح","مجرى","بالوعه","انسداد المجاري","sewage","drainage"],
 "Health":["مستشفى","مركز صحي","مرض","وباء","كوليرا","اسهالات","اسهال","إسهال","إسهالات","تسمم","عياده","صحه","ادويه","فيروس","عدوى","حمى","علاج","اصابات","hospital","health","clinic","cholera","epidemic"],
 "Environment":["تلوث","بيئه","حرق نفايات","دخان المصانع","تلوث الهواء","pollution","environment"],
 "Emergency":["حريق","نار","دخان","انفجار","انهيار","غرق","فيضان","حادث خطير","emergency","fire","explosion"],
 "Traffic":["مرور","حادث مروري","اشاره مرور","ازدحام","اختناق مروري","اشارات","traffic","accident"],
 "Education":["مدرسه","مدارس","تعليم","فصل دراسي","معلم","مدرس","school","education"],
 "Other":["جريمة","جريمه","سرقة","سرقه","اعتداء","شجار","احتيال","نهب","تهديد","شرطة","شرطه","بلاغ جنائي","مشاجرة","أمن","حرامي","سطو","crime","theft","police","robbery"]
}
CRITICAL_TERMS = ["حريق","نار","انفجار","صعق","سلك عريان","سلك مكشوف","سلك واقع","عمود واقع","عمود ساقط","انهيار","غرق","فيضان","تسمم","وباء","كوليرا","سرقة","جريمة","قتل","سطو","fire","explosion","emergency","crime"]
URGENT_TERMS = ["انقطاع المياه","انقطاع الكهرباء","المويه قاطعه","النور قاطع","ماسوره مكسوره","طفح المجاري","تسرب كبير","حادث","اسهالات","no water","no electricity"]
IMPORTANT_TERMS = ["مدرسه","مستشفى","مركز صحي","الحي بالكامل","كل الحي","شارع رئيسي","عدد كبير","hospital","whole neighborhood"]

# ------------------------- Database -------------------------
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def add_column_if_missing(conn, table, column, definition):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def normalize_text(value):
    text = unicodedata.normalize("NFKC", str(value or "").lower().strip())
    text = re.sub(r"[ً-ٰٟ]", "", text).replace("ـ", "")
    text = text.translate(str.maketrans({"أ":"ا","إ":"ا","آ":"ا","ى":"ي","ة":"ه"}))
    return re.sub(r"\s+", " ", text)

def analyze_report(description):
    text = normalize_text(description)
    scores, detected = {}, []
    for cat, words in CATEGORY_KEYWORDS.items():
        matches = [w for w in words if normalize_text(w) in text]
        scores[cat] = len(matches)
        detected.extend(matches)
    best = max(scores, key=scores.get) if scores else "Other"
    if scores.get(best, 0) == 0:
        best = "Other"
    critical = any(normalize_text(x) in text for x in CRITICAL_TERMS)
    urgent = any(normalize_text(x) in text for x in URGENT_TERMS)
    important = any(normalize_text(x) in text for x in IMPORTANT_TERMS)
    if critical: priority, risk = "Emergency", 95
    elif urgent: priority, risk = "Urgent", 75
    elif important: priority, risk = "Important", 50
    else: priority, risk = "Normal", 20
    return best, priority, risk, DEPARTMENTS[best]["ar"], detected[:10], critical

def initialize_database():
    conn = get_connection()
    conn.execute("""CREATE TABLE IF NOT EXISTS identities(
      id INTEGER PRIMARY KEY AUTOINCREMENT, identity_code TEXT UNIQUE,
      full_name TEXT NOT NULL,email TEXT NOT NULL UNIQUE,user_type TEXT,
      password_hash TEXT DEFAULT '',created_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS reports(
      id INTEGER PRIMARY KEY AUTOINCREMENT,report_code TEXT UNIQUE,
      identity_code TEXT DEFAULT '',category TEXT,description TEXT,location TEXT,
      latitude REAL,longitude REAL,priority TEXT,status TEXT,created_at TEXT)""")
    for col, definition in {
      "department_id":"INTEGER","department_name":"TEXT DEFAULT ''",
      "city":"TEXT DEFAULT ''","neighborhood":"TEXT DEFAULT ''",
      "risk_score":"INTEGER DEFAULT 0","is_critical":"INTEGER DEFAULT 0",
      "updated_at":"TEXT DEFAULT ''"}.items():
        add_column_if_missing(conn,"reports",col,definition)
    conn.execute("""CREATE TABLE IF NOT EXISTS departments(
      id INTEGER PRIMARY KEY AUTOINCREMENT,department_key TEXT UNIQUE,
      name_ar TEXT,name_en TEXT,is_active INTEGER DEFAULT 1)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS staff_users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE,full_name TEXT,
      password_hash TEXT,role TEXT,department_id INTEGER,city TEXT DEFAULT '',
      is_active INTEGER DEFAULT 1)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS admin_notifications(
      id INTEGER PRIMARY KEY AUTOINCREMENT,report_id INTEGER,title TEXT NOT NULL,
      message TEXT NOT NULL,created_at TEXT NOT NULL,is_read INTEGER DEFAULT 0,
      recipient_type TEXT DEFAULT 'admin',department_id INTEGER)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS citizen_notifications(
      id INTEGER PRIMARY KEY AUTOINCREMENT,identity_code TEXT,report_id INTEGER,
      title TEXT,message TEXT,created_at TEXT,is_read INTEGER DEFAULT 0)""")
    add_column_if_missing(conn,"admin_notifications","recipient_type","TEXT DEFAULT 'admin'")
    add_column_if_missing(conn,"admin_notifications","department_id","INTEGER")
    for key,item in DEPARTMENTS.items():
        conn.execute("""INSERT OR IGNORE INTO departments(department_key,name_ar,name_en)
          VALUES(?,?,?)""",(key,item["ar"],item["en"]))
    # Backfill is intentionally after keyword dictionaries and normalize_text exist.
    rows = conn.execute("""SELECT id,category,description FROM reports
      WHERE department_id IS NULL OR department_id='' OR department_name IS NULL OR department_name=''""").fetchall()
    for rid, cat, desc in rows:
        if not cat or cat == "Auto":
            detected, *_ = analyze_report(desc or "")
            cat = detected
        if cat not in DEPARTMENTS:
            cat = "Other"
        dept = conn.execute("SELECT id,name_ar FROM departments WHERE department_key=?",(cat,)).fetchone()
        if dept:
            conn.execute("UPDATE reports SET category=?,department_id=?,department_name=? WHERE id=?",
                         (cat,dept[0],dept[1],rid))
    conn.commit()
    conn.close()

# Critical fix: initialize only after text engine definitions are ready.
initialize_database()

# ------------------------- Security / helpers -------------------------
def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),200000)
    return salt+"$"+digest.hex()

def verify_password(password, stored):
    try:
        salt, expected = stored.split("$",1)
        actual = hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),200000).hex()
        return hmac.compare_digest(actual,expected)
    except Exception:
        return False

def get_department_id(category):
    conn=get_connection()
    row=conn.execute("SELECT id FROM departments WHERE department_key=?",(category,)).fetchone()
    conn.close()
    return row[0] if row else None

def load_reports():
    conn=get_connection()
    df=pd.read_sql_query("""SELECT * FROM reports ORDER BY
      CASE priority WHEN 'Emergency' THEN 1 WHEN 'Urgent' THEN 2
      WHEN 'Important' THEN 3 ELSE 4 END,id DESC""",conn)
    conn.close()
    return df

def load_identities():
    conn=get_connection()
    df=pd.read_sql_query("SELECT id,identity_code,full_name,email,user_type,created_at FROM identities ORDER BY id DESC",conn)
    conn.close()
    return df

def create_notification(report_id,title,message,recipient_type="admin",department_id=None):
    conn=get_connection()
    conn.execute("""INSERT INTO admin_notifications
      (report_id,title,message,created_at,is_read,recipient_type,department_id)
      VALUES(?,?,?,?,0,?,?)""",(report_id,title,message,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),recipient_type,department_id))
    conn.commit(); conn.close()

def notify_citizen(identity_code,report_id,title,message):
    conn=get_connection()
    conn.execute("""INSERT INTO citizen_notifications(identity_code,report_id,title,message,created_at)
      VALUES(?,?,?,?,?)""",(identity_code,report_id,title,message,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); conn.close()

def load_notifications(department_id=None):
    conn=get_connection()
    if department_id is None:
        query="""SELECT n.*,r.category,r.location,r.priority,r.status FROM admin_notifications n
          LEFT JOIN reports r ON n.report_id=r.id WHERE n.recipient_type='admin' ORDER BY n.id DESC"""
        df=pd.read_sql_query(query,conn)
    else:
        query="""SELECT n.*,r.category,r.location,r.priority,r.status FROM admin_notifications n
          LEFT JOIN reports r ON n.report_id=r.id WHERE n.recipient_type='department'
          AND n.department_id=? ORDER BY n.id DESC"""
        df=pd.read_sql_query(query,conn,params=(department_id,))
    conn.close()
    return df

def current_identity():
    code=st.session_state.get("citizen_identity_code")
    if not code: return None
    conn=get_connection()
    row=conn.execute("SELECT identity_code,full_name,email,user_type,created_at FROM identities WHERE identity_code=?",(code,)).fetchone()
    conn.close()
    return row

def logout_citizen():
    st.session_state.pop("citizen_identity_code",None)
    st.session_state.pop("citizen_identity_verified",None)
    st.rerun()

def mask_email(email):
    if not email or "@" not in email: return email
    user,domain=email.split("@",1)
    masked=user[0]+"*"*max(1,len(user)-2)+(user[-1] if len(user)>2 else "")
    return masked+"@"+domain

def seed_default_departments():
    conn=get_connection()
    depts=conn.execute("SELECT id,department_key,name_ar FROM departments").fetchall()
    count=0
    for did,key,name in depts:
        username=f"{key.lower()}_user"
        if not conn.execute("SELECT id FROM staff_users WHERE username=?",(username,)).fetchone():
            conn.execute("""INSERT INTO staff_users(username,full_name,password_hash,role,department_id,city,is_active)
              VALUES(?,?,?,'department',?,'',1)""",
              (username,f"مسؤول {name}",hash_password(f"{key.lower()}12345"),did))
            count+=1
    conn.commit(); conn.close()
    return count

def get_staff():
    uid=st.session_state.get("staff_id")
    if uid == -999 and st.session_state.get("root_admin"):
        return (-999,"admin","مدير النظام","admin",None,"")
    if not uid: return None
    conn=get_connection()
    row=conn.execute("""SELECT id,username,full_name,role,department_id,city
      FROM staff_users WHERE id=? AND is_active=1""",(uid,)).fetchone()
    conn.close()
    return row

def staff_login(username,password):
    conn=get_connection()
    row=conn.execute("SELECT id,password_hash FROM staff_users WHERE username=? AND is_active=1",(username,)).fetchone()
    conn.close()
    if row and verify_password(password,row[1]):
        st.session_state["staff_id"]=row[0]
        st.session_state.pop("root_admin",None)
        return True
    return False

def get_admin_password():
    try: return st.secrets["ADMIN_PASSWORD"]
    except Exception: return os.environ.get("ADMIN_PASSWORD","admin123")

def generate_qr(data):
    qr=qrcode.QRCode(version=1,box_size=8,border=3)
    qr.add_data(data); qr.make(fit=True)
    img=qr.make_image(fill_color="#12304A",back_color="white")
    buf=io.BytesIO(); img.save(buf,format="PNG"); buf.seek(0)
    return buf

def category_name(category):
    item=DEPARTMENTS.get(category,DEPARTMENTS["Other"])
    return item["ar"] if AR else item["en"]

def priority_name(priority): return PRIORITIES.get(priority,priority)
def status_name(status): return STATUSES.get(status,status)

# ------------------------- Assistant -------------------------
def smart_assistant(question):
    text=normalize_text(question)
    if not text:
        return label("يرجى كتابة سؤالك لنتمكن من مساعدتك.","Please type your question so we can assist you.")
    if any(x in text for x in ["كيف ارسل","تقديم بلاغ","طريقة البلاغ","كيف اشتكي","ارسل بلاغ","اعمل بلاغ","خطوات البلاغ"]):
        return label("لإرسال بلاغ جديد:\n1. سجل دخولك أو أنشئ هوية رقمية.\n2. افتح صفحة (إرسال بلاغ).\n3. اختر منطقتك واكتب وصف المشكلة.\n4. سيوجه النظام البلاغ للجهة المختصة.",
          "To submit a report: log in or create a digital identity, open Submit Report, select your location and describe the issue. WNS routes it to the responsible department.")
    if any(x in text for x in ["متابعة","متابعه","اين بلاغي","حالة البلاغ","تتبع","بلاغاتي","نتيجة البلاغ"]):
        return label("يمكنك متابعة بلاغاتك وتحديثاتها من صفحة (خدماتي وبلاغاتي) بعد تسجيل الدخول.",
          "Track your reports and updates in My Services after logging in.")
    if any(x in text for x in ["جهة","جهات","مسؤول","من يتعامل","مين المسؤول","اختصاص"]):
        return label("تربط المنصة البلاغات بالجهات المعنية مثل المياه والكهرباء والنظافة والطرق والصحة والمرور والدفاع المدني حسب وصف البلاغ.",
          "WNS routes reports to the relevant authority based on the report description.")
    scores={}; details={}
    for cat,words in CATEGORY_KEYWORDS.items():
        matched=[w for w in words if normalize_text(w) in text]
        if matched: scores[cat]=len(matched); details[cat]=matched
    if scores:
        ordered=sorted(scores.items(),key=lambda item:item[1],reverse=True)
        top_cat=ordered[0][0]
        top_info=DEPARTMENTS.get(top_cat,DEPARTMENTS["Other"])
        top_name=top_info["ar"] if AR else top_info["en"]
        if len(ordered)>1:
            second_cat=ordered[1][0]
            second_info=DEPARTMENTS.get(second_cat,DEPARTMENTS["Other"])
            second_name=second_info["ar"] if AR else second_info["en"]
            return label(
              f"سؤالك يتعلق بأكثر من موضوع. ({details[top_cat][0]}) يتبع لـ {top_name}، بينما ({details[second_cat][0]}) يتبع لـ {second_name}. يُفضّل تقديم بلاغ منفصل لكل مشكلة.",
              f"Your question covers multiple topics: {top_name} and {second_name}. Separate reports will help each authority handle its issue.")
        return label(f"هذا الموضوع يقع تحت اختصاص **{top_name}** {top_info['icon']}. يمكنك تقديم البلاغ وسيوجهه النظام تلقائياً.",
          f"This topic falls under **{top_name}**. Submit a report and WNS will route it automatically.")
    return label("أنا مساعد النيل الأبيض الذكي 🌍. اسألني عن تقديم البلاغات أو متابعتها أو عن الكهرباء والمياه والطرق والنظافة والصحة والمرور والدفاع المدني.",
      "I am the White Nile Smart Assistant. Ask about submitting or tracking reports, or about public services.")

# ------------------------- Header / navigation -------------------------
st.markdown("""<div class="wns-header"><h1>🌍 النيل الأبيض الذكية</h1>
<h3>WHITE NILE SMART (WNS)</h3><p>منصة التحول الرقمي والخدمات الحكومية الذكية</p></div>""",unsafe_allow_html=True)

pages={
 "digital_identities":label("الهويات الرقمية","Digital Identities"),
 "verify_identity":label("التحقق من الهوية","Verify Identity"),
 "submit_report":label("إرسال بلاغ","Submit Report"),
 "my_services":label("خدماتي وبلاغاتي","My Services"),
 "dashboard":label("لوحة التحكم","Dashboard"),
 "city_map":label("خريطة المدينة","City Map"),
 "assistant":label("مساعد النيل الأبيض","Smart Assistant"),
 "manage_reports":label("إدارة البلاغات والإشعارات","Reports & Notifications")
}
if st.session_state.get("navigation_target") in pages:
    default_key=st.session_state.pop("navigation_target")
    default_index=list(pages).index(default_key)
else: default_index=0
selected_page=st.sidebar.radio(label("القائمة الرئيسية","Main Navigation"),list(pages),index=default_index,format_func=lambda k:pages[k])

# =========================================================
# DASHBOARD
# =========================================================
if selected_page=="dashboard":
    st.header("📊 "+label("لوحة التحكم والتحليلات","Dashboard"))
    reports=load_reports(); total=len(reports)
    pending=int((reports.status=="Pending").sum()) if total else 0
    resolved=int((reports.status=="Resolved").sum()) if total else 0
    urgent=int(reports.priority.isin(["Urgent","Emergency"]).sum()) if total else 0
    c1,c2,c3,c4=st.columns(4)
    c1.metric(label("إجمالي البلاغات","Total Reports"),total)
    c2.metric(label("قيد الانتظار","Pending"),pending)
    c3.metric(label("تمت المعالجة","Resolved"),resolved)
    c4.metric(label("البلاغات العاجلة والطارئة","Urgent Reports"),urgent)
    if not reports.empty:
        left,right=st.columns(2)
        with left:
            st.subheader(label("البلاغات حسب النوع","Reports by Category"))
            chart=reports.category.value_counts().reset_index(); chart.columns=["Category","Count"]
            chart.Category=chart.Category.apply(category_name)
            st.plotly_chart(px.pie(chart,names="Category",values="Count",hole=.45),use_container_width=True)
        with right:
            st.subheader(label("البلاغات حسب الحالة","Reports by Status"))
            chart=reports.status.value_counts().reset_index(); chart.columns=["Status","Count"]
            chart.Status=chart.Status.apply(status_name)
            st.plotly_chart(px.bar(chart,x="Status",y="Count"),use_container_width=True)
        st.subheader(label("أحدث البلاغات","Recent Reports"))
        display=reports.head(10).copy()
        display["category"]=display.category.apply(category_name)
        display["priority"]=display.priority.apply(priority_name)
        display["status"]=display.status.apply(status_name)
        st.dataframe(display[["report_code","category","location","priority","status"]],use_container_width=True,hide_index=True)
    else: st.info(label("لا توجد بلاغات مسجلة.","No reports yet."))

# =========================================================
# DIGITAL IDENTITIES
# =========================================================
elif selected_page=="digital_identities":
    st.header("🪪 "+label("إنشاء الهوية الرقمية","Digital Identity"))
    tab1,tab2=st.tabs([label("إنشاء حساب","Create Account"),label("تسجيل الدخول","Login")])
    with tab1:
        with st.form("create_identity"):
            name=st.text_input(label("الاسم الكامل","Full Name"))
            email=st.text_input(label("البريد الإلكتروني","Email")).strip().lower()
            user_type=st.selectbox(label("نوع المستخدم","User Type"),["Citizen","Student","Employee","Other"])
            password=st.text_input(label("كلمة المرور","Password"),type="password")
            confirm=st.text_input(label("تأكيد كلمة المرور","Confirm Password"),type="password")
            submit=st.form_submit_button(label("إنشاء الهوية الرقمية","Create Identity"))
        if submit:
            if not name.strip() or not email or not password: st.error(label("يرجى تعبئة جميع الحقول.","Fill all fields."))
            elif len(password)<8: st.error(label("كلمة المرور يجب أن تكون 8 أحرف على الأقل.","Password must be at least 8 characters."))
            elif password!=confirm: st.error(label("كلمتا المرور غير متطابقتين.","Passwords do not match."))
            else:
                conn=get_connection()
                try:
                    code="WNS-"+str(uuid.uuid4())[:8].upper()
                    conn.execute("""INSERT INTO identities(identity_code,full_name,email,user_type,password_hash,created_at)
                      VALUES(?,?,?,?,?,?)""",(code,name.strip(),email,user_type,hash_password(password),datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.session_state["citizen_identity_code"]=code
                    st.session_state["citizen_identity_verified"]=True
                    st.success(label("تم إنشاء هويتك الرقمية بنجاح!","Identity created successfully!"))
                    st.code(code); st.image(generate_qr(code).getvalue(),width=180)
                except sqlite3.IntegrityError: st.error(label("هذا البريد مسجل بالفعل.","Email already exists."))
                finally: conn.close()
    with tab2:
        with st.form("citizen_login"):
            email=st.text_input(label("البريد الإلكتروني","Email")).strip().lower()
            password=st.text_input(label("كلمة المرور","Password"),type="password")
            login=st.form_submit_button(label("تسجيل الدخول","Login"))
        if login:
            conn=get_connection(); row=conn.execute("SELECT identity_code,password_hash FROM identities WHERE email=?",(email,)).fetchone(); conn.close()
            if row and verify_password(password,row[1]):
                st.session_state["citizen_identity_code"]=row[0]; st.session_state["citizen_identity_verified"]=True
                st.success(label("تم تسجيل الدخول بنجاح.","Login successful.")); st.rerun()
            else: st.error(label("بيانات الدخول غير صحيحة.","Incorrect login details."))

# =========================================================
# SUBMIT REPORT
# =========================================================
elif selected_page=="submit_report":
    st.header("📝 "+label("إرسال بلاغ جديد","Submit New Report"))
    identity=current_identity()
    if not identity:
        st.warning(label("يجب تسجيل الدخول أولاً.","Please log in first."))
        if st.button(label("الذهاب للهويات الرقمية","Go to Digital Identity")):
            st.session_state["navigation_target"]="digital_identities"; st.rerun()
    else:
        st.success(f"{label('مرحباً','Welcome')} {identity[1]}")
        st.info(label("سيتم ربط بلاغك بهويتك الرقمية وإرساله تلقائياً للجهة المختصة.","Your report will be linked to your identity and routed to the responsible department."))
        col_geo,col_status=st.columns([1,2])
        with col_geo:
            try: detected=streamlit_geolocation()
            except Exception: detected=None
        with col_status:
            if isinstance(detected,dict) and detected.get("latitude") is not None and detected.get("longitude") is not None:
                st.session_state["report_lat"]=float(detected["latitude"])
                st.session_state["report_lon"]=float(detected["longitude"])
                st.success(f"📍 {label('تم تحديد موقعك الجغرافي','Location detected')}: ({detected['latitude']:.4f}, {detected['longitude']:.4f})")
            else: st.caption(label("💡 حدّد موقعك من الزر أو اختر المدينة أدناه.","Use location detection or select a city below."))
        with st.form("new_report_form"):
            city=st.selectbox(label("المدينة / المحلية","City / Locality"),list(CITIES),index=list(CITIES).index("كوستي"))
            neighborhood=st.text_input(label("الحي أو الشارع","Neighborhood / Street"))
            landmark=st.text_input(label("أقرب معلم معروف (اختياري)","Nearest Landmark (optional)"))
            category_options=["Auto"]+list(DEPARTMENTS)
            category=st.selectbox(label("نوع البلاغ","Report Category"),category_options,
              format_func=lambda x:label("تصنيف تلقائي حسب وصف المشكلة","Automatic Classification") if x=="Auto" else category_name(x))
            description=st.text_area(label("وصف المشكلة بالتفصيل","Describe the Issue"),height=140)
            default_lat,default_lon=CITIES[city]
            latitude=st.number_input(label("خط العرض","Latitude"),value=float(st.session_state.get("report_lat",default_lat)),format="%.6f")
            longitude=st.number_input(label("خط الطول","Longitude"),value=float(st.session_state.get("report_lon",default_lon)),format="%.6f")
            submit=st.form_submit_button(label("🚀 إرسال البلاغ","Submit Report"))
        if submit:
            if not neighborhood.strip() or not description.strip(): st.error(label("يرجى كتابة الحي ووصف البلاغ.","Enter neighborhood and report description."))
            else:
                predicted,priority,risk,_,keywords,critical=analyze_report(description)
                final_category=predicted if category=="Auto" else category
                dept_info=DEPARTMENTS[final_category]
                dept=dept_info["ar"] if AR else dept_info["en"]
                department_id=get_department_id(final_category)
                location=f"{city} - {neighborhood.strip()}"
                if landmark.strip(): location+=f" - بالقرب من {landmark.strip()}"
                report_code="REP-"+str(uuid.uuid4())[:8].upper()
                now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn=get_connection(); cur=conn.cursor()
                cur.execute("""INSERT INTO reports(report_code,identity_code,category,description,location,latitude,longitude,
                  priority,status,created_at,department_id,department_name,city,neighborhood,risk_score,is_critical,updated_at)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (report_code,identity[0],final_category,description,location,latitude,longitude,priority,"Pending",now,
                   department_id,dept,city,neighborhood,risk,int(critical),now))
                report_id=cur.lastrowid; conn.commit(); conn.close()
                create_notification(report_id,"بلاغ جديد / New Report",
                  f"بلاغ جديد من {identity[1]} | التصنيف: {category_name(final_category)} | الموقع: {location} | الأولوية: {priority_name(priority)} | التفاصيل: {description}",
                  "department",department_id)
                create_notification(report_id,"بلاغ جديد يحتاج المتابعة",
                  f"تم توجيه البلاغ {report_code} إلى {dept} | الموقع: {location} | الأولوية: {priority_name(priority)}",
                  "admin",None)
                notify_citizen(identity[0],report_id,"تم استلام بلاغك",f"تم استلام البلاغ {report_code} وتوجيهه إلى {dept}.")
                st.success(label("تم إرسال البلاغ وتوجيهه للجهة المختصة بنجاح!","Report submitted and routed successfully!"))
                st.subheader(label("نتيجة التوجيه الذكي","Smart Routing Result"))
                st.write(f"**{label('رمز البلاغ','Report Code')}:** {report_code}")
                st.write(f"**{label('التصنيف','Category')}:** {category_name(final_category)}")
                st.write(f"**{label('الجهة المختصة','Department')}:** {dept}")
                st.write(f"**{label('الأولوية','Priority')}:** {priority_name(priority)}")
                st.write(f"**{label('درجة الخطورة التقديرية','Estimated Risk')}:** {risk}%")
                st.progress(risk/100)
                qr=generate_qr(report_code).getvalue(); st.image(qr,width=180)
                st.download_button(label("تحميل رمز البلاغ QR","Download Report QR"),data=qr,file_name=f"{report_code}.png",mime="image/png")

# =========================================================
# MY SERVICES
# =========================================================
elif selected_page=="my_services":
    st.header("👤 "+label("خدماتي وبلاغاتي","My Services"))
    identity=current_identity()
    if not identity: st.warning(label("يرجى تسجيل الدخول أولاً.","Please log in first."))
    else:
        st.success(f"{label('مرحباً','Welcome')} {identity[1]}")
        st.write(f"**{label('البريد الإلكتروني','Email')}:** {identity[2]}")
        st.write(f"**{label('رمز الهوية','Identity Code')}:** {identity[0]}")
        if st.button(label("تسجيل الخروج","Logout")): logout_citizen()
        conn=get_connection()
        reports=pd.read_sql_query("SELECT * FROM reports WHERE identity_code=? ORDER BY id DESC",conn,params=(identity[0],))
        notifications=pd.read_sql_query("SELECT * FROM citizen_notifications WHERE identity_code=? ORDER BY id DESC",conn,params=(identity[0],))
        conn.close()
        st.subheader(label("بلاغاتي","My Reports"))
        if reports.empty: st.info(label("لا توجد بلاغات حتى الآن.","No reports yet."))
        else:
            for _,row in reports.iterrows():
                with st.expander(f"{row['report_code']} | {category_name(row['category'])} | {status_name(row['status'])}"):
                    st.write(f"**{label('الوصف','Description')}:** {row['description']}")
                    st.write(f"**{label('الموقع','Location')}:** {row['location']}")
                    st.write(f"**{label('الجهة المختصة','Department')}:** {row['department_name']}")
                    st.write(f"**{label('الأولوية','Priority')}:** {priority_name(row['priority'])}")
                    st.write(f"**{label('الحالة','Status')}:** {status_name(row['status'])}")
                    st.write(f"**{label('التاريخ','Date')}:** {row['created_at']}")
        st.subheader("🔔 "+label("إشعاراتي","My Notifications"))
        if notifications.empty: st.info(label("لا توجد إشعارات.","No notifications."))
        else:
            for _,row in notifications.iterrows():
                st.info(f"**{row['title']}** — {row['message']}"); st.caption(row["created_at"])

# =========================================================
# VERIFY IDENTITY
# =========================================================
elif selected_page=="verify_identity":
    st.header("🔍 "+label("التحقق من الهوية الرقمية","Verify Identity"))
    code=st.text_input(label("رمز الهوية أو البريد الإلكتروني","Identity Code or Email"))
    if st.button(label("التحقق","Verify")):
        conn=get_connection()
        result=conn.execute("SELECT identity_code,full_name,email,user_type,created_at FROM identities WHERE identity_code=? OR email=?",
          (code.strip(),code.strip().lower())).fetchone()
        conn.close()
        if result:
            st.success(label("الهوية الرقمية صحيحة ومسجلة بالنظام.","Valid registered digital identity."))
            st.write(f"**{label('الاسم','Name')}:** {result[1]}")
            st.write(f"**Email:** {mask_email(result[2])}")
            st.write(f"**Identity Code:** {result[0]}")
            st.write(f"**{label('نوع المستفيد','User Type')}:** {result[3]}")
            st.write(f"**{label('تاريخ الإنشاء','Created At')}:** {result[4]}")
        else: st.error(label("الهوية غير موجودة.","Identity not found."))

# =========================================================
# CITY MAP
# =========================================================
elif selected_page=="city_map":
    st.header("🗺️ "+label("خريطة بلاغات النيل الأبيض التفصيلية","White Nile Detailed Reports Map"))
    reports=load_reports()
    # Keep a consistent tooltip schema for city and report layers.
    city_df=pd.DataFrame([{"name":city,"latitude":xy[0],"longitude":xy[1],
      "report_code":city,"category_ar":label("مدينة","City"),"status_ar":"",
      "location":city,"kind":"City"} for city,xy in CITIES.items()])
    layers=[pdk.Layer("ScatterplotLayer",data=city_df,get_position="[longitude,latitude]",
      get_radius=1200,get_fill_color=[7,155,145,180],pickable=True)]
    located=pd.DataFrame()
    if not reports.empty:
        located=reports.copy()
        located["latitude"]=pd.to_numeric(located["latitude"],errors="coerce")
        located["longitude"]=pd.to_numeric(located["longitude"],errors="coerce")
        located=located.dropna(subset=["latitude","longitude"])
        if not located.empty:
            located["category_ar"]=located.category.apply(category_name)
            located["status_ar"]=located.status.apply(status_name)
            located["priority_ar"]=located.priority.apply(priority_name)
            layers.append(pdk.Layer("ScatterplotLayer",data=located,get_position="[longitude,latitude]",
              get_radius=350,get_fill_color=[232,180,74,220],pickable=True))
    deck=pdk.Deck(layers=layers,initial_view_state=pdk.ViewState(latitude=13.16,longitude=32.66,zoom=7),
      tooltip={"html":"<b>{report_code}</b><br/><b>التصنيف:</b> {category_ar}<br/><b>الحالة:</b> {status_ar}<br/><b>الموقع:</b> {location}",
      "style":{"color":"white","backgroundColor":"#12304A"}})
    st.pydeck_chart(deck,use_container_width=True)
    st.caption(label("الخريطة تعرض المدن ومواقع البلاغات المسجلة ذات الإحداثيات.","Map displays cities and geolocated reports."))
    if not located.empty:
        st.subheader(label("📋 تفاصيل البلاغات المعروضة على الخريطة","Geolocated Reports Details"))
        for _,r in located.iterrows():
            with st.expander(f"📍 {r['report_code']} | {r['category_ar']} | {r['status_ar']}"):
                st.write(f"**{label('الوصف','Description')}:** {r['description']}")
                st.write(f"**{label('الموقع الجغرافي','Location')}:** {r['location']}")
                st.write(f"**{label('الإحداثيات','Coordinates')}:** {r['latitude']:.5f}, {r['longitude']:.5f}")
                st.write(f"**{label('الأولوية','Priority')}:** {r['priority_ar']}")
                st.write(f"**{label('الجهة المختصة','Department')}:** {r['department_name']}")

# =========================================================
# SMART ASSISTANT
# =========================================================
elif selected_page=="assistant":
    st.header("🤖 "+label("مساعد النيل الأبيض الذكي","White Nile Smart Assistant"))
    st.markdown("""<div class="wns-card"><h3>🌍 WNS Smart Assistant</h3>
      <p>مساعدك الذكي لمعرفة الخدمات الحكومية وطريقة تقديم البلاغات.</p></div>""",unsafe_allow_html=True)
    question=st.text_area(label("كيف يمكنني مساعدتك؟","How can I help you?"),
      placeholder=label("مثال: أين أبلغ عن انقطاع المياه أو انتشار الكوليرا؟","Example: Where can I report a water outage or cholera outbreak?"))
    if st.button(label("إرسال السؤال","Send Question")):
        if question.strip(): st.success(smart_assistant(question))
        else: st.warning(label("اكتب سؤالك أولاً.","Please enter your question first."))

# =========================================================
# REPORT MANAGEMENT / STAFF PORTAL
# =========================================================
elif selected_page=="manage_reports":
    st.header("⚙️ "+label("الإدارة والجهات الحكومية","Administration & Departments"))
    staff=get_staff()
    if staff:
        staff_id,username,full_name,role,department_id,staff_city=staff
        st.success(f"{label('مرحباً','Welcome')} {full_name} | {role}")
        if st.button(label("تسجيل الخروج","Logout")):
            st.session_state.pop("staff_id",None); st.session_state.pop("root_admin",None); st.rerun()
        reports=load_reports()
        if role=="department": reports=reports[reports.department_id==department_id]
        elif role=="locality" and staff_city: reports=reports[reports.city==staff_city]
        elif role not in ["admin","governor","locality"]:
            st.error(label("ليس لديك صلاحية.","Access denied.")); st.stop()

        st.subheader("🔔 "+label("الإشعارات الذكية","Smart Notifications"))
        notifications=load_notifications(department_id) if role=="department" else load_notifications()
        if notifications.empty: st.info(label("لا توجد إشعارات.","No notifications."))
        else:
            unread=notifications[notifications.is_read==0]
            read=notifications[notifications.is_read==1]
            tab_u,tab_r=st.tabs([f"{label('غير المقروءة','Unread')} ({len(unread)})",f"{label('المقروءة','Read')} ({len(read)})"])
            with tab_u:
                if unread.empty: st.info(label("جميع الإشعارات مقروءة.","All notifications read."))
                for _,n in unread.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**🔔 {n['title']}**"); st.write(n["message"])
                        if pd.notna(n.get("location")): st.write(f"📍 {n['location']}")
                        st.caption(n["created_at"])
                        if st.button(label("تحديد كمقروء","Mark as Read"),key=f"read_{n['id']}"):
                            conn=get_connection()
                            conn.execute("UPDATE admin_notifications SET is_read=1 WHERE id=?",(int(n["id"]),))
                            conn.commit(); conn.close(); st.rerun()
            with tab_r:
                if read.empty: st.info(label("لا توجد إشعارات مقروءة.","No read notifications."))
                for _,n in read.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**✔️ {n['title']}**"); st.write(n["message"]); st.caption(n["created_at"])

        st.divider(); st.subheader("📋 "+label("البلاغات الموجهة إليك","Assigned Reports"))
        if reports.empty: st.info(label("لا توجد بلاغات.","No reports available."))
        else:
            for _,row in reports.iterrows():
                with st.expander(f"{row['report_code']} | {category_name(row['category'])} | {priority_name(row['priority'])}"):
                    st.write(f"**{label('الوصف','Description')}:** {row['description']}")
                    st.write(f"**{label('الموقع','Location')}:** {row['location']}")
                    st.write(f"**{label('الجهة','Department')}:** {row['department_name']}")
                    st.write(f"**{label('الأولوية','Priority')}:** {priority_name(row['priority'])}")
                    st.write(f"**{label('الحالة','Status')}:** {status_name(row['status'])}")
                    can_update=(role in ["admin","governor","locality"] or (role=="department" and department_id==row["department_id"]))
                    if can_update:
                        options=["Pending","In Progress","Resolved"]
                        current=row["status"] if row["status"] in options else "Pending"
                        new_status=st.selectbox(label("تحديث حالة البلاغ","Update Status"),options,index=options.index(current),
                          format_func=status_name,key=f"status_{row['id']}")
                        if st.button(label("حفظ التحديث","Save Update"),key=f"save_{row['id']}"):
                            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            conn=get_connection()
                            conn.execute("UPDATE reports SET status=?,updated_at=? WHERE id=?",(new_status,now,int(row["id"])))
                            conn.commit(); conn.close()
                            notify_citizen(row["identity_code"],int(row["id"]),"تحديث حالة البلاغ",
                              f"تم تحديث البلاغ {row['report_code']} إلى {status_name(new_status)}")
                            create_notification(int(row["id"]),"تحديث حالة بلاغ",
                              f"تم تحديث حالة البلاغ {row['report_code']} إلى {new_status}","admin",None)
                            st.success(label("تم تحديث البلاغ وإشعار المواطن.","Report updated and citizen notified.")); st.rerun()

        if role in ["admin","governor"]:
            st.divider(); st.subheader("🏢 "+label("إدارة الجهات والمستخدمين","Departments & Staff Management"))
            conn=get_connection()
            departments_df=pd.read_sql_query("SELECT * FROM departments ORDER BY id",conn)
            conn.close()
            st.dataframe(departments_df,use_container_width=True,hide_index=True)
            with st.expander(label("⚡ إنشاء حسابات الجهات التلقائية","Generate Default Department Accounts")):
                st.info(label("ينشئ حساباً افتراضياً لكل جهة لا تملك حساباً.","Creates a default account for each department without one."))
                st.warning(label("للتجربة فقط: غيّر كلمات المرور الافتراضية قبل النشر.","Demo only: change default passwords before deployment."))
                if st.button(label("توليد الحسابات الافتراضية الآن","Generate Default Accounts Now")):
                    count=seed_default_departments()
                    st.success(label(f"تم إنشاء {count} حسابات جديدة.",f"Created {count} new accounts.")) if count else st.info(label("الحسابات موجودة بالفعل.","Accounts already exist."))
                    st.rerun()
            with st.expander(label("➕ إنشاء حساب جهة حكومية","Create Department Account")):
                with st.form("staff_creation"):
                    staff_name=st.text_input(label("اسم المسؤول","Staff Name"))
                    new_username=st.text_input(label("اسم المستخدم","Username"))
                    staff_password=st.text_input(label("كلمة المرور","Password"),type="password")
                    staff_role=st.selectbox(label("نوع الصلاحية","Role"),["department","locality"],
                      format_func=lambda x:"مسؤول جهة حكومية" if x=="department" else "مدير محلية")
                    selected_department=st.selectbox(label("الجهة الحكومية","Department"),departments_df.id.tolist(),
                      format_func=lambda x:departments_df.loc[departments_df.id==x,"name_ar"].iloc[0])
                    staff_city=st.selectbox(label("المحلية / المدينة","City"),[""]+list(CITIES))
                    create_user=st.form_submit_button(label("إنشاء الحساب","Create Account"))
                if create_user:
                    if not staff_name.strip() or not new_username.strip() or len(staff_password)<8:
                        st.error(label("أدخل جميع البيانات، واجعل كلمة المرور 8 أحرف على الأقل.","Complete all fields and use at least 8 characters."))
                    else:
                        conn=get_connection()
                        try:
                            conn.execute("""INSERT INTO staff_users(username,full_name,password_hash,role,department_id,city)
                              VALUES(?,?,?,?,?,?)""",(new_username.strip(),staff_name.strip(),hash_password(staff_password),staff_role,selected_department,staff_city))
                            conn.commit(); st.success(label("تم إنشاء حساب المسؤول بنجاح.","Staff account created successfully.")); st.rerun()
                        except sqlite3.IntegrityError: st.error(label("اسم المستخدم مستخدم بالفعل.","Username already exists."))
                        finally: conn.close()
            with st.expander(label("👥 عرض حسابات المسؤولين","View Staff Accounts")):
                conn=get_connection()
                staff_df=pd.read_sql_query("SELECT id,username,full_name,role,department_id,city,is_active FROM staff_users ORDER BY id DESC",conn)
                conn.close(); st.dataframe(staff_df,use_container_width=True,hide_index=True)
                active_df=staff_df[staff_df.is_active==1] if not staff_df.empty else staff_df
                if not active_df.empty:
                    chosen=st.selectbox(label("اختر حساباً لتعطيله","Select Account to Disable"),active_df.id.tolist())
                    if st.button(label("تعطيل الحساب","Disable Account")):
                        conn=get_connection(); conn.execute("UPDATE staff_users SET is_active=0 WHERE id=?",(int(chosen),))
                        conn.commit(); conn.close(); st.success(label("تم تعطيل الحساب.","Account disabled.")); st.rerun()
            st.divider()
            st.download_button(label("📥 تحميل جميع البلاغات CSV","Download Reports CSV"),
              data=reports.to_csv(index=False).encode("utf-8-sig"),file_name="WNS_Reports.csv",mime="text/csv")
    else:
        tab_admin,tab_dept=st.tabs([label("دخول الإدارة العامة","General Administration"),label("دخول الجهات الحكومية","Department Login")])
        with tab_admin:
            password=st.text_input(label("كلمة مرور مدير النظام","Administrator Password"),type="password")
            if st.button(label("دخول المدير","Admin Login")):
                expected=get_admin_password()
                if hmac.compare_digest(password,expected):
                    st.session_state["root_admin"]=True; st.session_state["staff_id"]=-999; st.rerun()
                else: st.error(label("كلمة المرور غير صحيحة.","Incorrect password."))
            st.caption(label("كلمة المرور الافتراضية admin123 للتجربة فقط. اضبط ADMIN_PASSWORD في Secrets أو متغيرات البيئة قبل النشر.",
              "Default admin123 is for demo only. Set ADMIN_PASSWORD in Streamlit Secrets or environment variables before deployment."))
        with tab_dept:
            st.info(label("الحسابات الافتراضية تُنشأ من حساب الإدارة العامة. بعد إنشائها استخدم البيانات التالية:","Default accounts are generated by the administrator. After generation, use:"))
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
11. **غرفة المتابعة:** `other_user` / `other12345`
""")
            username=st.text_input(label("اسم المستخدم","Username"),key="dept_username_input")
            password=st.text_input(label("كلمة المرور","Password"),type="password",key="staff_password_login")
            if st.button(label("تسجيل الدخول","Login to Department")):
                if staff_login(username,password): st.rerun()
                else: st.error(label("اسم المستخدم أو كلمة المرور غير صحيحة.","Incorrect username or password."))

# ------------------------- Footer -------------------------
st.divider()
st.markdown("""<div style="text-align:center;padding:20px;color:#12304A;background:white;border-radius:12px">
<h4>🌍 WHITE NILE SMART (WNS)</h4><p>النيل الأبيض الذكية | منصة التحول الرقمي المتكاملة</p>
<p style="color:#079B91">Smart Government • AI • Digital Services • Smart Notifications</p></div>""",unsafe_allow_html=True)
