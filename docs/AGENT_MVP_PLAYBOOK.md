# Agent MVP（閉環）
場景：客服知識庫更新 → 產出 FAQ → 開 PR → CI → Deploy
Orchestrator：CodeWriter（PR）、Auto-QA（CI）、Deploy Agent（發佈）
驗收：/agent/tasks 可見 log/DAG；PR 自動合入；post-deploy 綠燈
