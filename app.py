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
            "كهرباء", "إنارة", "انقطاع"
        ],

        "Water": [
            "water", "leak", "pipe",
            "مياه", "تسريب", "ماسورة"
        ],

        "Cleaning": [
            "garbage", "waste", "trash",
            "نفاياتLECT * FROM identities WHERE identity_code = ?",
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
    
