import streamlit as st

st.set_page_config(
    page_title="FleetAudit.io - Fleet Fraud Detection",
    page_icon="🚛",
    layout="wide", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Obliterate sidebar */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
        width: 0 !important;
        visibility: hidden !important;
    }

    /* Remove left margin */
    .css-1d391kg {
        margin-left: 0 !important;
    }

    /* Remove Streamlit's auto padding */
    section.main > div:first-child {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

import pandas as pd
import json
from datetime import datetime, timedelta
import random

# Initialize navigation state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

def show_home_page():
    """Landing page content"""
    
    # Simple navbar using columns
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown("### 🚛 FleetAudit.io")
    
    with col2:
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        with nav_col1:
            if st.button("Features"):
                pass  # Could scroll to features section
        with nav_col2:
            if st.button("Demo"):
                pass  # Could scroll to demo section  
        with nav_col3:
            if st.button("Pricing"):
                pass  # Could scroll to pricing section
    
    with col3:
        if st.button("Try FleetAudit →", type="primary"):
            st.session_state.current_page = 'product'
            st.rerun()
    
    st.markdown("---")
    
    # Hero Section
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0f9ff 100%); border-radius: 1.5rem; margin: 2rem auto 4rem; max-width: 900px;">
        <h1 style="color: #111827; font-size: 3.75rem; font-weight: 800; margin-bottom: 1.5rem;">Stop Fleet Fraud Before It Costs You Thousands</h1>
        <h2 style="color: #4b5563; font-size: 1.375rem; font-weight: 400; margin-bottom: 2.5rem;">AI-powered fraud detection that analyzes your fuel, GPS, and job data to uncover theft, misuse, and policy violations in minutes.</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Try FleetAudit Free", type="primary", use_container_width=True):
            st.session_state.current_page = 'product'
            st.rerun()

def show_product_page():
    """Product page content"""
    
    # Simple navbar
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("### 🚛 FleetAudit.io")
    with col2:
        if st.button("← Back to Home"):
            st.session_state.current_page = 'home'
            st.rerun()
    
    st.markdown("---")
    
    # Upload sections
    st.markdown("## 📁 Data Upload")
    st.markdown("Upload your fleet data files to begin fraud detection analysis")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background-color:white; padding:20px; border-radius:12px; box-shadow:0 0 10px rgba(0,0,0,0.05); text-align:center;">
            <h4>⛽ Fuel Data Upload</h4>
        """, unsafe_allow_html=True)
        fuel_file = st.file_uploader("Upload Fuel CSV", type=["csv"], key="fuel", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background-color:white; padding:20px; border-radius:12px; box-shadow:0 0 10px rgba(0,0,0,0.05); text-align:center;">
            <h4>🗺️ GPS Data Upload</h4>
        """, unsafe_allow_html=True)
        gps_file = st.file_uploader("Upload GPS CSV", type=["csv"], key="gps", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background-color:white; padding:20px; border-radius:12px; box-shadow:0 0 10px rgba(0,0,0,0.05); text-align:center;">
            <h4>📋 Job Data Upload</h4>
        """, unsafe_allow_html=True)
        job_file = st.file_uploader("Upload Job CSV", type=["csv"], key="job", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Analysis button
    st.markdown("---")
    if st.button("🔍 Run Fraud Analysis", type="primary", use_container_width=True):
        if fuel_file:
            st.success("🎉 Analysis complete! Found 3 potential violations.")
            
            # Sample results
            st.markdown("### 🚨 Fraud Detection Results")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🚨 Violations Found", "3", delta="3 issues")
            with col2:
                st.metric("💰 Estimated Loss", "$425.00", delta="-$425.00")
            with col3:
                st.metric("⚠️ High Risk", "2", delta="2 critical")
            
            st.markdown("---")
            
            # Sample violation details
            with st.expander("**Excessive Volume** - Driver: John Smith (TRUCK-001)"):
                st.write("**Vehicle:** TRUCK-001")
                st.write("**Time:** 2024-01-15 14:30:00")
                st.write("**Location:** Shell Station - Highway 85")
                st.write("**Description:** Purchased 45 gallons - exceeds tank capacity (30 gallons)")
                st.write("**Severity:** HIGH")
                st.write("**Estimated Loss:** $225.00")
        else:
            st.error("Please upload fuel data to run analysis.")

# Main app logic
def main():
    if st.session_state.current_page == 'home':
        show_home_page()
    elif st.session_state.current_page == 'product':
        show_product_page()

if __name__ == "__main__":
    main()