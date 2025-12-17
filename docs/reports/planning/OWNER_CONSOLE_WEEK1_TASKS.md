# Owner Console MVP - Week 1 任務清單

**日期**: 2025-11-01  
**CTO 審查**: 已完成  
**狀態**: 進行中

---

## 📋 總覽

### ✅ 已完成
- Backend v2 Auth 實作（已在 main 分支）
- Frontend auth.ts 模組（已在 main 分支）
- P0 部署閘門修復（已在 main 分支）
- 生產環境變數配置完成

### 🚧 待完成（預估 7-9 小時）
1. Task 1: Frontend Auth Integration (2-3 小時) - **P0 優先**
2. Task 5: Testing Framework (2 小時) - **P1**
3. Task 4: Connect Real APIs (1-2 小時) - **P1**
4. Task 3: 2FA TOTP 骨架 (2 小時) - **P1**

---

## Task 1: Frontend Auth Integration (P0)

**預估時間**: 2-3 小時  
**優先級**: P0 Critical  
**負責人**: Frontend Squad

### 🎯 目標
將 `owner-console/src/lib/auth.ts` 整合到 `App.jsx`，修復 3 個關鍵 bug。

### 📝 子任務

#### 1.1 修復 Bug #1: API 回應格式不一致

**檔案**: `handoff/20250928/40_App/owner-console/src/lib/auth.ts`  
**位置**: Line 261-292 (`refreshAccessToken` function)

**問題**:
- 後端回傳: `{ tokens: { expiresAt: 1234567890 } }`
- 前端預期: `{ expiresAt: 1234567890 }`

**修正**:
```typescript
// 當前（錯誤）- Line 283-287
const data: RefreshTokenResponse = await response.json();

const newTokens: AuthTokens = {
  expiresAt: data.expiresAt,  // ❌ data.expiresAt 是 undefined
};

// 修正後
const data = await response.json();

const newTokens: AuthTokens = {
  expiresAt: data.tokens.expiresAt,  // ✅ 正確路徑
};
```

**驗證**:
```bash
# 測試 refresh endpoint
curl -X POST https://your-backend.onrender.com/api/auth/v2/refresh \
  -H "Cookie: refresh_token=..." \
  -H "X-CSRF-Token: ..." \
  --cookie-jar cookies.txt
```

---

#### 1.2 修復 Bug #2: 缺少 CSRF Header

**檔案**: `handoff/20250928/40_App/owner-console/src/lib/auth.ts`  
**位置**: Line 270-276 (`refreshAccessToken`), Line 242-248 (`logout`)

**問題**:
- `refresh()` 和 `logout()` 是 POST 請求（unsafe methods）
- 當 `COOKIE_SAMESITE=None` 時，後端 CSRF middleware 會檢查 `X-CSRF-Token` header
- 前端未發送此 header → 403 Forbidden

**修正**:

1. 新增 helper function 讀取 CSRF token:
```typescript
// 在 auth.ts 頂部新增
function getCsrfTokenFromCookie(): string | null {
  if (typeof document === 'undefined') return null;
  
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token') {
      return decodeURIComponent(value);
    }
  }
  return null;
}
```

2. 修改 `refreshAccessToken()`:
```typescript
// Line 270-276
const response = await fetch(`${API_BASE_URL}/api/auth/v2/refresh`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': getCsrfTokenFromCookie() || '',  // ✅ 加入 CSRF header
  },
  credentials: 'include',
});
```

3. 修改 `logout()`:
```typescript
// Line 242-248
await fetch(`${API_BASE_URL}/api/auth/v2/logout`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': getCsrfTokenFromCookie() || '',  // ✅ 加入 CSRF header
  },
  credentials: 'include',
});
```

**驗證**:
```javascript
// 在 browser console 測試
document.cookie.split(';').find(c => c.includes('csrf_token'))
// 應該看到 csrf_token=xxx
```

---

#### 1.3 修復 Bug #3: CSRF Bootstrap

**檔案**: `handoff/20250928/40_App/owner-console/src/lib/auth.ts`  
**位置**: Line 375-387 (`initAuth` function)

**問題**:
- 當 `COOKIE_SAMESITE=None` 時，需要先呼叫 `/api/auth/v2/csrf` 取得 CSRF token
- 否則第一次 refresh/logout 會 403

**修正**:
```typescript
// Line 375-387
export function initAuth(): { isAuthenticated: boolean; user: User | null } {
  const authenticated = isAuthenticated();
  const user = getStoredUser();
  
  if (authenticated && user) {
    // ✅ 新增：Bootstrap CSRF token if needed
    const csrfToken = getCsrfTokenFromCookie();
    if (!csrfToken) {
      fetch(`${API_BASE_URL}/api/auth/v2/csrf`, { credentials: 'include' })
        .catch(err => console.error('Failed to bootstrap CSRF token:', err));
    }
    
    startTokenRefresh();
  }
  
  return {
    isAuthenticated: authenticated,
    user,
  };
}
```

---

#### 1.4 整合 App.jsx

**檔案**: `handoff/20250928/40_App/owner-console/src/App.jsx`  
**位置**: Line 14-61 (`AppContent` component)

**當前問題**:
```javascript
// Line 15: 硬編碼 authenticated = true
const [isAuthenticated, setIsAuthenticated] = useState(true)

// Line 16-22: 硬編碼 mock user
const [user, setUser] = useState({
  id: 'owner_dev',
  name: 'Ryan Chen',
  email: 'ryan@morningai.com',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
  role: 'Owner'
})
```

**修正**:
```javascript
import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import Sidebar from '@/components/Sidebar'
import LoginPage from '@/components/LoginPage'
import { initAuth, login, logout, cleanupAuth } from '@/lib/auth'  // ✅ 導入 auth
import './App.css'

const OwnerDashboard = lazy(() => import('@/pages/OwnerDashboard'))
const AgentGovernance = lazy(() => import('@/pages/AgentGovernance'))
const TenantManagement = lazy(() => import('@/pages/TenantManagement'))
const SystemMonitoring = lazy(() => import('@/pages/SystemMonitoring'))
const PlatformSettings = lazy(() => import('@/pages/PlatformSettings'))

function AppContent() {
  // ✅ 使用 initAuth() 初始化
  const authState = initAuth()
  const [isAuthenticated, setIsAuthenticated] = useState(authState.isAuthenticated)
  const [user, setUser] = useState(authState.user)

  // ✅ Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupAuth()
    }
  }, [])

  // ✅ 整合真實 login
  const handleLogin = async (credentials) => {
    try {
      const response = await login(credentials)
      setUser(response.user)
      setIsAuthenticated(true)
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  // ✅ 整合真實 logout
  const handleLogout = async () => {
    try {
      await logout()
      setUser(null)
      setIsAuthenticated(false)
    } catch (error) {
      console.error('Logout failed:', error)
      // Still clear local state even if API call fails
      setUser(null)
      setIsAuthenticated(false)
    }
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />
  }

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <Sidebar user={user} onLogout={handleLogout} />
        
        <main id="main-content" className="flex-1 overflow-y-auto" role="main">
          <Suspense fallback={<div className="flex items-center justify-center h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div></div>}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<OwnerDashboard />} />
              <Route path="/governance" element={<AgentGovernance />} />
              <Route path="/tenants" element={<TenantManagement />} />
              <Route path="/monitoring" element={<SystemMonitoring />} />
              <Route path="/settings" element={<PlatformSettings />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </Router>
  )
}

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <AppContent />
    </ThemeProvider>
  )
}

export default App
```

---

#### 1.5 更新 LoginPage

**檔案**: `handoff/20250928/40_App/owner-console/src/components/LoginPage.jsx`

**確認**:
- `onLogin` prop 接收 `{ email, password }` 並呼叫 `handleLogin(credentials)`
- 顯示錯誤訊息（如果 login 失敗）

**測試帳號**:
- Email: `owner@morningai.com`
- Password: `owner123`

---

### ✅ 驗收標準

- [ ] 可以使用 `owner@morningai.com` / `owner123` 登入
- [ ] 登入後顯示真實用戶資訊（從 `/api/auth/v2/me` 取得）
- [ ] Token 自動 refresh 運作正常（15 分鐘前自動刷新）
- [ ] Logout 清除 cookies 並導向登入頁
- [ ] 跨域請求帶上 cookies（檢查 Network tab 的 `Cookie` header）
- [ ] CSRF token 正確發送（檢查 Network tab 的 `X-CSRF-Token` header）
- [ ] 無 console errors

### 🧪 測試步驟

1. **本地測試**:
```bash
cd handoff/20250928/40_App/owner-console
pnpm dev
```

2. **登入測試**:
   - 開啟 http://localhost:5173
   - 輸入 owner@morningai.com / owner123
   - 檢查 Network tab:
     - POST /api/auth/v2/login → 200 OK
     - Response 包含 `Set-Cookie: access_token=...; HttpOnly`
     - Response 包含 `Set-Cookie: refresh_token=...; HttpOnly`

3. **Token Refresh 測試**:
   - 等待 10 分鐘（或修改 `TOKEN_REFRESH_BUFFER_MS` 為 1 分鐘測試）
   - 檢查 Network tab:
     - POST /api/auth/v2/refresh → 200 OK
     - Request 包含 `X-CSRF-Token` header
     - Response 包含新的 `Set-Cookie`

4. **Logout 測試**:
   - 點擊 Logout
   - 檢查 Network tab:
     - POST /api/auth/v2/logout → 200 OK
     - Request 包含 `X-CSRF-Token` header
   - 確認導向登入頁

---

## Task 5: Testing Framework (P1)

**預估時間**: 2 小時  
**優先級**: P1  
**負責人**: QA Squad

### 🎯 目標
安裝 Vitest，撰寫基本單元測試與 1 個 E2E 測試，達到 30% 覆蓋率。

### 📝 子任務

#### 5.1 安裝 Vitest

```bash
cd handoff/20250928/40_App/owner-console

# 安裝依賴
pnpm add -D vitest @vitest/ui @testing-library/react @testing-library/jest-dom jsdom
```

#### 5.2 配置 Vitest

**新增檔案**: `handoff/20250928/40_App/owner-console/vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData/',
        'dist/',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

**新增檔案**: `handoff/20250928/40_App/owner-console/src/test/setup.ts`

```typescript
import '@testing-library/jest-dom'
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Cleanup after each test
afterEach(() => {
  cleanup()
})
```

#### 5.3 撰寫單元測試

**新增檔案**: `handoff/20250928/40_App/owner-console/src/lib/auth.test.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  storeTokenExpiry,
  getStoredTokenExpiry,
  clearTokens,
  isTokenExpired,
  isAuthenticated,
  storeUser,
  getStoredUser,
} from './auth'

describe('Auth Utils', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('Token Expiry Management', () => {
    it('should store and retrieve token expiry', () => {
      const expiresAt = Date.now() + 60000
      storeTokenExpiry(expiresAt)
      expect(getStoredTokenExpiry()).toBe(expiresAt)
    })

    it('should return null when no token expiry stored', () => {
      expect(getStoredTokenExpiry()).toBeNull()
    })

    it('should clear token expiry', () => {
      storeTokenExpiry(Date.now() + 60000)
      clearTokens()
      expect(getStoredTokenExpiry()).toBeNull()
    })
  })

  describe('Token Expiration Check', () => {
    it('should return false for future expiry', () => {
      const futureExpiry = Date.now() + 60 * 60 * 1000 // 1 hour
      expect(isTokenExpired(futureExpiry)).toBe(false)
    })

    it('should return true for past expiry', () => {
      const pastExpiry = Date.now() - 1000 // 1 second ago
      expect(isTokenExpired(pastExpiry)).toBe(true)
    })

    it('should return true when close to expiry (within buffer)', () => {
      const closeExpiry = Date.now() + 4 * 60 * 1000 // 4 minutes (< 5 min buffer)
      expect(isTokenExpired(closeExpiry)).toBe(true)
    })
  })

  describe('Authentication Status', () => {
    it('should return false when no token stored', () => {
      expect(isAuthenticated()).toBe(false)
    })

    it('should return true when valid token stored', () => {
      const futureExpiry = Date.now() + 60 * 60 * 1000
      storeTokenExpiry(futureExpiry)
      expect(isAuthenticated()).toBe(true)
    })

    it('should return false when token expired', () => {
      const pastExpiry = Date.now() - 1000
      storeTokenExpiry(pastExpiry)
      expect(isAuthenticated()).toBe(false)
    })
  })

  describe('User Management', () => {
    it('should store and retrieve user', () => {
      const user = {
        id: 'test-id',
        email: 'test@example.com',
        role: 'owner' as const,
        tenantId: 'test-tenant',
        name: 'Test User',
      }
      storeUser(user)
      expect(getStoredUser()).toEqual(user)
    })

    it('should return null when no user stored', () => {
      expect(getStoredUser()).toBeNull()
    })

    it('should clear user data', () => {
      const user = {
        id: 'test-id',
        email: 'test@example.com',
        role: 'owner' as const,
        tenantId: 'test-tenant',
      }
      storeUser(user)
      clearTokens()
      expect(getStoredUser()).toBeNull()
    })
  })
})
```

#### 5.4 撰寫 E2E 測試

**新增檔案**: `handoff/20250928/40_App/owner-console/tests/auth.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:5000'

test.describe('Authentication Flow', () => {
  test('should complete full auth flow: login → me → refresh → logout', async ({ page }) => {
    // Navigate to app
    await page.goto('http://localhost:5173')

    // Should show login page
    await expect(page.locator('h1')).toContainText('Login')

    // Fill login form
    await page.fill('input[type="email"]', 'owner@morningai.com')
    await page.fill('input[type="password"]', 'owner123')

    // Submit login
    await page.click('button[type="submit"]')

    // Wait for redirect to dashboard
    await page.waitForURL('**/dashboard')

    // Verify authenticated state
    await expect(page.locator('text=Ryan Chen')).toBeVisible()

    // Check cookies are set
    const cookies = await page.context().cookies()
    const accessToken = cookies.find(c => c.name === 'access_token')
    const refreshToken = cookies.find(c => c.name === 'refresh_token')
    const csrfToken = cookies.find(c => c.name === 'csrf_token')

    expect(accessToken).toBeDefined()
    expect(refreshToken).toBeDefined()
    expect(csrfToken).toBeDefined()

    // Verify HttpOnly flags
    expect(accessToken?.httpOnly).toBe(true)
    expect(refreshToken?.httpOnly).toBe(true)
    expect(csrfToken?.httpOnly).toBe(false) // CSRF token needs to be readable by JS

    // Test logout
    await page.click('button:has-text("Logout")')

    // Should redirect to login
    await expect(page.locator('h1')).toContainText('Login')

    // Verify cookies are cleared
    const cookiesAfterLogout = await page.context().cookies()
    const accessTokenAfter = cookiesAfterLogout.find(c => c.name === 'access_token')
    expect(accessTokenAfter).toBeUndefined()
  })

  test('should handle invalid credentials', async ({ page }) => {
    await page.goto('http://localhost:5173')

    await page.fill('input[type="email"]', 'invalid@example.com')
    await page.fill('input[type="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')

    // Should show error message
    await expect(page.locator('text=Invalid')).toBeVisible()
  })
})
```

#### 5.5 更新 package.json

**檔案**: `handoff/20250928/40_App/owner-console/package.json`

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest run --coverage"
  }
}
```

### ✅ 驗收標準

- [ ] `pnpm test` 可以執行
- [ ] 所有單元測試通過（auth.test.ts）
- [ ] E2E 測試通過（auth.spec.ts）
- [ ] 覆蓋率 ≥ 30%（執行 `pnpm test:coverage` 檢查）
- [ ] CI 整合（可選，本週可先手動執行）

---

## Task 4: Connect Real APIs (P1)

**預估時間**: 1-2 小時  
**優先級**: P1  
**負責人**: Frontend Squad

### 🎯 目標
至少 1 個頁面連接真實 API，證明 auth 端到端運作。

### 📝 子任務

#### 4.1 選擇頁面

建議從 **OwnerDashboard** 開始（最簡單）。

#### 4.2 實作 API 呼叫

**檔案**: `handoff/20250928/40_App/owner-console/src/pages/OwnerDashboard.jsx`

**新增**:
```javascript
import { useState, useEffect } from 'react'
import { getCurrentUser } from '@/lib/auth'

function OwnerDashboard() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchUser() {
      try {
        const userData = await getCurrentUser()
        setUser(userData)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchUser()
  }, [])

  if (loading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error: {error}</div>
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Owner Dashboard</h1>
      
      {/* Display real user data */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h2 className="text-lg font-semibold mb-2">Current User</h2>
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-gray-500">Name</dt>
            <dd className="font-medium">{user?.name}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Email</dt>
            <dd className="font-medium">{user?.email}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Role</dt>
            <dd className="font-medium">{user?.role}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Tenant ID</dt>
            <dd className="font-medium">{user?.tenantId}</dd>
          </div>
        </dl>
      </div>

      {/* Rest of dashboard content */}
      {/* ... */}
    </div>
  )
}

export default OwnerDashboard
```

### ✅ 驗收標準

- [ ] OwnerDashboard 顯示真實用戶資訊（從 `/api/auth/v2/me`）
- [ ] Loading 狀態正確顯示
- [ ] Error 處理正確（如果 API 失敗）
- [ ] 401 錯誤會觸發 token refresh 或導向登入

---

## Task 3: 2FA TOTP 骨架 (P1)

**預估時間**: 2 小時  
**優先級**: P1  
**負責人**: Backend + Frontend Squad

### 🎯 目標
實作 2FA 的基本流程骨架（本週完成基本架構，下週完善實作）。

### 📝 子任務

#### 3.1 Backend Endpoints（Stub 實作）

**新增檔案**: `handoff/20250928/40_App/api-backend/src/routes/auth_2fa.py`

```python
"""
2FA TOTP Implementation (Stub)
Week 1: Basic structure
Week 2: Full implementation with pyotp
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

auth_2fa_bp = Blueprint('auth_2fa', __name__)


@auth_2fa_bp.route('/setup', methods=['GET'])
def setup_2fa():
    """
    Generate TOTP secret and QR code URL
    
    Response:
        {
            "secret": "BASE32_SECRET",
            "otpauthUrl": "otpauth://totp/MorningAI:user@example.com?secret=...",
            "qrCodeUrl": "https://api.qrserver.com/v1/create-qr-code/?data=..."
        }
    """
    # TODO Week 2: Generate real TOTP secret with pyotp
    mock_secret = "JBSWY3DPEHPK3PXP"
    user_email = "owner@morningai.com"  # TODO: Get from JWT
    
    otpauth_url = f"otpauth://totp/MorningAI:{user_email}?secret={mock_secret}&issuer=MorningAI"
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={otpauth_url}"
    
    return jsonify({
        'secret': mock_secret,
        'otpauthUrl': otpauth_url,
        'qrCodeUrl': qr_code_url
    }), 200


@auth_2fa_bp.route('/verify', methods=['POST'])
def verify_2fa():
    """
    Verify TOTP code
    
    Request:
        {
            "code": "123456"
        }
    
    Response:
        {
            "valid": true
        }
    """
    data = request.get_json()
    code = data.get('code')
    
    if not code or len(code) != 6:
        return jsonify({'message': 'Invalid code format'}), 400
    
    # TODO Week 2: Verify with pyotp
    # For now, accept any 6-digit code
    is_valid = code.isdigit()
    
    return jsonify({'valid': is_valid}), 200


@auth_2fa_bp.route('/enable', methods=['POST'])
def enable_2fa():
    """
    Enable 2FA for user
    
    Request:
        {
            "code": "123456"
        }
    """
    data = request.get_json()
    code = data.get('code')
    
    # TODO Week 2: Verify code and update user in database
    
    return jsonify({'message': '2FA enabled successfully'}), 200


@auth_2fa_bp.route('/disable', methods=['POST'])
def disable_2fa():
    """
    Disable 2FA for user
    
    Request:
        {
            "code": "123456"
        }
    """
    data = request.get_json()
    code = data.get('code')
    
    # TODO Week 2: Verify code and update user in database
    
    return jsonify({'message': '2FA disabled successfully'}), 200
```

**註冊 Blueprint**: `handoff/20250928/40_App/api-backend/src/main.py`

```python
from src.routes.auth_2fa import auth_2fa_bp

app.register_blueprint(auth_2fa_bp, url_prefix='/api/auth/v2/2fa')
```

#### 3.2 Frontend UI（基本流程）

**新增檔案**: `handoff/20250928/40_App/owner-console/src/components/TwoFactorSetup.jsx`

```javascript
import { useState } from 'react'

function TwoFactorSetup({ onComplete }) {
  const [step, setStep] = useState('setup') // 'setup' | 'verify' | 'complete'
  const [secret, setSecret] = useState('')
  const [qrCodeUrl, setQrCodeUrl] = useState('')
  const [code, setCode] = useState('')
  const [error, setError] = useState('')

  const handleSetup = async () => {
    try {
      const response = await fetch('/api/auth/v2/2fa/setup', {
        credentials: 'include'
      })
      const data = await response.json()
      setSecret(data.secret)
      setQrCodeUrl(data.qrCodeUrl)
      setStep('verify')
    } catch (err) {
      setError('Failed to setup 2FA')
    }
  }

  const handleVerify = async () => {
    try {
      const response = await fetch('/api/auth/v2/2fa/enable', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ code })
      })
      
      if (response.ok) {
        setStep('complete')
        onComplete?.()
      } else {
        setError('Invalid code')
      }
    } catch (err) {
      setError('Failed to enable 2FA')
    }
  }

  if (step === 'setup') {
    return (
      <div className="p-6">
        <h2 className="text-xl font-bold mb-4">Enable Two-Factor Authentication</h2>
        <p className="mb-4">Add an extra layer of security to your account.</p>
        <button 
          onClick={handleSetup}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Get Started
        </button>
      </div>
    )
  }

  if (step === 'verify') {
    return (
      <div className="p-6">
        <h2 className="text-xl font-bold mb-4">Scan QR Code</h2>
        <div className="mb-4">
          <img src={qrCodeUrl} alt="QR Code" className="mx-auto" />
        </div>
        <p className="text-sm text-gray-600 mb-2">Or enter this code manually:</p>
        <code className="block bg-gray-100 p-2 rounded mb-4">{secret}</code>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Enter 6-digit code from your authenticator app:
          </label>
          <input
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            maxLength={6}
            className="w-full px-3 py-2 border rounded"
            placeholder="123456"
          />
        </div>
        
        {error && <p className="text-red-600 mb-4">{error}</p>}
        
        <button 
          onClick={handleVerify}
          disabled={code.length !== 6}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Verify and Enable
        </button>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">2FA Enabled!</h2>
      <p>Two-factor authentication has been successfully enabled for your account.</p>
    </div>
  )
}

export default TwoFactorSetup
```

### ✅ 驗收標準

- [ ] 可以進入 2FA 設定流程
- [ ] 顯示 QR code 和 manual entry key
- [ ] 可以輸入 6 位數驗證碼
- [ ] 驗證流程可以通過（即使是 stub 實作）
- [ ] UI 流程完整（setup → verify → complete）

---

## 📊 進度追蹤

### Week 1 Checklist

- [ ] Task 1: Frontend Auth Integration (P0)
  - [ ] Bug #1: API 回應格式修正
  - [ ] Bug #2: CSRF header 加入
  - [ ] Bug #3: CSRF bootstrap
  - [ ] App.jsx 整合
  - [ ] 端到端測試通過

- [ ] Task 5: Testing Framework (P1)
  - [ ] Vitest 安裝與配置
  - [ ] auth.test.ts 單元測試
  - [ ] auth.spec.ts E2E 測試
  - [ ] 覆蓋率 ≥ 30%

- [ ] Task 4: Connect Real APIs (P1)
  - [ ] OwnerDashboard 連接 /api/auth/v2/me
  - [ ] 顯示真實用戶資訊
  - [ ] Error handling

- [ ] Task 3: 2FA TOTP 骨架 (P1)
  - [ ] Backend endpoints (stub)
  - [ ] Frontend UI (基本流程)
  - [ ] 端到端流程可運作

### 預估完成時間

- **最快**: 7 小時（如果一切順利）
- **預期**: 9 小時（包含測試與 debug）
- **最慢**: 12 小時（如果遇到跨域問題或其他阻塞）

---

## 🚨 已知風險與緩解措施

### 風險 1: 跨域 Cookies 問題

**症狀**: Cookies 未在 Vercel ↔ Render 之間傳遞

**檢查**:
```javascript
// 在 browser console
document.cookie
// 應該看到 access_token, refresh_token, csrf_token
```

**緩解**:
- 確認 `COOKIE_SAMESITE=None`
- 確認 `COOKIE_SECURE=true`
- 確認 `COOKIE_DOMAIN=.gm365.me`（或正確的 apex domain）

### 風險 2: CSRF 403 錯誤

**症狀**: refresh/logout 回傳 403 Forbidden

**檢查**:
```javascript
// 在 Network tab 檢查 Request Headers
X-CSRF-Token: xxx  // 應該存在
```

**緩解**:
- 確認 `getCsrfTokenFromCookie()` 正確讀取 cookie
- 確認所有 POST/PUT/PATCH/DELETE 請求都加入 `X-CSRF-Token` header

### 風險 3: Token Refresh 循環

**症狀**: 無限 refresh 請求

**檢查**:
- 確認 `refreshAccessToken()` 正確解析 `data.tokens.expiresAt`
- 確認 `storeTokenExpiry()` 正確儲存新的 expiry

**緩解**:
- 修復 Bug #1（API 回應格式）
- 加入 debug logging

---

## 📞 支援與聯絡

**CTO**: @RC918  
**技術問題**: 請在 PR 留言或 Slack #owner-console-dev  
**緊急問題**: 直接聯絡 CTO

---

**最後更新**: 2025-11-01  
**版本**: 1.0
