module.exports = {
  morningai: {
    input: './src/lib/openapi.yaml',
    output: {
      target: 'src/lib/generated/api.ts',
      client: 'fetch',
      override: {
        mutator: {
          path: 'src/lib/api-client.ts',
          name: 'customFetch'
        }
      }
    }
  }
}
