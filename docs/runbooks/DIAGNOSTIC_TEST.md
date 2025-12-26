# Diagnostic Test Document

This document is created to trigger the MorningAI Reviewer Agent and capture diagnostic logs for 422 debugging.

## Purpose

Test the diagnostic logging added in PR #3056 to investigate why inline comments fail with 422 errors in production.

## Expected Behavior

When this PR is opened, the MorningAI Reviewer Agent should:
1. Generate a code review using the LLM (Qwen-Plus)
2. Log diagnostic information at 4 key points:
   - `[Reviewer] DIAGNOSTIC: LLM raw comment output`
   - `[Publisher] DIAGNOSTIC: Diff coverage for validation`
   - `[Publisher] DIAGNOSTIC: Comment X validation check`
   - `[GitHub] DIAGNOSTIC: Final payload`

## Investigation

We are investigating why:
- Staging (OpenAI model) successfully posts inline comments
- Production (Qwen model) encounters 422 "Line could not be resolved" errors

Hypothesis: Model variance in line number semantics between OpenAI and Qwen.
