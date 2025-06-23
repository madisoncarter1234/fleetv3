import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .utils import calculate_distance

class MPGAnalyzer:
    """Detect fuel theft through MPG analysis - identifies odometer fraud, fuel dumping, and idle refills"""
    
    def __init__(self):
        # Expected MPG ranges for different vehicle types (conservative estimates)
        self.mpg_expectations = {
            'truck': {'min': 7, 'max': 12, 'avg': 9},      # Heavy trucks/commercial
            'van': {'min': 12, 'max': 18, 'avg': 15},      # Delivery vans
            'pickup': {'min': 15, 'max': 25, 'avg': 20},   # Pickup trucks
            'car': {'min': 20, 'max': 35, 'avg': 28},      # Passenger cars
            'default': {'min': 9, 'max': 12, 'avg': 10.5}  # Conservative commercial default
        }
        
        # Thresholds for flagging violations
        self.violation_thresholds = {
            'odometer_fraud': 0.5,      # MPG < 50% of minimum expected = odometer fraud
            'fuel_dumping': 0.3,        # MPG < 30% of minimum expected = fuel dumping
            'excessive_idling': 0.7,    # MPG < 70% of minimum expected = excessive idling
            'minimum_miles': 5,         # Need at least 5 miles driven to calculate MPG
            'minimum_fuel': 3           # Need at least 3 gallons consumed
        }
    
    def analyze_vehicle_mpg(self, fuel_df: pd.DataFrame, gps_df: pd.DataFrame, 
                           vehicle_id: str, vehicle_type: str = 'default') -> List[Dict]:
        """
        Analyze MPG patterns for a specific vehicle to detect fraud
        
        Returns violations with financial impact calculations
        """
        violations = []
        
        if fuel_df.empty or gps_df.empty:
            return violations
        
        # Filter data for this vehicle
        vehicle_fuel = fuel_df[fuel_df['vehicle_id'] == vehicle_id].copy()
        vehicle_gps = gps_df[gps_df['vehicle_id'] == vehicle_id].copy()
        
        if vehicle_fuel.empty or vehicle_gps.empty:
            return violations
        
        # Sort by timestamp
        vehicle_fuel = vehicle_fuel.sort_values('timestamp')
        vehicle_gps = vehicle_gps.sort_values('timestamp')
        
        # Get MPG expectations for this vehicle type
        mpg_range = self.mpg_expectations.get(vehicle_type, self.mpg_expectations['default'])
        
        # Analyze fuel periods (between fill-ups)
        for i in range(len(vehicle_fuel) - 1):
            current_fill = vehicle_fuel.iloc[i]
            next_fill = vehicle_fuel.iloc[i + 1]
            
            # Calculate fuel consumed (assuming fill-ups)
            fuel_consumed = next_fill['gallons'] if pd.notna(next_fill['gallons']) else None
            
            if fuel_consumed is None or fuel_consumed < self.violation_thresholds['minimum_fuel']:
                continue
            
            # Calculate distance driven between fill-ups
            distance = self._calculate_distance_between_times(
                vehicle_gps, current_fill['timestamp'], next_fill['timestamp']
            )
            
            if distance < self.violation_thresholds['minimum_miles']:
                # Very low miles but significant fuel consumption = idle refill or fraud
                violations.append(self._create_idle_refill_violation(
                    vehicle_id, next_fill, distance, fuel_consumed, mpg_range
                ))
                continue
            
            # Calculate actual MPG
            actual_mpg = distance / fuel_consumed
            
            # Determine violation type based on MPG
            violation = self._analyze_mpg_violation(
                vehicle_id, next_fill, actual_mpg, distance, fuel_consumed, mpg_range
            )
            
            if violation:
                violations.append(violation)
        
        return violations
    
    def _calculate_distance_between_times(self, gps_df: pd.DataFrame, 
                                        start_time: datetime, end_time: datetime) -> float:
        """Calculate total distance driven between two timestamps"""
        
        # Filter GPS data to time window
        time_filtered = gps_df[
            (gps_df['timestamp'] >= start_time) & 
            (gps_df['timestamp'] <= end_time)
        ].copy()
        
        if len(time_filtered) < 2:
            return 0.0
        
        total_distance = 0.0
        
        # Calculate cumulative distance between GPS points
        for i in range(len(time_filtered) - 1):
            current = time_filtered.iloc[i]
            next_point = time_filtered.iloc[i + 1]
            
            # Skip if coordinates are invalid
            if any(pd.isna([current['lat'], current['lon'], next_point['lat'], next_point['lon']])):
                continue
            
            distance = calculate_distance(
                current['lat'], current['lon'],
                next_point['lat'], next_point['lon']
            )
            total_distance += distance
        
        return total_distance
    
    def _analyze_mpg_violation(self, vehicle_id: str, fuel_record: pd.Series, 
                              actual_mpg: float, distance: float, fuel_consumed: float,
                              mpg_range: Dict) -> Optional[Dict]:
        """Analyze if MPG indicates a violation and determine type"""
        
        min_expected_mpg = mpg_range['min']
        avg_expected_mpg = mpg_range['avg']
        
        # Calculate financial impact
        expected_fuel = distance / avg_expected_mpg
        excess_fuel = fuel_consumed - expected_fuel
        fuel_cost = excess_fuel * 3.75  # Average fuel cost per gallon
        
        # Determine violation type based on severity
        if actual_mpg < min_expected_mpg * self.violation_thresholds['fuel_dumping']:
            # Extremely low MPG = fuel dumping or major fraud
            return {
                'vehicle_id': vehicle_id,
                'timestamp': fuel_record['timestamp'],
                'violation_type': 'fuel_theft',
                'detection_method': 'fuel_dumping_mpg',
                'description': f"Fuel dumping detected: {fuel_consumed:.1f} gal used, {distance:.1f} miles logged → {actual_mpg:.1f} MPG (expected: {min_expected_mpg}–{mpg_range['max']}). Indicates fuel dumping or major odometer manipulation.",
                'location': fuel_record['location'],
                'actual_mpg': actual_mpg,
                'expected_mpg_range': f"{min_expected_mpg}-{mpg_range['max']}",
                'distance_miles': distance,
                'fuel_gallons': fuel_consumed,
                'excess_fuel_gallons': excess_fuel,
                'estimated_loss': fuel_cost,
                'severity': 'high',
                'confidence': 0.95
            }
        
        elif actual_mpg < min_expected_mpg * self.violation_thresholds['odometer_fraud']:
            # Very low MPG = odometer fraud
            return {
                'vehicle_id': vehicle_id,
                'timestamp': fuel_record['timestamp'],
                'violation_type': 'fuel_theft',
                'detection_method': 'odometer_fraud_mpg',
                'description': f"Odometer fraud suspected: {fuel_consumed:.1f} gal used, {distance:.1f} miles logged → {actual_mpg:.1f} MPG (expected: {min_expected_mpg}–{mpg_range['max']}). Miles may be under-reported to hide excessive fuel consumption.",
                'location': fuel_record['location'],
                'actual_mpg': actual_mpg,
                'expected_mpg_range': f"{min_expected_mpg}-{mpg_range['max']}",
                'distance_miles': distance,
                'fuel_gallons': fuel_consumed,
                'excess_fuel_gallons': excess_fuel,
                'estimated_loss': fuel_cost,
                'severity': 'high',
                'confidence': 0.90
            }
        
        elif actual_mpg < min_expected_mpg * self.violation_thresholds['excessive_idling']:
            # Moderately low MPG = excessive idling or personal use
            return {
                'vehicle_id': vehicle_id,
                'timestamp': fuel_record['timestamp'],
                'violation_type': 'idle_abuse',
                'detection_method': 'excessive_consumption_mpg',
                'description': f"Excessive fuel consumption: {fuel_consumed:.1f} gal used, {distance:.1f} miles logged → {actual_mpg:.1f} MPG (expected: {min_expected_mpg}–{mpg_range['max']}). May indicate excessive idling or personal vehicle use.",
                'location': fuel_record['location'],
                'actual_mpg': actual_mpg,
                'expected_mpg_range': f"{min_expected_mpg}-{mpg_range['max']}",
                'distance_miles': distance,
                'fuel_gallons': fuel_consumed,
                'excess_fuel_gallons': excess_fuel,
                'estimated_loss': fuel_cost,
                'severity': 'medium',
                'confidence': 0.75
            }
        
        return None
    
    def _create_idle_refill_violation(self, vehicle_id: str, fuel_record: pd.Series,
                                    distance: float, fuel_consumed: float, 
                                    mpg_range: Dict) -> Dict:
        """Create violation for cases where significant fuel is consumed with minimal mileage"""
        
        # Calculate financial impact
        fuel_cost = fuel_consumed * 3.75  # Average fuel cost per gallon
        
        return {
            'vehicle_id': vehicle_id,
            'timestamp': fuel_record['timestamp'],
            'violation_type': 'fuel_theft',
            'detection_method': 'idle_refill_mpg',
            'description': f"Idle refill detected: {fuel_consumed:.1f} gallons consumed with only {distance:.1f} miles driven. Vehicle may have been used for personal purposes or fuel transferred to another vehicle.",
            'location': fuel_record['location'],
            'actual_mpg': distance / fuel_consumed if fuel_consumed > 0 else 0,
            'expected_mpg_range': f"{mpg_range['min']}-{mpg_range['max']}",
            'distance_miles': distance,
            'fuel_gallons': fuel_consumed,
            'excess_fuel_gallons': fuel_consumed * 0.8,  # Assume 80% was wasted/stolen
            'estimated_loss': fuel_cost * 0.8,
            'severity': 'high',
            'confidence': 0.90
        }
    
    def calculate_vehicle_financial_impact(self, violations: List[Dict], 
                                         time_period_days: int = 7) -> Dict:
        """Calculate financial impact per vehicle for a given time period"""
        
        vehicle_impacts = {}
        
        for violation in violations:
            vehicle_id = violation['vehicle_id']
            estimated_loss = violation.get('estimated_loss', 0)
            
            if vehicle_id not in vehicle_impacts:
                vehicle_impacts[vehicle_id] = {
                    'total_loss': 0,
                    'violation_count': 0,
                    'violation_types': set(),
                    'confidence_weighted_loss': 0
                }
            
            # Add to totals
            vehicle_impacts[vehicle_id]['total_loss'] += estimated_loss
            vehicle_impacts[vehicle_id]['violation_count'] += 1
            vehicle_impacts[vehicle_id]['violation_types'].add(violation.get('detection_method', 'unknown'))
            
            # Weight loss by confidence
            confidence = violation.get('confidence', 1.0)
            vehicle_impacts[vehicle_id]['confidence_weighted_loss'] += estimated_loss * confidence
        
        # Format results
        formatted_results = {}
        for vehicle_id, impact in vehicle_impacts.items():
            formatted_results[vehicle_id] = {
                'total_estimated_loss': impact['total_loss'],
                'confidence_weighted_loss': impact['confidence_weighted_loss'],
                'violation_count': impact['violation_count'],
                'violation_methods': list(impact['violation_types']),
                'weekly_loss_estimate': impact['total_loss'] * (7 / time_period_days) if time_period_days > 0 else 0,
                'monthly_loss_estimate': impact['total_loss'] * (30 / time_period_days) if time_period_days > 0 else 0
            }
        
        return formatted_results
    
    def get_fleet_mpg_summary(self, violations: List[Dict]) -> Dict:
        """Generate fleet-wide MPG analysis summary"""
        
        if not violations:
            return {}
        
        mpg_violations = [v for v in violations if 'actual_mpg' in v]
        
        if not mpg_violations:
            return {}
        
        total_violations = len(mpg_violations)
        total_estimated_loss = sum(v.get('estimated_loss', 0) for v in mpg_violations)
        
        # Group by detection method
        by_method = {}
        for violation in mpg_violations:
            method = violation.get('detection_method', 'unknown')
            if method not in by_method:
                by_method[method] = []
            by_method[method].append(violation)
        
        summary = {
            'total_mpg_violations': total_violations,
            'total_estimated_weekly_loss': total_estimated_loss,
            'violations_by_method': {
                method: {
                    'count': len(violations),
                    'total_loss': sum(v.get('estimated_loss', 0) for v in violations),
                    'avg_mpg': sum(v.get('actual_mpg', 0) for v in violations) / len(violations)
                }
                for method, violations in by_method.items()
            },
            'worst_performing_vehicle': max(
                mpg_violations, 
                key=lambda x: x.get('estimated_loss', 0)
            )['vehicle_id'] if mpg_violations else None
        }
        
        return summary