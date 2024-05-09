from pygwalker.api.streamlit import StreamlitRenderer
import pandas as pd
import streamlit as st
 
# Adjust the width of the Streamlit page
st.set_page_config(
    page_title="SRR Anlaytics Tool",
    layout="wide"
)
 
# Add Title
st.title("SRR Anlaytics Tool")
 
# You should cache your pygwalker renderer, if you don't want your memory to explode
@st.cache_resource
def get_pyg_renderer() -> "StreamlitRenderer":
    df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vSQVnfH-edbXqAXxlCb2FrhxxpsOHJhtqKMYsHWxf5SyLVpAPTSIWQeIGrBAGa16dE4CA59o2wyz59G/pub?gid=0&single=true&output=csv')
    # If you want to use feature of saving chart config, set `spec_io_mode="rw"`
    return StreamlitRenderer(df, spec="./gw_config.json")
 
 
renderer = get_pyg_renderer()
 
st.subheader("Display Explore UI")
 
tab1, tab2, tab3, tab4 = st.tabs(
    ["graphic walker", "data profiling", "graphic renderer", "pure chart"]
)
 
with tab1:
    renderer.explorer()
 
with tab2:
    renderer.explorer(default_tab="data")
 
with tab3:
    renderer.render_filter_renderer()
 
with tab4:
    st.markdown("### registered per weekday")
    renderer.chart(0)
    st.markdown("### registered per day")
    renderer.chart(1)