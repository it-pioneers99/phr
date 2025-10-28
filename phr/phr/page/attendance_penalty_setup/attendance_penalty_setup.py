# -*- coding: utf-8 -*-
# Copyright (c) 2025, Pioneers and contributors
# For license information, please see license.txt

import frappe
from frappe import _

@frappe.whitelist()
def get_penalty_setup_status():
    """
    Get the current status of attendance penalty setup
    
    Returns:
        dict: Status information about penalty types and recent penalty records
    """
    # Check if penalty types exist
    penalty_types = frappe.get_all(
        "Penalty Type",
        filters={"penalty_type": ["in", [
            "Late Arrival 15-30 Minutes",
            "Late Arrival 30-45 Minutes",
            "Late Arrival 45-75 Minutes",
            "Late Arrival Over 75 Minutes",
            "Early Departure Before 15 Minutes"
        ]]},
        fields=["name", "penalty_type", "docstatus"],
        order_by="penalty_type"
    )
    
    # Get recent penalty records
    recent_penalties = frappe.get_all(
        "Penalty Record",
        filters={"creation": [">=", frappe.utils.add_days(frappe.utils.today(), -30)]},
        fields=["name", "employee", "violation_date", "violation_type", "penalty_amount", "penalty_status"],
        order_by="creation desc",
        limit=10
    )
    
    # Count total penalties by status
    penalty_stats = frappe.db.sql("""
        SELECT penalty_status, COUNT(*) as count, SUM(penalty_amount) as total_amount
        FROM `tabPenalty Record`
        WHERE violation_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY penalty_status
    """, as_dict=True)
    
    return {
        "penalty_types_configured": len(penalty_types) == 5,
        "penalty_types": penalty_types,
        "recent_penalties": recent_penalties,
        "penalty_stats": penalty_stats
    }


@frappe.whitelist()
def get_employee_penalty_summary(employee=None, from_date=None, to_date=None):
    """
    Get penalty summary for a specific employee or all employees
    
    Args:
        employee: Employee ID (optional)
        from_date: Start date (optional)
        to_date: End date (optional)
    
    Returns:
        list: Penalty summary by employee
    """
    filters = {}
    
    if employee:
        filters["employee"] = employee
    
    if from_date:
        filters["violation_date"] = [">=", from_date]
    
    if to_date:
        if "violation_date" in filters:
            filters["violation_date"] = ["between", [from_date, to_date]]
        else:
            filters["violation_date"] = ["<=", to_date]
    
    # Get penalty summary grouped by employee and violation type
    penalties = frappe.db.sql("""
        SELECT 
            pr.employee,
            e.employee_name,
            pr.violation_type,
            COUNT(*) as occurrence_count,
            SUM(pr.penalty_amount) as total_penalty_amount,
            MAX(pr.violation_date) as last_violation_date
        FROM `tabPenalty Record` pr
        LEFT JOIN `tabEmployee` e ON pr.employee = e.name
        WHERE pr.docstatus != 2
        {employee_filter}
        {date_filter}
        GROUP BY pr.employee, pr.violation_type
        ORDER BY pr.employee, total_penalty_amount DESC
    """.format(
        employee_filter=f"AND pr.employee = '{employee}'" if employee else "",
        date_filter=f"AND pr.violation_date >= '{from_date}' AND pr.violation_date <= '{to_date}'" if from_date and to_date else ""
    ), as_dict=True)
    
    return penalties

