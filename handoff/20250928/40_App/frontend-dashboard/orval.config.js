export default {
  morningai: {
    input: './src/lib/openapi.yaml',
    output: {
      mode: 'split',
      target: 'src/lib/generated/api.ts',
      schemas: 'src/lib/generated/schemas',
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
