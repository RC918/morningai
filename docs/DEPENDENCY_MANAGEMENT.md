# Dependency Management Guidelines

## 📦 Package Manager Policy

### Official Package Manager: pnpm

**Morning AI 專案統一使用 pnpm 作為依賴管理工具。**

> **政策變更**: 2025-10-24 從 npm 遷移到 pnpm  
> **理由**: 參見 [ADR-001: 遷移到 pnpm + Turborepo](../docs/adr/001-pnpm-turborepo-migration.md)

### Why pnpm?

1. **性能優異**：安裝速度比 npm 快 2-3 倍（12.8s vs 30-40s）
2. **磁碟空間節省**：content-addressable storage 節省 60-70% 空間
3. **依賴隔離**：嚴格的 node_modules 結構，防止 phantom dependencies
4. **Monorepo 支持**：原生 workspaces 功能，與 Turborepo 完美整合
5. **生態系統**：Vercel、Next.js、Vue、Svelte 等大型項目都使用 pnpm

---

## ✅ 推薦使用的工具

### ✅ pnpm（包管理器）

```bash
# ✅ 正確
pnpm install
pnpm add package-name
pnpm remove package-name
```

### ✅ Turborepo（構建系統）

```bash
# ✅ 正確
pnpm build        # 構建所有應用
pnpm dev          # 開發所有應用
pnpm test         # 測試所有應用
```

### ❌ 不要使用 npm 或 yarn

```bash
# ❌ 錯誤
npm install
yarn install

# ✅ 正確
pnpm install
```

---

## 📋 標準操作流程

### 1. 安裝依賴

```bash
# 開發環境
pnpm install

# 生產環境（CI）
pnpm install --frozen-lockfile
```

### 2. 新增依賴

```bash
# 生產依賴
pnpm add package-name

# 開發依賴
pnpm add -D package-name

# 為特定 workspace 添加依賴
pnpm add package-name --filter frontend-dashboard
```

### 3. 更新依賴

```bash
# 更新單一套件
pnpm update package-name

# 更新所有套件
pnpm update

# 互動式更新
pnpm update -i
```

### 4. 移除依賴

```bash
pnpm remove package-name

# 從特定 workspace 移除
pnpm remove package-name --filter frontend-dashboard
```

### 5. Workspace 操作

```bash
# 在所有 workspaces 執行命令
pnpm -r build

# 在特定 workspace 執行命令
pnpm --filter frontend-dashboard dev

# 執行根目錄腳本
pnpm build:all
```

---

## 🔒 Lockfile 管理

### pnpm-lock.yaml 是必須的

- ✅ **必須提交** `pnpm-lock.yaml` 到 Git
- ❌ **禁止提交** `package-lock.json` 或 `yarn.lock`
- ❌ **禁止在 .gitignore 排除** `pnpm-lock.yaml`

### 為什麼需要 lockfile？

1. **版本鎖定**：確保所有環境使用相同版本
2. **可重現性**：CI/CD 與本地環境一致
3. **安全性**：防止依賴被惡意替換
4. **性能優化**：pnpm 使用 lockfile 實現快速安裝

---

## 🛠️ CI/CD 配置

### GitHub Actions

```yaml
- name: Setup pnpm
  uses: pnpm/action-setup@v4
  with:
    version: 9.15.1

- name: Install dependencies
  run: pnpm install --frozen-lockfile

- name: Cache pnpm dependencies
  uses: actions/cache@v3
  with:
    path: ~/.pnpm-store
    key: ${{ runner.os }}-pnpm-${{ hashFiles('**/pnpm-lock.yaml') }}
```

### Vercel

```json
{
  "installCommand": "pnpm install",
  "buildCommand": "pnpm build"
}
```

### Turborepo

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"]
    },
    "dev": {
      "cache": false
    }
  }
}
```

---

## 🚨 常見問題與解決方案

### 問題 1: pnpm 安裝失敗

**症狀**：
```
ERR_PNPM_NO_MATCHING_VERSION
```

**解決方案**：
```bash
# 確保使用正確的 pnpm 版本
pnpm --version  # 應該是 9.15.1

# 如果版本不對，重新安裝
npm install -g pnpm@9.15.1
```

### 問題 2: 本地與 CI 環境不一致

**症狀**：
- 本地測試通過，CI 失敗
- 依賴版本不一致

**解決方案**：
1. 確保 pnpm-lock.yaml 已提交
2. CI 使用 `pnpm install --frozen-lockfile`
3. 定期執行 `pnpm audit` 檢查安全性

### 問題 3: Phantom Dependencies

**症狀**：
- 代碼 import 了未在 package.json 聲明的依賴
- 本地可以運行，但 CI 失敗

**解決方案**：
```bash
# pnpm 的嚴格模式會自動檢測
# 將缺失的依賴添加到 package.json
pnpm add missing-package
```

### 問題 4: 從 npm 遷移到 pnpm

**步驟**：
```bash
# 1. 移除舊的 lockfile 和 node_modules
rm -rf node_modules package-lock.json

# 2. 安裝 pnpm
npm install -g pnpm@9.15.1

# 3. 生成 pnpm-lock.yaml
pnpm install

# 4. 測試所有應用
pnpm build
pnpm test

# 5. 提交變更
git add pnpm-lock.yaml .npmrc pnpm-workspace.yaml
git commit -m "chore: 遷移到 pnpm"
```

---

## 📚 延伸閱讀

- [pnpm Documentation](https://pnpm.io/)
- [pnpm Workspaces](https://pnpm.io/workspaces)
- [Turborepo Documentation](https://turbo.build/repo/docs)
- [Why pnpm?](https://pnpm.io/motivation)
- [pnpm vs npm vs yarn](https://pnpm.io/benchmarks)

---

## 🔄 版本歷史

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2025-10-24 | 2.0.0 | 遷移到 pnpm + Turborepo，提升性能 2-10x |
| 2025-10-21 | 1.0.0 | 初版發布，統一使用 npm |

---

## 📞 聯絡資訊

如有任何疑問，請聯絡：
- **技術負責人**：Ryan Chen (@RC918)
- **問題回報**：GitHub Issues
