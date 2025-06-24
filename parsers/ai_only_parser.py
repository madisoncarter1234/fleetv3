import pandas as pd
import json
from typing import Dict, List, Optional
from anthropic import Anthropic
import os

class AIOnlyParser:
    """100% AI-powered parser - optimized for cost and performance"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Try multiple ways to get API key for Streamlit compatibility
        if api_key:
            self.client = Anthropic(api_key=api_key)
        elif os.getenv('ANTHROPIC_API_KEY'):
            self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        else:
            # Try Streamlit secrets if available
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
                    self.client = Anthropic(api_key=st.secrets['ANTHROPIC_API_KEY'])
                else:
                    self.client = Anthropic()  # Let Anthropic handle auth
            except:
                self.client = Anthropic()  # Let Anthropic handle auth
        self.primary_model = "claude-3-haiku-20240307"  # Fast & cheap
        # HAIKU ONLY - no fallback to expensive Sonnet
    
    def parse_and_detect_violations(self, fuel_file_path: str, gps_file_path: str = None, job_file_path: str = None) -> Dict:
        """
        Let AI do EVERYTHING:
        1. Parse the fuel CSV
        2. Normalize the data  
        3. Cross-reference with GPS/job data if provided
        4. Detect violations
        5. Return clean results
        """
        # Read RAW fuel CSV content
        with open(fuel_file_path, 'r') as f:
            fuel_csv_content = f.read()
        
        # Check file size but process all data
        fuel_csv_lines = fuel_csv_content.split('\n')
        print(f"Processing fuel file with {len(fuel_csv_lines)} rows")
        
        # Two-stage approach: Parse first, then detect violations
        prompt = f"""Parse this fuel CSV into standardized format. Return ONLY valid JSON.

CSV:
{fuel_csv_content}

Return this exact format:
{{
  "parsed_data": [
    {{"timestamp": "YYYY-MM-DD HH:MM:SS", "location": "station", "gallons": 25.5, "vehicle_id": "TRUCK001", "amount": 75.25}}
  ]
}}

Include ALL rows. No text outside JSON."""
        
        # Skip GPS/job for now - focus on just getting fuel parsing to work
        # TODO: Add violation detection in separate step
        if gps_file_path:
            print(f"GPS file available for future violation detection")
        if job_file_path:
            print(f"Job file available for future violation detection")
        
        
        # HAIKU ONLY - no expensive Sonnet fallback
        try:
            print("🚀 Using Claude Haiku for analysis...")
            print(f"🔍 API client initialized: {self.client is not None}")
            print(f"🔍 Model: {self.primary_model}")
            print(f"🔍 Prompt length: {len(prompt)} characters")
            
            response = self.client.messages.create(
                model=self.primary_model,
                max_tokens=8000,  # Increased for months of data
                temperature=0.1,
                timeout=90.0,  # Longer timeout for more data
                messages=[{"role": "user", "content": prompt}]
            )
            
            print(f"🔍 API call successful, response received")
            
            result_text = response.content[0].text.strip()
            print(f"🔍 Raw AI response (first 500 chars): {result_text[:500]}...")
            result = self._parse_ai_response(result_text)
            
            # Return Haiku result - always create DataFrame for app compatibility
            if result and result.get('parsed_data'):
                transactions = result['parsed_data']
                print(f"✅ Haiku completed! Found {len(transactions)} transactions")
                
                # Create DataFrame
                df = pd.DataFrame(transactions)
                print(f"DataFrame created with columns: {list(df.columns)}")
                
                # Standardize column names
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                elif 'datetime' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['datetime'], errors='coerce')
                    
                # Ensure required columns exist
                required_cols = ['timestamp', 'location', 'gallons', 'vehicle_id']
                for col in required_cols:
                    if col not in df.columns:
                        # Map from common alternatives
                        if col == 'location' and 'station' in df.columns:
                            df['location'] = df['station']
                        elif col == 'gallons' and 'volume' in df.columns:
                            df['gallons'] = df['volume']
                        else:
                            df[col] = None
                
                result['dataframe'] = df
                # Add empty violations for now (TODO: implement violation detection)
                result['violations'] = []
                result['summary'] = {"total_transactions": len(df), "violations_found": 0}
                return result
            else:
                print("⚠️ Haiku returned invalid result")
                return {
                    "parsed_data": [],
                    "dataframe": pd.DataFrame(),
                    "violations": [],
                    "summary": {"total_transactions": 0, "violations_found": 0}
                }
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ EXCEPTION in AI call: {type(e).__name__}: {e}")
            print(f"❌ Full traceback: {e.__class__.__module__}.{e.__class__.__name__}")
            
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                print(f"❌ Authentication failed: {e}")
                error_msg = "API key not configured. Please set ANTHROPIC_API_KEY environment variable."
            else:
                print(f"❌ Haiku failed: {e}")
            
            return {
                "error": error_msg,
                "parsed_data": [],
                "dataframe": pd.DataFrame(),
                "violations": [],
                "summary": {"total_transactions": 0, "violations_found": 0}
            }
    
    def _parse_ai_response(self, result_text: str) -> Dict:
        """Parse AI response and convert to usable format"""
        try:
            # Extract JSON - handle text before JSON
            if '```json' in result_text:
                json_text = result_text.split('```json')[1].split('```')[0]
                print(f"🔍 Extracted JSON from ```json blocks")
            elif '```' in result_text:
                json_text = result_text.split('```')[1].split('```')[0]
                print(f"🔍 Extracted JSON from ``` blocks")
            elif '{' in result_text:
                # Find the first { and take everything from there
                start_pos = result_text.find('{')
                json_text = result_text[start_pos:]
                print(f"🔍 Extracted JSON starting from first {{ bracket")
            else:
                json_text = result_text
                print(f"🔍 Using raw response as JSON")
            
            print(f"🔍 JSON to parse (first 200 chars): {json_text[:200]}...")
            result = json.loads(json_text)
            print(f"🔍 Successfully parsed JSON with keys: {list(result.keys())}")
            
            if 'parsed_data' in result:
                print(f"🔍 Found {len(result['parsed_data'])} items in parsed_data")
            else:
                print(f"⚠️ No 'parsed_data' key in result!")
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to parse AI response: {e}")
            print(f"❌ Raw response: {result_text}")
            return None