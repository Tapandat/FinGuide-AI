import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import plotly.express as px
import joblib
import numpy as np
from email_service import send_email

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="FinGuide AI",
    page_icon="💰",
    layout="wide"
)

# ---------------- PROFESSIONAL CSS ----------------

st.markdown("""
<style>

/* Main App */

.stApp {
    background-color: #f4f7fb;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background-color: #020c2b;
    color: white;
    padding-top: 20px;
}

/* Sidebar Text */

section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Titles */

h1 {
    color: #0f172a !important;
    font-weight: 800;
}

h2, h3 {
    color: #1e293b !important;
}

/* Metric Cards */

[data-testid="metric-container"] {

    background-color: white;

    border: 1px solid #e2e8f0;

    padding: 20px;

    border-radius: 15px;

    box-shadow:
        0px 2px 10px rgba(0,0,0,0.05);

}

/* Buttons */

.stButton > button {

    background-color: #2563eb;

    color: white;

    border: none;

    border-radius: 10px;

    padding: 10px 18px;

    font-weight: 600;

}

.stButton > button:hover {

    background-color: #1d4ed8;

    color: white;

}

/* Inputs */

.stTextInput input,
.stNumberInput input {

    border-radius: 10px;

    border: 1px solid #cbd5e1;

    padding: 10px;

}

</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------

def create_connection():

    return sqlite3.connect("finance.db")

# ---------------- CREATE TABLES ----------------

conn = create_connection()

cursor = conn.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT UNIQUE,

    email TEXT UNIQUE,

    password BLOB

)

""")

cursor.execute("""

CREATE TABLE IF NOT EXISTS expenses (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id TEXT,

    category TEXT,

    amount REAL,

    note TEXT

)

""")

cursor.execute("""

CREATE TABLE IF NOT EXISTS income (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id TEXT,

    source TEXT,

    amount REAL

)

""")

conn.commit()

conn.close()

# ---------------- USER FUNCTIONS ----------------

def register_user(
    username,
    email,
    password
):

    conn = create_connection()

    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    )

    try:

        cursor.execute(
            """
            INSERT INTO users(
                username,
                email,
                password
            )

            VALUES (?, ?, ?)
            """,
            (
                username,
                email,
                hashed_password
            )
        )

        conn.commit()

        return True

    except Exception as e:

        st.error(e)

        return False

    finally:

        conn.close()

def login_user(username, password):

    conn = create_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM users
        WHERE username=?
        """,
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        stored_password = user[3]

        if bcrypt.checkpw(
            password.encode('utf-8'),
            stored_password
        ):

            return True

    return False

def get_user_email(username):

    conn = create_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT email
        FROM users
        WHERE username=?
        """,
        (username,)
    )

    result = cursor.fetchone()

    conn.close()

    if result:

        return result[0]

    return None

# ---------------- EXPENSE FUNCTIONS ----------------

def add_expense(
    user_id,
    category,
    amount,
    note
):

    conn = create_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO expenses(
            user_id,
            category,
            amount,
            note
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            category,
            amount,
            note
        )
    )

    conn.commit()

    conn.close()

def load_expenses(user_id):

    conn = create_connection()

    query = f"""

    SELECT * FROM expenses

    WHERE user_id='{user_id}'
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df

# ---------------- INCOME FUNCTIONS ----------------

def add_income(
    user_id,
    source,
    amount
):

    conn = create_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO income(
            user_id,
            source,
            amount
        )

        VALUES (?, ?, ?)
        """,
        (
            user_id,
            source,
            amount
        )
    )

    conn.commit()

    conn.close()

def load_income(user_id):

    conn = create_connection()

    query = f"""

    SELECT * FROM income

    WHERE user_id='{user_id}'
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df

# ---------------- SESSION ----------------

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

# ---------------- AUTH ----------------

if not st.session_state.logged_in:

    st.title("💰 FinGuide AI")

    auth_mode = st.sidebar.radio(
        "Choose Option",
        ["Login", "Register"]
    )

    username = st.text_input("Username")

    email = st.text_input("Email")

    password = st.text_input(
        "Password",
        type="password"
    )

    # ---------------- REGISTER ----------------

    if auth_mode == "Register":

        if st.button("Register"):

            success = register_user(
                username,
                email,
                password
            )

            if success:

                st.success(
                    "Registration Successful ✅"
                )

            else:

                st.error(
                    "Registration Failed"
                )

    # ---------------- LOGIN ----------------

    else:

        if st.button("Login"):

            success = login_user(
                username,
                password
            )

            if success:

                st.session_state.logged_in = True

                st.session_state.username = username

                st.rerun()

            else:

                st.error(
                    "Invalid Credentials"
                )

# ---------------- MAIN APP ----------------

else:

    st.sidebar.title("💰 FinGuide AI")

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Income Manager",
            "Expense Entry",
            "Analytics",
            "Budget Planner",
            "Predictions",
            "Settings"
        ]
    )

    # ---------------- LOGOUT ----------------

    if st.sidebar.button("Logout"):

        st.session_state.clear()

        st.rerun()

    current_user = st.session_state.get(
        "username",
        None
    )

    if current_user is None:

        st.warning(
            "Please login again."
        )

        st.stop()

    # ---------------- LOAD DATA ----------------

    expense_df = load_expenses(current_user)

    income_df = load_income(current_user)

    total_income = (
        income_df['amount'].sum()
        if not income_df.empty else 0
    )

    total_expense = (
        expense_df['amount'].sum()
        if not expense_df.empty else 0
    )

    savings = total_income - total_expense

    # ---------------- DASHBOARD ----------------

    if menu == "Dashboard":

        st.title("💰 FinGuide AI Dashboard")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Income",
            f"₹{total_income}"
        )

        col2.metric(
            "Total Expenses",
            f"₹{total_expense}"
        )

        col3.metric(
            "Savings",
            f"₹{savings}"
        )

        st.markdown("---")

        if not expense_df.empty:

            category_data = expense_df.groupby(
                'category'
            )['amount'].sum().reset_index()

            fig = px.pie(
                category_data,
                names='category',
                values='amount',
                hole=0.4
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )
