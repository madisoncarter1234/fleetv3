import pandas as pd
from datetime import datetime, timedelta
from haversine import haversine, Unit
from typing import Tuple, List, Dict, Optional

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in miles using haversine formula"""
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return float('inf')
    
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)
    return haversine(point1, point2, unit=Unit.MILES)

def is_within_time_window(timestamp1: datetime, timestamp2: datetime, window_minutes: int = 15) -> bool:
    """Check if two timestamps are within specified time window"""
    if pd.isna(timestamp1) or pd.isna(timestamp2):
        return False
    
    time_diff = abs((timestamp1 - timestamp2).total_seconds() / 60)
    return time_diff <= window_minutes

def is_within_distance(lat1: float, lon1: float, lat2: float, lon2: float, max_distance_miles: float = 1.0) -> bool:
    """Check if two coordinates are within specified distance"""
    distance = calculate_distance(lat1, lon1, lat2, lon2)
    return distance <= max_distance_miles

def geocode_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    """Simple geocoding placeholder - in production use Google Maps API or similar"""
    # This is a placeholder - implement with actual geocoding service
    # For MVP, you might want to manually add coordinates for known job sites
    # or use a simple geocoding library like geopy
    return None, None

def is_business_hours(timestamp: datetime, start_hour: int = 7, end_hour: int = 18) -> bool:
    """Check if timestamp falls within business hours"""
    if pd.isna(timestamp):
        return False
    
    # Only check weekdays (Monday=0, Sunday=6)
    if timestamp.weekday() >= 5:  # Weekend
        return False
    
    hour = timestamp.hour
    return start_hour <= hour <= end_hour

def find_gps_near_location(gps_df: pd.DataFrame, lat: float, lon: float, 
                          timestamp: datetime, distance_miles: float = 1.0, 
                          time_window_minutes: int = 15) -> pd.DataFrame:
    """Find GPS records near a specific location and time"""
    if lat is None or lon is None:
        return pd.DataFrame()
    
    # Filter by time window first (more efficient)
    time_mask = gps_df['timestamp'].apply(
        lambda t: is_within_time_window(t, timestamp, time_window_minutes)
    )
    time_filtered = gps_df[time_mask]
    
    if time_filtered.empty:
        return pd.DataFrame()
    
    # Then filter by distance
    distance_mask = time_filtered.apply(
        lambda row: is_within_distance(row['lat'], row['lon'], lat, lon, distance_miles),
        axis=1
    )
    
    return time_filtered[distance_mask]

def detect_idle_periods(gps_df: pd.DataFrame, min_idle_minutes: int = 10, 
                       max_speed_mph: float = 3) -> List[Dict]:
    """Detect periods where vehicle was idle for extended time"""
    idle_periods = []
    
    # Group by vehicle
    for vehicle_id, vehicle_data in gps_df.groupby('vehicle_id'):
        if vehicle_data.empty:
            continue
            
        # Sort by timestamp
        vehicle_data = vehicle_data.sort_values('timestamp')
        
        # Find consecutive low-speed periods
        is_idle = vehicle_data['speed_mph'] <= max_speed_mph
        
        # Group consecutive idle periods
        idle_groups = (is_idle != is_idle.shift()).cumsum()
        
        for group_id, group_data in vehicle_data.groupby(idle_groups):
            if group_data['speed_mph'].iloc[0] <= max_speed_mph:
                # Calculate idle duration
                start_time = group_data['timestamp'].min()
                end_time = group_data['timestamp'].max()
                duration_minutes = (end_time - start_time).total_seconds() / 60
                
                if duration_minutes >= min_idle_minutes:
                    idle_periods.append({
                        'vehicle_id': vehicle_id,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration_minutes': duration_minutes,
                        'location_lat': group_data['lat'].mean(),
                        'location_lon': group_data['lon'].mean(),
                        'violation_type': 'idle_abuse'
                    })
    
    return idle_periods

def filter_business_hours_violations(gps_df: pd.DataFrame, 
                                   start_hour: int = 7, 
                                   end_hour: int = 18) -> List[Dict]:
    """Find GPS activity outside business hours"""
    violations = []
    
    # Filter for non-business hours activity
    after_hours = gps_df[~gps_df['timestamp'].apply(
        lambda t: is_business_hours(t, start_hour, end_hour)
    )]
    
    # Group by vehicle and create violations
    for vehicle_id, vehicle_data in after_hours.groupby('vehicle_id'):
        if vehicle_data.empty:
            continue
        
        # Group by date to avoid duplicate violations for same day
        for date, daily_data in vehicle_data.groupby(vehicle_data['timestamp'].dt.date):
            violations.append({
                'vehicle_id': vehicle_id,
                'date': date,
                'first_violation_time': daily_data['timestamp'].min(),
                'last_violation_time': daily_data['timestamp'].max(),
                'total_records': len(daily_data),
                'violation_type': 'after_hours_driving'
            })
    
    return violations