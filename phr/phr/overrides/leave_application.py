import frappe
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication as HRMSLeaveApplication

class LeaveApplication(HRMSLeaveApplication):
    website = frappe._dict({
        "condition_field": "status",
        "template": "templates/leave_application.html"
    })
    
    def get_context(self, context):
        context.update({
            "doc": self,
            "title": f"Leave Application - {self.employee_name}",
            "description": f"Leave application for {self.employee_name} from {self.from_date} to {self.to_date}"
        })
        return context
