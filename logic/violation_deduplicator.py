import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

class ViolationDeduplicator:
    """Consolidate and deduplicate related violations for clean production reporting"""
    
    def __init__(self):
        # Define which violations should be grouped together
        self.related_violations = {
            'fuel_theft_cluster': [
                'volume_excess',
                'obvious_rapid_refill', 
                'price_excess',
                'price_premium',
                'pattern_deviation',
                'daily_excess',
                'estimated_volume_excess',
                'extreme_amount_deviation'
            ],
            'mpg_fraud_cluster': [
                'fuel_dumping_mpg',
                'odometer_fraud_mpg',
                'excessive_consumption_mpg',
                'idle_refill_mpg'
            ],
            'idle_cluster': [
                'idle_abuse',
                'excessive_consumption_mpg'
            ],
            'timing_cluster': [
                'timing_anomaly',
                'frequency_anomaly'
            ]
        }
        
        # Time window for grouping violations (same incident)
        self.grouping_window_hours = 2
        self.grouping_distance_miles = 5  # Same location if within 5 miles
    
    def deduplicate_violations(self, violations: List[Dict]) -> List[Dict]:
        """
        Group related violations and create consolidated incident reports
        
        Returns cleaned list with grouped violations and financial summaries
        """
        if not violations:
            return []
        
        # Group violations by vehicle and approximate time/location
        violation_groups = self._group_violations_by_incident(violations)
        
        # Consolidate each group into a single incident
        consolidated_violations = []
        for group in violation_groups:
            consolidated = self._consolidate_violation_group(group)
            consolidated_violations.append(consolidated)
        
        # Sort by severity and estimated loss
        consolidated_violations.sort(key=lambda x: (
            self._severity_score(x['severity']),
            -x.get('total_estimated_loss', 0)
        ), reverse=True)
        
        return consolidated_violations
    
    def _group_violations_by_incident(self, violations: List[Dict]) -> List[List[Dict]]:
        """Group violations that likely represent the same incident"""
        
        # Create DataFrame for easier grouping
        df = pd.DataFrame(violations)
        
        if df.empty:
            return []
        
        grouped_violations = []
        processed_indices = set()
        
        for i, violation in df.iterrows():
            if i in processed_indices:
                continue
            
            # Start a new group with this violation
            current_group = [violation.to_dict()]
            processed_indices.add(i)
            
            # Find related violations
            for j, other_violation in df.iterrows():
                if j in processed_indices or i == j:
                    continue
                
                if self._are_violations_related(violation, other_violation):
                    current_group.append(other_violation.to_dict())
                    processed_indices.add(j)
            
            grouped_violations.append(current_group)
        
        return grouped_violations
    
    def _are_violations_related(self, v1: pd.Series, v2: pd.Series) -> bool:
        """Determine if two violations are part of the same incident"""
        
        # Must be same vehicle
        if v1['vehicle_id'] != v2['vehicle_id']:
            return False
        
        # Must be within time window
        time_diff = abs((pd.to_datetime(v1['timestamp']) - pd.to_datetime(v2['timestamp'])).total_seconds() / 3600)
        if time_diff > self.grouping_window_hours:
            return False
        
        # Check if violation types are related
        method1 = v1.get('detection_method', '')
        method2 = v2.get('detection_method', '')
        
        for cluster_name, methods in self.related_violations.items():
            if method1 in methods and method2 in methods:
                return True
        
        # Check location proximity (if location data available)
        if 'location' in v1 and 'location' in v2:
            if pd.notna(v1['location']) and pd.notna(v2['location']):
                # Simple string comparison - in production could use geocoding
                if str(v1['location']).strip() == str(v2['location']).strip():
                    return True
        
        return False
    
    def _consolidate_violation_group(self, violation_group: List[Dict]) -> Dict:
        """Combine multiple related violations into a single consolidated incident"""
        
        if len(violation_group) == 1:
            # Single violation - just add financial summary
            violation = violation_group[0].copy()
            violation['total_estimated_loss'] = violation.get('estimated_loss', 0)
            violation['detection_methods'] = [violation.get('detection_method', 'unknown')]
            violation['evidence_count'] = 1
            return violation
        
        # Multiple violations - consolidate
        primary_violation = violation_group[0].copy()  # Use first as base
        
        # Aggregate detection methods
        detection_methods = []
        total_loss = 0
        max_confidence = 0
        max_severity = 'low'
        
        evidence_details = []
        
        for violation in violation_group:
            method = violation.get('detection_method', 'unknown')
            if method not in detection_methods:
                detection_methods.append(method)
            
            total_loss += violation.get('estimated_loss', 0)
            max_confidence = max(max_confidence, violation.get('confidence', 0))
            
            # Track severity (high > medium > low)
            current_severity = violation.get('severity', 'low')
            if self._severity_score(current_severity) > self._severity_score(max_severity):
                max_severity = current_severity
            
            # Collect evidence details
            evidence_details.append({
                'method': method,
                'description': violation.get('description', ''),
                'confidence': violation.get('confidence', 0),
                'loss': violation.get('estimated_loss', 0)
            })
        
        # Create consolidated description
        consolidated_description = self._create_consolidated_description(
            primary_violation, detection_methods, evidence_details
        )
        
        # Create consolidated violation
        consolidated = primary_violation.copy()
        consolidated.update({
            'detection_method': 'multi_factor_analysis',
            'detection_methods': detection_methods,
            'description': consolidated_description,
            'evidence_count': len(violation_group),
            'evidence_details': evidence_details,
            'total_estimated_loss': total_loss,
            'confidence': min(max_confidence + 0.1, 0.99),  # Boost confidence for multiple evidence
            'severity': max_severity,
            'consolidated': True
        })
        
        return consolidated
    
    def _create_consolidated_description(self, primary_violation: Dict, 
                                       detection_methods: List[str], 
                                       evidence_details: List[Dict]) -> str:
        """Create a comprehensive description for consolidated violations"""
        
        vehicle_id = primary_violation['vehicle_id']
        timestamp = primary_violation['timestamp']
        location = primary_violation.get('location', 'Unknown location')
        
        # Group methods by type
        fuel_theft_methods = []
        mpg_methods = []
        other_methods = []
        
        for method in detection_methods:
            if any(method in cluster for cluster in [
                self.related_violations['fuel_theft_cluster'],
                self.related_violations['mpg_fraud_cluster']
            ]):
                if 'mpg' in method:
                    mpg_methods.append(method)
                else:
                    fuel_theft_methods.append(method)
            else:
                other_methods.append(method)
        
        # Build description
        description_parts = []
        
        if fuel_theft_methods and mpg_methods:
            description_parts.append("**MULTI-FACTOR FUEL THEFT DETECTED**")
        elif fuel_theft_methods:
            description_parts.append("**FUEL THEFT DETECTED**")
        elif mpg_methods:
            description_parts.append("**FUEL EFFICIENCY FRAUD DETECTED**")
        else:
            description_parts.append("**FLEET VIOLATION DETECTED**")
        
        # Add evidence summary
        if fuel_theft_methods:
            fuel_evidence = [d for d in evidence_details if d['method'] in fuel_theft_methods]
            description_parts.append(f"Fuel theft evidence ({len(fuel_evidence)} indicators):")
            for evidence in fuel_evidence[:3]:  # Show top 3
                description_parts.append(f"• {self._format_method_name(evidence['method'])}")
        
        if mpg_methods:
            mpg_evidence = [d for d in evidence_details if d['method'] in mpg_methods]
            description_parts.append(f"MPG analysis evidence ({len(mpg_evidence)} indicators):")
            for evidence in mpg_evidence[:3]:
                description_parts.append(f"• {self._format_method_name(evidence['method'])}")
        
        # Add financial impact
        total_loss = sum(d['loss'] for d in evidence_details)
        if total_loss > 0:
            description_parts.append(f"**Estimated financial impact: ${total_loss:.2f}**")
        
        return " ".join(description_parts)
    
    def _format_method_name(self, method: str) -> str:
        """Convert method names to readable format"""
        
        method_names = {
            'volume_excess': 'Tank capacity exceeded',
            'obvious_rapid_refill': 'Rapid refill pattern',
            'price_excess': 'Excessive transaction cost',
            'price_premium': 'Unusually high fuel price',
            'pattern_deviation': 'Statistical pattern anomaly',
            'daily_excess': 'Daily fuel consumption exceeded',
            'fuel_dumping_mpg': 'Fuel dumping (MPG analysis)',
            'odometer_fraud_mpg': 'Odometer manipulation suspected',
            'excessive_consumption_mpg': 'Excessive fuel consumption',
            'idle_refill_mpg': 'Idle refill detected',
            'estimated_volume_excess': 'Estimated volume exceeded',
            'extreme_amount_deviation': 'Extreme cost deviation'
        }
        
        return method_names.get(method, method.replace('_', ' ').title())
    
    def _severity_score(self, severity: str) -> int:
        """Convert severity to numeric score for sorting"""
        scores = {'low': 1, 'medium': 2, 'high': 3}
        return scores.get(severity, 0)
    
    def generate_financial_summary(self, consolidated_violations: List[Dict], 
                                 time_period_days: int = 7) -> Dict:
        """Generate fleet-wide financial impact summary"""
        
        if not consolidated_violations:
            return {}
        
        # Calculate by vehicle
        vehicle_losses = defaultdict(lambda: {
            'total_loss': 0,
            'violation_count': 0,
            'highest_single_incident': 0,
            'violation_types': set()
        })
        
        total_fleet_loss = 0
        
        for violation in consolidated_violations:
            vehicle_id = violation['vehicle_id']
            loss = violation.get('total_estimated_loss', 0)
            
            vehicle_losses[vehicle_id]['total_loss'] += loss
            vehicle_losses[vehicle_id]['violation_count'] += 1
            vehicle_losses[vehicle_id]['highest_single_incident'] = max(
                vehicle_losses[vehicle_id]['highest_single_incident'], loss
            )
            
            # Track violation types
            if 'detection_methods' in violation:
                for method in violation['detection_methods']:
                    vehicle_losses[vehicle_id]['violation_types'].add(method)
            
            total_fleet_loss += loss
        
        # Format vehicle summaries
        vehicle_summaries = {}
        for vehicle_id, data in vehicle_losses.items():
            weekly_loss = data['total_loss'] * (7 / time_period_days) if time_period_days > 0 else 0
            monthly_loss = data['total_loss'] * (30 / time_period_days) if time_period_days > 0 else 0
            
            vehicle_summaries[vehicle_id] = {
                'total_loss': data['total_loss'],
                'weekly_estimate': weekly_loss,
                'monthly_estimate': monthly_loss,
                'violation_count': data['violation_count'],
                'highest_single_incident': data['highest_single_incident'],
                'violation_methods': list(data['violation_types']),
                'summary_text': f"Vehicle {vehicle_id} flagged for ${data['total_loss']:.2f} of likely stolen fuel this period"
            }
        
        # Overall fleet summary
        summary = {
            'total_fleet_loss': total_fleet_loss,
            'weekly_fleet_estimate': total_fleet_loss * (7 / time_period_days) if time_period_days > 0 else 0,
            'monthly_fleet_estimate': total_fleet_loss * (30 / time_period_days) if time_period_days > 0 else 0,
            'total_violations': len(consolidated_violations),
            'vehicles_flagged': len(vehicle_losses),
            'vehicle_summaries': vehicle_summaries,
            'worst_offender': max(vehicle_summaries.keys(), 
                                key=lambda v: vehicle_summaries[v]['total_loss']) if vehicle_summaries else None
        }
        
        return summary