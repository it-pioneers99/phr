import frappe
from frappe.utils import getdate, date_diff, add_days
from frappe import _

@frappe.whitelist()
def create_sick_leave_salary_components():
    """
    Create salary components for sick leave deductions
    """
    try:
        # Create Sick Leave Deduction component
        if not frappe.db.exists("Salary Component", "Sick Leave Deduction"):
            salary_component = frappe.get_doc({
                "doctype": "Salary Component",
                "salary_component": "Sick Leave Deduction",
                "description": "Deduction for sick leave taken",
                "type": "Deduction",
                "is_tax_applicable": 1,
                "is_flexible_benefit": 0,
                "variable_based_on_taxable_salary": 0,
                "do_not_include_in_total": 0,
                "remove_if_zero_valued": 0,
                "disabled": 0
            })
            salary_component.insert(ignore_permissions=True)
            frappe.db.commit()
            print("Sick Leave Deduction salary component created successfully")
        
        # Create Sick Leave Deduction 25% component
        if not frappe.db.exists("Salary Component", "Sick Leave Deduction 25%"):
            salary_component = frappe.get_doc({
                "doctype": "Salary Component",
                "salary_component": "Sick Leave Deduction 25%",
                "description": "25% deduction for sick leave days 31-90",
                "type": "Deduction",
                "is_tax_applicable": 1,
                "is_flexible_benefit": 0,
                "variable_based_on_taxable_salary": 0,
                "do_not_include_in_total": 0,
                "remove_if_zero_valued": 0,
                "disabled": 0
            })
            salary_component.insert(ignore_permissions=True)
            frappe.db.commit()
            print("Sick Leave Deduction 25% salary component created successfully")
        
        # Create Sick Leave Deduction 100% component
        if not frappe.db.exists("Salary Component", "Sick Leave Deduction 100%"):
            salary_component = frappe.get_doc({
                "doctype": "Salary Component",
                "salary_component": "Sick Leave Deduction 100%",
                "description": "100% deduction for sick leave days 90+",
                "type": "Deduction",
                "is_tax_applicable": 1,
                "is_flexible_benefit": 0,
                "variable_based_on_taxable_salary": 0,
                "do_not_include_in_total": 0,
                "remove_if_zero_valued": 0,
                "disabled": 0
            })
            salary_component.insert(ignore_permissions=True)
            frappe.db.commit()
            print("Sick Leave Deduction 100% salary component created successfully")
        
        return {"status": "success", "message": "Salary components created successfully"}
    
    except Exception as e:
        frappe.log_error(f"Error creating salary components: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def calculate_sick_leave_deduction(employee_id, start_date, end_date):
    """
    Calculate sick leave deduction for a specific period
    """
    try:
        # Get sick leave applications for the period
        sick_leaves = frappe.get_all("Leave Application",
            filters={
                "employee": employee_id,
                "leave_type": ["in", get_sick_leave_types()],
                "from_date": [">=", start_date],
                "to_date": ["<=", end_date],
                "status": "Approved"
            },
            fields=["from_date", "to_date", "total_leave_days"]
        )
        
        total_sick_days = sum(leave.total_leave_days for leave in sick_leaves)
        
        if total_sick_days == 0:
            return {
                "status": "success",
                "message": "No sick leave taken in the specified period",
                "data": {
                    "sick_days_taken": 0,
                    "deduction_25_percent": 0,
                    "deduction_100_percent": 0,
                    "total_deduction": 0
                }
            }
        
        # Calculate deductions based on sick leave rules
        # Days 1-30: Full pay (0% deduction)
        # Days 31-90: 75% pay (25% deduction)
        # Days 90+: No pay (100% deduction)
        
        days_1_30 = min(total_sick_days, 30)
        days_31_90 = min(max(total_sick_days - 30, 0), 60)
        days_90_plus = max(total_sick_days - 90, 0)
        
        # Calculate deductions (assuming daily salary rate)
        daily_salary_rate = get_daily_salary_rate(employee_id)
        
        deduction_25_percent = days_31_90 * daily_salary_rate * 0.25
        deduction_100_percent = days_90_plus * daily_salary_rate
        total_deduction = deduction_25_percent + deduction_100_percent
        
        return {
            "status": "success",
            "message": f"Sick leave deduction calculated for {total_sick_days} days",
            "data": {
                "sick_days_taken": total_sick_days,
                "days_1_30": days_1_30,
                "days_31_90": days_31_90,
                "days_90_plus": days_90_plus,
                "deduction_25_percent": deduction_25_percent,
                "deduction_100_percent": deduction_100_percent,
                "total_deduction": total_deduction,
                "daily_salary_rate": daily_salary_rate
            }
        }
    
    except Exception as e:
        frappe.log_error(f"Error calculating sick leave deduction: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_sick_leave_types():
    """Get all sick leave types"""
    return frappe.get_all("Leave Type",
        filters={"is_sick_leave": 1},
        pluck="name"
    )

def apply_sick_leave_deductions(salary_slip):
    """
    Apply sick leave deductions to salary slip
    """
    try:
        employee_id = salary_slip.employee
        start_date = salary_slip.start_date
        end_date = salary_slip.end_date
        
        # Calculate sick leave deductions
        result = calculate_sick_leave_deduction(employee_id, start_date, end_date)
        
        if result["status"] == "success" and result["data"]["total_deduction"] > 0:
            data = result["data"]
            
            # Add 25% deduction component
            if data["deduction_25_percent"] > 0:
                salary_slip.append("deductions", {
                    "salary_component": "Sick Leave Deduction 25%",
                    "amount": data["deduction_25_percent"],
                    "description": f"Sick leave deduction for {data['days_31_90']} days (25%)"
                })
            
            # Add 100% deduction component
            if data["deduction_100_percent"] > 0:
                salary_slip.append("deductions", {
                    "salary_component": "Sick Leave Deduction 100%",
                    "amount": data["deduction_100_percent"],
                    "description": f"Sick leave deduction for {data['days_90_plus']} days (100%)"
                })
        
        return result
    
    except Exception as e:
        frappe.log_error(f"Error applying sick leave deductions: {str(e)}")
        return {"status": "error", "message": str(e)}

def get_daily_salary_rate(employee_id):
    """
    Get daily salary rate for employee
    """
    try:
        # Get employee's basic salary
        employee = frappe.get_doc("Employee", employee_id)
        
        # Get salary structure assignment
        salary_structure = frappe.get_all("Salary Structure Assignment",
            filters={"employee": employee_id, "docstatus": 1},
            fields=["salary_structure"],
            order_by="from_date desc",
            limit=1
        )
        
        if salary_structure:
            # Get salary structure details
            salary_structure_doc = frappe.get_doc("Salary Structure", salary_structure[0].salary_structure)
            
            # Find basic salary component
            basic_salary = 0
            for component in salary_structure_doc.earnings:
                if component.salary_component == "Basic":
                    basic_salary = component.amount
                    break
            
            if basic_salary > 0:
                # Calculate daily rate (assuming 30 days per month)
                return basic_salary / 30
            else:
                # Fallback to a default daily rate
                return 100  # Default daily rate
        else:
            # Fallback to a default daily rate
            return 100  # Default daily rate
    
    except Exception as e:
        frappe.log_error(f"Error getting daily salary rate: {str(e)}")
        return 100  # Default daily rate

@frappe.whitelist()
def create_salary_components():
    """
    Create all salary components for PHR system
    """
    try:
        result = create_sick_leave_salary_components()
        return result
    except Exception as e:
        frappe.log_error(f"Error creating salary components: {str(e)}")
        return {"status": "error", "message": str(e)}
