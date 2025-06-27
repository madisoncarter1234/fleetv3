import streamlit as st

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.write("🧪 **Path Test - If you see this, the root path works!**")
st.write("Current file: `index.py` at repo root")
st.write("This proves Streamlit Cloud can read files from the root directory.")

if st.button("Test Navigation"):
    st.write("Navigation would work from here!")