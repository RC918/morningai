# Architecture Overview
- 前端：Vite/React（PWA/RWD）
- 後端：Flask（/healthz 斷言、OpenAPI authority）、Redis Queue、Supabase
- Orchestrator：LangGraph/LangChain、GitHub API、pgvector 記憶
- CI/CD：post-deploy 健康斷言、coverage gate（每週 +5%）
目錄導覽：handoff/20250928/40_App/...、docs/...
