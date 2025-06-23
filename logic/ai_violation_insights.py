import pandas as pd
from typing import Dict, List, Optional
from anthropic import Anthropic
import os
import json

class AIViolationInsights:
    """AI-powered analysis for flagged violations to provide human-readable insights"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Claude API key"""
        self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
    
    def analyze_violation(self, violation: Dict, context_data: Dict = None) -> Dict:
        """
        Analyze a flagged violation and provide AI insights
        
        Args:
            violation: The violation dict from audit logic
            context_data: Optional context (nearby transactions, patterns, etc.)
        
        Returns:
            Enhanced violation dict with AI insights
        """
        try:
            # Create context for AI analysis
            analysis_prompt = self._build_analysis_prompt(violation, context_data)
            
            # Get AI insights
            insights = self._get_ai_insights(analysis_prompt)
            
            # Add insights to violation
            enhanced_violation = violation.copy()
            enhanced_violation['ai_insights'] = insights
            enhanced_violation['confidence_score'] = insights.get('confidence', 0.5)
            enhanced_violation['explanation'] = insights.get('explanation', 'No explanation available')
            enhanced_violation['risk_level'] = insights.get('risk_level', 'medium')
            
            return enhanced_violation
            
        except Exception as e:
            print(f"AI analysis failed for violation: {e}")
            # Return original violation if AI fails
            violation['ai_insights'] = {'error': str(e)}
            return violation
    
    def analyze_violations_batch(self, violations: List[Dict], context_data: Dict = None) -> List[Dict]:
        """Analyze multiple violations with AI insights"""
        enhanced_violations = []
        
        for violation in violations:
            try:
                enhanced = self.analyze_violation(violation, context_data)
                enhanced_violations.append(enhanced)
            except Exception as e:
                print(f"Failed to analyze violation: {e}")
                violation['ai_insights'] = {'error': str(e)}
                enhanced_violations.append(violation)
        
        return enhanced_violations
    
    def _build_analysis_prompt(self, violation: Dict, context_data: Dict = None) -> str:
        """Build prompt for AI analysis"""
        
        violation_type = violation.get('type', 'unknown')
        severity = violation.get('severity', 'unknown')
        details = violation.get('details', {})
        
        prompt = f"""
You are a fleet audit expert analyzing a potential violation. Provide insights about whether this looks legitimate or suspicious.

VIOLATION DETAILS:
- Type: {violation_type}
- Severity: {severity}
- Vehicle: {violation.get('vehicle_id', 'unknown')}
- Timestamp: {violation.get('timestamp', 'unknown')}
- Location: {details.get('location', 'unknown')}
- Details: {details}

"""
        
        # Add context if available
        if context_data:
            prompt += f"\nCONTEXT DATA:\n{json.dumps(context_data, indent=2, default=str)}\n"
        
        prompt += """
ANALYSIS INSTRUCTIONS:
1. Assess if this violation pattern indicates actual fraud/theft/waste
2. Consider normal business operations vs suspicious behavior
3. Look for red flags or innocent explanations
4. Rate confidence level (0.0-1.0) in your assessment
5. Assign risk level: low, medium, high

Return ONLY a JSON object with this format:
{
    "confidence": 0.85,
    "risk_level": "high",
    "explanation": "This looks like theft because...",
    "red_flags": ["flag1", "flag2"],
    "innocent_explanations": ["explanation1"],
    "recommended_action": "Investigate immediately"
}
"""
        
        return prompt
    
    def _get_ai_insights(self, prompt: str) -> Dict:
        """Get AI insights from the prompt"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
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
            
            insights = json.loads(insights_text)
            return insights
            
        except Exception as e:
            print(f"AI insights failed: {e}")
            return {
                "confidence": 0.5,
                "risk_level": "medium", 
                "explanation": f"AI analysis failed: {e}",
                "red_flags": [],
                "innocent_explanations": [],
                "recommended_action": "Manual review required"
            }
    
    def generate_violation_summary(self, violations: List[Dict]) -> str:
        """Generate an AI summary of all violations found"""
        
        if not violations:
            return "No violations found."
        
        # Prepare violation summary for AI
        violation_summary = []
        for v in violations:
            summary_item = {
                'type': v.get('type'),
                'severity': v.get('severity'),
                'vehicle': v.get('vehicle_id'),
                'explanation': v.get('explanation', v.get('ai_insights', {}).get('explanation', 'No explanation'))
            }
            violation_summary.append(summary_item)
        
        prompt = f"""
Generate a brief executive summary of these fleet audit violations:

VIOLATIONS FOUND:
{json.dumps(violation_summary, indent=2)}

Provide a 2-3 sentence summary highlighting:
1. Most serious issues found
2. Overall risk assessment
3. Key recommendations

Keep it concise and actionable for fleet managers.
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            return f"Summary generation failed: {e}"