import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

class GPSParser:
    """Parser for GPS log data from various fleet providers"""
    
    @staticmethod
    def parse_samsara(file_path: str) -> pd.DataFrame:
        """Parse Samsara GPS export CSV"""
        df = pd.read_csv(file_path)
        
        # Map Samsara column names to normalized format
        column_mapping = {
            'Time': 'timestamp',
            'Vehicle': 'vehicle_id', 
            'Latitude': 'lat',
            'Longitude': 'lon',
            'Speed (mph)': 'speed_mph'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Ensure required columns exist
        required_cols = ['timestamp', 'vehicle_id', 'lat', 'lon', 'speed_mph']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        return df[required_cols]
    
    @staticmethod
    def parse_verizon(file_path: str) -> pd.DataFrame:
        """Parse Verizon Connect GPS export CSV"""
        df = pd.read_csv(file_path)
        
        # Map Verizon column names to normalized format
        column_mapping = {
            'DateTime': 'timestamp',
            'VehicleName': 'vehicle_id',
            'Lat': 'lat', 
            'Lng': 'lon',
            'Speed': 'speed_mph'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Ensure required columns exist
        required_cols = ['timestamp', 'vehicle_id', 'lat', 'lon', 'speed_mph']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        return df[required_cols]
    
    @staticmethod
    def auto_parse(file_path: str, provider: str = None) -> pd.DataFrame:
        """Auto-detect and parse GPS data based on provider or column headers"""
        
        # Read first few rows to detect format
        sample_df = pd.read_csv(file_path, nrows=5)
        
        if provider == 'samsara' or 'Vehicle' in sample_df.columns:
            return GPSParser.parse_samsara(file_path)
        elif provider == 'verizon' or 'VehicleName' in sample_df.columns:
            return GPSParser.parse_verizon(file_path)
        else:
            # Try generic parsing
            return GPSParser.parse_generic(file_path)
    
    @staticmethod
    def parse_generic(file_path: str) -> pd.DataFrame:
        """Generic parser for unknown GPS formats"""
        df = pd.read_csv(file_path)
        
        # Try to map common column patterns
        timestamp_cols = ['timestamp', 'time', 'datetime', 'date_time']
        vehicle_cols = ['vehicle_id', 'vehicle', 'unit', 'asset']
        lat_cols = ['latitude', 'lat']
        lon_cols = ['longitude', 'lon', 'lng']
        speed_cols = ['speed', 'speed_mph', 'velocity']
        
        def find_column(df, possible_names):
            for col in df.columns:
                if col.lower() in [name.lower() for name in possible_names]:
                    return col
            return None
        
        # Find matching columns
        timestamp_col = find_column(df, timestamp_cols)
        vehicle_col = find_column(df, vehicle_cols)
        lat_col = find_column(df, lat_cols)
        lon_col = find_column(df, lon_cols)
        speed_col = find_column(df, speed_cols)
        
        # Create normalized dataframe
        normalized_df = pd.DataFrame()
        
        if timestamp_col:
            normalized_df['timestamp'] = pd.to_datetime(df[timestamp_col])
        if vehicle_col:
            normalized_df['vehicle_id'] = df[vehicle_col]
        if lat_col:
            normalized_df['lat'] = df[lat_col]
        if lon_col:
            normalized_df['lon'] = df[lon_col]
        if speed_col:
            normalized_df['speed_mph'] = df[speed_col]
        
        # Fill missing columns with None
        required_cols = ['timestamp', 'vehicle_id', 'lat', 'lon', 'speed_mph']
        for col in required_cols:
            if col not in normalized_df.columns:
                normalized_df[col] = None
        
        return normalized_df[required_cols]