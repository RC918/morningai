# Epic Workflow Guide

This guide explains how to use the Epic system for tracking large initiatives in MorningAI.

## Overview

Epics are high-level tracking issues that group related work across multiple phases. Each Epic follows a standardized Phase structure and integrates with GitHub Projects for progress tracking.

## Prerequisites

### gh CLI Installation

This guide uses the GitHub CLI (`gh`). Install it before proceeding:

```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
winget install GitHub.cli
```

After installation, authenticate:

```bash
gh auth login
```

### Required Permissions

To use all features in this guide, you need:

| Permission | Required For |
|------------|--------------|
| **Repository write access** | Creating issues, adding labels |
| **Project write access** | Adding items to project, editing fields |

> **Note**: If you don't have Project write access, ask a project admin to add issues for you, or request access via your team lead.

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
   <!-- Replace <issue-number> with actual issue number -->
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

All commands use placeholders. Replace them with actual values:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `<project-number>` | GitHub Project number | `1` |
| `<owner>` | Repository/org owner | `RC918` |
| `<repo>` | Repository name | `morningai` |
| `<issue-number>` | Issue number | `2304` |

```bash
# Create epic label (one-time setup)
gh label create epic --color "7057ff" --description "Epic tracking issue" --repo <owner>/<repo>
# Example: gh label create epic --color "7057ff" --description "Epic tracking issue" --repo RC918/morningai

# Add issue to project
gh project item-add <project-number> --owner <owner> --url https://github.com/<owner>/<repo>/issues/<issue-number>
# Example: gh project item-add 1 --owner RC918 --url https://github.com/RC918/morningai/issues/2304

# List project fields
gh project field-list <project-number> --owner <owner>
# Example: gh project field-list 1 --owner RC918

# View project items
gh project item-list <project-number> --owner <owner>
# Example: gh project item-list 1 --owner RC918
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `gh: command not found` | Install gh CLI (see Prerequisites) |
| `HTTP 403: Must have admin rights` | Request Project write access from admin |
| `Project not found` | Verify project number with `gh project list --owner <owner>` |
| `Field not found` | Field may have been renamed; check with `gh project field-list` |

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
