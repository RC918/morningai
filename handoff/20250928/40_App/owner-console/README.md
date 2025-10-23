# MorningAI Owner Console

**独立的平台管理控制台，专为 Owner 角色设计**

## 概述

Owner Console 是 MorningAI 平台的独立管理界面，与租户 Dashboard 完全分离。它提供平台级别的管理功能，包括：

- **Agent Governance**: 监控 agent 信誉、权限和合规性
- **Tenant Management**: 管理租户账户和权限
- **System Monitoring**: 监控系统健康状况和性能指标
- **Platform Settings**: 配置平台级设置和策略

## 架构设计

### 三层分离架构

```
┌─────────────────────────────────────────────────────────┐
│                    Owner Console                         │
│  (独立应用 - 仅 Owner 角色可访问)                        │
│  - Agent Governance                                      │
│  - Tenant Management                                     │
│  - System Monitoring                                     │
│  - Platform Settings                                     │
└─────────────────────────────────────────────────────────┘
                            │
                            │ API Calls
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   API Backend                            │
│  (共享后端 - 基于角色的权限控制)                         │
│  - /api/governance/* (Owner only)                        │
│  - /api/tenants/* (Owner only)                           │
│  - /api/monitoring/* (Owner only)                        │
└─────────────────────────────────────────────────────────┘
                            │
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Tenant Dashboard                         │
│  (租户应用 - 租户用户可访问)                             │
│  - Dashboard                                             │
│  - Strategies                                            │
│  - Approvals                                             │
│  - History                                               │
│  - Costs                                                 │
└─────────────────────────────────────────────────────────┘
```

### 权限分离

- **Owner Console**: 
  - 只有 `role: 'Owner'` 的用户可以访问
  - 使用独立的认证 token (`owner_auth_token`)
  - 可以管理所有租户和系统设置
  
- **Tenant Dashboard**: 
  - 租户用户可以访问
  - 使用租户认证 token (`auth_token`)
  - 只能访问自己租户的数据

## 技术栈

- **Frontend**: React 19 + Vite
- **UI Components**: Radix UI + Tailwind CSS
- **Routing**: React Router v7
- **State Management**: Zustand
- **Design System**: 基于 `/docs/UX/` 的设计规范

## 开发

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 环境变量

创建 `.env.local` 文件（**不要提交到 git**）：

```env
# API Configuration
VITE_API_BASE_URL=https://morningai-backend-v2.onrender.com
VITE_OWNER_CONSOLE=true

# Tolgee Translation Management (可选 - 应用在没有这些变量时仍可正常运作)
VITE_TOLGEE_API_URL=https://app.tolgee.io
VITE_TOLGEE_API_KEY=your_api_key_here
VITE_TOLGEE_PROJECT_ID=your_project_id_here
```

**Tolgee 配置说明**：
- 这些变量是可选的，应用在没有它们的情况下会使用本地 JSON 翻译文件
- 如需使用 in-context 翻译编辑功能（Alt+T），请设置这些变量
- 详细设置指南请参考：[Tolgee 设置文档](/docs/TOLGEE_SETUP.md)

## 部署

Owner Console 应该部署到独立的 URL，例如：

- **Owner Console**: `admin.morningai.com` 或 `owner.morningai.com`
- **Tenant Dashboard**: `dashboard.morningai.com` 或 `app.morningai.com`

这样可以确保：
1. 清晰的角色分离
2. 独立的安全策略
3. 不同的访问控制

## UI/UX 设计

Owner Console 使用与 Tenant Dashboard 相同的设计系统，但有以下区别：

- **主题色**: 使用紫色 (purple) 而不是蓝色 (blue)，以区分 Owner 和租户界面
- **图标**: 使用 Shield、Users、Activity 等管理相关图标
- **布局**: 保持一致的 Sidebar + Main Content 布局

## 功能模块

### 1. Agent Governance (已实现)

从 PR #618 恢复的完整 Agent Governance 功能：

- Agent 信誉排行榜
- 权限级别管理
- 事件历史记录
- 违规监控

### 2. Tenant Management (基础实现)

- 租户列表和状态
- 添加/编辑租户
- 租户权限管理

### 3. System Monitoring (基础实现)

- API 服务健康状况
- 数据库性能指标
- Worker 节点状态

### 4. Platform Settings (基础实现)

- 平台级配置
- 安全策略设置
- 系统参数管理

## 与 Tenant Dashboard 的区别

| 特性 | Owner Console | Tenant Dashboard |
|------|---------------|------------------|
| 访问权限 | Owner only | Tenant users |
| URL | admin.morningai.com | dashboard.morningai.com |
| 主题色 | Purple | Blue |
| 功能范围 | 平台管理 | 租户功能 |
| Agent Governance | ✅ 完整访问 | ❌ 不可见 |
| Tenant Management | ✅ 管理所有租户 | ❌ 不可见 |
| Dashboard | ✅ 平台概览 | ✅ 租户数据 |

## 下一步

1. ✅ 创建独立的 Owner Console 应用
2. ✅ 实现核心页面和组件
3. ✅ 恢复 Agent Governance 功能
4. ⏳ 实现完整的权限验证逻辑
5. ⏳ 连接真实的 API endpoints
6. ⏳ 添加完整的测试覆盖
7. ⏳ 部署到生产环境

## 相关文档

- [UX Design System](/docs/UX/README.md)
- [Design Tokens](/docs/UX/tokens.json)
- [Components Guide](/docs/UX/Design System/Components.md)
- [API Documentation](/handoff/20250928/40_App/30_API/openapi/)
