# Usability Testing Script

## MorningAI Dashboard Usability Study

**Version**: 1.0  
**Last Updated**: 2025-10-23  
**Session Duration**: 60 minutes

---

## Pre-Session Checklist (5 minutes before)

- [ ] Test environment is ready (staging/demo environment)
- [ ] Test credentials prepared
- [ ] Recording software tested
- [ ] Consent form printed/ready
- [ ] Observation notes template open
- [ ] Timer ready
- [ ] Incentive payment ready

---

## Session Structure

| Section | Duration | Activity |
|---------|----------|----------|
| Introduction | 5 min | Welcome, consent, overview |
| Scenario 1 | 15 min | First-time user onboarding |
| Scenario 2 | 10 min | Decision approval workflow |
| Scenario 3 | 10 min | Cost analysis exploration |
| Scenario 4 | 10 min | Strategy management |
| Scenario 5 | 10 min | Mobile experience |
| Wrap-up | 10 min | Post-test questions, SUS survey |

**Total**: 60 minutes

---

## Introduction (5 minutes)

### Welcome

> "Thank you for participating in this usability test today. My name is [Your Name], and I'll be guiding you through this session."

### Explain Purpose

> "Today, we'll be testing the MorningAI dashboard interface. This is a system designed to help users manage automated decisions, monitor costs, and configure optimization strategies."
>
> "I want to emphasize: **This is a test of the interface, not of you.** There are no right or wrong answers. We want to understand how real users interact with the system so we can make it better."

### Think-Aloud Protocol

> "As you work through the tasks, please **think aloud**. Tell me what you're thinking, what you're looking for, what you're trying to do, and any confusion you experience. This helps us understand your thought process."
>
> "For example, if you're looking for a button, you might say: 'I'm looking for a way to approve this decision. I would expect it to be near the top... I see an Approve button here.'"

### Recording Consent

> "Before we begin, I need to confirm: Are you comfortable with us recording your screen and audio for this session? The recording will only be used for analysis and will be deleted within 30 days."

[Wait for verbal consent]

> "Great, I'm starting the recording now."

[Start recording]

### Questions

> "Do you have any questions before we begin?"

[Answer any questions]

> "Alright, let's get started!"

---

## Scenario 1: First-Time User Onboarding (15 minutes)

### Context

> "Imagine you are a new operations manager at a company that just started using MorningAI. This is your first time logging into the system. Your goal is to understand what the dashboard does and complete your first meaningful action."

### Task 1.1: Login (2 minutes)

> "Your task is to log in to the MorningAI dashboard using these credentials:"
>
> **Username**: [provide test username]  
> **Password**: [provide test password]
>
> "Please log in now."

**Observe**:
- Does user find the login page easily?
- Any confusion with the login form?
- Time to complete login

**Path Tracking Events to Verify**:
- `user_login`

### Task 1.2: Understand Dashboard (5 minutes)

> "Now that you're logged in, take a moment to look at the dashboard. Without clicking anything yet, can you tell me:"
>
> 1. "What do you think this dashboard is for?"
> 2. "What information is being displayed?"
> 3. "What actions do you think you can take from here?"

**Observe**:
- Does user understand the purpose?
- Can they identify key metrics?
- Do they notice navigation elements?

### Task 1.3: First Meaningful Action (8 minutes)

> "Your task is to save your dashboard settings or preferences. This could be anything that personalizes your experience. Try to complete this action."

**Observe**:
- Can user find settings/preferences?
- Time to complete first action
- Any errors or confusion?

**Path Tracking Events to Verify**:
- `first-value-operation`

### Post-Task Questions

1. "On a scale of 1-5, how difficult was this task?" (1=Very Easy, 5=Very Difficult)
2. "What was confusing, if anything?"
3. "What would have made this easier?"

---

## Scenario 2: Decision Approval Workflow (10 minutes)

### Context

> "Now imagine you've been using MorningAI for a few days. You receive a notification that there are pending decisions that need your approval. Your task is to review and respond to these decisions."

### Task 2.1: Navigate to Decision Approval (2 minutes)

> "Navigate to the page where you can see pending decisions."

**Observe**:
- Does user find the navigation easily?
- Do they use sidebar, menu, or other method?

### Task 2.2: Review Decision Details (3 minutes)

> "Select one of the pending decisions and review its details. Can you tell me:"
>
> 1. "What is this decision about?"
> 2. "What information is provided to help you make a decision?"
> 3. "What would be the impact of approving or rejecting this?"

**Observe**:
- Does user understand the decision context?
- Is the information clear and sufficient?

### Task 2.3: Approve and Reject Decisions (5 minutes)

> "Now, please:"
>
> 1. "Approve one decision and add a comment explaining why."
> 2. "Reject another decision and provide a reason."

**Observe**:
- Can user complete actions without errors?
- Is the approval/rejection flow intuitive?
- Does user understand the outcome?

**Path Tracking Events to Verify**:
- `decision_approve`
- `decision_reject`

### Post-Task Questions

1. "On a scale of 1-5, how difficult was this task?"
2. "Did you feel confident in your decisions?"
3. "What additional information would have been helpful?"

---

## Scenario 3: Cost Analysis Exploration (10 minutes)

### Context

> "Your manager asks you to prepare a report on the company's costs for the past month. You need to use the Cost Analysis feature to gather this information."

### Task 3.1: Navigate to Cost Analysis (1 minute)

> "Navigate to the Cost Analysis page."

**Observe**:
- Does user find it easily?

### Task 3.2: Identify Highest Cost Category (3 minutes)

> "Looking at the cost data, can you tell me:"
>
> 1. "What is the highest cost category?"
> 2. "How much was spent in that category?"

**Observe**:
- Can user interpret the data visualization?
- Is the information architecture clear?

### Task 3.3: Filter by Time Period (3 minutes)

> "Now, filter the data to show only the past 7 days."

**Observe**:
- Can user find the filter controls?
- Is the filtering interaction intuitive?

### Task 3.4: Export Report (3 minutes)

> "If you needed to export this cost data for your manager, how would you do that? Try to export the report."

**Observe**:
- Is export functionality discoverable?
- Does user understand export options?

**Path Tracking Events to Verify**:
- `cost_analysis_view`

### Post-Task Questions

1. "On a scale of 1-5, how difficult was this task?"
2. "Was the cost data easy to understand?"
3. "What would make this feature more useful?"

---

## Scenario 4: Strategy Management (10 minutes)

### Context

> "Your company wants to optimize its automated strategies. You need to review the current strategies and understand what they do."

### Task 4.1: Navigate to Strategy Management (1 minute)

> "Navigate to the Strategy Management page."

### Task 4.2: Understand Current Strategies (4 minutes)

> "Looking at the strategies displayed, can you tell me:"
>
> 1. "How many strategies are currently active?"
> 2. "What does one of these strategies do?"
> 3. "What parameters can be configured?"

**Observe**:
- Does user understand strategy purpose?
- Is the information clear?

### Task 4.3: Modify a Strategy (5 minutes)

> "Try to modify one of the strategy settings. You can change any parameter you think would be useful."

**Observe**:
- Can user find edit controls?
- Is the modification process clear?
- Does user understand the impact of changes?

**Path Tracking Events to Verify**:
- `strategy_management_view`

### Post-Task Questions

1. "On a scale of 1-5, how difficult was this task?"
2. "Did you feel confident making changes?"
3. "What additional information would have helped?"

---

## Scenario 5: Mobile Experience (10 minutes)

### Context

> "Now, let's test the mobile experience. Please switch to your mobile device (or I'll resize the browser to mobile size)."

### Task 5.1: Access Dashboard on Mobile (2 minutes)

> "Access the MorningAI dashboard on your mobile device using the same credentials."

**Observe**:
- Does the mobile site load correctly?
- Is the layout responsive?

### Task 5.2: Navigate Between Pages (3 minutes)

> "Navigate to the Decision Approval page and then to the Cost Analysis page."

**Observe**:
- Is navigation accessible on mobile?
- Are touch targets adequate (44x44px minimum)?
- Any horizontal scrolling?

### Task 5.3: Approve a Decision on Mobile (5 minutes)

> "Try to approve one of the pending decisions on your mobile device."

**Observe**:
- Can user complete the task on mobile?
- Are buttons and controls easy to tap?
- Is the experience comparable to desktop?

### Post-Task Questions

1. "On a scale of 1-5, how was the mobile experience?"
2. "What was frustrating about using it on mobile?"
3. "Would you use this on mobile regularly?"

---

## Wrap-up Questions (10 minutes)

### Overall Impression

1. "What was your overall impression of the MorningAI dashboard?"
2. "What did you like most about the interface?"
3. "What was the most confusing or frustrating part?"
4. "If you could change one thing, what would it be?"

### Comparison

5. "Have you used similar dashboards before? How does this compare?"

### Net Promoter Score

6. "On a scale of 0-10, how likely are you to recommend MorningAI to a colleague?"
   - 0 = Not at all likely
   - 10 = Extremely likely

### Open Feedback

7. "Is there anything else you'd like to share about your experience?"

### System Usability Scale (SUS)

> "Finally, I'd like you to complete a brief 10-question survey about the system. For each statement, rate your agreement on a scale of 1-5:"
>
> - 1 = Strongly Disagree
> - 2 = Disagree
> - 3 = Neutral
> - 4 = Agree
> - 5 = Strongly Agree

[Provide SUS questionnaire - see SUS_QUESTIONNAIRE.md]

---

## Closing (2 minutes)

### Thank You

> "Thank you so much for your time and feedback today. Your insights are incredibly valuable and will help us improve the MorningAI dashboard."

### Compensation

> "As a thank you, here is [your compensation: NT$ 1,000 / 3 months free subscription code]."

[Provide compensation]

### Follow-up

> "If you have any questions or additional feedback after today, please feel free to email us at ux@morningai.app."

### Stop Recording

> "I'm going to stop the recording now. Have a great day!"

[Stop recording]

---

## Post-Session Tasks

- [ ] Save recording with participant ID (e.g., P001_2025-10-23.mp4)
- [ ] Transfer observation notes to analysis document
- [ ] Calculate task completion times
- [ ] Score SUS questionnaire
- [ ] Update participant tracking spreadsheet
- [ ] Send thank you email (if applicable)

---

## Notes for Facilitator

### Do's
- ✅ Be friendly and welcoming
- ✅ Encourage think-aloud protocol
- ✅ Stay neutral (don't lead or judge)
- ✅ Take detailed notes
- ✅ Allow silence (don't rush to help)
- ✅ Observe body language and facial expressions

### Don'ts
- ❌ Don't defend the design
- ❌ Don't explain how things work (unless user is stuck >2 minutes)
- ❌ Don't interrupt user's thought process
- ❌ Don't show frustration or disappointment
- ❌ Don't skip scenarios due to time (adjust if needed)

### If User Gets Stuck

**After 1 minute**: "What are you thinking right now?"

**After 2 minutes**: "What would you expect to happen if you [suggest action]?"

**After 3 minutes**: "Let me give you a hint: [provide minimal guidance]"

**After 4 minutes**: "Let's move on to the next task. We'll note this as an area for improvement."

---

**Document Owner**: MorningAI UX Team  
**Version**: 1.0  
**Last Updated**: 2025-10-23
