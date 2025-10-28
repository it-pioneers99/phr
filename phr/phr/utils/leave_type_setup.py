import frappe
from frappe import _

@frappe.whitelist()
def create_default_leave_types():
    """Create default leave types with restriction fields"""
    
    default_leave_types = [
        {
            'leave_type_name': 'Annual Leave',
            'is_annual_leave': 1,
            'is_sick_leave': 0,
            'is_muslim': 0,
            'is_female': 0
        },
        {
            'leave_type_name': 'Sick Leave',
            'is_annual_leave': 0,
            'is_sick_leave': 1,
            'is_muslim': 0,
            'is_female': 0
        },
        {
            'leave_type_name': 'Annual Leave - Female Only',
            'is_annual_leave': 1,
            'is_sick_leave': 0,
            'is_muslim': 0,
            'is_female': 1
        },
        {
            'leave_type_name': 'Sick Leave - Female Only',
            'is_annual_leave': 0,
            'is_sick_leave': 1,
            'is_muslim': 0,
            'is_female': 1
        },
        {
            'leave_type_name': 'Annual Leave - Muslim Only',
            'is_annual_leave': 1,
            'is_sick_leave': 0,
            'is_muslim': 1,
            'is_female': 0
        },
        {
            'leave_type_name': 'Sick Leave - Muslim Only',
            'is_annual_leave': 0,
            'is_sick_leave': 1,
            'is_muslim': 1,
            'is_female': 0
        },
        {
            'leave_type_name': 'Annual Leave - Muslim Female Only',
            'is_annual_leave': 1,
            'is_sick_leave': 0,
            'is_muslim': 1,
            'is_female': 1
        },
        {
            'leave_type_name': 'Sick Leave - Muslim Female Only',
            'is_annual_leave': 0,
            'is_sick_leave': 1,
            'is_muslim': 1,
            'is_female': 1
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for leave_type_data in default_leave_types:
        leave_type_name = leave_type_data['leave_type_name']
        
        if frappe.db.exists('Leave Type', leave_type_name):
            # Update existing leave type
            leave_type = frappe.get_doc('Leave Type', leave_type_name)
            leave_type.is_annual_leave = leave_type_data['is_annual_leave']
            leave_type.is_sick_leave = leave_type_data['is_sick_leave']
            leave_type.is_muslim = leave_type_data['is_muslim']
            leave_type.is_female = leave_type_data['is_female']
            leave_type.save()
            updated_count += 1
        else:
            # Create new leave type
            leave_type = frappe.get_doc({
                'doctype': 'Leave Type',
                'leave_type_name': leave_type_name,
                'is_annual_leave': leave_type_data['is_annual_leave'],
                'is_sick_leave': leave_type_data['is_sick_leave'],
                'is_muslim': leave_type_data['is_muslim'],
                'is_female': leave_type_data['is_female']
            })
            leave_type.insert()
            created_count += 1
    
    frappe.db.commit()
    
    return {
        'status': 'success',
        'message': f'Leave types setup completed. Created: {created_count}, Updated: {updated_count}',
        'created': created_count,
        'updated': updated_count
    }

@frappe.whitelist()
def get_leave_types_by_restrictions(employee_id=None):
    """Get leave types based on employee restrictions"""
    
    if not employee_id:
        return {
            'status': 'error',
            'message': 'Employee ID is required'
        }
    
    # Get employee details
    employee = frappe.get_doc('Employee', employee_id)
    
    # Build filter based on employee restrictions
    filters = {}
    
    # If employee is female, include female-only leave types
    if employee.is_female:
        filters['is_female'] = 1
    else:
        # If not female, exclude female-only leave types
        filters['is_female'] = 0
    
    # If employee is Muslim, include Muslim-only leave types
    if employee.is_muslim:
        filters['is_muslim'] = 1
    else:
        # If not Muslim, exclude Muslim-only leave types
        filters['is_muslim'] = 0
    
    # Get matching leave types
    leave_types = frappe.get_all('Leave Type',
        filters=filters,
        fields=['name', 'leave_type_name', 'is_annual_leave', 'is_sick_leave', 'is_muslim', 'is_female']
    )
    
    return {
        'status': 'success',
        'employee_name': employee.employee_name,
        'is_female': employee.is_female,
        'is_muslim': employee.is_muslim,
        'leave_types': leave_types,
        'total_count': len(leave_types)
    }

@frappe.whitelist()
def get_annual_leave_types():
    """Get all annual leave types"""
    return frappe.get_all('Leave Type',
        filters={'is_annual_leave': 1},
        fields=['name', 'leave_type_name', 'is_muslim', 'is_female']
    )

@frappe.whitelist()
def get_sick_leave_types():
    """Get all sick leave types"""
    return frappe.get_all('Leave Type',
        filters={'is_sick_leave': 1},
        fields=['name', 'leave_type_name', 'is_muslim', 'is_female']
    )

@frappe.whitelist()
def get_female_leave_types():
    """Get all female-only leave types"""
    return frappe.get_all('Leave Type',
        filters={'is_female': 1},
        fields=['name', 'leave_type_name', 'is_annual_leave', 'is_sick_leave', 'is_muslim']
    )

@frappe.whitelist()
def get_muslim_leave_types():
    """Get all Muslim-only leave types"""
    return frappe.get_all('Leave Type',
        filters={'is_muslim': 1},
        fields=['name', 'leave_type_name', 'is_annual_leave', 'is_sick_leave', 'is_female']
    )

@frappe.whitelist()
def get_all_leave_types_with_restrictions():
    """Get all leave types with their restriction flags"""
    return frappe.get_all('Leave Type',
        fields=['name', 'leave_type_name', 'is_annual_leave', 'is_sick_leave', 'is_muslim', 'is_female']
    )
