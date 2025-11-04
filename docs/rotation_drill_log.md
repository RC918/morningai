# Secret Rotation Drill Log

This log tracks quarterly rotation drills to verify procedures and SLO achievability.

**Related Documentation**: [Secret Rotation Policy](./SECRET_ROTATION_POLICY.md) - Section 8 (Quarterly Rotation Drills)

---

## Drill Log

| Date | Quarter | Secrets Rotated | Tier 1 Time | Tier 2 Time | Issues | Procedure Updates | Participants |
|------|---------|----------------|-------------|-------------|--------|-------------------|--------------|
| YYYY-MM-DD | Q# YYYY | SECRET1, SECRET2 | Xh Ym | Xh Ym | None / Description | ✅ No changes / ⚠️ Updated | Names |

---

## Instructions

1. **Schedule drills**: 2 weeks before actual quarterly rotation
2. **Environment**: Always use staging environment (never production)
3. **Scope**: Rotate 2 representative secrets (1 Tier 1 + 1 Tier 2)
4. **Record times**: Document actual time taken vs. SLO targets
5. **Document issues**: Note any problems, blockers, or deviations from procedures
6. **Update procedures**: If issues found, update rotation procedures and note here

## SLO Targets

- **Tier 1 (Critical)**: 4h target, 8h maximum
- **Tier 2 (Secret)**: 8h target, 24h maximum

## Example Entries

| Date | Quarter | Secrets Rotated | Tier 1 Time | Tier 2 Time | Issues | Procedure Updates | Participants |
|------|---------|----------------|-------------|-------------|--------|-------------------|--------------|
| 2025-01-15 | Q1 2025 | JWT_SECRET_KEY, REDIS_URL | 2.5h | 1.5h | None | ✅ No changes needed | CTO, DevOps Lead |
| 2025-04-15 | Q2 2025 | DATABASE_URL, CLOUDFLARE_API_TOKEN | 3.5h | 2h | DATABASE_URL took longer due to multi-service coordination | ⚠️ Updated DATABASE_URL procedure with parallel deployment steps | CTO, DevOps Lead, Backend Dev |

---

**Last Updated**: 2025-11-03  
**Maintained By**: CTO + DevOps Team  
**Next Drill**: Q1 2026 (mid-January 2026)
