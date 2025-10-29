"""
PHR Employee Custom Fields Configuration
All Employee custom fields are defined here in a single place
"""

EMPLOYEE_CUSTOM_FIELDS = [
    # Basic Information Section
    {
        "fieldname": "custom_nationalit",
        "fieldtype": "Select",
        "label": "Nationality",
        "options": "Saudi\nEgyptian\nIndian\nPakistani\nFilipino\nBangladeshi\nOther",
        "default": "Saudi",
        "insert_after": "employee_name",
        "reqd": 0
    },
    {
        "fieldname": "salary",
        "fieldtype": "Currency",
        "label": "Current Salary",
        "insert_after": "custom_nationalit",
        "reqd": 0
    },
    
    # Contract Information Section
    {
        "fieldname": "contract_start_date",
        "fieldtype": "Date",
        "label": "Contract Start Date",
        "insert_after": "date_of_joining",
        "reqd": 0
    },
    {
        "fieldname": "contract_end_date",
        "fieldtype": "Date",
        "label": "Contract End Date",
        "insert_after": "contract_start_date",
        "reqd": 0
    },
    {
        "fieldname": "contract_duration_months",
        "fieldtype": "Int",
        "label": "Contract Duration Months",
        "insert_after": "contract_end_date",
        "default": 15,
        "read_only": 1
    },
    {
        "fieldname": "contract_duration_years",
        "fieldtype": "Int",
        "label": "Contract Duration Years",
        "insert_after": "contract_duration_months",
        "default": 1,
        "read_only": 1
    },
    {
        "fieldname": "contract_duration_days",
        "fieldtype": "Int",
        "label": "Contract Duration Days",
        "insert_after": "contract_duration_years",
        "default": 180,
        "read_only": 1
    },
    {
        "fieldname": "remaining_contract_days",
        "fieldtype": "Int",
        "label": "Remaining Contract Days",
        "insert_after": "contract_duration_days",
        "default": 0,
        "read_only": 1
    },
    {
        "fieldname": "contract_status",
        "fieldtype": "Select",
        "label": "Contract Status",
        "options": "Active\nExpired\nTerminated\nCancelled",
        "default": "Active",
        "insert_after": "remaining_contract_days",
        "reqd": 0
    },
    {
        "fieldname": "years_of_service",
        "fieldtype": "Float",
        "label": "Years of Service",
        "insert_after": "contract_status",
        "read_only": 1,
        "precision": 2
    },
    
    # Employee Details Section
    {
        "fieldname": "is_muslim",
        "fieldtype": "Check",
        "label": "Is Muslim",
        "insert_after": "years_of_service",
        "default": 0
    },
    {
        "fieldname": "is_female",
        "fieldtype": "Check",
        "label": "Is Female",
        "insert_after": "is_muslim",
        "default": 0
    },
    {
        "fieldname": "custom_employee_status",
        "fieldtype": "Select",
        "label": "Employee Status",
        "options": "In Service\nOut of Service\nOn Leave\nSuspended",
        "default": "In Service",
        "insert_after": "is_female",
        "reqd": 0
    },
    
    # Testing Period Section
    {
        "fieldname": "testing_period_end_date",
        "fieldtype": "Date",
        "label": "Testing Period End Date",
        "insert_after": "custom_employee_status",
        "depends_on": "eval:doc.status == 'Active'",
        "reqd": 0
    },
    {
        "fieldname": "testing_period_remaining_days",
        "fieldtype": "Int",
        "label": "Testing Period Remaining Days",
        "insert_after": "testing_period_end_date",
        "default": 0,
        "read_only": 1,
        "depends_on": "eval:doc.status == 'Active'"
    },
    {
        "fieldname": "remaining_testing_days",
        "fieldtype": "Int",
        "label": "Remaining Testing Days",
        "insert_after": "testing_period_remaining_days",
        "default": 0,
        "read_only": 1,
        "depends_on": "eval:doc.status == 'Active'"
    },
    
    # Leave Analysis Section
    {
        "fieldname": "leave_analysis_section",
        "fieldtype": "Section Break",
        "label": "Leave Analysis",
        "insert_after": "remaining_testing_days"
    },
    {
        "fieldname": "total_leave_balance",
        "fieldtype": "Float",
        "label": "Total Leave Balance",
        "insert_after": "leave_analysis_section",
        "default": 0.0,
        "read_only": 1,
        "precision": 1
    },
    {
        "fieldname": "annual_leave_balance",
        "fieldtype": "Float",
        "label": "Annual Leave Balance",
        "insert_after": "total_leave_balance",
        "default": 0.0,
        "read_only": 1,
        "precision": 1
    },
    {
        "fieldname": "is_additional_annual_leave",
        "fieldtype": "Check",
        "label": "Is Additional Annual Leave",
        "insert_after": "annual_leave_balance",
        "default": 0,
        "description": "Check if employee is eligible for additional annual leave (2.5 days/month instead of 1.75 days/month)"
    },
    {
        "fieldname": "annual_leave_used",
        "fieldtype": "Float",
        "label": "Annual Leave Used",
        "insert_after": "is_additional_annual_leave",
        "default": 0.0,
        "read_only": 1,
        "precision": 1
    },
    {
        "fieldname": "annual_leave_remaining",
        "fieldtype": "Float",
        "label": "Annual Leave Remaining",
        "insert_after": "annual_leave_used",
        "default": 0.0,
        "read_only": 1,
        "precision": 1
    },
    {
        "fieldname": "sick_leave_balance",
        "fieldtype": "Float",
        "label": "Sick Leave Balance",
        "insert_after": "annual_leave_remaining",
        "default": 0.0,
        "read_only": 1,
        "precision": 1
    },
    {
        "fieldname": "sick_leave_used",
        "fieldtype": "Float",
        "label": "Sick Leave Used",
        "insert_after": "sick_leave_balance",
        "default": 0.0,
        "read_only": 1,
        "precision": 1
    },
    {
        "fieldname": "sick_leave_remaining",
        "fieldtype": "Float",
        "label": "Sick Leave Remaining",
        "insert_after": "sick_leave_used",
        "default": 0.0,
        "read_only": 1,
        "precision": 1
    },
    {
        "fieldname": "last_leave_calculation_date",
        "fieldtype": "Date",
        "label": "Last Leave Calculation Date",
        "insert_after": "sick_leave_remaining",
        "read_only": 1
    },
    
    # Notification Section
    {
        "fieldname": "notification_section",
        "fieldtype": "Section Break",
        "label": "Notifications",
        "insert_after": "last_leave_calculation_date"
    },
    {
        "fieldname": "last_notification_date",
        "fieldtype": "Date",
        "label": "Last Notification Date",
        "insert_after": "notification_section",
        "read_only": 1
    },
    {
        "fieldname": "notification_sent_30_days",
        "fieldtype": "Check",
        "label": "30-Day Notification Sent",
        "insert_after": "last_notification_date",
        "default": 0,
        "read_only": 1
    },
    {
        "fieldname": "notification_sent_90_days",
        "fieldtype": "Check",
        "label": "90-Day Notification Sent",
        "insert_after": "notification_sent_30_days",
        "default": 0,
        "read_only": 1
    },
    
    # Additional Fields Section
    {
        "fieldname": "additional_fields_section",
        "fieldtype": "Section Break",
        "label": "Additional Information",
        "insert_after": "notification_sent_90_days"
    },
    {
        "fieldname": "custom_sub_record",
        "fieldtype": "Data",
        "label": "Sub Record",
        "insert_after": "additional_fields_section",
        "reqd": 0
    },
    
    # Hidden Fields for Internal Use
    {
        "fieldname": "sick_leave_balance_custom",
        "fieldtype": "Float",
        "label": "Sick Leave Balance (Hidden)",
        "insert_after": "custom_sub_record",
        "read_only": 1,
        "precision": 1,
        "hidden": 1,
        "print_hide": 1,
        "report_hide": 1,
        "allow_on_submit": 1,
        "depends_on": "eval:doc.status == 'Active'"
    },
    {
        "fieldname": "sick_leave_remaining_custom",
        "fieldtype": "Float",
        "label": "Sick Leave Remaining (Hidden)",
        "insert_after": "sick_leave_balance_custom",
        "read_only": 1,
        "precision": 1,
        "hidden": 1,
        "print_hide": 1,
        "report_hide": 1,
        "allow_on_submit": 1,
        "depends_on": "eval:doc.status == 'Active'"
    }
]

