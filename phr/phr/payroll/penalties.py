import frappe
from frappe import _


def _get_or_create_component(name: str = "Attendance Penalty") -> str:
    if not frappe.db.exists("Salary Component", name):
        comp = frappe.new_doc("Salary Component")
        comp.salary_component = name
        comp.type = "Deduction"
        comp.description = "Aggregated attendance penalties"
        comp.insert(ignore_permissions=True)
    return name


def _sum_penalties_for_period(employee: str, start_date, end_date) -> float:
    # Sum percentage penalties in the period; actual payroll calc may multiply by base
    rows = frappe.get_all(
        "Penalty Record",
        filters={
            "employee": employee,
            "penalty_date": ("between", [start_date, end_date]),
        },
        fields=["penalty_percentage"],
    )
    return sum(float(r.penalty_percentage or 0) for r in rows)


def apply_attendance_penalties_to_salary_slip(doc, method=None):
    """Hook: add/replace an Earnings/Deductions row for attendance penalties.
    This uses a simple aggregation of penalty percentages over the slip period.
    """
    if not getattr(doc, "start_date", None) or not getattr(doc, "end_date", None):
        return
    component = _get_or_create_component()
    total_pct = _sum_penalties_for_period(doc.employee, doc.start_date, doc.end_date)
    # Find or add deduction row
    target_row = None
    for row in (doc.deductions or []):
        if row.salary_component == component:
            target_row = row
            break
    if not target_row:
        target_row = doc.append("deductions")
        target_row.salary_component = component
    # Here we store percentage in amount; downstream custom calc may apply to base
    target_row.amount = float(total_pct)


def update_employee_flags_on_penalty(doc, method=None):
    """Hook: when a Penalty Record is created, update employee flags when needed.
    Example: if penalty_type implies withholding promotion/allowance, set a flag.
    """
    try:
        # Simple example: if percentage >= 100, mark a withholding flag
        if float(getattr(doc, "penalty_percentage", 0) or 0) >= 100:
            frappe.db.set_value("Employee", doc.employee, {
                "custom_withhold_promotion": 1,
                "custom_last_penalty_date": doc.penalty_date,
            })
    except Exception:
        frappe.log_error(frappe.get_traceback(), _("Failed to update employee flags on penalty"))


