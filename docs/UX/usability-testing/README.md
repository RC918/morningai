# Usability Testing Materials - Week 4

## Overview

This directory contains all materials needed to conduct usability testing for the MorningAI dashboard, as outlined in the Week 4 UX Enhancement Roadmap.

> **⚠️ Execution Status**: Legal review completed, formal execution deferred until public beta. Materials are GDPR-compliant and ready for future use.

### Data Privacy and Usage Limitation

**Purpose Limitation**: All data collected during usability testing is used **exclusively for product usability research** to improve the MorningAI dashboard interface. Data will not be used for:
- Marketing or promotional purposes
- User profiling or behavioral tracking outside of research
- Sale or transfer to third parties
- Any purpose other than usability research and product improvement

**Data Minimization**: We collect only the minimum data necessary to conduct usability research:
- Screen recordings and audio (for task observation)
- Path Tracking data (for TTV measurement)
- Survey responses (for usability metrics)
- Observation notes (for qualitative insights)

**Retention and Deletion**: All personal data will be retained for a maximum of **90 days** from the test session date, or until research completion plus 30 days, whichever comes first. After this period:
- All video and audio recordings will be permanently deleted
- Personal identifiers will be removed from notes
- Only anonymized, aggregated data will be retained

For more details, see [CONSENT_FORM.md](CONSENT_FORM.md).

## Quick Start

### For Facilitators

1. **Review the Plan**: Read [USABILITY_TESTING_PLAN.md](../USABILITY_TESTING_PLAN.md) for full context
2. **Prepare Materials**: Print/prepare all documents listed below
3. **Set Up Environment**: Configure test environment and tools
4. **Recruit Participants**: Use screening criteria in the plan
5. **Conduct Tests**: Follow [TEST_SCRIPT.md](TEST_SCRIPT.md)
6. **Analyze Results**: Use [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)

### For Participants

You will be asked to:
- Sign a consent form
- Complete 5 test scenarios (60 minutes total)
- Think aloud as you work
- Answer questions about your experience
- Complete a brief survey

---

## Directory Structure

```
usability-testing/
├── README.md                           # This file
├── CONSENT_FORM.md                     # Participant consent form
├── TEST_SCRIPT.md                      # Facilitator guide for conducting tests
├── OBSERVATION_NOTES_TEMPLATE.md       # Template for recording observations
├── SUS_QUESTIONNAIRE.md                # System Usability Scale survey
├── POST_TEST_INTERVIEW_QUESTIONS.md    # Post-test interview guide
├── PATH_TRACKING_VALIDATION.md         # Guide for validating Path Tracking
└── REPORT_TEMPLATE.md                  # Template for final report
```

---

## Document Descriptions

### 1. CONSENT_FORM.md

**Purpose**: Obtain informed consent from participants

**When to Use**: At the beginning of each test session, before starting recording

**Key Sections**:
- Study information and purpose
- Data collection and usage
- Privacy and confidentiality
- Voluntary participation
- Compensation details
- Signature section

**Action Items**:
- [ ] Print one copy per participant
- [ ] Have participant read and sign before testing
- [ ] Provide copy to participant
- [ ] Store signed forms securely

---

### 2. TEST_SCRIPT.md

**Purpose**: Guide facilitators through the test session

**When to Use**: During each test session as a reference

**Key Sections**:
- Pre-session checklist
- Session structure and timing
- Introduction script
- 5 test scenarios with tasks
- Wrap-up questions
- Post-session tasks

**Tips for Facilitators**:
- ✅ Read through the entire script before your first session
- ✅ Practice with a pilot test
- ✅ Stay neutral and don't lead participants
- ✅ Allow silence - don't rush to help
- ✅ Take detailed notes

---

### 3. OBSERVATION_NOTES_TEMPLATE.md

**Purpose**: Record observations during test sessions

**When to Use**: During each test session (real-time note-taking)

**Key Sections**:
- Session information
- Participant demographics
- Notes for each scenario
- Task timing and success rates
- User quotes
- Issues identified
- SUS responses
- Path Tracking validation

**Tips**:
- ✅ Fill out as much as possible during the session
- ✅ Complete remaining sections immediately after
- ✅ Capture exact user quotes (use quotation marks)
- ✅ Note both positive and negative observations
- ✅ Record timestamps for key events

---

### 4. SUS_QUESTIONNAIRE.md

**Purpose**: Measure system usability with standardized scale

**When to Use**: At the end of each test session (wrap-up phase)

**Key Sections**:
- 10 standardized questions
- 5-point Likert scale
- Scoring instructions
- Interpretation guide

**Important**:
- ✅ Administer after all tasks are complete
- ✅ Don't explain questions - let participants interpret naturally
- ✅ Calculate score immediately after session
- ✅ Target score: > 80 (Grade A)

---

### 5. POST_TEST_INTERVIEW_QUESTIONS.md

**Purpose**: Gather qualitative feedback and deeper insights

**When to Use**: During wrap-up phase, after SUS questionnaire

**Key Sections**:
- Overall experience questions
- Specific feature feedback
- Comparison to similar tools
- Mobile experience
- Learning curve
- Trust and confidence
- Net Promoter Score

**Tips**:
- ✅ Use follow-up prompts to dig deeper
- ✅ Let participants elaborate
- ✅ Capture exact quotes
- ✅ Be empathetic and non-judgmental

---

### 6. PATH_TRACKING_VALIDATION.md

**Purpose**: Validate Path Tracking implementation and accuracy

**When to Use**: During and after each test session

**Key Sections**:
- Expected Path Tracking events
- Validation checklist
- Validation methods (Sentry, console, network)
- Event validation criteria
- TTV calculation validation
- Troubleshooting guide

**Important**:
- ✅ Verify all 6 core events are captured
- ✅ Check TTV accuracy (±30 seconds acceptable)
- ✅ Note any missing or duplicate events
- ✅ Document issues for engineering team

---

### 7. REPORT_TEMPLATE.md

**Purpose**: Compile findings into comprehensive report

**When to Use**: After all 5 test sessions are complete

**Key Sections**:
- Executive summary
- Methodology
- Participant demographics
- Quantitative results (TTV, success rates, SUS, NPS)
- Qualitative findings
- Issue list (prioritized by severity)
- Path Tracking analysis
- Recommendations

**Timeline**:
- Day 6-7: Data analysis and report writing
- Day 8: Present findings to team

---

## Test Execution Workflow

### Phase 1: Preparation (Day 1-2)

**Tasks**:
- [ ] Recruit 5 participants (see USABILITY_TESTING_PLAN.md)
- [ ] Schedule test sessions
- [ ] Prepare test environment (staging/demo)
- [ ] Create test user accounts
- [ ] Print consent forms
- [ ] Set up recording software
- [ ] Configure Sentry for Path Tracking
- [ ] Conduct pilot test with internal team member

**Deliverables**:
- Participant schedule
- Test environment URL
- Test credentials
- Printed materials

---

### Phase 2: Testing (Day 3-5)

**Tasks**:
- [ ] Conduct 5 usability test sessions (1-2 per day)
- [ ] Record each session (screen + audio)
- [ ] Take observation notes in real-time
- [ ] Validate Path Tracking during sessions
- [ ] Calculate SUS scores immediately after each session
- [ ] Save recordings with participant IDs

**Deliverables**:
- 5 completed observation notes
- 5 SUS scores
- 5 NPS scores
- 5 session recordings
- Path Tracking validation data

---

### Phase 3: Analysis (Day 6-7)

**Tasks**:
- [ ] Review all observation notes
- [ ] Calculate aggregate metrics (avg TTV, success rates, etc.)
- [ ] Identify common themes and patterns
- [ ] Prioritize issues by severity (P0, P1, P2, P3)
- [ ] Extract key user quotes
- [ ] Analyze Path Tracking data
- [ ] Create video highlights (5-10 minutes)
- [ ] Write usability testing report

**Deliverables**:
- Completed usability testing report
- Video highlights compilation
- Prioritized issue list

---

### Phase 4: Action (Day 8+)

**Tasks**:
- [ ] Present findings to team
- [ ] Create GitHub Issues for P0 and P1 items
- [ ] Assign owners and timelines
- [ ] Update design documentation
- [ ] Plan fixes for Week 5

**Deliverables**:
- Presentation slides
- GitHub Issues with `usability-test` label
- Updated roadmap

---

## Success Criteria

### Test Execution

- [ ] 5 participants recruited and tested
- [ ] All 5 tests completed successfully
- [ ] All 5 scenarios covered in each test
- [ ] Data collected for all metrics

### Baseline Establishment

- [ ] TTV baseline measured (5 samples minimum)
- [ ] Task success rates calculated
- [ ] SUS baseline established (5 responses)
- [ ] NPS baseline established (5 responses)

### Actionable Insights

- [ ] At least 10 usability issues identified
- [ ] Issues prioritized by severity
- [ ] Recommendations provided for each issue
- [ ] GitHub Issues created for P0/P1 items

### Path Tracking Validation

- [ ] All 6 core events validated
- [ ] Event capture rate > 95%
- [ ] TTV accuracy validated (±30 seconds)
- [ ] Issues documented and reported

---

## Tools and Resources

### Required Tools

| Tool | Purpose | Setup Required |
|------|---------|----------------|
| Zoom / Google Meet | Video conferencing | Create meeting links |
| Zoom Recording | Screen + audio recording | Enable recording |
| Google Docs | Note taking | Create shared doc |
| Google Forms | SUS survey | Create form |
| Sentry | Path Tracking analytics | Configure DSN |
| Spreadsheet | Data analysis | Create template |

### Test Environment

**URL**: [Insert staging/demo URL]  
**Test Credentials**:
- User 1: [username] / [password]
- User 2: [username] / [password]
- User 3: [username] / [password]
- User 4: [username] / [password]
- User 5: [username] / [password]

### Sentry Access

**Dashboard**: https://sentry.io/organizations/morningai/  
**Project**: morningai-dashboard  
**Access**: Request from DevOps team

---

## Tips for Success

### For Facilitators

1. **Be Neutral**: Don't defend the design or lead participants
2. **Encourage Think-Aloud**: Remind participants to verbalize their thoughts
3. **Allow Silence**: Don't rush to help - let users struggle a bit
4. **Take Detailed Notes**: Capture exact quotes and behaviors
5. **Stay on Schedule**: Keep sessions to 60 minutes
6. **Be Empathetic**: Thank participants and make them comfortable

### For Observers

1. **Stay Silent**: Don't interrupt or provide hints
2. **Take Notes**: Capture observations from your perspective
3. **Note Patterns**: Look for recurring issues across participants
4. **Be Objective**: Record what you see, not what you think

### For Analysts

1. **Look for Patterns**: Identify issues that affect multiple participants
2. **Prioritize by Impact**: Focus on issues that prevent task completion
3. **Use Data**: Support findings with quantitative metrics
4. **Be Specific**: Provide actionable recommendations
5. **Include Quotes**: Use participant quotes to illustrate points

---

## Common Pitfalls to Avoid

### During Testing

- ❌ **Leading Questions**: "Don't you think this button is easy to find?"
- ✅ **Neutral Questions**: "How would you find the button to approve this?"

- ❌ **Defending Design**: "Well, we put it there because..."
- ✅ **Acknowledging Feedback**: "Thank you for that feedback."

- ❌ **Helping Too Soon**: Jumping in after 30 seconds of struggle
- ✅ **Allowing Struggle**: Wait 2-3 minutes before offering hints

### During Analysis

- ❌ **Cherry-Picking Data**: Only reporting positive findings
- ✅ **Balanced Reporting**: Include both positive and negative findings

- ❌ **Vague Recommendations**: "Improve the navigation"
- ✅ **Specific Recommendations**: "Add a breadcrumb trail to help users understand their location"

- ❌ **Ignoring Patterns**: Treating each participant's feedback in isolation
- ✅ **Identifying Patterns**: "4 out of 5 participants struggled with..."

---

## Frequently Asked Questions

### Q: What if a participant can't complete a task?

**A**: After 3-4 minutes of struggle, provide a hint. If they still can't complete it after 5 minutes, mark it as a failure and move on. This is valuable data - it shows a critical usability issue.

### Q: What if Path Tracking isn't working during a test?

**A**: Continue the test and rely on manual timing. Note the Path Tracking issue in your observation notes. After the session, investigate and fix before the next test.

### Q: What if a participant asks "Is this the right way to do it?"

**A**: Respond with: "There's no right or wrong way. Just do what feels natural to you."

### Q: How do I handle a very talkative participant?

**A**: Gently redirect them: "That's great feedback. Let's move on to the next task so we can cover everything."

### Q: What if a participant finishes early?

**A**: Use the extra time for deeper interview questions. Ask them to elaborate on their experience.

### Q: What if technical issues occur during testing?

**A**: Pause the test, fix the issue, and resume. If it can't be fixed quickly, reschedule the participant. Document the issue.

---

## Contact Information

**UX Team Lead**: [Name]  
**Email**: ux@morningai.app  
**Slack**: #ux-research

**For Technical Issues**:
- Path Tracking: DevOps team (#devops)
- Test Environment: Engineering team (#engineering)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-23 | Initial creation | MorningAI UX Team |

---

## Related Documents

- [USABILITY_TESTING_PLAN.md](../USABILITY_TESTING_PLAN.md) - Full testing plan
- [UI_UX_AUDIT_REPORT.md](../UI_UX_AUDIT_REPORT.md) - Initial audit findings
- [8_WEEK_ENHANCEMENT_ROADMAP.md](../8_WEEK_ENHANCEMENT_ROADMAP.md) - Overall roadmap

---

**Document Owner**: MorningAI UX Team  
**Last Updated**: 2025-10-23  
**Status**: Ready for use
