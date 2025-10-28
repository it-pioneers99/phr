# PHR Employee Summary System

## Overview
The PHR Employee Summary System provides comprehensive employee management features including annual leave balance calculation, sick leave tracking with salary deductions, and test period notifications.

## Features

### 1. Annual Leave Balance Calculation
- **Years of Service Based**: Leave allocation increases with years of service
  - 0-2 years: 21 days
  - 3-5 years: 30 days  
  - 6-10 years: 35 days
  - 10+ years: 40 days
- **Automatic Calculation**: Updates leave balances based on service years
- **Real-time Tracking**: Shows used, remaining, and allocated leave

### 2. Sick Leave Management
- **Salary Deductions**: Automatic calculation based on sick leave days
  - First 30 days: No deduction
  - Days 31-90: 25% salary deduction
  - Days 91+: 100% salary deduction
- **Balance Tracking**: Monitors used and remaining sick leave
- **Financial Impact**: Shows total deduction amounts

### 3. Test Period Management
- **180-Day Period**: Calculated from joining date
- **Automatic Notifications**:
  - 60 days before end (120 days from joining)
  - 30 days before end (150 days from joining)
- **Status Tracking**: Shows remaining days and status

### 4. Dashboard Interface
- **Visual Dashboard**: Interactive employee summary display
- **Progress Bars**: Visual representation of leave usage
- **Alert System**: Color-coded alerts for test period warnings
- **Real-time Updates**: Refresh data and recalculate balances

## File Structure

```
phr/
├── phr/
│   ├── employee_summary_calculator.py    # Core calculation logic
│   ├── api/
│   │   └── employee_summary.py           # API endpoints
│   ├── scheduled_tasks/
│   │   └── employee_summary_tasks.py     # Daily/weekly tasks
│   └── patches/
│       └── v1_0/
│           └── add_phr_fields_to_employee.py  # Database fields
├── public/
│   └── js/
│       └── employee_summary_dashboard.js # Frontend dashboard
└── hooks.py                              # App configuration
```

## Installation

1. **Database Fields**: The system automatically adds required fields to the Employee doctype
2. **Scheduled Tasks**: Configured in hooks.py for automatic execution
3. **API Endpoints**: Available for external integrations

## Usage

### API Endpoints

#### Get Employee Summary
```python
POST /api/method/phr.api.employee_summary.get_employee_summary
{
    "employee_id": "EMP-001"
}
```

#### Calculate Leave Balance
```python
POST /api/method/phr.api.employee_summary.calculate_employee_leave_balance
{
    "employee_id": "EMP-001"
}
```

#### Get All Employees Summary
```python
POST /api/method/phr.api.employee_summary.get_all_employees_summary
```

#### Get Leave Balance Report
```python
POST /api/method/phr.api.employee_summary.get_leave_balance_report
```

#### Get Test Period Alerts
```python
POST /api/method/phr.api.employee_summary.get_test_period_alerts
```

### Frontend Integration

#### Employee Dashboard
```javascript
// Initialize dashboard
const dashboard = new phr.employee_summary.EmployeeSummaryDashboard($('#container'));
dashboard.load('EMP-001');

// Refresh data
phr.employee_summary.refreshData('EMP-001');

// Calculate leave balance
phr.employee_summary.calculateLeaveBalance('EMP-001');
```

### Scheduled Tasks

#### Daily Tasks
- **Employee Summary Calculation**: Updates all employee summaries
- **Test Period Notifications**: Sends alerts for ending test periods

#### Weekly Tasks
- **Leave Balance Report**: Generates and emails weekly reports

#### Monthly Tasks
- **Cleanup**: Removes old notifications and logs

## Configuration

### Email Settings
Update email recipients in `scheduled_tasks/employee_summary_tasks.py`:
```python
frappe.sendmail(
    recipients=["hr@pioneersholding.ae"],  # Update this
    subject="...",
    message="..."
)
```

### Leave Allocation Rules
Modify in `employee_summary_calculator.py`:
```python
def get_annual_leave_allocation(years_of_service):
    if years_of_service < 3:
        return 21
    elif years_of_service < 6:
        return 30
    elif years_of_service < 11:
        return 35
    else:
        return 40
```

### Sick Leave Deduction Rules
Modify in `employee_summary_calculator.py`:
```python
def calculate_sick_leave_deductions(used_days, daily_salary):
    # First 30 days: No deduction
    # Days 31-90: 25% deduction
    # Days 91+: 100% deduction
```

## Database Fields

The system adds these fields to the Employee doctype:

### Leave Management
- `annual_leave_balance`: Total allocated annual leave
- `annual_leave_used`: Days used this year
- `annual_leave_remaining`: Days remaining
- `sick_leave_balance`: Total allocated sick leave
- `sick_leave_used`: Days used this year
- `sick_leave_remaining`: Days remaining

### Test Period
- `testing_period_end_date`: End date of test period
- `remaining_testing_days`: Days remaining in test period

### Service Information
- `years_of_service`: Calculated years of service
- `contract_end_date`: Contract end date
- `is_muslim`: Muslim employee flag
- `is_female`: Female employee flag

## Testing

Run the test script to verify the system:
```bash
cd /home/gadallah/frappe-bench
python test_employee_summary.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all files are in correct locations
2. **Database Errors**: Run the patch to add required fields
3. **Permission Errors**: Check user permissions for API access
4. **Email Errors**: Verify email configuration in Frappe

### Logs
Check Frappe logs for detailed error information:
```bash
tail -f /home/gadallah/frappe-bench/logs/frappe.log
```

## Support

For issues or questions:
- Check Frappe logs for error details
- Verify database field existence
- Test API endpoints individually
- Contact system administrator

## Version History

- **v1.0**: Initial implementation with basic leave calculation
- **v1.1**: Added sick leave deductions and test period notifications
- **v1.2**: Enhanced dashboard and API endpoints
