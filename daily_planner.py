import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# Disable PyplotGlobalUseWarning
st.set_option('deprecation.showPyplotGlobalUse', False)

# Function to create database connection
def create_connection():
    conn = sqlite3.connect('tasks.db')
    return conn

# Function to create table if not exists
def create_table(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                due_datetime DATETIME NOT NULL,
                status TEXT NOT NULL DEFAULT 'Not yet started',
                category TEXT)''')
    conn.commit()

# Function to add task to database
def add_task(conn, task, due_datetime, status, category):
    c = conn.cursor()
    c.execute("INSERT INTO tasks (task, due_datetime, status, category) VALUES (?, ?, ?, ?)",
              (task, due_datetime, status, category))
    conn.commit()

# Function to retrieve tasks for a specific date
def get_tasks_for_date(conn, selected_date):
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE DATE(due_datetime) = ?", (selected_date,))
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

# # Function to perform exploratory data analysis (EDA)
# def perform_eda(tasks):
#     df = pd.DataFrame(tasks, columns=['id', 'task', 'due_datetime', 'status', 'category'])
    
#     # Define color palette based on task statuses
#     status_palette = {'Completed': 'green', 'In Progress': 'blue', 'Not yet started': 'orange', 'Canceled': 'red'}
#     status_colors = [status_palette[status] for status in df['status']]
    
#     # Countplot of task category distribution with stacked bars for status
#     plt.figure(figsize=(10, 6))
#     sns.countplot(data=df, y='category', hue='status', palette=status_palette)
#     plt.title('Task Category Distribution with Status')
#     plt.xlabel('Count')
#     plt.ylabel('Category')
#     st.pyplot()

# Main function
def main():
    # Create database connection and table
    conn = create_connection()
    create_table(conn)

    # Sidebar title and menu options
    st.sidebar.title("Menu")
    menu_options = ["Add Task", "View Tasks"]
    choice = st.sidebar.selectbox("Select Option", menu_options)

    # Add Task
    if choice == "Add Task":
        st.title("Plan your day")
        task = st.text_area("Task", height=100)
        due_date = st.date_input("Due Date")
        due_time = st.time_input("Due Time")
        due_datetime = datetime.combine(due_date, due_time)
        status = st.selectbox("Status", ["Completed", "In Progress", "Not yet started", "Canceled"])
        category = st.selectbox("Category", ["Strategic", "New Learning", "Improve", "Achievement"])
        if st.button("Add"):
            if task:
                add_task(conn, task, due_datetime, status, category)
                st.success("Task added successfully!")
            else:
                st.warning("Please enter a task.")

    # View Tasks
    elif choice == "View Tasks":
        st.title("View Tasks")
        selected_date = st.date_input("Select Date")
        tasks = get_tasks_for_date(conn, selected_date)

        if tasks:
            for task in tasks:
                task_id, task_text, due_datetime_str, status, category = task
                formatted_due_date = format_due_date(due_datetime_str)
                task_display = f"<p style='font-size: 16px;'><span style='background-color: {'yellow' if category == 'Strategic' else 'orange' if category == 'New Learning' else 'green' if category == 'Improve' else 'blue' if category == 'Achievement' else 'white'}; color: black;'>Category: {category}</span> - <span style='color: {'green' if status == 'Completed' else 'blue' if status == 'In Progress' else 'orange' if status == 'Not yet started' else 'red'};'>Status: {status}</span> - Task: {task_text} - Due Date: {formatted_due_date}</p>"
                st.write(task_display, unsafe_allow_html=True)
                if status != "Completed":
                    new_status = st.selectbox("Update Status", ["Completed", "In Progress", "Not yet started", "Canceled"], key=task_id)
                    if st.button("Update Status", key=f"update_{task_id}"):
                        update_task_status(conn, task_id, new_status)
                        st.success("Status updated successfully!")
            # # Perform EDA after displaying tasks
            # perform_eda(tasks)
        else:
            st.write("No tasks found for selected date.")

if __name__ == "__main__":
    main()
