"""
Biometric Sync Service Control API
==================================

This module provides API endpoints to start, stop, and check the status
of the biometric attendance sync service.

The sync service can be:
- A systemd service (recommended)
- A running Python process
- A cron job (status only)
"""

import frappe
from frappe import _
import subprocess
import os
import json
from pathlib import Path


@frappe.whitelist()
def get_sync_status():
    """
    Get the current status of the biometric sync service.
    
    Returns:
    {
        "running": true/false,
        "service_name": "attendance-sync",
        "last_sync": "2025-01-27 14:30:00",
        "message": "Service is running"
    }
    """
    try:
        # Check for systemd service
        service_name = "attendance-sync"
        status = check_systemd_service(service_name)
        
        if status:
            return {
                "running": True,
                "service_name": service_name,
                "last_sync": get_last_sync_time(),
                "message": f"Service '{service_name}' is running",
                "method": "systemd"
            }
        
        # Check for running process
        process_status = check_running_process()
        if process_status["running"]:
            return {
                "running": True,
                "service_name": None,
                "last_sync": get_last_sync_time(),
                "message": "Sync process is running",
                "method": "process",
                "pid": process_status.get("pid")
            }
        
        return {
            "running": False,
            "service_name": service_name,
            "last_sync": get_last_sync_time(),
            "message": "Biometric sync service is not running",
            "method": None
        }
        
    except Exception as e:
        frappe.log_error(f"Error checking sync status: {str(e)}", "Biometric Sync Status")
        return {
            "running": False,
            "message": f"Error checking status: {str(e)}"
        }


@frappe.whitelist()
def start_sync():
    """
    Start the biometric sync service.
    
    Returns:
    {
        "success": true/false,
        "message": "Service started successfully"
    }
    """
    try:
        # Try systemd first
        service_name = "attendance-sync"
        
        # Check if systemd service exists and try to start it
        try:
            # First check if service exists (without sudo)
            result = subprocess.run(
                ["systemctl", "status", service_name],
                capture_output=True,
                timeout=5
            )
            
            # If service exists (returncode 0 or 3 means service exists)
            if result.returncode in [0, 3]:
                # Try without sudo first (if user has permissions)
                try:
                    result = subprocess.run(
                        ["systemctl", "start", service_name],
                        capture_output=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "message": f"Service '{service_name}' started successfully",
                            "method": "systemd"
                        }
                except:
                    pass
                
                # If that fails, skip systemd and use process method instead
                # (We don't use sudo to avoid password prompts)
                frappe.log_error(
                    f"Could not start systemd service '{service_name}' (may require sudo). Falling back to process method.",
                    "Biometric Sync Start"
                )
        except Exception as e:
            frappe.log_error(f"Systemd check error: {str(e)}", "Biometric Sync Start")
        
        # Try starting Python process directly
        sync_script_path = "/home/gadallah/frappe-bench/biometric-attendance-sync-tool/erpnext_sync.py"
        
        if os.path.exists(sync_script_path):
            # Check if already running
            if check_running_process()["running"]:
                return {
                    "success": False,
                    "message": "Sync process is already running"
                }
            
            # Start as background process
            try:
                # Use nohup to run in background
                subprocess.Popen(
                    ["python3", sync_script_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                
                return {
                    "success": True,
                    "message": "Biometric sync process started",
                    "method": "process"
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Failed to start process: {str(e)}"
                }
        else:
            return {
                "success": False,
                "message": f"Sync script not found at {sync_script_path}"
            }
            
    except Exception as e:
        frappe.log_error(f"Error starting sync: {str(e)}", "Biometric Sync Start")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@frappe.whitelist()
def stop_sync():
    """
    Stop the biometric sync service.
    
    Returns:
    {
        "success": true/false,
        "message": "Service stopped successfully"
    }
    """
    try:
        # Try systemd first
        service_name = "attendance-sync"
        
        try:
            # Check if service exists and try to stop it
            result = subprocess.run(
                ["systemctl", "status", service_name],
                capture_output=True,
                timeout=5
            )
            
            # If service exists (returncode 0 or 3 means service exists)
            if result.returncode in [0, 3]:
                # Try without sudo first (if user has permissions)
                try:
                    result = subprocess.run(
                        ["systemctl", "stop", service_name],
                        capture_output=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "message": f"Service '{service_name}' stopped successfully",
                            "method": "systemd"
                        }
                except:
                    pass
                
                # If that fails, continue to process method
                # (We don't use sudo to avoid password prompts)
                frappe.log_error(
                    f"Could not stop systemd service '{service_name}' (may require sudo). Trying process method.",
                    "Biometric Sync Stop"
                )
        except Exception as e:
            frappe.log_error(f"Systemd stop error: {str(e)}", "Biometric Sync Stop")
        
        # Stop running Python processes
        process_status = check_running_process()
        if process_status["running"]:
            try:
                pid = process_status["pid"]
                subprocess.run(["kill", "-15", str(pid)], timeout=10)
                
                # Wait a bit and check
                import time
                time.sleep(2)
                
                if not check_running_process()["running"]:
                    return {
                        "success": True,
                        "message": f"Sync process (PID {pid}) stopped successfully",
                        "method": "process"
                    }
                else:
                    # Force kill if graceful stop didn't work
                    subprocess.run(["kill", "-9", str(pid)], timeout=5)
                    return {
                        "success": True,
                        "message": f"Sync process (PID {pid}) force stopped",
                        "method": "process"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Failed to stop process: {str(e)}"
                }
        
        return {
            "success": False,
            "message": "No running sync service found"
        }
        
    except Exception as e:
        frappe.log_error(f"Error stopping sync: {str(e)}", "Biometric Sync Stop")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def check_systemd_service(service_name):
    """Check if systemd service is running"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0 and result.stdout.decode().strip() == "active"
    except:
        return False


def check_running_process():
    """Check if sync process is running"""
    try:
        sync_script = "erpnext_sync.py"
        result = subprocess.run(
            ["pgrep", "-f", sync_script],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            pid = int(result.stdout.decode().strip().split('\n')[0])
            return {"running": True, "pid": pid}
        
        return {"running": False, "pid": None}
    except:
        return {"running": False, "pid": None}


def get_last_sync_time():
    """Get last sync time from status file"""
    try:
        status_file = "/home/gadallah/frappe-bench/biometric-attendance-sync-tool/logs/status.json"
        
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status_data = json.load(f)
                last_sync = status_data.get('lift_off_timestamp')
                if last_sync:
                    # Parse and format
                    from datetime import datetime
                    try:
                        dt = datetime.strptime(last_sync, "%Y-%m-%d %H:%M:%S.%f")
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        return last_sync
        
        return None
    except:
        return None

