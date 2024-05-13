import streamlit as st
import pandas as pd
import time
import numpy as np
import altair as alt
from streamlit_lottie import st_lottie
import requests
import json
import streamlit.components.v1 as components
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from st_aggrid.shared import JsCode
import plotly.express as px
import base64
from io import BytesIO
from streamlit_gsheets import GSheetsConnection


st.set_page_config(page_title="Off Hours", page_icon=":city_sunset:", layout="wide")


# @st.cache_data(ttl=120, show_spinner=True)
# def load_data(url):
#     df = pd.read_csv(url)
#     df['Date Created'] = pd.to_datetime(df['Date Created'], errors='coerce')  # set 'Date Created' as datetime
#     df.rename(columns={'In process (On It SME)': 'SME (On It)'}, inplace=True)  # Renaming column
#     df = df.loc[df['Working Hours?'] == 'No'] # Filter Dataframe to only include rows with 'No' in the 'Working Hours?' column
#     df['TimeTo: On It (Raw)'] = df['TimeTo: On It'].copy()
#     df['TimeTo: Attended (Raw)'] = df['TimeTo: Attended'].copy()
#     return df

@st.cache_data(ttl=120, show_spinner=True)
def load_data(data):
    df = data.copy()  # Make a copy to avoid modifying the original DataFrame
    df['Date Created'] = pd.to_datetime(df['Date Created'], errors='coerce')  
    df.rename(columns={'In process (On It SME)': 'SME (On It)'}, inplace=True)
    df = df.loc[df['Working Hours?'] == 'No'] # Filter Dataframe to only include rows with 'No' in the 'Working Hours?' column  
    df['TimeTo: On It (Raw)'] = df['TimeTo: On It'].copy()
    df['TimeTo: Attended (Raw)'] = df['TimeTo: Attended'].copy()
    df.dropna(subset=['Service'], inplace=True)
    return df

def calculate_metrics(df):
    unique_case_count = df['Service'].count()
    survey_avg = df['Survey'].mean()
    survey_count = df['Survey'].count()
    return unique_case_count, survey_avg, survey_count

def convert_to_seconds(time_str):
    if pd.isnull(time_str):
        return 0
    try:
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    except ValueError:
        return 0

def seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def minutes_to_hms(minutes):
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    secs = 0
    return f"{hours:02d}:{mins:02d}:{secs:02d}"

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSQVnfH-edbXqAXxlCb2FrhxxpsOHJhtqKMYsHWxf5SyLVpAPTSIWQeIGrBAGa16dE4CA59o2wyz59G/pub?gid=0&single=true&output=csv'
# df = load_data(url).copy()

conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet="Response and Survey Form")
df = load_data(data).copy()

# Function to load a lottie animation from a URL
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_people = load_lottieurl("https://lottie.host/2ad92c27-a3c0-47cc-8882-9eb531ee1e0c/A9tbMxONxp.json")
lottie_clap = load_lottieurl("https://lottie.host/af0a6ccc-a8ac-4921-8564-5769d8e09d1e/4Czx1gna6U.json")
lottie_queuing = load_lottieurl("https://lottie.host/910429d2-a0a4-4668-a4d4-ee831f9ccecd/yOKbdL2Yze.json")
lottie_inprogress = load_lottieurl("https://lottie.host/c5c6caea-922b-4b4e-b34a-41ecaafe2a13/mphMkSfOkR.json")
lottie_chill = load_lottieurl("https://lottie.host/2acdde4d-32d7-44a8-aa64-03e1aa191466/8EG5a8ToOQ.json")

# Button to refresh the data - align to upper right
col1, col2 = st.columns([3, .350])
with col2:
    if st.button(':red[Refresh Data]'):
        # st.experimental_memo.clear()
        st.cache_data.clear()
        # st.experimental_rerun()
        st.rerun()

# Center align 'five9 srr agent view'
st.markdown(
    f"<h1 style='text-align: center;'>Five9 SRR Management View</h1>",
    unsafe_allow_html=True
)

st.markdown(
    f"<h3 style='text-align: center;'>Off Hours</h3>",
    unsafe_allow_html=True
)

cols1, cols2, cols3 = st.columns(3)

with cols1:
# Display Lottie animation
    st_lottie(lottie_people, speed=1, reverse=False, loop=True, quality="low", height=200, width=200, key=None)

with cols2:
    if st.selectbox:
        selected_service = st.selectbox('Service', ['All'] + list(df['Service'].unique()))

    # Apply filtering
    if selected_service != 'All':
        df_filtered = df[df['Service'] == selected_service]
    else:
        df_filtered = df

with cols3:
    if st.selectbox:
        selected_month = st.selectbox('Month', ['All'] + list(df_filtered['Month'].unique()))

    # Apply filtering
    if selected_month != 'All':
        df_filtered = df_filtered[df_filtered['Month'] == selected_month]
    else:
        df_filtered = df_filtered

st.write(':wave: Welcome:exclamation:')
# st.title('Five9 SRR Management View')


# Insert Five9 logo
five9logo_url = "https://raw.githubusercontent.com/mackensey31712/srr/main/five9log1.png"


# DataFrames for "In Queue" and "In Progress"
df_inqueue = df_filtered[df_filtered['Status'] == 'In Queue']
df_inqueue = df_inqueue[['Case #', 'Requestor','Service','Creation Timestamp', 'Message Link']]
df_inprogress = df_filtered[df_filtered['Status'] == 'In Progress']
df_inprogress = df_inprogress[['Case #', 'Requestor','Service','Creation Timestamp', 'SME (On It)', 'TimeTo: On It', 'Message Link']]


# Metrics
df_filtered['TimeTo: On It Sec'] = df_filtered['TimeTo: On It'].apply(convert_to_seconds)
df_filtered['TimeTo: Attended Sec'] = df_filtered['TimeTo: Attended'].apply(convert_to_seconds)
# overall_avg_on_it = df_filtered['TimeTo: On It Sec'].mean()
# overall_avg_attended = df_filtered['TimeTo: Attended Sec'].mean()
# unique_case_count, survey_avg, survey_count = calculate_metrics(df_filtered)

# # Display metrics
# col1, col2, col3, col4, col5 = st.columns(5)
# with col1:
#     st.metric(label="Interactions", value=unique_case_count)
# with col2:
#     st.metric(label="Survey Avg.", value=f"{survey_avg:.2f}")
# with col3:
#     st.metric(label="Answered Surveys", value=survey_count)
# with col4:
#     st.metric("Overall Avg. TimeTo: On It", seconds_to_hms(overall_avg_on_it))
# with col5:
#     st.metric("Overall Avg. TimeTo: Attended", seconds_to_hms(overall_avg_attended))


# Ensure 'TimeTo: On It' and 'TimeTo: Attended' are in timedelta format
df_filtered['TimeTo: On It'] = pd.to_timedelta(df_filtered['TimeTo: On It'])
df_filtered['TimeTo: Attended'] = pd.to_timedelta(df_filtered['TimeTo: Attended'])

# Calculate the average seconds directly from 'TimeTo: On It' and 'TimeTo: Attended', and convert to 'hh:mm:ss'
overall_avg_on_it_sec = df_filtered['TimeTo: On It'].dt.total_seconds().mean()
overall_avg_attended_sec = df_filtered['TimeTo: Attended'].dt.total_seconds().mean()
unique_case_count, survey_avg, survey_count = calculate_metrics(df_filtered)

overall_avg_on_it_hms = seconds_to_hms(overall_avg_on_it_sec)
overall_avg_attended_hms = seconds_to_hms(overall_avg_attended_sec)


# Display metrics
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(label="Interactions", value=unique_case_count)
with col2:
    st.metric(label="Survey Avg.", value=f"{survey_avg:.2f}")
with col3:
    st.metric(label="Answered Surveys", value=survey_count)
with col4:
    st.metric("Overall Avg. TimeTo: On It", overall_avg_on_it_hms)
with col5:
    st.metric("Overall Avg. TimeTo: Attended", overall_avg_attended_hms)

# Preprocess the DataFrame to remove commas from the "Case #" column
df_inqueue['Case #'] = df_inqueue['Case #'].astype(str).str.replace(',', '')
df_inprogress['Case #'] = df_inprogress['Case #'].astype(str).str.replace(',', '')

# Display "In Queue" DataFrame with count and some text
in_queue_count = len(df_inqueue)

# Using columns to place text and animation side by side
if in_queue_count == 0:
    col1, col2 = st.columns([0.3, 1.2])  # Adjust the ratio as needed for your layout
    with col1:
        st.title(f'In Queue (0)')
    with col2:
        # Display Lottie animation if count is 0
        st_lottie(lottie_clap, speed=1, height=100, width=200)  # Adjust height as needed
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(df_inqueue, use_container_width=True)
else:
    col1, col2 = st.columns([0.3, 1.2])  # Adjust the ratio as needed for your layout
    with col1:
        st.title(f'In Queue ({in_queue_count})')
    with col2:
        # Display Lottie animation if count is not 0
        st_lottie(lottie_queuing, speed=1, height=100, width=200)  # Adjust height as needed
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(df_inqueue, use_container_width=True)


# Display "In Progress" DataFrame with count
in_progress_count = len(df_inprogress)
if in_progress_count == 0:
    col1, col2 = st.columns([0.4, 1.2])  # Adjust the ratio as needed for your layout
    with col1:
        st.title(f'In Progress (0)')
    with col2:
        # Display Lottie animation if count is 0
        st_lottie(lottie_chill, speed=1, height=100, width=200)  # Adjust height as needed
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(df_inprogress, use_container_width=True)
else:
    col1, col2 = st.columns([0.4, 1.2])  # Adjust the ratio as needed for your layout
    with col1:
        st.title(f'In Progress ({in_progress_count})')
    with col2:
        # Display Lottie animation if count is not 0
        st_lottie(lottie_inprogress, speed=1, height=100, width=200)  # Adjust height as needed
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(df_inprogress, use_container_width=True)

filtered_columns = ['Case #', 'Service', 'Inquiry', 'Requestor', 'Creation Timestamp',
       'SME (On It)', 'On It Time', 'Attendee', 'Attended Timestamp',
       'Message Link', 'Message Link 0', 'Message Link 1', 'Message Link 2',
       'Status', 'Case Reason', 'AFI', 'AFI Comment', 'Article#',
       'TimeTo: On It (Raw)', 'TimeTo: Attended (Raw)','Month', 'Day', 'Weekend?',
       'Date Created', 'Working Hours?', 'Survey', 'Hour_Created']

# Display the filtered dataframe
st.title('Data')
with st.expander(':blue[Show Data]', expanded=False):
    st.dataframe(df_filtered[filtered_columns], use_container_width=True)

"---"
col1, col2 = st.columns(2)

with col1:
    # Create a bar chart showing the stacked counts of "Service" by "Hour_Created"
    agg_hour_service = df_filtered.groupby(['Hour_Created', 'Service']).size().unstack(fill_value=0).reset_index()

    # Sum of counts for each hour to use as data labels
    agg_hour_service['Total'] = agg_hour_service.iloc[:, 1:].sum(axis=1)

    fig = px.bar(agg_hour_service, x='Hour_Created', y=agg_hour_service.columns[1:-1], title='Hourly Interactions by Service',
                labels={'value': 'Interactions', 'Hour_Created': 'Hour of Creation', 'variable': 'Service'}, 
                category_orders={'Service': agg_hour_service.columns[1:-1]})
    fig.update_layout(barmode='stack')

    # Add data labels with total counts
    for i in range(len(agg_hour_service)):
        fig.add_annotation(x=agg_hour_service['Hour_Created'][i], y=agg_hour_service['Total'][i],
                        text=str(agg_hour_service['Total'][i]),
                        showarrow=False,
                        yshift=5,  # Adjust the y-shift to move the label above the bar
                        font=dict(color='black', size=10))  # Adjust font color and size

    st.plotly_chart(fig, use_container_width=True)

    csv = agg_hour_service.to_csv(index=False).encode('utf-8')

    # Show the data in a collapsible table
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(agg_hour_service, use_container_width=True)
        # Download button
        st.download_button(':green[Download Data]', csv, file_name='hourly_interactions_by_service.csv', mime='text/csv', 
                        help="Click to download the Hourly Interactions by Service in CSV format")


with col2:
    # Create a line chart that would show the average 'TimeTo: On It' in minutes by "Hour_Created"
    # Group by 'Hour_Created' and calculate mean 'TimeTo: On It Sec'
    agg_hour_on_it = df_filtered.groupby('Hour_Created')[['TimeTo: On It Sec']].mean().reset_index()

    # Convert mean 'TimeTo: On It Sec' to minutes
    agg_hour_on_it['TimeTo: On It Minutes'] = agg_hour_on_it['TimeTo: On It Sec'] / 60

    # Create the line chart
    fig = px.line(agg_hour_on_it, x='Hour_Created', y='TimeTo: On It Minutes', title='Average Timeto: On It By The Hour')
    st.plotly_chart(fig, use_container_width=True)

    # Convert 'TimeTo: On It Minutes' to "h:mm:ss" format
    agg_hour_on_it['TimeTo: On It HH:MM:SS'] = agg_hour_on_it['TimeTo: On It Minutes'].apply(minutes_to_hms)

    csv = agg_hour_on_it.to_csv(index=False).encode('utf-8')

    # Show the data in a collapsible table
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(agg_hour_on_it[['Hour_Created', 'TimeTo: On It HH:MM:SS']], use_container_width=True)
        # Download button
        st.download_button(':green[Download Data]', csv, file_name='average_time_to_on_it.csv', mime='text/csv', help="Click to download the Average Time to On It by Hour in CSV format")

col1, col2 = st.columns(2)

with col1:
    pivot_table = df_filtered.pivot_table(index='Hour_Created', columns='Case Reason', values='Service', aggfunc='count', fill_value=0)

    # Create the stacked bar chart
    fig = px.bar(pivot_table, x=pivot_table.index, y=pivot_table.columns, barmode='stack', title='Case Reason Distribution by Hour')

    # Customize the layout
    fig.update_layout(
        xaxis_title='Hour',
        yaxis_title='Count',
        legend_title='Case Reason',
        xaxis=dict(tickangle=0),  # Rotate x-axis labels by 45 degrees
    )

    # Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

agg_month = df_filtered.groupby('Month').agg({
    'TimeTo: On It Sec': 'mean',
    'TimeTo: Attended Sec': 'mean'
}).reset_index()

agg_month['TimeTo: On It'] = agg_month['TimeTo: On It Sec'].apply(seconds_to_hms)
agg_month['TimeTo: Attended'] = agg_month['TimeTo: Attended Sec'].apply(seconds_to_hms)

agg_service = df_filtered.groupby('Service').agg({
    'TimeTo: On It Sec': 'mean',
    'TimeTo: Attended Sec': 'mean'
}).reset_index()

agg_service['TimeTo: On It'] = agg_service['TimeTo: On It Sec'].apply(seconds_to_hms)
agg_service['TimeTo: Attended'] = agg_service['TimeTo: Attended Sec'].apply(seconds_to_hms)

# converting seconds to minutes or hours for a more interpretable visualization
agg_month['TimeTo: On It Minutes'] = agg_month['TimeTo: On It Sec'] / 60
agg_month['TimeTo: Attended Minutes'] = agg_month['TimeTo: Attended Sec'] / 60

with col2:
    
    # Group by "Case Reason" and count "Case #" occurrences
    case_counts = df_filtered.groupby('Case Reason')['Service'].count().reset_index()

    # Sort the DataFrame by counts in ascending order
    case_counts_sorted = case_counts.sort_values(by='Service', ascending=True)

    # Generate a pie chart
    fig = px.pie(case_counts_sorted, values='Service', names='Case Reason', title='Distribution of Case Reasons', hole=0.5)

    # Show the pie chart in the Streamlit app
    st.plotly_chart(fig)

col1, col2 = st.columns(2)

with col1:
    # Group by 'Case Reason' and calculate the mean 'TimeTo: Attended Sec'
    avg_attended_by_case_reason = df_filtered.groupby('Case Reason')['TimeTo: Attended Sec'].mean().reset_index().sort_values(by='TimeTo: Attended Sec', ascending=False)

    # Convert the mean 'TimeTo: Attended Sec' to a readable time format
    avg_attended_by_case_reason['Avg TimeTo: Attended'] = avg_attended_by_case_reason['TimeTo: Attended Sec'].apply(seconds_to_hms)

    # Display the table
    st.subheader('Average TimeTo: Attended by Case Reason')
    st.dataframe(avg_attended_by_case_reason[['Case Reason', 'Avg TimeTo: Attended']].reset_index(drop=True), use_container_width=True)


with col2:
     # Group by 'Case Reason' and calculate the mean 'TimeTo: Attended Sec'
    avg_on_it_by_case_reason = df_filtered.groupby('Case Reason')['TimeTo: On It Sec'].mean().reset_index().sort_values(by='TimeTo: On It Sec', ascending=False)

    # Convert the mean 'TimeTo: Attended Sec' to a readable time format
    avg_on_it_by_case_reason['Avg TimeTo: On It'] = avg_on_it_by_case_reason['TimeTo: On It Sec'].apply(seconds_to_hms)

    # Display the table
    st.subheader('Average TimeTo: On It by Case Reason')
    st.dataframe(avg_on_it_by_case_reason[['Case Reason', 'Avg TimeTo: On It']].reset_index(drop=True), use_container_width=True)



col1,col5 = st.columns(2)

# Create an interactive bar chart using Altair

# Adjust the column names to remove spaces and special characters
agg_month.rename(columns={
    'TimeTo: On It Minutes': 'TimeTo_On_It_Minutes',
    'TimeTo: Attended Minutes': 'TimeTo_Attended_Minutes'
}, inplace=True)

agg_month_long = agg_month.melt(id_vars=['Month'],
                                value_vars=['TimeTo_On_It_Minutes', 'TimeTo_Attended_Minutes'],
                                var_name='Category',
                                value_name='Minutes')

month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# Create a stacked bar chart with months ordered as specified
chart = alt.Chart(agg_month_long).mark_bar().encode(
    x=alt.X('Month', sort=month_order),  # Use the 'sort' argument to order months
    y=alt.Y('Minutes', stack='zero'),  # Use stack='zero' for stacking
    color='Category',  # Color distinguishes the categories
    tooltip=['Month', 'Category', 'Minutes']  # Optional: add tooltip for interactivity
).properties(
    title='Monthly Response Times',
    width=600,
    height=400
)

# Display the 'Monthly Response Times' chart
with col1:
    st.write(chart)

# Convert seconds to minutes directly for 'agg_service'
agg_service['TimeTo_On_It_Minutes'] = agg_service['TimeTo: On It Sec'] / 60
agg_service['TimeTo_Attended_Minutes'] = agg_service['TimeTo: Attended Sec'] / 60

# Now, the DataFrame 'agg_service' contains correctly named columns for melting
agg_service_long = agg_service.melt(id_vars=['Service'],
                                    value_vars=['TimeTo_On_It_Minutes', 'TimeTo_Attended_Minutes'],
                                    var_name='Category',
                                    value_name='Minutes')

# Create a grouped bar chart
chart2 = alt.Chart(agg_service_long).mark_bar().encode(
    x='Service',
    y=alt.Y('Minutes', stack='zero'),  # Use stack='zero' for stacking
    color='Category',  # Color distinguishes the categories
    tooltip=['Service', 'Category', 'Minutes']  # Optional: add tooltip for interactivity
).properties(
    title='Group Response Times',
    width=600,
    height=400
)

# Display 'Group Response Times'
with col5:
    st.write(chart2)

# Create an interactive bar chart to show the 'unique case count' for each unique 'Service'
chart3 = alt.Chart(df_filtered).mark_bar().encode(
    x='Service',
    y='count()',
    tooltip=['Service', 'count()']
).properties(
    title='Interaction Count',
    width=600,
    height=600
)

# Display 'Interaction Count' chart
with col1:
    st.write(chart3)

# Create an interactive bar chart to show the 'unique case count' for each 'SME (On It)'
chart4 = alt.Chart(df_filtered).mark_bar().encode(
    y=alt.Y('SME (On It):N', sort='-x'),  # Sorting based on the count in descending order, ensure to specify ':N' for nominal data
    x=alt.X('count()', title='Unique Case Count'),
    tooltip=['SME (On It)', 'count()']
).properties(
    title='Interactions Handled',
    width=600,
    height=600
)

# Display 'Interactions Handled' chart
with col5:
    st.write(chart4)

st.subheader('Interaction Count by Requestor')

# Display a Dataframe where the rows are the 'Requestor', the columns would be the 'Service', and the values would be the count of each 'Service'

# Create a pivot table using pandas
pivot_df = df_filtered.pivot_table(index='Requestor', columns='Service', aggfunc='size', fill_value=0)

# Reset the index so 'Requestor' becomes a regular column
pivot_df.reset_index(inplace=True)

# Setting up GridOptions for AgGrid
gb = GridOptionsBuilder.from_dataframe(pivot_df)
gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)  # Enable pagination
# gb.configure_side_bar(filters_panel=False, columns_panel=False)  # Enable side bar if you want filters and columns tool panel
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=False)

gridOptions = gb.build()

# Display the AgGrid component with the configured options
AgGrid(pivot_df, gridOptions=gridOptions, update_mode=GridUpdateMode.MODEL_CHANGED, fit_columns_on_grid_load=True)

# Convert the DataFrame to CSV
csv = pivot_df.to_csv(index=False)

# # Create a download button
# b64 = base64.b64encode(csv.encode()).decode()
# href = f'<a href="data:file/csv;base64,{b64}" download="interaction_count_by_requestor.csv">Download in CSV</a>'
# st.markdown(href, unsafe_allow_html=True)

csv = pivot_df.to_csv(index=False).encode('utf-8') 

# Create an download button using st.download_button to download the pivot_df to CSV
st.download_button(':green[Download Data]', csv, file_name='interaction_count_by_requestor.csv', mime='text/csv',help="Download Interaction Count by Requestor Data in CSV format")

st.divider()

# Creating the Summary Table where it sorts the SME (On It) column by first getting the total average TimeTo: On It and average TimeTo: Attended and then sorting it by the number of Interactions
# and then by the highest average survey.

# Group by 'SME (On It)' and calculate the required metrics including average survey
df_grouped = df_filtered.groupby('SME (On It)').agg(
    Avg_On_It_Sec=pd.NamedAgg(column='TimeTo: On It Sec', aggfunc='mean'),
    Avg_Attended_Sec=pd.NamedAgg(column='TimeTo: Attended Sec', aggfunc='mean'),
    Number_of_Interactions=pd.NamedAgg(column='SME (On It)', aggfunc='count'),
    Avg_Survey=pd.NamedAgg(column='Survey', aggfunc='mean')  # Calculate the average survey score
).reset_index()

df_grouped['Total_Avg_Sec'] = df_grouped['Avg_On_It_Sec'] + df_grouped['Avg_Attended_Sec']

# Sort by Total_Avg_Sec, Number_of_Interactions, and then by Avg_Survey in descending order
df_sorted = df_grouped.sort_values(by=['Total_Avg_Sec', 'Number_of_Interactions', 'Avg_Survey'], ascending=[True, False, False])

df_sorted['Avg_On_It'] = df_sorted['Avg_On_It_Sec'].apply(seconds_to_hms)
df_sorted['Avg_Attended'] = df_sorted['Avg_Attended_Sec'].apply(seconds_to_hms)

# Rename 'SME (On It)' column to 'SME'
df_sorted.rename(columns={'SME (On It)': 'SME'}, inplace=True)

# Display "Summary Table"
st.subheader('SME Summary Table')
st.dataframe(df_sorted[['SME', 'Avg_On_It', 'Avg_Attended', 'Number_of_Interactions', 'Avg_Survey']].reset_index(drop=True))


# Convert the 'Avg_On_It_Sec' and 'Avg_Attended_Sec' columns to minutes
df_sorted['Avg_On_It_Min'] = df_sorted['Avg_On_It_Sec'] / 60
df_sorted['Avg_Attended_Min'] = df_sorted['Avg_Attended_Sec'] / 60

st.markdown(":arrow_up: 5 minutes = :red[red]")

# Define the Altair chart for Avg_On_It_Min
chart_on_it = alt.Chart(df_sorted).mark_bar().encode(
    x=alt.X('SME', title='SME', sort='-y'),
    y=alt.Y('Avg_On_It_Min:Q', title='Average Time On It (Minutes)'),
    color=alt.condition(
        alt.datum.Avg_On_It_Min > 5,
        alt.value('red'),
        alt.value('steelblue')
    ),
    tooltip=['SME', alt.Tooltip('Avg_On_It_Min:Q', title='Average Time On It (Minutes)')]
).properties(
    width=600,
    height=400,
    title='Average Time On It by SME'
)

# Define the Altair chart for Avg_Attended_Min
chart_attended = alt.Chart(df_sorted).mark_bar().encode(
    x=alt.X('SME', title='SME', sort='-y'),
    y=alt.Y('Avg_Attended_Min:Q', title='Average Time Attended (Minutes)'),
    tooltip=['SME', alt.Tooltip('Avg_Attended_Min:Q', title='Average Time Attended (Minutes)')]
).properties(
    width=600,
    height=400,
    title='Average Time Attended by SME'
)

# Display the charts using Altair's interactive renderer
st.altair_chart(chart_on_it, use_container_width=True)
st.altair_chart(chart_attended, use_container_width=True)

# Auto-update every 5 minutes
refresh_rate = 120  # 300 seconds = 5 minutes
time.sleep(refresh_rate)
st.rerun()
