import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

class FuelParser:
    """Parser for fuel card data from various providers"""
    
    @staticmethod
    def parse_wex(file_path: str) -> pd.DataFrame:
        """Parse WEX fuel card export CSV"""
        df = pd.read_csv(file_path)
        
        # Handle separate date and time columns (ChatGPT format)
        if 'Transaction Date' in df.columns and 'Transaction Time' in df.columns:
            print("Detected WEX format with separate date/time columns")
            
            # Clean and validate time data first
            df['Transaction Time'] = df['Transaction Time'].fillna('')
            df['Transaction Date'] = df['Transaction Date'].fillna('')
            
            # Check if we actually have valid time data
            has_valid_time = df['Transaction Time'].str.strip().str.len() > 0
            
            if has_valid_time.any():
                # For mixed data, handle valid and invalid time entries separately
                valid_time_mask = has_valid_time
                
                # Create combined strings only for valid time entries
                combined_strings = pd.Series(index=df.index, dtype='object')
                combined_strings[valid_time_mask] = (
                    df.loc[valid_time_mask, 'Transaction Date'].astype(str) + ' ' + 
                    df.loc[valid_time_mask, 'Transaction Time'].astype(str)
                )
                combined_strings[~valid_time_mask] = df.loc[~valid_time_mask, 'Transaction Date'].astype(str)
                
                # Parse timestamps
                df['timestamp'] = FuelParser._parse_timestamps(combined_strings)
                
                # If parsing failed and resulted in mostly NaT, fall back to date-only for all
                nat_count = df['timestamp'].isna().sum()
                total_count = len(df['timestamp'])
                
                if nat_count > total_count * 0.5:  # More than 50% failed
                    print("Warning: Time parsing mostly failed, falling back to date-only parsing for all records")
                    df['timestamp'] = FuelParser._parse_timestamps(df['Transaction Date'])
            else:
                print("Warning: No valid time data found, using date-only parsing")
                df['timestamp'] = FuelParser._parse_timestamps(df['Transaction Date'])
                
        elif 'Transaction Date' in df.columns:
            print("Detected WEX format with combined date/time column")
            df['timestamp'] = FuelParser._parse_timestamps(df['Transaction Date'])
        
        # Map WEX column names to normalized format (swiss army knife - handles all variants)
        column_mapping = {
            'Site Name': 'location',
            'Merchant Name': 'location',  # ChatGPT WEX format
            'Station Name': 'location',   # Alternative format
            'Location': 'location',       # Generic format
            'Store': 'location',          # Simplified format
            'Gallons': 'gallons',
            'Fuel Quantity': 'gallons',   # Alternative format
            'Volume': 'gallons',          # Generic format
            'Liters': 'gallons',          # Metric format (will need conversion)
            'Vehicle Number': 'vehicle_id',
            'Vehicle': 'vehicle_id',      # Simplified format
            'Unit': 'vehicle_id',         # Fleet format
            'Unit Number': 'vehicle_id',  # Fleet format
            'Truck': 'vehicle_id',        # Generic format
            'Card Number': 'card_id',
            'Card': 'card_id',            # Simplified format
            'Fleet Card': 'card_id',      # Descriptive format
            'Amount': 'amount',
            'Total Cost': 'amount',       # ChatGPT WEX format
            'Total Amount': 'amount',     # Alternative format
            'Cost': 'amount',             # Simplified format
            'Price': 'amount',            # Generic format
            'Charge': 'amount'            # Payment format
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
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
        
        # Enhanced detection patterns (swiss army knife - catches everything)
        wex_indicators = [
            'transaction date', 'site name', 'vehicle number', 'transaction time',
            'merchant name',  # ChatGPT WEX format
            'total cost',     # ChatGPT WEX format
            'driver name',    # ChatGPT WEX format
            'fuel type',      # ChatGPT WEX format
            'odometer reading', # ChatGPT WEX format
            'payment method'  # ChatGPT WEX format
        ]
        fleetcor_indicators = ['merchant name', 'fuel quantity', 'fleet card']
        fuelman_indicators = ['trans date', 'merchant', 'unit number']
        
        # Check for WEX format (including ChatGPT separated date/time format)
        if (provider == 'wex' or 
            any(indicator in column_names for indicator in wex_indicators) or
            'transaction date' in column_names or
            ('transaction date' in column_names and 'transaction time' in column_names)):
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
            '%m/%d/%Y %I:%M %p',      # 06/15/2024 04:56 AM (12-hour with AM/PM)
            '%d/%m/%Y %I:%M %p',      # 15/06/2024 04:56 AM
            '%Y-%m-%d %I:%M %p',      # 2024-06-15 04:56 AM
            '%m-%d-%Y %I:%M %p',      # 06-15-2024 04:56 AM
            '%d-%m-%Y %I:%M %p',      # 15-06-2024 04:56 AM
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
        
        # Try pandas auto-detection first with mixed format support
        try:
            # Use mixed format to handle inconsistent timestamp formats
            parsed = pd.to_datetime(timestamp_series, format='mixed', errors='coerce')
            
            # Check if parsing was successful (not all NaT or midnight)
            valid_parsed = parsed.dropna()
            if len(valid_parsed) > 0:
                midnight_count = (valid_parsed.dt.time == pd.Timestamp('00:00:00').time()).sum()
                total_count = len(valid_parsed)
                
                # If more than 80% are midnight, likely the original data is date-only
                if midnight_count < total_count * 0.8:
                    print(f"Mixed format parsing successful. Midnight entries: {midnight_count}/{total_count}")
                    return parsed
                elif midnight_count > total_count * 0.8:
                    print(f"Warning: {midnight_count}/{total_count} timestamps defaulted to midnight - likely date-only data")
                    return parsed
        except Exception as e:
            print(f"Mixed format parsing failed: {e}")
            pass
        
        # Fallback to traditional auto-detection
        try:
            parsed = pd.to_datetime(timestamp_series, infer_datetime_format=True)
            # Check if parsing was successful (not all NaT or midnight)
            midnight_count = (parsed.dt.time == pd.Timestamp('00:00:00').time()).sum()
            total_count = len(parsed.dropna())
            
            # If more than 80% are midnight, likely the original data is date-only
            if not parsed.isna().all() and midnight_count < total_count * 0.8:
                print(f"Auto-detection successful. Midnight entries: {midnight_count}/{total_count}")
                return parsed
            elif midnight_count > total_count * 0.8:
                print(f"Warning: {midnight_count}/{total_count} timestamps defaulted to midnight - likely date-only data")
        except Exception as e:
            print(f"Auto-detection failed: {e}")
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