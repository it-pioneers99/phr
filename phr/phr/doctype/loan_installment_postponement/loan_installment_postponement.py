import frappe
from frappe.model.document import Document
from frappe import _

class LoanInstallmentPostponement(Document):
    def validate(self):
        self.validate_installment_dates()
    
    def validate_installment_dates(self):
        """Validate that new installment month is after current month"""
        if self.current_installment_month and self.new_installment_month:
            if self.new_installment_month <= self.current_installment_month:
                frappe.throw(_("New installment month must be after current installment month"))
    
    def on_submit(self):
        """Handle postponement approval"""
        if self.status == "Approved":
            self.update_loan_schedule()
            self.create_loan_reference()
    
    def update_loan_schedule(self):
        """Update the loan repayment schedule"""
        if not self.loan_id or not self.current_installment_month or not self.new_installment_month:
            return
        
        # Update the loan schedule
        # This would need to be implemented based on the loan doctype structure
        # For now, we'll create a reference in the loan doctype
        
        loan_doc = frappe.get_doc("Loan", self.loan_id)
        
        # Add a note about the postponement
        if not hasattr(loan_doc, 'postponements'):
            loan_doc.postponements = []
        
        loan_doc.append("postponements", {
            "postponement_request": self.name,
            "original_date": self.current_installment_month,
            "new_date": self.new_installment_month,
            "reason": self.reason
        })
        
        loan_doc.save()
    
    def create_loan_reference(self):
        """Create reference in loan doctype"""
        # This method creates a link in the loan doctype
        # indicating that the installment has been postponed
        pass
    
    def calculate_outstanding_balance(self, employee):
        """Calculate outstanding loan balance for employee"""
        # This method would be used in End of Service calculation
        loans = frappe.get_all("Loan", 
            filters={"applicant": employee, "docstatus": 1},
            fields=["name", "total_payment", "total_amount_paid"]
        )
        
        total_outstanding = 0
        for loan in loans:
            outstanding = loan.total_payment - loan.total_amount_paid
            total_outstanding += outstanding
        
        return total_outstanding
