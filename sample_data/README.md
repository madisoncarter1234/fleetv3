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

## 🎯 **Data Quality Tiers - Test Different Scenarios:**

### **Tier 1: Premium Data (`enhanced_fuel_theft_sample.csv`)**
- **Contains:** Amount + Gallons + Location + Timestamp
- **Detection:** Full enhanced detection (95% confidence)
- **Catches:** Volume violations, price anomalies, pattern deviations

### **Tier 2: Good Data (`fuel_amount_only_sample.csv`)**  
- **Contains:** Amount + Location + Timestamp (no gallons)
- **Detection:** Financial pattern analysis (80% confidence)
- **Catches:** Estimated volume violations, amount pattern deviations

### **Tier 3: Moderate Data (`fuel_gallons_only_sample.csv`)**
- **Contains:** Gallons + Location + Timestamp (no amount)
- **Detection:** Volume analysis only (70% confidence)  
- **Catches:** Tank capacity violations, volume patterns

### **Tier 4: Basic Data (`fuel_basic_sample.csv`)**
- **Contains:** Location + Timestamp only
- **Detection:** Timing/frequency analysis (50% confidence)
- **Catches:** After-hours purchases, multiple daily transactions

## Demo Script:

"FleetAudit.io automatically adapts to whatever data quality you have. Whether you have a premium fuel card system with full transaction details, or just basic purchase records, we provide the best possible theft detection for your data. The system clearly shows confidence levels and suggests how to improve detection by upgrading your data sources."