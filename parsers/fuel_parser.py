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
        
        # Convert timestamp to datetime with multiple format attempts
        if 'timestamp' in df.columns:
            df['timestamp'] = FuelParser._parse_timestamps(df['timestamp'])
        
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
        
        # Convert timestamp to datetime with multiple format attempts
        if 'timestamp' in df.columns:
            df['timestamp'] = FuelParser._parse_timestamps(df['timestamp'])
        
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
        
        # Convert timestamp to datetime with multiple format attempts
        if 'timestamp' in df.columns:
            df['timestamp'] = FuelParser._parse_timestamps(df['timestamp'])
        
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
        column_names = [col.lower().strip() for col in sample_df.columns]
        
        # Enhanced detection patterns
        wex_indicators = ['transaction date', 'site name', 'vehicle number']
        fleetcor_indicators = ['merchant name', 'fuel quantity']
        fuelman_indicators = ['trans date', 'merchant']
        
        # Check for WEX format
        if (provider == 'wex' or 
            any(indicator in column_names for indicator in wex_indicators) or
            'transaction date' in column_names):
            print(f"Detected WEX format based on columns: {sample_df.columns.tolist()}")
            return FuelParser.parse_wex(file_path)
        
        # Check for Fleetcor format
        elif (provider == 'fleetcor' or 
              any(indicator in column_names for indicator in fleetcor_indicators) or
              'merchant name' in column_names):
            print(f"Detected Fleetcor format based on columns: {sample_df.columns.tolist()}")
            return FuelParser.parse_fleetcor(file_path)
        
        # Check for Fuelman format
        elif (provider == 'fuelman' or 
              any(indicator in column_names for indicator in fuelman_indicators) or
              'trans date' in column_names):
            print(f"Detected Fuelman format based on columns: {sample_df.columns.tolist()}")
            return FuelParser.parse_fuelman(file_path)
        
        else:
            # Try generic parsing
            print(f"Using generic parsing for columns: {sample_df.columns.tolist()}")
            return FuelParser.parse_generic(file_path)
    
    @staticmethod
    def parse_generic(file_path: str) -> pd.DataFrame:
        """Generic parser for unknown fuel card formats"""
        df = pd.read_csv(file_path)
        
        # Try to map common column patterns (more comprehensive)
        timestamp_cols = ['timestamp', 'date', 'transaction_date', 'trans_date', 'transaction date', 'trans date', 'datetime', 'time']
        location_cols = ['location', 'site', 'merchant', 'station', 'site_name', 'site name', 'merchant_name', 'merchant name', 'store']
        gallons_cols = ['gallons', 'quantity', 'fuel_quantity', 'fuel quantity', 'volume', 'liters', 'fuel_amount', 'fuel amount']
        vehicle_cols = ['vehicle_id', 'vehicle', 'unit', 'vehicle_number', 'vehicle number', 'unit_number', 'unit number', 'card_number', 'card number']
        amount_cols = ['amount', 'cost', 'total', 'price', 'value', 'charge']
        
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
        amount_col = find_column(df, amount_cols)
        
        # Create normalized dataframe
        normalized_df = pd.DataFrame()
        
        if timestamp_col:
            normalized_df['timestamp'] = FuelParser._parse_timestamps(df[timestamp_col])
        if location_col:
            normalized_df['location'] = df[location_col]
        if gallons_col:
            normalized_df['gallons'] = pd.to_numeric(df[gallons_col], errors='coerce')
        if vehicle_col:
            normalized_df['vehicle_id'] = df[vehicle_col]
        if amount_col:
            normalized_df['amount'] = pd.to_numeric(df[amount_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
        
        # Fill missing columns with None
        required_cols = ['timestamp', 'location', 'gallons', 'vehicle_id']
        for col in required_cols:
            if col not in normalized_df.columns:
                normalized_df[col] = None
        
        # Add amount column if available
        if 'amount' not in normalized_df.columns:
            normalized_df['amount'] = None
        
        # Print detection summary
        detected_cols = {k: v for k, v in {
            'timestamp': timestamp_col,
            'location': location_col, 
            'gallons': gallons_col,
            'vehicle_id': vehicle_col,
            'amount': amount_col
        }.items() if v is not None}
        
        print(f"Generic parser detected: {detected_cols}")
        
        return normalized_df
    
    @staticmethod
    def _parse_timestamps(timestamp_series: pd.Series) -> pd.Series:
        """Robust timestamp parsing with multiple format attempts"""
        
        # Common timestamp formats found in fuel card exports
        common_formats = [
            '%Y-%m-%d %H:%M:%S',      # 2024-06-15 14:30:00
            '%m/%d/%Y %H:%M:%S',      # 06/15/2024 14:30:00
            '%d/%m/%Y %H:%M:%S',      # 15/06/2024 14:30:00
            '%Y-%m-%d %H:%M',         # 2024-06-15 14:30
            '%m/%d/%Y %H:%M',         # 06/15/2024 14:30
            '%d/%m/%Y %H:%M',         # 15/06/2024 14:30
            '%Y-%m-%d',               # 2024-06-15 (date only)
            '%m/%d/%Y',               # 06/15/2024 (date only)
            '%d/%m/%Y',               # 15/06/2024 (date only)
            '%m-%d-%Y %H:%M:%S',      # 06-15-2024 14:30:00
            '%d-%m-%Y %H:%M:%S',      # 15-06-2024 14:30:00
            '%m-%d-%Y %H:%M',         # 06-15-2024 14:30
            '%d-%m-%Y %H:%M',         # 15-06-2024 14:30
            '%m-%d-%Y',               # 06-15-2024 (date only)
            '%d-%m-%Y',               # 15-06-2024 (date only)
        ]
        
        # Try pandas auto-detection first
        try:
            parsed = pd.to_datetime(timestamp_series, infer_datetime_format=True)
            # Check if parsing was successful (not all NaT or midnight)
            if not parsed.isna().all() and not (parsed.dt.time == pd.Timestamp('00:00:00').time()).all():
                return parsed
        except:
            pass
        
        # Try each format manually
        for fmt in common_formats:
            try:
                parsed = pd.to_datetime(timestamp_series, format=fmt, errors='coerce')
                # Check if at least 50% of dates were parsed successfully
                if parsed.notna().sum() > len(parsed) * 0.5:
                    return parsed
            except:
                continue
        
        # Try without format specification as last resort
        try:
            parsed = pd.to_datetime(timestamp_series, errors='coerce')
            return parsed
        except:
            # If all else fails, return original series
            print(f"Warning: Could not parse timestamps. Sample values: {timestamp_series.head().tolist()}")
            return timestamp_series