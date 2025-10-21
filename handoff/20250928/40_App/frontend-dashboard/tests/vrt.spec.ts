import { test, expect } from '@playwright/test'

async function setAuthToken(page) {
  await page.addInitScript(() => {
    try {
      window.localStorage.setItem('auth_token', 'test-token')
    } catch {}
  })
}

test('[@vrt] Landing page visual baseline', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/MorningAI/i)
  await expect(page).toHaveScreenshot({ fullPage: true })
})

test('[@vrt] Login page visual baseline', async ({ page }) => {
  await page.goto('/login')
  await expect(page.locator('form')).toBeVisible()
  await expect(page).toHaveScreenshot({ fullPage: true })
})

test('[@vrt] Dashboard page visual baseline (with auth)', async ({ page }) => {
  await setAuthToken(page)
  await page.goto('/dashboard')
  await expect(page).toHaveScreenshot({ fullPage: true })
})
