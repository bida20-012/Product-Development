import streamlit as st
import plotly.express as px
import pandas as pd
import datetime
import os
import requests

st.set_page_config(page_title="olympics", page_icon=":bar_chart:", layout="wide")
st.markdown("<style>div.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True)

df = pd.read_csv("olympic_web_server_logs.csv")
image = "Olympics-logo.jpg.jfif"

# Convert 'Date' column to datetime
df['Date'] = pd.to_datetime(df['Date'])
df['Hour'] = pd.to_datetime(df['Hour'])


col1, col2 = st.columns([0.1, 0.9])
with col1:
    # Update box_date outside the sidebar
    box_date = str(datetime.datetime.now().strftime("%d %B %Y"))

    # Use st.sidebar directly for layout elements within the sidebar
    st.sidebar.image(image, width=200)
    st.sidebar.write(f"Last updated by: \n {box_date}")

html_title = """
    <style>
    .title-test {
    font-weight:bold;
    padding:5px
    border-radius:6px
    }
    </style>
    <center><h1 class= "test-title">Olympic Web Server Log Analysis </h1></center>"""
with col2:
    st.markdown(html_title, unsafe_allow_html=True)

# Define columns for metrics
col3, col4, col5, col6 = st.columns(4)

# Define a custom class for the div container
div_container_class = "custom-metric-container"

# Function to calculate metrics based on the filtered dataframe
def calculate_metrics(df):
    # Total Visits
    total_visits = len(df)
    col3.metric(label="Total Visits", value=total_visits, delta=0)  # Set delta to 0 for color consistency

    # Average Visits per Day
    avg_visits_per_day = df.groupby(df['Date']).size().mean()
    col4.metric(label="Avg Visits per Day", value=f"{avg_visits_per_day:.2f}", delta=0)

    # Standard Deviation of Daily Visits
    std_daily_visits = df.groupby(df['Date']).size().std()
    col5.metric(label="Std Dev of Daily Visits", value=f"{std_daily_visits:.2f}", delta=0)

    # Average Visit Duration (assuming 'Timestamp' is a string column)
    if 'Start_Time' not in df.columns and 'End_Time' not in df.columns:
        if 'Timestamp' in df.columns:
            try:
                # Attempt to convert Timestamp to datetime
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df['Visit_Duration'] = df['Timestamp'].diff().dt.total_seconds().fillna(0)  # Handle potential NaNs
                df['Visit_Duration'] = df['Visit_Duration'].clip(lower=0)  # Ensure non-negative duration
                avg_visit_duration = df['Visit_Duration'].mean()
                # Convert seconds to hours (modify if needed)
                avg_visit_duration = avg_visit_duration / 3600
                col6.metric(label="Avg Visit Duration (hours)", value=f"{avg_visit_duration:.2f}")
            except ValueError:
                # Handle cases where Timestamp conversion fails (e.g., invalid format)
                col6.metric(label="Avg Visit Duration", value="NA (Invalid Timestamp Format)")
        else:
            col6.metric(label="Avg Visit Duration", value="NA (Data Required)")
    else:
        # Existing code for calculating duration using Start_Time and End_Time (if present)
        pass

# Sidebar - Filter by country
selected_country = st.sidebar.selectbox("Select Country", ["All"] + df['Country'].unique().tolist(), index=0)
start_date = pd.to_datetime(st.sidebar.date_input("Start Date", min_value=min(df['Date']), max_value=max(df['Date']), value=min(df['Date'])))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", min_value=min(df['Date']), max_value=max(df['Date']), value=max(df['Date'])))

# Apply filters to the dataframe
if selected_country != "All":
    filtered_df = df[df['Country'] == selected_country]
else:
    filtered_df = df
filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]

# Update metrics based on the filtered dataframe
calculate_metrics(filtered_df)

# Apply custom styling for metrics cards container
st.markdown("""
    <style>
        .custom-metric-container {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }
    </style>
""", unsafe_allow_html=True)

unique_key = f"file_uploader_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"], key=unique_key )
if uploaded_file is not None:
    # Read uploaded file
    new_df = pd.read_csv(uploaded_file)
    
    # Display uploaded data
    st.write("Uploaded Data:")
    st.write(new_df)
    
    
    # Check if data is fetched successfully
   
# Or, you can add a separate button to trigger API data fetching:



# Define columns for charts
col7,col8 = st.columns([0.45, 0.45])

with col7:
    # Top 10 Countries by Visitors Chart
    country_visits = filtered_df['Country'].value_counts().head(10).reset_index()
    country_visits.columns = ['Country', 'Number of Visits']
    fig_country = px.bar(country_visits, x='Country', y='Number of Visits',
                         title="Top 10 Countries by Visitors",
                         template="gridon", height=500)
    fig_country.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.6)
    fig_country.update_layout(clickmode='event+select')
    st.plotly_chart(fig_country, use_container_width=True)

_, view1, dwn1, view2, dwn2 = st.columns([0.15, 0.20, 0.20, 0.20, 0.20])

with view1:
    expander = st.expander("Country of Origin by No. Views")
    data = df['Country'].value_counts()
    expander.write(data)

with dwn1:
    csv_data = data.to_csv().encode("utf-8")
    st.download_button("Get Data", csv_data, file_name="Countries of Origin by Number of visits.csv", mime="text/csv")

st.divider()

with col8:
    # Hourly Traffic Trend
    hourly_traffic = filtered_df.groupby([filtered_df['Date'].dt.date, filtered_df['Hour'].dt.hour]).size().reset_index(name='Number of Visits')
    fig_hourly_traffic = px.line(hourly_traffic, x='Date', y='Number of Visits',
                                 title=f'Daily Traffic Trend for {selected_country}',
                                 labels={'Number of Visits': 'Number of Visits', 'Date': 'Date'},
                                 template="gridon")
    st.plotly_chart(fig_hourly_traffic, use_container_width=True)

with view2:
    expander = st.expander("Number of Visits by Date and Hour")
    data = filtered_df.groupby([filtered_df['Date'].dt.date, filtered_df['Hour'].dt.hour]).size().reset_index(name='Number of Visits')
    expander.write(data)

with dwn2:
    csv_data = data.to_csv().encode("utf-8")
    st.download_button("Get Data", csv_data, file_name="Traffic Trend Analysis.csv", mime="text/csv")


col9,col10 = st.columns([0.45, 0.45])
with col9:
    # Top 10 Viewed Events
    top_events = filtered_df['Event'].value_counts().head(10).reset_index()
    top_events.columns = ['Event', 'Number of Visits']
    fig_top_events = px.bar(top_events, x='Event', y='Number of Visits',
                            title="Top 10 Viewed Events",
                            labels={'Number of Visits': 'Number of Visits', 'Event': 'Event Name'},
                            template="gridon", height=500)
    fig_top_events.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.6)
    fig_top_events.update_layout(clickmode='event+select')
    st.plotly_chart(fig_top_events, use_container_width=True)

_, view3, dwn3, view4, dwn4 = st.columns([0.15, 0.20, 0.20, 0.20, 0.20])
with view3:
    expander = st.expander("Number of Visits by Viewed Events")
    event_visits = df.groupby('Event').size().reset_index(name='Number of Visits')
    expander.write(event_visits)

with dwn3:
    csv_data = data.to_csv().encode("utf-8")
    st.download_button("Get Data", csv_data, file_name="Number of by Viewed Content.csv", mime="text/csv")   

with col10:
    # Extract the hour from the 'Timestamp' column and create a new 'Hour' column
    filtered_df['Hour'] = filtered_df['Timestamp'].dt.hour

    # Count the number of visits for each hour
    hourly_traffic = filtered_df.groupby('Hour').size().reset_index(name='Number of Visits')

    # Plot the distribution of the number of visits for each hour as a line chart
    fig_hourly_traffic = px.line(hourly_traffic, x='Hour', y='Number of Visits',
                                 title=f'Hourly Traffic Trend for {selected_country}',
                                 labels={'Number of Visits': 'Number of Visits', 'Hour': 'Hour of the Day'},
                                 template="gridon")
    st.plotly_chart(fig_hourly_traffic, use_container_width=True)

with view4:
    expander = st.expander("Distribution of Number of Visits for Each Hour")
    expander.write(hourly_traffic)

with dwn4:
    csv_data = hourly_traffic.to_csv(index=False).encode("utf-8")  # Exclude index column
    st.download_button("Get Data", csv_data, file_name="Hourly Traffic Trend.csv", mime="text/csv")
st.divider()

col11, col12 = st.columns([0.45,0.45])
with col11:

   treemap_data = df.groupby(['Request Method', 'Referrer Method', 'Event']).size().reset_index(name='Count')

# Create the treemap
   fig_treemap = px.treemap(treemap_data, path=['Referrer Method', 'Request Method', 'Event'], 
                         values='Count', color='Count',
                         title="Count of Requests with Referrer Method for Each Event", template='gridon')

# Show the treemap
   st.plotly_chart(fig_treemap, use_container_width=True)

   _, view6, dwn6 = st.columns([0.15, 0.20, 0.20])

   with view6:
    expander = st.expander("Distribution of Requests for Each Event by Method")
    expander.write(treemap_data)

   with dwn6:
    csv_data = treemap_data.to_csv(index=False).encode("utf-8")  # Exclude index column
    st.download_button("Get Data", csv_data, file_name="Requests_Distribution_By_Method.csv", mime="text/csv")

   with col12:
    # Distribution of HTTP Status Codes
    status_counts = filtered_df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig_status = px.pie(status_counts, values='Count', names='Status',
                        title=f'Distribution of HTTP Status Codes for {selected_country}',
                        template="gridon")
    st.plotly_chart(fig_status, use_container_width=True)

    _, view5, dwn5 = st.columns([0.15, 0.20,0.20])
with view5:
    expander = st.expander("Percentage of Visits by HTTP Status")
    total_visits = len(df)
    status_visits = df['Status'].value_counts(normalize=True).reset_index(name='Percentage of Visits')
    status_visits['Percentage of Visits'] *= 100  # Convert to percentage
    expander.write(status_visits)

with dwn5:
    csv_data = status_visits.to_csv(index=False).encode("utf-8")  # Exclude index column
    st.download_button("Get Data", csv_data, file_name="Percentage of Visits by HTTP Status.csv", mime="text/csv")

