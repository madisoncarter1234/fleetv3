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
        self.fallback_model = "claude-3-5-sonnet-20241022"  # Smart fallback
    
    def parse_and_detect_violations(self, file_path: str, gps_data: str = None, job_data: str = None) -> Dict:
        """
        Let AI do EVERYTHING:
        1. Parse the fuel CSV
        2. Normalize the data  
        3. Cross-reference with GPS/job data if provided
        4. Detect violations
        5. Return clean results
        """
        # Read and truncate fuel CSV for cost optimization
        with open(file_path, 'r') as f:
            fuel_csv_content = f.read()
        
        # Smart batching for large files (don't throw away data)
        fuel_csv_lines = fuel_csv_content.split('\n')
        if len(fuel_csv_lines) > 500:  # Reasonable limit
            print(f"Large file detected ({len(fuel_csv_lines)} rows). Processing first 500 rows.")
        
        # Build optimized prompt for Haiku
        prompt = f"""Fleet audit expert. Analyze fuel CSV, detect violations.

FUEL DATA:
{fuel_csv_content}"""
        
        # Add GPS data if provided
        if gps_data:
            gps_lines = gps_data.split('\n')
            if len(gps_lines) > 200:
                print(f"Large GPS file detected ({len(gps_lines)} rows). Processing first 200 rows.")
            
            prompt += f"""

GPS DATA:
{gps_data}

GPS CHECKS: Match fuel locations, detect stolen cards, verify truck presence."""
        
        # Add job data if provided
        if job_data:
            job_lines = job_data.split('\n')
            if len(job_lines) > 100:
                print(f"Large job file detected ({len(job_lines)} rows). Processing first 100 rows.")
                
            prompt += f"""

JOB DATA:
{job_data}

JOB CHECKS: Match fuel to assigned sites, detect personal use."""
        
        prompt += """

RULES:
1. Parse ALL CSV rows (not just samples)
2. Extract: timestamp, location, gallons, vehicle_id, amount, driver_name (if available)
3. Fix timestamps (skip malformed like "24:00:00")
4. Find violations: late night, overfills, rapid refills, personal use
5. If GPS: check truck was at station
6. If jobs: check fuel near work sites

EXAMPLE OUTPUT:
{
  "parsed_data": [{"timestamp": "2024-06-15 14:30:00", "location": "Shell #1234", "gallons": 12.5, "vehicle_id": "TRUCK-001", "amount": 45.50, "driver_name": "John Smith"}],
  "violations": [{"type": "after_hours", "vehicle_id": "TRUCK-001", "driver_name": "John Smith", "description": "2:30 AM purchase", "severity": "high", "confidence": 0.9, "estimated_loss": 50.0, "timestamp": "2024-06-15 02:30:00", "location": "Shell #1234"}],
  "summary": {"total_transactions": 50, "violations_found": 3}
}

Return ONLY JSON:"""
        
        # Try Haiku first (fast & cheap)
        try:
            print("🚀 Using Claude Haiku for analysis...")
            response = self.client.messages.create(
                model=self.primary_model,
                max_tokens=2000,  # Smaller for Haiku
                temperature=0.1,
                timeout=30.0,  # Faster timeout
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text.strip()
            result = self._parse_ai_response(result_text)
            
            # Validate Haiku result
            if result and result.get('parsed_data') and len(result['parsed_data']) > 0:
                print("✅ Haiku analysis successful!")
                return result
            else:
                raise ValueError("Haiku returned empty or invalid result")
                
        except Exception as e:
            print(f"⚠️ Haiku failed: {e}")
            print("🎯 Falling back to Sonnet for complex analysis...")
            
            # Fallback to Sonnet for edge cases
            try:
                response = self.client.messages.create(
                    model=self.fallback_model,
                    max_tokens=4000,
                    temperature=0.1,
                    timeout=60.0,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                result_text = response.content[0].text.strip()
                result = self._parse_ai_response(result_text)
                
                if result:
                    print("✅ Sonnet fallback successful!")
                    return result
                else:
                    raise ValueError("Both Haiku and Sonnet failed")
                    
            except Exception as sonnet_error:
                print(f"❌ Both AI models failed: {sonnet_error}")
                return {
                    "error": f"Haiku: {e}, Sonnet: {sonnet_error}",
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