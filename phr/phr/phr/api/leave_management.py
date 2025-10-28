import frappe
from frappe.utils import getdate, today, add_days
from phr.phr.utils.leave_calculation_engine import LeaveCalculationEngine, get_enhanced_leave_analysis, check_employee_eligibility
from phr.phr.utils.contract_management import check_contract_end_notifications, get_contract_summary
from phr.phr.utils.salary_components import create_salary_components

@frappe.whitelist()
def get_employee_leave_summary(employee_id):
    """
    Get comprehensive leave summary for an employee
    """
    try:
        engine = LeaveCalculationEngine(employee_id)
        
        # Get basic info
        employee = frappe.get_doc("Employee", employee_id)
        
        # Calculate balances
        balances = engine.calculate_leave_balances_by_type()
        
        # Find annual leave balance (look for any leave type that is annual leave)
        annual_balance = {}
        sick_balance = {}
        
        for leave_type, balance in balances.items():
            if balance.get('is_annual_leave'):
                annual_balance = balance
                break
        
        for leave_type, balance in balances.items():
            if balance.get('is_sick_leave'):
                sick_balance = balance
                break
        
        # Get leave allocations
        allocations = frappe.get_all("Leave Allocation",
            filters={
                "employee": employee_id,
                "docstatus": 1
            },
            fields=["leave_type", "total_leaves_allocated", "unused_leaves", "from_date", "to_date"]
        )
        
        # Get leave applications
        applications = frappe.get_all("Leave Application",
            filters={
                "employee": employee_id,
                "docstatus": 1
            },
            fields=["leave_type", "from_date", "to_date", "total_leave_days", "status"]
        )
        
        # Get additional annual leave flag
        is_additional_annual_leave = frappe.db.get_value("Employee", employee_id, "is_additional_annual_leave") or 0
        
        return {
            "employee_info": {
                "name": employee.name,
                "employee_name": employee.employee_name,
                "date_of_joining": employee.date_of_joining,
                "contract_end_date": employee.contract_end_date,
                "working_years": engine.working_years,
                "working_months": engine.working_months,
                "is_eligible_30_days": engine.is_eligible_for_30_days_annual_leave(),
                "is_additional_annual_leave": bool(is_additional_annual_leave),
                "is_muslim": employee.is_muslim,
                "is_female": employee.is_female
            },
            "annual_leave": {
                **annual_balance,
                "days_per_month": engine.get_annual_leave_days_per_month(),
                "is_additional_annual_leave": bool(is_additional_annual_leave),
                "calculation_reason": f"{'Additional Annual Leave' if is_additional_annual_leave else ('5+ Years Service' if engine.is_eligible_for_30_days_annual_leave() else 'Standard Rate')} ({engine.working_years:.1f} years, {engine.get_annual_leave_days_per_month()} days/month)"
            },
            "sick_leave": sick_balance,
            "allocations": allocations,
            "applications": applications
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting employee leave summary: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_enhanced_leave_analysis_api(employee_id, leave_type=None, start_date=None, end_date=None):
    """
    Get enhanced leave analysis based on leave type, allocation, and period
    """
    try:
        return get_enhanced_leave_analysis(employee_id, leave_type, start_date, end_date)
    except Exception as e:
        frappe.log_error(f"Error getting enhanced leave analysis: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def check_employee_eligibility_api(employee_id):
    """
    Check employee eligibility for 30 days annual leave based on 60-month threshold
    """
    try:
        return check_employee_eligibility(employee_id)
    except Exception as e:
        frappe.log_error(f"Error checking employee eligibility: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def create_employee_leave_allocations(employee_id):
    """
    Create automatic leave allocations for an employee based on 60-month threshold
    """
    try:
        engine = LeaveCalculationEngine(employee_id)
        allocations = engine.create_automatic_allocations()
        
        # Update employee balances
        engine.update_employee_leave_balances()
        
        return {
            "status": "success",
            "message": f"Created {len(allocations)} leave allocations based on {engine.working_months} months of service",
            "allocations": allocations,
            "working_months": engine.working_months,
            "is_eligible_30_days": engine.is_eligible_for_30_days_annual_leave()
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating leave allocations: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def sync_all_employee_leave_balances():
    """
    Sync leave balances for all active employees
    """
    try:
        employees = frappe.get_all("Employee",
            filters={"status": "Active"},
            fields=["name"]
        )
        
        synced_count = 0
        errors = []
        
        for employee in employees:
            try:
                engine = LeaveCalculationEngine(employee.name)
                engine.update_employee_leave_balances()
                synced_count += 1
            except Exception as e:
                errors.append(f"Employee {employee.name}: {str(e)}")
        
        return {
            "status": "success",
            "message": f"Synced leave balances for {synced_count} employees",
            "synced_count": synced_count,
            "errors": errors
        }
        
    except Exception as e:
        frappe.log_error(f"Error syncing leave balances: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_leave_analysis_by_period(employee_id, start_date, end_date, leave_type=None):
    """
    Get detailed leave analysis for a specific period
    """
    try:
        engine = LeaveCalculationEngine(employee_id)
        analysis = engine.get_leave_analysis_by_type_and_period(leave_type, start_date, end_date)
        
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting leave analysis by period: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_leave_analysis_by_type(employee_id, leave_type):
    """
    Get leave analysis for a specific leave type
    """
    try:
        engine = LeaveCalculationEngine(employee_id)
        analysis = engine.get_leave_analysis_by_type_and_period(leave_type)
        
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting leave analysis by type: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def check_contract_notifications():
    """
    Check and send contract end notifications
    """
    try:
        result = check_contract_end_notifications()
        return result
    except Exception as e:
        frappe.log_error(f"Error checking contract notifications: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_contract_summary_data():
    """
    Get contract summary data
    """
    try:
        return get_contract_summary()
    except Exception as e:
        frappe.log_error(f"Error getting contract summary: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def setup_phr_system():
    """
    Setup PHR system with all required components
    """
    try:
        # Create salary components
        salary_result = create_salary_components()
        
        # Create default leave types
        leave_types = [
            {"name": "Annual Leave", "is_annual": True, "is_sick": False},
            {"name": "Sick Leave", "is_annual": False, "is_sick": True},
            {"name": "Female Leave", "is_annual": False, "is_sick": False, "is_female": True},
            {"name": "Muslim Leave", "is_annual": False, "is_sick": False, "is_muslim": True}
        ]
        
        created_types = []
        for lt in leave_types:
            if not frappe.db.exists("Leave Type", lt["name"]):
                leave_type = frappe.get_doc({
                    "doctype": "Leave Type",
                    "leave_type_name": lt["name"],
                    "max_leaves_allowed": 30,
                    "is_annual_leave": 1 if lt.get("is_annual") else 0,
                    "is_sick_leave": 1 if lt.get("is_sick") else 0,
                    "is_female": 1 if lt.get("is_female") else 0,
                    "is_muslim": 1 if lt.get("is_muslim") else 0,
                    "is_paid_leave": 1,
                    "include_holiday": 0,
                    "is_compensatory": 0
                })
                leave_type.insert()
                created_types.append(lt["name"])
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "PHR system setup completed successfully",
            "salary_components": salary_result,
            "leave_types_created": created_types
        }
        
    except Exception as e:
        frappe.log_error(f"Error setting up PHR system: {str(e)}")
        return {"status": "error", "message": str(e)}
