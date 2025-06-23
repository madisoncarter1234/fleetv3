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
from logic.ai_violation_insights import AIViolationInsights

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
    with st.expander("ℹ️ How FleetAudit.io works - simple and automatic"):
        st.write("""
        **🤖 Step 1: Upload Fuel CSV** (any format - AI handles it automatically)
        - **Auto-Detection:** AI reads any fuel card format (WEX, Fleetcor, etc.)
        - **Enhanced Theft Detection:** Volume analysis, price validation, pattern detection
        - **Statistical Analysis:** Timing, frequency, and location anomalies
        
        **🚨 Step 2: Add GPS Data** (optional but recommended for maximum protection)
        - **Location Validation:** Confirms vehicle was actually at gas station
        - **Stolen Card Detection:** Fuel purchases without truck present
        - **MPG Fraud Detection:** Catches odometer manipulation and fuel dumping
        - **After-Hours Monitoring:** Unauthorized vehicle use detection
        
        **👻 Step 3: Add Job Data** (optional for route verification)
        - **Ghost Job Detection:** Confirms vehicles visited assigned locations
        - **Route Validation:** Matches job schedules with actual GPS routes
        
        **💡 Tip:** Enhanced fuel detection works with just fuel card data and catches theft that GPS-based systems miss!
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
            
            with st.expander("ℹ️ What fuel card data works best?"):
                st.write("""
                **✅ Fleet fuel cards** (WEX, FleetCor, Fuelman):
                • Include gallons + dollar amounts
                • Best detection (95% confidence)
                • Track fuel consumption automatically
                
                **⚠️ Regular credit cards:**
                • Only dollar amounts (no gallons)
                • Limited detection (estimated volumes)
                • May miss some theft patterns
                
                **💡 Most fleet fuel card systems export gallons data** - check your online portal for "transaction export" or "detailed reports"
                """)
            
            # Simplified - always use AI parsing, no options needed
            
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
                    
                    # FUCK THE MANUAL LOGIC - 100% AI EVERYTHING
                    from parsers.ai_only_parser import AIOnlyParser
                    ai_parser = AIOnlyParser()
                    ai_result = ai_parser.parse_and_detect_violations(tmp_path)
                    
                    if 'dataframe' in ai_result and len(ai_result['dataframe']) > 0:
                        fuel_data = ai_result['dataframe']
                        # Store AI violations for display
                        st.session_state.ai_violations = ai_result.get('violations', [])
                        st.session_state.ai_summary = ai_result.get('summary', {})
                    else:
                        # Fallback to old method only if AI completely fails
                        fuel_data = FuelParser.parse_with_ai(tmp_path)
                        st.session_state.ai_violations = []
                        st.session_state.ai_summary = {}
                    
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
            
            # Initialize auditor to check for date overlap issues
            auditor = FleetAuditor()
            auditor.load_data(
                gps_df=st.session_state.gps_data,
                fuel_df=st.session_state.fuel_data,
                job_df=st.session_state.job_data
            )
            
            # Check for overlap warnings
            overlap_warnings = auditor.get_overlap_warnings()
            if overlap_warnings:
                st.warning("⚠️ **Data Time Period Issues Detected:**")
                for warning in overlap_warnings:
                    if warning['type'] == 'no_overlap':
                        sources = ' and '.join([s.upper() for s in warning['sources']])
                        st.error(f"❌ **{sources} data are from different time periods** - Upload matching dates to cross-check for violations")
                    elif warning['type'] == 'limited_overlap':
                        sources = ' and '.join([s.upper() for s in warning['sources']])
                        st.warning(f"⚠️ **{sources} data barely overlap** - Detection will be limited to common time period")
                
                with st.expander("📅 View Data Date Ranges"):
                    for source, date_info in auditor.date_ranges.items():
                        st.write(f"**{source.upper()}:** {date_info['start'].strftime('%Y-%m-%d')} to {date_info['end'].strftime('%Y-%m-%d')} ({date_info['count']} records)")
            
            # Show which violation types can be detected
            available_violations = []
            
            # Check what's possible with current data
            if st.session_state.gps_data is not None and st.session_state.fuel_data is not None:
                available_violations.append("🚨 Fuel theft detection")
                
            if st.session_state.gps_data is not None and st.session_state.job_data is not None:
                available_violations.append("👻 Ghost job detection")
                
            if st.session_state.gps_data is not None:
                available_violations.append("⏰ Idle time abuse")
                available_violations.append("🌙 After-hours driving")
            
            if available_violations:
                st.success(f"**Ready to detect:** {', '.join(available_violations)}")
                
                # Show fuel data quality if fuel data is loaded
                if st.session_state.fuel_data is not None:
                    from logic.enhanced_fuel_detector import EnhancedFuelDetector
                    detector = EnhancedFuelDetector()
                    quality_summary = detector.get_data_quality_summary(st.session_state.fuel_data)
                    
                    with st.expander("📊 Fuel Data Quality Assessment"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Data Tier:** {quality_summary['data_tier']}/4")
                            st.write(f"**Quality:** {quality_summary['description']}")
                            st.write(f"**Records:** {quality_summary['total_records']}")
                        
                        with col2:
                            if quality_summary.get('improvement_suggestions'):
                                st.write("**💡 To improve detection:**")
                                for suggestion in quality_summary['improvement_suggestions'][:2]:
                                    st.write(f"• {suggestion}")
                                    
                        if quality_summary['data_tier'] < 4:
                            confidence = int(quality_summary['confidence_multiplier'] * 100)
                            st.info(f"Current detection confidence: {confidence}% - {quality_summary['description']}")
            
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
                
                # Simplified - automatically run all available detections
                if st.session_state.fuel_data is not None:
                    st.success("**🔍 Automatic Detection Enabled:**")
                    if st.session_state.gps_data is not None:
                        st.info("🚨 **Fuel + GPS**: Theft detection, location validation, MPG fraud, pattern analysis")
                    else:
                        st.info("⛽ **Fuel Only**: Enhanced theft detection, pattern analysis, volume anomalies")
            
            # Run audit button
            if st.button("🚀 Run Fleet Audit", type="primary", use_container_width=True):
                with st.spinner("Running fleet audit... This may take a few moments."):
                    try:
                        # Use the auditor we already initialized above
                        # (it already has the data loaded and overlap analysis done)
                        
                        # Use AI violations if available, otherwise run manual audit
                        if hasattr(st.session_state, 'ai_violations') and st.session_state.ai_violations:
                            # Use pure AI results
                            audit_results = {
                                'consolidated_violations': st.session_state.ai_violations,
                                'financial_summary': {
                                    'total_fleet_loss': len(st.session_state.ai_violations) * 50,  # Estimate $50 per violation
                                    'vehicles_flagged': len(set(v.get('vehicle_id') for v in st.session_state.ai_violations)),
                                    'weekly_fleet_estimate': len(st.session_state.ai_violations) * 50 * 52 / 12  # Rough weekly estimate
                                },
                                'ai_summary': st.session_state.ai_summary
                            }
                        else:
                            # Fallback to manual audit logic
                            has_fuel = st.session_state.fuel_data is not None
                            has_gps = st.session_state.gps_data is not None
                            
                            audit_results = auditor.run_full_audit(
                                enable_fuel_only_analysis=has_fuel and not has_gps,
                                enable_enhanced_fuel_detection=has_fuel,
                                enable_mpg_analysis=has_fuel and has_gps
                            )
                        
                        # Skip AI violation insights - keep it lightweight and fast
                        # AI is only used for CSV parsing, violations are detected by fast logic
                        
                        # Store results in session state
                        st.session_state.audit_results = audit_results
                        st.session_state.auditor = auditor
                        
                        st.success("✅ Comprehensive audit completed successfully!")
                        
                        # Show financial impact summary
                        financial_summary = audit_results.get('financial_summary', {})
                        consolidated_violations = audit_results.get('consolidated_violations', [])
                        
                        if consolidated_violations:
                            total_loss = financial_summary.get('total_fleet_loss', 0)
                            vehicles_flagged = financial_summary.get('vehicles_flagged', 0)
                            
                            st.error(f"⚠️ **{len(consolidated_violations)} incidents detected** affecting {vehicles_flagged} vehicles")
                            if total_loss > 0:
                                weekly_estimate = financial_summary.get('weekly_fleet_estimate', 0)
                                st.error(f"💰 **Estimated financial impact: ${total_loss:.2f}** (${weekly_estimate:.2f}/week)")
                        else:
                            st.success("🎉 No violations detected!")
                        
                    except Exception as e:
                        st.error(f"❌ Error running audit: {str(e)}")
                        st.error("**Debug Info:**")
                        st.code(traceback.format_exc())
    
    with tab3:
        st.header("📊 Comprehensive Audit Results")
        
        if st.session_state.audit_results is None:
            st.info("No audit results available. Please run an audit first.")
        else:
            results = st.session_state.audit_results
            financial_summary = results.get('financial_summary', {})
            consolidated_violations = results.get('consolidated_violations', [])
            
            # Financial Impact Summary
            if financial_summary:
                st.subheader("💰 Financial Impact Analysis")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Fleet Loss",
                        f"${financial_summary.get('total_fleet_loss', 0):.2f}",
                        delta=None
                    )
                
                with col2:
                    st.metric(
                        "Weekly Estimate",
                        f"${financial_summary.get('weekly_fleet_estimate', 0):.2f}",
                        delta=None
                    )
                
                with col3:
                    st.metric(
                        "Incidents Detected",
                        len(consolidated_violations),
                        delta=None
                    )
                
                with col4:
                    st.metric(
                        "Vehicles Flagged",
                        financial_summary.get('vehicles_flagged', 0),
                        delta=None
                    )
                
                # Vehicle-specific financial impact
                vehicle_summaries = financial_summary.get('vehicle_summaries', {})
                if vehicle_summaries:
                    st.subheader("🚗 Per-Vehicle Financial Impact")
                    
                    for vehicle_id, summary in vehicle_summaries.items():
                        with st.expander(f"**{vehicle_id}** - ${summary['total_loss']:.2f} total loss"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**Total Loss:** ${summary['total_loss']:.2f}")
                                st.write(f"**Violations:** {summary['violation_count']}")
                            
                            with col2:
                                st.write(f"**Weekly Est:** ${summary['weekly_estimate']:.2f}")
                                st.write(f"**Monthly Est:** ${summary['monthly_estimate']:.2f}")
                            
                            with col3:
                                st.write(f"**Worst Incident:** ${summary['highest_single_incident']:.2f}")
                                st.write(f"**Detection Methods:** {len(summary['violation_methods'])}")
                            
                            st.info(summary['summary_text'])
            
            # Consolidated Violations
            if consolidated_violations:
                st.subheader("🔍 Incident Details")
                
                # Group by severity
                high_severity = [v for v in consolidated_violations if v.get('severity') == 'high']
                medium_severity = [v for v in consolidated_violations if v.get('severity') == 'medium']
                low_severity = [v for v in consolidated_violations if v.get('severity') == 'low']
                
                if high_severity:
                    with st.expander(f"🚨 **HIGH SEVERITY** ({len(high_severity)} incidents)", expanded=True):
                        for violation in high_severity:
                            _display_violation_card(violation)
                
                if medium_severity:
                    with st.expander(f"⚠️ **MEDIUM SEVERITY** ({len(medium_severity)} incidents)", expanded=False):
                        for violation in medium_severity:
                            _display_violation_card(violation)
                
                if low_severity:
                    with st.expander(f"ℹ️ **LOW SEVERITY** ({len(low_severity)} incidents)", expanded=False):
                        for violation in low_severity:
                            _display_violation_card(violation)
            
            # Raw data view for debugging
            if st.checkbox("🔧 Show raw audit data (debug)"):
                raw_violations = results.get('raw_violations', {})
                for violation_type, violations in raw_violations.items():
                    if violations:
                        with st.expander(f"Raw {violation_type} ({len(violations)} items)"):
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
                    
                    # Create summary stats from new audit results structure
                    financial_summary = st.session_state.audit_results.get('financial_summary', {})
                    consolidated_violations = st.session_state.audit_results.get('consolidated_violations', [])
                    
                    summary_stats = {
                        'total_violations': len(consolidated_violations),
                        'vehicles_with_violations': financial_summary.get('vehicles_flagged', 0),
                        'violations_by_type': {},
                        'date_range': {
                            'start': start_date,
                            'end': end_date
                        }
                    }
                    
                    # Count violations by type
                    for violation in consolidated_violations:
                        v_type = violation.get('violation_type', 'unknown')
                        summary_stats['violations_by_type'][v_type] = summary_stats['violations_by_type'].get(v_type, 0) + 1
                    
                    html_preview = generator.generate_html_report(
                        st.session_state.audit_results,
                        summary_stats,
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
                            
                            # Create summary stats from new audit results structure
                            financial_summary = st.session_state.audit_results.get('financial_summary', {})
                            consolidated_violations = st.session_state.audit_results.get('consolidated_violations', [])
                            
                            summary_stats = {
                                'total_violations': len(consolidated_violations),
                                'vehicles_with_violations': financial_summary.get('vehicles_flagged', 0),
                                'violations_by_type': {},
                                'date_range': {
                                    'start': start_date,
                                    'end': end_date
                                }
                            }
                            
                            # Count violations by type
                            for violation in consolidated_violations:
                                v_type = violation.get('violation_type', 'unknown')
                                summary_stats['violations_by_type'][v_type] = summary_stats['violations_by_type'].get(v_type, 0) + 1
                            
                            report_path = generator.generate_pdf_report(
                                st.session_state.audit_results,
                                summary_stats,
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

def _display_violation_card(violation):
    """Display a violation in a formatted card"""
    
    # Calculate color based on severity and confidence
    severity = violation.get('severity', 'low')
    confidence = violation.get('confidence', 0) * 100
    
    if severity == 'high':
        color = "#ff4444"
    elif severity == 'medium':
        color = "#ff8800"
    else:
        color = "#ffaa00"
    
    st.markdown(f"""
    <div style="border-left: 4px solid {color}; padding: 1rem; margin: 0.5rem 0; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h4 style="margin: 0 0 0.5rem 0;">{violation['vehicle_id']} - {str(violation.get('detection_method', 'Unknown')).replace('_', ' ').title()}</h4>
        <p style="margin: 0 0 0.5rem 0;"><strong>Time:</strong> {violation['timestamp']}</p>
        <p style="margin: 0 0 0.5rem 0;"><strong>Location:</strong> {violation.get('location', 'Unknown')}</p>
        <p style="margin: 0 0 1rem 0;">{violation.get('description', 'No description available')}</p>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span><strong>Confidence:</strong> {confidence:.0f}%</span>
            <span><strong>Estimated Loss:</strong> ${violation.get('total_estimated_loss', 0):.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()