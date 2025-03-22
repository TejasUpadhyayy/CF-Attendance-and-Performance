import pandas as pd
from datetime import datetime
from collections import defaultdict
import plotly.graph_objects as go
from groq import Groq
from functools import lru_cache

# Task status conversion rates
TASK_CONVERSION = {
    "Completed": 100,
    "Ongoing": 60,
    "Research": 30,
    "Finishing": 90
}

def calculate_task_completion_rate(row):
    """Calculate task completion rate based on the task status and deadline."""
    task_status = row["Task Status"]
    deadline = pd.to_datetime(row["Task Assigned Date"], format="%d/%m/%Y", errors='coerce')
    completed_on_time = pd.to_datetime(row["Today's Date"], format="%d/%m/%Y", errors='coerce') <= deadline

    if task_status in TASK_CONVERSION:
        return TASK_CONVERSION[task_status] if completed_on_time else 0
    return 0  # Default if status is unrecognized or past deadline

def process_attendance(df):
    """Calculate attendance based on 'Today's Date' column."""
    # Convert date only once at the beginning and reuse
    if "Today's Date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["Today's Date"]):
        df["Today's Date"] = pd.to_datetime(df["Today's Date"], format="%d/%m/%Y", errors='coerce')
    
    # Use value_counts instead of groupby for better performance with unique counts
    attendance = df.dropna(subset=["Today's Date"]).groupby("Email")["Today's Date"].nunique().to_dict()
    return attendance

def fetch_tasks(df):
    """Fetch tasks assigned to each intern."""
    tasks = defaultdict(list)
    for _, row in df.iterrows():
        if pd.notna(row.get("Assigned Task Name")) and pd.notna(row.get("Task Status")):
            tasks[row["Email"]].append((row["Assigned Task Name"], row["Task Status"]))
    return tasks

def compute_performance(df):
    """Compute task completion rate for each intern."""
    df["Task Completion Rate"] = df.apply(calculate_task_completion_rate, axis=1)
    performance = df.groupby("Email")["Task Completion Rate"].mean().round(2).fillna(0)
    return performance.to_dict()

# Cached version for repeated calls with the same data
@lru_cache(maxsize=32)
def compute_performance_cached(df_json):
    """Compute task completion rate for each intern with caching."""
    # Convert json string to DataFrame (needed for caching)
    df = pd.read_json(df_json)
    
    df["Task Completion Rate"] = df.apply(calculate_task_completion_rate, axis=1)
    performance = df.groupby("Email")["Task Completion Rate"].mean().round(2).fillna(0)
    return performance.to_dict()

def generate_ai_insights(df):
    """Generate insights for performance analysis without using external API."""
    insights = {}
    
    # Process all employees
    all_tasks = fetch_tasks(df)
    all_emails = list(all_tasks.keys())
    
    for email in all_emails:
        tasks = all_tasks[email]
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task, status in tasks if "Finishing" in status or "Completed" in status)
        days_present = len(df[df["Email"] == email]["Today's Date"].unique())
        days_absent = 30 - days_present  # Assuming a 30-day month
        ongoing_tasks = sum(1 for task, status in tasks if "Ongoing" in status)
        research_tasks = sum(1 for task, status in tasks if "Research" in status)
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        attendance_rate = (days_present / 30 * 100)
        
        # Generate insights based on the data
        if completion_rate >= 80 and attendance_rate >= 90:
            performance_level = "Excellent"
            recommendation = "Consider for promotion or additional responsibilities."
        elif completion_rate >= 70 and attendance_rate >= 80:
            performance_level = "Good"
            recommendation = "Performing well, but has room for improvement in task efficiency."
        elif completion_rate >= 50 and attendance_rate >= 70:
            performance_level = "Average"
            recommendation = "Needs improvement in task completion and consistency."
        else:
            performance_level = "Below Average"
            recommendation = "Requires immediate attention and performance improvement plan."
        
        # Create the insight text
        insight = f"""Performance Level: {performance_level}
        
Task Analysis:
- Completed {completed_tasks} out of {total_tasks} tasks ({completion_rate:.1f}%)
- Currently has {ongoing_tasks} ongoing tasks and {research_tasks} in research phase
- Attendance rate: {attendance_rate:.1f}% ({days_present} days present)

Recommendation: {recommendation}

Key focus areas:
"""
        
        # Add specific recommendations based on task status
        if completion_rate < 70:
            insight += "- Improve task completion rate by setting smaller milestones\n"
        if attendance_rate < 80:
            insight += "- Improve attendance and consistency\n"
        if ongoing_tasks > completed_tasks:
            insight += "- Work on finishing ongoing tasks before starting new ones\n"
        if research_tasks > (total_tasks / 3):
            insight += "- Move research tasks to implementation phase faster\n"
        
        # Add a summary statement
        if performance_level in ["Excellent", "Good"]:
            insight += "\nOverall, performing well with minor adjustments needed."
        else:
            insight += "\nNeeds structured guidance to improve performance metrics."
            
        insights[email] = insight
            
    return insights

def plot_performance_graph(email, performance, attendance, tasks):
    """Generate enhanced Plotly graphs for performance analysis."""
    
    # Calculate task completion trend if data available
    task_trend = {}
    if email in tasks and tasks[email]:
        for task, status in tasks[email]:
            task_date = task.split(' - ')[1] if ' - ' in task else None
            if task_date:
                try:
                    date = pd.to_datetime(task_date)
                    status_value = TASK_CONVERSION.get(status, 0)
                    if date not in task_trend:
                        task_trend[date] = []
                    task_trend[date].append(status_value)
                except:
                    pass
    
    # Bar chart with improved styling
    bar_fig = go.Figure(data=[
        go.Bar(name="Task Completion (%)", x=[email], y=[performance.get(email, 0)],
              marker_color='rgba(58, 71, 80, 0.6)', marker_line_color='rgba(8, 48, 107, 1.0)',
              marker_line_width=1.5),
        go.Bar(name="Days Present", x=[email], y=[attendance.get(email, 0)],
              marker_color='rgba(246, 78, 139, 0.6)', marker_line_color='rgba(178, 58, 84, 1.0)',
              marker_line_width=1.5)
    ])
    
    bar_fig.update_layout(
        barmode="group", 
        title=f"Performance Overview for {email}",
        xaxis_title="Employee",
        yaxis_title="Value",
        legend_title="Metrics",
        template="plotly_white"
    )

    # Pie chart with better color scheme
    task_counts = pd.Series([status for task, status in tasks[email]]).value_counts() if email in tasks else pd.Series()
    
    pie_fig = go.Figure(data=[go.Pie(
        labels=task_counts.index, 
        values=task_counts.values,
        hole=.3,
        marker=dict(colors=['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A'])
    )])
    
    pie_fig.update_layout(
        title="Task Status Distribution",
        template="plotly_white"
    )

    return bar_fig, pie_fig

def calculate_performance_score(performance_rate, attendance_rate, task_completion_rate):
    """Calculate an overall performance score based on multiple metrics."""
    # Weights for different components
    weights = {
        'performance': 0.4,  
        'attendance': 0.3,   
        'task_completion': 0.3
    }
    
    # Calculate weighted score
    score = (
        weights['performance'] * performance_rate +
        weights['attendance'] * (attendance_rate/30 * 100) +  # Assuming 30 days in month
        weights['task_completion'] * task_completion_rate
    )
    
    return round(score, 1)

def analyze_deadline_performance(df):
    """Analyze how well employees meet deadlines."""
    if "Task Assigned Date" not in df.columns or "Today's Date" not in df.columns:
        return {}
        
    # Convert date columns
    df["Task Assigned Date"] = pd.to_datetime(df["Task Assigned Date"], format="%d/%m/%Y", errors='coerce')
    df["Today's Date"] = pd.to_datetime(df["Today's Date"], format="%d/%m/%Y", errors='coerce')
    
    # Calculate days to complete (negative means completed before deadline)
    df["Days to Complete"] = (df["Today's Date"] - df["Task Assigned Date"]).dt.days
    
    # Group by email and calculate average days to completion
    deadline_performance = df.groupby("Email")["Days to Complete"].agg(
        ['mean', 'min', 'max', 'count']
    ).round(1).to_dict('index')
    
    return deadline_performance