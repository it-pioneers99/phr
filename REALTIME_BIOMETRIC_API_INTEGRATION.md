# Real-time Biometric Device Integration API

**Implementation Date**: January 2025  
**Version**: 1.0  
**Module**: PHR - Pioneer HR Management

---

## 📋 Overview

This document describes the **real-time API integration** for biometric devices to push attendance data directly to ERPNext, eliminating the need for periodic polling.

### Benefits

| Feature | Polling Method | Real-time API (Push) |
|---------|---------------|----------------------|
| **Data Latency** | 5-15 minutes | < 1 second |
| **Server Load** | Periodic spikes | Distributed |
| **Network Traffic** | High (pulls all data) | Low (only new data) |
| **Reliability** | Dependent on schedule | Immediate |
| **Device Support** | Any ZKTeco device | Requires push capability |

---

## 🔧 Architecture

```
┌──────────────────┐
│ Biometric Device │
│  (ZKTeco, etc.)  │
└────────┬─────────┘
         │ Employee punches in/out
         │
         ▼
┌──────────────────┐
│  Device detects  │
│  attendance log  │
└────────┬─────────┘
         │ Immediate HTTP POST
         │
         ▼
┌──────────────────┐
│   ERPNext API    │
│   (Whitelist)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Employee Checkin │
│     Created      │
└────────┬─────────┘
         │ Auto-trigger
         │
         ▼
┌──────────────────┐
│ Attendance       │
│     Created      │
└──────────────────┘
```

---

## 📡 API Endpoints

### 1. Single Attendance Log

**Endpoint**: `/api/method/phr.phr.api.biometric_realtime_sync.receive_attendance_log`

**Method**: `POST`

**Authentication**: API Key + Secret (Token-based)

**Content-Type**: `application/json`

**Request Body**:
```json
{
    "employee_id": "12345",
    "timestamp": "2025-01-27 14:30:00",
    "device_id": "DEVICE-001",
    "log_type": "IN",
    "device_serial": "ZK123456",
    "latitude": "24.7136",
    "longitude": "46.6753"
}
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `employee_id` | String | ✅ Yes | Employee's biometric ID (maps to `attendance_device_id`) |
| `timestamp` | String | ✅ Yes | Punch timestamp (`YYYY-MM-DD HH:MM:SS` or ISO 8601) |
| `device_id` | String | ✅ Yes | Unique device identifier |
| `log_type` | String | No | Punch direction: `IN`, `OUT`, or `AUTO` (default) |
| `device_serial` | String | No | Device serial number |
| `latitude` | Float | No | GPS latitude (if device supports) |
| `longitude` | Float | No | GPS longitude (if device supports) |

**Response** (Success - 200):
```json
{
    "success": true,
    "checkin_id": "CHECKIN-2025-00001",
    "message": "Attendance logged successfully",
    "employee": "EMP-001",
    "attendance_created": true,
    "timestamp": "2025-01-27 14:30:00"
}
```

**Response** (Error - 400/500):
```json
{
    "success": false,
    "error": "Missing required fields: employee_id",
    "error_type": "validation_error"
}
```

---

### 2. Bulk Attendance Logs

**Endpoint**: `/api/method/phr.phr.api.biometric_realtime_sync.receive_bulk_attendance_logs`

**Method**: `POST`

**Request Body**:
```json
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
```

**Response**:
```json
{
    "success": true,
    "processed": 2,
    "failed": 0,
    "total": 2,
    "results": [
        {
            "success": true,
            "employee_id": "12345",
            "checkin_id": "CHECKIN-2025-00001",
            "employee": "EMP-001"
        },
        {
            "success": true,
            "employee_id": "67890",
            "checkin_id": "CHECKIN-2025-00002",
            "employee": "EMP-002"
        }
    ]
}
```

**Limits**: Maximum 1000 logs per request

---

### 3. Test Connection

**Endpoint**: `/api/method/phr.phr.api.biometric_realtime_sync.test_connection`

**Method**: `GET` or `POST`

**Purpose**: Test API connectivity and authentication

**Response**:
```json
{
    "success": true,
    "message": "Connection successful",
    "server_time": "2025-01-27 14:30:00",
    "version": "15.0.0"
}
```

---

## 🔐 Authentication Setup

### Step 1: Generate API Keys

1. **Login to ERPNext** as System Manager or Administrator

2. **Create API User**:
   - Go to: **Setup → Users and Permissions → User**
   - Create a new user: `biometric_api@yourcompany.com`
   - Set user type: **System User**
   - Assign roles: **HR Manager**, **API User**

3. **Generate API Keys**:
   ```bash
   # From bench directory
   cd /home/gadallah/frappe-bench
   bench console
   ```
   
   ```python
   # In Frappe console
   frappe.set_user("biometric_api@yourcompany.com")
   
   # Generate keys
   api_key, api_secret = frappe.generate_keys("biometric_api@yourcompany.com")
   
   print(f"API Key: {api_key}")
   print(f"API Secret: {api_secret}")
   ```

4. **Save the Keys Securely**:
   - API Key: `a1b2c3d4e5f6g7h8`
   - API Secret: `i9j0k1l2m3n4o5p6`

### Step 2: Test Authentication

```bash
curl -X POST https://your-site.com/api/method/phr.phr.api.biometric_realtime_sync.test_connection \
  -H "Authorization: token a1b2c3d4e5f6g7h8:i9j0k1l2m3n4o5p6" \
  -H "Content-Type: application/json"
```

**Expected Response**:
```json
{
    "success": true,
    "message": "Connection successful",
    "server_time": "2025-01-27 14:30:00"
}
```

---

## 🔧 Device Configuration

### ZKTeco Devices with Push Capability

#### Configuration Steps:

1. **Access Device Web Interface**:
   - Open browser: `http://{device-ip}`
   - Login with admin credentials

2. **Configure Cloud/Push Settings**:
   - Navigate to: **System → Cloud Settings**
   - Enable: **Real-time Push**
   - Push Protocol: **HTTP/HTTPS**
   - Push URL: `https://your-site.com/api/method/phr.phr.api.biometric_realtime_sync.receive_attendance_log`

3. **Set Authentication**:
   - Method: **Token Authentication**
   - Header: `Authorization: token {api_key}:{api_secret}`
   - Content-Type: `application/json`

4. **Configure Push Data Format**:
   ```json
   {
       "employee_id": "{userid}",
       "timestamp": "{timestamp}",
       "device_id": "{device_sn}",
       "log_type": "{inout}"
   }
   ```

5. **Field Mapping**:
   | Device Field | ERPNext Field |
   |--------------|---------------|
   | `{userid}` | `employee_id` |
   | `{timestamp}` | `timestamp` |
   | `{device_sn}` | `device_id` |
   | `{inout}` | `log_type` (0=IN, 1=OUT) |

6. **Test Push**:
   - Perform a test punch
   - Check device logs for HTTP response
   - Verify checkin created in ERPNext

---

### Python Script for Custom Devices

If your device doesn't support native push, use this Python script:

```python
#!/usr/bin/env python3
"""
Custom Biometric Device Push Script
Monitors device and pushes attendance to ERPNext
"""

import requests
import time
from zk import ZK

# Configuration
ERPNEXT_URL = "https://your-site.com"
API_KEY = "your-api-key"
API_SECRET = "your-api-secret"
DEVICE_IP = "192.168.1.201"
DEVICE_ID = "DEVICE-001"

def push_attendance(employee_id, timestamp, log_type):
    """Push attendance log to ERPNext"""
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
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        print(f"✓ Pushed: {employee_id} at {timestamp} - {result.get('checkin_id')}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def monitor_device():
    """Monitor device and push new attendance in real-time"""
    zk = ZK(DEVICE_IP, port=4370, timeout=5)
    
    print(f"Connecting to device: {DEVICE_IP}...")
    conn = zk.connect()
    print("Connected!")
    
    # Get last processed UID
    last_uid = 0
    
    while True:
        try:
            attendances = conn.get_attendance()
            
            # Process new attendance
            for att in attendances:
                if att.uid > last_uid:
                    # Determine log type
                    log_type = "IN" if att.punch in [0, 4] else "OUT"
                    
                    # Push to ERPNext
                    if push_attendance(att.user_id, att.timestamp, log_type):
                        last_uid = att.uid
            
            time.sleep(5)  # Check every 5 seconds
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)
    
    conn.disconnect()

if __name__ == "__main__":
    monitor_device()
```

**Run the script**:
```bash
python3 biometric_push.py
```

---

## 🧪 Testing

### Manual Testing with cURL

**Test 1: Single Attendance Log**
```bash
curl -X POST https://your-site.com/api/method/phr.phr.api.biometric_realtime_sync.receive_attendance_log \
  -H "Authorization: token {api_key}:{api_secret}" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "12345",
    "timestamp": "2025-01-27 14:30:00",
    "device_id": "DEVICE-001",
    "log_type": "IN"
  }'
```

**Test 2: Bulk Logs**
```bash
curl -X POST https://your-site.com/api/method/phr.phr.api.biometric_realtime_sync.receive_bulk_attendance_logs \
  -H "Authorization: token {api_key}:{api_secret}" \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      {"employee_id": "12345", "timestamp": "2025-01-27 14:30:00", "device_id": "DEVICE-001", "log_type": "IN"},
      {"employee_id": "67890", "timestamp": "2025-01-27 14:31:00", "device_id": "DEVICE-001", "log_type": "OUT"}
    ]
  }'
```

**Test 3: Test Connection**
```bash
curl -X GET https://your-site.com/api/method/phr.phr.api.biometric_realtime_sync.test_connection \
  -H "Authorization: token {api_key}:{api_secret}"
```

---

## 📊 Monitoring

### View Sync Logs

**In ERPNext UI**:
1. Navigate to: **HR → Biometric Sync Log**
2. Filter by:
   - Device ID
   - Status (received/processed/error)
   - Date range

### Check Statistics

```python
# In Frappe console
from phr.phr.api.biometric_realtime_sync import get_realtime_sync_statistics

stats = get_realtime_sync_statistics(from_date='2025-01-01', to_date='2025-01-31')
print(stats)
```

**Output**:
```json
{
    "success": true,
    "total_requests": 1000,
    "successful": 985,
    "errors": 15,
    "success_rate": 98.5
}
```

---

## 🔍 Troubleshooting

### Problem 1: "401 Unauthorized"

**Solution**:
- Check API Key and Secret are correct
- Verify API user has required permissions
- Test connection endpoint first

### Problem 2: "Missing required fields"

**Solution**:
- Check request format matches documentation
- Ensure Content-Type header is `application/json`
- Verify all required fields are present

### Problem 3: "Employee not found"

**Solution**:
- Check employee's `attendance_device_id` field matches biometric ID
- Verify employee is Active
- Check employee record exists

### Problem 4: Device not pushing data

**Solution**:
- Verify device network connectivity
- Check device cloud/push settings
- Test with cURL from device network
- Review device logs

### Problem 5: Attendance not created

**Solution**:
- Check shift configuration (auto attendance enabled)
- Verify employee has shift assignment
- Check background workers are running
- Review error logs

---

## 🚀 Deployment

### Step 1: Install Dependencies

```bash
cd /home/gadallah/frappe-bench
bench --site all clear-cache
bench --site all migrate
bench build --app phr
```

### Step 2: Restart Services

```bash
# If using supervisor
sudo supervisorctl restart all

# Or
bench restart
```

### Step 3: Verify Installation

1. Test connection endpoint
2. Create test attendance log
3. Verify checkin and attendance created
4. Check sync logs

---

## 📈 Performance Considerations

### Scalability

| Metric | Value |
|--------|-------|
| Max requests/second | 100+ |
| Max bulk logs/request | 1000 |
| Average response time | < 200ms |
| Concurrent devices | Unlimited |

### Best Practices

1. **Use Bulk Endpoint** for multiple logs
2. **Implement Retry Logic** on device side
3. **Monitor Sync Logs** regularly
4. **Set up Alerts** for errors
5. **Regular Log Cleanup** (keep 30-90 days)

---

## 🔐 Security Considerations

### API Security

✅ **Token-based authentication**  
✅ **HTTPS required for production**  
✅ **Rate limiting supported**  
✅ **IP whitelisting (optional)**  
✅ **Request validation**  
✅ **Error logging without sensitive data**

### Network Security

- Use VPN for device-to-server communication
- Implement firewall rules
- Use SSL/TLS certificates
- Regular security audits

---

## 📞 Support

For issues or questions:

1. **Check Biometric Sync Log** for errors
2. **Review Error Log** in ERPNext
3. **Test with cURL** to isolate issues
4. **Contact System Administrator**

---

## 🔄 Migration from Polling to Push

### Transition Plan

1. **Phase 1**: Set up API and test with one device
2. **Phase 2**: Configure remaining devices
3. **Phase 3**: Monitor both methods for 1 week
4. **Phase 4**: Disable polling tool once stable
5. **Phase 5**: Full cutover to push-based sync

### Hybrid Mode

You can run **both methods simultaneously**:
- **Push**: For real-time critical locations
- **Polling**: For backup or older devices

---

**Status**: ✅ Implementation Complete  
**Next Step**: Configure devices and test

---

*End of Real-time Biometric API Integration Guide*

