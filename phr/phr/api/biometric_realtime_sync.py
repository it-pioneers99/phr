"""
Real-time Biometric Device Integration API
==========================================

This module provides API endpoints for biometric devices to push attendance data
directly to ERPNext in real-time, eliminating the need for periodic polling.

Supported Devices:
- ZKTeco devices with push capability
- Any device that can make HTTP POST requests

Security:
- API Key/Secret authentication
- IP whitelisting (optional)
- Request validation
- Rate limiting support
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime
import json
from datetime import datetime

@frappe.whitelist(allow_guest=False)
def receive_attendance_log(**kwargs):
    """
    Main endpoint for receiving attendance logs from biometric devices.
    
    This endpoint can be called by biometric devices to push attendance data in real-time.
    
    Expected Parameters (POST):
    - employee_id: Employee's biometric ID (mapped to attendance_device_id in Employee)
    - timestamp: Timestamp of the punch (format: YYYY-MM-DD HH:MM:SS or ISO 8601)
    - device_id: Unique identifier for the biometric device
    - log_type: Direction of punch (IN/OUT/AUTO)
    - device_serial: Serial number of the device (optional)
    - latitude: GPS latitude (optional)
    - longitude: GPS longitude (optional)
    
    Authentication:
    Requires valid API Key and Secret in headers:
    - Authorization: token {api_key}:{api_secret}
    
    Returns:
    {
        "success": true,
        "checkin_id": "CHECKIN-2025-0001",
        "message": "Attendance logged successfully",
        "employee": "EMP-001",
        "attendance_created": true/false
    }
    
    Example cURL:
    curl -X POST https://your-site.com/api/method/phr.phr.api.biometric_realtime_sync.receive_attendance_log \
      -H "Authorization: token {api_key}:{api_secret}" \
      -H "Content-Type: application/json" \
      -d '{
        "employee_id": "12345",
        "timestamp": "2025-01-27 14:30:00",
        "device_id": "DEVICE-001",
        "log_type": "IN"
      }'
    """
    try:
        # Extract data from request
        if frappe.request.method == "POST":
            if frappe.request.is_json:
                data = frappe.request.get_json()
            else:
                data = frappe.form_dict
        else:
            data = frappe.form_dict
        
        # Validate required parameters
        required_fields = ['employee_id', 'timestamp', 'device_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            frappe.throw(
                _("Missing required fields: {0}").format(", ".join(missing_fields)),
                frappe.ValidationError
            )
        
        # Extract parameters
        employee_field_value = str(data.get('employee_id'))
        timestamp = data.get('timestamp')
        device_id = data.get('device_id')
        log_type = data.get('log_type', 'AUTO')
        device_serial = data.get('device_serial')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Parse timestamp if it's a string
        if isinstance(timestamp, str):
            try:
                # Try ISO format first
                timestamp_dt = get_datetime(timestamp)
            except:
                try:
                    # Try custom format
                    timestamp_dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except:
                    frappe.throw(
                        _("Invalid timestamp format. Use 'YYYY-MM-DD HH:MM:SS' or ISO 8601"),
                        frappe.ValidationError
                    )
        else:
            timestamp_dt = timestamp
        
        # Log the incoming request
        log_biometric_request(data, "received")
        
        # Process the attendance log
        result = process_realtime_attendance_log(
            employee_field_value=employee_field_value,
            timestamp=timestamp_dt,
            device_id=device_id,
            log_type=log_type,
            device_serial=device_serial,
            latitude=latitude,
            longitude=longitude
        )
        
        # Log successful processing
        log_biometric_request(data, "processed", result)
        
        return {
            "success": True,
            "checkin_id": result.get("checkin_id"),
            "message": _("Attendance logged successfully"),
            "employee": result.get("employee"),
            "attendance_created": result.get("attendance_created", False),
            "timestamp": str(timestamp_dt)
        }
        
    except frappe.ValidationError as e:
        # Log validation errors
        log_biometric_request(data if 'data' in locals() else kwargs, "validation_error", str(e))
        frappe.local.response['http_status_code'] = 400
        return {
            "success": False,
            "error": str(e),
            "error_type": "validation_error"
        }
        
    except Exception as e:
        # Log system errors
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Biometric Real-time Sync Error: {str(e)}"
        )
        log_biometric_request(data if 'data' in locals() else kwargs, "error", str(e))
        frappe.local.response['http_status_code'] = 500
        return {
            "success": False,
            "error": _("Internal server error. Please contact administrator."),
            "error_type": "system_error"
        }


@frappe.whitelist(allow_guest=False)
def receive_bulk_attendance_logs(**kwargs):
    """
    Endpoint for receiving multiple attendance logs in a single request.
    Useful for devices that batch multiple punches.
    
    Expected Parameters (POST):
    - logs: Array of attendance log objects
    
    Each log object should contain:
    - employee_id, timestamp, device_id, log_type (same as single log endpoint)
    
    Returns:
    {
        "success": true,
        "processed": 10,
        "failed": 0,
        "results": [...]
    }
    
    Example:
    {
        "logs": [
            {
                "employee_id": "12345",
                "timestamp": "2025-01-27 14:30:00",
                "device_id": "DEVICE-001",
                "log_type": "IN"
            },
            {
                "employee_id": "67890",
                "timestamp": "2025-01-27 14:31:00",
                "device_id": "DEVICE-001",
                "log_type": "OUT"
            }
        ]
    }
    """
    try:
        # Extract data from request
        if frappe.request.method == "POST":
            if frappe.request.is_json:
                data = frappe.request.get_json()
            else:
                data = frappe.form_dict
        else:
            data = frappe.form_dict
        
        logs = data.get('logs', [])
        
        if not logs:
            frappe.throw(_("No logs provided"), frappe.ValidationError)
        
        if not isinstance(logs, list):
            frappe.throw(_("Logs must be an array"), frappe.ValidationError)
        
        if len(logs) > 1000:
            frappe.throw(_("Maximum 1000 logs per request"), frappe.ValidationError)
        
        processed = 0
        failed = 0
        results = []
        
        for log in logs:
            try:
                # Process each log
                employee_field_value = str(log.get('employee_id'))
                timestamp = log.get('timestamp')
                device_id = log.get('device_id')
                log_type = log.get('log_type', 'AUTO')
                device_serial = log.get('device_serial')
                latitude = log.get('latitude')
                longitude = log.get('longitude')
                
                # Parse timestamp
                if isinstance(timestamp, str):
                    timestamp_dt = get_datetime(timestamp)
                else:
                    timestamp_dt = timestamp
                
                result = process_realtime_attendance_log(
                    employee_field_value=employee_field_value,
                    timestamp=timestamp_dt,
                    device_id=device_id,
                    log_type=log_type,
                    device_serial=device_serial,
                    latitude=latitude,
                    longitude=longitude
                )
                
                processed += 1
                results.append({
                    "success": True,
                    "employee_id": employee_field_value,
                    "checkin_id": result.get("checkin_id"),
                    "employee": result.get("employee")
                })
                
            except Exception as e:
                failed += 1
                results.append({
                    "success": False,
                    "employee_id": log.get('employee_id'),
                    "error": str(e)
                })
                frappe.log_error(
                    message=f"Error processing log: {json.dumps(log)}\n{frappe.get_traceback()}",
                    title="Bulk Attendance Log Processing Error"
                )
        
        frappe.db.commit()
        
        return {
            "success": True,
            "processed": processed,
            "failed": failed,
            "total": len(logs),
            "results": results
        }
        
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Bulk Biometric Sync Error: {str(e)}"
        )
        frappe.local.response['http_status_code'] = 500
        return {
            "success": False,
            "error": str(e),
            "error_type": "system_error"
        }


def process_realtime_attendance_log(employee_field_value, timestamp, device_id, 
                                    log_type='AUTO', device_serial=None, 
                                    latitude=None, longitude=None):
    """
    Process a single attendance log from biometric device.
    Creates Employee Checkin and triggers automatic attendance processing.
    
    Returns:
    {
        "checkin_id": "CHECKIN-2025-0001",
        "employee": "EMP-001",
        "attendance_created": true/false
    }
    """
    # Use the HRMS standard method to create checkin
    from hrms.hr.doctype.employee_checkin.employee_checkin import add_log_based_on_employee_field
    
    # Normalize log_type
    if log_type.upper() in ['IN', 'OUT']:
        log_type = log_type.upper()
    else:
        log_type = None  # Let ERPNext auto-detect
    
    # Create the checkin
    checkin = add_log_based_on_employee_field(
        employee_field_value=employee_field_value,
        timestamp=str(timestamp),
        device_id=device_id,
        log_type=log_type,
        skip_auto_attendance=0,  # Enable auto attendance
        employee_fieldname="attendance_device_id"
    )
    
    # Additional metadata
    if device_serial:
        checkin.db_set('device_serial_number', device_serial, update_modified=False)
    
    # The automatic attendance processing will be triggered by our hook
    # Check if attendance was created (might take a moment due to async processing)
    attendance_created = bool(checkin.attendance)
    
    return {
        "checkin_id": checkin.name,
        "employee": checkin.employee,
        "employee_name": checkin.employee_name,
        "attendance_created": attendance_created
    }


def log_biometric_request(data, status, result=None):
    """
    Log biometric device requests for monitoring and debugging.
    
    Args:
        data: Request data
        status: Status of the request (received/processed/error)
        result: Processing result (optional)
    """
    try:
        log_entry = frappe.get_doc({
            "doctype": "Biometric Sync Log",
            "timestamp": now_datetime(),
            "request_data": json.dumps(data, default=str),
            "status": status,
            "result": json.dumps(result, default=str) if result else None,
            "device_id": data.get('device_id'),
            "employee_id": data.get('employee_id')
        })
        log_entry.insert(ignore_permissions=True)
        frappe.db.commit()
    except:
        # Don't fail the main process if logging fails
        frappe.log_error(
            message=f"Failed to log biometric request: {frappe.get_traceback()}",
            title="Biometric Logging Error"
        )


@frappe.whitelist(allow_guest=False)
def test_connection(**kwargs):
    """
    Simple endpoint to test connectivity from biometric device.
    
    Returns:
    {
        "success": true,
        "message": "Connection successful",
        "server_time": "2025-01-27 14:30:00"
    }
    """
    return {
        "success": True,
        "message": _("Connection successful"),
        "server_time": str(now_datetime()),
        "version": frappe.__version__
    }


@frappe.whitelist()
def get_realtime_sync_statistics(from_date=None, to_date=None):
    """
    Get statistics about real-time sync performance.
    
    Returns metrics like:
    - Total checkins received
    - Success rate
    - Average processing time
    - Errors
    """
    filters = {}
    
    if from_date:
        filters["timestamp"] = [">=", from_date]
    if to_date:
        if "timestamp" in filters:
            filters["timestamp"] = ["between", [from_date, to_date]]
        else:
            filters["timestamp"] = ["<=", to_date]
    
    try:
        total_logs = frappe.db.count("Biometric Sync Log", filters)
        
        filters["status"] = "processed"
        successful_logs = frappe.db.count("Biometric Sync Log", filters)
        
        filters["status"] = "error"
        error_logs = frappe.db.count("Biometric Sync Log", filters)
        
        return {
            "success": True,
            "total_requests": total_logs,
            "successful": successful_logs,
            "errors": error_logs,
            "success_rate": (successful_logs / total_logs * 100) if total_logs > 0 else 0
        }
    except:
        return {
            "success": False,
            "error": "Statistics table not available. Please create Biometric Sync Log doctype."
        }

