module.exports = {
  morningai: {
    input: './src/lib/openapi.yaml',
    output: {
<<<<<<< HEAD:handoff/20250928/40_App/frontend-dashboard/orval.config.cjs
      target: 'src/lib/generated/api.ts',
=======
      target: 'src/lib/generated/api.js',
>>>>>>> origin/main:handoff/20250928/40_App/frontend-dashboard/orval.config.js
      client: 'fetch',
      override: {
        mutator: {
          path: 'src/lib/api.js',
          name: 'apiClient'
        }
      }
    }
  }
}
