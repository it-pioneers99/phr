from . import __version__ as app_version

app_name = "phr"
app_title = "PHR - Pioneer HR Management"
app_publisher = "Pioneer Holding"
app_description = "PHR - Pioneer HR Management System"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@pioneersholding.ae"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/phr/css/phr.css"
# app_include_js = "/assets/phr/js/phr.js"

# include js, css files in header of web template
# web_include_css = "/assets/phr/css/phr.css"
# web_include_js = "/assets/phr/js/phr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "phr/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Employee": "phr/public/js/employee.js"
}

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "phr.install.before_install"
# after_install = "phr.phr.phr.setup_dynamic_leave_system.setup_dynamic_leave_system"

# Uninstallation
# ------------

# before_uninstall = "phr.uninstall.before_uninstall"
# after_uninstall = "phr.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "phr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# Temporarily disabled PHR event handlers to test Employee save
# doc_events = {
#     "Employee": {
#         "after_insert": "phr.phr.doc_events.employee_leave_events.after_insert",
#         "on_update": "phr.phr.doc_events.employee_leave_events.on_update",
#         "validate": "phr.phr.doc_events.employee_leave_events.validate",
#         "on_cancel": "phr.phr.doc_events.employee_leave_events.on_cancel"
#     },
#     "Leave Application": {
#         "validate": "phr.phr.doc_events.leave_application_events.validate",
#         "on_submit": "phr.phr.doc_events.leave_application_events.on_submit",
#         "on_cancel": "phr.phr.doc_events.leave_application_events.on_cancel",
#         "before_save": "phr.phr.doc_events.leave_application_events.before_save"
#     },
#     "Salary Slip": {
#         "before_submit": "phr.phr.doc_events.salary_slip_leave_events.before_submit"
#     }
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    "daily": [
        "phr.phr.scheduled_tasks.employee_summary_tasks.daily_employee_summary_calculation",
        "phr.phr.scheduled_tasks.employee_summary_tasks.send_test_period_notifications"
    ],
    "weekly": [
        "phr.phr.scheduled_tasks.employee_summary_tasks.generate_weekly_leave_report"
    ],
    "monthly": [
        "phr.phr.scheduled_tasks.employee_summary_tasks.cleanup_old_notifications"
    ]
}

# Testing
# -------

# before_tests = "phr.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "phr.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation, plus data members specific to the overriding function
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "phr.event.get_events"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"phr.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# translate_link_doctypes = ["DocType", "Role", "Module Def", "Print Format", "Report", "Workspace"]
