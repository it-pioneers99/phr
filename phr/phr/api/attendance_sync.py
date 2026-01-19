"""
Attendance Sync API
===================

This module provides API endpoints to sync Employee Checkin and Attendance
data from localhost to the live server (test.pioneers-holding.link).

Features:
- Sync Employee Checkin records
- Sync Attendance records
- Track sync status and logs
- Handle errors gracefully
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, cstr
import requests
import json
import base64
from datetime import datetime
from typing import List, Dict, Any


# Remote server configuration
REMOTE_SERVER_URL = "https://test.pioneers-holding.link"
REMOTE_API_KEY = "1e516e181f9efb2"
REMOTE_API_SECRET = "879ec3d0d2e926d"


@frappe.whitelist()
def sync_employee_checkins(checkin_names=None, date_from=None, date_to=None):
    """
    Sync Employee Checkin records to remote server.
    
    Args:
        checkin_names: List of specific checkin names to sync (optional)
        date_from: Start date for syncing (optional, format: YYYY-MM-DD)
        date_to: End date for syncing (optional, format: YYYY-MM-DD)
    
    Returns:
        {
            "success": true/false,
            "synced": 10,
            "failed": 2,
            "message": "Sync completed",
            "details": [...]
        }
    """
    try:
        # Build filters
        filters = {}
        
        # Parse checkin_names if it's a string
        if checkin_names and isinstance(checkin_names, str):
            try:
                checkin_names = json.loads(checkin_names)
            except:
                checkin_names = [n.strip() for n in checkin_names.split(",") if n.strip()]
        
        if checkin_names:
            # Ensure it's a list
            if not isinstance(checkin_names, list):
                checkin_names = [checkin_names]
            
            # Log for debugging (keep title short)
            frappe.log_error(
                f"Fetching {len(checkin_names)} checkins",
                "Attendance Sync Debug"
            )
            
            filters["name"] = ["in", checkin_names]
        else:
            if date_from:
                filters["time"] = [">=", date_from]
            if date_to:
                if "time" in filters:
                    filters["time"].append("<=")
                    filters["time"].append(date_to)
                else:
                    filters["time"] = ["<=", date_to]
        
        # Get checkin records
        checkins = frappe.get_all(
            "Employee Checkin",
            filters=filters,
            fields=[
                "name", "employee", "employee_name", "time", "log_type",
                "device_id", "skip_auto_attendance", "latitude", "longitude"
            ],
            order_by="time desc"
        )
        
        # Log for debugging (keep title short)
        frappe.log_error(
            f"Found {len(checkins)} checkins to sync",
            "Attendance Sync Debug"
        )
        
        if not checkins:
            # Try to verify if records exist
            if checkin_names:
                existing_records = frappe.get_all(
                    "Employee Checkin",
                    filters={"name": ["in", checkin_names]},
                    fields=["name"],
                    limit=5
                )
                missing = [name for name in checkin_names if name not in [r.name for r in existing_records]]
                error_msg = f"No checkin records found to sync. "
                if missing:
                    error_msg += f"Missing records: {missing[:5]}. "
                error_msg += f"Filters used: {filters}"
            else:
                error_msg = f"No checkin records found to sync. Filters used: {filters}"
            
            return {
                "success": True,
                "synced": 0,
                "failed": 0,
                "total": 0,
                "message": error_msg,
                "details": []
            }
        
        synced_count = 0
        failed_count = 0
        details = []
        
        for checkin in checkins:
            try:
                # Get employee's attendance_device_id (required for remote API)
                employee_doc = frappe.get_doc("Employee", checkin.employee)
                attendance_device_id = employee_doc.get("attendance_device_id")
                
                if not attendance_device_id:
                    failed_count += 1
                    details.append({
                        "checkin": checkin.name,
                        "employee": checkin.employee,
                        "status": "failed",
                        "error": f"Employee {checkin.employee} does not have attendance_device_id set"
                    })
                    continue
                
                # Prepare data for remote server
                # The API expects employee_field_value to be the attendance_device_id
                checkin_data = {
                    "employee_field_value": attendance_device_id,
                    "timestamp": str(checkin.time),
                    "log_type": checkin.log_type or "IN",
                    "device_id": checkin.device_id,
                    "skip_auto_attendance": checkin.skip_auto_attendance or 0,
                }
                
                if checkin.latitude:
                    checkin_data["latitude"] = checkin.latitude
                if checkin.longitude:
                    checkin_data["longitude"] = checkin.longitude
                
                # Send to remote server
                result = send_to_remote_server(
                    doctype="Employee Checkin",
                    data=checkin_data,
                    method="add_log_based_on_employee_field"
                )
                
                if result.get("success"):
                    synced_count += 1
                    details.append({
                        "checkin": checkin.name,
                        "employee": checkin.employee,
                        "status": "success",
                        "remote_id": result.get("name")
                    })
                else:
                    failed_count += 1
                    error_msg = result.get("error", "Unknown error")
                    # Log detailed error for debugging
                    frappe.log_error(
                        f"Sync failed for checkin {checkin.name}: {error_msg}",
                        "Attendance Sync Error"
                    )
                    details.append({
                        "checkin": checkin.name,
                        "employee": checkin.employee,
                        "status": "failed",
                        "error": error_msg[:200]  # Limit error message length
                    })
                    
            except Exception as e:
                failed_count += 1
                details.append({
                    "checkin": checkin.name,
                    "employee": checkin.employee,
                    "status": "error",
                    "error": str(e)
                })
                frappe.log_error(f"Error syncing checkin {checkin.name}: {str(e)}", "Attendance Sync")
        
        # Log sync result
        log_sync_result("Employee Checkin", synced_count, failed_count, len(checkins))
        
        return {
            "success": True,
            "synced": synced_count,
            "failed": failed_count,
            "total": len(checkins),
            "message": f"Synced {synced_count} of {len(checkins)} checkin records",
            "details": details
        }
        
    except Exception as e:
        frappe.log_error(f"Error in sync_employee_checkins: {str(e)}", "Attendance Sync")
        return {
            "success": False,
            "synced": 0,
            "failed": 0,
            "message": f"Error: {str(e)}",
            "details": []
        }


@frappe.whitelist()
def sync_attendance_records(attendance_names=None, date_from=None, date_to=None):
    """
    Sync Attendance records to remote server.
    
    Args:
        attendance_names: List of specific attendance names to sync (optional)
        date_from: Start date for syncing (optional, format: YYYY-MM-DD)
        date_to: End date for syncing (optional, format: YYYY-MM-DD)
    
    Returns:
        {
            "success": true/false,
            "synced": 10,
            "failed": 2,
            "message": "Sync completed",
            "details": [...]
        }
    """
    try:
        # Build filters
        filters = {}
        
        if attendance_names:
            filters["name"] = ["in", attendance_names]
        else:
            if date_from:
                filters["attendance_date"] = [">=", date_from]
            if date_to:
                if "attendance_date" in filters:
                    filters["attendance_date"].append("<=")
                    filters["attendance_date"].append(date_to)
                else:
                    filters["attendance_date"] = ["<=", date_to]
        
        # Get attendance records
        attendances = frappe.get_all(
            "Attendance",
            filters=filters,
            fields=[
                "name", "employee", "employee_name", "attendance_date",
                "status", "working_hours", "leave_type", "shift"
            ],
            order_by="attendance_date desc"
        )
        
        if not attendances:
            return {
                "success": True,
                "synced": 0,
                "failed": 0,
                "message": "No attendance records found to sync",
                "details": []
            }
        
        synced_count = 0
        failed_count = 0
        details = []
        
        for attendance in attendances:
            try:
                # Get full attendance document
                doc = frappe.get_doc("Attendance", attendance.name)
                
                # Prepare data for remote server
                attendance_data = {
                    "employee": attendance.employee,
                    "attendance_date": str(attendance.attendance_date),
                    "status": attendance.status,
                }
                
                if attendance.working_hours:
                    attendance_data["working_hours"] = attendance.working_hours
                if attendance.leave_type:
                    attendance_data["leave_type"] = attendance.leave_type
                if attendance.shift:
                    attendance_data["shift"] = attendance.shift
                
                # Send to remote server
                result = send_to_remote_server(
                    doctype="Attendance",
                    data=attendance_data,
                    method="create"
                )
                
                if result.get("success"):
                    synced_count += 1
                    details.append({
                        "attendance": attendance.name,
                        "employee": attendance.employee,
                        "status": "success",
                        "remote_id": result.get("name")
                    })
                else:
                    failed_count += 1
                    details.append({
                        "attendance": attendance.name,
                        "employee": attendance.employee,
                        "status": "failed",
                        "error": result.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                failed_count += 1
                details.append({
                    "attendance": attendance.name,
                    "employee": attendance.employee,
                    "status": "error",
                    "error": str(e)
                })
                frappe.log_error(f"Error syncing attendance {attendance.name}: {str(e)}", "Attendance Sync")
        
        # Log sync result
        log_sync_result("Attendance", synced_count, failed_count, len(attendances))
        
        return {
            "success": True,
            "synced": synced_count,
            "failed": failed_count,
            "total": len(attendances),
            "message": f"Synced {synced_count} of {len(attendances)} attendance records",
            "details": details
        }
        
    except Exception as e:
        frappe.log_error(f"Error in sync_attendance_records: {str(e)}", "Attendance Sync")
        return {
            "success": False,
            "synced": 0,
            "failed": 0,
            "message": f"Error: {str(e)}",
            "details": []
        }


@frappe.whitelist()
def sync_selected_records(doctype, names):
    """
    Sync selected records (Employee Checkin or Attendance) to remote server.
    
    Args:
        doctype: "Employee Checkin" or "Attendance"
        names: List of record names to sync (can be string or list)
    
    Returns:
        Sync result dictionary
    """
    try:
        # Parse names if it's a string (JSON)
        if isinstance(names, str):
            try:
                names = json.loads(names)
            except:
                # If not JSON, treat as comma-separated string
                names = [n.strip() for n in names.split(",") if n.strip()]
        
        # Ensure names is a list
        if not isinstance(names, list):
            names = [names] if names else []
        
        # Log for debugging (keep title short to avoid exceeding 140 char limit)
        if len(names) > 0:
            frappe.log_error(
                f"Sync: {doctype}, {len(names)} records",
                "Attendance Sync Debug"
            )
        
        if not names:
            return {
                "success": False,
                "synced": 0,
                "failed": 0,
                "message": "No records selected for sync",
                "details": []
            }
        
        if doctype == "Employee Checkin":
            return sync_employee_checkins(checkin_names=names)
        elif doctype == "Attendance":
            return sync_attendance_records(attendance_names=names)
        else:
            return {
                "success": False,
                "synced": 0,
                "failed": 0,
                "message": f"Unsupported doctype: {doctype}",
                "details": []
            }
    except Exception as e:
        # Truncate error message to avoid exceeding log title limit
        error_msg = str(e)[:100] if len(str(e)) > 100 else str(e)
        frappe.log_error(f"Error in sync_selected_records: {error_msg}", "Attendance Sync")
        
        # Get full error in details
        full_error = str(e)
        return {
            "success": False,
            "synced": 0,
            "failed": 0,
            "message": f"Error: {full_error[:200]}",
            "details": []
        }


def send_to_remote_server(doctype, data, method=None):
    """
    Send data to remote server via API.
    
    Args:
        doctype: DocType name
        data: Data dictionary to send
        method: API method name (optional)
    
    Returns:
        {
            "success": true/false,
            "name": "remote_record_name",
            "error": "error message"
        }
    """
    try:
        # Determine API endpoint
        if doctype == "Employee Checkin":
            if method == "add_log_based_on_employee_field":
                endpoint = f"{REMOTE_SERVER_URL}/api/method/hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field"
            else:
                endpoint = f"{REMOTE_SERVER_URL}/api/resource/{doctype}"
        elif doctype == "Attendance":
            endpoint = f"{REMOTE_SERVER_URL}/api/resource/{doctype}"
        else:
            return {
                "success": False,
                "error": f"Unsupported doctype: {doctype}"
            }
        
        # Prepare headers with authentication
        # Try both token and Basic auth formats (Frappe supports both)
        # First try token format (most common)
        auth_token = f"{REMOTE_API_KEY}:{REMOTE_API_SECRET}"
        headers = {
            "Authorization": f"token {auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Make API request
        if method == "add_log_based_on_employee_field":
            # For Employee Checkin, use the method endpoint
            # The API expects employee_field_value (attendance_device_id) and timestamp
            payload = {
                "employee_field_value": data.get("employee_field_value") or data.get("employee"),
                "timestamp": data.get("timestamp") or data.get("time"),
                "log_type": data.get("log_type", "IN"),
                "device_id": data.get("device_id"),
                "skip_auto_attendance": data.get("skip_auto_attendance", 0),
            }
            if "latitude" in data:
                payload["latitude"] = data["latitude"]
            if "longitude" in data:
                payload["longitude"] = data["longitude"]
            
            # Don't log every sync to avoid spam - errors will be logged separately
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        else:
            # For other doctypes, use resource endpoint
            response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        
        # Handle response
        if response.status_code == 200:
            try:
                result = response.json()
                
                # Don't log successful responses to avoid spam
                
                if "message" in result:
                    # Check if message is a dict with name
                    if isinstance(result["message"], dict):
                        if "name" in result["message"]:
                            return {
                                "success": True,
                                "name": result["message"]["name"]
                            }
                        # If it's a dict but no name, might be the checkin doc itself
                        elif "employee" in result["message"]:
                            return {
                                "success": True,
                                "name": result["message"].get("name")
                            }
                    # Check if message is a string (could be JSON string)
                    elif isinstance(result["message"], str):
                        try:
                            msg_data = json.loads(result["message"])
                            if isinstance(msg_data, dict) and "name" in msg_data:
                                return {
                                    "success": True,
                                    "name": msg_data["name"]
                                }
                        except:
                            # If message is just a string (like the checkin name)
                            if result["message"]:
                                return {
                                    "success": True,
                                    "name": result["message"]
                                }
                
                # If we get here, the response was 200 but format is unexpected
                return {
                    "success": True,
                    "name": None,
                    "note": "Response format unexpected"
                }
            except json.JSONDecodeError:
                # Response is not JSON, might be plain text
                return {
                    "success": True,
                    "name": response.text[:100] if response.text else None
                }
        elif response.status_code == 401:
            # Authentication failed - try Basic auth as fallback
            try:
                # Try Basic authentication
                token = base64.b64encode(auth_token.encode()).decode("utf-8")
                headers_basic = {
                    "Authorization": f"Basic {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                # Retry with Basic auth
                if method == "add_log_based_on_employee_field":
                    retry_response = requests.post(endpoint, headers=headers_basic, json=payload, timeout=30)
                else:
                    retry_response = requests.post(endpoint, headers=headers_basic, json=data, timeout=30)
                
                if retry_response.status_code == 200:
                    # Basic auth worked, process response
                    try:
                        result = retry_response.json()
                        if "message" in result:
                            if isinstance(result["message"], dict) and "name" in result["message"]:
                                return {
                                    "success": True,
                                    "name": result["message"]["name"]
                                }
                            elif isinstance(result["message"], str):
                                return {
                                    "success": True,
                                    "name": result["message"]
                                }
                        return {
                            "success": True,
                            "name": None
                        }
                    except:
                        return {
                            "success": True,
                            "name": retry_response.text[:100] if retry_response.text else None
                        }
                else:
                    # Basic auth also failed, update response for error handling
                    response = retry_response
            except Exception as retry_error:
                pass  # Continue with original response error handling
        
        # Handle non-200 responses (including failed auth attempts)
        if response.status_code != 200:
            # Try to extract error message
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                
                # Log error for debugging (truncate to avoid title length issues)
                try:
                    error_summary = json.dumps(error_data)[:150] if isinstance(error_data, dict) else str(error_data)[:150]
                    frappe.log_error(
                        f"Remote API error: {error_summary[:100]}",
                        "Attendance Sync Error"
                    )
                except:
                    pass  # Don't fail if logging fails
                
                if "exc" in error_data:
                    try:
                        exc_data = json.loads(error_data["exc"])
                        if isinstance(exc_data, list) and len(exc_data) > 0:
                            error_msg = exc_data[0]
                    except:
                        if isinstance(error_data["exc"], str):
                            error_msg = error_data["exc"]
                elif "message" in error_data:
                    error_msg = error_data["message"]
                elif "_error_message" in error_data:
                    error_msg = error_data["_error_message"]
            except:
                error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
            
            # If authentication error, provide more helpful message
            if response.status_code == 401:
                error_msg = f"Authentication failed. Please verify API key and secret are correct for {REMOTE_SERVER_URL}. Original error: {error_msg[:150]}"
            
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error: {str(e)}"
        }


def log_sync_result(doctype, synced, failed, total):
    """Log sync result to Biometric Sync Log doctype"""
    try:
        # Determine status based on results
        if failed == 0 and synced > 0:
            status = "processed"
        elif synced > 0:
            status = "processed"  # Partial success is still processed
        else:
            status = "error"
        
        # Create result summary
        result_summary = {
            "sync_type": f"{doctype} Sync",
            "records_synced": synced,
            "records_failed": failed,
            "total_records": total,
            "remote_server": REMOTE_SERVER_URL
        }
        
        doc = frappe.get_doc({
            "doctype": "Biometric Sync Log",
            "timestamp": now_datetime(),  # Required field
            "status": status,  # Required field (received/processed/validation_error/error)
            "device_id": "Attendance Sync",  # Optional but useful
            "result": json.dumps(result_summary, default=str),  # Store summary in result field
            "request_data": json.dumps({
                "sync_type": f"{doctype} Sync",
                "total_records": total
            }, default=str)
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        # Don't fail the sync if logging fails
        frappe.log_error(f"Error logging sync result: {str(e)[:100]}", "Attendance Sync Log")

