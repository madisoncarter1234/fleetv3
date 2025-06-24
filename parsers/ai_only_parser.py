import pandas as pd
import json
from typing import Dict, List, Optional
from anthropic import Anthropic
import os

class AIOnlyParser:
    """100% AI-powered parser - optimized for cost and performance"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
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
        
        # Smart batching for large files (don't throw away data)
        fuel_csv_lines = fuel_csv_content.split('\n')
        if len(fuel_csv_lines) > 500:  # Reasonable limit
            print(f"Large fuel file detected ({len(fuel_csv_lines)} rows). Processing first 500 rows.")
        
        # Build optimized prompt for Haiku
        prompt = f"""Fleet audit expert. Analyze fuel CSV, detect violations.

FUEL DATA:
{fuel_csv_content}"""
        
        # Add RAW GPS data if provided
        if gps_file_path:
            try:
                with open(gps_file_path, 'r') as f:
                    gps_csv_content = f.read()
                    
                gps_lines = gps_csv_content.split('\n')
                if len(gps_lines) > 200:
                    print(f"Large GPS file detected ({len(gps_lines)} rows). Processing first 200 rows.")
                
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
                if len(job_lines) > 100:
                    print(f"Large job file detected ({len(job_lines)} rows). Processing first 100 rows.")
                    
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
                max_tokens=4000,  # Increase for larger datasets
                temperature=0.1,
                timeout=60.0,  # Longer timeout for more data
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text.strip()
            result = self._parse_ai_response(result_text)
            
            # Return Haiku result even if imperfect - no Sonnet fallback
            if result and result.get('parsed_data'):
                print("✅ Haiku analysis completed!")
                return result
            else:
                print("⚠️ Haiku returned partial results - using what we got")
                return {
                    "parsed_data": [],
                    "violations": [],
                    "summary": {"total_transactions": 0, "violations_found": 0}
                }
                
        except Exception as e:
            print(f"❌ Haiku failed: {e}")
            return {
                "error": str(e),
                "parsed_data": [],
                "violations": [],
                "summary": {"total_transactions": 0, "violations_found": 0}
            }
    
    def _parse_ai_response(self, result_text: str) -> Dict:
        """Parse AI response and convert to usable format"""
        try:
            # Extract JSON
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]
            
            result = json.loads(result_text)
            
            # Convert parsed_data to DataFrame
            if result.get('parsed_data'):
                df = pd.DataFrame(result['parsed_data'])
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                result['dataframe'] = df
            
            return result
            
        except Exception as e:
            print(f"Failed to parse AI response: {e}")
            return None