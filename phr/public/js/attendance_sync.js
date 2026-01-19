/**
 * Attendance Sync Custom Button
 * Adds "Send Sync Attends" button to Employee Checkin and Attendance list views
 */

// Employee Checkin List View
frappe.listview_settings["Employee Checkin"] = {
	onload: function (listview) {
		// Keep existing "Fetch Shifts" functionality if it exists
		// Add "Send Sync Attends" button
		listview.page.add_action_item(__("Send Sync Attends"), () => {
			const selected = listview.get_checked_items();
			
			if (selected.length === 0) {
				frappe.msgprint({
					title: __("No Selection"),
					message: __("Please select at least one Employee Checkin record to sync."),
					indicator: "orange"
				});
				return;
			}
			
			const checkin_names = selected.map(item => item.name);
			
			// Debug: Log selected names
			console.log("Selected checkin names:", checkin_names);
			console.log("Selected count:", checkin_names.length);
			
			// Show confirmation dialog
			frappe.confirm(
				__("Are you sure you want to sync {0} Employee Checkin record(s) to the remote server?", [selected.length]),
				() => {
					// Proceed with sync
					frappe.call({
						method: "phr.phr.api.attendance_sync.sync_selected_records",
						args: {
							doctype: "Employee Checkin",
							names: checkin_names
						},
						freeze: true,
						freeze_message: __("Syncing Employee Checkin records..."),
						callback: function(r) {
							console.log("Sync response:", r);
							if (r.message) {
								const result = r.message;
								
								// Always show the message, even if 0 synced
								if (result.success !== false) {
									// Show alert with detailed message
									const alert_msg = result.message || 
										__("Sync completed: {0} synced, {1} failed out of {2} total", [
											result.synced || 0,
											result.failed || 0,
											result.total || 0
										]);
									
									frappe.show_alert({
										message: alert_msg,
										indicator: result.failed > 0 || (result.synced === 0 && result.failed === 0) ? "orange" : "green"
									}, 8);
									
									// Show details if there are failures or if nothing synced
									if ((result.failed > 0 || result.synced === 0) && result.details) {
										const failed_details = result.details
											.filter(d => d.status === "failed" || d.status === "error")
											.map(d => `- ${d.checkin || d.attendance || d.name}: ${d.error || "Unknown error"}`)
											.join("\n");
										
										if (failed_details) {
											frappe.msgprint({
												title: __("Sync Details"),
												message: __("Sync Results:\n\n{0}", [failed_details]),
												indicator: result.synced === 0 ? "red" : "orange"
											});
										}
									} else if (result.synced === 0 && result.failed === 0) {
										// Show message if no records were processed
										frappe.msgprint({
											title: __("No Records Processed"),
											message: result.message || __("No records were found to sync. Please check the selected records."),
											indicator: "orange"
										});
									}
									
									// Refresh list
									listview.refresh();
								} else {
									frappe.msgprint({
										title: __("Sync Failed"),
										message: result.message || __("An error occurred during sync"),
										indicator: "red"
									});
								}
							} else {
								frappe.msgprint({
									title: __("Error"),
									message: __("No response from server"),
									indicator: "red"
								});
							}
						},
						error: function(r) {
							console.error("Sync error:", r);
							frappe.msgprint({
								title: __("Error"),
								message: __("An error occurred: {0}", [r.message || r.exc || "Unknown error"]),
								indicator: "red"
							});
						}
					});
				}
			);
		});
	}
};

// Attendance List View
frappe.listview_settings["Attendance"] = {
	onload: function (listview) {
		// Add "Send Sync Attends" button
		listview.page.add_action_item(__("Send Sync Attends"), () => {
			const selected = listview.get_checked_items();
			
			if (selected.length === 0) {
				frappe.msgprint({
					title: __("No Selection"),
					message: __("Please select at least one Attendance record to sync."),
					indicator: "orange"
				});
				return;
			}
			
			const attendance_names = selected.map(item => item.name);
			
			// Debug: Log selected names
			console.log("Selected attendance names:", attendance_names);
			console.log("Selected count:", attendance_names.length);
			
			// Show confirmation dialog
			frappe.confirm(
				__("Are you sure you want to sync {0} Attendance record(s) to the remote server?", [selected.length]),
				() => {
					// Proceed with sync
					frappe.call({
						method: "phr.phr.api.attendance_sync.sync_selected_records",
						args: {
							doctype: "Attendance",
							names: attendance_names
						},
						freeze: true,
						freeze_message: __("Syncing Attendance records..."),
						callback: function(r) {
							console.log("Sync response:", r);
							if (r.message) {
								const result = r.message;
								
								// Always show the message, even if 0 synced
								if (result.success !== false) {
									// Show alert with detailed message
									const alert_msg = result.message || 
										__("Sync completed: {0} synced, {1} failed out of {2} total", [
											result.synced || 0,
											result.failed || 0,
											result.total || 0
										]);
									
									frappe.show_alert({
										message: alert_msg,
										indicator: result.failed > 0 || (result.synced === 0 && result.failed === 0) ? "orange" : "green"
									}, 8);
									
									// Show details if there are failures or if nothing synced
									if ((result.failed > 0 || result.synced === 0) && result.details) {
										const failed_details = result.details
											.filter(d => d.status === "failed" || d.status === "error")
											.map(d => `- ${d.attendance || d.checkin || d.name}: ${d.error || "Unknown error"}`)
											.join("\n");
										
										if (failed_details) {
											frappe.msgprint({
												title: __("Sync Details"),
												message: __("Sync Results:\n\n{0}", [failed_details]),
												indicator: result.synced === 0 ? "red" : "orange"
											});
										}
									} else if (result.synced === 0 && result.failed === 0) {
										// Show message if no records were processed
										frappe.msgprint({
											title: __("No Records Processed"),
											message: result.message || __("No records were found to sync. Please check the selected records."),
											indicator: "orange"
										});
									}
									
									// Refresh list
									listview.refresh();
								} else {
									frappe.msgprint({
										title: __("Sync Failed"),
										message: result.message || __("An error occurred during sync"),
										indicator: "red"
									});
								}
							} else {
								frappe.msgprint({
									title: __("Error"),
									message: __("No response from server"),
									indicator: "red"
								});
							}
						},
						error: function(r) {
							console.error("Sync error:", r);
							frappe.msgprint({
								title: __("Error"),
								message: __("An error occurred: {0}", [r.message || r.exc || "Unknown error"]),
								indicator: "red"
							});
						}
					});
				}
			);
		});
	}
};

