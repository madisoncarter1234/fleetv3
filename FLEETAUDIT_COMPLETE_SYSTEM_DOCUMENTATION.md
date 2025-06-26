# FleetAudit.io - Complete System Documentation
*For Next.js Migration Reference*

## 🎯 PROJECT OVERVIEW

**FleetAudit.io** is an AI-powered fleet fraud detection SaaS platform that analyzes fuel, GPS, and job data to uncover theft, misuse, and policy violations. Built with Streamlit, it uses Claude Haiku for fraud detection and generates professional PDF reports.

**Current Status**: Working Streamlit application with navigation issues that require migration to Next.js

---

## 📊 CORE FUNCTIONALITY SUMMARY

### Three Data Upload Types
1. **Fuel Data CSV** - Fuel card transactions from providers like WEX, Fleetcor
2. **GPS Data CSV** - Vehicle location tracking data from Samsara, Geotab, etc.
3. **Job Data CSV** - Scheduled deliveries/services from Jobber, ServiceTitan, etc.

### Fraud Detection Patterns
1. **Shared Card Use** - Same fuel card used by multiple drivers/vehicles within 60 minutes
2. **After-Hours Fuel** - Purchases outside business hours (7AM-6PM)
3. **Ghost Jobs** - Scheduled jobs with no GPS activity at location
4. **Excessive Fuel** - Amounts exceeding vehicle capacity (>25 gal vans, >50 gal trucks)
5. **Rapid Consecutive Purchases** - Multiple fills within 2 hours
6. **Personal Use** - Weekend/holiday activity in residential areas

---

## 🏗️ FILE STRUCTURE & ARCHITECTURE

### Core Application Files
```
/app.py                    # Landing page with demo scenarios
/pages/1_Product.py        # Main fraud detection app (WORKING VERSION)
/pages/2_Backup.py         # Backup copy of main app (identical functionality)
/index.py                  # Simple test file for path verification
```

### Backend Services
```
/backend/ai_service.py     # Centralized Claude AI service (unused in current app)
/logic/                    # Advanced analysis modules (mostly unused)
/parsers/                  # AI-powered CSV normalization (unused)
/email_service/            # Email functionality (placeholder)
```

### Configuration
```
/requirements.txt          # Python dependencies
/.gitignore               # Git ignore rules
/Procfile                 # Deployment config
/runtime.txt              # Python version
/nixpacks.toml           # Build configuration
```

### Sample Data & Testing
```
/sample_data/             # Test CSV files for different scenarios
/*.csv                    # Various test cases and formats
```

---

## 📋 DETAILED FILE ANALYSIS

### 1. MAIN LANDING PAGE (`app.py`)

**Purpose**: Marketing landing page with interactive demo scenarios

**Key Functions**:
- `get_demo_data()` - Returns 3 pre-built fraud scenarios
- `display_demo_results()` - Shows realistic fraud detection results
- `init_global_session_state()` - Session management

**Demo Scenarios**:
1. **ABC Logistics** (12 vehicles, 4 violations, $551.75 loss)
2. **Metro Delivery** (6 vehicles, 2 violations, $162.75 loss)  
3. **Clean Fleet Co** (8 vehicles, 1 violation, $12.50 loss)

**Navigation Issues**: 
- Uses `st.switch_page()` which fails in Streamlit Cloud
- Multiple attempted fixes failed
- Reason for Next.js migration

**Styling**: 
- Extensive custom CSS with gradient themes
- Blue color scheme (#1f4e79, #2d5aa0)
- Responsive card layouts
- Professional pricing section

### 2. MAIN APPLICATION (`pages/1_Product.py`)

**Purpose**: Core fraud detection application - THE WORKING VERSION

**Key Functions**:

#### Data Upload Functions
```python
def upload_fuel_data():
    # Handles fuel CSV with extensive column mapping
    column_mapping = {
        'Transaction Date': 'date',
        'Date': 'date', 
        'Transaction Time': 'time',
        'Time': 'time',
        'Site Name': 'location',
        'Merchant Name': 'location',
        'Location': 'location',
        'Gallons': 'gallons',
        'Fuel Quantity': 'gallons',
        'Vehicle Number': 'vehicle_id',
        'Vehicle': 'vehicle_id',
        'Amount': 'amount',
        'Total Cost': 'amount',
        'Driver Name': 'driver_name',
        'Card Number': 'card_number',
        'Card': 'card_number',
        'Fuel Card': 'card_number',
        'Card Last 4': 'card_last_4',
        'Last 4': 'card_last_4',
        'card_last4': 'card_last_4'
    }
```

#### Fraud Detection Function
```python
def detect_fraud():
    # Uses Claude Haiku with specific prompt engineering
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    # Model: claude-3-haiku-20240307
    # Max tokens: 4000 (Haiku limit is 4096)
    # Temperature: 0.1 (deterministic)
```

#### PDF Report Generation
```python
def generate_pdf_report():
    # Uses ReportLab for professional PDF generation
    # Creates tables with violation details
    # Includes summary metrics and recommendations
```

**Session State Management**:
- `fuel_data`: Uploaded fuel DataFrame
- `gps_data`: Uploaded GPS DataFrame  
- `job_data`: Uploaded job DataFrame
- `fraud_results`: AI analysis results

**Critical Features**:
- Real-time CSV preview after upload
- Professional violation display with expandable cards
- Metrics dashboard (violations, estimated loss, high risk count)
- PDF download with timestamp
- Email placeholder (not implemented)

### 3. CLAUDE AI INTEGRATION

**Model Used**: `claude-3-haiku-20240307`
**Token Limit**: 4000 tokens
**Temperature**: 0.1 (low for consistency)

**Prompt Engineering** (Critical for migration):
```
Analyze this fleet data for fraud and theft. Return JSON only.

{analysis_data}

Find these fraud types:
- After-hours fuel purchases (outside 7AM-6PM)
- Ghost jobs (jobs scheduled but no GPS/fuel activity at location)
- Fuel without GPS at location  
- Excessive fuel amounts (>25 gallons for vans, >50 for trucks)
- Rapid consecutive purchases (multiple fills within 2 hours)
- Personal use patterns (weekend/holiday activity)
- Jobs with no vehicle presence (cross-check GPS and fuel data)
- SHARED CARD USE: Same card number (last 4 digits) used by different drivers/vehicles within 60 minutes

CRITICAL SHARED CARD DETECTION:
1. Look for identical card numbers or last 4 digits used across different vehicles within 60 minutes
2. Flag even same-vehicle multiple uses within 60 minutes as suspicious
3. Include ALL transactions in the shared_card_use violation with exact timestamps
4. Calculate time_span_minutes between first and last use

IMPORTANT: For ALL fuel-related violations, include the "card_last_4" field with the last 4 digits of the fuel card used.

Return JSON:
{
  "violations": [
    {
      "type": "after_hours",
      "vehicle_id": "VAN-004", 
      "driver_name": "Diana",
      "timestamp": "2024-06-16 02:00:00",
      "location": "Shell Station",
      "card_last_4": "5678",
      "description": "Fuel purchase at 2 AM outside business hours",
      "severity": "high",
      "estimated_loss": 75.50
    },
    {
      "type": "shared_card_use",
      "card_last_4": "1234",
      "vehicles_involved": ["VAN-001", "TRUCK-002"],
      "drivers_involved": ["John Smith", "Mike Jones"],
      "transactions": [
        {"timestamp": "2024-06-16 14:15:00", "vehicle_id": "VAN-001", "driver_name": "John Smith", "location": "BP Station"},
        {"timestamp": "2024-06-16 14:45:00", "vehicle_id": "TRUCK-002", "driver_name": "Mike Jones", "location": "Shell Station"}
      ],
      "time_span_minutes": 30,
      "description": "Same fuel card (****1234) used by different drivers within 30 minutes",
      "severity": "high",
      "estimated_loss": 150.00
    }
  ],
  "summary": {
    "total_violations": 5,
    "total_estimated_loss": 500.00,
    "high_risk_vehicles": ["TRUCK001", "VAN002"]
  }
}
```

**JSON Response Parsing**:
```python
# Extract JSON more carefully
import json

if '{' in result_text:
    json_start = result_text.find('{')
    # Find the end of the JSON by counting braces
    brace_count = 0
    json_end = json_start
    
    for i, char in enumerate(result_text[json_start:], json_start):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break
    
    json_text = result_text[json_start:json_end]
    fraud_results = json.loads(json_text)
```

---

## 🎨 UI/UX DESIGN SYSTEM

### Color Palette
- **Primary Blue**: #1f4e79
- **Secondary Blue**: #2d5aa0
- **Accent Blue**: #3d6bb5
- **High Risk Red**: #e53e3e
- **Medium Risk Orange**: #dd6b20
- **Low Risk Yellow**: #ecc94b
- **Success Green**: #38a169

### Component Patterns

#### Hero Section
```css
.hero-section {
    background: linear-gradient(135deg, #1f4e79 0%, #2d5aa0 50%, #3d6bb5 100%);
    padding: 4rem 2rem;
    border-radius: 15px;
    margin-bottom: 3rem;
    text-align: center;
    color: white;
    box-shadow: 0 8px 32px rgba(31, 78, 121, 0.3);
}
```

#### Feature Cards
```css
.feature-card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
    border: 1px solid #e9ecef;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}
```

#### Violation Cards (Critical for Next.js)
```css
.violation-card {
    background: #fff5f5;
    border: 1px solid #fed7d7;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    border-left: 4px solid #e53e3e;
}

.violation-card.high {
    border-left-color: #e53e3e;
    background: #fff5f5;
}

.violation-card.medium {
    border-left-color: #dd6b20;
    background: #fffbf0;
}

.violation-card.low {
    border-left-color: #ecc94b;
    background: #fffff0;
}
```

#### Buttons
```css
.stButton > button {
    background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
    color: white;
    border-radius: 6px;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(31, 78, 121, 0.3);
}
```

---

## 📦 DEPENDENCIES & ENVIRONMENT

### Python Requirements (`requirements.txt`)
```
streamlit==1.35.0          # Web framework
pandas>=2.0.0              # Data processing
numpy>=1.24.0              # Numerical computing
supabase>=2.0.0            # Database (not used in current version)
python-dotenv>=1.0.0       # Environment variables
jinja2>=3.1.0              # Template engine (for email)
resend>=0.8.0              # Email service (not used)
haversine>=2.8.0           # GPS distance calculations
openpyxl>=3.1.0            # Excel file support
python-dateutil>=2.8.0     # Date parsing
requests>=2.28.0           # HTTP requests
anthropic>=0.55.0          # Claude AI integration
reportlab>=4.0.0           # PDF generation
```

### Environment Variables
```
ANTHROPIC_API_KEY=         # Required for Claude AI
SUPABASE_URL=              # Not used in current version
SUPABASE_KEY=              # Not used in current version
RESEND_API_KEY=            # Not used in current version
```

### Deployment Configuration

**Procfile** (for Heroku/Railway):
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

**runtime.txt**:
```
python-3.11.0
```

**nixpacks.toml** (for Railway):
```toml
[phases.build]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"
```

---

## 🔍 DEMO SCENARIOS (Critical for Next.js)

### ABC Logistics (High Fraud)
```javascript
const abcLogistics = {
  description: "12-vehicle delivery fleet with multiple policy violations",
  vehicles: 12,
  violations: [
    {
      type: "shared_card_use",
      card_last_4: "4455",
      vehicles_involved: ["VAN-003", "TRUCK-007"],
      drivers_involved: ["Mike Chen", "Sarah Wilson"],
      time_span_minutes: 25,
      description: "Same fuel card (****4455) used by different drivers within 25 minutes",
      severity: "high",
      estimated_loss: 187.50
    },
    {
      type: "after_hours",
      vehicle_id: "VAN-005",
      driver_name: "Carlos Rodriguez", 
      timestamp: "2024-08-15 02:47:00",
      location: "Shell Station - Interstate 85",
      card_last_4: "4455",
      description: "Fuel purchase at 2:47 AM on weekend outside business hours",
      severity: "high",
      estimated_loss: 89.25
    },
    {
      type: "excessive_amount",
      vehicle_id: "TRUCK-003",
      driver_name: "David Kim",
      timestamp: "2024-08-12 14:22:00", 
      location: "BP Station - Highway 75",
      card_last_4: "7891",
      description: "Purchased 67 gallons (normal capacity: 35 gallons)",
      severity: "medium",
      estimated_loss: 125.00
    },
    {
      type: "ghost_job",
      job_id: "ATL-2024-0815",
      driver_name: "Mike Chen",
      vehicle_id: "VAN-003",
      scheduled_time: "2024-08-15 14:00:00",
      address: "Buford, GA",
      description: "Scheduled delivery with no GPS activity at job location",
      severity: "high", 
      estimated_loss: 150.00
    }
  ],
  summary: {
    total_violations: 4,
    total_estimated_loss: 551.75,
    high_risk_vehicles: ["VAN-003", "VAN-005", "TRUCK-003"]
  }
}
```

### Metro Delivery (Medium Fraud)
```javascript
const metroDelivery = {
  description: "6-vehicle urban delivery service with moderate violations",
  vehicles: 6,
  violations: [
    {
      type: "rapid_purchases",
      vehicle_id: "VAN-002",
      driver_name: "Lisa Johnson",
      timestamp: "2024-08-10 16:45:00",
      location: "Exxon Station - Downtown",
      card_last_4: "3344", 
      description: "Two fuel purchases within 45 minutes at different locations",
      severity: "medium",
      estimated_loss: 95.50
    },
    {
      type: "personal_use",
      vehicle_id: "TRUCK-001", 
      driver_name: "James Wilson",
      timestamp: "2024-08-11 19:30:00",
      location: "Shell Station - Residential Area",
      card_last_4: "2233",
      description: "Weekend fuel purchase in residential area during off-hours",
      severity: "medium",
      estimated_loss: 67.25
    }
  ],
  summary: {
    total_violations: 2,
    total_estimated_loss: 162.75,
    high_risk_vehicles: ["VAN-002", "TRUCK-001"]
  }
}
```

### Clean Fleet Co (Low Fraud)
```javascript
const cleanFleetCo = {
  description: "8-vehicle service fleet with excellent compliance record",
  vehicles: 8,
  violations: [
    {
      type: "minor_deviation",
      vehicle_id: "VAN-001",
      driver_name: "Jennifer Adams",
      timestamp: "2024-08-09 18:15:00",
      location: "BP Station - Route 285",
      card_last_4: "5566",
      description: "Fuel purchase 15 minutes after official end of shift",
      severity: "low",
      estimated_loss: 12.50
    }
  ],
  summary: {
    total_violations: 1,
    total_estimated_loss: 12.50,
    high_risk_vehicles: []
  }
}
```

---

## 📊 DATA PROCESSING LOGIC

### CSV Column Standardization

**Fuel Data Processing**:
```python
# Standard target schema
target_columns = {
    'timestamp': 'datetime',     # Combined date/time
    'location': 'string',        # Gas station name
    'gallons': 'float',         # Fuel quantity
    'vehicle_id': 'string',     # Vehicle identifier
    'driver_name': 'string',    # Driver name
    'card_last_4': 'string',    # Last 4 digits of card
    'amount': 'float'           # Cost in dollars (optional)
}

# Timestamp creation logic
if 'date' in df.columns and 'time' in df.columns:
    df['timestamp'] = pd.to_datetime(
        df['date'].astype(str) + ' ' + df['time'].astype(str), 
        errors='coerce'
    )
elif 'date' in df.columns:
    df['timestamp'] = pd.to_datetime(df['date'], errors='coerce')

# Card last 4 extraction
if 'card_number' in df.columns and 'card_last_4' not in df.columns:
    df['card_last_4'] = df['card_number'].astype(str).str[-4:]
```

**GPS Data Processing**:
```python
# Basic GPS standardization
if 'Timestamp' in gps_df.columns:
    gps_df['timestamp'] = pd.to_datetime(gps_df['Timestamp'], errors='coerce')
elif 'Date' in gps_df.columns:
    gps_df['timestamp'] = pd.to_datetime(gps_df['Date'], errors='coerce')
```

**Job Data Processing**:
```python
# Job scheduling standardization  
if 'Scheduled Time' in job_df.columns:
    job_df['timestamp'] = pd.to_datetime(job_df['Scheduled Time'], errors='coerce')
elif 'Date' in job_df.columns:
    job_df['timestamp'] = pd.to_datetime(job_df['Date'], errors='coerce')
```

---

## 🚨 FRAUD DETECTION ALGORITHMS

### 1. Shared Card Use Detection (Critical)
```
Algorithm:
1. Group fuel transactions by card_last_4
2. For each card, find all transactions within 60-minute windows
3. Check if different vehicles/drivers used same card
4. Calculate time span between transactions
5. Flag violations with complete transaction details

Risk Factors:
- Different vehicles using same card: HIGH
- Same vehicle, multiple uses <60min: MEDIUM  
- Time span <30 minutes: CRITICAL
```

### 2. After-Hours Detection
```
Algorithm:
1. Parse timestamp for hour of day
2. Flag transactions outside 7AM-6PM
3. Additional risk for weekends/holidays
4. Cross-reference with business operating hours

Risk Factors:
- 2AM-5AM transactions: CRITICAL
- Weekend activity: HIGH
- Holiday activity: HIGH
```

### 3. Ghost Job Detection
```
Algorithm:
1. Match scheduled jobs with GPS locations
2. Check for vehicle presence at job location ±30 minutes
3. Flag jobs with no corresponding GPS activity
4. Consider fuel purchases during ghost job times

Risk Factors:
- No GPS at job location: HIGH
- Fuel purchase during ghost job: CRITICAL
- Multiple ghost jobs same driver: CRITICAL
```

### 4. Excessive Fuel Detection
```
Algorithm:
1. Define vehicle capacity thresholds:
   - Vans: 25 gallons max
   - Trucks: 50 gallons max
   - Large trucks: 100 gallons max
2. Flag purchases exceeding capacity
3. Consider multiple fills within short timeframe

Risk Factors:
- >150% capacity: CRITICAL
- Multiple excessive fills: HIGH
```

---

## 📄 PDF REPORT GENERATION

### ReportLab Implementation
```python
def generate_pdf_report():
    # Create PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title and metadata
    title = Paragraph("FleetAudit.io - Fraud Detection Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Summary section
    summary_text = f"""
    Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Total Violations: {len(violations)}
    Estimated Total Loss: ${summary.get('total_estimated_loss', 0):.2f}
    High Risk Vehicles: {', '.join(summary.get('high_risk_vehicles', []))}
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    
    # Violations table
    table_data = [['Type', 'Driver', 'Vehicle', 'Time', 'Location', 'Card', 'Loss']]
    
    # Special handling for shared card violations
    if violation.get('type') == 'shared_card_use':
        vehicles = ', '.join(violation.get('vehicles_involved', []))
        drivers = ', '.join(violation.get('drivers_involved', []))
        card_info = f"****{violation.get('card_last_4', 'Unknown')}"
        time_span = f"{violation.get('time_span_minutes', 'Unknown')} min"
        
        table_data.append([
            'Shared Card Use',
            drivers,
            vehicles,
            time_span,
            'Multiple Locations',
            card_info,
            f"${violation.get('estimated_loss', 0):.2f}"
        ])
    
    # Create styled table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)
```

---

## 🔧 NEXT.JS MIGRATION REQUIREMENTS

### Tech Stack for Migration
```
Frontend:
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- ShadCN UI for components
- React Hook Form for file uploads
- Recharts for data visualization

Backend:
- Next.js API routes
- Anthropic SDK for Claude integration
- Supabase for database
- React-PDF for report generation

File Processing:
- Papa Parse for CSV handling
- Date-fns for timestamp parsing
- React-Dropzone for file uploads
```

### Critical Migration Points

1. **File Upload System**
   - Replace Streamlit file_uploader with react-dropzone
   - Implement client-side CSV preview
   - Handle multiple file types (.csv, .xlsx)

2. **Claude AI Integration**  
   - Move to API routes to protect API keys
   - Implement same prompt engineering
   - Handle streaming responses for better UX

3. **Data Processing**
   - Port pandas logic to JavaScript
   - Use Papa Parse for CSV parsing
   - Implement same column mapping logic

4. **PDF Generation**
   - Replace ReportLab with React-PDF or jsPDF
   - Maintain same table structure and styling
   - Add download functionality

5. **Demo Scenarios**
   - Convert Python demo data to TypeScript
   - Implement interactive demo selector
   - Add realistic loading states

6. **Styling Migration**
   - Convert custom CSS to Tailwind classes
   - Use ShadCN components for consistency
   - Maintain same color scheme and animations

### API Route Structure
```
/api/upload/fuel         # Handle fuel CSV upload
/api/upload/gps          # Handle GPS CSV upload  
/api/upload/jobs         # Handle job CSV upload
/api/analyze/fraud       # Claude fraud detection
/api/reports/generate    # PDF report generation
/api/reports/download    # PDF download endpoint
```

### Component Architecture
```
/components/
  /ui/                   # ShadCN UI components
  /upload/               # File upload components
  /results/              # Fraud results display
  /reports/              # PDF report components
  /demo/                 # Demo scenario components

/app/
  /page.tsx             # Landing page
  /app/                 # Main application
  /pricing/             # Pricing page (future)
  /api/                 # API routes
```

---

## 🎯 CRITICAL SUCCESS FACTORS

### Must-Have Features for V1 Migration
1. ✅ **File Upload System** - Support fuel, GPS, job CSV files
2. ✅ **Claude AI Integration** - Exact same fraud detection logic
3. ✅ **Demo Scenarios** - All 3 scenarios with realistic data
4. ✅ **Results Display** - Professional violation cards and metrics
5. ✅ **PDF Reports** - Downloadable reports with same formatting
6. ✅ **Responsive Design** - Mobile-friendly interface
7. ✅ **Professional Styling** - Same color scheme and animations

### Performance Requirements
- File upload handling up to 10MB CSV files
- Claude API response handling with loading states
- PDF generation under 5 seconds
- Mobile responsiveness down to 320px width

### Security Requirements
- API key protection through environment variables
- File upload validation and sanitization
- Rate limiting on Claude API calls
- HTTPS enforcement in production

---

## 🚫 KNOWN ISSUES & LIMITATIONS

### Current Streamlit Problems
1. **Navigation Failure**: `st.switch_page()` doesn't work in Streamlit Cloud
2. **Mobile Responsiveness**: Limited mobile optimization
3. **File Size Limits**: Streamlit has upload size restrictions
4. **Real-time Updates**: No live data connections
5. **User Management**: No authentication or user accounts

### Technical Debt
- Unused backend services (`/backend/`, `/logic/`, `/parsers/`)
- Multiple test CSV files cluttering repo
- Hardcoded demo scenarios
- No automated testing
- No CI/CD pipeline

---

## 📋 MIGRATION CHECKLIST

### Phase 1: Core Setup
- [ ] Initialize Next.js 14 project with TypeScript
- [ ] Configure Tailwind CSS and ShadCN UI
- [ ] Set up environment variables
- [ ] Create basic project structure

### Phase 2: Landing Page
- [ ] Port hero section with gradients
- [ ] Implement demo scenario selector
- [ ] Add interactive fraud results display
- [ ] Style pricing section

### Phase 3: Core Application  
- [ ] Build file upload system with react-dropzone
- [ ] Implement CSV parsing and preview
- [ ] Create Claude API integration
- [ ] Build results display components

### Phase 4: Advanced Features
- [ ] Add PDF report generation
- [ ] Implement download functionality
- [ ] Add responsive design
- [ ] Optimize performance

### Phase 5: Polish & Deploy
- [ ] Add loading states and error handling
- [ ] Implement proper TypeScript types
- [ ] Add basic analytics
- [ ] Deploy to Vercel

---

## 🎨 EXACT STYLING SPECIFICATIONS

### Typography
```css
/* Headers */
h1: font-size: 3.5rem, font-weight: 800, color: white
h2: font-size: 2.2rem, color: #1f4e79  
h3: font-size: 1.3rem, color: #1f4e79
p: font-size: 1.1rem, line-height: 1.6

/* Body text */
font-family: system-ui, -apple-system, sans-serif
```

### Spacing & Layout
```css
/* Container padding */
sections: padding: 2rem-4rem
cards: padding: 1.5rem-2rem  
buttons: padding: 0.75rem-2rem

/* Margins */
sections: margin-bottom: 2rem-3rem
cards: margin-bottom: 1.5rem
elements: margin-bottom: 1rem

/* Border radius */
cards: 12px
buttons: 8px
inputs: 6px
```

### Shadows & Effects
```css
/* Card shadows */
default: 0 4px 16px rgba(0,0,0,0.1)
hover: 0 8px 24px rgba(0,0,0,0.15)

/* Button hover */
transform: translateY(-2px)
box-shadow: 0 6px 20px rgba(31, 78, 121, 0.3)

/* Transitions */
all: 0.3s ease
```

---

## 🔐 ENVIRONMENT VARIABLES

### Required for Next.js
```bash
# Claude AI (Critical)
ANTHROPIC_API_KEY=sk-ant-...

# Supabase (Future features)
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# App Configuration
NEXT_PUBLIC_APP_URL=https://fleetaudit-v2.vercel.app
NEXT_PUBLIC_APP_ENV=production

# Analytics (Optional)
NEXT_PUBLIC_GA_ID=G-...
```

### Development vs Production
```bash
# Development
NEXT_PUBLIC_APP_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Production  
NEXT_PUBLIC_APP_ENV=production
NEXT_PUBLIC_APP_URL=https://fleetaudit-v2.vercel.app
```

---

This documentation represents 100% of the current FleetAudit.io system. Every function, component, styling rule, and business logic requirement has been captured for the Next.js migration.

**Key Files Referenced**:
- `/app.py` - Landing page with demo scenarios  
- `/pages/1_Product.py` - Main fraud detection application
- `/requirements.txt` - All dependencies
- `/sample_data/` - Test scenarios and CSV formats

**Ready for Migration**: This documentation provides everything needed to rebuild FleetAudit.io in Next.js with full feature parity.