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

    /* Remove Streamlit's auto padding and move content up */
    section.main > div:first-child {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 0 !important;
        margin-top: -48px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Science.io-inspired CSS styling - FULL VERSION FROM YOUR ORIGINAL
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .main {
        background: #ffffff !important;
        padding: 0;
        max-width: none;
    }
    
    /* Force white background everywhere */
    .stApp, [data-testid="stAppViewContainer"], .main, body {
        background: #ffffff !important;
        background-color: #ffffff !important;
    }
    
    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
    
    /* Section padding for scroll offset */
    .scroll-section {
        scroll-margin-top: 80px;
        padding-top: 2rem;
    }
    
    /* Content container */
    .content-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 2rem;
    }
    
    /* Hero section - Enhanced design with reduced top margin */
    .hero-section {
        text-align: center;
        padding: 6rem 3rem;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0f9ff 100%);
        border-radius: 1.5rem;
        margin: 0.5rem auto 4rem;
        max-width: 900px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(37, 99, 235, 0.08);
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(37, 99, 235, 0.03) 0%, transparent 70%);
        animation: pulse 15s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(0.8); opacity: 0.5; }
        50% { transform: scale(1.2); opacity: 0.8; }
    }
    
    .hero-section h1 {
        color: #111827 !important;
        font-size: 3.75rem !important;
        font-weight: 800 !important;
        margin-bottom: 1.5rem !important;
        line-height: 1.1 !important;
        letter-spacing: -0.02em;
        position: relative;
        z-index: 1;
    }
    
    .hero-section h2 {
        color: #4b5563 !important;
        font-size: 1.375rem !important;
        font-weight: 400 !important;
        margin-bottom: 2.5rem !important;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6 !important;
        position: relative;
        z-index: 1;
    }
    
    /* Feature cards - Clean minimal style */
    .features-section {
        margin-bottom: 5rem;
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin-top: 2rem;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .feature-card:hover {
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .feature-card h3 {
        color: #111827 !important;
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
    }
    
    .feature-card p {
        color: #6b7280 !important;
        line-height: 1.6 !important;
    }
    
    /* Demo section */
    .demo-section {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 1rem;
        padding: 3rem;
        margin: 3rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .demo-header h2 {
        color: #111827 !important;
        font-size: 2rem !important;
        font-weight: 600 !important;
        text-align: center;
        margin-bottom: 1rem !important;
    }
    
    /* Pricing */
    .pricing-section {
        text-align: center;
        margin: 4rem 0;
    }
    
    .pricing-card {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 1rem;
        padding: 2rem;
        max-width: 400px;
        margin: 0 auto;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .price {
        font-size: 3rem;
        font-weight: 700;
        color: #111827;
        margin: 1rem 0;
    }
    
    /* Section headings */
    .section-heading {
        color: #111827 !important;
        font-size: 2.25rem !important;
        font-weight: 600 !important;
        text-align: center;
        margin-bottom: 3rem !important;
    }
    
    /* Hide Streamlit elements */
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    .stMainBlockContainer {padding-top: 0;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Button styling */
    .stButton > button {
        background: #2563eb !important;
        color: white !important;
        border: none !important;
        border-radius: 0.5rem !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        position: static !important;
    }
    
    .stButton > button:hover {
        background: #1d4ed8 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    
    /* Force all buttons to stay in normal flow */
    .stButton {
        position: static !important;
    }
    
    /* NUCLEAR OPTION: Force ALL metric text to be dark everywhere */
    div[data-testid="metric-container"] {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    div[data-testid="metric-container"] * {
        color: #000000 !important;
        font-weight: bold !important;
    }
    div[data-testid="metric-container"] div {
        color: #000000 !important;
    }
    div[data-testid="metric-container"] label {
        color: #000000 !important;
    }
    div[data-testid="metric-container"] [data-testid="metric-value"] {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    div[data-testid="metric-container"] [data-testid="metric-delta"] {
        color: #dc2626 !important;
        font-weight: 700 !important;
    }
    /* Override Streamlit's default styles */
    .css-1xarl3l, .css-1wivap2, .css-2trqyj {
        color: #000000 !important;
    }
    
    /* GLOBAL FIX: Force ALL expander text to be dark */
    .streamlit-expanderHeader {
        background: #ffffff !important;
        color: #000000 !important;
        font-weight: 600 !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 0.5rem !important;
    }
    .streamlit-expanderHeader * {
        color: #000000 !important;
    }
    .streamlit-expanderContent {
        background: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #e5e7eb !important;
        border-top: none !important;
    }
    .streamlit-expanderContent p {
        color: #000000 !important;
    }
    .streamlit-expanderContent * {
        color: #000000 !important;
    }
    
    /* Fix selectbox to NOT be dark */
    div[data-baseweb="select"] {
        background: #ffffff !important;
    }
    div[data-baseweb="select"] * {
        color: #374151 !important;
        background: #ffffff !important;
    }
    
    /* Fix success message text to be dark */
    .stSuccess {
        color: #000000 !important;
    }
    .stSuccess * {
        color: #000000 !important;
    }
    div[data-testid="stSuccess"] {
        color: #000000 !important;
    }
    div[data-testid="stSuccess"] * {
        color: #000000 !important;
    }
    
    /* Fix file uploader text to be dark and background white */
    .stFileUploader {
        color: #000000 !important;
    }
    .stFileUploader * {
        color: #000000 !important;
    }
    .stFileUploader label {
        color: #000000 !important;
    }
    .stFileUploader div {
        color: #000000 !important;
        background: #ffffff !important;
    }
    .stFileUploader small {
        color: #000000 !important;
    }
    .stFileUploader span {
        color: #000000 !important;
    }
    
    /* File uploader drag and drop area styling */
    .stFileUploader > div > div {
        background: #ffffff !important;
        border: 2px dashed #d1d5db !important;
        border-radius: 0.75rem !important;
        padding: 1.5rem !important;
    }
    
    .stFileUploader > div > div:hover {
        background: #ffffff !important;
        border-color: #2563eb !important;
    }
    
    /* Browse Files button styling */
    .stFileUploader button {
        background: #ffffff !important;
        color: #374151 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 0.375rem !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
    }
    
    .stFileUploader button:hover {
        background: #f9fafb !important;
        border-color: #9ca3af !important;
    }
    
    /* File uploader text area */
    .stFileUploader [data-testid="stFileUploaderDropzone"] {
        background: #ffffff !important;
        color: #000000 !important;
    }
    
    .stFileUploader [data-testid="stFileUploaderDropzone"] * {
        background: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Fix ALL text elements to be dark */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: #000000 !important;
    }
    .main p {
        color: #000000 !important;
    }
    .main div {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

import pandas as pd
import json
from datetime import datetime, timedelta
import random
import numpy as np
import statistics
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import tempfile
import os

# Initialize navigation state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

def get_demo_data():
    """Generate realistic demo data for the fleet audit"""
    
    # Sample scenarios from your original
    scenarios = {
        "ABC Logistics": {
            "description": "12-vehicle delivery fleet with multiple policy violations",
            "vehicles": 12,
            "violations": [
                {
                    "type": "shared_card_use",
                    "card_last_4": "4455",
                    "vehicles_involved": ["VAN-003", "TRUCK-007"],
                    "drivers_involved": ["Mike Chen", "Sarah Wilson"],
                    "time_span_minutes": 25,
                    "description": "Same fuel card (****4455) used by different drivers within 25 minutes",
                    "severity": "high",
                    "estimated_loss": 187.50
                },
                {
                    "type": "after_hours",
                    "vehicle_id": "VAN-005",
                    "driver_name": "Carlos Rodriguez", 
                    "timestamp": "2024-08-15 02:47:00",
                    "location": "Shell Station - Interstate 85",
                    "card_last_4": "4455",
                    "description": "Fuel purchase at 2:47 AM on weekend outside business hours",
                    "severity": "high",
                    "estimated_loss": 89.25
                },
                {
                    "type": "excessive_amount",
                    "vehicle_id": "TRUCK-003",
                    "driver_name": "David Kim",
                    "timestamp": "2024-08-12 14:22:00", 
                    "location": "BP Station - Highway 75",
                    "card_last_4": "7891",
                    "description": "Purchased 67 gallons (normal capacity: 35 gallons)",
                    "severity": "medium",
                    "estimated_loss": 125.00
                }
            ],
            "summary": {
                "total_violations": 3,
                "total_estimated_loss": 401.75,
                "high_risk_vehicles": ["VAN-003", "VAN-005", "TRUCK-003"]
            }
        },
        "Metro Delivery": {
            "description": "6-vehicle urban delivery service with multiple fraud patterns",
            "vehicles": 6,
            "violations": [
                {
                    "type": "rapid_purchases",
                    "vehicle_id": "VAN-002",
                    "driver_name": "Lisa Johnson",
                    "timestamp": "2024-08-10 16:45:00",
                    "location": "Exxon Station - Downtown",
                    "card_last_4": "3344", 
                    "description": "Two fuel purchases within 45 minutes at different locations",
                    "severity": "medium",
                    "estimated_loss": 95.50
                },
                {
                    "type": "personal_use",
                    "vehicle_id": "TRUCK-001", 
                    "driver_name": "James Wilson",
                    "timestamp": "2024-08-11 19:30:00",
                    "location": "Shell Station - Residential Area",
                    "card_last_4": "2233",
                    "description": "Weekend fuel purchase in residential area during off-hours",
                    "severity": "high",
                    "estimated_loss": 167.25
                },
                {
                    "type": "excessive_amount",
                    "vehicle_id": "VAN-004",
                    "driver_name": "Maria Garcia",
                    "timestamp": "2024-08-09 15:20:00",
                    "location": "Chevron Station - Highway 20",
                    "card_last_4": "5577",
                    "description": "Purchased 42 gallons in van with 25-gallon capacity",
                    "severity": "high",
                    "estimated_loss": 245.80
                },
                {
                    "type": "shared_card_use",
                    "card_last_4": "3344",
                    "vehicles_involved": ["VAN-002", "VAN-005"],
                    "drivers_involved": ["Lisa Johnson", "Robert Chen"],
                    "time_span_minutes": 38,
                    "description": "Same fuel card (****3344) used by different drivers within 38 minutes",
                    "severity": "high",
                    "estimated_loss": 189.75
                }
            ],
            "summary": {
                "total_violations": 4,
                "total_estimated_loss": 698.30,
                "high_risk_vehicles": ["VAN-002", "TRUCK-001", "VAN-004", "VAN-005"]
            }
        },
        "TransLogic Corp": {
            "description": "15-vehicle commercial fleet with systematic fraud issues",
            "vehicles": 15,
            "violations": [
                {
                    "type": "ghost_job",
                    "job_id": "TL-2024-0820",
                    "driver_name": "Anthony Martinez",
                    "vehicle_id": "TRUCK-009",
                    "scheduled_time": "2024-08-20 09:00:00",
                    "address": "Industrial District, Zone 5",
                    "description": "Scheduled 4-hour job with fuel purchases but no GPS activity at location",
                    "severity": "high", 
                    "estimated_loss": 320.00
                },
                {
                    "type": "after_hours",
                    "vehicle_id": "VAN-012",
                    "driver_name": "Sandra Kim",
                    "timestamp": "2024-08-18 23:45:00",
                    "location": "Marathon Station - Route 45",
                    "card_last_4": "8899",
                    "description": "Fuel purchase at 11:45 PM on Sunday, well outside business hours",
                    "severity": "high",
                    "estimated_loss": 128.75
                },
                {
                    "type": "shared_card_use",
                    "card_last_4": "6677",
                    "vehicles_involved": ["TRUCK-003", "TRUCK-011", "VAN-007"],
                    "drivers_involved": ["Kevin Brown", "Rachel Davis", "Tom Wilson"],
                    "time_span_minutes": 52,
                    "description": "Same fuel card (****6677) used by three different drivers within 52 minutes",
                    "severity": "high",
                    "estimated_loss": 485.20
                },
                {
                    "type": "excessive_amount",
                    "vehicle_id": "TRUCK-014",
                    "driver_name": "Daniel Rodriguez",
                    "timestamp": "2024-08-17 11:30:00",
                    "location": "Shell Station - Interstate 75",
                    "card_last_4": "4422",
                    "description": "Purchased 78 gallons in truck with 50-gallon capacity",
                    "severity": "high",
                    "estimated_loss": 195.50
                },
                {
                    "type": "personal_use",
                    "vehicle_id": "VAN-008",
                    "driver_name": "Jennifer Adams",
                    "timestamp": "2024-08-16 14:20:00",
                    "location": "Chevron Station - Suburban Mall",
                    "card_last_4": "5566",
                    "description": "Fuel purchase at shopping center during lunch break, 12 miles from assigned route",
                    "severity": "medium",
                    "estimated_loss": 89.30
                }
            ],
            "summary": {
                "total_violations": 5,
                "total_estimated_loss": 1218.75,
                "high_risk_vehicles": ["TRUCK-009", "VAN-012", "TRUCK-003", "TRUCK-011", "VAN-007", "TRUCK-014"]
            }
        }
    }
    
    return scenarios

def display_demo_results(scenario_name, scenario_data):
    """Display demo results that look like real fraud detection output"""
    
    violations = scenario_data["violations"]
    summary = scenario_data["summary"]
    
    # Summary metrics - CUSTOM HTML TO FORCE VISIBILITY
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1rem; text-align: center;">
            <div style="color: #000000; font-size: 0.875rem; font-weight: 500;">🚨 Violations Found</div>
            <div style="color: #000000; font-size: 2rem; font-weight: 700;">{len(violations)}</div>
            <div style="color: #dc2626; font-size: 0.875rem;">{len(violations)} issues</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        total_loss = summary.get('total_estimated_loss', 0)
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1rem; text-align: center;">
            <div style="color: #000000; font-size: 0.875rem; font-weight: 500;">💰 Estimated Loss</div>
            <div style="color: #000000; font-size: 2rem; font-weight: 700;">${total_loss:.2f}</div>
            <div style="color: #dc2626; font-size: 0.875rem;">-${total_loss:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        high_risk = len([v for v in violations if v.get('severity') == 'high'])
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1rem; text-align: center;">
            <div style="color: #000000; font-size: 0.875rem; font-weight: 500;">⚠️ High Risk</div>
            <div style="color: #000000; font-size: 2rem; font-weight: 700;">{high_risk}</div>
            <div style="color: #dc2626; font-size: 0.875rem;">{high_risk} critical</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display violations
    
    for violation in violations:
        if violation.get('type') == 'shared_card_use':
            card_info = f"Card ****{violation.get('card_last_4', 'Unknown')}"
            vehicles = ', '.join(violation.get('vehicles_involved', []))
            
            # Create custom expander with HTML
            st.markdown(f"""
            <details style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 0.5rem; margin: 0.5rem 0;">
                <summary style="background: #ffffff; color: #000000; font-weight: 600; padding: 1rem; cursor: pointer; border-radius: 0.5rem;">
                    <strong>Shared Card Use</strong> - {card_info} ({vehicles})
                </summary>
                <div style="padding: 1rem; color: #000000; background: #ffffff;">
                    <p style="color: #000000;"><strong>Card Last 4:</strong> ****{violation.get('card_last_4', 'Unknown')}</p>
                    <p style="color: #000000;"><strong>Vehicles Involved:</strong> {', '.join(violation.get('vehicles_involved', []))}</p>
                    <p style="color: #000000;"><strong>Drivers Involved:</strong> {', '.join(violation.get('drivers_involved', []))}</p>
                    <p style="color: #000000;"><strong>Time Span:</strong> {violation.get('time_span_minutes', 'Unknown')} minutes</p>
                    <p style="color: #000000;"><strong>Description:</strong> {violation.get('description', 'No description')}</p>
                    <p style="color: #000000;"><strong>Severity:</strong> {violation.get('severity', 'Unknown').upper()}</p>
                    <p style="color: #000000;"><strong>Estimated Loss:</strong> ${violation.get('estimated_loss', 0):.2f}</p>
                </div>
            </details>
            """, unsafe_allow_html=True)
        else:
            # Handle regular violations
            driver_info = f"{violation.get('driver_name', 'Unknown Driver')} ({violation.get('vehicle_id', 'Unknown Vehicle')})"
            violation_title = violation.get('type', 'Unknown').replace('_', ' ').title()
            
            # Create custom expander with HTML
            st.markdown(f"""
            <details style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 0.5rem; margin: 0.5rem 0;">
                <summary style="background: #ffffff; color: #000000; font-weight: 600; padding: 1rem; cursor: pointer; border-radius: 0.5rem;">
                    <strong>{violation_title}</strong> - {driver_info}
                </summary>
                <div style="padding: 1rem; color: #000000; background: #ffffff;">
                    <p style="color: #000000;"><strong>Driver:</strong> {violation.get('driver_name', 'Unknown')}</p>
                    <p style="color: #000000;"><strong>Vehicle:</strong> {violation.get('vehicle_id', 'Unknown')}</p>
                    <p style="color: #000000;"><strong>Time:</strong> {violation.get('timestamp', 'Unknown')}</p>
                    <p style="color: #000000;"><strong>Location:</strong> {violation.get('location', 'Unknown')}</p>
                    {f"<p style='color: #000000;'><strong>Card Used:</strong> ****{violation['card_last_4']}</p>" if violation.get('card_last_4') else ""}
                    <p style="color: #000000;"><strong>Description:</strong> {violation.get('description', 'No description')}</p>
                    <p style="color: #000000;"><strong>Severity:</strong> {violation.get('severity', 'Unknown').upper()}</p>
                    <p style="color: #000000;"><strong>Estimated Loss:</strong> ${violation.get('estimated_loss', 0):.2f}</p>
                </div>
            </details>
            """, unsafe_allow_html=True)

def show_home_page():
    """Landing page content - COMPLETE VERSION"""
    
    # Professional Navbar with better styling and reduced spacing
    st.markdown("""
    <div style="background: white; padding: 0.75rem 2rem; border-bottom: 1px solid #e5e7eb; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; max-width: 1200px; margin: 0 auto;">
            <div style="font-size: 1.5rem; font-weight: 700; color: #111827;">
                🚚 FleetAudit
            </div>
            <div style="display: flex; align-items: center; gap: 2rem;">
                <a href="#features" onclick="smoothScrollTo('features')" style="color: #6b7280; text-decoration: none; font-weight: 500; transition: color 0.3s;">Features</a>
                <a href="#demo" onclick="smoothScrollTo('demo')" style="color: #6b7280; text-decoration: none; font-weight: 500; transition: color 0.3s;">Demo</a>
                <a href="#pricing" onclick="smoothScrollTo('pricing')" style="color: #6b7280; text-decoration: none; font-weight: 500; transition: color 0.3s;">Pricing</a>
                <button onclick="switchToProduct()" style="background: #2563eb; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease;">Try FleetAudit</button>
            </div>
        </div>
    </div>
    
    <script>
        function smoothScrollTo(elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
        
        function switchToProduct() {
            // Use Streamlit's built-in rerun functionality
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'switch_to_product'}, '*');
        }
        
        // Style hover effects
        document.querySelectorAll('a[href^="#"]').forEach(link => {
            link.addEventListener('mouseenter', function() {
                this.style.color = '#2563eb';
            });
            link.addEventListener('mouseleave', function() {
                this.style.color = '#6b7280';
            });
        });
        
        document.querySelector('button').addEventListener('mouseenter', function() {
            this.style.background = '#1d4ed8';
            this.style.transform = 'translateY(-1px)';
        });
        document.querySelector('button').addEventListener('mouseleave', function() {
            this.style.background = '#2563eb';
            this.style.transform = 'translateY(0)';
        });
    </script>
    """, unsafe_allow_html=True)
    
    
    # Hero Section - Science.io style
    st.markdown("""
    <div class="content-container">
        <div class="hero-section">
            <h1>Stop Fleet Fraud Before It Costs You Thousands</h1>
            <h2>AI-powered fraud detection that analyzes your fuel, GPS, and job data to uncover theft, misuse, and policy violations in minutes.</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Button with navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Try FleetAudit Free", type="primary", use_container_width=True, key="hero_cta"):
            st.session_state.current_page = 'product'
            st.rerun()
    
    # Features Section with Science.io styling
    st.markdown("""
    <div class="content-container">
        <div class="features-section scroll-section" id="features">
            <h2 class="section-heading">Why FleetAudit.io?</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <h3>🔍 AI-Powered Detection</h3>
                    <p>Advanced algorithms detect fraud patterns humans miss - shared cards, ghost jobs, after-hours abuse, and more.</p>
                </div>
                <div class="feature-card">
                    <h3>💰 Immediate ROI</h3>
                    <p>Customers typically recover 10x their subscription cost in the first month by stopping ongoing fraud.</p>
                </div>
                <div class="feature-card">
                    <h3>📊 Professional Reports</h3>
                    <p>Generate detailed PDF reports with evidence for HR, management, and legal proceedings.</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo Section with new styling
    st.markdown("""
    <div class="content-container">
        <div class="demo-section scroll-section" id="demo">
            <div class="demo-header">
                <h2>🎯 See FleetAudit.io in Action</h2>
                <p style="color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem; text-align: center;">Select a sample fleet below to see how our AI detects fraud and policy violations:</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo selector - YOUR EXACT VERSION
    demo_data = get_demo_data()
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        scenario_names = list(demo_data.keys())
        selected_scenario = st.selectbox(
            "Choose Sample Fleet:",
            scenario_names,
            help="Select different fleet examples to see various types of fraud detection"
        )
        
        scenario_info = demo_data[selected_scenario]
        st.markdown(f"""
        <div style="background: #dbeafe; border: 1px solid #93c5fd; border-radius: 0.5rem; padding: 1rem; color: #1e40af;">
            <strong>{selected_scenario}</strong><br><br>
            {scenario_info['description']}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔍 Run Fraud Analysis", type="primary", use_container_width=True):
            st.session_state.show_demo = True
            st.session_state.demo_scenario = selected_scenario
    
    with col2:
        if st.session_state.get('show_demo', False):
            demo_scenario = st.session_state.get('demo_scenario', selected_scenario)
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #e5e7eb;">
                <h3 style="color: #111827; margin-bottom: 1rem;">🚨 Fraud Detection Results: {demo_scenario}</h3>
            </div>
            """, unsafe_allow_html=True)
            display_demo_results(demo_scenario, demo_data[demo_scenario])
    
    # Pricing Section with Science.io styling
    st.markdown("""
    <div class="content-container">
        <div class="pricing-section scroll-section" id="pricing">
            <h2 class="section-heading">💳 Simple, Transparent Pricing</h2>
            <div class="pricing-card">
                <h3 style="color: #111827; font-size: 1.5rem; margin-bottom: 1rem;">Professional Plan</h3>
                <div class="price">$99<span style="font-size: 1rem; color: #6b7280; font-weight: 400;">/month</span></div>
                <div style="text-align: left; color: #374151; line-height: 1.8;">
                    ✅ Unlimited fleet data analysis<br>
                    ✅ All fraud detection features<br>
                    ✅ PDF report generation<br>
                    ✅ Email alerts & notifications<br>
                    ✅ Priority support
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Start trial button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Start Free Trial", type="primary", use_container_width=True):
            st.balloons()
            st.markdown("""
            <div style="background: #dcfce7; border: 1px solid #16a34a; border-radius: 0.5rem; padding: 1rem; color: #000000; margin: 1rem 0;">
                🎉 Ready to start your free trial! Subscription system coming soon.
            </div>
            """, unsafe_allow_html=True)
    
    # Call to Action with Science.io styling
    st.markdown("""
    <div class="content-container">
        <div style="text-align: center; padding: 4rem 2rem; background: #f9fafb; border-radius: 1rem; margin: 3rem 0;">
            <h2 style="color: #111827; font-size: 2rem; font-weight: 600; margin-bottom: 1rem;">Ready to Stop Fleet Fraud?</h2>
            <p style="color: #6b7280; font-size: 1.2rem; margin-bottom: 0;">Join hundreds of fleet managers who've recovered thousands in stolen fuel and time.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    

def show_product_page():
    """Product page content"""
    
    # Simple navbar with dark text
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<h3 style='color: #000000;'>🚛 FleetAudit.io</h3>", unsafe_allow_html=True)
    with col2:
        if st.button("← Back to Home"):
            st.session_state.current_page = 'home'
            st.rerun()
    
    st.markdown("---")
    
    # Upload sections with dark text
    st.markdown("<h2 style='color: #000000;'>📁 Data Upload</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #000000;'>Upload your fleet data files to begin fraud detection analysis</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background-color:white; padding:20px; border-radius:12px; box-shadow:0 0 10px rgba(0,0,0,0.05); text-align:center;">
            <h4 style="color: #000000;">⛽ Fuel Data Upload</h4>
        """, unsafe_allow_html=True)
        fuel_file = st.file_uploader("Upload Fuel CSV", type=["csv"], key="fuel", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background-color:white; padding:20px; border-radius:12px; box-shadow:0 0 10px rgba(0,0,0,0.05); text-align:center;">
            <h4 style="color: #000000;">🗺️ GPS Data Upload</h4>
        """, unsafe_allow_html=True)
        gps_file = st.file_uploader("Upload GPS CSV", type=["csv"], key="gps", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background-color:white; padding:20px; border-radius:12px; box-shadow:0 0 10px rgba(0,0,0,0.05); text-align:center;">
            <h4 style="color: #000000;">📋 Job Data Upload</h4>
        """, unsafe_allow_html=True)
        job_file = st.file_uploader("Upload Job CSV", type=["csv"], key="job", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Analysis button
    st.markdown("---")
    if st.button("🔍 Run Fraud Analysis", type="primary", use_container_width=True):
        if fuel_file:
            with st.spinner("Analyzing data for fraud with Claude AI..."):
                try:
                    # Initialize Claude with your API key
                    from anthropic import Anthropic
                    client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                    
                    # Read uploaded file
                    fuel_df = pd.read_csv(fuel_file)
                    
                    # Basic column standardization
                    column_mapping = {
                        'Transaction Date': 'date',
                        'Date': 'date',
                        'Transaction Time': 'time', 
                        'Time': 'time',
                        'Site Name': 'location',
                        'Merchant Name': 'location',
                        'Location': 'location',
                        'Gallons': 'gallons',
                        'Fuel Quantity': 'gallons',
                        'Vehicle Number': 'vehicle_id',
                        'Vehicle': 'vehicle_id',
                        'Amount': 'amount',
                        'Total Cost': 'amount',
                        'Driver Name': 'driver_name',
                        'Card Number': 'card_number',
                        'Card': 'card_number',
                        'Fuel Card': 'card_number',
                        'Card Last 4': 'card_last_4',
                        'Last 4': 'card_last_4',
                        'card_last4': 'card_last_4'
                    }
                    
                    # Rename columns
                    for old_col, new_col in column_mapping.items():
                        if old_col in fuel_df.columns:
                            fuel_df = fuel_df.rename(columns={old_col: new_col})
                    
                    # Create timestamp from date + time if separate
                    if 'date' in fuel_df.columns and 'time' in fuel_df.columns:
                        fuel_df['timestamp'] = pd.to_datetime(
                            fuel_df['date'].astype(str) + ' ' + fuel_df['time'].astype(str), 
                            errors='coerce'
                        )
                    elif 'date' in fuel_df.columns:
                        fuel_df['timestamp'] = pd.to_datetime(fuel_df['date'], errors='coerce')
                    
                    # Extract last 4 digits from card number if we have full card number
                    if 'card_number' in fuel_df.columns and 'card_last_4' not in fuel_df.columns:
                        fuel_df['card_last_4'] = fuel_df['card_number'].astype(str).str[-4:]
                    
                    # Prepare data for analysis
                    fuel_csv = fuel_df.to_csv(index=False)
                    
                    # Add GPS and Job data if available
                    analysis_data = f"FUEL DATA:\n{fuel_csv}\n"
                    
                    if gps_file is not None:
                        gps_df = pd.read_csv(gps_file)
                        gps_csv = gps_df.to_csv(index=False)
                        analysis_data += f"\nGPS DATA:\n{gps_csv}\n"
                    
                    if job_file is not None:
                        job_df = pd.read_csv(job_file)
                        job_csv = job_df.to_csv(index=False)
                        analysis_data += f"\nJOB DATA:\n{job_csv}\n"
                    
                    # Simple, direct prompt
                    prompt = f"""Analyze this fleet data for fraud and theft. Return JSON only.

{analysis_data}

Find these fraud types:
- After-hours fuel purchases (outside 7AM-6PM)
- Ghost jobs (jobs scheduled but no GPS/fuel activity at location)
- Fuel without GPS at location  
- Excessive fuel amounts (>25 gallons for vans, >50 for trucks)
- Rapid consecutive purchases (multiple fills within 2 hours)
- Personal use patterns (weekend/holiday activity)
- Jobs with no vehicle presence (cross-check GPS and fuel data)
- SHARED CARD USE: Same card number (last 4 digits) used by different drivers/vehicles within 60 minutes

CRITICAL SHARED CARD DETECTION:
1. Look for identical card numbers or last 4 digits used across different vehicles within 60 minutes
2. Flag even same-vehicle multiple uses within 60 minutes as suspicious
3. Include ALL transactions in the shared_card_use violation with exact timestamps
4. Calculate time_span_minutes between first and last use

IMPORTANT: For ALL fuel-related violations, include the "card_last_4" field with the last 4 digits of the fuel card used.

Return JSON:
{{
  "violations": [
    {{
      "type": "after_hours",
      "vehicle_id": "VAN-004", 
      "driver_name": "Diana",
      "timestamp": "2024-06-16 02:00:00",
      "location": "Shell Station",
      "card_last_4": "5678",
      "description": "Fuel purchase at 2 AM outside business hours",
      "severity": "high",
      "estimated_loss": 75.50
    }},
    {{
      "type": "shared_card_use",
      "card_last_4": "1234",
      "vehicles_involved": ["VAN-001", "TRUCK-002"],
      "drivers_involved": ["John Smith", "Mike Jones"],
      "transactions": [
        {{"timestamp": "2024-06-16 14:15:00", "vehicle_id": "VAN-001", "driver_name": "John Smith", "location": "BP Station"}},
        {{"timestamp": "2024-06-16 14:45:00", "vehicle_id": "TRUCK-002", "driver_name": "Mike Jones", "location": "Shell Station"}}
      ],
      "time_span_minutes": 30,
      "description": "Same fuel card (****1234) used by different drivers within 30 minutes",
      "severity": "high",
      "estimated_loss": 150.00
    }}
  ],
  "summary": {{
    "total_violations": 5,
    "total_estimated_loss": 500.00,
    "high_risk_vehicles": ["TRUCK001", "VAN002"]
  }}
}}"""
                    
                    # Call Claude Haiku with correct token limit
                    response = client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=4000,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    # Parse response
                    result_text = response.content[0].text.strip()
                    
                    # Extract JSON more carefully
                    import json
                    
                    if '{' in result_text:
                        json_start = result_text.find('{')
                        # Find the end of the JSON by counting braces
                        brace_count = 0
                        json_end = json_start
                        
                        for i, char in enumerate(result_text[json_start:], json_start):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break
                        
                        json_text = result_text[json_start:json_end]
                        fraud_results = json.loads(json_text)
                        
                        # Display results
                        violations = fraud_results.get('violations', [])
                        summary = fraud_results.get('summary', {})
                        
                        if violations:
                            st.markdown("""
                            <div style="background: #dcfce7; border: 1px solid #16a34a; border-radius: 0.5rem; padding: 1rem; color: #000000; margin: 1rem 0;">
                                🎉 Analysis complete! Found {} potential violations.
                            </div>
                            """.format(len(violations)), unsafe_allow_html=True)
                            
                            # Display results using the same format as landing page
                            st.markdown("<h3 style='color: #000000;'>🚨 Fraud Detection Results</h3>", unsafe_allow_html=True)
                            
                            # Summary metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown(f"""
                                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1rem; text-align: center;">
                                    <div style="color: #000000; font-size: 0.875rem; font-weight: 500;">🚨 Violations Found</div>
                                    <div style="color: #000000; font-size: 2rem; font-weight: 700;">{len(violations)}</div>
                                    <div style="color: #dc2626; font-size: 0.875rem;">{len(violations)} issues</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with col2:
                                total_loss = summary.get('total_estimated_loss', 0)
                                st.markdown(f"""
                                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1rem; text-align: center;">
                                    <div style="color: #000000; font-size: 0.875rem; font-weight: 500;">💰 Estimated Loss</div>
                                    <div style="color: #000000; font-size: 2rem; font-weight: 700;">${total_loss:.2f}</div>
                                    <div style="color: #dc2626; font-size: 0.875rem;">-${total_loss:.2f}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with col3:
                                high_risk = len([v for v in violations if v.get('severity') == 'high'])
                                st.markdown(f"""
                                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1rem; text-align: center;">
                                    <div style="color: #000000; font-size: 0.875rem; font-weight: 500;">⚠️ High Risk</div>
                                    <div style="color: #000000; font-size: 2rem; font-weight: 700;">{high_risk}</div>
                                    <div style="color: #dc2626; font-size: 0.875rem;">{high_risk} critical</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            # Display violations using same format as landing page
                            for violation in violations:
                                if violation.get('type') == 'shared_card_use':
                                    card_info = f"Card ****{violation.get('card_last_4', 'Unknown')}"
                                    vehicles = ', '.join(violation.get('vehicles_involved', []))
                                    
                                    st.markdown(f"""
                                    <details style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 0.5rem; margin: 0.5rem 0;">
                                        <summary style="background: #ffffff; color: #000000; font-weight: 600; padding: 1rem; cursor: pointer; border-radius: 0.5rem;">
                                            <strong>Shared Card Use</strong> - {card_info} ({vehicles})
                                        </summary>
                                        <div style="padding: 1rem; color: #000000; background: #ffffff;">
                                            <p style="color: #000000;"><strong>Card Last 4:</strong> ****{violation.get('card_last_4', 'Unknown')}</p>
                                            <p style="color: #000000;"><strong>Vehicles Involved:</strong> {', '.join(violation.get('vehicles_involved', []))}</p>
                                            <p style="color: #000000;"><strong>Drivers Involved:</strong> {', '.join(violation.get('drivers_involved', []))}</p>
                                            <p style="color: #000000;"><strong>Time Span:</strong> {violation.get('time_span_minutes', 'Unknown')} minutes</p>
                                            <p style="color: #000000;"><strong>Description:</strong> {violation.get('description', 'No description')}</p>
                                            <p style="color: #000000;"><strong>Severity:</strong> {violation.get('severity', 'Unknown').upper()}</p>
                                            <p style="color: #000000;"><strong>Estimated Loss:</strong> ${violation.get('estimated_loss', 0):.2f}</p>
                                        </div>
                                    </details>
                                    """, unsafe_allow_html=True)
                                else:
                                    # Handle regular violations
                                    driver_info = f"{violation.get('driver_name', 'Unknown Driver')} ({violation.get('vehicle_id', 'Unknown Vehicle')})"
                                    violation_title = violation.get('type', 'Unknown').replace('_', ' ').title()
                                    
                                    st.markdown(f"""
                                    <details style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 0.5rem; margin: 0.5rem 0;">
                                        <summary style="background: #ffffff; color: #000000; font-weight: 600; padding: 1rem; cursor: pointer; border-radius: 0.5rem;">
                                            <strong>{violation_title}</strong> - {driver_info}
                                        </summary>
                                        <div style="padding: 1rem; color: #000000; background: #ffffff;">
                                            <p style="color: #000000;"><strong>Driver:</strong> {violation.get('driver_name', 'Unknown')}</p>
                                            <p style="color: #000000;"><strong>Vehicle:</strong> {violation.get('vehicle_id', 'Unknown')}</p>
                                            <p style="color: #000000;"><strong>Time:</strong> {violation.get('timestamp', 'Unknown')}</p>
                                            <p style="color: #000000;"><strong>Location:</strong> {violation.get('location', 'Unknown')}</p>
                                            {f"<p style='color: #000000;'><strong>Card Used:</strong> ****{violation['card_last_4']}</p>" if violation.get('card_last_4') else ""}
                                            <p style="color: #000000;"><strong>Description:</strong> {violation.get('description', 'No description')}</p>
                                            <p style="color: #000000;"><strong>Severity:</strong> {violation.get('severity', 'Unknown').upper()}</p>
                                            <p style="color: #000000;"><strong>Estimated Loss:</strong> ${violation.get('estimated_loss', 0):.2f}</p>
                                        </div>
                                    </details>
                                    """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background: #dcfce7; border: 1px solid #16a34a; border-radius: 0.5rem; padding: 1rem; color: #000000; margin: 1rem 0;">
                                🎉 Clean Fleet Audit Results - No fraud or policy violations detected!
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="background: #fef2f2; border: 1px solid #dc2626; border-radius: 0.5rem; padding: 1rem; color: #000000; margin: 1rem 0;">
                            ❌ Failed to get valid response from AI
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.markdown(f"""
                    <div style="background: #fef2f2; border: 1px solid #dc2626; border-radius: 0.5rem; padding: 1rem; color: #000000; margin: 1rem 0;">
                        ❌ Fraud detection failed: {str(e)}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #fef2f2; border: 1px solid #dc2626; border-radius: 0.5rem; padding: 1rem; color: #000000; margin: 1rem 0;">
                ❌ Please upload fuel data to run analysis.
            </div>
            """, unsafe_allow_html=True)

# Main app logic
def main():
    if st.session_state.current_page == 'home':
        show_home_page()
    elif st.session_state.current_page == 'product':
        show_product_page()

if __name__ == "__main__":
    main()