import streamlit as st
import pandas as pd
from pygwalker.api.streamlit import StreamlitRenderer, init_streamlit_comm
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="srr anlaytics tool", page_icon= ":bar_chart:", layout="wide")

# Adjust the width of the Streamlit page

    # Main header
st.title("SRR Analytics Tool 📊")
st.write("---")


# Function to load data
# @st.cache_data(ttl=120, show_spinner=True)
# def load_data(url):
#     df = pd.read_csv(url)
#     df['Date Created'] = pd.to_datetime(df['Date Created'], errors='coerce')  # set 'Date Created' as datetime
#     df.rename(columns={'In process (On It SME)': 'SME (On It)'}, inplace=True)  # Renaming column
#     return df

@st.cache_data(ttl=120, show_spinner=True)
def load_data(data):
    df = data.copy()  # Make a copy to avoid modifying the original DataFrame
    df['Date Created'] = pd.to_datetime(df['Date Created'], errors='coerce')  
    df.rename(columns={'In process (On It SME)': 'SME (On It)'}, inplace=True)  
    df['TimeTo: On It (Raw)'] = df['TimeTo: On It'].copy()
    df['TimeTo: Attended (Raw)'] = df['TimeTo: Attended'].copy()
    df.dropna(subset=['Service'], inplace=True)
    return df

# url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSQVnfH-edbXqAXxlCb2FrhxxpsOHJhtqKMYsHWxf5SyLVpAPTSIWQeIGrBAGa16dE4CA59o2wyz59G/pub?gid=0&single=true&output=csv'
# dataframe = load_data(url).copy()

conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet="Response and Survey Form")
dataframe = load_data(data).copy()


def convert_to_seconds(time_str):
        if pd.isnull(time_str):
            return 0
        try:
            h, m, s = map(int, time_str.split(':'))
            return h * 3600 + m * 60 + s
        except ValueError:
            return 0

def convert_to_minutes(time_str):
    if pd.isnull(time_str):
        return 0
    try:
        h, m, s = map(int, time_str.split(':'))
        return (h * 3600 + m * 60 + s) // 60
    except ValueError:
        return 0


def seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


dataframe['TimeTo: On It Sec'] = dataframe['TimeTo: On It'].apply(convert_to_seconds)
dataframe['TimeTo: Attended Sec'] = dataframe['TimeTo: Attended'].apply(convert_to_seconds)

dataframe['TimeTo: On It Min'] = dataframe['TimeTo: On It'].apply(convert_to_minutes)
dataframe['TimeTo: Attended Min'] = dataframe['TimeTo: Attended'].apply(convert_to_minutes)



# Display PygWalker interface
renderer = StreamlitRenderer(dataframe, spec="./gw_config.json", spec_io_mode="rw")
renderer.explorer()

# Function to perform EDA
def perform_eda(dataframe):
    numerical_columns = dataframe.select_dtypes(include=np.number).columns
    correlation_matrix = dataframe[numerical_columns].corr()
    
    fig, ax = plt.subplots(figsize=(10, 10))
    sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    ax.set_title("Correlation Matrix")
    
    col1, buff = st.columns(2)
    with col1:
        st.pyplot(fig)
    st.markdown("***Dataset Shape:***")
    st.write(dataframe.shape)
    st.divider()
    st.markdown("***First 5 Rows:***")
    st.write(dataframe.head())
    st.markdown("***Last 5 Rows:***")
    st.write(dataframe.tail())
    st.divider()

    # Display columns and their data types
    column_types = pd.DataFrame(dataframe.dtypes, columns=["Data Type"])
    column_types.index.name = "Column"
    st.markdown("***Dataset Columns and Data Types:***")
    st.table(column_types)
    st.divider()

    # Display summary statistics
    st.markdown("***Summary Statistics***")
    st.write(dataframe.describe(include='all'))
    
    st.divider()
    unique_values = dataframe.nunique()
    unique_values_df = pd.DataFrame({"Columns": unique_values.index, "Count of Unique Values": unique_values.values})
    unique_values_df.index += 1
    st.markdown("***Unique Value Count***")
    st.table(unique_values_df)
    
    # Get columns with missing values
    null_columns = dataframe.columns[dataframe.isnull().any()].tolist()
    null_counts = dataframe.isnull().sum()

    if null_columns:
        st.divider()
        st.markdown("***Columns With Null Values:***")
        null_columns_df = pd.DataFrame({"Columns with Null": null_columns, "Number of Nulls": [null_counts[col] for col in null_columns]})
        null_columns_df = null_columns_df.reset_index(drop=True, inplace=False)
        null_columns_df.index += 1
        st.table(null_columns_df)
        
        # Selectbox for choosing column to view Nulls
        selected_column = st.selectbox("Select a column to view Nulls:", null_columns)
        
        # Display Nulls for the selected column
        null_rows = dataframe[dataframe[selected_column].isnull()]
        st.write(f"Rows with Nulls in '{selected_column}':")
        st.dataframe(null_rows)
    else:
        st.write("No missing values found in the dataset.")

    st.divider()

    # Identify columns with duplicates
    duplicates_info = {col: dataframe.duplicated(subset=[col]).sum() for col in dataframe.columns if dataframe.duplicated(subset=[col]).sum() > 0}
    
    if duplicates_info:
        st.write("Columns With Duplicates:")
        st.table(pd.DataFrame.from_dict(duplicates_info, orient='index', columns=['Count of Duplicates']))
        
        # Selection for detailed duplicate view
        column_to_view = st.selectbox("Select a column to view duplicates:", options=list(duplicates_info.keys()))
        
        # Display duplicates for the selected column
        duplicates = dataframe[dataframe.duplicated(subset=[column_to_view], keep=False)].sort_values(by=[column_to_view])
        st.write(f"Duplicates in '{column_to_view}':")
        st.dataframe(duplicates)
    else:
        st.write("No columns with duplicates found.")

# Display EDA
if dataframe is not None:
    perform_eda(dataframe)
else:
    st.header("Error Reading Data")
