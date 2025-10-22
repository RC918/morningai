const SSO_PROVIDERS = {
  GOOGLE: 'google',
  APPLE: 'apple',
  GITHUB: 'github'
}

const SSO_CONFIG = {
  [SSO_PROVIDERS.GOOGLE]: {
    clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID,
    redirectUri: `${window.location.origin}/auth/callback/google`,
    authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    scope: 'openid profile email',
    responseType: 'code'
  },
  [SSO_PROVIDERS.APPLE]: {
    clientId: import.meta.env.VITE_APPLE_CLIENT_ID,
    redirectUri: `${window.location.origin}/auth/callback/apple`,
    authUrl: 'https://appleid.apple.com/auth/authorize',
    scope: 'name email',
    responseType: 'code id_token',
    responseMode: 'form_post'
  },
  [SSO_PROVIDERS.GITHUB]: {
    clientId: import.meta.env.VITE_GITHUB_CLIENT_ID,
    redirectUri: `${window.location.origin}/auth/callback/github`,
    authUrl: 'https://github.com/login/oauth/authorize',
    scope: 'read:user user:email'
  }
}

export class SSOAuthService {
  constructor() {
    this.apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'
  }

  generateState() {
    const array = new Uint8Array(32)
    crypto.getRandomValues(array)
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
  }

  generateCodeVerifier() {
    const array = new Uint8Array(32)
    crypto.getRandomValues(array)
    return btoa(String.fromCharCode.apply(null, array))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '')
  }

  async generateCodeChallenge(verifier) {
    const encoder = new TextEncoder()
    const data = encoder.encode(verifier)
    const hash = await crypto.subtle.digest('SHA-256', data)
    return btoa(String.fromCharCode.apply(null, new Uint8Array(hash)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '')
  }

  async initiateGoogleLogin() {
    const config = SSO_CONFIG[SSO_PROVIDERS.GOOGLE]
    const state = this.generateState()
    const codeVerifier = this.generateCodeVerifier()
    const codeChallenge = await this.generateCodeChallenge(codeVerifier)

    sessionStorage.setItem('oauth_state', state)
    sessionStorage.setItem('code_verifier', codeVerifier)

    const params = new URLSearchParams({
      client_id: config.clientId,
      redirect_uri: config.redirectUri,
      response_type: config.responseType,
      scope: config.scope,
      state: state,
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
      access_type: 'offline',
      prompt: 'consent'
    })

    window.location.href = `${config.authUrl}?${params.toString()}`
  }

  async initiateAppleLogin() {
    const config = SSO_CONFIG[SSO_PROVIDERS.APPLE]
    const state = this.generateState()

    sessionStorage.setItem('oauth_state', state)

    const params = new URLSearchParams({
      client_id: config.clientId,
      redirect_uri: config.redirectUri,
      response_type: config.responseType,
      response_mode: config.responseMode,
      scope: config.scope,
      state: state
    })

    window.location.href = `${config.authUrl}?${params.toString()}`
  }

  async initiateGitHubLogin() {
    const config = SSO_CONFIG[SSO_PROVIDERS.GITHUB]
    const state = this.generateState()

    sessionStorage.setItem('oauth_state', state)

    const params = new URLSearchParams({
      client_id: config.clientId,
      redirect_uri: config.redirectUri,
      scope: config.scope,
      state: state,
      allow_signup: 'true'
    })

    window.location.href = `${config.authUrl}?${params.toString()}`
  }

  async handleCallback(provider, searchParams) {
    const state = searchParams.get('state')
    const code = searchParams.get('code')
    const error = searchParams.get('error')

    if (error) {
      throw new Error(`SSO Error: ${error} - ${searchParams.get('error_description') || 'Unknown error'}`)
    }

    const savedState = sessionStorage.getItem('oauth_state')
    if (state !== savedState) {
      throw new Error('Invalid state parameter - possible CSRF attack')
    }

    const codeVerifier = sessionStorage.getItem('code_verifier')

    sessionStorage.removeItem('oauth_state')
    sessionStorage.removeItem('code_verifier')

    const response = await fetch(`${this.apiBaseUrl}/api/auth/sso/callback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        provider,
        code,
        code_verifier: codeVerifier,
        redirect_uri: SSO_CONFIG[provider].redirectUri
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error?.message || 'SSO authentication failed')
    }

    return await response.json()
  }

  async loginWithProvider(provider) {
    switch (provider) {
      case SSO_PROVIDERS.GOOGLE:
        return await this.initiateGoogleLogin()
      case SSO_PROVIDERS.APPLE:
        return await this.initiateAppleLogin()
      case SSO_PROVIDERS.GITHUB:
        return await this.initiateGitHubLogin()
      default:
        throw new Error(`Unsupported SSO provider: ${provider}`)
    }
  }
}

export const ssoAuthService = new SSOAuthService()
export { SSO_PROVIDERS }
