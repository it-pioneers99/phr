// Copyright (c) 2025, Pioneer and contributors
// License: MIT. See LICENSE

frappe.ui.form.on("Employee Checkin", {
	refresh: function(frm) {
		// Add buttons to form view
		get_biometric_sync_status().then(status => {
			// Clear any existing buttons first
			frm.page.actions.find('.btn-custom[data-label*="Biometric Sync"]').remove();
			
			// Add Start button
			frm.add_custom_button(__("Start Biometric Sync"), function() {
				start_biometric_sync(null, frm);
			}, __("Biometric Sync"));
			
			// Add Stop button
			frm.add_custom_button(__("Stop Biometric Sync"), function() {
				stop_biometric_sync(null, frm);
			}, __("Biometric Sync"));
			
			// Get button references after they're created
			setTimeout(() => {
				let buttons = frm.page.actions.find('.btn-custom[data-label*="Biometric Sync"]');
				if (buttons.length >= 2) {
					frm.biometric_start_btn = buttons.filter(function() {
						return $(this).text().includes("Start");
					}).first();
					frm.biometric_stop_btn = buttons.filter(function() {
						return $(this).text().includes("Stop");
					}).first();
					
					// Update button states based on status
					update_button_states(frm, status);
				}
			}, 100);
		});
	},
});

// Add buttons to Employee Checkin List page
frappe.listview_settings['Employee Checkin'] = {
	onload: function(list_view) {
		// Get sync status
		get_biometric_sync_status().then(status => {
			// Add Start button
			list_view.page.add_action_item(__("Start Biometric Sync"), function() {
				start_biometric_sync(list_view);
			});
			
			// Add Stop button
			list_view.page.add_action_item(__("Stop Biometric Sync"), function() {
				stop_biometric_sync(list_view);
			});
			
			// Get button references after they're created
			setTimeout(() => {
				let action_items = list_view.page.page_actions.find('.page-action-item');
				if (action_items.length >= 2) {
					let start_btn = action_items.filter(function() {
						return $(this).text().includes("Start Biometric");
					}).first();
					let stop_btn = action_items.filter(function() {
						return $(this).text().includes("Stop Biometric");
					}).first();
					
					if (start_btn.length && stop_btn.length) {
						list_view.biometric_start_btn = start_btn;
						list_view.biometric_stop_btn = stop_btn;
						
						// Update button states
						update_list_button_states(list_view, status);
					}
				}
			}, 100);
			
			// Add status indicator
			add_status_indicator(list_view, status);
		});
	}
};

function update_button_states(frm, status) {
	if (!frm) return;
	
	if (status.running) {
		// Disable Start button, enable Stop button
		if (frm.biometric_start_btn) {
			frm.biometric_start_btn.prop('disabled', true).addClass('btn-disabled').css('opacity', '0.5');
		}
		if (frm.biometric_stop_btn) {
			frm.biometric_stop_btn.prop('disabled', false).removeClass('btn-disabled').css('opacity', '1');
		}
	} else {
		// Enable Start button, disable Stop button
		if (frm.biometric_start_btn) {
			frm.biometric_start_btn.prop('disabled', false).removeClass('btn-disabled').css('opacity', '1');
		}
		if (frm.biometric_stop_btn) {
			frm.biometric_stop_btn.prop('disabled', true).addClass('btn-disabled').css('opacity', '0.5');
		}
	}
}

function update_list_button_states(list_view, status) {
	if (!list_view) return;
	
	if (status.running) {
		// Disable Start, enable Stop
		if (list_view.biometric_start_btn) {
			list_view.biometric_start_btn.prop('disabled', true).addClass('btn-disabled').css('opacity', '0.5');
		}
		if (list_view.biometric_stop_btn) {
			list_view.biometric_stop_btn.prop('disabled', false).removeClass('btn-disabled').css('opacity', '1');
		}
	} else {
		// Enable Start, disable Stop
		if (list_view.biometric_start_btn) {
			list_view.biometric_start_btn.prop('disabled', false).removeClass('btn-disabled').css('opacity', '1');
		}
		if (list_view.biometric_stop_btn) {
			list_view.biometric_stop_btn.prop('disabled', true).addClass('btn-disabled').css('opacity', '0.5');
		}
	}
}

function add_status_indicator(list_view, status) {
	let status_html = `
		<div class="biometric-sync-status" style="padding: 8px; margin: 10px; border-radius: 4px; background: ${status.running ? '#d4edda' : '#f8d7da'};">
			<strong>Biometric Sync:</strong> 
			<span style="color: ${status.running ? '#155724' : '#721c24'};">
				${status.running ? '🟢 Running' : '🔴 Stopped'}
			</span>
			${status.last_sync ? `<br><small>Last Sync: ${status.last_sync}</small>` : ''}
		</div>
	`;
	
	list_view.page.add_inner_message(status_html);
}

function get_biometric_sync_status() {
	return new Promise((resolve) => {
		frappe.call({
			method: "phr.phr.api.biometric_sync_control.get_sync_status",
			callback: function(r) {
				resolve(r.message || { running: false, last_sync: null });
			},
			error: function() {
				resolve({ running: false, last_sync: null });
			}
		});
	});
}

function start_biometric_sync(list_view, frm) {
	frappe.confirm(
		__("Are you sure you want to start the biometric sync service?"),
		function() {
			frappe.call({
				method: "phr.phr.api.biometric_sync_control.start_sync",
				freeze: true,
				freeze_message: __("Starting biometric sync service..."),
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __("Biometric sync service started successfully"),
							indicator: "green"
						});
						
						// Refresh status and update buttons
						refresh_sync_status(list_view, frm);
					} else {
						frappe.show_alert({
							message: __(r.message?.message || "Failed to start service"),
							indicator: "red"
						});
					}
				}
			});
		}
	);
}

function stop_biometric_sync(list_view, frm) {
	frappe.confirm(
		__("Are you sure you want to stop the biometric sync service?"),
		function() {
			frappe.call({
				method: "phr.phr.api.biometric_sync_control.stop_sync",
				freeze: true,
				freeze_message: __("Stopping biometric sync service..."),
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __("Biometric sync service stopped successfully"),
							indicator: "green"
						});
						
						// Refresh status and update buttons
						refresh_sync_status(list_view, frm);
					} else {
						frappe.show_alert({
							message: __(r.message?.message || "Failed to stop service"),
							indicator: "red"
						});
					}
				}
			});
		}
	);
}

function refresh_sync_status(list_view, frm) {
	// Refresh status after start/stop operation
	get_biometric_sync_status().then(status => {
		if (list_view) {
			// Re-fetch button references if needed
			if (!list_view.biometric_start_btn || !list_view.biometric_stop_btn) {
				let action_items = list_view.page.page_actions.find('.page-action-item');
				if (action_items.length >= 2) {
					list_view.biometric_start_btn = action_items.filter(function() {
						return $(this).text().includes("Start Biometric");
					}).first();
					list_view.biometric_stop_btn = action_items.filter(function() {
						return $(this).text().includes("Stop Biometric");
					}).first();
				}
			}
			
			// Update list view buttons
			update_list_button_states(list_view, status);
			
			// Update status indicator
			$('.biometric-sync-status').remove();
			add_status_indicator(list_view, status);
		}
		
		if (frm) {
			// Re-fetch button references if needed
			if (!frm.biometric_start_btn || !frm.biometric_stop_btn) {
				let buttons = frm.page.actions.find('.btn-custom[data-label*="Biometric Sync"]');
				if (buttons.length >= 2) {
					frm.biometric_start_btn = buttons.filter(function() {
						return $(this).text().includes("Start");
					}).first();
					frm.biometric_stop_btn = buttons.filter(function() {
						return $(this).text().includes("Stop");
					}).first();
				}
			}
			
			// Update form view buttons
			update_button_states(frm, status);
		}
		
		// If neither provided, try to get current context
		if (!list_view && !frm && cur_frm) {
			let buttons = cur_frm.page.actions.find('.btn-custom[data-label*="Biometric Sync"]');
			if (buttons.length >= 2 && (!cur_frm.biometric_start_btn || !cur_frm.biometric_stop_btn)) {
				cur_frm.biometric_start_btn = buttons.filter(function() {
					return $(this).text().includes("Start");
				}).first();
				cur_frm.biometric_stop_btn = buttons.filter(function() {
					return $(this).text().includes("Stop");
				}).first();
			}
			update_button_states(cur_frm, status);
		}
	});
}

