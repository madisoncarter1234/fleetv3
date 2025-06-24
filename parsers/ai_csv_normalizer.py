import pandas as pd
import json
import io
from typing import Dict, List, Optional
from anthropic import Anthropic
import os
from datetime import datetime

class AICsvNormalizer:
    """AI-powered CSV normalizer that converts any fuel CSV to consistent schema"""
    
    def __init__(self, api_key: Optional[str] = None, use_backend_service: bool = True):
        """Initialize with Claude API key or backend service"""
        self.use_backend_service = use_backend_service
        
        if use_backend_service:
            # Use centralized backend service for SaaS
            from backend.ai_service import FleetAuditAIService
            self.ai_service = FleetAuditAIService()
        else:
            # Direct API access (for development/testing)
            self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        
        # Target schema that audit logic expects
        self.target_schema = {
            'timestamp': 'datetime - transaction date and time',
            'location': 'string - gas station, merchant name, or location',
            'gallons': 'float - fuel quantity in gallons',
            'vehicle_id': 'string - vehicle identifier, unit number, or vehicle name',
            'amount': 'float - optional cost/price in dollars (if available)'
        }
    
    def normalize_csv(self, file_path: str) -> pd.DataFrame:
        """Convert any fuel CSV to normalized schema using AI"""
        
        # Read the raw CSV
        raw_df = pd.read_csv(file_path)
        print(f"Processing CSV with {len(raw_df)} rows and columns: {list(raw_df.columns)}")
        
        # Get sample data for AI analysis
        sample_size = min(5, len(raw_df))
        sample_df = raw_df.head(sample_size)
        
        # Convert sample to string for AI
        sample_csv = sample_df.to_csv(index=False)
        
        # Get column mapping from AI
        column_mapping = self._get_ai_column_mapping(sample_csv)
        print(f"AI detected column mapping: {column_mapping}")
        
        # Apply mapping and normalize
        normalized_df = self._apply_mapping(raw_df, column_mapping)
        
        # Validate and clean the result
        normalized_df = self._validate_and_clean(normalized_df)
        
        print(f"Successfully normalized to {len(normalized_df)} rows with schema: {list(normalized_df.columns)}")
        return normalized_df
    
    def _get_ai_column_mapping(self, sample_csv: str) -> Dict[str, str]:
        """Use AI to analyze CSV and map columns to target schema"""
        
        if self.use_backend_service:
            # Use centralized backend service
            try:
                result = self.ai_service.normalize_csv_data(sample_csv)
                if result["success"]:
                    return result["mapping"]
                else:
                    print(f"Backend AI service failed: {result.get('error')}")
                    return self._fallback_column_mapping(sample_csv)
            except Exception as e:
                print(f"Backend service error: {e}")
                return self._fallback_column_mapping(sample_csv)
        else:
            # Direct API access (development mode)
            prompt = f"""
You are a CSV analysis expert. Analyze this fuel card transaction CSV sample and map the columns to our target schema.

TARGET SCHEMA (what we need):
- timestamp: transaction date and time 
- location: gas station/merchant name
- gallons: fuel quantity in gallons
- vehicle_id: vehicle identifier/unit number
- amount: cost in dollars (optional)

CSV SAMPLE:
{sample_csv}

INSTRUCTIONS:
1. Identify which CSV columns map to each target schema field
2. If date and time are separate columns, note both
3. Handle various formats (WEX, Fleetcor, Fuelman, etc.)
4. If a target field is missing, mark as null
5. Consider column name variations and synonyms

Return ONLY a JSON object with this exact format:
{{
    "timestamp": "Column Name" or {{"date_col": "Date Column", "time_col": "Time Column"}} or null,
    "location": "Column Name" or null,
    "gallons": "Column Name" or null, 
    "vehicle_id": "Column Name" or null,
    "amount": "Column Name" or null
}}
"""
            
            try:
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=500,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                mapping_text = response.content[0].text.strip()
                
                # Extract JSON from response
                if '```json' in mapping_text:
                    mapping_text = mapping_text.split('```json')[1].split('```')[0]
                elif '```' in mapping_text:
                    mapping_text = mapping_text.split('```')[1].split('```')[0]
                
                mapping = json.loads(mapping_text)
                return mapping
                
            except Exception as e:
                print(f"AI mapping failed: {e}")
                # Fallback to simple heuristics
                return self._fallback_column_mapping(sample_csv)
    
    def _fallback_column_mapping(self, sample_csv: str) -> Dict[str, str]:
        """Fallback column mapping using simple heuristics"""
        lines = sample_csv.split('\n')
        if len(lines) < 1:
            return {}
            
        columns = [col.strip().lower() for col in lines[0].split(',')]
        mapping = {}
        
        # Simple pattern matching
        for col in columns:
            if 'date' in col and 'time' not in col:
                mapping['timestamp'] = col
            elif 'time' in col:
                if 'timestamp' in mapping and isinstance(mapping['timestamp'], str):
                    # Convert to separate date/time format
                    mapping['timestamp'] = {
                        'date_col': mapping['timestamp'],
                        'time_col': col
                    }
                else:
                    mapping['timestamp'] = col
            elif any(x in col for x in ['location', 'merchant', 'station', 'site']):
                mapping['location'] = col
            elif any(x in col for x in ['gallon', 'quantity', 'volume', 'liter']):
                mapping['gallons'] = col
            elif any(x in col for x in ['vehicle', 'unit', 'truck', 'card']):
                mapping['vehicle_id'] = col
            elif any(x in col for x in ['amount', 'cost', 'price', 'total']):
                mapping['amount'] = col
        
        return mapping
    
    def _apply_mapping(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """Apply the column mapping to create normalized DataFrame"""
        normalized_df = pd.DataFrame()
        
        # Handle timestamp (can be single column or date+time combination)
        if mapping.get('timestamp'):
            if isinstance(mapping['timestamp'], dict):
                # Separate date and time columns
                date_col = mapping['timestamp'].get('date_col')
                time_col = mapping['timestamp'].get('time_col')
                
                if date_col in df.columns and time_col in df.columns:
                    # Combine date and time with PROPER validation
                    combined = df[date_col].astype(str) + ' ' + df[time_col].astype(str)
                    
                    # Parse timestamps directly - eliminate old parser dependency
                    normalized_df['timestamp'] = pd.to_datetime(combined, errors='coerce')
                elif date_col in df.columns:
                    normalized_df['timestamp'] = pd.to_datetime(df[date_col], errors='coerce')
            else:
                # Single timestamp column
                if mapping['timestamp'] in df.columns:
                    # Parse timestamps directly - eliminate old parser dependency
                    normalized_df['timestamp'] = pd.to_datetime(df[mapping['timestamp']], errors='coerce')
        
        # Handle other columns
        for target_col, source_col in mapping.items():
            if target_col == 'timestamp' or source_col is None:
                continue
                
            if isinstance(source_col, str) and source_col in df.columns:
                if target_col == 'gallons' or target_col == 'amount':
                    # Convert to numeric
                    normalized_df[target_col] = pd.to_numeric(
                        df[source_col].astype(str).str.replace('$', '').str.replace(',', ''), 
                        errors='coerce'
                    )
                else:
                    # Keep as string
                    normalized_df[target_col] = df[source_col].astype(str)
        
        return normalized_df
    
    def _validate_and_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean the normalized DataFrame"""
        
        # Ensure required columns exist
        required_cols = ['timestamp', 'location', 'gallons', 'vehicle_id']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
                print(f"Warning: Missing required column '{col}', filled with None")
        
        # Add amount if not present
        if 'amount' not in df.columns:
            df['amount'] = None
        
        # Clean data
        if 'timestamp' in df.columns:
            # Remove rows with invalid timestamps
            invalid_timestamps = df['timestamp'].isna().sum()
            if invalid_timestamps > 0:
                print(f"Warning: {invalid_timestamps} rows have invalid timestamps")
        
        if 'gallons' in df.columns:
            # Remove rows with invalid gallons
            invalid_gallons = df['gallons'].isna().sum()
            if invalid_gallons > 0:
                print(f"Warning: {invalid_gallons} rows have invalid gallons")
        
        # Return only the columns in the expected order
        final_cols = ['timestamp', 'location', 'gallons', 'vehicle_id', 'amount']
        return df[final_cols]
    
    def normalize_csv_batch(self, file_paths: List[str]) -> List[pd.DataFrame]:
        """Normalize multiple CSV files"""
        results = []
        for file_path in file_paths:
            try:
                normalized_df = self.normalize_csv(file_path)
                results.append(normalized_df)
            except Exception as e:
                print(f"Failed to normalize {file_path}: {e}")
                results.append(pd.DataFrame())
        return results