import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

class JobParser:
    """Parser for job scheduling data from various providers"""
    
    @staticmethod
    def parse_jobber(file_path: str) -> pd.DataFrame:
        """Parse Jobber job export CSV"""
        # Handle both CSV and Excel files
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # Map Jobber column names to normalized format
        column_mapping = {
            'Job Number': 'job_id',
            'Scheduled Start': 'scheduled_time',
            'Address': 'address',
            'Assigned To': 'driver_id',
            'Job Status': 'status',
            'Client Name': 'client_name'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Convert scheduled_time to datetime
        if 'scheduled_time' in df.columns:
            df['scheduled_time'] = pd.to_datetime(df['scheduled_time'])
        
        # Ensure required columns exist
        required_cols = ['job_id', 'scheduled_time', 'address', 'driver_id']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        return df[required_cols]
    
    @staticmethod
    def parse_housecall_pro(file_path: str) -> pd.DataFrame:
        """Parse Housecall Pro job export CSV"""
        # Handle both CSV and Excel files
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # Map Housecall Pro column names to normalized format
        column_mapping = {
            'Job ID': 'job_id',
            'Start Time': 'scheduled_time',
            'Service Address': 'address',
            'Technician': 'driver_id',
            'Status': 'status',
            'Customer': 'client_name'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Convert scheduled_time to datetime
        if 'scheduled_time' in df.columns:
            df['scheduled_time'] = pd.to_datetime(df['scheduled_time'])
        
        # Ensure required columns exist
        required_cols = ['job_id', 'scheduled_time', 'address', 'driver_id']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        return df[required_cols]
    
    @staticmethod
    def parse_servicetitan(file_path: str) -> pd.DataFrame:
        """Parse ServiceTitan job export CSV"""
        # Handle both CSV and Excel files
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # Map ServiceTitan column names to normalized format
        column_mapping = {
            'Job Number': 'job_id',
            'Appointment Start': 'scheduled_time',
            'Location Address': 'address',
            'Technician Name': 'driver_id',
            'Job Status': 'status',
            'Customer Name': 'client_name'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Convert scheduled_time to datetime
        if 'scheduled_time' in df.columns:
            df['scheduled_time'] = pd.to_datetime(df['scheduled_time'])
        
        # Ensure required columns exist
        required_cols = ['job_id', 'scheduled_time', 'address', 'driver_id']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        return df[required_cols]
    
    @staticmethod
    def auto_parse(file_path: str, provider: str = None) -> pd.DataFrame:
        """Auto-detect and parse job data based on provider or column headers"""
        
        # Read first few rows to detect format
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            sample_df = pd.read_excel(file_path, nrows=5)
        else:
            sample_df = pd.read_csv(file_path, nrows=5)
        
        if provider == 'jobber' or 'Job Number' in sample_df.columns:
            return JobParser.parse_jobber(file_path)
        elif provider == 'housecall_pro' or 'Job ID' in sample_df.columns:
            return JobParser.parse_housecall_pro(file_path)
        elif provider == 'servicetitan' or 'Appointment Start' in sample_df.columns:
            return JobParser.parse_servicetitan(file_path)
        else:
            # Try generic parsing
            return JobParser.parse_generic(file_path)
    
    @staticmethod
    def parse_generic(file_path: str) -> pd.DataFrame:
        """Generic parser for unknown job scheduling formats"""
        # Handle both CSV and Excel files
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # Try to map common column patterns
        job_id_cols = ['job_id', 'job_number', 'job', 'id', 'ticket_number']
        scheduled_cols = ['scheduled_time', 'start_time', 'appointment_start', 'scheduled_start']
        address_cols = ['address', 'service_address', 'location', 'location_address']
        driver_cols = ['driver_id', 'technician', 'assigned_to', 'driver', 'tech_name']
        
        def find_column(df, possible_names):
            for col in df.columns:
                if col.lower().replace(' ', '_') in [name.lower() for name in possible_names]:
                    return col
            return None
        
        # Find matching columns
        job_id_col = find_column(df, job_id_cols)
        scheduled_col = find_column(df, scheduled_cols)
        address_col = find_column(df, address_cols)
        driver_col = find_column(df, driver_cols)
        
        # Create normalized dataframe
        normalized_df = pd.DataFrame()
        
        if job_id_col:
            normalized_df['job_id'] = df[job_id_col]
        if scheduled_col:
            normalized_df['scheduled_time'] = pd.to_datetime(df[scheduled_col])
        if address_col:
            normalized_df['address'] = df[address_col]
        if driver_col:
            normalized_df['driver_id'] = df[driver_col]
        
        # Fill missing columns with None
        required_cols = ['job_id', 'scheduled_time', 'address', 'driver_id']
        for col in required_cols:
            if col not in normalized_df.columns:
                normalized_df[col] = None
        
        return normalized_df[required_cols]