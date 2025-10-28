#!/bin/bash

# ==============================================
# ERPNext Biometric API Test Script
# ==============================================
# This script tests the real-time biometric API endpoints
#
# Usage:
#   ./test_api.sh
#
# Before running:
#   1. Edit the configuration below
#   2. Make executable: chmod +x test_api.sh

# ==============================================
# CONFIGURATION
# ==============================================

# ERPNext URL and Credentials
ERPNEXT_URL="https://your-site.com"
API_KEY="your-api-key"
API_SECRET="your-api-secret"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==============================================
# HELPER FUNCTIONS
# ==============================================

print_header() {
    echo ""
    echo "=============================================="
    echo "$1"
    echo "=============================================="
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# ==============================================
# TEST FUNCTIONS
# ==============================================

test_connection() {
    print_header "Test 1: Connection Test"
    
    response=$(curl -s -X GET "${ERPNEXT_URL}/api/method/phr.phr.api.biometric_realtime_sync.test_connection" \
        -H "Authorization: token ${API_KEY}:${API_SECRET}")
    
    echo "Response: $response"
    
    if echo "$response" | grep -q '"success": true'; then
        print_success "Connection test passed"
        return 0
    else
        print_error "Connection test failed"
        return 1
    fi
}

test_single_attendance() {
    print_header "Test 2: Single Attendance Log"
    
    # Generate current timestamp
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    response=$(curl -s -X POST "${ERPNEXT_URL}/api/method/phr.phr.api.biometric_realtime_sync.receive_attendance_log" \
        -H "Authorization: token ${API_KEY}:${API_SECRET}" \
        -H "Content-Type: application/json" \
        -d "{
            \"employee_id\": \"TEST001\",
            \"timestamp\": \"${TIMESTAMP}\",
            \"device_id\": \"TEST-DEVICE\",
            \"log_type\": \"IN\"
        }")
    
    echo "Response: $response"
    
    if echo "$response" | grep -q '"success": true'; then
        print_success "Single attendance log test passed"
        CHECKIN_ID=$(echo "$response" | grep -o '"checkin_id": "[^"]*"' | cut -d'"' -f4)
        print_info "Checkin ID: $CHECKIN_ID"
        return 0
    else
        print_error "Single attendance log test failed"
        return 1
    fi
}

test_bulk_attendance() {
    print_header "Test 3: Bulk Attendance Logs"
    
    # Generate timestamps
    TIMESTAMP1=$(date '+%Y-%m-%d %H:%M:%S')
    sleep 1
    TIMESTAMP2=$(date '+%Y-%m-%d %H:%M:%S')
    
    response=$(curl -s -X POST "${ERPNEXT_URL}/api/method/phr.phr.api.biometric_realtime_sync.receive_bulk_attendance_logs" \
        -H "Authorization: token ${API_KEY}:${API_SECRET}" \
        -H "Content-Type: application/json" \
        -d "{
            \"logs\": [
                {
                    \"employee_id\": \"TEST001\",
                    \"timestamp\": \"${TIMESTAMP1}\",
                    \"device_id\": \"TEST-DEVICE\",
                    \"log_type\": \"IN\"
                },
                {
                    \"employee_id\": \"TEST002\",
                    \"timestamp\": \"${TIMESTAMP2}\",
                    \"device_id\": \"TEST-DEVICE\",
                    \"log_type\": \"OUT\"
                }
            ]
        }")
    
    echo "Response: $response"
    
    if echo "$response" | grep -q '"success": true'; then
        print_success "Bulk attendance logs test passed"
        PROCESSED=$(echo "$response" | grep -o '"processed": [0-9]*' | cut -d' ' -f2)
        print_info "Processed: $PROCESSED logs"
        return 0
    else
        print_error "Bulk attendance logs test failed"
        return 1
    fi
}

test_invalid_data() {
    print_header "Test 4: Invalid Data (Should Fail)"
    
    response=$(curl -s -X POST "${ERPNEXT_URL}/api/method/phr.phr.api.biometric_realtime_sync.receive_attendance_log" \
        -H "Authorization: token ${API_KEY}:${API_SECRET}" \
        -H "Content-Type: application/json" \
        -d "{
            \"employee_id\": \"TEST001\"
        }")
    
    echo "Response: $response"
    
    if echo "$response" | grep -q '"success": false'; then
        print_success "Invalid data test passed (correctly rejected)"
        return 0
    else
        print_error "Invalid data test failed (should have been rejected)"
        return 1
    fi
}

test_invalid_auth() {
    print_header "Test 5: Invalid Authentication (Should Fail)"
    
    response=$(curl -s -X GET "${ERPNEXT_URL}/api/method/phr.phr.api.biometric_realtime_sync.test_connection" \
        -H "Authorization: token invalid:credentials")
    
    echo "Response: $response"
    
    if echo "$response" | grep -q "Authentication failed\|Invalid API key\|Unauthorized"; then
        print_success "Invalid auth test passed (correctly rejected)"
        return 0
    else
        print_error "Invalid auth test failed"
        return 1
    fi
}

# ==============================================
# MAIN EXECUTION
# ==============================================

main() {
    print_header "ERPNext Biometric API Test Suite"
    echo "Target: $ERPNEXT_URL"
    echo ""
    
    # Check if configuration is set
    if [ "$ERPNEXT_URL" == "https://your-site.com" ]; then
        print_error "Please configure ERPNEXT_URL, API_KEY, and API_SECRET in this script"
        exit 1
    fi
    
    # Run tests
    PASSED=0
    FAILED=0
    
    if test_connection; then
        ((PASSED++))
    else
        ((FAILED++))
        print_error "Connection test failed. Cannot continue."
        exit 1
    fi
    
    if test_single_attendance; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
    
    if test_bulk_attendance; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
    
    if test_invalid_data; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
    
    if test_invalid_auth; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
    
    # Summary
    print_header "Test Summary"
    echo -e "Tests Passed: ${GREEN}$PASSED${NC}"
    echo -e "Tests Failed: ${RED}$FAILED${NC}"
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        print_success "All tests passed!"
        exit 0
    else
        print_error "Some tests failed"
        exit 1
    fi
}

# Run main function
main

