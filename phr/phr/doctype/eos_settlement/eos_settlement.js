// Copyright (c) 2024, PHR and contributors
// For license information, please see license.txt

frappe.ui.form.on('EOS Settlement', {
	refresh: function(frm) {
		// Add custom buttons or functionality here if needed
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Calculate Settlement'), function() {
				frm.trigger('calculate_settlement');
			}, __('Actions'));
		}
	},
	
	calculate_settlement: function(frm) {
		if (frm.doc.employee && frm.doc.end_of_service_date) {
			frm.call('calculate_years_of_service');
			frm.call('calculate_gratuity');
			frm.call('calculate_vacation_allowance');
			frm.call('calculate_loan_details');
			frm.call('calculate_total_settlement');
		} else {
			frappe.msgprint(__('Please select Employee and End of Service Date first'));
		}
	},
	
	employee: function(frm) {
		if (frm.doc.employee) {
			frm.call('get_employee_details');
		}
	},
	
	end_of_service_date: function(frm) {
		if (frm.doc.employee && frm.doc.end_of_service_date) {
			frm.call('calculate_years_of_service');
		}
	}
});
