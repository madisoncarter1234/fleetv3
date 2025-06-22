import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import tempfile
import traceback

# Import our custom modules
from parsers.gps_parser import GPSParser
from parsers.fuel_parser import FuelParser
from parsers.job_parser import JobParser
from logic.matcher import FleetAuditor
from logic.report_generator import ReportGenerator
from email_service.send_email import EmailSender

# Page configuration
st.set_page_config(
    page_title="FleetAudit.io",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .violation-card {
        background: white;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 4px solid #e74c3c;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'gps_data' not in st.session_state:
        st.session_state.gps_data = None
    if 'fuel_data' not in st.session_state:
        st.session_state.fuel_data = None
    if 'job_data' not in st.session_state:
        st.session_state.job_data = None
    if 'audit_results' not in st.session_state:
        st.session_state.audit_results = None
    if 'report_path' not in st.session_state:
        st.session_state.report_path = None
    if 'company_name' not in st.session_state:
        st.session_state.company_name = "Your Fleet Company"

def main():
    """Main application function"""
    
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🚛 FleetAudit.io</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Automated Fleet Monitoring & Audit Reports</div>', unsafe_allow_html=True)
    
    # Quick info about data requirements
    with st.expander("ℹ️ What data do I need for different violation types?"):
        st.write("""
        **🚨 Fuel Theft Detection:** Requires GPS logs + Fuel card data
        - Cross-references fuel purchases with vehicle locations
        - Flags purchases when vehicle wasn't near gas station
        
        **👻 Ghost Job Detection:** Requires GPS logs + Job scheduling data  
        - Checks if vehicles actually visited scheduled job sites
        - Identifies jobs marked complete without site visits
        
        **⏰ Idle Time Abuse:** Requires GPS logs only
        - Detects vehicles sitting idle for extended periods
        - Flags excessive fuel waste from idling
        
        **🌙 After-Hours Driving:** Requires GPS logs only
        - Monitors vehicle usage outside business hours
        - Catches unauthorized personal use of company vehicles
        
        **💡 Tip:** Upload whatever data you have - the system will detect what violations it can analyze!
        """)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Company name
        company_name = st.text_input(
            "Company Name",
            value=st.session_state.company_name,
            help="This will appear on your reports"
        )
        st.session_state.company_name = company_name
        
        # Email configuration
        st.subheader("📧 Email Settings")
        email_provider = st.selectbox(
            "Email Provider",
            ["resend", "sendgrid", "smtp"],
            help="Choose your email service provider"
        )
        
        recipient_email = st.text_input(
            "Report Recipient Email",
            help="Where to send the audit reports"
        )
        
        # Date range for report
        st.subheader("📅 Report Period")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=7)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now()
            )
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Upload Data", "🔍 Run Audit", "📊 View Results", "📧 Send Report"])
    
    with tab1:
        st.header("Upload Fleet Data Files")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="upload-section">', unsafe_allow_html=True)
            st.subheader("🗺️ GPS Logs")
            st.write("Upload GPS tracking data (CSV)")
            
            gps_provider = st.selectbox(
                "GPS Provider",
                ["auto-detect", "samsara", "verizon", "generic"],
                key="gps_provider"
            )
            
            gps_file = st.file_uploader(
                "Choose GPS CSV file",
                type=['csv'],
                key="gps_upload",
                help="Upload GPS logs from Samsara, Verizon Connect, or other providers"
            )
            
            if gps_file is not None:
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                        tmp_file.write(gps_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Parse GPS data
                    if gps_provider == "auto-detect":
                        gps_data = GPSParser.auto_parse(tmp_path)
                    else:
                        gps_data = getattr(GPSParser, f'parse_{gps_provider}')(tmp_path)
                    
                    st.session_state.gps_data = gps_data
                    st.success(f"✅ GPS data loaded: {len(gps_data)} records")
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    st.error(f"❌ Error parsing GPS file: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="upload-section">', unsafe_allow_html=True)
            st.subheader("⛽ Fuel Card Data")
            st.write("Upload fuel purchase records (CSV)")
            
            fuel_provider = st.selectbox(
                "Fuel Card Provider",
                ["auto-detect", "wex", "fleetcor", "fuelman", "generic"],
                key="fuel_provider"
            )
            
            fuel_file = st.file_uploader(
                "Choose Fuel CSV file",
                type=['csv'],
                key="fuel_upload",
                help="Upload fuel card transaction data"
            )
            
            if fuel_file is not None:
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                        tmp_file.write(fuel_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Parse fuel data
                    if fuel_provider == "auto-detect":
                        fuel_data = FuelParser.auto_parse(tmp_path)
                    else:
                        fuel_data = getattr(FuelParser, f'parse_{fuel_provider}')(tmp_path)
                    
                    st.session_state.fuel_data = fuel_data
                    st.success(f"✅ Fuel data loaded: {len(fuel_data)} records")
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    st.error(f"❌ Error parsing fuel file: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="upload-section">', unsafe_allow_html=True)
            st.subheader("📋 Job Logs")
            st.write("Upload job scheduling data (CSV/XLS)")
            
            job_provider = st.selectbox(
                "Job Management System",
                ["auto-detect", "jobber", "housecall_pro", "servicetitan", "generic"],
                key="job_provider"
            )
            
            job_file = st.file_uploader(
                "Choose Job file",
                type=['csv', 'xlsx', 'xls'],
                key="job_upload",
                help="Upload job scheduling and dispatch data"
            )
            
            if job_file is not None:
                try:
                    # Save uploaded file temporarily
                    file_extension = job_file.name.split('.')[-1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
                        tmp_file.write(job_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Parse job data
                    if job_provider == "auto-detect":
                        job_data = JobParser.auto_parse(tmp_path)
                    else:
                        job_data = getattr(JobParser, f'parse_{job_provider}')(tmp_path)
                    
                    st.session_state.job_data = job_data
                    st.success(f"✅ Job data loaded: {len(job_data)} records")
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    st.error(f"❌ Error parsing job file: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Data preview section
        if any([st.session_state.gps_data is not None, 
                st.session_state.fuel_data is not None, 
                st.session_state.job_data is not None]):
            
            st.header("📋 Data Preview")
            
            preview_tab1, preview_tab2, preview_tab3 = st.tabs(["GPS Data", "Fuel Data", "Job Data"])
            
            with preview_tab1:
                if st.session_state.gps_data is not None:
                    st.write(f"**GPS Records:** {len(st.session_state.gps_data)}")
                    st.dataframe(st.session_state.gps_data.head(10), use_container_width=True)
                else:
                    st.info("No GPS data uploaded yet")
            
            with preview_tab2:
                if st.session_state.fuel_data is not None:
                    st.write(f"**Fuel Records:** {len(st.session_state.fuel_data)}")
                    st.dataframe(st.session_state.fuel_data.head(10), use_container_width=True)
                else:
                    st.info("No fuel data uploaded yet")
            
            with preview_tab3:
                if st.session_state.job_data is not None:
                    st.write(f"**Job Records:** {len(st.session_state.job_data)}")
                    st.dataframe(st.session_state.job_data.head(10), use_container_width=True)
                else:
                    st.info("No job data uploaded yet")
    
    with tab2:
        st.header("🔍 Run Fleet Audit")
        
        # Check if at least one data source is loaded
        has_data = any([
            st.session_state.gps_data is not None,
            st.session_state.fuel_data is not None,
            st.session_state.job_data is not None
        ])
        
        if not has_data:
            st.warning("⚠️ Please upload at least one data file (GPS, Fuel, or Jobs) to run an audit.")
        else:
            uploaded_data = []
            if st.session_state.gps_data is not None:
                uploaded_data.append("GPS logs")
            if st.session_state.fuel_data is not None:
                uploaded_data.append("Fuel card data")
            if st.session_state.job_data is not None:
                uploaded_data.append("Job logs")
            
            st.success(f"✅ Data loaded: {', '.join(uploaded_data)}")
            
            # Show which violation types can be detected
            st.info("**Available Violation Detection:**")
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state.gps_data is not None and st.session_state.fuel_data is not None:
                    st.write("🚨 Fuel theft detection")
                if st.session_state.gps_data is not None and st.session_state.job_data is not None:
                    st.write("👻 Ghost job detection")
            with col2:
                if st.session_state.gps_data is not None:
                    st.write("⏰ Idle time abuse")
                    st.write("🌙 After-hours driving")
            
            missing_data = []
            if st.session_state.gps_data is None:
                missing_data.append("GPS logs")
            if st.session_state.fuel_data is None:
                missing_data.append("Fuel card data")
            if st.session_state.job_data is None:
                missing_data.append("Job logs")
            
            if missing_data:
                st.write(f"**Optional:** Upload {', '.join(missing_data)} for additional violation types")
            
            # Audit configuration
            st.subheader("⚙️ Audit Parameters")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Fuel Theft Detection**")
                fuel_distance_threshold = st.slider(
                    "Distance threshold (miles)",
                    min_value=0.5, max_value=5.0, value=1.0, step=0.5,
                    help="Maximum distance from fuel purchase location"
                )
                fuel_time_threshold = st.slider(
                    "Time window (minutes)",
                    min_value=5, max_value=60, value=15, step=5,
                    help="Time window around fuel purchase"
                )
                
                st.write("**Idle Abuse Detection**")
                idle_time_threshold = st.slider(
                    "Minimum idle time (minutes)",
                    min_value=5, max_value=60, value=10, step=5,
                    help="Minimum time to consider as excessive idling"
                )
            
            with col2:
                st.write("**Ghost Job Detection**")
                job_distance_threshold = st.slider(
                    "Job site radius (miles)",
                    min_value=0.1, max_value=2.0, value=0.5, step=0.1,
                    help="Required proximity to job site"
                )
                job_time_buffer = st.slider(
                    "Time buffer (minutes)",
                    min_value=15, max_value=120, value=30, step=15,
                    help="Time window around scheduled job"
                )
                
                st.write("**Business Hours**")
                business_start = st.time_input("Start time", value=datetime.strptime("07:00", "%H:%M").time())
                business_end = st.time_input("End time", value=datetime.strptime("18:00", "%H:%M").time())
            
            # Run audit button
            if st.button("🚀 Run Fleet Audit", type="primary", use_container_width=True):
                with st.spinner("Running fleet audit... This may take a few moments."):
                    try:
                        # Initialize auditor
                        auditor = FleetAuditor()
                        auditor.load_data(
                            st.session_state.gps_data,
                            st.session_state.fuel_data,
                            st.session_state.job_data
                        )
                        
                        # Run audit with custom parameters
                        audit_results = auditor.run_full_audit()
                        summary_stats = auditor.get_summary_stats()
                        
                        # Store results in session state
                        st.session_state.audit_results = audit_results
                        st.session_state.summary_stats = summary_stats
                        st.session_state.auditor = auditor
                        
                        st.success("✅ Audit completed successfully!")
                        
                        # Show quick summary
                        total_violations = summary_stats.get('total_violations', 0)
                        
                        if total_violations > 0:
                            st.warning(f"⚠️ Found {total_violations} potential violations")
                        else:
                            st.success("🎉 No violations detected!")
                        
                    except Exception as e:
                        st.error(f"❌ Error running audit: {str(e)}")
                        st.error("**Debug Info:**")
                        st.code(traceback.format_exc())
    
    with tab3:
        st.header("📊 Audit Results")
        
        if st.session_state.audit_results is None:
            st.info("No audit results available. Please run an audit first.")
        else:
            results = st.session_state.audit_results
            summary = st.session_state.summary_stats
            
            # Summary metrics
            st.subheader("📈 Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Violations",
                    summary.get('total_violations', 0),
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Vehicles Flagged",
                    summary.get('vehicles_with_violations', 0),
                    delta=None
                )
            
            with col3:
                st.metric(
                    "Fuel Theft",
                    len(results.get('fuel_theft', [])),
                    delta=None
                )
            
            with col4:
                st.metric(
                    "Ghost Jobs",
                    len(results.get('ghost_jobs', [])),
                    delta=None
                )
            
            # Detailed results
            st.subheader("🔍 Detailed Violations")
            
            for violation_type, violations in results.items():
                if violations:
                    violation_names = {
                        'fuel_theft': '🚨 Potential Fuel Theft',
                        'ghost_jobs': '👻 Ghost Jobs',
                        'idle_abuse': '⏰ Excessive Idling',
                        'after_hours_driving': '🌙 After Hours Activity'
                    }
                    
                    with st.expander(f"{violation_names.get(violation_type, violation_type)} ({len(violations)} incidents)"):
                        violations_df = pd.DataFrame(violations)
                        st.dataframe(violations_df, use_container_width=True)
    
    with tab4:
        st.header("📧 Generate & Send Report")
        
        if st.session_state.audit_results is None:
            st.info("No audit results available. Please run an audit first.")
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Report Preview")
                
                # Generate report preview
                try:
                    generator = ReportGenerator()
                    html_preview = generator.generate_html_report(
                        st.session_state.audit_results,
                        st.session_state.summary_stats,
                        st.session_state.company_name,
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    # Show HTML preview in an iframe or container
                    st.components.v1.html(html_preview, height=600, scrolling=True)
                    
                except Exception as e:
                    st.error(f"Error generating report preview: {str(e)}")
            
            with col2:
                st.subheader("Actions")
                
                # Generate Report button
                if st.button("📄 Generate Report", type="primary", use_container_width=True):
                    with st.spinner("Generating report..."):
                        try:
                            generator = ReportGenerator()
                            report_path = generator.generate_pdf_report(
                                st.session_state.audit_results,
                                st.session_state.summary_stats,
                                st.session_state.company_name,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d')
                            )
                            
                            st.session_state.report_path = report_path
                            
                            # Check if it's HTML or PDF
                            is_html = report_path.endswith('.html')
                            file_type = "HTML" if is_html else "PDF"
                            
                            st.success(f"✅ {file_type} report generated!")
                            
                            # Provide download link
                            with open(report_path, "rb") as report_file:
                                file_extension = "html" if is_html else "pdf"
                                mime_type = "text/html" if is_html else "application/pdf"
                                
                                st.download_button(
                                    label=f"📥 Download {file_type} Report",
                                    data=report_file.read(),
                                    file_name=f"fleet_audit_report_{datetime.now().strftime('%Y%m%d')}.{file_extension}",
                                    mime=mime_type,
                                    use_container_width=True
                                )
                        
                        except Exception as e:
                            st.error(f"Error generating report: {str(e)}")
                
                st.divider()
                
                # Email report section
                if st.session_state.report_path and recipient_email:
                    if st.button("📧 Email Report", type="secondary", use_container_width=True):
                        with st.spinner("Sending email..."):
                            try:
                                sender = EmailSender(email_provider)
                                success = sender.send_report_email(
                                    recipient_email,
                                    st.session_state.company_name,
                                    st.session_state.report_path
                                )
                                
                                if success:
                                    st.success(f"✅ Report sent to {recipient_email}")
                                else:
                                    st.error("❌ Failed to send email")
                            
                            except Exception as e:
                                st.error(f"Error sending email: {str(e)}")
                
                elif not recipient_email:
                    st.info("📧 Set recipient email in sidebar to send reports")
                elif not st.session_state.report_path:
                    st.info("📄 Generate report first")

if __name__ == "__main__":
    main()