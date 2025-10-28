import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta

class EOSSettlement(Document):
    def validate(self):
        self.calculate_years_of_service()
        self.calculate_gratuity()
        self.calculate_vacation_allowance()
        self.calculate_total_settlement()
    
    def calculate_years_of_service(self):
        """Calculate years of service from appointment to end of service"""
        if self.appointment_date and self.end_of_service_date:
            from frappe.utils import getdate
            appointment_date = getdate(self.appointment_date)
            end_date = getdate(self.end_of_service_date)
            delta = end_date - appointment_date
            self.years_of_service = round(delta.days / 365.25, 2)
    
    def calculate_gratuity(self):
        """Calculate gratuity based on Saudi Labor Law Articles 84/85"""
        if not self.last_basic_salary or not self.years_of_service:
            return
        
        years = int(self.years_of_service)
        partial_year = self.years_of_service - years
        
        if self.termination_reason == "Termination by Employer":
            # Article 84: Employer termination
            gratuity = 0
            
            # Half salary for each year of first 5 years
            first_5_years = min(years, 5)
            gratuity += (first_5_years * self.last_basic_salary * 0.5)
            
            # Full salary for each year after 5 years
            if years > 5:
                remaining_years = years - 5
                gratuity += (remaining_years * self.last_basic_salary)
            
            # Add partial year proportionally
            if partial_year > 0:
                if years < 5:
                    gratuity += (partial_year * self.last_basic_salary * 0.5)
                else:
                    gratuity += (partial_year * self.last_basic_salary)
        
        elif self.termination_reason == "Resignation":
            # Article 85: Employee resignation
            if years < 2:
                gratuity = 0  # Nothing due
            elif years < 5:
                # One-third of Article 84 calculation
                base_gratuity = self.calculate_article_84_gratuity()
                gratuity = base_gratuity * (1/3)
            elif years < 10:
                # Two-thirds of Article 84 calculation
                base_gratuity = self.calculate_article_84_gratuity()
                gratuity = base_gratuity * (2/3)
            else:
                # Full Article 84 calculation
                gratuity = self.calculate_article_84_gratuity()
        else:
            # Contract expiry - same as Article 84
            gratuity = self.calculate_article_84_gratuity()
        
        self.gratuity_amount = gratuity
        self.eligible_for_gratuity = gratuity > 0
    
    def calculate_article_84_gratuity(self):
        """Calculate gratuity according to Article 84"""
        years = int(self.years_of_service)
        partial_year = self.years_of_service - years
        
        gratuity = 0
        
        # Half salary for each year of first 5 years
        first_5_years = min(years, 5)
        gratuity += (first_5_years * self.last_basic_salary * 0.5)
        
        # Full salary for each year after 5 years
        if years > 5:
            remaining_years = years - 5
            gratuity += (remaining_years * self.last_basic_salary)
        
        # Add partial year proportionally
        if partial_year > 0:
            if years < 5:
                gratuity += (partial_year * self.last_basic_salary * 0.5)
            else:
                gratuity += (partial_year * self.last_basic_salary)
        
        return gratuity
    
    def calculate_vacation_allowance(self):
        """Calculate vacation allowance for unused vacation days"""
        if not self.employee or not self.last_basic_salary:
            return
        
        # Get unused vacation days for each year
        # This would need integration with HRMS leave management
        # For now, we'll use a simplified calculation
        
        daily_salary = self.last_basic_salary / 30  # Assuming 30 days per month
        
        # Half month for each year of first 5 years
        first_5_years = min(int(self.years_of_service), 5)
        vacation_allowance = first_5_years * (self.last_basic_salary * 0.5)
        
        # Full month for each year after 5 years
        if self.years_of_service > 5:
            remaining_years = int(self.years_of_service) - 5
            vacation_allowance += remaining_years * self.last_basic_salary
        
        self.vacation_allowance = vacation_allowance
    
    def calculate_total_settlement(self):
        """Calculate total settlement amount"""
        gratuity = self.gratuity_amount or 0
        vacation = self.vacation_allowance or 0
        
        # Check for loan deductions
        loan_deduction = self.calculate_loan_deduction()
        
        self.total_settlement = gratuity + vacation - loan_deduction
    
    def calculate_loan_deduction(self):
        """Calculate loan balance deduction"""
        if not self.employee:
            return 0
        
        try:
            # Get outstanding loan balance
            from phr.phr.doctype.loan_installment_postponement.loan_installment_postponement import LoanInstallmentPostponement
            
            loan_postponement = LoanInstallmentPostponement()
            outstanding_balance = loan_postponement.calculate_outstanding_balance(self.employee)
            
            if outstanding_balance > self.total_settlement:
                frappe.msgprint(_("Warning: Outstanding loan balance ({0}) exceeds total settlement ({1})").format(
                    outstanding_balance, self.total_settlement
                ))
            
            return min(outstanding_balance, self.total_settlement)
        except Exception as e:
            frappe.log_error(f"Error calculating loan deduction: {str(e)}", "EOS Settlement Loan Calculation")
            return 0
    
    def create_final_salary_slip(self):
        """Create final salary slip for the employee"""
        # This method would create a salary slip with:
        # - End of service gratuity component
        # - Vacation allowance component
        # - Loan balance deduction component
        
        frappe.msgprint(_("Final salary slip creation functionality to be implemented"))
