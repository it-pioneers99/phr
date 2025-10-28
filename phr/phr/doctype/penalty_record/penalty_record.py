import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta

class PenaltyRecord(Document):
    def validate(self):
        self.calculate_penalty_level()
        self.calculate_total_penalty_value()
    
    def calculate_penalty_level(self):
        """Calculate penalty level based on previous violations within 180 days"""
        if not self.employee or not self.violation_type or not self.violation_date:
            return
        
        # Get penalty type to access penalty levels
        penalty_type_doc = frappe.get_doc("Penalty Type", self.violation_type)
        if not penalty_type_doc.penalty_levels:
            return
        
        # Ensure violation_date is a date object
        from frappe.utils import getdate
        violation_date = getdate(self.violation_date)
        
        # Find last violation of same type within 180 days
        cutoff_date = violation_date - timedelta(days=180)
        
        last_violation = frappe.db.sql("""
            SELECT name, violation_date
            FROM `tabPenalty Record`
            WHERE employee = %s
            AND violation_type = %s
            AND violation_date >= %s
            AND violation_date < %s
            AND docstatus = 1
            ORDER BY violation_date DESC
            LIMIT 1
        """, (self.employee, self.violation_type, cutoff_date, violation_date), as_dict=True)
        
        if last_violation:
            # Continue to next level
            occurrence_number = self.get_next_occurrence_number()
        else:
            # Reset to first level
            occurrence_number = 1
        
        # Find matching penalty level
        for level in penalty_type_doc.penalty_levels:
            if level.occurrence_number == occurrence_number:
                self.append("penalty_levels", {
                    "occurrence_number": level.occurrence_number,
                    "penalty_type_level": "Percentage Deduction",  # All our penalties are percentage deductions
                    "penalty_value_level": level.penalty_value_level,
                    "is_percentage_level": level.is_percentage_level
                })
                break
    
    def get_next_occurrence_number(self):
        """Get the next occurrence number for this violation type"""
        from frappe.utils import getdate
        
        # Ensure violation_date is a date object
        violation_date = getdate(self.violation_date)
        
        # Count previous violations of same type within 180 days
        cutoff_date = violation_date - timedelta(days=180)
        
        count = frappe.db.count("Penalty Record", {
            "employee": self.employee,
            "violation_type": self.violation_type,
            "violation_date": [">=", cutoff_date],
            "violation_date": ["<", violation_date],
            "docstatus": 1
        })
        
        return count + 1
    
    def calculate_total_penalty_value(self):
        """Calculate total penalty value from penalty levels"""
        total = 0
        for level in self.penalty_levels:
            if level.penalty_type_level in ["Percentage Deduction", "Day Deduction"]:
                total += level.penalty_value_level
        
        self.total_penalty_value = total
    
    def on_submit(self):
        """Handle penalty submission"""
        if self.penalty_status == "Approved":
            self.create_salary_component_deduction()
            
            # Check for termination
            for level in self.penalty_levels:
                if level.penalty_type_level == "Termination":
                    self.terminate_employee()
                    break
    
    def create_salary_component_deduction(self):
        """Create salary component deduction for penalties"""
        # This will be handled by salary slip calculation
        pass
    
    def terminate_employee(self):
        """Terminate employee if penalty type is termination"""
        employee_doc = frappe.get_doc("Employee", self.employee)
        employee_doc.status = "Left"
        employee_doc.relieving_date = self.violation_date
        employee_doc.save()
        
        frappe.msgprint(_("Employee {0} has been terminated due to penalty violation").format(self.employee))
