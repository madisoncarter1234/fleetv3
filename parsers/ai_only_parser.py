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
        
        # Build optimized prompt for Haiku (RESTORE WORKING VERSION)
        prompt = f"""Fleet audit expert. Analyze fuel CSV, detect violations.

FUEL DATA:
{fuel_csv_content}"""
        
        # Add RAW GPS data if provided
        if gps_file_path:
            try:
                with open(gps_file_path, 'r') as f:
                    gps_csv_content = f.read()
                    
                gps_lines = gps_csv_content.split('\n')
                print(f"Including GPS data with {len(gps_lines)} rows")
                
                prompt += f"""

GPS DATA:
{gps_csv_content}

GPS CHECKS: Match fuel locations, detect stolen cards, verify truck presence."""
            except Exception as e:
                print(f"Could not read GPS file: {e}")
        
        # Add RAW job data if provided
        if job_file_path:
            try:
                with open(job_file_path, 'r') as f:
                    job_csv_content = f.read()
                    
                job_lines = job_csv_content.split('\n')
                print(f"Including job data with {len(job_lines)} rows")
                    
                prompt += f"""

JOB DATA:
{job_csv_content}

JOB CHECKS: Match fuel to assigned sites, detect personal use."""
            except Exception as e:
                print(f"Could not read job file: {e}")
        
        prompt += """

CRITICAL: Parse EVERY SINGLE ROW in the fuel CSV. Include ALL transactions in parsed_data array.

RULES:
1. Parse ALL CSV rows (every single transaction) - include all in parsed_data
2. Extract: timestamp, location, gallons, vehicle_id, amount, driver_name (if available)  
3. Fix timestamps (skip malformed like "24:00:00")
4. Find violations: late night, overfills, rapid refills, personal use
5. If GPS: check truck was at station
6. If jobs: check fuel near work sites

IMPORTANT: If dataset is large, you can abbreviate violations but MUST include ALL transactions in parsed_data.

RETURN FORMAT:
{
  "parsed_data": [ALL_TRANSACTIONS_HERE],
  "violations": [FOUND_VIOLATIONS],
  "summary": {"total_transactions": ACTUAL_COUNT, "violations_found": VIOLATION_COUNT}
}

Return complete JSON with ALL parsed data:"""
        
        
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
            
            # Validate Haiku result (RESTORE WORKING VERSION)
            if result and result.get('parsed_data') and len(result['parsed_data']) > 0:
                print("✅ Haiku analysis successful!")
                return result
            else:
                raise ValueError("Haiku returned empty or invalid result")
                
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
            
            # Convert parsed_data to DataFrame (RESTORE WORKING VERSION)
            if result.get('parsed_data'):
                df = pd.DataFrame(result['parsed_data'])
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                result['dataframe'] = df
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to parse AI response: {e}")
            print(f"❌ Raw response: {result_text}")
            return None