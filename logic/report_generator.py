import os
import pandas as pd
from datetime import datetime, timedelta
from jinja2 import Template, Environment, FileSystemLoader
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from typing import Dict, List, Optional
import tempfile

class ReportGenerator:
    """Generate HTML and PDF reports from audit results"""
    
    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def generate_html_report(self, audit_results: Dict, summary_stats: Dict, 
                           company_name: str = "Fleet Company", 
                           start_date: str = None, end_date: str = None) -> str:
        """Generate HTML report from audit results"""
        
        # Set default date range if not provided
        if start_date is None or end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        template = self.env.get_template('report.html')
        
        # Prepare context for template
        context = {
            'company_name': company_name,
            'start_date': start_date,
            'end_date': end_date,
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'violations': audit_results,
            'summary_stats': summary_stats
        }
        
        return template.render(context)
    
    def generate_pdf_report(self, audit_results: Dict, summary_stats: Dict,
                           company_name: str = "Fleet Company",
                           start_date: str = None, end_date: str = None,
                           output_path: str = None) -> str:
        """Generate PDF report from audit results"""
        
        # Generate HTML first
        html_content = self.generate_html_report(
            audit_results, summary_stats, company_name, start_date, end_date
        )
        
        # Set output path
        if output_path is None:
            reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(reports_dir, f'fleet_audit_report_{timestamp}.pdf')
        
        # Convert HTML to PDF
        try:
            font_config = FontConfiguration()
            html_doc = HTML(string=html_content)
            html_doc.write_pdf(output_path, font_config=font_config)
            return output_path
        except Exception as e:
            # Fallback: save as HTML if PDF generation fails
            html_output_path = output_path.replace('.pdf', '.html')
            with open(html_output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            raise Exception(f"PDF generation failed: {str(e)}. HTML saved to {html_output_path}")
    
    def create_weekly_report(self, auditor, company_name: str = "Fleet Company") -> str:
        """Create a complete weekly report from FleetAuditor results"""
        
        if not auditor.violations:
            raise ValueError("No audit results available. Run audit first.")
        
        # Get audit results and summary
        audit_results = auditor.run_full_audit()
        summary_stats = auditor.get_summary_stats()
        
        # Generate PDF
        return self.generate_pdf_report(audit_results, summary_stats, company_name)
    
    def preview_report_html(self, audit_results: Dict, summary_stats: Dict,
                           company_name: str = "Fleet Company") -> str:
        """Generate HTML for preview purposes (no PDF)"""
        return self.generate_html_report(audit_results, summary_stats, company_name)

def create_sample_report():
    """Create a sample report for testing"""
    
    # Sample data
    sample_violations = {
        'fuel_theft': [
            {
                'vehicle_id': 'TRUCK-001',
                'timestamp': datetime(2024, 1, 15, 14, 30),
                'location': 'Shell Station - Main St',
                'gallons': 25.5,
                'description': 'Fuel purchase of 25.5 gallons with no GPS activity within 1 miles and 15 minutes'
            }
        ],
        'ghost_jobs': [
            {
                'job_id': 'JOB-2024-001',
                'driver_id': 'DRIVER-003',
                'scheduled_time': datetime(2024, 1, 16, 9, 0),
                'address': '123 Customer Ave, City, ST',
                'description': 'No GPS activity found near job site during scheduled time window'
            }
        ],
        'idle_abuse': [
            {
                'vehicle_id': 'TRUCK-002',
                'start_time': datetime(2024, 1, 17, 11, 15),
                'end_time': datetime(2024, 1, 17, 11, 45),
                'duration_minutes': 30.0,
                'description': 'Vehicle was idle for extended period'
            }
        ],
        'after_hours_driving': [
            {
                'vehicle_id': 'TRUCK-001',
                'date': datetime(2024, 1, 18).date(),
                'first_violation_time': datetime(2024, 1, 18, 22, 30),
                'last_violation_time': datetime(2024, 1, 18, 23, 45),
                'total_records': 15,
                'description': 'Vehicle activity detected outside authorized hours'
            }
        ]
    }
    
    sample_summary = {
        'total_violations': 4,
        'violations_by_type': {
            'fuel_theft': 1,
            'ghost_jobs': 1,  
            'idle_abuse': 1,
            'after_hours_driving': 1
        },
        'vehicles_with_violations': 2,
        'date_range': {
            'start': datetime(2024, 1, 15),
            'end': datetime(2024, 1, 18)
        }
    }
    
    # Generate report
    generator = ReportGenerator()
    report_path = generator.generate_pdf_report(
        sample_violations, sample_summary, 
        company_name="Sample Fleet Company"
    )
    
    return report_path

if __name__ == "__main__":
    # Generate sample report for testing
    sample_path = create_sample_report()
    print(f"Sample report generated: {sample_path}")