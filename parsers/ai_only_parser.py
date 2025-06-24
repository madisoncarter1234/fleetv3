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
        
        # Build ultra-optimized prompt for Haiku
        prompt = f"""Parse fuel CSV, find violations.

CSV:
{fuel_csv_content}

Find: theft, after-hours, overfills, rapid refills, personal use.
Return JSON: {{"parsed_data":[ALL_ROWS], "violations":[VIOLATIONS]}}"""
        
        # Add RAW GPS data if provided
        if gps_file_path:
            try:
                with open(gps_file_path, 'r') as f:
                    gps_csv_content = f.read()
                    
                gps_lines = gps_csv_content.split('\n')
                print(f"Including GPS data with {len(gps_lines)} rows")
                
                prompt += f"\n\nGPS:\n{gps_csv_content}\nCheck: truck at station?"
            except Exception as e:
                print(f"Could not read GPS file: {e}")
        
        # Add RAW job data if provided
        if job_file_path:
            try:
                with open(job_file_path, 'r') as f:
                    job_csv_content = f.read()
                    
                job_lines = job_csv_content.split('\n')
                print(f"Including job data with {len(job_lines)} rows")
                    
                prompt += f"\n\nJOBS:\n{job_csv_content}\nCheck: fuel near work?"
            except Exception as e:
                print(f"Could not read job file: {e}")
        
        
        # HAIKU ONLY - no expensive Sonnet fallback
        try:
            print("🚀 Using Claude Haiku for analysis...")
            response = self.client.messages.create(
                model=self.primary_model,
                max_tokens=8000,  # Increased for months of data
                temperature=0.1,
                timeout=90.0,  # Longer timeout for more data
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text.strip()
            print(f"🔍 Raw AI response (first 500 chars): {result_text[:500]}...")
            result = self._parse_ai_response(result_text)
            
            # Return Haiku result - always create DataFrame for app compatibility
            if result:
                print(f"✅ Haiku completed! Found {len(result.get('parsed_data', []))} transactions")
                # Ensure we always have a dataframe for app.py compatibility
                if result.get('parsed_data'):
                    df = pd.DataFrame(result['parsed_data'])
                    print(f"DataFrame created with columns: {list(df.columns)}")
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                    result['dataframe'] = df
                else:
                    print("⚠️ No parsed_data in AI result")
                    result['dataframe'] = pd.DataFrame()
                    result['parsed_data'] = []
                return result
            else:
                print("⚠️ Haiku returned invalid JSON - creating empty result")
                return {
                    "parsed_data": [],
                    "dataframe": pd.DataFrame(),
                    "violations": [],
                    "summary": {"total_transactions": 0, "violations_found": 0}
                }
                
        except Exception as e:
            error_msg = str(e)
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
            # Extract JSON
            if '```json' in result_text:
                json_text = result_text.split('```json')[1].split('```')[0]
                print(f"🔍 Extracted JSON from ```json blocks")
            elif '```' in result_text:
                json_text = result_text.split('```')[1].split('```')[0]
                print(f"🔍 Extracted JSON from ``` blocks")
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