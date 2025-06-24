import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from anthropic import Anthropic

# Page config
st.set_page_config(
    page_title="FleetAudit.io - Clean Version",
    page_icon="🚛",
    layout="wide"
)

def init_session_state():
    """Initialize session state"""
    if 'fuel_data' not in st.session_state:
        st.session_state.fuel_data = None
    if 'gps_data' not in st.session_state:
        st.session_state.gps_data = None
    if 'job_data' not in st.session_state:
        st.session_state.job_data = None
    if 'fraud_results' not in st.session_state:
        st.session_state.fraud_results = None

def upload_fuel_data():
    """Simple pandas-based fuel data upload"""
    st.subheader("⛽ Fuel Data Upload")
    
    fuel_file = st.file_uploader(
        "Upload Fuel CSV", 
        type=['csv'], 
        key="fuel_upload",
        help="Upload fuel card transaction data"
    )
    
    if fuel_file is not None:
        try:
            # Simple pandas parsing
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
                'Driver Name': 'driver_name'
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
            
            st.session_state.fuel_data = fuel_df
            st.success(f"✅ Fuel data loaded: {len(fuel_df)} records")
            
            # Show preview
            st.write("**Preview:**")
            st.dataframe(fuel_df.head(), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error loading fuel data: {str(e)}")

def upload_gps_data():
    """Simple pandas-based GPS data upload"""
    st.subheader("🗺️ GPS Data Upload")
    
    gps_file = st.file_uploader(
        "Upload GPS CSV", 
        type=['csv'], 
        key="gps_upload",
        help="Upload GPS tracking data"
    )
    
    if gps_file is not None:
        try:
            gps_df = pd.read_csv(gps_file)
            
            # Basic standardization
            if 'Timestamp' in gps_df.columns:
                gps_df['timestamp'] = pd.to_datetime(gps_df['Timestamp'], errors='coerce')
            elif 'Date' in gps_df.columns:
                gps_df['timestamp'] = pd.to_datetime(gps_df['Date'], errors='coerce')
            
            st.session_state.gps_data = gps_df
            st.success(f"✅ GPS data loaded: {len(gps_df)} records")
            
            # Show preview
            st.write("**Preview:**")
            st.dataframe(gps_df.head(), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error loading GPS data: {str(e)}")

def upload_job_data():
    """Simple pandas-based job data upload"""
    st.subheader("📋 Job Data Upload") 
    
    job_file = st.file_uploader(
        "Upload Job CSV", 
        type=['csv'], 
        key="job_upload",
        help="Upload job scheduling data"
    )
    
    if job_file is not None:
        try:
            job_df = pd.read_csv(job_file)
            
            # Basic standardization
            if 'Scheduled Time' in job_df.columns:
                job_df['timestamp'] = pd.to_datetime(job_df['Scheduled Time'], errors='coerce')
            elif 'Date' in job_df.columns:
                job_df['timestamp'] = pd.to_datetime(job_df['Date'], errors='coerce')
                
            st.session_state.job_data = job_df
            st.success(f"✅ Job data loaded: {len(job_df)} records")
            
            # Show preview
            st.write("**Preview:**")
            st.dataframe(job_df.head(), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error loading job data: {str(e)}")

def detect_fraud():
    """Claude Haiku-only fraud detection"""
    st.subheader("🚨 Fraud Detection")
    
    if st.session_state.fuel_data is None:
        st.warning("⚠️ Please upload fuel data first")
        return
    
    if st.button("🔍 Detect Fraud", type="primary", use_container_width=True):
        with st.spinner("Analyzing data for fraud with Claude Haiku..."):
            try:
                # Initialize Claude Haiku
                client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                
                # Prepare data for analysis
                fuel_csv = st.session_state.fuel_data.to_csv(index=False)
                
                # Add GPS data if available
                analysis_data = f"FUEL DATA:\n{fuel_csv}\n"
                
                if st.session_state.gps_data is not None:
                    gps_csv = st.session_state.gps_data.to_csv(index=False)
                    analysis_data += f"\nGPS DATA:\n{gps_csv}\n"
                
                if st.session_state.job_data is not None:
                    job_csv = st.session_state.job_data.to_csv(index=False)
                    analysis_data += f"\nJOB DATA:\n{job_csv}\n"
                
                # Simple, direct prompt
                prompt = f"""Analyze this fleet data for fraud and theft. Return JSON only.

{analysis_data}

Find these fraud types:
- After-hours fuel purchases
- Fuel without GPS at location  
- Excessive fuel amounts
- Rapid consecutive purchases
- Personal use patterns

Return JSON:
{{
  "violations": [
    {{
      "type": "after_hours",
      "vehicle_id": "TRUCK001", 
      "timestamp": "2024-06-16 02:00:00",
      "location": "Shell Station",
      "description": "Fuel purchase at 2 AM outside business hours",
      "severity": "high",
      "estimated_loss": 75.50
    }}
  ],
  "summary": {{
    "total_violations": 5,
    "total_estimated_loss": 500.00,
    "high_risk_vehicles": ["TRUCK001", "VAN002"]
  }}
}}"""
                
                # Call Claude Haiku
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
                else:
                    raise ValueError("No JSON found in response")
                    
                    st.session_state.fraud_results = fraud_results
                    
                    # Display results
                    violations = fraud_results.get('violations', [])
                    summary = fraud_results.get('summary', {})
                    
                    if violations:
                        st.error(f"🚨 **{len(violations)} fraud incidents detected!**")
                        
                        if summary.get('total_estimated_loss'):
                            st.error(f"💰 **Estimated loss: ${summary['total_estimated_loss']:.2f}**")
                        
                        # Show violations
                        for i, violation in enumerate(violations):
                            with st.expander(f"**{violation.get('type', 'Unknown').replace('_', ' ').title()}** - {violation.get('vehicle_id', 'Unknown Vehicle')}"):
                                st.write(f"**Time:** {violation.get('timestamp', 'Unknown')}")
                                st.write(f"**Location:** {violation.get('location', 'Unknown')}")
                                st.write(f"**Description:** {violation.get('description', 'No description')}")
                                st.write(f"**Severity:** {violation.get('severity', 'Unknown').upper()}")
                                if violation.get('estimated_loss'):
                                    st.write(f"**Estimated Loss:** ${violation['estimated_loss']:.2f}")
                    else:
                        st.success("🎉 No fraud detected in your fleet data!")
                
                else:
                    st.error("❌ Failed to get valid response from AI")
                    
            except Exception as e:
                st.error(f"❌ Fraud detection failed: {str(e)}")

def main():
    """Main app"""
    init_session_state()
    
    # Header
    st.title("🚛 FleetAudit.io - Clean Version")
    st.write("**Simple, AI-powered fleet fraud detection**")
    
    # Upload section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        upload_fuel_data()
    
    with col2:
        upload_gps_data()
        
    with col3:
        upload_job_data()
    
    st.divider()
    
    # Fraud detection
    detect_fraud()
    
    # Show current data status
    st.divider()
    st.subheader("📊 Data Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.fuel_data is not None:
            st.metric("Fuel Records", len(st.session_state.fuel_data))
        else:
            st.metric("Fuel Records", "Not loaded")
    
    with col2:
        if st.session_state.gps_data is not None:
            st.metric("GPS Records", len(st.session_state.gps_data))
        else:
            st.metric("GPS Records", "Not loaded")
            
    with col3:
        if st.session_state.job_data is not None:
            st.metric("Job Records", len(st.session_state.job_data))
        else:
            st.metric("Job Records", "Not loaded")

if __name__ == "__main__":
    main()