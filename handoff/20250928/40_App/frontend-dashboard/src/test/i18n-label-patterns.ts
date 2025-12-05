/**
 * i18n Label Patterns for Testing
 *
 * These regex patterns are used with @testing-library's getByLabelText
 * to query form fields in a way that works with both:
 * - i18n translation keys (e.g., "auth.login.email")
 * - Translated text in any supported language (e.g., "Email", "電子郵件")
 *
 * Pattern Design Principles:
 * 1. Use anchored patterns (^ and $) to prevent false matches
 * 2. Include i18n key as first alternative for test environments
 * 3. Include all supported language translations
 * 4. Use case-insensitive matching (/i flag)
 *
 * @see docs/testing/TEST_CONVENTIONS.md for usage guidelines
 */

// =============================================================================
// LoginPage Field Patterns
// =============================================================================

/**
 * Matches: "auth.login.email", "Email", "電子郵件"
 * Used for: LoginPage email input field
 */
export const LOGIN_EMAIL_LABEL = /^auth\.login\.email$|^Email$|^電子郵件$/i

/**
 * Matches: "auth.login.password", "Password", "密碼"
 * Used for: LoginPage password input field
 * Note: Anchored to prevent matching "Confirm Password" or "confirmPassword"
 */
export const LOGIN_PASSWORD_LABEL = /^auth\.login\.password$|^Password$|^密碼$/i

// =============================================================================
// SignupPage Field Patterns
// =============================================================================

/**
 * Matches: "auth.signup.fullName", "Full Name", "姓名"
 * Used for: SignupPage full name input field
 */
export const SIGNUP_FULL_NAME_LABEL = /^auth\.signup\.fullName$|^Full Name$|^姓名$/i

/**
 * Matches: "auth.signup.email", "Email", "電子郵件"
 * Used for: SignupPage email input field
 */
export const SIGNUP_EMAIL_LABEL = /^auth\.signup\.email$|^Email$|^電子郵件$/i

/**
 * Matches: "auth.signup.password", "Password", "密碼"
 * Used for: SignupPage password input field
 * Note: Anchored to prevent matching "Confirm Password" or "confirmPassword"
 */
export const SIGNUP_PASSWORD_LABEL = /^auth\.signup\.password$|^Password$|^密碼$/i

/**
 * Matches: "auth.signup.confirmPassword", "Confirm Password", "確認密碼"
 * Used for: SignupPage confirm password input field
 */
export const SIGNUP_CONFIRM_PASSWORD_LABEL = /^auth\.signup\.confirmPassword$|^Confirm Password$|^確認密碼$/i

// =============================================================================
// Common SSO Button Patterns
// =============================================================================

/**
 * SSO button patterns for querying by aria-label
 * These are used with screen.getByRole('button', { name: pattern })
 */
export const SSO_GOOGLE_BUTTON = /google/i
export const SSO_APPLE_BUTTON = /apple/i
export const SSO_GITHUB_BUTTON = /github/i
