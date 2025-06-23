import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

class EnhancedFuelDetector:
    """Advanced fuel theft detection using volume, price, and behavioral analysis"""
    
    def __init__(self):
        self.violations = []
        # Average fuel prices (could be made dynamic with API)
        self.avg_fuel_price = 3.75  # dollars per gallon (updated 2024)
        self.price_tolerance = 0.40  # +/- 40 cents per gallon tolerance (regional variation)
        
        # More realistic commercial vehicle tank capacities
        self.default_tank_capacity = 40.0  # gallons (commercial vehicle average)
        self.vehicle_capacities = {
            # Could be loaded from vehicle database
            # 'TRUCK-001': 30.0,
            # 'VAN-002': 20.0,
        }
    
    def detect_enhanced_fuel_theft(self, fuel_df: pd.DataFrame, gps_df: pd.DataFrame = None) -> List[Dict]:
        """
        Enhanced fuel theft detection with graceful degradation:
        - Automatically adapts to available data quality
        - Provides best possible detection for each customer's data
        - Clear confidence levels based on data completeness
        """
        violations = []
        
        if fuel_df is None or fuel_df.empty:
            return violations
        
        # Prepare and analyze data quality
        fuel_df = self._prepare_fuel_data(fuel_df)
        data_tier = self._assess_data_quality(fuel_df)
        
        # Apply detection methods based on data tier
        if data_tier['tier'] >= 1:  # Has both amount and gallons
            violations.extend(self._detect_volume_violations(fuel_df))
            violations.extend(self._detect_price_violations(fuel_df))
            violations.extend(self._detect_pattern_violations(fuel_df))
            violations.extend(self._detect_frequency_violations(fuel_df))
            
        elif data_tier['tier'] >= 2:  # Has amount only
            violations.extend(self._detect_amount_only_violations(fuel_df))
            violations.extend(self._detect_pattern_violations(fuel_df))
            violations.extend(self._detect_frequency_violations(fuel_df))
            
        elif data_tier['tier'] >= 3:  # Has gallons only
            violations.extend(self._detect_volume_violations(fuel_df))
            violations.extend(self._detect_pattern_violations(fuel_df))
            
        else:  # Minimal data - timing/frequency only
            violations.extend(self._detect_basic_violations(fuel_df))
        
        # Add data quality context to violations
        for violation in violations:
            violation['data_tier'] = data_tier['tier']
            violation['data_quality'] = data_tier['description']
            
            # Adjust confidence based on data quality
            if 'confidence' in violation:
                violation['confidence'] *= data_tier['confidence_multiplier']
        
        # Add GPS validation if available (boosts confidence)
        if gps_df is not None and not gps_df.empty:
            gps_violations = self._detect_location_violations(fuel_df, gps_df)
            for violation in gps_violations:
                violation['confidence'] = min(0.95, violation.get('confidence', 0.8) + 0.1)
            violations.extend(gps_violations)
        
        return violations
    
    def _assess_data_quality(self, fuel_df: pd.DataFrame) -> Dict:
        """Assess the quality of fuel data and determine detection tier"""
        
        has_amount = 'amount' in fuel_df.columns and not fuel_df['amount'].isna().all()
        has_gallons = 'gallons' in fuel_df.columns and not fuel_df['gallons'].isna().all()
        has_location = 'location' in fuel_df.columns and not fuel_df['location'].isna().all()
        has_timestamp = 'timestamp' in fuel_df.columns and not fuel_df['timestamp'].isna().all()
        
        if has_amount and has_gallons:
            return {
                'tier': 1,
                'description': 'Premium Data Quality (Amount + Gallons)',
                'confidence_multiplier': 1.0,
                'capabilities': ['volume_analysis', 'price_analysis', 'pattern_analysis', 'frequency_analysis']
            }
        elif has_amount:
            return {
                'tier': 2, 
                'description': 'Good Data Quality (Amount Only)',
                'confidence_multiplier': 0.8,
                'capabilities': ['amount_analysis', 'pattern_analysis', 'frequency_analysis']
            }
        elif has_gallons:
            return {
                'tier': 3,
                'description': 'Moderate Data Quality (Gallons Only)', 
                'confidence_multiplier': 0.7,
                'capabilities': ['volume_analysis', 'pattern_analysis']
            }
        else:
            return {
                'tier': 4,
                'description': 'Basic Data Quality (Timing Only)',
                'confidence_multiplier': 0.5,
                'capabilities': ['timing_analysis', 'basic_patterns']
            }
    
    def _prepare_fuel_data(self, fuel_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate fuel data"""
        df = fuel_df.copy()
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Extract or calculate amount if missing
        if 'amount' not in df.columns and 'gallons' in df.columns:
            # Estimate amount if not provided
            df['amount'] = df['gallons'] * self.avg_fuel_price
        
        # Clean and validate numeric columns
        df['gallons'] = pd.to_numeric(df['gallons'], errors='coerce')
        if 'amount' in df.columns:
            # Remove dollar signs and convert to float
            df['amount'] = df['amount'].astype(str).str.replace('$', '').str.replace(',', '')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        return df
    
    def _detect_volume_violations(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Detect violations based on fuel volume analysis"""
        violations = []
        
        for vehicle_id, vehicle_data in fuel_df.groupby('vehicle_id'):
            tank_capacity = self.vehicle_capacities.get(vehicle_id, self.default_tank_capacity)
            vehicle_data = vehicle_data.sort_values('timestamp')
            
            for idx, purchase in vehicle_data.iterrows():
                gallons = purchase['gallons']
                
                if pd.isna(gallons) or gallons <= 0:
                    continue
                
                # Check 1: Single purchase exceeds tank capacity
                if gallons > tank_capacity:
                    violations.append({
                        'vehicle_id': vehicle_id,
                        'timestamp': purchase['timestamp'],
                        'violation_type': 'fuel_theft',
                        'detection_method': 'volume_excess',
                        'description': f"Purchase of {gallons:.1f} gallons exceeds tank capacity ({tank_capacity} gallons) - likely filling personal vehicle too",
                        'location': purchase['location'],
                        'gallons': gallons,
                        'severity': 'high',
                        'confidence': 0.95
                    })
                
                # Check 2: Overwhelmingly obvious rapid refill scenarios
                previous_purchases = vehicle_data[vehicle_data['timestamp'] < purchase['timestamp']]
                if not previous_purchases.empty:
                    last_purchase = previous_purchases.iloc[-1]
                    hours_since_last = (purchase['timestamp'] - last_purchase['timestamp']).total_seconds() / 3600
                    
                    # Only flag if EXTREMELY suspicious (much higher thresholds)
                    suspicious_conditions = [
                        # Condition 1: Massive purchase after recent fill-up
                        (hours_since_last < 12 and  # Very recent
                         last_purchase['gallons'] > (tank_capacity * 0.9) and  # Almost full tank
                         gallons > (tank_capacity * 1.2)),  # Buying way more than capacity
                        
                        # Condition 2: Two huge purchases same day
                        (hours_since_last < 8 and  # Same work day
                         last_purchase['gallons'] > tank_capacity and  # Already exceeded capacity
                         gallons > tank_capacity),  # Doing it again
                        
                        # Condition 3: Overnight fill-up followed by morning excess
                        (hours_since_last < 16 and  # Since yesterday evening
                         last_purchase['timestamp'].hour >= 18 and  # Evening purchase  
                         purchase['timestamp'].hour <= 10 and  # Morning purchase
                         last_purchase['gallons'] > (tank_capacity * 0.8) and  # Good fill-up
                         gallons > (tank_capacity * 0.9))  # Another near-full tank
                    ]
                    
                    if any(suspicious_conditions):
                        total_gallons = last_purchase['gallons'] + gallons
                        
                        # Check for potential emergency scenarios (reduce confidence)
                        confidence = 0.95
                        note = ""
                        
                        # Emergency indicators: very small previous purchase (ran out of gas)
                        if last_purchase['gallons'] < 5 and hours_since_last < 2:
                            confidence = 0.60
                            note = " - May be emergency refueling after running out of gas"
                        
                        # Different locations suggest legitimate travel
                        elif purchase['location'] != last_purchase['location']:
                            confidence = 0.80
                            note = " - Different locations may indicate legitimate travel"
                        
                        violations.append({
                            'vehicle_id': vehicle_id,
                            'timestamp': purchase['timestamp'],
                            'violation_type': 'fuel_theft',
                            'detection_method': 'obvious_rapid_refill',
                            'description': f"Extremely suspicious: {gallons:.1f} gallons purchased only {hours_since_last:.1f} hours after {last_purchase['gallons']:.1f} gallon purchase. Total: {total_gallons:.1f} gallons in {hours_since_last:.1f} hours - far exceeds normal vehicle consumption{note}",
                            'location': purchase['location'],
                            'gallons': gallons,
                            'previous_gallons': last_purchase['gallons'],
                            'hours_between': hours_since_last,
                            'total_gallons': total_gallons,
                            'severity': 'high' if confidence > 0.8 else 'medium',
                            'confidence': confidence
                        })
        
        return violations
    
    def _detect_price_violations(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Detect violations based on price analysis"""
        violations = []
        
        for idx, purchase in fuel_df.iterrows():
            if pd.isna(purchase['gallons']) or pd.isna(purchase.get('amount')):
                continue
            
            gallons = purchase['gallons']
            amount = purchase['amount']
            
            if gallons <= 0 or amount <= 0:
                continue
            
            # Calculate price per gallon
            price_per_gallon = amount / gallons
            
            # Expected cost range
            min_expected = gallons * (self.avg_fuel_price - self.price_tolerance)
            max_expected = gallons * (self.avg_fuel_price + self.price_tolerance)
            
            # Check for excessive cost (indicates non-fuel purchases)
            if amount > max_expected * 1.5:  # 50% over expected range (was 30% - too sensitive)
                excess_amount = amount - max_expected
                
                # Reduce confidence for potential DEF fluid or equipment purchases
                confidence = 0.75
                note = ""
                
                # DEF fluid detection (smaller amounts, specific price ranges)
                if 15 <= amount <= 60 and gallons < 15:
                    confidence = 0.45
                    note = " - May be DEF fluid or equipment fuel"
                
                violations.append({
                    'vehicle_id': purchase['vehicle_id'],
                    'timestamp': purchase['timestamp'],
                    'violation_type': 'fuel_theft',
                    'detection_method': 'price_excess',
                    'description': f"Transaction cost ${amount:.2f} is ${excess_amount:.2f} more than expected for {gallons:.1f} gallons (${price_per_gallon:.2f}/gal vs expected ~${self.avg_fuel_price:.2f}/gal) - likely includes non-fuel purchases{note}",
                    'location': purchase['location'],
                    'gallons': gallons,
                    'amount': amount,
                    'excess_cost': excess_amount,
                    'severity': 'medium' if confidence > 0.6 else 'low',
                    'confidence': confidence
                })
            
            # Check for extremely high price per gallon (premium fuel + extras)
            elif price_per_gallon > (self.avg_fuel_price + 2.00):  # $2.00 over average (was $1.50 - account for premium diesel)
                violations.append({
                    'vehicle_id': purchase['vehicle_id'],
                    'timestamp': purchase['timestamp'],
                    'violation_type': 'fuel_theft',
                    'detection_method': 'price_premium',
                    'description': f"Very high price per gallon: ${price_per_gallon:.2f} vs expected ~${self.avg_fuel_price:.2f} - may include premium fuel, services, or non-fuel items",
                    'location': purchase['location'],
                    'gallons': gallons,
                    'amount': amount,
                    'price_per_gallon': price_per_gallon,
                    'severity': 'low',
                    'confidence': 0.50  # Lower confidence for price-only anomalies
                })
        
        return violations
    
    def _detect_pattern_violations(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Detect violations based on driver behavioral patterns"""
        violations = []
        
        for vehicle_id, vehicle_data in fuel_df.groupby('vehicle_id'):
            if len(vehicle_data) < 5:  # Need minimum history for pattern analysis
                continue
            
            # Calculate baseline statistics
            amounts = vehicle_data['amount'].dropna()
            gallons = vehicle_data['gallons'].dropna()
            
            if amounts.empty or gallons.empty:
                continue
            
            avg_amount = amounts.mean()
            std_amount = amounts.std()
            avg_gallons = gallons.mean()
            std_gallons = gallons.std()
            
            # Skip if no variation (not enough data)
            if std_amount == 0 or std_gallons == 0:
                continue
            
            # Check each purchase against driver's pattern
            for idx, purchase in vehicle_data.iterrows():
                if pd.isna(purchase['amount']) or pd.isna(purchase['gallons']):
                    continue
                
                amount_zscore = abs((purchase['amount'] - avg_amount) / std_amount)
                gallons_zscore = abs((purchase['gallons'] - avg_gallons) / std_gallons)
                
                # Flag purchases that are statistical outliers (3+ standard deviations)
                if amount_zscore > 3.0 and purchase['amount'] > avg_amount:
                    violations.append({
                        'vehicle_id': vehicle_id,
                        'timestamp': purchase['timestamp'],
                        'violation_type': 'fuel_theft',
                        'detection_method': 'pattern_deviation',
                        'description': f"Purchase amount ${purchase['amount']:.2f} significantly exceeds driver's normal pattern (avg: ${avg_amount:.2f}, this is {amount_zscore:.1f} std deviations above normal)",
                        'location': purchase['location'],
                        'gallons': purchase['gallons'],
                        'amount': purchase['amount'],
                        'deviation_score': amount_zscore,
                        'severity': 'medium',
                        'confidence': 0.70
                    })
        
        return violations
    
    def _detect_frequency_violations(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Detect violations based on purchase frequency"""
        violations = []
        
        for vehicle_id, vehicle_data in fuel_df.groupby('vehicle_id'):
            vehicle_data = vehicle_data.sort_values('timestamp')
            
            # Check for multiple purchases same day
            daily_groups = vehicle_data.groupby(vehicle_data['timestamp'].dt.date)
            
            for date, day_purchases in daily_groups:
                if len(day_purchases) > 1:
                    total_gallons = day_purchases['gallons'].sum()
                    total_amount = day_purchases['amount'].sum() if 'amount' in day_purchases.columns else None
                    
                    # Get tank capacity
                    tank_capacity = self.vehicle_capacities.get(vehicle_id, self.default_tank_capacity)
                    
                    # Flag if total daily purchases exceed reasonable amount
                    if total_gallons > tank_capacity * 2.0:  # Increased from 1.5x to 2.0x (more conservative)
                        
                        # Check for legitimate multi-purchase scenarios
                        confidence = 0.85
                        note = ""
                        
                        # Small individual purchases suggest equipment/multiple vehicles
                        avg_purchase = total_gallons / len(day_purchases)
                        if avg_purchase < tank_capacity * 0.3:  # Small individual purchases
                            confidence = 0.60
                            note = " - Small purchases may indicate equipment refueling or multiple vehicles"
                        
                        # Many small purchases in one day
                        elif len(day_purchases) >= 4 and avg_purchase < tank_capacity * 0.5:
                            confidence = 0.55
                            note = " - Multiple small purchases may be legitimate equipment/fleet operations"
                        
                        violations.append({
                            'vehicle_id': vehicle_id,
                            'timestamp': day_purchases['timestamp'].min(),
                            'violation_type': 'fuel_theft',
                            'detection_method': 'daily_excess',
                            'description': f"{len(day_purchases)} purchases on {date} totaling {total_gallons:.1f} gallons - significantly exceeds vehicle capacity ({tank_capacity} gal) suggesting personal use{note}",
                            'location': 'Multiple locations',
                            'gallons': total_gallons,
                            'amount': total_amount,
                            'purchase_count': len(day_purchases),
                            'severity': 'high' if confidence > 0.7 else 'medium',
                            'confidence': confidence
                        })
        
        return violations
    
    def _detect_location_violations(self, fuel_df: pd.DataFrame, gps_df: pd.DataFrame) -> List[Dict]:
        """Enhanced GPS-based detection with additional context"""
        violations = []
        
        # This would integrate with the existing GPS detection but add context
        # from volume and price analysis to strengthen confidence scores
        
        # For now, return empty - this would enhance the existing GPS detection
        # by adding confidence scores based on volume/price red flags
        
        return violations
    
    def _detect_amount_only_violations(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Detect violations using only dollar amounts (estimate gallons)"""
        violations = []
        
        for vehicle_id, vehicle_data in fuel_df.groupby('vehicle_id'):
            vehicle_data = vehicle_data.sort_values('timestamp')
            
            for idx, purchase in vehicle_data.iterrows():
                if pd.isna(purchase.get('amount')) or purchase['amount'] <= 0:
                    continue
                
                # Estimate gallons from amount
                estimated_gallons = purchase['amount'] / self.avg_fuel_price
                tank_capacity = self.vehicle_capacities.get(vehicle_id, self.default_tank_capacity)
                
                # Only flag overwhelmingly obvious volume excess (much higher threshold)
                if estimated_gallons > tank_capacity * 1.6:  # 60% over capacity (was 20%)
                    violations.append({
                        'vehicle_id': vehicle_id,
                        'timestamp': purchase['timestamp'],
                        'violation_type': 'fuel_theft',
                        'detection_method': 'estimated_volume_excess',
                        'description': f"Purchase amount ${purchase['amount']:.2f} suggests ~{estimated_gallons:.1f} gallons (estimated), far exceeding tank capacity ({tank_capacity} gal) - likely filling multiple vehicles or personal purchases",
                        'location': purchase['location'],
                        'amount': purchase['amount'],
                        'estimated_gallons': estimated_gallons,
                        'severity': 'high',
                        'confidence': 0.80
                    })
                
                # Check for overwhelmingly obvious amount deviations (higher threshold)
                vehicle_amounts = vehicle_data['amount'].dropna()
                if len(vehicle_amounts) >= 5:  # Need more history (was 3)
                    avg_amount = vehicle_amounts.mean()
                    if purchase['amount'] > avg_amount * 3:  # 3x normal (was 2x)
                        violations.append({
                            'vehicle_id': vehicle_id,
                            'timestamp': purchase['timestamp'],
                            'violation_type': 'fuel_theft',
                            'detection_method': 'extreme_amount_deviation',
                            'description': f"Purchase amount ${purchase['amount']:.2f} is extremely high compared to vehicle's typical ${avg_amount:.2f} (3x normal) - likely includes significant non-fuel purchases",
                            'location': purchase['location'],
                            'amount': purchase['amount'],
                            'typical_amount': avg_amount,
                            'severity': 'high',
                            'confidence': 0.85
                        })
        
        return violations
    
    def _detect_basic_violations(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Basic detection using only timing and frequency patterns"""
        violations = []
        
        # Group by vehicle for frequency analysis
        for vehicle_id, vehicle_data in fuel_df.groupby('vehicle_id'):
            vehicle_data = vehicle_data.sort_values('timestamp')
            
            # Check for multiple purchases same day
            daily_groups = vehicle_data.groupby(vehicle_data['timestamp'].dt.date)
            
            for date, day_purchases in daily_groups:
                if len(day_purchases) > 2:  # More than 2 purchases per day is suspicious
                    violations.append({
                        'vehicle_id': vehicle_id,
                        'timestamp': day_purchases['timestamp'].min(),
                        'violation_type': 'fuel_theft',
                        'detection_method': 'frequency_anomaly',
                        'description': f"{len(day_purchases)} fuel card transactions on {date} - unusual frequency may indicate personal use or fraud",
                        'location': 'Multiple locations',
                        'purchase_count': len(day_purchases),
                        'severity': 'low',
                        'confidence': 0.50
                    })
            
            # Check for unusual timing
            for idx, purchase in vehicle_data.iterrows():
                hour = purchase['timestamp'].hour
                day_of_week = purchase['timestamp'].weekday()
                
                # Flag very early morning or late night purchases
                if hour < 5 or hour > 23:
                    violations.append({
                        'vehicle_id': vehicle_id,
                        'timestamp': purchase['timestamp'],
                        'violation_type': 'fuel_theft',
                        'detection_method': 'timing_anomaly',
                        'description': f"Fuel purchase at {hour:02d}:{purchase['timestamp'].minute:02d} - outside typical business hours",
                        'location': purchase['location'],
                        'severity': 'low',
                        'confidence': 0.45
                    })
        
        return violations
    
    def get_data_quality_summary(self, fuel_df: pd.DataFrame) -> Dict:
        """Generate summary of data quality and detection capabilities"""
        if fuel_df is None or fuel_df.empty:
            return {'tier': 0, 'description': 'No data available'}
        
        data_tier = self._assess_data_quality(fuel_df)
        
        summary = {
            'data_tier': data_tier['tier'],
            'description': data_tier['description'],
            'confidence_multiplier': data_tier['confidence_multiplier'],
            'capabilities': data_tier['capabilities'],
            'total_records': len(fuel_df),
            'date_range': {
                'start': fuel_df['timestamp'].min() if 'timestamp' in fuel_df.columns else None,
                'end': fuel_df['timestamp'].max() if 'timestamp' in fuel_df.columns else None
            },
            'improvement_suggestions': self._get_improvement_suggestions(data_tier)
        }
        
        return summary
    
    def _get_improvement_suggestions(self, data_tier: Dict) -> List[str]:
        """Suggest how customer can improve their data quality"""
        suggestions = []
        
        if data_tier['tier'] == 4:
            suggestions.extend([
                "Add fuel amount or gallon data to enable volume analysis",
                "Include transaction amounts to detect price anomalies",
                "Consider upgrading to a fuel card that tracks gallons"
            ])
        elif data_tier['tier'] == 3:
            suggestions.extend([
                "Add transaction amounts to enable price analysis",
                "Include cost data to detect mixed purchases (fuel + personal items)"
            ])
        elif data_tier['tier'] == 2:
            suggestions.extend([
                "Add gallon quantities to enable precise volume analysis",
                "Include fuel quantities to detect tank capacity violations"
            ])
        elif data_tier['tier'] == 1:
            suggestions.extend([
                "Add GPS tracking for location-based validation",
                "Consider real-time fuel price data for more accurate analysis"
            ])
        
        return suggestions
    
    def get_enhanced_summary(self, violations: List[Dict]) -> Dict:
        """Generate summary with confidence levels and financial impact"""
        if not violations:
            return {}
        
        # Group by detection method
        by_method = {}
        total_suspected_loss = 0
        
        for violation in violations:
            method = violation.get('detection_method', 'unknown')
            if method not in by_method:
                by_method[method] = []
            by_method[method].append(violation)
            
            # Estimate financial impact
            if 'excess_cost' in violation:
                total_suspected_loss += violation['excess_cost']
            elif 'amount' in violation and violation.get('confidence', 0) > 0.8:
                # For high-confidence violations, estimate 20% of transaction as fraud
                total_suspected_loss += violation['amount'] * 0.20
        
        summary = {
            'total_violations': len(violations),
            'by_detection_method': {method: len(viols) for method, viols in by_method.items()},
            'high_confidence_violations': len([v for v in violations if v.get('confidence', 0) > 0.8]),
            'estimated_monthly_loss': total_suspected_loss * 4,  # Weekly * 4
            'most_common_method': max(by_method.keys(), key=lambda k: len(by_method[k])) if by_method else None
        }
        
        return summary