import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from anthropic import Anthropic
# Optional PDF generation imports
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Create dummy classes to prevent errors
    letter = None
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    Table = None
    TableStyle = None

# Page config - this runs for each page
st.set_page_config(
    page_title="FleetAudit.io - App",
    page_icon="🚛",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main theme colors */
    .main {
        padding-top: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .main-header h1 {
        color: white !important;
        margin-bottom: 0.5rem;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: #e8f4f8 !important;
        font-size: 1.2rem;
        margin-bottom: 0;
    }
    
    /* Upload section styling */
    .upload-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    
    /* Violation card styling */
    .violation-card {
        background: #fff5f5;
        border: 1px solid #fed7d7;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #e53e3e;
    }
    
    .violation-card.high {
        border-left-color: #e53e3e;
        background: #fff5f5;
    }
    
    .violation-card.medium {
        border-left-color: #dd6b20;
        background: #fffbf0;
    }
    
    .violation-card.low {
        border-left-color: #ecc94b;
        background: #fffff0;
    }
    
    /* Success styling */
    .success-card {
        background: #f0fff4;
        border: 1px solid #c6f6d5;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        border-left: 4px solid #38a169;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(31, 78, 121, 0.3);
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Upload widget styling */
    .uploadedFile {
        border: 2px dashed #2d5aa0;
        border-radius: 8px;
        padding: 1rem;
        background: #f8f9fa;
    }
    
    /* Divider styling */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #2d5aa0 50%, transparent 100%);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    /* Remove Streamlit branding */
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

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
    st.markdown("### ⛽ Fuel Data Upload")
    with st.container():
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
            elif 'card_last_4' not in fuel_df.columns and 'card_number' not in fuel_df.columns:
                # Try to find any column that might contain card info
                card_columns = [col for col in fuel_df.columns if 'card' in col.lower() or 'last' in col.lower()]
                if card_columns:
                    fuel_df['card_last_4'] = fuel_df[card_columns[0]].astype(str).str[-4:]
            
            st.session_state.fuel_data = fuel_df
            st.success(f"✅ Fuel data loaded: {len(fuel_df)} records")
            
            # Show preview
            st.write("**Preview:**")
            st.dataframe(fuel_df.head(), use_container_width=True)
            
            
        except Exception as e:
            st.error(f"❌ Error loading fuel data: {str(e)}")

def upload_gps_data():
    """Simple pandas-based GPS data upload"""
    st.markdown("### 🗺️ GPS Data Upload")
    with st.container():
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
    st.markdown("### 📋 Job Data Upload")
    with st.container():
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
    st.markdown("### 🚨 Fraud Detection")
    st.markdown("Upload your fleet data above, then click the button below to analyze for potential fraud and policy violations.")
    st.markdown("---")
    
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
                analysis_data = f"FUEL DATA:\\n{fuel_csv}\\n"
                
                if st.session_state.gps_data is not None:
                    gps_csv = st.session_state.gps_data.to_csv(index=False)
                    analysis_data += f"\\nGPS DATA:\\n{gps_csv}\\n"
                
                if st.session_state.job_data is not None:
                    job_csv = st.session_state.job_data.to_csv(index=False)
                    analysis_data += f"\\nJOB DATA:\\n{job_csv}\\n"
                
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
                    max_tokens=4000,  # Haiku max is 4096
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
                    
                    st.session_state.fraud_results = fraud_results
                    
                    # Display results
                    violations = fraud_results.get('violations', [])
                    summary = fraud_results.get('summary', {})
                    
                    if violations:
                        # Summary cards
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
                        
                        # Show violations
                        for i, violation in enumerate(violations):
                            # Handle shared card use violations differently
                            if violation.get('type') == 'shared_card_use':
                                card_info = f"Card ****{violation.get('card_last_4', 'Unknown')}"
                                vehicles = ', '.join(violation.get('vehicles_involved', []))
                                with st.expander(f"**Shared Card Use** - {card_info} ({vehicles})"):
                                    st.write(f"**Card Last 4:** ****{violation.get('card_last_4', 'Unknown')}")
                                    st.write(f"**Vehicles Involved:** {', '.join(violation.get('vehicles_involved', []))}")
                                    st.write(f"**Drivers Involved:** {', '.join(violation.get('drivers_involved', []))}")
                                    st.write(f"**Time Span:** {violation.get('time_span_minutes', 'Unknown')} minutes")
                                    
                                    # Show transaction details
                                    st.write("**Transactions:**")
                                    for tx in violation.get('transactions', []):
                                        st.write(f"  • {tx.get('timestamp', 'Unknown')} - {tx.get('driver_name', 'Unknown')} in {tx.get('vehicle_id', 'Unknown')} at {tx.get('location', 'Unknown')}")
                                    
                                    st.write(f"**Description:** {violation.get('description', 'No description')}")
                                    st.write(f"**Severity:** {violation.get('severity', 'Unknown').upper()}")
                                    if violation.get('estimated_loss'):
                                        st.write(f"**Estimated Loss:** ${violation['estimated_loss']:.2f}")
                            else:
                                # Handle regular violations
                                driver_info = f"{violation.get('driver_name', 'Unknown Driver')} ({violation.get('vehicle_id', 'Unknown Vehicle')})"
                                with st.expander(f"**{violation.get('type', 'Unknown').replace('_', ' ').title()}** - {driver_info}"):
                                    st.write(f"**Driver:** {violation.get('driver_name', 'Unknown')}")
                                    st.write(f"**Vehicle:** {violation.get('vehicle_id', 'Unknown')}")
                                    st.write(f"**Time:** {violation.get('timestamp', 'Unknown')}")
                                    st.write(f"**Location:** {violation.get('location', 'Unknown')}")
                                    # Show card last 4 for fuel-related violations
                                    if violation.get('card_last_4'):
                                        st.write(f"**Card Used:** ****{violation['card_last_4']}")
                                    st.write(f"**Description:** {violation.get('description', 'No description')}")
                                    st.write(f"**Severity:** {violation.get('severity', 'Unknown').upper()}")
                                    if violation.get('estimated_loss'):
                                        st.write(f"**Estimated Loss:** ${violation['estimated_loss']:.2f}")
                    else:
                        st.markdown("""
                        <div class="success-card">
                            <h3>🎉 Clean Fleet Audit Results</h3>
                            <p>No fraud or policy violations detected in your fleet data!</p>
                            <p><em>Your fleet operations appear to be following proper procedures.</em></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                else:
                    st.error("❌ Failed to get valid response from AI")
                    
            except Exception as e:
                st.error(f"❌ Fraud detection failed: {str(e)}")

def generate_pdf_report():
    """Generate PDF report of fraud findings"""
    if not st.session_state.fraud_results:
        return None
        
    if not REPORTLAB_AVAILABLE:
        return None
        
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf_path = tmp_file.name
    
    # Create PDF
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("FleetAudit.io - Fraud Detection Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Summary
    violations = st.session_state.fraud_results.get('violations', [])
    summary = st.session_state.fraud_results.get('summary', {})
    
    summary_text = f"""Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Total Violations: {len(violations)}
    Estimated Total Loss: ${summary.get('total_estimated_loss', 0):.2f}
    High Risk Vehicles: {', '.join(summary.get('high_risk_vehicles', []))}"""
    
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Violations table
    if violations:
        story.append(Paragraph("Detected Violations:", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        # Table data
        table_data = [['Type', 'Driver', 'Vehicle', 'Time', 'Location', 'Card', 'Loss']]
        
        for violation in violations:
            if violation.get('type') == 'shared_card_use':
                # Handle shared card violations with special formatting
                vehicles = ', '.join(violation.get('vehicles_involved', []))
                drivers = ', '.join(violation.get('drivers_involved', []))
                card_info = f"****{violation.get('card_last_4', 'Unknown')}"
                time_span = f"{violation.get('time_span_minutes', 'Unknown')} min"
                
                table_data.append([
                    'Shared Card Use',
                    drivers,
                    vehicles,
                    time_span,
                    'Multiple Locations',
                    card_info,
                    f"${violation.get('estimated_loss', 0):.2f}"
                ])
            else:
                # Handle regular violations
                card_used = f"****{violation.get('card_last_4', 'N/A')}" if violation.get('card_last_4') else 'N/A'
                table_data.append([
                    violation.get('type', '').replace('_', ' ').title(),
                    violation.get('driver_name', 'Unknown'),
                    violation.get('vehicle_id', 'Unknown'),
                    violation.get('timestamp', 'Unknown'),
                    violation.get('location', 'Unknown'),
                    card_used,
                    f"${violation.get('estimated_loss', 0):.2f}"
                ])
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    
    # Build PDF
    doc.build(story)
    return pdf_path

def export_reports():
    """Export and email reports section"""
    st.markdown("### 📄 Export Reports")
    st.markdown("Generate professional reports for management and compliance purposes.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download PDF Report", use_container_width=True):
            if not REPORTLAB_AVAILABLE:
                st.error("📄 PDF generation requires reportlab. Install it to enable PDF exports.")
            else:
                with st.spinner("Generating PDF report..."):
                    try:
                        pdf_path = generate_pdf_report()
                        
                        if pdf_path:
                            with open(pdf_path, "rb") as pdf_file:
                                st.download_button(
                                    label="📥 Download Report",
                                    data=pdf_file.read(),
                                    file_name=f"fraud_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            
                            # Clean up temp file
                            os.unlink(pdf_path)
                            
                    except Exception as e:
                        st.error(f"PDF generation failed: {str(e)}")
    
    with col2:
        recipient_email = st.text_input("📧 Email Report To:", placeholder="manager@company.com")
        
        if st.button("📧 Send Email Report", use_container_width=True) and recipient_email:
            st.info("🔧 Email functionality coming soon - use PDF download for now")

def main():
    """Main app"""
    init_session_state()
    
    # Simple working navigation for deployed version
    with st.sidebar:
        st.markdown("### Navigation")
        
        if st.button("🏠 Go to Landing", key="nav_to_landing"):
            st.switch_page("app.py")
            
        st.markdown("**🚛 App** ← You are here")
        
        if st.button("🔧 Go to Backup", key="nav_to_backup"):
            st.switch_page("pages/2_Backup.py")
    
    # Styled header
    st.markdown("""
    <div class="main-header">
        <h1>🚛 FleetAudit.io - App</h1>
        <p>AI-Powered Fleet Fraud Detection & Audit Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload section
    st.markdown("## 📁 Data Upload")
    st.markdown("Upload your fleet data files to begin fraud detection analysis.")
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        upload_fuel_data()
    
    with col2:
        upload_gps_data()
        
    with col3:
        upload_job_data()
    
    st.markdown("---")
    
    # Fraud detection
    detect_fraud()
    
    # Report export section
    if st.session_state.fraud_results:
        st.divider()
        export_reports()
    
    # Show current data status
    st.markdown("---")
    st.markdown("### 📊 Data Status")
    st.markdown("Overview of uploaded data and system readiness.")
    
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

# Run the main function for multipage apps
main()