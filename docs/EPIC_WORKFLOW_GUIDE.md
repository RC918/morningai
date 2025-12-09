# Epic Workflow Guide

This guide explains how to use the Epic system for tracking large initiatives in MorningAI.

## Overview

Epics are high-level tracking issues that group related work across multiple phases. Each Epic follows a standardized Phase structure and integrates with GitHub Projects for progress tracking.

## Creating an Epic

### Using the Epic Template

1. Go to [New Issue](https://github.com/RC918/morningai/issues/new/choose)
2. Select **Epic** template
3. Fill in the required fields:
   - **Title**: Use format `[Epic] Your Epic Title`
   - **Overview**: Brief description of goals and scope
   - **Priority**: Select P0-P3
4. Add child issues to each Phase section using task list syntax:
   ```markdown
   - [ ] #1234 - Description of the task
   ```

### Phase Structure

Every Epic should have 4 phases:

| Phase | Purpose | Examples |
|-------|---------|----------|
| **Phase 0: Foundation** | Infrastructure and prerequisites | Token unification, CSS variables |
| **Phase 1: Core** | Main components and features | New components, core logic |
| **Phase 2: Integration** | Migration and integration work | Page migrations, API integration |
| **Phase 3: Governance** | Documentation, testing, rules | Storybook, tests, governance docs |

## GitHub Project Integration

### Project Fields

The **MorningAI MVP Project** has the following fields for Epic tracking:

| Field | Type | Options |
|-------|------|---------|
| **Type** | Single Select | Epic, Task, Bug, Feature |
| **Phase** | Single Select | Phase 0: Foundation, Phase 1: Core, Phase 2: Integration, Phase 3: Governance |
| **Priority** | Single Select | P0, P1, P2, P3 |
| **Status** | Single Select | (Project default statuses) |

### Adding Issues to Project

When creating child issues for an Epic:

1. Add the issue to the project: `gh project item-add 1 --owner RC918 --url <issue-url>`
2. Set the Phase field to match the Epic's phase structure
3. Link the issue in the Epic's checklist

### Tracking Progress

- Use the **Sub-issues progress** field to see completion percentage
- Group by **Phase** to see progress per phase
- Filter by **Type = Epic** to see all Epics

## Labels

| Label | Description |
|-------|-------------|
| `epic` | Applied automatically to all Epics created with the template |

## Best Practices

1. **One Epic per initiative**: Don't create multiple Epics for the same work
2. **Keep phases balanced**: Aim for 2-5 issues per phase
3. **Update checklists**: Mark items as complete when child issues are closed
4. **Link dependencies**: Note cross-Epic dependencies in the Dependencies section
5. **Regular reviews**: Review Epic progress weekly

## CLI Commands

```bash
# Create epic label (already done)
gh label create epic --color "7057ff" --description "Epic tracking issue"

# Add issue to project
gh project item-add 1 --owner RC918 --url https://github.com/RC918/morningai/issues/XXXX

# List project fields
gh project field-list 1 --owner RC918

# View project items
gh project item-list 1 --owner RC918
```

## Example Epic

See [#2304 - UI/UX 系統化標準化計畫](https://github.com/RC918/morningai/issues/2304) for a complete example of an Epic with:
- 4 phases (Phase 0-3)
- 12 child issues
- Clear acceptance criteria per phase
- Dependencies documented

## Future Enhancements

The following automation features are planned for future implementation:

- [ ] Auto-add issues with `epic` label to Roadmap project
- [ ] Auto-calculate Epic completion percentage
- [ ] Auto-archive Epics when 100% complete
- [ ] Gantt chart view for Epic timelines
