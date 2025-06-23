import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from .utils import (
    calculate_distance, is_within_time_window, is_within_distance,
    find_gps_near_location, detect_idle_periods, filter_business_hours_violations,
    geocode_address
)
from .fuel_only_analyzer import FuelOnlyAnalyzer
from .enhanced_fuel_detector import EnhancedFuelDetector

class FleetAuditor:
    """Main class for detecting fleet violations"""
    
    def __init__(self):
        self.violations = []
        self.gps_data = None
        self.fuel_data = None
        self.job_data = None
        self.date_ranges = {}
        self.overlap_analysis = {}
    
    def load_data(self, gps_df: pd.DataFrame = None, fuel_df: pd.DataFrame = None, job_df: pd.DataFrame = None):
        """Load normalized data from parsers"""
        self.gps_data = gps_df.copy() if gps_df is not None else None
        self.fuel_data = fuel_df.copy() if fuel_df is not None else None
        self.job_data = job_df.copy() if job_df is not None else None
        self.violations = []
        
        # Analyze date ranges and overlaps
        self._analyze_date_ranges()
        self._analyze_overlaps()
    
    def detect_fuel_theft(self, distance_threshold_miles: float = 1.0, 
                         time_threshold_minutes: int = 15) -> List[Dict]:
        """Detect potential fuel theft by finding fuel purchases without nearby GPS activity"""
        fuel_theft_violations = []
        
        if self.fuel_data is None or self.gps_data is None:
            return fuel_theft_violations
        
        # Get filtered data that only includes overlapping time periods
        filtered_fuel, filtered_gps = self.get_filtered_data_for_comparison('fuel', 'gps')
        
        if filtered_fuel.empty or filtered_gps.empty:
            # No overlap - add warning but don't flag as theft
            return fuel_theft_violations
        
        for _, fuel_record in filtered_fuel.iterrows():
            if pd.isna(fuel_record['timestamp']) or pd.isna(fuel_record['vehicle_id']):
                continue
            
            # Get GPS data for this vehicle around the fuel purchase time
            vehicle_gps = filtered_gps[
                filtered_gps['vehicle_id'] == fuel_record['vehicle_id']
            ]
            
            if vehicle_gps.empty:
                continue
            
            # For now, we'll use a simple location match based on fuel station location
            # In production, you'd geocode the fuel station address
            fuel_lat, fuel_lon = geocode_address(str(fuel_record['location']))
            
            if fuel_lat is None or fuel_lon is None:
                # Skip if we can't geocode the location
                continue
            
            # Find GPS records near the fuel purchase location and time
            nearby_gps = find_gps_near_location(
                vehicle_gps, fuel_lat, fuel_lon, 
                fuel_record['timestamp'], 
                distance_threshold_miles, 
                time_threshold_minutes
            )
            
            # If no GPS activity found near fuel purchase, flag as potential theft
            if nearby_gps.empty:
                fuel_theft_violations.append({
                    'vehicle_id': fuel_record['vehicle_id'],
                    'timestamp': fuel_record['timestamp'],
                    'location': fuel_record['location'],
                    'gallons': fuel_record['gallons'],
                    'violation_type': 'fuel_theft',
                    'description': f"Fuel purchase of {fuel_record['gallons']} gallons with no GPS activity within {distance_threshold_miles} miles and {time_threshold_minutes} minutes"
                })
        
        return fuel_theft_violations
    
    def detect_ghost_jobs(self, distance_threshold_miles: float = 0.5, 
                         time_buffer_minutes: int = 30) -> List[Dict]:
        """Detect ghost jobs - jobs scheduled but no GPS activity at job site"""
        ghost_job_violations = []
        
        if self.job_data is None or self.gps_data is None:
            return ghost_job_violations
        
        # Get filtered data that only includes overlapping time periods
        filtered_jobs, filtered_gps = self.get_filtered_data_for_comparison('jobs', 'gps')
        
        if filtered_jobs.empty or filtered_gps.empty:
            # No overlap - can't detect ghost jobs
            return ghost_job_violations
        
        for _, job_record in filtered_jobs.iterrows():
            if pd.isna(job_record['scheduled_time']) or pd.isna(job_record['address']):
                continue
            
            # Geocode job address
            job_lat, job_lon = geocode_address(str(job_record['address']))
            
            if job_lat is None or job_lon is None:
                # Skip if we can't geocode the job address
                continue
            
            # Get GPS data for the assigned driver/vehicle
            if pd.notna(job_record['driver_id']):
                # Filter by driver if available (assuming driver_id maps to vehicle_id)
                relevant_gps = filtered_gps[
                    filtered_gps['vehicle_id'] == job_record['driver_id']
                ]
            else:
                # If no specific driver, check all vehicles
                relevant_gps = filtered_gps
            
            if relevant_gps.empty:
                continue
            
            # Look for GPS activity within time window of scheduled job
            job_window_start = job_record['scheduled_time'] - timedelta(minutes=time_buffer_minutes)
            job_window_end = job_record['scheduled_time'] + timedelta(minutes=time_buffer_minutes * 2)  # Longer window after
            
            time_filtered_gps = relevant_gps[
                (relevant_gps['timestamp'] >= job_window_start) &
                (relevant_gps['timestamp'] <= job_window_end)
            ]
            
            if time_filtered_gps.empty:
                ghost_job_violations.append({
                    'job_id': job_record['job_id'],
                    'driver_id': job_record['driver_id'],
                    'scheduled_time': job_record['scheduled_time'],
                    'address': job_record['address'],
                    'violation_type': 'ghost_job',
                    'description': f"No GPS activity found near job site during scheduled time window"
                })
                continue
            
            # Check if any GPS records are near the job location
            nearby_gps = time_filtered_gps[
                time_filtered_gps.apply(
                    lambda row: is_within_distance(
                        row['lat'], row['lon'], job_lat, job_lon, distance_threshold_miles
                    ), axis=1
                )
            ]
            
            if nearby_gps.empty:
                ghost_job_violations.append({
                    'job_id': job_record['job_id'],
                    'driver_id': job_record['driver_id'],
                    'scheduled_time': job_record['scheduled_time'],
                    'address': job_record['address'],
                    'violation_type': 'ghost_job',
                    'description': f"GPS activity found during job window but not within {distance_threshold_miles} miles of job site"
                })
        
        return ghost_job_violations
    
    def detect_idle_abuse(self, min_idle_minutes: int = 10, max_speed_mph: float = 3) -> List[Dict]:
        """Detect vehicles idling for extended periods"""
        if self.gps_data is None:
            return []
        
        return detect_idle_periods(self.gps_data, min_idle_minutes, max_speed_mph)
    
    def detect_after_hours_driving(self, start_hour: int = 7, end_hour: int = 18) -> List[Dict]:
        """Detect driving activity outside business hours"""
        if self.gps_data is None:
            return []
        
        return filter_business_hours_violations(self.gps_data, start_hour, end_hour)
    
    def run_full_audit(self, enable_fuel_only_analysis: bool = False, 
                      enable_enhanced_fuel_detection: bool = True) -> Dict[str, List[Dict]]:
        """Run all violation detection algorithms and return results"""
        if not any([self.gps_data is not None, self.fuel_data is not None, self.job_data is not None]):
            raise ValueError("At least one data source (GPS, fuel, or jobs) must be loaded before running audit")
        
        audit_results = {
            'ghost_jobs': self.detect_ghost_jobs(),
            'idle_abuse': self.detect_idle_abuse(),
            'after_hours_driving': self.detect_after_hours_driving()
        }
        
        # Enhanced fuel theft detection (replaces basic GPS-only detection)
        if self.fuel_data is not None and enable_enhanced_fuel_detection:
            enhanced_detector = EnhancedFuelDetector()
            enhanced_fuel_violations = enhanced_detector.detect_enhanced_fuel_theft(
                self.fuel_data, self.gps_data
            )
            audit_results['fuel_theft'] = enhanced_fuel_violations
        else:
            # Fallback to basic GPS-only detection
            audit_results['fuel_theft'] = self.detect_fuel_theft()
        
        # Add fuel-only analysis if enabled and we have fuel data but no GPS
        if enable_fuel_only_analysis and self.fuel_data is not None:
            fuel_analyzer = FuelOnlyAnalyzer()
            fuel_only_results = fuel_analyzer.analyze_fuel_patterns(self.fuel_data)
            audit_results.update(fuel_only_results)
        
        # Store all violations for reporting
        self.violations = []
        for violation_type, violations in audit_results.items():
            self.violations.extend(violations)
        
        return audit_results
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of violations"""
        if not self.violations:
            return {}
        
        violations_df = pd.DataFrame(self.violations)
        
        summary = {
            'total_violations': len(self.violations),
            'violations_by_type': violations_df['violation_type'].value_counts().to_dict(),
            'vehicles_with_violations': violations_df['vehicle_id'].nunique() if 'vehicle_id' in violations_df.columns else 0,
            'date_range': {
                'start': violations_df['timestamp'].min() if 'timestamp' in violations_df.columns else None,
                'end': violations_df['timestamp'].max() if 'timestamp' in violations_df.columns else None
            }
        }
        
        return summary
    
    def _analyze_date_ranges(self):
        """Analyze the date ranges of each data source"""
        self.date_ranges = {}
        
        if self.gps_data is not None and not self.gps_data.empty:
            self.date_ranges['gps'] = {
                'start': self.gps_data['timestamp'].min(),
                'end': self.gps_data['timestamp'].max(),
                'count': len(self.gps_data)
            }
        
        if self.fuel_data is not None and not self.fuel_data.empty:
            self.date_ranges['fuel'] = {
                'start': self.fuel_data['timestamp'].min(),
                'end': self.fuel_data['timestamp'].max(),
                'count': len(self.fuel_data)
            }
        
        if self.job_data is not None and not self.job_data.empty:
            self.date_ranges['jobs'] = {
                'start': self.job_data['scheduled_time'].min(),
                'end': self.job_data['scheduled_time'].max(),
                'count': len(self.job_data)
            }
    
    def _analyze_overlaps(self):
        """Analyze overlap between data sources and flag mismatches"""
        self.overlap_analysis = {
            'has_overlaps': {},
            'overlap_periods': {},
            'warnings': []
        }
        
        data_sources = [(k, v) for k, v in self.date_ranges.items()]
        
        # Check pairwise overlaps
        for i, (source1, range1) in enumerate(data_sources):
            for source2, range2 in data_sources[i+1:]:
                overlap_key = f"{source1}_{source2}"
                
                # Calculate overlap
                overlap_start = max(range1['start'], range2['start'])
                overlap_end = min(range1['end'], range2['end'])
                
                if overlap_start <= overlap_end:
                    # There is overlap
                    overlap_days = (overlap_end - overlap_start).days + 1
                    self.overlap_analysis['has_overlaps'][overlap_key] = True
                    self.overlap_analysis['overlap_periods'][overlap_key] = {
                        'start': overlap_start,
                        'end': overlap_end,
                        'days': overlap_days
                    }
                    
                    # Warn if overlap is very small
                    total_days_source1 = (range1['end'] - range1['start']).days + 1
                    total_days_source2 = (range2['end'] - range2['start']).days + 1
                    min_total_days = min(total_days_source1, total_days_source2)
                    
                    if overlap_days < min_total_days * 0.3:  # Less than 30% overlap
                        self.overlap_analysis['warnings'].append({
                            'type': 'limited_overlap',
                            'sources': [source1, source2],
                            'message': f"Limited overlap between {source1} and {source2} data ({overlap_days} days of {min_total_days} days)"
                        })
                else:
                    # No overlap
                    self.overlap_analysis['has_overlaps'][overlap_key] = False
                    gap_days = (overlap_start - overlap_end).days
                    
                    self.overlap_analysis['warnings'].append({
                        'type': 'no_overlap',
                        'sources': [source1, source2],
                        'message': f"No temporal overlap between {source1} and {source2} data (gap of {gap_days} days)"
                    })
    
    def get_overlap_warnings(self) -> List[Dict]:
        """Get warnings about data overlap issues"""
        return self.overlap_analysis.get('warnings', [])
    
    def get_filtered_data_for_comparison(self, source1: str, source2: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get filtered data for two sources that only includes overlapping time periods"""
        overlap_key = f"{source1}_{source2}"
        alt_overlap_key = f"{source2}_{source1}"
        
        # Find the overlap period
        overlap_period = None
        if overlap_key in self.overlap_analysis.get('overlap_periods', {}):
            overlap_period = self.overlap_analysis['overlap_periods'][overlap_key]
        elif alt_overlap_key in self.overlap_analysis.get('overlap_periods', {}):
            overlap_period = self.overlap_analysis['overlap_periods'][alt_overlap_key]
        
        if overlap_period is None:
            # No overlap, return empty DataFrames
            return pd.DataFrame(), pd.DataFrame()
        
        # Filter data to overlap period
        start_date = overlap_period['start']
        end_date = overlap_period['end']
        
        data1 = None
        data2 = None
        
        if source1 == 'gps' and self.gps_data is not None:
            data1 = self.gps_data[
                (self.gps_data['timestamp'] >= start_date) & 
                (self.gps_data['timestamp'] <= end_date)
            ].copy()
        elif source1 == 'fuel' and self.fuel_data is not None:
            data1 = self.fuel_data[
                (self.fuel_data['timestamp'] >= start_date) & 
                (self.fuel_data['timestamp'] <= end_date)
            ].copy()
        elif source1 == 'jobs' and self.job_data is not None:
            data1 = self.job_data[
                (self.job_data['scheduled_time'] >= start_date) & 
                (self.job_data['scheduled_time'] <= end_date)
            ].copy()
        
        if source2 == 'gps' and self.gps_data is not None:
            data2 = self.gps_data[
                (self.gps_data['timestamp'] >= start_date) & 
                (self.gps_data['timestamp'] <= end_date)
            ].copy()
        elif source2 == 'fuel' and self.fuel_data is not None:
            data2 = self.fuel_data[
                (self.fuel_data['timestamp'] >= start_date) & 
                (self.fuel_data['timestamp'] <= end_date)
            ].copy()
        elif source2 == 'jobs' and self.job_data is not None:
            data2 = self.job_data[
                (self.job_data['scheduled_time'] >= start_date) & 
                (self.job_data['scheduled_time'] <= end_date)
            ].copy()
        
        return data1 if data1 is not None else pd.DataFrame(), data2 if data2 is not None else pd.DataFrame()