import frappe
from frappe import _
from phr.phr.utils.leave_management import get_employee_leave_summary, update_employee_leave_balances

@frappe.whitelist()
def get_leave_dashboard_data(employee=None):
    """Get comprehensive leave dashboard data"""
    try:
        if not employee:
            employee = frappe.session.user
        
        # Get employee leave summary
        summary = get_employee_leave_summary(employee)
        
        if not summary:
            return {"error": "Unable to fetch leave summary"}
        
        # Get additional dashboard data
        dashboard_data = {
            "employee_summary": summary,
            "leave_statistics": get_leave_statistics(employee),
            "upcoming_contracts": get_upcoming_contracts(),
            "recent_leave_applications": get_recent_leave_applications(employee),
            "leave_balance_chart": get_leave_balance_chart_data(employee)
        }
        
        return dashboard_data
        
    except Exception as e:
        frappe.log_error(f"Error getting leave dashboard data: {str(e)}", "PHR Leave Dashboard")
        return {"error": str(e)}

def get_leave_statistics(employee):
    """Get leave statistics for employee"""
    try:
        current_year = frappe.utils.getdate().year
        leave_period_start = frappe.utils.getdate(f"{current_year}-01-01")
        leave_period_end = frappe.utils.getdate(f"{current_year}-12-31")
        
        # Get total leave applications this year
        total_applications = frappe.db.count(
            "Leave Application",
            {
                "employee": employee,
                "from_date": [">=", leave_period_start],
                "to_date": ["<=", leave_period_end]
            }
        )
        
        # Get approved applications
        approved_applications = frappe.db.count(
            "Leave Application",
            {
                "employee": employee,
                "status": "Approved",
                "from_date": [">=", leave_period_start],
                "to_date": ["<=", leave_period_end]
            }
        )
        
        # Get pending applications
        pending_applications = frappe.db.count(
            "Leave Application",
            {
                "employee": employee,
                "status": "Open",
                "from_date": [">=", leave_period_start],
                "to_date": ["<=", leave_period_end]
            }
        )
        
        return {
            "total_applications": total_applications,
            "approved_applications": approved_applications,
            "pending_applications": pending_applications,
            "approval_rate": round((approved_applications / total_applications * 100) if total_applications > 0 else 0, 2)
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting leave statistics: {str(e)}", "PHR Leave Dashboard")
        return {}

def get_upcoming_contracts():
    """Get upcoming contract expirations"""
    try:
        today = frappe.utils.getdate()
        next_90_days = frappe.utils.add_days(today, 90)
        
        contracts = frappe.get_list(
            "Employee",
            filters={
                "contract_end_date": ["between", (today, next_90_days)],
                "status": "Active"
            },
            fields=["name", "employee_name", "contract_end_date", "remaining_contract_days"],
            order_by="contract_end_date"
        )
        
        return contracts
        
    except Exception as e:
        frappe.log_error(f"Error getting upcoming contracts: {str(e)}", "PHR Leave Dashboard")
        return []

def get_recent_leave_applications(employee, limit=5):
    """Get recent leave applications for employee"""
    try:
        applications = frappe.get_list(
            "Leave Application",
            filters={"employee": employee},
            fields=[
                "name", "leave_type", "from_date", "to_date", 
                "total_leave_days", "status", "reason", "creation"
            ],
            order_by="creation desc",
            limit=limit
        )
        
        return applications
        
    except Exception as e:
        frappe.log_error(f"Error getting recent leave applications: {str(e)}", "PHR Leave Dashboard")
        return []

def get_leave_balance_chart_data(employee):
    """Get data for leave balance chart"""
    try:
        summary = get_employee_leave_summary(employee)
        
        if not summary or not summary.get("allocations"):
            return {"labels": [], "datasets": []}
        
        # Prepare chart data
        labels = []
        allocated_data = []
        used_data = []
        remaining_data = []
        
        for allocation in summary["allocations"]:
            labels.append(allocation["leave_type_name"])
            allocated_data.append(allocation["allocated"])
            used_data.append(allocation["used"])
            remaining_data.append(allocation["remaining"])
        
        chart_data = {
            "labels": labels,
            "datasets": [
                {
                    "label": "Allocated",
                    "data": allocated_data,
                    "backgroundColor": "#28a745"
                },
                {
                    "label": "Used",
                    "data": used_data,
                    "backgroundColor": "#dc3545"
                },
                {
                    "label": "Remaining",
                    "data": remaining_data,
                    "backgroundColor": "#17a2b8"
                }
            ]
        }
        
        return chart_data
        
    except Exception as e:
        frappe.log_error(f"Error getting leave balance chart data: {str(e)}", "PHR Leave Dashboard")
        return {"labels": [], "datasets": []}

@frappe.whitelist()
def refresh_employee_leave_balances(employee):
    """Refresh leave balances for specific employee"""
    try:
        success = update_employee_leave_balances(employee)
        
        if success:
            frappe.msgprint(f"Leave balances refreshed for {employee}")
            return {"success": True, "message": "Leave balances refreshed successfully"}
        else:
            return {"success": False, "message": "Failed to refresh leave balances"}
            
    except Exception as e:
        frappe.log_error(f"Error refreshing leave balances for {employee}: {str(e)}", "PHR Leave Dashboard")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def get_leave_type_compatibility(employee):
    """Get compatible leave types for employee"""
    try:
        employee_doc = frappe.get_doc("Employee", employee)
        
        # Get all leave types
        leave_types = frappe.get_list(
            "Leave Type",
            fields=["name", "leave_type_name", "is_annual_leave", "is_sick_leave", "is_muslim", "is_female"]
        )
        
        compatible_types = []
        for leave_type in leave_types:
            # Check compatibility
            is_compatible = True
            
            if leave_type.is_muslim and not employee_doc.is_muslim:
                is_compatible = False
            
            if leave_type.is_female and not employee_doc.is_female:
                is_compatible = False
            
            if is_compatible:
                compatible_types.append(leave_type)
        
        return compatible_types
        
    except Exception as e:
        frappe.log_error(f"Error getting leave type compatibility for {employee}: {str(e)}", "PHR Leave Dashboard")
        return []
