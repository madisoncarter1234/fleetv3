# FleetAudit.io MVP

A comprehensive fleet monitoring and audit system that analyzes GPS logs, fuel card data, and job schedules to detect waste, fraud, and suspicious behavior.

## Features

🚛 **Multi-Source Data Integration**
- GPS tracking data (Samsara, Verizon Connect)
- Fuel card transactions (WEX, Fleetcor, Fuelman)
- Job scheduling data (Jobber, Housecall Pro, ServiceTitan)

🔍 **Automated Violation Detection**
- Fuel theft detection
- Ghost jobs (scheduled but not visited)
- Excessive vehicle idling
- After-hours driving activity

📊 **Professional Reporting**
- Branded PDF reports
- Executive summary with key metrics
- Detailed violation breakdowns
- Automated email delivery

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd fleetaudit

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file with your API keys:

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual keys
RESEND_API_KEY=your_resend_api_key
SENDGRID_API_KEY=your_sendgrid_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Run the Application

```bash
# Start the Streamlit app
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage

### Step 1: Upload Data Files

1. **GPS Logs**: Upload CSV files from your GPS tracking provider
2. **Fuel Card Data**: Upload transaction records from your fuel card provider
3. **Job Logs**: Upload scheduling data from your job management system

### Step 2: Configure Audit Parameters

- Set detection thresholds for each violation type
- Configure business hours
- Specify company information

### Step 3: Run Audit

- Click "Run Fleet Audit" to analyze your data
- Review violation summary and detailed results

### Step 4: Generate & Send Reports

- Preview the HTML report
- Generate branded PDF report
- Email reports to stakeholders

## Supported Data Formats

### GPS Providers
- **Samsara**: Standard CSV export
- **Verizon Connect**: Fleet tracking export
- **Generic**: Auto-detection for other providers

### Fuel Card Providers
- **WEX**: Transaction history export
- **Fleetcor**: Fuel purchase records
- **Fuelman**: Standard transaction export

### Job Management Systems
- **Jobber**: Job export (CSV/Excel)
- **Housecall Pro**: Schedule export
- **ServiceTitan**: Job dispatch records

## Project Structure

```
fleetaudit/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── parsers/              # Data parsing modules
│   ├── gps_parser.py     # GPS data normalization
│   ├── fuel_parser.py    # Fuel card data parsing
│   └── job_parser.py     # Job scheduling data parsing
├── logic/                # Core audit logic
│   ├── matcher.py        # Violation detection algorithms
│   ├── utils.py          # Utility functions
│   └── report_generator.py # Report generation
├── templates/            # Report templates
│   └── report.html       # HTML report template
├── email/                # Email functionality
│   └── send_email.py     # Email sending logic
└── reports/              # Generated reports (auto-created)
```

## Violation Detection Algorithms

### 1. Fuel Theft Detection
- Cross-references fuel purchases with GPS location data
- Flags purchases without corresponding GPS activity
- Configurable distance and time thresholds

### 2. Ghost Job Detection
- Matches scheduled jobs with GPS tracking data
- Identifies jobs marked as completed without site visits
- Configurable proximity and time window settings

### 3. Idle Time Abuse
- Analyzes GPS speed data to identify extended idle periods
- Flags excessive idling beyond set thresholds
- Excludes legitimate stops and traffic delays

### 4. After-Hours Driving
- Monitors GPS activity outside business hours
- Flags unauthorized vehicle usage
- Configurable business hour settings

## Email Providers

The system supports multiple email providers:

### Resend (Recommended)
```bash
RESEND_API_KEY=your_api_key
```

### SendGrid
```bash
SENDGRID_API_KEY=your_api_key
```

### SMTP (Fallback)
```bash
SMTP_USER=your_email@domain.com
SMTP_PASSWORD=your_password
```

## Deployment Options

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

### Fly.io
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy
fly auth login
fly launch
fly deploy
```

### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Development

### Adding New Data Providers

1. **GPS Provider**: Add new parser method to `parsers/gps_parser.py`
2. **Fuel Provider**: Add new parser method to `parsers/fuel_parser.py`
3. **Job Provider**: Add new parser method to `parsers/job_parser.py`

### Custom Violation Rules

Add new detection algorithms to `logic/matcher.py`:

```python
def detect_custom_violation(self, custom_params):
    """Implement custom violation detection logic"""
    violations = []
    # Your custom logic here
    return violations
```

## Testing

Generate a sample report for testing:

```bash
python logic/report_generator.py
```

## Troubleshooting

### Common Issues

1. **PDF Generation Fails**
   - Install system dependencies for WeasyPrint
   - macOS: `brew install cairo pango gdk-pixbuf libffi`
   - Ubuntu: `apt-get install libcairo2-dev libpango1.0-dev`

2. **Email Sending Fails**
   - Verify API keys are correctly set
   - Check email provider quotas and limits
   - Ensure sender domain is verified

3. **Data Parsing Errors**
   - Verify CSV format matches expected structure
   - Check for missing columns or data types
   - Use generic parser for unknown formats

### Support

For issues and feature requests, please create an issue in the repository.

## License

This project is licensed under the MIT License.

## Roadmap

- [ ] Real-time data ingestion via APIs
- [ ] Advanced analytics and trend analysis
- [ ] Mobile app for field verification
- [ ] Integration with fleet management systems
- [ ] Machine learning for anomaly detection