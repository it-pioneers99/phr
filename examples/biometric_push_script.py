#!/usr/bin/env python3
"""
Real-time Biometric Device Push Script
======================================

This script monitors a biometric device and pushes attendance logs
to ERPNext in real-time using the push API.

Usage:
    python biometric_push_script.py

Requirements:
    pip install pyzk requests

Configuration:
    Edit the variables below with your ERPNext and device details.
"""

import requests
import time
import sys
from datetime import datetime
from zk import ZK

# ============================================
# CONFIGURATION
# ============================================

# ERPNext Configuration
ERPNEXT_URL = "https://your-site.com"  # Your ERPNext URL
API_KEY = "your-api-key"                # Generated from ERPNext
API_SECRET = "your-api-secret"          # Generated from ERPNext

# Biometric Device Configuration
DEVICE_IP = "192.168.1.201"             # Device IP address
DEVICE_PORT = 4370                      # Default ZKTeco port
DEVICE_ID = "DEVICE-001"                # Unique device identifier
DEVICE_TIMEOUT = 5                      # Connection timeout in seconds

# Sync Configuration
POLL_INTERVAL = 5                       # Check for new logs every N seconds
PUSH_BATCH_SIZE = 50                    # Max logs to push at once

# Log Type Mapping (ZKTeco punch values)
PUNCH_VALUES_IN = [0, 4]                # Punch values for IN
PUNCH_VALUES_OUT = [1, 5]               # Punch values for OUT

# ============================================
# API FUNCTIONS
# ============================================

def push_single_attendance(employee_id, timestamp, log_type):
    """
    Push a single attendance log to ERPNext.
    
    Args:
        employee_id: Employee's biometric ID
        timestamp: Datetime object
        log_type: "IN", "OUT", or "AUTO"
    
    Returns:
        dict: API response or None if error
    """
    url = f"{ERPNEXT_URL}/api/method/phr.phr.api.biometric_realtime_sync.receive_attendance_log"
    
    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}",
        "Content-Type": "application/json"
    }
    
    data = {
        "employee_id": str(employee_id),
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "device_id": DEVICE_ID,
        "log_type": log_type
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            print(f"✓ [{datetime.now().strftime('%H:%M:%S')}] Pushed: {employee_id} at {timestamp} -> {result.get('checkin_id')}")
            return result
        else:
            print(f"✗ [{datetime.now().strftime('%H:%M:%S')}] Failed: {result.get('error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"✗ [{datetime.now().strftime('%H:%M:%S')}] Network Error: {e}")
        return None
    except Exception as e:
        print(f"✗ [{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        return None


def push_bulk_attendance(logs):
    """
    Push multiple attendance logs to ERPNext in one request.
    
    Args:
        logs: List of log dictionaries
    
    Returns:
        dict: API response or None if error
    """
    url = f"{ERPNEXT_URL}/api/method/phr.phr.api.biometric_realtime_sync.receive_bulk_attendance_logs"
    
    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}",
        "Content-Type": "application/json"
    }
    
    data = {"logs": logs}
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            print(f"✓ [{datetime.now().strftime('%H:%M:%S')}] Bulk Push: {result.get('processed')} success, {result.get('failed')} failed")
            return result
        else:
            print(f"✗ [{datetime.now().strftime('%H:%M:%S')}] Bulk Failed: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"✗ [{datetime.now().strftime('%H:%M:%S')}] Bulk Error: {e}")
        return None


def test_connection():
    """Test API connectivity and authentication."""
    url = f"{ERPNEXT_URL}/api/method/phr.phr.api.biometric_realtime_sync.test_connection"
    
    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            print(f"✓ API Connection: OK (Server Time: {result.get('server_time')})")
            return True
        else:
            print(f"✗ API Connection: Failed")
            return False
            
    except Exception as e:
        print(f"✗ API Connection Error: {e}")
        return False


# ============================================
# DEVICE MONITORING
# ============================================

def get_log_type(punch_value):
    """Determine log type from punch value."""
    if punch_value in PUNCH_VALUES_IN:
        return "IN"
    elif punch_value in PUNCH_VALUES_OUT:
        return "OUT"
    else:
        return "AUTO"


def monitor_device_realtime():
    """
    Monitor biometric device and push new attendance logs in real-time.
    Uses continuous polling with configurable interval.
    """
    print("=" * 60)
    print("Real-time Biometric Push Sync")
    print("=" * 60)
    print(f"Device: {DEVICE_IP}:{DEVICE_PORT}")
    print(f"ERPNext: {ERPNEXT_URL}")
    print(f"Poll Interval: {POLL_INTERVAL} seconds")
    print("=" * 60)
    
    # Test API connection first
    print("\n1. Testing API Connection...")
    if not test_connection():
        print("\n✗ Cannot connect to ERPNext API. Please check configuration.")
        sys.exit(1)
    
    # Connect to device
    print(f"\n2. Connecting to biometric device: {DEVICE_IP}...")
    zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=DEVICE_TIMEOUT)
    
    try:
        conn = zk.connect()
        print(f"✓ Connected to device!")
        
        # Get device info
        firmware = conn.get_firmware_version()
        print(f"  Firmware: {firmware}")
        
    except Exception as e:
        print(f"✗ Cannot connect to device: {e}")
        sys.exit(1)
    
    # Main monitoring loop
    print(f"\n3. Starting real-time monitoring...")
    print(f"   Press Ctrl+C to stop\n")
    
    last_uid = 0
    pending_logs = []
    
    try:
        while True:
            try:
                # Get all attendance logs from device
                attendances = conn.get_attendance()
                
                # Process new logs
                new_logs = [att for att in attendances if att.uid > last_uid]
                
                if new_logs:
                    for att in new_logs:
                        log_type = get_log_type(att.punch)
                        
                        # Prepare log data
                        log_data = {
                            "employee_id": str(att.user_id),
                            "timestamp": att.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "device_id": DEVICE_ID,
                            "log_type": log_type
                        }
                        
                        # Option 1: Push immediately (real-time)
                        result = push_single_attendance(
                            att.user_id,
                            att.timestamp,
                            log_type
                        )
                        
                        if result:
                            last_uid = att.uid
                        
                        # Option 2: Batch push (uncomment to use)
                        # pending_logs.append(log_data)
                        # if len(pending_logs) >= PUSH_BATCH_SIZE:
                        #     push_bulk_attendance(pending_logs)
                        #     pending_logs = []
                        #     last_uid = att.uid
                
                # Sleep before next check
                time.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"✗ Error in monitoring loop: {e}")
                time.sleep(10)  # Wait before retry
        
    except KeyboardInterrupt:
        print(f"\n\n✓ Monitoring stopped by user")
    finally:
        # Disconnect from device
        if conn:
            conn.disconnect()
            print("✓ Disconnected from device")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    try:
        monitor_device_realtime()
    except Exception as e:
        print(f"\n✗ Fatal Error: {e}")
        sys.exit(1)

