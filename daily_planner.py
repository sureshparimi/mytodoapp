import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import hashlib

# Function to create database connection
def create_connection():
    conn = sqlite3.connect('tasks.db')
    return conn

# Function to create table if not exists
def create_tables(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                due_datetime DATETIME NOT NULL,
                status TEXT NOT NULL DEFAULT 'Not yet started',
                category TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id))''')
    conn.commit()

# Function to add user to database
def add_user(conn, username, password):
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              (username, hashlib.sha256(password.encode()).hexdigest()))
    conn.commit()

# Function to authenticate user
def authenticate_user(conn, username, password):
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hashlib.sha256(password.encode()).hexdigest()))
    return c.fetchone()

# Function to add task to database
def add_task(conn, user_id, task, due_datetime, status, category):
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, task, due_datetime, status, category) VALUES (?, ?, ?, ?, ?)",
              (user_id, task, due_datetime, status, category))
    conn.commit()

# Function to retrieve tasks for a specific date
def get_tasks_for_date(conn, user_id, selected_date):
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE user_id=? AND DATE(due_datetime) = ?", (user_id, selected_date))
    return c.fetchall()

# Function to retrieve tasks for the current week
def get_tasks_for_current_week(conn, user_id):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE user_id=? AND due_datetime BETWEEN ? AND ?",
              (user_id, start_of_week, end_of_week))
    return c.fetchall()

# Function to update task status in the database
def update_task_status(conn, task_id, status):
    c = conn.cursor()
    c.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    conn.commit()

# Function to format due date
def format_due_date(due_datetime_str):
    due_datetime = datetime.strptime(due_datetime_str, "%Y-%m-%d %H:%M:%S")
    return due_datetime.strftime("%d %B %Y, %H:%M:%S")

# Main function
def main():
    # Create database connection and table
    conn = create_connection()
    create_tables(conn)

    # Sidebar title and menu options
    st.sidebar.title("Menu")
    menu_options = ["Register", "Login", "Add Task", "View Tasks"]
    choice = st.sidebar.selectbox("Select Option", menu_options)

    # Display user name if logged in
    if "logged_in_user" in st.session_state:
        st.sidebar.write(f"Logged in as: {st.session_state.logged_in_user_username}")

    selected_date = datetime.now().date()  # Default selected date

    # Register
    if choice == "Register":
        st.title("Register")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if username and password:
                add_user(conn, username, password)
                st.success("Registration successful!")
            else:
                st.warning("Please enter username and password.")

    # Login
    elif choice == "Login":
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username and password:
                user = authenticate_user(conn, username, password)
                if user:
                    st.success(f"Welcome, {username}!")
                    st.session_state.logged_in_user = user[0]
                    st.session_state.logged_in_user_username = user[1]
                else:
                    st.error("Invalid username or password.")
            else:
                st.warning("Please enter username and password.")

    # Add Task
    elif choice == "Add Task":
        st.title("Plan your day")
        if "logged_in_user" not in st.session_state:
            st.warning("Please login to add tasks.")
        else:
            st.title("Add Task")
            task = st.text_area("Task", height=100)
            due_date = st.date_input("Due Date")
            due_time = st.time_input("Due Time")
            due_datetime = datetime.combine(due_date, due_time)
            status = st.selectbox("Status", ["Completed", "In Progress", "Not yet started", "Canceled"])
            category = st.selectbox("Category", ["Strategic", "New Learning", "Improve", "Achievement"])
            if st.button("Add"):
                if task:
                    add_task(conn, st.session_state.logged_in_user, task, due_datetime, status, category)
                    st.success("Task added successfully!")
                else:
                    st.warning("Please enter a task.")

    # View Tasks
    elif choice == "View Tasks":
        st.title("View Tasks")
        if "logged_in_user" not in st.session_state:
            st.warning("Please login to view tasks.")
        else:
            selected_period = st.selectbox("Select Period", ["Day", "Week", "Month"], index=1)  # Set to Week by default
            if selected_period == "Day":
                selected_date = st.date_input("Select Date")
                tasks = get_tasks_for_date(conn, st.session_state.logged_in_user, selected_date)
            elif selected_period == "Week":
                tasks = get_tasks_for_current_week(conn, st.session_state.logged_in_user)
            else:  # Month
                st.warning("Month view is not implemented yet.")
                tasks = []

            if tasks:
                df = pd.DataFrame(tasks, columns=["id", "user_id", "task", "due_datetime", "status", "category"])

                st.write("### Calendar View of Tasks")
                st.write("Here is a basic calendar view of tasks:")
                st.write("<div class='calendar-container'>", unsafe_allow_html=True)
                calendar_days = [selected_date + timedelta(days=i) for i in range(-3, 4)]  # 3 days before and after
                for day in calendar_days:
                    if day == datetime.now().date():
                        st.markdown(f"<div class='calendar-day today'>{day.strftime('%A, %B %d, %Y')}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='calendar-day'>{day.strftime('%A, %B %d, %Y')}</div>", unsafe_allow_html=True)
                    tasks_for_day = df[pd.to_datetime(df["due_datetime"]).dt.date == day]
                    if not tasks_for_day.empty:
                        for _, row in tasks_for_day.iterrows():
                            st.write(f"- {row['task']}")
                    else:
                        st.write("No tasks")
                st.write("</div>", unsafe_allow_html=True)
            else:
                st.write("No tasks found for selected period.")

        # Add CSS styles for grid view
        st.markdown("""
        <style>
        .calendar-container {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 10px;
        }

        .calendar-day {
            padding: 10px;
            border: 1px solid #ccc;
            text-align: center;
            background-color: #f0f0f0;
        }

        .today {
            background-color: #b3d9ff;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
