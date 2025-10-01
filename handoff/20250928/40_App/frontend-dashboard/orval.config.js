export default {
  morningai: {
    input: './src/lib/openapi.yaml',
    output: {
      target: 'src/lib/generated/api.js',
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
