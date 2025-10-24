# Path Tracking Validation Guide

## Overview

This document provides guidance on validating Path Tracking implementation during usability testing. Path Tracking is critical for measuring Time To Value (TTV) and understanding user journeys.

---

## Expected Path Tracking Events

### Core Events

| Event Name | Trigger | Expected Data | Priority |
|------------|---------|---------------|----------|
| `user_login` | User successfully logs in | `userId`, `timestamp`, `sessionId` | P0 |
| `first-value-operation` | User completes first meaningful action | `userId`, `timestamp`, `action`, `ttv` | P0 |
| `decision_approve` | User approves a decision | `userId`, `decisionId`, `timestamp`, `comment` | P0 |
| `decision_reject` | User rejects a decision | `userId`, `decisionId`, `timestamp`, `reason` | P0 |
| `cost_analysis_view` | User views Cost Analysis page | `userId`, `timestamp`, `filters` | P1 |
| `strategy_management_view` | User views Strategy Management page | `userId`, `timestamp` | P1 |

---

## Validation Checklist

### Pre-Test Setup

- [ ] Sentry DSN configured in environment
- [ ] Path Tracking enabled in application
- [ ] Test user accounts created
- [ ] Sentry dashboard access confirmed
- [ ] Test event sent to verify connectivity

### During Test

For each scenario, verify:

- [ ] Event is triggered at the correct moment
- [ ] Event contains all expected data fields
- [ ] Timestamp is accurate
- [ ] No duplicate events
- [ ] No missing events

### Post-Test Analysis

- [ ] All expected events captured (6/6)
- [ ] Event timing is accurate (±2 seconds)
- [ ] TTV calculated correctly
- [ ] No phantom events (events without user action)
- [ ] Session tracking is continuous

---

## Validation Methods

### Method 1: Real-Time Sentry Dashboard

**Steps**:
1. Open Sentry dashboard before test session
2. Filter by test user ID or session ID
3. Monitor events as they occur during test
4. Note any missing or unexpected events

**Pros**: Immediate feedback, can catch issues during test  
**Cons**: Requires Sentry access, may be distracting

---

### Method 2: Post-Test Sentry Query

**Steps**:
1. Complete usability test session
2. Query Sentry for events by user ID and time range
3. Export event data to CSV
4. Compare against expected events checklist

**Pros**: Comprehensive analysis, less distracting  
**Cons**: Can't fix issues during test

**Sentry Query Example**:
```
user.id:P001 AND timestamp:[2025-10-23T10:00:00 TO 2025-10-23T11:00:00]
```

---

### Method 3: Browser Console Logging

**Steps**:
1. Open browser DevTools Console
2. Filter for "Path Tracking" or "Sentry" logs
3. Observe events being sent in real-time
4. Screenshot any errors

**Pros**: Immediate visibility, no Sentry access needed  
**Cons**: Only works if console logging is enabled

---

### Method 4: Network Tab Monitoring

**Steps**:
1. Open browser DevTools Network tab
2. Filter for requests to Sentry endpoint
3. Inspect request payload for each event
4. Verify data completeness

**Pros**: See exact data being sent  
**Cons**: Technical, requires understanding of network requests

---

## Event Validation Criteria

### 1. user_login

**Expected Trigger**: After successful authentication

**Required Fields**:
```json
{
  "event": "user_login",
  "userId": "string",
  "timestamp": "ISO 8601 datetime",
  "sessionId": "string",
  "loginMethod": "email|google|github"
}
```

**Validation**:
- [ ] Event fires immediately after login success
- [ ] userId matches test user
- [ ] timestamp is accurate (±2 seconds)
- [ ] sessionId is unique per session

**Common Issues**:
- Event fires before authentication completes
- Missing userId (user not yet in context)
- Duplicate events on page refresh

---

### 2. first-value-operation

**Expected Trigger**: User completes first meaningful action (e.g., save dashboard settings, approve first decision)

**Required Fields**:
```json
{
  "event": "first-value-operation",
  "userId": "string",
  "timestamp": "ISO 8601 datetime",
  "action": "string (description of action)",
  "ttv": "number (seconds from login to this action)"
}
```

**Validation**:
- [ ] Event fires on first meaningful action only
- [ ] TTV is calculated correctly (time from login)
- [ ] action field describes what user did
- [ ] Does not fire on trivial actions (page navigation, hover)

**Common Issues**:
- Fires on every action instead of first only
- TTV calculation incorrect (wrong start time)
- Fires on page load instead of user action

---

### 3. decision_approve

**Expected Trigger**: User clicks "Approve" button and confirms

**Required Fields**:
```json
{
  "event": "decision_approve",
  "userId": "string",
  "decisionId": "string",
  "timestamp": "ISO 8601 datetime",
  "comment": "string (optional)"
}
```

**Validation**:
- [ ] Event fires after approval is confirmed (not on button click)
- [ ] decisionId matches the approved decision
- [ ] comment is captured if provided
- [ ] Does not fire if user cancels

**Common Issues**:
- Fires on button click before confirmation
- Missing decisionId
- Fires even if approval fails

---

### 4. decision_reject

**Expected Trigger**: User clicks "Reject" button and provides reason

**Required Fields**:
```json
{
  "event": "decision_reject",
  "userId": "string",
  "decisionId": "string",
  "timestamp": "ISO 8601 datetime",
  "reason": "string"
}
```

**Validation**:
- [ ] Event fires after rejection is confirmed
- [ ] decisionId matches the rejected decision
- [ ] reason is captured
- [ ] Does not fire if user cancels

**Common Issues**:
- Fires before reason is provided
- Missing or empty reason field
- Fires even if rejection fails

---

### 5. cost_analysis_view

**Expected Trigger**: User navigates to Cost Analysis page

**Required Fields**:
```json
{
  "event": "cost_analysis_view",
  "userId": "string",
  "timestamp": "ISO 8601 datetime",
  "filters": {
    "timeRange": "string",
    "category": "string (optional)"
  }
}
```

**Validation**:
- [ ] Event fires when page loads
- [ ] filters reflect current state
- [ ] Does not fire multiple times on same page

**Common Issues**:
- Fires on every filter change (should be separate event)
- Missing filter data
- Fires before page fully loads

---

### 6. strategy_management_view

**Expected Trigger**: User navigates to Strategy Management page

**Required Fields**:
```json
{
  "event": "strategy_management_view",
  "userId": "string",
  "timestamp": "ISO 8601 datetime"
}
```

**Validation**:
- [ ] Event fires when page loads
- [ ] Does not fire multiple times on same page

**Common Issues**:
- Fires on every strategy interaction
- Missing userId

---

## TTV Calculation Validation

### Formula

```
TTV = timestamp(first-value-operation) - timestamp(user_login)
```

### Expected Range

- **Target**: < 10 minutes (600 seconds)
- **Typical**: 3-8 minutes (180-480 seconds)
- **Concerning**: > 15 minutes (900 seconds)

### Validation Steps

1. **Extract Timestamps**:
   - Login timestamp: `2025-10-23T10:00:00Z`
   - First value operation timestamp: `2025-10-23T10:05:30Z`

2. **Calculate Difference**:
   - TTV = 5 minutes 30 seconds = 330 seconds

3. **Verify Against Manual Timing**:
   - Compare with facilitator's manual timer
   - Acceptable variance: ±30 seconds

4. **Check for Anomalies**:
   - TTV < 30 seconds: Likely error (too fast)
   - TTV > 30 minutes: User took break or got stuck

### Common TTV Calculation Errors

| Error | Symptom | Cause | Fix |
|-------|---------|-------|-----|
| Negative TTV | TTV shows negative value | Timestamps out of order | Check system clock sync |
| Zero TTV | TTV = 0 | Both events have same timestamp | Increase timestamp precision |
| Extremely high TTV | TTV > 1 hour | User took break | Filter out sessions with breaks |
| Missing TTV | TTV not calculated | first-value-operation not captured | Check event trigger logic |

---

## Troubleshooting

### Issue: Events Not Appearing in Sentry

**Possible Causes**:
1. Sentry DSN not configured
2. Network connectivity issues
3. Events being filtered by Sentry rules
4. Incorrect environment (dev vs prod)

**Debugging Steps**:
1. Check browser console for Sentry errors
2. Verify Sentry DSN in environment variables
3. Check network tab for failed requests
4. Test with a simple event (e.g., page load)

---

### Issue: Duplicate Events

**Possible Causes**:
1. Event handler attached multiple times
2. Page refresh triggers event again
3. React component re-renders

**Debugging Steps**:
1. Add event deduplication logic
2. Use `useEffect` cleanup in React
3. Check for multiple event listener registrations

---

### Issue: Missing Event Data

**Possible Causes**:
1. Data not available at event trigger time
2. Async operations not completed
3. Context not properly passed

**Debugging Steps**:
1. Log data before sending event
2. Add delays for async operations
3. Verify context providers are wrapping components

---

### Issue: Incorrect Timestamps

**Possible Causes**:
1. Client clock out of sync
2. Timezone issues
3. Using wrong timestamp source

**Debugging Steps**:
1. Use server-side timestamps when possible
2. Normalize all timestamps to UTC
3. Compare client and server times

---

## Reporting Path Tracking Issues

### Issue Template

```markdown
## Path Tracking Issue

**Event**: [event name]
**Participant**: P[number]
**Timestamp**: [when it occurred]
**Severity**: P0 / P1 / P2

### Expected Behavior
[What should have happened]

### Actual Behavior
[What actually happened]

### Steps to Reproduce
1. 
2. 
3. 

### Screenshots/Logs
[Attach relevant screenshots or logs]

### Impact
[How this affects usability testing or metrics]

### Suggested Fix
[If known]
```

---

## Post-Test Analysis Checklist

### Data Completeness

- [ ] All 5 participants have login events
- [ ] All 5 participants have first-value-operation events
- [ ] Decision approval/rejection events captured for all participants
- [ ] Page view events captured for all scenarios

### Data Quality

- [ ] No duplicate events
- [ ] All timestamps are reasonable
- [ ] All required fields are populated
- [ ] No phantom events (events without user action)

### TTV Analysis

- [ ] TTV calculated for all 5 participants
- [ ] Average TTV calculated
- [ ] Median TTV calculated
- [ ] TTV distribution analyzed (min, max, std dev)
- [ ] Outliers identified and explained

### Path Analysis

- [ ] Common user paths identified
- [ ] Deviation from expected paths noted
- [ ] Drop-off points identified
- [ ] Success paths documented

---

## Metrics to Report

### Quantitative Metrics

1. **Event Capture Rate**: (Events Captured / Events Expected) × 100%
   - Target: 100%
   - Acceptable: > 95%

2. **Average TTV**: Sum of all TTVs / Number of participants
   - Target: < 10 minutes
   - Acceptable: < 15 minutes

3. **Median TTV**: Middle value of sorted TTVs
   - More robust to outliers than average

4. **TTV Standard Deviation**: Measure of TTV variability
   - Lower is better (more consistent experience)

### Qualitative Insights

1. **Common Path Patterns**: Most frequent user journeys
2. **Unexpected Behaviors**: Actions not anticipated
3. **Drop-off Points**: Where users get stuck
4. **Success Factors**: What helps users complete tasks quickly

---

## Recommendations for Path Tracking Improvements

Based on validation findings, provide recommendations such as:

1. **Add Missing Events**: Identify user actions that should be tracked
2. **Improve Event Data**: Add fields that would provide more context
3. **Fix Timing Issues**: Correct events that fire at wrong times
4. **Reduce Noise**: Remove or consolidate redundant events
5. **Enhance TTV Calculation**: Improve accuracy or add variants (e.g., TTV by user role)

---

## Tools and Resources

### Sentry Dashboard

- **URL**: https://sentry.io/organizations/morningai/
- **Project**: morningai-dashboard
- **Access**: Request from DevOps team

### Browser DevTools

- **Console**: Filter for "Path Tracking" or "Sentry"
- **Network**: Filter for "sentry.io" requests
- **Application**: Check Local Storage for session data

### Analysis Tools

- **Spreadsheet**: For calculating TTV and aggregating data
- **Sentry CLI**: For querying events programmatically
- **Jupyter Notebook**: For advanced analysis (if needed)

---

## References

- **Path Tracking Implementation**: `/frontend-dashboard-deploy/src/lib/pathTracking.js`
- **Sentry Configuration**: `/frontend-dashboard-deploy/src/lib/sentry.js`
- **Event Definitions**: `/docs/UX/PATH_TRACKING_SPEC.md`

---

**Document Owner**: MorningAI UX Team  
**Version**: 1.0  
**Last Updated**: 2025-10-23
