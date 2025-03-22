import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sheets_api import fetch_sheet_data
from performance_analysis import (
    process_attendance, fetch_tasks, compute_performance, 
    generate_ai_insights, plot_performance_graph,
    calculate_performance_score, analyze_deadline_performance
)

# Page configuration
st.set_page_config(
    page_title="Employee Performance Tracker",
    page_icon="📊",
    layout="wide"
)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Performance Dashboard", "Attendance Tracker", "Deadline Analysis"])

# Load Google Sheets Data
@st.cache_data(ttl=300)  # Cache data for 5 minutes
def load_data():
    try:
        return fetch_sheet_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.warning("No data found. Ensure the Google Sheet is populated.")
    
    # Provide mock data for testing when no data is available
    mock_data = {
        "Email": ["example@example.com"],
        "Intern name": ["Example User"],
        "Today's Date": [datetime.today().strftime("%d/%m/%Y")],
        "Assigned Task Name": ["Mock Task"],
        "Task Status": ["Ongoing"],
        "Task Assigned Date": [(datetime.today() - timedelta(days=2)).strftime("%d/%m/%Y")]
    }
    df = pd.DataFrame(mock_data)
    st.info("Using mock data for demonstration purposes.")

# Attendance Calculation
attendance = process_attendance(df)

# Task Data
tasks = fetch_tasks(df)

# Performance Calculation
performance = compute_performance(df)

# AI Insights - Generate without API dependency
if 'ai_insights' not in st.session_state:
    with st.spinner("Generating performance insights..."):
        st.session_state.ai_insights = generate_ai_insights(df)
ai_insights = st.session_state.ai_insights

# Deadline Performance
deadline_performance = analyze_deadline_performance(df)

# 🏆 **Performance Dashboard**
if page == "Performance Dashboard":
    st.title("📊 Employee Performance Tracker")

    # Display Performance Table
    st.subheader("Employee Performance Overview")
    
    # Calculate overall performance scores
    overall_scores = {}
    for email in attendance.keys():
        perf_rate = performance.get(email, 0)
        attend_rate = attendance.get(email, 0)
        task_rate = len([t for t, s in tasks.get(email, []) if s == "Completed"])
        
        score = calculate_performance_score(perf_rate, attend_rate, task_rate)
        overall_scores[email] = score
    
    # Create enhanced summary dataframe
    df_summary = pd.DataFrame({
        "Email": list(attendance.keys()),
        "Days Present": list(attendance.values()),
        "Task Completion (%)": [performance.get(email, 0) for email in attendance.keys()],
        "Overall Score": [overall_scores.get(email, 0) for email in attendance.keys()],
        "AI Insights": [ai_insights.get(email, "No insights available") for email in attendance.keys()]
    })
    
    # Sort by overall score
    df_summary = df_summary.sort_values(by="Overall Score", ascending=False)
    
    # Add color highlighting based on score
    def highlight_score(val):
        if val >= 80:
            return 'background-color: #9ACD32'  # Green
        elif val >= 60:
            return 'background-color: #FFD700'  # Yellow
        else:
            return 'background-color: #FF6347'  # Red
    
    # Apply styling and display the table
    styled_df = df_summary.style.applymap(highlight_score, subset=['Overall Score'])
    st.dataframe(styled_df, hide_index=True, use_container_width=True)

    # Individual Employee Details
    st.subheader("Intern Details")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_email = st.selectbox("Select Intern Email", df_summary["Email"])
        
        # Fetch employee name
        intern_name = df[df['Email'] == selected_email]['Intern name'].values[0] if any(df['Email'] == selected_email) else "Unknown"
        st.write(f"**Name:** {intern_name}")
        st.write(f"**Days Present:** {attendance.get(selected_email, 0)}")
        st.write(f"**Task Completion Rate:** {performance.get(selected_email, 0)}%")
        st.write(f"**Overall Score:** {overall_scores.get(selected_email, 0)}")
        
        # Deadline performance
        if selected_email in deadline_performance:
            dp = deadline_performance[selected_email]
            st.write("**Deadline Performance:**")
            st.write(f"- Avg days to complete: {dp['mean']}")
            st.write(f"- Fastest completion: {dp['min']} days")
            st.write(f"- Slowest completion: {dp['max']} days")
    
    with col2:
        # Task Display with improved handling
        st.write(f"**Tasks Done:**")
        if selected_email in tasks and tasks[selected_email]:  
            for task, status in tasks[selected_email]:
                # Use color coding for status
                if status == "Completed":
                    st.markdown(f"- {task} (✅ {status})")
                elif status == "Ongoing":
                    st.markdown(f"- {task} (🔄 {status})")
                elif status == "Research":
                    st.markdown(f"- {task} (🔍 {status})")
                elif status == "Finishing":
                    st.markdown(f"- {task} (🏁 {status})")
                else:
                    st.markdown(f"- {task} ({status})")
        else:
            st.write("No tasks found.")

    # AI Insights with expandable section
    with st.expander("AI Insights", expanded=False):
        st.write(f"{ai_insights.get(selected_email, 'No insights available')}")

    # Plot Performance Graphs
    st.subheader("Performance Analysis")
    bar_chart, pie_chart = plot_performance_graph(selected_email, performance, attendance, tasks)
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart, use_container_width=True)
    with col2:
        st.plotly_chart(pie_chart, use_container_width=True)


# 📅 **Attendance Tracker (Separate Page)**
elif page == "Attendance Tracker":
    st.title("📅 Monthly Attendance Tracker")

    # Select an employee
    selected_email = st.selectbox("Select Employee", df["Email"].unique(), key="attendance")

    # Get today's date
    today = datetime.today()
    start_of_month = today.replace(day=1)

    # Generate only past & present dates of this month
    all_dates = [(start_of_month + timedelta(days=i)).strftime("%d/%m/%Y")
                 for i in range(today.day)]  # Only show dates up to today

    # Get present dates from Google Sheets where the employee has submitted the form
    # Convert dates to the same format for comparison
    if "Today's Date" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["Today's Date"]):
            df["Today's Date"] = pd.to_datetime(df["Today's Date"], format="%d/%m/%Y", errors='coerce')
        
        # Extract all dates for this employee and convert to string in the format matching all_dates
        present_dates = df[df["Email"] == selected_email]["Today's Date"].dt.strftime("%d/%m/%Y").dropna().tolist()

    # Create attendance DataFrame
    attendance_df = pd.DataFrame({"Date": all_dates})
    attendance_df["Status"] = attendance_df["Date"].apply(lambda x: "✅ Present" if x in present_dates else "❌ Absent")

    # Calculate attendance statistics
    total_days = len(all_dates)
    present_days = sum(1 for status in attendance_df["Status"] if "Present" in status)
    absent_days = total_days - present_days
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Display attendance stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Days", total_days)
    col2.metric("Days Present", present_days)
    col3.metric("Attendance Rate", f"{attendance_rate:.1f}%")
    
    # Display Attendance Table with color coding
    def color_status(val):
        if 'Present' in val:
            return 'background-color: #9ACD32'
        else:
            return 'background-color: #FF6347'
    
    styled_attendance = attendance_df.style.applymap(color_status, subset=['Status'])
    st.dataframe(styled_attendance, hide_index=True, use_container_width=True)

# Deadline Analysis Page (New)
elif page == "Deadline Analysis":
    st.title("⏱️ Task Deadline Analysis")
    
    # Create a summary of deadline performance
    deadline_df = pd.DataFrame()
    
    if deadline_performance:
        emails = []
        avg_days = []
        fastest = []
        slowest = []
        task_count = []
        
        for email, stats in deadline_performance.items():
            emails.append(email)
            avg_days.append(stats['mean'])
            fastest.append(stats['min'])
            slowest.append(stats['max'])
            task_count.append(stats['count'])
        
        deadline_df = pd.DataFrame({
            "Email": emails,
            "Average Days to Complete": avg_days,
            "Fastest Completion (days)": fastest,
            "Slowest Completion (days)": slowest,
            "Number of Tasks": task_count
        })
        
        # Sort by average completion time
        deadline_df = deadline_df.sort_values(by="Average Days to Complete")
        
        # Apply styling based on average completion time
        def highlight_completion(val):
            if isinstance(val, (int, float)):
                if val < 0:
                    return 'background-color: #9ACD32'  # Green (before deadline)
                elif val <= 2:
                    return 'background-color: #FFD700'  # Yellow (on or near deadline)
                else:
                    return 'background-color: #FF6347'  # Red (after deadline)
            return ''
        
        styled_deadline = deadline_df.style.applymap(highlight_completion, subset=['Average Days to Complete'])
        st.dataframe(styled_deadline, hide_index=True, use_container_width=True)
        
        # Create a visualization for deadline performance
        selected_email = st.selectbox("Select Employee for Detailed Analysis", deadline_df["Email"])
        
        # Find all tasks for this employee
        employee_tasks = []
        if selected_email in tasks:
            employee_tasks = tasks[selected_email]
        
        # Find completion times for tasks
        task_data = df[df["Email"] == selected_email]
        
        if not task_data.empty and len(employee_tasks) > 0:
            st.subheader(f"Task Timeline for {selected_email}")
            
            # Create bar chart showing completion time for each task
            import plotly.express as px
            
            task_list = []
            completion_days = []
            status_list = []
            
            for _, row in task_data.iterrows():
                if pd.notna(row.get("Assigned Task Name")) and pd.notna(row.get("Task Status")):
                    task = row["Assigned Task Name"]
                    assigned_date = pd.to_datetime(row["Task Assigned Date"], errors='coerce')
                    completion_date = pd.to_datetime(row["Today's Date"], errors='coerce')
                    
                    if pd.notna(assigned_date) and pd.notna(completion_date):
                        days_diff = (completion_date - assigned_date).days
                        task_list.append(task)
                        completion_days.append(days_diff)
                        status_list.append(row["Task Status"])
            
            if task_list:
                timeline_df = pd.DataFrame({
                    "Task": task_list,
                    "Days to Complete": completion_days,
                    "Status": status_list
                })
                
                fig = px.bar(
                    timeline_df, 
                    x="Task", 
                    y="Days to Complete", 
                    color="Status",
                    color_discrete_map={
                        "Completed": "#00CC96",
                        "Ongoing": "#636EFA",
                        "Research": "#AB63FA",
                        "Finishing": "#FFA15A"
                    }
                )
                
                fig.update_layout(
                    title="Days to Complete Tasks",
                    xaxis_title="Task",
                    yaxis_title="Days (negative means completed before deadline)",
                    template="plotly_white"
                )
                
                # Add a horizontal line at y=0 to indicate the deadline
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    y0=0,
                    x1=len(task_list)-0.5,
                    y1=0,
                    line=dict(color="red", width=2, dash="dash")
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No task timeline data available for this employee.")
        else:
            st.write("No task data available for this employee.")
    else:
        st.write("No deadline performance data available. Make sure your data includes task assignment dates and completion dates.")
