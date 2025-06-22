import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

class FuelParser:
    """Parser for fuel card data from various providers"""
    
    @staticmethod
    def parse_wex(file_path: str) -> pd.DataFrame:
        """Parse WEX fuel card export CSV"""
        df = pd.read_csv(file_path)
        
        # Map WEX column names to normalized format
        column_mapping = {
            'Transaction Date': 'timestamp',
            'Site Name': 'location',
            'Gallons': 'gallons',
            'Vehicle Number': 'vehicle_id',
            'Card Number': 'card_id',
            'Amount': 'amount'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Ensure required columns exist
        required_cols = ['timestamp', 'location', 'gallons', 'vehicle_id']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        return df[required_cols]
    
    @staticmethod
    def parse_fleetcor(file_path: str) -> pd.DataFrame:
        """Parse Fleetcor fuel card export CSV"""
        df = pd.read_csv(file_path)
        
        # Map Fleetcor column names to normalized format
        column_mapping = {
            'Date': 'timestamp',
            'Merchant Name': 'location',
            'Fuel Quantity': 'gallons',
            'Vehicle': 'vehicle_id',
            'Card': 'card_id',
            'Total Amount': 'amount'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Ensure required columns exist
        required_cols = ['timestamp', 'location', 'gallons', 'vehicle_id']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        return df[required_cols]
    
    @staticmethod
    def parse_fuelman(file_path: str) -> pd.DataFrame:
        """Parse Fuelman fuel card export CSV"""
        df = pd.read_csv(file_path)
        
        # Map Fuelman column names to normalized format
        column_mapping = {
            'Trans Date': 'timestamp',
            'Location': 'location',
            'Quantity': 'gallons',
            'Unit Number': 'vehicle_id',
            'Card': 'card_id',
            'Net Amount': 'amount'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Ensure required columns exist
        required_cols = ['timestamp', 'location', 'gallons', 'vehicle_id']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        return df[required_cols]
    
    @staticmethod
    def auto_parse(file_path: str, provider: str = None) -> pd.DataFrame:
        """Auto-detect and parse fuel data based on provider or column headers"""
        
        # Read first few rows to detect format
        sample_df = pd.read_csv(file_path, nrows=5)
        
        if provider == 'wex' or 'Transaction Date' in sample_df.columns:
            return FuelParser.parse_wex(file_path)
        elif provider == 'fleetcor' or 'Merchant Name' in sample_df.columns:
            return FuelParser.parse_fleetcor(file_path)
        elif provider == 'fuelman' or 'Trans Date' in sample_df.columns:
            return FuelParser.parse_fuelman(file_path)
        else:
            # Try generic parsing
            return FuelParser.parse_generic(file_path)
    
    @staticmethod
    def parse_generic(file_path: str) -> pd.DataFrame:
        """Generic parser for unknown fuel card formats"""
        df = pd.read_csv(file_path)
        
        # Try to map common column patterns
        timestamp_cols = ['timestamp', 'date', 'transaction_date', 'trans_date']
        location_cols = ['location', 'site', 'merchant', 'station', 'site_name']
        gallons_cols = ['gallons', 'quantity', 'fuel_quantity', 'volume']
        vehicle_cols = ['vehicle_id', 'vehicle', 'unit', 'vehicle_number', 'unit_number']
        
        def find_column(df, possible_names):
            for col in df.columns:
                if col.lower().replace(' ', '_') in [name.lower() for name in possible_names]:
                    return col
            return None
        
        # Find matching columns
        timestamp_col = find_column(df, timestamp_cols)
        location_col = find_column(df, location_cols)
        gallons_col = find_column(df, gallons_cols)
        vehicle_col = find_column(df, vehicle_cols)
        
        # Create normalized dataframe
        normalized_df = pd.DataFrame()
        
        if timestamp_col:
            normalized_df['timestamp'] = pd.to_datetime(df[timestamp_col])
        if location_col:
            normalized_df['location'] = df[location_col]
        if gallons_col:
            normalized_df['gallons'] = pd.to_numeric(df[gallons_col], errors='coerce')
        if vehicle_col:
            normalized_df['vehicle_id'] = df[vehicle_col]
        
        # Fill missing columns with None
        required_cols = ['timestamp', 'location', 'gallons', 'vehicle_id']
        for col in required_cols:
            if col not in normalized_df.columns:
                normalized_df[col] = None
        
        return normalized_df[required_cols]