# Usability Testing Plan - Week 4

## Overview

This document outlines the usability testing plan for MorningAI's dashboard interface, focusing on key user flows and Path Tracking integration.

## Objectives

1. Validate user journey flows (login, decision approval, cost analysis)
2. Measure Time To Value (TTV) for first-time users
3. Identify usability issues and pain points
4. Verify Path Tracking accuracy and completeness
5. Assess WCAG 2.1 AA compliance in real-world usage

## Test Scope

### In Scope
- Login flow
- Dashboard navigation
- Decision approval workflow
- Cost analysis viewing
- Strategy management
- Mobile responsiveness

### Out of Scope
- Backend API performance
- Database operations
- Third-party integrations
- Payment processing

## Participant Recruitment

### Target Participants

**Total**: 5 participants (Nielsen Norman Group recommendation for usability testing)

**Roles**:
1. Operations Manager (1 participant)
2. Customer Service Representative (1 participant)
3. Business Analyst (1 participant)
4. Admin/Manager (1 participant)
5. New User (no prior experience) (1 participant)

### Recruitment Channels

1. **Existing Users**: Email invitation to active users
2. **Social Media**: LinkedIn, Twitter posts
3. **User Interview List**: Previous interview participants
4. **Internal Team**: Non-development team members

### Screening Criteria

**Must Have**:
- 18+ years old
- Comfortable using web applications
- Available for 60-minute session
- Stable internet connection

**Nice to Have**:
- Experience with SaaS dashboards
- Familiarity with decision approval workflows
- Mobile device for mobile testing

### Incentives

**Option A**: NT$ 1,000 cash per participant
**Option B**: 3 months free MorningAI subscription (for existing/potential users)

## Test Scenarios

### Scenario 1: First-Time User Onboarding (15 minutes)

**Goal**: Measure TTV and identify onboarding friction

**Tasks**:
1. Create account (if applicable) or log in with provided credentials
2. Complete first login
3. Navigate to dashboard
4. Understand key metrics displayed
5. Perform first meaningful action (save dashboard settings)

**Success Criteria**:
- TTV < 10 minutes
- User can explain dashboard purpose
- User completes first action without assistance

**Path Tracking Events**:
- `user_login`
- `first-value-operation` (dashboard save)

### Scenario 2: Decision Approval Workflow (10 minutes)

**Goal**: Validate decision approval UX and Path Tracking

**Tasks**:
1. Navigate to Decision Approval page
2. Review pending decision details
3. Approve one decision with comment
4. Reject one decision with reason
5. Verify decision status updates

**Success Criteria**:
- User completes approval/rejection without errors
- User understands decision impact
- Path Tracking captures all actions

**Path Tracking Events**:
- `decision_approve`
- `decision_reject`

### Scenario 3: Cost Analysis Exploration (10 minutes)

**Goal**: Assess information architecture and data comprehension

**Tasks**:
1. Navigate to Cost Analysis page
2. Identify highest cost category
3. Filter data by time period
4. Export cost report (if available)

**Success Criteria**:
- User finds information within 2 minutes
- User can explain cost trends
- No confusion about data visualization

**Path Tracking Events**:
- `cost_analysis_view`

### Scenario 4: Strategy Management (10 minutes)

**Goal**: Evaluate strategy configuration UX

**Tasks**:
1. Navigate to Strategy Management
2. View current strategies
3. Understand strategy parameters
4. Modify a strategy setting (if permitted)

**Success Criteria**:
- User understands strategy purpose
- User can modify settings confidently
- Changes are saved successfully

**Path Tracking Events**:
- `strategy_management_view`

### Scenario 5: Mobile Experience (10 minutes)

**Goal**: Validate mobile responsiveness and touch interactions

**Tasks**:
1. Access dashboard on mobile device
2. Navigate between pages
3. Approve a decision on mobile
4. Verify touch targets are adequate (44x44px minimum)

**Success Criteria**:
- All features accessible on mobile
- Touch targets meet WCAG guidelines
- No horizontal scrolling required

## Test Script

### Introduction (5 minutes)

```
Thank you for participating in this usability test. Today, we'll be testing the MorningAI dashboard interface. 

This is a test of the interface, not of you. There are no right or wrong answers. We want to understand how real users interact with the system.

Please think aloud as you work through the tasks. Tell us what you're thinking, what you're looking for, and any confusion you experience.

Do you have any questions before we begin?
```

### Task Instructions

For each scenario, provide:
1. Context: "Imagine you are a [role] who needs to [goal]"
2. Task: "Your task is to [specific action]"
3. Observation: Watch user, take notes, don't interrupt unless stuck >2 minutes

### Wrap-up Questions (5 minutes)

1. What was your overall impression of the interface?
2. What was the most confusing part?
3. What did you like most?
4. On a scale of 1-10, how likely are you to recommend this to a colleague?
5. Any other feedback?

## Data Collection

### Quantitative Metrics

1. **Time To Value (TTV)**
   - Measurement: Time from first login to first meaningful action
   - Target: < 10 minutes
   - Collection: Automatic via Path Tracking

2. **Task Success Rate**
   - Measurement: % of tasks completed successfully
   - Target: > 80%
   - Collection: Manual observation

3. **Task Completion Time**
   - Measurement: Time to complete each scenario
   - Target: Within estimated time
   - Collection: Manual timing

4. **Error Rate**
   - Measurement: Number of errors per task
   - Target: < 2 errors per task
   - Collection: Manual observation

5. **System Usability Scale (SUS)**
   - Measurement: 10-question standardized survey
   - Target: > 80 (Grade A)
   - Collection: Post-test survey

6. **Net Promoter Score (NPS)**
   - Measurement: Likelihood to recommend (0-10)
   - Target: > 35 (Good)
   - Collection: Post-test question

### Qualitative Data

1. **Think-Aloud Protocol**
   - Record user verbalizations
   - Note confusion points
   - Capture positive reactions

2. **Observation Notes**
   - Navigation patterns
   - Hesitations
   - Error recovery strategies
   - Facial expressions

3. **Post-Task Feedback**
   - Difficulty ratings
   - Satisfaction ratings
   - Open-ended comments

## Data Analysis

### Issue Classification

**Severity Levels**:
- **Critical (P0)**: Prevents task completion, must fix before launch
- **High (P1)**: Causes significant frustration, fix in next sprint
- **Medium (P2)**: Minor inconvenience, fix when possible
- **Low (P3)**: Cosmetic issue, nice to have

**Issue Categories**:
- Navigation
- Information Architecture
- Visual Design
- Interaction Design
- Content/Copy
- Accessibility
- Performance

### Analysis Methods

1. **Thematic Analysis**
   - Group similar issues
   - Identify patterns across participants
   - Prioritize by frequency and severity

2. **Quantitative Analysis**
   - Calculate average TTV
   - Compute task success rates
   - Analyze SUS and NPS scores
   - Compare against baseline (if available)

3. **Path Tracking Validation**
   - Verify all expected events captured
   - Check event timing accuracy
   - Identify missing tracking points

## Reporting

### Report Structure

1. **Executive Summary**
   - Key findings (3-5 bullet points)
   - Overall usability score
   - Critical issues requiring immediate attention

2. **Methodology**
   - Participant demographics
   - Test scenarios
   - Data collection methods

3. **Quantitative Results**
   - TTV metrics
   - Task success rates
   - SUS and NPS scores
   - Comparison to targets

4. **Qualitative Findings**
   - Common pain points
   - Positive feedback
   - User quotes
   - Observed behaviors

5. **Issue List**
   - Prioritized by severity
   - Screenshots/videos
   - Recommended solutions

6. **Path Tracking Analysis**
   - Event capture completeness
   - Timing accuracy
   - Recommendations for improvement

7. **Recommendations**
   - Immediate fixes (P0)
   - Short-term improvements (P1)
   - Long-term enhancements (P2/P3)

8. **Appendices**
   - Raw data
   - Participant demographics
   - Test script
   - SUS questionnaire

### Deliverables

1. **Usability Test Report** (PDF)
2. **Issue Tracker** (GitHub Issues with `usability-test` label)
3. **Video Highlights** (5-10 minute compilation)
4. **Path Tracking Validation Report**

## Timeline

### Week 4 Schedule

**Day 1-2**: Participant recruitment and scheduling
**Day 3**: Pilot test with internal team member
**Day 4-5**: Conduct 5 usability tests (1-2 per day)
**Day 6-7**: Data analysis and report writing
**Day 8**: Present findings to team

## Success Criteria

### Test Execution
- [ ] 5 participants recruited
- [ ] All 5 tests completed
- [ ] All scenarios covered
- [ ] Data collected for all metrics

### Baseline Establishment
- [ ] TTV baseline measured (50+ samples)
- [ ] Path success rates calculated (100+ samples)
- [ ] SUS baseline established (30+ responses)
- [ ] NPS baseline established (30+ responses)

### Actionable Insights
- [ ] At least 10 usability issues identified
- [ ] Issues prioritized by severity
- [ ] Recommendations provided for each issue
- [ ] GitHub Issues created for P0/P1 items

## Tools and Resources

### Required Tools
- **Video Conferencing**: Zoom/Google Meet (with recording)
- **Screen Recording**: Zoom recording or Loom
- **Note Taking**: Google Docs or Notion
- **Survey Tool**: Google Forms or Typeform
- **Analytics**: Sentry (for Path Tracking data)

### Templates
- Consent form
- Test script
- Observation notes template
- SUS questionnaire
- Post-test interview questions

## Ethical Considerations

### Informed Consent
- Explain test purpose
- Obtain recording permission
- Clarify data usage
- Allow opt-out at any time

### Data Privacy
- Anonymize participant data
- Secure storage of recordings
- Delete recordings after analysis (or as agreed)
- Comply with GDPR/local privacy laws

### Participant Wellbeing
- No pressure to complete tasks
- Allow breaks if needed
- Respectful observation
- Thank participants for their time

## Next Steps After Testing

1. **Immediate (Week 5)**
   - Fix P0 issues
   - Create GitHub Issues for P1/P2 items
   - Update design documentation

2. **Short-term (Week 6-8)**
   - Implement P1 improvements
   - Re-test critical flows
   - Update Storybook documentation

3. **Long-term (Phase 10)**
   - Quarterly usability testing
   - Continuous Path Tracking monitoring
   - A/B testing for major changes

## References

- Nielsen Norman Group: [How Many Test Users in a Usability Study?](https://www.nngroup.com/articles/how-many-test-users/)
- System Usability Scale: [Measuring Usability with the System Usability Scale](https://measuringu.com/sus/)
- WCAG 2.1 Guidelines: [Web Content Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
