# PHR - Pioneer HR Management System

## Overview
The PHR (Pioneer HR) system is a comprehensive human resource management solution built on the Frappe framework. It provides advanced leave management, contract tracking, and employee lifecycle management features.

## Features

### 1. Employee Management
- **Enhanced Employee Records**: Additional fields for contract management, testing periods, and demographic information
- **Working Years Calculation**: Automatic calculation of years of service from joining date
- **Contract End Tracking**: Monitor contract end dates with automated notifications
- **Testing Period Management**: Track and calculate remaining testing period days

### 2. Leave Management System
- **Automatic Leave Allocation**: Based on years of service (21 days for <5 years, 30 days for 5+ years)
- **Sick Leave Tracking**: Daily accumulation with different rates based on service years
- **Leave Balance Management**: Real-time calculation and tracking of leave balances
- **Gender and Religious Restrictions**: Support for gender and religious-specific leave types

### 3. Contract Management
- **90-Day Notifications**: Automated notifications for contracts ending within 90 days
- **Email Alerts**: Automatic email notifications to HR team
- **Contract Dashboard**: Visual summary of contracts ending soon
- **ToDo Integration**: Automatic task creation for contract management

### 4. Salary Integration
- **Sick Leave Deductions**: Automatic salary deductions for sick leave beyond paid periods
- **Flexible Deduction Rules**: 25% deduction for days 31-90, 100% for days 90+
- **Salary Component Management**: Automatic creation of required salary components

## Installation

### Prerequisites
- Frappe Framework installed
- ERPNext or HRMS app installed
- MySQL database

### Setup Steps

1. **Install the PHR App**:
   ```bash
   bench get-app phr
   bench --site [site-name] install-app phr
   ```

2. **Run Database Migrations**:
   ```bash
   bench --site [site-name] migrate
   ```

3. **Setup PHR System**:
   ```bash
   bench --site [site-name] console
   ```
   ```python
   from phr.setup_phr import setup_phr_system
   setup_phr_system()
   ```

4. **Restart Services**:
   ```bash
   bench restart
   ```

## Configuration

### Employee Fields Added
- `contract_end_date`: Date when employee contract ends
- `testing_period_end_date`: End date of testing period
- `remaining_testing_days`: Days remaining in testing period
- `is_muslim`: Flag for Muslim employees (0 or 1)
- `is_female`: Flag for female employees (0 or 1)
- `annual_leave_balance`: Total annual leave allocated
- `annual_leave_used`: Annual leave used
- `annual_leave_remaining`: Annual leave remaining
- `sick_leave_balance`: Sick leave balance
- `sick_leave_used`: Sick leave used
- `sick_leave_remaining`: Sick leave remaining

### Leave Type Fields Added
- `is_annual_leave`: Flag for annual leave types
- `is_sick_leave`: Flag for sick leave types
- `is_female`: Flag for female-only leave types
- `is_muslim`: Flag for Muslim-only leave types

## Usage

### Employee Management

1. **Creating Employee Records**:
   - Fill in basic employee information
   - Set joining date (triggers automatic calculations)
   - Set contract end date (enables contract tracking)
   - Mark gender and religious preferences

2. **Automatic Leave Allocation**:
   - System automatically creates leave allocations based on joining date
   - Annual leave: 21 days for <5 years service, 30 days for 5+ years
   - Sick leave: Unlimited but tracked with daily accumulation

3. **Leave Balance Management**:
   - Use "Calculate Leave Balances" button to update balances
   - View comprehensive leave summary
   - Track sick leave daily accumulation

### Contract Management

1. **Contract End Notifications**:
   - System automatically checks for contracts ending in 90 days
   - Sends email notifications to HR team
   - Creates ToDo tasks for follow-up

2. **Contract Dashboard**:
   - View all contracts ending soon
   - Categorize by urgency (30, 60, 90 days)
   - Track contract renewal status

### Leave Applications

1. **Sick Leave Processing**:
   - First 30 days: Full pay
   - Days 31-90: 75% pay (25% deduction)
   - Days 90+: No pay (100% deduction)

2. **Salary Integration**:
   - Automatic salary deductions for sick leave
   - Flexible deduction rules based on leave duration
   - Integration with salary slip generation

## API Endpoints

### Leave Management
- `get_employee_leave_summary(employee_id)`: Get comprehensive leave summary
- `create_employee_leave_allocations(employee_id)`: Create automatic allocations
- `sync_all_employee_leave_balances()`: Sync all employee balances

### Contract Management
- `check_contract_notifications()`: Check and send notifications
- `get_contract_summary_data()`: Get contract summary

### System Setup
- `setup_phr_system()`: Initialize PHR system

## Scheduler Events

### Daily Tasks
- Contract end notification checks
- Leave balance synchronization

### Hourly Tasks
- Daily leave balance updates
- Sick leave accumulation

## Customization

### Adding New Leave Types
1. Create new Leave Type record
2. Set appropriate flags (is_annual_leave, is_sick_leave, etc.)
3. Configure maximum leaves allowed
4. Set gender/religious restrictions if needed

### Modifying Deduction Rules
1. Edit salary components in Salary Component doctype
2. Modify formulas in `phr.phr.utils.salary_components`
3. Update deduction logic as needed

### Custom Notifications
1. Modify notification templates in `phr.phr.utils.contract_management`
2. Add custom email templates
3. Configure notification recipients

## Troubleshooting

### Common Issues

1. **Leave Balances Not Updating**:
   - Run "Calculate Leave Balances" manually
   - Check if leave allocations exist
   - Verify employee joining date

2. **Contract Notifications Not Sending**:
   - Check scheduler status
   - Verify email configuration
   - Check contract end dates

3. **Salary Deductions Not Applied**:
   - Verify salary components exist
   - Check leave application status
   - Ensure salary slip is properly configured

### Debug Mode
Enable debug mode in site_config.json:
```json
{
    "debug": 1
}
```

## Support

For technical support or feature requests, contact:
- Email: info@pioneersholding.ae
- Documentation: [Internal Wiki]
- Issue Tracker: [Internal System]

## Version History

### v1.0 (September 12, 2025)
- Initial release
- Employee management enhancements
- Leave management system
- Contract management
- Salary integration
- Automated notifications

## License

This software is proprietary to Pioneer Holding and is not for public distribution.
