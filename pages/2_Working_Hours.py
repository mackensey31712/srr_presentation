import streamlit as st
import pandas as pd
import time
import numpy as np
import altair as alt
from streamlit_lottie import st_lottie
import requests
import streamlit.components.v1 as components
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from st_aggrid.shared import JsCode
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Working Hours (M-F, 5am-4PM)", page_icon=":city_sunrise:", layout="wide")

# Set timezone to America/Los_Angeles
timezone = pytz.timezone('America/Los_Angeles')

# @st.cache_data(ttl=120, show_spinner=True)
# def load_data(url):
#     df = pd.read_csv(url)
#     df['Date Created'] = pd.to_datetime(df['Date Created'], errors='coerce')  # set 'Date Created' as datetime
#     df.rename(columns={'In process (On It SME)': 'SME (On It)'}, inplace=True)  # Renaming column
#     df = df.loc[df['Working Hours?'] == 'Yes'] # Filter Dataframe to only include rows with 'Yes' in the 'Working Hours?' column
#     df['TimeTo: On It (Raw)'] = df['TimeTo: On It'].copy()
#     df['TimeTo: Attended (Raw)'] = df['TimeTo: Attended'].copy()
#     return df

@st.cache_data(ttl=120, show_spinner=True)
def load_data(data):
    df = data.copy()  # Make a copy to avoid modifying the original DataFrame
    df['Date Created'] = pd.to_datetime(df['Date Created'], errors='coerce').dt.tz_localize(timezone)   
    df.rename(columns={'In process (On It SME)': 'SME (On It)'}, inplace=True)
    df = df.loc[df['Working Hours?'] == 'Yes'] # Filter Dataframe to only include rows with 'Yes' in the 'Working Hours?' column  
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

# def seconds_to_hms(seconds):
#     hours = seconds // 3600
#     minutes = (seconds % 3600) // 60
#     seconds = seconds % 60
#     return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

# Convert seconds to h:mmm:ss while also accounting for negative values
def seconds_to_hms(seconds):
    if np.isnan(seconds):
        return "00:00:00"
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"

def minutes_to_hms(minutes):
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    secs = 0
    return f"{hours:02d}:{mins:02d}:{secs:02d}"

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet="Response and Survey Form", usecols=list(range(31)))
df = load_data(data).copy()

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

col1, col2 = st.columns([3, .350])
with col2:
    if st.button(':red[Refresh Data]'):
        st.cache_data.clear()
        st.rerun()

st.markdown(
    f"<h1 style='text-align: center;'>Five9 SRR Management View</h1>",
    unsafe_allow_html=True
)

st.markdown(
    f"<h2 style='text-align: center;'>Working Hours (M-F, 5am - 4 pm)</h2>",
    unsafe_allow_html=True
)

cols1, cols2, cols3, cols4 = st.columns(4)

with cols1:
    st_lottie(lottie_people, speed=1, reverse=False, loop=True, quality="low", height=200, width=200, key=None)

with cols2:
    selected_service = st.selectbox('Service', ['All'] + list(df['Service'].unique()))
    if selected_service != 'All':
        df_filtered = df[df['Service'] == selected_service]
    else:
        df_filtered = df

with cols3:
    current_month = datetime.now(timezone).strftime('%B')
    selected_month = st.selectbox('Month', ['All'] + list(df_filtered['Month'].unique()), index=(df_filtered['Month'].unique().tolist().index(current_month) + 1) if current_month in df_filtered['Month'].unique() else 0)
    if selected_month != 'All':
        df_filtered = df_filtered[df_filtered['Month'] == selected_month]
    else:
        df_filtered = df

with cols4:
    default_start_date = (datetime.now(timezone).replace(day=1) - timedelta(days=1)).replace(day=1)
    default_end_date = datetime.now(timezone).replace(day=1) - timedelta(days=1)

    date_range = st.date_input("Select Delta Range", value=(default_start_date, default_end_date))
    start_date, end_date = date_range[0], date_range[1]

    start_date = timezone.localize(datetime.combine(start_date, datetime.min.time()))
    end_date = timezone.localize(datetime.combine(end_date, datetime.max.time()))

st.write(':wave: Welcome:exclamation:')

la_timezone = pytz.timezone('America/Los_Angeles')

la_now = datetime.now(la_timezone)

st.sidebar.markdown(f"**Last Updated:** {la_now.strftime('%Y-%m-%d, %H:%M:%S %Z%z')}")

five9logo_url = "https://raw.githubusercontent.com/mackensey31712/srr/main/five9log1.png"

df_inqueue = df_filtered[df_filtered['Status'] == 'In Queue']
df_inqueue = df_inqueue[['Case #', 'Requestor', 'Service', 'Creation Timestamp', 'Message Link']]
df_inprogress = df_filtered[df_filtered['Status'] == 'In Progress']
df_inprogress = df_inprogress[['Case #', 'Requestor', 'Service', 'Creation Timestamp', 'SME (On It)', 'TimeTo: On It', 'Message Link']]

df_filtered.loc[:, 'TimeTo: On It Sec'] = df_filtered['TimeTo: On It'].apply(convert_to_seconds)
df_filtered.loc[:, 'TimeTo: Attended Sec'] = df_filtered['TimeTo: Attended'].apply(convert_to_seconds)

df_filtered.loc[:, 'TimeTo: On It'] = pd.to_timedelta(df_filtered['TimeTo: On It'], errors='coerce')
df_filtered.loc[:, 'TimeTo: Attended'] = pd.to_timedelta(df_filtered['TimeTo: Attended'], errors='coerce')

overall_avg_on_it_sec = df_filtered['TimeTo: On It'].dt.total_seconds().mean()
overall_avg_attended_sec = df_filtered['TimeTo: Attended'].dt.total_seconds().mean()
unique_case_count, survey_avg, survey_count = calculate_metrics(df_filtered)

overall_avg_on_it_hms = seconds_to_hms(overall_avg_on_it_sec)
overall_avg_attended_hms = seconds_to_hms(overall_avg_attended_sec)

df_custom_range = df[(df['Date Created'] >= start_date) & (df['Date Created'] <= end_date)]

df_custom_range.loc[:, 'TimeTo: On It'] = pd.to_timedelta(df_custom_range['TimeTo: On It'], errors='coerce')
df_custom_range.loc[:, 'TimeTo: Attended'] = pd.to_timedelta(df_custom_range['TimeTo: Attended'], errors='coerce')

custom_range_avg_on_it_sec = df_custom_range['TimeTo: On It'].dt.total_seconds().mean()
custom_range_avg_attended_sec = df_custom_range['TimeTo: Attended'].dt.total_seconds().mean()

delta_on_it = overall_avg_on_it_sec - custom_range_avg_on_it_sec if not np.isnan(custom_range_avg_on_it_sec) else 0
delta_attended = overall_avg_attended_sec - custom_range_avg_attended_sec if not np.isnan(custom_range_avg_attended_sec) else 0

delta_on_it_hms = seconds_to_hms(delta_on_it)
delta_attended_hms = seconds_to_hms(delta_attended)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(label="Interactions", value=unique_case_count)
with col2:
    st.metric(label="Survey Avg.", value=f"{survey_avg:.2f}")
with col3:
    st.metric(label="Answered Surveys", value=survey_count)
with col4:
    st.metric("Overall Avg. TimeTo: On It", overall_avg_on_it_hms, delta=delta_on_it_hms, delta_color="inverse" )
with col5:
    st.metric("Overall Avg. TimeTo: Attended", overall_avg_attended_hms, delta=delta_attended_hms, delta_color="inverse")

df_inqueue['Case #'] = df_inqueue['Case #'].astype(str).str.replace(',', '')
df_inprogress['Case #'] = df_inprogress['Case #'].astype(str).str.replace(',', '')

in_queue_count = len(df_inqueue)

if in_queue_count == 0:
    col1, col2 = st.columns([0.3, 1.2])
    with col1:
        st.title(f'In Queue (0)')
    with col2:
        st.lottie(lottie_clap, speed=1, height=100, width=200)
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(df_inqueue, use_container_width=True)
else:
    col1, col2 = st.columns([0.3, 1.2])
    with col1:
        st.title(f'In Queue ({in_queue_count})')
    with col2:
        st.lottie(lottie_queuing, speed=1, height=100, width=200)
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(df_inqueue, use_container_width=True)

in_progress_count = len(df_inprogress)
if in_progress_count == 0:
    col1, col2 = st.columns([0.4, 1.2])
    with col1:
        st.title(f'In Progress (0)')
    with col2:
        st.lottie(lottie_chill, speed=1, height=100, width=200)
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(df_inprogress, use_container_width=True)
else:
    col1, col2 = st.columns([0.4, 1.2])
    with col1:
        st.title(f'In Progress ({in_progress_count})')
    with col2:
        st.lottie(lottie_inprogress, speed=1, height=100, width=200)
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(df_inprogress, use_container_width=True)

filtered_columns = ['Case #', 'Service', 'Inquiry', 'Requestor', 'Creation Timestamp', 'SME (On It)', 'On It Time', 'Attendee', 'Attended Timestamp', 'Message Link', 'Message Link 0', 'Message Link 1', 'Message Link 2', 'Status', 'Case Reason', 'AFI', 'AFI Comment', 'Article#', 'TimeTo: On It (Raw)', 'TimeTo: Attended (Raw)', 'Month', 'Day', 'Weekend?', 'Date Created', 'Working Hours?', 'Survey', 'Hour_Created']

st.title('Data')
with st.expander(':blue[Show Data]', expanded=False):
    st.dataframe(df_filtered[filtered_columns], use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    agg_hour_service = df_filtered.groupby(['Hour_Created', 'Service']).size().unstack(fill_value=0).reset_index()
    agg_hour_service['Total'] = agg_hour_service.iloc[:, 1:].sum(axis=1)

    fig = px.bar(agg_hour_service, x='Hour_Created', y=agg_hour_service.columns[1:-1], title='Hourly Interactions by Service', labels={'value': 'Interactions', 'Hour_Created': 'Hour of Creation', 'variable': 'Service'}, category_orders={'Service': agg_hour_service.columns[1:-1]})
    fig.update_layout(barmode='stack')

    for i in range(len(agg_hour_service)):
        fig.add_annotation(x=agg_hour_service['Hour_Created'][i], y=agg_hour_service['Total'][i], text=str(agg_hour_service['Total'][i]), showarrow=False, yshift=5, font=dict(color='black', size=10))

    st.plotly_chart(fig, use_container_width=True)
    csv = agg_hour_service.to_csv(index=False).encode('utf-8')
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(agg_hour_service, use_container_width=True)
        st.download_button(':green[Download Data]', csv, file_name='hourly_interactions_by_service.csv', mime='text/csv', help="Click to download the Hourly Interactions by Service in CSV format")

with col2:
    agg_hour_on_it = df_filtered.groupby('Hour_Created')[['TimeTo: On It Sec']].mean().reset_index()
    agg_hour_on_it['TimeTo: On It Minutes'] = agg_hour_on_it['TimeTo: On It Sec'] / 60
    fig = px.line(agg_hour_on_it, x='Hour_Created', y='TimeTo: On It Minutes', title='Average Timeto: On It By The Hour')
    st.plotly_chart(fig, use_container_width=True)
    agg_hour_on_it['TimeTo: On It HH:MM:SS'] = agg_hour_on_it['TimeTo: On It Minutes'].apply(minutes_to_hms)
    csv = agg_hour_on_it.to_csv(index=False).encode('utf-8')
    with st.expander(":blue[Show Data]", expanded=False):
        st.dataframe(agg_hour_on_it[['Hour_Created', 'TimeTo: On It HH:MM:SS']], use_container_width=True)
        st.download_button(':green[Download Data]', csv, file_name='average_time_to_on_it.csv', mime='text/csv', help="Click to download the Average Time to On It by Hour in CSV format")

col1, col2 = st.columns(2)

# with col1:
#     pivot_table = df_filtered.pivot_table(index='Hour_Created', columns='Case Reason', values='Service', aggfunc='count', fill_value=0)
#     fig = px.bar(pivot_table, x=pivot_table.index, y=pivot_table.columns, barmode='stack', title='Case Reason Distribution by Hour')
#     fig.update_layout(xaxis_title='Hour', yaxis_title='Count', legend_title='Case Reason', xaxis=dict(tickangle=0))
#     st.plotly_chart(fig, use_container_width=True)

with col1:
    pivot_table = df_filtered.pivot_table(index='Hour_Created', columns='Case Reason', values='Service', aggfunc='count', fill_value=0).reset_index()
    pivot_table_long = pivot_table.melt(id_vars=['Hour_Created'], var_name='Case Reason', value_name='Count')

    # Create the stacked bar chart
    fig = px.bar(pivot_table_long, x='Hour_Created', y='Count', color='Case Reason', barmode='stack', title='Case Reason Distribution by Hour')

    # Customize the layout
    fig.update_layout(
        xaxis_title='Hour',
        yaxis_title='Count',
        legend_title='Case Reason',
        xaxis=dict(tickangle=0)  # Rotate x-axis labels by 45 degrees
    )

    # Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

agg_month = df_filtered.groupby('Month').agg({'TimeTo: On It Sec': 'mean', 'TimeTo: Attended Sec': 'mean'}).reset_index()
agg_month['TimeTo: On It'] = agg_month['TimeTo: On It Sec'].apply(seconds_to_hms)
agg_month['TimeTo: Attended'] = agg_month['TimeTo: Attended Sec'].apply(seconds_to_hms)
agg_service = df_filtered.groupby('Service').agg({'TimeTo: On It Sec': 'mean', 'TimeTo: Attended Sec': 'mean'}).reset_index()
agg_service['TimeTo: On It'] = agg_service['TimeTo: On It Sec'].apply(seconds_to_hms)
agg_service['TimeTo: Attended'] = agg_service['TimeTo: Attended Sec'].apply(seconds_to_hms)

agg_month['TimeTo: On It Minutes'] = agg_month['TimeTo: On It Sec'] / 60
agg_month['TimeTo: Attended Minutes'] = agg_month['TimeTo: Attended Sec'] / 60

with col2:
    case_counts = df_filtered.groupby('Case Reason')['Service'].count().reset_index()
    case_counts_sorted = case_counts.sort_values(by='Service', ascending=True)
    fig = px.pie(case_counts_sorted, values='Service', names='Case Reason', title='Distribution of Case Reasons', hole=0.5)
    st.plotly_chart(fig)

col1, col2 = st.columns(2)

with col1:
    avg_attended_by_case_reason = df_filtered.groupby('Case Reason')['TimeTo: Attended Sec'].mean().reset_index().sort_values(by='TimeTo: Attended Sec', ascending=False)
    avg_attended_by_case_reason['Avg TimeTo: Attended'] = avg_attended_by_case_reason['TimeTo: Attended Sec'].apply(seconds_to_hms)
    st.subheader('Average TimeTo: Attended by Case Reason')
    st.dataframe(avg_attended_by_case_reason[['Case Reason', 'Avg TimeTo: Attended']].reset_index(drop=True), use_container_width=True)

with col2:
    avg_on_it_by_case_reason = df_filtered.groupby('Case Reason')['TimeTo: On It Sec'].mean().reset_index().sort_values(by='TimeTo: On It Sec', ascending=False)
    avg_on_it_by_case_reason['Avg TimeTo: On It'] = avg_on_it_by_case_reason['TimeTo: On It Sec'].apply(seconds_to_hms)
    st.subheader('Average TimeTo: On It by Case Reason')
    st.dataframe(avg_on_it_by_case_reason[['Case Reason', 'Avg TimeTo: On It']].reset_index(drop=True), use_container_width=True)

col1, col5 = st.columns(2)

agg_month.rename(columns={'TimeTo: On It Minutes': 'TimeTo_On_It_Minutes', 'TimeTo: Attended Minutes': 'TimeTo_Attended_Minutes'}, inplace=True)
agg_month_long = agg_month.melt(id_vars=['Month'], value_vars=['TimeTo_On_It_Minutes', 'TimeTo_Attended_Minutes'], var_name='Category', value_name='Minutes')
month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

chart = alt.Chart(agg_month_long).mark_bar().encode(
    x=alt.X('Month', sort=month_order),  
    y=alt.Y('Minutes', stack='zero'),  
    color='Category',  
    tooltip=['Month', 'Category', 'Minutes']  
).properties(
    title='Monthly Response Times',
    width=800,
    height=600
)

agg_month['TimeTo_On_It_HH:MM:SS'] = agg_month['TimeTo_On_It_Minutes'].apply(minutes_to_hms)
agg_month['TimeTo_Attended_HH:MM:SS'] = agg_month['TimeTo_Attended_Minutes'].apply(minutes_to_hms)

csv = agg_month.to_csv(index=False).encode('utf-8')

with col1:
    st.write(chart)
    with st.expander(':blue[Show Data]', expanded=False):
        agg_month_filtered = agg_month[agg_month['Month'].isin(month_order)]
        agg_month_filtered['Month'] = pd.Categorical(agg_month_filtered['Month'], categories=month_order, ordered=True)
        agg_month_sorted = agg_month_filtered.sort_values('Month').reset_index(drop=True)
        st.dataframe(agg_month_sorted[['Month', 'TimeTo_On_It_HH:MM:SS', 'TimeTo_Attended_HH:MM:SS']], use_container_width=True)
        csv = agg_month_sorted[['Month', 'TimeTo_On_It_HH:MM:SS', 'TimeTo_Attended_HH:MM:SS']].to_csv(index=False).encode('utf-8')
        st.download_button(':green[Download Data]', csv, file_name='monthly_response_times.csv', mime='text/csv', help="Click to download the Monthly Response Times in CSV format")

agg_service['TimeTo_On_It_Minutes'] = agg_service['TimeTo: On It Sec'] / 60
agg_service['TimeTo_Attended_Minutes'] = agg_service['TimeTo: Attended Sec'] / 60

agg_service_long = agg_service.melt(id_vars=['Service'], value_vars=['TimeTo_On_It_Minutes', 'TimeTo_Attended_Minutes'], var_name='Category', value_name='Minutes')

chart2 = alt.Chart(agg_service_long).mark_bar().encode(
    x='Service',
    y=alt.Y('Minutes', stack='zero'),  
    color='Category',  
    tooltip=['Service', 'Category', 'Minutes']  
).properties(
    title='Group Response Times',
    width=800,
    height=600
)

with col5:
    st.write(chart2)
    agg_service['TimeTo_On_It_HH:MM:SS'] = agg_service['TimeTo_On_It_Minutes'].apply(minutes_to_hms)
    agg_service['TimeTo_Attended_HH:MM:SS'] = agg_service['TimeTo_Attended_Minutes'].apply(minutes_to_hms)
    with st.expander(':blue[Show Data]', expanded=False):
        st.dataframe(agg_service[['Service', 'TimeTo_On_It_HH:MM:SS', 'TimeTo_Attended_HH:MM:SS']], use_container_width=True)
        csv = agg_service[['Service', 'TimeTo_On_It_HH:MM:SS', 'TimeTo_Attended_HH:MM:SS']].to_csv(index=False).encode('utf-8')
        st.download_button(':green[Download Data]', csv, file_name='group_response_times.csv', mime='text/csv', help="Click to download the Group Response Times in CSV format")

service_counts = df_filtered['Service'].value_counts().reset_index()
service_counts.columns = ['Service', 'Count']

chart3 = px.bar(service_counts, x='Service', y='Count', color='Service', text='Count', title='Interaction Count')
chart3.update_traces(textposition='outside')
chart3.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_tickangle=-0)
chart3.update_layout(width=800, height=600)

with col1:
    st.write(chart3)

chart4 = alt.Chart(df_filtered).mark_bar().encode(
    y=alt.Y('SME:N', sort='-x'),  # Sorting based on the count in descending order, ensure to specify ':N' for nominal data
    x=alt.X('count()', title='Unique Case Count'),
    tooltip=['SME', 'count()']
).properties(
    title='Interactions Handled by SME Attended',
    width=700,
    height=600
)

# Prepare data for table
data_chart4 = df_filtered['SME'].value_counts().reset_index()
data_chart4.index = data_chart4.index + 1
data_chart4.columns = ['SME', 'Unique Case Count']

# To display the chart in your Streamlit app
with col5:
    st.write(chart4)
    with st.expander("Show Data", expanded=False):
        st.dataframe(data_chart4, use_container_width=True)

st.subheader('Interaction Count by Requestor')

pivot_df = df_filtered.pivot_table(index='Requestor', columns='Service', aggfunc='size', fill_value=0)
pivot_df.reset_index(inplace=True)

gb = GridOptionsBuilder.from_dataframe(pivot_df)
gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=False)

gridOptions = gb.build()

AgGrid(pivot_df, gridOptions=gridOptions, update_mode=GridUpdateMode.MODEL_CHANGED, fit_columns_on_grid_load=True)

csv = pivot_df.to_csv(index=False).encode('utf-8')
st.download_button(':green[Download Data]', csv, file_name='interaction_count_by_requestor.csv', mime='text/csv', help="Download Interaction Count by Requestor Data in CSV format")

st.divider()

df_grouped = df_filtered.groupby('SME (On It)').agg(
    Avg_On_It_Sec=pd.NamedAgg(column='TimeTo: On It Sec', aggfunc='mean'),
    Avg_Attended_Sec=pd.NamedAgg(column='TimeTo: Attended Sec', aggfunc='mean'),
    Number_of_Interactions=pd.NamedAgg(column='SME (On It)', aggfunc='count'),
    Avg_Survey=pd.NamedAgg(column='Survey', aggfunc='mean')
).reset_index()

df_grouped['Total_Avg_Sec'] = df_grouped['Avg_On_It_Sec'] + df_grouped['Avg_Attended_Sec']
df_sorted = df_grouped.sort_values(by=['Total_Avg_Sec', 'Number_of_Interactions', 'Avg_Survey'], ascending=[True, False, False])
df_sorted['Avg_On_It'] = df_sorted['Avg_On_It_Sec'].apply(seconds_to_hms)
df_sorted['Avg_Attended'] = df_sorted['Avg_Attended_Sec'].apply(seconds_to_hms)
df_sorted.rename(columns={'SME (On It)': 'SME'}, inplace=True)

st.subheader('SME Summary Table')
st.dataframe(df_sorted[['SME', 'Avg_On_It', 'Avg_Attended', 'Number_of_Interactions', 'Avg_Survey']].reset_index(drop=True))

df_sorted['Avg_On_It_Min'] = df_sorted['Avg_On_It_Sec'] / 60
df_sorted['Avg_Attended_Min'] = df_sorted['Avg_Attended_Sec'] / 60

st.markdown(":arrow_up: 5 minutes = :red[red]")

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

chart_attended = alt.Chart(df_sorted).mark_bar().encode(
    x=alt.X('SME', title='SME', sort='-y'),
    y=alt.Y('Avg_Attended_Min:Q', title='Average Time Attended (Minutes)'),
    tooltip=['SME', alt.Tooltip('Avg_Attended_Min:Q', title='Average Time Attended (Minutes)')]
).properties(
    width=600,
    height=400,
    title='Average Time Attended by SME'
)

st.altair_chart(chart_on_it, use_container_width=True)
st.altair_chart(chart_attended, use_container_width=True)

refresh_rate = 120

def countdown_timer(duration):
    countdown_seconds = duration

    sidebar_html = st.sidebar.empty()
    sidebar_html.markdown("<p style='color:red;'>Time to refresh: 02:00</p>", unsafe_allow_html=True)

    while countdown_seconds:
        mins, secs = divmod(countdown_seconds, 60)
        timer_text = f"Time to refresh: {mins:02d}:{secs:02d}"
        sidebar_html.markdown(f"<p style='color:red;'>{timer_text}</p>", unsafe_allow_html=True)
        time.sleep(1)
        countdown_seconds -= 1

    sidebar_html.markdown("<p style='color:red;'>Refreshing...</p>", unsafe_allow_html=True)
    st.cache_data.clear()
    st.rerun()

while True:
    countdown_timer(refresh_rate)