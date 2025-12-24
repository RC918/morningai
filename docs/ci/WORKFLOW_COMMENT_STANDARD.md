# CI Workflow Comment Standard

This document defines the standard patterns for GitHub Actions workflows that post comments on Pull Requests. Following these conventions ensures consistent behavior, prevents comment collisions between different bots, and maintains security best practices.

## Overview

All PR commenting workflows in this repository use the `peter-evans/find-comment` + `peter-evans/create-or-update-comment` pattern with hidden markers. This approach:

- Prevents duplicate comments (updates existing comment instead of creating new ones)
- Allows multiple workflows to post comments without overwriting each other
- Provides security against fork PR permission issues

## Hidden Marker Convention

### Format

Every workflow comment must include a unique hidden marker at the beginning of the comment body:

```
<!-- id: {workflow-name} -->
```

### Naming Rules

1. Use lowercase with hyphens (kebab-case)
2. Be descriptive but concise
3. Match the workflow's primary purpose
4. Ensure uniqueness across all workflows

### Current Markers in Use

| Workflow | Marker | Purpose |
|----------|--------|---------|
| design-system-audit.yml | `<!-- id: design-system-audit -->` | Design system audit results |
| design-system-audit.yml | `<!-- id: shared-ui-coverage-baseline -->` | Test coverage baseline |
| frontend.yml | `<!-- id: typescript-strict-progress -->` | TypeScript strict mode progress |
| enforce-shared-ui.yml | `<!-- id: shared-ui-import-audit -->` | Shared-UI import compliance |
| legacy-component-check.yml | `<!-- id: legacy-component-check -->` | Legacy component detection |
| storybook-coverage-check.yml | `<!-- id: storybook-coverage-check -->` | Storybook coverage check |
| token-sync-check.yml | `<!-- id: token-sync-check -->` | Token sync validation |
| lhci.yml | `<!-- id: lhci-report -->` | Lighthouse CI report |
| qwen-pr-review.yml | `<!-- id: qwen-ai-review -->` | Qwen AI code review |

## Implementation Pattern

### Standard Template

```yaml
# Step 1: Find existing comment by hidden marker
- name: Find existing comment
  if: github.event_name == 'pull_request' && github.event.pull_request.head.repo.fork == false
  uses: peter-evans/find-comment@v3
  id: find-comment
  with:
    issue-number: ${{ github.event.pull_request.number }}
    body-includes: "<!-- id: your-unique-marker -->"

# Step 2: Create or update the comment
- name: Post PR comment
  if: github.event_name == 'pull_request' && github.event.pull_request.head.repo.fork == false
  uses: peter-evans/create-or-update-comment@v4
  with:
    issue-number: ${{ github.event.pull_request.number }}
    comment-id: ${{ steps.find-comment.outputs.comment-id }}
    edit-mode: replace
    body: |
      <!-- id: your-unique-marker -->
      ## Your Comment Title
      
      Your comment content here...
```

### Key Points

1. **Always include fork guard**: `github.event.pull_request.head.repo.fork == false`
   - Fork PRs don't have write access to post comments
   - This prevents permission errors

2. **Use `edit-mode: replace`**: Ensures the entire comment is replaced, not appended

3. **Place marker at the start**: The hidden marker must be the first line of the comment body

4. **Use step ID for find-comment**: The `id` field (e.g., `find-comment`) is used to reference the output

5. **Handling Multiple Comments**: A single workflow can manage multiple distinct comments (e.g., `design-system-audit.yml` posts both audit results and coverage baseline). To do this, repeat the `find-comment` and `create-or-update-comment` steps for each unique comment marker. Ensure each `find-comment` step has a unique `id` so its output can be referenced correctly by the corresponding `create-or-update-comment` step.

## Security: Env Passthrough Pattern

When using untrusted inputs (like PR title, branch name, or user-provided data) in shell scripts, always pass them through environment variables to prevent script injection attacks.

### Correct Pattern

```yaml
- name: Check PR
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
    PR_LABELS: ${{ join(github.event.pull_request.labels.*.name, ',') }}
  run: |
    # Always quote variables in shell
    echo "PR Title: $PR_TITLE"
    
    # Safe to use in conditionals when quoted
    if [[ "$PR_TITLE" =~ "pattern" ]]; then
      echo "Match found"
    fi
```

### Dangerous Pattern (DO NOT USE)

```yaml
- name: Check PR
  run: |
    # DANGEROUS: Direct interpolation allows script injection
    PR_TITLE="${{ github.event.pull_request.title }}"
    
    # An attacker could set PR title to: "; rm -rf / #
    # This would execute arbitrary commands
```

### Why This Works

1. GitHub Actions evaluates `${{ }}` expressions before the shell runs
2. When using env vars, the value is passed as a string to the shell
3. Proper quoting (`"$VAR"`) prevents word splitting and glob expansion
4. The shell treats the entire value as a single string, not as code

## Fork PR Policy

### Behavior

- Fork PRs will **skip** PR commenting steps
- This is an intentional security measure
- Fork PRs don't have write access to the base repository

### Guard Condition

```yaml
if: github.event.pull_request.head.repo.fork == false
```

This condition:
- Returns `true` for PRs from branches in the same repository
- Returns `false` for PRs from forked repositories
- Does NOT affect internal feature branches (they are not forks)

## Smoke Test: Verifying Comment Update Behavior

After implementing or modifying a workflow comment, verify it works correctly:

### Test Procedure

1. **Create a test PR** that triggers the workflow
2. **Verify initial comment** appears with the hidden marker
3. **Push another commit** to the same PR
4. **Verify the comment is updated** (not duplicated)
   - Check the comment timestamp changed
   - Check there's only ONE comment with that marker
   - Check the content reflects the latest run

### What to Look For

- Only one comment per marker (no duplicates)
- Comment timestamp updates on each push
- Hidden marker is present at the start of the comment
- Fork PRs don't show errors (they just skip commenting)

## Migration Notes

### From `comment-tag` (Invalid Parameter)

The `comment-tag` parameter was never valid for `peter-evans/create-or-update-comment@v4`. If you see this in old workflows, migrate to the find-comment pattern.

### From `marocchino/sticky-pull-request-comment`

Replace with the peter-evans pattern. Note that:
- Old comments with `marocchino` won't be found by the new pattern
- First run after migration creates a new comment
- Subsequent runs update the new comment
- Consider manually cleaning up old duplicate comments

## Troubleshooting

### Multiple Comments Appearing

**Cause**: The hidden marker changed or was missing in previous runs.

**Solution**: 
1. Manually delete duplicate comments
2. Ensure the marker is consistent and at the start of the body

### Comment Not Updating

**Cause**: `find-comment` not finding the existing comment.

**Check**:
1. Marker spelling matches exactly
2. Marker is at the very start of the comment body
3. No extra whitespace before the marker

### Permission Errors on Fork PRs

**Cause**: Missing fork guard condition.

**Solution**: Add `github.event.pull_request.head.repo.fork == false` to the `if` condition.

## References

- [peter-evans/find-comment](https://github.com/peter-evans/find-comment)
- [peter-evans/create-or-update-comment](https://github.com/peter-evans/create-or-update-comment)
- PR #2893: Implementation of this standard
- Issue #2892: Original actionlint error fixes
