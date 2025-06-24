import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import random

# Page config
st.set_page_config(
    page_title="FleetAudit.io - Fleet Fraud Detection",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for landing page styling
st.markdown("""
<style>
    /* Main theme colors */
    .main {
        padding-top: 1rem;
    }
    
    /* Hero section styling */
    .hero-section {
        background: linear-gradient(135deg, #1f4e79 0%, #2d5aa0 50%, #3d6bb5 100%);
        padding: 4rem 2rem;
        border-radius: 15px;
        margin-bottom: 3rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(31, 78, 121, 0.3);
    }
    
    .hero-section h1 {
        color: white !important;
        margin-bottom: 1rem;
        font-size: 3.5rem;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .hero-section h2 {
        color: #e8f4f8 !important;
        font-size: 1.4rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    .hero-section p {
        color: #b8dae8 !important;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Feature cards */
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        border: 1px solid #e9ecef;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    
    .feature-card h3 {
        color: #1f4e79;
        margin-bottom: 1rem;
        font-size: 1.3rem;
    }
    
    /* Demo section */
    .demo-section {
        background: #f8f9fa;
        padding: 3rem 2rem;
        border-radius: 12px;
        margin: 2rem 0;
        border: 2px solid #e9ecef;
    }
    
    .demo-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .demo-header h2 {
        color: #1f4e79;
        font-size: 2.2rem;
        margin-bottom: 1rem;
    }
    
    /* Violation cards for demo */
    .violation-demo {
        background: #fff5f5;
        border: 1px solid #fed7d7;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #e53e3e;
    }
    
    .violation-demo.high {
        border-left-color: #e53e3e;
        background: #fff5f5;
    }
    
    .violation-demo.medium {
        border-left-color: #dd6b20;
        background: #fffbf0;
    }
    
    /* CTA Button */
    .cta-button {
        background: linear-gradient(90deg, #e53e3e 0%, #c53030 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        border: none;
        font-size: 1.2rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
        margin: 1rem;
    }
    
    .cta-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(229, 62, 62, 0.4);
    }
    
    /* Pricing preview */
    .pricing-preview {
        background: white;
        border: 2px solid #2d5aa0;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    
    .price {
        font-size: 3rem;
        font-weight: 800;
        color: #1f4e79;
        margin: 1rem 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(31, 78, 121, 0.3);
    }
    
    /* Remove Streamlit branding */
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Clean navigation links */
    .nav-link {
        display: block;
        padding: 0.5rem 0;
        color: #1f4e79;
        text-decoration: none;
        cursor: pointer;
        font-size: 1.1rem;
    }
    
    .nav-link:hover {
        color: #2d5aa0;
        text-decoration: underline;
    }
    
    .nav-current {
        font-weight: bold;
        color: #2d5aa0;
    }
</style>
""", unsafe_allow_html=True)

def get_demo_data():
    """Generate realistic demo data for the fleet audit"""
    
    # Sample scenarios
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
                },
                {
                    "type": "ghost_job",
                    "job_id": "ATL-2024-0815",
                    "driver_name": "Mike Chen",
                    "vehicle_id": "VAN-003",
                    "scheduled_time": "2024-08-15 14:00:00",
                    "address": "Buford, GA",
                    "description": "Scheduled delivery with no GPS activity at job location",
                    "severity": "high", 
                    "estimated_loss": 150.00
                }
            ],
            "summary": {
                "total_violations": 4,
                "total_estimated_loss": 551.75,
                "high_risk_vehicles": ["VAN-003", "VAN-005", "TRUCK-003"]
            }
        },
        "Metro Delivery": {
            "description": "6-vehicle urban delivery service with moderate violations",
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
                    "severity": "medium",
                    "estimated_loss": 67.25
                }
            ],
            "summary": {
                "total_violations": 2,
                "total_estimated_loss": 162.75,
                "high_risk_vehicles": ["VAN-002", "TRUCK-001"]
            }
        },
        "Clean Fleet Co": {
            "description": "8-vehicle service fleet with excellent compliance record",
            "vehicles": 8,
            "violations": [
                {
                    "type": "minor_deviation",
                    "vehicle_id": "VAN-001",
                    "driver_name": "Jennifer Adams",
                    "timestamp": "2024-08-09 18:15:00",
                    "location": "BP Station - Route 285",
                    "card_last_4": "5566",
                    "description": "Fuel purchase 15 minutes after official end of shift",
                    "severity": "low",
                    "estimated_loss": 12.50
                }
            ],
            "summary": {
                "total_violations": 1,
                "total_estimated_loss": 12.50,
                "high_risk_vehicles": []
            }
        }
    }
    
    return scenarios

def display_demo_results(scenario_name, scenario_data):
    """Display demo results that look like real fraud detection output"""
    
    violations = scenario_data["violations"]
    summary = scenario_data["summary"]
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🚨 Violations Found", len(violations), delta=f"{len(violations)} issues")
    with col2:
        total_loss = summary.get('total_estimated_loss', 0)
        st.metric("💰 Estimated Loss", f"${total_loss:.2f}", delta=f"-${total_loss:.2f}")
    with col3:
        high_risk = len([v for v in violations if v.get('severity') == 'high'])
        st.metric("⚠️ High Risk", high_risk, delta=f"{high_risk} critical")
    
    st.markdown("---")
    
    # Display violations
    for violation in violations:
        if violation.get('type') == 'shared_card_use':
            card_info = f"Card ****{violation.get('card_last_4', 'Unknown')}"
            vehicles = ', '.join(violation.get('vehicles_involved', []))
            with st.expander(f"**Shared Card Use** - {card_info} ({vehicles})"):
                st.write(f"**Card Last 4:** ****{violation.get('card_last_4', 'Unknown')}")
                st.write(f"**Vehicles Involved:** {', '.join(violation.get('vehicles_involved', []))}")
                st.write(f"**Drivers Involved:** {', '.join(violation.get('drivers_involved', []))}")
                st.write(f"**Time Span:** {violation.get('time_span_minutes', 'Unknown')} minutes")
                st.write(f"**Description:** {violation.get('description', 'No description')}")
                st.write(f"**Severity:** {violation.get('severity', 'Unknown').upper()}")
                if violation.get('estimated_loss'):
                    st.write(f"**Estimated Loss:** ${violation['estimated_loss']:.2f}")
        else:
            # Handle regular violations
            driver_info = f"{violation.get('driver_name', 'Unknown Driver')} ({violation.get('vehicle_id', 'Unknown Vehicle')})"
            violation_title = violation.get('type', 'Unknown').replace('_', ' ').title()
            with st.expander(f"**{violation_title}** - {driver_info}"):
                st.write(f"**Driver:** {violation.get('driver_name', 'Unknown')}")
                st.write(f"**Vehicle:** {violation.get('vehicle_id', 'Unknown')}")
                st.write(f"**Time:** {violation.get('timestamp', 'Unknown')}")
                if violation.get('location'):
                    st.write(f"**Location:** {violation.get('location', 'Unknown')}")
                if violation.get('address'):
                    st.write(f"**Job Address:** {violation.get('address', 'Unknown')}")
                if violation.get('card_last_4'):
                    st.write(f"**Card Used:** ****{violation['card_last_4']}")
                st.write(f"**Description:** {violation.get('description', 'No description')}")
                st.write(f"**Severity:** {violation.get('severity', 'Unknown').upper()}")
                if violation.get('estimated_loss'):
                    st.write(f"**Estimated Loss:** ${violation['estimated_loss']:.2f}")

def main():
    # Simple working navigation for deployed version
    with st.sidebar:
        st.markdown("### Navigation")
        st.markdown("**🏠 Landing Page** ← You are here")
        
        # Simple form-based navigation that should work in deployed environments
        if st.button("🚛 Go to App", key="nav_to_app"):
            st.switch_page("1_Product")
            
        if st.button("🔧 Go to Backup", key="nav_to_backup"):
            st.switch_page("2_Backup")
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1>🚛 FleetAudit.io</h1>
        <h2>Stop Fleet Fraud Before It Costs You Thousands</h2>
        <p>AI-powered fraud detection that analyzes your fuel, GPS, and job data to uncover theft, misuse, and policy violations in minutes.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features Section
    st.markdown("## Why FleetAudit.io?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🔍 AI-Powered Detection</h3>
            <p>Advanced algorithms detect fraud patterns humans miss - shared cards, ghost jobs, after-hours abuse, and more.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>💰 Immediate ROI</h3>
            <p>Customers typically recover 10x their subscription cost in the first month by stopping ongoing fraud.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Professional Reports</h3>
            <p>Generate detailed PDF reports with evidence for HR, management, and legal proceedings.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Demo Section
    st.markdown("""
    <div class="demo-section">
        <div class="demo-header">
            <h2>🎯 See FleetAudit.io in Action</h2>
            <p>Select a sample fleet below to see how our AI detects fraud and policy violations:</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo selector
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
        st.info(f"**{selected_scenario}**\n\n{scenario_info['description']}")
        
        if st.button("🔍 Run Fraud Analysis", type="primary", use_container_width=True):
            st.session_state.show_demo = True
    
    with col2:
        if st.session_state.get('show_demo', False):
            st.markdown(f"### 🚨 Fraud Detection Results: {selected_scenario}")
            display_demo_results(selected_scenario, demo_data[selected_scenario])
    
    # Pricing Preview
    st.markdown("---")
    st.markdown("## 💳 Simple, Transparent Pricing")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="pricing-preview">
            <h3>Professional Plan</h3>
            <div class="price">$99<span style="font-size: 1rem; color: #666;">/month</span></div>
            <p>✅ Unlimited fleet data analysis<br>
            ✅ All fraud detection features<br>
            ✅ PDF report generation<br>
            ✅ Email alerts & notifications<br>
            ✅ Priority support</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Free Trial", type="primary", use_container_width=True):
            st.balloons()
            st.success("🎉 Ready to start your free trial! Subscription system coming soon.")
    
    # Call to Action
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2>Ready to Stop Fleet Fraud?</h2>
        <p style="font-size: 1.2rem; margin-bottom: 2rem;">Join hundreds of fleet managers who've recovered thousands in stolen fuel and time.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**FleetAudit.io**")
        st.markdown("AI-powered fleet fraud detection")
    
    with col2:
        st.markdown("**Features**")
        st.markdown("• Shared card detection\n• Ghost job analysis\n• After-hours monitoring\n• GPS cross-referencing")
    
    with col3:
        st.markdown("**Support**")
        st.markdown("• 24/7 customer support\n• Implementation assistance\n• Training & onboarding")

if __name__ == "__main__":
    main()