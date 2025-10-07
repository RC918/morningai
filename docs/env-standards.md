# Environment Variables Standard
| Name              | Service(s)                  | Required | Default | Secret? | Notes |
|-------------------|-----------------------------|----------|---------|---------|------|
| JWT_SECRET_KEY    | backend, e2e workflows      | Yes      | –       | Yes     | HS256 signing key |
| REDIS_URL         | backend, worker             | Yes      | –       | Yes     | Must match DB index across services |
| RQ_QUEUE_NAME     | backend, worker             | Yes      | orchestrator | No  | Queue name must match |
| RQ_SERIALIZER     | backend, worker             | Yes      | json    | No      | Must be `json` for both |
| SENTRY_DSN        | all                         | Optional | –       | Yes     | Required for Sentry smoke/alerts |
| SUPABASE_URL      | frontend/backend (if used)  | Optional | –       | No      |  |
| SUPABASE_KEY      | frontend/backend (if used)  | Optional | –       | Yes     | Use anon/service_role appropriately |

> 管理規範：
> - 所有 Secrets 一律放 GitHub Repo Secrets（或 Render 的環境變數管理）。
> - 發版前以 workflow 檢查必填變數是否存在（缺失則 fail）。
> - 變更必須在此文件更新並提報到發版 Release notes。
