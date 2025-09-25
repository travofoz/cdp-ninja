# CDP-Ninja Bug Report

## Console Clear Endpoint Not Working

**Issue**: The `/cdp/console/clear` endpoint returns 405 Method Not Allowed

**Root Cause**:
- There are two conflicting route definitions for `/cdp/console/clear`:
  1. In `server.py` line ~XXX - registered without methods (defaults to GET only)
  2. In `routes/debugging.py` line ~XXX - registered with POST method

**Impact**:
- Console cannot be cleared via the documented API endpoint
- Both GET and POST requests fail with 405 errors

**Fix**:
- Remove the duplicate route registration in `server.py`
- OR update the server.py registration to support POST method
- Ensure only one route handler exists for this endpoint

**Workaround**:
- Use `/cdp/execute` endpoint with `{"code": "console.clear()"}` to clear console
- This bypasses the broken clear endpoint

**Files to check**:
- `/root/dev/cdp-ninja/cdp_ninja/server.py`
- `/root/dev/cdp-ninja/cdp_ninja/routes/debugging.py`

Priority: Medium (workaround exists but API documentation is incorrect)