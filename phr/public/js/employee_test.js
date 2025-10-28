frappe.ui.form.on('Employee', {
    refresh: function(frm) {
        console.log('PHR Employee script loaded successfully!');
        frm.add_custom_button(__('Test PHR Button'), function() {
            frappe.msgprint(__('PHR Test Button Clicked!'));
        });
    }
});
