# Copyright (c) 2025, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PenaltyType(Document):
	def validate(self):
		"""Auto-populate time fields from selected shift type"""
		if self.shift_type:
			shift_doc = frappe.get_doc("Shift Type", self.shift_type)
			self.time_from = shift_doc.start_time
			self.time_to = shift_doc.end_time
		else:
			self.time_from = None
			self.time_to = None
