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
from .mpg_analyzer import MPGAnalyzer
from .violation_deduplicator import ViolationDeduplicator

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
                      enable_enhanced_fuel_detection: bool = True,
                      enable_mpg_analysis: bool = True,
                      vehicle_types: Dict[str, str] = None) -> Dict:
        """
        Run comprehensive fleet audit with all detection methods
        
        Returns consolidated results with financial impact analysis
        """
        if not any([self.gps_data is not None, self.fuel_data is not None, self.job_data is not None]):
            raise ValueError("At least one data source (GPS, fuel, or jobs) must be loaded before running audit")
        
        all_violations = []
        audit_results = {}
        
        # Traditional violation detection
        audit_results['ghost_jobs'] = self.detect_ghost_jobs()
        audit_results['idle_abuse'] = self.detect_idle_abuse()
        audit_results['after_hours_driving'] = self.detect_after_hours_driving()
        
        # Enhanced fuel theft detection
        if self.fuel_data is not None and enable_enhanced_fuel_detection:
            enhanced_detector = EnhancedFuelDetector()
            enhanced_fuel_violations = enhanced_detector.detect_enhanced_fuel_theft(
                self.fuel_data, self.gps_data
            )
            audit_results['enhanced_fuel_theft'] = enhanced_fuel_violations
            all_violations.extend(enhanced_fuel_violations)
        else:
            # Fallback to basic GPS-only detection
            fuel_violations = self.detect_fuel_theft()
            audit_results['fuel_theft'] = fuel_violations
            all_violations.extend(fuel_violations)
        
        # MPG-based fraud detection
        if (enable_mpg_analysis and self.fuel_data is not None and 
            self.gps_data is not None and not self.fuel_data.empty and not self.gps_data.empty):
            
            mpg_analyzer = MPGAnalyzer()
            mpg_violations = []
            
            # Analyze each vehicle
            for vehicle_id in self.fuel_data['vehicle_id'].unique():
                if pd.notna(vehicle_id):
                    # Determine vehicle type
                    vehicle_type = self._get_vehicle_type(vehicle_id, vehicle_types)
                    
                    vehicle_mpg_violations = mpg_analyzer.analyze_vehicle_mpg(
                        self.fuel_data, self.gps_data, vehicle_id, vehicle_type
                    )
                    mpg_violations.extend(vehicle_mpg_violations)
            
            audit_results['mpg_analysis'] = mpg_violations
            all_violations.extend(mpg_violations)
        
        # Add fuel-only analysis if enabled
        if enable_fuel_only_analysis and self.fuel_data is not None:
            fuel_analyzer = FuelOnlyAnalyzer()
            fuel_only_results = fuel_analyzer.analyze_fuel_patterns(self.fuel_data)
            for key, violations in fuel_only_results.items():
                audit_results[f"fuel_only_{key}"] = violations
                all_violations.extend(violations)
        
        # Deduplicate and consolidate violations
        deduplicator = ViolationDeduplicator()
        consolidated_violations = deduplicator.deduplicate_violations(all_violations)
        
        # Calculate financial impact
        financial_summary = deduplicator.generate_financial_summary(
            consolidated_violations, 
            time_period_days=self._calculate_audit_period_days()
        )
        
        # Store results
        self.violations = consolidated_violations
        
        # Return comprehensive results
        return {
            'raw_violations': audit_results,
            'consolidated_violations': consolidated_violations,
            'financial_summary': financial_summary,
            'overlap_warnings': self.get_overlap_warnings(),
            'data_quality': self._get_data_quality_summary(),
            'audit_period_days': self._calculate_audit_period_days(),
            'vehicles_analyzed': self._get_vehicles_analyzed()
        }
    
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
    
    def _get_vehicle_type(self, vehicle_id: str, vehicle_types: Dict[str, str] = None) -> str:
        """Determine vehicle type for MPG analysis"""
        if vehicle_types and vehicle_id in vehicle_types:
            return vehicle_types[vehicle_id]
        
        # Auto-detect based on vehicle ID naming patterns
        vehicle_id_lower = str(vehicle_id).lower()
        
        if any(keyword in vehicle_id_lower for keyword in ['truck', 'semi', 'tractor', 'freight']):
            return 'truck'
        elif any(keyword in vehicle_id_lower for keyword in ['van', 'delivery', 'cargo']):
            return 'van'
        elif any(keyword in vehicle_id_lower for keyword in ['pickup', 'f150', 'f250', 'silverado', 'ram']):
            return 'pickup'
        elif any(keyword in vehicle_id_lower for keyword in ['car', 'sedan', 'civic', 'corolla', 'accord']):
            return 'car'
        else:
            return 'default'  # Conservative commercial vehicle estimate
    
    def _calculate_audit_period_days(self) -> int:
        """Calculate the time span of the audit data"""
        all_dates = []
        
        if self.gps_data is not None and not self.gps_data.empty:
            all_dates.extend(self.gps_data['timestamp'].tolist())
        
        if self.fuel_data is not None and not self.fuel_data.empty:
            all_dates.extend(self.fuel_data['timestamp'].tolist())
        
        if self.job_data is not None and not self.job_data.empty:
            all_dates.extend(self.job_data['scheduled_time'].tolist())
        
        if not all_dates:
            return 7  # Default to 1 week
        
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        return max(1, (max_date - min_date).days + 1)
    
    def _get_data_quality_summary(self) -> Dict:
        """Get overall data quality assessment"""
        summary = {
            'has_gps': self.gps_data is not None and not self.gps_data.empty,
            'has_fuel': self.fuel_data is not None and not self.fuel_data.empty,
            'has_jobs': self.job_data is not None and not self.job_data.empty,
            'gps_records': len(self.gps_data) if self.gps_data is not None else 0,
            'fuel_records': len(self.fuel_data) if self.fuel_data is not None else 0,
            'job_records': len(self.job_data) if self.job_data is not None else 0
        }
        
        # Assess fuel data quality if available
        if summary['has_fuel']:
            from .enhanced_fuel_detector import EnhancedFuelDetector
            detector = EnhancedFuelDetector()
            fuel_quality = detector.get_data_quality_summary(self.fuel_data)
            summary['fuel_quality'] = fuel_quality
        
        # Assess cross-referencing capability
        summary['can_cross_reference'] = {
            'fuel_gps': summary['has_fuel'] and summary['has_gps'],
            'job_gps': summary['has_jobs'] and summary['has_gps'],
            'mpg_analysis': summary['has_fuel'] and summary['has_gps']
        }
        
        return summary
    
    def _get_vehicles_analyzed(self) -> Dict:
        """Get summary of vehicles in the analysis"""
        vehicles = set()
        
        if self.gps_data is not None:
            vehicles.update(self.gps_data['vehicle_id'].dropna().unique())
        
        if self.fuel_data is not None:
            vehicles.update(self.fuel_data['vehicle_id'].dropna().unique())
        
        if self.job_data is not None and 'driver_id' in self.job_data.columns:
            vehicles.update(self.job_data['driver_id'].dropna().unique())
        
        return {
            'total_vehicles': len(vehicles),
            'vehicle_ids': sorted(list(vehicles)),
            'vehicles_with_gps': len(self.gps_data['vehicle_id'].unique()) if self.gps_data is not None else 0,
            'vehicles_with_fuel': len(self.fuel_data['vehicle_id'].unique()) if self.fuel_data is not None else 0
        }