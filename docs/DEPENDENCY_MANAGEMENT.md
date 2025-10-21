# Dependency Management Guidelines

## 📦 Package Manager Policy

### Official Package Manager: npm

**Morning AI 專案統一使用 npm 作為唯一的依賴管理工具。**

### Why npm?

1. **一致性**：避免 pnpm/yarn/npm 混用導致的 lockfile 衝突
2. **CI/CD 穩定性**：GitHub Actions 與 Vercel 預設支援 npm
3. **團隊協作**：降低新成員學習成本
4. **生態系統**：最廣泛的支援與文檔

---

## 🚫 禁止使用的工具

### ❌ 不要使用 pnpm

```bash
# ❌ 錯誤
pnpm install
pnpm add package-name

# ✅ 正確
npm install
npm install package-name
```

### ❌ 不要使用 yarn

```bash
# ❌ 錯誤
yarn install
yarn add package-name

# ✅ 正確
npm install
npm install package-name
```

---

## 📋 標準操作流程

### 1. 安裝依賴

```bash
# 開發環境
npm install

# 生產環境
npm ci
```

### 2. 新增依賴

```bash
# 生產依賴
npm install package-name

# 開發依賴
npm install --save-dev package-name
```

### 3. 更新依賴

```bash
# 更新單一套件
npm update package-name

# 更新所有套件
npm update
```

### 4. 移除依賴

```bash
npm uninstall package-name
```

---

## 🔒 Lockfile 管理

### package-lock.json 是必須的

- ✅ **必須提交** `package-lock.json` 到 Git
- ❌ **禁止提交** `pnpm-lock.yaml` 或 `yarn.lock`
- ❌ **禁止在 .gitignore 排除** `package-lock.json`

### 為什麼需要 lockfile？

1. **版本鎖定**：確保所有環境使用相同版本
2. **可重現性**：CI/CD 與本地環境一致
3. **安全性**：防止依賴被惡意替換

---

## 🛠️ CI/CD 配置

### GitHub Actions

```yaml
- name: Install dependencies
  run: npm ci

- name: Cache npm dependencies
  uses: actions/cache@v3
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
```

### Vercel

```json
{
  "installCommand": "npm install --include=dev",
  "buildCommand": "npm run build"
}
```

---

## 🚨 常見問題與解決方案

### 問題 1: Vercel 使用 pnpm 導致部署失敗

**症狀**：
```
ERR_INVALID_THIS
Value of 'this' must be of type URLSearchParams
```

**根本原因**：
- Vercel Production Overrides 使用舊設定（pnpm install）
- .vercelignore 排除了 pnpm-lock.yaml
- 導致 pnpm 無法正確安裝依賴

**解決方案**：
1. 在 vercel.json 明確指定 `installCommand: "npm install --include=dev"`
2. 移除 rootDirectory，使用完整路徑
3. 清除 Vercel Production Overrides 的舊設定

### 問題 2: 本地與 CI 環境不一致

**症狀**：
- 本地測試通過，CI 失敗
- 依賴版本不一致

**解決方案**：
1. 確保 package-lock.json 已提交
2. CI 使用 `npm ci` 而非 `npm install`
3. 定期執行 `npm audit` 檢查安全性

### 問題 3: 多個 lockfile 衝突

**症狀**：
- 同時存在 package-lock.json 和 pnpm-lock.yaml
- Git 衝突頻繁

**解決方案**：
```bash
# 移除非 npm 的 lockfile
rm -f pnpm-lock.yaml yarn.lock

# 重新生成 package-lock.json
rm -rf node_modules package-lock.json
npm install

# 提交變更
git add package-lock.json
git commit -m "chore: 統一使用 npm，移除 pnpm lockfile"
```

---

## 📚 延伸閱讀

- [npm Documentation](https://docs.npmjs.com/)
- [package-lock.json 說明](https://docs.npmjs.com/cli/v9/configuring-npm/package-lock-json)
- [npm ci vs npm install](https://docs.npmjs.com/cli/v9/commands/npm-ci)

---

## 🔄 版本歷史

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2025-10-21 | 1.0.0 | 初版發布，統一使用 npm |

---

## 📞 聯絡資訊

如有任何疑問，請聯絡：
- **技術負責人**：Ryan Chen (@RC918)
- **問題回報**：GitHub Issues
