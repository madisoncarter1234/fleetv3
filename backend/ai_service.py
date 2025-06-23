import os
from typing import Dict, Optional
from anthropic import Anthropic

class FleetAuditAIService:
    """Centralized AI service for FleetAudit.io SaaS"""
    
    def __init__(self):
        """Initialize with server-side API key"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")
        
        self.client = Anthropic(api_key=api_key)
        self.usage_tracking = {}
    
    def normalize_csv_data(self, csv_sample: str, user_id: str = "anonymous") -> Dict:
        """
        Normalize CSV data for a customer
        Tracks usage per user for billing/limits
        """
        try:
            # Track usage
            if user_id not in self.usage_tracking:
                self.usage_tracking[user_id] = {"csv_parses": 0, "insights": 0}
            
            self.usage_tracking[user_id]["csv_parses"] += 1
            
            # Build prompt for CSV analysis
            prompt = f"""
You are a CSV analysis expert. Analyze this fuel card transaction CSV sample and map the columns to our target schema.

TARGET SCHEMA (what we need):
- timestamp: transaction date and time 
- location: gas station/merchant name
- gallons: fuel quantity in gallons
- vehicle_id: vehicle identifier/unit number
- amount: cost in dollars (optional)

CSV SAMPLE:
{csv_sample}

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
            
            import json
            mapping = json.loads(mapping_text)
            
            return {
                "success": True,
                "mapping": mapping,
                "usage": self.usage_tracking[user_id]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": "Use manual parsing"
            }
    
    def analyze_violation(self, violation_data: Dict, user_id: str = "anonymous") -> Dict:
        """
        Analyze a violation and provide insights
        """
        try:
            # Track usage
            if user_id not in self.usage_tracking:
                self.usage_tracking[user_id] = {"csv_parses": 0, "insights": 0}
            
            self.usage_tracking[user_id]["insights"] += 1
            
            violation_type = violation_data.get('type', 'unknown')
            severity = violation_data.get('severity', 'unknown')
            details = violation_data.get('details', {})
            
            prompt = f"""
You are a fleet audit expert analyzing a potential violation. Provide insights about whether this looks legitimate or suspicious.

VIOLATION DETAILS:
- Type: {violation_type}
- Severity: {severity}
- Vehicle: {violation_data.get('vehicle_id', 'unknown')}
- Timestamp: {violation_data.get('timestamp', 'unknown')}
- Location: {details.get('location', 'unknown')}
- Details: {details}

ANALYSIS INSTRUCTIONS:
1. Assess if this violation pattern indicates actual fraud/theft/waste
2. Consider normal business operations vs suspicious behavior
3. Look for red flags or innocent explanations
4. Rate confidence level (0.0-1.0) in your assessment
5. Assign risk level: low, medium, high

Return ONLY a JSON object with this format:
{{
    "confidence": 0.85,
    "risk_level": "high",
    "explanation": "This looks like theft because...",
    "red_flags": ["flag1", "flag2"],
    "innocent_explanations": ["explanation1"],
    "recommended_action": "Investigate immediately"
}}
"""
            
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            insights_text = response.content[0].text.strip()
            
            # Extract JSON from response
            if '```json' in insights_text:
                insights_text = insights_text.split('```json')[1].split('```')[0]
            elif '```' in insights_text:
                insights_text = insights_text.split('```')[1].split('```')[0]
            
            import json
            insights = json.loads(insights_text)
            
            return {
                "success": True,
                "insights": insights,
                "usage": self.usage_tracking[user_id]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "insights": {
                    "confidence": 0.5,
                    "risk_level": "medium", 
                    "explanation": f"AI analysis failed: {e}",
                    "red_flags": [],
                    "innocent_explanations": [],
                    "recommended_action": "Manual review required"
                }
            }
    
    def get_usage_stats(self, user_id: str = "anonymous") -> Dict:
        """Get usage statistics for billing/monitoring"""
        return self.usage_tracking.get(user_id, {"csv_parses": 0, "insights": 0})
    
    def estimate_costs(self, user_id: str = "anonymous") -> Dict:
        """Estimate AI costs for transparency"""
        usage = self.get_usage_stats(user_id)
        
        # Rough cost estimates (actual costs are much lower)
        csv_cost = usage["csv_parses"] * 0.001  # ~$0.001 per CSV
        insights_cost = usage["insights"] * 0.01  # ~$0.01 per insight
        total_cost = csv_cost + insights_cost
        
        return {
            "csv_parsing_cost": csv_cost,
            "insights_cost": insights_cost,
            "total_estimated_cost": total_cost,
            "note": "Actual costs are typically much lower"
        }