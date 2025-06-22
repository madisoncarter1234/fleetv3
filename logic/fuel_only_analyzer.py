import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics

class FuelOnlyAnalyzer:
    """Advanced fuel pattern analysis for fuel-card-only data"""
    
    def __init__(self):
        self.violations = []
        self.baseline_days = 14  # Days to establish baseline patterns
    
    def analyze_fuel_patterns(self, fuel_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Run comprehensive fuel-only analysis"""
        
        if fuel_df is None or fuel_df.empty:
            return {'fuel_anomalies': []}
        
        violations = []
        
        # Ensure timestamp is datetime
        fuel_df['timestamp'] = pd.to_datetime(fuel_df['timestamp'])
        
        # Run all fuel-only detection methods
        violations.extend(self.detect_time_anomalies(fuel_df))
        violations.extend(self.detect_volume_anomalies(fuel_df))
        violations.extend(self.detect_frequency_anomalies(fuel_df))
        violations.extend(self.detect_location_anomalies(fuel_df))
        violations.extend(self.detect_impossible_scenarios(fuel_df))
        
        return {'fuel_anomalies': violations}
    
    def detect_time_anomalies(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Detect suspicious timing patterns"""
        violations = []
        
        for _, purchase in fuel_df.iterrows():
            timestamp = purchase['timestamp']
            hour = timestamp.hour
            day_of_week = timestamp.weekday()  # 0 = Monday, 6 = Sunday
            
            # Flag purchases during unusual hours
            if hour < 5 or hour > 22:  # 10 PM to 5 AM
                violations.append({
                    'vehicle_id': purchase['vehicle_id'],
                    'timestamp': timestamp,
                    'violation_type': 'fuel_anomalies',
                    'anomaly_type': 'unusual_hours',
                    'description': f"Fuel purchase at {hour:02d}:{timestamp.minute:02d} - outside normal business hours",
                    'location': purchase['location'],
                    'gallons': purchase['gallons'],
                    'severity': 'medium'
                })
            
            # Flag weekend purchases for business fleets
            if day_of_week >= 5:  # Saturday or Sunday
                violations.append({
                    'vehicle_id': purchase['vehicle_id'],
                    'timestamp': timestamp,
                    'violation_type': 'fuel_anomalies',
                    'anomaly_type': 'weekend_purchase',
                    'description': f"Fuel purchase on {timestamp.strftime('%A')} - unusual for business fleet",
                    'location': purchase['location'],
                    'gallons': purchase['gallons'],
                    'severity': 'low'
                })
        
        return violations
    
    def detect_volume_anomalies(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Detect unusual fuel volume patterns"""
        violations = []
        
        # Group by vehicle to analyze patterns
        for vehicle_id, vehicle_data in fuel_df.groupby('vehicle_id'):
            if len(vehicle_data) < 3:  # Need minimum data for pattern analysis
                continue
            
            volumes = vehicle_data['gallons'].dropna()
            if volumes.empty:
                continue
            
            # Calculate baseline statistics
            mean_volume = volumes.mean()
            std_volume = volumes.std()
            
            if std_volume == 0:  # All purchases same volume
                continue
            
            # Flag unusually large purchases (3 standard deviations above mean)
            threshold_high = mean_volume + (3 * std_volume)
            
            for _, purchase in vehicle_data.iterrows():
                if pd.notna(purchase['gallons']) and purchase['gallons'] > threshold_high:
                    violations.append({
                        'vehicle_id': vehicle_id,
                        'timestamp': purchase['timestamp'],
                        'violation_type': 'fuel_anomalies',
                        'anomaly_type': 'excessive_volume',
                        'description': f"Unusually large fuel purchase: {purchase['gallons']} gallons (normal: {mean_volume:.1f}±{std_volume:.1f})",
                        'location': purchase['location'],
                        'gallons': purchase['gallons'],
                        'severity': 'high'
                    })
        
        return violations
    
    def detect_frequency_anomalies(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Detect unusual purchase frequency patterns"""
        violations = []
        
        # Group by vehicle to analyze frequency
        for vehicle_id, vehicle_data in fuel_df.groupby('vehicle_id'):
            if len(vehicle_data) < 4:  # Need minimum data
                continue
            
            # Sort by timestamp
            vehicle_data = vehicle_data.sort_values('timestamp')
            
            # Calculate time between purchases
            time_diffs = []
            for i in range(1, len(vehicle_data)):
                diff = (vehicle_data.iloc[i]['timestamp'] - vehicle_data.iloc[i-1]['timestamp']).days
                time_diffs.append(diff)
            
            if not time_diffs:
                continue
            
            avg_days_between = statistics.mean(time_diffs)
            
            # Flag multiple purchases same day
            daily_counts = vehicle_data.groupby(vehicle_data['timestamp'].dt.date).size()
            multiple_purchase_days = daily_counts[daily_counts > 1]
            
            for date, count in multiple_purchase_days.items():
                day_purchases = vehicle_data[vehicle_data['timestamp'].dt.date == date]
                total_gallons = day_purchases['gallons'].sum()
                
                violations.append({
                    'vehicle_id': vehicle_id,
                    'timestamp': datetime.combine(date, datetime.min.time()),
                    'violation_type': 'fuel_anomalies',
                    'anomaly_type': 'multiple_daily_purchases',
                    'description': f"{count} fuel purchases in one day totaling {total_gallons:.1f} gallons - suspicious frequency",
                    'location': 'Multiple locations',
                    'gallons': total_gallons,
                    'severity': 'high'
                })
        
        return violations
    
    def detect_location_anomalies(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Detect unusual location patterns"""
        violations = []
        
        # Group by vehicle to analyze location patterns
        for vehicle_id, vehicle_data in fuel_df.groupby('vehicle_id'):
            if len(vehicle_data) < 5:  # Need minimum data
                continue
            
            # Get location frequency
            location_counts = vehicle_data['location'].value_counts()
            total_purchases = len(vehicle_data)
            
            # Flag locations used only once (outliers)
            rare_locations = location_counts[location_counts == 1]
            
            for location in rare_locations.index:
                purchase = vehicle_data[vehicle_data['location'] == location].iloc[0]
                
                # Only flag if vehicle has established pattern at other locations
                if len(location_counts) > 3:  # Has used multiple locations
                    violations.append({
                        'vehicle_id': vehicle_id,
                        'timestamp': purchase['timestamp'],
                        'violation_type': 'fuel_anomalies',
                        'anomaly_type': 'unusual_location',
                        'description': f"One-time fuel purchase at unfamiliar location: {location}",
                        'location': purchase['location'],
                        'gallons': purchase['gallons'],
                        'severity': 'medium'
                    })
        
        return violations
    
    def detect_impossible_scenarios(self, fuel_df: pd.DataFrame) -> List[Dict]:
        """Detect physically impossible scenarios"""
        violations = []
        
        # Sort by timestamp for sequence analysis
        fuel_df_sorted = fuel_df.sort_values(['vehicle_id', 'timestamp'])
        
        # Group by vehicle for sequential analysis
        for vehicle_id, vehicle_data in fuel_df_sorted.groupby('vehicle_id'):
            vehicle_data = vehicle_data.reset_index(drop=True)
            
            for i in range(len(vehicle_data) - 1):
                current = vehicle_data.iloc[i]
                next_purchase = vehicle_data.iloc[i + 1]
                
                time_diff = (next_purchase['timestamp'] - current['timestamp']).total_seconds() / 3600  # hours
                
                # Flag purchases too close together in time
                if time_diff < 2:  # Less than 2 hours apart
                    total_gallons = current['gallons'] + next_purchase['gallons']
                    
                    violations.append({
                        'vehicle_id': vehicle_id,
                        'timestamp': next_purchase['timestamp'],
                        'violation_type': 'fuel_anomalies',
                        'anomaly_type': 'rapid_succession',
                        'description': f"Two fuel purchases {time_diff:.1f} hours apart totaling {total_gallons:.1f} gallons - suspicious timing",
                        'location': f"{current['location']} → {next_purchase['location']}",
                        'gallons': total_gallons,
                        'severity': 'high'
                    })
        
        return violations
    
    def generate_fuel_insights(self, fuel_df: pd.DataFrame) -> Dict:
        """Generate summary insights from fuel data"""
        if fuel_df.empty:
            return {}
        
        insights = {
            'total_vehicles': fuel_df['vehicle_id'].nunique(),
            'total_purchases': len(fuel_df),
            'total_gallons': fuel_df['gallons'].sum(),
            'date_range': {
                'start': fuel_df['timestamp'].min(),
                'end': fuel_df['timestamp'].max()
            },
            'most_active_vehicle': fuel_df['vehicle_id'].value_counts().index[0] if not fuel_df.empty else None,
            'average_purchase_size': fuel_df['gallons'].mean(),
            'unique_locations': fuel_df['location'].nunique()
        }
        
        return insights