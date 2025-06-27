# Enterprise Fraud Detection AI Prompts

## Overview
These prompts convert our sophisticated enterprise fraud detection logic into structured AI prompts that can be integrated into Claude system prompts. Each prompt represents a specific detection module from our original system.

---

## 1. Enhanced Fuel Volume Analysis

### Prompt:
```
FUEL VOLUME FRAUD DETECTION:

Analyze fuel purchase data for volume-based fraud indicators. For each fuel transaction, check:

TANK CAPACITY VIOLATIONS:
- Compare purchase gallons against estimated vehicle tank capacity
- Commercial trucks: 40-60 gallons, Vans: 20-35 gallons, Pickups: 25-35 gallons
- Flag purchases exceeding tank capacity by >20%
- Calculate excess gallons and financial impact (excess_gallons * $3.75)

RAPID REFILL DETECTION:
- Identify purchases within 12 hours where:
  * Previous purchase was >90% of tank capacity AND current purchase >120% of capacity
  * Two purchases exceeding tank capacity within same day
  * Total gallons in 24-hour period >2x tank capacity
- Exclude emergency scenarios (previous purchase <5 gallons, different locations)

DAILY EXCESS ANALYSIS:
- Group purchases by vehicle and date
- Flag if daily total >2x estimated tank capacity
- Account for legitimate multi-vehicle or equipment scenarios

OUTPUT FORMAT:
{
  "violation_type": "volume_excess",
  "confidence": 0.95,
  "severity": "high",
  "estimated_loss": 150.25,
  "detection_details": {
    "tank_capacity": 40,
    "purchase_gallons": 65,
    "excess_gallons": 25
  }
}
```

---

## 2. Statistical Pattern Deviation Analysis

### Prompt:
```
BEHAVIORAL PATTERN FRAUD DETECTION:

Analyze driver/vehicle fuel purchasing patterns to identify statistical anomalies:

BASELINE ESTABLISHMENT:
- Calculate mean and standard deviation for each vehicle's:
  * Purchase amounts (dollars)
  * Purchase volumes (gallons)
  * Purchase frequency (days between)
- Require minimum 5 historical purchases for pattern analysis

OUTLIER DETECTION:
- Flag purchases >3 standard deviations above vehicle's mean
- Calculate z-score: (current_purchase - mean) / std_deviation
- Only flag positive outliers (excessive purchases)

FREQUENCY ANOMALIES:
- Identify vehicles with >2 purchases per day
- Compare against vehicle's historical frequency pattern
- Flag clusters of purchases within short time windows

CONFIDENCE SCORING:
- High confidence (0.85+): >3 std deviations with strong historical pattern
- Medium confidence (0.65-0.84): 2-3 std deviations
- Low confidence (<0.65): Limited historical data or edge cases

OUTPUT FORMAT:
{
  "violation_type": "pattern_deviation",
  "confidence": 0.80,
  "severity": "medium",
  "z_score": 3.2,
  "vehicle_baseline": {
    "avg_purchase": 125.50,
    "std_deviation": 45.20,
    "current_purchase": 270.00
  }
}
```

---

## 3. Price Analysis Fraud Detection

### Prompt:
```
FUEL PRICE FRAUD DETECTION:

Analyze transaction costs to identify non-fuel purchases and price anomalies:

PRICE PER GALLON ANALYSIS:
- Calculate: price_per_gallon = total_amount / gallons
- Expected range: $3.35 - $4.15 per gallon (adjust for regional pricing)
- Flag transactions >$2.00 above expected range

EXCESSIVE COST DETECTION:
- Compare total cost against expected: gallons * avg_fuel_price
- Flag transactions >50% above expected cost
- Calculate excess amount potentially spent on non-fuel items

NON-FUEL PURCHASE INDICATORS:
- Round amounts ($50.00, $100.00) suggest cash withdrawal
- Very high $/gallon ratios indicate convenience store purchases
- Small gallons with high costs suggest DEF fluid, oil, etc.

CONFIDENCE ADJUSTMENTS:
- Reduce confidence for potential legitimate scenarios:
  * DEF fluid purchases (15-60 gallon range, specific price patterns)
  * Premium fuel locations (airports, remote areas)
  * Equipment fuel vs vehicle fuel

OUTPUT FORMAT:
{
  "violation_type": "price_excess",
  "confidence": 0.75,
  "severity": "medium",
  "price_analysis": {
    "price_per_gallon": 6.50,
    "expected_price": 3.75,
    "excess_amount": 45.80,
    "likely_non_fuel": true
  }
}
```

---

## 4. MPG-Based Fraud Detection

### Prompt:
```
MPG FRAUD DETECTION:

Cross-reference fuel consumption with GPS mileage data to detect fuel theft:

MPG CALCULATION:
- Calculate: actual_mpg = miles_driven / gallons_consumed
- Expected MPG ranges by vehicle type:
  * Heavy trucks: 7-12 MPG
  * Delivery vans: 12-18 MPG  
  * Pickup trucks: 15-25 MPG
  * Cars: 20-35 MPG

FRAUD TYPE DETECTION:

FUEL DUMPING (Extremely Low MPG):
- Actual MPG <30% of minimum expected
- Indicates fuel being dumped/sold rather than used
- High confidence violation (0.95)

ODOMETER FRAUD (Very Low MPG):
- Actual MPG <50% of minimum expected
- Suggests miles under-reported to hide excessive consumption
- High confidence violation (0.90)

IDLE REFILLS (Minimal Mileage):
- <5 miles driven but >3 gallons consumed
- Indicates vehicle used for personal purposes or fuel transfer
- Calculate 80% of fuel as likely theft

EXCESSIVE CONSUMPTION:
- Actual MPG <70% of minimum expected  
- May indicate excessive idling or personal vehicle use
- Medium confidence (0.75)

OUTPUT FORMAT:
{
  "violation_type": "fuel_dumping_mpg",
  "confidence": 0.95,
  "severity": "high",
  "mpg_analysis": {
    "actual_mpg": 2.1,
    "expected_range": "7-12",
    "miles_driven": 15.2,
    "gallons_consumed": 7.3,
    "excess_fuel_gallons": 5.8
  }
}
```

---

## 5. Temporal Fraud Detection

### Prompt:
```
TIME-BASED FRAUD DETECTION:

Analyze purchase timing to identify policy violations and fraud indicators:

AFTER-HOURS VIOLATIONS:
- Flag purchases outside business hours (7AM-6PM)
- Include weekend purchases for business fleets
- Weight severity based on hour (2AM = higher than 7PM)

IMPOSSIBLE SCENARIOS:
- Multiple purchases <2 hours apart at different locations
- Purchases during scheduled maintenance/downtime
- Fuel purchases during known GPS blackout periods

HOLIDAY/WEEKEND PATTERNS:
- Business vehicles fueling on holidays
- Personal use indicators (residential area purchases)
- Off-duty hour clustering

FREQUENCY ANALYSIS:
- Multiple daily purchases (>2 per day)
- Unusual clustering patterns
- Deviations from historical timing patterns

OUTPUT FORMAT:
{
  "violation_type": "after_hours",
  "confidence": 0.70,
  "severity": "medium",
  "timing_details": {
    "purchase_time": "02:30 AM",
    "day_of_week": "Sunday",
    "business_hours": false,
    "estimated_personal_use_percentage": 30
  }
}
```

---

## 6. Cross-Data Validation

### Prompt:
```
GPS-FUEL CROSS-VALIDATION:

When both GPS and fuel data are available, cross-reference for validation:

LOCATION VALIDATION:
- Verify fuel purchases occur near GPS locations
- Flag fuel purchases with no GPS activity within:
  * 1 mile radius and 15-minute window
- Account for GPS signal gaps in remote areas

ROUTE CORRELATION:
- Fuel purchases should align with travel routes
- Flag purchases far from typical operating areas
- Identify potential personal detours

GHOST JOB DETECTION:
- Compare scheduled jobs with actual GPS presence
- Flag jobs with no GPS activity at location
- Cross-check fuel purchases near job sites

GPS-BASED MPG VALIDATION:
- Use GPS data to calculate actual miles driven
- Compare with fuel consumption for MPG analysis
- Identify patterns suggesting GPS tampering

OUTPUT FORMAT:
{
  "violation_type": "location_mismatch",
  "confidence": 0.85,
  "severity": "high",
  "cross_validation": {
    "fuel_location": "Shell Station - Highway 85",
    "nearest_gps": "2.3 miles away",
    "time_gap": "45 minutes",
    "gps_activity_present": false
  }
}
```

---

## 7. Financial Impact Calculation

### Prompt:
```
FINANCIAL IMPACT ASSESSMENT:

Calculate estimated financial losses for each violation type:

LOSS CALCULATION METHODS:

Volume Excess:
- Direct loss: excess_gallons * avg_fuel_price
- Confidence factor: volume_confidence * loss_amount

Pattern Deviations: 
- Estimated loss: (actual_amount - expected_amount) * fraud_probability
- Fraud probability based on z-score and violation type

MPG-Based Fraud:
- Expected fuel: miles_driven / expected_mpg
- Excess fuel: actual_fuel - expected_fuel  
- Loss: excess_fuel * fuel_price * confidence

Time-Based Violations:
- Estimated personal use percentage * transaction_amount
- After-hours: 30% personal use assumption
- Weekend: 20% personal use assumption

CONFIDENCE WEIGHTING:
- Multiply base loss by confidence score
- High confidence (>0.8): Full loss amount
- Medium confidence (0.6-0.8): 70% of loss amount  
- Low confidence (<0.6): 40% of loss amount

WEEKLY/MONTHLY PROJECTIONS:
- Scale violations to weekly estimates
- Account for seasonal variations
- Provide conservative and aggressive estimates

OUTPUT FORMAT:
{
  "financial_impact": {
    "immediate_loss": 125.50,
    "confidence_weighted_loss": 100.40,
    "weekly_projection": 502.00,
    "monthly_projection": 2008.00,
    "annual_impact": 24096.00
  }
}
```

---

## 8. Violation Consolidation Logic

### Prompt:
```
VIOLATION CONSOLIDATION:

Group related violations to avoid duplicate reporting and provide clear incident summaries:

GROUPING CRITERIA:
- Same vehicle within 2-hour window
- Related violation types (volume + price + pattern)
- Same location or route

CONSOLIDATION RULES:

Multi-Factor Incidents:
- Combine volume excess + price anomaly + pattern deviation
- Boost confidence score by 10% for multiple evidence types
- Create comprehensive incident description

Severity Escalation:
- Take highest severity among grouped violations
- Escalate to "critical" if 3+ high-severity violations grouped
- Maintain individual evidence details

Financial Aggregation:
- Sum all estimated losses in group
- Apply confidence weighting to total
- Avoid double-counting overlapping losses

INCIDENT DESCRIPTION:
- Lead with highest-confidence violation
- List supporting evidence
- Provide actionable summary for management

OUTPUT FORMAT:
{
  "incident_type": "multi_factor_fraud",
  "consolidated_violations": 3,
  "total_estimated_loss": 287.50,
  "confidence": 0.92,
  "severity": "critical",
  "evidence_summary": [
    "Tank capacity exceeded by 15 gallons",
    "Transaction cost 40% above expected",
    "Purchase pattern 3.2x above driver norm"
  ]
}
```

---

## Implementation Notes

### Integration Strategy:
1. **System Prompt Enhancement**: Add these as specialized detection modules in Claude's system prompt
2. **Sequential Analysis**: Run each prompt type in sequence for comprehensive coverage
3. **Confidence Weighting**: Use confidence scores to prioritize violations
4. **Context Awareness**: Maintain context between prompts for cross-validation

### Prompt Chaining:
1. Data Quality Assessment → Determine available analysis types
2. Volume Analysis → Detect obvious theft patterns  
3. Statistical Analysis → Find behavioral anomalies
4. Cross-Validation → Strengthen findings with GPS/job data
5. Consolidation → Group related violations
6. Financial Impact → Calculate business impact

### Output Standardization:
- Consistent JSON format across all detection types
- Standardized confidence scoring (0.0-1.0)
- Severity levels: low, medium, high, critical
- Financial impact in USD with projections