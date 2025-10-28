// Copyright (c) 2025, Pioneer Holding and contributors
// For license information, please see license.txt

frappe.ui.form.on('Biometric Sync Log', {
	refresh: function(frm) {
		// Add custom buttons or actions if needed
		if (frm.doc.status === 'error') {
			frm.set_indicator_color('Red');
		} else if (frm.doc.status === 'processed') {
			frm.set_indicator_color('Green');
		} else if (frm.doc.status === 'validation_error') {
			frm.set_indicator_color('Orange');
		}
	}
});

