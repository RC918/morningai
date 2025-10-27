# Week 7-8 Features: Usability Testing, A/B Testing & Metrics Analysis

## Overview

This document describes the new features implemented in Week 7-8 of the UI/UX Enhancement Roadmap:

1. **Usability Testing Framework** - Automated testing sessions with SUS/NPS surveys
2. **A/B Testing System** - Frontend experimentation with statistical analysis
3. **Metrics Analysis** - Performance and UX metrics collection and analysis

---

## 🧪 Usability Testing Framework

### Quick Start

#### 1. Start a Testing Session

```javascript
import { usabilityTest } from '@/lib/usability-testing'

// Start session
const session = usabilityTest.start('P001', 'session-001')

// Start a task
usabilityTest.startTask('login', 'User Login', 'Log in to the dashboard')

// Track interactions
usabilityTest.recordInteraction('click', 'login-button')

// End task
usabilityTest.endTask(true, 'Completed successfully')

// End session
const summary = usabilityTest.end()
```

#### 2. Administer Surveys

```jsx
import SUSQuestionnaire from '@/components/usability/SUSQuestionnaire'
import NPSQuestionnaire from '@/components/usability/NPSQuestionnaire'

// SUS Survey
<SUSQuestionnaire
  participantId="P001"
  sessionId="session-001"
  onComplete={(result) => {
    console.log('SUS Score:', result.sus_score)
  }}
/>

// NPS Survey
<NPSQuestionnaire
  participantId="P001"
  sessionId="session-001"
  onComplete={(result) => {
    console.log('NPS Score:', result.nps_score)
  }}
/>
```

#### 3. View Results

```jsx
import UsabilityTestDashboard from '@/components/usability/UsabilityTestDashboard'

// Admin dashboard
<UsabilityTestDashboard />
```

### Features

- ✅ Automated session tracking
- ✅ Task completion metrics
- ✅ SUS questionnaire (System Usability Scale)
- ✅ NPS survey (Net Promoter Score)
- ✅ Data export for analysis
- ✅ Real-time metrics dashboard

### Files

- `src/lib/usability-testing.js` - Core framework
- `src/components/usability/SUSQuestionnaire.jsx` - SUS survey component
- `src/components/usability/NPSQuestionnaire.jsx` - NPS survey component
- `src/components/usability/UsabilityTestDashboard.jsx` - Admin dashboard

---

## 🔬 A/B Testing System

### Quick Start

#### 1. Create a Test

```javascript
import { createABTest } from '@/lib/ab-testing'

const test = createABTest('dashboard-cta', [
  { id: 'control', name: 'Get Started', weight: 1 },
  { id: 'variant-a', name: 'Try Now - Free!', weight: 1 }
])

// Check variant
if (test.isVariant('variant-a')) {
  buttonText = 'Try Now - Free!'
} else {
  buttonText = 'Get Started'
}

// Track conversion
test.trackConversion({ action: 'signup' })
```

#### 2. Use React Hook

```jsx
import { useABTest } from '@/lib/ab-testing'

function DashboardCTA() {
  const { variant, isVariant, trackConversion } = useABTest(
    'dashboard-cta',
    [
      { id: 'control', name: 'Original', weight: 1 },
      { id: 'variant-a', name: 'New CTA', weight: 1 }
    ]
  )

  return (
    <button onClick={() => trackConversion()}>
      {isVariant('variant-a') ? 'Try Now - Free!' : 'Get Started'}
    </button>
  )
}
```

#### 3. View Results

```jsx
import ABTestDashboard from '@/components/ab-testing/ABTestDashboard'

// Admin dashboard
<ABTestDashboard />
```

### Features

- ✅ Automatic variant assignment
- ✅ Persistent assignments (localStorage)
- ✅ Event tracking (conversions, clicks, custom)
- ✅ Statistical significance calculation
- ✅ Integration with Sentry & Google Analytics
- ✅ Results visualization

### Example Tests

#### Test 1: Dashboard CTA Text

```javascript
const test = createABTest('dashboard-cta', [
  { id: 'control', name: 'Get Started', weight: 1 },
  { id: 'variant-a', name: 'Try Now - Free!', weight: 1 }
])
```

#### Test 2: Approval Button Color

```javascript
const test = createABTest('approval-button-color', [
  { id: 'green', name: 'Green Button', weight: 1 },
  { id: 'blue', name: 'Blue Button', weight: 1 }
])

const buttonVariant = test.isVariant('blue') ? 'primary' : 'success'
```

#### Test 3: Cost Alert Threshold

```javascript
const test = createABTest('cost-alert-threshold', [
  { id: 'threshold-80', name: '80% Default', weight: 1 },
  { id: 'threshold-90', name: '90% Default', weight: 1 }
])

const defaultThreshold = test.isVariant('threshold-90') ? 90 : 80
```

### Files

- `src/lib/ab-testing.js` - Core framework
- `src/components/ab-testing/ABTestDashboard.jsx` - Admin dashboard

---

## 📊 Metrics Analysis

### Quick Start

#### 1. Start Collection

```javascript
import { startMetricsCollection, recordMetric } from '@/lib/metrics-analysis'

// Start automatic collection
startMetricsCollection()

// Record custom metrics
recordMetric('ux', 'TTV', 450000, { user_id: 'user123' })
recordMetric('task', 'login', 5000, { success: true })
```

#### 2. Generate Report

```javascript
import { getMetricsReport } from '@/lib/metrics-analysis'

// Get analysis report
const report = getMetricsReport()

console.log('Web Vitals:', report.web_vitals)
console.log('Task Performance:', report.task_performance)
console.log('Recommendations:', report.recommendations)
```

#### 3. View Dashboard

```jsx
import MetricsAnalysisDashboard from '@/components/metrics/MetricsAnalysisDashboard'

// Admin dashboard
<MetricsAnalysisDashboard />
```

### Features

- ✅ Automatic Web Vitals collection (LCP, CLS, INP, FCP, TTFB)
- ✅ Custom metrics (TTV, task completion, errors)
- ✅ Trend analysis
- ✅ Regression analysis (compare with baseline)
- ✅ Automated recommendations
- ✅ Data export

### Metrics Tracked

#### Web Vitals

| Metric | Description | Target |
|--------|-------------|--------|
| LCP | Largest Contentful Paint | < 2.5s |
| CLS | Cumulative Layout Shift | < 0.1 |
| INP | Interaction to Next Paint | < 200ms |
| FCP | First Contentful Paint | < 1.8s |
| TTFB | Time to First Byte | < 800ms |

#### UX Metrics

- **TTV**: Time to Value (< 10 minutes)
- **Task Success Rate**: > 90%
- **Error Rate**: < 5%

### Files

- `src/lib/metrics-analysis.js` - Core framework
- `src/components/metrics/MetricsAnalysisDashboard.jsx` - Admin dashboard

---

## 🚀 Getting Started

### Installation

All dependencies are already included in the project. No additional installation required.

### Integration

#### 1. Add to App.jsx

```jsx
import { useEffect } from 'react'
import { startMetricsCollection } from '@/lib/metrics-analysis'

function App() {
  useEffect(() => {
    // Start metrics collection on app load
    startMetricsCollection()
  }, [])

  return (
    // Your app content
  )
}
```

#### 2. Add Admin Routes

```jsx
import UsabilityTestDashboard from '@/components/usability/UsabilityTestDashboard'
import ABTestDashboard from '@/components/ab-testing/ABTestDashboard'
import MetricsAnalysisDashboard from '@/components/metrics/MetricsAnalysisDashboard'

// Add routes
<Route path="/admin/usability-testing" element={<UsabilityTestDashboard />} />
<Route path="/admin/ab-testing" element={<ABTestDashboard />} />
<Route path="/admin/metrics" element={<MetricsAnalysisDashboard />} />
```

#### 3. Implement A/B Tests

```jsx
import { useABTest } from '@/lib/ab-testing'

function MyComponent() {
  const { isVariant, trackConversion } = useABTest('my-test', [
    { id: 'control', name: 'Control', weight: 1 },
    { id: 'variant', name: 'Variant', weight: 1 }
  ])

  return (
    <div>
      {isVariant('variant') ? (
        <NewFeature onSuccess={() => trackConversion()} />
      ) : (
        <OldFeature onSuccess={() => trackConversion()} />
      )}
    </div>
  )
}
```

---

## 📖 Documentation

### Comprehensive Guides

- **[Week 7-8 Implementation Guide](../../docs/UX/WEEK_7_8_IMPLEMENTATION_GUIDE.md)** - Complete implementation guide
- **[Usability Testing Materials](../../docs/UX/usability-testing/README.md)** - Testing scripts and templates
- **[UI/UX Resources](../../docs/UI_UX_RESOURCES.md)** - Centralized resource index

### API Documentation

#### Usability Testing API

```javascript
// Session Management
usabilityTest.start(participantId, sessionId)
usabilityTest.end()
usabilityTest.getSummary()
usabilityTest.export()

// Task Tracking
usabilityTest.startTask(taskId, taskName, description)
usabilityTest.endTask(success, notes)
usabilityTest.addNote(note)

// Event Recording
usabilityTest.recordError(type, description)
usabilityTest.recordInteraction(action, target, metadata)

// Data Management
usabilityTest.loadSession(sessionId)
usabilityTest.listSessions()
usabilityTest.deleteSession(sessionId)
```

#### A/B Testing API

```javascript
// Test Management
createABTest(testId, variants, options)
getABTest(testId)

// Variant Checking
test.getVariant()
test.isVariant(variantId)
test.getVariantConfig()

// Event Tracking
test.trackEvent(eventName, metadata)
test.trackConversion(metadata)
test.trackClick(target, metadata)

// Analysis
calculateABTestResults(testId)
exportAllABTestData()
```

#### Metrics Analysis API

```javascript
// Collection
startMetricsCollection()
stopMetricsCollection()
recordMetric(category, name, value, metadata)

// Analysis
getMetricsReport(baseline)
exportMetricsData()

// Data Management
MetricsCollector.loadMetrics()
MetricsCollector.clearMetrics()
```

---

## 🎯 Best Practices

### Usability Testing

1. **Recruit diverse participants** - Different backgrounds, skill levels
2. **Use realistic scenarios** - Based on actual user tasks
3. **Stay neutral** - Don't lead or defend the design
4. **Record everything** - Video, audio, notes, metrics
5. **Analyze systematically** - Look for patterns, prioritize issues

### A/B Testing

1. **Test one variable** - Change only one thing at a time
2. **Define hypothesis** - Clear, measurable prediction
3. **Run long enough** - 1-2 weeks minimum, 100+ participants per variant
4. **Wait for significance** - p < 0.05 before declaring winner
5. **Document learnings** - Share results with team

### Metrics Analysis

1. **Set baseline early** - Establish reference point
2. **Monitor continuously** - Regular check-ins
3. **Act on insights** - Don't just collect, improve
4. **Compare with benchmarks** - Industry standards
5. **Share regularly** - Keep team informed

---

## 🔧 Troubleshooting

### Common Issues

#### Usability Testing

**Problem**: Session data not saving  
**Solution**: Check localStorage is enabled, export data regularly

**Problem**: SUS scores not calculating  
**Solution**: Ensure all 10 questions are answered with values 1-5

#### A/B Testing

**Problem**: Variant not persisting  
**Solution**: Check localStorage is enabled, verify test ID is consistent

**Problem**: Statistical significance not calculating  
**Solution**: Ensure sufficient sample size (minimum 30 per variant)

#### Metrics Analysis

**Problem**: Web Vitals not collecting  
**Solution**: Check browser supports PerformanceObserver API

**Problem**: Metrics not appearing  
**Solution**: Verify metrics collection is started, check localStorage

---

## 📈 Success Metrics

### Week 7-8 Goals

| Metric | Target | How to Measure |
|--------|--------|----------------|
| SUS Score | > 80 | SUS Questionnaire |
| NPS | > 35 | NPS Survey |
| Task Success Rate | > 90% | Usability Testing |
| TTV | < 10 min | Metrics Analysis |
| A/B Tests | 3+ tests | A/B Test Dashboard |
| Statistical Significance | p < 0.05 | A/B Test Results |

---

## 🤝 Contributing

When adding new features:

1. **Document thoroughly** - Add to this guide
2. **Test extensively** - Manual and automated tests
3. **Follow patterns** - Use existing code style
4. **Update metrics** - Track new features
5. **Share learnings** - Document insights

---

## 📞 Support

For questions or issues:

- **Documentation**: See [Week 7-8 Implementation Guide](../../docs/UX/WEEK_7_8_IMPLEMENTATION_GUIDE.md)
- **Issues**: Create GitHub issue with `ux` label
- **Slack**: #ux-research channel

---

**Last Updated**: 2025-10-23  
**Version**: 1.0  
**Status**: ✅ Complete
