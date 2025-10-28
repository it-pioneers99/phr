import frappe
from frappe import _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

@frappe.whitelist()
def sync_employee_leave_allocation(employee, date_of_joining, is_female=0, is_muslim=0):
    """Sync leave allocation for an employee based on joining date and demographics"""
    try:
        # Calculate years of service
        years_of_service = calculate_years_of_service(date_of_joining)
        
        # Get current year
        current_year = datetime.now().year
        
        # Get appropriate leave types based on demographics
        leave_types = get_appropriate_leave_types(is_female, is_muslim)
        
        # Create/update leave allocations
        for leave_type in leave_types:
            try:
                create_or_update_leave_allocation(
                    employee, 
                    leave_type, 
                    years_of_service, 
                    current_year,
                    date_of_joining
                )
            except Exception as e:
                # Log individual leave type errors but continue with others
                frappe.log_error(f"Error creating leave allocation for {employee}, {leave_type['name']}: {str(e)[:100]}")
                continue
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error syncing leave allocation for {employee}: {str(e)[:100]}")
        return False

@frappe.whitelist()
def create_automatic_leave_allocation(employee, date_of_joining, is_female=0, is_muslim=0):
    """Create automatic leave allocation for a new employee"""
    try:
        # Calculate years of service
        years_of_service = calculate_years_of_service(date_of_joining)
        
        # Get current year
        current_year = datetime.now().year
        
        # Get appropriate leave types based on demographics
        leave_types = get_appropriate_leave_types(is_female, is_muslim)
        
        # Create leave allocations
        allocations_created = []
        for leave_type in leave_types:
            try:
                allocation = create_or_update_leave_allocation(
                    employee, 
                    leave_type, 
                    years_of_service, 
                    current_year,
                    date_of_joining
                )
                if allocation:
                    allocations_created.append(allocation)
            except Exception as e:
                # Log individual leave type errors but continue with others
                frappe.log_error(f"Error creating leave allocation for {employee}, {leave_type['name']}: {str(e)[:100]}")
                continue
        
        return allocations_created
        
    except Exception as e:
        frappe.log_error(f"Error creating automatic leave allocation for {employee}: {str(e)[:100]}")
        return False

def calculate_years_of_service(date_of_joining):
    """Calculate years of service from joining date"""
    if isinstance(date_of_joining, str):
        date_of_joining = datetime.strptime(date_of_joining, '%Y-%m-%d').date()
    
    current_date = date.today()
    years_of_service = (current_date - date_of_joining).days / 365.25
    
    return years_of_service

def get_appropriate_leave_types(is_female, is_muslim):
    """Get appropriate leave types based on employee demographics"""
    leave_types = []
    
    # Get all leave types with demographic flags
    all_leave_types = frappe.get_all('Leave Type', 
        fields=['name', 'is_female', 'is_muslim', 'is_annual_leave', 'is_sick_leave', 'max_leaves_allowed'],
        filters={'is_lwp': 0}  # Exclude loss of pay leave types
    )
    
    for lt in all_leave_types:
        # Check if this leave type matches employee demographics
        if should_allocate_leave_type(lt, is_female, is_muslim):
            leave_types.append(lt)
    
    return leave_types

def should_allocate_leave_type(leave_type, is_female, is_muslim):
    """Determine if a leave type should be allocated to an employee based on demographics"""
    # Basic leave types (Annual Leave, Sick Leave) are always allocated
    if leave_type['name'] in ['Annual Leave', 'Sick Leave', 'إجازة سنوية', 'إجازة مرضية']:
        return True
    
    # Check demographic matching
    lt_is_female = leave_type.get('is_female', 0)
    lt_is_muslim = leave_type.get('is_muslim', 0)
    
    # Rule 1: If leave type has is_muslim == TRUE, allocate to employee which have is_female == TRUE && is_muslim == TRUE
    if lt_is_muslim == 1:
        return bool(is_female == 1 and is_muslim == 1)
    
    # Rule 2: If leave type has is_female == TRUE && is_muslim == FALSE, allocate to employee which have is_female == TRUE && is_muslim == FALSE
    elif lt_is_female == 1 and lt_is_muslim == 0:
        return bool(is_female == 1 and is_muslim == 0)
    
    # Rule 3: If leave type has is_female == TRUE (regardless of is_muslim), allocate to employee which have is_female == TRUE
    elif lt_is_female == 1:
        return bool(is_female == 1)
    
    # Rule 4: Employee which have is_female == TRUE don't allocate to leave types which have is_female != TRUE
    # (This means if employee is female, they should only get leave types that are specifically for females)
    if is_female == 1 and lt_is_female != 1:
        return False
    
    # If leave type has no demographic restrictions, allocate to everyone
    if not lt_is_female and not lt_is_muslim:
        return True
    
    return False

def create_or_update_leave_allocation(employee, leave_type, years_of_service, year, date_of_joining):
    """Create or update leave allocation for an employee"""
    try:
        # Calculate allocation days based on leave type and years of service
        allocation_days = calculate_allocation_days(leave_type, years_of_service, year, date_of_joining)
        
        if allocation_days <= 0:
            return None
        
        # Check if allocation already exists
        existing_allocation = frappe.get_value('Leave Allocation', {
            'employee': employee,
            'leave_type': leave_type['name'],
            'from_date': f'{year}-01-01',
            'to_date': f'{year}-12-31'
        })
        
        if existing_allocation:
            # Update existing allocation
            allocation = frappe.get_doc('Leave Allocation', existing_allocation)
            allocation.new_leaves_allocated = allocation_days
            allocation.save()
            allocation.submit()
        else:
            # Create new allocation
            allocation = frappe.get_doc({
                'doctype': 'Leave Allocation',
                'employee': employee,
                'leave_type': leave_type['name'],
                'from_date': f'{year}-01-01',
                'to_date': f'{year}-12-31',
                'new_leaves_allocated': allocation_days,
                'carry_forward': 0
            })
            allocation.insert()
            allocation.submit()
        
        return allocation.name
        
    except Exception as e:
        # Re-raise the exception to be caught by the calling function
        raise e

def calculate_allocation_days(leave_type, years_of_service, year, date_of_joining):
    """Calculate allocation days based on leave type and years of service"""
    leave_type_name = leave_type['name']
    max_leaves_allowed = leave_type.get('max_leaves_allowed', None)
    
    if 'Annual Leave' in leave_type_name or 'إجازة سنوية' in leave_type_name:
        # Annual leave allocation based on years of service
        if years_of_service < 5:
            base_days = 21  # Less than 5 years
        else:
            base_days = 30  # 5 years or more
        
        # Calculate proportional allocation for mid-year joiners
        current_date = datetime.now()
        if current_date.year == year:
            year_start = datetime(year, 1, 1)
            year_end = datetime(year, 12, 31)
            days_in_year = (year_end - year_start).days + 1
            
            # Use the provided joining date
            if isinstance(date_of_joining, str):
                joining_date = datetime.strptime(date_of_joining, '%Y-%m-%d')
            else:
                joining_date = datetime.combine(date_of_joining, datetime.min.time())
            
            if joining_date.year == year:
                days_worked = (year_end - joining_date).days + 1
                proportional_days = (base_days * days_worked) / days_in_year
                base_days = round(proportional_days, 2)
        
        # Apply maximum days limit if set
        if max_leaves_allowed and base_days > max_leaves_allowed:
            base_days = max_leaves_allowed
            
        return base_days
    
    elif 'Sick Leave' in leave_type_name or 'إجازة مرضية' in leave_type_name:
        # Sick leave allocation - use max_leaves_allowed if set, otherwise 30 days
        if max_leaves_allowed:
            return max_leaves_allowed
        else:
            return 30
    
    else:
        # For other leave types, use predefined values but respect max_leaves_allowed
        special_leave_types = {
            'إجازة الوضع': 90,  # Maternity leave
            'إجازة مولود للموظف': 3,  # Paternity leave
            'إجازة الوفاة': 3,  # Bereavement leave
            'إجازة الزواج': 3,  # Marriage leave
            'إجازة عمره': 15,  # Umrah leave
            'اجازة حج': 30,  # Hajj leave
            'إجازة العدة للموظفة المسلمة': 130,  # Muslim female iddah
            'إجازة العدة للموظفة غير المسلمة': 90,  # Non-Muslim female iddah
            'إجازة عيد الأضحي': 3,  # Eid al-Adha
            'إجازة عيد الفطر': 3,  # Eid al-Fitr

        }
        
        base_days = special_leave_types.get(leave_type_name, 1)
        
        # Apply maximum days limit if set
        if max_leaves_allowed and base_days > max_leaves_allowed:
            base_days = max_leaves_allowed
            
        return base_days

@frappe.whitelist()
def create_new_leave_period_allocations():
    """Create new leave allocations for all employees for a new leave period"""
    try:
        current_year = datetime.now().year
        
        # Get all active employees
        employees = frappe.get_all('Employee', 
            fields=['name', 'date_of_joining', 'is_female', 'is_muslim'],
            filters={'status': 'Active'}
        )
        
        allocations_created = 0
        errors = 0
        
        for emp in employees:
            try:
                if emp['date_of_joining']:
                    # Get appropriate leave types based on demographics
                    leave_types = get_appropriate_leave_types(
                        emp.get('is_female', 0), 
                        emp.get('is_muslim', 0)
                    )
                    
                    # Create allocations for each appropriate leave type
                    for leave_type in leave_types:
                        try:
                            allocation = create_or_update_leave_allocation(
                                emp['name'], 
                                leave_type, 
                                calculate_years_of_service(emp['date_of_joining']), 
                                current_year,
                                emp['date_of_joining']
                            )
                            if allocation:
                                allocations_created += 1
                        except Exception as e:
                            frappe.log_error(f"Error creating allocation for {emp['name']}, {leave_type['name']}: {str(e)[:100]}")
                            errors += 1
                            continue
                            
            except Exception as e:
                frappe.log_error(f"Error processing employee {emp['name']}: {str(e)[:100]}")
                errors += 1
                continue
        
        return {
            'allocations_created': allocations_created,
            'errors': errors,
            'total_employees': len(employees)
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating new leave period allocations: {str(e)[:100]}")
        return False

@frappe.whitelist()
def calculate_sick_leave_deduction(employee, sick_days, monthly_salary):
    """Calculate sick leave salary deduction"""
    try:
        daily_salary = monthly_salary / 30
        deduction_amount = 0
        deduction_details = []
        
        if sick_days <= 30:
            # First 30 days - no deduction
            deduction_amount = 0
            deduction_details.append(f"Days 1-{min(sick_days, 30)}: Full pay (0% deduction)")
        elif sick_days <= 90:
            # Days 31-90 - 25% deduction
            days_25_percent = sick_days - 30
            deduction_amount = daily_salary * days_25_percent * 0.25
            deduction_details.append("Days 1-30: Full pay (0% deduction)")
            deduction_details.append(f"Days 31-{sick_days}: 25% deduction")
        else:
            # Days 90+ - 100% deduction for excess days
            days_25_percent = 60  # Days 31-90
            days_100_percent = sick_days - 90
            deduction_amount = (daily_salary * days_25_percent * 0.25) + (daily_salary * days_100_percent * 1.0)
            deduction_details.append("Days 1-30: Full pay (0% deduction)")
            deduction_details.append("Days 31-90: 25% deduction")
            deduction_details.append(f"Days 91-{sick_days}: 100% deduction")
        
        return {
            'deduction_amount': deduction_amount,
            'deduction_details': deduction_details,
            'daily_salary': daily_salary,
            'net_salary': monthly_salary - deduction_amount
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating sick leave deduction: {str(e)[:100]}")
        return None

@frappe.whitelist()
def create_salary_components():
    """Create salary components for sick leave deductions"""
    try:
        # Create sick leave deduction component
        if not frappe.db.exists('Salary Component', 'Sick Leave Deduction'):
            sick_leave_component = frappe.get_doc({
                'doctype': 'Salary Component',
                'salary_component': 'Sick Leave Deduction',
                'type': 'Deduction',
                'description': 'Deduction for sick leave taken beyond 30 days',
                'is_tax_applicable': 1,
                'variable_based_on_taxable_salary': 1
            })
            sick_leave_component.insert()
            frappe.msgprint("Sick Leave Deduction salary component created")
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error creating salary components: {str(e)[:100]}")
        return False
