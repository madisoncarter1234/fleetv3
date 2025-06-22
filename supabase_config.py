import os
from supabase import create_client, Client
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime

class SupabaseConfig:
    """Supabase integration for authentication and data storage"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(self.url, self.key)
    
    def create_tables(self):
        """Create necessary tables for FleetAudit (run once during setup)"""
        
        # Users table (handled by Supabase Auth)
        
        # Companies table
        companies_sql = """
        CREATE TABLE IF NOT EXISTS companies (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Audit runs table
        audit_runs_sql = """
        CREATE TABLE IF NOT EXISTS audit_runs (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            company_id UUID REFERENCES companies(id),
            user_id UUID REFERENCES auth.users(id),
            start_date DATE,
            end_date DATE,
            total_violations INTEGER DEFAULT 0,
            report_path TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Violations table
        violations_sql = """
        CREATE TABLE IF NOT EXISTS violations (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            audit_run_id UUID REFERENCES audit_runs(id),
            violation_type TEXT NOT NULL,
            vehicle_id TEXT,
            driver_id TEXT,
            timestamp TIMESTAMP WITH TIME ZONE,
            description TEXT,
            severity TEXT DEFAULT 'medium',
            resolved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        try:
            # Execute table creation (this would typically be done via Supabase dashboard)
            print("Tables should be created via Supabase dashboard SQL editor")
            print("Companies table SQL:", companies_sql)
            print("Audit runs table SQL:", audit_runs_sql)
            print("Violations table SQL:", violations_sql)
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with Supabase Auth"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None
    
    def register_user(self, email: str, password: str) -> Optional[Dict]:
        """Register new user"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return response
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return None
    
    def get_user(self) -> Optional[Dict]:
        """Get current authenticated user"""
        try:
            return self.supabase.auth.get_user()
        except Exception as e:
            print(f"Get user error: {str(e)}")
            return None
    
    def sign_out(self):
        """Sign out current user"""
        try:
            self.supabase.auth.sign_out()
        except Exception as e:
            print(f"Sign out error: {str(e)}")
    
    def create_company(self, name: str) -> Optional[str]:
        """Create a new company record"""
        try:
            response = self.supabase.table("companies").insert({
                "name": name
            }).execute()
            
            if response.data:
                return response.data[0]['id']
            return None
        except Exception as e:
            print(f"Error creating company: {str(e)}")
            return None
    
    def get_companies(self, user_id: str) -> List[Dict]:
        """Get companies for a user"""
        try:
            response = self.supabase.table("companies").select("*").execute()
            return response.data or []
        except Exception as e:
            print(f"Error fetching companies: {str(e)}")
            return []
    
    def save_audit_run(self, company_id: str, user_id: str, 
                       start_date: str, end_date: str, 
                       total_violations: int, report_path: str = None) -> Optional[str]:
        """Save audit run results"""
        try:
            response = self.supabase.table("audit_runs").insert({
                "company_id": company_id,
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
                "total_violations": total_violations,
                "report_path": report_path
            }).execute()
            
            if response.data:
                return response.data[0]['id']
            return None
        except Exception as e:
            print(f"Error saving audit run: {str(e)}")
            return None
    
    def save_violations(self, audit_run_id: str, violations: List[Dict]) -> bool:
        """Save violation records"""
        try:
            # Prepare violations for database
            db_violations = []
            for violation in violations:
                db_violations.append({
                    "audit_run_id": audit_run_id,
                    "violation_type": violation.get('violation_type'),
                    "vehicle_id": violation.get('vehicle_id'),
                    "driver_id": violation.get('driver_id'),
                    "timestamp": violation.get('timestamp').isoformat() if violation.get('timestamp') else None,
                    "description": violation.get('description', ''),
                    "severity": violation.get('severity', 'medium')
                })
            
            response = self.supabase.table("violations").insert(db_violations).execute()
            return len(response.data) > 0 if response.data else False
        except Exception as e:
            print(f"Error saving violations: {str(e)}")
            return False
    
    def get_audit_history(self, company_id: str, limit: int = 50) -> List[Dict]:
        """Get audit run history for a company"""
        try:
            response = self.supabase.table("audit_runs").select("*").eq(
                "company_id", company_id
            ).order("created_at", desc=True).limit(limit).execute()
            
            return response.data or []
        except Exception as e:
            print(f"Error fetching audit history: {str(e)}")
            return []
    
    def get_violations_by_audit(self, audit_run_id: str) -> List[Dict]:
        """Get violations for a specific audit run"""
        try:
            response = self.supabase.table("violations").select("*").eq(
                "audit_run_id", audit_run_id
            ).order("created_at", desc=True).execute()
            
            return response.data or []
        except Exception as e:
            print(f"Error fetching violations: {str(e)}")
            return []
    
    def upload_file(self, bucket: str, file_path: str, file_data: bytes) -> Optional[str]:
        """Upload file to Supabase Storage"""
        try:
            response = self.supabase.storage.from_(bucket).upload(
                file_path, file_data
            )
            
            if response:
                # Get public URL
                public_url = self.supabase.storage.from_(bucket).get_public_url(file_path)
                return public_url
            return None
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return None
    
    def download_file(self, bucket: str, file_path: str) -> Optional[bytes]:
        """Download file from Supabase Storage"""
        try:
            response = self.supabase.storage.from_(bucket).download(file_path)
            return response
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return None

# Streamlit integration helpers
def get_supabase_client():
    """Get configured Supabase client for Streamlit"""
    try:
        return SupabaseConfig()
    except Exception as e:
        print(f"Supabase not configured: {str(e)}")
        return None

def init_supabase_session(st):
    """Initialize Supabase session state for Streamlit"""
    if 'supabase_client' not in st.session_state:
        st.session_state.supabase_client = get_supabase_client()
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'company_id' not in st.session_state:
        st.session_state.company_id = None