import frappe
from frappe.utils import getdate, date_diff, add_days, get_first_day, get_last_day, nowdate
from datetime import datetime, timedelta

@frappe.whitelist()
def create_automatic_leave_allocation(employee_id):
    """
    Create automatic leave allocation for employee based on joining date and years of service
    """
    try:
        employee = frappe.get_doc("Employee", employee_id)
        if not employee.date_of_joining:
            return {"status": "error", "message": "Employee joining date is required"}
        
        # Calculate years of service
        joining_date = getdate(employee.date_of_joining)
        current_date = getdate()
        years_of_service = date_diff(current_date, joining_date) / 365.25
        
        # Get annual leave types
        annual_leave_types = frappe.get_all(
            "Leave Type",
            filters={"is_annual_leave": 1},
            fields=["name"]
        )
        
        if not annual_leave_types:
            return {"status": "error", "message": "No annual leave types found"}
        
        # Initialize allocations list
        allocations_created = []
        
        # Determine leave days based on years of service and additional annual leave flag
        is_additional_annual_leave = frappe.db.get_value("Employee", employee_id, "is_additional_annual_leave") or 0
        
        if is_additional_annual_leave:
            # If additional annual leave is checked, always give 30 days
            annual_leave_days = 30
        else:
            # Standard logic based on years of service
            annual_leave_days = 30 if years_of_service >= 5 else 21
        
        # Process each annual leave type
        for leave_type in annual_leave_types:
            # Check if leave type has max_leaves_allowed limit
            leave_type_doc = frappe.get_doc("Leave Type", leave_type.name)
            max_allowed = leave_type_doc.get("max_leaves_allowed", 0)
            final_leave_days = annual_leave_days
            if max_allowed and final_leave_days > max_allowed:
                final_leave_days = max_allowed
        
            
            # Calculate proportional allocation if joined mid-year
            current_year = current_date.year
            year_start = getdate(f"{current_year}-01-01")
            year_end = getdate(f"{current_year}-12-31")
            
            # If employee joined this year, calculate proportional allocation
            if joining_date.year == current_year:
                days_in_year = date_diff(year_end, year_start) + 1
                days_worked = date_diff(year_end, joining_date) + 1
                proportional_days = (final_leave_days * days_worked) / days_in_year
                final_leave_days = round(proportional_days, 2)
            
            # Create leave allocation for this annual leave type
            annual_allocation = create_leave_allocation_record(
                employee_id, leave_type.name, final_leave_days, current_year
            )
            if annual_allocation:
                allocations_created.append(f"{leave_type.name}: {final_leave_days} days")
        
        # Get or create sick leave type
        sick_leave_type = get_or_create_leave_type("Sick Leave", is_sick=True)
        
        # Sick Leave Allocation (usually unlimited or high number)
        sick_allocation = create_leave_allocation_record(
            employee_id, sick_leave_type, 365, current_year  # 365 days for sick leave
        )
        if sick_allocation:
            allocations_created.append(f"Sick Leave: 365 days")
        
        return {
            "status": "success", 
            "message": f"Leave allocations created: {', '.join(allocations_created)}",
            "annual_leave_days": annual_leave_days,
            "years_of_service": round(years_of_service, 2)
        }
        
    except Exception as e:
        frappe.log_error(f"Error in create_automatic_leave_allocation: {str(e)}")
        return {"status": "error", "message": str(e)}

def get_or_create_leave_type(leave_type_name, is_annual=False, is_sick=False):
    """
    Get existing leave type or create new one
    """
    try:
        leave_type = frappe.get_doc("Leave Type", leave_type_name)
    except frappe.DoesNotExistError:
        # Create new leave type
        leave_type = frappe.get_doc({
            "doctype": "Leave Type",
            "leave_type_name": leave_type_name,
            "max_leaves_allowed": 365 if is_sick else 30,
            "is_annual_leave": 1 if is_annual else 0,
            "is_sick_leave": 1 if is_sick else 0,
            "is_paid_leave": 1,
            "include_holiday": 0,
            "is_compensatory": 0
        })
        leave_type.insert()
        frappe.db.commit()
    
    return leave_type.name

def create_leave_allocation_record(employee_id, leave_type, new_leaves_allocated, year):
    """
    Create or update leave allocation record
    """
    try:
        # Check if allocation already exists for this year
        existing_allocation = frappe.get_all("Leave Allocation",
            filters={
                "employee": employee_id,
                "leave_type": leave_type,
                "from_date": f"{year}-01-01",
                "to_date": f"{year}-12-31"
            },
            limit=1
        )
        
        if existing_allocation:
            # Update existing allocation
            allocation_doc = frappe.get_doc("Leave Allocation", existing_allocation[0].name)
            allocation_doc.new_leaves_allocated = new_leaves_allocated
            allocation_doc.save()
            return allocation_doc.name
        else:
            # Create new allocation
            allocation_doc = frappe.get_doc({
                "doctype": "Leave Allocation",
                "employee": employee_id,
                "leave_type": leave_type,
                "from_date": f"{year}-01-01",
                "to_date": f"{year}-12-31",
                "new_leaves_allocated": new_leaves_allocated,
                "carry_forward": 0
            })
            allocation_doc.insert()
            allocation_doc.submit()
            frappe.db.commit()
            return allocation_doc.name
            
    except Exception as e:
        frappe.log_error(f"Error creating leave allocation: {str(e)}")
        return None

@frappe.whitelist()
def calculate_sick_leave_salary_deduction(employee_id, sick_days_taken):
    """
    Calculate salary deduction for sick leave based on company policy:
    - First 30 days: Full pay (0% deduction)
    - Days 31-90: 25% deduction (75% pay)
    - Days 90+: 100% deduction (0% pay)
    """
    try:
        employee = frappe.get_doc("Employee", employee_id)
        sick_days = float(sick_days_taken)
        
        # Get employee's basic salary (you may need to adjust this based on your salary structure)
        salary_structure = frappe.get_all("Salary Structure Assignment",
            filters={"employee": employee_id, "docstatus": 1},
            fields=["base"],
            order_by="from_date desc",
            limit=1
        )
        
        if not salary_structure:
            return {"status": "error", "message": "No salary structure found for employee"}
        
        monthly_salary = salary_structure[0].base
        daily_salary = monthly_salary / 30  # Assuming 30 days per month
        
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
            "status": "success",
            "deduction_amount": round(deduction_amount, 2),
            "daily_salary": round(daily_salary, 2),
            "monthly_salary": monthly_salary,
            "sick_days": sick_days,
            "deduction_details": deduction_details
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating sick leave deduction: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_employee_sick_leave_summary(employee_id, year=None):
    """
    Get summary of sick leave taken by employee in a given year
    """
    try:
        if not year:
            year = datetime.now().year
        
        # Get all sick leave applications for the year
        sick_leave_applications = frappe.get_all("Leave Application",
            filters={
                "employee": employee_id,
                "leave_type": ["in", get_sick_leave_types()],
                "from_date": [">=", f"{year}-01-01"],
                "to_date": ["<=", f"{year}-12-31"],
                "status": "Approved"
            },
            fields=["name", "from_date", "to_date", "total_leave_days", "leave_type"]
        )
        
        total_sick_days = sum([app.total_leave_days for app in sick_leave_applications])
        
        # Calculate deduction
        deduction_info = calculate_sick_leave_salary_deduction(employee_id, total_sick_days)
        
        return {
            "status": "success",
            "employee_id": employee_id,
            "year": year,
            "total_sick_days": total_sick_days,
            "applications": sick_leave_applications,
            "deduction_info": deduction_info
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting sick leave summary: {str(e)}")
        return {"status": "error", "message": str(e)}

def get_sick_leave_types():
    """
    Get all leave types marked as sick leave
    """
    return frappe.get_all("Leave Type",
        filters={"is_sick_leave": 1},
        pluck="name"
    )

@frappe.whitelist()
def create_custom_fields():
    """Create all required custom fields for Employee and Leave Type DocTypes"""
    
    # Employee custom fields
    employee_fields = [
        {
            "dt": "Employee", 
            "fieldname": "online_present_days_used",
            "label": "Online Present Days Used",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "date_of_joining"
        }
    ]
    
    # Leave Type custom field
    leave_type_fields = [
        {
            "dt": "Leave Type",
            "fieldname": "is_online_present",
            "label": "Is Online Present", 
            "fieldtype": "Check",
            "insert_after": "is_sick_leave"
        }
    ]
    
    all_fields = employee_fields + leave_type_fields
    
    for field_data in all_fields:
        try:
            if not frappe.db.exists("Custom Field", {"dt": field_data["dt"], "fieldname": field_data["fieldname"]}):
                custom_field = frappe.new_doc("Custom Field")
                custom_field.update(field_data)
                custom_field.insert()
                print(f"✅ Added {field_data['fieldname']} to {field_data['dt']}")
            else:
                print(f"ℹ️ {field_data['fieldname']} already exists in {field_data['dt']}")
        except Exception as e:
            print(f"❌ Error adding {field_data['fieldname']}: {str(e)}")
    
    # Make date_of_joining required
    try:
        employee_dt = frappe.get_doc("DocType", "Employee")
        for field in employee_dt.fields:
            if field.fieldname == "date_of_joining":
                field.reqd = 1
                field.save()
                print("✅ Made date_of_joining field required in Employee")
                break
    except Exception as e:
        print(f"❌ Error making date_of_joining required: {str(e)}")
    
    # Create Online Present leave type
    try:
        if not frappe.db.exists("Leave Type", "Online Present"):
            leave_type = frappe.new_doc("Leave Type")
            leave_type.leave_type_name = "Online Present"
            leave_type.is_online_present = 1
            leave_type.max_leaves_allowed = 12
            leave_type.is_annual_leave = 0
            leave_type.is_sick_leave = 0
            leave_type.is_paid_leave = 1
            leave_type.include_holiday = 0
            leave_type.is_compensatory = 0
            leave_type.allow_negative = 0
            leave_type.allow_encashment = 0
            leave_type.encashment_threshold_days = 0
            leave_type.insert()
            print("✅ Created Online Present leave type")
        else:
            print("ℹ️ Online Present leave type already exists")
    except Exception as e:
        print(f"❌ Error creating Online Present leave type: {str(e)}")
    
    frappe.db.commit()
    return "✅ All custom fields and leave type created successfully!"

@frappe.whitelist()
def test_annual_leave_functionality():
    """Test the annual leave functionality"""
    
    print("🧪 Testing Annual Leave Functionality...")
    
    # Get an existing employee
    employees = frappe.get_all("Employee", 
        filters={"status": "Active"}, 
        fields=["name", "employee_name"],
        limit=1
    )
    
    if not employees:
        print("❌ No active employees found for testing")
        return "No active employees found"
    
    employee = employees[0]
    print(f"📋 Testing with Employee: {employee.employee_name} ({employee.name})")
    
    # Test: Calculate annual leave balance
    print(f"\n1️⃣ Testing Annual Leave Calculation")
    result = calculate_annual_leave_balance(employee.name)
    if result.get("error"):
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Annual Leave: {result['total_allocation']} days (Rate: {result['days_per_month']} days/month)")
    
    print("\n🎉 Test completed!")
    return "Test completed successfully"

@frappe.whitelist()
def calculate_annual_leave_balance(employee):
    """
    Calculate comprehensive annual leave balance for an employee
    
    Args:
        employee: Employee ID
        
    Returns:
        dict: Complete annual leave balance information
    """
    try:
        employee_doc = frappe.get_doc("Employee", employee)
        current_date = getdate(nowdate())
        current_year = current_date.year
        
        # Calculate years of service
        if not employee_doc.date_of_joining:
            return {"error": "Employee joining date is required"}
            
        joining_date = getdate(employee_doc.date_of_joining)
        years_of_service = date_diff(current_date, joining_date) / 365.25
        
        # Get is_additional_annual_leave value from database (custom field)
        is_additional_annual_leave = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
        
        # Determine allocation based on years of service and additional annual leave flag
        if is_additional_annual_leave:
            # If additional annual leave is checked, always give 2.5 days per month (30 days/year)
            days_per_month = 2.5
            allocation_reason = f"Additional Annual Leave ({years_of_service:.1f} years, 2.5 days/month)"
        elif years_of_service < 5:
            # Less than 5 years = 1.75 days per month
            days_per_month = 1.75
            allocation_reason = f"Standard Rate ({years_of_service:.1f} years, 1.75 days/month)"
        else:
            # 5+ years = 2.5 days per month
            days_per_month = 2.5
            allocation_reason = f"5+ Years Service ({years_of_service:.1f} years, 2.5 days/month)"
        
        # Calculate total allocation for the year (12 months)
        total_allocation = days_per_month * 12
        base_allocation = total_allocation
        additional_days = 0
        
        # Get current year allocation
        allocation = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employee,
                "leave_type": ["in", frappe.get_all("Leave Type", filters={"is_annual_leave": 1}, pluck="name")],
                "from_date": [">=", f"{current_year}-01-01"],
                "to_date": ["<=", f"{current_year}-12-31"],
                "docstatus": 1
            },
            fields=["name", "new_leaves_allocated", "from_date", "to_date"],
            limit=1
        )
        
        if allocation:
            allocated_days = allocation[0].new_leaves_allocated or 0
            allocation_start = allocation[0].from_date
            allocation_end = allocation[0].to_date
        else:
            allocated_days = total_allocation
            allocation_start = f"{current_year}-01-01"
            allocation_end = f"{current_year}-12-31"
        
        # Calculate used days
        used_days = frappe.db.sql("""
            SELECT COALESCE(SUM(total_leave_days), 0) as used_days
            FROM `tabLeave Application`
            WHERE employee = %s
            AND leave_type IN (SELECT name FROM `tabLeave Type` WHERE is_annual_leave = 1)
            AND from_date >= %s
            AND to_date <= %s
            AND docstatus = 1
            AND status = 'Approved'
        """, (employee, allocation_start, allocation_end), as_dict=True)
        
        days_used = used_days[0].used_days if used_days else 0
        days_remaining = allocated_days - days_used
        usage_percentage = round((days_used / allocated_days * 100), 1) if allocated_days > 0 else 0
        
        # Calculate days until expiry
        allocation_end_date = getdate(allocation_end)
        days_until_expiry = date_diff(allocation_end_date, current_date)
        
        return {
            "employee_name": employee_doc.employee_name,
            "date_of_joining": employee_doc.date_of_joining,
            "years_of_service": round(years_of_service, 1),
            "is_additional_annual_leave": bool(is_additional_annual_leave),
            "base_allocation": base_allocation,
            "additional_days": additional_days,
            "total_allocation": total_allocation,
            "allocated_days": allocated_days,
            "allocation_reason": allocation_reason,
            "days_per_month": days_per_month,
            "days_used": days_used,
            "days_remaining": days_remaining,
            "usage_percentage": usage_percentage,
            "current_year": current_year,
            "allocation_start": allocation_start,
            "allocation_end": allocation_end,
            "days_until_expiry": days_until_expiry
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating annual leave balance for {employee}: {str(e)}", "Annual Leave Balance")
        return {"error": str(e)}

@frappe.whitelist()
def get_annual_leave_dashboard_data(employee):
    """
    Get simplified annual leave data for dashboard display
    
    Args:
        employee: Employee ID
        
    Returns:
        dict: Dashboard data for annual leave
    """
    try:
        balance_data = calculate_annual_leave_balance(employee)
        
        if "error" in balance_data:
            return balance_data
            
        return {
            "total_allocation": balance_data.get("allocated_days", 0),
            "days_remaining": balance_data.get("days_remaining", 0),
            "usage_percentage": balance_data.get("usage_percentage", 0),
            "days_until_expiry": balance_data.get("days_until_expiry", 0)
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting dashboard data for {employee}: {str(e)}", "Annual Leave Dashboard")
        return {"error": str(e)}

