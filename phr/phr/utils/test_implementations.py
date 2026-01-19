"""
Test implementations for PHR
"""
import frappe
from frappe.utils import getdate, add_days, today, date_diff
from frappe import _

@frappe.whitelist()
def test_contract_notifications():
    """Test contract notification system"""
    try:
        from phr.phr.utils.contract_management import check_contract_end_notifications
        
        result = check_contract_end_notifications()
        return {
            "status": "success",
            "message": "Contract notification test completed",
            "result": result
        }
    except Exception as e:
        frappe.log_error(f"Error testing contract notifications: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def test_testing_period_calculation(employee_id=None):
    """Test testing period calculation"""
    try:
        from phr.phr.doc_events.employee_leave_events import update_testing_period_remaining_days
        
        if not employee_id:
            # Get first employee with date_of_joining
            employees = frappe.get_all("Employee",
                filters={"date_of_joining": ["is", "set"], "status": "Active"},
                fields=["name"],
                limit=1
            )
            if not employees:
                return {"status": "error", "message": "No employees found with date_of_joining"}
            employee_id = employees[0].name
        
        emp_doc = frappe.get_doc("Employee", employee_id)
        before_days = emp_doc.remaining_testing_days or 0
        
        update_testing_period_remaining_days(emp_doc)
        frappe.db.commit()
        
        emp_doc.reload()
        after_days = emp_doc.remaining_testing_days or 0
        
        return {
            "status": "success",
            "message": "Testing period calculation test completed",
            "employee": employee_id,
            "before": before_days,
            "after": after_days,
            "testing_period_end_date": emp_doc.testing_period_end_date
        }
    except Exception as e:
        frappe.log_error(f"Error testing testing period: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def test_daily_leave_balance(employee_id=None):
    """Test daily leave balance sync"""
    try:
        from phr.phr.utils.leave_management import update_employee_leave_balances
        
        if not employee_id:
            # Get first active employee
            employees = frappe.get_all("Employee",
                filters={"status": "Active"},
                fields=["name"],
                limit=1
            )
            if not employees:
                return {"status": "error", "message": "No active employees found"}
            employee_id = employees[0].name
        
        result = update_employee_leave_balances(employee_id)
        emp_doc = frappe.get_doc("Employee", employee_id)
        
        return {
            "status": "success",
            "message": "Daily leave balance test completed",
            "employee": employee_id,
            "annual_leave_balance": emp_doc.get("annual_leave_balance", 0),
            "annual_leave_used": emp_doc.get("annual_leave_used", 0),
            "annual_leave_remaining": emp_doc.get("annual_leave_remaining", 0)
        }
    except Exception as e:
        frappe.log_error(f"Error testing leave balance: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def run_all_tests():
    """Run all tests"""
    results = {
        "contract_notifications": test_contract_notifications(),
        "testing_period": test_testing_period_calculation(),
        "leave_balance": test_daily_leave_balance()
    }
    
    all_passed = all(r.get("status") == "success" for r in results.values())
    
    return {
        "status": "success" if all_passed else "partial",
        "all_passed": all_passed,
        "results": results
    }

