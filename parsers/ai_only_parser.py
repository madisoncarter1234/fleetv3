import pandas as pd
import json
from typing import Dict, List, Optional
from anthropic import Anthropic
import os

class AIOnlyParser:
    """100% AI-powered parser - no manual logic, no bullshit"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
    
    def parse_and_detect_violations(self, file_path: str, gps_data: str = None, job_data: str = None) -> Dict:
        """
        Let AI do EVERYTHING:
        1. Parse the fuel CSV
        2. Normalize the data  
        3. Cross-reference with GPS/job data if provided
        4. Detect violations
        5. Return clean results
        """
        # Read raw fuel CSV
        with open(file_path, 'r') as f:
            fuel_csv_content = f.read()
        
        # Build prompt with all available data
        prompt = f"""
You are a fleet audit expert. Analyze this fuel card CSV and detect violations.

FUEL CARD DATA:
{fuel_csv_content}"""
        
        # Add GPS data if provided
        if gps_data:
            prompt += f"""

GPS TRACKING DATA:
{gps_data}

ENHANCED DETECTION WITH GPS:
- Match fuel purchases to actual vehicle locations
- Detect stolen card use (fuel purchase without truck present)
- Calculate MPG efficiency and flag anomalies
- Verify vehicles were actually at gas stations during purchases"""
        
        # Add job data if provided
        if job_data:
            prompt += f"""

JOB ASSIGNMENT DATA:
{job_data}

ENHANCED DETECTION WITH JOB DATA:
- Flag fuel purchases far from assigned job sites
- Detect personal use (fuel near employee homes, not job sites)
- Match fuel timing with scheduled work hours
- Identify route deviations for personal errands"""
        
        prompt += """

TASK:
1. Parse the CSV and understand the columns
2. Normalize timestamps properly (NO 00:00:00 defaults for malformed times)
3. Detect fuel theft violations:
   - Suspicious timing (late night/weekend purchases)
   - Volume anomalies (overfilling, unusual amounts)
   - Frequency issues (multiple purchases same day)
   - Location patterns (outlier locations)

CRITICAL: If a time is malformed (like "24:00:00" or "15:03:99"), SKIP that row entirely. Do NOT default to midnight.

Return ONLY a JSON object:
{{
    "parsed_data": [
        {{"timestamp": "2024-06-15 14:30:00", "location": "Shell #1234", "gallons": 12.5, "vehicle_id": "TRUCK-001", "amount": 45.50}},
        ...
    ],
    "violations": [
        {{"type": "suspicious_timing", "vehicle_id": "TRUCK-001", "description": "Fuel purchase at 2:30 AM", "severity": "medium", "timestamp": "2024-06-15 02:30:00"}},
        ...
    ],
    "summary": {{"total_transactions": 50, "violations_found": 3, "clean_timestamps": 48}}
}}
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1,
                timeout=60.0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text.strip()
            
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
            print(f"AI parsing failed: {e}")
            return {
                "error": str(e),
                "parsed_data": [],
                "violations": [],
                "summary": {"total_transactions": 0, "violations_found": 0, "clean_timestamps": 0}
            }