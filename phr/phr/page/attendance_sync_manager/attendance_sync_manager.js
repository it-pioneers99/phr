frappe.pages['attendance-sync-manager'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Attendance Sync Manager'),
		single_column: true
	});

	// Add primary button for bulk processing
	page.add_inner_button(__('Process Pending Checkins'), function() {
		show_bulk_process_dialog(page);
	}, __('Actions'));

	// Add button to refresh statistics
	page.add_inner_button(__('Refresh Statistics'), function() {
		load_statistics(page);
	}, __('Actions'));

	// Create the page layout
	let $content = $(page.body);
	$content.html(`
		<div class="attendance-sync-manager">
			<div class="row">
				<div class="col-md-12">
					<div class="page-card-head">
						<h4>${__('Automatic Attendance Sync Status')}</h4>
						<p class="text-muted">
							${__('This page shows the status of automatic attendance processing from employee checkins.')}
						</p>
					</div>
				</div>
			</div>
			<div class="row" style="margin-top: 20px;">
				<div class="col-md-3">
					<div class="card">
						<div class="card-body text-center">
							<h3 id="total-checkins" class="text-primary">-</h3>
							<p class="text-muted">${__('Total Checkins')}</p>
						</div>
					</div>
				</div>
				<div class="col-md-3">
					<div class="card">
						<div class="card-body text-center">
							<h3 id="processed-checkins" class="text-success">-</h3>
							<p class="text-muted">${__('Processed Checkins')}</p>
						</div>
					</div>
				</div>
				<div class="col-md-3">
					<div class="card">
						<div class="card-body text-center">
							<h3 id="pending-checkins" class="text-warning">-</h3>
							<p class="text-muted">${__('Pending Checkins')}</p>
						</div>
					</div>
				</div>
				<div class="col-md-3">
					<div class="card">
						<div class="card-body text-center">
							<h3 id="total-attendance" class="text-info">-</h3>
							<p class="text-muted">${__('Total Attendance')}</p>
						</div>
					</div>
				</div>
			</div>
			<div class="row" style="margin-top: 20px;">
				<div class="col-md-12">
					<div class="card">
						<div class="card-body">
							<h5>${__('How It Works')}</h5>
							<ul>
								<li>${__('When biometric devices sync employee checkins, the system automatically processes them.')}</li>
								<li>${__('For each checkin, the system identifies the shift and creates attendance records.')}</li>
								<li>${__('This happens in the background without any manual intervention.')}</li>
								<li>${__('If any checkins are missed, you can use the "Process Pending Checkins" button above.')}</li>
							</ul>
						</div>
					</div>
				</div>
			</div>
		</div>
	`);

	// Load initial statistics
	load_statistics(page);
}

function load_statistics(page) {
	frappe.call({
		method: 'phr.phr.phr.page.attendance_sync_manager.attendance_sync_manager.get_sync_statistics',
		callback: function(r) {
			if (r.message) {
				$('#total-checkins').text(r.message.total_checkins || 0);
				$('#processed-checkins').text(r.message.processed_checkins || 0);
				$('#pending-checkins').text(r.message.pending_checkins || 0);
				$('#total-attendance').text(r.message.total_attendance || 0);
			}
		}
	});
}

function show_bulk_process_dialog(page) {
	let dialog = new frappe.ui.Dialog({
		title: __('Process Pending Checkins'),
		fields: [
			{
				fieldtype: 'Date',
				fieldname: 'from_date',
				label: __('From Date'),
				default: frappe.datetime.add_days(frappe.datetime.get_today(), -30)
			},
			{
				fieldtype: 'Date',
				fieldname: 'to_date',
				label: __('To Date'),
				default: frappe.datetime.get_today()
			},
			{
				fieldtype: 'HTML',
				fieldname: 'info',
				options: `<div class="alert alert-info">
					${__('This will process all pending employee checkins and create attendance records. This may take a few minutes depending on the number of checkins.')}
				</div>`
			}
		],
		primary_action_label: __('Process'),
		primary_action: function(values) {
			frappe.show_progress(__('Processing Checkins'), 0, 100, __('Please wait...'));
			
			frappe.call({
				method: 'phr.phr.doc_events.employee_checkin_events.bulk_process_pending_checkins',
				args: {
					from_date: values.from_date,
					to_date: values.to_date
				},
				callback: function(r) {
					frappe.hide_progress();
					dialog.hide();
					
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __('Processed {0} checkins successfully. {1} errors.', 
								[r.message.processed, r.message.errors]),
							indicator: r.message.errors > 0 ? 'orange' : 'green'
						});
						
						// Refresh statistics
						load_statistics(page);
					}
				},
				error: function(r) {
					frappe.hide_progress();
					frappe.msgprint(__('Error processing checkins. Please check error log.'));
				}
			});
		}
	});
	
	dialog.show();
}

