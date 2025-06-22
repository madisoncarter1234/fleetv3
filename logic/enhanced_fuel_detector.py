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
        self.avg_fuel_price = 3.50  # dollars per gallon
        self.price_tolerance = 0.25  # +/- 25 cents per gallon tolerance
        
        # Common vehicle tank capacities (could be vehicle-specific)
        self.default_tank_capacity = 25.0  # gallons
        self.vehicle_capacities = {
            # Could be loaded from vehicle database
            # 'TRUCK-001': 30.0,
            # 'VAN-002': 20.0,
        }
    
    def detect_enhanced_fuel_theft(self, fuel_df: pd.DataFrame, gps_df: pd.DataFrame = None) -> List[Dict]:
        """
        Enhanced fuel theft detection using multiple layers:
        1. Volume analysis (tank capacity, refill frequency)
        2. Price analysis (cost vs gallons)
        3. Behavioral patterns (driver baselines)
        4. GPS validation (if available)
        """
        violations = []
        
        if fuel_df is None or fuel_df.empty:
            return violations
        
        # Ensure required columns exist and have proper types
        fuel_df = self._prepare_fuel_data(fuel_df)
        
        # Run all detection layers
        violations.extend(self._detect_volume_violations(fuel_df))
        violations.extend(self._detect_price_violations(fuel_df))
        violations.extend(self._detect_pattern_violations(fuel_df))
        violations.extend(self._detect_frequency_violations(fuel_df))
        
        # Add GPS validation if available
        if gps_df is not None and not gps_df.empty:
            violations.extend(self._detect_location_violations(fuel_df, gps_df))
        
        return violations
    
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
                
                # Check 2: Rapid refill (tank should still be full)
                previous_purchases = vehicle_data[vehicle_data['timestamp'] < purchase['timestamp']]
                if not previous_purchases.empty:
                    last_purchase = previous_purchases.iloc[-1]
                    hours_since_last = (purchase['timestamp'] - last_purchase['timestamp']).total_seconds() / 3600
                    
                    # If last purchase was large and recent, current large purchase is suspicious
                    if (hours_since_last < 24 and 
                        last_purchase['gallons'] > (tank_capacity * 0.8) and 
                        gallons > (tank_capacity * 0.6)):
                        
                        violations.append({
                            'vehicle_id': vehicle_id,
                            'timestamp': purchase['timestamp'],
                            'violation_type': 'fuel_theft',
                            'detection_method': 'rapid_refill',
                            'description': f"Large refill ({gallons:.1f} gal) only {hours_since_last:.1f} hours after previous large purchase ({last_purchase['gallons']:.1f} gal) - tank should still be full",
                            'location': purchase['location'],
                            'gallons': gallons,
                            'severity': 'high',
                            'confidence': 0.90
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
            if amount > max_expected * 1.3:  # 30% over expected range
                excess_amount = amount - max_expected
                
                violations.append({
                    'vehicle_id': purchase['vehicle_id'],
                    'timestamp': purchase['timestamp'],
                    'violation_type': 'fuel_theft',
                    'detection_method': 'price_excess',
                    'description': f"Transaction cost ${amount:.2f} is ${excess_amount:.2f} more than expected for {gallons:.1f} gallons (${price_per_gallon:.2f}/gal vs expected ~${self.avg_fuel_price:.2f}/gal) - likely includes non-fuel purchases",
                    'location': purchase['location'],
                    'gallons': gallons,
                    'amount': amount,
                    'excess_cost': excess_amount,
                    'severity': 'medium',
                    'confidence': 0.75
                })
            
            # Check for extremely high price per gallon (premium fuel + extras)
            elif price_per_gallon > (self.avg_fuel_price + 1.50):  # $1.50 over average
                violations.append({
                    'vehicle_id': purchase['vehicle_id'],
                    'timestamp': purchase['timestamp'],
                    'violation_type': 'fuel_theft',
                    'detection_method': 'price_premium',
                    'description': f"Extremely high price per gallon: ${price_per_gallon:.2f} vs expected ~${self.avg_fuel_price:.2f} - may include premium services or non-fuel items",
                    'location': purchase['location'],
                    'gallons': gallons,
                    'amount': amount,
                    'price_per_gallon': price_per_gallon,
                    'severity': 'low',
                    'confidence': 0.60
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
                    if total_gallons > tank_capacity * 1.5:
                        violations.append({
                            'vehicle_id': vehicle_id,
                            'timestamp': day_purchases['timestamp'].min(),
                            'violation_type': 'fuel_theft',
                            'detection_method': 'daily_excess',
                            'description': f"{len(day_purchases)} purchases on {date} totaling {total_gallons:.1f} gallons - exceeds vehicle capacity ({tank_capacity} gal) suggesting personal use",
                            'location': 'Multiple locations',
                            'gallons': total_gallons,
                            'amount': total_amount,
                            'purchase_count': len(day_purchases),
                            'severity': 'high',
                            'confidence': 0.85
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