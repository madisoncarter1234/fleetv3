import pandas as pd
from datetime import datetime, date
from typing import Optional, List, Dict, Tuple, Union
import re
import warnings

class DateTimeParser:
    """
    Swiss Army knife datetime parser for fuel card data from multiple platforms.
    Handles inconsistent formats, missing data, and provides robust error handling.
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.parsing_stats = {
            'total_attempts': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'format_usage': {},
            'failures': []
        }
        
        # Comprehensive format library - ordered by most common first for performance
        self.datetime_formats = [
            # Standard datetime formats
            '%Y-%m-%d %H:%M:%S',      # 2024-06-15 14:30:00
            '%m/%d/%Y %H:%M:%S',      # 06/15/2024 14:30:00
            '%d/%m/%Y %H:%M:%S',      # 15/06/2024 14:30:00
            '%Y-%m-%d %H:%M',         # 2024-06-15 14:30
            '%m/%d/%Y %H:%M',         # 06/15/2024 14:30
            '%d/%m/%Y %H:%M',         # 15/06/2024 14:30
            
            # 12-hour formats with AM/PM
            '%m/%d/%Y %I:%M:%S %p',   # 06/15/2024 02:30:15 PM
            '%d/%m/%Y %I:%M:%S %p',   # 15/06/2024 02:30:15 PM
            '%Y-%m-%d %I:%M:%S %p',   # 2024-06-15 02:30:15 PM
            '%m/%d/%Y %I:%M %p',      # 06/15/2024 02:30 PM
            '%d/%m/%Y %I:%M %p',      # 15/06/2024 02:30 PM
            '%Y-%m-%d %I:%M %p',      # 2024-06-15 02:30 PM
            
            # Date-only formats
            '%Y-%m-%d',               # 2024-06-15
            '%m/%d/%Y',               # 06/15/2024
            '%d/%m/%Y',               # 15/06/2024
            '%m-%d-%Y',               # 06-15-2024
            '%d-%m-%Y',               # 15-06-2024
            '%Y/%m/%d',               # 2024/06/15
            
            # Alternative separators
            '%m-%d-%Y %H:%M:%S',      # 06-15-2024 14:30:00
            '%d-%m-%Y %H:%M:%S',      # 15-06-2024 14:30:00
            '%m-%d-%Y %H:%M',         # 06-15-2024 14:30
            '%d-%m-%Y %H:%M',         # 15-06-2024 14:30
            '%m-%d-%Y %I:%M %p',      # 06-15-2024 02:30 PM
            '%d-%m-%Y %I:%M %p',      # 15-06-2024 02:30 PM
            
            # Compact formats
            '%Y%m%d %H:%M:%S',        # 20240615 14:30:00
            '%Y%m%d %H:%M',           # 20240615 14:30
            '%Y%m%d',                 # 20240615
            
            # Excel-style formats
            '%m/%d/%y %H:%M:%S',      # 6/15/24 14:30:00
            '%m/%d/%y %H:%M',         # 6/15/24 14:30
            '%m/%d/%y %I:%M %p',      # 6/15/24 2:30 PM
            '%m/%d/%y',               # 6/15/24
        ]
        
        # Time-only formats for when date and time are separate
        self.time_formats = [
            '%H:%M:%S',               # 14:30:00
            '%H:%M',                  # 14:30
            '%I:%M:%S %p',            # 02:30:15 PM
            '%I:%M %p',               # 02:30 PM
            '%H.%M.%S',               # 14.30.00
            '%H.%M',                  # 14.30
        ]
    
    def clean_datetime_string(self, dt_str: str) -> str:
        """Clean and normalize datetime strings for better parsing success."""
        if not isinstance(dt_str, str):
            return str(dt_str)
        
        # Remove extra whitespace
        dt_str = dt_str.strip()
        
        # Normalize AM/PM indicators
        dt_str = re.sub(r'\b(am|AM|Am|aM)\b', 'AM', dt_str)
        dt_str = re.sub(r'\b(pm|PM|Pm|pM)\b', 'PM', dt_str)
        
        # Remove timezone indicators (we'll assume local time)
        dt_str = re.sub(r'\s*[+-]\d{2}:?\d{2}\s*$', '', dt_str)
        dt_str = re.sub(r'\s*(UTC|GMT|EST|PST|CST|MST)\s*$', '', dt_str, flags=re.IGNORECASE)
        
        # Normalize separators
        dt_str = re.sub(r'[/\-\.]\s*', '/', dt_str)  # Normalize date separators
        dt_str = re.sub(r':\s*', ':', dt_str)        # Normalize time separators
        
        # Handle common Excel export issues
        dt_str = re.sub(r'\s+', ' ', dt_str)         # Multiple spaces to single
        
        return dt_str
    
    def parse_datetime(self, date_str: Union[str, None], time_str: Union[str, None] = None) -> Optional[datetime]:
        """
        Parse datetime from separate date and time strings, or combined datetime string.
        
        Args:
            date_str: Date string (or combined datetime string if time_str is None)
            time_str: Optional time string
            
        Returns:
            datetime object or None if parsing fails
        """
        self.parsing_stats['total_attempts'] += 1
        
        # Handle None inputs
        if not date_str or pd.isna(date_str):
            self._record_failure('date_str is None or NaN', date_str, time_str)
            return None
        
        # Convert to string if needed
        date_str = str(date_str).strip()
        if not date_str:
            self._record_failure('date_str is empty', date_str, time_str)
            return None
        
        # Clean the input strings
        date_str = self.clean_datetime_string(date_str)
        
        # If we have separate time string, combine them
        if time_str and not pd.isna(time_str):
            time_str = str(time_str).strip()
            if time_str:
                time_str = self.clean_datetime_string(time_str)
                combined_str = f"{date_str} {time_str}"
            else:
                combined_str = date_str
        else:
            combined_str = date_str
        
        # Try pandas auto-detection first (fastest for standard formats)
        try:
            result = pd.to_datetime(combined_str, errors='coerce')
            if not pd.isna(result):
                self._record_success('pandas_auto', combined_str)
                return result.to_pydatetime()
        except:
            pass
        
        # Try each format in our comprehensive list
        for fmt in self.datetime_formats:
            try:
                result = datetime.strptime(combined_str, fmt)
                self._record_success(fmt, combined_str)
                return result
            except ValueError:
                continue
        
        # If combined parsing failed and we have separate strings, try date + time parsing
        if time_str and not pd.isna(time_str) and str(time_str).strip():
            return self._parse_separate_date_time(date_str, time_str)
        
        # Try as date-only and add midnight time
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y', '%Y/%m/%d']:
            try:
                result = datetime.strptime(date_str, fmt)
                self._record_success(f'{fmt}_date_only', date_str)
                return result
            except ValueError:
                continue
        
        # Final attempt: try to extract date components with regex
        result = self._regex_parse_date(combined_str)
        if result:
            self._record_success('regex_extraction', combined_str)
            return result
        
        # All parsing attempts failed
        self._record_failure('all_formats_failed', date_str, time_str)
        return None
    
    def _parse_separate_date_time(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse date and time from separate strings."""
        # First parse the date part
        date_part = None
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y']:
            try:
                date_part = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
        
        if not date_part:
            return None
        
        # Then parse the time part
        time_part = None
        for fmt in self.time_formats:
            try:
                time_obj = datetime.strptime(time_str, fmt).time()
                time_part = time_obj
                break
            except ValueError:
                continue
        
        if not time_part:
            # Default to midnight if time parsing fails
            time_part = datetime.min.time()
        
        return datetime.combine(date_part, time_part)
    
    def _regex_parse_date(self, dt_str: str) -> Optional[datetime]:
        """Last resort: extract date components using regex."""
        # Look for patterns like MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
        patterns = [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',     # YYYY-MM-DD or YYYY/MM/DD
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',     # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})',     # MM/DD/YY or DD/MM/YY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, dt_str)
            if match:
                try:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # Year first
                        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    else:  # Month/day first (assume US format for ambiguity)
                        if len(groups[2]) == 2:  # 2-digit year
                            year = 2000 + int(groups[2])
                        else:
                            year = int(groups[2])
                        month, day = int(groups[0]), int(groups[1])
                    
                    return datetime(year, month, day)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _record_success(self, format_used: str, input_str: str):
        """Record successful parsing for statistics."""
        self.parsing_stats['successful_parses'] += 1
        self.parsing_stats['format_usage'][format_used] = \
            self.parsing_stats['format_usage'].get(format_used, 0) + 1
        
        if self.debug:
            print(f"✅ Parsed '{input_str}' using format: {format_used}")
    
    def _record_failure(self, reason: str, date_str: str, time_str: str = None):
        """Record parsing failure for debugging."""
        self.parsing_stats['failed_parses'] += 1
        failure_info = {
            'reason': reason,
            'date_str': date_str,
            'time_str': time_str
        }
        self.parsing_stats['failures'].append(failure_info)
        
        if self.debug:
            print(f"❌ Failed to parse: date='{date_str}', time='{time_str}', reason='{reason}'")
    
    def get_stats(self) -> Dict:
        """Get parsing statistics for debugging and optimization."""
        stats = self.parsing_stats.copy()
        if stats['total_attempts'] > 0:
            stats['success_rate'] = stats['successful_parses'] / stats['total_attempts']
        else:
            stats['success_rate'] = 0.0
        return stats
    
    def print_stats(self):
        """Print formatted parsing statistics."""
        stats = self.get_stats()
        print("=== DateTime Parsing Statistics ===")
        print(f"Total attempts: {stats['total_attempts']}")
        print(f"Successful: {stats['successful_parses']}")
        print(f"Failed: {stats['failed_parses']}")
        print(f"Success rate: {stats['success_rate']:.1%}")
        
        if stats['format_usage']:
            print("\nMost used formats:")
            for fmt, count in sorted(stats['format_usage'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {fmt}: {count} times")
        
        if stats['failures'] and self.debug:
            print(f"\nRecent failures ({len(stats['failures'])} total):")
            for failure in stats['failures'][-3:]:  # Show last 3 failures
                print(f"  {failure['reason']}: '{failure['date_str']}' + '{failure['time_str']}'")


class ColumnMapper:
    """
    Maps various fuel card platform column names to a standardized schema.
    Easily extensible for new platforms and formats.
    """
    
    def __init__(self):
        # Define column mappings for different platforms and variations
        self.column_aliases = {
            # Date columns
            'date': [
                'date', 'transaction_date', 'trans_date', 'fuel_date', 'purchase_date',
                'transaction date', 'trans date', 'fuel date', 'purchase date',
                'date_time', 'datetime', 'timestamp', 'time_stamp',
                'invoice_date', 'bill_date', 'card_date'
            ],
            
            # Time columns (when separate from date)
            'time': [
                'time', 'transaction_time', 'trans_time', 'fuel_time', 'purchase_time',
                'transaction time', 'trans time', 'fuel time', 'purchase time',
                'time_of_day', 'hour', 'clock_time'
            ],
            
            # Vehicle identification
            'vehicle_id': [
                'vehicle_id', 'vehicle', 'unit', 'truck', 'vehicle_number', 'unit_number',
                'vehicle number', 'unit number', 'vehicle_name', 'unit_name',
                'fleet_id', 'asset_id', 'equipment_id', 'vin', 'license_plate',
                'truck_number', 'van_number', 'car_id'
            ],
            
            # Location information
            'location': [
                'location', 'site_name', 'station', 'merchant', 'merchant_name',
                'site name', 'merchant name', 'station_name', 'store',
                'fuel_station', 'gas_station', 'service_station', 'retailer',
                'vendor', 'supplier', 'facility'
            ],
            
            # Fuel quantity
            'gallons': [
                'gallons', 'quantity', 'volume', 'fuel_quantity', 'fuel_volume',
                'fuel quantity', 'fuel volume', 'amount_dispensed', 'liters',
                'gal', 'qty', 'vol', 'fuel_amount'
            ],
            
            # Transaction amount
            'amount': [
                'amount', 'total', 'cost', 'price', 'total_cost', 'total_amount',
                'total cost', 'total amount', 'transaction_amount', 'charge',
                'net_amount', 'gross_amount', 'invoice_amount', 'bill_amount',
                'fuel_cost', 'purchase_amount'
            ],
            
            # Card information
            'card_id': [
                'card_id', 'card', 'card_number', 'fleet_card', 'payment_method',
                'card number', 'fleet card', 'payment method', 'account',
                'account_number', 'card_name', 'payment_card'
            ]
        }
    
    def normalize_column_name(self, col_name: str) -> str:
        """Normalize a column name by removing common variations."""
        if not isinstance(col_name, str):
            return str(col_name).lower().strip()
        
        # Convert to lowercase and clean
        normalized = col_name.lower().strip()
        
        # Remove common prefixes/suffixes
        normalized = re.sub(r'^(fuel_|transaction_|trans_)', '', normalized)
        normalized = re.sub(r'(_date|_time|_id|_number|_name)$', '', normalized)
        
        # Replace separators with underscores
        normalized = re.sub(r'[\s\-\.]+', '_', normalized)
        
        # Remove special characters
        normalized = re.sub(r'[^\w_]', '', normalized)
        
        return normalized
    
    def map_columns(self, df_columns: List[str]) -> Dict[str, str]:
        """
        Map DataFrame columns to standardized names.
        
        Args:
            df_columns: List of column names from the DataFrame
            
        Returns:
            Dictionary mapping original column names to standard names
        """
        mapping = {}
        df_columns_lower = [col.lower().strip() for col in df_columns]
        
        for standard_name, aliases in self.column_aliases.items():
            for original_col in df_columns:
                original_lower = original_col.lower().strip()
                
                # Direct match
                if original_lower in [alias.lower() for alias in aliases]:
                    mapping[original_col] = standard_name
                    break
                
                # Fuzzy match after normalization
                normalized = self.normalize_column_name(original_col)
                for alias in aliases:
                    if normalized == self.normalize_column_name(alias):
                        mapping[original_col] = standard_name
                        break
                
                if original_col in mapping:
                    break
        
        return mapping
    
    def apply_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply column mapping to a DataFrame."""
        mapping = self.map_columns(df.columns.tolist())
        
        # Rename columns using the mapping
        df_mapped = df.rename(columns=mapping)
        
        # Ensure all standard columns exist (fill with None if missing)
        for standard_col in self.column_aliases.keys():
            if standard_col not in df_mapped.columns:
                df_mapped[standard_col] = None
        
        return df_mapped


def extract_safe_datetimes(df: pd.DataFrame, date_col: str, time_col: str = None, 
                          debug: bool = False) -> Tuple[List[datetime], Dict]:
    """
    Extract datetime objects from DataFrame columns with robust error handling.
    
    Args:
        df: DataFrame containing datetime data
        date_col: Name of the date column
        time_col: Optional name of the time column
        debug: Whether to print debugging information
        
    Returns:
        Tuple of (list of valid datetime objects, parsing statistics)
    """
    parser = DateTimeParser(debug=debug)
    valid_datetimes = []
    
    for idx, row in df.iterrows():
        date_val = row.get(date_col)
        time_val = row.get(time_col) if time_col else None
        
        parsed_dt = parser.parse_datetime(date_val, time_val)
        if parsed_dt:
            valid_datetimes.append(parsed_dt)
    
    if debug:
        parser.print_stats()
    
    return valid_datetimes, parser.get_stats()


def safe_date_range(datetimes: List[datetime]) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Safely calculate min and max dates from a list of datetime objects.
    
    Args:
        datetimes: List of datetime objects (may contain None values)
        
    Returns:
        Tuple of (min_date, max_date) or (None, None) if no valid dates
    """
    # Filter out None values
    valid_dates = [dt for dt in datetimes if dt is not None]
    
    if not valid_dates:
        return None, None
    
    return min(valid_dates), max(valid_dates)


# Example usage and testing
if __name__ == "__main__":
    # Example 1: Basic datetime parsing
    parser = DateTimeParser(debug=True)
    
    test_cases = [
        ("06/14/2024", "04:56 AM"),
        ("2024-06-15", "14:30:00"),
        ("6/16/24 3:15 PM", None),
        ("Invalid date", "Invalid time"),
        (None, None),
        ("06/17/2024", ""),
    ]
    
    print("=== DateTime Parsing Examples ===")
    for date_str, time_str in test_cases:
        result = parser.parse_datetime(date_str, time_str)
        print(f"Input: '{date_str}' + '{time_str}' -> {result}")
    
    parser.print_stats()
    
    # Example 2: Column mapping
    print("\n=== Column Mapping Examples ===")
    mapper = ColumnMapper()
    
    sample_columns = [
        "Transaction Date", "Transaction Time", "Vehicle Number", 
        "Merchant Name", "Fuel Quantity", "Total Cost"
    ]
    
    mapping = mapper.map_columns(sample_columns)
    print("Column mapping:")
    for orig, std in mapping.items():
        print(f"  '{orig}' -> '{std}'")
    
    # Example 3: Safe datetime extraction
    print("\n=== Safe DateTime Extraction Example ===")
    sample_data = {
        'Transaction Date': ['06/14/2024', '06/15/2024', 'Invalid', None],
        'Transaction Time': ['04:56 AM', '11:30 PM', '25:99', ''],
        'Vehicle': ['TRUCK-001', 'TRUCK-002', 'TRUCK-003', 'TRUCK-004']
    }
    
    df = pd.DataFrame(sample_data)
    datetimes, stats = extract_safe_datetimes(df, 'Transaction Date', 'Transaction Time', debug=True)
    
    min_date, max_date = safe_date_range(datetimes)
    print(f"\nSafe date range: {min_date} to {max_date}")
    print(f"Valid datetimes extracted: {len(datetimes)} out of {len(df)} rows")