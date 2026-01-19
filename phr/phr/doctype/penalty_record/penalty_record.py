import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta

class PenaltyRecord(Document):
    def validate(self):
        self.calculate_penalty_period()
        self.calculate_penalty_level()
        self.calculate_total_penalty_value()
    
    def calculate_penalty_period(self):
        """
        Calculate penalty period (day 21 to day 20 of next month).
        This is used for tracking violations within a specific period.
        """
        if not self.violation_date:
            return
        
        from frappe.utils import getdate
        violation_date = getdate(self.violation_date)
        
        # Penalty period: from day 21 of current month to day 20 of next month
        if violation_date.day >= 21:
            # Period starts on day 21 of current month
            self.penalty_period_start = violation_date.replace(day=21)
            # Period ends on day 20 of next month
            if violation_date.month == 12:
                self.penalty_period_end = violation_date.replace(year=violation_date.year + 1, month=1, day=20)
            else:
                self.penalty_period_end = violation_date.replace(month=violation_date.month + 1, day=20)
        else:
            # If before day 21, period is from day 21 of previous month to day 20 of current month
            if violation_date.month == 1:
                self.penalty_period_start = violation_date.replace(year=violation_date.year - 1, month=12, day=21)
            else:
                self.penalty_period_start = violation_date.replace(month=violation_date.month - 1, day=21)
            self.penalty_period_end = violation_date.replace(day=20)
    
    def calculate_penalty_level(self):
        """
        Calculate penalty level based on previous violations within 180 days.
        This method populates the penalty_levels child table from Penalty Type's levels.
        """
        if not self.employee or not self.violation_type or not self.violation_date:
            return
        
        # Clear existing penalty levels first
        self.penalty_levels = []
        
        # Get penalty type to access penalty levels
        try:
            penalty_type_doc = frappe.get_doc("Penalty Type", self.violation_type)
        except Exception as e:
            frappe.log_error(f"Error loading Penalty Type {self.violation_type}: {str(e)}")
            return
        
        if not penalty_type_doc.penalty_levels:
            frappe.msgprint(_("No penalty levels defined for this penalty type"), alert=True)
            return
        
        # Ensure violation_date is a date object
        from frappe.utils import getdate
        violation_date = getdate(self.violation_date)
        
        # Calculate occurrence number based on 180-day rolling window
        occurrence_number = self.get_next_occurrence_number()
        
        # Update occurrence_number field
        self.occurrence_number = occurrence_number
        
        # Find matching penalty level from Penalty Type
        matching_level = None
        for level in penalty_type_doc.penalty_levels:
            if level.occurrence_number == occurrence_number:
                matching_level = level
                break
        
        if not matching_level:
            # If no exact match, use the highest defined level
            if penalty_type_doc.penalty_levels:
                matching_level = max(penalty_type_doc.penalty_levels, key=lambda x: x.occurrence_number or 0)
        
        if matching_level:
            # Determine penalty type level based on value
            # If value is 0, it's a Warning; otherwise Percentage Deduction
            penalty_type_level = "Warning" if (matching_level.penalty_value_level or 0) == 0 else "Percentage Deduction"
            
            # Add penalty level to child table
            self.append("penalty_levels", {
                "occurrence_number": matching_level.occurrence_number,
                "penalty_type_level": penalty_type_level,
                "penalty_value_level": matching_level.penalty_value_level or 0,
                "is_percentage_level": matching_level.is_percentage_level or 1
            })
    
    def get_next_occurrence_number(self):
        """
        Get the next occurrence number for this violation type within the penalty period.
        Penalty period: Day 21 to Day 20 of next month (30 days).
        If employee reaches last level, subsequent violations use last level.
        """
        from frappe.utils import getdate
        
        # Ensure violation_date is a date object
        violation_date = getdate(self.violation_date)
        
        # Calculate penalty period (day 21 to day 20 of next month)
        if violation_date.day >= 21:
            # Period starts on day 21 of current month
            period_start = violation_date.replace(day=21)
            # Period ends on day 20 of next month
            if violation_date.month == 12:
                period_end = violation_date.replace(year=violation_date.year + 1, month=1, day=20)
            else:
                period_end = violation_date.replace(month=violation_date.month + 1, day=20)
        else:
            # If before day 21, period is from day 21 of previous month to day 20 of current month
            if violation_date.month == 1:
                period_start = violation_date.replace(year=violation_date.year - 1, month=12, day=21)
            else:
                period_start = violation_date.replace(month=violation_date.month - 1, day=21)
            period_end = violation_date.replace(day=20)
        
        # Count previous violations of same type within current penalty period
        count = frappe.db.count("Penalty Record", {
            "employee": self.employee,
            "violation_type": self.violation_type,
            "violation_date": [">=", period_start],
            "violation_date": ["<=", period_end],
            "violation_date": ["<", violation_date],  # Exclude current violation
            "docstatus": 1
        })
        
        # Get maximum level defined for this penalty type
        try:
            penalty_type_doc = frappe.get_doc("Penalty Type", self.violation_type)
            if penalty_type_doc.penalty_levels:
                max_level = max([level.occurrence_number or 0 for level in penalty_type_doc.penalty_levels])
            else:
                max_level = 4  # Default
        except Exception:
            max_level = 4  # Default
        
        # Calculate occurrence number
        occurrence_number = count + 1
        
        # If occurrence exceeds max level, use max level (don't go beyond)
        if occurrence_number > max_level:
            occurrence_number = max_level
        
        return occurrence_number
    
    def calculate_total_penalty_value(self):
        """
        Calculate total penalty value and penalty amount from penalty levels.
        Penalty amount is calculated based on employee's daily wage and penalty percentage.
        """
        from frappe.utils import flt
        
        # Calculate total penalty percentage
        total_percentage = 0
        for level in self.penalty_levels:
            if level.penalty_type_level in ["Percentage Deduction", "Day Deduction"]:
                total_percentage += flt(level.penalty_value_level or 0)
        
        self.total_penalty_value = total_percentage
        
        # Calculate penalty amount in currency (if percentage)
        if total_percentage > 0 and self.employee:
            try:
                # Get employee's daily wage
                employee_doc = frappe.get_doc("Employee", self.employee)
                monthly_salary = getattr(employee_doc, 'salary', 0) or getattr(employee_doc, 'base', 0)
                
                if monthly_salary:
                    daily_wage = flt(monthly_salary) / 30  # Assuming 30 days per month
                    # Calculate penalty amount as percentage of daily wage
                    self.penalty_amount = (daily_wage * total_percentage) / 100
                else:
                    self.penalty_amount = 0
            except Exception as e:
                frappe.log_error(f"Error calculating penalty amount: {str(e)}")
                self.penalty_amount = 0
        else:
            self.penalty_amount = 0
    
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
