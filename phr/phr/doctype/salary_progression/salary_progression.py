import frappe
from frappe.model.document import Document
from frappe import _

class SalaryProgression(Document):
    def validate(self):
        self.validate_date_range()
        self.validate_salary_amount()
    
    def validate_date_range(self):
        """Validate that from_date is before to_date"""
        if self.from_date and self.to_date:
            if self.from_date >= self.to_date:
                frappe.throw(_("From Date must be before To Date"))
    
    def validate_salary_amount(self):
        """Validate salary amount is positive"""
        if self.salary_amount and self.salary_amount <= 0:
            frappe.throw(_("Salary amount must be greater than zero"))
    
    def on_submit(self):
        """Update employee salary when salary progression is submitted"""
        if self.employee and self.salary_amount:
            self.update_employee_salary()
    
    def update_employee_salary(self):
        """Update employee's current salary"""
        employee_doc = frappe.get_doc("Employee", self.employee)
        
        # Update salary field if it exists
        if hasattr(employee_doc, 'salary'):
            employee_doc.salary = self.salary_amount
            employee_doc.save()
            
            frappe.msgprint(_("Employee salary updated to {0}").format(self.salary_amount))
