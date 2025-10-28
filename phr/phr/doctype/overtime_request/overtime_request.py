import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta

class OvertimeRequest(Document):
    def validate(self):
        self.validate_overtime_limits()
        self.validate_approval_requirements()
    
    def validate_overtime_limits(self):
        """Validate overtime limits according to business rules"""
        if not self.hours_requested:
            return
        
        # Maximum 2 hours per day
        if self.hours_requested > 2:
            frappe.throw(_("Overtime hours cannot exceed 2 hours per day"))
        
        # Check monthly limit (5 hours per month)
        month_start = self.overtime_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_overtime = frappe.db.sql("""
            SELECT SUM(hours_requested)
            FROM `tabOvertime Request`
            WHERE employee = %s
            AND overtime_date BETWEEN %s AND %s
            AND status = 'Approved'
            AND docstatus = 1
        """, (self.employee, month_start, month_end), as_list=True)
        
        total_monthly = (monthly_overtime[0][0] or 0) + self.hours_requested
        if total_monthly > 5:
            frappe.throw(_("Total monthly overtime cannot exceed 5 hours"))
        
        # Check 10% salary cap
        employee_doc = frappe.get_doc("Employee", self.employee)
        if hasattr(employee_doc, 'salary') and employee_doc.salary:
            monthly_salary = employee_doc.salary
            max_overtime_value = monthly_salary * 0.1
            hourly_rate = monthly_salary / 30 / 8  # Assuming 8 hours per day, 30 days per month
            overtime_value = self.hours_requested * hourly_rate * 1.5  # 50% premium
            
            if overtime_value > max_overtime_value:
                frappe.throw(_("Overtime value cannot exceed 10% of monthly salary"))
    
    def validate_approval_requirements(self):
        """Validate if executive approval is required"""
        if not self.hours_requested or self.hours_requested <= 2:
            return
        
        # If more than 2 hours, require executive approval
        if self.status == "Submitted" and not self.approved_by:
            frappe.msgprint(_("Overtime exceeding 2 hours requires executive approval"))
        
        # Check if employee salary > 5000 SAR
        employee_doc = frappe.get_doc("Employee", self.employee)
        if hasattr(employee_doc, 'salary') and employee_doc.salary and employee_doc.salary > 5000:
            if self.status == "Submitted" and not self.approved_by:
                frappe.msgprint(_("Employees with salary > 5000 SAR require executive approval for overtime"))
    
    def on_submit(self):
        """Handle overtime request submission"""
        if self.status == "Approved":
            self.approval_date = frappe.utils.now()
            self.approved_by = frappe.session.user
            self.save()
    
    def calculate_overtime_allowance(self):
        """Calculate overtime allowance for salary component"""
        if not self.hours_requested or self.status != "Approved":
            return 0
        
        # Get employee's hourly rate
        employee_doc = frappe.get_doc("Employee", self.employee)
        if not hasattr(employee_doc, 'salary') or not employee_doc.salary:
            return 0
        
        monthly_salary = employee_doc.salary
        hourly_rate = monthly_salary / 30 / 8  # Assuming 8 hours per day, 30 days per month
        
        # Overtime rate is hourly rate + 50% premium
        overtime_rate = hourly_rate * 1.5
        
        return self.hours_requested * overtime_rate
