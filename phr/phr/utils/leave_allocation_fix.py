import frappe
from frappe import _

@frappe.whitelist()
def fix_exceeding_leave_allocations():
    """Fix leave allocations that exceed the maximum allowed days"""
    try:
        # Get all leave allocations that might be exceeding limits
        allocations = frappe.get_all('Leave Allocation', 
            fields=['name', 'employee', 'leave_type', 'new_leaves_allocated', 'from_date', 'to_date'],
            filters={'docstatus': 1}  # Only submitted allocations
        )
        
        fixed_count = 0
        error_count = 0
        
        for allocation in allocations:
            try:
                # Get leave type details
                leave_type = frappe.get_doc('Leave Type', allocation['leave_type'])
                max_days_allowed = leave_type.get('max_days_allowed', 0)
                
                if max_days_allowed and allocation['new_leaves_allocated'] > max_days_allowed:
                    # Fix the allocation
                    allocation_doc = frappe.get_doc('Leave Allocation', allocation['name'])
                    allocation_doc.new_leaves_allocated = max_days_allowed
                    allocation_doc.save()
                    allocation_doc.submit()
                    
                    frappe.msgprint(f"Fixed allocation for {allocation['employee']} - {allocation['leave_type']}: {allocation['new_leaves_allocated']} → {max_days_allowed} days")
                    fixed_count += 1
                    
            except Exception as e:
                frappe.log_error(f"Error fixing allocation {allocation['name']}: {str(e)}")
                error_count += 1
        
        frappe.msgprint(f"Fixed {fixed_count} allocations. {error_count} errors occurred.")
        return True
        
    except Exception as e:
        frappe.log_error(f"Error fixing exceeding leave allocations: {str(e)}")
        return False

@frappe.whitelist()
def check_leave_type_limits():
    """Check all leave types and their maximum limits"""
    try:
        leave_types = frappe.get_all('Leave Type', 
            fields=['name', 'max_days_allowed', 'is_female', 'is_muslim', 'is_annual_leave', 'is_sick_leave'],
            filters={'is_lwp': 0}
        )
        
        result = []
        for lt in leave_types:
            result.append({
                'leave_type': lt['name'],
                'max_days_allowed': lt.get('max_days_allowed', 'No limit'),
                'is_female': lt.get('is_female', 0),
                'is_muslim': lt.get('is_muslim', 0),
                'is_annual_leave': lt.get('is_annual_leave', 0),
                'is_sick_leave': lt.get('is_sick_leave', 0)
            })
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error checking leave type limits: {str(e)}")
        return []

@frappe.whitelist()
def get_employee_leave_allocations(employee):
    """Get all leave allocations for an employee"""
    try:
        allocations = frappe.get_all('Leave Allocation', 
            fields=['name', 'leave_type', 'new_leaves_allocated', 'from_date', 'to_date', 'docstatus'],
            filters={'employee': employee, 'docstatus': 1}
        )
        
        result = []
        for allocation in allocations:
            # Get leave type max limit
            leave_type = frappe.get_doc('Leave Type', allocation['leave_type'])
            max_days_allowed = leave_type.get('max_days_allowed', 0)
            
            result.append({
                'allocation_name': allocation['name'],
                'leave_type': allocation['leave_type'],
                'allocated_days': allocation['new_leaves_allocated'],
                'max_days_allowed': max_days_allowed,
                'is_exceeding': max_days_allowed and allocation['new_leaves_allocated'] > max_days_allowed,
                'from_date': allocation['from_date'],
                'to_date': allocation['to_date']
            })
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error getting employee leave allocations: {str(e)}")
        return []
