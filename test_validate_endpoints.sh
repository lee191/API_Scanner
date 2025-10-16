#!/bin/bash

# API Endpoint Validation Script
# Total endpoints: 4

echo '=== API Endpoint Validation ==='
echo ''

PASS=0
FAIL=0
TOTAL=0

# Test 1: GET http://example.com/api/users
echo 'Testing endpoint 1/4: GET http://example.com/api/users'
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X GET 'http://example.com/api/users?id=123&name=john')
TOTAL=$((TOTAL + 1))

if [ $HTTP_CODE -ge 200 ] && [ $HTTP_CODE -lt 400 ]; then
  echo '  ✓ PASS (HTTP $HTTP_CODE)'
  PASS=$((PASS + 1))
else
  echo '  ✗ FAIL (HTTP $HTTP_CODE)'
  FAIL=$((FAIL + 1))
fi
echo ''

# Test 2: POST http://example.com/api/users
echo 'Testing endpoint 2/4: POST http://example.com/api/users'
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer token123' \
  -d '{"name": "John Doe", "email": "john@example.com"}' http://example.com/api/users)
TOTAL=$((TOTAL + 1))

if [ $HTTP_CODE -ge 200 ] && [ $HTTP_CODE -lt 400 ]; then
  echo '  ✓ PASS (HTTP $HTTP_CODE)'
  PASS=$((PASS + 1))
else
  echo '  ✗ FAIL (HTTP $HTTP_CODE)'
  FAIL=$((FAIL + 1))
fi
echo ''

# Test 3: PUT http://example.com/api/users/123
echo 'Testing endpoint 3/4: PUT http://example.com/api/users/123'
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' \
  -X PUT \
  -d name=john \
  -d status=active http://example.com/api/users/123)
TOTAL=$((TOTAL + 1))

if [ $HTTP_CODE -ge 200 ] && [ $HTTP_CODE -lt 400 ]; then
  echo '  ✓ PASS (HTTP $HTTP_CODE)'
  PASS=$((PASS + 1))
else
  echo '  ✗ FAIL (HTTP $HTTP_CODE)'
  FAIL=$((FAIL + 1))
fi
echo ''

# Test 4: DELETE http://example.com/api/users
echo 'Testing endpoint 4/4: DELETE http://example.com/api/users'
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' \
  -X DELETE \
  -H 'Authorization: Bearer token123' 'http://example.com/api/users?id=123')
TOTAL=$((TOTAL + 1))

if [ $HTTP_CODE -ge 200 ] && [ $HTTP_CODE -lt 400 ]; then
  echo '  ✓ PASS (HTTP $HTTP_CODE)'
  PASS=$((PASS + 1))
else
  echo '  ✗ FAIL (HTTP $HTTP_CODE)'
  FAIL=$((FAIL + 1))
fi
echo ''

echo '=== Validation Summary ==='
echo "Total: $TOTAL"
echo "Passed: $PASS"
echo "Failed: $FAIL"

if [ $FAIL -eq 0 ]; then
  echo '✓ All endpoints validated successfully!'
  exit 0
else
  echo '✗ Some endpoints failed validation'
  exit 1
fi