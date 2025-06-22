# FleetAudit.io Sample Data Files

These sample data files are designed to demonstrate FleetAudit.io's violation detection capabilities.

## Files Included:

### 1. GPS Data (`gps_sample_samsara.csv`)
- **Format**: Samsara GPS export
- **Vehicles**: TRUCK-001, TRUCK-002
- **Time Range**: June 15-16, 2024
- **Violations Built In**:
  - ⏰ **Excessive Idling**: TRUCK-001 at Queens location (30+ minutes)
  - 🌙 **After-Hours Activity**: TRUCK-001 driving at 22:30-23:15

### 2. Fuel Data (`fuel_sample_wex.csv`)
- **Format**: WEX fuel card export
- **Vehicles**: TRUCK-001, TRUCK-002, TRUCK-003, TRUCK-004, TRUCK-005
- **Violations Built In**:
  - 🚨 **Potential Fuel Theft**: TRUCK-003, TRUCK-004, TRUCK-005 fuel purchases with no corresponding GPS data

### 3. Job Data (`jobs_sample_jobber.csv`)
- **Format**: Jobber job management export
- **Violations Built In**:
  - 👻 **Ghost Jobs**: JOB-2024-006 and JOB-2024-007 scheduled for non-existent locations with no GPS activity

## How to Test:

1. **Upload all three files** to your FleetAudit.io app
2. **Set audit parameters**:
   - Business hours: 7:00 AM - 6:00 PM
   - Idle threshold: 10 minutes
   - Distance threshold: 1 mile
3. **Run the audit** - you should see:
   - **4 violations total**
   - **1 idle abuse incident**
   - **1 after-hours driving incident** 
   - **2 ghost jobs**
   - **3 potential fuel theft incidents**

## Expected Results:

- **Total Violations**: ~6-8 depending on detection settings
- **Vehicles Flagged**: 4-5 vehicles
- **Violation Types**: All four categories should be triggered

This demonstrates FleetAudit.io can detect real fleet management issues and generate actionable reports for your customers.

## Demo Script:

"Here's a sample week of data from a small NYC delivery company. As you can see, FleetAudit.io detected several concerning patterns including unauthorized after-hours vehicle use, excessive idling costing fuel, and potential fraud with ghost job entries. The system automatically flagged these for investigation, potentially saving thousands in operational costs."