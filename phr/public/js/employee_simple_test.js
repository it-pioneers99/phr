frappe.ui.form.on('Employee', {
    refresh: function(frm) {
        console.log('PHR Employee script loaded successfully!');
        
        // Add a simple test button
        frm.add_custom_button(__('PHR Test'), function() {
            frappe.msgprint(__('PHR Test Button Clicked!'));
        });
        
        // Add the main PHR button
        frm.add_custom_button(__('PHR Management'), function() {
            frappe.msgprint(__('PHR Management Button Clicked!'));
        });
    }
});
